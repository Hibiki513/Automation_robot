import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext


process = None
selected_files = []
cancel_flag = threading.Event()


def output_to_right_frame():
    global process

    get_valid_ips()
    # 外部スクリプト実行中はIP追加・保存ボタンを無効化、キャンセルボタンを有効化
    add_button.config(state=tk.DISABLED)
    submit_button.config(state=tk.DISABLED)
    cancel_button.config(state=tk.NORMAL)
    disable_ip_fields()
    # 外部スクリプトをバックグラウンドで実行
    threading.Thread(target=run_external_script, daemon=True).start()
    root.focus()


def get_valid_ips():
    # entry_widgets から有効なIPアドレスを取得
    ips = [widget.get().strip() for widget in entry_widgets if widget.get().strip()]
    if not ips:
        pass
    return ips


def disable_ip_fields():
    for entry in entry_widgets:
        entry.config(state=tk.DISABLED)


def enable_ip_fields():
    for entry in entry_widgets:
        entry.config(state=tk.NORMAL)


def disable_radio_buttons():
    radio1.config(state=tk.DISABLED)
    radio2.config(state=tk.DISABLED)
    radio3.config(state=tk.DISABLED)


def enable_radio_buttons():
    radio1.config(state=tk.NORMAL)
    radio2.config(state=tk.NORMAL)
    radio3.config(state=tk.NORMAL)


def stream_output(proc, stream, is_error):
    while True:
        output_line = stream.readline()
        # 空行でない場合のみ処理
        if output_line.strip():
            root.after(0, lambda line=output_line: (
                output.config(state=tk.NORMAL),
                output.insert(tk.END, line),
                output.config(state=tk.DISABLED),
                output.yview(tk.END)  # 自動でスクロール
            ))
            if "Please enter the package name:" in output_line:
                root.after(0, lambda: enable_apk_input())
                root.update()  # GUIを更新して入力を可能にする

        # プロセスが終了したらループを抜ける
        if output_line == '' and proc.poll() is not None:
            break
    root.after(0, lambda: handle_finally())


def handle_finally():
    # process終了後のfinally処理
    enable_ip_fields()
    enable_radio_buttons()
    clear_input()
    reset_widgets()
    disable_apk_input()


def enable_apk_input():
    apk_input_label.config(state=tk.NORMAL)
    apk_input_entry.config(state=tk.NORMAL)
    # **イベントバインド**
    apk_input_entry.bind("<KeyRelease>", check_apk_input)
    apk_input_entry.bind("<Return>", lambda event: submit_apk_input())
    apk_submit_button.config(command=submit_apk_input)


def check_apk_input(event=None):
    apk_input = apk_input_entry.get().strip()
    if apk_input:
        apk_submit_button.config(state=tk.NORMAL)
    else:
        apk_submit_button.config(state=tk.DISABLED)


def disable_apk_input():
    # apk_input_label.config(state=tk.DISABLED)
    apk_input_entry.config(state=tk.DISABLED)
    apk_submit_button.config(state=tk.DISABLED)


