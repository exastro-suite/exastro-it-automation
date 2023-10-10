-- ------------------------------------------------------------
-- ▼VIWE UPDATE START
-- ------------------------------------------------------------

-- 比較対象メニュープルダウン
CREATE OR REPLACE VIEW V_COMPARE_MENU_PULLDOWN AS
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

-- ------------------------------------------------------------
-- ▼VIWE UPDATE END
-- ------------------------------------------------------------