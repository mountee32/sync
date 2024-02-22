import os
import stat
import paramiko
import subprocess
import time
from dotenv import load_dotenv
from loguru import logger
from tqdm import tqdm

# Load .env file
load_dotenv("./config/.env")

# Define environment variables and settings
env = os.getenv("ENV").lower()
connection_host = os.getenv(f"{env.upper()}_CONNECTION_HOST")
connection_user = os.getenv(f"{env.upper()}_CONNECTION_USER")
connection_password = os.getenv(f"{env.upper()}_CONNECTION_PASSWORD")
connection_private_key = os.getenv(f"{env.upper()}_CONNECTION_PRIVATE_KEY")
connection_dir = os.getenv(f"{env.upper()}_CONNECTION_DIR")
local_dir = os.getenv("LOCAL_DIR")
log_path = "./data/"+os.getenv("LOG_FILE")
wait_time = int(os.getenv("WAIT_TIME", "30"))  # Default wait time in seconds

MAX_RETRIES = 3
RETRY_WAIT_TIME = 5 * 60  # 5 minutes

# Setup logging
logger.add(log_path, rotation="500 MB")
if not env or not connection_host:
    logger.error("Required environment variables are missing.")
    exit(1)

logger.info(f"Connecting to {env.upper()} environment")

class FileDownloader:
    def __init__(self):
        self.progress_bar = None

    def progress_callback(self, size, sent):
        self.progress_bar.update(sent)

    def download_new_or_updated_files(self, sftp, remote_dir, local_dir):
        try:
            remote_files = sftp.listdir_attr(remote_dir)
        except Exception as e:
            logger.error(f"Failed to list directory: {remote_dir}. Error: {e}")
            return

        for file in remote_files:
            remote_file_path = os.path.join(remote_dir, file.filename)
            local_file_path = os.path.join(local_dir, file.filename)

            if stat.S_ISDIR(file.st_mode):
                logger.info(f"Found directory: {file.filename}")
                if not os.path.exists(local_file_path):
                    os.makedirs(local_file_path, exist_ok=True)
                self.download_new_or_updated_files(sftp, remote_file_path, local_file_path)
            else:
                logger.info(f"Found file: {file.filename}, Size: {file.st_size} bytes")
                # Your logic for handling files (downloading or skipping) goes here
                # This is simplified for brevity
                with tqdm(total=file.st_size, unit='B', unit_scale=True, desc=file.filename) as self.progress_bar:
                    sftp.get(remote_file_path, local_file_path, callback=self.progress_callback)

def establish_connection(retry_limit=MAX_RETRIES, retry_wait=RETRY_WAIT_TIME):
    for attempt in range(retry_limit):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(connection_host, username=connection_user, password=connection_password, key_filename=connection_private_key, timeout=10)
            sftp = ssh.open_sftp()
            return ssh, sftp
        except Exception as e:
            logger.error(f"Attempt {attempt+1} failed: {e}")
            if attempt < retry_limit - 1:
                time.sleep(retry_wait)
            else:
                logger.error("Max retries reached. Exiting...")
                exit(1)

# Main script execution
ssh, sftp = establish_connection()
downloader = FileDownloader()
downloader.download_new_or_updated_files(sftp, connection_dir, local_dir)

# Cleanup
if sftp:
    sftp.close()
if ssh:
    ssh.close()

# Wait before exit (if needed)
logger.info(f"Now waiting for: {wait_time} Seconds")
time.sleep(wait_time)
