-- -----------------------------------------------------------------------------
-- - ▼実行環境管理
-- - 　下記項目削除
-- - 　　ベースイメージOS種別
-- - 　　ユーザー
-- - 　　パスワード
-- - 　　アタッチリポジトリ
-- -----------------------------------------------------------------------------
ALTER TABLE T_ANSC_EXECDEV     DROP COLUMN BASE_IMAGE_OS_TYPE;
ALTER TABLE T_ANSC_EXECDEV_JNL DROP COLUMN BASE_IMAGE_OS_TYPE;
ALTER TABLE T_ANSC_EXECDEV     DROP COLUMN USER_NAME;
ALTER TABLE T_ANSC_EXECDEV_JNL DROP COLUMN USER_NAME;
ALTER TABLE T_ANSC_EXECDEV     DROP COLUMN PASSWORD;
ALTER TABLE T_ANSC_EXECDEV_JNL DROP COLUMN PASSWORD;
ALTER TABLE T_ANSC_EXECDEV     DROP COLUMN ATTACH_REPOSITORY;
ALTER TABLE T_ANSC_EXECDEV_JNL DROP COLUMN ATTACH_REPOSITORY;

-- -----------------------------------------------------------------------------
-- - ▼ベースイメージOS種別マスタ削除
-- -----------------------------------------------------------------------------
DROP TABLE T_ANSC_BASE_IMAGE_OS_TYPE;