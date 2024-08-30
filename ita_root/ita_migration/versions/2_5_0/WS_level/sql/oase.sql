-- ------------------------------------------------------------
-- T_OASE_EVENT_TYPE: CREATE
-- ------------------------------------------------------------
-- イベント種別マスタ
CREATE TABLE T_OASE_EVENT_TYPE
(
    EVENT_TYPE_ID                   VARCHAR(2),                                 -- イベント種別ID
    EVENT_TYPE_NAME_JA              VARCHAR(255),                               -- イベント種別(ja)
    EVENT_TYPE_NAME_EN              VARCHAR(255),                               -- イベント種別(en)
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(EVENT_TYPE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;


-- ------------------------------------------------------------
-- T_OASE_EVENT_STATUS: CREATE
-- ------------------------------------------------------------
-- イベント状態マスタ
CREATE TABLE T_OASE_EVENT_STATUS
(
    EVENT_STATUS_ID                 VARCHAR(2),                                 -- イベント状態ID
    EVENT_STATUS_NAME_JA            VARCHAR(255),                               -- イベント状態(ja)
    EVENT_STATUS_NAME_EN            VARCHAR(255),                               -- イベント状態(en)
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(EVENT_STATUS_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;


-- ------------------------------------------------------------
-- T_OASE_EVENT: CREATE
-- ------------------------------------------------------------
-- イベントマスタ
CREATE TABLE T_OASE_EVENT
(
    EVENT_ID                        VARCHAR(2),                                 -- イベントID
    EVENT_NAME_JA                   VARCHAR(255),                               -- イベント(ja)
    EVENT_NAME_EN                   VARCHAR(255),                               -- イベント(en)
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(EVENT_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;


-- ------------------------------------------------------------
-- T_OASE_NOTIFICATION_TEMPLATE_COMMON: ALTER
-- ------------------------------------------------------------
ALTER TABLE T_OASE_NOTIFICATION_TEMPLATE_COMMON MODIFY NOTIFICATION_TEMPLATE_ID VARCHAR(40);
ALTER TABLE T_OASE_NOTIFICATION_TEMPLATE_COMMON_JNL MODIFY NOTIFICATION_TEMPLATE_ID VARCHAR(40);
