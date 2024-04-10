import os
import stat
import paramiko
import subprocess
import time
import json
from dotenv import load_dotenv
from loguru import logger
import shutil
from tqdm import tqdm

# Load .env file
load_dotenv("./config/.env")

# Load environment
env = os.getenv("ENV")

if env.lower() == "live":
    connection_host = os.getenv("CONNECTION_HOST")
    connection_user = os.getenv("CONNECTION_USER")
    connection_password = os.getenv("CONNECTION_PASSWORD")
    connection_private_key = os.getenv("CONNECTION_PRIVATE_KEY")
    connection_dir = os.getenv("CONNECTION_DIR")
elif env.lower() == "uat":
    connection_host = os.getenv("UAT_CONNECTION_HOST")
    connection_user = os.getenv("UAT_CONNECTION_USER")
    connection_password = os.getenv("UAT_CONNECTION_PASSWORD")
    connection_private_key = os.getenv("UAT_CONNECTION_PRIVATE_KEY")
    connection_dir = os.getenv("UAT_CONNECTION_DIR")
else:
    logger.error(f"Invalid environment: {env}")
    exit(1)
logger.info(f"Connecting to {env.upper()} environment")
local_dir = os.getenv("LOCAL_DIR")

# Load files to skip
try:
    with open("files_to_skip.json", "r") as f:
        files_to_skip = json.load(f)["files_to_skip"]
except FileNotFoundError:
    logger.warning("files_to_skip.json file not found. Assuming no files to skip.")
    files_to_skip = []
except json.JSONDecodeError as e:
    logger.error(f"Error parsing files_to_skip.json: {e}")
    exit(1)

log_path = "./data/" + os.getenv("LOG_FILE")
logger.add(log_path, rotation="500 MB")

wait_time = int(os.getenv("WAIT_TIME", "30"))  # Default wait time in seconds if the env variable is not set

MAX_RETRIES = 3
RETRY_WAIT_TIME = 5 * 60  # 5 minutes

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
                logger.info(f"Size of the file is: {file.st_size} bytes")

                if file.st_size > 1e9:  # Skip files larger than 1GB
                    logger.info(f"Skipping file {file.filename} as it is larger than 1GB.")
                    continue

                if file.filename in files_to_skip:
                    logger.info(f"Skipping file {file.filename} as it is in the files_to_skip list.")
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
#change below when running in replit 
if env.lower() == "live":
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