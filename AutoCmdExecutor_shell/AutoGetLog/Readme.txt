【AutoGetLog】

[概要]
	pepperからlogcat, new-logger, naoの３つのログをPCにコピーして取得するためのツールです。
	Desktopに「Log_yyyy-mm-dd_hh-mm-ss_Robot10.52.xx.xxx」というフォルダーを作成し、その中に３つの各ログを取得します。

	このツールは複数機体のログを一括で取得することができます。１台のみの使用もできます。
	複数機体のログを取得する場合は、ロボットごとにフォルダが作成されます。

	※このスクリプトではデスクトップフォルダが'$HOME/Desktop'にあることを前提としています。
	 これは多くのLinux系システムで標準的ですが、異なるデスクトップ環境や言語設定によっては、デスクトップの名前が"Desktop"ではない場合があります。
	 その場合は、スクリプトの'desktop_path'の設定を適宜変更してください。
	 必要に応じて、以下のようにデスクトップのパスを動的に取得することもできます。
	     desktop_path=$(xdg-user-dir DESKTOP)


	取得するログを限定したい場合は、以下の実行文を編集することで変更できます。
	デフォルトは①と③のみ実行します。
	①logcatを取得する：get_logcat
	②new-loggerを取得する：get_logger
	③naoqiログを取得する：get_nao
	必要に応じて、取得したくないログは、下記のget_loggerの様に、半角「#」を先頭につけ、コメントアウトしてください。
	====================================================================================
	# 実行文
	if [ $# -lt 1 ]; then
    	    echo "ERROR: Invalid arguments. Please enter at least one IP address."
    	    exit 1
	fi

	for HOSTNAME in "$@"; do
            echo "INFO: Start to get logs from $HOSTNAME"
    	    local_dir=$(make_folder "$HOSTNAME")

    	    get_logcat "$HOSTNAME" "$local_dir"
	    # get_logger "$HOSTNAME" "$local_dir"
    	    get_nao "$HOSTNAME" "$local_dir"
	done

	echo "Finished the script!"
	======================================================================================



[ディレクトリ構成]
	autoGetLog.sh
	Readme.txt

[前提条件]
	・接続するpepperのIPまたは名称がわかっていること
	・pepperと同じネットワークを使用していること
	・使用するネットワークが安定していること(ツール実行中に切断されないこと)
	・LogToolがpepperにインストール済みであること
	※これらの前提条件が整っており、正しい<実行方法>であれば、実行する現在位置には依存せずツールを実行できます。

<実行方法>
	sh [autoGetLog.shまでのパス] [IPまたは名称.local]
	<例>
	sh Desktop/AutoGetLog/autoGetLog.sh 10.52.xx.xxx


	複数台同時にログを取得する場合は、以下のように、IPアドレスをスペース区切りで追加してください。
	sh [autoGetLog.shまでのパス] [IPまたは名称.local] [IPまたは名称.local]
	<例>
	sh Desktop/AutoGetLog/autoGetLog.sh 10.52.xx.xxx 10.52.xx.xxx

[注意点]

	過去に使用したことのあるI.Pの場合以下のWARNINGが発生し、ツールを実行できなくなる場合があります。
	@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
	@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @
	@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
	IT IS POSSIBLE THAT SOMEONE IS DOING SOMETHING NASTY!
	Someone could be eavesdropping on you right now (man-in-the-middle attack)!
	It is also possible that a host key has just been changed.
	The fingerprint for the RSA key sent by the remote host is
	0b:1d:3b:5e:b8:ba:ad:07:b5:71:7a:16:32:91:8d:2d.
	Please contact your system administrator.
	Add correct host key in /Users/noguchiwataru/.ssh/known_hosts to get rid of this message.
	Offending RSA key in /Users/noguchiwataru/.ssh/known_hosts:14
	RSA host key for 192.168.0.114 has changed and you have requested strict checking.
	Host key verification failed.

	その場合、以下のコマンドを実行し、再度ツールを実行してください。
	rm ~/.ssh/known_hosts

	==========================================================================================

	ツール実行時に、以下のメッセージが表示される場合があります。

	The authenticity of host '169.254.239.121 (169.254.239.121)' can't be established.
	ED25519 key fingerprint is SHA256:dOU/SvjU5K4i+0rUViz4ffnWxv9hJ9YogOg4Y68nWxU.
	This key is not known by any other names.

	その場合、一度マニュアルでssh接続・切断をしてから、再度ツールを実行してください。