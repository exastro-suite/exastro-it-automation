-- T_ANSC_DEVICE: UPDATE
-- - サーバー証明書:WINRM_SSL_CA_FILEを削除
-- - winrm公開鍵ファイル:WINRM_CERT_PEM_FILEを追加
-- - winrm秘密鍵ファイル:WINRM_CERT_KEY_PEM_FILEを追加
ALTER TABLE T_ANSC_DEVICE     ADD  COLUMN WINRM_CERT_PEM_FILE VARCHAR(255)  AFTER WINRM_PORT;
ALTER TABLE T_ANSC_DEVICE     ADD  COLUMN WINRM_CERT_KEY_PEM_FILE VARCHAR(255)  AFTER WINRM_CERT_PEM_FILE;
ALTER TABLE T_ANSC_DEVICE     DROP COLUMN WINRM_SSL_CA_FILE;
ALTER TABLE T_ANSC_DEVICE_JNL ADD  COLUMN WINRM_CERT_PEM_FILE VARCHAR(255)  AFTER WINRM_PORT;
ALTER TABLE T_ANSC_DEVICE_JNL ADD  COLUMN WINRM_CERT_KEY_PEM_FILE VARCHAR(255)  AFTER WINRM_CERT_PEM_FILE;
ALTER TABLE T_ANSC_DEVICE_JNL DROP COLUMN WINRM_SSL_CA_FILE;

-- ------------------------------------------------------------
-- - ▼ Legacy 代入値自動登録・Pioneer 代入値自動登録・Role 代入値自動登録に
-- -    MENU_NAME_REST:メニュー名(Rest)追加
-- ------------------------------------------------------------
ALTER TABLE T_ANSL_VALUE_AUTOREG     ADD  COLUMN MENU_NAME_REST VARCHAR(40)  AFTER COLUMN_ID;
ALTER TABLE T_ANSP_VALUE_AUTOREG     ADD  COLUMN MENU_NAME_REST VARCHAR(40)  AFTER COLUMN_ID;
ALTER TABLE T_ANSR_VALUE_AUTOREG     ADD  COLUMN MENU_NAME_REST VARCHAR(40)  AFTER COLUMN_ID;
ALTER TABLE T_ANSL_VALUE_AUTOREG_JNL ADD  COLUMN MENU_NAME_REST VARCHAR(40)  AFTER COLUMN_ID;
ALTER TABLE T_ANSP_VALUE_AUTOREG_JNL ADD  COLUMN MENU_NAME_REST VARCHAR(40)  AFTER COLUMN_ID;
ALTER TABLE T_ANSR_VALUE_AUTOREG_JNL ADD  COLUMN MENU_NAME_REST VARCHAR(40)  AFTER COLUMN_ID;

