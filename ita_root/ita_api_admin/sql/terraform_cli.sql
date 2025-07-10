-- インターフェース情報
CREATE TABLE T_TERC_IF_INFO
(
    TERRAFORM_IF_INFO_ID            VARCHAR(40),                                -- 項番(UUID)
    NULL_DATA_HANDLING_FLG          VARCHAR(2),                                 -- NULL連携
    TERRAFORM_REFRESH_INTERVAL      INT,                                        -- 状態監視周期(単位ミリ秒)
    TERRAFORM_TAILLOG_LINES         INT,                                        -- 進行状態表示行数
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(TERRAFORM_IF_INFO_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_TERC_IF_INFO_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    TERRAFORM_IF_INFO_ID            VARCHAR(40),                                -- 項番(UUID)
    NULL_DATA_HANDLING_FLG          VARCHAR(2),                                 -- NULL連携
    TERRAFORM_REFRESH_INTERVAL      INT,                                        -- 状態監視周期(単位ミリ秒)
    TERRAFORM_TAILLOG_LINES         INT,                                        -- 進行状態表示行数
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- Workspace管理
CREATE TABLE T_TERC_WORKSPACE
(
    WORKSPACE_ID                    VARCHAR(40),                                -- 項番(UUID)
    WORKSPACE_NAME                  VARCHAR(90),                                -- Workspace名
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(WORKSPACE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_TERC_WORKSPACE_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    WORKSPACE_ID                    VARCHAR(40),                                -- 項番(UUID)
    WORKSPACE_NAME                  VARCHAR(90),                                -- Workspace名
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- Movement一覧
CREATE OR REPLACE VIEW V_TERC_MOVEMENT AS
SELECT
    MOVEMENT_ID,
    MOVEMENT_NAME,
    ITA_EXT_STM_ID,
    TIME_LIMIT,
    TERC_WORKSPACE_ID,
    NOTE,
    DISUSE_FLAG,
    LAST_UPDATE_TIMESTAMP,
    LAST_UPDATE_USER
FROM
    T_COMN_MOVEMENT
WHERE
    ITA_EXT_STM_ID = 5
;
CREATE OR REPLACE VIEW V_TERC_MOVEMENT_JNL AS
SELECT
    JOURNAL_SEQ_NO,
    JOURNAL_REG_DATETIME,
    JOURNAL_ACTION_CLASS,
    MOVEMENT_ID,
    MOVEMENT_NAME,
    ITA_EXT_STM_ID,
    TIME_LIMIT,
    TERC_WORKSPACE_ID,
    NOTE,
    DISUSE_FLAG,
    LAST_UPDATE_TIMESTAMP,
    LAST_UPDATE_USER
FROM
    T_COMN_MOVEMENT_JNL
WHERE
    ITA_EXT_STM_ID = 5
;



-- Module素材集
CREATE TABLE T_TERC_MODULE
(
    MODULE_MATTER_ID                VARCHAR(40),                                -- 項番(UUID)
    MODULE_MATTER_NAME              VARCHAR(255),                               -- Module素材名
    MODULE_MATTER_FILE              VARCHAR(255),                               -- Module素材
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(MODULE_MATTER_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_TERC_MODULE_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    MODULE_MATTER_ID                VARCHAR(40),                                -- 項番(UUID)
    MODULE_MATTER_NAME              VARCHAR(255),                               -- Module素材名
    MODULE_MATTER_FILE              VARCHAR(255),                               -- Module素材
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- Movement-Module紐付
CREATE TABLE T_TERC_MVMT_MOD_LINK
(
    MVMT_MOD_LINK_ID                VARCHAR(40),                                -- 項番(UUID)
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement(ID連携)
    MODULE_MATTER_ID                VARCHAR(40),                                -- Module素材(ID連携)
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(MVMT_MOD_LINK_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_TERC_MVMT_MOD_LINK_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    MVMT_MOD_LINK_ID                VARCHAR(40),                                -- 項番(UUID)
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement(ID連携)
    MODULE_MATTER_ID                VARCHAR(40),                                -- Module素材(ID連携)
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 変数ネスト管理
CREATE TABLE T_TERC_NESTVAR_MEMBER_MAX_COL
(
    MAX_COL_SEQ_ID                  VARCHAR(40),                                -- 項番(UUID)
    VARS_ID                         VARCHAR(40),                                -- 変数(ID連携)
    MEMBER_VARS_ID                  VARCHAR(40),                                -- メンバー変数(ID連携)
    MAX_COL_SEQ                     INT,                                        -- 最大繰り返し数
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(MAX_COL_SEQ_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_TERC_NESTVAR_MEMBER_MAX_COL_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    MAX_COL_SEQ_ID                  VARCHAR(40),                                -- 項番(UUID)
    VARS_ID                         VARCHAR(40),                                -- 変数(ID連携)
    MEMBER_VARS_ID                  VARCHAR(40),                                -- メンバー変数(ID連携)
    MAX_COL_SEQ                     INT,                                        -- 最大繰り返し数
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 代入値自動登録設定
CREATE TABLE T_TERC_VALUE_AUTOREG
(
    VALUE_AUTOREG_ID                VARCHAR(40),                                -- 項番(UUID)
    MENU_NAME_REST                  VARCHAR(40),                                -- メニュー名(REST)
    MENU_ID                         VARCHAR(40),                                -- メニュー名
    COLUMN_LIST_ID                  VARCHAR(40),                                -- 項目名
    COLUMN_ASSIGN_SEQ               INT,                                        -- 代入順序
    COL_TYPE                        VARCHAR(2),                                 -- 登録方式
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement(ID連携)
    MVMT_VAR_LINK_ID                VARCHAR(40),                                -- 変数名(ID連携)
    HCL_FLAG                        VARCHAR(2),                                 -- HCL設定
    MEMBER_VARS_ID                  VARCHAR(40),                                -- メンバー変数(ID連携)
    ASSIGN_SEQ                      INT,                                        -- 代入順序
    NULL_DATA_HANDLING_FLG          VARCHAR(2),                                 -- NULL連携
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(VALUE_AUTOREG_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_TERC_VALUE_AUTOREG_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    VALUE_AUTOREG_ID                VARCHAR(40),                                -- 項番(UUID)
    MENU_NAME_REST                  VARCHAR(40),                                -- メニュー名(REST)
    MENU_ID                         VARCHAR(40),                                -- メニュー名
    COLUMN_LIST_ID                  VARCHAR(40),                                -- 項目名
    COLUMN_ASSIGN_SEQ               INT,                                        -- 代入順序
    COL_TYPE                        VARCHAR(2),                                 -- 登録方式
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement(ID連携)
    MVMT_VAR_LINK_ID                VARCHAR(40),                                -- 変数名(ID連携)
    HCL_FLAG                        VARCHAR(2),                                 -- HCL設定
    MEMBER_VARS_ID                  VARCHAR(40),                                -- メンバー変数(ID連携)
    ASSIGN_SEQ                      INT,                                        -- 代入順序
    NULL_DATA_HANDLING_FLG          VARCHAR(2),                                 -- NULL連携
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 作業管理
CREATE TABLE T_TERC_EXEC_STS_INST
(
    EXECUTION_NO                    VARCHAR(40),                                -- 項番(UUID)
    RUN_MODE                        VARCHAR(2),                                 -- 実行種別
    STATUS_ID                       VARCHAR(2),                                 -- ステータス
    CONDUCTOR_INSTANCE_NO           VARCHAR(40),                                -- Conductorインスタンス番号
    CONDUCTOR_NAME                  VARCHAR(255),                               -- 呼び出し元Conductor
    EXECUTION_USER                  VARCHAR(255),                               -- 実行ユーザ
    TIME_REGISTER                   DATETIME(6),                                -- 登録日時
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement/ID
    I_MOVEMENT_NAME                 VARCHAR(255),                               -- Movement/名称
    I_TIME_LIMIT                    INT,                                        -- Movement/遅延タイマー
    I_WORKSPACE_ID                  VARCHAR(40),                                -- Movement/Terraform利用情報/WorkspaceID
    I_WORKSPACE_NAME                VARCHAR(90),                                -- Movement/Terraform利用情報/Workspace名
    OPERATION_ID                    VARCHAR(40),                                -- オペレーション/No.
    I_OPERATION_NAME                VARCHAR(255),                               -- オペレーション/名称
    FILE_INPUT                      VARCHAR(1024),                              -- 入力データ/投入データ
    FILE_RESULT                     VARCHAR(1024),                              -- 出力データ/結果データ
    TIME_BOOK                       DATETIME(6),                                -- 作業状況/予約日時
    TIME_START                      DATETIME(6),                                -- 作業状況/開始日時
    TIME_END                        DATETIME(6),                                -- 作業状況/終了日時
    LOGFILELIST_JSON                TEXT,                                       -- 分割された実行ログ情報
    MULTIPLELOG_MODE                INT,                                        -- 実行ログ分割フラグ
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(EXECUTION_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_TERC_EXEC_STS_INST_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    EXECUTION_NO                    VARCHAR(40),                                -- 項番(UUID)
    RUN_MODE                        VARCHAR(2),                                 -- 実行種別
    STATUS_ID                       VARCHAR(2),                                 -- ステータス
    CONDUCTOR_INSTANCE_NO           VARCHAR(40),                                -- Conductorインスタンス番号
    CONDUCTOR_NAME                  VARCHAR(255),                               -- 呼び出し元Conductor
    EXECUTION_USER                  VARCHAR(255),                               -- 実行ユーザ
    TIME_REGISTER                   DATETIME(6),                                -- 登録日時
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement/ID
    I_MOVEMENT_NAME                 VARCHAR(255),                               -- Movement/名称
    I_TIME_LIMIT                    INT,                                        -- Movement/遅延タイマー
    I_WORKSPACE_ID                  VARCHAR(40),                                -- Movement/Terraform利用情報/WorkspaceID
    I_WORKSPACE_NAME                VARCHAR(90),                                -- Movement/Terraform利用情報/Workspace名
    OPERATION_ID                    VARCHAR(40),                                -- オペレーション/No.
    I_OPERATION_NAME                VARCHAR(255),                               -- オペレーション/名称
    FILE_INPUT                      VARCHAR(1024),                              -- 入力データ/投入データ
    FILE_RESULT                     VARCHAR(1024),                              -- 出力データ/結果データ
    TIME_BOOK                       DATETIME(6),                                -- 作業状況/予約日時
    TIME_START                      DATETIME(6),                                -- 作業状況/開始日時
    TIME_END                        DATETIME(6),                                -- 作業状況/終了日時
    LOGFILELIST_JSON                TEXT,                                       -- 分割された実行ログ情報
    MULTIPLELOG_MODE                INT,                                        -- 実行ログ分割フラグ
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 代入値管理
CREATE TABLE T_TERC_VALUE
(
    ASSIGN_ID                       VARCHAR(40),                                -- 項番(UUID)
    EXECUTION_NO                    VARCHAR(40),                                -- 作業No.
    OPERATION_ID                    VARCHAR(40),                                -- オペレーション(ID連携)
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement(ID連携)
    MVMT_VAR_LINK_ID                VARCHAR(40),                                -- 変数名(ID連携)
    HCL_FLAG                        VARCHAR(2),                                 -- HCL設定
    MEMBER_VARS_ID                  VARCHAR(40),                                -- メンバー変数名(ID連携)
    ASSIGN_SEQ                      INT,                                        -- 代入順序
    SENSITIVE_FLAG                  VARCHAR(2),                                 -- Sensitive設定
    VARS_ENTRY                      LONGTEXT,                                   -- 具体値
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ASSIGN_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_TERC_VALUE_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    ASSIGN_ID                       VARCHAR(40),                                -- 項番(UUID)
    EXECUTION_NO                    VARCHAR(40),                                -- 作業No.
    OPERATION_ID                    VARCHAR(40),                                -- オペレーション(ID連携)
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement(ID連携)
    MVMT_VAR_LINK_ID                VARCHAR(40),                                -- 変数名(ID連携)
    HCL_FLAG                        VARCHAR(2),                                 -- HCL設定
    MEMBER_VARS_ID                  VARCHAR(40),                                -- メンバー変数名(ID連携)
    ASSIGN_SEQ                      INT,                                        -- 代入順序
    SENSITIVE_FLAG                  VARCHAR(2),                                 -- Sensitive設定
    VARS_ENTRY                      LONGTEXT,                                   -- 具体値
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- Module-変数紐付
CREATE TABLE T_TERC_MOD_VAR_LINK
(
    MODULE_VARS_LINK_ID             VARCHAR(40),                                -- 項番(UUID)
    MODULE_MATTER_ID                VARCHAR(40),                                -- Module素材(ID連携)
    VARS_NAME                       VARCHAR(128),                               -- 変数名
    TYPE_ID                         VARCHAR(2),                                 -- タイプ(ID連携)
    VARS_VALUE                      TEXT,                                       -- デフォルト値
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(MODULE_VARS_LINK_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_TERC_MOD_VAR_LINK_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    MODULE_VARS_LINK_ID             VARCHAR(40),                                -- 項番(UUID)
    MODULE_MATTER_ID                VARCHAR(40),                                -- Module素材(ID連携)
    VARS_NAME                       VARCHAR(128),                               -- 変数名
    TYPE_ID                         VARCHAR(2),                                 -- タイプ(ID連携)
    VARS_VALUE                      TEXT,                                       -- デフォルト値
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- メンバー変数管理
CREATE TABLE T_TERC_VAR_MEMBER
(
    CHILD_MEMBER_VARS_ID            VARCHAR(40),                                -- 項番(UUID)
    PARENT_VARS_ID                  VARCHAR(40),                                -- 親変数(Module-変数紐付のID連携)
    PARENT_MEMBER_VARS_ID           VARCHAR(40),                                -- 親メンバー変数のID(自分自身とID連携)
    CHILD_MEMBER_VARS_NEST          TEXT,                                       -- メンバー変数のキー(フル)
    CHILD_MEMBER_VARS_KEY           TEXT,                                       -- メンバー変数のキー
    CHILD_VARS_TYPE_ID              VARCHAR(40),                                -- 子メンバ変数のタイプID
    ARRAY_NEST_LEVEL                INT,                                        -- 子メンバ変数の階層
    ASSIGN_SEQ                      INT,                                        -- 代入順序
    CHILD_MEMBER_VARS_VALUE         TEXT,                                       -- デフォルト値
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(CHILD_MEMBER_VARS_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_TERC_VAR_MEMBER_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    CHILD_MEMBER_VARS_ID            VARCHAR(40),                                -- 項番(UUID)
    PARENT_VARS_ID                  VARCHAR(40),                                -- 親変数(Module-変数紐付のID連携)
    PARENT_MEMBER_VARS_ID           VARCHAR(40),                                -- 親メンバー変数のID(自分自身とID連携)
    CHILD_MEMBER_VARS_NEST          TEXT,                                       -- メンバー変数のキー(フル)
    CHILD_MEMBER_VARS_KEY           TEXT,                                       -- メンバー変数のキー
    CHILD_VARS_TYPE_ID              VARCHAR(40),                                -- 子メンバ変数のタイプID
    ARRAY_NEST_LEVEL                INT,                                        -- 子メンバ変数の階層
    ASSIGN_SEQ                      INT,                                        -- 代入順序
    CHILD_MEMBER_VARS_VALUE         TEXT,                                       -- デフォルト値
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- Movement-変数紐付
CREATE TABLE T_TERC_MVMT_VAR_LINK
(
    MVMT_VAR_LINK_ID                VARCHAR(40),                                -- 項番(UUID)
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement(ID連携)
    MODULE_VARS_LINK_ID             VARCHAR(40),                                -- Module-変数紐付(ID連携)
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(MVMT_VAR_LINK_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_TERC_MVMT_VAR_LINK_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    MVMT_VAR_LINK_ID                VARCHAR(40),                                -- 項番(UUID)
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement(ID連携)
    MODULE_VARS_LINK_ID             VARCHAR(40),                                -- Module-変数紐付(ID連携)
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- Movement-メンバー変数紐付
CREATE TABLE T_TERC_MVMT_VAR_MEMBER_LINK
(
    MVMT_VAR_MEMBER_LINK_ID         VARCHAR(40),                                -- 項番(UUID)
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement(ID連携)
    MODULE_VARS_LINK_ID             VARCHAR(40),                                -- Module-変数紐付(ID連携)
    CHILD_MEMBER_VARS_ID            VARCHAR(40),                                -- メンバー変数ID(ID連携)
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(MVMT_VAR_MEMBER_LINK_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_TERC_MVMT_VAR_MEMBER_LINK_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    MVMT_VAR_MEMBER_LINK_ID         VARCHAR(40),                                -- 項番(UUID)
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement(ID連携)
    MODULE_VARS_LINK_ID             VARCHAR(40),                                -- Module-変数紐付(ID連携)
    CHILD_MEMBER_VARS_ID            VARCHAR(40),                                -- メンバー変数ID(ID連携)
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- メンバー変数管理(VIEW)
CREATE OR REPLACE VIEW V_TERC_VAR_MEMBER AS
SELECT
        CHILD_MEMBER_VARS_ID,
        PARENT_VARS_ID,
        PARENT_MEMBER_VARS_ID,
        CHILD_MEMBER_VARS_NEST,
        CHILD_MEMBER_VARS_KEY,
        CHILD_VARS_TYPE_ID,
        ARRAY_NEST_LEVEL,
        ASSIGN_SEQ,
        CHILD_MEMBER_VARS_VALUE,
          CASE
            WHEN
            NOT EXISTS(
              SELECT PARENT_MEMBER_VARS_ID FROM T_TERC_VAR_MEMBER AS TAB_B WHERE TAB_B.PARENT_MEMBER_VARS_ID = TAB_A.CHILD_MEMBER_VARS_ID AND TAB_B.DISUSE_FLAG = 0 OR TAB_A.CHILD_VARS_TYPE_ID = 7 AND TAB_B.DISUSE_FLAG = 0
            )
            AND
            NOT EXISTS(
              SELECT CHILD_MEMBER_VARS_ID FROM T_TERC_VAR_MEMBER AS TAB_B WHERE PARENT_VARS_ID = TAB_A.PARENT_VARS_ID AND TAB_B.CHILD_VARS_TYPE_ID = 7 AND TAB_B.DISUSE_FLAG = 0
            )
            THEN "1"
            ELSE "0"
          END AS VARS_ASSIGN_FLAG,
        NOTE,
        DISUSE_FLAG,
        LAST_UPDATE_TIMESTAMP,
        LAST_UPDATE_USER
FROM    T_TERC_VAR_MEMBER AS TAB_A;
CREATE OR REPLACE VIEW V_TERC_VAR_MEMBER_JNL AS
SELECT
        JOURNAL_SEQ_NO,
        JOURNAL_REG_DATETIME,
        JOURNAL_ACTION_CLASS,
        CHILD_MEMBER_VARS_ID,
        PARENT_VARS_ID,
        PARENT_MEMBER_VARS_ID,
        CHILD_MEMBER_VARS_NEST,
        CHILD_MEMBER_VARS_KEY,
        CHILD_VARS_TYPE_ID,
        ARRAY_NEST_LEVEL,
        ASSIGN_SEQ,
        CHILD_MEMBER_VARS_VALUE,
          CASE
            WHEN
            NOT EXISTS(
              SELECT PARENT_MEMBER_VARS_ID FROM T_TERC_VAR_MEMBER AS TAB_B WHERE TAB_B.PARENT_MEMBER_VARS_ID = TAB_A.CHILD_MEMBER_VARS_ID AND TAB_B.DISUSE_FLAG = 0 OR TAB_A.CHILD_VARS_TYPE_ID = 7 AND TAB_B.DISUSE_FLAG = 0
            )
            AND
            NOT EXISTS(
              SELECT CHILD_MEMBER_VARS_ID FROM T_TERC_VAR_MEMBER AS TAB_B WHERE PARENT_VARS_ID = TAB_A.PARENT_VARS_ID AND TAB_B.CHILD_VARS_TYPE_ID = 7 AND TAB_B.DISUSE_FLAG = 0
            )
            THEN "1"
            ELSE "0"
          END AS VARS_ASSIGN_FLAG,
        NOTE,
        DISUSE_FLAG,
        LAST_UPDATE_TIMESTAMP,
        LAST_UPDATE_USER
FROM    T_TERC_VAR_MEMBER_JNL AS TAB_A;



-- Movement-変数紐付(VIEW)
CREATE OR REPLACE VIEW V_TERC_MVMT_VAR_LINK AS
SELECT
        TAB_A.MVMT_VAR_LINK_ID,
        TAB_A.MOVEMENT_ID,
        TAB_B.MOVEMENT_NAME,
        TAB_A.MODULE_VARS_LINK_ID,
        TAB_C.MODULE_MATTER_ID,
        TAB_C.VARS_NAME,
        TAB_C.TYPE_ID,
        TAB_C.VARS_VALUE,
        CONCAT(TAB_B.MOVEMENT_NAME,':',TAB_C.VARS_NAME) MOVEMENT_VARS_NAME,
        TAB_A.NOTE,
        TAB_A.DISUSE_FLAG,
        TAB_A.LAST_UPDATE_TIMESTAMP,
        TAB_A.LAST_UPDATE_USER
FROM    T_TERC_MVMT_VAR_LINK AS TAB_A
LEFT JOIN V_TERC_MOVEMENT TAB_B ON ( TAB_A.MOVEMENT_ID = TAB_B.MOVEMENT_ID )
LEFT JOIN T_TERC_MOD_VAR_LINK TAB_C ON ( TAB_A.MODULE_VARS_LINK_ID = TAB_C.MODULE_VARS_LINK_ID )
;
CREATE OR REPLACE VIEW V_TERC_MVMT_VAR_LINK_JNL AS
SELECT
        TAB_A.JOURNAL_SEQ_NO,
        TAB_A.JOURNAL_REG_DATETIME,
        TAB_A.JOURNAL_ACTION_CLASS,
        TAB_A.MODULE_VARS_LINK_ID,
        TAB_C.MODULE_MATTER_ID,
        TAB_C.VARS_NAME,
        TAB_C.TYPE_ID,
        TAB_C.VARS_VALUE,
        CONCAT(TAB_B.MOVEMENT_NAME,':',TAB_C.VARS_NAME) MOVEMENT_VARS_NAME,
        TAB_A.NOTE,
        TAB_A.DISUSE_FLAG,
        TAB_A.LAST_UPDATE_TIMESTAMP,
        TAB_A.LAST_UPDATE_USER
FROM    T_TERC_MVMT_VAR_LINK_JNL AS TAB_A
LEFT JOIN V_TERC_MOVEMENT_JNL TAB_B ON ( TAB_A.MOVEMENT_ID = TAB_B.MOVEMENT_ID )
LEFT JOIN T_TERC_MOD_VAR_LINK_JNL TAB_C ON ( TAB_A.MODULE_VARS_LINK_ID = TAB_C.MODULE_VARS_LINK_ID )
;



-- Movement-メンバー変数紐付(VIEW)
CREATE OR REPLACE VIEW V_TERC_MVMT_VAR_MEMBER_LINK AS
SELECT
        TAB_A.MVMT_VAR_MEMBER_LINK_ID,
        TAB_A.MOVEMENT_ID,
        TAB_B.MOVEMENT_NAME,
        TAB_A.MODULE_VARS_LINK_ID,
        TAB_A.CHILD_MEMBER_VARS_ID,
        TAB_D.CHILD_MEMBER_VARS_NEST,
        CONCAT(TAB_B.MOVEMENT_NAME,':',TAB_C.VARS_NAME,':',TAB_D.CHILD_MEMBER_VARS_NEST) MOVEMENT_VAR_MEMBER_NAME,
        TAB_D.VARS_ASSIGN_FLAG,
        TAB_A.NOTE,
        TAB_A.DISUSE_FLAG,
        TAB_A.LAST_UPDATE_TIMESTAMP,
        TAB_A.LAST_UPDATE_USER
FROM    T_TERC_MVMT_VAR_MEMBER_LINK AS TAB_A
LEFT JOIN V_TERC_MOVEMENT TAB_B ON ( TAB_A.MOVEMENT_ID = TAB_B.MOVEMENT_ID )
LEFT JOIN T_TERC_MOD_VAR_LINK TAB_C ON ( TAB_A.MODULE_VARS_LINK_ID = TAB_C.MODULE_VARS_LINK_ID )
LEFT JOIN V_TERC_VAR_MEMBER TAB_D ON ( TAB_A.CHILD_MEMBER_VARS_ID = TAB_D.CHILD_MEMBER_VARS_ID )
WHERE
TAB_D.VARS_ASSIGN_FLAG = 1
;
CREATE OR REPLACE VIEW V_TERC_MVMT_VAR_MEMBER_LINK_JNL AS
SELECT
        TAB_A.JOURNAL_SEQ_NO,
        TAB_A.JOURNAL_REG_DATETIME,
        TAB_A.JOURNAL_ACTION_CLASS,
        TAB_A.MVMT_VAR_MEMBER_LINK_ID,
        TAB_A.MOVEMENT_ID,
        TAB_B.MOVEMENT_NAME,
        TAB_A.MODULE_VARS_LINK_ID,
        TAB_A.CHILD_MEMBER_VARS_ID,
        TAB_D.CHILD_MEMBER_VARS_NEST,
        CONCAT(TAB_B.MOVEMENT_NAME,':',TAB_C.VARS_NAME,':',TAB_D.CHILD_MEMBER_VARS_NEST) MOVEMENT_VAR_MEMBER_NAME,
        TAB_D.VARS_ASSIGN_FLAG,
        TAB_A.NOTE,
        TAB_A.DISUSE_FLAG,
        TAB_A.LAST_UPDATE_TIMESTAMP,
        TAB_A.LAST_UPDATE_USER
FROM    T_TERC_MVMT_VAR_MEMBER_LINK_JNL AS TAB_A
LEFT JOIN V_TERC_MOVEMENT_JNL TAB_B ON ( TAB_A.MOVEMENT_ID = TAB_B.MOVEMENT_ID )
LEFT JOIN T_TERC_MOD_VAR_LINK_JNL TAB_C ON ( TAB_A.MODULE_VARS_LINK_ID = TAB_C.MODULE_VARS_LINK_ID )
LEFT JOIN V_TERC_VAR_MEMBER_JNL TAB_D ON ( TAB_A.CHILD_MEMBER_VARS_ID = TAB_D.CHILD_MEMBER_VARS_ID )
WHERE
TAB_D.VARS_ASSIGN_FLAG = 1
;



-- インデックス
CREATE INDEX T_TERC_IF_INFO_01 ON T_TERC_IF_INFO (DISUSE_FLAG);
CREATE INDEX T_TERC_WORKSPACE_01 ON T_TERC_WORKSPACE (DISUSE_FLAG);
CREATE INDEX T_TERC_MODULE_01 ON T_TERC_MODULE (DISUSE_FLAG);
CREATE INDEX T_TERC_MVMT_MOD_LINK_01 ON T_TERC_MVMT_MOD_LINK (DISUSE_FLAG);
CREATE INDEX T_TERC_NESTVAR_MEMBER_MAX_COL_01 ON T_TERC_NESTVAR_MEMBER_MAX_COL (DISUSE_FLAG);
CREATE INDEX T_TERC_VALUE_AUTOREG_01 ON T_TERC_VALUE_AUTOREG (DISUSE_FLAG);
CREATE INDEX T_TERC_EXEC_STS_INST_01 ON T_TERC_EXEC_STS_INST (DISUSE_FLAG);
CREATE INDEX T_TERC_VALUE_01 ON T_TERC_VALUE (DISUSE_FLAG);
CREATE INDEX T_TERC_MOD_VAR_LINK_01 ON T_TERC_MOD_VAR_LINK (DISUSE_FLAG);
CREATE INDEX T_TERC_VAR_MEMBER_01 ON T_TERC_VAR_MEMBER (DISUSE_FLAG);
CREATE INDEX T_TERC_MVMT_VAR_LINK_01 ON T_TERC_MVMT_VAR_LINK (DISUSE_FLAG);
CREATE INDEX T_TERC_MVMT_VAR_MEMBER_LINK_01 ON T_TERC_MVMT_VAR_MEMBER_LINK (DISUSE_FLAG);