def run_external_script():
    global process
    global selected_files

    def run_process():
        global process
        cancel_flag.clear()
        # 選択されたオプションに基づくスクリプト名を決定
        script_map = {
            "Option 1": "autoGetLog.sh",
            "Option 2": "autoApkInfo.sh",
            "Option 3": "autoInstall.sh"
        }
        selected_option = radio_var.get()
        script_name = script_map.get(selected_option, "autoGetLog.sh")  # default
        disable_radio_buttons()
        ips = get_valid_ips()
        try:
            for ip in ips:
                args = ['sh', script_name, ip]
                if selected_option == "Option 3":
                    args.extend(selected_files)
                # サブプロセスを実行
                process = subprocess.Popen(
                    args,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                # スレッドで標準出力を逐次読み込む
                stdout_thread = threading.Thread(target=stream_output, args=(process, process.stdout, False), daemon=True)
                stdout_thread.start()
                # スレッドで標準エラーを逐次読み込む
                stderr_thread = threading.Thread(target=stream_output, args=(process, process.stderr, True), daemon=True)
                stderr_thread.start()
                # 全てのスレッドが終了するまで待機
                process.wait()
                stdout_thread.join()
                stderr_thread.join()
        except Exception as e:
            exception_msg = f"Exception: {str(e)}\n"
            root.after(0, lambda: output.insert(tk.END, exception_msg))
        finally:
            process = None
            root.after(0, lambda: handle_finally())

    # プロセスを非同期に実行
    threading.Thread(target=run_process, daemon=True).start()


def clear_input():
    for entry in entry_widgets:
        entry.delete(0, tk.END)
    apk_input_entry.config(state=tk.NORMAL)
    apk_input_entry.delete(0, tk.END)
    file_label.config(text="No file selected")


def add_ip():
    base_row = len(label_widgets) + len(entry_widgets)
    row = base_row

    if len(entry_widgets) < 5:
        label_text = f"Robot IP address {len(label_widgets) + 1}:"
        label = tk.Label(upper_left_frame, text=label_text)
        entry = tk.Entry(upper_left_frame)
        label.grid(row=row, column=0, padx=10, pady=0, sticky='ew')
        entry.grid(row=row, column=1, padx=0, pady=5, sticky='ew')
        label_widgets.append(label)
        entry_widgets.append(entry)
        entry.bind("<KeyRelease>", update_check_value)

        # ボタンやファイルフレームを再配置
        button_position()
        # ファイル選択フレームを再配置
        update_check_value()

    if len(entry_widgets) == 5:
        add_button.config(state=tk.DISABLED)


def delete_ip(start_index, end_index):
    global entry_widgets, label_widgets

    if radio_var.get() == "Option 2":
        # 指定範囲のウィジェットを削除
        for i in range(start_index, end_index + 1):
            label_widgets[i].destroy()
            entry_widgets[i].destroy()

        # ウィジェットリストを更新
        label_widgets = label_widgets[:start_index] + label_widgets[end_index + 1:]
        entry_widgets = entry_widgets[:start_index] + entry_widgets[end_index + 1:]

        # 他のUIの状態を更新
        update_add_button_state()
        update_submit_button_state()


def button_position():
    # ボタンの再配置
    base_row = len(label_widgets) + len(entry_widgets)
    row = base_row
    add_button.grid(row=row + 1, column=0, columnspan=2, pady=10, sticky='e')
    submit_button.grid(row=row + 1, column=0, columnspan=2, pady=10, sticky='')
    cancel_button.grid(row=row + 1, column=0, columnspan=2, pady=10, sticky='w')


def cancel_script():
    global process
    if process:
        confirm = messagebox.askyesno("確認", "キャンセルしますか？")
        if confirm:
            cancel_flag.set()
            process.terminate()
            process = None
            root.after(0, lambda: (
                output.config(state=tk.NORMAL),  # 出力を有効化
                output.insert(tk.END, "ERROR: Process cancelled.\n"),  # メッセージを挿入
                output.config(state=tk.DISABLED),  # 再び出力を無効化
                output.yview(tk.END)  # 自動スクロール
            ))
            cancel_button.config(state=tk.DISABLED)
            handle_finally()


def clear_output():
    output.config(state=tk.NORMAL)
    output.delete(1.0, tk.END)
    output.config(state=tk.DISABLED)


def submit_apk_input():
    apk_submit_button.config(state=tk.DISABLED)
    apk_input_entry.config(state=tk.DISABLED)
    apk_input = apk_input_entry.get().strip()
    output.insert(tk.END, apk_input + '\n')
    process.stdin.write(apk_input + '\n')
    process.stdin.flush()


def select_file():
    global selected_files
    selected_files = filedialog.askopenfilenames(
        filetypes=[("", "*.apk *.pkg")]
    )
    selected_files = list(selected_files)
    if selected_files:
        max_length = 40  # 表示文字数の最大値
        file_names = []
        for file_path in selected_files:
            if len(file_path) > max_length:
                file_name = f"...{file_path[-(max_length - 3):]}"
            else:
                file_name = file_path
            file_names.append(file_name)
        # ラベルに複数ファイルを改行で表示
        file_label.config(text="\n".join(file_names))


def reset_file_selection(selected_option):
    if selected_option in ["Option 1", "Option 2"]:
        file_label.config(text="No file selected")
        file_button.config(state=tk.DISABLED)


# エントリウィジェットのリセット用関数
def reset_widgets():
    # すべてのラベルとエントリを非表示に
    for widget in label_widgets + entry_widgets:
        widget.grid_forget()
    # 最初のラベルとエントリだけ表示
    if label_widgets and entry_widgets:
        label_widgets[0].grid(row=1, column=0, padx=10, pady=0, sticky='ew')
        entry_widgets[0].grid(row=1, column=1, padx=0, pady=5, sticky='ew')


def update_submit_button_state():
    ip = entry_widgets[0].get().strip()
    selected_option = radio_var.get()
    if ip:
        if selected_option == "Option 3":
            if file_label.cget("text") != "No file selected":
                submit_button.config(state=tk.NORMAL)
        else:
            submit_button.config(state=tk.NORMAL)
    else:
        submit_button.config(state=tk.DISABLED)
        if selected_option == "Option 3":
            if file_label.cget("text") != "No file selected":
                submit_button.config(state=tk.NORMAL)


def update_add_button_state():
    if radio_var.get() == "Option 2":
        add_button.config(state=tk.DISABLED)
    else:
        if len(entry_widgets) == 5:
            add_button.config(state=tk.DISABLED)
        else:
            add_button.config(state=tk.NORMAL)


def update_file_selection_button():
    selected_option = radio_var.get()
    if selected_option == "Option 3":
        file_button.config(state=tk.NORMAL)
    else:
        file_button.config(state=tk.DISABLED)


def update_check_value(*args):
    selected_option = radio_var.get()
    reset_file_selection(selected_option)
    update_submit_button_state()
    update_add_button_state()
    update_file_selection_button()
    # ファイル選択の状態に応じてfile_frameの表示
    file_frame.grid(row=len(label_widgets) + len(entry_widgets) + 6, column=0, columnspan=2, pady=5, padx=5, sticky='ew')
    delete_ip(1, len(entry_widgets) - 1)


def update_apk_input_button(*args):
    if apk_input_entry.get().strip():
        apk_submit_button.config(state=tk.NORMAL)
    else:
        apk_submit_button.config(state=tk.DISABLED)


def close_dialog():
    if messagebox.askokcancel("Quit", "ウィンドウを閉じてもよろしいですか？"):
        root.destroy()


# メインウィンドウ設定
root = tk.Tk()
root.title("AutoCmdExecutor")
root.geometry("850x600")
root.resizable(False, False)
root.protocol("WM_DELETE_WINDOW", close_dialog)

# レイアウト設定
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)

