-- ------------------------------------------------------------
-- ▼ TABLE CREATE START
-- ------------------------------------------------------------
-- 20109 収集項目値管理
CREATE TABLE IF NOT EXISTS T_ANSC_CMDB_LINK
(
    ROW_ID                          VARCHAR(40),                                -- 項番
    FILE_PREFIX                     VARCHAR(4000),                              -- PREFIX(ファイル名)
    VARS_NAME                       VARCHAR(4000),                              -- 変数名
    VRAS_MEMBER_NAME                VARCHAR(4000),                              -- メンバ変数
    PARSE_TYPE_ID                   VARCHAR(2),                                 -- パース形式
    COLUMN_LIST_ID                  VARCHAR(40),                                -- 項目
    INPUT_ORDER                     INT,                                        -- 代入順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ROW_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE IF NOT EXISTS T_ANSC_CMDB_LINK_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    ROW_ID                          VARCHAR(40),                                -- 項番
    FILE_PREFIX                     VARCHAR(4000),                              -- PREFIX(ファイル名)
    VARS_NAME                       VARCHAR(4000),                              -- 変数名
    VRAS_MEMBER_NAME                VARCHAR(4000),                              -- メンバ変数
    PARSE_TYPE_ID                   VARCHAR(2),                                 -- パース形式
    COLUMN_LIST_ID                  VARCHAR(40),                                -- 項目
    INPUT_ORDER                     INT,                                        -- 代入順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 20201 Legacy Movemnet一覧
CREATE OR REPLACE VIEW V_ANSL_MOVEMENT AS
SELECT
MOVEMENT_ID,
MOVEMENT_NAME,
ITA_EXT_STM_ID,
TIME_LIMIT,
ANS_HOST_DESIGNATE_TYPE_ID,
ANS_PARALLEL_EXE,
ANS_WINRM_ID,
ANS_PLAYBOOK_HED_DEF,
ANS_EXEC_OPTIONS,
ANS_EXECUTION_ENVIRONMENT_NAME,
ANS_ANSIBLE_CONFIG_FILE,
NOTE,
DISUSE_FLAG,
LAST_UPDATE_TIMESTAMP,
LAST_UPDATE_USER
FROM
  T_COMN_MOVEMENT
WHERE
  ITA_EXT_STM_ID = 1;
CREATE OR REPLACE VIEW V_ANSL_MOVEMENT_JNL AS
SELECT
JOURNAL_SEQ_NO,
JOURNAL_REG_DATETIME,
JOURNAL_ACTION_CLASS,
MOVEMENT_ID,
MOVEMENT_NAME,
ITA_EXT_STM_ID,
TIME_LIMIT,
ANS_HOST_DESIGNATE_TYPE_ID,
ANS_PARALLEL_EXE,
ANS_WINRM_ID,
ANS_PLAYBOOK_HED_DEF,
ANS_EXEC_OPTIONS,
ANS_EXECUTION_ENVIRONMENT_NAME,
ANS_ANSIBLE_CONFIG_FILE,
NOTE,
DISUSE_FLAG,
LAST_UPDATE_TIMESTAMP,
LAST_UPDATE_USER
FROM
  T_COMN_MOVEMENT_JNL
WHERE
  ITA_EXT_STM_ID = 1;



-- 20202 Legacy Playbook素材集
CREATE TABLE IF NOT EXISTS T_ANSL_MATL_COLL
(
    PLAYBOOK_MATTER_ID              VARCHAR(40),                                -- 項番
    PLAYBOOK_MATTER_NAME            VARCHAR(255),                               -- Playbook素材名
    PLAYBOOK_MATTER_FILE            VARCHAR(255),                               -- Playbook素材
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(PLAYBOOK_MATTER_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE IF NOT EXISTS T_ANSL_MATL_COLL_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    PLAYBOOK_MATTER_ID              VARCHAR(40),                                -- 項番
    PLAYBOOK_MATTER_NAME            VARCHAR(255),                               -- Playbook素材名
    PLAYBOOK_MATTER_FILE            VARCHAR(255),                               -- Playbook素材
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 20203 Legacy Movement-変数紐付
CREATE TABLE IF NOT EXISTS T_ANSL_MVMT_VAR_LINK
(
    MVMT_VAR_LINK_ID                VARCHAR(40),                                -- 項番
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement
    VARS_NAME                       VARCHAR(255),                               -- 変数名
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(MVMT_VAR_LINK_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- 20204 Legacy Move-Playbook紐付
CREATE TABLE IF NOT EXISTS T_ANSL_MVMT_MATL_LINK
(
    MVMT_MATL_LINK_ID               VARCHAR(40),                                -- 項番
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement
    PLAYBOOK_MATTER_ID              VARCHAR(40),                                -- Playbook素材
    INCLUDE_SEQ                     INT,                                        -- インクルード順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(MVMT_MATL_LINK_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE IF NOT EXISTS T_ANSL_MVMT_MATL_LINK_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    MVMT_MATL_LINK_ID               VARCHAR(40),                                -- 項番
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement
    PLAYBOOK_MATTER_ID              VARCHAR(40),                                -- Playbook素材
    INCLUDE_SEQ                     INT,                                        -- インクルード順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 20205 Legacy 代入値自動登録
CREATE TABLE IF NOT EXISTS T_ANSL_VALUE_AUTOREG
(
    COLUMN_ID                       VARCHAR(40),                                -- 項番
    MENU_ID                         VARCHAR(40),                                -- メニュー名
    COLUMN_LIST_ID                  VARCHAR(40),                                -- 項目名
    COLUMN_ASSIGN_SEQ               INT,                                        -- 代入順序
    COL_TYPE                        VARCHAR(2),                                 -- 登録方式
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement
    MVMT_VAR_LINK_ID                VARCHAR(40),                                -- 変数名
    ASSIGN_SEQ                      INT,                                        -- 代入順序
    NULL_DATA_HANDLING_FLG          VARCHAR(2),                                 -- NULL連携
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(COLUMN_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE IF NOT EXISTS T_ANSL_VALUE_AUTOREG_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    COLUMN_ID                       VARCHAR(40),                                -- 項番
    MENU_ID                         VARCHAR(40),                                -- メニュー名
    COLUMN_LIST_ID                  VARCHAR(40),                                -- 項目名
    COLUMN_ASSIGN_SEQ               INT,                                        -- 代入順序
    COL_TYPE                        VARCHAR(2),                                 -- 登録方式
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement
    MVMT_VAR_LINK_ID                VARCHAR(40),                                -- 変数名
    ASSIGN_SEQ                      INT,                                        -- 代入順序
    NULL_DATA_HANDLING_FLG          VARCHAR(2),                                 -- NULL連携
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 20206 Legacy 作業対象ホスト
CREATE TABLE IF NOT EXISTS T_ANSL_TGT_HOST
(
    PHO_LINK_ID                     VARCHAR(40),                                -- 項番
    EXECUTION_NO                    VARCHAR(40),                                -- 作業実行番号
    OPERATION_ID                    VARCHAR(40),                                -- オペレーション
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement
    SYSTEM_ID                       VARCHAR(40),                                -- ホスト
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(PHO_LINK_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- 20207 Legacy 代入値管理
CREATE TABLE IF NOT EXISTS T_ANSL_VALUE
(
    ASSIGN_ID                       VARCHAR(40),                                -- 項番
    EXECUTION_NO                    VARCHAR(40),                                -- 作業実行番号
    OPERATION_ID                    VARCHAR(40),                                -- オペレーション
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement
    SYSTEM_ID                       VARCHAR(40),                                -- ホスト
    MVMT_VAR_LINK_ID                VARCHAR(40),                                -- 変数名
    SENSITIVE_FLAG                  VARCHAR(2),                                 -- Sensitive設定
    VARS_ENTRY                      TEXT,                                       -- 値
    VARS_ENTRY_FILE                 VARCHAR(255),                               -- ファイル
    ASSIGN_SEQ                      INT,                                        -- 代入順序
    VARS_ENTRY_USE_TPFVARS          VARCHAR(1),                                 -- テンプレート変数使用有無
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ASSIGN_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- 20209 Legacy 作業管理
CREATE TABLE IF NOT EXISTS T_ANSL_EXEC_STS_INST
(
    EXECUTION_NO                    VARCHAR(40),                                -- 作業番号
    RUN_MODE                        VARCHAR(2),                                 -- 実行種別
    STATUS_ID                       VARCHAR(2),                                 -- ステータス
    EXEC_MODE                       VARCHAR(2),                                 -- 実行エンジン
    CONDUCTOR_NAME                  VARCHAR(255),                               -- 呼出元Conductor
    EXECUTION_USER                  VARCHAR(255),                               -- 実行ユーザ
    TIME_REGISTER                   DATETIME(6),                                -- 登録日時
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement/ID
    I_MOVEMENT_NAME                 VARCHAR(255),                               -- Movement/名称
    I_TIME_LIMIT                    INT,                                        -- Movement/遅延タイマー
    I_ANS_HOST_DESIGNATE_TYPE_ID    VARCHAR(2),                                 -- Movement/Ansible利用情報/ホスト指定形式
    I_ANS_PARALLEL_EXE              INT,                                        -- Movement/Ansible利用情報/並列実行数
    I_ANS_WINRM_ID                  VARCHAR(2),                                 -- Movement/Ansible利用情報/WinRM接続
    I_ANS_PLAYBOOK_HED_DEF          TEXT,                                       -- Movement/Ansible利用情報/ヘッダーセクション
    I_EXECUTION_ENVIRONMENT_NAME    VARCHAR(255),                               -- Movement/Ansible Automation Controller利用情報/実行環境
    I_ANSIBLE_CONFIG_FILE           VARCHAR(255),                               -- Movement/ansible.cfg
    OPERATION_ID                    VARCHAR(40),                                -- オペレーション/No.
    I_OPERATION_NAME                VARCHAR(255),                               -- オペレーション/名称
    FILE_INPUT                      VARCHAR(1024),                              -- 入力データ/投入データ
    FILE_RESULT                     VARCHAR(1024),                              -- 出力データ/結果データ
    TIME_BOOK                       DATETIME(6),                                -- 作業状況/予約日時
    TIME_START                      DATETIME(6),                                -- 作業状況/開始日時
    TIME_END                        DATETIME(6),                                -- 作業状況/終了日時
    COLLECT_STATUS                  VARCHAR(2),                                 -- 収集状況/ステータス
    COLLECT_LOG                     VARCHAR(1024),                              -- 収集状況/収集ログ
    CONDUCTOR_INSTANCE_NO           VARCHAR(40),                                -- Conductorインスタンス番号
    I_ANS_EXEC_OPTIONS              TEXT,                                       -- オプションパラメータ
    LOGFILELIST_JSON                TEXT,                                       -- 分割された実行ログ情報
    MULTIPLELOG_MODE                INT,                                        -- 実行ログ分割フラグ
    EXECUTE_HOST_NAME               VARCHAR(40),                                -- 実行ホスト名
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(EXECUTION_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE IF NOT EXISTS T_ANSL_EXEC_STS_INST_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    EXECUTION_NO                    VARCHAR(40),                                -- 作業番号
    RUN_MODE                        VARCHAR(2),                                 -- 実行種別
    STATUS_ID                       VARCHAR(2),                                 -- ステータス
    EXEC_MODE                       VARCHAR(2),                                 -- 実行エンジン
    CONDUCTOR_NAME                  VARCHAR(255),                               -- 呼出元Conductor
    EXECUTION_USER                  VARCHAR(255),                               -- 実行ユーザ
    TIME_REGISTER                   DATETIME(6),                                -- 登録日時
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement/ID
    I_MOVEMENT_NAME                 VARCHAR(255),                               -- Movement/名称
    I_TIME_LIMIT                    INT,                                        -- Movement/遅延タイマー
    I_ANS_HOST_DESIGNATE_TYPE_ID    VARCHAR(2),                                 -- Movement/Ansible利用情報/ホスト指定形式
    I_ANS_PARALLEL_EXE              INT,                                        -- Movement/Ansible利用情報/並列実行数
    I_ANS_WINRM_ID                  VARCHAR(2),                                 -- Movement/Ansible利用情報/WinRM接続
    I_ANS_PLAYBOOK_HED_DEF          TEXT,                                       -- Movement/Ansible利用情報/ヘッダーセクション
    I_EXECUTION_ENVIRONMENT_NAME    VARCHAR(255),                               -- Movement/Ansible Automation Controller利用情報/実行環境
    I_ANSIBLE_CONFIG_FILE           VARCHAR(255),                               -- Movement/ansible.cfg
    OPERATION_ID                    VARCHAR(40),                                -- オペレーション/No.
    I_OPERATION_NAME                VARCHAR(255),                               -- オペレーション/名称
    FILE_INPUT                      VARCHAR(1024),                              -- 入力データ/投入データ
    FILE_RESULT                     VARCHAR(1024),                              -- 出力データ/結果データ
    TIME_BOOK                       DATETIME(6),                                -- 作業状況/予約日時
    TIME_START                      DATETIME(6),                                -- 作業状況/開始日時
    TIME_END                        DATETIME(6),                                -- 作業状況/終了日時
    COLLECT_STATUS                  VARCHAR(2),                                 -- 収集状況/ステータス
    COLLECT_LOG                     VARCHAR(1024),                              -- 収集状況/収集ログ
    CONDUCTOR_INSTANCE_NO           VARCHAR(40),                                -- Conductorインスタンス番号
    I_ANS_EXEC_OPTIONS              TEXT,                                       -- オプションパラメータ
    LOGFILELIST_JSON                TEXT,                                       -- 分割された実行ログ情報
    MULTIPLELOG_MODE                INT,                                        -- 実行ログ分割フラグ
    EXECUTE_HOST_NAME               VARCHAR(40),                                -- 実行ホスト名
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 20301 Pionner Movemnet一覧
CREATE OR REPLACE VIEW V_ANSP_MOVEMENT AS
SELECT
MOVEMENT_ID,
MOVEMENT_NAME,
ITA_EXT_STM_ID,
TIME_LIMIT,
ANS_HOST_DESIGNATE_TYPE_ID,
ANS_PARALLEL_EXE,
ANS_WINRM_ID,
ANS_PLAYBOOK_HED_DEF,
ANS_EXEC_OPTIONS,
ANS_EXECUTION_ENVIRONMENT_NAME,
ANS_ANSIBLE_CONFIG_FILE,
NOTE,
DISUSE_FLAG,
LAST_UPDATE_TIMESTAMP,
LAST_UPDATE_USER
FROM
  T_COMN_MOVEMENT
WHERE
  ITA_EXT_STM_ID = 2;
CREATE OR REPLACE VIEW V_ANSP_MOVEMENT_JNL AS
SELECT
JOURNAL_SEQ_NO,
JOURNAL_REG_DATETIME,
JOURNAL_ACTION_CLASS,
MOVEMENT_ID,
MOVEMENT_NAME,
ITA_EXT_STM_ID,
TIME_LIMIT,
ANS_HOST_DESIGNATE_TYPE_ID,
ANS_PARALLEL_EXE,
ANS_WINRM_ID,
ANS_PLAYBOOK_HED_DEF,
ANS_EXEC_OPTIONS,
ANS_EXECUTION_ENVIRONMENT_NAME,
ANS_ANSIBLE_CONFIG_FILE,
NOTE,
DISUSE_FLAG,
LAST_UPDATE_TIMESTAMP,
LAST_UPDATE_USER
FROM
  T_COMN_MOVEMENT_JNL
WHERE
  ITA_EXT_STM_ID = 2;



-- 20302 Pionner 対話種別
CREATE TABLE IF NOT EXISTS T_ANSP_DIALOG_TYPE
(
    DIALOG_TYPE_ID                  VARCHAR(40),                                -- 項番
    DIALOG_TYPE_NAME                VARCHAR(255),                               -- 対話種別名
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(DIALOG_TYPE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE IF NOT EXISTS T_ANSP_DIALOG_TYPE_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    DIALOG_TYPE_ID                  VARCHAR(40),                                -- 項番
    DIALOG_TYPE_NAME                VARCHAR(255),                               -- 対話種別名
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 20303 Pionner OS種別
CREATE TABLE IF NOT EXISTS T_ANSP_OS_TYPE
(
    OS_TYPE_ID                      VARCHAR(40),                                -- 項番
    OS_TYPE_NAME                    VARCHAR(255),                               -- OS種別名
    HARDAWRE_TYPE_SV                VARCHAR(2),                                 -- SV
    HARDAWRE_TYPE_ST                VARCHAR(2),                                 -- ST
    HARDAWRE_TYPE_NW                VARCHAR(2),                                 -- NW
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(OS_TYPE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE IF NOT EXISTS T_ANSP_OS_TYPE_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    OS_TYPE_ID                      VARCHAR(40),                                -- 項番
    OS_TYPE_NAME                    VARCHAR(255),                               -- OS種別名
    HARDAWRE_TYPE_SV                VARCHAR(2),                                 -- SV
    HARDAWRE_TYPE_ST                VARCHAR(2),                                 -- ST
    HARDAWRE_TYPE_NW                VARCHAR(2),                                 -- NW
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 20304 Pionner 対話ファイル素材集
CREATE TABLE IF NOT EXISTS T_ANSP_MATL_COLL
(
    DIALOG_MATTER_ID                VARCHAR(40),                                -- 項番
    DIALOG_TYPE_ID                  VARCHAR(40),                                -- 対話種別
    OS_TYPE_ID                      VARCHAR(40),                                -- OS種別
    DIALOG_MATTER_FILE              VARCHAR(255),                               -- 対話ファイル素材
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(DIALOG_MATTER_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE IF NOT EXISTS T_ANSP_MATL_COLL_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    DIALOG_MATTER_ID                VARCHAR(40),                                -- 項番
    DIALOG_TYPE_ID                  VARCHAR(40),                                -- 対話種別
    OS_TYPE_ID                      VARCHAR(40),                                -- OS種別
    DIALOG_MATTER_FILE              VARCHAR(255),                               -- 対話ファイル素材
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 20305 Pionner Movement-変数紐付
CREATE TABLE IF NOT EXISTS T_ANSP_MVMT_VAR_LINK
(
    MVMT_VAR_LINK_ID                VARCHAR(40),                                -- 項番
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement
    VARS_NAME                       VARCHAR(255),                               -- 変数名
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(MVMT_VAR_LINK_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- 20306 Pioneer Movement-対話種別紐付
CREATE TABLE IF NOT EXISTS T_ANSP_MVMT_MATL_LINK
(
    MVMT_MATL_LINK_ID               VARCHAR(40),                                -- 項番
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement
    DIALOG_TYPE_ID                  VARCHAR(40),                                -- 対話種別
    INCLUDE_SEQ                     INT,                                        -- インクルード順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(MVMT_MATL_LINK_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE IF NOT EXISTS T_ANSP_MVMT_MATL_LINK_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    MVMT_MATL_LINK_ID               VARCHAR(40),                                -- 項番
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement
    DIALOG_TYPE_ID                  VARCHAR(40),                                -- 対話種別
    INCLUDE_SEQ                     INT,                                        -- インクルード順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 20307 Pioneer 代入値自動登録
CREATE TABLE IF NOT EXISTS T_ANSP_VALUE_AUTOREG
(
    COLUMN_ID                       VARCHAR(40),                                -- 項番
    MENU_ID                         VARCHAR(40),                                -- メニュー名
    COLUMN_LIST_ID                  VARCHAR(40),                                -- 項目名
    COLUMN_ASSIGN_SEQ               INT,                                        -- 代入順序
    COL_TYPE                        VARCHAR(2),                                 -- 登録方式
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement
    MVMT_VAR_LINK_ID                VARCHAR(40),                                -- 変数名
    ASSIGN_SEQ                      INT,                                        -- 代入順序
    NULL_DATA_HANDLING_FLG          VARCHAR(2),                                 -- NULL連携
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(COLUMN_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE IF NOT EXISTS T_ANSP_VALUE_AUTOREG_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    COLUMN_ID                       VARCHAR(40),                                -- 項番
    MENU_ID                         VARCHAR(40),                                -- メニュー名
    COLUMN_LIST_ID                  VARCHAR(40),                                -- 項目名
    COLUMN_ASSIGN_SEQ               INT,                                        -- 代入順序
    COL_TYPE                        VARCHAR(2),                                 -- 登録方式
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement
    MVMT_VAR_LINK_ID                VARCHAR(40),                                -- 変数名
    ASSIGN_SEQ                      INT,                                        -- 代入順序
    NULL_DATA_HANDLING_FLG          VARCHAR(2),                                 -- NULL連携
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 20308 Pioneer 作業対象ホスト
CREATE TABLE IF NOT EXISTS T_ANSP_TGT_HOST
(
    PHO_LINK_ID                     VARCHAR(40),                                -- 項番
    EXECUTION_NO                    VARCHAR(40),                                -- 作業実行番号
    OPERATION_ID                    VARCHAR(40),                                -- オペレーション
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement
    SYSTEM_ID                       VARCHAR(40),                                -- ホスト
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(PHO_LINK_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- 20309 Pioneer 代入値管理
CREATE TABLE IF NOT EXISTS T_ANSP_VALUE
(
    ASSIGN_ID                       VARCHAR(40),                                -- 項番
    EXECUTION_NO                    VARCHAR(40),                                -- 作業実行番号
    OPERATION_ID                    VARCHAR(40),                                -- オペレーション
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement
    SYSTEM_ID                       VARCHAR(40),                                -- ホスト
    MVMT_VAR_LINK_ID                VARCHAR(40),                                -- 変数名
    SENSITIVE_FLAG                  VARCHAR(2),                                 -- Sensitive設定
    VARS_ENTRY                      TEXT,                                       -- 値
    VARS_ENTRY_FILE                 VARCHAR(255),                               -- ファイル
    ASSIGN_SEQ                      INT,                                        -- 代入順序
    VARS_ENTRY_USE_TPFVARS          VARCHAR(1),                                 -- テンプレート変数使用有無
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ASSIGN_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- 20310 Pioneer 作業管理
CREATE TABLE IF NOT EXISTS T_ANSP_EXEC_STS_INST
(
    EXECUTION_NO                    VARCHAR(40),                                -- 作業番号
    RUN_MODE                        VARCHAR(2),                                 -- 実行種別
    STATUS_ID                       VARCHAR(2),                                 -- ステータス
    EXEC_MODE                       VARCHAR(2),                                 -- 実行エンジン
    CONDUCTOR_NAME                  VARCHAR(255),                               -- 呼出元Conductor
    EXECUTION_USER                  VARCHAR(255),                               -- 実行ユーザ
    TIME_REGISTER                   DATETIME(6),                                -- 登録日時
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement/ID
    I_MOVEMENT_NAME                 VARCHAR(255),                               -- Movement/名称
    I_TIME_LIMIT                    INT,                                        -- Movement/遅延タイマー
    I_ANS_HOST_DESIGNATE_TYPE_ID    VARCHAR(2),                                 -- Movement/Ansible利用情報/ホスト指定形式
    I_ANS_PARALLEL_EXE              INT,                                        -- Movement/Ansible利用情報/並列実行数
    I_ANS_WINRM_ID                  VARCHAR(2),                                 -- Movement/Ansible利用情報/WinRM接続
    I_ANS_PLAYBOOK_HED_DEF          TEXT,                                       -- Movement/Ansible利用情報/ヘッダーセクション
    I_EXECUTION_ENVIRONMENT_NAME    VARCHAR(255),                               -- Movement/Ansible Automation Controller利用情報/実行環境
    I_ANSIBLE_CONFIG_FILE           VARCHAR(255),                               -- Movement/ansible.cfg
    OPERATION_ID                    VARCHAR(40),                                -- オペレーション/No.
    I_OPERATION_NAME                VARCHAR(255),                               -- オペレーション/名称
    FILE_INPUT                      VARCHAR(1024),                              -- 入力データ/投入データ
    FILE_RESULT                     VARCHAR(1024),                              -- 出力データ/結果データ
    TIME_BOOK                       DATETIME(6),                                -- 作業状況/予約日時
    TIME_START                      DATETIME(6),                                -- 作業状況/開始日時
    TIME_END                        DATETIME(6),                                -- 作業状況/終了日時
    COLLECT_STATUS                  VARCHAR(2),                                 -- 収集状況/ステータス
    COLLECT_LOG                     VARCHAR(1024),                              -- 収集状況/収集ログ
    CONDUCTOR_INSTANCE_NO           VARCHAR(40),                                -- Conductorインスタンス番号
    I_ANS_EXEC_OPTIONS              TEXT,                                       -- オプションパラメータ
    LOGFILELIST_JSON                TEXT,                                       -- 分割された実行ログ情報
    MULTIPLELOG_MODE                INT,                                        -- 実行ログ分割フラグ
    EXECUTE_HOST_NAME               VARCHAR(40),                                -- 実行ホスト名
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(EXECUTION_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE IF NOT EXISTS T_ANSP_EXEC_STS_INST_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    EXECUTION_NO                    VARCHAR(40),                                -- 作業番号
    RUN_MODE                        VARCHAR(2),                                 -- 実行種別
    STATUS_ID                       VARCHAR(2),                                 -- ステータス
    EXEC_MODE                       VARCHAR(2),                                 -- 実行エンジン
    CONDUCTOR_NAME                  VARCHAR(255),                               -- 呼出元Conductor
    EXECUTION_USER                  VARCHAR(255),                               -- 実行ユーザ
    TIME_REGISTER                   DATETIME(6),                                -- 登録日時
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement/ID
    I_MOVEMENT_NAME                 VARCHAR(255),                               -- Movement/名称
    I_TIME_LIMIT                    INT,                                        -- Movement/遅延タイマー
    I_ANS_HOST_DESIGNATE_TYPE_ID    VARCHAR(2),                                 -- Movement/Ansible利用情報/ホスト指定形式
    I_ANS_PARALLEL_EXE              INT,                                        -- Movement/Ansible利用情報/並列実行数
    I_ANS_WINRM_ID                  VARCHAR(2),                                 -- Movement/Ansible利用情報/WinRM接続
    I_ANS_PLAYBOOK_HED_DEF          TEXT,                                       -- Movement/Ansible利用情報/ヘッダーセクション
    I_EXECUTION_ENVIRONMENT_NAME    VARCHAR(255),                               -- Movement/Ansible Automation Controller利用情報/実行環境
    I_ANSIBLE_CONFIG_FILE           VARCHAR(255),                               -- Movement/ansible.cfg
    OPERATION_ID                    VARCHAR(40),                                -- オペレーション/No.
    I_OPERATION_NAME                VARCHAR(255),                               -- オペレーション/名称
    FILE_INPUT                      VARCHAR(1024),                              -- 入力データ/投入データ
    FILE_RESULT                     VARCHAR(1024),                              -- 出力データ/結果データ
    TIME_BOOK                       DATETIME(6),                                -- 作業状況/予約日時
    TIME_START                      DATETIME(6),                                -- 作業状況/開始日時
    TIME_END                        DATETIME(6),                                -- 作業状況/終了日時
    COLLECT_STATUS                  VARCHAR(2),                                 -- 収集状況/ステータス
    COLLECT_LOG                     VARCHAR(1024),                              -- 収集状況/収集ログ
    CONDUCTOR_INSTANCE_NO           VARCHAR(40),                                -- Conductorインスタンス番号
    I_ANS_EXEC_OPTIONS              TEXT,                                       -- オプションパラメータ
    LOGFILELIST_JSON                TEXT,                                       -- 分割された実行ログ情報
    MULTIPLELOG_MODE                INT,                                        -- 実行ログ分割フラグ
    EXECUTE_HOST_NAME               VARCHAR(40),                                -- 実行ホスト名
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;
CREATE TABLE IF NOT EXISTS T_ANSC_PARSE_TYPE
(
    PARSE_TYPE_ID                   VARCHAR(2),                                 -- ROW_ID
    PARSE_TYPE_NAME                 VARCHAR(255),                               -- パース形式名
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(PARSE_TYPE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;
-- ------------------------------------------------------------
-- ▲ TABLE CREATE END
-- ------------------------------------------------------------

-- ------------------------------------------------------------
-- ▼TABLE UPDATE START
-- ------------------------------------------------------------
-- 20101 機器一覧
ALTER TABLE T_ANSC_DEVICE            MODIFY OS_TYPE_ID VARCHAR(40);
ALTER TABLE T_ANSC_DEVICE_JNL        MODIFY OS_TYPE_ID VARCHAR(40);
-- 20412 Role 作業管理
ALTER TABLE T_ANSR_EXEC_STS_INST     ADD COLUMN EXECUTE_HOST_NAME VARCHAR(40)  AFTER MULTIPLELOG_MODE;
ALTER TABLE T_ANSR_EXEC_STS_INST_JNL ADD COLUMN EXECUTE_HOST_NAME VARCHAR(40)  AFTER MULTIPLELOG_MODE;
-- ------------------------------------------------------------
-- ▲ TABLE UPDATE END
-- ------------------------------------------------------------

-- ------------------------------------------------------------
-- ▲ VIEW UPDATE START
-- ------------------------------------------------------------
-- V002_作業管理検索ビュー
CREATE OR REPLACE VIEW V_ANSC_EXEC_STS_INST     AS
SELECT
  'Legacy' as DRIVER_NAME, 'L' as DRIVER_ID, EXECUTION_NO, STATUS_ID, TIME_BOOK, DISUSE_FLAG, LAST_UPDATE_TIMESTAMP, TIME_REGISTER
FROM
  T_ANSL_EXEC_STS_INST
WHERE
  DISUSE_FLAG = '0'
UNION
SELECT
  'Pioneer' as DRIVER_NAME, 'P' as DRIVER_ID, EXECUTION_NO, STATUS_ID, TIME_BOOK, DISUSE_FLAG, LAST_UPDATE_TIMESTAMP, TIME_REGISTER
FROM
  T_ANSP_EXEC_STS_INST
WHERE
  DISUSE_FLAG = '0'
UNION
SELECT
  'Legacy-Role' as DRIVER_NAME, 'R' as DRIVER_ID, EXECUTION_NO, STATUS_ID, TIME_BOOK, DISUSE_FLAG, LAST_UPDATE_TIMESTAMP, TIME_REGISTER
FROM
  T_ANSR_EXEC_STS_INST
WHERE
  DISUSE_FLAG = '0';
-- ------------------------------------------------------------
-- ▲ VIEW UPDATE END
-- ------------------------------------------------------------

-- ------------------------------------------------------------
-- ▼ VIEW CREATE START
-- ------------------------------------------------------------
-- V011_代入値自動登録_Movement名_変数名ビュー
CREATE OR REPLACE VIEW V_ANSL_VAL_VARS_LINK AS
SELECT
TAB_A.MVMT_VAR_LINK_ID,
TAB_A.MOVEMENT_ID,
TAB_A.VARS_NAME,
TAB_A.NOTE,
TAB_A.DISUSE_FLAG,
TAB_A.LAST_UPDATE_TIMESTAMP,
TAB_A.LAST_UPDATE_USER,
CONCAT(TAB_B.MOVEMENT_NAME, ":", TAB_A.VARS_NAME) AS MOVEMENT_VARS_NAME
FROM
T_ANSL_MVMT_VAR_LINK TAB_A
LEFT JOIN
V_ANSL_MOVEMENT TAB_B ON (TAB_A.MOVEMENT_ID = TAB_B.MOVEMENT_ID)
WHERE
TAB_A.DISUSE_FLAG = 0
AND
TAB_B.DISUSE_FLAG = 0;
CREATE OR REPLACE VIEW V_ANSL_VAL_VARS_LINK_JNL AS
SELECT
TAB_A.MVMT_VAR_LINK_ID,
TAB_A.MOVEMENT_ID,
TAB_A.VARS_NAME,
TAB_A.NOTE,
TAB_A.DISUSE_FLAG,
TAB_A.LAST_UPDATE_TIMESTAMP,
TAB_A.LAST_UPDATE_USER,
CONCAT(TAB_B.MOVEMENT_NAME, ":", TAB_A.VARS_NAME) AS MOVEMENT_VARS_NAME
FROM
T_ANSL_MVMT_VAR_LINK TAB_A
LEFT JOIN
V_ANSL_MOVEMENT_JNL TAB_B ON (TAB_A.MOVEMENT_ID = TAB_B.MOVEMENT_ID)
WHERE
TAB_A.DISUSE_FLAG = 0
AND
TAB_B.DISUSE_FLAG = 0;

-- V012_代入値自動登録_Movement名_変数名ビュー
CREATE OR REPLACE VIEW V_ANSP_VAL_VARS_LINK AS
SELECT
TAB_A.MVMT_VAR_LINK_ID,
TAB_A.MOVEMENT_ID,
TAB_A.VARS_NAME,
TAB_A.NOTE,
TAB_A.DISUSE_FLAG,
TAB_A.LAST_UPDATE_TIMESTAMP,
TAB_A.LAST_UPDATE_USER,
CONCAT(TAB_B.MOVEMENT_NAME, ":", TAB_A.VARS_NAME) AS MOVEMENT_VARS_NAME
FROM
T_ANSP_MVMT_VAR_LINK TAB_A
LEFT JOIN
V_ANSP_MOVEMENT TAB_B ON (TAB_A.MOVEMENT_ID = TAB_B.MOVEMENT_ID)
WHERE
TAB_A.DISUSE_FLAG = 0
AND
TAB_B.DISUSE_FLAG = 0;

CREATE OR REPLACE VIEW V_ANSP_VAL_VARS_LINK_JNL AS
SELECT
TAB_A.MVMT_VAR_LINK_ID,
TAB_A.MOVEMENT_ID,
TAB_A.VARS_NAME,
TAB_A.NOTE,
TAB_A.DISUSE_FLAG,
TAB_A.LAST_UPDATE_TIMESTAMP,
TAB_A.LAST_UPDATE_USER,
CONCAT(TAB_B.MOVEMENT_NAME, ":", TAB_A.VARS_NAME) AS MOVEMENT_VARS_NAME
FROM
T_ANSP_MVMT_VAR_LINK TAB_A
LEFT JOIN
V_ANSP_MOVEMENT_JNL TAB_B ON (TAB_A.MOVEMENT_ID = TAB_B.MOVEMENT_ID)
WHERE
TAB_A.DISUSE_FLAG = 0
AND
TAB_B.DISUSE_FLAG = 0;



-- V013_代入値自動登録用項目表示ビュー
CREATE OR REPLACE VIEW V_ANSP_COLUMN_LIST AS
SELECT
TAB_A.COLUMN_DEFINITION_ID,
TAB_A.MENU_ID,
TAB_A.COLUMN_NAME_JA,
TAB_A.COLUMN_NAME_EN,
TAB_A.COLUMN_NAME_REST,
TAB_A.COL_GROUP_ID,
TAB_A.COLUMN_CLASS,
TAB_A.COLUMN_DISP_SEQ,
TAB_A.REF_TABLE_NAME,
TAB_A.REF_PKEY_NAME,
TAB_A.REF_COL_NAME,
TAB_A.REF_SORT_CONDITIONS,
TAB_A.REF_MULTI_LANG,
TAB_A.SENSITIVE_COL_NAME,
TAB_A.FILE_UPLOAD_PLACE,
TAB_A.COL_NAME,
TAB_A.SAVE_TYPE,
TAB_A.AUTO_INPUT,
TAB_A.INPUT_ITEM,
TAB_A.VIEW_ITEM,
TAB_A.UNIQUE_ITEM,
TAB_A.REQUIRED_ITEM,
TAB_A.AUTOREG_HIDE_ITEM,
TAB_A.AUTOREG_ONLY_ITEM,
TAB_A.INITIAL_VALUE,
TAB_A.VALIDATE_OPTION,
TAB_A.BEFORE_VALIDATE_REGISTER,
TAB_A.AFTER_VALIDATE_REGISTER,
TAB_A.DESCRIPTION_JA,
TAB_A.DESCRIPTION_EN,
TAB_A.NOTE,
TAB_A.DISUSE_FLAG,
TAB_A.LAST_UPDATE_TIMESTAMP,
TAB_A.LAST_UPDATE_USER,
TAB_B.VERTICAL,
concat(TAB_D.MENU_GROUP_NAME_JA, ":", concat(TAB_C.MENU_NAME_JA, ":" , TAB_A.COLUMN_NAME_JA)) as GROUP_MENU_COLUMN_NAME_JA,
concat(TAB_D.MENU_GROUP_NAME_EN, ":", concat(TAB_C.MENU_NAME_EN, ":" , TAB_A.COLUMN_NAME_EN)) as GROUP_MENU_COLUMN_NAME_EN
FROM T_COMN_MENU_COLUMN_LINK TAB_A
LEFT JOIN T_COMN_MENU_TABLE_LINK TAB_B ON (TAB_A.MENU_ID = TAB_B.MENU_ID)
LEFT JOIN T_COMN_MENU TAB_C ON (TAB_B.MENU_ID = TAB_C.MENU_ID)
LEFT JOIN T_COMN_MENU_GROUP TAB_D ON ( TAB_C.MENU_GROUP_ID = TAB_D.MENU_GROUP_ID )
WHERE TAB_A.AUTOREG_HIDE_ITEM = 0
AND TAB_A.DISUSE_FLAG = 0
AND (TAB_B.SHEET_TYPE = 1 OR TAB_B.SHEET_TYPE = 4)
AND TAB_A.COLUMN_CLASS <> 2
AND TAB_B.DISUSE_FLAG = 0
AND TAB_B.SUBSTITUTION_VALUE_LINK_FLAG =1
AND TAB_C.DISUSE_FLAG = 0
AND TAB_D.DISUSE_FLAG = 0;

CREATE OR REPLACE VIEW V_ANSP_COLUMN_LIST_JNL AS
SELECT
TAB_A.JOURNAL_SEQ_NO,
TAB_A.JOURNAL_REG_DATETIME,
TAB_A.JOURNAL_ACTION_CLASS,
TAB_A.COLUMN_DEFINITION_ID,
TAB_A.MENU_ID,
TAB_A.COLUMN_NAME_JA,
TAB_A.COLUMN_NAME_EN,
TAB_A.COLUMN_NAME_REST,
TAB_A.COL_GROUP_ID,
TAB_A.COLUMN_CLASS,
TAB_A.COLUMN_DISP_SEQ,
TAB_A.REF_TABLE_NAME,
TAB_A.REF_PKEY_NAME,
TAB_A.REF_COL_NAME,
TAB_A.REF_SORT_CONDITIONS,
TAB_A.REF_MULTI_LANG,
TAB_A.SENSITIVE_COL_NAME,
TAB_A.FILE_UPLOAD_PLACE,
TAB_A.COL_NAME,
TAB_A.SAVE_TYPE,
TAB_A.AUTO_INPUT,
TAB_A.INPUT_ITEM,
TAB_A.VIEW_ITEM,
TAB_A.UNIQUE_ITEM,
TAB_A.REQUIRED_ITEM,
TAB_A.AUTOREG_HIDE_ITEM,
TAB_A.AUTOREG_ONLY_ITEM,
TAB_A.INITIAL_VALUE,
TAB_A.VALIDATE_OPTION,
TAB_A.BEFORE_VALIDATE_REGISTER,
TAB_A.AFTER_VALIDATE_REGISTER,
TAB_A.DESCRIPTION_JA,
TAB_A.DESCRIPTION_EN,
TAB_A.NOTE,
TAB_A.DISUSE_FLAG,
TAB_A.LAST_UPDATE_TIMESTAMP,
TAB_A.LAST_UPDATE_USER,
TAB_B.VERTICAL,
concat(TAB_D.MENU_GROUP_NAME_JA, ":", concat(TAB_C.MENU_NAME_JA, ":" , TAB_A.COLUMN_NAME_JA)) as GROUP_MENU_COLUMN_NAME_JA,
concat(TAB_D.MENU_GROUP_NAME_EN, ":", concat(TAB_C.MENU_NAME_EN, ":" , TAB_A.COLUMN_NAME_EN)) as GROUP_MENU_COLUMN_NAME_EN
FROM T_COMN_MENU_COLUMN_LINK_JNL TAB_A
LEFT JOIN T_COMN_MENU_TABLE_LINK_JNL TAB_B ON (TAB_A.MENU_ID = TAB_B.MENU_ID)
LEFT JOIN T_COMN_MENU_JNL TAB_C ON (TAB_B.MENU_ID = TAB_C.MENU_ID)
LEFT JOIN T_COMN_MENU_GROUP_JNL TAB_D ON ( TAB_C.MENU_GROUP_ID = TAB_D.MENU_GROUP_ID )
WHERE TAB_A.AUTOREG_HIDE_ITEM = 0
AND TAB_A.DISUSE_FLAG = 0
AND (TAB_B.SHEET_TYPE = 1 OR TAB_B.SHEET_TYPE = 4)
AND TAB_A.COLUMN_CLASS <> 2
AND TAB_B.DISUSE_FLAG = 0
AND TAB_B.SUBSTITUTION_VALUE_LINK_FLAG =1
AND TAB_C.DISUSE_FLAG = 0
AND TAB_D.DISUSE_FLAG = 0;

-- V014_入力用項目表示ビュー
CREATE OR REPLACE VIEW V_ANSC_INPUT_COLUMN_LIST AS
SELECT
TAB_A.COLUMN_DEFINITION_ID,
TAB_A.MENU_ID,
TAB_A.COLUMN_NAME_JA,
TAB_A.COLUMN_NAME_EN,
TAB_A.COLUMN_NAME_REST,
TAB_A.COL_GROUP_ID,
TAB_A.COLUMN_CLASS,
TAB_A.COLUMN_DISP_SEQ,
TAB_A.REF_TABLE_NAME,
TAB_A.REF_PKEY_NAME,
TAB_A.REF_COL_NAME,
TAB_A.REF_SORT_CONDITIONS,
TAB_A.REF_MULTI_LANG,
TAB_A.SENSITIVE_COL_NAME,
TAB_A.FILE_UPLOAD_PLACE,
TAB_A.COL_NAME,
TAB_A.SAVE_TYPE,
TAB_A.AUTO_INPUT,
TAB_A.INPUT_ITEM,
TAB_A.VIEW_ITEM,
TAB_A.UNIQUE_ITEM,
TAB_A.REQUIRED_ITEM,
TAB_A.AUTOREG_HIDE_ITEM,
TAB_A.AUTOREG_ONLY_ITEM,
TAB_A.INITIAL_VALUE,
TAB_A.VALIDATE_OPTION,
TAB_A.BEFORE_VALIDATE_REGISTER,
TAB_A.AFTER_VALIDATE_REGISTER,
TAB_A.DESCRIPTION_JA,
TAB_A.DESCRIPTION_EN,
TAB_A.NOTE,
TAB_A.DISUSE_FLAG,
TAB_A.LAST_UPDATE_TIMESTAMP,
TAB_A.LAST_UPDATE_USER,
TAB_B.VERTICAL,
concat(TAB_D.MENU_GROUP_NAME_JA, ":", concat(TAB_C.MENU_NAME_JA, ":" , TAB_A.COLUMN_NAME_JA)) as GROUP_MENU_COLUMN_NAME_JA,
concat(TAB_D.MENU_GROUP_NAME_EN, ":", concat(TAB_C.MENU_NAME_EN, ":" , TAB_A.COLUMN_NAME_EN)) as GROUP_MENU_COLUMN_NAME_EN
FROM T_COMN_MENU_COLUMN_LINK TAB_A
LEFT JOIN T_COMN_MENU_TABLE_LINK TAB_B ON (TAB_A.MENU_ID = TAB_B.MENU_ID)
LEFT JOIN T_COMN_MENU TAB_C ON (TAB_B.MENU_ID = TAB_C.MENU_ID)
LEFT JOIN T_COMN_MENU_GROUP TAB_D ON ( TAB_C.MENU_GROUP_ID = TAB_D.MENU_GROUP_ID )
WHERE TAB_A.AUTOREG_HIDE_ITEM = 0
AND TAB_A.DISUSE_FLAG = 0
AND TAB_A.INPUT_ITEM =1
AND (TAB_B.SHEET_TYPE = 1 OR TAB_B.SHEET_TYPE = 4)
AND TAB_B.DISUSE_FLAG = 0
AND TAB_B.SUBSTITUTION_VALUE_LINK_FLAG =0
AND TAB_C.DISUSE_FLAG = 0
AND TAB_D.DISUSE_FLAG = 0;

CREATE OR REPLACE VIEW V_ANSC_INPUT_COLUMN_LIST_JNL AS
SELECT
TAB_A.JOURNAL_SEQ_NO,
TAB_A.JOURNAL_REG_DATETIME,
TAB_A.JOURNAL_ACTION_CLASS,
TAB_A.COLUMN_DEFINITION_ID,
TAB_A.MENU_ID,
TAB_A.COLUMN_NAME_JA,
TAB_A.COLUMN_NAME_EN,
TAB_A.COLUMN_NAME_REST,
TAB_A.COL_GROUP_ID,
TAB_A.COLUMN_CLASS,
TAB_A.COLUMN_DISP_SEQ,
TAB_A.REF_TABLE_NAME,
TAB_A.REF_PKEY_NAME,
TAB_A.REF_COL_NAME,
TAB_A.REF_SORT_CONDITIONS,
TAB_A.REF_MULTI_LANG,
TAB_A.SENSITIVE_COL_NAME,
TAB_A.FILE_UPLOAD_PLACE,
TAB_A.COL_NAME,
TAB_A.SAVE_TYPE,
TAB_A.AUTO_INPUT,
TAB_A.INPUT_ITEM,
TAB_A.VIEW_ITEM,
TAB_A.UNIQUE_ITEM,
TAB_A.REQUIRED_ITEM,
TAB_A.AUTOREG_HIDE_ITEM,
TAB_A.AUTOREG_ONLY_ITEM,
TAB_A.INITIAL_VALUE,
TAB_A.VALIDATE_OPTION,
TAB_A.BEFORE_VALIDATE_REGISTER,
TAB_A.AFTER_VALIDATE_REGISTER,
TAB_A.DESCRIPTION_JA,
TAB_A.DESCRIPTION_EN,
TAB_A.NOTE,
TAB_A.DISUSE_FLAG,
TAB_A.LAST_UPDATE_TIMESTAMP,
TAB_A.LAST_UPDATE_USER,
TAB_B.VERTICAL,
concat(TAB_D.MENU_GROUP_NAME_JA, ":", concat(TAB_C.MENU_NAME_JA, ":" , TAB_A.COLUMN_NAME_JA)) as GROUP_MENU_COLUMN_NAME_JA,
concat(TAB_D.MENU_GROUP_NAME_EN, ":", concat(TAB_C.MENU_NAME_EN, ":" , TAB_A.COLUMN_NAME_EN)) as GROUP_MENU_COLUMN_NAME_EN
FROM T_COMN_MENU_COLUMN_LINK_JNL TAB_A
LEFT JOIN T_COMN_MENU_TABLE_LINK_JNL TAB_B ON (TAB_A.MENU_ID = TAB_B.MENU_ID)
LEFT JOIN T_COMN_MENU_JNL TAB_C ON (TAB_B.MENU_ID = TAB_C.MENU_ID)
LEFT JOIN T_COMN_MENU_GROUP_JNL TAB_D ON ( TAB_C.MENU_GROUP_ID = TAB_D.MENU_GROUP_ID )
WHERE TAB_A.AUTOREG_HIDE_ITEM = 0
AND TAB_A.DISUSE_FLAG = 0
AND TAB_A.INPUT_ITEM =1
AND (TAB_B.SHEET_TYPE = 1 OR TAB_B.SHEET_TYPE = 4)
AND TAB_B.DISUSE_FLAG = 0
AND TAB_B.SUBSTITUTION_VALUE_LINK_FLAG =0
AND TAB_C.DISUSE_FLAG = 0
AND TAB_D.DISUSE_FLAG = 0;
-- ------------------------------------------------------------
-- ▲ VIEW CREATE END
-- ------------------------------------------------------------

-- ------------------------------------------------------------
-- ▼ INDEX CREATE END
-- ------------------------------------------------------------
CREATE INDEX IND_T_ANSL_MATL_COLL_01          ON T_ANSL_MATL_COLL(DISUSE_FLAG);
CREATE INDEX IND_T_ANSL_MVMT_VAR_LINK_01      ON T_ANSL_MVMT_VAR_LINK(DISUSE_FLAG);
CREATE INDEX IND_T_ANSL_MVMT_VAR_LINK_02      ON T_ANSL_MVMT_VAR_LINK(MVMT_VAR_LINK_ID, MOVEMENT_ID, DISUSE_FLAG);
CREATE INDEX IND_T_ANSL_MVMT_MATL_LINK_01     ON T_ANSL_MVMT_MATL_LINK(DISUSE_FLAG);
CREATE INDEX IND_T_ANSL_MVMT_MATL_LINK_02     ON T_ANSL_MVMT_MATL_LINK(MOVEMENT_ID, DISUSE_FLAG);
CREATE INDEX IND_T_ANSL_VALUE_AUTOREG_01      ON T_ANSL_VALUE_AUTOREG(DISUSE_FLAG);
CREATE INDEX IND_T_ANSL_VALUE_AUTOREG_02      ON T_ANSL_VALUE_AUTOREG(COLUMN_ID, MOVEMENT_ID, DISUSE_FLAG, MVMT_VAR_LINK_ID, ASSIGN_SEQ);
CREATE INDEX IND_T_ANSL_VALUE_AUTOREG_03      ON T_ANSL_VALUE_AUTOREG(COLUMN_LIST_ID);
CREATE INDEX IND_T_ANSL_TGT_HOST_01           ON T_ANSL_TGT_HOST(DISUSE_FLAG);
CREATE INDEX IND_T_ANSL_TGT_HOST_02           ON T_ANSL_TGT_HOST(EXECUTION_NO, OPERATION_ID, MOVEMENT_ID, SYSTEM_ID, DISUSE_FLAG);
CREATE INDEX IND_T_ANSL_VALUE_01              ON T_ANSL_VALUE(DISUSE_FLAG);
CREATE INDEX IND_T_ANSL_VALUE_02              ON T_ANSL_VALUE(EXECUTION_NO, OPERATION_ID, MOVEMENT_ID, SYSTEM_ID, MVMT_VAR_LINK_ID, ASSIGN_SEQ, DISUSE_FLAG);
CREATE INDEX IND_T_ANSL_EXEC_STS_INST_01      ON T_ANSL_EXEC_STS_INST(DISUSE_FLAG);
CREATE INDEX IND_T_ANSP_DIALOG_TYPE_01        ON T_ANSP_DIALOG_TYPE(DISUSE_FLAG);
CREATE INDEX IND_T_ANSP_OS_TYPE_01            ON T_ANSP_OS_TYPE(DISUSE_FLAG);
CREATE INDEX IND_T_ANSP_MATL_COLL_01          ON T_ANSP_MATL_COLL(DISUSE_FLAG);
CREATE INDEX IND_T_ANSP_MATL_COLL_02          ON T_ANSP_MATL_COLL(OS_TYPE_ID);
CREATE INDEX IND_T_ANSP_MVMT_VAR_LINK_01      ON T_ANSP_MVMT_VAR_LINK(DISUSE_FLAG);
CREATE INDEX IND_T_ANSP_MVMT_VAR_LINK_02      ON T_ANSP_MVMT_VAR_LINK(MVMT_VAR_LINK_ID, MOVEMENT_ID, DISUSE_FLAG);
CREATE INDEX IND_T_ANSP_MVMT_MATL_LINK_01     ON T_ANSP_MVMT_MATL_LINK(DISUSE_FLAG);
CREATE INDEX IND_T_ANSP_MVMT_MATL_LINK_02     ON T_ANSP_MVMT_MATL_LINK(MOVEMENT_ID, DISUSE_FLAG);
CREATE INDEX IND_T_ANSP_VALUE_AUTOREG_01      ON T_ANSP_VALUE_AUTOREG(DISUSE_FLAG);
CREATE INDEX IND_T_ANSP_VALUE_AUTOREG_02      ON T_ANSP_VALUE_AUTOREG(COLUMN_ID, MOVEMENT_ID, DISUSE_FLAG, MVMT_VAR_LINK_ID, ASSIGN_SEQ);
CREATE INDEX IND_T_ANSP_TGT_HOST_01           ON T_ANSP_TGT_HOST(DISUSE_FLAG);
CREATE INDEX IND_T_ANSP_TGT_HOST_02           ON T_ANSP_TGT_HOST(EXECUTION_NO, OPERATION_ID, MOVEMENT_ID, SYSTEM_ID, DISUSE_FLAG);
CREATE INDEX IND_T_ANSP_VALUE_01              ON T_ANSP_VALUE(DISUSE_FLAG);
CREATE INDEX IND_T_ANSP_VALUE_02              ON T_ANSP_VALUE(EXECUTION_NO, OPERATION_ID, MOVEMENT_ID, SYSTEM_ID, MVMT_VAR_LINK_ID, ASSIGN_SEQ, DISUSE_FLAG);
CREATE INDEX IND_T_ANSP_EXEC_STS_INST_01      ON T_ANSP_EXEC_STS_INST(DISUSE_FLAG);
CREATE INDEX IND_T_ANSC_TWR_INSTANCE_GROUP_01 ON T_ANSC_TWR_INSTANCE_GROUP(DISUSE_FLAG);
CREATE INDEX IND_T_ANSC_TWR_ORGANIZATION_01   ON T_ANSC_TWR_ORGANIZATION(DISUSE_FLAG);
-- ------------------------------------------------------------
-- ▲ INDEX CREATE END
-- ------------------------------------------------------------
