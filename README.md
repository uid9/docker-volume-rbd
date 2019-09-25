# Docker volume plugin for ceph rbd
This plugin can be used to create rbd images and mount them within docker containers.
## Usage
### Install the plugin
```
docker volume install uid9/rbd \
    --alias=ssd_rbd \
    RBD_POOL="ssd" \
```
#### Driver configuration options
```
RBD_POOL: optional, defaults to 'rbd'
MOUNT_OPTIONS: optional, defaults to 'noatime' (comma separated syntax)
```
### Create a volume
```
docker volume create -d ssd_rbd -o size=512 myvol

~$ docker volume ls
DRIVER              VOLUME NAME
ssd_rbd:latest      myvol
```
#### Volume creation options
```
size: optional, defaults to 10240 (MB)
fstype: optional, defauls to ext4
mkfsopts: optional, defaults to '-O mmp' (multiple mount protection)
```
### Use a volume
```
docker run -it -v myvol:/mnt alpine sh
```
