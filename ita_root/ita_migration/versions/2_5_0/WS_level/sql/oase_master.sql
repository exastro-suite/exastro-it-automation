-- INSERT/UPDATE: -2.5.0
    -- T_COMN_MENU_COLUMN_LINK: UPDATE
    -- T_COMN_MENU: UPDATE

-- T_COMN_MENU_COLUMN_LINK: UPDATE
UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '[最大長]4000バイト
ログインするユーザーのパスワードを入力します。', DESCRIPTION_EN = '[Maximum length] 4000 bytes
Enter the password of the user to log in.', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010111';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '[最大長]4000バイト
ログインするユーザーのパスワードを入力します。', DESCRIPTION_EN = '[Maximum length] 4000 bytes
Enter the password of the user to log in.', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010111';

UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '[最大長]255バイト
どのルールから作成された結論イベントなのかを、恒久的に判別するため"_exastro_rule_name"ラベルに設定する任意の名前を入力します。
※編集不可', DESCRIPTION_EN = '[Maximum length] 255 bytes
Enter any name you want to set in the "_exastro_rule_name" label to permanently identify which rule the conclusion event was created from.
* Unable to edit', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010904';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '[最大長]255バイト
どのルールから作成された結論イベントなのかを、恒久的に判別するため"_exastro_rule_name"ラベルに設定する任意の名前を入力します。
※編集不可', DESCRIPTION_EN = '[Maximum length] 255 bytes
Enter any name you want to set in the "_exastro_rule_name" label to permanently identify which rule the conclusion event was created from.
* Unable to edit', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010904';

UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '[元データ]Conductor作業履歴', DESCRIPTION_EN = '[Original data]Conductor history', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011007';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '[元データ]Conductor作業履歴', DESCRIPTION_EN = '[Original data]Conductor history', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011007';

UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '[元データ]Conductor作業履歴', DESCRIPTION_EN = '[Original data]Conductor history', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011009';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '[元データ]Conductor作業履歴', DESCRIPTION_EN = '[Original data]Conductor history', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011009';

-- ------------------------------------------------------------
-- T_COMN_MENU: UPDATE
-- ------------------------------------------------------------
UPDATE T_COMN_MENU SET WEB_PRINT_LIMIT = 10000, WEB_PRINT_CONFIRM = 1000 WHERE MENU_ID IN ('110101','110102','110103','110104','110105','110106','110107','110108','110109','110110');
UPDATE T_COMN_MENU_JNL SET WEB_PRINT_LIMIT = 10000, WEB_PRINT_CONFIRM = 1000 WHERE MENU_ID IN ('110101','110102','110103','110104','110105','110106','110107','110108','110109','110110');
UPDATE T_COMN_MENU SET INITIAL_FILTER_FLG = 1 WHERE MENU_ID IN ('110101','110102','110105','110106','110107','110108','110109');
UPDATE T_COMN_MENU_JNL SET INITIAL_FILTER_FLG = 1 WHERE MENU_ID IN ('110101','110102','110105','110106','110107','110108','110109');