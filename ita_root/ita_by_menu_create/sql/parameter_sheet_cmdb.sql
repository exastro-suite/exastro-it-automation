DROP TABLE IF EXISTS `____CMDB_TABLE_NAME____`;
DROP TABLE IF EXISTS `____CMDB_TABLE_NAME_JNL____`;

-- ----テーブル作成
CREATE TABLE `____CMDB_TABLE_NAME____`
(
    ROW_ID                  VARCHAR(40),
    HOST_ID                 VARCHAR(40),
    OPERATION_ID            VARCHAR(40),
    DATA_JSON               LONGTEXT,
    NOTE                    TEXT,
    DISUSE_FLAG             VARCHAR(1),
    LAST_UPDATE_TIMESTAMP   DATETIME(6),
    LAST_UPDATE_USER        VARCHAR(40),
    PRIMARY KEY(ROW_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

-- ----履歴テーブル作成
CREATE TABLE `____CMDB_TABLE_NAME_JNL____`
(
    JOURNAL_SEQ_NO          VARCHAR(40),
    JOURNAL_REG_DATETIME    DATETIME(6),
    JOURNAL_ACTION_CLASS    VARCHAR(8),
    ROW_ID                  VARCHAR(40),
    HOST_ID                 VARCHAR(40),
    OPERATION_ID            VARCHAR(40),
    DATA_JSON               LONGTEXT,
    NOTE                    TEXT,
    DISUSE_FLAG             VARCHAR(1),
    LAST_UPDATE_TIMESTAMP   DATETIME(6),
    LAST_UPDATE_USER        VARCHAR(40),
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

-- ----VIEW作成
CREATE OR REPLACE VIEW `____CMDB_VIEW_NAME____` AS
SELECT
    TAB_A.ROW_ID,
    TAB_A.HOST_ID,
    TAB_A.OPERATION_ID,
    TAB_B.BASE_TIMESTAMP,
    TAB_B.LAST_EXECUTE_TIMESTAMP,
    TAB_A.OPERATION_ID as OPERATION_NAME,
    TAB_B.OPERATION_DATE,
    TAB_A.DATA_JSON,
    TAB_A.NOTE,
    TAB_A.DISUSE_FLAG,
    TAB_A.LAST_UPDATE_TIMESTAMP,
    TAB_A.LAST_UPDATE_USER
FROM `____CMDB_TABLE_NAME____` TAB_A
LEFT JOIN V_COMN_OPERATION TAB_B
ON (TAB_A.OPERATION_ID = TAB_B.OPERATION_ID AND TAB_B.DISUSE_FLAG = '0');

-- ----履歴VIEW作成
CREATE OR REPLACE VIEW `____CMDB_VIEW_NAME_JNL____` AS
SELECT
    TAB_A.JOURNAL_SEQ_NO,
    TAB_A.JOURNAL_REG_DATETIME,
    TAB_A.JOURNAL_ACTION_CLASS,
    TAB_A.ROW_ID,
    TAB_A.HOST_ID,
    TAB_A.OPERATION_ID,
    TAB_B.BASE_TIMESTAMP,
    TAB_B.LAST_EXECUTE_TIMESTAMP,
    TAB_A.OPERATION_ID as OPERATION_NAME,
    TAB_B.OPERATION_DATE,
    TAB_A.DATA_JSON,
    TAB_A.NOTE,
    TAB_A.DISUSE_FLAG,
    TAB_A.LAST_UPDATE_TIMESTAMP,
    TAB_A.LAST_UPDATE_USER
FROM `____CMDB_TABLE_NAME_JNL____` TAB_A
LEFT JOIN V_COMN_OPERATION TAB_B
ON (TAB_A.OPERATION_ID = TAB_B.OPERATION_ID AND TAB_B.DISUSE_FLAG = '0');

-- ----INDEX
CREATE INDEX `IND_____CMDB_TABLE_NAME_____01` ON `____CMDB_TABLE_NAME____` (DISUSE_FLAG);
