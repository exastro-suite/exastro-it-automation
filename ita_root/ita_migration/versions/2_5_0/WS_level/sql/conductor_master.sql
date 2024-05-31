-- INSERT/UPDATE: 2.5.0
    -- T_COMN_MENU : UPDATE
    -- T_COMN_MENU_TABLE_LINK : UPDATE
    -- T_COMN_MENU_COLUMN_LINK: UPDATE

-- T_COMN_MENU : UPDATE
UPDATE T_COMN_MENU SET SORT_KEY = '[{"ASC":"notice_name"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='30102';
UPDATE T_COMN_MENU_JNL SET SORT_KEY = '[{"ASC":"notice_name"}]', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID ='30102';

UPDATE T_COMN_MENU SET MENU_NAME_JA = 'Conductor作業履歴', MENU_NAME_EN = 'Conductor history', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE MENU_ID='30105';
UPDATE T_COMN_MENU_JNL SET MENU_NAME_JA = 'Conductor作業履歴', MENU_NAME_EN = 'Conductor history', LAST_UPDATE_TIMESTAMP = _____DATE_____        WHERE MENU_ID='30105';

-- T_COMN_MENU_TABLE_LINK : UPDATE
UPDATE T_COMN_MENU_TABLE_LINK SET MENU_INFO_JA = 'Conductorで作業時に実行される通知に関する定義を設定します。
通知はWebhookを利用して行います。

各種設定項目について：
   - 通知先URL：通知先のURLを入力してください。
   - ヘッダー：httpヘッダーフィールドをJson形式で入力してください。
   - メッセージ：通知先サービスの仕様に従い、通知内容を入力してください。
   - PROXY URL：PROXYの設定が必要な場合、URLを入力してください。
   - PROXY PORT：PROXYの設定が必要な場合、PORTを入力してください。
   - 作業確認URL：作業確認用URLの予約変数で使用する,FQDNを入力してください。

Microsoft Teams/Slackでの設定例：
   - 通知先URL：各サービスのWebhook URLを入力します。
   - ヘッダー：{ "Content-Type": "application/json" }
   - メッセージ：{"text": "通知名：__NOTICE_NAME__, <br>Conductor名称: __CONDUCTOR_NAME__, <br> ConductorインスタンスID:__CONDUCTOR_INSTANCE_ID__,<br> ステータス: __STATUS_ID__, <br> 作業URL: __JUMP_URL__, <br> "}
   ※メッセージの入力形式、改行の表記方法については、各サービスのWebhookによるメッセージの送信についてご参照ください。

以下はメッセージ内で利用できる変数となります。
Conductor作業履歴の情報を指定することができます。
    __CONDUCTOR_INSTANCE_ID__:  ConductorインスタンスID
    __CONDUCTOR_NAME__:  Conductor名称
    __STATUS_ID__:  ステータスID
    __OPERATION_ID__:  オペレーションID
    __OPERATION_NAME__:  実行時のオペレーション名
    __EXECUTION_USER__:  作業実行ユーザー
    __PARENT_CONDUCTOR_INSTANCE_ID__:  親ConductorインスタンスID
    __PARENT_CONDUCTOR_NAME__:  親Conductor名称
    __TOP_CONDUCTOR_INSTANCE_ID__:  最上位ConductorインスタンスID
    __TOP_CONDUCTOR_NAME__:  最上位Conductor名称
    __ABORT_EXECUTE_FLAG__:  緊急停止フラグ
    __REGISTER_TIME__:  登録日時
    __TIME_BOOK__:  予約日時
    __TIME_START__:  開始日時
    __TIME_END__:  終了日時
    __NOTICE_NAME__:  通知ログ
    __NOTE__:  備考
    __JUMP_URL__:  Conductor作業確認画面のURL(作業確認URLを使用)

ステータスIDに対応するステータス名は以下となります。
   - 3：実行中
   - 4：実行中（遅延）
   - 5：一時停止
   - 6：正常終了
   - 7：異常終了
   - 8：警告終了
   - 9：緊急停止
   - 10：予約取消
   - 11：想定外エラー', MENU_INFO_EN = 'You can set definition for notification performed in Conductor.
Notification is sent using Webhook.

About setting items:
   - Notice URL: Enter the URL of the notification destination.
   - Header: Enter the http header field in Json format.
   - Message: Enter the content of the notification according to the specifications of the service to be notified.
   - PROXY URL: If PROXY settings are required, enter the URL.
   - PROXY PORT：If PROXY settings are required, enter the PORT.
   - Confirmation URL: Enter the FQDN to be used in the ITA variable for the Confirmation URL.

