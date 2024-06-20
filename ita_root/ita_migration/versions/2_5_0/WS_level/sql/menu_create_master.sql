-- ------------------------------------------------------------
-- T_COMN_MENU: UPDATE
-- ------------------------------------------------------------
UPDATE T_COMN_MENU SET WEB_PRINT_LIMIT = 10000, WEB_PRINT_CONFIRM = 1000 WHERE MENU_ID IN ('50101','50102','50103','50104','50106','50107','50109','50110','50111','50112','50191','50192','50501');
UPDATE T_COMN_MENU_JNL SET WEB_PRINT_LIMIT = 10000, WEB_PRINT_CONFIRM = 1000 WHERE MENU_ID IN ('50101','50102','50103','50104','50106','50107','50109','50110','50111','50112','50191','50192','50501');

-- ------------------------------------------------------------
-- T_COMN_MENU_COLUMN_LINK: UPDATE
-- ------------------------------------------------------------
UPDATE T_COMN_MENU_COLUMN_LINK SET VALIDATE_OPTION='{
"int_min": 1,
"int_max": 9223372036854775807
}' WHERE COLUMN_DEFINITION_ID='5010432';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET VALIDATE_OPTION='{
"int_min": 1,
"int_max": 9223372036854775807
}' WHERE COLUMN_DEFINITION_ID='5010432';
