-- メニュー-テーブル紐付管理
ALTER TABLE T_COMN_MENU_TABLE_LINK ADD COLUMN HOSTGROUP VARCHAR(2) AFTER VERTICAL;
ALTER TABLE T_COMN_MENU_TABLE_LINK_JNL ADD COLUMN HOSTGROUP VARCHAR(2) AFTER VERTICAL;


-- バージョン確認
DROP TABLE IF EXISTS T_COMN_VERSION;


-- Movement一覧
ALTER TABLE T_COMN_MOVEMENT ADD COLUMN TERE_WORKSPACE_ID VARCHAR(40) AFTER ANS_ANSIBLE_CONFIG_FILE;
ALTER TABLE T_COMN_MOVEMENT ADD COLUMN TERC_WORKSPACE_ID VARCHAR(40) AFTER TERE_WORKSPACE_ID;
ALTER TABLE T_COMN_MOVEMENT_JNL ADD COLUMN TERE_WORKSPACE_ID VARCHAR(40) AFTER ANS_ANSIBLE_CONFIG_FILE;
ALTER TABLE T_COMN_MOVEMENT_JNL ADD COLUMN TERC_WORKSPACE_ID VARCHAR(40) AFTER TERE_WORKSPACE_ID;


-- Webテーブル設定
CREATE TABLE IF NOT EXISTS T_COMN_WEB_TABLE_SETTINGS
(
    ROW_ID                          VARCHAR(40),                                -- UUID
    USER_ID                         VARCHAR(64),                                -- ユーザID
    WEB_TABLE_SETTINGS              LONGTEXT,                                   -- テーブル設定
    WIDGET_SETTINGS                 LONGTEXT,                                   -- ウィジェット設定
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    PRIMARY KEY(ROW_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- オペレーション削除管理
CREATE TABLE IF NOT EXISTS T_COMN_DEL_OPERATION_LIST
(
    ROW_ID                          VARCHAR(40),                                -- 項番
    LG_DAYS                         INT,                                        -- 論理削除日数
    PH_DAYS                         INT,                                        -- 物理削除日数
    MENU_NAME                       VARCHAR(40),                                -- メニューグループ：メニュー名
    DATA_STORAGE_PATH               VARCHAR(1024),                              -- データストレージパス
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ROW_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE IF NOT EXISTS T_COMN_DEL_OPERATION_LIST_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    ROW_ID                          VARCHAR(40),                                -- 項番
    LG_DAYS                         INT,                                        -- 論理削除日数
    PH_DAYS                         INT,                                        -- 物理削除日数
    MENU_NAME                       VARCHAR(40),                                -- メニューグループ：メニュー名
    DATA_STORAGE_PATH               VARCHAR(1024),                              -- データストレージパス
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- ファイル削除管理
CREATE TABLE IF NOT EXISTS T_COMN_DEL_FILE_LIST
(
    ROW_ID                          VARCHAR(40),                                -- 項番
    DEL_DAYS                        INT,                                        -- 削除日数
    TARGET_DIR                      VARCHAR(1024),                              -- 削除対象ディレクトリ
    TARGET_FILE                     VARCHAR(1024),                              -- 削除対象ファイル
    DEL_SUB_DIR_FLG                 VARCHAR(40),                                -- サブディレクトリ削除有無
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ROW_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE IF NOT EXISTS T_COMN_DEL_FILE_LIST_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    ROW_ID                          VARCHAR(40),                                -- 項番
    DEL_DAYS                        INT,                                        -- 削除日数
    TARGET_DIR                      VARCHAR(1024),                              -- 削除対象ディレクトリ
    TARGET_FILE                     VARCHAR(1024),                              -- 削除対象ファイル
    DEL_SUB_DIR_FLG                 VARCHAR(40),                                -- サブディレクトリ削除有無
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;


CREATE INDEX IND_T_COMN_MOVEMENT_02           ON T_COMN_MOVEMENT(MOVEMENT_NAME, ITA_EXT_STM_ID);
CREATE INDEX IND_T_COMN_MENU_03               ON T_COMN_MENU(MENU_NAME_REST, DISUSE_FLAG);
CREATE INDEX IND_T_COMN_SYSTEM_CONFIG_02      ON T_COMN_SYSTEM_CONFIG(CONFIG_ID);
