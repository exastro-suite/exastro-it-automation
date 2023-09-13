-- ------------------------------------------------------------
-- ▼TABLE INSERT START
-- ------------------------------------------------------------
-- パラメータ集検索条件情報 追加
CREATE TABLE T_MENU_COLLECTION_FILTER_DATA
(
    UUID                            VARCHAR(40),                                -- 項番
    FILTER_NAME                     VARCHAR(255),                               -- 検索条件名
    FILTER_JSON                     LONGTEXT,                                   -- 検索条件内容
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(UUID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

-- ------------------------------------------------------------
-- ▲ TABLE UPDATE END
-- ------------------------------------------------------------