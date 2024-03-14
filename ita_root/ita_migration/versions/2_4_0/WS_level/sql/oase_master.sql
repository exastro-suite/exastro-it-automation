-- INSERT/UPDATE: -2.4.0
    -- T_COMN_MENU_TABLE_LINK : UPDATE
    -- T_COMN_MENU_COLUMN_LINK : UPDATE
    -- T_COMN_MENU_COLUMN_LINK : INSERT
    -- T_OASE_COMPARISON_METHOD: UPDATE
    -- T_OASE_COMPARISON_METHOD: INSERT
    -- T_OASE_ACTION_STATUS: UPDATE
    -- T_OASE_LABEL_KEY_FIXED: UPDATE
    -- T_OASE_LABEL_KEY_FIXED: INSERT
    -- T_OASE_SEARCH_CONDITION: INSERT

-- T_COMN_MENU_TABLE_LINK : UPDATE
UPDATE T_COMN_MENU_TABLE_LINK SET VIEW_NAME = 'V_OASE_ACTION', UNIQUE_CONSTRAINT = '[["operation_id","conductor_class_id","event_collaboration","host_name","parameter_sheet_name"]]', BEFORE_VALIDATE_REGISTER = 'external_valid_menu_before', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE TABLE_DEFINITION_ID = '110108';
UPDATE T_COMN_MENU_TABLE_LINK_JNL SET VIEW_NAME = 'V_OASE_ACTION', UNIQUE_CONSTRAINT = '[["operation_id","conductor_class_id","event_collaboration","host_name","parameter_sheet_name"]]', BEFORE_VALIDATE_REGISTER = 'external_valid_menu_before', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE TABLE_DEFINITION_ID = '110108';

-- T_COMN_MENU_COLUMN_LINK: UPDATE
UPDATE T_COMN_MENU_COLUMN_LINK SET COLUMN_NAME_JA = '接続先', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010105';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET COLUMN_NAME_JA = '接続先', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010105';
UPDATE T_COMN_MENU_COLUMN_LINK SET COLUMN_NAME_EN = 'Access Point', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010105';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET COLUMN_NAME_EN = 'Access Point', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010105';
UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '[最大長]1024バイト
接続先を入力します。

以下のように入力してください。
メールサーバの場合
　→ホスト名を入力。ex.example.com
APIの場合
　→URLを入力。ex.http://example.com/dir/', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010105';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '[最大長]1024バイト
接続先を入力します。

以下のように入力してください。
メールサーバの場合
　→ホスト名を入力。ex.example.com
APIの場合
　→URLを入力。ex.http://example.com/dir/', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010105';
UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_EN = '[Maximum length] 1024 bytes
Enter the connection destination.

Please enter as below.
For mail servers
　→Enter the host name. ex.example.com
For API
　→Enter the URL. ex.http://example.com/dir/', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010105';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_EN = '[Maximum length] 1024 bytes
Enter the connection destination.

