-- 20101 機器一覧
CREATE TABLE T_ANSC_DEVICE
(
    SYSTEM_ID                       VARCHAR(40),                                -- 項番
    HARDAWRE_TYPE_ID                VARCHAR(2),                                 -- HW機器種別
    HOST_NAME                       VARCHAR(255),                               -- ホスト名
    HOST_DNS_NAME                   VARCHAR(255),                               -- DNSホスト名
    IP_ADDRESS                      VARCHAR(15),                                -- IPアドレス
    LOGIN_USER                      VARCHAR(255),                               -- ユーザ
    LOGIN_PW                        TEXT,                                       -- パスワード
    LOGIN_PW_ANSIBLE_VAULT          TEXT,                                       -- vailt暗号化パスワード
    SSH_KEY_FILE                    VARCHAR(255),                               -- ssh秘密鍵ファイル
    SSH_KEY_FILE_PASSPHRASE         TEXT,                                       -- パスフレーズ
    LOGIN_AUTH_TYPE                 VARCHAR(2),                                 -- 認証方式
    WINRM_PORT                      INT,                                        -- ポート番号
    WINRM_SSL_CA_FILE               VARCHAR(255),                               -- サーバー証明書
    PROTOCOL_ID                     VARCHAR(2),                                 -- プロトコル
    OS_TYPE_ID                      VARCHAR(2),                                 -- OS種別
    PIONEER_LANG_ID                 VARCHAR(2),                                 -- LANG
    SSH_EXTRA_ARGS                  TEXT,                                       -- 接続オプション
    HOSTS_EXTRA_ARGS                TEXT,                                       -- インベントリファイル追加オプション
    ANSTWR_INSTANCE_GROUP_NAME      VARCHAR(255),                               -- インスタンスグループ名
    CREDENTIAL_TYPE_ID              VARCHAR(2),                                 -- 接続タイプ
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(SYSTEM_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_ANSC_DEVICE_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    SYSTEM_ID                       VARCHAR(40),                                -- 項番
    HARDAWRE_TYPE_ID                VARCHAR(2),                                 -- HW機器種別
    HOST_NAME                       VARCHAR(255),                               -- ホスト名
    HOST_DNS_NAME                   VARCHAR(255),                               -- DNSホスト名
    IP_ADDRESS                      VARCHAR(15),                                -- IPアドレス
    LOGIN_USER                      VARCHAR(255),                               -- ユーザ
    LOGIN_PW                        TEXT,                                       -- パスワード
    LOGIN_PW_ANSIBLE_VAULT          TEXT,                                       -- vailt暗号化パスワード
    SSH_KEY_FILE                    VARCHAR(255),                               -- ssh秘密鍵ファイル
    SSH_KEY_FILE_PASSPHRASE         TEXT,                                       -- パスフレーズ
    LOGIN_AUTH_TYPE                 VARCHAR(2),                                 -- 認証方式
    WINRM_PORT                      INT,                                        -- ポート番号
    WINRM_SSL_CA_FILE               VARCHAR(255),                               -- サーバー証明書
    PROTOCOL_ID                     VARCHAR(2),                                 -- プロトコル
    OS_TYPE_ID                      VARCHAR(2),                                 -- OS種別
    PIONEER_LANG_ID                 VARCHAR(2),                                 -- LANG
    SSH_EXTRA_ARGS                  TEXT,                                       -- 接続オプション
    HOSTS_EXTRA_ARGS                TEXT,                                       -- インベントリファイル追加オプション
    ANSTWR_INSTANCE_GROUP_NAME      VARCHAR(255),                               -- インスタンスグループ名
    CREDENTIAL_TYPE_ID              VARCHAR(2),                                 -- 接続タイプ
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 20102 インターフェース情報
CREATE TABLE T_ANSC_IF_INFO
(
    ANSIBLE_IF_INFO_ID              VARCHAR(40),                                -- 項番
    ANSIBLE_EXEC_MODE               VARCHAR(2),                                 -- 実行エンジン
    ANSIBLE_HOSTNAME                VARCHAR(255),                               -- ホスト
    ANSIBLE_PROTOCOL                VARCHAR(8),                                 -- プロトコル
    ANSIBLE_PORT                    INT,                                        -- ポート
    ANSIBLE_EXEC_USER               VARCHAR(255),                               -- 実行ユーザー
    ANSIBLE_ACCESS_KEY_ID           VARCHAR(64),                                -- Access_key_id
    ANSIBLE_SECRET_ACCESS_KEY       VARCHAR(64),                                -- Secret_access_key
    ANSTWR_HOST_ID                  VARCHAR(40),                                -- 代表ホスト
    ANSTWR_PROTOCOL                 VARCHAR(8),                                 -- プロトコル
    ANSTWR_PORT                     INT,                                        -- ポート
    ANSTWR_ORGANIZATION             VARCHAR(255),                               -- 組織名
    ANSTWR_AUTH_TOKEN               VARCHAR(255),                               -- 認証トークン
    ANSTWR_DEL_RUNTIME_DATA         VARCHAR(2),                                 -- 実行時データ削除
    ANSIBLE_PROXY_ADDRESS           VARCHAR(255),                               -- Address
    ANSIBLE_PROXY_PORT              INT,                                        -- Port
    ANSIBLE_VAULT_PASSWORD          VARCHAR(64),                                -- Ansible-vaultパスワード
    ANSIBLE_CORE_PATH               VARCHAR(255),                               -- Ansible-Coreインストールパス
    ANS_GIT_HOSTNAME                VARCHAR(255),                               -- ホスト名
    ANS_GIT_USER                    VARCHAR(255),                               -- ユーザー
    ANS_GIT_SSH_KEY_FILE            VARCHAR(255),                               -- ssh秘密鍵ファイル
    ANS_GIT_SSH_KEY_FILE_PASS       text,                                       -- パスフレーズ
    ANSIBLE_STORAGE_PATH_LNX        VARCHAR(255),                               -- データリレイストレージパス(ITA)
    ANSIBLE_STORAGE_PATH_ANS        VARCHAR(255),                               -- データリレイストレージパス(Ansible)
    CONDUCTOR_STORAGE_PATH_ANS      VARCHAR(255),                               -- Conductorインスタンスデータリレイストレージパス(Ansible)
    ANSIBLE_EXEC_OPTIONS            TEXT,                                       -- オプションパラメータ
    NULL_DATA_HANDLING_FLG          VARCHAR(2),                                 -- NULL連携
    ANSIBLE_NUM_PARALLEL_EXEC       INT,                                        -- 並列実行数
    ANSIBLE_REFRESH_INTERVAL        INT,                                        -- 状態監視周期(単位ミリ秒)
    ANSIBLE_TAILLOG_LINES           INT,                                        -- 進行状態表示行数
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ANSIBLE_IF_INFO_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_ANSC_IF_INFO_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    ANSIBLE_IF_INFO_ID              VARCHAR(40),                                -- 項番
    ANSIBLE_EXEC_MODE               VARCHAR(2),                                 -- 実行エンジン
    ANSIBLE_HOSTNAME                VARCHAR(255),                               -- ホスト
    ANSIBLE_PROTOCOL                VARCHAR(8),                                 -- プロトコル
    ANSIBLE_PORT                    INT,                                        -- ポート
    ANSIBLE_EXEC_USER               VARCHAR(255),                               -- 実行ユーザー
    ANSIBLE_ACCESS_KEY_ID           VARCHAR(64),                                -- Access_key_id
    ANSIBLE_SECRET_ACCESS_KEY       VARCHAR(64),                                -- Secret_access_key
    ANSTWR_HOST_ID                  VARCHAR(40),                                -- 代表ホスト
    ANSTWR_PROTOCOL                 VARCHAR(8),                                 -- プロトコル
    ANSTWR_PORT                     INT,                                        -- ポート
    ANSTWR_ORGANIZATION             VARCHAR(255),                               -- 組織名
    ANSTWR_AUTH_TOKEN               VARCHAR(255),                               -- 認証トークン
    ANSTWR_DEL_RUNTIME_DATA         VARCHAR(2),                                 -- 実行時データ削除
    ANSIBLE_PROXY_ADDRESS           VARCHAR(255),                               -- Address
    ANSIBLE_PROXY_PORT              INT,                                        -- Port
    ANSIBLE_VAULT_PASSWORD          VARCHAR(64),                                -- Ansible-vaultパスワード
    ANSIBLE_CORE_PATH               VARCHAR(255),                               -- Ansible-Coreインストールパス
    ANS_GIT_HOSTNAME                VARCHAR(255),                               -- ホスト名
    ANS_GIT_USER                    VARCHAR(255),                               -- ユーザー
    ANS_GIT_SSH_KEY_FILE            VARCHAR(255),                               -- ssh秘密鍵ファイル
    ANS_GIT_SSH_KEY_FILE_PASS       text,                                       -- パスフレーズ
    ANSIBLE_STORAGE_PATH_LNX        VARCHAR(255),                               -- データリレイストレージパス(ITA)
    ANSIBLE_STORAGE_PATH_ANS        VARCHAR(255),                               -- データリレイストレージパス(Ansible)
    CONDUCTOR_STORAGE_PATH_ANS      VARCHAR(255),                               -- Conductorインスタンスデータリレイストレージパス(Ansible)
    ANSIBLE_EXEC_OPTIONS            TEXT,                                       -- オプションパラメータ
    NULL_DATA_HANDLING_FLG          VARCHAR(2),                                 -- NULL連携
    ANSIBLE_NUM_PARALLEL_EXEC       INT,                                        -- 並列実行数
    ANSIBLE_REFRESH_INTERVAL        INT,                                        -- 状態監視周期(単位ミリ秒)
    ANSIBLE_TAILLOG_LINES           INT,                                        -- 進行状態表示行数
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 20103 AAC ホスト一覧
CREATE TABLE T_ANSC_TOWER_HOST
(
    ANSTWR_HOST_ID                  VARCHAR(40),                                -- 項番
    ANSTWR_HOSTNAME                 VARCHAR(255),                               -- ホスト
    ANSTWR_LOGIN_AUTH_TYPE          VARCHAR(2),                                 -- 認証方式
    ANSTWR_LOGIN_USER               VARCHAR(255),                               -- ユーザー
    ANSTWR_LOGIN_PASSWORD           TEXT,                                       -- パスワード
    ANSTWR_LOGIN_SSH_KEY_FILE       VARCHAR(255),                               -- ssh秘密鍵ファイル
    ANSTWR_LOGIN_SSH_KEY_FILE_PASS  TEXT,                                       -- パスフレーズ
    ANSTWR_ISOLATED_TYPE            VARCHAR(2),                                 -- isolatedTower
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ANSTWR_HOST_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_ANSC_TOWER_HOST_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    ANSTWR_HOST_ID                  VARCHAR(40),                                -- 項番
    ANSTWR_HOSTNAME                 VARCHAR(255),                               -- ホスト
    ANSTWR_LOGIN_AUTH_TYPE          VARCHAR(2),                                 -- 認証方式
    ANSTWR_LOGIN_USER               VARCHAR(255),                               -- ユーザー
    ANSTWR_LOGIN_PASSWORD           TEXT,                                       -- パスワード
    ANSTWR_LOGIN_SSH_KEY_FILE       VARCHAR(255),                               -- ssh秘密鍵ファイル
    ANSTWR_LOGIN_SSH_KEY_FILE_PASS  TEXT,                                       -- パスフレーズ
    ANSTWR_ISOLATED_TYPE            VARCHAR(2),                                 -- isolatedTower
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 20104 グローバル変数管理
CREATE TABLE T_ANSC_GLOBAL_VAR
(
    GBL_VARS_NAME_ID                VARCHAR(40),                                -- 項番
    VARS_NAME                       VARCHAR(255),                               -- グローバル変数名
    VARS_ENTRY                      TEXT,                                       -- 具体値
    VARS_DESCRIPTION                TEXT,                                       -- 変数名説明
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(GBL_VARS_NAME_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_ANSC_GLOBAL_VAR_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    GBL_VARS_NAME_ID                VARCHAR(40),                                -- 項番
    VARS_NAME                       VARCHAR(255),                               -- グローバル変数名
    VARS_ENTRY                      TEXT,                                       -- 具体値
    VARS_DESCRIPTION                TEXT,                                       -- 変数名説明
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 20105 ファイル管理
CREATE TABLE T_ANSC_CONTENTS_FILE
(
    CONTENTS_FILE_ID                VARCHAR(40),                                -- 素材ID
    CONTENTS_FILE_VARS_NAME         VARCHAR(255),                               -- ファイル埋込変数名
    CONTENTS_FILE                   VARCHAR(255),                               -- ファイル素材
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(CONTENTS_FILE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_ANSC_CONTENTS_FILE_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    CONTENTS_FILE_ID                VARCHAR(40),                                -- 素材ID
    CONTENTS_FILE_VARS_NAME         VARCHAR(255),                               -- ファイル埋込変数名
    CONTENTS_FILE                   VARCHAR(255),                               -- ファイル素材
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 20106 テンプレート管理
CREATE TABLE T_ANSC_TEMPLATE_FILE
(
    ANS_TEMPLATE_ID                 VARCHAR(40),                                -- 素材ID
    ANS_TEMPLATE_VARS_NAME          VARCHAR(255),                               -- テンプレート埋込変数名
    ANS_TEMPLATE_FILE               VARCHAR(255),                               -- テンプレート素材
    VARS_LIST                       TEXT,                                       -- 変数定義
    VAR_STRUCT_ANAL_JSON_STRING     LONGTEXT,                                   -- 変数定義解析結果
    ROLE_ONLY_FLAG                  VARCHAR(1),                                 -- 多段変数や読替変数定義有無
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ANS_TEMPLATE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_ANSC_TEMPLATE_FILE_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    ANS_TEMPLATE_ID                 VARCHAR(40),                                -- 素材ID
    ANS_TEMPLATE_VARS_NAME          VARCHAR(255),                               -- テンプレート埋込変数名
    ANS_TEMPLATE_FILE               VARCHAR(255),                               -- テンプレート素材
    VARS_LIST                       TEXT,                                       -- 変数定義
    VAR_STRUCT_ANAL_JSON_STRING     LONGTEXT,                                   -- 変数定義解析結果
    ROLE_ONLY_FLAG                  VARCHAR(1),                                 -- 多段変数や読替変数定義有無
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 20107 共通変数使用一覧
CREATE TABLE T_ANSC_COMVRAS_USLIST
(
    ROW_ID                          VARCHAR(40),                                -- 項番
    FILE_ID                         VARCHAR(2),                                 -- 資材種別
    VRA_ID                          VARCHAR(2),                                 -- 変数種別
    CONTENTS_ID                     VARCHAR(40),                                -- 使用素材集のPkey
    VAR_NAME                        VARCHAR(255),                               -- 変数名
    REVIVAL_FLAG                    VARCHAR(1),                                 -- 再利用フラグ
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ROW_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- 20108 管理対象外変数一覧
CREATE TABLE T_ANSC_UNMANAGED_VARLIST
(
    ROW_ID                          VARCHAR(40),                                -- 項番
    VAR_NAME                        VARCHAR(255),                               -- 変数名
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ROW_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_ANSC_UNMANAGED_VARLIST_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    ROW_ID                          VARCHAR(40),                                -- 項番
    VAR_NAME                        VARCHAR(255),                               -- 変数名
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 20401 Role ロール名管理
CREATE TABLE T_ANSR_ROLE_NAME
(
    ROLE_ID                         VARCHAR(40),                                -- 項番
    ROLE_PACKAGE_ID                 VARCHAR(40),                                -- ロールパッケージ名
    ROLE_NAME                       TEXT,                                       -- ロール名
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ROLE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- 20402 Role Movemnet一覧
CREATE VIEW V_ANSR_MOVEMENT AS
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
ANS_ENGINE_VIRTUALENV_NAME,
ANS_EXECUTION_ENVIRONMENT_NAME,
ANS_ANSIBLE_CONFIG_FILE,
NOTE,
DISUSE_FLAG,
LAST_UPDATE_TIMESTAMP,
LAST_UPDATE_USER
FROM 
  T_COMN_MOVEMENT
WHERE 
  ITA_EXT_STM_ID = 3;
CREATE VIEW V_ANSR_MOVEMENT_JNL AS
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
ANS_ENGINE_VIRTUALENV_NAME,
ANS_EXECUTION_ENVIRONMENT_NAME,
ANS_ANSIBLE_CONFIG_FILE,
NOTE,
DISUSE_FLAG,
LAST_UPDATE_TIMESTAMP,
LAST_UPDATE_USER
FROM 
  T_COMN_MOVEMENT_JNL
WHERE 
  ITA_EXT_STM_ID = 3;



-- 20403 Role ロールパッケージ管理
CREATE TABLE T_ANSR_MATL_COLL
(
    ROLE_PACKAGE_ID                 VARCHAR(40),                                -- 項番
    ROLE_PACKAGE_NAME               VARCHAR(255),                               -- ロールパッケージ名
    ROLE_PACKAGE_FILE               VARCHAR(255),                               -- ロールパッケージファイル(ZIP形式)
    VAR_STRUCT_ANAL_JSON_STRING     LONGTEXT,                                   -- 変数定義解析結果
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ROLE_PACKAGE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_ANSR_MATL_COLL_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    ROLE_PACKAGE_ID                 VARCHAR(40),                                -- 項番
    ROLE_PACKAGE_NAME               VARCHAR(255),                               -- ロールパッケージ名
    ROLE_PACKAGE_FILE               VARCHAR(255),                               -- ロールパッケージファイル(ZIP形式)
    VAR_STRUCT_ANAL_JSON_STRING     LONGTEXT,                                   -- 変数定義解析結果
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 20404 Role Movement-ロール紐付
CREATE TABLE T_ANSR_MVMT_MATL_LINK
(
    MVMT_MATL_LINK_ID               VARCHAR(40),                                -- 項番
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement
    ROLE_PACKAGE_ID                 VARCHAR(40),                                -- ロールパッケージ名
    ROLE_ID                         VARCHAR(40),                                -- ロール名
    INCLUDE_SEQ                     INT,                                        -- インクルード順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(MVMT_MATL_LINK_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_ANSR_MVMT_MATL_LINK_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    MVMT_MATL_LINK_ID               VARCHAR(40),                                -- 項番
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement
    ROLE_PACKAGE_ID                 VARCHAR(40),                                -- ロールパッケージ名
    ROLE_ID                         VARCHAR(40),                                -- ロール名
    INCLUDE_SEQ                     INT,                                        -- インクルード順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 20405 Role Movement-変数紐付
CREATE TABLE T_ANSR_MVMT_VAR_LINK
(
    MVMT_VAR_LINK_ID                VARCHAR(40),                                -- 項番
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement
    VARS_NAME                       VARCHAR(255),                               -- 変数名
    VARS_ATTRIBUTE_01               VARCHAR(2),                                 -- 変数タイプ
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(MVMT_VAR_LINK_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- 20406 Role 変数ネスト管理
CREATE TABLE T_ANSR_NESTVAR_MEMBER_MAX_COL
(
    MAX_COL_SEQ_ID                  VARCHAR(40),                                -- 項番
    MVMT_VAR_LINK_ID                VARCHAR(40),                                -- 変数名
    ARRAY_MEMBER_ID                 VARCHAR(40),                                -- メンバー変数名（繰返し有）
    MAX_COL_SEQ                     INT,                                        -- 最大繰返数
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(MAX_COL_SEQ_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_ANSR_NESTVAR_MEMBER_MAX_COL_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    MAX_COL_SEQ_ID                  VARCHAR(40),                                -- 項番
    MVMT_VAR_LINK_ID                VARCHAR(40),                                -- 変数名
    ARRAY_MEMBER_ID                 VARCHAR(40),                                -- メンバー変数名（繰返し有）
    MAX_COL_SEQ                     INT,                                        -- 最大繰返数
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 20407 Role 代入値自動登録
CREATE TABLE T_ANSR_VALUE_AUTOREG
(
    COLUMN_ID                       VARCHAR(40),                                -- 項番
    MENU_ID                         VARCHAR(40),                                -- メニュー名
    COLUMN_LIST_ID                  VARCHAR(40),                                -- 項目名
    COLUMN_ASSIGN_SEQ               INT,                                        -- 代入順序
    COL_TYPE                        VARCHAR(2),                                 -- 登録方式
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement
    MVMT_VAR_LINK_ID                VARCHAR(40),                                -- 変数名
    COL_SEQ_COMBINATION_ID          VARCHAR(40),                                -- メンバー変数
    ASSIGN_SEQ                      INT,                                        -- 代入順序
    NULL_DATA_HANDLING_FLG          VARCHAR(2),                                 -- NULL連携
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(COLUMN_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_ANSR_VALUE_AUTOREG_JNL
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
    COL_SEQ_COMBINATION_ID          VARCHAR(40),                                -- メンバー変数
    ASSIGN_SEQ                      INT,                                        -- 代入順序
    NULL_DATA_HANDLING_FLG          VARCHAR(2),                                 -- NULL連携
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 20408 Role 作業対象ホスト
CREATE TABLE T_ANSR_TGT_HOST
(
    PHO_LINK_ID                     VARCHAR(40),                                -- 項番
    EXECUTION_NO                    VARCHAR(40),                                -- 作業No.
    OPERATION_ID                    VARCHAR(40),                                -- オペレーション
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement
    SYSTEM_ID                       VARCHAR(40),                                -- ホスト
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(PHO_LINK_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- 20409 Role 代入値管理
CREATE TABLE T_ANSR_VALUE
(
    ASSIGN_ID                       VARCHAR(40),                                -- 項番
    EXECUTION_NO                    VARCHAR(40),                                -- 作業No.
    OPERATION_ID                    VARCHAR(40),                                -- オペレーション
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement
    SYSTEM_ID                       VARCHAR(40),                                -- ホスト
    MVMT_VAR_LINK_ID                VARCHAR(40),                                -- 変数名
    COL_SEQ_COMBINATION_ID          VARCHAR(40),                                -- メンバー変数名
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




-- 20412 Role 作業管理
CREATE TABLE T_ANSR_EXEC_STS_INST
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
    I_ENGINE_VIRTUALENV_NAME        VARCHAR(255),                               -- Movement/Ansible-Core利用情報/virtualenv
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
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(EXECUTION_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_ANSR_EXEC_STS_INST_JNL
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
    I_ENGINE_VIRTUALENV_NAME        VARCHAR(255),                               -- Movement/Ansible-Core利用情報/virtualenv
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
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 20413 Role 多段変数メンバー管理
CREATE TABLE T_ANSR_NESTVAR_MEMBER
(
    ARRAY_MEMBER_ID                 VARCHAR(40),                                -- 項番
    MVMT_VAR_LINK_ID                VARCHAR(40),                                -- 親変数名
    PARENT_VARS_KEY_ID              INT,                                        -- 親メンバー変数へのキー
    VARS_KEY_ID                     INT,                                        -- 自メンバー変数のキー
    VARS_NAME                       VARCHAR(256),                               -- メンバー変数名
    ARRAY_NEST_LEVEL                INT,                                        -- 階層
    ASSIGN_SEQ_NEED                 INT,                                        -- 代入順序有無
    COL_SEQ_NEED                    INT,                                        -- 列順序有無
    MEMBER_DISP                     INT,                                        -- 代入値管理系の表示有無
    MAX_COL_SEQ                     INT,                                        -- 最大繰返数
    VRAS_NAME_PATH                  VARCHAR(512),                               -- メンバー変数の階層パス
    VRAS_NAME_ALIAS                 VARCHAR(1024),                              -- 代入値管理系の表示メンバー変数名
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ARRAY_MEMBER_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- 20414 Role 多段変数配列組合せ管理
CREATE TABLE T_ANSR_NESTVAR_MEMBER_COL_COMB
(
    COL_SEQ_COMBINATION_ID          VARCHAR(40),                                -- 項番
    MVMT_VAR_LINK_ID                VARCHAR(40),                                -- 変数名
    ARRAY_MEMBER_ID                 VARCHAR(40),                                -- 多段変数項番
    COL_COMBINATION_MEMBER_ALIAS    TEXT,                                       -- プルダウン表示メンバー変数
    COL_SEQ_VALUE                   TEXT,                                       -- 列順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(COL_SEQ_COMBINATION_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- M001_登録方式マスタ
CREATE TABLE T_ANSC_AUTOREG_REG_TYPE
(
    TYPE_ID                         VARCHAR(2),                                 -- UUID
    TYPE_NAME_JA                    VARCHAR(256),                               -- 登録方式名(ja)
    TYPE_NAME_EN                    VARCHAR(256),                               -- 登録方式名(en)
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            VARCHAR(4000),                              -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(TYPE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- M002_Ansible実行種別マスタ
CREATE TABLE T_ANSC_EXEC_MODE
(
    EXEC_MODE_ID                    VARCHAR(2),                                 -- UUID
    EXEC_MODE_NAME_JA               VARCHAR(256),                               -- 実行モード名(ja)
    EXEC_MODE_NAME_EN               VARCHAR(256),                               -- 実行モード名(en)
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            VARCHAR(4000),                              -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(EXEC_MODE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- M003_変数タイプマスタ
CREATE TABLE T_ANSC_VAR_TYPE
(
    TYPE_ID                         VARCHAR(2),                                 -- UUID
    TYPE_NAME_JA                    VARCHAR(256),                               -- 変数タイプ名(ja)
    TYPE_NAME_EN                    VARCHAR(256),                               -- 変数タイプ名(en)
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            VARCHAR(4000),                              -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(TYPE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- M004_Pionnerプロトコルマスタ
CREATE TABLE T_ANSC_PIONEER_PROTOCOL_TYPE
(
    PROTOCOL_ID                     VARCHAR(2),                                 -- UUID
    PROTOCOL_NAME                   VARCHAR(256),                               -- プロトコル名
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            VARCHAR(4000),                              -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(PROTOCOL_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- M005_ログイン認証方式マスタ
CREATE TABLE T_ANSC_LOGIN_AUTH_TYPE
(
    LOGIN_AUTH_TYPE_ID              VARCHAR(2),                                 -- UUID
    LOGIN_AUTH_TYPE_NAME_JA         VARCHAR(256),                               -- 認証方式名(ja)
    LOGIN_AUTH_TYPE_NAME_EN         VARCHAR(256),                               -- 認証方式名(en)
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            VARCHAR(4000),                              -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(LOGIN_AUTH_TYPE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- M006_Ansibleステータスマスタ
CREATE TABLE T_ANSC_EXEC_STATUS
(
    EXEC_STATUS_ID                  VARCHAR(2),                                 -- UUID
    EXEC_STATUS_NAME_JA             VARCHAR(256),                               -- 実行状態名(ja)
    EXEC_STATUS_NAME_EN             VARCHAR(256),                               -- 実行状態名(en)
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            VARCHAR(4000),                              -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(EXEC_STATUS_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- M007_AnsiblePioneerLNAGマスタ
CREATE TABLE T_ANSC_PIONEER_LANG
(
    ID                              VARCHAR(2),                                 -- UUID
    NAME                            VARCHAR(256),                               -- 文字コード名
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            VARCHAR(4000),                              -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- M008_Ansible実行区分マスタ
CREATE TABLE T_ANSC_EXEC_ENGINE
(
    ID                              VARCHAR(2),                                 -- UUID
    NAME                            VARCHAR(256),                               -- 実行エンジン名
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            VARCHAR(4000),                              -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- M009_TowerJobTemplateプロパティ
CREATE TABLE T_ANSC_TWR_JOBTP_PROPERTY
(
    ROWID                           VARCHAR(2),                                 -- UUID
    KEY_NAME                        VARCHAR(64),                                -- パラメータ名
    SHORT_KEY_NAME                  VARCHAR(32),                                -- ショートカットパラメータ名
    PROPERTY_TYPE                   VARCHAR(64),                                -- パラメータタイプ
    PROPERTY_NAME                   VARCHAR(64),                                -- Towerプロパティ名
    TOWERONLY                       INT,                                        -- Towerのみのパラメータ判定
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            VARCHAR(4000),                              -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ROWID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- M010_ANSIBLETOWER_組織名マスタ
CREATE TABLE T_ANSC_TWR_ORGANIZATION
(
    ORGANIZATION_ITA_MANAGED_ID     VARCHAR(40),                                -- UUID
    ORGANIZATION_NAME               VARCHAR(256),                               -- 組織名
    ORGANIZATION_ID                 INT,                                        -- 組織名ID
    NOTE                            VARCHAR(4000),                              -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ORGANIZATION_ITA_MANAGED_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- M011_AnsibleTower認証情報 接続タイプマスタ
CREATE TABLE T_ANSC_TWR_CREDENTIAL_TYPE
(
    CREDENTIAL_TYPE_ID              VARCHAR(2),                                 -- UUID
    CREDENTIAL_TYPE_NAME            VARCHAR(256),                               -- Tower認証タイプ名
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            VARCHAR(4000),                              -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(CREDENTIAL_TYPE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- M012_収集状況マスタ
CREATE TABLE T_ANSC_COLLECT_STATUS
(
    COLLECT_STATUS_ID               VARCHAR(2),                                 -- UUID
    COLLECT_STATUS_NAME_JA          VARCHAR(256),                               -- 収集状態名(ja)
    COLLECT_STATUS_NAME_EN          VARCHAR(256),                               -- 収集状態名(en)
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            VARCHAR(4000),                              -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(COLLECT_STATUS_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- M013_Ansible共通変数利用リスト_変数種別マスタ
CREATE TABLE T_ANSC_COMVRAS_USLIST_V_ID
(
    ROW_ID                          VARCHAR(2),                                 -- UUID
    NAME                            VARCHAR(64),                                -- 変数種別
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ROW_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- M014_Ansible共通変数利用リスト_ファイル種別マスタ
CREATE TABLE T_ANSC_COMVRAS_USLIST_F_ID
(
    ROW_ID                          VARCHAR(2),                                 -- UUID
    NAME                            VARCHAR(64),                                -- 素材種別
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ROW_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- M015_ハードウェア種別マスタ
CREATE TABLE T_ANSC_HARDAWRE_TYPE
(
    HARDAWRE_TYPE_ID                VARCHAR(2),                                 -- UUID
    HARDAWRE_TYPE_NAME              VARCHAR(255),                               -- ハードウェア種別
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(HARDAWRE_TYPE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- AACインスタンスグループ管理
CREATE TABLE T_ANSC_TWR_INSTANCE_GROUP
(
    INSTANCE_GROUP_ITA_MANAGED_ID   VARCHAR(40),                                -- UUID
    INSTANCE_GROUP_NAME             VARCHAR(256),                               -- インスタンスグループ名
    INSTANCE_GROUP_ID               INT,                                        -- インスタンスグループID
    NOTE                            VARCHAR(4000),                              -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(INSTANCE_GROUP_ITA_MANAGED_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- AAC用ログイン認証方式マスタ
CREATE VIEW V_ANSC_TWR_LOGIN_AUTH_TYPE AS
SELECT 
  *
FROM 
  T_ANSC_LOGIN_AUTH_TYPE
WHERE 
  LOGIN_AUTH_TYPE_ID <= 4;



-- V001_代入値自動登録用項目表示ビュー
CREATE VIEW V_ANSC_COLUMN_LIST AS 
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
AND TAB_B.DISUSE_FLAG = 0
AND TAB_B.SUBSTITUTION_VALUE_LINK_FLAG =1
AND TAB_C.DISUSE_FLAG = 0
AND TAB_D.DISUSE_FLAG = 0;
CREATE VIEW V_ANSC_COLUMN_LIST_JNL AS 
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
AND TAB_B.DISUSE_FLAG = 0
AND TAB_B.SUBSTITUTION_VALUE_LINK_FLAG =1
AND TAB_C.DISUSE_FLAG = 0
AND TAB_D.DISUSE_FLAG = 0;



-- V002_作業管理検索ビュー
CREATE VIEW V_ANSC_EXEC_STS_INST     AS 
SELECT
  'Legacy-Role' as DRIVER_NAME, 'R' as DRIVER_ID, EXECUTION_NO, STATUS_ID, TIME_BOOK, DISUSE_FLAG, LAST_UPDATE_TIMESTAMP, TIME_REGISTER
FROM
  T_ANSR_EXEC_STS_INST
WHERE
  DISUSE_FLAG = '0';



-- V003_代表ホストビュー
CREATE VIEW V_ANSC_HOST AS 
SELECT
TAB_A.ANSTWR_HOST_ID,
TAB_A.ANSTWR_HOSTNAME,
TAB_A.ANSTWR_LOGIN_AUTH_TYPE,
TAB_A.ANSTWR_LOGIN_USER,
TAB_A.ANSTWR_LOGIN_PASSWORD,
TAB_A.ANSTWR_LOGIN_SSH_KEY_FILE,
TAB_A.ANSTWR_LOGIN_SSH_KEY_FILE_PASS,
TAB_A.ANSTWR_ISOLATED_TYPE,
TAB_A.NOTE,
TAB_A.DISUSE_FLAG,
TAB_A.LAST_UPDATE_TIMESTAMP,
TAB_A.LAST_UPDATE_USER
FROM 
T_ANSC_TOWER_HOST TAB_A
WHERE 
TAB_A.DISUSE_FLAG = 0
AND 
(TAB_A.ANSTWR_ISOLATED_TYPE is NULL OR TAB_A.ANSTWR_ISOLATED_TYPE <> '1');
CREATE VIEW V_ANSC_HOST_JNL AS 
SELECT
TAB_A.JOURNAL_SEQ_NO,
TAB_A.JOURNAL_REG_DATETIME,
TAB_A.JOURNAL_ACTION_CLASS,
TAB_A.ANSTWR_HOST_ID,
TAB_A.ANSTWR_HOSTNAME,
TAB_A.ANSTWR_LOGIN_AUTH_TYPE,
TAB_A.ANSTWR_LOGIN_USER,
TAB_A.ANSTWR_LOGIN_PASSWORD,
TAB_A.ANSTWR_LOGIN_SSH_KEY_FILE,
TAB_A.ANSTWR_LOGIN_SSH_KEY_FILE_PASS,
TAB_A.ANSTWR_ISOLATED_TYPE,
TAB_A.NOTE,
TAB_A.DISUSE_FLAG,
TAB_A.LAST_UPDATE_TIMESTAMP,
TAB_A.LAST_UPDATE_USER
FROM 
T_ANSC_TOWER_HOST_JNL TAB_A
WHERE 
TAB_A.DISUSE_FLAG = 0
AND 
(TAB_A.ANSTWR_ISOLATED_TYPE is NULL OR TAB_A.ANSTWR_ISOLATED_TYPE <> '1');



-- V004_ロールパッケージ名_ロール名ビュー
CREATE VIEW V_ANSR_ROLE AS
SELECT
TAB_A.ROLE_ID,
TAB_A.ROLE_PACKAGE_ID,
TAB_A.ROLE_NAME,
TAB_A.NOTE,
TAB_A.DISUSE_FLAG,
TAB_A.LAST_UPDATE_TIMESTAMP,
TAB_A.LAST_UPDATE_USER,
CONCAT(TAB_B.ROLE_PACKAGE_NAME, ':', TAB_A.ROLE_NAME) AS PAKAGE_ROLE_NAME
FROM
T_ANSR_ROLE_NAME TAB_A
LEFT JOIN
T_ANSR_MATL_COLL TAB_B ON (TAB_A.ROLE_PACKAGE_ID = TAB_B.ROLE_PACKAGE_ID)
WHERE
TAB_A.DISUSE_FLAG = 0
AND
TAB_B.DISUSE_FLAG = 0;
CREATE VIEW V_ANSR_ROLE_JNL AS
SELECT
TAB_A.ROLE_ID,
TAB_A.ROLE_PACKAGE_ID,
TAB_A.ROLE_NAME,
TAB_A.NOTE,
TAB_A.DISUSE_FLAG,
TAB_A.LAST_UPDATE_TIMESTAMP,
TAB_A.LAST_UPDATE_USER,
CONCAT(TAB_B.ROLE_PACKAGE_NAME, ':', TAB_A.ROLE_NAME) AS PAKAGE_ROLE_NAME
FROM
T_ANSR_ROLE_NAME TAB_A
LEFT JOIN
T_ANSR_MATL_COLL_JNL TAB_B ON (TAB_A.ROLE_PACKAGE_ID = TAB_B.ROLE_PACKAGE_ID)
WHERE
TAB_A.DISUSE_FLAG = 0
AND
TAB_B.DISUSE_FLAG = 0;



-- V005_変数ネスト管理 move_varビュー
CREATE VIEW V_ANSR_NESTVAR_MOVEMENT AS
SELECT 
TAB_A.MAX_COL_SEQ_ID,
TAB_A.MVMT_VAR_LINK_ID,
TAB_A.ARRAY_MEMBER_ID,
TAB_A.MAX_COL_SEQ,
TAB_A.NOTE,
TAB_A.DISUSE_FLAG,
TAB_A.LAST_UPDATE_TIMESTAMP,
TAB_A.LAST_UPDATE_USER,
TAB_B.MOVEMENT_ID
FROM
T_ANSR_NESTVAR_MEMBER_MAX_COL TAB_A
LEFT JOIN T_ANSR_MVMT_VAR_LINK TAB_B ON (TAB_A.MVMT_VAR_LINK_ID = TAB_B.MVMT_VAR_LINK_ID);
CREATE VIEW V_ANSR_NESTVAR_MOVEMENT_JNL AS
SELECT 
JOURNAL_SEQ_NO,
JOURNAL_REG_DATETIME,
JOURNAL_ACTION_CLASS,
TAB_A.MAX_COL_SEQ_ID,
TAB_A.MVMT_VAR_LINK_ID,
TAB_A.ARRAY_MEMBER_ID,
TAB_A.MAX_COL_SEQ,
TAB_A.NOTE,
TAB_A.DISUSE_FLAG,
TAB_A.LAST_UPDATE_TIMESTAMP,
TAB_A.LAST_UPDATE_USER,
TAB_B.MOVEMENT_ID
FROM
T_ANSR_NESTVAR_MEMBER_MAX_COL_JNL TAB_A
LEFT JOIN T_ANSR_MVMT_VAR_LINK TAB_B ON (TAB_A.MVMT_VAR_LINK_ID = TAB_B.MVMT_VAR_LINK_ID);



-- V006_代入値自動登録_メニュー名ビュー
CREATE VIEW V_ANSC_MENU AS 
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
TAB_C.MENU_NAME_JA,
TAB_C.MENU_NAME_EN
FROM
T_COMN_MENU_COLUMN_LINK TAB_A 
LEFT JOIN
T_COMN_MENU_TABLE_LINK TAB_B ON (TAB_A.MENU_ID = TAB_B.MENU_ID)
LEFT JOIN
T_COMN_MENU TAB_C ON (TAB_B.MENU_ID = TAB_C.MENU_ID)
WHERE TAB_A.AUTOREG_HIDE_ITEM = 0
AND TAB_A.DISUSE_FLAG = 0
AND (TAB_B.SHEET_TYPE = 1 OR TAB_B.SHEET_TYPE = 4)
AND TAB_B.DISUSE_FLAG = 0
AND TAB_B.SUBSTITUTION_VALUE_LINK_FLAG =1
AND TAB_C.DISUSE_FLAG = 0;
CREATE VIEW V_ANSC_MENU_JNL AS 
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
TAB_C.MENU_NAME_JA,
TAB_C.MENU_NAME_EN
FROM
T_COMN_MENU_COLUMN_LINK_JNL TAB_A 
LEFT JOIN
T_COMN_MENU_TABLE_LINK_JNL TAB_B ON (TAB_A.MENU_ID = TAB_B.MENU_ID)
LEFT JOIN
T_COMN_MENU_JNL TAB_C ON (TAB_B.MENU_ID = TAB_C.MENU_ID)
WHERE TAB_A.AUTOREG_HIDE_ITEM = 0
AND TAB_A.DISUSE_FLAG = 0
AND (TAB_B.SHEET_TYPE = 1 OR TAB_B.SHEET_TYPE = 4)
AND TAB_B.DISUSE_FLAG = 0
AND TAB_B.SUBSTITUTION_VALUE_LINK_FLAG =1
AND TAB_C.DISUSE_FLAG = 0;



-- V007_代入値自動登録_Movement名_変数名ビュー
CREATE VIEW V_ANSR_VAL_VARS_LINK AS
SELECT
TAB_A.MVMT_VAR_LINK_ID,
TAB_A.MOVEMENT_ID,
TAB_A.VARS_NAME,
TAB_A.VARS_ATTRIBUTE_01,
TAB_A.NOTE,
TAB_A.DISUSE_FLAG,
TAB_A.LAST_UPDATE_TIMESTAMP,
TAB_A.LAST_UPDATE_USER,
CONCAT(TAB_B.MOVEMENT_NAME, ":", TAB_A.VARS_NAME) AS MOVEMENT_VARS_NAME
FROM
T_ANSR_MVMT_VAR_LINK TAB_A
LEFT JOIN
V_ANSR_MOVEMENT TAB_B ON (TAB_A.MOVEMENT_ID = TAB_B.MOVEMENT_ID)
WHERE
TAB_A.DISUSE_FLAG = 0
AND
TAB_B.DISUSE_FLAG = 0;
CREATE VIEW V_ANSR_VAL_VARS_LINK_JNL AS
SELECT
TAB_A.MVMT_VAR_LINK_ID,
TAB_A.MOVEMENT_ID,
TAB_A.VARS_NAME,
TAB_A.VARS_ATTRIBUTE_01,
TAB_A.NOTE,
TAB_A.DISUSE_FLAG,
TAB_A.LAST_UPDATE_TIMESTAMP,
TAB_A.LAST_UPDATE_USER,
CONCAT(TAB_B.MOVEMENT_NAME, ":", TAB_A.VARS_NAME) AS MOVEMENT_VARS_NAME
FROM
T_ANSR_MVMT_VAR_LINK TAB_A
LEFT JOIN
V_ANSR_MOVEMENT_JNL TAB_B ON (TAB_A.MOVEMENT_ID = TAB_B.MOVEMENT_ID)
WHERE
TAB_A.DISUSE_FLAG = 0
AND
TAB_B.DISUSE_FLAG = 0;



-- V008_代入値自動登録_Movement名_変数名_メンバー
CREATE VIEW V_ANSR_VAL_COL_SEQ_COMBINATION AS
SELECT
TAB_A.COL_SEQ_COMBINATION_ID,
TAB_A.MVMT_VAR_LINK_ID,
TAB_A.ARRAY_MEMBER_ID,
TAB_A.COL_COMBINATION_MEMBER_ALIAS,
TAB_A.NOTE,
TAB_A.DISUSE_FLAG,
TAB_A.LAST_UPDATE_TIMESTAMP,
TAB_A.LAST_UPDATE_USER,
TAB_B.MOVEMENT_ID,
CONCAT(TAB_D.MOVEMENT_NAME, ":", CONCAT(TAB_B.VARS_NAME, ":", TAB_A.COL_COMBINATION_MEMBER_ALIAS)) AS MOVEMENT_VARS_COL_COMBINATION_MEMBER
FROM
T_ANSR_NESTVAR_MEMBER_COL_COMB TAB_A
LEFT JOIN
T_ANSR_MVMT_VAR_LINK TAB_B ON (TAB_A.MVMT_VAR_LINK_ID = TAB_B.MVMT_VAR_LINK_ID)
LEFT JOIN
V_ANSR_MOVEMENT TAB_D ON (TAB_B.MOVEMENT_ID = TAB_D.MOVEMENT_ID)
WHERE
TAB_A.DISUSE_FLAG = 0
AND
TAB_B.DISUSE_FLAG = 0
AND
TAB_D.DISUSE_FLAG = 0;
CREATE VIEW V_ANSR_VAL_COL_SEQ_COMBINATION_JNL AS
SELECT
TAB_A.COL_SEQ_COMBINATION_ID,
TAB_A.MVMT_VAR_LINK_ID,
TAB_A.ARRAY_MEMBER_ID,
TAB_A.COL_COMBINATION_MEMBER_ALIAS,
TAB_A.NOTE,
TAB_A.DISUSE_FLAG,
TAB_A.LAST_UPDATE_TIMESTAMP,
TAB_A.LAST_UPDATE_USER,
CONCAT(TAB_D.MOVEMENT_NAME, ":", CONCAT(TAB_B.VARS_NAME, ":", TAB_A.COL_COMBINATION_MEMBER_ALIAS)) AS MOVEMENT_VARS_COL_COMBINATION_MEMBER
FROM
T_ANSR_NESTVAR_MEMBER_COL_COMB TAB_A
LEFT JOIN
T_ANSR_MVMT_VAR_LINK TAB_B ON (TAB_A.MVMT_VAR_LINK_ID = TAB_B.MVMT_VAR_LINK_ID)
LEFT JOIN
V_ANSR_MOVEMENT_JNL TAB_D ON (TAB_B.MOVEMENT_ID = TAB_D.MOVEMENT_ID)
WHERE
TAB_A.DISUSE_FLAG = 0
AND
TAB_B.DISUSE_FLAG = 0
AND
TAB_D.DISUSE_FLAG = 0;



-- V009_多段変数メンバー管理_Movementビュー
CREATE VIEW V_ANSR_NESTVAR_MEMBER_MENU AS
SELECT
TAB_A.ARRAY_MEMBER_ID,
TAB_A.MVMT_VAR_LINK_ID,
TAB_A.PARENT_VARS_KEY_ID,
TAB_A.VARS_KEY_ID,
TAB_A.VARS_NAME,
TAB_A.ARRAY_NEST_LEVEL,
TAB_A.ASSIGN_SEQ_NEED,
TAB_A.COL_SEQ_NEED,
TAB_A.MEMBER_DISP,
TAB_A.MAX_COL_SEQ,
TAB_A.VRAS_NAME_PATH,
TAB_A.VRAS_NAME_ALIAS,
TAB_A.NOTE,
TAB_A.DISUSE_FLAG,
TAB_A.LAST_UPDATE_TIMESTAMP,
TAB_A.LAST_UPDATE_USER,
TAB_B.MOVEMENT_ID
FROM
T_ANSR_NESTVAR_MEMBER TAB_A
LEFT JOIN
T_ANSR_MVMT_VAR_LINK TAB_B ON (TAB_A.MVMT_VAR_LINK_ID = TAB_B.MVMT_VAR_LINK_ID);



-- V010_多段変数配列組合せ管理_Movementビュー
CREATE VIEW V_ANSR_NESTVAR_MEMBER_COL_COMB_MENU AS
SELECT
TAB_A.COL_SEQ_COMBINATION_ID,
TAB_A.MVMT_VAR_LINK_ID,
TAB_A.ARRAY_MEMBER_ID,
TAB_A.COL_COMBINATION_MEMBER_ALIAS,
TAB_A.NOTE,
TAB_A.DISUSE_FLAG,
TAB_A.LAST_UPDATE_TIMESTAMP,
TAB_A.LAST_UPDATE_USER,
TAB_B.MOVEMENT_ID
FROM
T_ANSR_NESTVAR_MEMBER_COL_COMB TAB_A
LEFT JOIN
T_ANSR_MVMT_VAR_LINK TAB_B ON (TAB_A.MVMT_VAR_LINK_ID = TAB_B.MVMT_VAR_LINK_ID);



