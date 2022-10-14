-- メニューグループ管理
CREATE TABLE T_COMN_MENU_GROUP
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

CREATE TABLE T_COMN_MENU_GROUP_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
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
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- メニュー管理
CREATE TABLE T_COMN_MENU
(
    MENU_ID                         VARCHAR(40),                                -- メニューID
    MENU_GROUP_ID                   VARCHAR(40),                                -- メニューグループ
    MENU_NAME_JA                    VARCHAR(255),                               -- メニュー名(ja)
    MENU_NAME_EN                    VARCHAR(255),                               -- メニュー名(en)
    MENU_NAME_REST                  VARCHAR(255),                               -- メニュー名(REST)
    DISP_SEQ                        INT,                                        -- メニューグループ内表示順序
    AUTOFILTER_FLG                  VARCHAR(2),                                 -- オートフィルタチェック
    INITIAL_FILTER_FLG              VARCHAR(2),                                 -- 初回フィルタ
    WEB_PRINT_LIMIT                 INT,                                        -- Web表示最大行数
    WEB_PRINT_CONFIRM               INT,                                        -- Web表示前確認行数
    XLS_PRINT_LIMIT                 INT,                                        -- Excel出力最大行数
    SORT_KEY                        TEXT,                                       -- ソートキー
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(MENU_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_COMN_MENU_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    MENU_ID                         VARCHAR(40),                                -- メニューID
    MENU_GROUP_ID                   VARCHAR(40),                                -- メニューグループ
    MENU_NAME_JA                    VARCHAR(255),                               -- メニュー名(ja)
    MENU_NAME_EN                    VARCHAR(255),                               -- メニュー名(en)
    MENU_NAME_REST                  VARCHAR(255),                               -- メニュー名(REST)
    DISP_SEQ                        INT,                                        -- メニューグループ内表示順序
    AUTOFILTER_FLG                  VARCHAR(2),                                 -- オートフィルタチェック
    INITIAL_FILTER_FLG              VARCHAR(2),                                 -- 初回フィルタ
    WEB_PRINT_LIMIT                 INT,                                        -- Web表示最大行数
    WEB_PRINT_CONFIRM               INT,                                        -- Web表示前確認行数
    XLS_PRINT_LIMIT                 INT,                                        -- Excel出力最大行数
    SORT_KEY                        TEXT,                                       -- ソートキー
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- ロール-メニュー紐付
CREATE TABLE T_COMN_ROLE_MENU_LINK
(
    LINK_ID                         VARCHAR(40),                                -- UUID
    MENU_ID                         VARCHAR(40),                                -- メニュー
    ROLE_ID                         VARCHAR(64),                                -- ロール
    PRIVILEGE                       VARCHAR(2),                                 -- 紐付
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(LINK_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_COMN_ROLE_MENU_LINK_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    LINK_ID                         VARCHAR(40),                                -- UUID
    MENU_ID                         VARCHAR(40),                                -- メニュー
    ROLE_ID                         VARCHAR(64),                                -- ロール
    PRIVILEGE                       VARCHAR(2),                                 -- 紐付
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- メニュー-テーブル紐付管理
CREATE TABLE T_COMN_MENU_TABLE_LINK
(
    TABLE_DEFINITION_ID             VARCHAR(40),                                -- UUID
    MENU_ID                         VARCHAR(40),                                -- メニュー
    TABLE_NAME                      VARCHAR(255),                               -- テーブル名
    VIEW_NAME                       VARCHAR(255),                               -- ビュー名
    PK_COLUMN_NAME_REST             VARCHAR(255),                               -- PK項目名(REST）
    MENU_INFO_JA                    TEXT,                                       -- 説明(ja)
    MENU_INFO_EN                    TEXT,                                       -- 説明(en)
    SHEET_TYPE                      VARCHAR(2),                                 -- シートタイプ
    HISTORY_TABLE_FLAG              VARCHAR(2),                                 -- 履歴テーブル有無
    INHERIT                         VARCHAR(2),                                 -- 継承フラグ
    VERTICAL                        VARCHAR(2),                                 -- 縦型フラグ
    ROW_INSERT_FLAG                 VARCHAR(2),                                 -- 登録許可フラグ
    ROW_UPDATE_FLAG                 VARCHAR(2),                                 -- 更新許可フラグ
    ROW_DISUSE_FLAG                 VARCHAR(2),                                 -- 廃止許可フラグ
    ROW_REUSE_FLAG                  VARCHAR(2),                                 -- 復活許可フラグ
    SUBSTITUTION_VALUE_LINK_FLAG    VARCHAR(2),                                 -- 代入値自動登録対象フラグ
    LOCK_TABLE                      TEXT,                                       -- ロック対象テーブル
    UNIQUE_CONSTRAINT               TEXT,                                       -- 組み合わせ一意制約
    BEFORE_VALIDATE_REGISTER        TEXT,                                       -- 個別バリデーション前
    AFTER_VALIDATE_REGISTER         TEXT,                                       -- 個別バリデーション後
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(TABLE_DEFINITION_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_COMN_MENU_TABLE_LINK_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    TABLE_DEFINITION_ID             VARCHAR(40),                                -- UUID
    MENU_ID                         VARCHAR(40),                                -- メニュー
    TABLE_NAME                      VARCHAR(255),                               -- テーブル名
    VIEW_NAME                       VARCHAR(255),                               -- ビュー名
    PK_COLUMN_NAME_REST             VARCHAR(255),                               -- PK項目名(REST）
    MENU_INFO_JA                    TEXT,                                       -- 説明(ja)
    MENU_INFO_EN                    TEXT,                                       -- 説明(en)
    SHEET_TYPE                      VARCHAR(2),                                 -- シートタイプ
    HISTORY_TABLE_FLAG              VARCHAR(2),                                 -- 履歴テーブル有無
    INHERIT                         VARCHAR(2),                                 -- 継承フラグ
    VERTICAL                        VARCHAR(2),                                 -- 縦型フラグ
    ROW_INSERT_FLAG                 VARCHAR(2),                                 -- 登録許可フラグ
    ROW_UPDATE_FLAG                 VARCHAR(2),                                 -- 更新許可フラグ
    ROW_DISUSE_FLAG                 VARCHAR(2),                                 -- 廃止許可フラグ
    ROW_REUSE_FLAG                  VARCHAR(2),                                 -- 復活許可フラグ
    SUBSTITUTION_VALUE_LINK_FLAG    VARCHAR(2),                                 -- 代入値自動登録対象フラグ
    LOCK_TABLE                      TEXT,                                       -- ロック対象テーブル
    UNIQUE_CONSTRAINT               TEXT,                                       -- 組み合わせ一意制約
    BEFORE_VALIDATE_REGISTER        TEXT,                                       -- 個別バリデーション前
    AFTER_VALIDATE_REGISTER         TEXT,                                       -- 個別バリデーション後
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- メニュー-カラム紐付管理
CREATE TABLE T_COMN_MENU_COLUMN_LINK
(
    COLUMN_DEFINITION_ID            VARCHAR(40),                                -- UUID
    MENU_ID                         VARCHAR(40),                                -- メニュー
    COLUMN_NAME_JA                  VARCHAR(255),                               -- 項目名(ja)
    COLUMN_NAME_EN                  VARCHAR(255),                               -- 項目名(en)
    COLUMN_NAME_REST                VARCHAR(255),                               -- 項目名(REST）
    COL_GROUP_ID                    VARCHAR(40),                                -- カラムグループ
    COLUMN_CLASS                    VARCHAR(2),                                 -- カラムクラス
    COLUMN_DISP_SEQ                 INT,                                        -- 表示順
    REF_TABLE_NAME                  VARCHAR(64),                                -- ID連携テーブル
    REF_PKEY_NAME                   VARCHAR(64),                                -- ID連携テーブルPK
    REF_COL_NAME                    VARCHAR(64),                                -- ID連携項目名
    REF_SORT_CONDITIONS             TEXT,                                       -- ID連携ソート条件
    REF_MULTI_LANG                  VARCHAR(2),                                 -- ID連携多言語対応有無
    REFERENCE_ITEM                  TEXT,                                       -- 参照項目
    SENSITIVE_COL_NAME              VARCHAR(64),                                -- Sensitive設定用カラム名
    FILE_UPLOAD_PLACE               VARCHAR(255),                               -- ファイルアップロード配置場所
    BUTTON_ACTION                   TEXT,                                       -- ボタンアクション
    COL_NAME                        VARCHAR(64),                                -- カラム名
    SAVE_TYPE                       VARCHAR(64),                                -- DB上の保存形式
    AUTO_INPUT                      VARCHAR(2),                                 -- 自動入力フラグ
    INPUT_ITEM                      VARCHAR(2),                                 -- 入力対象フラグ
    VIEW_ITEM                       VARCHAR(2),                                 -- 出力対象フラグ
    UNIQUE_ITEM                     VARCHAR(2),                                 -- 必須入力フラグ
    REQUIRED_ITEM                   VARCHAR(2),                                 -- 一意制約フラグ
    AUTOREG_HIDE_ITEM               VARCHAR(2),                                 -- 選択対象外フラグ
    AUTOREG_ONLY_ITEM               VARCHAR(2),                                 -- 代入値自動登録選択項目フラグ
    INITIAL_VALUE                   TEXT,                                       -- 初期値
    VALIDATE_OPTION                 TEXT,                                       -- バリデーション値
    VALIDATE_REG_EXP                TEXT,                                       -- 正規表現バリデーション
    BEFORE_VALIDATE_REGISTER        TEXT,                                       -- 個別バリデーション前
    AFTER_VALIDATE_REGISTER         TEXT,                                       -- 個別バリデーション後
    DESCRIPTION_JA                  TEXT,                                       -- 説明(ja)
    DESCRIPTION_EN                  TEXT,                                       -- 説明(en)
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(COLUMN_DEFINITION_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_COMN_MENU_COLUMN_LINK_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    COLUMN_DEFINITION_ID            VARCHAR(40),                                -- UUID
    MENU_ID                         VARCHAR(40),                                -- メニュー
    COLUMN_NAME_JA                  VARCHAR(255),                               -- 項目名(ja)
    COLUMN_NAME_EN                  VARCHAR(255),                               -- 項目名(en)
    COLUMN_NAME_REST                VARCHAR(255),                               -- 項目名(REST）
    COL_GROUP_ID                    VARCHAR(40),                                -- カラムグループ
    COLUMN_CLASS                    VARCHAR(2),                                 -- カラムクラス
    COLUMN_DISP_SEQ                 INT,                                        -- 表示順
    REF_TABLE_NAME                  VARCHAR(64),                                -- ID連携テーブル
    REF_PKEY_NAME                   VARCHAR(64),                                -- ID連携テーブルPK
    REF_COL_NAME                    VARCHAR(64),                                -- ID連携項目名
    REF_SORT_CONDITIONS             TEXT,                                       -- ID連携ソート条件
    REF_MULTI_LANG                  VARCHAR(2),                                 -- ID連携多言語対応有無
    REFERENCE_ITEM                  TEXT,                                       -- 参照項目
    SENSITIVE_COL_NAME              VARCHAR(64),                                -- Sensitive設定用カラム名
    FILE_UPLOAD_PLACE               VARCHAR(255),                               -- ファイルアップロード配置場所
    BUTTON_ACTION                   TEXT,                                       -- ボタンアクション
    COL_NAME                        VARCHAR(64),                                -- カラム名
    SAVE_TYPE                       VARCHAR(64),                                -- DB上の保存形式
    AUTO_INPUT                      VARCHAR(2),                                 -- 自動入力フラグ
    INPUT_ITEM                      VARCHAR(2),                                 -- 入力対象フラグ
    VIEW_ITEM                       VARCHAR(2),                                 -- 出力対象フラグ
    UNIQUE_ITEM                     VARCHAR(2),                                 -- 必須入力フラグ
    REQUIRED_ITEM                   VARCHAR(2),                                 -- 一意制約フラグ
    AUTOREG_HIDE_ITEM               VARCHAR(2),                                 -- 選択対象外フラグ
    AUTOREG_ONLY_ITEM               VARCHAR(2),                                 -- 代入値自動登録選択項目フラグ
    INITIAL_VALUE                   TEXT,                                       -- 初期値
    VALIDATE_OPTION                 TEXT,                                       -- バリデーション値
    VALIDATE_REG_EXP                TEXT,                                       -- 正規表現バリデーション
    BEFORE_VALIDATE_REGISTER        TEXT,                                       -- 個別バリデーション前
    AFTER_VALIDATE_REGISTER         TEXT,                                       -- 個別バリデーション後
    DESCRIPTION_JA                  TEXT,                                       -- 説明(ja)
    DESCRIPTION_EN                  TEXT,                                       -- 説明(en)
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- カラムグループ管理
CREATE TABLE T_COMN_COLUMN_GROUP
(
    COL_GROUP_ID                    VARCHAR(40),                                -- カラムグループID
    PA_COL_GROUP_ID                 VARCHAR(40),                                -- 親カラムグループ
    COL_GROUP_NAME_JA               VARCHAR(255),                               -- カラムグループ名(ja)
    COL_GROUP_NAME_EN               VARCHAR(255),                               -- カラムグループ名(en)
    FULL_COL_GROUP_NAME_JA          TEXT,                                       -- フルカラムグループ名(ja)
    FULL_COL_GROUP_NAME_EN          TEXT,                                       -- フルカラムグループ名(en)
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(COL_GROUP_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_COMN_COLUMN_GROUP_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    COL_GROUP_ID                    VARCHAR(40),                                -- カラムグループID
    PA_COL_GROUP_ID                 VARCHAR(40),                                -- 親カラムグループ
    COL_GROUP_NAME_JA               VARCHAR(255),                               -- カラムグループ名(ja)
    COL_GROUP_NAME_EN               VARCHAR(255),                               -- カラムグループ名(en)
    FULL_COL_GROUP_NAME_JA          TEXT,                                       -- フルカラムグループ名(ja)
    FULL_COL_GROUP_NAME_EN          TEXT,                                       -- フルカラムグループ名(en)
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- バージョン確認
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




-- システム設定
CREATE TABLE T_COMN_SYSTEM_CONFIG
(
    ITEM_ID                         VARCHAR(40),                                -- UUID
    CONFIG_ID                       VARCHAR(255),                               -- 識別ID
    CONFIG_NAME                     VARCHAR(255),                               -- 項目名
    VALUE                           TEXT,                                       -- 設定値
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ITEM_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_COMN_SYSTEM_CONFIG_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    ITEM_ID                         VARCHAR(40),                                -- UUID
    CONFIG_ID                       VARCHAR(255),                               -- 識別ID
    CONFIG_NAME                     VARCHAR(255),                               -- 項目名
    VALUE                           TEXT,                                       -- 設定値
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- オペレーション一覧
CREATE TABLE T_COMN_OPERATION
(
    OPERATION_ID                    VARCHAR(40),                                -- オペレーションID
    OPERATION_NAME                  VARCHAR(255),                               -- オペレーション名
    OPERATION_DATE                  DATETIME(6),                                -- 実施予定日時
    LAST_EXECUTE_TIMESTAMP          DATETIME(6),                                -- 最終実行日時
    ENVIRONMENT                     VARCHAR(40),                                -- 環境
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(OPERATION_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_COMN_OPERATION_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    OPERATION_ID                    VARCHAR(40),                                -- オペレーションID
    OPERATION_NAME                  VARCHAR(255),                               -- オペレーション名
    OPERATION_DATE                  DATETIME(6),                                -- 実施予定日時
    LAST_EXECUTE_TIMESTAMP          DATETIME(6),                                -- 最終実行日時
    ENVIRONMENT                     VARCHAR(40),                                -- 環境
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- Movement一覧
CREATE TABLE T_COMN_MOVEMENT
(
    MOVEMENT_ID                     VARCHAR(40),                                -- ＭovemenID
    MOVEMENT_NAME                   VARCHAR(255),                               -- Movemen名
    ITA_EXT_STM_ID                  VARCHAR(2),                                 -- オーケストレータ
    TIME_LIMIT                      INT,                                        -- 遅延タイマー
    ANS_HOST_DESIGNATE_TYPE_ID      VARCHAR(2),                                 -- ホスト指定形式
    ANS_PARALLEL_EXE                INT,                                        -- 並列実行数
    ANS_WINRM_ID                    VARCHAR(2),                                 -- WinRM接続
    ANS_PLAYBOOK_HED_DEF            TEXT,                                       -- ヘッダーセクション
    ANS_EXEC_OPTIONS                TEXT,                                       -- オプションパラメータ
    ANS_ENGINE_VIRTUALENV_NAME      VARCHAR(255),                               -- Virtualenv　
    ANS_EXECUTION_ENVIRONMENT_NAME  VARCHAR(255),                               -- 実行環境
    ANS_ANSIBLE_CONFIG_FILE         VARCHAR(255),                               -- Ansible.cfg
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(MOVEMENT_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;

CREATE TABLE T_COMN_MOVEMENT_JNL
(
    JOURNAL_SEQ_NO                  VARCHAR(40),                                -- 履歴用シーケンス
    JOURNAL_REG_DATETIME            DATETIME(6),                                -- 履歴用変更日時
    JOURNAL_ACTION_CLASS            VARCHAR (8),                                -- 履歴用変更種別
    MOVEMENT_ID                     VARCHAR(40),                                -- ＭovemenID
    MOVEMENT_NAME                   VARCHAR(255),                               -- Movemen名
    ITA_EXT_STM_ID                  VARCHAR(2),                                 -- オーケストレータ
    TIME_LIMIT                      INT,                                        -- 遅延タイマー
    ANS_HOST_DESIGNATE_TYPE_ID      VARCHAR(2),                                 -- ホスト指定形式
    ANS_PARALLEL_EXE                INT,                                        -- 並列実行数
    ANS_WINRM_ID                    VARCHAR(2),                                 -- WinRM接続
    ANS_PLAYBOOK_HED_DEF            TEXT,                                       -- ヘッダーセクション
    ANS_EXEC_OPTIONS                TEXT,                                       -- オプションパラメータ
    ANS_ENGINE_VIRTUALENV_NAME      VARCHAR(255),                               -- Virtualenv　
    ANS_EXECUTION_ENVIRONMENT_NAME  VARCHAR(255),                               -- 実行環境
    ANS_ANSIBLE_CONFIG_FILE         VARCHAR(255),                               -- Ansible.cfg
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(JOURNAL_SEQ_NO)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;



-- カラムクラスマスタ
CREATE TABLE T_COMN_COLUMN_CLASS
(
    COLUMN_CLASS_ID                 VARCHAR(2),                                 -- 主キー
    COLUMN_CLASS_NAME               VARCHAR(255),                               -- カラムクラス名
    COLUMN_CLASS_DISP_NAME_JA       VARCHAR(255),                               -- カラムクラス表示名(ja)
    COLUMN_CLASS_DISP_NAME_EN       VARCHAR(255),                               -- カラムクラス表示名(en)
    MENU_CREATE_TARGET_FLAG         VARCHAR(1),                                 -- メニュー作成対象フラグ
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(COLUMN_CLASS_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- シートタイプマスタ
CREATE TABLE T_COMN_SHEET_TYPE
(
    SHEET_TYPE_NAME_ID              VARCHAR(2),                                 -- 主キー
    SHEET_TYPE_NAME_JA              VARCHAR(255),                               -- シートタイプ名(ja)
    SHEET_TYPE_NAME_EN              VARCHAR(255),                               -- シートタイプ名(en)
    MENU_CREATE_TARGET_FLAG         VARCHAR(1),                                 -- メニュー作成利用フラグ
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(SHEET_TYPE_NAME_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- オーケストレータマスタ
CREATE TABLE T_COMN_ORCHESTRA
(
    ORCHESTRA_ID                    VARCHAR(2),                                 -- 主キー
    ORCHESTRA_NAME                  VARCHAR(255),                               -- オーケストレータ名
    ORCHESTRA_PATH                  VARCHAR(255),                               -- in/outディレクトリパス
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(ORCHESTRA_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- ホスト指定形式マスタ
CREATE TABLE T_COMN_HOST_DESIGNATE_TYPE
(
    HOST_DESIGNATE_TYPE_ID          VARCHAR(2),                                 -- 主キー
    HOST_DESIGNATE_TYPE_NAME_JA     VARCHAR(255),                               -- 形式名(ja)
    HOST_DESIGNATE_TYPE_NAME_EN     VARCHAR(255),                               -- 形式名(en)
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(HOST_DESIGNATE_TYPE_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- booleanフラグマスタ
CREATE TABLE T_COMN_BOOLEAN_FLAG
(
    FLAG_ID                         VARCHAR(2),                                 -- 主キー
    FLAG_NAME                       VARCHAR(255),                               -- 表示名
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(FLAG_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- アクセス権限マスタ
CREATE TABLE T_COMN_OPERATION_PRIVILEGES
(
    PRIVILEGES_ID                   VARCHAR(2),                                 -- 主キー
    PRIVILEGES_NAME_JA              VARCHAR(255),                               -- 操作権限名(ja)
    PRIVILEGES_NAME_EN              VARCHAR(255),                               -- 操作権限名(en)
    DISP_SEQ                        INT,                                        -- 表示順序
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(PRIVILEGES_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- バックヤードユーザーマスタ
CREATE TABLE T_COMN_BACKYARD_USER
(
    USER_ID                         VARCHAR(8),                                 -- 主キー
    USER_NAME_JA                    VARCHAR(255),                               -- バックヤードユーザ名(JA)
    USER_NAME_EN                    VARCHAR(255),                               -- バックヤードユーザ名(EN)
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(USER_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- テーブル一覧テーブル
CREATE TABLE T_COMN_RECODE_LOCK_TABLE
(
    TABLE_NAME                      VARCHAR(64),                                -- テーブル名
    PRIMARY KEY(TABLE_NAME )
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- AACvirtualenvマスタ
CREATE TABLE T_COMN_AAC_VIRTUALENV
(
    VIRTUALENV_ID                   VARCHAR(40),                                -- UUID
    VIRTUALENV_NAME                 VARCHAR(255),                               -- AAC 仮想環境名
    VIRTUALENV_AAC_ID               INT,                                        -- AAC 仮想環境ID
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(VIRTUALENV_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- AAC実行環境マスタ
CREATE TABLE T_COMN_AAC_EXECUTION_ENVIRONMENT
(
    EXECUTION_ENVIRONMENT_ID        VARCHAR(40),                                -- UUID
    EXECUTION_ENVIRONMENT_NAME      VARCHAR(255),                               -- AAC 実行環境名
    EXECUTION_ENVIRONMENT_AAC_ID    INT,                                        -- AAC 実行環境ID
    NOTE                            TEXT,                                       -- 備考
    DISUSE_FLAG                     VARCHAR(1),                                 -- 廃止フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    LAST_UPDATE_USER                VARCHAR(40),                                -- 最終更新者
    PRIMARY KEY(EXECUTION_ENVIRONMENT_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




-- メニューグルーブメニュー結合ビュー
CREATE VIEW V_COMN_MENU_GROUP_MENU_PULLDOWN AS 
SELECT 
  TBL_1.*,
  CONCAT(TBL_2.MENU_GROUP_NAME_JA,':',TBL_1.MENU_NAME_JA) MENU_GROUP_NAME_PULLDOWN_JA,
  CONCAT(TBL_2.MENU_GROUP_NAME_EN,':',TBL_1.MENU_NAME_EN) MENU_GROUP_NAME_PULLDOWN_EN
FROM
  T_COMN_MENU TBL_1
  LEFT JOIN T_COMN_MENU_GROUP TBL_2 ON (TBL_1.MENU_GROUP_ID = TBL_2.MENU_GROUP_ID);
CREATE VIEW V_COMN_MENU_GROUP_MENU_PULLDOWN_JNL AS 
SELECT 
  TBL_1.*,
  CONCAT(TBL_2.MENU_GROUP_NAME_JA,':',TBL_1.MENU_NAME_JA) MENU_GROUP_NAME_PULLDOWN_JA,
  CONCAT(TBL_2.MENU_GROUP_NAME_EN,':',TBL_1.MENU_NAME_EN) MENU_GROUP_NAME_PULLDOWN_EN
FROM
  T_COMN_MENU_JNL TBL_1
  LEFT JOIN T_COMN_MENU_GROUP_JNL TBL_2 ON (TBL_1.MENU_GROUP_ID = TBL_2.MENU_GROUP_ID);



-- 処理実行フラグ管理
CREATE TABLE T_COMN_PROC_LOADED_LIST
(
    ROW_ID                          VARCHAR(40),                                -- UUID
    PROC_NAME                       VARCHAR(64),                                -- 処理名
    LOADED_FLG                      VARCHAR(1),                                 -- 実行フラグ
    LAST_UPDATE_TIMESTAMP           DATETIME(6),                                -- 最終更新日時
    PRIMARY KEY(ROW_ID)
)ENGINE = InnoDB, CHARSET = utf8mb4, COLLATE = utf8mb4_bin, ROW_FORMAT=COMPRESSED ,KEY_BLOCK_SIZE=8;




