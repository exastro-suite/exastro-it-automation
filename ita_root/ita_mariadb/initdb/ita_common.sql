-- OrganizationDB管理
CREATE TABLE T_COMN_ORGANIZATION_DB_INFO
(
    PRIMARY_KEY                     VARCHAR(40),                                -- 主キー
    ORGANIZATION_ID                 VARCHAR(255),                               -- organizationのID
    DB_HOST                         VARCHAR(255),                               -- DBホスト
    DB_PORT                         INT,                                        -- DBポート
    DB_DATABASE                     VARCHAR(255),                               -- DB名
    DB_USER                         VARCHAR(255),                               -- DBユーザ
    DB_PASSWORD                     VARCHAR(255),                               -- DBパスワード
    DB_ADMIN_USER                   VARCHAR(255),                               -- DBadminユーザ
    DB_ADMIN_PASSWORD               VARCHAR(255),                               -- DBadminパスワード
    GITLAB_USER                     VARCHAR(255),                               -- GitLabユーザ
    GITLAB_TOKEN                    VARCHAR(255),                               -- GitLabトークン
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(PRIMARY_KEY)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- 初期設定データ
CREATE TABLE T_COMN_INITIAL_DATA
(
    PRIMARY_KEY                     VARCHAR(40),                                -- 主キー
    INITIAL_DATA_ANSIBLE_IF         LONGTEXT,                                   -- Ansible IF初期設定データ
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(PRIMARY_KEY)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- インデックス
CREATE INDEX IND_T_COMN_ORGANIZATION_DB_INFO_01 ON T_COMN_ORGANIZATION_DB_INFO (DISUSE_FLAG);



