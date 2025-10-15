-- 検索方法マスタ
CREATE TABLE IF NOT EXISTS T_OASE_SEARCH_CONDITION
(
    SEARCH_CONDITION_ID             VARCHAR(2),                                 -- 検索方法ID
    SEARCH_CONDITION_NAME_EN        VARCHAR(255),                               -- 検索方法名(en)
    SEARCH_CONDITION_NAME_JA        VARCHAR(255),                               -- 検索方法名(ja)
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(SEARCH_CONDITION_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- 接続方式マスタ
CREATE TABLE IF NOT EXISTS T_OASE_CONNECTION_METHOD
(
    CONNECTION_METHOD_ID            VARCHAR(2),                                 -- 接続方式ID
    CONNECTION_METHOD_NAME_EN       VARCHAR(255),                               -- 接続方式名(en)
    CONNECTION_METHOD_NAME_JA       VARCHAR(255),                               -- 接続方式名(ja)
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(CONNECTION_METHOD_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- リクエストメソッドマスタ
CREATE TABLE IF NOT EXISTS T_OASE_REQUEST_METHOD
(
    REQUEST_METHOD_ID               VARCHAR(2),                                 -- リクエストメソッドID
    REQUEST_METHOD_NAME             VARCHAR(255),                               -- リクエストメソッド名
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(REQUEST_METHOD_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- イベント収集設定
CREATE TABLE IF NOT EXISTS T_OASE_EVENT_COLLECTION_SETTINGS
(
    EVENT_COLLECTION_SETTINGS_ID    VARCHAR(40),                                -- イベント収集ID
    EVENT_COLLECTION_SETTINGS_NAME  VARCHAR(255),                               -- イベント収集名
    CONNECTION_METHOD_ID            VARCHAR(2),                                 -- 接続方式ID
    REQUEST_METHOD_ID               VARCHAR(2),                                 -- リクエストメソッドID
    URL                             VARCHAR(4096),                              -- 接続先
    PORT                            INT,                                        -- ポート
    REQUEST_HEADER                  TEXT,                                       -- リクエストヘッダー
    PROXY                           VARCHAR(4096),                              -- プロキシ
    AUTH_TOKEN                      VARCHAR(4096),                              -- 認証トークン
    USERNAME                        VARCHAR(255),                               -- ユーザー名
    PASSWORD                        TEXT,                                       -- パスワード
    MAILBOXNAME                     VARCHAR(255),                               -- メールボックス名
    ACCESS_KEY_ID                   VARCHAR(1024),                              -- アクセスキーID
    SECRET_ACCESS_KEY               TEXT,                                       -- 秘密アクセスキー
    PARAMETER                       TEXT,                                       -- パラメータ
    RESPONSE_LIST_FLAG              VARCHAR(2),                                 -- レスポンスリストフラグ
    RESPONSE_KEY                    VARCHAR(255),                               -- レスポンスキー
    EVENT_ID_KEY                    VARCHAR(255),                               -- イベントIDキー
    TTL                             INT,                                        -- TTL
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(EVENT_COLLECTION_SETTINGS_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE IF NOT EXISTS T_OASE_EVENT_COLLECTION_SETTINGS_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    EVENT_COLLECTION_SETTINGS_ID    VARCHAR(40),                                -- イベント収集ID
    EVENT_COLLECTION_SETTINGS_NAME  VARCHAR(255),                               -- イベント収集名
    CONNECTION_METHOD_ID            VARCHAR(2),                                 -- 接続方式ID
    REQUEST_METHOD_ID               VARCHAR(2),                                 -- リクエストメソッドID
    URL                             VARCHAR(4096),                              -- 接続先
    PORT                            INT,                                        -- ポート
    REQUEST_HEADER                  TEXT,                                       -- リクエストヘッダー
    PROXY                           VARCHAR(4096),                              -- プロキシ
    AUTH_TOKEN                      VARCHAR(4096),                              -- 認証トークン
    USERNAME                        VARCHAR(255),                               -- ユーザー名
    PASSWORD                        TEXT,                                       -- パスワード
    MAILBOXNAME                     VARCHAR(255),                               -- メールボックス名
    ACCESS_KEY_ID                   VARCHAR(1024),                              -- アクセスキーID
    SECRET_ACCESS_KEY               TEXT,                                       -- 秘密アクセスキー
    PARAMETER                       TEXT,                                       -- パラメータ
    RESPONSE_LIST_FLAG              VARCHAR(2),                                 -- レスポンスリストフラグ
    RESPONSE_KEY                    VARCHAR(255),                               -- レスポンスキー
    EVENT_ID_KEY                    VARCHAR(255),                               -- イベントIDキー
    TTL                             INT,                                        -- TTL
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- イベント種別マスタ
CREATE TABLE IF NOT EXISTS T_OASE_EVENT_TYPE
(
    EVENT_TYPE_ID                   VARCHAR(255),                               -- イベント種別ID
    EVENT_TYPE_NAME_JA              VARCHAR(255),                               -- イベント種別(ja)
    EVENT_TYPE_NAME_EN              VARCHAR(255),                               -- イベント種別(en)
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(EVENT_TYPE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- 通知テンプレート(共通)
CREATE TABLE IF NOT EXISTS T_OASE_NOTIFICATION_TEMPLATE_COMMON
(
    NOTIFICATION_TEMPLATE_ID        VARCHAR(40),                                -- 通知テンプレートID
    EVENT_TYPE                      VARCHAR(255),                               -- イベント種別
    TEMPLATE_FILE                   VARCHAR(255),                               -- テンプレート
    NOTIFICATION_DESTINATION        TEXT,                                       -- 通知先
    IS_DEFAULT                      VARCHAR(10)  ,                              -- デフォルト
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(NOTIFICATION_TEMPLATE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE IF NOT EXISTS T_OASE_NOTIFICATION_TEMPLATE_COMMON_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    NOTIFICATION_TEMPLATE_ID        VARCHAR(40),                                -- 通知テンプレートID
    EVENT_TYPE                      VARCHAR(255),                               -- イベント種別
    TEMPLATE_FILE                   VARCHAR(255),                               -- テンプレート
    NOTIFICATION_DESTINATION        TEXT,                                       -- 通知先
    IS_DEFAULT                      VARCHAR(10)  ,                              -- デフォルト
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- イベント状態マスタ
CREATE TABLE IF NOT EXISTS T_OASE_EVENT_STATUS
(
    EVENT_STATUS_ID                 VARCHAR(2),                                 -- イベント状態ID
    EVENT_STATUS_NAME_JA            VARCHAR(255),                               -- イベント状態(ja)
    EVENT_STATUS_NAME_EN            VARCHAR(255),                               -- イベント状態(en)
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(EVENT_STATUS_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- イベントマスタ
CREATE TABLE IF NOT EXISTS T_OASE_EVENT
(
    EVENT_ID                        VARCHAR(2),                                 -- イベントID
    EVENT_NAME_JA                   VARCHAR(255),                               -- イベント名(ja)
    EVENT_NAME_EN                   VARCHAR(255),                               -- イベント名(en)
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(EVENT_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- イベント履歴
CREATE TABLE IF NOT EXISTS T_OASE_EVENT_HISTORY
(
    id                              VARCHAR(40),                                -- オブジェクトID
    event_collection_settings_id    VARCHAR(40),                                -- イベント収集設定UUID
    fetched_time                    DATETIME(6),                                -- イベント収集日時
    end_time                        DATETIME(6),                                -- イベント有効日時
    event_status                    VARCHAR(255),                               -- イベント状態
    event_type                      VARCHAR(255),                               -- イベント種別
    labels                          TEXT,                                       -- ラベル
    rule_name                       VARCHAR(255),                               -- 評価ルール名
    events                          TEXT,                                       -- 利用イベント
    PRIMARY KEY(id)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- ラベルキー固定マスタ
CREATE TABLE IF NOT EXISTS T_OASE_LABEL_KEY_FIXED
(
    LABEL_KEY_ID                    VARCHAR(40),                                -- ラベルキーID
    LABEL_KEY_NAME                  VARCHAR(255),                               -- ラベルキー
    COLOR_CODE                      VARCHAR(40),                                -- カラーコード
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(LABEL_KEY_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- ラベルキー入力マスタ
CREATE TABLE IF NOT EXISTS T_OASE_LABEL_KEY_INPUT
(
    LABEL_KEY_ID                    VARCHAR(40),                                -- ラベルキーID
    LABEL_KEY_NAME                  VARCHAR(255),                               -- ラベルキー
    COLOR_CODE                      VARCHAR(40),                                -- カラーコード
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(LABEL_KEY_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE IF NOT EXISTS T_OASE_LABEL_KEY_INPUT_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    LABEL_KEY_ID                    VARCHAR(40),                                -- ラベルキーID
    LABEL_KEY_NAME                  VARCHAR(255),                               -- ラベルキー
    COLOR_CODE                      VARCHAR(40),                                -- カラーコード
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- ラベルキー結合ビュー
CREATE OR REPLACE VIEW V_OASE_LABEL_KEY_GROUP AS
SELECT
    LABEL_KEY_ID,
    LABEL_KEY_NAME,
    COLOR_CODE,
    NOTE,
    DISUSE_FLAG,
    LAST_UPDATE_TIMESTAMP,
    LAST_UPDATE_USER
FROM
    T_OASE_LABEL_KEY_INPUT
UNION
SELECT
    LABEL_KEY_ID,
    LABEL_KEY_NAME,
    COLOR_CODE,
    NOTE,
    DISUSE_FLAG,
    LAST_UPDATE_TIMESTAMP,
    LAST_UPDATE_USER
FROM
    T_OASE_LABEL_KEY_FIXED
ORDER BY
    LABEL_KEY_ID ASC
;



-- 比較方法マスタ
CREATE TABLE IF NOT EXISTS T_OASE_COMPARISON_METHOD
(
    COMPARISON_METHOD_ID            VARCHAR(2),                                 -- 比較方法ID
    COMPARISON_METHOD_NAME_EN       VARCHAR(255),                               -- 比較方法名(en)
    COMPARISON_METHOD_NAME_JA       VARCHAR(255),                               -- 比較方法名(ja)
    COMPARISON_METHOD_SYMBOL        VARCHAR(40),                                -- 比較方法(記号)
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(COMPARISON_METHOD_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- ターゲットタイプマスタ
CREATE TABLE IF NOT EXISTS T_OASE_TARGET_TYPE
(
    TYPE_ID                         VARCHAR(2),                                 -- タイプID
    TYPE_NAME_EN                    VARCHAR(40),                                -- タイプ名(en)
    TYPE_NAME_JA                    VARCHAR(40),                                -- タイプ名(ja)
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(TYPE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- ラベリング設定
CREATE TABLE IF NOT EXISTS T_OASE_LABELING_SETTINGS
(
    LABELING_SETTINGS_ID            VARCHAR(40),                                -- ラベリング設定ID
    LABELING_SETTINGS_NAME          VARCHAR(255),                               -- ラベリング設定名
    EVENT_COLLECTION_SETTINGS_ID    VARCHAR(40),                                -- イベント収集設定名ID
    SEARCH_KEY_NAME                 VARCHAR(255),                               -- キー
    TYPE_ID                         VARCHAR(2),                                 -- 値のデータ型
    COMPARISON_METHOD_ID            VARCHAR(2),                                 -- 比較方法
    SEARCH_VALUE_NAME               TEXT,                                       -- 比較する値
    LABEL_KEY_ID                    VARCHAR(255),                               -- キー
    LABEL_VALUE_NAME                VARCHAR(255),                               -- 値
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(LABELING_SETTINGS_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE IF NOT EXISTS T_OASE_LABELING_SETTINGS_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    LABELING_SETTINGS_ID            VARCHAR(40),                                -- ラベリング設定ID
    LABELING_SETTINGS_NAME          VARCHAR(255),                               -- ラベリング設定名
    EVENT_COLLECTION_SETTINGS_ID    VARCHAR(40),                                -- イベント収集設定名ID
    SEARCH_KEY_NAME                 VARCHAR(255),                               -- キー
    TYPE_ID                         VARCHAR(2),                                 -- 値のデータ型
    COMPARISON_METHOD_ID            VARCHAR(2),                                 -- 比較方法
    SEARCH_VALUE_NAME               TEXT,                                       -- 比較する値
    LABEL_KEY_ID                    VARCHAR(255),                               -- キー
    LABEL_VALUE_NAME                VARCHAR(255),                               -- 値
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



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




-- イベント収集経過
CREATE TABLE IF NOT EXISTS T_OASE_EVENT_COLLECTION_PROGRESS
(
    EVENT_COLLECTION_ID             VARCHAR(40),                                -- イベント収集ID
    EVENT_COLLECTION_SETTINGS_ID    VARCHAR(40),                                -- イベント収集設定ID
    FETCHED_TIME                    INT,                                        -- 経過時間
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(EVENT_COLLECTION_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- フィルター組み合わせ演算子マスタ
CREATE TABLE IF NOT EXISTS T_OASE_FILTER_OPERATOR
(
    OPERATION_ID                    VARCHAR(2),                                 -- 演算子ID
    OPERATION_NAME                  VARCHAR(255),                               -- 演算子名
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(OPERATION_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- フィルター
CREATE TABLE IF NOT EXISTS T_OASE_FILTER
(
    FILTER_ID                       VARCHAR(40),                                -- フィルターID
    AVAILABLE_FLAG                  VARCHAR(2),                                 -- 有効
    FILTER_NAME                     VARCHAR(255),                               -- フィルター名
    FILTER_CONDITION_JSON           TEXT,                                       -- フィルター条件
    SEARCH_CONDITION_ID             VARCHAR(2),                                 -- 検索方法
    GROUP_LABEL_KEY_IDS             TEXT,                                       -- グルーピングラベル
    GROUP_CONDITION_ID              VARCHAR(2),                                 -- グルーピング条件ID
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(FILTER_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE IF NOT EXISTS T_OASE_FILTER_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    FILTER_ID                       VARCHAR(40),                                -- フィルターID
    AVAILABLE_FLAG                  VARCHAR(2),                                 -- 有効
    FILTER_NAME                     VARCHAR(255),                               -- フィルター名
    FILTER_CONDITION_JSON           TEXT,                                       -- フィルター条件
    SEARCH_CONDITION_ID             VARCHAR(2),                                 -- 検索方法
    GROUP_LABEL_KEY_IDS             TEXT,                                       -- グルーピングラベル
    GROUP_CONDITION_ID              VARCHAR(2),                                 -- グルーピング条件ID
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
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




-- アクションステータスマスタ
CREATE TABLE IF NOT EXISTS T_OASE_ACTION_STATUS
(
    ACTION_STASTUS_ID               VARCHAR(2),                                 -- アクションステータスID
    ACTION_STASTUS_NAME_JA          VARCHAR(255),                               -- アクションステータス名（ja）
    ACTION_STASTUS_NAME_EN          VARCHAR(255),                               -- アクションステータス名（en）
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ACTION_STASTUS_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- アクション
CREATE TABLE IF NOT EXISTS T_OASE_ACTION
(
    ACTION_ID                       VARCHAR(40),                                -- アクションID
    ACTION_NAME                     VARCHAR(255),                               -- アクション名称
    OPERATION_ID                    VARCHAR(40),                                -- オペレーションID
    CONDUCTOR_CLASS_ID              VARCHAR(40),                                -- ConductorクラスID
    EVENT_COLLABORATION             VARCHAR(2),                                 -- イベント連携
    HOST_ID                         VARCHAR(40),                                -- 指定
    PARAMETER_SHEET_ID              VARCHAR(40),                                -- 利用パラメータシート
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ACTION_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE IF NOT EXISTS T_OASE_ACTION_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    ACTION_ID                       VARCHAR(40),                                -- アクションID
    ACTION_NAME                     VARCHAR(255),                               -- アクション名称
    OPERATION_ID                    VARCHAR(40),                                -- オペレーションID
    CONDUCTOR_CLASS_ID              VARCHAR(40),                                -- ConductorクラスID
    EVENT_COLLABORATION             VARCHAR(2),                                 -- イベント連携
    HOST_ID                         VARCHAR(40),                                -- 指定
    PARAMETER_SHEET_ID              VARCHAR(40),                                -- 利用パラメータシート
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- アクションビュー
CREATE OR REPLACE VIEW V_OASE_ACTION AS
SELECT
    ACTION_ID,
    ACTION_NAME,
    OPERATION_ID,
    CONDUCTOR_CLASS_ID,
    EVENT_COLLABORATION,
    HOST_ID,
    PARAMETER_SHEET_ID,
    PARAMETER_SHEET_ID PARAMETER_SHEET_NAME_REST,
    NOTE,
    DISUSE_FLAG,
    LAST_UPDATE_TIMESTAMP,
    LAST_UPDATE_USER
FROM
    T_OASE_ACTION
ORDER BY
    ACTION_ID ASC
;
CREATE VIEW V_OASE_ACTION_JNL AS
SELECT
    JOURNAL_SEQ_NO,
    JOURNAL_REG_DATETIME,
    JOURNAL_ACTION_CLASS,
    ACTION_ID,
    ACTION_NAME,
    OPERATION_ID,
    CONDUCTOR_CLASS_ID,
    EVENT_COLLABORATION,
    HOST_ID,
    PARAMETER_SHEET_ID,
    PARAMETER_SHEET_ID PARAMETER_SHEET_NAME_REST,
    NOTE,
    DISUSE_FLAG,
    LAST_UPDATE_TIMESTAMP,
    LAST_UPDATE_USER
FROM
    T_OASE_ACTION_JNL
ORDER BY
    ACTION_ID ASC
;



-- 利用パラメータシートビュー
CREATE OR REPLACE VIEW V_OASE_MENU_PULLDOWN AS
SELECT
    TAB_A.*
FROM
    T_COMN_MENU TAB_A
LEFT JOIN
    T_COMN_MENU_TABLE_LINK TAB_B  ON (TAB_A.MENU_ID = TAB_B.MENU_ID)
WHERE
    TAB_B.SHEET_TYPE = 1
AND
    TAB_A.DISUSE_FLAG = 0
AND
    TAB_B.VERTICAL = 0
AND
    TAB_B.HOSTGROUP = 0
AND
    TAB_B.SUBSTITUTION_VALUE_LINK_FLAG = 0
ORDER BY
    MENU_ID
;



-- アクション用ホストグループビュー
CREATE OR REPLACE VIEW V_OASE_HGSP_UQ_HOST_LIST AS
SELECT
    SYSTEM_ID AS KY_KEY,
    CONCAT('[H]', HOST_NAME) AS KY_VALUE,
    0 AS KY_SOURCE,
    2147483647 AS PRIORITY,
    DISUSE_FLAG AS DISUSE_FLAG,
    LAST_UPDATE_TIMESTAMP AS LAST_UPDATE_TIMESTAMP,
    LAST_UPDATE_USER AS LAST_UPDATE_USER
FROM
    T_ANSC_DEVICE
WHERE
    DISUSE_FLAG = '0'
;



-- ルール
CREATE TABLE IF NOT EXISTS T_OASE_RULE
(
    RULE_ID                         VARCHAR(40),                                -- ルールID
    AVAILABLE_FLAG                  VARCHAR(2),                                 -- 有効
    RULE_NAME                       VARCHAR(255),                               -- ルール名
    RULE_LABEL_NAME                 VARCHAR(255),                               -- ルールラベル名
    RULE_PRIORITY                   INT,                                        -- 優先順位
    FILTER_A                        VARCHAR(40),                                -- フィルターA
    FILTER_OPERATOR                 VARCHAR(2),                                 -- フィルター演算子
    FILTER_B                        VARCHAR(40),                                -- フィルターB
    BEFORE_NOTIFICATION             VARCHAR(255),                               -- 事前_通知
    BEFORE_APPROVAL_PENDING         VARCHAR(1)  ,                               -- 事前_承認待ち
    BEFORE_NOTIFICATION_DESTINATION TEXT,                                       -- 事前_通知先
    ACTION_ID                       VARCHAR(40),                                -- アクション名
    AFTER_NOTIFICATION              VARCHAR(255),                               -- 事後_通知
    AFTER_APPROVAL_PENDING          VARCHAR(1)  ,                               -- 事後_承認待ち
    AFTER_NOTIFICATION_DESTINATION  TEXT,                                       -- 事後_通知先
    ACTION_LABEL_INHERITANCE_FLAG   VARCHAR(2),                                 -- アクション
    EVENT_LABEL_INHERITANCE_FLAG    VARCHAR(2),                                 -- イベント
    CONCLUSION_LABEL_SETTINGS       TEXT,                                       -- 結論ラベル設定
    TTL                             INT,                                        -- TTL
    EVENT_ID_LIST                   TEXT,                                       -- 使用イベント保存用
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(RULE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE IF NOT EXISTS T_OASE_RULE_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    RULE_ID                         VARCHAR(40),                                -- ルールID
    AVAILABLE_FLAG                  VARCHAR(2),                                 -- 有効
    RULE_NAME                       VARCHAR(255),                               -- ルール名
    RULE_LABEL_NAME                 VARCHAR(255),                               -- ルールラベル名
    RULE_PRIORITY                   INT,                                        -- 優先順位
    FILTER_A                        VARCHAR(40),                                -- フィルターA
    FILTER_OPERATOR                 VARCHAR(2),                                 -- フィルター演算子
    FILTER_B                        VARCHAR(40),                                -- フィルターB
    BEFORE_NOTIFICATION             VARCHAR(255),                               -- 事前_通知
    BEFORE_APPROVAL_PENDING         VARCHAR(1)  ,                               -- 事前_承認待ち
    BEFORE_NOTIFICATION_DESTINATION TEXT,                                       -- 事前_通知先
    ACTION_ID                       VARCHAR(40),                                -- アクション名
    AFTER_NOTIFICATION              VARCHAR(255),                               -- 事後_通知
    AFTER_APPROVAL_PENDING          VARCHAR(1)  ,                               -- 事後_承認待ち
    AFTER_NOTIFICATION_DESTINATION  TEXT,                                       -- 事後_通知先
    ACTION_LABEL_INHERITANCE_FLAG   VARCHAR(2),                                 -- アクション
    EVENT_LABEL_INHERITANCE_FLAG    VARCHAR(2),                                 -- イベント
    CONCLUSION_LABEL_SETTINGS       TEXT,                                       -- 結論ラベル設定
    TTL                             INT,                                        -- TTL
    EVENT_ID_LIST                   TEXT,                                       -- 使用イベント保存用
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 結論ラベルキー結合ビュー
CREATE OR REPLACE VIEW V_OASE_CONCLUSION_LABEL_KEY_GROUP AS
SELECT
    LABEL_KEY_ID,
    LABEL_KEY_NAME,
    COLOR_CODE,
    NOTE,
    DISUSE_FLAG,
    LAST_UPDATE_TIMESTAMP,
    LAST_UPDATE_USER
FROM
    T_OASE_LABEL_KEY_INPUT
UNION
SELECT
    LABEL_KEY_ID,
    LABEL_KEY_NAME,
    COLOR_CODE,
    NOTE,
    DISUSE_FLAG,
    LAST_UPDATE_TIMESTAMP,
    LAST_UPDATE_USER
FROM
    T_OASE_LABEL_KEY_FIXED
WHERE
    LABEL_KEY_ID = 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx09'
ORDER BY
    LABEL_KEY_ID ASC
;



-- 評価結果
CREATE TABLE IF NOT EXISTS T_OASE_ACTION_LOG
(
    ACTION_LOG_ID                   VARCHAR(40),                                -- アクション履歴ID
    RULE_ID                         VARCHAR(40),                                -- ルールID
    RULE_NAME                       VARCHAR(255),                               -- ルール名称
    STATUS_ID                       VARCHAR(2),                                 -- ステータスID
    ACTION_ID                       VARCHAR(40),                                -- アクションID
    ACTION_NAME                     VARCHAR(255),                               -- アクション名称
    CONDUCTOR_INSTANCE_ID           VARCHAR(40),                                -- ConductorインスタンスID
    CONDUCTOR_INSTANCE_NAME         VARCHAR(255),                               -- Conductor名称
    OPERATION_ID                    VARCHAR(40),                                -- オペレーションID
    OPERATION_NAME                  VARCHAR(255),                               -- オペレーション名
    EVENT_COLLABORATION             VARCHAR(2),                                 -- イベント連携
    HOST_ID                         VARCHAR(40),                                -- 指定ホストID
    HOST_NAME                       VARCHAR(255),                               -- 指定ホスト名
    PARAMETER_SHEET_ID              VARCHAR(40),                                -- 利用パラメータシート
    PARAMETER_SHEET_NAME            VARCHAR(255),                               -- 利用パラメータシート名
    PARAMETER_SHEET_NAME_REST       VARCHAR(255),                               -- 利用パラメータシート(rest)
    EVENT_ID_LIST                   TEXT,                                       -- 利用イベントID
    ACTION_LABEL_INHERITANCE_FLAG   VARCHAR(2),                                 -- アクション
    EVENT_LABEL_INHERITANCE_FLAG    VARCHAR(2),                                 -- イベント
    ACTION_PARAMETERS               TEXT,                                       -- アクションパラメータ
    CONCLUSION_EVENT_LABELS         TEXT,                                       -- 結論ラベル
    TIME_REGISTER                   DATETIME(6),                                -- 登録日時
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ACTION_LOG_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE IF NOT EXISTS T_OASE_ACTION_LOG_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    ACTION_LOG_ID                   VARCHAR(40),                                -- アクション履歴ID
    RULE_ID                         VARCHAR(40),                                -- ルールID
    RULE_NAME                       VARCHAR(255),                               -- ルール名称
    STATUS_ID                       VARCHAR(2),                                 -- ステータスID
    ACTION_ID                       VARCHAR(40),                                -- アクションID
    ACTION_NAME                     VARCHAR(255),                               -- アクション名称
    CONDUCTOR_INSTANCE_ID           VARCHAR(40),                                -- ConductorインスタンスID
    CONDUCTOR_INSTANCE_NAME         VARCHAR(255),                               -- Conductor名称
    OPERATION_ID                    VARCHAR(40),                                -- オペレーションID
    OPERATION_NAME                  VARCHAR(255),                               -- オペレーション名
    EVENT_COLLABORATION             VARCHAR(2),                                 -- イベント連携
    HOST_ID                         VARCHAR(40),                                -- 指定ホストID
    HOST_NAME                       VARCHAR(255),                               -- 指定ホスト名
    PARAMETER_SHEET_ID              VARCHAR(40),                                -- 利用パラメータシート
    PARAMETER_SHEET_NAME            VARCHAR(255),                               -- 利用パラメータシート名
    PARAMETER_SHEET_NAME_REST       VARCHAR(255),                               -- 利用パラメータシート(rest)
    EVENT_ID_LIST                   TEXT,                                       -- 利用イベントID
    ACTION_LABEL_INHERITANCE_FLAG   VARCHAR(2),                                 -- アクション
    EVENT_LABEL_INHERITANCE_FLAG    VARCHAR(2),                                 -- イベント
    ACTION_PARAMETERS               TEXT,                                       -- アクションパラメータ
    CONCLUSION_EVENT_LABELS         TEXT,                                       -- 結論ラベル
    TIME_REGISTER                   DATETIME(6),                                -- 登録日時
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- インデックス
CREATE INDEX IND_T_OASE_CONNECTION_METHOD_01 ON T_OASE_CONNECTION_METHOD(DISUSE_FLAG);
CREATE INDEX IND_T_OASE_REQUEST_METHOD_01 ON T_OASE_REQUEST_METHOD (DISUSE_FLAG);
CREATE INDEX IND_T_OASE_EVENT_COLLECTION_SETTINGS_01 ON T_OASE_EVENT_COLLECTION_SETTINGS(DISUSE_FLAG);
CREATE INDEX IND_T_OASE_LABEL_KEY_FIXED_01 ON T_OASE_LABEL_KEY_FIXED(DISUSE_FLAG);
CREATE INDEX IND_T_OASE_LABEL_KEY_INPUT_01 ON T_OASE_LABEL_KEY_INPUT(DISUSE_FLAG);
CREATE INDEX IND_T_OASE_COMPARISON_METHOD_01 ON T_OASE_COMPARISON_METHOD(DISUSE_FLAG);
CREATE INDEX IND_T_OASE_TARGET_TYPE_01 ON T_OASE_TARGET_TYPE(DISUSE_FLAG);
CREATE INDEX IND_T_OASE_LABELING_SETTINGS_01 ON T_OASE_LABELING_SETTINGS(DISUSE_FLAG);
CREATE INDEX IND_T_OASE_EVENT_COLLECTION_PROGRESS_01 ON T_OASE_EVENT_COLLECTION_PROGRESS(DISUSE_FLAG);
CREATE INDEX IND_T_OASE_ACTION_STATUS_01 ON T_OASE_ACTION_STATUS (DISUSE_FLAG);
CREATE INDEX IND_T_OASE_ACTION_01 ON T_OASE_ACTION (DISUSE_FLAG);
CREATE INDEX IND_T_OASE_ACTION_LOG_01 ON T_OASE_ACTION_LOG (DISUSE_FLAG);



