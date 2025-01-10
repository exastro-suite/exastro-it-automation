UPDATE T_COMN_MENU_COLUMN_LINK      SET VALIDATE_OPTION = '{
"int_min": 1,
"int_max": 65536
}', DESCRIPTION_JA = '最大バイト数を入力します。
[最大長]65536バイト
半角英数字なら文字数分となります。
全角文字ならば文字数×３＋２バイト必要になります。', DESCRIPTION_EN = 'Enter the maximum number of bytes.
Total number of bytes (65536).
For single byte alphanumeric characters, the required bytes will be equal to the number of characters.
For double byte characters, the number of characters multiplied by 3, plus 2 bytes will be required.'   WHERE COLUMN_DEFINITION_ID = '5010413';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL  SET VALIDATE_OPTION = '{
"int_min": 1,
"int_max": 65536
}', DESCRIPTION_JA = '最大バイト数を入力します。
[最大長]65536バイト
半角英数字なら文字数分となります。
全角文字ならば文字数×３＋２バイト必要になります。', DESCRIPTION_EN = 'Enter the maximum number of bytes.
Total number of bytes (65536).
For single byte alphanumeric characters, the required bytes will be equal to the number of characters.
For double byte characters, the number of characters multiplied by 3, plus 2 bytes will be required.'   WHERE COLUMN_DEFINITION_ID = '5010413';
UPDATE T_COMN_MENU_COLUMN_LINK      SET VALIDATE_OPTION = '{
"min_length": 0,
"max_length": 65536
}'  WHERE COLUMN_DEFINITION_ID = '5010415';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL  SET VALIDATE_OPTION = '{
"min_length": 0,
"max_length": 65536
}'  WHERE COLUMN_DEFINITION_ID = '5010415';

UPDATE T_COMN_MENU_COLUMN_LINK      SET VALIDATE_OPTION = '{
"int_min": 1,
"int_max": 65536
}', DESCRIPTION_JA = '最大バイト数を入力します。
[最大長]65536バイト
半角英数字なら文字数分となります。
全角文字ならば文字数×３＋２バイト必要になります。', DESCRIPTION_EN = 'Enter the maximum number of bytes.
Total number of bytes (65536).
For single byte alphanumeric characters, the required bytes will be equal to the number of characters.
For double byte characters, the number of characters multiplied by 3, plus 2 bytes will be required.'   WHERE COLUMN_DEFINITION_ID = '5010416';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL  SET VALIDATE_OPTION = '{
"int_min": 1,
"int_max": 65536
}', DESCRIPTION_JA = '最大バイト数を入力します。
[最大長]65536バイト
半角英数字なら文字数分となります。
全角文字ならば文字数×３＋２バイト必要になります。', DESCRIPTION_EN = 'Enter the maximum number of bytes.
Total number of bytes (65536).
For single byte alphanumeric characters, the required bytes will be equal to the number of characters.
For double byte characters, the number of characters multiplied by 3, plus 2 bytes will be required.'   WHERE COLUMN_DEFINITION_ID = '5010416';
UPDATE T_COMN_MENU_COLUMN_LINK      SET VALIDATE_OPTION = '{
"min_length": 0,
"max_length": 65536
}'  WHERE COLUMN_DEFINITION_ID = '5010418';
UPDATE T_COMN_MENU_COLUMN_LINK_JNL  SET VALIDATE_OPTION = '{
"min_length": 0,
"max_length": 65536
}'  WHERE COLUMN_DEFINITION_ID = '5010418';