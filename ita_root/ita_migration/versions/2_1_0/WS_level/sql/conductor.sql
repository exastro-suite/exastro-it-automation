-- CREATE TABLE IF NOT EXISTS/VIEW: -2.1.0
    -- T_COMN_CONDUCTOR_NOTICE:
    -- T_COMN_CONDUCTOR_REGULARLY_LIST
    -- T_COMN_CONDUCTOR_REGULARLY_PERIOD
    -- T_COMN_CONDUCTOR_DAY_OF_WEEK
    -- T_COMN_CONDUCTOR_WEEK_NUMBER
    -- T_COMN_CONDUCTOR_REGULARLY_STATUS
    -- V_COMN_CONDUCTOR_NODE_INSTANCE

-- ALTER: -2.1.0
    -- none

-- Conductor通知
CREATE TABLE IF NOT EXISTS T_COMN_CONDUCTOR_NOTICE
(
    CONDUCTOR_NOTICE_ID             VARCHAR(40),                                -- Conductor通知ID
    NOTICE_NAME                     VARCHAR(255),                               -- 通知名称
    NOTICE_URL                      VARCHAR(255),                               -- 通知先
    HEADER                          VARCHAR(255),                               -- ヘッダー
    FIELDS                          TEXT,                                       -- メッセージ
    PROXY_URL                       VARCHAR(255),                               -- Proxy URL
    PROXY_PORT                      INT,                                        -- Proxy Port
    FQDN                            VARCHAR(255),                               -- 作業確認URL
    OTHER                           VARCHAR(255),                               -- その他
    SUPPRESS_START                  DATETIME(6),                                -- 抑止開始日時
    SUPPRESS_END                    DATETIME(6),                                -- 抑止終了日時
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(CONDUCTOR_NOTICE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE IF NOT EXISTS T_COMN_CONDUCTOR_NOTICE_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    CONDUCTOR_NOTICE_ID             VARCHAR(40),                                -- Conductor通知ID
    NOTICE_NAME                     VARCHAR(255),                               -- 通知名称
    NOTICE_URL                      VARCHAR(255),                               -- 通知先
    HEADER                          VARCHAR(255),                               -- ヘッダー
    FIELDS                          TEXT,                                       -- メッセージ
    PROXY_URL                       VARCHAR(255),                               -- Proxy URL
    PROXY_PORT                      INT,                                        -- Proxy Port
    FQDN                            VARCHAR(255),                               -- 作業確認URL
    OTHER                           VARCHAR(255),                               -- その他
    SUPPRESS_START                  DATETIME(6),                                -- 抑止開始日時
    SUPPRESS_END                    DATETIME(6),                                -- 抑止終了日時
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- Conductor定期作業実行リスト
CREATE TABLE IF NOT EXISTS T_COMN_CONDUCTOR_REGULARLY_LIST
(
    REGULARLY_ID                    VARCHAR(40),                                -- 定期作業実行ID
    CONDUCTOR_CLASS_ID              VARCHAR(40),                                -- ConductorクラスID
    OPERATION_ID                    VARCHAR(40),                                -- オペレーションID
    CONDUCTOR_INSTANCE_ID           VARCHAR(40),                                -- ConductorインスタンスID
    STATUS_ID                       VARCHAR(2),                                 -- ステータスID
    EXECUTION_USER_ID               VARCHAR(40),                                -- 実行ユーザID
    NEXT_EXECUTION_DATE             DATETIME(6),                                -- 次回実行日付
    START_DATE                      DATETIME(6),                                -- 開始日付
    END_DATE                        DATETIME(6),                                -- 終了日付
    REGULARLY_PERIOD_ID             VARCHAR(2),                                 -- 定期作業実行周期ID
    EXECUTION_INTERVAL              INT,                                        -- 実行間隔
    PATTERN_WEEK_NUMBER_ID          VARCHAR(2),                                 -- 実行週番号ID
    PATTERN_DAY_OF_WEEK_ID          VARCHAR(2),                                 -- 実行曜日ID
    PATTERN_DAY                     INT,                                        -- 実行日
    PATTERN_TIME                    VARCHAR(9),                                 -- 実行時分
    EXECUTION_STOP_START_DATE       DATETIME(6),                                -- 実行停止期間の開始日付
    EXECUTION_STOP_END_DATE         DATETIME(6),                                -- 実行停止期間の終了日付
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(REGULARLY_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE IF NOT EXISTS T_COMN_CONDUCTOR_REGULARLY_LIST_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    REGULARLY_ID                    VARCHAR(40),                                -- 定期作業実行ID
    CONDUCTOR_CLASS_ID              VARCHAR(40),                                -- ConductorクラスID
    OPERATION_ID                    VARCHAR(40),                                -- オペレーションID
    CONDUCTOR_INSTANCE_ID           VARCHAR(40),                                -- ConductorインスタンスID
    STATUS_ID                       VARCHAR(2),                                 -- ステータスID
    EXECUTION_USER_ID               VARCHAR(40),                                -- 実行ユーザID
    NEXT_EXECUTION_DATE             DATETIME(6),                                -- 次回実行日付
    START_DATE                      DATETIME(6),                                -- 開始日付
    END_DATE                        DATETIME(6),                                -- 終了日付
    REGULARLY_PERIOD_ID             VARCHAR(2),                                 -- 定期作業実行周期ID
    EXECUTION_INTERVAL              INT,                                        -- 実行間隔
    PATTERN_WEEK_NUMBER_ID          VARCHAR(2),                                 -- 実行週番号ID
    PATTERN_DAY_OF_WEEK_ID          VARCHAR(2),                                 -- 実行曜日ID
    PATTERN_DAY                     INT,                                        -- 実行日
    PATTERN_TIME                    VARCHAR(9),                                 -- 実行時分
    EXECUTION_STOP_START_DATE       DATETIME(6),                                -- 実行停止期間の開始日付
    EXECUTION_STOP_END_DATE         DATETIME(6),                                -- 実行停止期間の終了日付
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- Conductor定期作業実行周期マスタ
CREATE TABLE IF NOT EXISTS T_COMN_CONDUCTOR_REGULARLY_PERIOD
(
    REGULARLY_PERIOD_ID             VARCHAR(2),                                 -- Conductor定期作業実行パターンID
    REGULARLY_PERIOD_NAME_JA        VARCHAR(32),                                -- Conductor定期作業実行パターン名称
    REGULARLY_PERIOD_NAME_EN        VARCHAR(32),                                -- Conductor定期作業実行パターン名称
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(REGULARLY_PERIOD_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- Conductor曜日マスタ
CREATE TABLE IF NOT EXISTS T_COMN_CONDUCTOR_DAY_OF_WEEK
(
    DAY_OF_WEEK_ID                  VARCHAR(2),                                 -- 曜日ID
    DAY_OF_WEEK_NAME_JA             VARCHAR(16),                                -- 曜日名称
    DAY_OF_WEEK_NAME_EN             VARCHAR(16),                                -- 曜日名称
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(DAY_OF_WEEK_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- Conductor週番号マスタ
CREATE TABLE IF NOT EXISTS T_COMN_CONDUCTOR_WEEK_NUMBER
(
    WEEK_NUMBER_ID                  VARCHAR(2),                                 -- 週番号ID
    WEEK_NUMBER_NAME_JA             VARCHAR(16),                                -- 週番号名称
    WEEK_NUMBER_NAME_EN             VARCHAR(16),                                -- 週番号名称
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(WEEK_NUMBER_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- Conductor定期作業実行ステータスマスタ
CREATE TABLE IF NOT EXISTS T_COMN_CONDUCTOR_REGULARLY_STATUS
(
    REGULARLY_STATUS_ID             VARCHAR(2),                                 -- 主キー
    REGULARLY_STATUS_NAME_JA        VARCHAR(255),                               -- 表示名
    REGULARLY_STATUS_NAME_EN        VARCHAR(255),                               -- 表示名
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(REGULARLY_STATUS_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- ConductorNodeインスタンスビュー
CREATE OR REPLACE VIEW V_COMN_CONDUCTOR_NODE_INSTANCE AS
SELECT
  TAB_A.*,
  TAB_B.OPERATION_ID
FROM
  T_COMN_CONDUCTOR_NODE_INSTANCE TAB_A
  LEFT JOIN
  T_COMN_CONDUCTOR_INSTANCE TAB_B ON (TAB_A.CONDUCTOR_INSTANCE_ID = TAB_B.CONDUCTOR_INSTANCE_ID);
CREATE OR REPLACE VIEW V_COMN_CONDUCTOR_NODE_INSTANCE_JNL AS
SELECT
  TAB_A.*,
  TAB_B.OPERATION_ID
FROM
  T_COMN_CONDUCTOR_NODE_INSTANCE_JNL TAB_A
  LEFT JOIN
  T_COMN_CONDUCTOR_INSTANCE TAB_B ON (TAB_A.CONDUCTOR_INSTANCE_ID = TAB_B.CONDUCTOR_INSTANCE_ID);

