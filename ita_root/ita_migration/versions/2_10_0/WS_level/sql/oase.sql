-- ------------------------------------------------------------
-- T_OASE_ACTION_LOG: ALTER - Add ACTION_RESULT Column
-- ------------------------------------------------------------
-- アクション結果カラムを追加（アクションの起動・実行時の詳細を保存）

-- T_OASE_ACTION_LOG にカラム追加
SET @exist := (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'T_OASE_ACTION_LOG'
    AND COLUMN_NAME = 'ACTION_RESULT'
);
SET @sql := IF(@exist = 0,
    'ALTER TABLE T_OASE_ACTION_LOG ADD COLUMN ACTION_RESULT LONGTEXT AFTER ACTION_NAME',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- T_OASE_ACTION_LOG_JNL にカラム追加
SET @exist := (
    SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'T_OASE_ACTION_LOG_JNL'
    AND COLUMN_NAME = 'ACTION_RESULT'
);
SET @sql := IF(@exist = 0,
    'ALTER TABLE T_OASE_ACTION_LOG_JNL ADD COLUMN ACTION_RESULT LONGTEXT AFTER ACTION_NAME',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ------------------------------------------------------------
-- VIEW: CREATE OR REPLACE (T_COMN_MENU へのカラム追加を反映)
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW V_OASE_MENU_PULLDOWN AS
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
