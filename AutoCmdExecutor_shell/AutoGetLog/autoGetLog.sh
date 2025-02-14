#!/bin/bash

# 定数の定義
host=$1
id="test"
pass="test"
LOGCAT_DIR="/home/test/.local/share/PackageManager/apps/packageName/log/logcat"
LOGGER_DIR="/home/test/.local/share/PackageManager/apps/packageName"


auto_ssh() {
    local host=$1

    output=$(expect -c "
    set timeout 15
    spawn ssh ${id}@${host}
    expect {
        \"Are you sure you want to continue connecting\" {
            send \"yes\n\"
            expect \"Password:\"
            send \"${pass}\n\"
        }
        \"Password:\" {
            send \"${pass}\n\r\"
        }
        \"ssh:\" {
            puts \"ERROR: Please check IP address and network.\"
            exit 1
        }
        \"WARNING\" {
            puts \"ERROR: WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!\"
            exit 1
        }
        timeout {
            puts \"ERROR: Connection timeout. Please check IP address and network.\"
            exit 1
        }
    }
    ")

    if [[ "$output" == *"ERROR"* ]]; then
        echo $output
        exit 1
    fi
}

# SSH接続確認
ssh_connect() {
    if [ $? -ne 0 ]; then
        echo "ERROR: SSH connection failed."
        exit 1
    else
        echo ""
    fi
}

# reportがダウンロードできたか確認
check_report() {
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to copy directory."
    else
        echo "INFO: Succeed to copy directory."
    fi
}

# SCPコマンド実行関数
download_log() {
    local host=$1
    local log_dir=$2
    local local_dir=$3

    echo "INFO: Downloading logs. Please wait for a while..."
    expect -c "
        set timeout -1
        spawn scp -r -o Compression=yes -o Ciphers=aes256-ctr \"$id@$host:$log_dir\" \"$local_dir\"
        expect {
            \"Are you sure you want to continue connecting (yes/no)?\" {
                send \"yes\n\"
                expect \"Password:\"
                send \"${pass}\n\"
            }
            \"Password:\" {
                send \"${pass}\n\"
            }
        }
        expect {
            \"No such file or directory\" {
                send_user \"ERROR: Remote directory does not exist. Please install LogTool.\n\"
            }
            \"ETA*\" {
                exp_continue
            }
            eof {
                send_user \"INFO: Success to download logs.\n\"
            }
        }
    "
}

# logcatを取得
get_logcat() {
    local host=$1
    auto_ssh "$host"
    download_log "$host" "$LOGCAT_DIR" "$local_dir"
}

# new-loggerを取得
get_logger() {
    local host=$1
    auto_ssh "$host"
    download_log "$host" "$LOGGER_DIR" "$local_dir"
}

# test-diagnosisを取得
get_test() {
    local host=$1
    local local_dir=$2
    echo "INFO: Generating report. Please wait for a while..."
    TAR_NAME=""
    expect -c "
    log_user 1
    set timeout -1
    spawn ssh ${id}@${host} \"test-diagnostic\"
    expect {
        \"Are you sure you want to continue connecting (yes/no)?\" {
            send \"yes\n\"
            expect \"Password:\"
            send \"${pass}\n\"
        }
        \"Password:\" {
            send \"${pass}\n\"
        }
    }
    expect {
    \"*\\$ \" { send \"exit\n\" }
    }
    " | while IFS= read -r line; do
        # 不要な行をスキップ
        if [[ "$line" == *"cp"* && "$line" == *"Permission denied"* ]] || [[ "$line" == *"/dev"* ]]; then
            continue
        fi
        echo "$line"  # 実行結果を逐次出力

        # TAR_NAME の抽出
        if [[ "$line" =~ /home/test/diagnosis/test-diagnosis_[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{2}-[0-9]{2}\.tar\.xz ]]; then
            TAR_NAME="${BASH_REMATCH[0]}"
        fi
        echo "$TAR_NAME" > /tmp/tar_name_output
    done
    TAR_NAME=$(cat /tmp/tar_name_output)
    rm -f /tmp/tar_name_output
    # "| grep -o '/home/test/diagnosis/test-diagnosis_[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}_[0-9]\{2\}-[0-9]\{2\}\.tar\.xz')

    if [ -z "$TAR_NAME" ]; then
        echo "ERROR: Failed to find the tar file."
        exit 1
    fi
    # SCPコマンドを実行してファイルをダウンロード
    echo "INFO: Downloading report. Please wait for a while..."
    expect -c "
        set timeout -1
        spawn scp -r \"$id@$host:$TAR_NAME\" \"$local_dir\"
        expect {
            \"Are you sure you want to continue connecting (yes/no)?\" {
                send \"yes\n\"
                expect \"Password:\"
                send \"${pass}\n\"
            }
            \"Password:\" {
                send \"${pass}\n\"
            }
        }
        expect {
        \"ETA\" {
            exp_continue
        }
        \"*\\$ \" { send \"exit\n\" }
    }
    "
    check_report
}

# ZIPファイルを解凍
unzip() {
    local local_path="$1"
    local zip_name="$2"

    zip_name="${zip_name:20}"

    if [[ "$zip_name" == *.tar.xz ]]; then
        tar_name="${zip_name%.tar.xz}"
    else
        tar_name="$zip_name"
    fi

    TAR_PATH="$local_path/$zip_name"

    if [[ -f "$TAR_PATH" ]]; then
        unzip_dir="$local_path/$tar_name"
        mkdir -p "$unzip_dir"

        tar -xf "$TAR_PATH" -C "$unzip_dir"
        if [[ $? -eq 0 ]]; then
            echo "INFO: Succeed to unzip."
            rm "$TAR_PATH"
            echo "INFO: Succeed to delete the original file."
        else
            echo "ERROR: Failed to unzip the file."
        fi
    else
        echo "ERROR: ZIP file does not exist."
    fi
}


# デスクトップにフォルダを作成
make_folder() {
    local host=$1
    local desktop_path="$HOME/Desktop"
    local folder_name="Log_$(date +'%Y-%m-%d_%H-%M-%S')_Robot$host"
    local local_dir="$desktop_path/$folder_name"
    mkdir "$local_dir" && echo "$local_dir" || { echo "ERROR: Failed to create directory."; exit 1; }
}


# 実行文
if [ $# -lt 1 ]; then
    echo "ERROR: Invalid arguments. Please enter IP address."
    exit 1
fi

for HOSTNAME in "$@"; do
    auto_ssh "$HOSTNAME"
    echo "INFO: Start to get logs from $HOSTNAME"
    local_dir=$(make_folder "$HOSTNAME")

    #get_logcat "$HOSTNAME" "$local_dir"
    #get_logger "$HOSTNAME" "$local_dir"
    get_test "$HOSTNAME" "$local_dir"
    #unzip "$local_dir" "$TAR_NAME"
done

echo "INFO: Finished the script!"
