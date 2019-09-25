FROM debian:buster-slim
RUN apt-get update && apt-get install -y \
  ceph-common \
  python3-bottle \
  uwsgi \
  uwsgi-plugin-python3
ADD docker-volume-rbd.py /
