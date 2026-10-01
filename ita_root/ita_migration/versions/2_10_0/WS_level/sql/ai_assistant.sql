-- 添付ファイル
CREATE TABLE IF NOT EXISTS T_AI_ATTACHMENT_FILE
(
    UUID                            VARCHAR(40),                                -- UUID
    FILE_ID                         VARCHAR(50),                                -- FILE_ID
    SEQ_NO                          INT,                                        -- 連番
    FILE_NAME                       VARCHAR(255),                               -- ファイル名
    MIME_TYPE                       VARCHAR(255),                               -- Mime Type
    FILE_SIZE                       BIGINT,                                     -- サイズ
    FILE_DATA                       MEDIUMBLOB,                                 -- ファイルデータ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(UUID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- インデックス
--
-- IND_T_AI_ATTACHMENT_FILE_01
SET @exist := (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.STATISTICS
    WHERE table_schema = DATABASE()
        AND table_name   = 'T_AI_ATTACHMENT_FILE'
        AND index_name   = 'IND_T_AI_ATTACHMENT_FILE_01'
);
SET @sql := IF(@exist = 0,
    'CREATE UNIQUE INDEX IND_T_AI_ATTACHMENT_FILE_01 ON T_AI_ATTACHMENT_FILE(LAST_UPDATE_USER,FILE_ID,SEQ_NO)',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
--
-- IND_T_AI_ATTACHMENT_FILE_02
SET @exist := (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.STATISTICS
    WHERE table_schema = DATABASE()
        AND table_name   = 'T_AI_ATTACHMENT_FILE'
        AND index_name   = 'IND_T_AI_ATTACHMENT_FILE_02'
);
SET @sql := IF(@exist = 0,
    'CREATE INDEX IND_T_AI_ATTACHMENT_FILE_02 ON T_AI_ATTACHMENT_FILE(LAST_UPDATE_TIMESTAMP)',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;



