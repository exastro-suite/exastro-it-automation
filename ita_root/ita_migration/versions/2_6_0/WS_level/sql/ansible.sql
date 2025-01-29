ALTER TABLE T_ANSL_VALUE        MODIFY  VARS_ENTRY LONGTEXT;
ALTER TABLE T_ANSP_VALUE        MODIFY  VARS_ENTRY LONGTEXT;
ALTER TABLE T_ANSR_VALUE        MODIFY  VARS_ENTRY LONGTEXT;


-- 20113 グローバル変数（センシティブ）管理
CREATE TABLE T_ANSC_GLOBAL_VAR_SENSITIVE
(
    GBL_VARS_NAME_ID                VARCHAR(40),                                -- 項番
    VARS_NAME                       VARCHAR(255),                               -- グローバル変数名
    VARS_ENTRY                      TEXT,                                       -- 具体値
    VARS_DESCRIPTION                TEXT,                                       -- 変数名説明
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(GBL_VARS_NAME_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_ANSC_GLOBAL_VAR_SENSITIVE_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    GBL_VARS_NAME_ID                VARCHAR(40),                                -- 項番
    VARS_NAME                       VARCHAR(255),                               -- グローバル変数名
    VARS_ENTRY                      TEXT,                                       -- 具体値
    VARS_DESCRIPTION                TEXT,                                       -- 変数名説明
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE INDEX IND_T_ANSC_GLOBAL_VAR_SENSITIVE_01 ON T_ANSC_GLOBAL_VAR_SENSITIVE(DISUSE_FLAG);