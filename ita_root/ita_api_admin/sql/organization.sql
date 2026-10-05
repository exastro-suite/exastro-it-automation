-- WorkspaceDB管理
CREATE TABLE IF NOT EXISTS T_COMN_WORKSPACE_DB_INFO
(
    PRIMARY_KEY                             VARCHAR(40),                        -- 主キー
    WORKSPACE_ID                            VARCHAR(255),                       -- workspaceのID
    DB_HOST                                 VARCHAR(255),                       -- ホスト
    DB_PORT                                 INT,                                -- ポート
    DB_DATABASE                             VARCHAR(255),                       -- DB名
    DB_USER                                 VARCHAR(255),                       -- ユーザ
    DB_PASSWORD                             VARCHAR(255),                       -- パスワード
    MONGO_CONNECTION_STRING                 VARCHAR(512),                       -- MONGOの接続用URL
    MONGO_DATABASE                          VARCHAR(255),                       -- MONGODB名
    MONGO_USER                              VARCHAR(255),                       -- MONGOユーザ
    MONGO_PASSWORD                          VARCHAR(255),                       -- MONGOパスワード
    NO_INSTALL_DRIVER                       LONGTEXT,                           -- インストールしていないドライバ名
    NOTE                                    TEXT,                               -- 備考
    DISUSE_FLAG                             VARCHAR(1)  ,                       -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP                   DATETIME(6),                        -- 最終更新日時
    LAST_UPDATE_USER                        VARCHAR(40),                        -- 最終更新者
    PRIMARY KEY(PRIMARY_KEY)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- インデックス
SET @exist := (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.STATISTICS
    WHERE table_schema = DATABASE()
        AND table_name   = 'T_COMN_WORKSPACE_DB_INFO'
        AND index_name   = 'IND_T_COMN_WORKSPACE_DB_INFO_01'
);
SET @sql := IF(@exist = 0,
    'CREATE INDEX IND_T_COMN_WORKSPACE_DB_INFO_01 ON T_COMN_WORKSPACE_DB_INFO (DISUSE_FLAG)',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;


