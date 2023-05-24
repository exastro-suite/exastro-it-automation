-- ホストグループ一覧
CREATE TABLE T_HGSP_HOSTGROUP_LIST
(
    ROW_ID                          VARCHAR(40),                                -- ホストグループID
    HOSTGROUP_NAME                  VARCHAR(255),                               -- ホストグループ名
    PRIORITY                        INT,                                        -- 優先順位
    NOTE                            VARCHAR(4000),                              -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ROW_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_HGSP_HOSTGROUP_LIST_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    ROW_ID                          VARCHAR(40),                                -- ホストグループID
    HOSTGROUP_NAME                  VARCHAR(255),                               -- ホストグループ名
    PRIORITY                        INT,                                        -- 優先順位
    NOTE                            VARCHAR(4000),                              -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- ホストグループ親子紐付
CREATE TABLE T_HGSP_HOST_LINK_LIST
(
    ROW_ID                          VARCHAR(40),                                -- 項番
    PA_HOSTGROUP                    VARCHAR(40),                                -- 親ホストグループ
    CH_HOSTGROUP                    VARCHAR(40),                                -- 子ホストグループ
    NOTE                            VARCHAR(4000),                              -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ROW_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_HGSP_HOST_LINK_LIST_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    ROW_ID                          VARCHAR(40),                                -- 項番
    PA_HOSTGROUP                    VARCHAR(40),                                -- 親ホストグループ
    CH_HOSTGROUP                    VARCHAR(40),                                -- 子ホストグループ
    NOTE                            VARCHAR(4000),                              -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- ホスト紐付管理
CREATE TABLE T_HGSP_HOST_LINK
(
    ROW_ID                          VARCHAR(40),                                -- 項番
    HOSTGROUP_NAME                  VARCHAR(255),                               -- ホストグループ名
    OPERATION_ID                    VARCHAR(40),                                -- オペレーション
    HOSTNAME                        VARCHAR(40),                                -- ホスト名
    NOTE                            VARCHAR(4000),                              -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ROW_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_HGSP_HOST_LINK_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    ROW_ID                          VARCHAR(40),                                -- 項番
    HOSTGROUP_NAME                  VARCHAR(255),                               -- ホストグループ名
    OPERATION_ID                    VARCHAR(40),                                -- オペレーション
    HOSTNAME                        VARCHAR(40),                                -- ホスト名
    NOTE                            VARCHAR(4000),                              -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- ホストグループ分割対象
CREATE TABLE T_HGSP_SPLIT_TARGET
(
    ROW_ID                          VARCHAR(40),                                -- 項番
    INPUT_MENU_ID                   VARCHAR(40),                                -- 分割対象メニュー
    OUTPUT_MENU_ID                  VARCHAR(40),                                -- 登録対象メニュー
    DIVIDED_FLG                     VARCHAR(1)  ,                               -- 分割済みフラグ
    NOTE                            VARCHAR(4000),                              -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ROW_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- ホスト一覧プルダウン用
CREATE VIEW V_HGSP_UQ_HOST_LIST AS
SELECT
    SYSTEM_ID AS KY_KEY,
    CONCAT('[H]', HOST_NAME) AS KY_VALUE,
    0 AS KY_SOURCE,
    2147483647 AS PRIORITY,
    DISUSE_FLAG AS DISUSE_FLAG,
    LAST_UPDATE_TIMESTAMP AS LAST_UPDATE_TIMESTAMP,
    LAST_UPDATE_USER AS LAST_UPDATE_USER
FROM
    T_ANSC_DEVICE
WHERE
    DISUSE_FLAG = '0'
UNION
SELECT
    ROW_ID  AS KY_KEY,
    CONCAT('[HG]', HOSTGROUP_NAME) AS KY_VALUE,
    1 AS KY_SOURCE,
    PRIORITY AS PRIORITY,
    DISUSE_FLAG AS DISUSE_FLAG,
    LAST_UPDATE_TIMESTAMP AS LAST_UPDATE_TIMESTAMP,
    LAST_UPDATE_USER AS LAST_UPDATE_USER
FROM
    T_HGSP_HOSTGROUP_LIST
WHERE
    DISUSE_FLAG = '0'
;



-- 分割対象メニュープルダウン用
CREATE VIEW V_HGSP_SPLIT_TARGET_MENU AS 
SELECT
    TAB_A.*,
    TAB_C.MENU_GROUP_NAME_JA,
    TAB_C.MENU_GROUP_NAME_EN
FROM
    T_COMN_MENU TAB_A
LEFT JOIN T_COMN_MENU_TABLE_LINK TAB_B
    ON (TAB_A.MENU_ID = TAB_B.MENU_ID)
LEFT JOIN T_COMN_MENU_GROUP TAB_C 
    ON (TAB_A.MENU_GROUP_ID = TAB_C.MENU_GROUP_ID)
WHERE
    ( TAB_B.SHEET_TYPE = 1  OR TAB_B.SHEET_TYPE = 3 OR TAB_B.SHEET_TYPE = 4) 
AND TAB_A.DISUSE_FLAG = 0 
AND TAB_B.DISUSE_FLAG = 0 
AND TAB_B.SUBSTITUTION_VALUE_LINK_FLAG = 0
AND TAB_B.HOSTGROUP = 1
;



-- 登録対象メニュープルダウン用
CREATE VIEW V_HGSP_REGISTER_TARGET_MENU AS 
SELECT
    TAB_A.*,
    TAB_C.MENU_GROUP_NAME_JA,
    TAB_C.MENU_GROUP_NAME_EN
FROM
    T_COMN_MENU TAB_A
LEFT JOIN T_COMN_MENU_TABLE_LINK TAB_B
    ON (TAB_A.MENU_ID = TAB_B.MENU_ID)
LEFT JOIN T_COMN_MENU_GROUP TAB_C 
    ON (TAB_A.MENU_GROUP_ID = TAB_C.MENU_GROUP_ID)
WHERE
    ( TAB_B.SHEET_TYPE = 1  OR TAB_B.SHEET_TYPE = 3 OR TAB_B.SHEET_TYPE = 4) 
AND TAB_A.DISUSE_FLAG = 0 
AND TAB_B.DISUSE_FLAG = 0 
AND TAB_B.SUBSTITUTION_VALUE_LINK_FLAG = 1
AND TAB_B.HOSTGROUP = 1
;



-- インデックス



