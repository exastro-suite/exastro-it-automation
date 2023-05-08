# Copyright 2023 NEC Corporation#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from flask import g  # noqa: F401

from common_libs.hostgroup.classes.hostgroup_table_class import *  # noqa: F403
from common_libs.hostgroup.functions.split_function import *  # noqa: F403
from common_libs.hostgroup.classes.hostgroup_const import *  # noqa: F403


hostgroup_const = hostGroupConst()  # noqa: F405


def check_loop(objdbca, objtable, option):

    retBool = True
    msg = ''
    try:

        # get option data
        cmd_type = option.get('cmd_type')

        # Register / Update / Restore
        if cmd_type != "Discard":
            # Register, Update use entry_parameter / Restore use current_parameter
            if cmd_type == "Restore":
                current_parameter = option.get('current_parameter')
                checkhgc = current_parameter.get('parameter').get('hostgroup_child')
                paHg = current_parameter.get('parameter').get('hostgroup_parent')
            else:
                entry_parameter = option.get('entry_parameter')
                checkhgc = entry_parameter.get('parameter').get('hostgroup_child')
                paHg = entry_parameter.get('parameter').get('hostgroup_parent')

            # check host group parent == child
            if checkhgc == paHg:
                retBool = False
                msg = g.appmsg.get_api_message("MSG-70001", [])
                raise Exception()

            # check host group parent child loop: parameter
            # SQL:SELECT
            objhgpc = HostLinkListTable(objdbca)  # noqa: F405
            sql = objhgpc.create_sselect("WHERE DISUSE_FLAG = '0'")
            hostgroup_pc_list = objhgpc.exec_query(sql)
            for target_hostgroup_pc in hostgroup_pc_list:
                # call loop check
                loopCnt = 0
                loop_flg, loopCnt = loopCheck(hostgroup_pc_list, checkhgc, paHg, loopCnt)
                # loop
                if loop_flg is True:
                    retBool = False
                    msg = g.appmsg.get_api_message("MSG-70001", [])
                    raise Exception()
                elif loop_flg is False:
                    pass

            # check host group parent child loop: all parent-child data
            # SQL:SELECT
            objhgpc = HostLinkListTable(objdbca)  # noqa: F405
            sql = objhgpc.create_sselect("WHERE DISUSE_FLAG = '0'")
            hostgroup_pc_list = objhgpc.exec_query(sql)
            for target_hostgroup in hostgroup_pc_list:
                checkhgc = target_hostgroup.get("CH_HOSTGROUP")
                paHg = target_hostgroup.get("PA_HOSTGROUP")
                for target_hostgroup_pc in hostgroup_pc_list:
                    # call loop check
                    loopCnt = 0
                    loop_flg, loopCnt = loopCheck(hostgroup_pc_list, checkhgc, paHg, loopCnt)
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
                    return True, loopCnt,
                loopCnt += 1
                if hostgroup_const.HIERARCHY_LIMIT < loopCnt:
                    return True, loopCnt,
                if "" != target_hostgroup_pc['PA_HOSTGROUP']:
                    result, loopCnt = loopCheck(hostgroup_pc_list, checkHg, target_hostgroup_pc['PA_HOSTGROUP'], loopCnt)
                    if result is True:
                        return True, loopCnt,
    return False, loopCnt,


def external_valid_menu_after(objdbca, objtable, option):
    retBool = True
    msg = ''

    # ホストグループ分割対象を全てのDIVIDED_FLG=0にする
    result = reset_split_target_flg(objdbca)  # noqa: F405
    if result is False:
        raise Exception()

    return retBool, msg, option, False
