-- ------------------------------------------------------------
-- T_MENU_EXPORT_IMPORT: ALTER
-- ------------------------------------------------------------
ALTER TABLE `T_MENU_EXPORT_IMPORT` ADD `JOURNAL_TYPE`  VARCHAR(40) DEFAULT NULL AFTER `ABOLISHED_TYPE`;
ALTER TABLE `T_MENU_EXPORT_IMPORT_JNL` ADD `JOURNAL_TYPE` VARCHAR(40) DEFAULT NULL AFTER `ABOLISHED_TYPE`;


-- ------------------------------------------------------------
-- T_DP_JOURNAL_TYPE: CREATE
-- ------------------------------------------------------------
-- 履歴情報マスタ
CREATE TABLE T_DP_JOURNAL_TYPE
(
    ROW_ID                          VARCHAR(2),                                 -- 主キー
    JOURNAL_TYPE_NAME_JA            VARCHAR(255),                               -- 形式名(ja)
    JOURNAL_TYPE_NAME_EN            VARCHAR(255),                               -- 形式名(en)
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ROW_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

