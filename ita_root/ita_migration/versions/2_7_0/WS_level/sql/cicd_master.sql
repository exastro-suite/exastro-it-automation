-- -----------------------------------------------------------------------------
-- - ▼Issue 行末の空白調整
-- -----------------------------------------------------------------------------
UPDATE T_COMN_MENU_COLUMN_LINK      SET DESCRIPTION_EN = 'Input the Git user.
The Uses is an required item when "Private" is selected for Visibility.
[Maximum length] 255 Bytes'  WHERE COLUMN_DEFINITION_ID = '10010107';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL  SET DESCRIPTION_EN = 'Input the Git user.
The Uses is an required item when "Private" is selected for Visibility.
[Maximum length] 255 Bytes'  WHERE COLUMN_DEFINITION_ID = '10010107';

UPDATE T_COMN_MENU_COLUMN_LINK      SET DESCRIPTION_EN = 'Please input the password needed when running the Git clone command.
The password is required if the visibility type is set to "Private".
[Max size] 255 bytes'  WHERE COLUMN_DEFINITION_ID = '10010108';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL  SET DESCRIPTION_EN = 'Please input the password needed when running the Git clone command.
The password is required if the visibility type is set to "Private".
[Max size] 255 bytes'  WHERE COLUMN_DEFINITION_ID = '10010108';

UPDATE T_COMN_MENU_COLUMN_LINK      SET DESCRIPTION_EN = 'Select if the Remote Repository should be synchronized automatically or not.
True: Synchronizes with the remote repository with the input cycle.
False: Does not synchronize the remote repository automatically.'  WHERE COLUMN_DEFINITION_ID = '10010114';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL  SET DESCRIPTION_EN = 'Select if the Remote Repository should be synchronized automatically or not.
True: Synchronizes with the remote repository with the input cycle.
False: Does not synchronize the remote repository automatically.'  WHERE COLUMN_DEFINITION_ID = '10010114';

UPDATE T_COMN_MENU_COLUMN_LINK      SET DESCRIPTION_EN = 'Select if the Remote Repository should be synchronized automatically or not.
True: Synchronizes with the remote repository with the input cycle.
False: Does not synchronize the remote repository automatically.'  WHERE COLUMN_DEFINITION_ID = '10010309';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL  SET DESCRIPTION_EN = 'Select if the Remote Repository should be synchronized automatically or not.
True: Synchronizes with the remote repository with the input cycle.
False: Does not synchronize the remote repository automatically.'  WHERE COLUMN_DEFINITION_ID = '10010309';

