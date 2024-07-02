-- ------------------------------------------------------------
-- - ▼ Movement一覧
-- -    ANS_VENV_PATH:　仮想環境パス追加
-- ------------------------------------------------------------
ALTER TABLE T_COMN_MOVEMENT     ADD  COLUMN ANS_VENV_PATH  TEXT AFTER ANS_EXEC_OPTIONS;
ALTER TABLE T_COMN_MOVEMENT_JNL ADD  COLUMN ANS_VENV_PATH  TEXT AFTER ANS_EXEC_OPTIONS;
