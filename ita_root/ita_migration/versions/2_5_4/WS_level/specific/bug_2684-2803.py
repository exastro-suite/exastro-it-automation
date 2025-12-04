from flask import g


def main(work_dir_path, ws_db):
    ###########################################################
    # ansible_bug_2803
    ###########################################################
    g.applogger.info("[Trace][start] bug fix issue2684/2803")
    # トランザクション
    ws_db.db_transaction_start()

    """
        ・メニューカラム紐付にそもそも「2011107-2011110」がないなら（2011111-2011114のみがあるパターンしか考えられないので）対象外
        パターン１
            ・メニューカラム紐付でCOLUMN_DEFINITION_IDが「2011107-2011114」全て使用されている場合
        対処１
            1.COLUMN_DEFINITION_IDが「2011107-2011110」のレコードを削除
        パターン２
            ・メニューカラム紐付でCOLUMN_DEFINITION_IDが「2011107-2011110」のみ使用されている場合
        対処２
            1.COLUMN_DEFINITION_IDが「2011107-2011110」のレコードを「2011111-2011114」に更新
    """
    table_name = "T_COMN_MENU_COLUMN_LINK"
    table_name_jnl = table_name + "_JNL"
    menu_id = "20111"
    column_definition_id_list = ["2011107", "2011108", "2011109", "2011110"]

    target_record = ws_db.table_select(table_name, "WHERE `MENU_ID` = %s AND `COLUMN_DEFINITION_ID` IN %s", [menu_id, column_definition_id_list])

    if len(target_record) == 4:
        column_definition_id_list_2 = ["2011111", "2011112", "2011113", "2011114"]
        target_record_2 = ws_db.table_select(table_name, "WHERE `MENU_ID` = %s AND `COLUMN_DEFINITION_ID` IN %s", [menu_id, column_definition_id_list_2])
        if len(target_record_2) == 4:
            # パターン１
            g.applogger.info("[Trace] P1 START")
            sql = "DELETE FROM `{}` WHERE `MENU_ID` = %s AND `COLUMN_DEFINITION_ID` IN %s".format(table_name)
            g.applogger.info(f"[Trace] DELETE {column_definition_id_list}")
            ws_db.sql_execute(sql, [menu_id, column_definition_id_list])
            sql = "DELETE FROM `{}` WHERE `MENU_ID` = %s AND `JOURNAL_SEQ_NO` IN %s".format(table_name_jnl)
            g.applogger.info(f"[Trace] DELETE JNL {column_definition_id_list}")
            ws_db.sql_execute(sql, [menu_id, column_definition_id_list])

        elif len(target_record_2) == 0:
            # パターン２
            g.applogger.info("[Trace] P2 START")
            for i in range(4):
                # ex.  UPDATE T_COMN_MENU_COLUMN_LINK SET COLUMN_DEFINITION_ID = "2011111" WHERE COLUMN_DEFINITION_ID = "2011107";
                sql = "UPDATE `{}` SET COLUMN_DEFINITION_ID = %s WHERE `MENU_ID` = %s AND COLUMN_DEFINITION_ID = %s".format(table_name)
                # g.applogger.info(f"[Trace] UPDATE {column_definition_id_list[i]} -> {column_definition_id_list_2[i]}")
                ws_db.sql_execute(sql, [column_definition_id_list_2[i], menu_id, column_definition_id_list[i]])
                # ex.  UPDATE T_COMN_MENU_COLUMN_LINK_JNL SET  COLUMN_DEFINITION_ID = "2011111", JOURNAL_SEQ_NO = "2011111" WHERE JOURNAL_SEQ_NO = "2011107";
                sql = "UPDATE `{}` SET COLUMN_DEFINITION_ID = %s, JOURNAL_SEQ_NO = %s WHERE `MENU_ID` = %s AND JOURNAL_SEQ_NO = %s".format(table_name_jnl)
                # g.applogger.info(f"[Trace] UPDATE JNL {column_definition_id_list[i]} -> {column_definition_id_list_2[i]}")
                ws_db.sql_execute(sql, [column_definition_id_list_2[i], column_definition_id_list_2[i], menu_id, column_definition_id_list[i]])
        else:
            g.applogger.info("[Trace] Invalid Record Length-P")
    elif len(target_record) == 0:
        g.applogger.info("[Trace] NonTaget WS")
    else:
        g.applogger.info("[Trace] Invalid Record Length")
    # コミット
    ws_db.db_commit()

    g.applogger.info("[Trace][end] bug fix issue2684/2803")
    return 0
