-- ログレベル管理
CREATE TABLE IF NOT EXISTS T_COMN_LOGLEVEL
(
    PRIMARY_KEY                     VARCHAR(40),                                -- 主キー
    SERVICE_NAME                    VARCHAR(255),                               -- サービス名
    LOG_LEVEL                       VARCHAR(255),                               -- ログレベル
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(PRIMARY_KEY)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;


-- バージョン情報
CREATE TABLE IF NOT EXISTS T_COMN_VERSION
(
    SERVICE_ID                      VARCHAR(40),                                -- UUID
    VERSION                         VARCHAR(32),                                -- バージョン
    INSTALLED_DRIVER_JA             TEXT,                                       -- インストール済ドライバ(ja)
    INSTALLED_DRIVER_EN             TEXT,                                       -- インストール済ドライバ(en)
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(SERVICE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;


-- インデックス
CREATE INDEX IND_T_COMN_LOGLEVEL_01 ON T_COMN_LOGLEVEL (SERVICE_NAME);
CREATE INDEX IND_T_COMN_LOGLEVEL_02 ON T_COMN_LOGLEVEL (DISUSE_FLAG);
