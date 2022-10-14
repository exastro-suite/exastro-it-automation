-- メニュー定義一覧
CREATE TABLE T_MENU_DEFINE
(
    MENU_CREATE_ID                  VARCHAR(40),                                -- 項番(UUID)
    MENU_NAME_JA                    VARCHAR(255),                               -- メニュー名_JA
    MENU_NAME_EN                    VARCHAR(255),                               -- メニュー名_EN
    MENU_NAME_REST                  VARCHAR(255),                               -- メニュー名_REST
    SHEET_TYPE                      VARCHAR(2) ,                                -- シートタイプ
    DISP_SEQ                        INT,                                        -- 表示順序
    VERTICAL                        VARCHAR(2) ,                                -- 縦メニュー利用
    MENU_GROUP_ID_INPUT             VARCHAR(40),                                -- 入力用メニューグループ
    MENU_GROUP_ID_SUBST             VARCHAR(40),                                -- 代入値自動登録用メニューグループ
    MENU_GROUP_ID_REF               VARCHAR(40),                                -- 参照用メニューグループ
    MENU_CREATE_DONE_STATUS         VARCHAR(2) ,                                -- メニュー作成状態
    DESCRIPTION_JA                  TEXT,                                       -- 説明_JA
    DESCRIPTION_EN                  TEXT,                                       -- 説明_EN
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(MENU_CREATE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_MENU_DEFINE_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    MENU_CREATE_ID                  VARCHAR(40),                                -- 項番(UUID)
    MENU_NAME_JA                    VARCHAR(255),                               -- メニュー名_JA
    MENU_NAME_EN                    VARCHAR(255),                               -- メニュー名_EN
    MENU_NAME_REST                  VARCHAR(255),                               -- メニュー名_REST
    SHEET_TYPE                      VARCHAR(2) ,                                -- シートタイプ
    DISP_SEQ                        INT,                                        -- 表示順序
    VERTICAL                        VARCHAR(2) ,                                -- 縦メニュー利用
    MENU_GROUP_ID_INPUT             VARCHAR(40),                                -- 入力用メニューグループ
    MENU_GROUP_ID_SUBST             VARCHAR(40),                                -- 代入値自動登録用メニューグループ
    MENU_GROUP_ID_REF               VARCHAR(40),                                -- 参照用メニューグループ
    MENU_CREATE_DONE_STATUS         VARCHAR(2) ,                                -- メニュー作成状態
    DESCRIPTION_JA                  TEXT,                                       -- 説明_JA
    DESCRIPTION_EN                  TEXT,                                       -- 説明_EN
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- カラムグループ作成情報
CREATE TABLE T_MENU_COLUMN_GROUP
(
    CREATE_COL_GROUP_ID             VARCHAR(40),                                -- 項番(UUID)
    PA_COL_GROUP_ID                 VARCHAR(40),                                -- 親カラムグループID
    COL_GROUP_NAME_JA               VARCHAR(255),                               -- カラムグループ名_JA
    COL_GROUP_NAME_EN               VARCHAR(255),                               -- カラムグループ名_EN
    FULL_COL_GROUP_NAME_JA          TEXT,                                       -- フルカラムグループ名_JA
    FULL_COL_GROUP_NAME_EN          TEXT,                                       -- フルカラムグループ名_EN
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(CREATE_COL_GROUP_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_MENU_COLUMN_GROUP_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    CREATE_COL_GROUP_ID             VARCHAR(40),                                -- 項番(UUID)
    PA_COL_GROUP_ID                 VARCHAR(40),                                -- 親カラムグループID
    COL_GROUP_NAME_JA               VARCHAR(255),                               -- カラムグループ名_JA
    COL_GROUP_NAME_EN               VARCHAR(255),                               -- カラムグループ名_EN
    FULL_COL_GROUP_NAME_JA          TEXT,                                       -- フルカラムグループ名_JA
    FULL_COL_GROUP_NAME_EN          TEXT,                                       -- フルカラムグループ名_EN
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- メニュー項目作成情報
CREATE TABLE T_MENU_COLUMN
(
    CREATE_COLUMN_ID                VARCHAR(40),                                -- 項番(UUID)
    MENU_CREATE_ID                  VARCHAR(40),                                -- メニュー定義一覧のID
    COLUMN_NAME_JA                  VARCHAR(255),                               -- 項目名(ja)
    COLUMN_NAME_EN                  VARCHAR(255),                               -- 項目名(en)
    COLUMN_NAME_REST                VARCHAR(255),                               -- 項目名(REST）
    DESCRIPTION_JA                  TEXT,                                       -- 説明(ja)
    DESCRIPTION_EN                  TEXT,                                       -- 説明(en)
    CREATE_COL_GROUP_ID             VARCHAR(40),                                -- カラムグループ
    COLUMN_CLASS                    VARCHAR(2),                                 -- カラムクラス
    DISP_SEQ                        INT,                                        -- 表示順序
    REQUIRED                        VARCHAR(2) ,                                -- 必須
    UNIQUED                         VARCHAR(2) ,                                -- 一意制約
    SINGLE_MAX_LENGTH               INT,                                        -- 文字列(単一行) 最大バイト数
    SINGLE_REGULAR_EXPRESSION       TEXT,                                       -- 文字列(単一行) 正規表現
    SINGLE_DEFAULT_VALUE            TEXT,                                       -- 文字列(単一行) 初期値
    MULTI_MAX_LENGTH                INT,                                        -- 文字列(複数行) 最大バイト数
    MULTI_REGULAR_EXPRESSION        TEXT,                                       -- 文字列(複数行) 正規表現
    MULTI_DEFAULT_VALUE             TEXT,                                       -- 文字列(複数行) 初期値
    NUM_MAX                         INT,                                        -- 整数 最大値
    NUM_MIN                         INT,                                        -- 整数 最小値
    NUM_DEFAULT_VALUE               INT,                                        -- 整数 初期値
    FLOAT_MAX                       DOUBLE,                                     -- 小数 最大値
    FLOAT_MIN                       DOUBLE,                                     -- 小数 最小値
    FLOAT_DIGIT                     INT,                                        -- 小数 桁数
    FLOAT_DEFAULT_VALUE             DOUBLE,                                     -- 小数 初期値
    DATETIME_DEFAULT_VALUE          DATETIME(6)  ,                              -- 日時 初期値
    DATE_DEFAULT_VALUE              DATETIME(6)  ,                              -- 日付 初期値
    OTHER_MENU_LINK_ID              VARCHAR(40),                                -- プルダウン選択 メニューグループ:メニュー:項目
    OTHER_MENU_LINK_DEFAULT_VALUE   TEXT,                                       -- プルダウン選択 初期値
    REFERENCE_ITEM                  TEXT,                                       -- プルダウン選択 参照項目
    PASSWORD_MAX_LENGTH             INT,                                        -- パスワード 最大バイト数
    FILE_UPLOAD_MAX_SIZE            BIGINT,                                     -- ファイルアップロード 最大バイト数
    LINK_MAX_LENGTH                 INT,                                        -- リンク 最大バイト数
    LINK_DEFAULT_VALUE              TEXT,                                       -- リンク 初期値
    PARAM_SHEET_LINK_ID             VARCHAR(40),                                -- パラメータシート参照 連携ID
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(CREATE_COLUMN_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_MENU_COLUMN_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    CREATE_COLUMN_ID                VARCHAR(40),                                -- 項番(UUID)
    MENU_CREATE_ID                  VARCHAR(40),                                -- メニュー定義一覧のID
    COLUMN_NAME_JA                  VARCHAR(255),                               -- 項目名(ja)
    COLUMN_NAME_EN                  VARCHAR(255),                               -- 項目名(en)
    COLUMN_NAME_REST                VARCHAR(255),                               -- 項目名(REST）
    DESCRIPTION_JA                  TEXT,                                       -- 説明(ja)
    DESCRIPTION_EN                  TEXT,                                       -- 説明(en)
    CREATE_COL_GROUP_ID             VARCHAR(40),                                -- カラムグループ
    COLUMN_CLASS                    VARCHAR(2),                                 -- カラムクラス
    DISP_SEQ                        INT,                                        -- 表示順序
    REQUIRED                        VARCHAR(2) ,                                -- 必須
    UNIQUED                         VARCHAR(2) ,                                -- 一意制約
    SINGLE_MAX_LENGTH               INT,                                        -- 文字列(単一行) 最大バイト数
    SINGLE_REGULAR_EXPRESSION       TEXT,                                       -- 文字列(単一行) 正規表現
    SINGLE_DEFAULT_VALUE            TEXT,                                       -- 文字列(単一行) 初期値
    MULTI_MAX_LENGTH                INT,                                        -- 文字列(複数行) 最大バイト数
    MULTI_REGULAR_EXPRESSION        TEXT,                                       -- 文字列(複数行) 正規表現
    MULTI_DEFAULT_VALUE             TEXT,                                       -- 文字列(複数行) 初期値
    NUM_MAX                         INT,                                        -- 整数 最大値
    NUM_MIN                         INT,                                        -- 整数 最小値
    NUM_DEFAULT_VALUE               INT,                                        -- 整数 初期値
    FLOAT_MAX                       DOUBLE,                                     -- 小数 最大値
    FLOAT_MIN                       DOUBLE,                                     -- 小数 最小値
    FLOAT_DIGIT                     INT,                                        -- 小数 桁数
    FLOAT_DEFAULT_VALUE             DOUBLE,                                     -- 小数 初期値
    DATETIME_DEFAULT_VALUE          DATETIME(6)  ,                              -- 日時 初期値
    DATE_DEFAULT_VALUE              DATETIME(6)  ,                              -- 日付 初期値
    OTHER_MENU_LINK_ID              VARCHAR(40),                                -- プルダウン選択 メニューグループ:メニュー:項目
    OTHER_MENU_LINK_DEFAULT_VALUE   TEXT,                                       -- プルダウン選択 初期値
    REFERENCE_ITEM                  TEXT,                                       -- プルダウン選択 参照項目
    PASSWORD_MAX_LENGTH             INT,                                        -- パスワード 最大バイト数
    FILE_UPLOAD_MAX_SIZE            BIGINT,                                     -- ファイルアップロード 最大バイト数
    LINK_MAX_LENGTH                 INT,                                        -- リンク 最大バイト数
    LINK_DEFAULT_VALUE              TEXT,                                       -- リンク 初期値
    PARAM_SHEET_LINK_ID             VARCHAR(40),                                -- パラメータシート参照 連携ID
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 一意制約(複数項目)作成情報
CREATE TABLE T_MENU_UNIQUE_CONSTRAINT
(
    UNIQUE_CONSTRAINT_ID            VARCHAR(40),                                -- 項番(UUID)
    MENU_CREATE_ID                  VARCHAR(40),                                -- メニュー定義一覧のID
    UNIQUE_CONSTRAINT_ITEM          TEXT,                                       -- 一意制約(複数項目)
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(UNIQUE_CONSTRAINT_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_MENU_UNIQUE_CONSTRAINT_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    UNIQUE_CONSTRAINT_ID            VARCHAR(40),                                -- 項番(UUID)
    MENU_CREATE_ID                  VARCHAR(40),                                -- メニュー定義一覧のID
    UNIQUE_CONSTRAINT_ITEM          TEXT,                                       -- 一意制約(複数項目)
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- メニューロール作成情報
CREATE TABLE T_MENU_ROLE
(
    MENU_ROLE_ID                    VARCHAR(40),                                -- 項番(UUID)
    MENU_CREATE_ID                  VARCHAR(40),                                -- メニュー定義一覧のID
    ROLE_ID                         VARCHAR(40),                                -- ロールID
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(MENU_ROLE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_MENU_ROLE_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    MENU_ROLE_ID                    VARCHAR(40),                                -- 項番(UUID)
    MENU_CREATE_ID                  VARCHAR(40),                                -- メニュー定義一覧のID
    ROLE_ID                         VARCHAR(40),                                -- ロールID
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- メニュー作成履歴
CREATE TABLE T_MENU_CREATE_HISTORY
(
    HISTORY_ID                      VARCHAR(40),                                -- 項番(UUID)
    MENU_CREATE_ID                  VARCHAR(40),                                -- メニュー定義一覧のID
    STATUS_ID                       VARCHAR(40),                                -- ステータス
    CREATE_TYPE                     VARCHAR(40),                                -- 作成タイプ
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(HISTORY_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_MENU_CREATE_HISTORY_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    HISTORY_ID                      VARCHAR(40),                                -- 項番(UUID)
    MENU_CREATE_ID                  VARCHAR(40),                                -- メニュー定義一覧のID
    STATUS_ID                       VARCHAR(40),                                -- ステータス
    CREATE_TYPE                     VARCHAR(40),                                -- 作成タイプ
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- メニュー定義-テーブル紐付管理
CREATE TABLE T_MENU_TABLE_LINK
(
    MENU_TABLE_LINK_ID              VARCHAR(40),                                -- 項番(UUID)
    MENU_ID                         VARCHAR(40),                                -- メニュー一覧のID
    MENU_NAME_REST                  VARCHAR(40),                                -- メニュー一覧のMENU_NAME_RESTと紐づくID
    TABLE_NAME                      VARCHAR(255),                               -- テーブル名
    KEY_COL_NAME                    VARCHAR(255),                               -- 主キー
    TABLE_NAME_JNL                  VARCHAR(255),                               -- 履歴テーブル名
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(MENU_TABLE_LINK_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_MENU_TABLE_LINK_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    MENU_TABLE_LINK_ID              VARCHAR(40),                                -- 項番(UUID)
    MENU_ID                         VARCHAR(40),                                -- メニュー一覧のID
    MENU_NAME_REST                  VARCHAR(40),                                -- メニュー一覧のMENU_NAME_RESTと紐づくID
    TABLE_NAME                      VARCHAR(255),                               -- テーブル名
    KEY_COL_NAME                    VARCHAR(255),                               -- 主キー
    TABLE_NAME_JNL                  VARCHAR(255),                               -- 履歴テーブル名
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 他メニュー連携
CREATE TABLE T_MENU_OTHER_LINK
(
    LINK_ID                         VARCHAR(40),                                -- 項番(UUID)
    MENU_ID                         VARCHAR(40),                                -- メニュー一覧のID
    COLUMN_DISP_NAME_JA             VARCHAR(255),                               -- 項目名(ja)
    COLUMN_DISP_NAME_EN             VARCHAR(255),                               -- 項目名(en)
    REF_TABLE_NAME                  VARCHAR(64),                                -- ID連携テーブル
    REF_PKEY_NAME                   VARCHAR(64),                                -- ID連携テーブルPK
    REF_COL_NAME                    VARCHAR(64),                                -- ID連携項目名
    REF_COL_NAME_REST               VARCHAR(255),                               -- ID連携項目名(REST)
    REF_SORT_CONDITIONS             TEXT,                                       -- ID連携ソート条件
    REF_MULTI_LANG                  VARCHAR(2),                                 -- ID連携多言語対応有無
    COLUMN_CLASS                    VARCHAR(2),                                 -- カラムクラス
    MENU_CREATE_FLAG                VARCHAR(2),                                 -- メニュー作成対象フラグ
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(LINK_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_MENU_OTHER_LINK_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    LINK_ID                         VARCHAR(40),                                -- 項番(UUID)
    MENU_ID                         VARCHAR(40),                                -- メニュー一覧のID
    COLUMN_DISP_NAME_JA             VARCHAR(255),                               -- 項目名(ja)
    COLUMN_DISP_NAME_EN             VARCHAR(255),                               -- 項目名(en)
    REF_TABLE_NAME                  VARCHAR(64),                                -- ID連携テーブル
    REF_PKEY_NAME                   VARCHAR(64),                                -- ID連携テーブルPK
    REF_COL_NAME                    VARCHAR(64),                                -- ID連携項目名
    REF_COL_NAME_REST               VARCHAR(255),                               -- ID連携項目名(REST)
    REF_SORT_CONDITIONS             TEXT,                                       -- ID連携ソート条件
    REF_MULTI_LANG                  VARCHAR(2),                                 -- ID連携多言語対応有無
    COLUMN_CLASS                    VARCHAR(2),                                 -- カラムクラス
    MENU_CREATE_FLAG                VARCHAR(2),                                 -- メニュー作成対象フラグ
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 他メニュー連携ビュー
CREATE OR REPLACE VIEW V_MENU_OTHER_LINK AS 
SELECT DISTINCT TAB_A.LINK_ID              ,
       TAB_C.MENU_GROUP_ID                 ,
       TAB_A.MENU_ID                       ,
       TAB_A.MENU_ID MENU_ID_CLONE         ,
       TAB_B.MENU_NAME_JA                  ,
       TAB_B.MENU_NAME_EN                  ,
       TAB_B.MENU_NAME_REST                ,
       TAB_A.COLUMN_DISP_NAME_JA           ,
       TAB_A.COLUMN_DISP_NAME_EN           ,
       CONCAT(TAB_C.MENU_GROUP_NAME_JA,':',TAB_B.MENU_NAME_JA,':',TAB_A.COLUMN_DISP_NAME_JA) LINK_PULLDOWN_JA,
       CONCAT(TAB_C.MENU_GROUP_NAME_EN,':',TAB_B.MENU_NAME_EN,':',TAB_A.COLUMN_DISP_NAME_EN) LINK_PULLDOWN_EN,
       TAB_A.REF_TABLE_NAME                ,
       TAB_A.REF_PKEY_NAME                 ,
       TAB_A.REF_COL_NAME                  ,
       TAB_A.REF_COL_NAME_REST             ,
       TAB_A.REF_SORT_CONDITIONS           ,
       TAB_A.REF_MULTI_LANG                ,
       TAB_A.COLUMN_CLASS                  ,
       TAB_A.MENU_CREATE_FLAG              ,
       TAB_A.NOTE                          ,
       TAB_A.DISUSE_FLAG                   ,
       TAB_A.LAST_UPDATE_TIMESTAMP         ,
       TAB_A.LAST_UPDATE_USER
FROM T_MENU_OTHER_LINK TAB_A
LEFT JOIN T_COMN_MENU TAB_B ON (TAB_A.MENU_ID = TAB_B.MENU_ID)
LEFT JOIN T_COMN_MENU_GROUP TAB_C ON (TAB_B.MENU_GROUP_ID = TAB_C.MENU_GROUP_ID)
WHERE TAB_B.DISUSE_FLAG='0' AND TAB_C.DISUSE_FLAG='0'
;
CREATE OR REPLACE VIEW V_MENU_OTHER_LINK_JNL AS 
SELECT DISTINCT TAB_A.JOURNAL_SEQ_NO       ,
       TAB_A.JOURNAL_REG_DATETIME          ,
       TAB_A.JOURNAL_ACTION_CLASS          ,
       TAB_A.LINK_ID                       ,
       TAB_C.MENU_GROUP_ID                 ,
       TAB_A.MENU_ID                       ,
       TAB_A.MENU_ID MENU_ID_CLONE         ,
       TAB_B.MENU_NAME_JA                  ,
       TAB_B.MENU_NAME_EN                  ,
       TAB_B.MENU_NAME_REST                ,
       TAB_A.COLUMN_DISP_NAME_JA           ,
       TAB_A.COLUMN_DISP_NAME_EN           ,
       CONCAT(TAB_C.MENU_GROUP_NAME_JA,':',TAB_B.MENU_NAME_JA,':',TAB_A.COLUMN_DISP_NAME_JA) LINK_PULLDOWN_JA,
       CONCAT(TAB_C.MENU_GROUP_NAME_EN,':',TAB_B.MENU_NAME_EN,':',TAB_A.COLUMN_DISP_NAME_EN) LINK_PULLDOWN_EN,
       TAB_A.REF_TABLE_NAME                ,
       TAB_A.REF_PKEY_NAME                 ,
       TAB_A.REF_COL_NAME                  ,
       TAB_A.REF_COL_NAME_REST             ,
       TAB_A.REF_SORT_CONDITIONS           ,
       TAB_A.REF_MULTI_LANG                ,
       TAB_A.COLUMN_CLASS                  ,
       TAB_A.MENU_CREATE_FLAG              ,
       TAB_A.NOTE                          ,
       TAB_A.DISUSE_FLAG                   ,
       TAB_A.LAST_UPDATE_TIMESTAMP         ,
       TAB_A.LAST_UPDATE_USER
FROM T_MENU_OTHER_LINK_JNL TAB_A
LEFT JOIN T_COMN_MENU_JNL TAB_B ON (TAB_A.MENU_ID = TAB_B.MENU_ID)
LEFT JOIN T_COMN_MENU_GROUP_JNL TAB_C ON (TAB_B.MENU_GROUP_ID = TAB_C.MENU_GROUP_ID)
WHERE TAB_B.DISUSE_FLAG='0' AND TAB_C.DISUSE_FLAG='0'
;



-- 参照項目情報
CREATE TABLE T_MENU_REFERENCE_ITEM
(
    REFERENCE_ID                    VARCHAR(40),                                -- 項番
    LINK_ID                         VARCHAR(40),                                -- 他メニュー連携のID
    DISP_SEQ                        INT,                                        -- 表示順序
    COLUMN_CLASS                    VARCHAR(2),                                 -- カラムクラス
    COLUMN_NAME_JA                  VARCHAR(255),                               -- 項目名(ja)
    COLUMN_NAME_EN                  VARCHAR(255),                               -- 項目名(en)
    COLUMN_NAME_REST                VARCHAR(255),                               -- 項目名(REST）
    COL_GROUP_ID                    VARCHAR(40),                                -- カラムグループ
    REF_COL_NAME                    VARCHAR(64),                                -- ID連携項目名
    REF_SORT_CONDITIONS             TEXT,                                       -- ID連携ソート条件
    REF_MULTI_LANG                  VARCHAR(2),                                 -- ID連携多言語対応有無
    SENSITIVE_FLAG                  VARCHAR(2) ,                                -- SENSITIVE設定
    DESCRIPTION_JA                  TEXT,                                       -- 説明(ja)
    DESCRIPTION_EN                  TEXT,                                       -- 説明(en)
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(REFERENCE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_MENU_REFERENCE_ITEM_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    REFERENCE_ID                    VARCHAR(40),                                -- 項番
    LINK_ID                         VARCHAR(40),                                -- 他メニュー連携のID
    DISP_SEQ                        INT,                                        -- 表示順序
    COLUMN_CLASS                    VARCHAR(2),                                 -- カラムクラス
    COLUMN_NAME_JA                  VARCHAR(255),                               -- 項目名(ja)
    COLUMN_NAME_EN                  VARCHAR(255),                               -- 項目名(en)
    COLUMN_NAME_REST                VARCHAR(255),                               -- 項目名(REST）
    COL_GROUP_ID                    VARCHAR(40),                                -- カラムグループ
    REF_COL_NAME                    VARCHAR(64),                                -- ID連携項目名
    REF_SORT_CONDITIONS             TEXT,                                       -- ID連携ソート条件
    REF_MULTI_LANG                  VARCHAR(2),                                 -- ID連携多言語対応有無
    SENSITIVE_FLAG                  VARCHAR(2) ,                                -- SENSITIVE設定
    DESCRIPTION_JA                  TEXT,                                       -- 説明(ja)
    DESCRIPTION_EN                  TEXT,                                       -- 説明(en)
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- 参照項目情報ビュー
CREATE OR REPLACE VIEW V_MENU_REFERENCE_ITEM AS 
SELECT DISTINCT TAB_A.REFERENCE_ID         ,
       TAB_A.LINK_ID                       ,
       TAB_B.MENU_GROUP_ID                 ,
       TAB_B.MENU_ID                       ,
       TAB_B.MENU_ID MENU_ID_CLONE         ,
       TAB_B.MENU_NAME_JA                  ,
       TAB_B.MENU_NAME_EN                  ,
       TAB_B.MENU_NAME_REST                ,
       TAB_A.DISP_SEQ                      ,
       TAB_A.COLUMN_CLASS                  ,
       TAB_A.COLUMN_NAME_JA                ,
       TAB_A.COLUMN_NAME_EN                ,
       TAB_A.COLUMN_NAME_REST              ,
       TAB_A.COL_GROUP_ID                  ,
       TAB_B.REF_TABLE_NAME                ,
       TAB_B.REF_PKEY_NAME                 ,
       TAB_A.REF_COL_NAME                  ,
       TAB_A.REF_SORT_CONDITIONS           ,
       TAB_A.REF_MULTI_LANG                ,
       TAB_A.SENSITIVE_FLAG                ,
       TAB_A.DESCRIPTION_JA                ,
       TAB_A.DESCRIPTION_EN                ,
       TAB_B.MENU_CREATE_FLAG              ,
       TAB_A.NOTE                          ,
       TAB_A.DISUSE_FLAG                   ,
       TAB_A.LAST_UPDATE_TIMESTAMP         ,
       TAB_A.LAST_UPDATE_USER
FROM T_MENU_REFERENCE_ITEM TAB_A
LEFT JOIN V_MENU_OTHER_LINK TAB_B ON (TAB_A.LINK_ID = TAB_B.LINK_ID)
WHERE TAB_B.DISUSE_FLAG='0'
;
CREATE OR REPLACE VIEW V_MENU_REFERENCE_ITEM_JNL AS 
SELECT DISTINCT TAB_A.JOURNAL_SEQ_NO       ,
       TAB_A.JOURNAL_REG_DATETIME          ,
       TAB_A.JOURNAL_ACTION_CLASS          ,
       TAB_A.REFERENCE_ID                  ,
       TAB_A.LINK_ID                       ,
       TAB_B.MENU_GROUP_ID                 ,
       TAB_B.MENU_ID                       ,
       TAB_B.MENU_ID MENU_ID_CLONE         ,
       TAB_B.MENU_NAME_JA                  ,
       TAB_B.MENU_NAME_EN                  ,
       TAB_B.MENU_NAME_REST                ,
       TAB_A.DISP_SEQ                      ,
       TAB_A.COLUMN_CLASS                  ,
       TAB_A.COLUMN_NAME_JA                ,
       TAB_A.COLUMN_NAME_EN                ,
       TAB_A.COLUMN_NAME_REST              ,
       TAB_A.COL_GROUP_ID                  ,
       TAB_B.REF_TABLE_NAME                ,
       TAB_B.REF_PKEY_NAME                 ,
       TAB_A.REF_COL_NAME                  ,
       TAB_A.REF_SORT_CONDITIONS           ,
       TAB_A.REF_MULTI_LANG                ,
       TAB_A.SENSITIVE_FLAG                ,
       TAB_A.DESCRIPTION_JA                ,
       TAB_A.DESCRIPTION_EN                ,
       TAB_B.MENU_CREATE_FLAG              ,
       TAB_A.NOTE                          ,
       TAB_A.DISUSE_FLAG                   ,
       TAB_A.LAST_UPDATE_TIMESTAMP         ,
       TAB_A.LAST_UPDATE_USER
FROM T_MENU_REFERENCE_ITEM_JNL TAB_A
LEFT JOIN V_MENU_OTHER_LINK_JNL TAB_B ON (TAB_A.LINK_ID = TAB_B.LINK_ID)
WHERE TAB_B.DISUSE_FLAG='0'
;



-- 選択1
CREATE TABLE T_MENU_SELECT_1
(
    SELECT_ID                       VARCHAR(40),                                -- 項番
    STATUS_VALUE                    VARCHAR(255),                               -- *-(ブランク)
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(SELECT_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- 選択2
CREATE TABLE T_MENU_SELECT_2
(
    SELECT_ID                       VARCHAR(40),                                -- 項番
    STATUS_VALUE_1                  VARCHAR(255),                               -- Yes-No
    STATUS_VALUE_2                  VARCHAR(255),                               -- True-False
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(SELECT_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- メニュー作成ステータスマスタ
CREATE TABLE T_MENU_CREATE_STATUS
(
    STATUS_ID                       VARCHAR(40),                                -- 項番
    STATUS_NAME_JA                  VARCHAR(255),                               -- ステータス名(ja)
    STATUS_NAME_EN                  VARCHAR(255),                               -- ステータス名(en)
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(STATUS_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- メニュー作成タイプマスタ
CREATE TABLE T_MENU_CREATE_TYPE
(
    TYPE_ID                         VARCHAR(40),                                -- 項番
    TYPE_NAME_JA                    VARCHAR(255),                               -- タイプ名(ja)
    TYPE_NAME_EN                    VARCHAR(255),                               -- タイプ名(en)
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(TYPE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- メニュー作成用途マスタ
CREATE TABLE T_MENU_PARAM_PURPOSE
(
    PURPOSE_ID                      VARCHAR(40),                                -- 項番
    PURPOSE_NAME_JA                 VARCHAR(255),                               -- 用途(ja)
    PURPOSE_NAME_EN                 VARCHAR(255),                               -- 用途(en)
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(PURPOSE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- メニュー作成状態マスタ
CREATE TABLE T_MENU_CREATE_DONE_STATUS
(
    DONE_STATUS_ID                  VARCHAR(40),                                -- 項番
    DONE_STATUS_NAME_JA             VARCHAR(255),                               -- 作成状態(ja)
    DONE_STATUS_NAME_EN             VARCHAR(255),                               -- 作成状態(en)
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1)   ,                              -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6)  ,                              -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(DONE_STATUS_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- メニュー作成用カラムクラス一覧ビュー
CREATE OR REPLACE VIEW V_MENU_COLUMN_CLASS AS
SELECT
    COLUMN_CLASS_ID,
    COLUMN_CLASS_NAME,
    COLUMN_CLASS_DISP_NAME_JA,
    COLUMN_CLASS_DISP_NAME_EN,
    MENU_CREATE_TARGET_FLAG,
    DISP_SEQ,
    NOTE,
    DISUSE_FLAG,
    LAST_UPDATE_TIMESTAMP,
    LAST_UPDATE_USER
FROM
    T_COMN_COLUMN_CLASS
WHERE
    DISUSE_FLAG = 0
AND
    MENU_CREATE_TARGET_FLAG = 1;



-- メニュー作成用シートタイプ一覧ビュー
CREATE OR REPLACE VIEW V_MENU_SHEET_TYPE AS
SELECT
    SHEET_TYPE_NAME_ID,
    SHEET_TYPE_NAME_JA,
    SHEET_TYPE_NAME_EN,
    MENU_CREATE_TARGET_FLAG,
    DISP_SEQ,
    NOTE,
    DISUSE_FLAG,
    LAST_UPDATE_TIMESTAMP,
    LAST_UPDATE_USER
FROM
    T_COMN_SHEET_TYPE
WHERE
    DISUSE_FLAG = 0
AND
    MENU_CREATE_TARGET_FLAG = 1;



-- メニュー作成用対象メニューグループ一覧ビュー
CREATE OR REPLACE VIEW V_MENU_TARGET_MENU_GROUP AS
SELECT
    TAB_A.MENU_GROUP_ID,
    TAB_A.PARENT_MENU_GROUP_ID,
    TAB_A.MENU_GROUP_NAME_JA,
    TAB_A.MENU_GROUP_NAME_EN,
    CASE WHEN TAB_B.MENU_GROUP_NAME_JA IS NULL THEN TAB_A.MENU_GROUP_NAME_JA ELSE CONCAT(TAB_B.MENU_GROUP_NAME_JA, '/', TAB_A.MENU_GROUP_NAME_JA) END AS FULL_MENU_GROUP_NAME_JA,
    CASE WHEN TAB_B.MENU_GROUP_NAME_EN IS NULL THEN TAB_A.MENU_GROUP_NAME_EN ELSE CONCAT(TAB_B.MENU_GROUP_NAME_EN, '/', TAB_A.MENU_GROUP_NAME_EN) END AS FULL_MENU_GROUP_NAME_EN,
    TAB_A.MENU_CREATE_TARGET_FLAG,
    TAB_A.DISP_SEQ,
    TAB_A.NOTE,
    TAB_A.DISUSE_FLAG,
    TAB_A.LAST_UPDATE_TIMESTAMP,
    TAB_A.LAST_UPDATE_USER
FROM
    T_COMN_MENU_GROUP TAB_A
LEFT JOIN T_COMN_MENU_GROUP TAB_B ON(TAB_A.PARENT_MENU_GROUP_ID = TAB_B.MENU_GROUP_ID)
WHERE
    (TAB_A.DISUSE_FLAG = 0)
AND
    (TAB_A.MENU_CREATE_TARGET_FLAG = 1);



-- オペレーション一覧ビュー
CREATE OR REPLACE VIEW V_COMN_OPERATION AS
SELECT
    OPERATION_ID,
    OPERATION_NAME,
    CONCAT(DATE_FORMAT( OPERATION_DATE, '%Y/%m/%d %H:%i' ),':',OPERATION_NAME) OPERATION_DATE_NAME,
    CASE
        WHEN LAST_EXECUTE_TIMESTAMP IS NULL THEN OPERATION_DATE
        ELSE LAST_EXECUTE_TIMESTAMP
    END BASE_TIMESTAMP,
    OPERATION_DATE,
    DATE_FORMAT( OPERATION_DATE, '%Y/%m/%d %H:%i' ) OPERATION_DATE_DISP,
    LAST_EXECUTE_TIMESTAMP,
    ENVIRONMENT,
    NOTE,
    DISUSE_FLAG,
    LAST_UPDATE_TIMESTAMP,
    LAST_UPDATE_USER
FROM
    T_COMN_OPERATION
;
CREATE OR REPLACE VIEW V_COMN_OPERATION_JNL AS
SELECT
    JOURNAL_SEQ_NO,
    JOURNAL_REG_DATETIME,
    JOURNAL_ACTION_CLASS,
    OPERATION_ID,
    OPERATION_NAME,
    CONCAT(DATE_FORMAT( OPERATION_DATE, '%Y/%m/%d %H:%i' ),':',OPERATION_NAME) OPERATION_DATE_NAME,
    CASE
        WHEN LAST_EXECUTE_TIMESTAMP IS NULL THEN OPERATION_DATE
        ELSE LAST_EXECUTE_TIMESTAMP
    END BASE_TIMESTAMP,
    OPERATION_DATE,
    DATE_FORMAT( OPERATION_DATE, '%Y/%m/%d %H:%i' ) OPERATION_DATE_DISP,
    LAST_EXECUTE_TIMESTAMP,
    ENVIRONMENT,
    NOTE,
    DISUSE_FLAG,
    LAST_UPDATE_TIMESTAMP,
    LAST_UPDATE_USER
FROM
    T_COMN_OPERATION_JNL
;



