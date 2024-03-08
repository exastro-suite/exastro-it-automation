-- INSERT/UPDATE: -2.4.0
    -- T_COMN_MENU_COLUMN_LINK : UPDATE
    -- T_OASE_COMPARISON_METHOD: UPDATE
    -- T_OASE_COMPARISON_METHOD: INSERT
    -- T_OASE_ACTION_STATUS: UPDATE

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

-- T_OASE_COMPARISON_METHOD: UPDATE
UPDATE T_OASE_COMPARISON_METHOD SET COMPARISON_METHOD_NAME_EN = 'regular expression（no option）', COMPARISON_METHOD_NAME_JA = '正規表現（optionなし）', COMPARISON_METHOD_SYMBOL = 'RegExp', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COMPARISON_METHOD_ID = '7';

-- T_OASE_COMPARISON_METHOD: INSERT
INSERT INTO T_OASE_COMPARISON_METHOD (COMPARISON_METHOD_ID,COMPARISON_METHOD_NAME_EN,COMPARISON_METHOD_NAME_JA,COMPARISON_METHOD_SYMBOL,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('8','regular expression（DOTALL）','正規表現（DOTALL）','RegExp(DOTALL)',NULL,'0',_____DATE_____,1);
INSERT INTO T_OASE_COMPARISON_METHOD (COMPARISON_METHOD_ID,COMPARISON_METHOD_NAME_EN,COMPARISON_METHOD_NAME_JA,COMPARISON_METHOD_SYMBOL,NOTE,DISUSE_FLAG,LAST_UPDATE_TIMESTAMP,LAST_UPDATE_USER) VALUES('9','regular expression（MULTILINE ）','正規表現（MULTILINE ）','RegExp(MULTILINE )',NULL,'0',_____DATE_____,1);

-- T_OASE_ACTION_STATUS: UPDATE
UPDATE T_OASE_ACTION_STATUS SET ACTION_STASTUS_NAME_EN = 'Evaluated', ACTION_STASTUS_NAME_JA = '判定済み', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE ACTION_STASTUS_ID = '1';