Example configuration in Microsoft Teams/Slack:
   - Notice URL: Enter the Webhook URL for each service.
   - Header: { "Content-Type": "application/json" }
   - Message: {"text": "Notice Name：__NOTICE_NAME__, <br>Conductor Name: __CONDUCTOR_NAME__, <br> Conductor Instance ID:__CONDUCTOR_INSTANCE_ID__,<br> Status ID: __STATUS_ID__, <br> Confirmation URL: __JUMP_URL__, <br> "}
   * For information on message input format and line break notation, please refer to each service.

ITA variables that can be used in the message:
You can specify information for the Conductor history.
    __CONDUCTOR_INSTANCE_ID__: Conductor instance ID
    __CONDUCTOR_NAME__: Conductor name
    __STATUS_ID__: Status ID
    __OPERATION_ID__: Operation ID
    __OPERATION_NAME__: Operation name
    __EXECUTION_USER__: Execution user
    __PARENT_CONDUCTOR_INSTANCE_ID__: Parent Conductor instance ID
    __PARENT_CONDUCTOR_NAME__: Parent Conductor name
    __TOP_CONDUCTOR_INSTANCE_ID__: Top Conductor instance ID
    __TOP_CONDUCTOR_NAME__: Top Conductor Name
    __ABORT_EXECUTE_FLAG__: Abort execute flag
    __REGISTER_TIME__: Time Register
    __TIME_BOOK__: Time book
    __TIME_START__: Time start
    __TIME_END__: Time end
    __NOTICE_NAME__: Notification log
    __NOTE__: Remarks
    __JUMP_URL__: URL of the Conductor confirmation (use the enterd Confirmation URL)

The status name corresponding to the status ID is as follows:
   - 3: Executing
   - 4: Executing (delayed)
   - 5: Pause
   - 6: Normal end
   - 7: Abend
   - 8: Warning end
   - 9: Emergency stop
   - 10: Schedule Cancellation
   - 11: Unexpected error', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE TABLE_DEFINITION_ID = '30102';
UPDATE T_COMN_MENU_TABLE_LINK_JNL SET MENU_INFO_JA = 'Conductorで作業時に実行される通知に関する定義を設定します。
通知はWebhookを利用して行います。

各種設定項目について：
   - 通知先URL：通知先のURLを入力してください。
   - ヘッダー：httpヘッダーフィールドをJson形式で入力してください。
   - メッセージ：通知先サービスの仕様に従い、通知内容を入力してください。
   - PROXY URL：PROXYの設定が必要な場合、URLを入力してください。
   - PROXY PORT：PROXYの設定が必要な場合、PORTを入力してください。
   - 作業確認URL：作業確認用URLの予約変数で使用する,FQDNを入力してください。

Microsoft Teams/Slackでの設定例：
   - 通知先URL：各サービスのWebhook URLを入力します。
   - ヘッダー：{ "Content-Type": "application/json" }
   - メッセージ：{"text": "通知名：__NOTICE_NAME__, <br>Conductor名称: __CONDUCTOR_NAME__, <br> ConductorインスタンスID:__CONDUCTOR_INSTANCE_ID__,<br> ステータス: __STATUS_ID__, <br> 作業URL: __JUMP_URL__, <br> "}
   ※メッセージの入力形式、改行の表記方法については、各サービスのWebhookによるメッセージの送信についてご参照ください。

以下はメッセージ内で利用できる変数となります。
Conductor作業履歴の情報を指定することができます。
    __CONDUCTOR_INSTANCE_ID__:  ConductorインスタンスID
    __CONDUCTOR_NAME__:  Conductor名称
    __STATUS_ID__:  ステータスID
    __OPERATION_ID__:  オペレーションID
    __OPERATION_NAME__:  実行時のオペレーション名
    __EXECUTION_USER__:  作業実行ユーザー
    __PARENT_CONDUCTOR_INSTANCE_ID__:  親ConductorインスタンスID
    __PARENT_CONDUCTOR_NAME__:  親Conductor名称
    __TOP_CONDUCTOR_INSTANCE_ID__:  最上位ConductorインスタンスID
    __TOP_CONDUCTOR_NAME__:  最上位Conductor名称
    __ABORT_EXECUTE_FLAG__:  緊急停止フラグ
    __REGISTER_TIME__:  登録日時
    __TIME_BOOK__:  予約日時
    __TIME_START__:  開始日時
    __TIME_END__:  終了日時
    __NOTICE_NAME__:  通知ログ
    __NOTE__:  備考
    __JUMP_URL__:  Conductor作業確認画面のURL(作業確認URLを使用)

