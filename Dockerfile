FROM python:3.9

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install rclone
RUN apt-get update && apt-get install -y rclone

# Copy the rclone configuration file
COPY .rclone.conf /root/.config/rclone/rclone.conf

# Copy the current directory contents into the container at /app
COPY . /app

# Set the working directory to /app
WORKDIR /app

# Run the command to start your application
CMD ["python", "./sftpsync.py"]
