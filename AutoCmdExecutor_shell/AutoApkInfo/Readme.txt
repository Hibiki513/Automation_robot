【AutoApkInfo】

[概要]
	pepperにインストールされているapkのパッケージ名とアクティビティ名を取得するためのツールです。
	対象のapkは「com.softbankrobotics.」から始まるAPKのみです。それ以外には対応していません。

	ツール実行中にapk名の入力を求められます。
	「com.softbankrobotics.」を含む１行全てを入力してください。
	
	
	以下は表示・入力・出力例です。 
	[表示例」
	　　Packages:
	　　com.softbankrobotics.apps.common.ufo
	　　com.softbankrobotics.apps.party
	　　com.softbankrobotics.chatpepper
	[入力例]
	  「Enter the apk name:」と表示されるので、「ufo」のように入力してください。
	   ※chatpepperの場合は「com.softbankrobotics.apps.common.ufo」と入力してください。
	[出力例]
	　　 Package name: com.softbankrobotics.apps.common.ufo
	    Activity name: .activity.MainActivity
	ここで出力されたPackage nameがパッケージ名、Activity nameがアクティビティ名となります。

[ディレクトリ構成]
	autoApkInfo.sh
	Readme.txt

[前提条件]
	・接続するpepperのIPまたは名称がわかっていること
	・pepperと同じネットワークを使用していること
	・使用するネットワークが安定していること(ツール実行中に切断されないこと)
        ・ADBがONであること
	・package名/activity名を調べたいapkがインストール済みであること
	※これらの前提条件が整っており、正しい<実行方法>であれば、実行する現在位置には依存せずツールを実行できます。

<実行方法>
	sh [autoApkInfo.shまでのパス] [IPまたは名称.local]

	<例>
	sh Desktop/AutoApkInfo/autoApkInfo.sh 10.52.xx.xxx

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
