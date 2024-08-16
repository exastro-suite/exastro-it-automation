-- INSERT/UPDATE: -2.5.0
    -- T_COMN_MENU_COLUMN_LINK: UPDATE
    -- T_COMN_MENU: UPDATE

-- T_COMN_MENU_COLUMN_LINK: UPDATE
UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '[最大長]4000バイト
ログインするユーザーのパスワードを入力します。', DESCRIPTION_EN = '[Maximum length] 4000 bytes
Enter the password of the user to log in.', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010111';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '[最大長]4000バイト
ログインするユーザーのパスワードを入力します。', DESCRIPTION_EN = '[Maximum length] 4000 bytes
Enter the password of the user to log in.', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010111';

UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '[元データ]
OASE管理/イベント収集/イベント収集設定ID', DESCRIPTION_EN = '[Original data]
OASE Management/Event collection/Event Collection Setting ID', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010402';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '[元データ]
OASE管理/イベント収集/イベント収集設定ID', DESCRIPTION_EN = '[Original data]
OASE Management/Event collection/Event Collection Setting ID', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010402';

UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '[元データ]
OASE/ルール/ルールラベル名', DESCRIPTION_EN = '[Original data]
OASE/Rule/Rule label name', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010408';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '[元データ]
OASE/ルール/ルールラベル名', DESCRIPTION_EN = '[Original data]
OASE/Rule/Rule label name', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010408';

UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = 'イベント収集で登録したイベント収集設定名が表示されます。', DESCRIPTION_EN = 'Displays the event collection setting name registered with the Event collection.', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010603';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = 'イベント収集で登録したイベント収集設定名が表示されます。', DESCRIPTION_EN = 'Displays the event collection setting name registered with the Event collection.', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010603';

UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '[元データ]
Conductor/Conductor一覧/Conductor名称', DESCRIPTION_EN = '[Original data]
Conductor/Conductor class list/Conductor name', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010804';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '[元データ]
Conductor/Conductor一覧/Conductor名称', DESCRIPTION_EN = '[Original data]
Conductor/Conductor class list/Conductor name', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010804';

UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '[元データ]
基本コンソール/オペレーション一覧/オペレーション名', DESCRIPTION_EN = '[Original data]
Basic Console/Operation list/operation name', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010803';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '[元データ]
基本コンソール/オペレーション一覧/オペレーション名', DESCRIPTION_EN = '[Original data]
Basic Console/Operation list/operation name', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010803';

UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '[元データ]
Ansible共通/機器一覧/ホスト名', DESCRIPTION_EN = '[Original data]
Ansible Common/Device list/Host name', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010810';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '[元データ]
Ansible共通/機器一覧/ホスト名', DESCRIPTION_EN = '[Original data]
Ansible Common/Device list/Host name', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010810';

UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '[元データ]
パラメータシート(入力用)/パラメータシート名(ja)', DESCRIPTION_EN = '[Original data]
Parameter sheet(Input)/Parameter sheet name (ja)', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010811';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '[元データ]
パラメータシート(入力用)/パラメータシート名(ja)', DESCRIPTION_EN = '[Original data]
Parameter sheet(Input)/Parameter sheet name (ja)', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010811';

UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '[元データ]
パラメータシート(入力用)/パラメータシート名(rest)', DESCRIPTION_EN = '[Original data]
Parameter sheet(Input)/parameter sheet name (rest)', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010812';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '[元データ]
パラメータシート(入力用)/パラメータシート名(rest)', DESCRIPTION_EN = '[Original data]
Parameter sheet(Input)/parameter sheet name (rest)', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010812';


UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '[最大長]255バイト
どのルールから作成された結論イベントなのかを、恒久的に判別するため"_exastro_rule_name"ラベルに設定する任意の名前を入力します。
※編集不可', DESCRIPTION_EN = '[Maximum length] 255 bytes
Enter any name you want to set in the "_exastro_rule_name" label to permanently identify which rule the conclusion event was created from.
* Unable to edit', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010904';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '[最大長]255バイト
どのルールから作成された結論イベントなのかを、恒久的に判別するため"_exastro_rule_name"ラベルに設定する任意の名前を入力します。
※編集不可', DESCRIPTION_EN = '[Maximum length] 255 bytes
Enter any name you want to set in the "_exastro_rule_name" label to permanently identify which rule the conclusion event was created from.
* Unable to edit', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010904';

UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '[元データ]
OASE/ルール/フィルター/フィルタID', DESCRIPTION_EN = '[Original data]
OASE/Rule/Filter/Filter Id', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010906';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '[元データ]
OASE/ルール/フィルター/フィルタID', DESCRIPTION_EN = '[Original data]
OASE/Rule/Filter/Filter Id', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010906';

UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '[元データ]
OASE/ルール/フィルター/フィルタID', DESCRIPTION_EN = '[Original data]
OASE/Rule/Filter/Filter Id', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010908';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '[元データ]
OASE/ルール/フィルター/フィルタID', DESCRIPTION_EN = '[Original data]
OASE/Rule/Filter/Filter Id', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010908';

UPDATE T_COMN_MENU_COLUMN_LINK SET COLUMN_NAME_JA = 'アクション名', COLUMN_NAME_EN = 'Action Name', DESCRIPTION_JA = '[元データ]
OASE/アクション/アクション名', DESCRIPTION_EN = '[Original data]
OASE/Action/Action name', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010912';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET COLUMN_NAME_JA = 'アクション名', COLUMN_NAME_EN = 'Action Name', DESCRIPTION_JA = '[元データ]
OASE/アクション/アクション名', DESCRIPTION_EN = '[Original data]
OASE/Action/Action name', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010912';

UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '[元データ]
OASE/ルール/ルールID', DESCRIPTION_EN = '[Original data]
OASE/Rule/Rule ID', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011002';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '[元データ]
OASE/ルール/ルールID', DESCRIPTION_EN = '[Original data]
OASE/Rule/Rule ID', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011002';

UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '[元データ]
OASE/ルール/ルール名', DESCRIPTION_EN = '[Original data]
OASE/Rule/Rule Name', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011003';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '[元データ]
OASE/ルール/ルール名', DESCRIPTION_EN = '[Original data]
OASE/Rule/Rule Name', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011003';

UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '[元データ]
OASE/アクション/アクションID', DESCRIPTION_EN = '[Original data]
OASE/Action/Action ID', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011005';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '[元データ]
OASE/アクション/アクションID', DESCRIPTION_EN = '[Original data]
OASE/Action/Action ID', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011005';

UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '[元データ]
OASE/アクション/アクション名', DESCRIPTION_EN = '[Original data]
OASE/Action/Action name', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011006';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '[元データ]
OASE/アクション/アクション名', DESCRIPTION_EN = '[Original data]
OASE/Action/Action name', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011006';

UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '[元データ]
Conductor/Conductor作業履歴/ConductorインスタンスID', DESCRIPTION_EN = '[Original data]
Conductor/Conductor history/Conductor instance ID', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011007';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '[元データ]
Conductor/Conductor作業履歴/ConductorインスタンスID', DESCRIPTION_EN = '[Original data]
Conductor/Conductor history/Conductor instance ID', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011007';

UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '[元データ]
Conductor/Conductor作業履歴/Conductor名称', DESCRIPTION_EN = '[Original data]
Conductor/Conductor history/Conductor name', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011009';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '[元データ]
Conductor/Conductor作業履歴/Conductor名称', DESCRIPTION_EN = '[Original data]
Conductor/Conductor history/Conductor name', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011009';

UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '[元データ]
基本コンソール/オペレーション一覧/オペレーションID', DESCRIPTION_EN = '[Original data]
Basic Console/Operation list/Operation id', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011010';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '[元データ]
基本コンソール/オペレーション一覧/オペレーションID', DESCRIPTION_EN = '[Original data]
Basic Console/Operation list/Operation id', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011010';

UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '[元データ]
基本コンソール/オペレーション一覧/オペレーション名', DESCRIPTION_EN = '[Original data]
Basic Console/Operation list/Operation name', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011011';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '[元データ]
基本コンソール/オペレーション一覧/オペレーション名', DESCRIPTION_EN = '[Original data]
Basic Console/Operation list/Operation name', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011011';

UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '[元データ]
Ansible共通/機器一覧/管理システム項番', DESCRIPTION_EN = '[Original data]
Ansible Common/Device list/Management system item number', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011019';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '[元データ]
Ansible共通/機器一覧/管理システム項番', DESCRIPTION_EN = '[Original data]
Ansible Common/Device list/Management system item number', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011019';

UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '[元データ]
Ansible共通/機器一覧/ホスト名', DESCRIPTION_EN = '[Original data]
Ansible Common/Device list/Host name', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011020';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '[元データ]
Ansible共通/機器一覧/ホスト名', DESCRIPTION_EN = '[Original data]
Ansible Common/Device list/Host name', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011020';

UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '[元データ]
パラメータシート定義一覧/UUID', DESCRIPTION_EN = '[Original data]
Parameter sheet definition list/UUID', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011021';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '[元データ]
パラメータシート定義一覧/UUID', DESCRIPTION_EN = '[Original data]
Parameter sheet definition list/UUID', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011021';

UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '[元データ]
パラメータシート定義一覧/パラメータシート名(ja)', DESCRIPTION_EN = '[Original data]
Parameter sheet definition list/Parameter sheet name (ja)', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011022';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '[元データ]
パラメータシート定義一覧/パラメータシート名(ja)', DESCRIPTION_EN = '[Original data]
Parameter sheet definition list/Parameter sheet name (ja)', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011022';

UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '[元データ]
パラメータシート定義一覧/パラメータシート名(rest)', DESCRIPTION_EN = '[Original data]
Parameter sheet definition list/Parameter sheet name (rest)', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011023';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '[元データ]
パラメータシート定義一覧/パラメータシート名(rest)', DESCRIPTION_EN = '[Original data]
Parameter sheet definition list/Parameter sheet name (rest)', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11011023';

UPDATE T_COMN_MENU_COLUMN_LINK SET VALIDATE_OPTION = NULL, LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010203';
UPDATE T_COMN_MENU_COLUMN_LINK SET VALIDATE_OPTION = NULL, LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010909';
UPDATE T_COMN_MENU_COLUMN_LINK SET VALIDATE_OPTION = NULL, LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010913';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET VALIDATE_OPTION = NULL, LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010203';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET VALIDATE_OPTION = NULL, LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010909';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET VALIDATE_OPTION = NULL, LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '11010913';


-- ------------------------------------------------------------
-- T_COMN_MENU: UPDATE
-- ------------------------------------------------------------
UPDATE T_COMN_MENU SET WEB_PRINT_LIMIT = 10000, WEB_PRINT_CONFIRM = 1000 WHERE MENU_ID IN ('110101','110102','110103','110104','110105','110106','110107','110108','110109','110110');
UPDATE T_COMN_MENU_JNL SET WEB_PRINT_LIMIT = 10000, WEB_PRINT_CONFIRM = 1000 WHERE MENU_ID IN ('110101','110102','110103','110104','110105','110106','110107','110108','110109','110110');
UPDATE T_COMN_MENU SET INITIAL_FILTER_FLG = 1 WHERE MENU_ID IN ('110101','110102','110105','110106','110107','110108','110109');
UPDATE T_COMN_MENU_JNL SET INITIAL_FILTER_FLG = 1 WHERE MENU_ID IN ('110101','110102','110105','110106','110107','110108','110109');

UPDATE T_COMN_MENU SET MENU_NAME_JA = 'イベント収集', MENU_NAME_EN = 'Event collection', MENU_NAME_REST = 'event_collection', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID = '110101';
UPDATE T_COMN_MENU_JNL SET MENU_NAME_JA = 'イベント収集', MENU_NAME_EN = 'Event collection', MENU_NAME_REST = 'event_collection', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID = '110101';