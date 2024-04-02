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
    -- T_OASE_CONNECTION_METHOD: INSERT
    -- T_OASE_NOTIFICATION_TEMPLATE_COMMON_JNL: INSERT

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
UPDATE T_COMN_MENU_COLUMN_LINK SET COLUMN_DISP_SEQ = '190', INITIAL_VALUE = '3600', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010118';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET COLUMN_DISP_SEQ = '190', INITIAL_VALUE = '3600', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010118';
UPDATE T_COMN_MENU_COLUMN_LINK SET COLUMN_DISP_SEQ = '200', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010119';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET COLUMN_DISP_SEQ = '200', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010119';
UPDATE T_COMN_MENU_COLUMN_LINK SET COLUMN_DISP_SEQ = '210', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010120';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET COLUMN_DISP_SEQ = '210', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010120';
UPDATE T_COMN_MENU_COLUMN_LINK SET COLUMN_DISP_SEQ = '220', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010121';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET COLUMN_DISP_SEQ = '220', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010121';
UPDATE T_COMN_MENU_COLUMN_LINK SET COLUMN_DISP_SEQ = '230', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010122';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET COLUMN_DISP_SEQ = '230', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010122';
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
検索条件となる、イベントのプロパティのキーをJSONのクエリ言語（JMESPath）で指定します。
半角英数字と記号(!#%&()*+,-.;<=>?@[]^_{|}~)を使用できます。
下記キーも指定可能です。
・_exastro_event_collection_settings_id
・_exastro_fetched_time
・_exastro_end_time', DESCRIPTION_EN = '[Maximum length] 255 bytes
Specify the event property key as the search condition using the JSON query language (JMESPath).
You can use half-width alphanumeric characters and symbols (!#%&()*+,-.;<=>?@[]^_{|}~).
The following keys can also be specified.
・_exastro_event_collection_settings_id
・_exastro_fetched_time
・_exastro_end_time', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010604';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET VALIDATE_REG_EXP = '^[a-zA-Z0-9!#%&()*+,-.;<=>?@[\\]^_{|}~]+$', DESCRIPTION_JA = '[最大長]255バイト
検索条件となる、イベントのプロパティのキーをJSONのクエリ言語（JMESPath）で指定します。
半角英数字と記号(!#%&()*+,-.;<=>?@[]^_{|}~)を使用できます。
下記キーも指定可能です。
・_exastro_event_collection_settings_id
・_exastro_fetched_time
・_exastro_end_time', DESCRIPTION_EN = '[Maximum length] 255 bytes
Specify the event property key as the search condition using the JSON query language (JMESPath).
You can use half-width alphanumeric characters and symbols (!#%&()*+,-.;<=>?@[]^_{|}~).
The following keys can also be specified.
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

UPDATE T_COMN_MENU_COLUMN_LINK SET REF_TABLE_NAME = 'V_OASE_CONCLUSION_LABEL_KEY_GROUP', INITIAL_VALUE = '[["_exastro_type", "≠", "conclusion"]]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010704';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET REF_TABLE_NAME = 'V_OASE_CONCLUSION_LABEL_KEY_GROUP', INITIAL_VALUE = '[["_exastro_type", "≠", "conclusion"]]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010704';
UPDATE T_COMN_MENU_COLUMN_LINK SET INITIAL_VALUE = '[["_exastro_host", ""]]', COLUMN_DISP_SEQ = '180', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010916';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET INITIAL_VALUE = '[["_exastro_host", ""]]', COLUMN_DISP_SEQ = '180', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010916';
UPDATE T_COMN_MENU_COLUMN_LINK SET COLUMN_DISP_SEQ = '190', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010917';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET COLUMN_DISP_SEQ = '190', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010917';
UPDATE T_COMN_MENU_COLUMN_LINK SET COLUMN_DISP_SEQ = '200', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010918';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET COLUMN_DISP_SEQ = '200', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010918';
UPDATE T_COMN_MENU_COLUMN_LINK SET COLUMN_DISP_SEQ = '210', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010919';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET COLUMN_DISP_SEQ = '210', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010919';
UPDATE T_COMN_MENU_COLUMN_LINK SET COLUMN_DISP_SEQ = '220', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010920';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET COLUMN_DISP_SEQ = '220', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010920';
UPDATE T_COMN_MENU_COLUMN_LINK SET COLUMN_DISP_SEQ = '230', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010921';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET COLUMN_DISP_SEQ = '230', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010921';
UPDATE T_COMN_MENU_COLUMN_LINK SET COLUMN_DISP_SEQ = '240', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010922';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET COLUMN_DISP_SEQ = '240', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010922';
UPDATE T_COMN_MENU_COLUMN_LINK SET COLUMN_DISP_SEQ = '250', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010923';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET COLUMN_DISP_SEQ = '250', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010923';

UPDATE T_COMN_MENU_COLUMN_LINK SET COLUMN_DISP_SEQ = '40', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010803';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET COLUMN_DISP_SEQ = '40', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010803';
UPDATE T_COMN_MENU_COLUMN_LINK SET COLUMN_DISP_SEQ = '30', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010804';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET COLUMN_DISP_SEQ = '30', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010804';

UPDATE T_COMN_MENU_COLUMN_LINK SET COLUMN_DISP_SEQ = '180', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011012';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET COLUMN_DISP_SEQ = '180', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011012';
UPDATE T_COMN_MENU_COLUMN_LINK SET COLUMN_DISP_SEQ = '230', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011013';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET COLUMN_DISP_SEQ = '230', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011013';
UPDATE T_COMN_MENU_COLUMN_LINK SET COLUMN_DISP_SEQ = '240', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011014';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET COLUMN_DISP_SEQ = '240', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011014';
UPDATE T_COMN_MENU_COLUMN_LINK SET COLUMN_DISP_SEQ = '250', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011015';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET COLUMN_DISP_SEQ = '250', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011015';
UPDATE T_COMN_MENU_COLUMN_LINK SET COLUMN_DISP_SEQ = '260', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011016';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET COLUMN_DISP_SEQ = '260', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011016';
UPDATE T_COMN_MENU_COLUMN_LINK SET COLUMN_DISP_SEQ = '270', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011017';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET COLUMN_DISP_SEQ = '270', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011017';

UPDATE T_COMN_MENU_COLUMN_LINK SET REQUIRED_ITEM = '0', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010105';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET REQUIRED_ITEM = '0', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010105';


UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '以下の状態が存在します。
・検討中
・未知
・判定済み
・時間切れ', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010405';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '以下の状態が存在します。
・検討中
・未知
・判定済み
・時間切れ', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010405';

UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '以下の状態が存在します。
・イベント
・結論イベント', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010406';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '以下の状態が存在します。
・イベント
・結論イベント', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010406';

UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_EN = 'The following conditions exist:
・Under consideration
・Undetected
・Evaluated
・Time is up', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010405';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_EN = 'The following conditions exist:
・Under consideration
・Undetected
・Evaluated
・Time is up', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010405';

UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_EN = 'The following conditions exist:
・Event
・Conclusion event', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010406';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_EN = 'The following conditions exist:
・Event
・Conclusion event', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010406';

UPDATE T_COMN_MENU_COLUMN_LINK SET COLUMN_DISP_SEQ = '170', INPUT_ITEM = '1', VIEW_ITEM = '1', DISUSE_FLAG = '0', DESCRIPTION_JA = 'レスポンスのペイロード（※レスポンスキーで指定した階層）が配列かどうかを選択します。
Trueの場合、配列を分割し、その単位をイベントとして処理します。', DESCRIPTION_EN = 'Select whether the response payload (*layer specified by response key) is an array.
If True, splits the array and treats that unit as an event.', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010116';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET COLUMN_DISP_SEQ = '170', INPUT_ITEM = '1', VIEW_ITEM = '1', DISUSE_FLAG = '0', DESCRIPTION_JA = 'レスポンスのペイロード（※レスポンスキーで指定した階層）が配列かどうかを選択します。
Trueの場合、配列を分割し、その単位をイベントとして処理します。', DESCRIPTION_EN = 'Select whether the response payload (*layer specified by response key) is an array.
If True, splits the array and treats that unit as an event.', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010116';

UPDATE T_COMN_MENU_COLUMN_LINK SET COLUMN_DISP_SEQ = '160', DISUSE_FLAG = '0', DESCRIPTION_JA = 'レスポンスのペイロードから、OASEのイベントとして受け取るプロパティの、親となるキーを指定します。
レスポンスのペイロードの階層をJSONのクエリ言語（JMESPath）で指定します。', DESCRIPTION_EN = 'Specify the parent key of the property received as an OASE event from the response payload.
Specify the response payload hierarchy using the JSON query language (JMESPath).', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010117';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET COLUMN_DISP_SEQ = '160', DISUSE_FLAG = '0', DESCRIPTION_JA = 'レスポンスのペイロードから、OASEのイベントとして受け取るプロパティの、親となるキーを指定します。
レスポンスのペイロードの階層をJSONのクエリ言語（JMESPath）で指定します。', DESCRIPTION_EN = 'Specify the parent key of the property received as an OASE event from the response payload.
Specify the response payload hierarchy using the JSON query language (JMESPath).', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010117';

UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = 'イベント収集対象への接続方式を選択します。
・Bearer認証：
リクエストメソッドがGETかPOSTであり、接続先、認証トークンの入力が必須です。
・パスワード認証：
リクエストメソッドがGETかPOSTであり、接続先、ユーザー名、パスワードの入力が必須です。
・任意の認証：
リクエストメソッドがGETかPOSTであり、接続先の入力が必須です。
・IMAP　パスワード認証：
リクエストメソッドがIMAP: Plaintextであり、接続先、ユーザー名、パスワードの入力が必須です。
・エージェント不使用：
TTL以外に入力する必要はありません。', DESCRIPTION_EN = 'Select the connection method to the event collection target.
・Bearer certification:
The request method is GET or POST, and the connection destination and authentication token are required.
・Password authentication:
The request method is GET or POST, and the connection destination, user name, and password are required.
・Optional authentication:
The request method is GET or POST, and the connection destination is required.
・IMAP password authentication:
The request method is IMAP: Plaintext, and the connection destination, user name, and password are required.
・No agent used:
There is no need to enter anything other than TTL.', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010103';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = 'イベント収集対象への接続方式を選択します。
・Bearer認証：
リクエストメソッドがGETかPOSTであり、接続先、認証トークンの入力が必須です。
・パスワード認証：
リクエストメソッドがGETかPOSTであり、接続先、ユーザー名、パスワードの入力が必須です。
・任意の認証：
リクエストメソッドがGETかPOSTであり、接続先の入力が必須です。
・IMAP　パスワード認証：
リクエストメソッドがIMAP: Plaintextであり、接続先、ユーザー名、パスワードの入力が必須です。
・エージェント不使用：
TTL以外に入力する必要はありません。', DESCRIPTION_EN = 'Select the connection method to the event collection target.
・Bearer certification:
The request method is GET or POST, and the connection destination and authentication token are required.
・Password authentication:
The request method is GET or POST, and the connection destination, user name, and password are required.
・Optional authentication:
The request method is GET or POST, and the connection destination is required.
・IMAP password authentication:
The request method is IMAP: Plaintext, and the connection destination, user name, and password are required.
・No agent used:
There is no need to enter anything other than TTL.', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010103';

UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = 'リクエストメソッドを選択します。
・GET、POST
接続方式がBearer認証、パスワード認証、任意の認証の場合に利用可能です。
・IMAP: Plaintext
接続方式がIMAP　パスワード認証の場合に利用可能です。', DESCRIPTION_EN = 'Select a request method.
・GET, POST
Available when the connection method is Bearer authentication, password authentication, or any authentication.
・IMAP: Plaintext
Available when the connection method is IMAP password authentication.', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010104';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = 'リクエストメソッドを選択します。
・GET、POST
接続方式がBearer認証、パスワード認証、任意の認証の場合に利用可能です。
・IMAP: Plaintext
接続方式がIMAP　パスワード認証の場合に利用可能です。', DESCRIPTION_EN = 'Select a request method.
・GET, POST
Available when the connection method is Bearer authentication, password authentication, or any authentication.
・IMAP: Plaintext
Available when the connection method is IMAP password authentication.', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010104';

UPDATE T_COMN_MENU_COLUMN_LINK SET COLUMN_CLASS = '2', DISUSE_FLAG = '0', DESCRIPTION_JA = '[最大長]4000バイト
JSON形式で入力します。

・リクエストメソッドがGETの場合：
クエリパラメータ(接続先に追加される、"?"以降の値）として使用されます。
ex.
　接続先：http://example.com/dir/
　入力値：{ "name": "test" }
　の場合
　→リクエストURL：http://example.com/dir/?name=test
・リクエストメソッドがPOSTの場合：
リクエストのペイロードとして使用されます。', DESCRIPTION_EN = '[Maximum length] 4000 bytes
Enter in JSON format.

・If the request method is GET:
It is used as a query parameter (the value after "?" that is added to the connection destination).
ex.
Connect to: http://example.com/dir/
Input value: { "name": "test" }
 in the case of
→Request URL: http://example.com/dir/?name=test
・If the request method is POST:
Used as the payload of the request.', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010115';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET COLUMN_CLASS = '2', DISUSE_FLAG = '0', DESCRIPTION_JA = '[最大長]4000バイト
JSON形式で入力します。

・リクエストメソッドがGETの場合：
クエリパラメータ(接続先に追加される、"?"以降の値）として使用されます。
ex.
　接続先：http://example.com/dir/
　入力値：{ "name": "test" }
　の場合
　→リクエストURL：http://example.com/dir/?name=test
・リクエストメソッドがPOSTの場合：
リクエストのペイロードとして使用されます。', DESCRIPTION_EN = '[Maximum length] 4000 bytes
Enter in JSON format.

・If the request method is GET:
It is used as a query parameter (the value after "?" that is added to the connection destination).
ex.
Connect to: http://example.com/dir/
Input value: { "name": "test" }
 in the case of
→Request URL: http://example.com/dir/?name=test
・If the request method is POST:
Used as the payload of the request.', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010115';

UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '[最大長]4000バイト
リクエストヘッダーを入力します。', DESCRIPTION_EN = '[Maximum length] 4000 bytes
For API
   →Enter request header.', DISUSE_FLAG = '0', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010107';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '[最大長]4000バイト
リクエストヘッダーを入力します。', DESCRIPTION_EN = '[Maximum length] 4000 bytes
For API
   →Enter request header.', DISUSE_FLAG = '0', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010107';

UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '[最大長]10024バイト
Bearer認証の認証トークンを入力します。', DESCRIPTION_EN = '[Maximum length] 4000 bytes
For API
   →Enter the authentication token for Bearer authentication.', DISUSE_FLAG = '0', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010109';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '[最大長]10024バイト
Bearer認証の認証トークンを入力します。', DESCRIPTION_EN = '[Maximum length] 4000 bytes
For API
   →Enter the authentication token for Bearer authentication.', DISUSE_FLAG = '0', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010109';

UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '[最大長]1024バイト
SharedKeyLite認証のアクセスキーIDを入力します。', DESCRIPTION_EN = '[Maximum length] 4000 bytes
For API
   →Enter the access key ID for SharedKeyLite authentication.', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010113';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '[最大長]1024バイト
SharedKeyLite認証のアクセスキーIDを入力します。', DESCRIPTION_EN = '[Maximum length] 4000 bytes
For API
   →Enter the access key ID for SharedKeyLite authentication.', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010113';

UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '[最大長]4000バイト
SharedKeyLite認証の秘密アクセスキーを入力します。', DESCRIPTION_EN = '[Maximum length] 4000 bytes
For API
   →Enter the secret access key for SharedKeyLite authentication.', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010114';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '[最大長]4000バイト
SharedKeyLite認証の秘密アクセスキーを入力します。', DESCRIPTION_EN = '[Maximum length] 4000 bytes
For API
   →Enter the secret access key for SharedKeyLite authentication.', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010114';

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

INSERT INTO T_COMN_MENU_COLUMN_LINK (COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('11010810','110108','指定','Host ID','host_id','11010708','7',60,'V_OASE_HGSP_UQ_HOST_LIST','KY_KEY','KY_VALUE',NULL,'0',NULL,NULL,NULL,NULL,'HOST_ID',NULL,'0','1','1','0','0','1','0',NULL,NULL,NULL,NULL,NULL,'[元データ]機器一覧','[Original data] Device list',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK_JNL (JOURNAL_SEQ_NO,JOURNAL_REG_DATETIME,JOURNAL_ACTION_CLASS,COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES(11010810,_____DATE_____,'INSERT','11010810','110108','指定','Host ID','host_id','11010708','7',60,'V_OASE_HGSP_UQ_HOST_LIST','KY_KEY','KY_VALUE',NULL,'0',NULL,NULL,NULL,NULL,'HOST_ID',NULL,'0','1','1','0','0','1','0',NULL,NULL,NULL,NULL,NULL,'[元データ]機器一覧','[Original data] Device list',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK (COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('11010811','110108','利用パラメータシート','Parameter Sheet ID','parameter_sheet_id',NULL,'7',70,'V_OASE_MENU_PULLDOWN','MENU_ID','MENU_NAME',NULL,'1','["parameter_sheet_name_rest"]',NULL,NULL,NULL,'PARAMETER_SHEET_ID',NULL,'0','1','1','0','0','1','0',NULL,NULL,NULL,NULL,NULL,'[元データ]パラメータシート定義一覧','[Original data] Menu Definition list',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK_JNL (JOURNAL_SEQ_NO,JOURNAL_REG_DATETIME,JOURNAL_ACTION_CLASS,COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES(11010811,_____DATE_____,'INSERT','11010811','110108','利用パラメータシート','Parameter Sheet ID','parameter_sheet_id',NULL,'7',70,'V_OASE_MENU_PULLDOWN','MENU_ID','MENU_NAME',NULL,'1','["parameter_sheet_name_rest"]',NULL,NULL,NULL,'PARAMETER_SHEET_ID',NULL,'0','1','1','0','0','1','0',NULL,NULL,NULL,NULL,NULL,'[元データ]パラメータシート定義一覧','[Original data] Menu Definition list',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK (COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('11010812','110108','利用パラメータシート(rest)','Parameter Sheet Name(rest)','parameter_sheet_name_rest',NULL,'7',80,'V_OASE_MENU_PULLDOWN','MENU_ID','MENU_NAME_REST',NULL,'0',NULL,NULL,NULL,NULL,'PARAMETER_SHEET_NAME_REST',NULL,'0','2','1','0','0','1','0',NULL,NULL,NULL,NULL,NULL,'[元データ]パラメータシート定義一覧','[Original data] Menu Definition list',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK_JNL (JOURNAL_SEQ_NO,JOURNAL_REG_DATETIME,JOURNAL_ACTION_CLASS,COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES(11010812,_____DATE_____,'INSERT','11010812','110108','利用パラメータシート(rest)','Parameter Sheet Name(rest)','parameter_sheet_name_rest',NULL,'7',80,'V_OASE_MENU_PULLDOWN','MENU_ID','MENU_NAME_REST',NULL,'0',NULL,NULL,NULL,NULL,'PARAMETER_SHEET_NAME_REST',NULL,'0','2','1','0','0','1','0',NULL,NULL,NULL,NULL,NULL,'[元データ]パラメータシート定義一覧','[Original data] Menu Definition list',NULL,'0',_____DATE_____,1);

INSERT INTO T_COMN_MENU_COLUMN_LINK (COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('11011018','110110','イベント連携','Event collaboration','event_collaboration','11010708','7',120,'T_COMN_BOOLEAN_FLAG','FLAG_ID','FLAG_NAME',NULL,'0',NULL,NULL,NULL,NULL,'EVENT_COLLABORATION',NULL,'0','1','1','0','0','1','0',NULL,NULL,NULL,NULL,NULL,'イベントからの連携の有効無効を選択します。
True： 有効
False： 無効','Select whether to enable or disable collaboration from events.
True: Enabled
False: Disabled',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK_JNL (JOURNAL_SEQ_NO,JOURNAL_REG_DATETIME,JOURNAL_ACTION_CLASS,COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES(11011018,_____DATE_____,'INSERT','11011018','110110','イベント連携','Event collaboration','event_collaboration','11010708','7',120,'T_COMN_BOOLEAN_FLAG','FLAG_ID','FLAG_NAME',NULL,'0',NULL,NULL,NULL,NULL,'EVENT_COLLABORATION',NULL,'0','1','1','0','0','1','0',NULL,NULL,NULL,NULL,NULL,'イベントからの連携の有効無効を選択します。
True： 有効
False： 無効','Select whether to enable or disable collaboration from events.
True: Enabled
False: Disabled',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK (COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('11011019','110110','指定ホストID','Host ID','host_id','11010710','1',130,NULL,NULL,NULL,NULL,'0',NULL,NULL,NULL,NULL,'HOST_ID',NULL,'0','1','1','0','0','1','0',NULL,NULL,NULL,NULL,NULL,'[元データ]機器一覧','[Original data] Device list',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK_JNL (JOURNAL_SEQ_NO,JOURNAL_REG_DATETIME,JOURNAL_ACTION_CLASS,COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES(11011019,_____DATE_____,'INSERT','11011019','110110','指定ホストID','Host ID','host_id','11010710','1',130,NULL,NULL,NULL,NULL,'0',NULL,NULL,NULL,NULL,'HOST_ID',NULL,'0','1','1','0','0','1','0',NULL,NULL,NULL,NULL,NULL,'[元データ]機器一覧','[Original data] Device list',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK (COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('11011020','110110','指定ホスト名','Host NAME','host_name','11010710','1',140,NULL,NULL,NULL,NULL,'0',NULL,NULL,NULL,NULL,'HOST_NAME',NULL,'0','1','1','0','0','1','0',NULL,NULL,NULL,NULL,NULL,'[元データ]機器一覧','[Original data] Device list',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK_JNL (JOURNAL_SEQ_NO,JOURNAL_REG_DATETIME,JOURNAL_ACTION_CLASS,COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES(11011020,_____DATE_____,'INSERT','11011020','110110','指定ホスト名','Host NAME','host_name','11010710','1',140,NULL,NULL,NULL,NULL,'0',NULL,NULL,NULL,NULL,'HOST_NAME',NULL,'0','1','1','0','0','1','0',NULL,NULL,NULL,NULL,NULL,'[元データ]機器一覧','[Original data] Device list',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK (COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('11011021','110110','利用パラメータシート','Parameter Sheet ID','parameter_sheet_id',NULL,'1',150,NULL,NULL,NULL,NULL,'0',NULL,NULL,NULL,NULL,'PARAMETER_SHEET_ID',NULL,'0','1','1','0','0','1','0',NULL,NULL,NULL,NULL,NULL,'[元データ]パラメータシート定義一覧','[Original data] Menu Definition list',NULL,'1',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK_JNL (JOURNAL_SEQ_NO,JOURNAL_REG_DATETIME,JOURNAL_ACTION_CLASS,COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES(11011021,_____DATE_____,'INSERT','11011021','110110','利用パラメータシート','Parameter Sheet ID','parameter_sheet_id',NULL,'1',150,NULL,NULL,NULL,NULL,'0',NULL,NULL,NULL,NULL,'PARAMETER_SHEET_ID',NULL,'0','1','1','0','0','1','0',NULL,NULL,NULL,NULL,NULL,'[元データ]パラメータシート定義一覧','[Original data] Menu Definition list',NULL,'1',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK (COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('11011022','110110','利用パラメータシート名','Parameter Sheet Name','parameter_sheet_name',NULL,'1',160,NULL,NULL,NULL,NULL,'0',NULL,NULL,NULL,NULL,'PARAMETER_SHEET_NAME',NULL,'0','1','1','0','0','1','0',NULL,NULL,NULL,NULL,NULL,'[元データ]パラメータシート定義一覧','[Original data] Menu Definition list',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK_JNL (JOURNAL_SEQ_NO,JOURNAL_REG_DATETIME,JOURNAL_ACTION_CLASS,COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES(11011022,_____DATE_____,'INSERT','11011022','110110','利用パラメータシート名','Parameter Sheet Name','parameter_sheet_name',NULL,'1',160,NULL,NULL,NULL,NULL,'0',NULL,NULL,NULL,NULL,'PARAMETER_SHEET_NAME',NULL,'0','1','1','0','0','1','0',NULL,NULL,NULL,NULL,NULL,'[元データ]パラメータシート定義一覧','[Original data] Menu Definition list',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK (COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('11011023','110110','利用パラメータシート(rest)','Parameter Sheet Name(rest)','parameter_sheet_name_rest',NULL,'1',170,NULL,NULL,NULL,NULL,'0',NULL,NULL,NULL,NULL,'PARAMETER_SHEET_NAME_REST',NULL,'0','1','1','0','0','1','0',NULL,NULL,NULL,NULL,NULL,'[元データ]パラメータシート定義一覧','[Original data] Menu Definition list',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK_JNL (JOURNAL_SEQ_NO,JOURNAL_REG_DATETIME,JOURNAL_ACTION_CLASS,COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES(11011023,_____DATE_____,'INSERT','11011023','110110','利用パラメータシート(rest)','Parameter Sheet Name(rest)','parameter_sheet_name_rest',NULL,'1',170,NULL,NULL,NULL,NULL,'0',NULL,NULL,NULL,NULL,'PARAMETER_SHEET_NAME_REST',NULL,'0','1','1','0','0','1','0',NULL,NULL,NULL,NULL,NULL,'[元データ]パラメータシート定義一覧','[Original data] Menu Definition list',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK (COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('11011024','110110','アクション','Action Label Inheritance Flag','action_label_inheritance_flag','11010709','7',190,'T_COMN_BOOLEAN_FLAG','FLAG_ID','FLAG_NAME',NULL,'0',NULL,NULL,NULL,NULL,'ACTION_LABEL_INHERITANCE_FLAG',NULL,'0','1','1','0','1','0','0',NULL,NULL,NULL,NULL,NULL,'ルールに利用したイベント（元イベント）のラベルを、アクション実行のパラメータとして利用します。 True： 有効 False： 無効','Use the label of the event (original event) used in the rule as a parameter for action execution. True: Enabled False: Disabled',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK_JNL (JOURNAL_SEQ_NO,JOURNAL_REG_DATETIME,JOURNAL_ACTION_CLASS,COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES(11011024,_____DATE_____,'INSERT','11011024','110110','アクション','Action Label Inheritance Flag','action_label_inheritance_flag','11010709','7',190,'T_COMN_BOOLEAN_FLAG','FLAG_ID','FLAG_NAME',NULL,'0',NULL,NULL,NULL,NULL,'ACTION_LABEL_INHERITANCE_FLAG',NULL,'0','1','1','0','1','0','0',NULL,NULL,NULL,NULL,NULL,'ルールに利用したイベント（元イベント）のラベルを、アクション実行のパラメータとして利用します。 True： 有効 False： 無効','Use the label of the event (original event) used in the rule as a parameter for action execution. True: Enabled False: Disabled',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK (COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('11011025','110110','イベント','Event Label Inheritance Flag','event_label_inheritance_flag','11010709','7',200,'T_COMN_BOOLEAN_FLAG','FLAG_ID','FLAG_NAME',NULL,'0',NULL,NULL,NULL,NULL,'EVENT_LABEL_INHERITANCE_FLAG',NULL,'0','1','1','0','1','0','0',NULL,NULL,NULL,NULL,NULL,'ルールに利用したイベント（元イベント）のラベルを結論イベントに継承させます。 True： 有効 False： 無効','Let the conclusion event inherit the label of the event (original event) used in the rule. True: Enabled False: Disabled',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK_JNL (JOURNAL_SEQ_NO,JOURNAL_REG_DATETIME,JOURNAL_ACTION_CLASS,COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES(11011025,_____DATE_____,'INSERT','11011025','110110','イベント','Event Label Inheritance Flag','event_label_inheritance_flag','11010709','7',200,'T_COMN_BOOLEAN_FLAG','FLAG_ID','FLAG_NAME',NULL,'0',NULL,NULL,NULL,NULL,'EVENT_LABEL_INHERITANCE_FLAG',NULL,'0','1','1','0','1','0','0',NULL,NULL,NULL,NULL,NULL,'ルールに利用したイベント（元イベント）のラベルを結論イベントに継承させます。 True： 有効 False： 無効','Let the conclusion event inherit the label of the event (original event) used in the rule. True: Enabled False: Disabled',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK (COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('11011026','110110','アクションパラメータ','Action Parameters','action_parameters',NULL,'2',210,NULL,NULL,NULL,NULL,'0',NULL,NULL,NULL,NULL,'ACTION_PARAMETERS',NULL,'0','1','1','0','0','1','0',NULL,'{
"max_length": 4000
}',NULL,NULL,NULL,'アクションへのラベル継承するデータ','Configuring label inheritance for actions.',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK_JNL (JOURNAL_SEQ_NO,JOURNAL_REG_DATETIME,JOURNAL_ACTION_CLASS,COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES(11011026,_____DATE_____,'INSERT','11011026','110110','アクションパラメータ','Action Parameters','action_parameters',NULL,'2',210,NULL,NULL,NULL,NULL,'0',NULL,NULL,NULL,NULL,'ACTION_PARAMETERS',NULL,'0','1','1','0','0','1','0',NULL,'{
"max_length": 4000
}',NULL,NULL,NULL,'アクションへのラベル継承するデータ','Configuring label inheritance for actions.',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK (COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('11011027','110110','結論イベントラベル','Conclusion Event Labels','conclusion_event_labels',NULL,'2',220,NULL,NULL,NULL,NULL,'0',NULL,NULL,NULL,NULL,'CONCLUSION_EVENT_LABELS',NULL,'0','1','1','0','0','1','0',NULL,'{
"max_length": 4000
}',NULL,NULL,NULL,'結論イベントへのラベル継承するデータ','List of labels for events that match the rule',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK_JNL (JOURNAL_SEQ_NO,JOURNAL_REG_DATETIME,JOURNAL_ACTION_CLASS,COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES(11011027,_____DATE_____,'INSERT','11011027','110110','結論イベントラベル','Conclusion Event Labels','conclusion_event_labels',NULL,'2',220,NULL,NULL,NULL,NULL,'0',NULL,NULL,NULL,NULL,'CONCLUSION_EVENT_LABELS',NULL,'0','1','1','0','0','1','0',NULL,'{
"max_length": 4000
}',NULL,NULL,NULL,'結論イベントへのラベル継承するデータ','List of labels for events that match the rule',NULL,'0',_____DATE_____,1);

INSERT INTO T_COMN_MENU_COLUMN_LINK (COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('11010924','110109','アクション','Action label inheritance falg','action_label_inheritance_flag','11010709','7',160,'T_COMN_BOOLEAN_FLAG','FLAG_ID','FLAG_NAME',NULL,'0',NULL,NULL,NULL,NULL,'ACTION_LABEL_INHERITANCE_FLAG',NULL,'0','1','1','0','1','0','0','1',NULL,NULL,NULL,NULL,'ルールに利用したイベント（元イベント）のラベルを、アクション実行のパラメータとして利用します。
True： 有効
False： 無効','Use the label of the event (original event) used in the rule as a parameter for action execution.
True: Enabled
False: Disabled',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK_JNL (JOURNAL_SEQ_NO,JOURNAL_REG_DATETIME,JOURNAL_ACTION_CLASS,COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES(11010924,_____DATE_____,'INSERT','11010924','110109','アクション','Action label inheritance falg','action_label_inheritance_flag','11010709','7',160,'T_COMN_BOOLEAN_FLAG','FLAG_ID','FLAG_NAME',NULL,'0',NULL,NULL,NULL,NULL,'ACTION_LABEL_INHERITANCE_FLAG',NULL,'0','1','1','0','1','0','0','1',NULL,NULL,NULL,NULL,'ルールに利用したイベント（元イベント）のラベルを、アクション実行のパラメータとして利用します。
True： 有効
False： 無効','Use the label of the event (original event) used in the rule as a parameter for action execution.
True: Enabled
False: Disabled',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK (COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('11010925','110109','イベント','Event label inheritance falg','event_label_inheritance_flag','11010709','7',170,'T_COMN_BOOLEAN_FLAG','FLAG_ID','FLAG_NAME',NULL,'0',NULL,NULL,NULL,NULL,'EVENT_LABEL_INHERITANCE_FLAG',NULL,'0','1','1','0','1','0','0','0',NULL,NULL,NULL,NULL,'ルールに利用したイベント（元イベント）のラベルを結論イベントに継承させます。
True： 有効
False： 無効','Let the conclusion event inherit the label of the event (original event) used in the rule.
True: Enabled
False: Disabled',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK_JNL (JOURNAL_SEQ_NO,JOURNAL_REG_DATETIME,JOURNAL_ACTION_CLASS,COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES(11010925,_____DATE_____,'INSERT','11010925','110109','イベント','Event label inheritance falg','event_label_inheritance_flag','11010709','7',170,'T_COMN_BOOLEAN_FLAG','FLAG_ID','FLAG_NAME',NULL,'0',NULL,NULL,NULL,NULL,'EVENT_LABEL_INHERITANCE_FLAG',NULL,'0','1','1','0','1','0','0','0',NULL,NULL,NULL,NULL,'ルールに利用したイベント（元イベント）のラベルを結論イベントに継承させます。
True： 有効
False： 無効','Let the conclusion event inherit the label of the event (original event) used in the rule.
True: Enabled
False: Disabled',NULL,'0',_____DATE_____,1);

INSERT INTO T_COMN_MENU_COLUMN_LINK (COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('11010123','110101','イベントIDキー','EventId Key','event_id_key',NULL,'1',180,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'EVENT_ID_KEY',NULL,'0','1','1','0','0','0','0',NULL,'{
"min_length": 0,
"max_length": 255
}',NULL,NULL,NULL,'受け取ったイベントをユニークに判別するIDとなるキーがある場合に入力します。
レスポンスのペイロードの階層をJSONのクエリ言語（JMESPath）で指定します。
レスポンスキーの指定やレスポンスリストフラグの指定を考慮した、それ以下の階層を指定します。','Enter this if you have a key that serves as an ID to uniquely identify the received event.
Specify the response payload hierarchy using the JSON query language (JMESPath).
Specify the lower level, taking into account the response key specification and response list flag specification.',NULL,'0',_____DATE_____,1);
INSERT INTO T_COMN_MENU_COLUMN_LINK_JNL (JOURNAL_SEQ_NO,JOURNAL_REG_DATETIME,JOURNAL_ACTION_CLASS,COLUMN_DEFINITION_ID,MENU_ID,COLUMN_NAME_JA,COLUMN_NAME_EN,COLUMN_NAME_REST,COL_GROUP_ID,COLUMN_CLASS,COLUMN_DISP_SEQ,REF_TABLE_NAME,REF_PKEY_NAME,REF_COL_NAME,REF_SORT_CONDITIONS,REF_MULTI_LANG,REFERENCE_ITEM,SENSITIVE_COL_NAME,FILE_UPLOAD_PLACE,BUTTON_ACTION,COL_NAME,SAVE_TYPE,AUTO_INPUT,INPUT_ITEM,VIEW_ITEM,UNIQUE_ITEM,REQUIRED_ITEM,AUTOREG_HIDE_ITEM,AUTOREG_ONLY_ITEM,INITIAL_VALUE,VALIDATE_OPTION,VALIDATE_REG_EXP,BEFORE_VALIDATE_REGISTER,AFTER_VALIDATE_REGISTER,DESCRIPTION_JA,DESCRIPTION_EN,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES(11010123,_____DATE_____,'INSERT','11010123','110101','イベントIDキー','EventId Key','event_id_key',NULL,'1',180,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'EVENT_ID_KEY',NULL,'0','1','1','0','0','0','0',NULL,'{
"min_length": 0,
"max_length": 255
}',NULL,NULL,NULL,'受け取ったイベントをユニークに判別するIDとなるキーがある場合に入力します。
レスポンスのペイロードの階層をJSONのクエリ言語（JMESPath）で指定します。
レスポンスキーの指定やレスポンスリストフラグの指定を考慮した、それ以下の階層を指定します。','Enter this if you have a key that serves as an ID to uniquely identify the received event.
Specify the response payload hierarchy using the JSON query language (JMESPath).
Specify the lower level, taking into account the response key specification and response list flag specification.',NULL,'0',_____DATE_____,1);


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

-- T_OASE_CONNECTION_METHOD: INSERT
INSERT INTO T_OASE_CONNECTION_METHOD (CONNECTION_METHOD_ID,CONNECTION_METHOD_NAME_EN,CONNECTION_METHOD_NAME_JA,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('99','No Agent Used','エージェント不使用',NULL,'0',_____DATE_____,1);
INSERT INTO T_OASE_CONNECTION_METHOD (CONNECTION_METHOD_ID,CONNECTION_METHOD_NAME_EN,CONNECTION_METHOD_NAME_JA,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('1','Bearer Authentication','Bearer認証',NULL,'0',_____DATE_____,1);
INSERT INTO T_OASE_CONNECTION_METHOD (CONNECTION_METHOD_ID,CONNECTION_METHOD_NAME_EN,CONNECTION_METHOD_NAME_JA,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('2','password authentication','パスワード認証',NULL,'0',_____DATE_____,1);
INSERT INTO T_OASE_CONNECTION_METHOD (CONNECTION_METHOD_ID,CONNECTION_METHOD_NAME_EN,CONNECTION_METHOD_NAME_JA,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('4','IMAP password authentication','IMAP パスワード認証',NULL,'0',_____DATE_____,1);
INSERT INTO T_OASE_CONNECTION_METHOD (CONNECTION_METHOD_ID,CONNECTION_METHOD_NAME_EN,CONNECTION_METHOD_NAME_JA,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('5','Optional Authentication','任意の認証',NULL,'0',_____DATE_____,1);

-- T_OASE_REQUEST_METHOD: INSERT
INSERT INTO T_OASE_REQUEST_METHOD (REQUEST_METHOD_ID,REQUEST_METHOD_NAME,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('1','GET',NULL,'0',_____DATE_____,1);
INSERT INTO T_OASE_REQUEST_METHOD (REQUEST_METHOD_ID,REQUEST_METHOD_NAME,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('2','POST',NULL,'0',_____DATE_____,1);

-- T_OASE_NOTIFICATION_TEMPLATE_COMMON_JNL: INSERT
INSERT INTO T_OASE_NOTIFICATION_TEMPLATE_COMMON_JNL (JOURNAL_SEQ_NO,JOURNAL_REG_DATETIME,JOURNAL_ACTION_CLASS,NOTIFICATION_TEMPLATE_ID,EVENT_TYPE,TEMPLATE_FILE,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES(1,'20240209','INSERT','1','新規','新規.j2',NULL,'0','20240209',1);

INSERT INTO T_OASE_NOTIFICATION_TEMPLATE_COMMON_JNL (JOURNAL_SEQ_NO,JOURNAL_REG_DATETIME,JOURNAL_ACTION_CLASS,NOTIFICATION_TEMPLATE_ID,EVENT_TYPE,TEMPLATE_FILE,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES(2,'20240209','INSERT','2','既知（判定済）','既知（判定済）.j2',NULL,'0','20240209',1);

INSERT INTO T_OASE_NOTIFICATION_TEMPLATE_COMMON_JNL (JOURNAL_SEQ_NO,JOURNAL_REG_DATETIME,JOURNAL_ACTION_CLASS,NOTIFICATION_TEMPLATE_ID,EVENT_TYPE,TEMPLATE_FILE,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES(3,'20240209','INSERT','3','既知（時間切れ）','既知（時間切れ）.j2',NULL,'0','20240209',1);

INSERT INTO T_OASE_NOTIFICATION_TEMPLATE_COMMON_JNL (JOURNAL_SEQ_NO,JOURNAL_REG_DATETIME,JOURNAL_ACTION_CLASS,NOTIFICATION_TEMPLATE_ID,EVENT_TYPE,TEMPLATE_FILE,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES(4,'20240209','INSERT','4','未知','未知.j2',NULL,'0','20240209',1);
