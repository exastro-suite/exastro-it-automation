import pprint
import json
import copy
from common_libs.conductor.classes.util import ConductorCommonLibs

from flask import g


def conductor_class_validate(objdbca, objtable, option):

    retBool = True
    msg = ''
    try:
        """
        # 動確試験用（1系項目削除、変換処理 暫定対応）
        option = convert_conductor_ver_1(option)

        target_rest_name = 'setting'
        entry_parameter = option.get('entry_parameter')
        tmp_parameter = entry_parameter.get('parameter')
        conductor_data = json.loads(tmp_parameter.get(target_rest_name))
        
        cclibs = ConductorCommonLibs()
        result = cclibs.chk_format_all(copy.deepcopy(conductor_data))
        if result[0] is False:
            status_code = '499-00201'
            msg_args = ["{}".format(result)]
            msg = g.appmsg.get_api_message(status_code, msg_args)
            retBool = result[0]
        else:
            copy.deepcopy(conductor_data)
            result = cclibs.override_node_idlink(copy.deepcopy(conductor_data))
            if result[0] is False:
                status_code = '499-00201'
                msg_args = ["{}".format(result)]
                msg = g.appmsg.get_api_message(status_code, msg_args)
                retBool = result[0]
            conductor_data = result[1]
            conductor_data['conductor']['id'] = entry_parameter.get('parameter').get('conductor_class_id')
            option['entry_parameter']['parameter'][target_rest_name] = json.dumps(conductor_data)
        """
        pass
    except Exception:
        retBool = False

    return retBool, msg, option,


def convert_conductor_ver_1(option):
    config_var = '2'
    target_rest_name = 'setting'
    entry_parameter = option.get('entry_parameter')
    tmp_parameter = entry_parameter.get('parameter')
    tmp_setting = tmp_parameter.get(target_rest_name)
    if tmp_setting is not None:
        json_setting = json.loads(tmp_setting)
        if 'id' in json_setting['conductor']:
            config_var = '1'
        if 'ACCESS_AUTH' in json_setting['conductor']:
            config_var = '1'
        if 'NOTICE_INFO' in json_setting['conductor']:
            config_var = '1'
        if config_var == '1':
            tmp_setting = tmp_setting.replace("LUT4U", "last_update_date_time")
            tmp_setting = tmp_setting.replace("SKIP_FLAG", "skip_flag")
            tmp_setting = tmp_setting.replace("CALL_CONDUCTOR_ID", "call_conductor_id")
            tmp_setting = tmp_setting.replace("CONDUCTOR_NAME", "call_conductor_name")
            tmp_setting = tmp_setting.replace("OPERATION_NO_IDBH", "operation_id")
            tmp_setting = tmp_setting.replace("PATTERN_ID", "movement_id")
            tmp_setting = tmp_setting.replace("OPERATION_NO_IDBH", "operation_id")
            tmp_setting = tmp_setting.replace("ORCHESTRATOR_ID", "orchestra_id")
            tmp_setting = tmp_setting.replace("CONDUCTOR_NAME", "Name")
            tmp_setting = tmp_setting.replace("OPERATION_NAME", "operation_name")
            tmp_setting = tmp_setting.replace("END_TYPE", "end_type")
            # tmp_setting = tmp_setting.replace("egde", "edge")
            
            json_setting = json.loads(tmp_setting)
            if 'id' in json_setting['conductor']:
                json_setting['conductor']['id'] = None
            if 'ACCESS_AUTH' in json_setting['conductor']:
                del json_setting['conductor']['ACCESS_AUTH']
            if 'NOTICE_INFO' in json_setting['conductor']:
                del json_setting['conductor']['NOTICE_INFO']
            for ckey in json_setting.keys():
                carr = json_setting.get(ckey)
                n_type = carr.get('type')
                n_name_val = carr.get('Name')
                if n_type == 'movement':
                    del json_setting[ckey]['Name']
                    json_setting[ckey]['movement_name'] = n_name_val
                if n_type == 'end':
                    end_type = json_setting[ckey]['end_type']
                    if end_type is None:
                        json_setting[ckey]['end_type'] = "6"
                    elif end_type == "5":
                        json_setting[ckey]['end_type'] = "6"
                    elif end_type == "11":
                        json_setting[ckey]['end_type'] = "8"
                    elif end_type == "7":
                        json_setting[ckey]['end_type'] = "7"
        tmp_setting = json.dumps(json_setting, ensure_ascii=False)
    option['entry_parameter']['parameter']['setting'] = tmp_setting
    # pprint.pprint(option)
    return option
