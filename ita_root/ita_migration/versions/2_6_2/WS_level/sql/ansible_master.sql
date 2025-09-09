-- -----------------------------------------------------------------------------
-- - ▼Issue #2814 URLの項目長を拡張
-- -----------------------------------------------------------------------------
UPDATE T_COMN_MENU_COLUMN_LINK      SET VALIDATE_OPTION = NULL  WHERE COLUMN_DEFINITION_ID = '2010209';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL  SET VALIDATE_OPTION = NULL  WHERE COLUMN_DEFINITION_ID = '2010209';
