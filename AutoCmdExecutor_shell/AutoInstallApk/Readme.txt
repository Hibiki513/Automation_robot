【AutoInstallApk】

[概要]
	apkとpkgをインストールするためのツールです。
	<実行方法>のやり方でコマンドを実行することで、転送/インストール/不要になったファイルの削除を行います。

	このツールは複数機体にPKG/APKファイルを一括で転送/インストール/不要になったファイルの削除をすることができます。１台のみの使用もできます。

	ADBなしでapkのインストールを実行できるツールautoInstallerと同じで、ADBが有効かつALTabletServiceエラーが出た場合のみADBコマンドでの再インストールを実行します。

[ディレクトリ構成]
	autoApkInstall.sh
	installApps
	Readme.txt

[前提条件]
	・接続するpepperのIPまたは名称がわかっていること
	・pepperと同じネットワークを使用していること
	・使用するネットワークが安定していること(ツール実行中に切断されないこと)
	・ファイルがPepperにインストール済みでないこと（インストール済みだとエラーが出て失敗します）
	※これらの前提条件が整っており、正しい<実行方法>であれば、実行する現在位置には依存せずツールを実行できます。

<実行方法>
	sh [autoApkInstall.shまでのパス] [IPまたは名称.local]
	<例>
	sh Desktop/AutoInstallApk/autoApkInstall.sh 10.52.xx.xxx

	複数台同時にAPKをインストールする場合は、以下のように、IPアドレスをスペース区切りで追加してください。
	sh [autoApkInstall.shまでのパス] [インストールしたいapkファイルまでのパス] [IPまたは名称.local] [IPまたは名称.local]
	<例>
	sh Desktop/AutoInstallApk/autoApkInstall.sh 10.52.xx.xxx 10.52.xx.xxx

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
