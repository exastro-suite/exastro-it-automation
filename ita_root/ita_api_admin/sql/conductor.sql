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
    CONDUCTOR_INSTANCE_NAME         VARCHAR(255),                               -- Conductorインスタンス名
    I_CONDUCTOR_CLASS_ID            VARCHAR(40),                                -- インスタンス元のクラスID
    I_CONDUCTOR_NAME                VARCHAR(255),                               -- インスタンス元のクラス名
    I_CLASS_JSON                    TEXT,                                       -- インスタンス元の設定
    I_NOTE                          TEXT,                                       -- インスタンス元の備考
    CLASS_JSON                      TEXT,                                       -- クラス設定
    OPERATION_ID                    VARCHAR(40),                                -- オペレーションID
    I_OPERATION_NAME                VARCHAR(255),                               -- 実行時のオペレーション名
    EXECUTION_USER                  VARCHAR(255),                               -- 作業実行ユーザー
    PARENT_CONDUCTOR_INSTANCE_ID    VARCHAR(40),                                -- 親ConductorインスタンスID
    PARENT_CONDUCTOR_INSTANCE_NAME  VARCHAR(255),                               -- 親Conductorインスタンス名
    TOP_CONDUCTOR_INSTANCE_ID       VARCHAR(40),                                -- 最上位ConductorインスタンスID
    TOP_CONDUCTOR_INSTANCE_NAME     VARCHAR(255),                               -- 最上位Conductorインスタンス名
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
    CONDUCTOR_INSTANCE_NAME         VARCHAR(255),                               -- Conductorインスタンス名
    I_CONDUCTOR_CLASS_ID            VARCHAR(40),                                -- インスタンス元のクラスID
    I_CONDUCTOR_NAME                VARCHAR(255),                               -- インスタンス元のクラス名
    I_CLASS_JSON                    TEXT,                                       -- インスタンス元の設定
    I_NOTE                          TEXT,                                       -- インスタンス元の備考
    CLASS_JSON                      TEXT,                                       -- クラス設定
    OPERATION_ID                    VARCHAR(40),                                -- オペレーションID
    I_OPERATION_NAME                VARCHAR(255),                               -- 実行時のオペレーション名
    EXECUTION_USER                  VARCHAR(255),                               -- 作業実行ユーザー
    PARENT_CONDUCTOR_INSTANCE_ID    VARCHAR(40),                                -- 親ConductorインスタンスID
    PARENT_CONDUCTOR_INSTANCE_NAME  VARCHAR(255),                               -- 親Conductorインスタンス名
    TOP_CONDUCTOR_INSTANCE_ID       VARCHAR(40),                                -- 最上位ConductorインスタンスID
    TOP_CONDUCTOR_INSTANCE_NAME     VARCHAR(255),                               -- 最上位Conductorインスタンス名
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
    PARENT_CONDUCTOR_INSTANCE_NAME  VARCHAR(255),                               -- 親Conductorインスタンス名
    TOP_CONDUCTOR_INSTANCE_ID       VARCHAR(40),                                -- 最上位のConductorインスタンスID
    TOP_CONDUCTOR_INSTANCE_NAME     VARCHAR(255),                               -- 最上位のConductorインスタンス名
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
    PARENT_CONDUCTOR_INSTANCE_NAME  VARCHAR(255),                               -- 親Conductorインスタンス名
    TOP_CONDUCTOR_INSTANCE_ID       VARCHAR(40),                                -- 最上位のConductorインスタンスID
    TOP_CONDUCTOR_INSTANCE_NAME     VARCHAR(255),                               -- 最上位のConductorインスタンス名
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




