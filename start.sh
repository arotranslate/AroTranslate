#!/bin/bash

gunicorn --bind 0.0.0.0:5000 --worker-tmp-dir /dev/shm --workers 2 --worker-class gevent --worker-connections 1000 app:app