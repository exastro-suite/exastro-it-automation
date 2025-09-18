-- -----------------------------------------------------------------------------
-- - ▼Issue #2814 URLの項目長を拡張
-- -----------------------------------------------------------------------------
UPDATE T_COMN_MENU_COLUMN_LINK      SET VALIDATE_OPTION = NULL, DESCRIPTION_JA = 'git cloneコマンドに指定するクローン元のリポジトリを入力してください。', DESCRIPTION_EN = 'Enter the repository you want to clone from for the git clone command.'  WHERE COLUMN_DEFINITION_ID = '10010103';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL  SET VALIDATE_OPTION = NULL, DESCRIPTION_JA = 'git cloneコマンドに指定するクローン元のリポジトリを入力してください。', DESCRIPTION_EN = 'Enter the repository you want to clone from for the git clone command.'  WHERE COLUMN_DEFINITION_ID = '10010103';
UPDATE T_COMN_MENU_COLUMN_LINK      SET VALIDATE_OPTION = NULL, DESCRIPTION_JA = 'Proxyサーバを利用する場合、Proxyサーバのアドレスを入力して下さい。', DESCRIPTION_EN = 'If you are using a Proxy server, please enter the Proxy server address.'  WHERE COLUMN_DEFINITION_ID = '10010112';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL  SET VALIDATE_OPTION = NULL, DESCRIPTION_JA = 'Proxyサーバを利用する場合、Proxyサーバのアドレスを入力して下さい。', DESCRIPTION_EN = 'If you are using a Proxy server, please enter the Proxy server address.'  WHERE COLUMN_DEFINITION_ID = '10010112';
