#!/bin/bash
cd /home/andy/docker/sftpsync/
# Step 1: Clone the repository
git clone https://github.com/mountee32/sync.git

# Step 2: Navigate into the cloned repository
cd sync

# Step 3: Build the Docker Image
sudo docker build -t sftpsync .

# Step 4: Run the Docker Container with a Bind Mount
# Replace /path/to/data with the path to your data directory
sudo docker run -v /home/andy/docker/sftpsync/data:/app/data -d sftpsync
