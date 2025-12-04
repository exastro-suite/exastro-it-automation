-- -----------------------------------------------------------------------------
-- - ▼Issue #2814 URLの項目長を拡張
-- -----------------------------------------------------------------------------
UPDATE T_COMN_MENU_COLUMN_LINK      SET VALIDATE_OPTION = NULL, DESCRIPTION_JA = '接続先を入力します。

以下のように入力してください。
メールサーバの場合
　→ホスト名を入力。ex.example.com
APIの場合
　→URLを入力。ex.http://example.com/dir/', DESCRIPTION_EN = 'Enter the connection destination.

Please enter as below.
For mail servers
　→Enter the host name. ex.example.com
For API
　→Enter the URL. ex.http://example.com/dir/'  WHERE COLUMN_DEFINITION_ID = '11010105';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL  SET VALIDATE_OPTION = NULL, DESCRIPTION_JA = '接続先を入力します。

以下のように入力してください。
メールサーバの場合
　→ホスト名を入力。ex.example.com
APIの場合
　→URLを入力。ex.http://example.com/dir/', DESCRIPTION_EN = 'Enter the connection destination.

Please enter as below.
For mail servers
　→Enter the host name. ex.example.com
For API
　→Enter the URL. ex.http://example.com/dir/'  WHERE COLUMN_DEFINITION_ID = '11010105';
UPDATE T_COMN_MENU_COLUMN_LINK      SET VALIDATE_OPTION = NULL, DESCRIPTION_JA = 'リクエストヘッダーを入力します。', DESCRIPTION_EN = 'For API
   →Enter request header.'  WHERE COLUMN_DEFINITION_ID = '11010107';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL  SET VALIDATE_OPTION = NULL, DESCRIPTION_JA = 'リクエストヘッダーを入力します。', DESCRIPTION_EN = 'For API
   →Enter request header.'  WHERE COLUMN_DEFINITION_ID = '11010107';
UPDATE T_COMN_MENU_COLUMN_LINK      SET VALIDATE_OPTION = NULL, DESCRIPTION_JA = 'プロキシURIを入力します。', DESCRIPTION_EN = 'Enter proxy. '  WHERE COLUMN_DEFINITION_ID = '11010108';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL  SET VALIDATE_OPTION = NULL, DESCRIPTION_JA = 'プロキシURIを入力します。', DESCRIPTION_EN = 'Enter proxy. '  WHERE COLUMN_DEFINITION_ID = '11010108';
UPDATE T_COMN_MENU_COLUMN_LINK      SET VALIDATE_OPTION = NULL, DESCRIPTION_JA = 'Bearer認証の認証トークンを入力します。', DESCRIPTION_EN = 'For API
   →Enter the authentication token for Bearer authentication.'  WHERE COLUMN_DEFINITION_ID = '11010109';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL  SET VALIDATE_OPTION = NULL, DESCRIPTION_JA = 'Bearer認証の認証トークンを入力します。', DESCRIPTION_EN = 'For API
   →Enter the authentication token for Bearer authentication.'  WHERE COLUMN_DEFINITION_ID = '11010109';
UPDATE T_COMN_MENU_COLUMN_LINK      SET VALIDATE_OPTION = NULL, DESCRIPTION_JA = 'JSON形式で入力します。

・リクエストメソッドがGETの場合：
クエリパラメータ(接続先に追加される、"?"以降の値）として使用されます。
ex.
　接続先：http://example.com/dir/
　入力値：{ "name": "test" }
　の場合
　→リクエストURL：http://example.com/dir/?name=test
・リクエストメソッドがPOSTの場合：
リクエストのペイロードとして使用されます。', DESCRIPTION_EN = 'Enter in JSON format.

・If the request method is GET:
It is used as a query parameter (the value after "?" that is added to the connection destination).
ex.
Connect to: http://example.com/dir/
Input value: { "name": "test" }
 in the case of
→Request URL: http://example.com/dir/?name=test
・If the request method is POST:
Used as the payload of the request.'  WHERE COLUMN_DEFINITION_ID = '11010115';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL  SET VALIDATE_OPTION = NULL, DESCRIPTION_JA = 'JSON形式で入力します。

・リクエストメソッドがGETの場合：
クエリパラメータ(接続先に追加される、"?"以降の値）として使用されます。
ex.
　接続先：http://example.com/dir/
　入力値：{ "name": "test" }
　の場合
　→リクエストURL：http://example.com/dir/?name=test
・リクエストメソッドがPOSTの場合：
リクエストのペイロードとして使用されます。', DESCRIPTION_EN = 'Enter in JSON format.

・If the request method is GET:
It is used as a query parameter (the value after "?" that is added to the connection destination).
ex.
Connect to: http://example.com/dir/
Input value: { "name": "test" }
 in the case of
→Request URL: http://example.com/dir/?name=test
・If the request method is POST:
Used as the payload of the request.'  WHERE COLUMN_DEFINITION_ID = '11010115';
