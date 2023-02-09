-- メニューエクスポート・インポート管理
CREATE TABLE T_MENU_EXPORT_IMPORT
(
    EXECUTION_NO                    VARCHAR(40),                                -- 実行No.
    STATUS                          VARCHAR(40),                                -- ステータス
    EXECUTION_TYPE                  VARCHAR(40),                                -- 処理種別
    MODE                            VARCHAR(40),                                -- モード
    ABOLISHED_TYPE                  VARCHAR(40),                                -- 廃止情報
    SPECIFIED_TIME                  DATETIME(6)  ,                              -- 指定時刻
    FILE_NAME                       VARCHAR(64),                                -- ファイル名
    EXECUTION_USER                  VARCHAR(255),                               -- 実行ユーザ
    JSON_STORAGE_ITEM               LONGTEXT,                                   -- JSON格納用項目
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(EXECUTION_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_MENU_EXPORT_IMPORT_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    EXECUTION_NO                    VARCHAR(40),                                -- 実行No.
    STATUS                          VARCHAR(40),                                -- ステータス
    EXECUTION_TYPE                  VARCHAR(40),                                -- 処理種別
    MODE                            VARCHAR(40),                                -- モード
    ABOLISHED_TYPE                  VARCHAR(40),                                -- 廃止情報
    SPECIFIED_TIME                  DATETIME(6)  ,                              -- 指定時刻
    FILE_NAME                       VARCHAR(64),                                -- ファイル名
    EXECUTION_USER                  VARCHAR(255),                               -- 実行ユーザ
    JSON_STORAGE_ITEM               LONGTEXT,                                   -- JSON格納用項目
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- Excel一括エクスポート・インポート管理
CREATE TABLE T_BULK_EXCEL_EXPORT_IMPORT
(
    EXECUTION_NO                    VARCHAR(40),                                -- 実行No.
    STATUS                          VARCHAR(40),                                -- ステータス
    EXECUTION_TYPE                  VARCHAR(40),                                -- 処理種別
    ABOLISHED_TYPE                  VARCHAR(40),                                -- 廃止情報
    EXECUTION_USER                  VARCHAR(255),                               -- 実行ユーザ
    FILE_NAME                       VARCHAR(64),                                -- ファイル名
    LANGUAGE                        VARCHAR(40),                                -- 言語
    RESULT_FILE                     VARCHAR(64),                                -- 結果
    JSON_STORAGE_ITEM               LONGTEXT,                                   -- JSON格納用項目
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(EXECUTION_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_BULK_EXCEL_EXPORT_IMPORT_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    EXECUTION_NO                    VARCHAR(40),                                -- 実行No.
    STATUS                          VARCHAR(40),                                -- ステータス
    EXECUTION_TYPE                  VARCHAR(40),                                -- 処理種別
    ABOLISHED_TYPE                  VARCHAR(40),                                -- 廃止情報
    EXECUTION_USER                  VARCHAR(255),                               -- 実行ユーザ
    FILE_NAME                       VARCHAR(64),                                -- ファイル名
    LANGUAGE                        VARCHAR(40),                                -- 言語
    RESULT_FILE                     VARCHAR(64),                                -- 結果
    JSON_STORAGE_ITEM               LONGTEXT,                                   -- JSON格納用項目
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 非表示メニュー
CREATE TABLE T_DP_HIDE_MENU_LIST
(
    HIDE_ID                         VARCHAR(40),                                -- 識別シーケンス
    MENU_ID                         VARCHAR(40),                                -- メニューID
    PRIMARY KEY(HIDE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- ステータスマスタ
CREATE TABLE T_DP_STATUS_MASTER
(
    ROW_ID                          VARCHAR(2),                                 -- 主キー
    TASK_STATUS_NAME_JA             VARCHAR(255),                               -- 形式名(ja)
    TASK_STATUS_NAME_EN             VARCHAR(255),                               -- 形式名(en)
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ROW_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- 処理種別マスタ
CREATE TABLE T_DP_EXECUTION_TYPE
(
    ROW_ID                          VARCHAR(2),                                 -- 主キー
    EXECUTION_TYPE_NAME_JA          VARCHAR(255),                               -- 形式名(ja)
    EXECUTION_TYPE_NAME_EN          VARCHAR(255),                               -- 形式名(en)
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ROW_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- モードマスタ
CREATE TABLE T_DP_MODE
(
    ROW_ID                          VARCHAR(2),                                 -- 主キー
    MODE_NAME_JA                    VARCHAR(255),                               -- 形式名(ja)
    MODE_NAME_EN                    VARCHAR(255),                               -- 形式名(en)
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ROW_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- 廃止情報マスタ
CREATE TABLE T_DP_ABOLISHED_TYPE
(
    ROW_ID                          VARCHAR(2),                                 -- 主キー
    ABOLISHED_TYPE_NAME_JA          VARCHAR(255),                               -- 形式名(ja)
    ABOLISHED_TYPE_NAME_EN          VARCHAR(255),                               -- 形式名(en)
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ROW_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




