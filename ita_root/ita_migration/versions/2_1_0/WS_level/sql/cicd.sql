-- 100101 リモートリポジトリ
CREATE TABLE T_CICD_REPOSITORY_LIST
(
    REPO_ROW_ID                     VARCHAR(40),                                -- 項番
    REPO_NAME                       VARCHAR(255),                               -- リモートリポジトリ名
    REMORT_REPO_URL                 VARCHAR(255),                               -- リモートリポジトリ(URL)
    BRANCH_NAME                     VARCHAR(255),                               -- ブランチ
    GIT_PROTOCOL_TYPE_ROW_ID        VARCHAR(2),                                 -- プロトコルタイプ
    GIT_REPO_TYPE_ROW_ID            VARCHAR(2),                                 -- リポジトリタイプ
    GIT_USER                        VARCHAR(255),                               -- Git ユーザー
    GIT_PASSWORD                    TEXT,                                       -- Git パスワード
    SSH_PASSWORD                    TEXT,                                       -- ssh パスワード
    SSH_PASSPHRASE                  TEXT,                                       -- ssh鍵ファイル パスフレーズ
    SSH_EXTRA_ARGS                  TEXT,                                       -- ssh接続パラメータ
    PROXY_ADDRESS                   VARCHAR(255),                               -- プロキシーアドレス
    PROXY_PORT                      INT,                                        -- プロキシーポート
    AUTO_SYNC_FLG                   VARCHAR(2),                                 -- 自動同期有無
    SYNC_INTERVAL                   INT,                                        -- 同期周期(単位:秒)
    SYNC_STATUS_ROW_ID              VARCHAR(2),                                 -- 同期状態
    SYNC_LAST_TIMESTAMP             DATETIME(6),                                -- 最終同期日時
    SYNC_ERROR_NOTE                 TEXT,                                       -- 同期エラー時の内容
    RETRAY_INTERVAL                 INT,                                        -- リトライ周期 単位:秒
    RETRAY_COUNT                    INT,                                        -- リトライ回数
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(REPO_ROW_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_CICD_REPOSITORY_LIST_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    REPO_ROW_ID                     VARCHAR(40),                                -- 項番
    REPO_NAME                       VARCHAR(255),                               -- リモートリポジトリ名
    REMORT_REPO_URL                 VARCHAR(255),                               -- リモートリポジトリ(URL)
    BRANCH_NAME                     VARCHAR(255),                               -- ブランチ
    GIT_PROTOCOL_TYPE_ROW_ID        VARCHAR(2),                                 -- プロトコルタイプ
    GIT_REPO_TYPE_ROW_ID            VARCHAR(2),                                 -- リポジトリタイプ
    GIT_USER                        VARCHAR(255),                               -- Git ユーザー
    GIT_PASSWORD                    TEXT,                                       -- Git パスワード
    SSH_PASSWORD                    TEXT,                                       -- ssh パスワード
    SSH_PASSPHRASE                  TEXT,                                       -- ssh鍵ファイル パスフレーズ
    SSH_EXTRA_ARGS                  TEXT,                                       -- ssh接続パラメータ
    PROXY_ADDRESS                   VARCHAR(255),                               -- プロキシーアドレス
    PROXY_PORT                      INT,                                        -- プロキシーポート
    AUTO_SYNC_FLG                   VARCHAR(2),                                 -- 自動同期有無
    SYNC_INTERVAL                   INT,                                        -- 同期周期(単位:秒)
    SYNC_STATUS_ROW_ID              VARCHAR(2),                                 -- 同期状態
    SYNC_LAST_TIMESTAMP             DATETIME(6),                                -- 最終同期日時
    SYNC_ERROR_NOTE                 TEXT,                                       -- 同期エラー時の内容
    RETRAY_INTERVAL                 INT,                                        -- リトライ周期 単位:秒
    RETRAY_COUNT                    INT,                                        -- リトライ回数
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 100102 リモートリポジトリ資材
CREATE TABLE T_CICD_MATL_LIST
(
    MATL_ROW_ID                     VARCHAR(40),                                -- 項番
    REPO_ROW_ID                     VARCHAR(40),                                -- リモートリポジトリ
    MATL_FILE_PATH                  VARCHAR(4096),                              -- 資材パス
    MATL_FILE_TYPE_ROW_ID           VARCHAR(2),                                 -- 資材タイプ
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(MATL_ROW_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- 100103 資材紐付
CREATE TABLE T_CICD_MATL_LINK
(
    MATL_LINK_ROW_ID                VARCHAR(40),                                -- 項番
    MATL_LINK_NAME                  VARCHAR(255),                               -- 素材名
    REPO_ROW_ID                     VARCHAR(40),                                -- リポジトリ
    MATL_ROW_ID                     VARCHAR(40),                                -- 資材
    MATL_TYPE_ROW_ID                VARCHAR(2),                                 -- 紐付先素材集タイプ
    TEMPLATE_FILE_VARS_LIST         TEXT,                                       -- テンプレート変数定義
    DIALOG_TYPE_ID                  VARCHAR(40),                                -- 対話種別
    OS_TYPE_ID                      VARCHAR(40),                                -- OS種別
    AUTO_SYNC_FLG                   VARCHAR(2),                                 -- 自動同期有無
    SYNC_STATUS_ROW_ID              VARCHAR(2),                                 -- 同期状態
    SYNC_ERROR_NOTE                 TEXT,                                       -- 同期エラー時の内容
    SYNC_LAST_TIME                  DATETIME(6),                                -- 最終同期時間
    DEL_OPE_ID                      VARCHAR(40),                                -- 構築時のオペレーションID
    DEL_MOVE_ID                     VARCHAR(40),                                -- 構築時のMovementID
    DEL_EXEC_TYPE                   VARCHAR(2),                                 -- 構築時のドライラン
    DEL_ERROR_NOTE                  TEXT,                                       -- 構築エラー時の内容
    DEL_EXEC_INS_NO                 VARCHAR(40),                                -- 構築時の作業インスタンス番号
    DEL_MENU_NO                     VARCHAR(128),                               -- 構築時の作業実行確認メニューID
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(MATL_LINK_ROW_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_CICD_MATL_LINK_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    MATL_LINK_ROW_ID                VARCHAR(40),                                -- 項番
    MATL_LINK_NAME                  VARCHAR(255),                               -- 素材名
    REPO_ROW_ID                     VARCHAR(40),                                -- リポジトリ
    MATL_ROW_ID                     VARCHAR(40),                                -- 資材
    MATL_TYPE_ROW_ID                VARCHAR(2),                                 -- 紐付先素材集タイプ
    TEMPLATE_FILE_VARS_LIST         TEXT,                                       -- テンプレート変数定義
    DIALOG_TYPE_ID                  VARCHAR(40),                                -- 対話種別
    OS_TYPE_ID                      VARCHAR(40),                                -- OS種別
    AUTO_SYNC_FLG                   VARCHAR(2),                                 -- 自動同期有無
    SYNC_STATUS_ROW_ID              VARCHAR(2),                                 -- 同期状態
    SYNC_ERROR_NOTE                 TEXT,                                       -- 同期エラー時の内容
    SYNC_LAST_TIME                  DATETIME(6),                                -- 最終同期時間
    DEL_OPE_ID                      VARCHAR(40),                                -- 構築時のオペレーションID
    DEL_MOVE_ID                     VARCHAR(40),                                -- 構築時のMovementID
    DEL_EXEC_TYPE                   VARCHAR(2),                                 -- 構築時のドライラン
    DEL_ERROR_NOTE                  TEXT,                                       -- 構築エラー時の内容
    DEL_EXEC_INS_NO                 VARCHAR(40),                                -- 構築時の作業インスタンス番号
    DEL_MENU_NO                     VARCHAR(128),                               -- 構築時の作業実行確認メニューID
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- M001 GITプロトコル種別
CREATE TABLE T_CICD_GIT_PROTOCOL_TYPE
(
    GIT_PROTOCOL_TYPE_ROW_ID        VARCHAR(2),                                 -- 項番
    GIT_PROTOCOL_TYPE_NAME_JA       VARCHAR(128),                               -- プロトコル名
    GIT_PROTOCOL_TYPE_NAME_EN       VARCHAR(128),                               -- プロトコル名
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(GIT_PROTOCOL_TYPE_ROW_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- M002 GITリポジトリ種別
CREATE TABLE T_CICD_GIT_REPOSITORY_TYPE
(
    GIT_REPO_TYPE_ROW_ID            VARCHAR(2),                                 -- 項番
    GIT_REPO_TYPE_NAME              VARCHAR(128),                               -- リポジトリタイプ
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(GIT_REPO_TYPE_ROW_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- M003 GITリポジトリ同期状態
CREATE TABLE T_CICD_REPO_SYNC_STATUS
(
    SYNC_STATUS_ROW_ID              VARCHAR(2),                                 -- 項番
    SYNC_STATUS_NAME_JA             VARCHAR(32),                                -- 状態名
    SYNC_STATUS_NAME_EN             VARCHAR(32),                                -- 状態名
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(SYNC_STATUS_ROW_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- M004 ITA素材タイプ
CREATE TABLE T_CICD_MATL_TYPE
(
    MATL_TYPE_ROW_ID                VARCHAR(2),                                 -- 項番
    MENU_ID                         VARCHAR(40),                                -- メニューID
    DRIVER_TYPE                     INT,                                        -- ドライバタイプ
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(MATL_TYPE_ROW_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- M005 資材ファイルタイプ
CREATE TABLE T_CICD_MATL_FILE_TYPE
(
    MATL_FILE_TYPE_ROW_ID           VARCHAR(2),                                 -- 項番
    MATL_FILE_TYPE_NAME_JA          VARCHAR(128),                               -- 資材タイプ名
    MATL_FILE_TYPE_NAME_EN          VARCHAR(128),                               -- 資材タイプ名
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(MATL_FILE_TYPE_ROW_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- V001 リモートリポジトリとリポジトリ資材の結合ビュー
CREATE VIEW V_CICD_REPOSITORY_MATL_PATH_LINK AS
SELECT
     CONCAT(TAB_1.REPO_NAME,':',TAB_2.MATL_FILE_PATH)     MATL_FILE_PATH_PULLDOWN,
     TAB_2.MATL_ROW_ID                                    MATL_FILE_PATH_PULLKEY,
     TAB_2.NOTE,
     TAB_2.DISUSE_FLAG,
     TAB_2.LAST_UPDATE_TIMESTAMP,
     TAB_2.LAST_UPDATE_USER
FROM
          T_CICD_REPOSITORY_LIST    TAB_1
LEFT JOIN T_CICD_MATL_LIST          TAB_2 ON (TAB_1.REPO_ROW_ID = TAB_2.REPO_ROW_ID)
WHERE
     TAB_1.DISUSE_FLAG = '0' AND
     TAB_2.DISUSE_FLAG = '0' ;



-- V002 素材タイプとメニュー名の結合ビュー
CREATE VIEW V_CICD_MATL_TYPE AS
SELECT 
    TAB_1.MATL_TYPE_ROW_ID, 
    CONCAT(TAB_3.MENU_GROUP_NAME_JA, '/', TAB_2.MENU_NAME_JA) MATL_TYPE_NAME_JA, 
    CONCAT(TAB_3.MENU_GROUP_NAME_EN, '/', TAB_2.MENU_NAME_EN) MATL_TYPE_NAME_EN, 
    TAB_1.DRIVER_TYPE, 
    TAB_1.DISP_SEQ, 
    TAB_1.NOTE, 
    TAB_1.DISUSE_FLAG, 
    TAB_1.LAST_UPDATE_TIMESTAMP, 
    TAB_1.LAST_UPDATE_USER 
FROM 
    T_CICD_MATL_TYPE TAB_1 
INNER JOIN 
    T_COMN_MENU TAB_2 
ON 
    TAB_1.MENU_ID=TAB_2.MENU_ID 
INNER JOIN 
    T_COMN_MENU_GROUP TAB_3 
ON 
    TAB_2.MENU_GROUP_ID=TAB_3.MENU_GROUP_ID 
WHERE 
    TAB_1.DISUSE_FLAG='0' 
AND TAB_2.DISUSE_FLAG='0' 
AND TAB_3.DISUSE_FLAG='0' ;



-- INDEX定義
CREATE INDEX IND_T_CICD_REPOSITORY_LIST_01 ON T_CICD_REPOSITORY_LIST(DISUSE_FLAG);
CREATE INDEX IND_T_CICD_REPOSITORY_LIST_02 ON T_CICD_REPOSITORY_LIST(DISUSE_FLAG, AUTO_SYNC_FLG, SYNC_STATUS_ROW_ID);
CREATE INDEX IND_T_CICD_MATL_LIST_01 ON T_CICD_MATL_LIST(DISUSE_FLAG);
CREATE INDEX IND_T_CICD_MATL_LIST_02 ON T_CICD_MATL_LIST(REPO_ROW_ID, MATL_FILE_TYPE_ROW_ID);
CREATE INDEX IND_T_CICD_MATL_LINK_01 ON T_CICD_MATL_LINK(DISUSE_FLAG);
CREATE INDEX IND_T_CICD_MATL_LINK_02 ON T_CICD_MATL_LINK(REPO_ROW_ID, AUTO_SYNC_FLG, DISUSE_FLAG);
CREATE INDEX IND_T_CICD_MATL_LINK_03 ON T_CICD_MATL_LINK(DIALOG_TYPE_ID, OS_TYPE_ID, DISUSE_FLAG);
CREATE INDEX IND_T_CICD_GIT_PROTOCOL_TYPE_01 ON T_CICD_GIT_PROTOCOL_TYPE(DISUSE_FLAG);
CREATE INDEX IND_T_CICD_GIT_REPOSITORY_TYPE_01 ON T_CICD_GIT_REPOSITORY_TYPE(DISUSE_FLAG);
CREATE INDEX IND_T_CICD_REPO_SYNC_STATUS_01 ON T_CICD_REPO_SYNC_STATUS(DISUSE_FLAG);
CREATE INDEX IND_T_CICD_MATL_TYPE_01 ON T_CICD_MATL_TYPE(DISUSE_FLAG);
CREATE INDEX IND_T_CICD_MATL_FILE_TYPE_01 ON T_CICD_MATL_FILE_TYPE(DISUSE_FLAG);



