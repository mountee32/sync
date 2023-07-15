import os
import stat
import paramiko
import subprocess
import time
from dotenv import load_dotenv
from loguru import logger
import shutil
from tqdm import tqdm

# Load .env file
load_dotenv("./config/.env")

class FileDownloader:
    def __init__(self):
        self.progress_bar = None

    def progress_callback(self, size, sent):
        self.progress_bar.update(sent)

    def download_new_or_updated_files(self, sftp, remote_dir, local_dir):
        remote_files = sftp.listdir_attr(remote_dir)

        for file in remote_files:
            remote_file = os.path.join(remote_dir, file.filename)
            local_file = os.path.join(local_dir, file.filename)

            if stat.S_ISDIR(file.st_mode):
                logger.info(f"Found the following directory: {file.filename}")
                if os.path.isfile(local_file):
                    logger.error(f"Error: File with the same name as the directory already exists: {local_file}")
                    continue
                os.makedirs(local_file, exist_ok=True)
                self.download_new_or_updated_files(sftp, remote_file, local_file)
            else:
                logger.info(f"Found the following file: {file.filename}")

                if file.st_size > 1e9:  # Skip files larger than 1GB
                    logger.info(f"Skipping file {file.filename} as it is larger than 1GB.")
                    continue

                if os.path.exists(local_file):
                    local_file_stat = os.stat(local_file)
                    if local_file_stat.st_mtime < file.st_mtime:
                        logger.info("File has been updated on the server, downloading new version...")
                        with tqdm(total=file.st_size, unit='B', unit_scale=True, desc=file.filename) as self.progress_bar:
                            sftp.get(remote_file, local_file, callback=self.progress_callback)
                else:
                    logger.info("New file found on the server, downloading...")
                    with tqdm(total=file.st_size, unit='B', unit_scale=True, desc=file.filename) as self.progress_bar:
                        sftp.get(remote_file, local_file, callback=self.progress_callback)

connection_host = os.getenv("CONNECTION_HOST")
connection_user = os.getenv("CONNECTION_USER")
connection_password = os.getenv("CONNECTION_PASSWORD")
connection_private_key = os.getenv("CONNECTION_PRIVATE_KEY")
connection_dir = os.getenv("CONNECTION_DIR")

local_dir = os.getenv("LOCAL_DIR")

log_path = "./data/"+os.getenv("LOG_FILE")
logger.add(log_path, rotation="500 MB")

wait_time = int(os.getenv("WAIT_TIME", "30"))  # Default wait time in seconds if the env variable is not set

MAX_RETRIES = 3
RETRY_WAIT_TIME = 5 * 60  # 5 minutes

downloader = FileDownloader()

for attempt in range(MAX_RETRIES):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(connection_host, username=connection_user, password=connection_password, key_filename=connection_private_key)
        sftp_client = ssh.open_sftp()
        downloader.download_new_or_updated_files(sftp_client, connection_dir, local_dir)
        break  # If the download was successful, we break the loop and do not retry
    except paramiko.AuthenticationException as auth_error:
        logger.error(f"Authentication failed, please verify your credentials: {auth_error}")
    except Exception as e:
        logger.error(f"Failed to connect to SFTP server: {e}")
    finally:
        if sftp_client:
            sftp_client.close()
        if ssh:
            ssh.close()

    if attempt < MAX_RETRIES - 1:  # If this was not the last attempt
        logger.info(f"Retrying in {RETRY_WAIT_TIME/60} minutes...")
        time.sleep(RETRY_WAIT_TIME)
    else:
        logger.error("Max retries reached. Exiting...")
        exit(1)

rclone_path = os.getenv("RCLONE_PATH")
rclone_command = ["rclone", "--config=./config/rclone.conf", "copy", "-v", "--update", local_dir, rclone_path]
rclone_process = subprocess.run(rclone_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

stdout = rclone_process.stdout.decode()
if stdout.strip():
    logger.info(stdout)
else:
    logger.info("Rclone command executed successfully but produced no stdout output.")

stderr = rclone_process.stderr.decode()
if stderr.strip():
    if rclone_process.returncode != 0:  # If there's an error
        logger.error(stderr)
    else:  # If there's no error
        logger.info(stderr)

time.sleep(wait_time)
