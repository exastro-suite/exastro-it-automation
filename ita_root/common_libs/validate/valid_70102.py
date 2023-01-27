import pprint
import json
import copy

from flask import g

from common_libs.hostgroup.classes.hostgroup_table_class import *

HIERARCHY_LIMIT = 15


def check_loop(objdbca, objtable, option):

    retBool = True
    msg = ''
    try:

        # get option data
        cmd_type = option.get('cmd_type')

        # Register / Update / Restore
        if cmd_type != "Discard":
            # check target host group
            entry_parameter = option.get('entry_parameter')
            checkhgc = entry_parameter.get('parameter').get('hostgroup_child')
            paHg = entry_parameter.get('parameter').get('hostgroup_parent')

            # SQL:SELECT
            objhgpc = HostLinkListTable(objdbca)
            sql = objhgpc.create_sselect("WHERE DISUSE_FLAG = '0'")
            hostgroup_pc_list = objhgpc.execQuery(sql)

            menu_names = objhgpc.get_menu_names()

            # check host group parent child loop
            for target_hostgroup_pc in hostgroup_pc_list:
                # call loop check
                loopCnt = 0
                loop_flg = loopCheck(hostgroup_pc_list, checkhgc, paHg, loopCnt)
                # loop
                if loop_flg is True:
                    retBool = False
                    msg = g.appmsg.get_api_message("MSG-70001", [])
                    raise Exception()
                elif loop_flg is False:
                    pass
    except Exception:
        retBool = False

    return retBool, msg, option,


def loopCheck(hostgroup_pc_list, checkHg, paHg, loopCnt):
    """
        loopCheck
    Args:
        hostgroup_pc_list (list): _description_
        checkHg (uuid): hostg
        paHg (uuid): _description_
        loopCnt (int): _description_
    Returns:
        bool: _description_
    """
    if checkHg == paHg:
        return True
    else:
        for target_hostgroup_pc in hostgroup_pc_list:
            if target_hostgroup_pc['CH_HOSTGROUP'] == paHg:
                if target_hostgroup_pc['PA_HOSTGROUP'] == checkHg:
                    return True
                loopCnt += 1
                if HIERARCHY_LIMIT < loopCnt:
                    return False
                if "" != target_hostgroup_pc['PA_HOSTGROUP']:
                    result = loopCheck(hostgroup_pc_list, checkHg, target_hostgroup_pc['PA_HOSTGROUP'], loopCnt)
                    if result is True:
                        return True
    return False
