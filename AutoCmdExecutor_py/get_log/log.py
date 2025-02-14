import os
import re
import sys
from datetime import datetime
from stat import S_ISDIR
import socket
import tarfile

import paramiko
import pexpect


class Basic:
    ssh_client = None

    def ssh_connect(self, hostname, USERNAME, PASSWORD):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            client.connect(hostname, 22, USERNAME, PASSWORD)
            return client
        except paramiko.AuthenticationException:
            print("ERROR: Authentication failed. Please check your credentials.")
        except paramiko.SSHException:
            print("ERROR: SSH connection failed.")
        except TimeoutError:
            print("ERROR: Connection timeout. Please check IP address and network.")
            sys.exit(1)
        except socket.gaierror:
            print("ERROR: Unable to resolve hostname. Please check IP address.")
            sys.exit(1)


class LOG(Basic):
    def download_log(self, ssh_client, remote_dir, local_path, log_name):
        print(f"INFO: Downloading {log_name}. Please wait for a while...")
        try:
            with ssh_client.open_sftp() as sftp:
                self.copy_log(sftp, remote_dir, local_path)
            print("INFO: Succeed to download logs.")
        except Exception:
            print(f"ERROR: Failed to download logs. Please install LogTool.")

    def copy_log(self, sftp, remote_dir, local_path):
        for entry in sftp.listdir(remote_dir):
            remote_entry = os.path.join(remote_dir, entry)
            local_entry = os.path.join(local_path, entry)
            mode = sftp.stat(remote_entry).st_mode
            if S_ISDIR(mode):
                os.makedirs(local_entry, exist_ok=True)
                self.copy_log(sftp, remote_entry, local_entry)
            else:
                sftp.get(remote_entry, local_entry)
                self.progress(sftp, remote_entry, local_entry)

    def progress(self, sftp, remote_file, local_file, chunk_size=10 * 1024 * 1024):
        file_size = sftp.stat(remote_file).st_size
        bytes_received = 0

        with sftp.open(remote_file, 'rb') as remote_f, open(local_file, 'wb') as local_f:
            while bytes_received < file_size:
                data = remote_f.read(chunk_size)
                if not data:
                    break
                local_f.write(data)
                bytes_received += len(data)
                progress = (bytes_received / file_size) * 100

                if progress == 100:  # Only display when progress is 100%
                    remote_file = os.path.basename(remote_file)
                    print(remote_file)
                    break

    def get_logcat(self, ssh_client, folder_manager, LOGCAT_DIR):
        logcat_folder = folder_manager.create_subfolder("logcat")
        self.download_log(ssh_client, LOGCAT_DIR, logcat_folder, "logcat")

    def get_logger(self, ssh_client, folder_manager, LOGGER_DIR):
        logger_folder = folder_manager.create_subfolder("new-logger")
        self.download_log(ssh_client, LOGGER_DIR, logger_folder, "new-logger")


class Report(Basic):
    def generate_report(self, hostname, ssh_client, folder_manager):
        local_path = folder_manager.base_folder
        if not ssh_client:
            return
        stdin, stdout, stderr = ssh_client.exec_command("test-diagnostic")
        print("INFO: Generating report. Please wait for a while...")

        tar_pattern = re.compile(r'/home/test/diagnosis/test-diagnosis_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}\.tar\.xz')
        for line in stdout:
            print(line.strip())
            match = tar_pattern.search(line)
            if match:
                zip_name = match.group(0)
                self.get_test(hostname, zip_name, local_path)
                break

    def get_test(self, hostname, USERNAME, PASSWORD, zip_name, local_path):
        scp_command = f"scp -r {USERNAME}@{hostname}:{zip_name} {local_path}"
        scp_child = pexpect.spawn(scp_command, timeout=300, encoding="utf-8")
        scp_child.logfile_read = sys.stdout

        try:
            index = scp_child.expect(
                ["[Pp]assword:", "Are you sure you want to continue connecting", pexpect.EOF,
                 pexpect.TIMEOUT])
            print(index)
            if index == 0:  # パスワード入力
                scp_child.sendline(PASSWORD)
            elif index == 1:  # 初回接続確認
                scp_child.sendline("yes")
                scp_child.expect("[Pp]assword:")
                scp_child.sendline(PASSWORD)

            scp_child.expect(pexpect.EOF)
            scp_child.close()

            if scp_child.exitstatus == 0:
                print("INFO: Succeed to download")
                Unzip().unzip(local_path, zip_name)
            else:
                print(f"ERROR: Failed to download. Exit status: {scp_child.exitstatus}")

        except pexpect.exceptions.TIMEOUT:
            print("ERROR: Connection timeout. Please check NW and IP address.")
        except Exception as e:
            print(f"ERROR: Unexpected error occurred: {str(e)}")


class Unzip:
    def unzip(self, local_path, zip_name):
        zip_name = zip_name[20:]
        tar_name = zip_name[:-7] if zip_name.endswith('.tar.xz') else zip_name
        tar_path = os.path.join(local_path, zip_name)

        if os.path.isfile(tar_path):
            try:
                with tarfile.open(tar_path, 'r:xz') as tar:
                    extract_dir = os.path.join(local_path, tar_name)
                    tar.extractall(path=extract_dir)
                print("INFO: Succeed to unzip.")
                os.remove(tar_path)
                print("INFO: Deleted original zip.")
            except Exception as e:
                print(f"ERROR: Failed to unzip: {str(e)}")
        else:
            print("ERROR: ZIP file does not exist")


class newFolder:
    desktop_dir = os.path.expanduser("~/Desktop")

    def create_base_folder(self, hostname):
        now = datetime.now()
        folder_name = f"Log_{now.strftime('%Y-%m-%d_%H-%M-%S')}_{hostname}"
        self.base_folder = os.path.join(self.desktop_dir, folder_name)
        try:
            os.makedirs(self.base_folder, exist_ok=True)
            return self.base_folder
        except Exception as e:
            print(f"ERROR: Failed to create base folder: {str(e)}")
            return None

    def create_subfolder(self, subfolder_name):
        subfolder_path = os.path.join(self.base_folder, subfolder_name)
        try:
            os.makedirs(subfolder_path, exist_ok=True)
            return subfolder_path
        except Exception as e:
            print(f"ERROR: Failed to create subfolder: {str(e)}")
            return None
