-- ------------------------------------------------------------
-- ▼TABLE UPDATE START
-- ------------------------------------------------------------
-- 20102 インターフェース情報: REST APIタイムアウト値(単位 秒) 追加
ALTER TABLE T_ANSC_IF_INFO     ADD COLUMN ANSTWR_REST_TIMEOUT INT  AFTER ANSTWR_DEL_RUNTIME_DATA;
ALTER TABLE T_ANSC_IF_INFO_JNL ADD COLUMN ANSTWR_REST_TIMEOUT INT  AFTER ANSTWR_DEL_RUNTIME_DATA;
UPDATE T_ANSC_IF_INFO SET ANSTWR_REST_TIMEOUT = 60;
UPDATE T_ANSC_IF_INFO_JNL SET ANSTWR_REST_TIMEOUT = 60;
-- ------------------------------------------------------------
-- ▲ TABLE UPDATE END
-- ------------------------------------------------------------
