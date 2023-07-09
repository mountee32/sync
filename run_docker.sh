#!/bin/bash
cd /home/andy/docker/sftpsync/
#! 
# Fetch the remote repository
git stash save "Saving local changes"
git fetch https://github.com/mountee32/sync.git

# Reset your local branch to match the remote branch
git reset --hard FETCH_HEAD

# Navigate into the repository directory
cd sync

# Build the Docker Image
sudo docker build -t sftpsync .

# Run the Docker Container with a Bind Mount
# Replace /path/to/data with the path to your data directory
sudo docker run -v /home/andy/docker/sftpsync/data:/app/data -d sftpsync