ステータスIDに対応するステータス名は以下となります。
   - 3：実行中
   - 4：実行中（遅延）
   - 5：一時停止
   - 6：正常終了
   - 7：異常終了
   - 8：警告終了
   - 9：緊急停止
   - 10：予約取消
   - 11：想定外エラー', MENU_INFO_EN = 'You can set definition for notification performed in Conductor.
Notification is sent using Webhook.

About setting items:
   - Notice URL: Enter the URL of the notification destination.
   - Header: Enter the http header field in Json format.
   - Message: Enter the content of the notification according to the specifications of the service to be notified.
   - PROXY URL: If PROXY settings are required, enter the URL.
   - PROXY PORT：If PROXY settings are required, enter the PORT.
   - Confirmation URL: Enter the FQDN to be used in the ITA variable for the Confirmation URL.

Example configuration in Microsoft Teams/Slack:
   - Notice URL: Enter the Webhook URL for each service.
   - Header: { "Content-Type": "application/json" }
   - Message: {"text": "Notice Name：__NOTICE_NAME__, <br>Conductor Name: __CONDUCTOR_NAME__, <br> Conductor Instance ID:__CONDUCTOR_INSTANCE_ID__,<br> Status ID: __STATUS_ID__, <br> Confirmation URL: __JUMP_URL__, <br> "}
   * For information on message input format and line break notation, please refer to each service.

ITA variables that can be used in the message:
You can specify information for the Conductor history.
    __CONDUCTOR_INSTANCE_ID__: Conductor instance ID
    __CONDUCTOR_NAME__: Conductor name
    __STATUS_ID__: Status ID
    __OPERATION_ID__: Operation ID
    __OPERATION_NAME__: Operation name
    __EXECUTION_USER__: Execution user
    __PARENT_CONDUCTOR_INSTANCE_ID__: Parent Conductor instance ID
    __PARENT_CONDUCTOR_NAME__: Parent Conductor name
    __TOP_CONDUCTOR_INSTANCE_ID__: Top Conductor instance ID
    __TOP_CONDUCTOR_NAME__: Top Conductor Name
    __ABORT_EXECUTE_FLAG__: Abort execute flag
    __REGISTER_TIME__: Time Register
    __TIME_BOOK__: Time book
    __TIME_START__: Time start
    __TIME_END__: Time end
    __NOTICE_NAME__: Notification log
    __NOTE__: Remarks
    __JUMP_URL__: URL of the Conductor confirmation (use the enterd Confirmation URL)

The status name corresponding to the status ID is as follows:
   - 3: Executing
   - 4: Executing (delayed)
   - 5: Pause
   - 6: Normal end
   - 7: Abend
   - 8: Warning end
   - 9: Emergency stop
   - 10: Schedule Cancellation
   - 11: Unexpected error', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE TABLE_DEFINITION_ID = '30102';

UPDATE T_COMN_MENU_TABLE_LINK SET MENU_INFO_JA = 'Conductor作業履歴(実行履歴)を閲覧できます。
「詳細」を押下するとConductor作業確認メニューに遷移します。', MENU_INFO_EN = 'You can view the Conductor history (execution history).
Click Details to move to the Conductor confirmation menu.', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE TABLE_DEFINITION_ID = '30105';
UPDATE T_COMN_MENU_TABLE_LINK_JNL SET MENU_INFO_JA = 'Conductor作業履歴(実行履歴)を閲覧できます。
「詳細」を押下するとConductor作業確認メニューに遷移します。', MENU_INFO_EN = 'You can view the Conductor history (execution history).
Click Details to move to the Conductor confirmation menu.', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE TABLE_DEFINITION_ID = '30105';


-- T_COMN_MENU_COLUMN_LINK: UPDATE
UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '[元データ]Conductor作業履歴', DESCRIPTION_EN = '[Original data]Conductor history', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '3010902';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '[元データ]Conductor作業履歴', DESCRIPTION_EN = '[Original data]Conductor history', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '3010902';

UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '[元データ]Conductor作業履歴', DESCRIPTION_EN = '[Original data]Conductor history', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '3010903';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '[元データ]Conductor作業履歴', DESCRIPTION_EN = '[Original data]Conductor history', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '3010903';

UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '[元データ]Conductor作業履歴', DESCRIPTION_EN = '[Original data]Conductor history', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '3010904';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '[元データ]Conductor作業履歴', DESCRIPTION_EN = '[Original data]Conductor history', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '3010904';

UPDATE T_COMN_MENU_COLUMN_LINK SET DESCRIPTION_JA = '[元データ]Conductor作業履歴', DESCRIPTION_EN = '[Original data]Conductor history', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '3010905';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET DESCRIPTION_JA = '[元データ]Conductor作業履歴', DESCRIPTION_EN = '[Original data]Conductor history', LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = '3010905';











