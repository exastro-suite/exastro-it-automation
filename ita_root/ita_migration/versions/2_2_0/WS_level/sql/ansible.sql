-- ------------------------------------------------------------
-- ▼TABLE UPDATE START
-- ------------------------------------------------------------
-- 20102 AACホスト一覧: ポート番号 追加 
ALTER TABLE T_ANSC_TOWER_HOST     ADD COLUMN ANSTWR_PORT INT  AFTER ANSTWR_LOGIN_SSH_KEY_FILE_PASS;
ALTER TABLE T_ANSC_TOWER_HOST_JNL ADD COLUMN ANSTWR_PORT INT  AFTER ANSTWR_LOGIN_SSH_KEY_FILE_PASS;

-- ------------------------------------------------------------
-- ▲ TABLE UPDATE END
-- ------------------------------------------------------------
