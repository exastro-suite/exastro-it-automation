-- メニューエクスポート・インポート管理
CREATE TABLE T_MENU_EXPORT_IMPORT
(
    MENU_GROUP_ID                   VARCHAR(40),                                -- メニューグループID
    PARENT_MENU_GROUP_ID            VARCHAR(40),                                -- 親メニューグループ
    MENU_GROUP_NAME_JA              VARCHAR(255),                               -- メニューグループ名(ja)
    MENU_GROUP_NAME_EN              VARCHAR(255),                               -- メニューグループ名(en)
    MENU_GROUP_ICON                 VARCHAR(255),                               -- パネル用画像
    MENU_CREATE_TARGET_FLAG         VARCHAR(2),                                 -- メニュー作成利用フラグ
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(MENU_GROUP_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- Excel一括エクスポート・インポート管理
CREATE TABLE T_BULK_EXCEL_EXPORT_IMPORT
(
    MENU_GROUP_ID                   VARCHAR(40),                                -- メニューグループID
    PARENT_MENU_GROUP_ID            VARCHAR(40),                                -- 親メニューグループ
    MENU_GROUP_NAME_JA              VARCHAR(255),                               -- メニューグループ名(ja)
    MENU_GROUP_NAME_EN              VARCHAR(255),                               -- メニューグループ名(en)
    MENU_GROUP_ICON                 VARCHAR(255),                               -- パネル用画像
    MENU_CREATE_TARGET_FLAG         VARCHAR(2),                                 -- メニュー作成利用フラグ
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)  ,                               -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(MENU_GROUP_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- 非表示メニュー
CREATE TABLE T_HIDE_MENU_LIST
(
    HIDE_ID                         VARCHAR(40),                                -- 識別シーケンス
    MENU_ID                         VARCHAR(40),                                -- メニューID
    PRIMARY KEY(HIDE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




