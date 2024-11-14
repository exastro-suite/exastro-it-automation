-- ------------------------------------------------------------
-- - ▼ 代入値自動登録
-- -    MENU_NAME_REST:メニュー名(Rest)追加
-- ------------------------------------------------------------
ALTER TABLE T_TERC_VALUE_AUTOREG     ADD  COLUMN MENU_NAME_REST VARCHAR(40) AFTER VALUE_AUTOREG_ID;
ALTER TABLE T_TERC_VALUE_AUTOREG_JNL ADD  COLUMN MENU_NAME_REST VARCHAR(40) AFTER VALUE_AUTOREG_ID;
