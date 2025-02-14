# -*- coding: utf-8 -*-
import sys
import socket
import re
import subprocess

import paramiko


class Basic:
    def adb_check(self):
        try:
            adb_path = "/usr/local/bin/adb"
            subprocess.run([adb_path, "version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except (subprocess.CalledProcessError, IOError):
            print("ERROR: ADB is disabled.")
            return False

    def ssh_connect(self, hostname, USERNAME, PASSWORD):
        # SSHクライアントの作成
        client = paramiko.SSHClient()
        # ホスト鍵の自動追加を許可
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


class ApkInfo(Basic):
    def get_package_name(self, client):
        command = f"adb shell pm list packages"
        try:
            stdin, stdout, stderr = client.exec_command(command)
            print("Packages:")
            pkg_list = stdout.read().decode().strip().split("\n")
            pkgs = [re.sub(r'^package:', '', line).strip() for line in pkg_list]
            pkgs = [pkg for pkg in pkgs if re.search(r"^com\.test\..*", pkg)]
            return pkgs
        except Exception as e:
            print(f"ERROR: Command execution failed: {e}")

    def get_activity_name(self, client):
        while True:
            apk_input = input("Please enter the package name: ").strip()
            command = f"adb shell dumpsys package {apk_input}"
            stdin, stdout, stderr = client.exec_command(command)

            error_message = stderr.read().decode().strip()
            if error_message:
                print(f"ERROR: {error_message}")

            apk_info = stdout.read().decode().strip().splitlines()
            fourth_line = apk_info[3].strip()

            pattern = r"(com\.test\.[\w\.]+/[\w\.]+Activity)"
            match = re.search(pattern, fourth_line)

            if match:
                extracted_name = match.group(1)
                print(f"Extracted package/activity: {extracted_name}")
                if apk_input in extracted_name:
                    package_name, activity_name = match.group(0).split("/", 1)  # `/` で分割
                    print(f"\nPackageName: {package_name}\nActivityName: {activity_name}\n")
                    return True
                else:
                    print("ERROR: apk_input not found in extracted name.")
