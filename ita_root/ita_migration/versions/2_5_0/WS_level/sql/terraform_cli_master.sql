-- INSERT/UPDATE: 2.5.0
    -- T_COMN_MENU : UPDATE

UPDATE T_COMN_MENU SET SORT_KEY = '', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='90101';
UPDATE T_COMN_MENU_JNL SET SORT_KEY = '', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='90101';

UPDATE T_COMN_MENU SET SORT_KEY = '[{"ASC":"iteration_member_variable_name"}, {"ASC":"variable_name"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='90106';
UPDATE T_COMN_MENU_JNL SET SORT_KEY = '[{"ASC":"iteration_member_variable_name"}, {"ASC":"variable_name"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='90106';

UPDATE T_COMN_MENU SET SORT_KEY = '[{"DESC":"substitution_order"},{"ASC":"member_variable_name"},{"ASC":"variable_name"},{"ASC":"movement_name"},{"ASC":"column_substitution_order"},{"ASC":"menu_group_menu_item"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='90107';
UPDATE T_COMN_MENU_JNL SET SORT_KEY = '[{"DESC":"substitution_order"},{"ASC":"member_variable_name"},{"ASC":"variable_name"},{"ASC":"movement_name"},{"ASC":"column_substitution_order"},{"ASC":"menu_group_menu_item"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='90107';

UPDATE T_COMN_MENU SET SORT_KEY = '[{"ASC":"substitution_order"},{"ASC":"member_variable_name"},{"ASC":"variable_name"},{"ASC":"operation"},{"ASC":"execution_no"},{"ASC":"last_update_date_time"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='90111';
UPDATE T_COMN_MENU_JNL SET SORT_KEY = '[{"ASC":"substitution_order"},{"ASC":"member_variable_name"},{"ASC":"variable_name"},{"ASC":"operation"},{"ASC":"execution_no"},{"ASC":"last_update_date_time"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='90111';

UPDATE T_COMN_MENU SET SORT_KEY = '[{"ASC":"member_variable_name"},{"ASC":"key_ofchild_member_variable"},{"ASC":"parent_variable_name"}, {"ASC":"original_variable_name"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='90113';
UPDATE T_COMN_MENU_JNL SET SORT_KEY = '[{"ASC":"member_variable_name"},{"ASC":"key_ofchild_member_variable"},{"ASC":"parent_variable_name"}, {"ASC":"original_variable_name"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='90113';

UPDATE T_COMN_MENU SET WEB_PRINT_LIMIT = 10000, WEB_PRINT_CONFIRM = 1000 WHERE MENU_ID IN ('90101','90102','90103','90104','90105','90106','90107','90108','90109','90110','90111','90112','90113','90114','90115');
UPDATE T_COMN_MENU_JNL SET WEB_PRINT_LIMIT = 10000, WEB_PRINT_CONFIRM = 1000 WHERE MENU_ID IN ('90101','90102','90103','90104','90105','90106','90107','90108','90109','90110','90111','90112','90113','90114','90115');
UPDATE T_COMN_MENU SET INITIAL_FILTER_FLG = 1 WHERE MENU_ID IN ('90107');
UPDATE T_COMN_MENU_JNL SET INITIAL_FILTER_FLG = 1 WHERE MENU_ID IN ('90107');