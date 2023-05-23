-- 比較設定
CREATE TABLE T_COMPARE_CONFG_LIST
(
    COMPARE_ID                      VARCHAR(40),                                -- 比較ID
    COMPARE_NAME                    VARCHAR(255),                               -- 比較名称
    TARGET_MENU_1                   VARCHAR(40),                                -- 対象メニュー1
    TARGET_MENU_2                   VARCHAR(40),                                -- 対象メニュー2
    DETAIL_FLAG                     VARCHAR(40),                                -- 詳細設定フラグ
    NOTE                            VARCHAR(4000),                              -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(COMPARE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_COMPARE_CONFG_LIST_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    COMPARE_ID                      VARCHAR(40),                                -- 比較ID
    COMPARE_NAME                    VARCHAR(255),                               -- 比較名称
    TARGET_MENU_1                   VARCHAR(40),                                -- 対象メニュー1
    TARGET_MENU_2                   VARCHAR(40),                                -- 対象メニュー2
    DETAIL_FLAG                     VARCHAR(40),                                -- 詳細設定フラグ
    NOTE                            VARCHAR(4000),                              -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 比較詳細設定
CREATE TABLE T_COMPARE_DETAIL_LIST
(
    COMPARE_DETAIL_ID               VARCHAR(40),                                -- 比較詳細ID
    COMPARE_ID                      VARCHAR(40),                                -- 比較名称
    COMPARE_COL_TITLE               VARCHAR(255),                               -- 比較項目名称
    TARGET_COLUMN_ID_1              VARCHAR(40),                                -- 対象項目1
    TARGET_COLUMN_ID_2              VARCHAR(40),                                -- 対象項目2
    DISP_SEQ                        int(11),                                    -- 表示順
    NOTE                            VARCHAR(4000),                              -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(COMPARE_DETAIL_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_COMPARE_DETAIL_LIST_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    COMPARE_DETAIL_ID               VARCHAR(40),                                -- 比較詳細ID
    COMPARE_ID                      VARCHAR(40),                                -- 比較名称
    COMPARE_COL_TITLE               VARCHAR(255),                               -- 比較項目名称
    TARGET_COLUMN_ID_1              VARCHAR(40),                                -- 対象項目1
    TARGET_COLUMN_ID_2              VARCHAR(40),                                -- 対象項目2
    DISP_SEQ                        int(11),                                    -- 表示順
    NOTE                            VARCHAR(4000),                              -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 比較対象メニュープルダウン
CREATE VIEW V_COMPARE_MENU_PULLDOWN AS 
SELECT
    `TBL_1`.*
FROM 
    `T_COMN_MENU` `TBL_1`
LEFT JOIN `T_COMN_MENU_TABLE_LINK` `TBL_2` ON (`TBL_1`.`MENU_ID` = `TBL_2`.`MENU_ID`)
WHERE (`TBL_2`.`SHEET_TYPE` = '1'  or `TBL_2`.`SHEET_TYPE` = '4') 
AND `TBL_1`.`MENU_NAME_REST` LIKE '%_subst'
AND `TBL_1`.`DISUSE_FLAG` <> '1'
ORDER BY `TBL_1`.`DISP_SEQ`
;



-- 比較対象カラムプルダウン1
CREATE VIEW V_COMPARE_MENU_COLUMN_PULLDOWN_1 AS 
SELECT
    `TBL_1`.*,
    CONCAT(
        `TBL_2`.`MENU_NAME_JA`,
        ':',
        `TBL_1`.`COLUMN_NAME_JA`
    ) AS `MENU_COLUMN_NAME_PULLDOWN_JA`,
    CONCAT(
        `TBL_2`.`MENU_NAME_EN`,
        ':',
        `TBL_1`.`COLUMN_NAME_EN`
    ) AS `MENU_COLUMN_NAME_PULLDOWN_EN`,
    CONCAT(
        `TBL_2`.`MENU_NAME_REST`,
        ':',
        `TBL_1`.`COLUMN_NAME_REST`
    ) AS `MENU_COLUMN_NAME_PULLDOWN_REST`
FROM
    `T_COMN_MENU_COLUMN_LINK` `TBL_1`
LEFT JOIN `T_COMN_MENU` `TBL_2` ON (`TBL_1`.`MENU_ID` = `TBL_2`.`MENU_ID`)
LEFT JOIN `T_COMN_MENU_TABLE_LINK` `TBL_3` ON (`TBL_1`.`MENU_ID` = `TBL_3`.`MENU_ID`)
LEFT JOIN `T_COMPARE_CONFG_LIST` `TBL_4` ON (`TBL_1`.`MENU_ID` = `TBL_4`.`TARGET_MENU_1`)
WHERE (`TBL_3`.`SHEET_TYPE` = "1" or  `TBL_3`.`SHEET_TYPE` = "4" ) 
AND `TBL_1`.`COL_NAME` = "DATA_JSON"
AND `TBL_4`.`DETAIL_FLAG` = "1"
AND `TBL_1`.`DISUSE_FLAG` <> "1" 
AND `TBL_2`.`DISUSE_FLAG` <> "1"
AND `TBL_4`.`DISUSE_FLAG` <> "1" 
;



-- 比較対象カラムプルダウン2
CREATE VIEW V_COMPARE_MENU_COLUMN_PULLDOWN_2 AS 
SELECT
    `TBL_1`.*,
    CONCAT(
        `TBL_2`.`MENU_NAME_JA`,
        ':',
        `TBL_1`.`COLUMN_NAME_JA`
    ) AS `MENU_COLUMN_NAME_PULLDOWN_JA`,
    CONCAT(
        `TBL_2`.`MENU_NAME_EN`,
        ':',
        `TBL_1`.`COLUMN_NAME_EN`
    ) AS `MENU_COLUMN_NAME_PULLDOWN_EN`,
    CONCAT(
        `TBL_2`.`MENU_NAME_REST`,
        ':',
        `TBL_1`.`COLUMN_NAME_REST`
    ) AS `MENU_COLUMN_NAME_PULLDOWN_REST`
FROM
    `T_COMN_MENU_COLUMN_LINK` `TBL_1`
LEFT JOIN `T_COMN_MENU` `TBL_2` ON (`TBL_1`.`MENU_ID` = `TBL_2`.`MENU_ID`)
LEFT JOIN `T_COMN_MENU_TABLE_LINK` `TBL_3` ON (`TBL_1`.`MENU_ID` = `TBL_3`.`MENU_ID`)
LEFT JOIN `T_COMPARE_CONFG_LIST` `TBL_4` ON (`TBL_1`.`MENU_ID` = `TBL_4`.`TARGET_MENU_2`)
WHERE (`TBL_3`.`SHEET_TYPE` = "1" or  `TBL_3`.`SHEET_TYPE` = "4" ) 
AND `TBL_1`.`COL_NAME` = "DATA_JSON"
AND `TBL_4`.`DETAIL_FLAG` = "1"
AND `TBL_1`.`DISUSE_FLAG` <> "1" 
AND `TBL_2`.`DISUSE_FLAG` <> "1"
AND `TBL_4`.`DISUSE_FLAG` <> "1" 
;



-- 比較設定詳細対象プルダウン
CREATE VIEW V_COMPARE_CONFIG_LIST_PULLDOWN AS
SELECT
    `TBL_1`.*,
    CONCAT(
    `TBL_1`.`COMPARE_NAME`,
    ':',
    `TBL_2`.`MENU_NAME_JA`,
    ':',
    `TBL_3`.`MENU_NAME_JA`
    ) AS `COMPARE_NAME_JA`,
    CONCAT(
    `TBL_1`.`COMPARE_NAME`,
    ':',
    `TBL_2`.`MENU_NAME_EN`,
    ':',
    `TBL_3`.`MENU_NAME_EN`
    ) AS `COMPARE_NAME_EN`
FROM
    `T_COMPARE_CONFG_LIST` `TBL_1`
LEFT JOIN `T_COMN_MENU` `TBL_2` ON (`TBL_2`.`MENU_ID` = `TBL_1`.`TARGET_MENU_1`)
LEFT JOIN `T_COMN_MENU` `TBL_3` ON (`TBL_3`.`MENU_ID` = `TBL_1`.`TARGET_MENU_2`)
WHERE
    `TBL_1`.`DETAIL_FLAG` <> 0
AND `TBL_1`.`DISUSE_FLAG` <> 1
AND `TBL_2`.`DISUSE_FLAG` <> 1
AND `TBL_3`.`DISUSE_FLAG` <> 1
;



-- インデックス



