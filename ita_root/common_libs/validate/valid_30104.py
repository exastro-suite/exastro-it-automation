import pprint
import json
import copy

from common_libs.conductor.classes.util import ConductorCommonLibs

from flask import g


def conductor_class_validate(objdbca, objtable, option):

    retBool = True
    msg = ''
    try:
        target_rest_name = 'setting'
        entry_parameter = option.get('entry_parameter')
        tmp_parameter = entry_parameter.get('parameter')
        conductor_data = json.loads(tmp_parameter.get(target_rest_name))
        conductor_name = tmp_parameter.get('conductor_name')
        cclibs = ConductorCommonLibs(cmd_type=option.get('cmd_type'))
        result = cclibs.chk_format_all(copy.deepcopy(conductor_data))
        if result[0] is False:
            status_code = '499-00201'
            msg_args = ["{}".format(result[2])]
            msg = g.appmsg.get_api_message(status_code, msg_args)
            retBool = result[0]
        else:
            pass
            # """
            result = cclibs.override_node_idlink(copy.deepcopy(conductor_data))
            if result[0] is False:
                status_code = '499-00201'
                msg_args = ["{}".format(result[2])]
                msg = g.appmsg.get_api_message(status_code, msg_args)
                retBool = result[0]
            else:
                conductor_data = result[1]
                conductor_data['conductor']['id'] = entry_parameter.get('parameter').get('conductor_class_id')
                conductor_data['conductor']['conductor_name'] = conductor_name
                option['entry_parameter']['parameter'][target_rest_name] = json.dumps(conductor_data)
                
            # """
        # """
        pass
    except Exception:
        retBool = False

    return retBool, msg, option,

