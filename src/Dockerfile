# Use an official Python runtime as a parent image
FROM python:3.9

# Set the working directory to /app
WORKDIR /app

# Install dependencies
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install rclone
RUN apt-get update && apt-get install -y rclone

# Copy the config directory into the container at /app/config
COPY config/ config/

# Copy the rclone configuration file from the copied config directory
COPY config/.rclone.conf /root/.config/rclone/rclone.conf

# Verify rclone installation
RUN rclone version

# Copy the source code into the container
COPY src/* ./

# Run the command to start your application
CMD ["python", "./sftpsync.py"]
