# -*- coding: utf-8 -*-
import sys
import json
import os

from apk import ApkInfo, Basic


CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.json")


# 設定ファイルから USERNAME と PASSWORD を取得
def load_credentials():
    try:
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
            return config["USERNAME"], config["PASSWORD"]
    except Exception as e:
        print(f"ERROR: Could not load configuration file: {e}")
        sys.exit(1)


USERNAME, PASSWORD = load_credentials()


def main():
    basic = Basic()
    apk = ApkInfo()

    # コマンドライン引数からホスト名を取得
    if len(sys.argv) < 2:
        print("ERROR: Invalid arguments. Please input IP address.")
        sys.exit(1)
    host = sys.argv[1]

    basic.ssh_connect(host, USERNAME, PASSWORD)
    if not basic.adb_check():
        sys.exit(1)
    else:
        print("INFO: Start collecting packages.\n")
        client = basic.ssh_connect(host, USERNAME, PASSWORD)
        if client:
            pkg_names = apk.get_package_name(client)
            print("\n".join(pkg_names))
            apk.get_activity_name(client)
            if apk.get_activity_name:
                print("INFO: Finished the scripts!")


if __name__ == "__main__":
    main()
