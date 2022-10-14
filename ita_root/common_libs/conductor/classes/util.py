#   Copyright 2022 NEC Corporation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from flask import g
from common_libs.common.dbconnect import DBConnectWs
import re
import json
import copy


class ConductorCommonLibs():
    config_data = {}
    conductor_data = {}
    node_datas = {}
    edge_datas = {}

    _node_id_list = []

    _node_type_list = []

    _node_connect_point_condition = {
        'start': {
            'in': [],
            'out': ['movement', 'call', 'parallel-branch']
        },
        'end': {
            'in': ['movement', 'call', 'conditional-branch', 'merge', 'pause', 'status-file-branch'],
            'out': []
        },
        'call': {
            'in': ['start', 'movement', 'call', 'parallel-branch', 'conditional-branch', 'merge', 'pause', 'status-file-branch'],
            'out': ['end', 'movement', 'call', 'parallel-branch', 'conditional-branch', 'merge', 'pause', 'status-file-branch']
        },
        'movement': {
            'in': ['start', 'movement', 'call', 'parallel-branch', 'conditional-branch', 'merge', 'pause', 'status-file-branch'],
            'out': ['end', 'movement', 'call', 'parallel-branch', 'conditional-branch', 'merge', 'pause', 'status-file-branch']
        },
        'parallel-branch': {
            'in': ['start', 'movement', 'call', 'conditional-branch', 'merge', 'pause', 'status-file-branch'],
            'out': ['movement', 'call']
        },
        'conditional-branch': {
            'in': ['movement', 'call'],
            'out': ['end', 'movement', 'call', 'parallel-branch', 'pause']
        },
        'merge': {
            'in': ['movement', 'call', 'pause'],
            'out': ['end', 'movement', 'call', 'parallel-branch', 'pause']
        },
        'pause': {
            'in': ['movement', 'call', 'parallel-branch', 'merge', 'status-file-branch'],
            'out': ['end', 'movement', 'call', 'parallel-branch', 'pause']
        },
        'status-file-branch': {
            'in': ['movement', 'call'],
            'out': ['end', 'movement', 'call', 'parallel-branch', 'pause']
        },
    }

    _node_end_type_list = [6, 7, 8]

    _terminal_type_list = ['in', 'out']

    _node_status_list = []

    _orchestra_id_list = []

    _node_call_datas = {}

    _node_start_data = {}

    __db = None

    def __init__(self, wsdb_istc=None, cmd_type='Register'):
        if not wsdb_istc:
            wsdb_istc = DBConnectWs(g.get('WORKSPACE_ID'))  # noqa: F405
        self.__db = wsdb_istc

        self.cmd_type = cmd_type

        # set master list
        data_list = wsdb_istc.table_select('T_COMN_CONDUCTOR_NODE', 'WHERE `DISUSE_FLAG`=0')
        for data in data_list:
            self._node_type_list.append(data['NODE_TYPE_ID'])
        # print(self._node_type_list)

        # 正常終了、異常終了、警告終了のみ許容
        # data_list = wsdb_istc.table_select('T_COMN_CONDUCTOR_STATUS', 'WHERE `DISUSE_FLAG`=0 AND `STATUS_ID` in (6,7,8)')
        # for data in data_list:
        #     self._node_end_type_list.append(data['STATUS_ID'])
        # print(self._node_end_type_list)

        data_list = wsdb_istc.table_select('T_COMN_CONDUCTOR_NODE_STATUS', 'WHERE `DISUSE_FLAG`=0')
        for data in data_list:
            self._node_status_list.append(data['STATUS_ID'])
        ###  暫定追加
        self._node_status_list.append('__else__')
        self._node_status_list.append('9999')
        # print(self._node_status_list)

        data_list = wsdb_istc.table_select('T_COMN_ORCHESTRA', 'WHERE `DISUSE_FLAG`=0')
        for data in data_list:
            self._orchestra_id_list.append(data['ORCHESTRA_ID'])
        # print(self._orchestra_id_list)

        self.config_data = {}
        self.conductor_data = {}
        self.node_datas = {}
        self.edge_datas = {}

    def chk_format_all(self, c_all_data):
        """
        check all conductor infomation

        Arguments:
            c_data: conductor infomation(dict)
        Returns:
            (tuple)
            - retBool (bool)
            - err_code xxx-xxxxx
            - err msg args (list)
        """
        err_code = 'xxx-xxxxxx'
        err_code = '499-00201'
        tmp_c_all_data = copy.deepcopy(c_all_data)
        
        try:
            # check first block
            res_chk = self.chk_format(c_all_data)
            if res_chk[0] is False:
                return False, err_code, res_chk[1]

            # check config block
            res_chk = self.chk_config(self.config_data)
            if res_chk[0] is False:
                return False, err_code, res_chk[1]

            # check conductor block
            res_chk = self.chk_conductor(self.conductor_data)
            if res_chk[0] is False:
                return False, err_code, res_chk[1]

            # check edge block
            res_chk = self.chk_edge(self.edge_datas)
            if res_chk[0] is False:
                return False, err_code, res_chk[1]

            # check node block
            res_chk = self.chk_node(self.node_datas)
            if res_chk[0] is False:
                return False, err_code, res_chk[1]

            # check node detail
            res_chk = self.chk_node_detail(self.node_datas)
            if res_chk[0] is False:
                return False, err_code, res_chk[1]

            # check node call loop
            #  res_chk = self.chk_call_loop(self.conductor_data['id'], self._node_call_datas)
            # if res_chk[0] is False:
            #     return False, err_code, res_chk[1]

            # check node parallel
            if self.chk_type_parallel() is False:
                return False, err_code, 'condition from parallel-branch to merge is invalid'

            # chk parallel -> marge use case
            res_chk = self.chk_parallel_marge(tmp_c_all_data)
            if res_chk[0] is False:
                return False, err_code, res_chk[1]

            # check node call loop
            res_chk = self.chk_call_loop_base_1(tmp_c_all_data.get('conductor').get('id'), tmp_c_all_data)
            if res_chk[0] is False:
                return False, err_code, res_chk[1]

        except Exception:
            tmp_msg_key = g.appmsg.get_api_message('MSG-00004')
            tmp_msg = g.appmsg.get_api_message('MSG-40004')
            err_msg = json.dumps([json.dumps({tmp_msg_key: tmp_msg}, ensure_ascii=False)], ensure_ascii=False)
            return False, err_code, err_msg,

        return True,

    def chk_format(self, c_all_data):
        """
        check format

        Arguments:
            c_all_data: conductor infomation(dict)
        Returns:
            (tuple)
            - retBool (bool)
            - err msg args (list)
        """
        err_msg_args = []

        # check config
        if 'config' in c_all_data:
            if not c_all_data['config']:
                err_msg_args.append('config')
            self.config_data = c_all_data['config']
            del c_all_data['config']
        else:
            err_msg_args.append('config')

        # check conductor
        if 'conductor' in c_all_data:
            if not c_all_data['conductor']:
                err_msg_args.append('conductor')
            self.conductor_data = c_all_data['conductor']
            del c_all_data['conductor']
        else:
            err_msg_args.append('conductor')

        # check node and edge and extra
        is_exist_node = False
        is_exist_edge = False
        is_exist_extra = False
        for key, value in c_all_data.items():
            if re.fullmatch(r'node-\d{1,}', key):
                self.node_datas[key] = value
                is_exist_node = True
            elif re.fullmatch(r'line-\d{1,}', key):
                self.edge_datas[key] = value
                is_exist_edge = True
            else:
                is_exist_extra = True

        if is_exist_node is False:
            err_msg_args.append('node')
        if is_exist_edge is False:
            err_msg_args.append('edge')
        if is_exist_extra is True:
            err_msg_args.append('extra block is existed')

        if len(err_msg_args) != 0:
            msg = g.appmsg.get_api_message('MSG-40004')
            return False, msg,
            # return False, [','.join(err_msg_args)]
        else:
            return True,

    def chk_config(self, c_data):
        """
        check config block

        Arguments:
            c_data: config_data in conductor infomation(dict)
        Returns:
            (tuple)
            - retBool (bool)
            - err msg args (list)
        """
        err_msg_args = []

        if 'nodeNumber' not in c_data:
            err_msg_args.append('config.nodeNumber')
        else:
            if type(c_data['nodeNumber']) is not int:
                err_msg_args.append('config.nodeNumber')

        if 'terminalNumber' not in c_data:
            err_msg_args.append('config.terminalNumber')
        else:
            if type(c_data['terminalNumber']) is not int:
                err_msg_args.append('config.terminalNumber')

        if 'edgeNumber' not in c_data:
            err_msg_args.append('config.edgeNumber')
        else:
            if type(c_data['edgeNumber']) is not int:
                err_msg_args.append('config.edgeNumber')

        if len(err_msg_args) != 0:
            msg = g.appmsg.get_api_message('MSG-40005', [','.join(err_msg_args)])
            return False, msg,
            # return False, [','.join(err_msg_args)]
        else:
            return True,

    def chk_conductor(self, c_data):
        """
        check conductor block

        Arguments:
            c_data: conductor_data in conductor infomation(dict)
        Returns:
            (tuple)
            - retBool (bool)
            - err msg args (list)
        """
        err_msg_args = []

        if 'id' not in c_data:
            err_msg_args.append('conductor.id')
        elif c_data['id']:
            if self.cmd_type != 'Register':
                data_list = self.__db.table_select('T_COMN_CONDUCTOR_CLASS', 'WHERE `DISUSE_FLAG`=0 AND `CONDUCTOR_CLASS_ID`=%s', [c_data['id']])  # noqa E501
                if len(data_list) == 0:
                    err_msg_args.append('conductor.id not exists')

        if 'conductor_name' not in c_data:
            # err_msg_args.append('conductor.conductor_name')
            err_msg_args.append(g.appmsg.get_api_message('MSG-40006'))

        if 'note' not in c_data:
            err_msg_args.append('conductor.note')

        if 'last_update_date_time' not in c_data:
            err_msg_args.append('conductor.last_update_date_time')

        if len(err_msg_args) != 0:
            msg = g.appmsg.get_api_message('MSG-40006')
            return False, msg,
            # return False, [','.join(err_msg_args)]
        else:
            return True,

    def chk_node(self, node_datas):
        """
        check node block

        Arguments:
            node_datas: node_datas in conductor infomation(dict)
        Returns:
            (tuple)
            - retBool (bool)
            - err msg args (list)
        """
        err_msg_args = []

        for key, block_1 in node_datas.items():
            block_err_msg_args = []

            if 'id' not in block_1 or not re.fullmatch(r'node-\d{1,}', block_1['id']):
                block_err_msg_args.append('id')

            if 'type' not in block_1 or block_1['type'] not in self._node_type_list:
                block_err_msg_args.append('type')

            if 'terminal' not in block_1 or not block_1['terminal']:
                block_err_msg_args.append('terminal')
            else:
                res_chk_terminal_block = self.chk_terminal_block(block_1['terminal'])
                if res_chk_terminal_block[0] is False:
                    block_err_msg_args.append(res_chk_terminal_block[1])

            if 'x' not in block_1:
                block_err_msg_args.append('x')

            if 'y' not in block_1:
                block_err_msg_args.append('y')

            if 'w' not in block_1:
                block_err_msg_args.append('w')

            if 'h' not in block_1:
                block_err_msg_args.append('h')

            if 'note' in block_1 and block_1['note']:
                if len(block_1['note']) > 4000:
                    block_err_msg_args.append('note is too long')

            if len(block_err_msg_args) != 0:
                err_msg_args.append('{}:{}'.format(key, ','.join(block_err_msg_args)))
            else:
                # make node_id_list
                self._node_id_list.append(block_1['id'])
                # check type=start
                if block_1['type'] == 'start':
                    self._node_start_data[key] = block_1
                # extract type=call
                elif block_1['type'] == 'call':
                    self._node_call_datas[key] = block_1

        if len(err_msg_args) != 0:
            msg = g.appmsg.get_api_message('MSG-40008', [','.join(err_msg_args)])
            return False, msg,
            # return False, ['\n'.join(err_msg_args)]
        else:
            if len(self._node_start_data) != 1:
                msg = g.appmsg.get_api_message('MSG-40009')
                return False, msg,
                # return False, ['node[type=start] is duplicate']

            return True,

    def chk_terminal_block(self, terminal_blcok):
        """
        check node terminal block

        Arguments:
            node_type: node type
            terminal_blcok: terminal dict in node
        Returns:
            (tuple)
            - retBool (bool)
            - err msg (str)
        """
        err_msg_args = []

        for terminalname, terminalinfo in terminal_blcok.items():
            block_err_msg_args = []

            if 'id' not in terminalinfo or not re.fullmatch(r'terminal-\d{1,}', terminalinfo['id']):
                block_err_msg_args.append('terminal.{}.id'.format(terminalname))

            if 'type' not in terminalinfo or terminalinfo['type'] not in self._terminal_type_list:
                block_err_msg_args.append('terminal.{}.type'.format(terminalname))

            if 'targetNode' not in terminalinfo or not terminalinfo['targetNode']:
                block_err_msg_args.append('terminal.{}.targetNode'.format(terminalname))

            if 'edge' not in terminalinfo or not terminalinfo['edge']:
                block_err_msg_args.append('terminal.{}.edge'.format(terminalname))

            if 'x' not in terminalinfo:
                block_err_msg_args.append('terminal.{}.x'.format(terminalname))

            if 'y' not in terminalinfo:
                block_err_msg_args.append('terminal.{}.y'.format(terminalname))

            if len(block_err_msg_args) != 0:
                err_msg_args.append(','.join(block_err_msg_args))

        if len(err_msg_args) != 0:
            return False, g.appmsg.get_api_message('MSG-40028')
            return False, ','.join(err_msg_args)
        else:
            return True,

    def chk_node_detail(self, node_datas):
        """
        check node detail

        Arguments:
            node_datas: node_datas in conductor infomation(dict)
        Returns:
            (tuple)
            - retBool (bool)
            - err msg args (list)
        """
        err_msg_args = []
        for key, block_1 in node_datas.items():
            node_type = block_1['type']

            if node_type == 'end':
                if 'end_type' not in block_1 or int(block_1['end_type']) not in self._node_end_type_list:
                    # err_msg_args.append('{}(end_type)'.format(key))
                    tmp_msg = g.appmsg.get_api_message('MSG-40017')
                    err_msg_args.append(json.dumps({key: tmp_msg}, ensure_ascii=False))
                    continue
            elif node_type == 'movement':
                res_chk = self.chk_type_movement(block_1)
                if res_chk[0] is False:
                    # err_msg_args.append('{}({})'.format(key, res_chk[1]))
                    err_msg_args.append(json.dumps({key: res_chk[1]}, ensure_ascii=False))
                    continue
            elif node_type == 'call':
                res_chk = self.chk_type_call(block_1)
                if res_chk[0] is False:
                    # err_msg_args.append('{}({})'.format(key, res_chk[1]))
                    err_msg_args.append(json.dumps({key: res_chk[1]}, ensure_ascii=False))
                    continue

            # check node conditions
            res_chk = self.chk_node_conditions(node_type, block_1['terminal'])
            if res_chk[0] is False:
                # err_msg_args.append('{}({})'.format(key, res_chk[1]))
                err_msg_args.append(json.dumps({key: res_chk[1]}, ensure_ascii=False))
                continue

        if len(err_msg_args) != 0:
            msg = g.appmsg.get_api_message('MSG-40010', [json.dumps(err_msg_args, ensure_ascii=False)])
            return False, msg,
            # return False, ['\n'.join(err_msg_args)]
        else:
            return True,

    def chk_type_movement(self, node_blcok):
        """
        check node type=movement

        Arguments:
            node_blcok: node data
        Returns:
            (tuple)
            - retBool (bool)
            - err msg (str)
        """
        err_msg_args = []

        if 'movement_id' not in node_blcok or not node_blcok['movement_id']:
            # err_msg_args.append('movement_id')
            err_msg_args.append(g.appmsg.get_api_message('MSG-40014'))
        else:
            data_list = self.__db.table_select('T_COMN_MOVEMENT', 'WHERE `DISUSE_FLAG`=0 AND `MOVEMENT_ID`=%s', [node_blcok['movement_id']])
            if len(data_list) == 0:
                # err_msg_args.append('movement_id is not available')
                err_msg_args.append(g.appmsg.get_api_message('MSG-40014', [node_blcok.get('movement_id'), node_blcok.get('movement_name')]))
                
            # if 'movement_name' not in node_blcok:
            #    # err_msg_args.append('movement_name')
            #    err_msg_args.append(g.appmsg.get_api_message('MSG-40014', [node_blcok.get('movement_id'), node_blcok.get('movement_name')]))

        if 'skip_flag' not in node_blcok:
            # err_msg_args.append('skip_flag')
            err_msg_args.append(g.appmsg.get_api_message('MSG-40015'))

        if 'operation_id' not in node_blcok:
            # err_msg_args.append('operation_id')
            err_msg_args.append(g.appmsg.get_api_message('MSG-40016'))
        elif node_blcok['operation_id']:
            data_list = self.__db.table_select('T_COMN_OPERATION', 'WHERE `DISUSE_FLAG`=0 AND `OPERATION_ID`=%s', [node_blcok['operation_id']])
            if len(data_list) == 0:
                # err_msg_args.append('operation_id is not available')
                err_msg_args.append(g.appmsg.get_api_message('MSG-40016', [node_blcok.get('operation_id'), node_blcok.get('operation_name')]))

            # if 'operation_name' not in node_blcok:
            #    # err_msg_args.append('operation_name')
            #    err_msg_args.append(g.appmsg.get_api_message('MSG-40016', [node_blcok.get('operation_id'), node_blcok.get('operation_name')]))

        if 'orchestra_id' not in node_blcok or node_blcok['orchestra_id'] not in self._orchestra_id_list:
            # err_msg_args.append('orchestra_id')
            err_msg_args.append(g.appmsg.get_api_message('MSG-40016', [node_blcok.get('operation_id'), node_blcok.get('operation_name')]))

        if len(err_msg_args) != 0:
            return False, '\n'.join(err_msg_args)
        else:
            return True,

    def chk_type_call(self, node_blcok):
        """
        check node type=call

        Arguments:
            node_blcok: node data
        Returns:
            (tuple)
            - retBool (bool)
            - err msg (str)
        """
        err_msg_args = []

        if 'call_conductor_id' not in node_blcok or not node_blcok['call_conductor_id']:
            # err_msg_args.append('call_conductor_id')
            err_msg_args.append(g.appmsg.get_api_message('MSG-40018'))
        else:
            data_list = self.__db.table_select('T_COMN_CONDUCTOR_CLASS', 'WHERE `DISUSE_FLAG`=0 AND `CONDUCTOR_CLASS_ID`=%s', [node_blcok['call_conductor_id']])  # noqa E501
            if len(data_list) == 0:
                # err_msg_args.append('call_conductor_id is not available')
                tmp_msg = g.appmsg.get_api_message('MSG-40018', [node_blcok.get('call_conductor_id'), node_blcok.get('call_conductor_name')])
                err_msg_args.append(tmp_msg)
            if 'call_conductor_name' not in node_blcok:
                pass
                # err_msg_args.append('call_conductor_name')
                # tmp_msg = g.appmsg.get_api_message('MSG-40018', [node_blcok.get('call_conductor_id'), node_blcok.get('call_conductor_name')])
                # err_msg_args.append(tmp_msg)

        if 'skip_flag' not in node_blcok:
            # err_msg_args.append('skip_flag')
            err_msg_args.append(g.appmsg.get_api_message('MSG-40015'))

        if 'operation_id' not in node_blcok:
            # err_msg_args.append('operation_id')
            err_msg_args.append(g.appmsg.get_api_message('MSG-40016'))
        elif node_blcok['operation_id']:
            data_list = self.__db.table_select('T_COMN_OPERATION', 'WHERE `DISUSE_FLAG`=0 AND `OPERATION_ID`=%s', [node_blcok['operation_id']])
            if len(data_list) == 0:
                # err_msg_args.append('operation_id is not available')
                err_msg_args.append(g.appmsg.get_api_message('MSG-40016', [node_blcok.get('operation_id'), node_blcok.get('operation_name')]))
            if 'operation_name' not in node_blcok:
                pass
                # err_msg_args.append('operation_name')
                # err_msg_args.append(g.appmsg.get_api_message('MSG-40016', [node_blcok.get('operation_id'), node_blcok.get('operation_name')]))
                
        if len(err_msg_args) != 0:
            return False, '\n'.join(err_msg_args)
        else:
            return True,

    def chk_node_conditions(self, node_type, terminal_blcok):
        """
        check node conditions

        Arguments:
            node_type: node type
            terminal_blcok: terminal dict in node
        Returns:
            (tuple)
            - retBool (bool)
            - err msg (str)
        """
        err_msg_args = []

        if node_type in self._node_connect_point_condition:
            connect_point_condition = self._node_connect_point_condition[node_type]
        else:
            connect_point_condition = []

        for terminalname, terminalinfo in terminal_blcok.items():
            # check whether node is connected
            if terminalinfo['targetNode'] not in self._node_id_list:
                # err_msg_args.append('terminal.{}.targetNode not connected'.format(terminalname))
                tmp_msg = g.appmsg.get_api_message('MSG-40019', [terminalinfo['targetNode']])
                err_msg_args.append(tmp_msg)
                continue

            # check node connect point
            terminal_type = terminalinfo['type']
            target_node = terminalinfo['targetNode']
            target_node_type = self.node_datas[target_node]['type']
            if target_node_type not in connect_point_condition[terminal_type]:
                # err_msg_args.append('terminal.{}.target_node-connect-point is invalid'.format(terminalname))
                tmp_msg = g.appmsg.get_api_message('MSG-40020', [node_type, target_node_type])
                err_msg_args.append(tmp_msg)
                continue

        if len(err_msg_args) != 0:
            return False, ','.join(err_msg_args)

        # check 'conditional-branch' status id
        if node_type == 'conditional-branch':
            res_chk = self.chk_type_condtional_branch(terminal_blcok)

            if res_chk[0] is False:
                return False, res_chk[1]

        # check 'status-file-branch' condition
        elif node_type == 'status-file-branch':
            res_chk = self.chk_type_status_file_branch(terminal_blcok)

            if res_chk[0] is False:
                return False, res_chk[1]

        return True,

    def chk_type_condtional_branch(self, terminal_blcok):
        """
        check node type=condtional-branch

        Arguments:
            terminal_blcok: terminal dict in node
        Returns:
            (tuple)
            - retBool (bool)
            - err msg (str)
        """
        err_msg_args = []

        for terminalname, terminalinfo in terminal_blcok.items():
            if terminalinfo['type'] == 'out':
                if 'condition' not in terminalinfo or not terminalinfo['condition']:
                    # err_msg_args.append('terminal.{}.condition'.format(terminalname))
                    tmp_msg = g.appmsg.get_api_message('MSG-40021')
                    err_msg_args.append(tmp_msg)
                    continue

                is_conditon_invalid = True
                for condition in terminalinfo['condition']:
                    if condition not in self._node_status_list:
                        is_conditon_invalid = False
                        # err_msg_args.append('terminal.{}.condition'.format(terminalname))
                        tmp_msg = g.appmsg.get_api_message('MSG-40022')
                        err_msg_args.append(tmp_msg)
                        continue
                if is_conditon_invalid is False:
                    continue

        if len(err_msg_args) != 0:
            return False, ','.join(err_msg_args)
        else:
            return True,

    def chk_type_status_file_branch(self, terminal_blcok):
        """
        check node type=status-file-branch

        Arguments:
            terminal_blcok: terminal dict in node
        Returns:
            (tuple)
            - retBool (bool)
            - err msg (str)
        """
        err_msg_args = []
        condition_val_list = []
        condition_caseno_list = []

        for terminalname, terminalinfo in terminal_blcok.items():
            if terminalinfo['type'] == 'out':
                if 'case' not in terminalinfo or not terminalinfo['case']:
                    # err_msg_args.append('terminal.{}.case'.format(terminalname))
                    tmp_msg = g.appmsg.get_api_message('MSG-40023')
                    err_msg_args.append(tmp_msg)
                    continue
                elif terminalinfo['case'] == 'else':
                    continue

                if 'condition' not in terminalinfo or not terminalinfo['condition'] or not terminalinfo['condition'][0]:
                    # err_msg_args.append('terminal.{}.condition'.format(terminalname))
                    tmp_msg = g.appmsg.get_api_message('MSG-40023')
                    err_msg_args.append(tmp_msg)
                    continue

                is_conditon_invalid = True
                for condition in terminalinfo['condition']:
                    if condition not in self._node_status_list:
                        is_conditon_invalid = False
                        # err_msg_args.append('terminal.{}.condition'.format(terminalname))
                        tmp_msg = g.appmsg.get_api_message('MSG-40024', [condition])
                        err_msg_args.append(tmp_msg)
                        continue
                if is_conditon_invalid is False:
                    continue

                condtion_caseno = terminalinfo['case']
                condition_val = terminalinfo['condition'][0]

                if condtion_caseno not in condition_caseno_list:
                    condition_caseno_list.append(condtion_caseno)
                else:
                    # err_msg_args.append('terminal.{}.case is invalid'.format(terminalname))
                    tmp_msg = g.appmsg.get_api_message('MSG-40023')
                    err_msg_args.append(tmp_msg)
                    continue

                if condition_val not in condition_val_list:
                    condition_val_list.append(condition_val)
                else:
                    # err_msg_args.append('terminal.{}.condition is duplicate'.format(terminalname))
                    tmp_msg = g.appmsg.get_api_message('MSG-40025', [condition_val])
                    err_msg_args.append(tmp_msg)
                    continue

        if len(err_msg_args) != 0:
            return False, ','.join(err_msg_args)
        else:
            return True,

    def chk_type_parallel(self):
        """
        check whether contain 'conditional-branch' or 'status-file-branch' in way from parallel-branch to parallel-merge

        Arguments:
            
        Returns:
            (tuple)
            - retBool (bool)
        """
        return True

    def chk_edge(self, edge_datas):
        """
        check edge block

        Arguments:
            edge_datas: edge_datas in conductor infomation(dict)
        Returns:
            (tuple)
            - retBool (bool)
            - err msg args (list)
        """
        err_msg_args = []

        for key, block_1 in edge_datas.items():
            block_err_msg_args = []

            if 'id' not in block_1:
                block_err_msg_args.append('id')
            else:
                val = block_1['id']
                if not re.fullmatch(r'line-\d{1,}', val):
                    block_err_msg_args.append('id')

            if 'type' not in block_1:
                block_err_msg_args.append('type')
            else:
                val = block_1['type']
                if val not in ['edge', 'egde']:
                    block_err_msg_args.append('type')

            if 'inNode' not in block_1:
                block_err_msg_args.append('inNode')
            else:
                val = block_1['inNode']
                if not re.fullmatch(r'node-\d{1,}', val):
                    block_err_msg_args.append('inNode')

            if 'inTerminal' not in block_1:
                block_err_msg_args.append('inTerminal')
            else:
                val = block_1['inTerminal']
                if not re.fullmatch(r'terminal-\d{1,}', val):
                    block_err_msg_args.append('inTerminal')

            if 'outNode' not in block_1:
                block_err_msg_args.append('outNode')
            else:
                val = block_1['outNode']
                if not re.fullmatch(r'node-\d{1,}', val):
                    block_err_msg_args.append('outNode')

            if 'outTerminal' not in block_1:
                block_err_msg_args.append('outTerminal')
            else:
                val = block_1['outTerminal']
                if not re.fullmatch(r'terminal-\d{1,}', val):
                    block_err_msg_args.append('outTerminal')

            if len(block_err_msg_args) != 0:
                err_msg_args.append('{}({})'.format(key, ','.join(block_err_msg_args)))

        if len(err_msg_args) != 0:
            msg = g.appmsg.get_api_message('MSG-40007', [','.join(err_msg_args)])
            return False, msg,
            # return False, ['\n'.join(err_msg_args)]
        else:
            return True,

    def chk_call_loop(self, chk_call_conductor_id, node_call_datas):
        """
        check whether node type=call is loop recursively

        Arguments:
            chk_call_conductor_id: my conductor id
            node_call_datas: node datas type=call
        Returns:
            (tuple)
            - retBool (bool)
            - err msg args (list)
        """
        # dont check when you want to insert
        if not chk_call_conductor_id:
            return True,

        err_msg_args = []

        for key, block_1 in node_call_datas.items():
            res_chk = self._chk_call_loop_recursive(block_1['call_conductor_id'], chk_call_conductor_id)
            if res_chk[0] is False:
                err_msg_args.append('{}.{}'.format(key, res_chk[1]))

        if len(err_msg_args) != 0:
            return False, ['\n'.join(err_msg_args)]
        else:
            return True,

    def _chk_call_loop_recursive(self, call_conductor_id, chk_call_conductor_id):
        """
        check whether node type=call is loop

        Arguments:
            call_conductor_id: conductor id for target data
            chk_call_conductor_id: my conductor id
        Returns:
            (tuple)
            - retBool (bool)
            - err msg args (list)
        """
        data_list = self.__db.table_select('T_COMN_CONDUCTOR_CLASS', 'WHERE `DISUSE_FLAG`=0 AND `CONDUCTOR_CLASS_ID`=%s', [call_conductor_id])
        if len(data_list) == 0:
            return False, 'call_conductor_id={} is not available'.format(call_conductor_id)

        chk_c_data = json.loads(data_list[0]['SETTING'])
        chk_node_datas = self.extract_node(chk_c_data)
        chk_node_call_datas = self.extract_node_type(chk_node_datas, 'call')

        for key, block_1 in chk_node_call_datas.items():
            if block_1['call_conductor_id'] == chk_call_conductor_id:
                return False, 'call_conductor_id={} is loop'.format(chk_call_conductor_id)
            else:
                return self._chk_call_loop_recursive(block_1['call_conductor_id'], chk_call_conductor_id)

        return True,

    def extract_node_type(self, node_datas, node_type):
        """
        extract node type={node_type} from node datas

        Arguments:
            node_datas: node_datas in conductor infomation(dict)
        Returns:
            node_datas
        """
        res = {}

        for key, block_1 in node_datas.items():
            if block_1['type'] == node_type:
                res[key] = block_1

        return res

    def extract_node(self, c_data):
        """
        extract node datas

        Arguments:
            c_data: conductor infomation(dict)
        Returns:
            node_datas
        """
        res = {}

        for key, value in c_data.items():
            if re.fullmatch(r'node-\d{1,}', key):
                res[key] = value

        return res

    def override_node_idlink(self, c_all_data=None):
        """
        update conductor infomation(dict)

        Arguments:
            c_data: conductor infomation(dict)
        Returns:
        Returns:
            (tuple)
            - retBool (bool)
            - err_code xxx-xxxxx
            # - err msg args (list)
        """
        chk_num_1 = len(c_all_data)
        if c_all_data:
            res_check = self.chk_format_all(c_all_data)
            if res_check[0] is False:
                return res_check

        try:
            # conductor name
            if self.conductor_data['id']:
                if self.cmd_type != 'Register':
                    data_list = self.__db.table_select('T_COMN_CONDUCTOR_CLASS', 'WHERE `DISUSE_FLAG`=0 AND `CONDUCTOR_CLASS_ID`=%s', [self.conductor_data['id']])  # noqa E501
                    self.conductor_data['conductor_name'] = data_list[0]['CONDUCTOR_NAME']

            for key, block_1 in self.node_datas.items():
                node_type = block_1['type']

                if node_type == 'movement':
                    # movement_name
                    data_list = self.__db.table_select('T_COMN_MOVEMENT', 'WHERE `DISUSE_FLAG`=0 AND `MOVEMENT_ID`=%s', [block_1['movement_id']])
                    block_1['movement_name'] = data_list[0]['MOVEMENT_NAME']
                    # operation_name
                    if block_1['operation_id']:
                        data_list = self.__db.table_select('T_COMN_OPERATION', 'WHERE `DISUSE_FLAG`=0 AND `OPERATION_ID`=%s', [block_1['operation_id']])  # noqa E501
                        block_1['operation_name'] = data_list[0]['OPERATION_NAME']
                elif node_type == 'call':
                    # call_conductor_name
                    data_list = self.__db.table_select('T_COMN_CONDUCTOR_CLASS', 'WHERE `DISUSE_FLAG`=0 AND `CONDUCTOR_CLASS_ID`=%s', [block_1['call_conductor_id']])  # noqa E501
                    block_1['call_conductor_name'] = data_list[0]['CONDUCTOR_NAME']
                    # operation_name
                    if block_1['operation_id']:
                        data_list = self.__db.table_select('T_COMN_OPERATION', 'WHERE `DISUSE_FLAG`=0 AND `OPERATION_ID`=%s', [block_1['operation_id']])  # noqa E501
                        block_1['operation_name'] = data_list[0]['OPERATION_NAME']

        except Exception as e:
            g.applogger.error(e)
            print(e)
            msg = g.appmsg.get_api_message('MSG-40013')
            return False, msg
            # return False, retCode

        res = {
            'config': self.config_data,
            'conductor': self.conductor_data,
        }
        res.update(self.node_datas)
        res.update(self.edge_datas)
        
        chk_num_2 = len(res)
        if chk_num_1 != chk_num_2:
            msg = g.appmsg.get_api_message('MSG-40013')
            return False, msg

        return True, res,

    # parallel->marge  check処理呼び出し
    def chk_parallel_marge(self, c_data):
        """
        check conductor data
            use case parallel marge

        Arguments:
            c_data: conductor infomation(dict)
        Returns:
            (tuple)
            - retBool (bool)

        """
        retBool = True
        msg = ''
        try:
            parallel_node = ''
            for k, v in c_data.items():
                if 'node-' in k:
                    node_id = v.get('id')
                    node_type = v.get('type')
                    # Startからparallelを追跡
                    if node_type == 'start':
                        tmp_result = self.search_target_node('out', node_id, 'parallel-branch', c_data)
                        if tmp_result is not False:
                            if len(tmp_result) != 0:
                                # parallel<->mergeを検索
                                parallel_node = tmp_result[0]
                                tmp_result = self.search_parallel_marge(parallel_node, 'merge', c_data)
                                if tmp_result is False:
                                    raise Exception()
        except Exception:
            retBool = False
            tmp_msg_key = g.appmsg.get_api_message('MSG-00004')
            tmp_msg = g.appmsg.get_api_message('MSG-40011')
            msg = json.dumps([json.dumps({tmp_msg_key: tmp_msg}, ensure_ascii=False)], ensure_ascii=False)
        return retBool, msg,

    # parallel->margeNode検索
    def search_parallel_marge(self, parallel_node, target_node_type, c_data):
        """
        search conductor data node parallel<->marge
        Arguments:
            base_node_id: node_id
            target_node_type: node_type
            reverse_target_node_name: node_id
            c_data: conductor infomation(dict)
        Returns:

        """
        result = []
        try:
            # parallelからmergeを追跡
            t_terminal = c_data.get(parallel_node).get('terminal')
            for tname, tinfo in t_terminal.items():
                t_t_type = tinfo.get('type')
                if t_t_type == 'out':
                    tmp_result = self.search_target_node('out', parallel_node, 'merge', c_data)
                    if tmp_result is not False:
                        if len(tmp_result) != 0:
                            # mergeからparallelまで逆追跡
                            merge_node = tmp_result[0]
                            tmp_result = self.search_target_node_reverse(merge_node, 'parallel-branch', parallel_node, c_data)
                            if tmp_result is False:
                                raise Exception()
                            # mergeから先も追跡
                            tmp_result = self.search_target_node('out', merge_node, 'parallel-branch', c_data)
                            if tmp_result is not False:
                                if len(tmp_result) != 0:
                                    tmp_result = self.search_parallel_marge(tmp_result[0], 'merge', c_data)
        except Exception:
            result = False
        return result

    # Node検索in方向
    def search_target_node_reverse(self, base_node_id, target_node_type, reverse_target_node_name, c_data):
        """
        search conductor data node reverse
        Arguments:
            base_node_id: node_id
            target_node_type: node_type
            reverse_target_node_name: node_id
            c_data: conductor infomation(dict)
        Returns:

        """
        result = []
        try:
            # base_node_id->target_node_typeの検索
            terminal_type = 'in'
            tmp_result = self.search_target_node(terminal_type, base_node_id, target_node_type, c_data)
            if tmp_result is False:
                raise Exception()
            else:
                reverse_target_node = tmp_result[0]
                if reverse_target_node == reverse_target_node_name:
                    return True
                else:
                    tmp_result = self.search_target_node_reverse(reverse_target_node, target_node_type, reverse_target_node_name, c_data)
                    if tmp_result is False:
                        raise Exception()
        except Exception:
            result = False
        return result
    
    # Node検索処理呼び出し
    def search_target_node(self, terminal_type, base_node_id, target_node_type, c_data):
        """
        search conductor data node
        Arguments:
            terminal_type: terminal type (in or out)
            base_node_id: node_id
            target_node_type: node_type
            c_data: conductor infomation(dict)
        Returns:

        """
        result = []
        try:
            # 検索開始
            tmp_result = self.search_node(terminal_type, base_node_id, c_data)
            if tmp_result is False:
                raise Exception()
            else:
                for t_node_id in tmp_result:
                    t_node_type = c_data.get(t_node_id).get('type')
                    if t_node_type == target_node_type:
                        # 対象のnode_typeの場合
                        return tmp_result
                    else:
                        # merge->parallel-branch検索中(in)に
                        # conditional-branch,status-file-branchがあればエラー
                        if (target_node_type == 'parallel-branch' and
                                terminal_type == 'in' and
                                t_node_type in ['conditional-branch', 'status-file-branch']):
                            raise Exception()
                        # 対象のnode_typeでない場合、次のnodeを検索
                        tmp_result = self.search_target_node(terminal_type, t_node_id, target_node_type, c_data)
                        return tmp_result
        except Exception:
            result = False
        return result

    # Node検索処理
    def search_node(self, terminal_type, base_node_id, c_data):
        """
        search conductor node
        Arguments:
            terminal_type: terminal type (in or out)
            base_node_id: node_id
            c_data: conductor infomation(dict)
        Returns:

        """
        result = []
        try:
            base_node_info = c_data.get(base_node_id)
            base_terminlal = base_node_info.get('terminal')
            for tname, tinfo in base_terminlal.items():
                next_node = tinfo.get('targetNode')
                t_type = tinfo.get('type')
                if t_type == terminal_type:
                    result.append(next_node)
        except Exception:
            result = False
        return result

    # Callループチェック処理呼び出し用
    def chk_call_loop_base_1(self, chk_conductor_id, c_data, call_conductor_id_List={}):
        retBool = True
        msg = ''
        try:
            tmp_result = self.chk_loop_base_1(chk_conductor_id, c_data, call_conductor_id_List)
            if tmp_result is False:
                raise Exception()
        except Exception:
            retBool = False
            msg = json.dumps([json.dumps({"Usecase": g.appmsg.get_api_message('MSG-40012')}, ensure_ascii=False)], ensure_ascii=False)
        return retBool, msg,

    # Callループチェック処理
    def chk_loop_base_1(self, chk_conductor_id, c_data={}, call_conductor_id_List={}):
        try:
            table_name = 'T_COMN_CONDUCTOR_CLASS'
            where_str = 'WHERE `CONDUCTOR_CLASS_ID` = %s AND `DISUSE_FLAG`= 0 '
            # 最上位以外DBから取得 + 構造整理
            if c_data == {}:
                retArray = self.__db.table_select(table_name, where_str, [chk_conductor_id])
                tmpNodeLists = retArray[0]
            else:
                tmpNodeLists = {"SETTING": json.dumps(c_data)}
            arrCallLists = {}
            
            # 重複排除
            conductor_data = tmpNodeLists.get('SETTING')
            if isinstance(conductor_data, str):
                conductor_data = json.loads(conductor_data)
            for key2, val2 in conductor_data.items():
                if 'node-' in key2:
                    node_type = val2.get('type')
                    if node_type == 'call':
                        call_canductor_id = val2.get('call_conductor_id')
                        if isinstance(call_canductor_id, list):
                            call_canductor_id = val2.get('call_conductor_id')[0]
                        arrCallLists.setdefault(call_canductor_id, call_canductor_id)
            # loop chk
            if len(arrCallLists) != 0:
                for call_conductor_id in arrCallLists:
                    if chk_conductor_id is not None:
                        call_conductor_id_List.setdefault(chk_conductor_id, {call_conductor_id: call_conductor_id})
                        call_conductor_id_List[chk_conductor_id].setdefault(call_conductor_id, call_conductor_id)
                        call_conductor_id_List = self.chk_loop_base_1(call_conductor_id, {}, call_conductor_id_List)
                        if call_conductor_id_List is False:
                            raise Exception()
                        if chk_conductor_id in list(call_conductor_id_List.keys()):
                            if chk_conductor_id in list(call_conductor_id_List[chk_conductor_id].keys()):
                                # chk_conductor_idでcall(chk_conductor_id)
                                raise Exception()
                            elif call_conductor_id in list(call_conductor_id_List.keys()):
                                if chk_conductor_id in list(call_conductor_id_List[call_conductor_id].keys()):
                                    # call(call_conductor_id)内でchk_conductor_id
                                    raise Exception()
                        else:
                            raise Exception()

        except Exception:
            return False
        return call_conductor_id_List
