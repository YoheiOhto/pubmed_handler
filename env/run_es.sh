#!/bin/bash

set -e

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)

ESDATA=${ROOT_DIR}/data/esdata

mkdir -p "${ESDATA}"

ulimit -n 65535

echo "[INFO] Starting Elasticsearch..."

apptainer exec \
  --cleanenv \
  --env discovery.type=single-node \
  --env xpack.security.enabled=false \
  --env ES_JAVA_OPTS="-Xms4g -Xmx4g" \
  --bind ${ESDATA}:/usr/share/elasticsearch/data \
  ${ROOT_DIR}/sif/elasticsearch.sif \
  /usr/local/bin/docker-entrypoint.sh eswrapper