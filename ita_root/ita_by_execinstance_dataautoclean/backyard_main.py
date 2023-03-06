# Copyright 2022 NEC Corporation#
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
#


import os
import inspect
import time
import datetime
import configparser
import subprocess
import json
import re
import base64
import shutil

from flask import g

from common_libs.common.dbconnect.dbconnect_ws import DBConnectWs
# from common_libs.common.encrypt import decrypt_str
# from common_libs.loadtable import *
# from common_libs.ansible_driver.classes.AnscConstClass import AnscConst
# from common_libs.terraform_driver.common.Const import Const as TFCommonConst
# from common_libs.terraform_driver.cloud_ep.Const import Const as TFCloudEPConst
# from common_libs.terraform_driver.cli.Const import Const as TFCLIConst
# from common_libs.ansible_driver.functions.util import getDataRelayStorageDir, getLegacyPlaybookUploadDirPath, getPioneerDialogUploadDirPath, getRolePackageContentUploadDirPath, getFileContentUploadDirPath, getTemplateContentUploadDirPath
# from common_libs.ansible_driver.functions.rest_libs import insert_execution_list as a_insert_execution_list
# from common_libs.terraform_driver.common.Execute import insert_execution_list as t_insert_execution_list
# from common_libs.cicd.classes.cicd_definition import TD_SYNC_STATUS_NAME_DEFINE, TD_B_CICD_MATERIAL_FILE_TYPE_NAME, TD_B_CICD_MATERIAL_TYPE_NAME, TD_C_PATTERN_PER_ORCH, TD_B_CICD_GIT_PROTOCOL_TYPE_NAME, TD_B_CICD_GIT_REPOSITORY_TYPE_NAME, TD_B_CICD_MATERIAL_LINK_LIST
# from common_libs.cicd.functions.local_functions import MatlLinkColumnValidator2, MatlLinkColumnValidator3, MatlLinkColumnValidator5


def backyard_main(organization_id, workspace_id):

    print("backyard_main called")

    error_flag = 0
    if getattr(g, 'LANGUAGE', None) is None:
        g.LANGUAGE = 'en'

    if getattr(g, 'USER_ID', None) is None:
        g.USER_ID = '100101'

    DBobj = DBConnectWs()

    print("backyard_main end")