Please enter as below.
For mail servers
　→Enter the host name. ex.example.com
For API
　→Enter the URL. ex.http://example.com/dir/ Point', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010105';
UPDATE T_COMN_MENU_COLUMN_LINK SET INITIAL_VALUE = '3600', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010118';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET INITIAL_VALUE = '3600', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010118';
UPDATE T_COMN_MENU_COLUMN_LINK SET VALIDATE_OPTION = '{
"int_min": 10,
"int_max": 2147483647
}', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010118';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET VALIDATE_OPTION = '{
"int_min": 10,
"int_max": 2147483647
}', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010118';
UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '[最小値]10（秒）
[最大値]2147483647（秒）
[初期値]3600（秒）
TTL（Time To Live）とは、エージェントが取得したイベントが、ルールの評価対象として扱われる期間（秒）のことです。', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010118';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '[最小値]10（秒）
[最大値]2147483647（秒）
[初期値]3600（秒）
TTL（Time To Live）とは、エージェントが取得したイベントが、ルールの評価対象として扱われる期間（秒）のことです。', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010118';
UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_EN = '[Minimum value] 10 (seconds)
[Maximum value] 2147483647 (seconds)
[Initial value] 3600 (seconds)
TTL (Time To Live) is the period (in seconds) during which events acquired by an agent are treated as subject to rule evaluation.', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010118';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_EN = '[Minimum value] 10 (seconds)
[Maximum value] 2147483647 (seconds)
[Initial value] 3600 (seconds)
TTL (Time To Live) is the period (in seconds) during which events acquired by an agent are treated as subject to rule evaluation.', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010118';
UPDATE T_COMN_MENU_COLUMN_LINK SET INITIAL_VALUE = '3600', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010917';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET INITIAL_VALUE = '3600', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010917';
UPDATE T_COMN_MENU_COLUMN_LINK SET VALIDATE_OPTION = '{
"int_min": 10,
"int_max": 2147483647
}', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010917';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET VALIDATE_OPTION = '{
"int_min": 10,
"int_max": 2147483647
}', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010917';
UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '[最小値]10（秒）
[最大値]2147483647（秒）
[初期値]3600（秒）
TTL（Time To Live）とは、エージェントが取得したイベントが、ルールの評価対象として扱われる期間（秒）のことです。', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010917';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '[最小値]10（秒）
[最大値]2147483647（秒）
[初期値]3600（秒）
TTL（Time To Live）とは、エージェントが取得したイベントが、ルールの評価対象として扱われる期間（秒）のことです。', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010917';
UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_EN = '[Minimum value] 10 (seconds)
[Maximum value] 2147483647 (seconds)
[Initial value] 3600 (seconds)
TTL (Time To Live) is the period (in seconds) during which events acquired by an agent are treated as subject to rule evaluation.', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010917';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_EN = '[Minimum value] 10 (seconds)
[Maximum value] 2147483647 (seconds)
[Initial value] 3600 (seconds)
TTL (Time To Live) is the period (in seconds) during which events acquired by an agent are treated as subject to rule evaluation.', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010917';
UPDATE T_COMN_MENU_COLUMN_LINK SET VALIDATE_REG_EXP = '^[a-zA-Z0-9!#%&()*+,-.;<=>?@[\\]^_{|}~]+$', DESCRIPTION_JA = '[最大長]255バイト
検索条件となる、イベントのプロパティのキーを半角英数字と利用可能な記号(!#%&()*+,-.;<=>?@[]^_{|}~)で入力します。
下記キーも入力可能です。
・_exastro_event_collection_settings_id
・_exastro_fetched_time
・_exastro_end_time', DESCRIPTION_EN = '[Maximum length] 255 bytes
Enter the event property key as a search condition using half-width alphanumeric characters and available symbols (!#%&()*+,-.;<=>?@[]^_{|}~).
You can also enter the following keys.
・_exastro_event_collection_settings_id
・_exastro_fetched_time
・_exastro_end_time', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010604';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET VALIDATE_REG_EXP = '^[a-zA-Z0-9!#%&()*+,-.;<=>?@[\\]^_{|}~]+$', DESCRIPTION_JA = '[最大長]255バイト
検索条件となる、イベントのプロパティのキーを半角英数字と利用可能な記号(!#%&()*+,-.;<=>?@[]^_{|}~)で入力します。
下記キーも入力可能です。
・_exastro_event_collection_settings_id
・_exastro_fetched_time
・_exastro_end_time', DESCRIPTION_EN = '[Maximum length] 255 bytes
Enter the event property key as a search condition using half-width alphanumeric characters and available symbols (!#%&()*+,-.;<=>?@[]^_{|}~).
You can also enter the following keys.
・_exastro_event_collection_settings_id
・_exastro_fetched_time
・_exastro_end_time', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010604';
UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '値のデータ型を選択します。
・真偽値、オブジェクト、配列、空判定：
比較方法が[==, ≠]の場合に、いずれかを指定してください。
・その他：
比較方法が[RegExp, RegExp(DOTALL), RegExp(MULTILINE)]の場合は指定してください。', DESCRIPTION_EN = 'Select the data type of the value.
・Boolean value, object, array, empty judgment:
If the comparison method is [==, ≠], please specify one.
·others:
Please specify if the comparison method is [RegExp, RegExp(DOTALL), RegExp(MULTILINE)]. ', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010605';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET  DESCRIPTION_JA = '値のデータ型を選択します。
・真偽値、オブジェクト、配列、空判定：
比較方法が[==, ≠]の場合に、いずれかを指定してください。
・その他：
比較方法が[RegExp, RegExp(DOTALL), RegExp(MULTILINE)]の場合は指定してください。', DESCRIPTION_EN = 'Select the data type of the value.
・Boolean value, object, array, empty judgment:
If the comparison method is [==, ≠], please specify one.
·others:
Please specify if the comparison method is [RegExp, RegExp(DOTALL), RegExp(MULTILINE)]. ', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010605';
UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '比較方法を選択します。
・<, <=, >, >=：
値のデータ型が、[文字列、整数、小数]の場合のみ選択可能です。
・RegExp, RegExp(DOTALL), RegExp(MULTILINE)：
値のデータ型が、[その他]の場合のみ選択可能です。',  DESCRIPTION_EN = 'Select a comparison method.
・<, <=, >, >=：
Can only be selected when the value data type is [String, Integer, Decimal].
・RegExp, RegExp(DOTALL), RegExp(MULTILINE):
Can only be selected when the value data type is [Other]. ', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010606';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '比較方法を選択します。
・<, <=, >, >=：
値のデータ型が、[文字列、整数、小数]の場合のみ選択可能です。
・RegExp, RegExp(DOTALL), RegExp(MULTILINE)：
値のデータ型が、[その他]の場合のみ選択可能です。',  DESCRIPTION_EN = 'Select a comparison method.
・<, <=, >, >=：
Can only be selected when the value data type is [String, Integer, Decimal].
・RegExp, RegExp(DOTALL), RegExp(MULTILINE):
Can only be selected when the value data type is [Other]. ', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010606';
UPDATE T_COMN_MENU_COLUMN_LINK SET VALIDATE_REG_EXP = NULL, DESCRIPTION_JA = '[最大長]255バイト
ラベル付与したい値を入力します。

正規表現で使用したい場合は、以下のように入力してください。
①正規表現を使って（「比較する値」による）検索を行い、任意の値をラベルにつけたい
任意の値を入力してください。
②正規表現を使って（「比較する値」による）検索を行い、そのマッチした結果を、ラベルの値としてそのまま利用したい場合
値を空欄にしてください。
③②のマッチした結果に対して、正規表現置換を行いたい場合
検索結果のキャプチャグループの値を使いたい場合などを想定しています
ex.
・キャプチャグループの1個目をラベルの値にしたい場合
　→ \\1
・キャプチャグループの1個目 + 任意の値（.com）をラベルの値にしたい場合
　→ \\1.com', DESCRIPTION_EN = '[Maximum length] 255 bytes
Enter the value you want to label.

If you want to use it as a regular expression, enter it as follows.
① I want to search using regular expressions (by "value to compare") and add any value to the label.
Please enter any value.
② If you want to search using regular expressions (by "value to compare") and use the matching results as is as the label value.
Please leave the value blank.
③ If you want to perform regular expression replacement on the matched results of ②
This assumes cases where you want to use the capture group value of search results.
ex.
・If you want the first capture group to be the label value
→ \\1
・If you want to set the first capture group + any value (.com) as the label value
→ \\1.com', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010609';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET VALIDATE_REG_EXP = NULL, DESCRIPTION_JA = '[最大長]255バイト
ラベル付与したい値を入力します。

正規表現で使用したい場合は、以下のように入力してください。
①正規表現を使って（「比較する値」による）検索を行い、任意の値をラベルにつけたい
任意の値を入力してください。
②正規表現を使って（「比較する値」による）検索を行い、そのマッチした結果を、ラベルの値としてそのまま利用したい場合
値を空欄にしてください。
③②のマッチした結果に対して、正規表現置換を行いたい場合
検索結果のキャプチャグループの値を使いたい場合などを想定しています
ex.
・キャプチャグループの1個目をラベルの値にしたい場合
　→ \\1
・キャプチャグループの1個目 + 任意の値（.com）をラベルの値にしたい場合
　→ \\1.com', DESCRIPTION_EN = '[Maximum length] 255 bytes
Enter the value you want to label.

If you want to use it as a regular expression, enter it as follows.
① I want to search using regular expressions (by "value to compare") and add any value to the label.
Please enter any value.
② If you want to search using regular expressions (by "value to compare") and use the matching results as is as the label value.
Please leave the value blank.
③ If you want to perform regular expression replacement on the matched results of ②
This assumes cases where you want to use the capture group value of search results.
ex.
・If you want the first capture group to be the label value
→ \\1
・If you want to set the first capture group + any value (.com) as the label value
→ \\1.com', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010609';
UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '[最大長]255バイト
任意のルール名を入力します。', DESCRIPTION_EN = '[Maximum length] 255 bytes
Enter any rule name.', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010903';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '[最大長]255バイト
任意のルール名を入力します。', DESCRIPTION_EN = '[Maximum length] 255 bytes
Enter any rule name.', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010903';
UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '[最大長]255バイト
どのルールから作成された結論イベントなのかを、恒久的に判別するため"_exastro_rule_name"ラベルに設定する任意の名前を入力します。
※後から変更することはできません。', DESCRIPTION_EN = '[Maximum length] 255 bytes
Enter any name you want to set in the "_exastro_rule_name" label to permanently identify which rule the conclusion event was created from.
*You cannot change it later.', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010904';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '[最大長]255バイト
どのルールから作成された結論イベントなのかを、恒久的に判別するため"_exastro_rule_name"ラベルに設定する任意の名前を入力します。
※後から変更することはできません。', DESCRIPTION_EN = '[Maximum length] 255 bytes
Enter any name you want to set in the "_exastro_rule_name" label to permanently identify which rule the conclusion event was created from.
*You cannot change it later.', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010904';
UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = 'ステータスには以下の状態が存在します。
・判定済み
・実行中
・承認待ち
・承認済み
・承認却下済み
・完了
・完了（異常）
・完了確認待ち
・完了確認済み
・完了確認却下済み', DESCRIPTION_EN = 'The following status states exist.
・Evaluated
・Running
・Awaiting Approval
・Approved
・Rejected
・Completed
・Completed (abnormal)
・Waiting for completion confirmation
・Completion Confirmed
・Completion confirmed rejected', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011004';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = 'ステータスには以下の状態が存在します。
・判定済み
・実行中
・承認待ち
・承認済み
・承認却下済み
・完了
・完了（異常）
・完了確認待ち
・完了確認済み
・完了確認却下済み', DESCRIPTION_EN = 'The following status states exist.
・Evaluated
・Running
・Awaiting Approval
・Approved
・Rejected
・Completed
・Completed (abnormal)
・Waiting for completion confirmation
・Completion Confirmed
・Completion confirmed rejected', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011004';

UPDATE T_COMN_MENU_COLUMN_LINK SET INITIAL_VALUE = '[["_exastro_type", "≠", "conclusion"]]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010704';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET INITIAL_VALUE = '[["_exastro_type", "≠", "conclusion"]]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010704';
UPDATE T_COMN_MENU_COLUMN_LINK SET INITIAL_VALUE = '[["_exastro_host", ""]]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010916';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET INITIAL_VALUE = '[["_exastro_host", ""]]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010916';

UPDATE T_COMN_MENU_COLUMN_LINK SET COLUMN_DISP_SEQ = '40', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010803';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET COLUMN_DISP_SEQ = '40', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010803';
UPDATE T_COMN_MENU_COLUMN_LINK SET COLUMN_DISP_SEQ = '30', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010804';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET COLUMN_DISP_SEQ = '30', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010804';


-- T_COMN_MENU_COLUMN_LINK: INSERT

INSERT INTO T_COMN_MENU_COLUMN_LINK (COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('11010709','110107','検索方法','Search Condition Id','search_condition_id',NULL,'7',50,'T_OASE_SEARCH_CONDITION','SEARCH_CONDITION_ID','SEARCH_CONDITION_NAME',NULL,'1',NULL,NULL,NULL,NULL,'SEARCH_CONDITION_ID',NULL,'0','1','1','0','1','0','0','1',NULL,NULL,NULL,NULL,'検索方法を選択します。
ユニーク：一意のイベントの抽出しか許可しません。複数イベントがヒットした場合、ヒットしたイベントすべてを未知のイベントとして処理します。
キューイング：一意のイベントを抽出しますが、複数イベントがヒットした場合、一番古いイベントを使用します。ルールに複数回マッチする可能性があるため、ご注意ください。','Select a search method.
Unique: Only allows extraction of unique events. If multiple events are hit, all hit events are treated as unknown events.
Queuing: Extract unique events, but if multiple events are hit, use the oldest event. Please note that the rule may be matched multiple times.',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK_JNL (JOURNAL_SEQ_NO,JOURNAL_REG_DATETIME,JOURNAL_ACTION_CLASS,COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES(11010709,_____DATE_____,'INSERT','11010709','110107','検索方法','Search Condition Id','search_condition_id',NULL,'7',50,'T_OASE_SEARCH_CONDITION','SEARCH_CONDITION_ID','SEARCH_CONDITION_NAME',NULL,'1',NULL,NULL,NULL,NULL,'SEARCH_CONDITION_ID',NULL,'0','1','1','0','1','0','0','1',NULL,NULL,NULL,NULL,'検索方法を選択します。
ユニーク：一意のイベントの抽出しか許可しません。複数イベントがヒットした場合、ヒットしたイベントすべてを未知のイベントとして処理します。
キューイング：一意のイベントを抽出しますが、複数イベントがヒットした場合、一番古いイベントを使用します。ルールに複数回マッチする可能性があるため、ご注意ください。','Select a search method.
Unique: Only allows extraction of unique events. If multiple events are hit, all hit events are treated as unknown events.
Queuing: Extract unique events, but if multiple events are hit, use the oldest event. Please note that the rule may be matched multiple times.',NULL,'0',_____DATE_____,1);

INSERT INTO T_COMN_MENU_COLUMN_LINK (COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('11010809','110108','イベント連携','Event collaboration','event_collaboration','11010708','7',50,'T_COMN_BOOLEAN_FLAG','FLAG_ID','FLAG_NAME',NULL,'0',NULL,NULL,NULL,NULL,'EVENT_COLLABORATION',NULL,'0','1','1','0','1','0','0','0',NULL,NULL,NULL,NULL,'イベントからの連携の有効無効を選択します。
True： 有効
False： 無効','Select whether to enable or disable collaboration from events.
True: Enabled
False: Disabled',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK_JNL (JOURNAL_SEQ_NO,JOURNAL_REG_DATETIME,JOURNAL_ACTION_CLASS,COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES(11010809,_____DATE_____,'INSERT','11010809','110108','イベント連携','Event collaboration','event_collaboration','11010708','7',50,'T_COMN_BOOLEAN_FLAG','FLAG_ID','FLAG_NAME',NULL,'0',NULL,NULL,NULL,NULL,'EVENT_COLLABORATION',NULL,'0','1','1','0','1','0','0','0',NULL,NULL,NULL,NULL,'イベントからの連携の有効無効を選択します。
True： 有効
False： 無効','Select whether to enable or disable collaboration from events.
True: Enabled
False: Disabled',NULL,'0',_____DATE_____,1);

INSERT INTO T_COMN_MENU_COLUMN_LINK (COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('11010810','110108','指定','Host name','host_name','11010708','7',60,'V_HGSP_UQ_HOST_LIST','KY_KEY','KY_VALUE',NULL,'0',NULL,NULL,NULL,NULL,'HOST_NAME',NULL,'0','1','1','0','0','1','0',NULL,NULL,NULL,NULL,NULL,'[元データ]機器一覧','[Original data] Device list',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK_JNL (JOURNAL_SEQ_NO,JOURNAL_REG_DATETIME,JOURNAL_ACTION_CLASS,COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES(11010810,_____DATE_____,'INSERT','11010810','110108','指定','Host name','host_name','11010708','7',60,'V_HGSP_UQ_HOST_LIST','KY_KEY','KY_VALUE',NULL,'0',NULL,NULL,NULL,NULL,'HOST_NAME',NULL,'0','1','1','0','0','1','0',NULL,NULL,NULL,NULL,NULL,'[元データ]機器一覧','[Original data] Device list',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK (COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('11010811','110108','利用パラメータシート','Parameter Sheet Name','parameter_sheet_name',NULL,'7',70,'V_MENU_DEFINE','MENU_CREATE_ID','MENU_NAME',NULL,'1','["parameter_sheet_name_rest"]',NULL,NULL,NULL,'PARAMETER_SHEET_NAME',NULL,'0','1','1','0','0','1','0',NULL,NULL,NULL,NULL,NULL,'[元データ]パラメータシート定義一覧','[Original data] Menu Definition list',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK_JNL (JOURNAL_SEQ_NO,JOURNAL_REG_DATETIME,JOURNAL_ACTION_CLASS,COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES(11010811,_____DATE_____,'INSERT','11010811','110108','利用パラメータシート','Parameter Sheet Name','parameter_sheet_name',NULL,'7',70,'V_MENU_DEFINE','MENU_CREATE_ID','MENU_NAME',NULL,'1','["parameter_sheet_name_rest"]',NULL,NULL,NULL,'PARAMETER_SHEET_NAME',NULL,'0','1','1','0','0','1','0',NULL,NULL,NULL,NULL,NULL,'[元データ]パラメータシート定義一覧','[Original data] Menu Definition list',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK (COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('11010812','110108','利用パラメータシート(rest)','Parameter Sheet Name(rest)','parameter_sheet_name_rest',NULL,'7',80,'V_MENU_DEFINE','MENU_CREATE_ID','MENU_NAME_REST',NULL,'0',NULL,NULL,NULL,NULL,'PARAMETER_SHEET_NAME_REST',NULL,'0','2','1','0','0','1','0',NULL,NULL,NULL,NULL,NULL,'[元データ]パラメータシート定義一覧','[Original data] Menu Definition list',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK_JNL (JOURNAL_SEQ_NO,JOURNAL_REG_DATETIME,JOURNAL_ACTION_CLASS,COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES(11010812,_____DATE_____,'INSERT','11010812','110108','利用パラメータシート(rest)','Parameter Sheet Name(rest)','parameter_sheet_name_rest',NULL,'7',80,'V_MENU_DEFINE','MENU_CREATE_ID','MENU_NAME_REST',NULL,'0',NULL,NULL,NULL,NULL,'PARAMETER_SHEET_NAME_REST',NULL,'0','2','1','0','0','1','0',NULL,NULL,NULL,NULL,NULL,'[元データ]パラメータシート定義一覧','[Original data] Menu Definition list',NULL,'0',_____DATE_____,1);

INSERT INTO T_COMN_MENU_COLUMN_LINK (COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('11011018','110110','結論ラベル','Conclusion Labels','conclusion_labels',NULL,'2',130,NULL,NULL,NULL,NULL,'0',NULL,NULL,NULL,NULL,'CONCLUSION_LABELS',NULL,'0','1','1','0','0','1','0',NULL,'{
"max_length": 4000
}',NULL,NULL,NULL,'ルールにマッチしたイベントのラベル一覧','List of labels for events that match the rule',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK_JNL (JOURNAL_SEQ_NO,JOURNAL_REG_DATETIME,JOURNAL_ACTION_CLASS,COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES(11011018,_____DATE_____,'INSERT','11011018','110110','結論ラベル','Conclusion Labels','conclusion_labels',NULL,'2',130,NULL,NULL,NULL,NULL,'0',NULL,NULL,NULL,NULL,'CONCLUSION_LABELS',NULL,'0','1','1','0','0','1','0',NULL,'{
"max_length": 4000
}',NULL,NULL,NULL,'ルールにマッチしたイベントのラベル一覧','List of labels for events that match the rule',NULL,'0',_____DATE_____,1);



-- T_OASE_COMPARISON_METHOD: UPDATE
UPDATE T_OASE_COMPARISON_METHOD SET COMPARISON_METHOD_NAME_EN = 'regular expression（no option）', COMPARISON_METHOD_NAME_JA = '正規表現（optionなし）', COMPARISON_METHOD_SYMBOL = 'RegExp', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COMPARISON_METHOD_ID = '7';

-- T_OASE_COMPARISON_METHOD: INSERT
INSERT INTO T_OASE_COMPARISON_METHOD (COMPARISON_METHOD_ID,COMPARISON_METHOD_NAME_EN,COMPARISON_METHOD_NAME_JA,COMPARISON_METHOD_SYMBOL,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('8','regular expression（DOTALL）','正規表現（DOTALL）','RegExp(DOTALL)',NULL,'0',_____DATE_____,1);
INSERT INTO T_OASE_COMPARISON_METHOD (COMPARISON_METHOD_ID,COMPARISON_METHOD_NAME_EN,COMPARISON_METHOD_NAME_JA,COMPARISON_METHOD_SYMBOL,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('9','regular expression（MULTILINE ）','正規表現（MULTILINE ）','RegExp(MULTILINE )',NULL,'0',_____DATE_____,1);

-- T_OASE_ACTION_STATUS: UPDATE
UPDATE T_OASE_ACTION_STATUS SET ACTION_STASTUS_NAME_EN = 'Evaluated', ACTION_STASTUS_NAME_JA = '判定済み', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE ACTION_STASTUS_ID = '1';


-- T_OASE_LABEL_KEY_FIXED: UPDATE
UPDATE T_OASE_LABEL_KEY_FIXED SET DISUSE_FLAG = '0', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE LABEL_KEY_ID = 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx07';

-- T_OASE_LABEL_KEY_FIXED: INSERT
INSERT INTO T_OASE_LABEL_KEY_FIXED (LABEL_KEY_ID,LABEL_KEY_NAME,COLOR_CODE,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx09','_exastro_host',NULL,NULL,'0',_____DATE_____,1);

-- T_OASE_SEARCH_CONDITION
INSERT INTO T_OASE_SEARCH_CONDITION (SEARCH_CONDITION_ID,SEARCH_CONDITION_NAME_EN,SEARCH_CONDITION_NAME_JA,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('1','Unique','ユニーク',NULL,'0',_____DATE_____,1);

INSERT INTO T_OASE_SEARCH_CONDITION (SEARCH_CONDITION_ID,SEARCH_CONDITION_NAME_EN,SEARCH_CONDITION_NAME_JA,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('2','Queuing','キューイング',NULL,'0',_____DATE_____,1);
