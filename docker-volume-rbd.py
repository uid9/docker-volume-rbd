#!/usr/bin/python3

from bottle import Bottle, run, post, request
import os
import json
import random
import socket
from pathlib import Path
import subprocess


app = application = Bottle()
pool = os.getenv('RBD_POOL', 'rbd')
mount_options = os.getenv('MOUNT_OPTIONS')

@app.post('/Plugin.Activate')
def activate():
    return { "Implements": ["VolumeDriver"] }

@app.post('/VolumeDriver.Capabilities')
def list():
    return { "Capabilities": { "Scope": "global" } }

@app.post('/VolumeDriver.Get')
def get():
    data = json.loads(request.body.read().decode())
    name = data['Name']
    cp = subprocess.run(['rbd', '-p', pool, 'status', name], capture_output=True)
    if cp.returncode != 0:
        return { "Err": cp.stderr.decode() }
    return { "Volume": { "Name": name }, "Err": "" }

@app.post('/VolumeDriver.Create')
def create():
    data = json.loads(request.body.read().decode())
    if not 'Name' in data:
        name = ''.join(random.choice('0123456789abcdef') for _ in range(65))
    else:
        name = data['Name']
    if 'Opts' in data:
        size = data['Opts']['size'] if 'size' in data['Opts'] else '10240'
        fstype = data['Opts']['fstype'] if 'fstype' in data['Opts'] else 'ext4'
        mkfsopts = data['Opts']['mkfsopts'] if 'mkfsopts' in data['Opts'] else '-O mmp'
    cp = subprocess.run(['rbd', '-p', pool, 'create', name, '--size', size], capture_output=True)
    if cp.returncode != 0:
        return { "Err": cp.stderr.decode() }
    cp = subprocess.run(['rbd', '-p', pool, 'map', name], capture_output=True)
    if cp.returncode != 0:
        return { "Err": cp.stderr.decode() }
    device = cp.stdout.decode().strip()
    mkfs_cmd = ['mkfs', '-t', fstype] + mkfsopts.split() + [device]
    cp = subprocess.run(mkfs_cmd, capture_output=True)
    if cp.returncode != 0:
        return { "Err": cp.stderr.decode() }
    cp = subprocess.run(['rbd', '-p', pool, 'unmap', name], capture_output=True)
    if cp.returncode != 0:
        return { "Err": cp.stderr.decode() }
    return { "Err": "" }

@app.post('/VolumeDriver.Remove')
def remove():
    data = json.loads(request.body.read().decode())
    cp = subprocess.run(['rbd', '-p', pool, 'rm', data['Name']], capture_output=True)
    if cp.returncode != 0:
        return { "Err": cp.stderr.decode() }
    return { "Err": "" }

@app.post('/VolumeDriver.List')
def list():
    data = json.loads(request.body.read().decode())
    cp = subprocess.run(['rbd', '-p', pool, 'ls'], capture_output=True)
    if cp.returncode != 0:
        return { "Err": cp.stderr.decode() }
    volumes = [ { "Name": _ } for _ in cp.stdout.decode().strip().split() ]
    return { "Volumes": volumes, "Err": "" }

@app.post('/VolumeDriver.Mount')
def mount():
    data = json.loads(request.body.read().decode())
    name = data['Name']
    mountpoint = '/mnt/' + name
    p = Path(mountpoint)
    p.mkdir(parents=True, exist_ok=True)
    cp = subprocess.run(['rbd', '-p', pool, 'map', name], capture_output=True)
    if cp.returncode != 0:
        return { "Err": cp.stderr.decode() }
    device = cp.stdout.decode().strip()
    cp = subprocess.run(['mount', '-o', mount_options, device, mountpoint], capture_output=True)
    if cp.returncode != 0:
        return { "Err": cp.stderr.decode() }
    return { "Mountpoint": mountpoint, "Err": "" }

@app.post('/VolumeDriver.Path')
def path():
    data = json.loads(request.body.read().decode())
    name = data['Name']
    mountpoint = ""
    p = Path('/mnt/' + name)
    if p.exists() and p.is_mount():
        mountpoint = p.as_posix()
    return { "Mountpoint": mountpoint, "Err": "" }

@app.post('/VolumeDriver.Unmount')
def unmount():
    data = json.loads(request.body.read().decode())
    name = data['Name']
    mountpoint = '/mnt/' + name
    cp = subprocess.run(['umount', mountpoint], capture_output=True)
    if cp.returncode != 0:
        return { "Err": cp.stderr.decode() }
    cp = subprocess.run(['rbd', '-p', pool, 'unmap', name], capture_output=True)
    if cp.returncode != 0:
        return { "Err": cp.stderr.decode() }
    Path(mountpoint).rmdir()
    return { "Err": "" }