# 左フレームのレイアウト
left_frame = tk.Frame(root)
left_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
left_frame.grid_rowconfigure(0, weight=1, minsize=300)  # upper_left_frame
left_frame.grid_rowconfigure(1, weight=1, minsize=300)  # lower_left_frame
left_frame.grid_columnconfigure(0, weight=1)
# 左上半分のフレーム
upper_left_frame = tk.Frame(left_frame)
upper_left_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
upper_left_frame.grid_columnconfigure(0, weight=1)
upper_left_frame.grid_columnconfigure(1, weight=1)

# ラジオボタン
radio_frame = tk.Frame(upper_left_frame)
radio_frame.grid(row=0, column=0, columnspan=2, pady=10, padx=5, sticky='w')

radio_var = tk.StringVar(value="Option 1")  # デフォルト値
radio1 = tk.Radiobutton(radio_frame, text="getLog", variable=radio_var, value="Option 1", command=update_check_value)
radio2 = tk.Radiobutton(radio_frame, text="apkInfo", variable=radio_var, value="Option 2",
                        command=update_check_value)
radio3=tk.Radiobutton(radio_frame, text="apkInstall", variable=radio_var, value="Option 3",
                        command=update_check_value)
radio1.grid(row=0, column=0, padx=5, sticky='w')
radio2.grid(row=0, column=1, padx=5, sticky='w')
radio3.grid(row=0, column=2, padx=5, sticky='w')

