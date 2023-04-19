-- ------------------------------------------------------------
-- �� TABLE CREATE START
-- ------------------------------------------------------------
-- 20109 ���W���ڒl�Ǘ�
CREATE TABLE T_ANSC_CMDB_LINK
(
    ROW_ID                          VARCHAR(40),                                -- ����
    FILE_PREFIX                     VARCHAR(4000),                              -- PREFIX(�t�@�C����)
    VARS_NAME                       VARCHAR(4000),                              -- �ϐ���
    VRAS_MEMBER_NAME                VARCHAR(4000),                              -- �����o�ϐ�
    PARSE_TYPE_ID                   VARCHAR(2),                                 -- �p�[�X�`��
    COLUMN_LIST_ID                  VARCHAR(40),                                -- ����
    INPUT_ORDER                     INT,                                        -- �������
    NOTE                            TEXT,                                       -- ���l
    DISUSE_FLAG                     VARCHAR(1),                                 -- �p�~�t���O
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- �ŏI�X�V����
    LAST_UPDATE_USER                VARCHAR(40),                                -- �ŏI�X�V��
    PRIMARY KEY(ROW_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_ANSC_CMDB_LINK_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- ����p�V�[�P���X
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- ����p�ύX����
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- ����p�ύX���
    ROW_ID                          VARCHAR(40),                                -- ����
    FILE_PREFIX                     VARCHAR(4000),                              -- PREFIX(�t�@�C����)
    VARS_NAME                       VARCHAR(4000),                              -- �ϐ���
    VRAS_MEMBER_NAME                VARCHAR(4000),                              -- �����o�ϐ�
    PARSE_TYPE_ID                   VARCHAR(2),                                 -- �p�[�X�`��
    COLUMN_LIST_ID                  VARCHAR(40),                                -- ����
    INPUT_ORDER                     INT,                                        -- �������
    NOTE                            TEXT,                                       -- ���l
    DISUSE_FLAG                     VARCHAR(1),                                 -- �p�~�t���O
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- �ŏI�X�V����
    LAST_UPDATE_USER                VARCHAR(40),                                -- �ŏI�X�V��
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 20201 Legacy Movemnet�ꗗ
CREATE VIEW V_ANSL_MOVEMENT AS
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
CREATE VIEW V_ANSL_MOVEMENT_JNL AS
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



-- 20202 Legacy Playbook�f�ޏW
CREATE TABLE T_ANSL_MATL_COLL
(
    PLAYBOOK_MATTER_ID              VARCHAR(40),                                -- ����
    PLAYBOOK_MATTER_NAME            VARCHAR(255),                               -- Playbook�f�ޖ�
    PLAYBOOK_MATTER_FILE            VARCHAR(255),                               -- Playbook�f��
    NOTE                            TEXT,                                       -- ���l
    DISUSE_FLAG                     VARCHAR(1),                                 -- �p�~�t���O
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- �ŏI�X�V����
    LAST_UPDATE_USER                VARCHAR(40),                                -- �ŏI�X�V��
    PRIMARY KEY(PLAYBOOK_MATTER_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_ANSL_MATL_COLL_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- ����p�V�[�P���X
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- ����p�ύX����
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- ����p�ύX���
    PLAYBOOK_MATTER_ID              VARCHAR(40),                                -- ����
    PLAYBOOK_MATTER_NAME            VARCHAR(255),                               -- Playbook�f�ޖ�
    PLAYBOOK_MATTER_FILE            VARCHAR(255),                               -- Playbook�f��
    NOTE                            TEXT,                                       -- ���l
    DISUSE_FLAG                     VARCHAR(1),                                 -- �p�~�t���O
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- �ŏI�X�V����
    LAST_UPDATE_USER                VARCHAR(40),                                -- �ŏI�X�V��
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 20203 Legacy Movement-�ϐ��R�t
CREATE TABLE T_ANSL_MVMT_VAR_LINK
(
    MVMT_VAR_LINK_ID                VARCHAR(40),                                -- ����
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement
    VARS_NAME                       VARCHAR(255),                               -- �ϐ���
    NOTE                            TEXT,                                       -- ���l
    DISUSE_FLAG                     VARCHAR(1),                                 -- �p�~�t���O
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- �ŏI�X�V����
    LAST_UPDATE_USER                VARCHAR(40),                                -- �ŏI�X�V��
    PRIMARY KEY(MVMT_VAR_LINK_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- 20204 Legacy Move-Playbook�R�t
CREATE TABLE T_ANSL_MVMT_MATL_LINK
(
    MVMT_MATL_LINK_ID               VARCHAR(40),                                -- ����
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement
    PLAYBOOK_MATTER_ID              VARCHAR(40),                                -- Playbook�f��
    INCLUDE_SEQ                     INT,                                        -- �C���N���[�h����
    NOTE                            TEXT,                                       -- ���l
    DISUSE_FLAG                     VARCHAR(1),                                 -- �p�~�t���O
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- �ŏI�X�V����
    LAST_UPDATE_USER                VARCHAR(40),                                -- �ŏI�X�V��
    PRIMARY KEY(MVMT_MATL_LINK_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_ANSL_MVMT_MATL_LINK_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- ����p�V�[�P���X
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- ����p�ύX����
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- ����p�ύX���
    MVMT_MATL_LINK_ID               VARCHAR(40),                                -- ����
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement
    PLAYBOOK_MATTER_ID              VARCHAR(40),                                -- Playbook�f��
    INCLUDE_SEQ                     INT,                                        -- �C���N���[�h����
    NOTE                            TEXT,                                       -- ���l
    DISUSE_FLAG                     VARCHAR(1),                                 -- �p�~�t���O
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- �ŏI�X�V����
    LAST_UPDATE_USER                VARCHAR(40),                                -- �ŏI�X�V��
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 20205 Legacy ����l�����o�^
CREATE TABLE T_ANSL_VALUE_AUTOREG
(
    COLUMN_ID                       VARCHAR(40),                                -- ����
    MENU_ID                         VARCHAR(40),                                -- ���j���[��
    COLUMN_LIST_ID                  VARCHAR(40),                                -- ���ږ�
    COLUMN_ASSIGN_SEQ               INT,                                        -- �������
    COL_TYPE                        VARCHAR(2),                                 -- �o�^����
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement
    MVMT_VAR_LINK_ID                VARCHAR(40),                                -- �ϐ���
    ASSIGN_SEQ                      INT,                                        -- �������
    NULL_DATA_HANDLING_FLG          VARCHAR(2),                                 -- NULL�A�g
    NOTE                            TEXT,                                       -- ���l
    DISUSE_FLAG                     VARCHAR(1),                                 -- �p�~�t���O
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- �ŏI�X�V����
    LAST_UPDATE_USER                VARCHAR(40),                                -- �ŏI�X�V��
    PRIMARY KEY(COLUMN_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_ANSL_VALUE_AUTOREG_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- ����p�V�[�P���X
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- ����p�ύX����
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- ����p�ύX���
    COLUMN_ID                       VARCHAR(40),                                -- ����
    MENU_ID                         VARCHAR(40),                                -- ���j���[��
    COLUMN_LIST_ID                  VARCHAR(40),                                -- ���ږ�
    COLUMN_ASSIGN_SEQ               INT,                                        -- �������
    COL_TYPE                        VARCHAR(2),                                 -- �o�^����
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement
    MVMT_VAR_LINK_ID                VARCHAR(40),                                -- �ϐ���
    ASSIGN_SEQ                      INT,                                        -- �������
    NULL_DATA_HANDLING_FLG          VARCHAR(2),                                 -- NULL�A�g
    NOTE                            TEXT,                                       -- ���l
    DISUSE_FLAG                     VARCHAR(1),                                 -- �p�~�t���O
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- �ŏI�X�V����
    LAST_UPDATE_USER                VARCHAR(40),                                -- �ŏI�X�V��
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 20206 Legacy ��ƑΏۃz�X�g
CREATE TABLE T_ANSL_TGT_HOST
(
    PHO_LINK_ID                     VARCHAR(40),                                -- ����
    EXECUTION_NO                    VARCHAR(40),                                -- ��Ǝ��s�ԍ�
    OPERATION_ID                    VARCHAR(40),                                -- �I�y���[�V����
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement
    SYSTEM_ID                       VARCHAR(40),                                -- �z�X�g
    NOTE                            TEXT,                                       -- ���l
    DISUSE_FLAG                     VARCHAR(1),                                 -- �p�~�t���O
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- �ŏI�X�V����
    LAST_UPDATE_USER                VARCHAR(40),                                -- �ŏI�X�V��
    PRIMARY KEY(PHO_LINK_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- 20207 Legacy ����l�Ǘ�
CREATE TABLE T_ANSL_VALUE
(
    ASSIGN_ID                       VARCHAR(40),                                -- ����
    EXECUTION_NO                    VARCHAR(40),                                -- ��Ǝ��s�ԍ�
    OPERATION_ID                    VARCHAR(40),                                -- �I�y���[�V����
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement
    SYSTEM_ID                       VARCHAR(40),                                -- �z�X�g
    MVMT_VAR_LINK_ID                VARCHAR(40),                                -- �ϐ���
    SENSITIVE_FLAG                  VARCHAR(2),                                 -- Sensitive�ݒ�
    VARS_ENTRY                      TEXT,                                       -- �l
    VARS_ENTRY_FILE                 VARCHAR(255),                               -- �t�@�C��
    ASSIGN_SEQ                      INT,                                        -- �������
    VARS_ENTRY_USE_TPFVARS          VARCHAR(1),                                 -- �e���v���[�g�ϐ��g�p�L��
    NOTE                            TEXT,                                       -- ���l
    DISUSE_FLAG                     VARCHAR(1),                                 -- �p�~�t���O
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- �ŏI�X�V����
    LAST_UPDATE_USER                VARCHAR(40),                                -- �ŏI�X�V��
    PRIMARY KEY(ASSIGN_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- 20209 Legacy ��ƊǗ�
CREATE TABLE T_ANSL_EXEC_STS_INST
(
    EXECUTION_NO                    VARCHAR(40),                                -- ��Ɣԍ�
    RUN_MODE                        VARCHAR(2),                                 -- ���s���
    STATUS_ID                       VARCHAR(2),                                 -- �X�e�[�^�X
    EXEC_MODE                       VARCHAR(2),                                 -- ���s�G���W��
    CONDUCTOR_NAME                  VARCHAR(255),                               -- �ďo��Conductor
    EXECUTION_USER                  VARCHAR(255),                               -- ���s���[�U
    TIME_REGISTER                   DATETIME(6),                                -- �o�^����
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement/ID
    I_MOVEMENT_NAME                 VARCHAR(255),                               -- Movement/����
    I_TIME_LIMIT                    INT,                                        -- Movement/�x���^�C�}�[
    I_ANS_HOST_DESIGNATE_TYPE_ID    VARCHAR(2),                                 -- Movement/Ansible���p���/�z�X�g�w��`��
    I_ANS_PARALLEL_EXE              INT,                                        -- Movement/Ansible���p���/������s��
    I_ANS_WINRM_ID                  VARCHAR(2),                                 -- Movement/Ansible���p���/WinRM�ڑ�
    I_ANS_PLAYBOOK_HED_DEF          TEXT,                                       -- Movement/Ansible���p���/�w�b�_�[�Z�N�V����
    I_EXECUTION_ENVIRONMENT_NAME    VARCHAR(255),                               -- Movement/Ansible Automation Controller���p���/���s��
    I_ANSIBLE_CONFIG_FILE           VARCHAR(255),                               -- Movement/ansible.cfg
    OPERATION_ID                    VARCHAR(40),                                -- �I�y���[�V����/No.
    I_OPERATION_NAME                VARCHAR(255),                               -- �I�y���[�V����/����
    FILE_INPUT                      VARCHAR(1024),                              -- ���̓f�[�^/�����f�[�^
    FILE_RESULT                     VARCHAR(1024),                              -- �o�̓f�[�^/���ʃf�[�^
    TIME_BOOK                       DATETIME(6),                                -- ��Ə�/�\�����
    TIME_START                      DATETIME(6),                                -- ��Ə�/�J�n����
    TIME_END                        DATETIME(6),                                -- ��Ə�/�I������
    COLLECT_STATUS                  VARCHAR(2),                                 -- ���W��/�X�e�[�^�X
    COLLECT_LOG                     VARCHAR(1024),                              -- ���W��/���W���O
    CONDUCTOR_INSTANCE_NO           VARCHAR(40),                                -- Conductor�C���X�^���X�ԍ�
    I_ANS_EXEC_OPTIONS              TEXT,                                       -- �I�v�V�����p�����[�^
    LOGFILELIST_JSON                TEXT,                                       -- �������ꂽ���s���O���
    MULTIPLELOG_MODE                INT,                                        -- ���s���O�����t���O
    EXECUTE_HOST_NAME               VARCHAR(40),                                -- ���s�z�X�g��
    NOTE                            TEXT,                                       -- ���l
    DISUSE_FLAG                     VARCHAR(1),                                 -- �p�~�t���O
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- �ŏI�X�V����
    LAST_UPDATE_USER                VARCHAR(40),                                -- �ŏI�X�V��
    PRIMARY KEY(EXECUTION_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_ANSL_EXEC_STS_INST_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- ����p�V�[�P���X
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- ����p�ύX����
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- ����p�ύX���
    EXECUTION_NO                    VARCHAR(40),                                -- ��Ɣԍ�
    RUN_MODE                        VARCHAR(2),                                 -- ���s���
    STATUS_ID                       VARCHAR(2),                                 -- �X�e�[�^�X
    EXEC_MODE                       VARCHAR(2),                                 -- ���s�G���W��
    CONDUCTOR_NAME                  VARCHAR(255),                               -- �ďo��Conductor
    EXECUTION_USER                  VARCHAR(255),                               -- ���s���[�U
    TIME_REGISTER                   DATETIME(6),                                -- �o�^����
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement/ID
    I_MOVEMENT_NAME                 VARCHAR(255),                               -- Movement/����
    I_TIME_LIMIT                    INT,                                        -- Movement/�x���^�C�}�[
    I_ANS_HOST_DESIGNATE_TYPE_ID    VARCHAR(2),                                 -- Movement/Ansible���p���/�z�X�g�w��`��
    I_ANS_PARALLEL_EXE              INT,                                        -- Movement/Ansible���p���/������s��
    I_ANS_WINRM_ID                  VARCHAR(2),                                 -- Movement/Ansible���p���/WinRM�ڑ�
    I_ANS_PLAYBOOK_HED_DEF          TEXT,                                       -- Movement/Ansible���p���/�w�b�_�[�Z�N�V����
    I_EXECUTION_ENVIRONMENT_NAME    VARCHAR(255),                               -- Movement/Ansible Automation Controller���p���/���s��
    I_ANSIBLE_CONFIG_FILE           VARCHAR(255),                               -- Movement/ansible.cfg
    OPERATION_ID                    VARCHAR(40),                                -- �I�y���[�V����/No.
    I_OPERATION_NAME                VARCHAR(255),                               -- �I�y���[�V����/����
    FILE_INPUT                      VARCHAR(1024),                              -- ���̓f�[�^/�����f�[�^
    FILE_RESULT                     VARCHAR(1024),                              -- �o�̓f�[�^/���ʃf�[�^
    TIME_BOOK                       DATETIME(6),                                -- ��Ə�/�\�����
    TIME_START                      DATETIME(6),                                -- ��Ə�/�J�n����
    TIME_END                        DATETIME(6),                                -- ��Ə�/�I������
    COLLECT_STATUS                  VARCHAR(2),                                 -- ���W��/�X�e�[�^�X
    COLLECT_LOG                     VARCHAR(1024),                              -- ���W��/���W���O
    CONDUCTOR_INSTANCE_NO           VARCHAR(40),                                -- Conductor�C���X�^���X�ԍ�
    I_ANS_EXEC_OPTIONS              TEXT,                                       -- �I�v�V�����p�����[�^
    LOGFILELIST_JSON                TEXT,                                       -- �������ꂽ���s���O���
    MULTIPLELOG_MODE                INT,                                        -- ���s���O�����t���O
    EXECUTE_HOST_NAME               VARCHAR(40),                                -- ���s�z�X�g��
    NOTE                            TEXT,                                       -- ���l
    DISUSE_FLAG                     VARCHAR(1),                                 -- �p�~�t���O
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- �ŏI�X�V����
    LAST_UPDATE_USER                VARCHAR(40),                                -- �ŏI�X�V��
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 20301 Pionner Movemnet�ꗗ
CREATE VIEW V_ANSP_MOVEMENT AS
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
CREATE VIEW V_ANSP_MOVEMENT_JNL AS
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



-- 20302 Pionner �Θb���
CREATE TABLE T_ANSP_DIALOG_TYPE
(
    DIALOG_TYPE_ID                  VARCHAR(40),                                -- ����
    DIALOG_TYPE_NAME                VARCHAR(255),                               -- �Θb��ʖ�
    NOTE                            TEXT,                                       -- ���l
    DISUSE_FLAG                     VARCHAR(1),                                 -- �p�~�t���O
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- �ŏI�X�V����
    LAST_UPDATE_USER                VARCHAR(40),                                -- �ŏI�X�V��
    PRIMARY KEY(DIALOG_TYPE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_ANSP_DIALOG_TYPE_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- ����p�V�[�P���X
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- ����p�ύX����
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- ����p�ύX���
    DIALOG_TYPE_ID                  VARCHAR(40),                                -- ����
    DIALOG_TYPE_NAME                VARCHAR(255),                               -- �Θb��ʖ�
    NOTE                            TEXT,                                       -- ���l
    DISUSE_FLAG                     VARCHAR(1),                                 -- �p�~�t���O
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- �ŏI�X�V����
    LAST_UPDATE_USER                VARCHAR(40),                                -- �ŏI�X�V��
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 20303 Pionner OS���
CREATE TABLE T_ANSP_OS_TYPE
(
    OS_TYPE_ID                      VARCHAR(40),                                -- ����
    OS_TYPE_NAME                    VARCHAR(255),                               -- OS��ʖ�
    HARDAWRE_TYPE_SV                VARCHAR(2),                                 -- SV
    HARDAWRE_TYPE_ST                VARCHAR(2),                                 -- ST
    HARDAWRE_TYPE_NW                VARCHAR(2),                                 -- NW
    NOTE                            TEXT,                                       -- ���l
    DISUSE_FLAG                     VARCHAR(1),                                 -- �p�~�t���O
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- �ŏI�X�V����
    LAST_UPDATE_USER                VARCHAR(40),                                -- �ŏI�X�V��
    PRIMARY KEY(OS_TYPE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_ANSP_OS_TYPE_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- ����p�V�[�P���X
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- ����p�ύX����
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- ����p�ύX���
    OS_TYPE_ID                      VARCHAR(40),                                -- ����
    OS_TYPE_NAME                    VARCHAR(255),                               -- OS��ʖ�
    HARDAWRE_TYPE_SV                VARCHAR(2),                                 -- SV
    HARDAWRE_TYPE_ST                VARCHAR(2),                                 -- ST
    HARDAWRE_TYPE_NW                VARCHAR(2),                                 -- NW
    NOTE                            TEXT,                                       -- ���l
    DISUSE_FLAG                     VARCHAR(1),                                 -- �p�~�t���O
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- �ŏI�X�V����
    LAST_UPDATE_USER                VARCHAR(40),                                -- �ŏI�X�V��
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 20304 Pionner �Θb�t�@�C���f�ޏW
CREATE TABLE T_ANSP_MATL_COLL
(
    DIALOG_MATTER_ID                VARCHAR(40),                                -- ����
    DIALOG_TYPE_ID                  VARCHAR(40),                                -- �Θb���
    OS_TYPE_ID                      VARCHAR(40),                                -- OS���
    DIALOG_MATTER_FILE              VARCHAR(255),                               -- �Θb�t�@�C���f��
    NOTE                            TEXT,                                       -- ���l
    DISUSE_FLAG                     VARCHAR(1),                                 -- �p�~�t���O
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- �ŏI�X�V����
    LAST_UPDATE_USER                VARCHAR(40),                                -- �ŏI�X�V��
    PRIMARY KEY(DIALOG_MATTER_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_ANSP_MATL_COLL_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- ����p�V�[�P���X
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- ����p�ύX����
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- ����p�ύX���
    DIALOG_MATTER_ID                VARCHAR(40),                                -- ����
    DIALOG_TYPE_ID                  VARCHAR(40),                                -- �Θb���
    OS_TYPE_ID                      VARCHAR(40),                                -- OS���
    DIALOG_MATTER_FILE              VARCHAR(255),                               -- �Θb�t�@�C���f��
    NOTE                            TEXT,                                       -- ���l
    DISUSE_FLAG                     VARCHAR(1),                                 -- �p�~�t���O
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- �ŏI�X�V����
    LAST_UPDATE_USER                VARCHAR(40),                                -- �ŏI�X�V��
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 20305 Pionner Movement-�ϐ��R�t
CREATE TABLE T_ANSP_MVMT_VAR_LINK
(
    MVMT_VAR_LINK_ID                VARCHAR(40),                                -- ����
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement
    VARS_NAME                       VARCHAR(255),                               -- �ϐ���
    NOTE                            TEXT,                                       -- ���l
    DISUSE_FLAG                     VARCHAR(1),                                 -- �p�~�t���O
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- �ŏI�X�V����
    LAST_UPDATE_USER                VARCHAR(40),                                -- �ŏI�X�V��
    PRIMARY KEY(MVMT_VAR_LINK_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- 20306 Pioneer Movement-�Θb��ʕR�t
CREATE TABLE T_ANSP_MVMT_MATL_LINK
(
    MVMT_MATL_LINK_ID               VARCHAR(40),                                -- ����
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement
    DIALOG_TYPE_ID                  VARCHAR(40),                                -- �Θb���
    INCLUDE_SEQ                     INT,                                        -- �C���N���[�h����
    NOTE                            TEXT,                                       -- ���l
    DISUSE_FLAG                     VARCHAR(1),                                 -- �p�~�t���O
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- �ŏI�X�V����
    LAST_UPDATE_USER                VARCHAR(40),                                -- �ŏI�X�V��
    PRIMARY KEY(MVMT_MATL_LINK_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_ANSP_MVMT_MATL_LINK_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- ����p�V�[�P���X
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- ����p�ύX����
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- ����p�ύX���
    MVMT_MATL_LINK_ID               VARCHAR(40),                                -- ����
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement
    DIALOG_TYPE_ID                  VARCHAR(40),                                -- �Θb���
    INCLUDE_SEQ                     INT,                                        -- �C���N���[�h����
    NOTE                            TEXT,                                       -- ���l
    DISUSE_FLAG                     VARCHAR(1),                                 -- �p�~�t���O
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- �ŏI�X�V����
    LAST_UPDATE_USER                VARCHAR(40),                                -- �ŏI�X�V��
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 20307 Pioneer ����l�����o�^
CREATE TABLE T_ANSP_VALUE_AUTOREG
(
    COLUMN_ID                       VARCHAR(40),                                -- ����
    MENU_ID                         VARCHAR(40),                                -- ���j���[��
    COLUMN_LIST_ID                  VARCHAR(40),                                -- ���ږ�
    COLUMN_ASSIGN_SEQ               INT,                                        -- �������
    COL_TYPE                        VARCHAR(2),                                 -- �o�^����
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement
    MVMT_VAR_LINK_ID                VARCHAR(40),                                -- �ϐ���
    ASSIGN_SEQ                      INT,                                        -- �������
    NULL_DATA_HANDLING_FLG          VARCHAR(2),                                 -- NULL�A�g
    NOTE                            TEXT,                                       -- ���l
    DISUSE_FLAG                     VARCHAR(1),                                 -- �p�~�t���O
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- �ŏI�X�V����
    LAST_UPDATE_USER                VARCHAR(40),                                -- �ŏI�X�V��
    PRIMARY KEY(COLUMN_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_ANSP_VALUE_AUTOREG_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- ����p�V�[�P���X
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- ����p�ύX����
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- ����p�ύX���
    COLUMN_ID                       VARCHAR(40),                                -- ����
    MENU_ID                         VARCHAR(40),                                -- ���j���[��
    COLUMN_LIST_ID                  VARCHAR(40),                                -- ���ږ�
    COLUMN_ASSIGN_SEQ               INT,                                        -- �������
    COL_TYPE                        VARCHAR(2),                                 -- �o�^����
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement
    MVMT_VAR_LINK_ID                VARCHAR(40),                                -- �ϐ���
    ASSIGN_SEQ                      INT,                                        -- �������
    NULL_DATA_HANDLING_FLG          VARCHAR(2),                                 -- NULL�A�g
    NOTE                            TEXT,                                       -- ���l
    DISUSE_FLAG                     VARCHAR(1),                                 -- �p�~�t���O
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- �ŏI�X�V����
    LAST_UPDATE_USER                VARCHAR(40),                                -- �ŏI�X�V��
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 20308 Pioneer ��ƑΏۃz�X�g
CREATE TABLE T_ANSP_TGT_HOST
(
    PHO_LINK_ID                     VARCHAR(40),                                -- ����
    EXECUTION_NO                    VARCHAR(40),                                -- ��Ǝ��s�ԍ�
    OPERATION_ID                    VARCHAR(40),                                -- �I�y���[�V����
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement
    SYSTEM_ID                       VARCHAR(40),                                -- �z�X�g
    NOTE                            TEXT,                                       -- ���l
    DISUSE_FLAG                     VARCHAR(1),                                 -- �p�~�t���O
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- �ŏI�X�V����
    LAST_UPDATE_USER                VARCHAR(40),                                -- �ŏI�X�V��
    PRIMARY KEY(PHO_LINK_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- 20309 Pioneer ����l�Ǘ�
CREATE TABLE T_ANSP_VALUE
(
    ASSIGN_ID                       VARCHAR(40),                                -- ����
    EXECUTION_NO                    VARCHAR(40),                                -- ��Ǝ��s�ԍ�
    OPERATION_ID                    VARCHAR(40),                                -- �I�y���[�V����
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement
    SYSTEM_ID                       VARCHAR(40),                                -- �z�X�g
    MVMT_VAR_LINK_ID                VARCHAR(40),                                -- �ϐ���
    SENSITIVE_FLAG                  VARCHAR(2),                                 -- Sensitive�ݒ�
    VARS_ENTRY                      TEXT,                                       -- �l
    VARS_ENTRY_FILE                 VARCHAR(255),                               -- �t�@�C��
    ASSIGN_SEQ                      INT,                                        -- �������
    VARS_ENTRY_USE_TPFVARS          VARCHAR(1),                                 -- �e���v���[�g�ϐ��g�p�L��
    NOTE                            TEXT,                                       -- ���l
    DISUSE_FLAG                     VARCHAR(1),                                 -- �p�~�t���O
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- �ŏI�X�V����
    LAST_UPDATE_USER                VARCHAR(40),                                -- �ŏI�X�V��
    PRIMARY KEY(ASSIGN_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- 20310 Pioneer ��ƊǗ�
CREATE TABLE T_ANSP_EXEC_STS_INST
(
    EXECUTION_NO                    VARCHAR(40),                                -- ��Ɣԍ�
    RUN_MODE                        VARCHAR(2),                                 -- ���s���
    STATUS_ID                       VARCHAR(2),                                 -- �X�e�[�^�X
    EXEC_MODE                       VARCHAR(2),                                 -- ���s�G���W��
    CONDUCTOR_NAME                  VARCHAR(255),                               -- �ďo��Conductor
    EXECUTION_USER                  VARCHAR(255),                               -- ���s���[�U
    TIME_REGISTER                   DATETIME(6),                                -- �o�^����
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement/ID
    I_MOVEMENT_NAME                 VARCHAR(255),                               -- Movement/����
    I_TIME_LIMIT                    INT,                                        -- Movement/�x���^�C�}�[
    I_ANS_HOST_DESIGNATE_TYPE_ID    VARCHAR(2),                                 -- Movement/Ansible���p���/�z�X�g�w��`��
    I_ANS_PARALLEL_EXE              INT,                                        -- Movement/Ansible���p���/������s��
    I_ANS_WINRM_ID                  VARCHAR(2),                                 -- Movement/Ansible���p���/WinRM�ڑ�
    I_ANS_PLAYBOOK_HED_DEF          TEXT,                                       -- Movement/Ansible���p���/�w�b�_�[�Z�N�V����
    I_EXECUTION_ENVIRONMENT_NAME    VARCHAR(255),                               -- Movement/Ansible Automation Controller���p���/���s��
    I_ANSIBLE_CONFIG_FILE           VARCHAR(255),                               -- Movement/ansible.cfg
    OPERATION_ID                    VARCHAR(40),                                -- �I�y���[�V����/No.
    I_OPERATION_NAME                VARCHAR(255),                               -- �I�y���[�V����/����
    FILE_INPUT                      VARCHAR(1024),                              -- ���̓f�[�^/�����f�[�^
    FILE_RESULT                     VARCHAR(1024),                              -- �o�̓f�[�^/���ʃf�[�^
    TIME_BOOK                       DATETIME(6),                                -- ��Ə�/�\�����
    TIME_START                      DATETIME(6),                                -- ��Ə�/�J�n����
    TIME_END                        DATETIME(6),                                -- ��Ə�/�I������
    COLLECT_STATUS                  VARCHAR(2),                                 -- ���W��/�X�e�[�^�X
    COLLECT_LOG                     VARCHAR(1024),                              -- ���W��/���W���O
    CONDUCTOR_INSTANCE_NO           VARCHAR(40),                                -- Conductor�C���X�^���X�ԍ�
    I_ANS_EXEC_OPTIONS              TEXT,                                       -- �I�v�V�����p�����[�^
    LOGFILELIST_JSON                TEXT,                                       -- �������ꂽ���s���O���
    MULTIPLELOG_MODE                INT,                                        -- ���s���O�����t���O
    EXECUTE_HOST_NAME               VARCHAR(40),                                -- ���s�z�X�g��
    NOTE                            TEXT,                                       -- ���l
    DISUSE_FLAG                     VARCHAR(1),                                 -- �p�~�t���O
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- �ŏI�X�V����
    LAST_UPDATE_USER                VARCHAR(40),                                -- �ŏI�X�V��
    PRIMARY KEY(EXECUTION_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_ANSP_EXEC_STS_INST_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- ����p�V�[�P���X
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- ����p�ύX����
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- ����p�ύX���
    EXECUTION_NO                    VARCHAR(40),                                -- ��Ɣԍ�
    RUN_MODE                        VARCHAR(2),                                 -- ���s���
    STATUS_ID                       VARCHAR(2),                                 -- �X�e�[�^�X
    EXEC_MODE                       VARCHAR(2),                                 -- ���s�G���W��
    CONDUCTOR_NAME                  VARCHAR(255),                               -- �ďo��Conductor
    EXECUTION_USER                  VARCHAR(255),                               -- ���s���[�U
    TIME_REGISTER                   DATETIME(6),                                -- �o�^����
    MOVEMENT_ID                     VARCHAR(40),                                -- Movement/ID
    I_MOVEMENT_NAME                 VARCHAR(255),                               -- Movement/����
    I_TIME_LIMIT                    INT,                                        -- Movement/�x���^�C�}�[
    I_ANS_HOST_DESIGNATE_TYPE_ID    VARCHAR(2),                                 -- Movement/Ansible���p���/�z�X�g�w��`��
    I_ANS_PARALLEL_EXE              INT,                                        -- Movement/Ansible���p���/������s��
    I_ANS_WINRM_ID                  VARCHAR(2),                                 -- Movement/Ansible���p���/WinRM�ڑ�
    I_ANS_PLAYBOOK_HED_DEF          TEXT,                                       -- Movement/Ansible���p���/�w�b�_�[�Z�N�V����
    I_EXECUTION_ENVIRONMENT_NAME    VARCHAR(255),                               -- Movement/Ansible Automation Controller���p���/���s��
    I_ANSIBLE_CONFIG_FILE           VARCHAR(255),                               -- Movement/ansible.cfg
    OPERATION_ID                    VARCHAR(40),                                -- �I�y���[�V����/No.
    I_OPERATION_NAME                VARCHAR(255),                               -- �I�y���[�V����/����
    FILE_INPUT                      VARCHAR(1024),                              -- ���̓f�[�^/�����f�[�^
    FILE_RESULT                     VARCHAR(1024),                              -- �o�̓f�[�^/���ʃf�[�^
    TIME_BOOK                       DATETIME(6),                                -- ��Ə�/�\�����
    TIME_START                      DATETIME(6),                                -- ��Ə�/�J�n����
    TIME_END                        DATETIME(6),                                -- ��Ə�/�I������
    COLLECT_STATUS                  VARCHAR(2),                                 -- ���W��/�X�e�[�^�X
    COLLECT_LOG                     VARCHAR(1024),                              -- ���W��/���W���O
    CONDUCTOR_INSTANCE_NO           VARCHAR(40),                                -- Conductor�C���X�^���X�ԍ�
    I_ANS_EXEC_OPTIONS              TEXT,                                       -- �I�v�V�����p�����[�^
    LOGFILELIST_JSON                TEXT,                                       -- �������ꂽ���s���O���
    MULTIPLELOG_MODE                INT,                                        -- ���s���O�����t���O
    EXECUTE_HOST_NAME               VARCHAR(40),                                -- ���s�z�X�g��
    NOTE                            TEXT,                                       -- ���l
    DISUSE_FLAG                     VARCHAR(1),                                 -- �p�~�t���O
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- �ŏI�X�V����
    LAST_UPDATE_USER                VARCHAR(40),                                -- �ŏI�X�V��
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;
CREATE TABLE T_ANSC_PARSE_TYPE
(
    PARSE_TYPE_ID                   VARCHAR(2),                                 -- ROW_ID
    PARSE_TYPE_NAME                 VARCHAR(255),                               -- �p�[�X�`����
    DISP_SEQ                        INT,                                        -- �\������
    NOTE                            TEXT,                                       -- ���l
    DISUSE_FLAG                     VARCHAR(1),                                 -- �p�~�t���O
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- �ŏI�X�V����
    LAST_UPDATE_USER                VARCHAR(40),                                -- �ŏI�X�V��
    PRIMARY KEY(PARSE_TYPE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;
-- ------------------------------------------------------------
-- �� TABLE CREATE END
-- ------------------------------------------------------------

-- ------------------------------------------------------------
-- ��TABLE UPDATE START
-- ------------------------------------------------------------
-- 20101 �@��ꗗ
ALTER TABLE T_ANSC_DEVICE            MODIFY OS_TYPE_ID VARCHAR(40);
ALTER TABLE T_ANSC_DEVICE_JNL        MODIFY OS_TYPE_ID VARCHAR(40);
-- 20412 Role ��ƊǗ�
ALTER TABLE T_ANSR_EXEC_STS_INST     ADD COLUMN  EXECUTE_HOST_NAME VARCHAR(40)  AFTER MULTIPLELOG_MODE;
ALTER TABLE T_ANSR_EXEC_STS_INST_JNL ADD COLUMN  EXECUTE_HOST_NAME VARCHAR(40)  AFTER MULTIPLELOG_MODE;
-- ------------------------------------------------------------
-- �� TABLE UPDATE END
-- ------------------------------------------------------------

-- ------------------------------------------------------------
-- �� VIEW UPDATE START
-- ------------------------------------------------------------
-- V002_��ƊǗ������r���[
DROP VIEW V_ANSC_EXEC_STS_INST;

CREATE VIEW V_ANSC_EXEC_STS_INST     AS
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
-- �� VIEW UPDATE END
-- ------------------------------------------------------------

-- ------------------------------------------------------------
-- �� VIEW CREATE START
-- ------------------------------------------------------------
-- V011_����l�����o�^_Movement��_�ϐ����r���[
CREATE VIEW V_ANSL_VAL_VARS_LINK AS
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
CREATE VIEW V_ANSL_VAL_VARS_LINK_JNL AS
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

-- V012_����l�����o�^_Movement��_�ϐ����r���[
CREATE VIEW V_ANSP_VAL_VARS_LINK AS
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

CREATE VIEW V_ANSP_VAL_VARS_LINK_JNL AS
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



-- V013_����l�����o�^�p���ڕ\���r���[
CREATE VIEW V_ANSP_COLUMN_LIST AS 
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

CREATE VIEW V_ANSP_COLUMN_LIST_JNL AS 
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

-- V014_���͗p���ڕ\���r���[
CREATE VIEW V_ANSC_INPUT_COLUMN_LIST AS 
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

CREATE VIEW V_ANSC_INPUT_COLUMN_LIST_JNL AS 
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
-- �� VIEW CREATE END 
-- ------------------------------------------------------------

-- ------------------------------------------------------------
-- �� INDEX CREATE END 
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
-- �� INDEX CREATE END 
-- ------------------------------------------------------------
