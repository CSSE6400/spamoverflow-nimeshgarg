#!/bin/bash

# Change to the app folder.
cd app

sudo apt-get install docker-compose-plugin -y
# Buildkit to make sure we know what env
export DOCKER_BUILDKIT=1

# Build the docker container.
# docker build -t s4359540 .
docker compose up

# Run the docker container in the background and remove after its closed.
# docker run -d --rm -p 8080:8080 s4359540