# ipアドレス入力欄
label_widgets = []
entry_widgets = []

label = tk.Label(upper_left_frame, text="Robot IP address 1:")
entry = tk.Entry(upper_left_frame)
label.grid(row=1, column=0, padx=10, pady=0, sticky='ew')
entry.grid(row=1, column=1, padx=0, pady=5, sticky='ew')
label_widgets.append(label)
entry_widgets.append(entry)
entry.bind("<KeyRelease>", update_check_value)

add_button = tk.Button(upper_left_frame, text='+Add IP', width=10, command=add_ip)
submit_button = tk.Button(upper_left_frame, text='Submit', width=10, command=output_to_right_frame, state=tk.DISABLED)
cancel_button = tk.Button(upper_left_frame, text='Cancel', width=10, command=cancel_script, state=tk.DISABLED)
add_button.grid(row=len(entry_widgets) + 1, column=0, columnspan=2, pady=10, sticky='e')
submit_button.grid(row=len(entry_widgets) + 1, column=0, columnspan=2, pady=10, sticky='')
cancel_button.grid(row=len(entry_widgets) + 1, column=0, columnspan=2, pady=10, sticky='w')

# 左下半分のフレーム
lower_left_frame = tk.Frame(left_frame)
lower_left_frame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)

# APK関連ウィジェット
apk_input_label = tk.Label(lower_left_frame, text="Package name", state=tk.DISABLED)
apk_input_entry = tk.Entry(lower_left_frame, state=tk.DISABLED)
apk_submit_button = tk.Button(lower_left_frame, text='Submit Package', width=10, command=submit_apk_input,
                              state=tk.DISABLED)
apk_input_label.grid(row=len(entry_widgets) + 4, column=0, pady=10, padx=0, sticky='ew')
apk_input_entry.grid(row=len(entry_widgets) + 4, column=1, pady=0, padx=5, sticky='ew')
# apk_input_entry.bind("<KeyRelease>", lambda event: update_apk_input_button())
apk_submit_button.grid(row=len(entry_widgets) + 5, column=0, columnspan=2, pady=10, sticky='e')

# ファイル選択
file_frame = tk.Frame(lower_left_frame)
file_frame.grid(row=len(entry_widgets) + 6, column=0, columnspan=2, pady=2, padx=2, sticky='ew')
file_button = tk.Button(file_frame, text='Select file', width=10, command=select_file, state=tk.DISABLED)
file_label = tk.Label(file_frame, text='No file selected', width=30, anchor='w')
file_button.grid(row=0, column=0, padx=5, pady=5, sticky='n')
file_label.grid(row=0, column=1, padx=8, pady=8, sticky='n')
# 中央寄席のためcolumnの重さを設定
file_frame.columnconfigure(0, weight=1)
file_frame.columnconfigure(1, weight=1)
# 初期状態でファイル選択フレームを表示するが、ボタンは非活性
file_frame.grid(row=len(entry_widgets) + 6, column=0, columnspan=2, pady=5, padx=5, sticky='ew')

# 右フレームのレイアウト
right_frame = tk.Frame(root)
right_frame.grid(row=0, column=1, padx=10, pady=10, sticky='nsew')
right_frame.grid_rowconfigure(0, weight=1)
right_frame.grid_columnconfigure(0, weight=1)

# ouputエリア・clear ouptut/inputボタン
output = scrolledtext.ScrolledText(right_frame, width=50, height=60)
output.grid(row=0, column=0, sticky='nsew')
output.config(state=tk.DISABLED)
clear_output_button = tk.Button(right_frame, text='Clear Output', command=clear_output)
clear_input_button = tk.Button(right_frame, text='Clear Input', command=clear_input)
clear_output_button.grid(row=1, column=0, pady=10, sticky='e')
clear_input_button.grid(row=1, column=0, pady=10, sticky='w')

root.mainloop()

