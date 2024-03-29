-- ------------------------------------------------------------
-- ▼TABLE UPDATE START
-- ------------------------------------------------------------

-- 10103 メニュー管理: 独自メニュー用素材 追加
ALTER TABLE T_COMN_MENU     ADD COLUMN CUSTOM_MENU_ITEM VARCHAR(255)  AFTER INITIAL_FILTER_FLG;
ALTER TABLE T_COMN_MENU_JNL ADD COLUMN CUSTOM_MENU_ITEM VARCHAR(255)  AFTER INITIAL_FILTER_FLG;

-- ------------------------------------------------------------
-- ▼TABLE UPDATE END
-- ------------------------------------------------------------

-- ------------------------------------------------------------
-- ▼VIWE UPDATE START
-- ------------------------------------------------------------

-- メニューグルーブメニュー結合ビュー
CREATE OR REPLACE VIEW V_COMN_MENU_GROUP_MENU_PULLDOWN AS
SELECT
  TBL_1.*,
  CONCAT(TBL_2.MENU_GROUP_NAME_JA,':',TBL_1.MENU_NAME_JA) MENU_GROUP_NAME_PULLDOWN_JA,
  CONCAT(TBL_2.MENU_GROUP_NAME_EN,':',TBL_1.MENU_NAME_EN) MENU_GROUP_NAME_PULLDOWN_EN
FROM
  T_COMN_MENU TBL_1
  LEFT JOIN T_COMN_MENU_GROUP TBL_2 ON (TBL_1.MENU_GROUP_ID = TBL_2.MENU_GROUP_ID);
CREATE OR REPLACE VIEW V_COMN_MENU_GROUP_MENU_PULLDOWN_JNL AS
SELECT
  TBL_1.*,
  CONCAT(TBL_2.MENU_GROUP_NAME_JA,':',TBL_1.MENU_NAME_JA) MENU_GROUP_NAME_PULLDOWN_JA,
  CONCAT(TBL_2.MENU_GROUP_NAME_EN,':',TBL_1.MENU_NAME_EN) MENU_GROUP_NAME_PULLDOWN_EN
FROM
  T_COMN_MENU_JNL TBL_1
  LEFT JOIN T_COMN_MENU_GROUP_JNL TBL_2 ON (TBL_1.MENU_GROUP_ID = TBL_2.MENU_GROUP_ID);