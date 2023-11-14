-- 接続方式マスタ
CREATE TABLE T_OASE_CONNECTION_METHOD
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
CREATE TABLE T_OASE_REQUEST_METHOD
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
CREATE TABLE T_OASE_EVENT_COLLECTION_SETTINGS
(
    EVENT_COLLECTION_SETTINGS_ID    VARCHAR(40),                                -- イベント収集ID
    EVENT_COLLECTION_NAME           VARCHAR(255),                               -- イベント収集名
    CONNECTION_METHOD_ID            VARCHAR(2),                                 -- 接続方式ID
    REQUEST_METHOD_ID               VARCHAR(2),                                 -- リクエストメソッドID
    URL                             VARCHAR(1024),                              -- URL
    PORT                            INT,                                        -- ポート
    REQUEST_HEADER                  TEXT,                                       -- リクエストヘッダー
    PROXY                           VARCHAR(255),                               -- プロキシ
    AUTH_TOKEN                      VARCHAR(1024),                              -- 認証トークン
    USERNAME                        VARCHAR(255),                               -- ユーザー名
    PASSWORD                        TEXT,                                       -- パスワード
    MAILBOXNAME                     VARCHAR(255),                               -- メールボックス名
    ACCESS_KEY_ID                   VARCHAR(1024),                              -- アクセスキーID
    SECRET_ACCESS_KEY               TEXT,                                       -- 秘密アクセスキー
    PARAMETER                       TEXT,                                       -- パラメータ
    RESPONSE_LIST_FLAG              VARCHAR(2),                                 -- レスポンスリストフラグ
    RESPONSE_KEY                    VARCHAR(255),                               -- レスポンスキー
    TTL                             INT,                                        -- TTL
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(EVENT_COLLECTION_SETTINGS_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_OASE_EVENT_COLLECTION_SETTINGS_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    EVENT_COLLECTION_SETTINGS_ID    VARCHAR(40),                                -- イベント収集ID
    EVENT_COLLECTION_NAME           VARCHAR(255),                               -- イベント収集名
    CONNECTION_METHOD_ID            VARCHAR(2),                                 -- 接続方式ID
    REQUEST_METHOD_ID               VARCHAR(2),                                 -- リクエストメソッドID
    URL                             VARCHAR(1024),                              -- URL
    PORT                            INT,                                        -- ポート
    REQUEST_HEADER                  TEXT,                                       -- リクエストヘッダー
    PROXY                           VARCHAR(255),                               -- プロキシ
    AUTH_TOKEN                      VARCHAR(1024),                              -- 認証トークン
    USERNAME                        VARCHAR(255),                               -- ユーザー名
    PASSWORD                        TEXT,                                       -- パスワード
    MAILBOXNAME                     VARCHAR(255),                               -- メールボックス名
    ACCESS_KEY_ID                   VARCHAR(1024),                              -- アクセスキーID
    SECRET_ACCESS_KEY               TEXT,                                       -- 秘密アクセスキー
    PARAMETER                       TEXT,                                       -- パラメータ
    RESPONSE_LIST_FLAG              VARCHAR(2),                                 -- レスポンスリストフラグ
    RESPONSE_KEY                    VARCHAR(255),                               -- レスポンスキー
    TTL                             INT,                                        -- TTL
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 通知テンプレート(共通)
CREATE TABLE T_OASE_NOTIFICATION_TEMPLATE_COMMON
(
    NOTIFICATION_TEMPLATE_ID        VARCHAR(2),                                 -- 通知テンプレートID
    EVENT_TYPE                      VARCHAR(255),                               -- イベント種別
    TEMPLATE_FILE                   VARCHAR(255),                               -- テンプレート
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(NOTIFICATION_TEMPLATE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_OASE_NOTIFICATION_TEMPLATE_COMMON_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    NOTIFICATION_TEMPLATE_ID        VARCHAR(2),                                 -- 通知テンプレートID
    EVENT_TYPE                      VARCHAR(255),                               -- イベント種別
    TEMPLATE_FILE                   VARCHAR(255),                               -- テンプレート
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- イベント履歴
CREATE TABLE T_OASE_EVENT_HISTORY
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
CREATE TABLE T_OASE_LABEL_KEY_FIXED
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
CREATE TABLE T_OASE_LABEL_KEY_INPUT
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

CREATE TABLE T_OASE_LABEL_KEY_INPUT_JNL
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
CREATE VIEW V_OASE_LABEL_KEY_GROUP AS
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
CREATE TABLE T_OASE_COMPARISON_METHOD
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
CREATE TABLE T_OASE_TARGET_TYPE
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
CREATE TABLE T_OASE_LABELING_SETTINGS
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

CREATE TABLE T_OASE_LABELING_SETTINGS_JNL
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



-- イベント収集経過
CREATE TABLE T_OASE_EVENT_COLLECTION_PROGRESS
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

CREATE TABLE T_OASE_EVENT_COLLECTION_PROGRESS_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    EVENT_COLLECTION_ID             VARCHAR(40),                                -- イベント収集ID
    EVENT_COLLECTION_SETTINGS_ID    VARCHAR(40),                                -- イベント収集設定ID
    FETCHED_TIME                    INT,                                        -- 経過時間
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- フィルター組み合わせ演算子マスタ
CREATE TABLE T_OASE_FILTER_OPERATOR
(
    OPERATION_ID                    VARCHAR(2),                                 -- 演算子ID
    OPERATION_NAME                  VARCHAR(255),                               -- 演算子名
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(OPERATION_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- フィルター管理
CREATE TABLE T_OASE_FILTER
(
    FILTER_ID                       VARCHAR(40),                                -- フィルターID
    FILTER_NAME                     VARCHAR(255),                               -- フィルター名
    FILTER_CONDITION_JSON           LONGTEXT,                                   -- フィルター条件
    AVAILABLE_FLAG                  VARCHAR(2),                                 -- 有効
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(FILTER_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_OASE_FILTER_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    FILTER_ID                       VARCHAR(40),                                -- フィルターID
    FILTER_NAME                     VARCHAR(255),                               -- フィルター名
    FILTER_CONDITION_JSON           LONGTEXT,                                   -- フィルター条件
    AVAILABLE_FLAG                  VARCHAR(2),                                 -- 有効
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- アクションステータスマスタ
CREATE TABLE T_OASE_ACTION_STATUS
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




-- アクション定義
CREATE TABLE T_OASE_ACTION
(
    ACTION_ID                       VARCHAR(40),                                -- アクション定義ID
    ACTION_NAME                     VARCHAR(255),                               -- アクション名称
    OPERATION_ID                    VARCHAR(40),                                -- オペレーションID
    CONDUCTOR_CLASS_ID              VARCHAR(40),                                -- ConductorクラスID
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ACTION_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_OASE_ACTION_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    ACTION_ID                       VARCHAR(40),                                -- アクション定義ID
    ACTION_NAME                     VARCHAR(255),                               -- アクション名称
    OPERATION_ID                    VARCHAR(40),                                -- オペレーションID
    CONDUCTOR_CLASS_ID              VARCHAR(40),                                -- ConductorクラスID
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- ルール管理
CREATE TABLE T_OASE_RULE
(
    RULE_ID                         VARCHAR(40),                                -- ルールID
    RULE_NAME                       VARCHAR(255),                               -- ルール名
    RULE_LABEL_NAME                 VARCHAR(255),                               -- ルールラベル名
    RULE_PRIORITY                   INT,                                        -- 優先順位
    FILTER_COMBINATION_JSON         LONGTEXT,                                   -- フィルター組み合わせ情報
    BEFORE_NOTIFICATION             VARCHAR(255),                               -- 作業前_通知
    BEFORE_APPROVAL_PENDING         VARCHAR(1)  ,                               -- 作業前_承認待ち
    BEFORE_NOTIFICATION_DESTINATION LONGTEXT,                                   -- 作業前_通知先
    ACTION_ID                       VARCHAR(40),                                -- アクションID
    AFTER__NOTIFICATION             VARCHAR(255),                               -- 作業後_通知
    AFTER_APPROVAL_PENDING          VARCHAR(1)  ,                               -- 作業後_承認待ち
    AFTER_NOTIFICATION_DESTINATION  LONGTEXT,                                   -- 作業後_通知先
    LABELING_INFORMATION_JSON       LONGTEXT,                                   -- ラベリング情報
    REEVALUATE_TTL                  INT,                                        -- 再評価用TTL
    AVAILABLE_FLAG                  VARCHAR(2),                                 -- 有効
    EVENT_ID_LIST                   TEXT,                                       -- 使用イベント保存用
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(RULE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_OASE_RULE_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    RULE_ID                         VARCHAR(40),                                -- ルールID
    RULE_NAME                       VARCHAR(255),                               -- ルール名
    RULE_LABEL_NAME                 VARCHAR(255),                               -- ルールラベル名
    RULE_PRIORITY                   INT,                                        -- 優先順位
    FILTER_COMBINATION_JSON         LONGTEXT,                                   -- フィルター組み合わせ情報
    BEFORE_NOTIFICATION             VARCHAR(255),                               -- 作業前_通知
    BEFORE_APPROVAL_PENDING         VARCHAR(1)  ,                               -- 作業前_承認待ち
    BEFORE_NOTIFICATION_DESTINATION LONGTEXT,                                   -- 作業前_通知先
    ACTION_ID                       VARCHAR(40),                                -- アクションID
    AFTER__NOTIFICATION             VARCHAR(255),                               -- 作業後_通知
    AFTER_APPROVAL_PENDING          VARCHAR(1)  ,                               -- 作業後_承認待ち
    AFTER_NOTIFICATION_DESTINATION  LONGTEXT,                                   -- 作業後_通知先
    LABELING_INFORMATION_JSON       LONGTEXT,                                   -- ラベリング情報
    REEVALUATE_TTL                  INT,                                        -- 再評価用TTL
    AVAILABLE_FLAG                  VARCHAR(2),                                 -- 有効
    EVENT_ID_LIST                   TEXT,                                       -- 使用イベント保存用
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- アクション履歴
CREATE TABLE T_OASE_ACTION_LOG
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
    EVENT_ID_LIST                   TEXT,                                       -- 利用イベントID
    TIME_REGISTER                   DATETIME(6),                                -- 登録日時
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ACTION_LOG_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_OASE_ACTION_LOG_JNL
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
    EVENT_ID_LIST                   TEXT,                                       -- 利用イベントID
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



