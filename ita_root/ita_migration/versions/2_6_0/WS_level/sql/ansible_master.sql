-- -----------------------------------------------------------------------------
-- - ▼誤字修正
-- -   locla->local
-- -----------------------------------------------------------------------------
UPDATE T_COMN_MENU_COLUMN_LINK     SET DESCRIPTION_JA = 'Ansible Automation Controller認証情報の接続タイプを設定します。通常はmachineを選択します。ansible_connectionをlocalに設定する必要があるネットワーク機器の場合にNetworkを選択します。', DESCRIPTION_EN = 'Sets the connection type for Ansible Automation Controller credentials. Basically, select machine. Select Network for network devices that require ansible_connection set to local.' WHERE COLUMN_DEFINITION_ID = '2010120';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = 'Ansible Automation Controller認証情報の接続タイプを設定します。通常はmachineを選択します。ansible_connectionをlocalに設定する必要があるネットワーク機器の場合にNetworkを選択します。', DESCRIPTION_EN = 'Sets the connection type for Ansible Automation Controller credentials. Basically, select machine. Select Network for network devices that require ansible_connection set to local.' WHERE COLUMN_DEFINITION_ID = '2010120';

-- -----------------------------------------------------------------------------
-- - ▼Issue #2653　文字列カラムの最大長変更
-- -   8192バイト->65536バイト
-- -----------------------------------------------------------------------------
UPDATE T_COMN_MENU_COLUMN_LINK      SET VALIDATE_OPTION = '{
"min_length": 0,
"max_length": 65536
}', DESCRIPTION_JA = '[最大長]65536バイト', DESCRIPTION_EN = '[Maximum length] 65536 byte'  WHERE COLUMN_DEFINITION_ID = '2020708';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL  SET VALIDATE_OPTION = '{
"min_length": 0,
"max_length": 65536
}', DESCRIPTION_JA = '[最大長]65536バイト', DESCRIPTION_EN = '[Maximum length] 65536 byte'  WHERE COLUMN_DEFINITION_ID = '2020708';
UPDATE T_COMN_MENU_COLUMN_LINK      SET VALIDATE_OPTION = '{
"min_length": 0,
"max_length": 65536
}', DESCRIPTION_JA = '[最大長]65536バイト', DESCRIPTION_EN = '[Maximum length] 65536 byte'  WHERE COLUMN_DEFINITION_ID = '2030908';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL  SET VALIDATE_OPTION = '{
"min_length": 0,
"max_length": 65536
}', DESCRIPTION_JA = '[最大長]65536バイト', DESCRIPTION_EN = '[Maximum length] 65536 byte'  WHERE COLUMN_DEFINITION_ID = '2030908';
UPDATE T_COMN_MENU_COLUMN_LINK      SET VALIDATE_OPTION = '{
"min_length": 0,
"max_length": 65536
}', DESCRIPTION_JA = '[最大長]65536バイト', DESCRIPTION_EN = '[Maximum length] 65536 byte'  WHERE COLUMN_DEFINITION_ID = '2040909';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL  SET VALIDATE_OPTION = '{
"min_length": 0,
"max_length": 65536
}', DESCRIPTION_JA = '[最大長]65536バイト', DESCRIPTION_EN = '[Maximum length] 65536 byte'  WHERE COLUMN_DEFINITION_ID = '2040909';