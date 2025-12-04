-- -----------------------------------------------------------------------------
-- - ▼Issue 行末の空白調整
-- -----------------------------------------------------------------------------
UPDATE T_COMN_MENU_TABLE_LINK      SET MENU_INFO_EN = 'You can perform maintenance (view/update) for connection interface information.
This menu should be one record.'  WHERE TABLE_DEFINITION_ID = '90101';
UPDATE T_COMN_MENU_TABLE_LINK_JNL   SET MENU_INFO_EN = 'You can perform maintenance (view/update) for connection interface information.
This menu should be one record.'  WHERE TABLE_DEFINITION_ID = '90101';

UPDATE T_COMN_MENU_TABLE_LINK      SET MENU_INFO_EN = 'You can perform maintenance (view/register/update/discard) for operations registered in the associated menu, and Movement and variables associated with the setting value of item.

There are two methods to register the setting value of item.
Value type: Setting value of item is registered in the substitution value list as a specific value of associated variable.
Key type: Item name is registered in the substitution value list as a specific value of associated variable. '  WHERE TABLE_DEFINITION_ID = '90107';
UPDATE T_COMN_MENU_TABLE_LINK_JNL   SET MENU_INFO_EN = 'You can perform maintenance (view/register/update/discard) for operations registered in the associated menu, and Movement and variables associated with the setting value of item.

There are two methods to register the setting value of item.
Value type: Setting value of item is registered in the substitution value list as a specific value of associated variable.
Key type: Item name is registered in the substitution value list as a specific value of associated variable. '  WHERE TABLE_DEFINITION_ID = '90107';

UPDATE T_COMN_MENU_TABLE_LINK      SET MENU_INFO_EN = 'The following Stand alone Movement executions are possible.
・Immediate execution
・Scheduled execution
Select Movement and Operation ID to execute.'  WHERE TABLE_DEFINITION_ID = '90108';
UPDATE T_COMN_MENU_TABLE_LINK_JNL   SET MENU_INFO_EN = 'The following Stand alone Movement executions are possible.
・Immediate execution
・Scheduled execution
Select Movement and Operation ID to execute.'  WHERE TABLE_DEFINITION_ID = '90108';
