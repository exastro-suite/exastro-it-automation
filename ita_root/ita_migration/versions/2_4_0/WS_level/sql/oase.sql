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
-- 110107 フィルター 検索方法 追加
ALTER TABLE T_OASE_FILTER     ADD COLUMN SEARCH_CONDITION_ID VARCHAR(2) AFTER FILTER_CONDITION_JSON;
ALTER TABLE T_OASE_FILTER_JNL ADD COLUMN SEARCH_CONDITION_ID VARCHAR(2) AFTER FILTER_CONDITION_JSON;

-- 110108 アクション イベント連携 指定 利用パラメータシート 利用パラメータシート(rest) 追加
ALTER TABLE T_OASE_ACTION     ADD COLUMN EVENT_COLLABORATION VARCHAR(2) AFTER CONDUCTOR_CLASS_ID;
ALTER TABLE T_OASE_ACTION_JNL ADD COLUMN EVENT_COLLABORATION VARCHAR(2) AFTER CONDUCTOR_CLASS_ID;
ALTER TABLE T_OASE_ACTION     ADD COLUMN HOST_NAME VARCHAR(40) AFTER EVENT_COLLABORATION;
ALTER TABLE T_OASE_ACTION_JNL ADD COLUMN HOST_NAME VARCHAR(40) AFTER EVENT_COLLABORATION;
ALTER TABLE T_OASE_ACTION     ADD COLUMN PARAMETER_SHEET_NAME VARCHAR(40) AFTER HOST_NAME;
ALTER TABLE T_OASE_ACTION_JNL ADD COLUMN PARAMETER_SHEET_NAME VARCHAR(40) AFTER HOST_NAME;
ALTER TABLE T_OASE_ACTION     ADD COLUMN PARAMETER_SHEET_NAME_REST VARCHAR(40) AFTER PARAMETER_SHEET_NAME;
ALTER TABLE T_OASE_ACTION_JNL ADD COLUMN PARAMETER_SHEET_NAME_REST VARCHAR(40) AFTER PARAMETER_SHEET_NAME;

-- 110110 評価結果 結論ラベル　追加
ALTER TABLE T_OASE_ACTION_LOG ADD COLUMN CONCLUSION_LABELS TEXT AFTER EVENT_ID_LIST;
ALTER TABLE T_OASE_ACTION_LOG_JNL ADD COLUMN CONCLUSION_LABELS TEXT AFTER EVENT_ID_LIST;

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
    HOST_NAME,
    PARAMETER_SHEET_NAME,
    PARAMETER_SHEET_NAME PARAMETER_SHEET_NAME_REST,
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
    HOST_NAME,
    PARAMETER_SHEET_NAME,
    PARAMETER_SHEET_NAME PARAMETER_SHEET_NAME_REST,
    NOTE,
    DISUSE_FLAG,
    LAST_UPDATE_TIMESTAMP,
    LAST_UPDATE_USER
FROM
    T_OASE_ACTION_JNL
ORDER BY
    ACTION_ID ASC
;

-- メニュー作成一覧ビュー
CREATE OR REPLACE VIEW V_MENU_DEFINE AS
SELECT
    MENU_CREATE_ID,
    MENU_NAME_JA,
    MENU_NAME_EN,
    MENU_NAME_REST,
    SHEET_TYPE,
    DISP_SEQ,
    VERTICAL,
    HOSTGROUP,
    MENU_GROUP_ID_INPUT,
    MENU_GROUP_ID_SUBST,
    MENU_GROUP_ID_REF,
    MENU_CREATE_DONE_STATUS,
    DESCRIPTION_JA,
    DESCRIPTION_EN,
    NOTE,
    DISUSE_FLAG,
    LAST_UPDATE_TIMESTAMP,
    LAST_UPDATE_USER
FROM
    T_MENU_DEFINE
WHERE
    MENU_CREATE_DONE_STATUS = 2
AND
    DISUSE_FLAG = 0
AND
    SHEET_TYPE = 1;

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