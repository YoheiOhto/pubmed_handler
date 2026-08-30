#!/bin/bash

set -e

mkdir -p ../sif

apptainer build \
  ../sif/elasticsearch.sif \
  docker://docker.elastic.co/elasticsearch/elasticsearch:8.13.2