-- ------------------------------------------------------------
-- - ▲ 20110 実行環境定義テンプレート管理　追加
-- ------------------------------------------------------------
CREATE TABLE T_ANSC_EXECDEV_TEMPLATE_FILE
(
    ROW_ID                          VARCHAR(40),                                -- 項番
    TEMPLATE_NAME                   VARCHAR(255),                               -- テンプレート名
    TEMPLATE_FILE                   VARCHAR(255),                               -- テンプレートファイル
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ROW_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_ANSC_EXECDEV_TEMPLATE_FILE_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    ROW_ID                          VARCHAR(40),                                -- 項番
    TEMPLATE_NAME                   VARCHAR(255),                               -- テンプレート名
    TEMPLATE_FILE                   VARCHAR(255),                               -- テンプレートファイル
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

-- ------------------------------------------------------------
-- - ▲ 20111 実行環境管理　追加
-- ------------------------------------------------------------
CREATE TABLE T_ANSC_EXECDEV
(
    ROW_ID                          VARCHAR(40),                                -- 項番
    EXECUTION_ENVIRONMENT_NAME      VARCHAR(255),                               -- 実行環境名
    BUILD_TYPE                      VARCHAR(40),                                -- 実行環境構築方法
    TAG_NAME                        VARCHAR(255),                               -- タグ名
    EXECUTION_ENVIRONMENT_ID        VARCHAR(100),                               -- 実行環境定義名
    TEMPLATE_ID                     VARCHAR(40),                                -- テンプレート名
    BASE_IMAGE_OS_TYPE              VARCHAR(40),                                -- ベースイメージOS種別
    USER_NAME                       VARCHAR(255),                               -- ユーザー
    PASSWORD                        TEXT,                                       -- パスワード
    ATTACH_REPOSITORY               VARCHAR(255),                               -- アタッチリポジトリ
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ROW_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_ANSC_EXECDEV_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    ROW_ID                          VARCHAR(40),                                -- 項番
    EXECUTION_ENVIRONMENT_NAME      VARCHAR(255),                               -- 実行環境名
    BUILD_TYPE                      VARCHAR(40),                                -- 実行環境構築方法
    TAG_NAME                        VARCHAR(255),                               -- タグ名
    EXECUTION_ENVIRONMENT_ID        VARCHAR(100),                               -- 実行環境定義名
    TEMPLATE_ID                     VARCHAR(40),                                -- テンプレート名
    BASE_IMAGE_OS_TYPE              VARCHAR(40),                                -- ベースイメージOS種別
    USER_NAME                       VARCHAR(255),                               -- ユーザー
    PASSWORD                        TEXT,                                       -- パスワード
    ATTACH_REPOSITORY               VARCHAR(255),                               -- アタッチリポジトリ
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;


-- ------------------------------------------------------------
-- - ▲ 20112 エージェント管理　追加
-- ------------------------------------------------------------
CREATE TABLE T_ANSC_AGENT
(
    ROW_ID                          VARCHAR(40),                                -- 項番
    AGENT_NAME                      VARCHAR(255),                               -- エージェント名
    VERSION                         VARCHAR(40),                                -- バージョン
    STATUS_ID                       VARCHAR(2),                                 -- ステータス
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ROW_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

-- ------------------------------------------------------------
-- - ▲ Legacy Movement一覧
-- -    AG_EXECUTION_ENVIRONMENT_NAME  実行環境                    追加
-- -    AG_BUILDER_OPTIONS             ansible-builder パラメータ  追加
-- ------------------------------------------------------------
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
AG_EXECUTION_ENVIRONMENT_NAME,
AG_BUILDER_OPTIONS,
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
AG_EXECUTION_ENVIRONMENT_NAME,
AG_BUILDER_OPTIONS,
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

-- ------------------------------------------------------------
-- - ▲ Legacy 作業管理
-- -    ABORT_EXECUTE_FLAG:              緊急停止フラグ　追加
-- -    I_AG_EXECUTION_ENVIRONMENT_NAME  実行環境                    追加
-- -    I_AG_BUILDER_OPTIONS             ansible-builder パラメータ  追加
-- ------------------------------------------------------------
ALTER TABLE T_ANSL_EXEC_STS_INST     ADD  ABORT_EXECUTE_FLAG               VARCHAR(2)    AFTER EXEC_MODE;
ALTER TABLE T_ANSL_EXEC_STS_INST     ADD  I_AG_EXECUTION_ENVIRONMENT_NAME  VARCHAR(255)  AFTER I_ANS_PLAYBOOK_HED_DEF;
ALTER TABLE T_ANSL_EXEC_STS_INST     ADD  I_AG_BUILDER_OPTIONS             TEXT          AFTER I_ANS_PLAYBOOK_HED_DEF;
ALTER TABLE T_ANSL_EXEC_STS_INST_JNL ADD  ABORT_EXECUTE_FLAG               VARCHAR(2)    AFTER EXEC_MODE;
ALTER TABLE T_ANSL_EXEC_STS_INST_JNL ADD  I_AG_EXECUTION_ENVIRONMENT_NAME  VARCHAR(255)  AFTER I_ANS_PLAYBOOK_HED_DEF;
ALTER TABLE T_ANSL_EXEC_STS_INST_JNL ADD  I_AG_BUILDER_OPTIONS             TEXT          AFTER I_ANS_PLAYBOOK_HED_DEF;

-- ------------------------------------------------------------
-- - ▲ pioneer Movement一覧
-- -    AG_EXECUTION_ENVIRONMENT_NAME  実行環境                    追加
-- -    AG_BUILDER_OPTIONS             ansible-builder パラメータ  追加
-- ------------------------------------------------------------
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
AG_EXECUTION_ENVIRONMENT_NAME,
AG_BUILDER_OPTIONS,
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
AG_EXECUTION_ENVIRONMENT_NAME,
AG_BUILDER_OPTIONS,
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

-- ------------------------------------------------------------
-- - ▲ pioneer 作業管理
-- -    削除
-- -    ABORT_EXECUTE_FLAG:              緊急停止フラグ　追加
-- -    I_AG_EXECUTION_ENVIRONMENT_NAME  実行環境                    追加
-- -    I_AG_BUILDER_OPTIONS             ansible-builder パラメータ  追加
-- ------------------------------------------------------------
ALTER TABLE T_ANSP_EXEC_STS_INST     ADD  ABORT_EXECUTE_FLAG               VARCHAR(2)    AFTER EXEC_MODE;
ALTER TABLE T_ANSP_EXEC_STS_INST     ADD  I_AG_EXECUTION_ENVIRONMENT_NAME  VARCHAR(255)  AFTER I_ANS_PLAYBOOK_HED_DEF;
ALTER TABLE T_ANSP_EXEC_STS_INST     ADD  I_AG_BUILDER_OPTIONS             TEXT          AFTER I_ANS_PLAYBOOK_HED_DEF;
ALTER TABLE T_ANSP_EXEC_STS_INST_JNL ADD  ABORT_EXECUTE_FLAG               VARCHAR(2)    AFTER EXEC_MODE;
ALTER TABLE T_ANSP_EXEC_STS_INST_JNL ADD  I_AG_EXECUTION_ENVIRONMENT_NAME  VARCHAR(255)  AFTER I_ANS_PLAYBOOK_HED_DEF;
ALTER TABLE T_ANSP_EXEC_STS_INST_JNL ADD  I_AG_BUILDER_OPTIONS             TEXT          AFTER I_ANS_PLAYBOOK_HED_DEF;

-- ------------------------------------------------------------
-- - ▲ Legacy-role Movement一覧
-- -    AG_EXECUTION_ENVIRONMENT_NAME  実行環境                    追加
-- -    AG_BUILDER_OPTIONS             ansible-builder パラメータ  追加
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW V_ANSR_MOVEMENT AS
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
AG_EXECUTION_ENVIRONMENT_NAME,
AG_BUILDER_OPTIONS,
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

CREATE OR REPLACE VIEW V_ANSR_MOVEMENT_JNL AS
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
AG_EXECUTION_ENVIRONMENT_NAME,
AG_BUILDER_OPTIONS,
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

-- ------------------------------------------------------------
-- - ▲ Legacy-role 作業管理
-- -    削除
-- -    ABORT_EXECUTE_FLAG:              緊急停止フラグ　追加
-- -    I_AG_EXECUTION_ENVIRONMENT_NAME  実行環境                    追加
-- -    I_AG_BUILDER_OPTIONS             ansible-builder パラメータ  追加
-- ------------------------------------------------------------
ALTER TABLE T_ANSR_EXEC_STS_INST     ADD  ABORT_EXECUTE_FLAG               VARCHAR(2)    AFTER EXEC_MODE;
ALTER TABLE T_ANSR_EXEC_STS_INST     ADD  I_AG_EXECUTION_ENVIRONMENT_NAME  VARCHAR(255)  AFTER I_ANS_PLAYBOOK_HED_DEF;
ALTER TABLE T_ANSR_EXEC_STS_INST     ADD  I_AG_BUILDER_OPTIONS             TEXT          AFTER I_ANS_PLAYBOOK_HED_DEF;
ALTER TABLE T_ANSR_EXEC_STS_INST_JNL ADD  ABORT_EXECUTE_FLAG               VARCHAR(2)    AFTER EXEC_MODE;
ALTER TABLE T_ANSR_EXEC_STS_INST_JNL ADD  I_AG_EXECUTION_ENVIRONMENT_NAME  VARCHAR(255)  AFTER I_ANS_PLAYBOOK_HED_DEF;
ALTER TABLE T_ANSR_EXEC_STS_INST_JNL ADD  I_AG_BUILDER_OPTIONS             TEXT          AFTER I_ANS_PLAYBOOK_HED_DEF;


-- ------------------------------------------------------------
-- - ▲ M017_実行環境構築方法マスタ
-- ------------------------------------------------------------
CREATE TABLE T_ANSC_EXECDEV_BUILD_TYPE
(
    ROW_ID                          VARCHAR(2),                                 -- ROW_ID
    NAME                            VARCHAR(64),                                -- 構築方法名
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ROW_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

-- ------------------------------------------------------------
-- - ▲ M018_ベースイメージOS種別マスタ
-- ------------------------------------------------------------
CREATE TABLE T_ANSC_BASE_IMAGE_OS_TYPE
(
    ROW_ID                          VARCHAR(2),                                 -- ROW_ID
    NAME                            VARCHAR(255),                               -- OS種別名
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ROW_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

-- -------------------------------------------------------
-- - ▼パラメータシート 実行環境バラメータ定義
-- -------------------------------------------------------
CREATE TABLE `T_CMDB_f7a294e8-a7a7-4d03-8a76-e2f910db55d7`
(
    ROW_ID                          VARCHAR(40),                                -- ROW_ID
    DATA_JSON                       LONGTEXT,                                   -- 項目定義JOSN
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ROW_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;


CREATE TABLE `T_CMDB_f7a294e8-a7a7-4d03-8a76-e2f910db55d7_JNL`
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR(8),                                 -- 履歴用変更種別
    ROW_ID                          VARCHAR(40),                                -- ROW_ID
    DATA_JSON                       LONGTEXT,                                   -- 項目定義JOSN
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

-- -------------------------------------------------------
-- - ▼パラメータシート 実行環境バラメータ定義　INDEX定義
-- -------------------------------------------------------
CREATE INDEX `IND_T_CMDB_f7a294e8-a7a7-4d03-8a76-e2f910db55d7_01` ON `T_CMDB_f7a294e8-a7a7-4d03-8a76-e2f910db55d7`(DISUSE_FLAG);

-- -------------------------------------------------------
-- - ▼ M019_AnsibleExecutionステータスマスタ
-- -------------------------------------------------------
CREATE TABLE T_ANSC_EXECUTION_STATUS
(
    STATUS_ID                       VARCHAR(2),                                 -- UUID
    STATUS_NAME_JA                  VARCHAR(256),                               -- ステータス名(ja)
    STATUS_NAME_EN                  VARCHAR(256),                               -- ステータス名(en)
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            VARCHAR(4000),                              -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(STATUS_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;
-- -------------------------------------------------------
-- - ▲ M019_AnsibleExecutionステータスマスタ
-- -------------------------------------------------------