ALTER TABLE `T_COMN_ORGANIZATION_DB_INFO`
 ADD `MONGO_CONNECTION_STRING` VARCHAR(255) AFTER `DB_ADMIN_PASSWORD`,
 ADD `MONGO_ADMIN_USER` VARCHAR(255) AFTER `MONGO_CONNECTION_STRING`,
 ADD `MONGO_ADMIN_PASSWORD` VARCHAR(255) AFTER `MONGO_ADMIN_USER`;
ALTER TABLE `T_COMN_VERSION` ADD `ADDITIONAL_DRIVER` TEXT AFTER `INSTALLED_DRIVER_EN`;
