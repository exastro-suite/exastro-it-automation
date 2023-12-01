-- INSERT/UPDATE: -2.3.0
    -- T_COMN_MENU_TABLE_LINK : UPDATE

-- ------------------------------------------------------------
-- ▼TABLE MASTER UPDATE START
-- ------------------------------------------------------------

-- T_COMN_MENU_TABLE_LINK: UPDATE
UPDATE T_COMN_MENU_TABLE_LINK SET SHEET_TYPE = '28', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE TABLE_DEFINITION_ID = '20210';
UPDATE T_COMN_MENU_TABLE_LINK_JNL SET SHEET_TYPE = '28', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE TABLE_DEFINITION_ID = '20210';
UPDATE T_COMN_MENU_TABLE_LINK SET SHEET_TYPE = '28', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE TABLE_DEFINITION_ID = '20312';
UPDATE T_COMN_MENU_TABLE_LINK_JNL SET SHEET_TYPE = '28', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE TABLE_DEFINITION_ID = '20312';
UPDATE T_COMN_MENU_TABLE_LINK SET SHEET_TYPE = '28', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE TABLE_DEFINITION_ID = '20412';
UPDATE T_COMN_MENU_TABLE_LINK_JNL SET SHEET_TYPE = '28', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE TABLE_DEFINITION_ID = '20412';

-- T_COMN_MENU_COLUMN_LINK: UPDATE
UPDATE T_COMN_MENU_COLUMN_LINK SET INITIAL_VALUE = '- hosts: all
  remote_user: \"{{ __loginuser__ }}\"
  gather_facts: no', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '2020108';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET INITIAL_VALUE = '- hosts: all
  remote_user: \"{{ __loginuser__ }}\"
  gather_facts: no', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '2020108';
UPDATE T_COMN_MENU_COLUMN_LINK SET INITIAL_VALUE = '- hosts: all
  remote_user: \"{{ __loginuser__ }}\"
  gather_facts: no', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '2030108';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET INITIAL_VALUE = '- hosts: all
  remote_user: \"{{ __loginuser__ }}\"
  gather_facts: no', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '2030108';
UPDATE T_COMN_MENU_COLUMN_LINK SET INITIAL_VALUE = '- hosts: all
  remote_user: \"{{ __loginuser__ }}\"
  gather_facts: no', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '2040208';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET INITIAL_VALUE = '- hosts: all
  remote_user: \"{{ __loginuser__ }}\"
  gather_facts: no', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '2040208';

-- ------------------------------------------------------------
-- ▼TABLE MASTER UPDATE END
-- ------------------------------------------------------------