-- Issue 3029: インターフェース情報にサービスアカウント情報格納用のカラム追加
-- T_ANSC_IF_INFO テーブルへのカラム追加
ALTER TABLE T_ANSC_IF_INFO ADD COLUMN SERVICE_ACCOUNT_INFO LONGTEXT AFTER ANSIBLE_TAILLOG_LINES;
ALTER TABLE T_ANSC_IF_INFO ADD COLUMN SERVICE_ACCOUNT_TOKEN TEXT AFTER SERVICE_ACCOUNT_INFO;
-- T_ANSC_IF_INFO_JNL テーブルへのカラム追加
ALTER TABLE T_ANSC_IF_INFO_JNL ADD COLUMN SERVICE_ACCOUNT_INFO LONGTEXT  AFTER ANSIBLE_TAILLOG_LINES;
ALTER TABLE T_ANSC_IF_INFO_JNL ADD COLUMN SERVICE_ACCOUNT_TOKEN TEXT AFTER SERVICE_ACCOUNT_INFO;


-- Issue 3029: AAP(Cloud)連携用資材の管理テーブルを追加する
-- 20214 AAP(Cloud)連携用資材
CREATE TABLE T_ANSC_AAP_CLOUD_LINK_ASSETS
(
    ROW_ID                          VARCHAR(40),                                -- 項番
    ASSET_NAME                      VARCHAR(255),                               -- 資材名
    ASSET_FILE                      VARCHAR(255),                               -- 資材ファイル
    DESCRIPTION                     TEXT,                                       -- 説明
    DESCRIPTION_EN                  TEXT,                                       -- 説明(en)
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ROW_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_ANSC_AAP_CLOUD_LINK_ASSETS_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    ROW_ID                          VARCHAR(40),                                -- 項番
    ASSET_NAME                      VARCHAR(255),                               -- 資材名
    ASSET_FILE                      VARCHAR(255),                               -- 資材ファイル
    DESCRIPTION                     TEXT,                                       -- 説明
    DESCRIPTION_EN                  TEXT,                                       -- 説明(en)
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

-- Issue 3029: AAP(Cloud)連携用資材の管理テーブルのインデックス追加
CREATE INDEX IND_T_ANSC_AAP_CLOUD_LINK_ASSETS_01 ON T_ANSC_AAP_CLOUD_LINK_ASSETS (DISUSE_FLAG);
CREATE INDEX IND_T_ANSC_AAP_CLOUD_LINK_ASSETS_02 ON T_ANSC_AAP_CLOUD_LINK_ASSETS (ASSET_NAME);
CREATE INDEX IND_T_ANSC_AAP_CLOUD_LINK_ASSETS_JNL_01 ON T_ANSC_AAP_CLOUD_LINK_ASSETS_JNL (ROW_ID);

