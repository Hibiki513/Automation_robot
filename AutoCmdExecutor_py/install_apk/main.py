import sys
import json
import os

from install import Basic, List, Upload, Install, Clean


remote_dir = "/home/test"
apk_dir = "/.local/share/PackageManager/apps/boot-config/html/"
adb_flag = True
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
    files = List()
    upload = Upload()
    install = Install()
    clean = Clean()

    # ファイルのリスト取得
    pkg_files, apk_files = files.file_lists()
    all_files = pkg_files + apk_files

    if len(sys.argv) < 2:
        print("ERROR: Invalid arguments. Please check it and retry.")
        sys.exit(1)
    hostnames = sys.argv[1:]

    for host in hostnames:
        client = basic.ssh_connect(host, USERNAME, PASSWORD)
        print(f"INFO: Start to install files on {host}")

        adb_flag = basic.adb_check(client)
        err_flag = False  # 初期状態ではエラーフラグを False にする

        # すべてのファイルをアップロード
        print("INFO: Uploading files. Please wait for a while...")
        for file in all_files:
            upload.upload(client, file, remote_dir, USERNAME, apk_dir, err_flag)
        # すべてのファイルをインストール
        print("INFO: Installing files. Please wait for a while...")
        for file in all_files:
            install_err = install.install(client, file, remote_dir, USERNAME, apk_dir, adb_flag)
            if install_err:
                err_flag = True  # エラーフラグを更新
        # 全てのファイルをクリーンアップ
        for file in all_files:
            clean.remove(client, file, remote_dir, USERNAME, apk_dir, err_flag)

    print("INFO: Finished the scripts!")


if __name__ == "__main__":
    main()
