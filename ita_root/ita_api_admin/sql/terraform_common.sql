-- Terraformステータスマスタ
CREATE TABLE T_TERF_EXEC_STATUS
(
    EXEC_STATUS_ID                  VARCHAR(2),                                 -- UUID
    EXEC_STATUS_NAME_JA             VARCHAR(256),                               -- 実行状態名(ja)
    EXEC_STATUS_NAME_EN             VARCHAR(256),                               -- 実行状態名(en)
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            VARCHAR(4000),                              -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(EXEC_STATUS_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- Terraform実行種別マスタ
CREATE TABLE T_TERF_EXEC_MODE
(
    EXEC_MODE_ID                    VARCHAR(2),                                 -- UUID
    EXEC_MODE_NAME_JA               VARCHAR(256),                               -- 実行モード名(ja)
    EXEC_MODE_NAME_EN               VARCHAR(256),                               -- 実行モード名(en)
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            VARCHAR(4000),                              -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(EXEC_MODE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- Terraformタイプマスタ
CREATE TABLE T_TERF_TYPE_MASTER
(
    TYPE_ID                         VARCHAR(2),                                 -- UUID
    TYPE_NAME                       VARCHAR(256),                               -- タイプ名
    MEMBER_VARS_FLAG                VARCHAR(1),                                 -- メンバー変数フラグ
    ASSIGN_SEQ_FLAG                 VARCHAR(1),                                 -- 代入順序フラグ
    ENCODE_FLAG                     VARCHAR(1),                                 -- エンコードフラグ
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            VARCHAR(4000),                              -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(TYPE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- 登録方式
CREATE TABLE T_TERF_AUTOREG_REG_TYPE
(
    TYPE_ID                         VARCHAR(2),                                 -- UUID
    TYPE_NAME_JA                    VARCHAR(256),                               -- タイプ名(日本語)
    TYPE_NAME_EN                    VARCHAR(256),                               -- タイプ名(英語)
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            VARCHAR(4000),                              -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(TYPE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




