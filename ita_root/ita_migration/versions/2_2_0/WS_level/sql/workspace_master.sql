-- INSERT/UPDATE: -2.2.0
    -- T_COMN_DEL_OPERATION_LIST: UPDATE
    -- T_COMN_MENU_COLUMN_LINK: UPDATE
    -- T_COMN_SYSTEM_CONFIG: INSERT

-- T_COMN_DEL_OPERATION_LIST: UPDATE
UPDATE T_COMN_DEL_OPERATION_LIST SET DATA_STORAGE_PATH = "/driver/ansible/legacy_role",LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE ROW_ID = "9";
UPDATE T_COMN_DEL_OPERATION_LIST_JNL SET DATA_STORAGE_PATH = "/driver/ansible/legacy_role",LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE ROW_ID = "9";

-- T_COMN_MENU_COLUMN_LINK: UPDATE
UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = "データストレージパス(省略可能)
データストレージパスで管理しているファイルがある場合、そのパスを入力します。
/storage/<<organization>>/<<workspace>>/配下のパスの場合は、/storage/<<organization>>/<<workspace>>からの相対パスを記載します。
exp)
 Ansible-Legacy
  /driver/ansible/legacy
 Ansible-Pioneer
  /driver/ansible/pioneer",LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = "1010505";
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = "データストレージパス(省略可能)
データストレージパスで管理しているファイルがある場合、そのパスを入力します。
/storage/<<organization>>/<<workspace>>/配下のパスの場合は、/storage/<<organization>>/<<workspace>>からの相対パスを記載します。
exp)
 Ansible-Legacy
  /driver/ansible/legacy
 Ansible-Pioneer
  /driver/ansible/pioneer",LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = "1010505";

UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_EN = "Data storage path (Can be abbreviated)
If there are files that are managed in a Data storage path, input said path.For paths under /storage/<<organization>>/<<workspace>>/, input a relative path from /storage/<<organization>>/<<workspace>>. 
exp)
 Ansible-Legacy
  /driver/ansible/legacy
 Ansible-Pioneer
  /driver/ansible/pioneer",LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = "1010505";
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_EN = "Data storage path (Can be abbreviated)
If there are files that are managed in a Data storage path, input said path.For paths under /storage/<<organization>>/<<workspace>>/, input a relative path from /storage/<<organization>>/<<workspace>>. 
exp)
 Ansible-Legacy
  /driver/ansible/legacy
 Ansible-Pioneer
  /driver/ansible/pioneer",LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = "1010505";

