-- IN ITA_DB

-- バージョン情報
CREATE TABLE T_COMN_VERSION
(
    SERVICE_ID                      VARCHAR(40),                                -- UUID
    VERSION                         VARCHAR(32),                                -- バージョン
    INSTALLED_DRIVER_JA             TEXT,                                       -- インストール済ドライバ(ja)
    INSTALLED_DRIVER_EN             TEXT,                                       -- インストール済ドライバ(en)
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(SERVICE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

INSERT INTO T_COMN_VERSION (SERVICE_ID, VERSION, INSTALLED_DRIVER_JA, INSTALLED_DRIVER_EN, NOTE, DISUSE_FLAG, LAST_UPDATE_TIMESTAMP, LAST_UPDATE_USER) VALUES (1,'2.1.0','["パラメータシート作成","ホストグループ","Ansible","Terraform-Cloud/EP","Terraform-CLI","CI/CD"]','["Parameter sheet Create","Hostgroup","Ansible","Terraform-Cloud/EP","Terraform-CLI","CI/CD"]',NULL,'0',CURRENT_TIMESTAMP,1);

SELECT * FROM T_COMN_VERSION;
