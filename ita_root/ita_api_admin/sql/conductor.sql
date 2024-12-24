-- Conductorインターフェース
CREATE TABLE T_COMN_CONDUCTOR_IF_INFO
(
    CONDUCTOR_IF_INFO_ID            VARCHAR(40),                                -- ConductorインターフェースID
    CONDUCTOR_REFRESH_INTERVAL      INT,                                        -- 状態監視周期(単位ミリ秒)
    NOTE                            VARCHAR(4000),                              -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(CONDUCTOR_IF_INFO_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_COMN_CONDUCTOR_IF_INFO_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    CONDUCTOR_IF_INFO_ID            VARCHAR(40),                                -- ConductorインターフェースID
    CONDUCTOR_REFRESH_INTERVAL      INT,                                        -- 状態監視周期(単位ミリ秒)
    NOTE                            VARCHAR(4000),                              -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- Conductor通知
CREATE TABLE T_COMN_CONDUCTOR_NOTICE
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

CREATE TABLE T_COMN_CONDUCTOR_NOTICE_JNL
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



-- Conductorクラス
CREATE TABLE T_COMN_CONDUCTOR_CLASS
(
    CONDUCTOR_CLASS_ID              VARCHAR(40),                                -- ConductorクラスID
    CONDUCTOR_NAME                  VARCHAR(255),                               -- Conductor名称
    SETTING                         TEXT,                                       -- 設定
    NOTE                            VARCHAR(4000),                              -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(CONDUCTOR_CLASS_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_COMN_CONDUCTOR_CLASS_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    CONDUCTOR_CLASS_ID              VARCHAR(40),                                -- ConductorクラスID
    CONDUCTOR_NAME                  VARCHAR(255),                               -- Conductor名称
    SETTING                         TEXT,                                       -- 設定
    NOTE                            VARCHAR(4000),                              -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- Conductorインスタンス
CREATE TABLE T_COMN_CONDUCTOR_INSTANCE
(
    CONDUCTOR_INSTANCE_ID           VARCHAR(40),                                -- ConductorインスタンスID
    CONDUCTOR_INSTANCE_NAME         VARCHAR(255),                               -- Conductor名称
    I_CONDUCTOR_CLASS_ID            VARCHAR(40),                                -- インスタンス元のクラスID
    I_CONDUCTOR_NAME                VARCHAR(255),                               -- インスタンス元のクラス名
    I_CLASS_JSON                    TEXT,                                       -- インスタンス元の設定
    I_NOTE                          TEXT,                                       -- インスタンス元の備考
    CLASS_JSON                      TEXT,                                       -- クラス設定
    OPERATION_ID                    VARCHAR(40),                                -- オペレーションID
    I_OPERATION_NAME                VARCHAR(255),                               -- 実行時のオペレーション名
    EXECUTION_USER                  VARCHAR(255),                               -- 作業実行ユーザー
    PARENT_CONDUCTOR_INSTANCE_ID    VARCHAR(40),                                -- 親ConductorインスタンスID
    PARENT_CONDUCTOR_INSTANCE_NAME  VARCHAR(255),                               -- 親Conductor名称
    TOP_CONDUCTOR_INSTANCE_ID       VARCHAR(40),                                -- 最上位ConductorインスタンスID
    TOP_CONDUCTOR_INSTANCE_NAME     VARCHAR(255),                               -- 最上位Conductor名称
    NOTICE_INFO                     TEXT,                                       -- 通知設定
    NOTICE_DEFINITION               TEXT,                                       -- 通知定義
    STATUS_ID                       VARCHAR(40),                                -- ステータスID
    ABORT_EXECUTE_FLAG              VARCHAR(1),                                 -- 緊急停止フラグ
    TIME_REGISTER                   DATETIME(6),                                -- 登録日時
    TIME_BOOK                       DATETIME(6),                                -- 予約日時
    TIME_START                      DATETIME(6),                                -- 開始日時
    TIME_END                        DATETIME(6),                                -- 終了日時
    EXEC_LOG                        TEXT,                                       -- 実行ログ
    NOTICE_LOG                      TEXT,                                       -- 通知ログ
    NOTE                            VARCHAR(4000),                              -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(CONDUCTOR_INSTANCE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_COMN_CONDUCTOR_INSTANCE_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    CONDUCTOR_INSTANCE_ID           VARCHAR(40),                                -- ConductorインスタンスID
    CONDUCTOR_INSTANCE_NAME         VARCHAR(255),                               -- Conductor名称
    I_CONDUCTOR_CLASS_ID            VARCHAR(40),                                -- インスタンス元のクラスID
    I_CONDUCTOR_NAME                VARCHAR(255),                               -- インスタンス元のクラス名
    I_CLASS_JSON                    TEXT,                                       -- インスタンス元の設定
    I_NOTE                          TEXT,                                       -- インスタンス元の備考
    CLASS_JSON                      TEXT,                                       -- クラス設定
    OPERATION_ID                    VARCHAR(40),                                -- オペレーションID
    I_OPERATION_NAME                VARCHAR(255),                               -- 実行時のオペレーション名
    EXECUTION_USER                  VARCHAR(255),                               -- 作業実行ユーザー
    PARENT_CONDUCTOR_INSTANCE_ID    VARCHAR(40),                                -- 親ConductorインスタンスID
    PARENT_CONDUCTOR_INSTANCE_NAME  VARCHAR(255),                               -- 親Conductor名称
    TOP_CONDUCTOR_INSTANCE_ID       VARCHAR(40),                                -- 最上位ConductorインスタンスID
    TOP_CONDUCTOR_INSTANCE_NAME     VARCHAR(255),                               -- 最上位Conductor名称
    NOTICE_INFO                     TEXT,                                       -- 通知設定
    NOTICE_DEFINITION               TEXT,                                       -- 通知定義
    STATUS_ID                       VARCHAR(40),                                -- ステータスID
    ABORT_EXECUTE_FLAG              VARCHAR(1),                                 -- 緊急停止フラグ
    TIME_REGISTER                   DATETIME(6),                                -- 登録日時
    TIME_BOOK                       DATETIME(6),                                -- 予約日時
    TIME_START                      DATETIME(6),                                -- 開始日時
    TIME_END                        DATETIME(6),                                -- 終了日時
    EXEC_LOG                        TEXT,                                       -- 実行ログ
    NOTICE_LOG                      TEXT,                                       -- 通知ログ
    NOTE                            VARCHAR(4000),                              -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- ConductorNodeインスタンス
CREATE TABLE T_COMN_CONDUCTOR_NODE_INSTANCE
(
    NODE_INSTANCE_ID                VARCHAR(40),                                -- NodeインスタンスID
    I_NODE_NAME                     VARCHAR(255),                               -- インスタンス元のNode名
    I_NOTE                          TEXT,                                       -- インスタンス元の備考
    NODE_TYPE_ID                    VARCHAR(40),                                -- Nodeタイプ
    ORCHESTRA_ID                    VARCHAR(40),                                -- Movement種別
    I_MOVEMENT_ID                   VARCHAR(40),                                -- インスタンス元のMovementID
    I_MOVEMENT_NAME                 VARCHAR(255),                               -- インスタンス元のMovement名
    I_MOVEMENT_JSON                 TEXT,                                       -- インスタンス元のMovement情報
    I_CONDUCTOR_CLASS_ID            VARCHAR(40),                                -- インスタンス元のConductorID
    I_CONDUCTOR_CLASS_NAME          VARCHAR(255),                               -- インスタンス元のConductor名
    I_CONDUCTOR_CLASS_JSON          TEXT,                                       -- インスタンス元のConductor情報
    CONDUCTOR_INSTANCE_ID           VARCHAR(40),                                -- ConductorインスタンスID
    PARENT_CONDUCTOR_INSTANCE_ID    VARCHAR(40),                                -- 親ConductorインスタンスID
    PARENT_CONDUCTOR_INSTANCE_NAME  VARCHAR(255),                               -- 親Conductor名称
    TOP_CONDUCTOR_INSTANCE_ID       VARCHAR(40),                                -- 最上位のConductorインスタンスID
    TOP_CONDUCTOR_INSTANCE_NAME     VARCHAR(255),                               -- 最上位のConductor名称
    EXECUTION_ID                    VARCHAR(40),                                -- 作業実行ID
    STATUS_ID                       VARCHAR(40),                                -- ステータスID
    STATUS_FILE                     VARCHAR(40),                                -- ステータスファイル
    RELEASED_FLAG                   VARCHAR(1)  ,                               -- 保留解除フラグ
    EXE_SKIP_FLAG                   VARCHAR(1)  ,                               -- スキップ
    END_TYPE                        VARCHAR(1)  ,                               -- 終了タイプ
    OVRD_OPERATION_ID               VARCHAR(40),                                -- 個別オペレーションID
    OVRD_I_OPERATION_NAME           VARCHAR(255),                               -- 個別オペレーション名
    TIME_REGISTER                   DATETIME(5),                                -- 登録日時
    TIME_START                      DATETIME(6),                                -- 開始日時
    TIME_END                        DATETIME(6),                                -- 終了日時
    NOTE                            VARCHAR(4000),                              -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(NODE_INSTANCE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_COMN_CONDUCTOR_NODE_INSTANCE_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    NODE_INSTANCE_ID                VARCHAR(40),                                -- NodeインスタンスID
    I_NODE_NAME                     VARCHAR(255),                               -- インスタンス元のNode名
    I_NOTE                          TEXT,                                       -- インスタンス元の備考
    NODE_TYPE_ID                    VARCHAR(40),                                -- Nodeタイプ
    ORCHESTRA_ID                    VARCHAR(40),                                -- Movement種別
    I_MOVEMENT_ID                   VARCHAR(40),                                -- インスタンス元のMovementID
    I_MOVEMENT_NAME                 VARCHAR(255),                               -- インスタンス元のMovement名
    I_MOVEMENT_JSON                 TEXT,                                       -- インスタンス元のMovement情報
    I_CONDUCTOR_CLASS_ID            VARCHAR(40),                                -- インスタンス元のConductorID
    I_CONDUCTOR_CLASS_NAME          VARCHAR(255),                               -- インスタンス元のConductor名
    I_CONDUCTOR_CLASS_JSON          TEXT,                                       -- インスタンス元のConductor情報
    CONDUCTOR_INSTANCE_ID           VARCHAR(40),                                -- ConductorインスタンスID
    PARENT_CONDUCTOR_INSTANCE_ID    VARCHAR(40),                                -- 親ConductorインスタンスID
    PARENT_CONDUCTOR_INSTANCE_NAME  VARCHAR(255),                               -- 親Conductor名称
    TOP_CONDUCTOR_INSTANCE_ID       VARCHAR(40),                                -- 最上位のConductorインスタンスID
    TOP_CONDUCTOR_INSTANCE_NAME     VARCHAR(255),                               -- 最上位のConductor名称
    EXECUTION_ID                    VARCHAR(40),                                -- 作業実行ID
    STATUS_ID                       VARCHAR(40),                                -- ステータスID
    STATUS_FILE                     VARCHAR(40),                                -- ステータスファイル
    RELEASED_FLAG                   VARCHAR(1)  ,                               -- 保留解除フラグ
    EXE_SKIP_FLAG                   VARCHAR(1)  ,                               -- スキップ
    END_TYPE                        VARCHAR(1)  ,                               -- 終了タイプ
    OVRD_OPERATION_ID               VARCHAR(40),                                -- 個別オペレーションID
    OVRD_I_OPERATION_NAME           VARCHAR(255),                               -- 個別オペレーション名
    TIME_REGISTER                   DATETIME(5),                                -- 登録日時
    TIME_START                      DATETIME(6),                                -- 開始日時
    TIME_END                        DATETIME(6),                                -- 終了日時
    NOTE                            VARCHAR(4000),                              -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- Conductorステータスマスタ
CREATE TABLE T_COMN_CONDUCTOR_STATUS
(
    STATUS_ID                       VARCHAR(2),                                 -- 主キー
    STATUS_NAME_JA                  VARCHAR(255),                               -- 表示名
    STATUS_NAME_EN                  VARCHAR(255),                               -- 表示名
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(STATUS_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- ConductorNodeステータスマスタ
CREATE TABLE T_COMN_CONDUCTOR_NODE_STATUS
(
    STATUS_ID                       VARCHAR(2),                                 -- 主キー
    STATUS_NAME_JA                  VARCHAR(255),                               -- 表示名
    STATUS_NAME_EN                  VARCHAR(255),                               -- 表示名
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(STATUS_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- ConductorNodeマスタ
CREATE TABLE T_COMN_CONDUCTOR_NODE
(
    NODE_TYPE_ID                    VARCHAR(40),                                -- 主キー
    NODE_TYPE_NAME                  VARCHAR(255),                               -- 表示名
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(NODE_TYPE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- Conductor定期作業実行リスト
CREATE TABLE T_COMN_CONDUCTOR_REGULARLY_LIST
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
    PATTERN_DAY_OF_WEEK_ID          TEXT,                                       -- 実行曜日ID
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

CREATE TABLE T_COMN_CONDUCTOR_REGULARLY_LIST_JNL
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
    PATTERN_DAY_OF_WEEK_ID          TEXT,                                       -- 実行曜日ID
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
CREATE TABLE T_COMN_CONDUCTOR_REGULARLY_PERIOD
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
CREATE TABLE T_COMN_CONDUCTOR_DAY_OF_WEEK
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
CREATE TABLE T_COMN_CONDUCTOR_WEEK_NUMBER
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
CREATE TABLE T_COMN_CONDUCTOR_REGULARLY_STATUS
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
CREATE VIEW V_COMN_CONDUCTOR_NODE_INSTANCE AS
SELECT
  TAB_A.*,
  TAB_B.OPERATION_ID
FROM
  T_COMN_CONDUCTOR_NODE_INSTANCE TAB_A
  LEFT JOIN
  T_COMN_CONDUCTOR_INSTANCE TAB_B ON (TAB_A.CONDUCTOR_INSTANCE_ID = TAB_B.CONDUCTOR_INSTANCE_ID);
CREATE VIEW V_COMN_CONDUCTOR_NODE_INSTANCE_JNL AS
SELECT
  TAB_A.*,
  TAB_B.OPERATION_ID
FROM
  T_COMN_CONDUCTOR_NODE_INSTANCE_JNL TAB_A
  LEFT JOIN
  T_COMN_CONDUCTOR_INSTANCE TAB_B ON (TAB_A.CONDUCTOR_INSTANCE_ID = TAB_B.CONDUCTOR_INSTANCE_ID);



-- インデックス
CREATE INDEX IND_T_COMN_CONDUCTOR_CLASS_01 ON T_COMN_CONDUCTOR_CLASS (DISUSE_FLAG);
CREATE INDEX IND_T_COMN_CONDUCTOR_CLASS_02 ON T_COMN_CONDUCTOR_CLASS (DISUSE_FLAG,CONDUCTOR_NAME);
CREATE INDEX IND_T_COMN_CONDUCTOR_INSTANCE_01 ON T_COMN_CONDUCTOR_INSTANCE (DISUSE_FLAG);
CREATE INDEX IND_T_COMN_CONDUCTOR_INSTANCE_02 ON T_COMN_CONDUCTOR_INSTANCE (DISUSE_FLAG,STATUS_ID,TIME_BOOK,TIME_REGISTER);
CREATE INDEX IND_T_COMN_CONDUCTOR_NODE_INSTANCE_01 ON T_COMN_CONDUCTOR_NODE_INSTANCE (DISUSE_FLAG);
CREATE INDEX IND_T_COMN_CONDUCTOR_NODE_INSTANCE_02 ON T_COMN_CONDUCTOR_NODE_INSTANCE (DISUSE_FLAG,CONDUCTOR_INSTANCE_ID,NODE_TYPE_ID );
CREATE INDEX IND_T_COMN_CONDUCTOR_NODE_INSTANCE_03 ON T_COMN_CONDUCTOR_NODE_INSTANCE (DISUSE_FLAG,CONDUCTOR_INSTANCE_ID,NODE_TYPE_ID,EXECUTION_ID );
CREATE INDEX IND_T_COMN_CONDUCTOR_STATUS_01 ON T_COMN_CONDUCTOR_STATUS (DISUSE_FLAG);
CREATE INDEX IND_T_COMN_CONDUCTOR_NODE_STATUS_01 ON T_COMN_CONDUCTOR_NODE_STATUS (DISUSE_FLAG);
CREATE INDEX IND_T_COMN_CONDUCTOR_NODE_01 ON T_COMN_CONDUCTOR_NODE (DISUSE_FLAG);
CREATE INDEX IND_T_COMN_CONDUCTOR_IF_INFO_01 ON T_COMN_CONDUCTOR_IF_INFO (DISUSE_FLAG);



