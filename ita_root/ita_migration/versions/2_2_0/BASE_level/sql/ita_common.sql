-- メンテナンスモード設定値管理
CREATE TABLE IF NOT EXISTS T_COMN_MAINTENANCE_MODE
(
    MAINTENANCE_ID                  VARCHAR(40),                                -- 主キー
    MODE_NAME                       VARCHAR(255),                               -- メンテナンスモード名
    SETTING_VALUE                   VARCHAR(255),                               -- 設定値
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(MAINTENANCE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;
