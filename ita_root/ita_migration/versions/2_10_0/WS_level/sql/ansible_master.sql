-- メニュー・カラム紐付管理(UPDATE): インターフェース情報 - 実行エンジンの説明文
UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '実行するエンジンを4種類から選択します。
・Ansible Core
・Ansible Automation Controller
・Ansible Execution Agent
・Ansible Automation Platform (Cloud)
※Ansible Core以外を選択した場合もansible-vaultコマンドを実行するAnsible Coreインターフェースの設定が必要です。', DESCRIPTION_EN = 'Select the execution engine from 4 types.
・Ansible Core
・Ansible Automation Controller
・Ansible Execution Agent
・Ansible Automation Platform (Cloud)
※Configuring the Ansible Core interface is required in order to use ansible-vault commands, even if Ansible Core is not selected as the execution engine.', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '2010202';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '実行するエンジンを4種類から選択します。
・Ansible Core
・Ansible Automation Controller
・Ansible Execution Agent
・Ansible Automation Platform (Cloud)
※Ansible Core以外を選択した場合もansible-vaultコマンドを実行するAnsible Coreインターフェースの設定が必要です。', DESCRIPTION_EN = 'Select the execution engine from 4 types.
・Ansible Core
・Ansible Automation Controller
・Ansible Execution Agent
・Ansible Automation Platform (Cloud)
※Configuring the Ansible Core interface is required in order to use ansible-vault commands, even if Ansible Core is not selected as the execution engine.', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '2010202';

-- メニュー・カラム紐付管理(UPDATE): 作業管理(Legacy/Pioneer/Role) - 実行エンジンの説明文
UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '実行するエンジンを4種類から選択します。
・Ansible Core
・Ansible Automation Controller
・Ansible Execution Agent
・Ansible Automation Platform (Cloud)
※Ansible Core以外を選択した場合もansible-vaultコマンドを実行するAnsible Coreインターフェースの設定が必要です。', DESCRIPTION_EN = 'Select the execution engine from 4 types.
・Ansible Core
・Ansible Automation Controller
・Ansible Execution Agent
・Ansible Automation Platform (Cloud)
※Configuring the Ansible Core interface is required in order to use ansible-vault commands, even if Ansible Core is not selected as the execution engine.', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID IN ('2021005','2031205','2041205');
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '実行するエンジンを4種類から選択します。
・Ansible Core
・Ansible Automation Controller
・Ansible Execution Agent
・Ansible Automation Platform (Cloud)
※Ansible Core以外を選択した場合もansible-vaultコマンドを実行するAnsible Coreインターフェースの設定が必要です。', DESCRIPTION_EN = 'Select the execution engine from 4 types.
・Ansible Core
・Ansible Automation Controller
・Ansible Execution Agent
・Ansible Automation Platform (Cloud)
※Configuring the Ansible Core interface is required in order to use ansible-vault commands, even if Ansible Core is not selected as the execution engine.', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID IN ('2021005','2031205','2041205');

-- メニュー・カラム紐付管理(UPDATE): インターフェース情報 - Proxy Address/Port

-- T_COMN_MENU_COLUMN_LINK: Proxy Address (COLUMN_DEFINITION_ID='2010209')
UPDATE T_COMN_MENU_COLUMN_LINK SET
  COL_GROUP_ID = '2010202',
  COLUMN_NAME_JA = 'Proxy Address',
  COLUMN_NAME_EN = 'Proxy Address',
  LAST_UPDATE_TIMESTAMP = _____DATE_____
WHERE COLUMN_DEFINITION_ID = '2010209';

-- T_COMN_MENU_COLUMN_LINK: Proxy Port (COLUMN_DEFINITION_ID='2010210')
UPDATE T_COMN_MENU_COLUMN_LINK SET
  COL_GROUP_ID = '2010202',
  COLUMN_NAME_JA = 'Proxy Port',
  COLUMN_NAME_EN = 'Proxy Port',
  LAST_UPDATE_TIMESTAMP = _____DATE_____
WHERE COLUMN_DEFINITION_ID = '2010210';

-- T_COMN_MENU_COLUMN_LINK_JNL: Proxy Address (JOURNAL_SEQ_NO='2010209')
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET
  COL_GROUP_ID = '2010202',
  COLUMN_NAME_JA = 'Proxy Address',
  COLUMN_NAME_EN = 'Proxy Address',
  LAST_UPDATE_TIMESTAMP = _____DATE_____
WHERE COLUMN_DEFINITION_ID = '2010210';

-- T_COMN_MENU_COLUMN_LINK_JNL: Proxy Port (JOURNAL_SEQ_NO='2010210')
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET
  COL_GROUP_ID = '2010202',
  COLUMN_NAME_JA = 'Proxy Port',
  COLUMN_NAME_EN = 'Proxy Port',
  LAST_UPDATE_TIMESTAMP = _____DATE_____
WHERE COLUMN_DEFINITION_ID = '2010210';

-- 実行環境パラメータ定義のimageカラム初期値をUBI8からUBI9に変更

-- T_COMN_MENU_COLUMN_LINK: image (COLUMN_DEFINITION_ID='35cc8e65-ca2d-488d-9d69-2d9ec5622bf3')
UPDATE T_COMN_MENU_COLUMN_LINK SET
  INITIAL_VALUE = 'registry.access.redhat.com/ubi9/ubi-init:latest',
  LAST_UPDATE_TIMESTAMP = _____DATE_____
WHERE COLUMN_DEFINITION_ID = '35cc8e65-ca2d-488d-9d69-2d9ec5622bf3'
  AND MENU_ID = '8df96afe-552a-4a2a-b370-cb3888b27dee';

-- T_COMN_MENU_COLUMN_LINK_JNL: image (JOURNAL_SEQ_NO='571fbb1d-6c35-4139-9f3f-de0cd2da12fb')
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET
  INITIAL_VALUE = 'registry.access.redhat.com/ubi9/ubi-init:latest',
  LAST_UPDATE_TIMESTAMP = _____DATE_____
WHERE JOURNAL_SEQ_NO = '571fbb1d-6c35-4139-9f3f-de0cd2da12fb';

-- T_MENU_COLUMN: image (CREATE_COLUMN_ID='d6a6d91c-7283-49b0-9067-72a283ffc2d0')
UPDATE T_MENU_COLUMN SET
  MULTI_DEFAULT_VALUE = 'registry.access.redhat.com/ubi9/ubi-init:latest',
  LAST_UPDATE_TIMESTAMP = _____DATE_____
WHERE CREATE_COLUMN_ID = 'd6a6d91c-7283-49b0-9067-72a283ffc2d0';

-- T_MENU_COLUMN_JNL: image (JOURNAL_SEQ_NO='bfb3cc1c-be7a-418b-a21c-488d3ff89fb4')
UPDATE T_MENU_COLUMN_JNL SET
  MULTI_DEFAULT_VALUE = 'registry.access.redhat.com/ubi9/ubi-init:latest',
  LAST_UPDATE_TIMESTAMP = _____DATE_____
WHERE JOURNAL_SEQ_NO = 'bfb3cc1c-be7a-418b-a21c-488d3ff89fb4';
