#!/bin/sh
set -e
sleep 3
mc alias set local http://minio:9000 minioadmin minioadmin
mc mb -p local/sdlc-audit || true
mc anonymous set download local/sdlc-audit || true
echo "bucket ready"
