-- ------------------------------------------------------------
-- ▼TABLE UPDATE START
-- ------------------------------------------------------------
-- 20102 インターフェース情報: REST APIタイムアウト値(単位 秒) 追加
ALTER TABLE T_ANSC_IF_INFO     ADD COLUMN ANSTWR_REST_TIMEOUT INT  AFTER ANSTWR_DEL_RUNTIME_DATA;
ALTER TABLE T_ANSC_IF_INFO_JNL ADD COLUMN ANSTWR_REST_TIMEOUT INT  AFTER ANSTWR_DEL_RUNTIME_DATA;
-- ------------------------------------------------------------
-- ▲ TABLE UPDATE END
-- ------------------------------------------------------------
