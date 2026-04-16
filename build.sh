#!/bin/bash

# Fast build with Docker BuildKit
DOCKER_BUILDKIT=1 docker-compose build --progress=plain

# Or for even faster rebuilds with cache:
# docker buildx build --cache-from=type=local,src=/tmp/.buildx-cache --cache-to=type=local,dest=/tmp/.buildx-cache -t construction-planner .
