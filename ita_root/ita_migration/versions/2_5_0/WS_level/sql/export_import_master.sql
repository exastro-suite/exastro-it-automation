-- ------------------------------------------------------------
-- T_COMN_MENU: UPDATE
-- ------------------------------------------------------------
UPDATE T_COMN_MENU SET WEB_PRINT_LIMIT = 10000, WEB_PRINT_CONFIRM = 1000 WHERE MENU_ID IN ('60101','60102','60103','60104','60105','60106');
UPDATE T_COMN_MENU_JNL SET WEB_PRINT_LIMIT = 10000, WEB_PRINT_CONFIRM = 1000 WHERE MENU_ID IN ('60101','60102','60103','60104','60105','60106');