import json
from common_libs.loadtable import *  # noqa: F403

from flask import g  # noqa: F401


def conductor_class_data_sync(objdbca, objtable, option):

    retBool = True
    msg = ''
    try:
        cmd_type = option.get('cmd_type')
        conductor_class_id = option.get('uuid')
        jnl_id = option.get('uuid_jnl')
        conductor_name = None
        note = None
        
        if cmd_type in ['Update', 'Restore', 'Discard']:
            try:
                current_c_name = option.get('current_parameter').get('parameter').get('conductor_name')
            except Exception:
                current_c_name = None
            try:
                entry_c_name = option.get('entry_parameter').get('parameter').get('conductor_name')
            except Exception:
                entry_c_name = None
            try:
                current_remarks = option.get('current_parameter').get('parameter').get('remarks')
            except Exception:
                current_remarks = None
            try:
                entry_remarks = option.get('entry_parameter').get('parameter').get('remarks')
            except Exception:
                entry_remarks = None
                
            if current_c_name is not None and entry_c_name is not None:
                if current_c_name != entry_c_name:
                    conductor_name = entry_c_name
                
            if current_remarks is not None and entry_remarks is not None:
                if current_remarks != entry_remarks:
                    note = entry_remarks

            if conductor_name is not None or note is not None:
                cc_menu = 'conductor_class_edit'
                objcclass = load_table.loadTable(objdbca, cc_menu)  # noqa: F405

                filter_parameter = {
                    "conductor_class_id": {"LIST": [conductor_class_id]}
                }
                tmp_result = objcclass.rest_filter(filter_parameter)
                
                if tmp_result[0] != '000-00000':
                    raise Exception()

                result_cc_filter = tmp_result[1][0]
                setting = result_cc_filter.get('parameter').get('setting')
                if conductor_name is not None:
                    setting['conductor']['conductor_name'] = conductor_name
                if note is not None:
                    setting['conductor']['note'] = note
                # 本体
                update_parameter = {
                    'CONDUCTOR_CLASS_ID': conductor_class_id,
                    'SETTING': json.dumps(setting)
                }
                objdbca.table_update('T_COMN_CONDUCTOR_CLASS', update_parameter, 'CONDUCTOR_CLASS_ID', False)
                # 履歴対応
                update_parameter = {
                    'JOURNAL_SEQ_NO': jnl_id,
                    'SETTING': json.dumps(setting)
                }
                objdbca.table_update('T_COMN_CONDUCTOR_CLASS_JNL', update_parameter, 'JOURNAL_SEQ_NO', False)

    except Exception:
        retBool = False

    return retBool, msg, option,
