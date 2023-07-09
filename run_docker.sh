#!/bin/bash

# Step 1: Clone the repository
git clone https://github.com/mountee32/sync.git

# Step 2: Navigate into the cloned repository
cd sync

# Step 3: Build the Docker Image
docker build -t sftpsync .

# Step 4: Run the Docker Container with a Bind Mount
# Replace /path/to/data with the path to your data directory
docker run -v /path/to/data:/app/data -d my-python-app
