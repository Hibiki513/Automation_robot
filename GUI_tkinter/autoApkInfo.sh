#!/bin/bash

# 定数としてユーザー名とパスワードを設定
id="test"
pass="test"

# adb確認
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
            send_user \"ERROR: Please check IP address and network.\"
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
        echo $output
        exit 1
    elif [[ "$output" != *"LPT"* ]]; then
        echo "ERROR: Please activate ADB."
        exit 1
    fi
}

execute_command() {
    local host=$1
    local command=$2

    expect -c "
    set timeout -1
    spawn ssh ${id}@${host} \"${command}\"
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
    expect \"*\\$ \" { send \"exit\n\" }
    "
}

get_package_name() {
    local host=$1
    local pattern=$2  # grepのパターンを引数として追加
    echo "INFO: Start collecting packages."

    local command="adb shell pm list packages"
    packages=$(execute_command "$host" "$command" | grep -E "com\.test\..*" | sed 's/package://')

    echo "\nPackages:\n$packages"
}
get_activity_name() {
    local host=$1
    local pattern=$2  # grepのパターンを引数として追加
    while true; do
        echo "Please enter the package name:"
        read apk_input
        echo $apk_input
        local command="adb shell dumpsys package ${apk_input}"
        apk_info=$(execute_command "$host" "$command")

        pattern="com\.test\..*\/.*\..*Activity"
        for line in $apk_info; do
            if ! echo "$line" | grep -q "Database"; then
                if [[ "$line" =~ $pattern ]]; then
                    package_name=$(echo "$line" | cut -d'/' -f1)
                    activity_name=$(echo "$line" | cut -d'/' -f2)
                    echo "\n*****\nPackage name: ${package_name}\nActivity name: ${activity_name}\n*****\n"
                    found=true
                    break
                fi
            else
                break
            fi
        done

        if [ "$found" = true ]; then
            break
        else
            echo "ERROR: No matching activity found."
        fi
    done
}


# 実行文

if [ $# -lt 1 ]; then
    echo "ERROR: Invalid arguments. Please enter IP address."
    exit 1
fi

host=$1

adb_check "$host"
get_package_name "$host"
get_activity_name "$host"
echo "INFO: Finished the script!"
