#!/bin/bash

# The script assumes the following directory structure:
# /home/andy/docker/sftpsync/src/ : Directory of the local git repository with source code.
# /home/andy/docker/sftpsync/config/ : Directory that contains local configuration files.
# /home/andy/docker/sftpsync/data/ : Directory that contains local data that we want to preserve.

# Navigate into the local repository directory.
cd /home/andy/docker/sftpsync/

# Fetch the updates from the remote repository.
git fetch https://github.com/mountee32/sync.git

cd src

# Reset your local branch to match the remote branch.
git reset --hard FETCH_HEAD

cd /home/andy/docker/sftpsync/
# Build the Docker Image
docker build -t sftpsync .

# Run the Docker Container with a Bind Mount
# The data directory is mounted into the Docker container
docker run -v /home/andy/docker/sftpsync/data:/app/data -d sftpsync
