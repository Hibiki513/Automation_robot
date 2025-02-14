#!/bin/sh

# 定数の定義
id="test"
pass="test"
remote_dir="/home/test"
apk_dir=".local/share/PackageManager/apps/boot-config/html/"

apkArray=()
pkgArray=()

host=$1
shift 1
files=("$@")

for filepath in "${files[@]}"; do
    case "${filepath##*.}" in
        apk) apkArray+=("$filepath") ;;
        pkg) pkgArray+=("$filepath") ;;
    esac
done

# SSH コマンド実行用関数
auto_ssh() {
    local host=$1
    local command=$2

    expect -c "
    set timeout -1
    spawn ssh ${id}@${host} ${command}
    expect {
        \"Are you sure you want to continue connecting\" {
            send \"yes\n\"
            exp_continue
        }
        \"Password:\" {
            send \"${pass}\n\"
        }
    }
    expect eof
    " 2>&1
}

get_remote_path() {
    local filepath=$1
    local err_flag=$2
    local adb_flag=$3

    # err_flag=falseまたはpkgファイルの場合、通常のリモートパス
    if [[ "${filepath##*.}" == "pkg" ]]; then
        remote_path="${remote_dir}"
    elif [[ "${filepath##*.}" == "apk" ]]; then
        if [[ "$err_flag" == "false" ]]; then
            remote_path="${remote_dir}/${apk_dir}"
        else
            remote_path="${remote_dir}"
        fi
    fi

    echo $remote_path
}

# ファイル転送用関数
upload_file() {
    local host=$1
    local filepath=$2
    local err_flag=$3
    file=$(basename "$filepath")

    remote_path=$(get_remote_path "$filepath" "$err_flag")

    output=$(expect -c "
        log_user 0
        set timeout -1
        spawn scp $filepath ${id}@${host}:$remote_path
        expect {
            \"Are you sure you want to continue connecting (yes/no)?\" {
                send \"yes\n\"
                exp_continue
            }
            \"Password:\" {
                send \"${pass}\n\"
            }
        }
        expect {
            -re {.*100%.*} {
                send_user \"\$expect_out(0,string)\"
                exp_continue
            }
            -re {.*[0-9]+%.*} {
                exp_continue
            }
            eof {
            }
        }
    ")
    if [[ "$output" == *"100%"* ]]; then
        echo "$output\ntrue"
        echo "INFO: Succed to upload $file"
    else
        echo "$output\nfalse"
        echo "ERROR: Failed to upload $file"
    fi
}

# ファイルアップロード
upload_files() {
    local host=$1
    local err_flag=$2
    local adb_flag=$3
    echo "INFO: Uploading files. Please wait for a while..."

    for filepath in "${pkgArray[@]}" "${apkArray[@]}"; do
        upload_file "$host" "$filepath" "$err_flag" "$adb_flag"
    done
}

install_files() {
    local host=$1
    echo "INFO: Installing files. Please wait for a while..."
    # 各ファイルを処理
    for filepath in "${pkgArray[@]}" "${apkArray[@]}"; do
        filename=$(basename "$filepath")

        if [[ "$filename" == *.pkg ]]; then
            # **PKG のインストール**
            package="${remote_dir}/${filepath#$cwd/installApps/}"
            command="qicli call PackageManager.install $package"
            output=$(auto_ssh "$host" "$command")
        elif [[ "$filename" == *.apk ]]; then
            # **APK インストール処理**
            if [[ "$err_flag" == "false" ]]; then
                # **APK のインストール (ALTabletService)**
                command="qicli call ALTabletService._installApk \"http://198.18.0.1/apps/boot-config/$filename\""
                output=$(auto_ssh "$host" "$command")

                # **ALTabletService が見つからない場合**
                if echo "$output" | grep -q "No matching services"; then
                    echo "ERROR: ALTabletService not found."
                    err_flag=true
                    if [[ "$adb_flag" == "true" ]]; then
                        echo "INFO: Retrying APK upload and install using ADB."
                    else
                        echo "Failure"
                        echo "ERROR: Failed to install $filename"
                        break
                    fi
                fi
            fi

            # **err_flag が true の場合または ALTabletService が見つからない場合は adb でインストール**
            if [[ "$err_flag" == "true" ]] || echo "$output" | grep -q "No matching services found for pattern"; then
                # **ADB インストール処理**
                remote_path=$(get_remote_path "$filename")
                auto_ssh "$host" "scp \"$apk_dir$filename\" \"$remote_path\"" >/dev/null 2>&1
                adb_command="adb install -r $filename"
                output=$(auto_ssh "$host" "$adb_command")
            fi
        fi
        check_version "$host" "$filename" "$output"
    done
}

