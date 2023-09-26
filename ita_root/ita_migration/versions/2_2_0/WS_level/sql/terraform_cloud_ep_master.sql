-- INSERT/UPDATE: -2.2.0
    -- T_COMN_SYSTEM_CONFIG: INSERT
    -- T_COMN_MENU_COLUMN_LINK: UPDATE

-- T_COMN_SYSTEM_CONFIG: INSERT
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


-- T_COMN_MENU_COLUMN_LINK: UPDATE
UPDATE T_COMN_MENU_COLUMN_LINK SET VALIDATE_OPTION = NULL , DESCRIPTION_JA = "対象の変数もしくはメンバー変数配下のメンバー変数が繰り返される数。
最小値は1、最大値は「管理コンソール/システム設定 」内で設定変更可能。" , DESCRIPTION_EN = "The number of times the target variable or a member variable under the member variable is repeated.
The minimum value is 1, the maximum value can be changed within the Management console/System setting." , LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = "8011104";
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET VALIDATE_OPTION = NULL , DESCRIPTION_JA = "対象の変数もしくはメンバー変数配下のメンバー変数が繰り返される数。
最小値は1、最大値は「管理コンソール/システム設定 」内で設定変更可能。" , DESCRIPTION_EN = "The number of times the target variable or a member variable under the member variable is repeated.
The minimum value is 1, the maximum value can be changed within the Management console/System setting." , LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = "8011104";