-- T_COMN_SYSTEM_CONFIG: INSERT
INSERT INTO T_COMN_SYSTEM_CONFIG (ITEM_ID, CONFIG_ID, CONFIG_NAME, VALUE, NOTE, DISUSE_FLAG, LAST_UPDATE_TIMESTAMP, LAST_UPDATE_USER) VALUES("3", "MAXIMUM_ITERATION_ANSIBLE-LEGACYROLE", "Maximum iteration count of Ansible-LegacyRole", "1024", "Ansible-LegacyRole：変数ネスト管理における最大繰返数の上限値
1～1024の間で設定可能
1～1024：設定した値
上記以外：1024

Ansible-LegacyRole：Maximum iteration counts upper limit in Nested variable list
Can be set between 1 and 1024
Configured value: 1 ~ 1024
Other than the above: 1024", "0", _____DATE_____, "1");
INSERT INTO T_COMN_SYSTEM_CONFIG_JNL (JOURNAL_SEQ_NO, JOURNAL_REG_DATETIME, JOURNAL_ACTION_CLASS, ITEM_ID, CONFIG_ID, CONFIG_NAME, VALUE, NOTE, DISUSE_FLAG, LAST_UPDATE_TIMESTAMP, LAST_UPDATE_USER) VALUES ("3", _____DATE_____, "INSERT", "3", "MAXIMUM_ITERATION_ANSIBLE-LEGACYROLE", "Maximum iteration count of Ansible-LegacyRole", "1024", "Ansible-LegacyRole：変数ネスト管理における最大繰返数の上限値
1～1024の間で設定可能
1～1024：設定した値
上記以外：1024

Ansible-LegacyRole：Maximum iteration counts upper limit in Nested variable list
Can be set between 1 and 1024
Configured value: 1 ~ 1024
Other than the above: 1024", "0", _____DATE_____, "1");

INSERT INTO T_COMN_SYSTEM_CONFIG (ITEM_ID, CONFIG_ID, CONFIG_NAME, VALUE, NOTE, DISUSE_FLAG, LAST_UPDATE_TIMESTAMP, LAST_UPDATE_USER) VALUES ("4", "MAXIMUM_ITERATION_TERRAFORM-CLOUD-EP", "Maximum iteration count of Terraform-Cloud/EP", "1024", "Terraform-Cloud/EP：変数ネスト管理における最大繰返数の上限値
1～1024の間で設定可能
1～1024：設定した値
上記以外：1024

Terraform-Cloud/EP：Maximum iteration counts upper limit in Nested variable list
Can be set between 1 and 1024
Configured value: 1 ~ 1024
Other than the above: 1024", "0", _____DATE_____, "1");
INSERT INTO T_COMN_SYSTEM_CONFIG_JNL (JOURNAL_SEQ_NO, JOURNAL_REG_DATETIME, JOURNAL_ACTION_CLASS, ITEM_ID, CONFIG_ID, CONFIG_NAME, VALUE, NOTE, DISUSE_FLAG, LAST_UPDATE_TIMESTAMP, LAST_UPDATE_USER) VALUES ("4", _____DATE_____, "INSERT", "4", "MAXIMUM_ITERATION_TERRAFORM-CLOUD-EP", "Maximum iteration count of Terraform-Cloud/EP", "1024", "Terraform-Cloud/EP：変数ネスト管理における最大繰返数の上限値
1～1024の間で設定可能
1～1024：設定した値
上記以外：1024

Terraform-Cloud/EP：Maximum iteration counts upper limit in Nested variable list
Can be set between 1 and 1024
Configured value: 1 ~ 1024
Other than the above: 1024", "0", _____DATE_____, "1");

INSERT INTO T_COMN_SYSTEM_CONFIG (ITEM_ID, CONFIG_ID, CONFIG_NAME, VALUE, NOTE, DISUSE_FLAG, LAST_UPDATE_TIMESTAMP, LAST_UPDATE_USER) VALUES ("5", "MAXIMUM_ITERATION_TERRAFORM-CLI", "Maximum iteration count of Terraform-CLI", "1024", "Terraform-CLI：変数ネスト管理における最大繰返数の上限値
1～1024の間で設定可能
1～1024：設定した値
上記以外：1024

Terraform-CLI：Maximum iteration counts upper limit in Nested variable list
Can be set between 1 and 1024
Configured value: 1 ~ 1024
Other than the above: 1024", "0", _____DATE_____, "1");
INSERT INTO T_COMN_SYSTEM_CONFIG_JNL (JOURNAL_SEQ_NO, JOURNAL_REG_DATETIME, JOURNAL_ACTION_CLASS, ITEM_ID, CONFIG_ID, CONFIG_NAME, VALUE, NOTE, DISUSE_FLAG, LAST_UPDATE_TIMESTAMP, LAST_UPDATE_USER) VALUES ("5", _____DATE_____, "INSERT", "5", "MAXIMUM_ITERATION_TERRAFORM-CLI", "Maximum iteration count of Terraform-CLI", "1024", "Terraform-CLI：変数ネスト管理における最大繰返数の上限値
1～1024の間で設定可能
1～1024：設定した値
上記以外：1024

Terraform-CLI：Maximum iteration counts upper limit in Nested variable list
Can be set between 1 and 1024
Configured value: 1 ~ 1024
Other than the above: 1024", "0", _____DATE_____, "1");