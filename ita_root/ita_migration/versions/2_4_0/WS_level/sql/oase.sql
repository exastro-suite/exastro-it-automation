-- ------------------------------------------------------------
-- ▼ TABLE CREATE START
-- ------------------------------------------------------------
-- 検索方法マスタ
CREATE TABLE IF NOT EXISTS T_OASE_SEARCH_CONDITION
(
    SEARCH_CONDITION_ID             VARCHAR(2),                                 -- 検索方法ID
    SEARCH_CONDITION_NAME_EN        VARCHAR(255),                               -- 検索方法名(en)
    SEARCH_CONDITION_NAME_JA        VARCHAR(255),                               -- 検索方法名(ja)
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(SEARCH_CONDITION_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

-- ------------------------------------------------------------
-- ▲ TABLE CREATE END
-- ------------------------------------------------------------

-- ------------------------------------------------------------
-- ▼ TABLE UPDATE START
-- ------------------------------------------------------------
-- 110101 イベント 追加
ALTER TABLE T_OASE_EVENT_COLLECTION_SETTINGS     ADD COLUMN EVENT_ID_KEY VARCHAR(255) AFTER RESPONSE_KEY;
ALTER TABLE T_OASE_EVENT_COLLECTION_SETTINGS_JNL ADD COLUMN EVENT_ID_KEY VARCHAR(255) AFTER RESPONSE_KEY;

-- 110107 フィルター 検索方法 追加
ALTER TABLE T_OASE_FILTER     ADD COLUMN SEARCH_CONDITION_ID VARCHAR(2) AFTER FILTER_CONDITION_JSON;
ALTER TABLE T_OASE_FILTER_JNL ADD COLUMN SEARCH_CONDITION_ID VARCHAR(2) AFTER FILTER_CONDITION_JSON;

-- 110108 アクション イベント連携 指定 利用パラメータシート 利用パラメータシート(rest) 追加
ALTER TABLE T_OASE_ACTION     ADD COLUMN EVENT_COLLABORATION VARCHAR(2) AFTER CONDUCTOR_CLASS_ID;
ALTER TABLE T_OASE_ACTION_JNL ADD COLUMN EVENT_COLLABORATION VARCHAR(2) AFTER CONDUCTOR_CLASS_ID;
ALTER TABLE T_OASE_ACTION     ADD COLUMN HOST_ID VARCHAR(40) AFTER EVENT_COLLABORATION;
ALTER TABLE T_OASE_ACTION_JNL ADD COLUMN HOST_ID VARCHAR(40) AFTER EVENT_COLLABORATION;
ALTER TABLE T_OASE_ACTION     ADD COLUMN PARAMETER_SHEET_ID VARCHAR(40) AFTER HOST_ID;
ALTER TABLE T_OASE_ACTION_JNL ADD COLUMN PARAMETER_SHEET_ID VARCHAR(40) AFTER HOST_ID;

-- 110109 ルール 追加
ALTER TABLE T_OASE_RULE ADD COLUMN ACTION_LABEL_INHERITANCE_FLAG VARCHAR(2) AFTER AFTER_NOTIFICATION_DESTINATION;
ALTER TABLE T_OASE_RULE_JNL ADD COLUMN ACTION_LABEL_INHERITANCE_FLAG VARCHAR(2) AFTER AFTER_NOTIFICATION_DESTINATION;
ALTER TABLE T_OASE_RULE ADD COLUMN EVENT_LABEL_INHERITANCE_FLAG VARCHAR(2) AFTER ACTION_LABEL_INHERITANCE_FLAG;
ALTER TABLE T_OASE_RULE_JNL ADD COLUMN EVENT_LABEL_INHERITANCE_FLAG VARCHAR(2) AFTER ACTION_LABEL_INHERITANCE_FLAG;

-- 110110 評価結果 結論ラベル　追加
ALTER TABLE T_OASE_ACTION_LOG ADD COLUMN EVENT_COLLABORATION VARCHAR(2) AFTER OPERATION_NAME;
ALTER TABLE T_OASE_ACTION_LOG_JNL ADD COLUMN EVENT_COLLABORATION VARCHAR(2) AFTER OPERATION_NAME;
ALTER TABLE T_OASE_ACTION_LOG ADD COLUMN HOST_ID VARCHAR(40) AFTER EVENT_COLLABORATION;
ALTER TABLE T_OASE_ACTION_LOG_JNL ADD COLUMN HOST_ID VARCHAR(40) AFTER EVENT_COLLABORATION;
ALTER TABLE T_OASE_ACTION_LOG ADD COLUMN HOST_NAME VARCHAR(255) AFTER HOST_ID;
ALTER TABLE T_OASE_ACTION_LOG_JNL ADD COLUMN HOST_NAME VARCHAR(255) AFTER HOST_ID;
ALTER TABLE T_OASE_ACTION_LOG ADD COLUMN PARAMETER_SHEET_ID VARCHAR(40) AFTER HOST_NAME;
ALTER TABLE T_OASE_ACTION_LOG_JNL ADD COLUMN PARAMETER_SHEET_ID VARCHAR(40) AFTER HOST_NAME;
ALTER TABLE T_OASE_ACTION_LOG ADD COLUMN PARAMETER_SHEET_NAME VARCHAR(255) AFTER PARAMETER_SHEET_ID;
ALTER TABLE T_OASE_ACTION_LOG_JNL ADD COLUMN PARAMETER_SHEET_NAME VARCHAR(255) AFTER PARAMETER_SHEET_ID;
ALTER TABLE T_OASE_ACTION_LOG ADD COLUMN PARAMETER_SHEET_NAME_REST VARCHAR(255) AFTER PARAMETER_SHEET_NAME;
ALTER TABLE T_OASE_ACTION_LOG_JNL ADD COLUMN PARAMETER_SHEET_NAME_REST VARCHAR(255) AFTER PARAMETER_SHEET_NAME;
ALTER TABLE T_OASE_ACTION_LOG ADD COLUMN ACTION_LABEL_INHERITANCE_FLAG VARCHAR(2) AFTER EVENT_ID_LIST;
ALTER TABLE T_OASE_ACTION_LOG_JNL ADD COLUMN ACTION_LABEL_INHERITANCE_FLAG VARCHAR(2) AFTER EVENT_ID_LIST;
ALTER TABLE T_OASE_ACTION_LOG ADD COLUMN EVENT_LABEL_INHERITANCE_FLAG VARCHAR(2) AFTER ACTION_LABEL_INHERITANCE_FLAG;
ALTER TABLE T_OASE_ACTION_LOG_JNL ADD COLUMN EVENT_LABEL_INHERITANCE_FLAG VARCHAR(2) AFTER ACTION_LABEL_INHERITANCE_FLAG;
ALTER TABLE T_OASE_ACTION_LOG ADD COLUMN ACTION_PARAMETERS TEXT AFTER EVENT_LABEL_INHERITANCE_FLAG;
ALTER TABLE T_OASE_ACTION_LOG_JNL ADD COLUMN ACTION_PARAMETERS TEXT AFTER EVENT_LABEL_INHERITANCE_FLAG;
ALTER TABLE T_OASE_ACTION_LOG ADD COLUMN CONCLUSION_EVENT_LABELS TEXT AFTER ACTION_PARAMETERS;
ALTER TABLE T_OASE_ACTION_LOG_JNL ADD COLUMN CONCLUSION_EVENT_LABELS TEXT AFTER ACTION_PARAMETERS;

-- ------------------------------------------------------------
-- ▲ TABLE UPDATE END
-- ------------------------------------------------------------

-- ------------------------------------------------------------
-- ▼ VIEW CREATE START
-- ------------------------------------------------------------
-- アクションビュー
CREATE OR REPLACE VIEW V_OASE_ACTION AS
SELECT
    ACTION_ID,
    ACTION_NAME,
    OPERATION_ID,
    CONDUCTOR_CLASS_ID,
    EVENT_COLLABORATION,
    HOST_ID,
    PARAMETER_SHEET_ID,
    PARAMETER_SHEET_ID PARAMETER_SHEET_NAME_REST,
    NOTE,
    DISUSE_FLAG,
    LAST_UPDATE_TIMESTAMP,
    LAST_UPDATE_USER
FROM
    T_OASE_ACTION
ORDER BY
    ACTION_ID ASC
;
CREATE OR REPLACE VIEW V_OASE_ACTION_JNL AS
SELECT
    JOURNAL_SEQ_NO,
    JOURNAL_REG_DATETIME,
    JOURNAL_ACTION_CLASS,
    ACTION_ID,
    ACTION_NAME,
    OPERATION_ID,
    CONDUCTOR_CLASS_ID,
    EVENT_COLLABORATION,
    HOST_ID,
    PARAMETER_SHEET_ID,
    PARAMETER_SHEET_ID PARAMETER_SHEET_NAME_REST,
    NOTE,
    DISUSE_FLAG,
    LAST_UPDATE_TIMESTAMP,
    LAST_UPDATE_USER
FROM
    T_OASE_ACTION_JNL
ORDER BY
    ACTION_ID ASC
;

-- 利用パラメータシートビュー
CREATE VIEW V_OASE_MENU_PULLDOWN AS
SELECT
    TAB_A.*
FROM
    T_COMN_MENU TAB_A
LEFT JOIN
    T_COMN_MENU_TABLE_LINK TAB_B  ON (TAB_A.MENU_ID = TAB_B.MENU_ID)
WHERE
    TAB_B.SHEET_TYPE = 1
AND
    TAB_A.DISUSE_FLAG = 0
AND
    TAB_B.VERTICAL = 0
AND
    TAB_B.HOSTGROUP = 0
AND
    TAB_B.SUBSTITUTION_VALUE_LINK_FLAG = 0
ORDER BY
    MENU_ID
;

-- アクション用ホストグループビュー
CREATE VIEW V_OASE_HGSP_UQ_HOST_LIST AS
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
;

-- 結論ラベルキー結合ビュー
CREATE OR REPLACE VIEW  V_OASE_CONCLUSION_LABEL_KEY_GROUP AS
SELECT
    LABEL_KEY_ID,
    LABEL_KEY_NAME,
    COLOR_CODE,
    NOTE,
    DISUSE_FLAG,
    LAST_UPDATE_TIMESTAMP,
    LAST_UPDATE_USER
FROM
    T_OASE_LABEL_KEY_INPUT
UNION
SELECT
    LABEL_KEY_ID,
    LABEL_KEY_NAME,
    COLOR_CODE,
    NOTE,
    DISUSE_FLAG,
    LAST_UPDATE_TIMESTAMP,
    LAST_UPDATE_USER
FROM
    T_OASE_LABEL_KEY_FIXED
WHERE
    LABEL_KEY_ID = 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx09'
ORDER BY
    LABEL_KEY_ID ASC
;
-- ------------------------------------------------------------
-- ▲ VIEW CREATE END
-- ------------------------------------------------------------
