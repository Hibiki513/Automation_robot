# -*- coding: utf-8 -*-
import os
import glob
import sys
import re
import socket

import paramiko


class Basic:
    @staticmethod
    def adb_check(client):
        command = "adb devices"
        stdout, stderr = Basic.execute_command(client, command)

        if "devices" in stdout and "LPT" in stdout:
            print("INFO: ADB is enabled.")
            return True
        else:
            print("INFO: ADB is disabled.")
            return False

    @staticmethod
    def ssh_connect(hostname, USERNAME, PASSWORD):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(hostname, 22, USERNAME, PASSWORD, timeout=15)
            return client
        except paramiko.AuthenticationException:
            print("ERROR: Authentication failed. Please check your credentials.")
            sys.exit(1)
        except paramiko.SSHException:
            print("ERROR: SSH connection failed. Please check NW conditions.")
            sys.exit(1)
        except TimeoutError:
            print("ERROR: Connection timeout. Please check IP address and network.")
            sys.exit(1)
        except socket.gaierror:
            print("ERROR: Unable to resolve hostname. Please check IP address.")
            sys.exit(1)

    @staticmethod
    def execute_command(client, command):
        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        return output, error

    @staticmethod
    def get_remote_path(filename, remote_dir, USERNAME, apk_dir, err_flag):
        # ファイル拡張子またはerr_flagによってremote_pathを選択
        if filename.endswith(".pkg"):
            return f"{remote_dir}/{filename}"
        elif filename.endswith(".apk"):
            if err_flag == False:
                return f"/home/{USERNAME}{apk_dir}/{filename}"
            else:
                return f"{remote_dir}/{filename}"
        return None


class List:
    @staticmethod
    def file_lists():
        # ファイル拡張子によってapk, pkgのリストにわける
        files = glob.glob(os.path.join(os.path.dirname(__file__), "installApps", "*"))
        pkg_files = [file for file in files if file.endswith(".pkg")]
        apk_files = [file for file in files if file.endswith(".apk")]
        return pkg_files, apk_files


class Upload:
    @staticmethod
    def upload(client, file, remote_dir, USERNAME, apk_dir, err_flag=False):
        # ファイルをアップロード
        sftp = client.open_sftp()
        filename = file.split("/")[-1]
        remote_path = Basic.get_remote_path(filename, remote_dir, USERNAME, apk_dir, err_flag)

        try:
            sftp.put(file, remote_path)
            print("true")
            print(f"INFO: Succeed to upload {filename}")
        except Exception as e:
            print("false")
            print(f"ERROR: Failed to upload {filename}: {str(e)}")
        sftp.close()


class Install:
    @staticmethod
    def install(client, file, remote_dir, USERNAME, apk_dir, adb_flag):
        # ファイルをインストール (ALTabletServiceエラー時はadb_flag==Trueの場合のみADB インストールを実行)
        err_flag = False
        output = ""

        if file.endswith(".pkg"):
            filename = file.split("/")[-1]
            command = f"qicli call PackageManager.install {remote_dir}/{filename}"
            output, error = Basic.execute_command(client, command)
        elif file.endswith(".apk") and not err_flag:
            filename = os.path.basename(file)
            command = f'qicli call ALTabletService._installApk "http://198.18.0.1/apps/boot-config/{filename}"'
            output, error = Basic.execute_command(client, command)

            # ALTabletServiceエラー時の処理
            if "no attribute ALTabletService" in output:
                print(f"ERROR: Not found ALTabletService.")
                if adb_flag == True:
                    print("INFO: Retrying APK upload and install.")
                    err_flag = True
                    Upload.upload(client, file, remote_dir, USERNAME, apk_dir, err_flag=True)
                    adb_command = f"adb install -r {remote_dir}/{filename}"
                    output, error = Basic.execute_command(client, adb_command)
                else:
                    return Install.check_version(client, filename, output)

        elif file.endswith(".apk") and err_flag:
            print("INFO: Installing APK using ADB due to previous ALTabletService error.")
            adb_command = f"adb install -r {remote_dir}/{file}"
            output, error = Basic.execute_command(client, adb_command)

        Install.check_version(client, filename, output)
        return err_flag

    @staticmethod
    def check_version(client, filename, output):
        # インストール後のバージョン確認
        file = filename.split("/")[-1]

        if filename.endswith('.apk'):
            base_name = "-".join(filename.split("-")[:-1])
            command = f'qicli call ALTabletService._getApkVersion {base_name}'
        elif filename.endswith('.pkg'):
            base_name = filename.split("/")[-1].rsplit("-", 1)[0]
            command = f"cat .local/share/PackageManager/apps/{base_name}/manifest.xml | grep version"

        check, error = Basic.execute_command(client, command)
        if filename.endswith(".pkg"):  # PKGの場合はバージョンを抽出
            match = re.search(r'version="([0-9]+\.[0-9]+\.[0-9]+|[0-9]+\.[0-9]+)"', check)
            if match:
                check = match.group(1)  # マッチしたバージョン番号を取得
            else:
                check = None
        version = filename.split("-")[-1].rsplit(".", 1)[0]  # ファイル名からバージョンを抽出
        print("INFO: Current installed version:", check)

        if not check or "." not in check:
            print("Failure")
            print(f"ERROR: Failed to install {file} Please check file.")
        elif "Success" in output:
            print("Success")
            print(f"Succeed to install {file}")
        elif "ALTabletService" in check:
            print(f"ERROR: Failed to install {file} due to no ALTabletService.")
        elif version in check and ("true" in output or "Success" in output):
            print("Success")
            print(f"INFO: Succeed to install {file}")
        elif version in check and ("false" in output):
            print(f"INFO: {file} is already installed.")
        elif "ALTabletService" not in check:
            print(f"ERROR: Failed to install {file} Please check the version.")


class Clean:
    @staticmethod
    def remove(client, file, remote_dir, USERNAME, apk_dir, err_flag=False):
        # 不要ファイルを削除
        filename = os.path.basename(file)
        remote_path = Basic.get_remote_path(filename, remote_dir, USERNAME, apk_dir, err_flag)

        command = f"rm {remote_path}"
        Basic.execute_command(client, command)
        print(f"INFO: Cleaned up {filename}")