check_version() {
    local host=$1
    local filename=$2
    local output=$3

    local file=$(basename "$filename")
    local check=""

    if [[ "$filename" == *.apk ]]; then
        local base_name=$(echo "$filename" | rev | cut -d'-' -f2- | rev)
        command="qicli call ALTabletService._getApkVersion $base_name"
    elif [[ "$filename" == *.pkg ]]; then
        local base_name=$(basename "$filename" | rev | cut -d'-' -f2- | rev)
        command="cat .local/share/PackageManager/apps/$base_name/manifest.xml | grep version"
    fi

    check=$(auto_ssh "$host" "$command")
    version=$(echo "$filename" | sed -E 's/.*-([0-9]+\.[0-9]+(\.[0-9]+)?)\.(apk|pkg)/\1/')
    check=$(echo "$check" | sed -n 's/.*"\(.*\)".*/\1/p')
    echo "INFO: Current installed version: $check"

    if [[ "$check" == *"$version"* && "$output" == *"true"* ]]; then
        echo "Success"
        echo "INFO: Succeed to install $file"
    elif [[ "$check" == *"$version"* && "$output" == *"false"* ]]; then
        echo "INFO: $file is already installed."
    elif [[ "$output" == *"Success"* ]]; then
        echo "Success"
        echo "INFO: Succeed to install $file"
    elif [[ "$check" == *"ALTabletService"* ]]; then
        echo "ERROR: Failed to install $file due to no ALTabletService."
    else
        echo "Failure"
        echo "ERROR: Failed to install $file. Please check file."
    fi
}

# クリーンアップ
cleanup() {
    local host=$1
    err_flag=$2

    for filepath in "${pkgArray[@]}" "${apkArray[@]}"; do
        filename=$(basename "$filepath")
        remote_path=$(get_remote_path "$filename" "$err_flag")
        auto_ssh "$host" "rm -f $remote_path/$filename" >/dev/null 2>&1

        echo "INFO: Cleaned up $filename"
    done
}

adb_check() {
    local host=$1
    output=$(expect -c "
    set timeout 15
    log_user 0
    spawn ssh ${id}@${host} \"adb devices\"
    expect {
        \"Are you sure you want to continue connecting\" {
            send \"yes\n\"
            expect \"Password:\"
            send \"${pass}\n\"
        }
        \"Password:\" {
            send \"${pass}\n\"
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
    expect {
        \"*devices*\" {
            puts \"LPT\"
        }
        eof
    }
    ")

    if [[ "$output" == *"ERROR"* ]]; then
        echo "$output"
        exit 1
    elif [[ "$output" != *"LPT"* ]]; then
        echo "INFO: ADB is disabled."
        adb_flag=false
    elif [[ "$output" == *"LPT"* ]]; then
        echo "INFO: ADB is enabled."
        adb_flag=true
    fi
}

# 実行部分
err_flag=false  # default
adb_check "$host"
echo "INFO: Start to install files to $host"
upload_files "$host" "$err_flag"
install_files "$host" "$adb_flag"
cleanup "$host" "$err_flag"

echo "INFO: Finished the scripts!"
