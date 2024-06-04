-- INSERT/UPDATE: 2.5.0
    -- T_COMN_MENU : UPDATE

UPDATE T_COMN_MENU SET SORT_KEY = '', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='80101';
UPDATE T_COMN_MENU_JNL SET SORT_KEY = '', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='80101';

UPDATE T_COMN_MENU SET SORT_KEY = '[{"ASC":"iteration_member_variable_name"}, {"ASC":"variable_name"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='80111';
UPDATE T_COMN_MENU_JNL SET SORT_KEY = '[{"ASC":"iteration_member_variable_name"}, {"ASC":"variable_name"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='80111';

UPDATE T_COMN_MENU SET SORT_KEY = '[{"DESC":"substitution_order"},{"ASC":"member_variable_name"},{"ASC":"variable_name"},{"ASC":"movement_name"},{"ASC":"column_substitution_order"},{"ASC":"menu_group_menu_item"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='80112';
UPDATE T_COMN_MENU_JNL SET SORT_KEY = '[{"DESC":"substitution_order"},{"ASC":"member_variable_name"},{"ASC":"variable_name"},{"ASC":"movement_name"},{"ASC":"column_substitution_order"},{"ASC":"menu_group_menu_item"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='80112';

UPDATE T_COMN_MENU SET SORT_KEY = '[{"ASC":"substitution_order"},{"ASC":"member_variable_name"},{"ASC":"variable_name"},{"ASC":"operation"},{"ASC":"execution_no"},{"ASC":"last_update_date_time"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='80116';
UPDATE T_COMN_MENU_JNL SET SORT_KEY = '[{"ASC":"substitution_order"},{"ASC":"member_variable_name"},{"ASC":"variable_name"},{"ASC":"operation"},{"ASC":"execution_no"},{"ASC":"last_update_date_time"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='80116';

UPDATE T_COMN_MENU SET SORT_KEY = '[{"ASC":"member_variable_name"},{"ASC":"key_ofchild_member_variable"},{"ASC":"parent_variable_name"}, {"ASC":"original_variable_name"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='80119';
UPDATE T_COMN_MENU_JNL SET SORT_KEY = '[{"ASC":"member_variable_name"},{"ASC":"key_ofchild_member_variable"},{"ASC":"parent_variable_name"}, {"ASC":"original_variable_name"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='80119';

UPDATE T_COMN_MENU SET WEB_PRINT_LIMIT = 10000, WEB_PRINT_CONFIRM = 1000 WHERE MENU_ID IN ('80101','80102','80103','80104','80105','80106','80107','80108','80109','80110','80111','80112','80113','80114','80115','80116','80117','80118','80119','80120','80121');
UPDATE T_COMN_MENU_JNL SET WEB_PRINT_LIMIT = 10000, WEB_PRINT_CONFIRM = 1000 WHERE MENU_ID IN ('80101','80102','80103','80104','80105','80106','80107','80108','80109','80110','80111','80112','80113','80114','80115','80116','80117','80118','80119','80120','80121');
UPDATE T_COMN_MENU SET INITIAL_FILTER_FLG = 1 WHERE MENU_ID IN ('80112');
UPDATE T_COMN_MENU_JNL SET INITIAL_FILTER_FLG = 1 WHERE MENU_ID IN ('80112');