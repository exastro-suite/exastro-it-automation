-- ------------------------------------------------------------
-- T_ANSC_LOGIN_AUTH_TYPE: UPDATE
-- ------------------------------------------------------------
-- - 証明書認証(winrm)を追加
NSERT INTO T_ANSC_LOGIN_AUTH_TYPE (LOGIN_AUTH_TYPE_ID,LOGIN_AUTH_TYPE_NAME_JA,LOGIN_AUTH_TYPE_NAME_EN,DISP_SEQ,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('6','証明書認証(winrm)','Certificate authentication (winrm)',6,NULL,'0',_____DATE_____,1);

-- ------------------------------------------------------------
-- T_COMN_MENU_COLUMN_LINK: UPDATE
-- ------------------------------------------------------------
-- - T_ANSC_DEVICE: COLUMN UPDATE
-- - サーバー証明書:WINRM_SSL_CA_FILEを削除
-- - winrm公開鍵ファイル:WINRM_CERT_PEM_FILEを追加
-- - winrm秘密鍵ファイル:WINRM_CERT_KEY_PEM_FILEを追加
DELETE FROM T_COMN_MENU_COLUMN_LINK WHERE COLUMN_DEFINITION_ID in ('2010112',
                                                                   '2010113',
                                                                   '2010114',
                                                                   '2010115',
                                                                   '2010116',
                                                                   '2010117',
                                                                   '2010118',
                                                                   '2010119',
                                                                   '2010120',
                                                                   '2010121',
                                                                   '2010122',
                                                                   '2010123');
DELETE FROM T_COMN_MENU_COLUMN_LINK_JNL WHERE COLUMN_DEFINITION_ID in ("2010112",
                                                                       '2010113',
                                                                       '2010114',
                                                                       '2010115',
                                                                       '2010116',
                                                                       '2010117',
                                                                       '2010118',
                                                                       '2010119',
                                                                       '2010120',
                                                                       '2010121',
                                                                       '2010122',
                                                                       '2010123');

INSERT INTO T_COMN_MENU_COLUMN_LINK (COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('2010112','20101','winrm公開鍵ファイル','winrm public key file','winrm_public_key_file','2010105','20',120,NULL,NULL,NULL,NULL,'0',NULL,NULL,NULL,NULL,'WINRM_CERT_PEM_FILE',NULL,'0','1','1','0','0','1','0',NULL,'{
"upload_max_size": 104857600
}',NULL,NULL,NULL,'WindowsServerに証明書認証でWinRM接続する場合の公開鍵ファイル「ansible_winrm_cert_pem」を入力します。
Pythonのバージョンが2.7以降で証明書の検証を行わない場合、インベントリファイル追加オプションに下記のパラメータを入力して下さい。
    ansible_winrm_server_cert_validation: ignore','Enter the public key file "ansible_winrm_cert_pem" when connecting to Windows Server with WinRM using certificate authentication.
If the Python version is 2.7 or later and certificate verification is not performed, enter the following parameters in the inventory file addition option.

    ansible_winrm_server_cert_validation=ignore',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK_JNL (JOURNAL_SEQ_NO,JOURNAL_REG_DATETIME,JOURNAL_ACTION_CLASS,COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES(2010112,_____DATE_____,'INSERT','2010112','20101','winrm公開鍵ファイル','winrm public key file','winrm_public_key_file','2010105','20',120,NULL,NULL,NULL,NULL,'0',NULL,NULL,NULL,NULL,'WINRM_CERT_PEM_FILE',NULL,'0','1','1','0','0','1','0',NULL,'{
"upload_max_size": 104857600
}',NULL,NULL,NULL,'WindowsServerに証明書認証でWinRM接続する場合の公開鍵ファイル「ansible_winrm_cert_pem」を入力します。
Pythonのバージョンが2.7以降で証明書の検証を行わない場合、インベントリファイル追加オプションに下記のパラメータを入力して下さい。
    ansible_winrm_server_cert_validation: ignore','Enter the public key file "ansible_winrm_cert_pem" when connecting to Windows Server with WinRM using certificate authentication.
If the Python version is 2.7 or later and certificate verification is not performed, enter the following parameters in the inventory file addition option.

    ansible_winrm_server_cert_validation=ignore',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK (COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('2010113','20101','winrm秘密鍵ファイル','winrm private key file','winrm_private_key_file','2010105','20',130,NULL,NULL,NULL,NULL,'0',NULL,NULL,NULL,NULL,'WINRM_CERT_KEY_PEM_FILE',NULL,'0','1','1','0','0','1','0',NULL,'{
"upload_max_size": 104857600
}',NULL,NULL,NULL,'WindowsServerに証明書認証でWinRM接続する場合の秘密鍵ファイル「ansible_winrm_cert_key_pem」を入力します。
Pythonのバージョンが2.7以降で証明書の検証を行わない場合、インベントリファイル追加オプションに下記のパラメータを入力して下さい。
    ansible_winrm_server_cert_validation: ignore','Enter the private key file "ansible_winrm_cert_key_pem" when connecting WinRM to Windows Server using certificate authentication.
If the Python version is 2.7 or later and certificate verification is not performed, enter the following parameters in the inventory file addition option.

    ansible_winrm_server_cert_validation=ignore',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK_JNL (JOURNAL_SEQ_NO,JOURNAL_REG_DATETIME,JOURNAL_ACTION_CLASS,COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES(2010113,_____DATE_____,'INSERT','2010113','20101','winrm秘密鍵ファイル','winrm private key file','winrm_private_key_file','2010105','20',130,NULL,NULL,NULL,NULL,'0',NULL,NULL,NULL,NULL,'WINRM_CERT_KEY_PEM_FILE',NULL,'0','1','1','0','0','1','0',NULL,'{
"upload_max_size": 104857600
}',NULL,NULL,NULL,'WindowsServerに証明書認証でWinRM接続する場合の秘密鍵ファイル「ansible_winrm_cert_key_pem」を入力します。
Pythonのバージョンが2.7以降で証明書の検証を行わない場合、インベントリファイル追加オプションに下記のパラメータを入力して下さい。
    ansible_winrm_server_cert_validation: ignore','Enter the private key file "ansible_winrm_cert_key_pem" when connecting WinRM to Windows Server using certificate authentication.
If the Python version is 2.7 or later and certificate verification is not performed, enter the following parameters in the inventory file addition option.

    ansible_winrm_server_cert_validation=ignore',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK (COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('2010114','20101','プロトコル','Protocol','protocol','2010106','7',140,'T_ANSC_PIONEER_PROTOCOL_TYPE','PROTOCOL_ID','PROTOCOL_NAME',NULL,'0',NULL,NULL,NULL,NULL,'PROTOCOL_ID',NULL,'0','1','1','0','0','1','0',NULL,NULL,NULL,NULL,NULL,'Ansible-Pioneerにて機器ログインする際のプロトコルです。','Protocol for device login through Ansible-Pioneer.',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK_JNL (JOURNAL_SEQ_NO,JOURNAL_REG_DATETIME,JOURNAL_ACTION_CLASS,COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES(2010114,_____DATE_____,'INSERT','2010114','20101','プロトコル','Protocol','protocol','2010106','7',140,'T_ANSC_PIONEER_PROTOCOL_TYPE','PROTOCOL_ID','PROTOCOL_NAME',NULL,'0',NULL,NULL,NULL,NULL,'PROTOCOL_ID',NULL,'0','1','1','0','0','1','0',NULL,NULL,NULL,NULL,NULL,'Ansible-Pioneerにて機器ログインする際のプロトコルです。','Protocol for device login through Ansible-Pioneer.',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK (COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('2010115','20101','OS種別','OS type','os_type','2010106','7',150,'T_ANSP_OS_TYPE','OS_TYPE_ID','OS_TYPE_NAME',NULL,'0',NULL,NULL,NULL,NULL,'OS_TYPE_ID',NULL,'0','1','1','0','0','1','0',NULL,NULL,NULL,NULL,NULL,'Ansible-Pioneerにて対象機器のOS種別ごとに対話ファイルを使い分けるために利用します。','Used for different dialog files based on OS type of device in Ansible-Pioneer.',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK_JNL (JOURNAL_SEQ_NO,JOURNAL_REG_DATETIME,JOURNAL_ACTION_CLASS,COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES(2010115,_____DATE_____,'INSERT','2010115','20101','OS種別','OS type','os_type','2010106','7',150,'T_ANSP_OS_TYPE','OS_TYPE_ID','OS_TYPE_NAME',NULL,'0',NULL,NULL,NULL,NULL,'OS_TYPE_ID',NULL,'0','1','1','0','0','1','0',NULL,NULL,NULL,NULL,NULL,'Ansible-Pioneerにて対象機器のOS種別ごとに対話ファイルを使い分けるために利用します。','Used for different dialog files based on OS type of device in Ansible-Pioneer.',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK (COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('2010116','20101','LANG','LANG','lang','2010106','7',160,'T_ANSC_PIONEER_LANG','ID','NAME',NULL,'0',NULL,NULL,NULL,NULL,'PIONEER_LANG_ID',NULL,'0','1','1','0','0','1','0',NULL,NULL,NULL,NULL,NULL,'Pioneerの対話ファイルを実行する際の文字エンコード(LANG)を選択します。 空白の場合はutf-8扱いとなります。','Select the character encoding (LANG) when executing the Pioneer dialog file. If it is blank, it will be treated as utf-8.',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK_JNL (JOURNAL_SEQ_NO,JOURNAL_REG_DATETIME,JOURNAL_ACTION_CLASS,COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES(2010116,_____DATE_____,'INSERT','2010116','20101','LANG','LANG','lang','2010106','7',160,'T_ANSC_PIONEER_LANG','ID','NAME',NULL,'0',NULL,NULL,NULL,NULL,'PIONEER_LANG_ID',NULL,'0','1','1','0','0','1','0',NULL,NULL,NULL,NULL,NULL,'Pioneerの対話ファイルを実行する際の文字エンコード(LANG)を選択します。 空白の場合はutf-8扱いとなります。','Select the character encoding (LANG) when executing the Pioneer dialog file. If it is blank, it will be treated as utf-8.',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK (COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('2010117','20101','接続オプション','Connection options','connection_options','1020201','1',170,NULL,NULL,NULL,NULL,'0',NULL,NULL,NULL,NULL,'SSH_EXTRA_ARGS',NULL,'0','1','1','0','0','1','0',NULL,'{
"min_length": 0,
"max_length": 4000
}',NULL,NULL,NULL,'プロトコルがsshの場合
/etc/ansible/ansible.cfgのssh_argsに設定しているsshオプション以外のオプションを設定したい場合>、設定したいオプションを入力します。
(例)
    sshコンフィグファイルを指定する場合
      -F /root/.ssh/ssh_config

プロトコルがtelnetの場合
telnet接続時のオプションを設定したい場合、設定したいオプションを入力します。
(例)
    ポート番号を11123に指定する場合
      11123','When the protocol is ssh
To set options other than the ssh option set in ssh_args in /etc/ansible/ansible.cfg, specify the desired options.
(Example)
    To specify the ssh config file.
      -F /root/.ssh/ssh_config

When the protocol is telnet
To set options for telnet connections, specify the desired options.
(Example)
    To specify 11123 as the port number.
      11123',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK_JNL (JOURNAL_SEQ_NO,JOURNAL_REG_DATETIME,JOURNAL_ACTION_CLASS,COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES(2010117,_____DATE_____,'INSERT','2010117','20101','接続オプション','Connection options','connection_options','1020201','1',170,NULL,NULL,NULL,NULL,'0',NULL,NULL,NULL,NULL,'SSH_EXTRA_ARGS',NULL,'0','1','1','0','0','1','0',NULL,'{
"min_length": 0,
"max_length": 4000
}',NULL,NULL,NULL,'プロトコルがsshの場合
/etc/ansible/ansible.cfgのssh_argsに設定しているsshオプション以外のオプションを設定したい場合>、設定したいオプションを入力します。
(例)
    sshコンフィグファイルを指定する場合
      -F /root/.ssh/ssh_config

プロトコルがtelnetの場合
telnet接続時のオプションを設定したい場合、設定したいオプションを入力します。
(例)
    ポート番号を11123に指定する場合
      11123','When the protocol is ssh
To set options other than the ssh option set in ssh_args in /etc/ansible/ansible.cfg, specify the desired options.
(Example)
    To specify the ssh config file.
      -F /root/.ssh/ssh_config

When the protocol is telnet
To set options for telnet connections, specify the desired options.
(Example)
    To specify 11123 as the port number.
      11123',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK (COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('2010118','20101','インベントリファイル
追加オプション','Inventory file Additional option','inventory_file_additional_option','1020201','2',180,NULL,NULL,NULL,NULL,'0',NULL,NULL,NULL,NULL,'HOSTS_EXTRA_ARGS',NULL,'0','1','1','0','0','1','0',NULL,'{
"min_length": 0,
"max_length": 4000
}',NULL,NULL,NULL,'ITAが設定していないインベントリファイルのオプションパラメータをyaml形式で入力します。
(例)
    ansible_connection: network_cli
    ansible_network_os: nxos','Enter additional options in YAML format to set inventory file options that ITA does not set.
(Example)
    ansible_connection: network_cli
    ansible_network_os: nxos',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK_JNL (JOURNAL_SEQ_NO,JOURNAL_REG_DATETIME,JOURNAL_ACTION_CLASS,COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES(2010118,_____DATE_____,'INSERT','2010118','20101','インベントリファイル
追加オプション','Inventory file Additional option','inventory_file_additional_option','1020201','2',180,NULL,NULL,NULL,NULL,'0',NULL,NULL,NULL,NULL,'HOSTS_EXTRA_ARGS',NULL,'0','1','1','0','0','1','0',NULL,'{
"min_length": 0,
"max_length": 4000
}',NULL,NULL,NULL,'ITAが設定していないインベントリファイルのオプションパラメータをyaml形式で入力します。
(例)
    ansible_connection: network_cli
    ansible_network_os: nxos','Enter additional options in YAML format to set inventory file options that ITA does not set.
(Example)
    ansible_connection: network_cli
    ansible_network_os: nxos',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK (COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('2010119','20101','インスタンスグループ名','Instance group name','instance_group_name','1020204','7',190,'T_ANSC_TWR_INSTANCE_GROUP','INSTANCE_GROUP_NAME','INSTANCE_GROUP_NAME',NULL,'0',NULL,NULL,NULL,NULL,'ANSTWR_INSTANCE_GROUP_NAME',NULL,'0','1','1','0','0','1','0',NULL,NULL,NULL,NULL,NULL,'Ansible Automation Controllerのインベントリに設定するインスタンスグループを指定します。','Specify the instance group to be set as the inventory of Ansible Automation Controller.',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK_JNL (JOURNAL_SEQ_NO,JOURNAL_REG_DATETIME,JOURNAL_ACTION_CLASS,COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES(2010119,_____DATE_____,'INSERT','2010119','20101','インスタンスグループ名','Instance group name','instance_group_name','1020204','7',190,'T_ANSC_TWR_INSTANCE_GROUP','INSTANCE_GROUP_NAME','INSTANCE_GROUP_NAME',NULL,'0',NULL,NULL,NULL,NULL,'ANSTWR_INSTANCE_GROUP_NAME',NULL,'0','1','1','0','0','1','0',NULL,NULL,NULL,NULL,NULL,'Ansible Automation Controllerのインベントリに設定するインスタンスグループを指定します。','Specify the instance group to be set as the inventory of Ansible Automation Controller.',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK (COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('2010120','20101','接続タイプ','Connection type','connection_type','1020204','7',200,'T_ANSC_TWR_CREDENTIAL_TYPE','CREDENTIAL_TYPE_ID','CREDENTIAL_TYPE_NAME',NULL,'0',NULL,NULL,NULL,NULL,'CREDENTIAL_TYPE_ID',NULL,'0','1','1','0','1','1','0','1',NULL,NULL,NULL,NULL,'Ansible Automation Controller認証情報の接続タイプを設定します。通常はmachineを選択します。ansible_connectionをloclaに設定する必要があるネットワーク機器の場合にNetworkを選択します。','Sets the connection type for Ansible Automation Controller credentials. Basically, select machine. Select Network for network devices that require ansible_connection set to locla.',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK_JNL (JOURNAL_SEQ_NO,JOURNAL_REG_DATETIME,JOURNAL_ACTION_CLASS,COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES(2010120,_____DATE_____,'INSERT','2010120','20101','接続タイプ','Connection type','connection_type','1020204','7',200,'T_ANSC_TWR_CREDENTIAL_TYPE','CREDENTIAL_TYPE_ID','CREDENTIAL_TYPE_NAME',NULL,'0',NULL,NULL,NULL,NULL,'CREDENTIAL_TYPE_ID',NULL,'0','1','1','0','1','1','0','1',NULL,NULL,NULL,NULL,'Ansible Automation Controller認証情報の接続タイプを設定します。通常はmachineを選択します。ansible_connectionをloclaに設定する必要があるネットワーク機器の場合にNetworkを選択します。','Sets the connection type for Ansible Automation Controller credentials. Basically, select machine. Select Network for network devices that require ansible_connection set to locla.',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK (COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('2010121','20101','備考','Remarks','remarks',NULL,'12',210,NULL,NULL,NULL,NULL,'0',NULL,NULL,NULL,NULL,'NOTE',NULL,'0','1','1','0','0','1','0',NULL,'{
"min_length": 0,
"max_length": 4000
}',NULL,NULL,NULL,'自由記述欄。レコードの廃止・復活時にも記載可能。','Comments section. Can comment when removing or restoring records.',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK_JNL (JOURNAL_SEQ_NO,JOURNAL_REG_DATETIME,JOURNAL_ACTION_CLASS,COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES(2010121,_____DATE_____,'INSERT','2010121','20101','備考','Remarks','remarks',NULL,'12',210,NULL,NULL,NULL,NULL,'0',NULL,NULL,NULL,NULL,'NOTE',NULL,'0','1','1','0','0','1','0',NULL,'{
"min_length": 0,
"max_length": 4000
}',NULL,NULL,NULL,'自由記述欄。レコードの廃止・復活時にも記載可能。','Comments section. Can comment when removing or restoring records.',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK (COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('2010122','20101','廃止フラグ','Discard','discard',NULL,'1',220,NULL,NULL,NULL,NULL,'0',NULL,NULL,NULL,NULL,'DISUSE_FLAG',NULL,'1','1','1','0','1','1','0',NULL,NULL,NULL,NULL,NULL,'廃止フラグ。復活以外のオペレーションは不可','Discard flag. Cannot do operation other than restore.',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK_JNL (JOURNAL_SEQ_NO,JOURNAL_REG_DATETIME,JOURNAL_ACTION_CLASS,COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES(2010122,_____DATE_____,'INSERT','2010122','20101','廃止フラグ','Discard','discard',NULL,'1',220,NULL,NULL,NULL,NULL,'0',NULL,NULL,NULL,NULL,'DISUSE_FLAG',NULL,'1','1','1','0','1','1','0',NULL,NULL,NULL,NULL,NULL,'廃止フラグ。復活以外のオペレーションは不可','Discard flag. Cannot do operation other than restore.',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK (COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('2010123','20101','最終更新日時','Last update date/time','last_update_date_time',NULL,'13',230,NULL,NULL,NULL,NULL,'0',NULL,NULL,NULL,NULL,'LAST_UPDATE_TIMESTAMP',NULL,'1','0','1','0','1','1','0',NULL,NULL,NULL,NULL,NULL,'レコードの最終更新日。更新可否判定に使用。自動登録のため編集不可。','Last update date of record. Useful for judging the possibility of an update. Cannot edit because of auto-numbering.',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK_JNL (JOURNAL_SEQ_NO,JOURNAL_REG_DATETIME,JOURNAL_ACTION_CLASS,COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES(2010123,_____DATE_____,'INSERT','2010123','20101','最終更新日時','Last update date/time','last_update_date_time',NULL,'13',230,NULL,NULL,NULL,NULL,'0',NULL,NULL,NULL,NULL,'LAST_UPDATE_TIMESTAMP',NULL,'1','0','1','0','1','1','0',NULL,NULL,NULL,NULL,NULL,'レコードの最終更新日。更新可否判定に使用。自動登録のため編集不可。','Last update date of record. Useful for judging the possibility of an update. Cannot edit because of auto-numbering.',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK (COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('2010124','20101','最終更新者','Last updated by','last_updated_user',NULL,'14',240,NULL,NULL,NULL,NULL,'0',NULL,NULL,NULL,NULL,'LAST_UPDATE_USER',NULL,'1','0','1','0','1','1','0',NULL,NULL,NULL,NULL,NULL,'更新者。ログインユーザのIDが自動的に登録される。編集不可。','Updated by. Login user ID is automatically registered. Cannot edit.',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK_JNL (JOURNAL_SEQ_NO,JOURNAL_REG_DATETIME,JOURNAL_ACTION_CLASS,COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES(2010124,_____DATE_____,'INSERT','2010124','20101','最終更新者','Last updated by','last_updated_user',NULL,'14',240,NULL,NULL,NULL,NULL,'0',NULL,NULL,NULL,NULL,'LAST_UPDATE_USER',NULL,'1','0','1','0','1','1','0',NULL,NULL,NULL,NULL,NULL,'更新者。ログインユーザのIDが自動的に登録される。編集不可。','Updated by. Login user ID is automatically registered. Cannot edit.',NULL,'0',_____DATE_____,1);

-- ------------------------------------------------------------
-- T_COMN_MENU : UPDATE
-- ------------------------------------------------------------
-- - ソートキーの修正

UPDATE T_COMN_MENU SET SORT_KEY = '[{"ASC":"member_variables"},{"ASC":"variable_name"},{"ASC":"prefix_file_name"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='20109';
UPDATE T_COMN_MENU_JNL SET SORT_KEY = '[{"ASC":"member_variables"},{"ASC":"variable_name"},{"ASC":"prefix_file_name"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='20109';

UPDATE T_COMN_MENU SET SORT_KEY = '[{"ASC":"include_order"},{"ASC":"playbook_file"},{"ASC":"movement"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='20203';
UPDATE T_COMN_MENU_JNL SET SORT_KEY = '[{"ASC":"include_order"},{"ASC":"playbook_file"},{"ASC":"movement"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='20203';

UPDATE T_COMN_MENU SET SORT_KEY = '[{"ASC":"host"},{"ASC":"movement"},{"ASC":"operation"},{"ASC":"execution_no"},{"ASC":"last_update_date_time"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='20206';
UPDATE T_COMN_MENU_JNL SET SORT_KEY = '[{"ASC":"host"},{"ASC":"movement"},{"ASC":"operation"},{"ASC":"execution_no"},{"ASC":"last_update_date_time"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='20206';

UPDATE T_COMN_MENU SET SORT_KEY = '[{"ASC":"substitution_order"},{"ASC":"variable_name"},{"ASC":"host"},{"ASC":"operation"},{"ASC":"execution_no"},{"ASC":"last_update_date_time"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='20207';
UPDATE T_COMN_MENU_JNL SET SORT_KEY = '[{"ASC":"substitution_order"},{"ASC":"variable_name"},{"ASC":"host"},{"ASC":"operation"},{"ASC":"execution_no"},{"ASC":"last_update_date_time"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='20207';

UPDATE T_COMN_MENU SET SORT_KEY = '[{"ASC":"include_order"},{"ASC":"dialog_type"},{"ASC":"movement"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='20305';
UPDATE T_COMN_MENU_JNL SET SORT_KEY = '[{"ASC":"include_order"},{"ASC":"dialog_type"},{"ASC":"movement"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='20305';

UPDATE T_COMN_MENU SET SORT_KEY = '[{"ASC":"host"},{"ASC":"movement"},{"ASC":"operation"},{"ASC":"execution_no"},{"ASC":"last_update_date_time"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='20308';
UPDATE T_COMN_MENU_JNL SET SORT_KEY = '[{"ASC":"host"},{"ASC":"movement"},{"ASC":"operation"},{"ASC":"execution_no"},{"ASC":"last_update_date_time"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='20308';

UPDATE T_COMN_MENU SET SORT_KEY = '[{"ASC":"substitution_order"},{"ASC":"variable_name"},{"ASC":"host"},{"ASC":"operation"},{"ASC":"execution_no"},{"ASC":"last_update_date_time"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='20309';
UPDATE T_COMN_MENU_JNL SET SORT_KEY = '[{"ASC":"substitution_order"},{"ASC":"variable_name"},{"ASC":"host"},{"ASC":"operation"},{"ASC":"execution_no"},{"ASC":"last_update_date_time"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='20309';

UPDATE T_COMN_MENU SET SORT_KEY = '[{"ASC":"include_order"},{"ASC":"role_package_name_role_name"},{"ASC":"role_package_name"},{"ASC":"movement"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='20404';
UPDATE T_COMN_MENU_JNL SET SORT_KEY = '[{"ASC":"include_order"},{"ASC":"role_package_name_role_name"},{"ASC":"role_package_name"},{"ASC":"movement"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='20404';

UPDATE T_COMN_MENU SET SORT_KEY = '[{"ASC":"iteration_member_variable_name"},{"ASC":"variable_name"},{"ASC":"movement"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='20406';
UPDATE T_COMN_MENU_JNL SET SORT_KEY = '[{"ASC":"iteration_member_variable_name"},{"ASC":"variable_name"},{"ASC":"movement"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='20406';

UPDATE T_COMN_MENU SET SORT_KEY = '[{"ASC":"host"},{"ASC":"movement"},{"ASC":"operation"},{"ASC":"execution_no"},{"ASC":"last_update_date_time"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='20408';
UPDATE T_COMN_MENU_JNL SET SORT_KEY = '[{"ASC":"host"},{"ASC":"movement"},{"ASC":"operation"},{"ASC":"execution_no"},{"ASC":"last_update_date_time"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='20408';

UPDATE T_COMN_MENU SET SORT_KEY = '[{"ASC":"substitution_order"},{"ASC":"member_variable_name"},{"ASC":"variable_name"},{"ASC":"host"},{"ASC":"operation"},{"ASC":"execution_no"},{"ASC":"last_update_date_time"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='20409';
UPDATE T_COMN_MENU_JNL SET SORT_KEY = '[{"ASC":"substitution_order"},{"ASC":"member_variable_name"},{"ASC":"variable_name"},{"ASC":"host"},{"ASC":"operation"},{"ASC":"execution_no"},{"ASC":"last_update_date_time"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='20409';

UPDATE T_COMN_MENU SET SORT_KEY = '[{"ASC":"parent_variable_name"},{"ASC":"movement"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='20413';
UPDATE T_COMN_MENU_JNL SET SORT_KEY = '[{"ASC":"parent_variable_name"},{"ASC":"movement"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='20413';

UPDATE T_COMN_MENU SET SORT_KEY = '[{"ASC":"dropdown_display_member_variable"},{"ASC":"variable_name"},{"ASC":"movement"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='20414';
UPDATE T_COMN_MENU_JNL SET SORT_KEY = '[{"ASC":"dropdown_display_member_variable"},{"ASC":"variable_name"},{"ASC":"movement"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='20414';

UPDATE T_COMN_MENU SET WEB_PRINT_LIMIT = 10000, WEB_PRINT_CONFIRM = 1000 WHERE MENU_ID IN ('20101','20102','20103','20104','20105','20106','20107','20108','20109','20201','20202','20203','20204','20205','20206','20207','20208','20209',
'20210','20301','20302','20303','20304','20305','20306','20307','20308','20309','20310','20311','20312','20401','20402','20402','20403','20404','20405','20406','20407','20408','20409','20410','20411','20412','20413','20414');
UPDATE T_COMN_MENU_JNL SET WEB_PRINT_LIMIT = 10000, WEB_PRINT_CONFIRM = 1000 WHERE MENU_ID IN ('20101','20102','20103','20104','20105','20106','20107','20108','20109','20201','20202','20203','20204','20205','20206','20207','20208','20209',
'20210','20301','20302','20303','20304','20305','20306','20307','20308','20309','20310','20311','20312','20401','20402','20402','20403','20404','20405','20406','20407','20408','20409','20410','20411','20412','20413','20414');
UPDATE T_COMN_MENU SET INITIAL_FILTER_FLG = 1 WHERE MENU_ID IN ('20101','20103','20104','20105','20106','20108','20109','20205','20302','20303','20304','20305','20307','20407');
UPDATE T_COMN_MENU_JNL SET INITIAL_FILTER_FLG = 1 WHERE MENU_ID IN ('20101','20103','20104','20105','20106','20108','20109','20205','20302','20303','20304','20305','20307','20407');