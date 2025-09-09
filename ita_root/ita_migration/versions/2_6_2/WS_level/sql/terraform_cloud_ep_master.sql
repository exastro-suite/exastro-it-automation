-- -----------------------------------------------------------------------------
-- - ▼Issue #2814 URLの項目長を拡張
-- -----------------------------------------------------------------------------
UPDATE T_COMN_MENU_COLUMN_LINK      SET VALIDATE_OPTION = NULL, DESCRIPTION_JA = 'プロキシサーバのアドレス', DESCRIPTION_EN = 'Proxy server address'  WHERE COLUMN_DEFINITION_ID = '8010106';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL  SET VALIDATE_OPTION = NULL, DESCRIPTION_JA = 'プロキシサーバのアドレス', DESCRIPTION_EN = 'Proxy server address'  WHERE COLUMN_DEFINITION_ID = '8010106';
