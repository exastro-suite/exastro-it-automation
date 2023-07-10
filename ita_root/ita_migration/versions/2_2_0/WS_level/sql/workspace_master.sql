-- UPDATE: -2.2.0
    -- T_COMN_MENU_COLUMN_LINK: UPDATE
    -- T_COMN_DEL_OPERATION_LIST: UPDATE

UPDATE T_COMN_DEL_OPERATION_LIST SET DATA_STORAGE_PATH = "/driver/ansible/legacy_role",LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE ROW_ID = "9";

UPDATE T_COMN_MENU_COLUMN_LINK   SET DESCRIPTION_JA = "データストレージパス(省略可能)
データストレージパスで管理しているファイルがある場合、そのパスを入力します。
/storage/<<organization>>/<<workspace>>/配下のパスの場合は、/storage/<<organization>>/<<workspace>>からの相対パスを記載します。
exp)
 Ansible Legacy
   /driver/ansible/legacy
 Ansible pioneer
   /driver/ansible/pioneer",LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = "1010505";

UPDATE T_COMN_MENU_COLUMN_LINK   SET DESCRIPTION_EN = "Data storage path (Can be abbreviated)
If there are files that are managed in a Data storage path, input said path.For paths under /storage/<<organization>>/<<workspace>>/, input a relative path from /storage/<<organization>>/<<workspace>>. 
exp)
  Ansible Legacy
    /driver/ansible/legacyAnsible
  pioneer
    /driver/ansible/pioneer",LAST_UPDATE_TIMESTAMP = _____DATE_____ WHERE COLUMN_DEFINITION_ID = "1010505";

