-- イベント収集の設定
CREATE TABLE T_EVRE_EVENT_COLLECTION_SETTINGS
(
    GATHERING_EVENT_ID              VARCHAR(40),                                -- イベント収集ID
    GATHERING_EVENT_NAME            VARCHAR(255),                               -- イベント収集名
    AUTHENTICATION_METHOD_ID        VARCHAR(2),                                 -- 認証方法ID
    REQUEST_METHOD                  VARCHAR(40),                                -- リクエスト方法
    API_URL                         VARCHAR(1024),                              -- APIのURL
    REQUEST_HEADER                  TEXT,                                       -- リクエストヘッダー
    PROXY                           VARCHAR(255),                               -- プロキシ
    AUTH_TOKEN                      VARCHAR(1024),                              -- 認証トークン
    USERNAME                        VARCHAR(255),                               -- ユーザー名
    PASSWORD                        TEXT,                                       -- パスワード
    HOSTNAME                        VARCHAR(255),                               -- ホスト名
    PORT                            INT,                                        -- ポート
    COMMUNICATION_METHOD            VARCHAR(255),                               -- コミュニケーション方法
    ACCESS_KEY_ID                   VARCHAR(1024),                              -- アクセスキーID
    SECRET_ACCESS_KEY               VARCHAR(1024),                              -- 秘密アクセスキー
    PARAMETER                       TEXT,                                       -- パラメーター
    IS_LIST                         VARCHAR(2),                                 -- リスト
    LIST_KEY                        VARCHAR(255),                               -- リストキー
    TTL                             INT,                                        -- TTL
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(GATHERING_EVENT_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_EVRE_EVENT_COLLECTION_SETTINGS_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    GATHERING_EVENT_ID              VARCHAR(40),                                -- イベント収集ID
    GATHERING_EVENT_NAME            VARCHAR(255),                               -- イベント収集名
    AUTHENTICATION_METHOD_ID        VARCHAR(2),                                 -- 認証方法ID
    REQUEST_METHOD                  VARCHAR(40),                                -- リクエスト方法
    API_URL                         VARCHAR(1024),                              -- APIのURL
    REQUEST_HEADER                  TEXT,                                       -- リクエストヘッダー
    PROXY                           VARCHAR(255),                               -- プロキシ
    AUTH_TOKEN                      VARCHAR(1024),                              -- 認証トークン
    USERNAME                        VARCHAR(255),                               -- ユーザー名
    PASSWORD                        TEXT,                                       -- パスワード
    HOSTNAME                        VARCHAR(255),                               -- ホスト名
    PORT                            INT,                                        -- ポート
    COMMUNICATION_METHOD            VARCHAR(255),                               -- コミュニケーション方法
    ACCESS_KEY_ID                   VARCHAR(1024),                              -- アクセスキーID
    SECRET_ACCESS_KEY               VARCHAR(1024),                              -- 秘密アクセスキー
    PARAMETER                       TEXT,                                       -- パラメーター
    IS_LIST                         VARCHAR(2),                                 -- リスト
    LIST_KEY                        VARCHAR(255),                               -- リストキー
    TTL                             INT,                                        -- TTL
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- ラベリングの設定
CREATE TABLE T_EVRE_LABELING_SETTINGS
(
    LABELING_ID                     VARCHAR(40),                                -- ラベリングID
    LABELING_NAME                   VARCHAR(255),                               -- ラベリング名
    GATHERING_EVENT_ID              VARCHAR(40),                                -- イベント収集ID
    TARGET_KEY                      VARCHAR(255),                               -- ターゲットキー
    TARGET_TYPE_ID                  VARCHAR(2),                                 -- ターゲットのタイプID
    TARGET_VALUE                    TEXT,                                       -- ターゲットの値
    COMPARE_METHOD_ID               VARCHAR(2),                                 -- 比較方法ID
    ITA_LABEL_KEY_ID                VARCHAR(40),                                -- ITAラベルキーID
    ITA_LABEL_VALUE                 VARCHAR(255),                               -- ITAラベルキーラベル値
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(LABELING_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_EVRE_LABELING_SETTINGS_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    LABELING_ID                     VARCHAR(40),                                -- ラベリングID
    LABELING_NAME                   VARCHAR(255),                               -- ラベリング名
    GATHERING_EVENT_ID              VARCHAR(40),                                -- イベント収集ID
    TARGET_KEY                      VARCHAR(255),                               -- ターゲットキー
    TARGET_TYPE_ID                  VARCHAR(2),                                 -- ターゲットのタイプID
    TARGET_VALUE                    TEXT,                                       -- ターゲットの値
    COMPARE_METHOD_ID               VARCHAR(2),                                 -- 比較方法ID
    ITA_LABEL_KEY_ID                VARCHAR(40),                                -- ITAラベルキーID
    ITA_LABEL_VALUE                 VARCHAR(255),                               -- ITAラベルキーラベル値
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- ラベルキー入力マスタ
CREATE TABLE T_EVRE_LABEL_KEY_INPUT
(
    ITA_LABEL_KEY_ID                VARCHAR(40),                                -- ラベルキーID
    ITA_LABEL_KEY                   VARCHAR(255),                               -- ラベルキー
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ITA_LABEL_KEY_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_EVRE_LABEL_KEY_INPUT_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    ITA_LABEL_KEY_ID                VARCHAR(40),                                -- ラベルキーID
    ITA_LABEL_KEY                   VARCHAR(255),                               -- ラベルキー
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- イベント収集経過
CREATE TABLE T_EVRE_EVENT_COLLECTION_PROGRESS
(
    EVENT_COLLECTION_ID             VARCHAR(40),                                -- イベント収集ID
    FETCHED_TIME                    VARCHAR(40),                                -- 経過時間
    EVALUATED_FLAG                  VARCHAR(40),                                -- 評価フラグ
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(EVENT_COLLECTION_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_EVRE_EVENT_COLLECTION_PROGRESS_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    EVENT_COLLECTION_ID             VARCHAR(40),                                -- イベント収集ID
    FETCHED_TIME                    VARCHAR(40),                                -- 経過時間
    EVALUATED_FLAG                  VARCHAR(40),                                -- 評価フラグ
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 接続方式マスタ
CREATE TABLE T_EVRE_CONNECTION_METHOD
(
    AUTHENTICATION_METHOD_ID        VARCHAR(2),                                 -- 認証方法ID
    AUTH_METHOD_NAME_EN             VARCHAR(255),                               -- 認証方法名(en)
    AUTH_METHOD_NAME_JA             VARCHAR(255),                               -- 認証方法名(ja)
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(AUTHENTICATION_METHOD_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- 比較方法マスタ
CREATE TABLE T_EVRE_COMPARISON_METHOD
(
    COMPARE_METHOD_ID               VARCHAR(2),                                 -- 比較方法ID
    METHOD_NAME_EN                  VARCHAR(255),                               -- 方法名(en)
    METHOD_NAME_JA                  VARCHAR(255),                               -- 方法名(ja)
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(COMPARE_METHOD_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- ターゲットのデータ型マスタ
CREATE TABLE T_EVRE_TARGET_DATA_TYPE
(
    TARGET_TYPE_ID                  VARCHAR(2),                                 -- ターゲットのタイプID
    TARGET_TYPE_EN                  VARCHAR(40),                                -- ターゲットのタイプ(en)
    TARGET_TYPE_JA                  VARCHAR(40),                                -- ターゲットのタイプ(ja)
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(TARGET_TYPE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- ラベルキー固定マスタ
CREATE TABLE T_EVRE_LABEL_KEY_FIXED
(
    ITA_LABEL_KEY_ID                VARCHAR(40),                                -- ラベルキーID
    ITA_LABEL_KEY                   VARCHAR(255),                               -- ラベルキー
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ITA_LABEL_KEY_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- インデックス
CREATE INDEX IND_T_EVRE_EVENT_COLLECTION_SETTINGS_01 ON T_EVRE_EVENT_COLLECTION_SETTINGS (DISUSE_FLAG);
CREATE INDEX IND_T_EVRE_LABELING_SETTINGS_01 ON T_EVRE_LABELING_SETTINGS (DISUSE_FLAG);
CREATE INDEX IND_T_EVRE_LABEL_KEY_INPUT_01 ON T_EVRE_LABEL_KEY_INPUT (DISUSE_FLAG);
CREATE INDEX IND_T_EVRE_EVENT_COLLECTION_PROGRESS_01 ON T_EVRE_EVENT_COLLECTION_PROGRESS (DISUSE_FLAG);
CREATE INDEX IND_T_EVRE_CONNECTION_METHOD_01 ON T_EVRE_CONNECTION_METHOD (DISUSE_FLAG);
CREATE INDEX IND_T_EVRE_COMPARISON_METHOD_01 ON T_EVRE_COMPARISON_METHOD (DISUSE_FLAG);
CREATE INDEX IND_T_EVRE_TARGET_DATA_TYPE_01 ON T_EVRE_TARGET_DATA_TYPE (DISUSE_FLAG);
CREATE INDEX IND_T_EVRE_LABEL_KEY_FIXED_01 ON T_EVRE_LABEL_KEY_FIXED (DISUSE_FLAG);



