-- 重複排除
CREATE TABLE IF NOT EXISTS T_OASE_DEDUPLICATION_SETTINGS
(
    DEDUPLICATION_SETTING_ID        VARCHAR(40),                                -- 重複排除設定ID
    DEDUPLICATION_SETTING_NAME      VARCHAR(255),                               -- 重複排除設定名
    SETTING_PRIORITY                INT,                                        -- 優先順位
    EVENT_SOURCE_REDUNDANCY_GROUP   TEXT,                                       -- 冗長グループ（イベント収集先）
    CONDITION_LABEL_KEY_IDS         TEXT,                                       -- ラベル
    CONDITION_EXPRESSION_ID         VARCHAR(2),                                 -- 式
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(DEDUPLICATION_SETTING_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE IF NOT EXISTS T_OASE_DEDUPLICATION_SETTINGS_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    DEDUPLICATION_SETTING_ID        VARCHAR(40),                                -- 重複排除設定ID
    DEDUPLICATION_SETTING_NAME      VARCHAR(255),                               -- 重複排除設定名
    SETTING_PRIORITY                INT,                                        -- 優先順位
    EVENT_SOURCE_REDUNDANCY_GROUP   TEXT,                                       -- 冗長グループ（イベント収集先）
    CONDITION_LABEL_KEY_IDS         TEXT,                                       -- ラベル
    CONDITION_EXPRESSION_ID         VARCHAR(2),                                 -- 式
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

-- 重複排除条件式マスタ
CREATE TABLE IF NOT EXISTS T_OASE_DEDUPLICATION_CONDITION_EXPRESSION
(
    EXPRESSION_ID                   VARCHAR(2),                                 -- 条件式ID
    EXPRESSION_JA                   VARCHAR(255),                               -- 条件式（JA）
    EXPRESSION_EN                   VARCHAR(255),                               -- 条件式（EN）
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(EXPRESSION_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

-- フィルターグルーピング条件マスタ
CREATE TABLE IF NOT EXISTS T_OASE_FILTER_GROUP_CONDITION
(
    GROUP_CONDITION_ID              VARCHAR(2),                                 -- グルーピング条件ID
    GROUP_CONDITION_JA              VARCHAR(255),                               -- グルーピング条件名（JA）
    GROUP_CONDITION_EN              VARCHAR(255),                               -- グルーピング条件名（EN）
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(GROUP_CONDITION_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

-- イベント種別と通知先の組み合わせごとにテンプレートを管理できる機能追加対応
ALTER TABLE T_OASE_NOTIFICATION_TEMPLATE_COMMON ADD COLUMN NOTIFICATION_DESTINATION TEXT AFTER TEMPLATE_FILE;
ALTER TABLE T_OASE_NOTIFICATION_TEMPLATE_COMMON ADD COLUMN IS_DEFAULT VARCHAR(10) AFTER NOTIFICATION_DESTINATION;
ALTER TABLE T_OASE_NOTIFICATION_TEMPLATE_COMMON_JNL ADD COLUMN NOTIFICATION_DESTINATION TEXT AFTER TEMPLATE_FILE;
ALTER TABLE T_OASE_NOTIFICATION_TEMPLATE_COMMON_JNL ADD COLUMN IS_DEFAULT VARCHAR(10) AFTER NOTIFICATION_DESTINATION;

-- フィルタ：グルーピング条件項目の追加
ALTER TABLE T_OASE_FILTER ADD COLUMN GROUP_LABEL_KEY_IDS        TEXT        AFTER SEARCH_CONDITION_ID;
ALTER TABLE T_OASE_FILTER ADD COLUMN GROUP_CONDITION_ID         VARCHAR(2)  AFTER GROUP_LABEL_KEY_IDS;
ALTER TABLE T_OASE_FILTER_JNL ADD COLUMN GROUP_LABEL_KEY_IDS    TEXT        AFTER SEARCH_CONDITION_ID;
ALTER TABLE T_OASE_FILTER_JNL ADD COLUMN GROUP_CONDITION_ID     VARCHAR(2)  AFTER GROUP_LABEL_KEY_IDS;