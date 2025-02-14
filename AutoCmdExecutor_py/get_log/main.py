import sys
import json
import os

from log import Basic, LOG, Report, newFolder


LOGCAT_DIR = "/home/test/.local/share/PackageManager/apps/packageName/log/logcat"
LOGGER_DIR = "/home/test/.local/share/PackageManager/apps/packageName"
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
    log = LOG()
    report = Report()
    folder = newFolder()

    # コマンドライン引数からホスト名を取得
    if len(sys.argv) < 2:
        print("ERROR: Invalid arguments. Please enter at least one IP address.")
        sys.exit(1)
    hostnames = sys.argv[1:]

    for hostname in hostnames:
        ssh_client = basic.ssh_connect(hostname, USERNAME, PASSWORD)
        print("INFO: Start to get log from", hostname)
        if ssh_client:
            folder.create_base_folder(hostname)

            log.get_logcat(ssh_client, folder, LOGCAT_DIR)
            log.get_logger(ssh_client, folder, LOGGER_DIR)
            report.generate_report(hostname, USERNAME, PASSWORD, ssh_client, folder)
            ssh_client.close()
    print("Finished the script!")


if __name__ == "__main__":
    main()
