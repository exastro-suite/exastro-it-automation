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

"""
application logging module
"""
from flask import g
import logging
import logging.config
import yaml
import os


class AppLog:
    """
    application logging class
    """

    # logging namespace ex."stdAppLogger" or "fileAppLogger"
    __name__ = "stdAppLogger"

    # Instance of logging-Library（get from logging.getLogger）
    __logger_obj = None

    # logging dict-config
    _config = {}

    __available_log_level = ["ERROR", "INFO", "DEBUG"]

    __env_message = ""
    __tag_message = ""

    def __init__(self):
        """
        constructor
        """
        self.set_env_message()

        # is no-container-app or not(bool)
        isNonContainerLog = True if os.getenv('IS_NON_CONTAINER_LOG') == "1" else False

        # read config.yml
        #  #2079 /storage配下ではないので対象外
        with open(os.getenv('PYTHONPATH') + "/"+ 'logging.yml', 'r') as yml:
            dictConfig = yaml.safe_load(yml)

        self.__create_instance(isNonContainerLog, dictConfig)

    def __create_instance(self, isNonContainerLog, dictConfig={}):
        """
        create Instance of logging-Library and save it

        Arguments:
            isNonContainerLog: (bool) True : no-container-app, False : container-app(Saas)
            dictConfig: (dict) logging dict-config
        Returns:

        """
        self.__name__ = "fileAppLogger" if isNonContainerLog is True else "stdAppLogger"

        if isNonContainerLog is False:  # container-app(Saas)
            del dictConfig['loggers']["fileAppLogger"]
            if "myfile" not in list(dictConfig['loggers']["stdAppLogger"]["handlers"]):
                del dictConfig['handlers']["myfile"]
        else:  # no-container-app
            del dictConfig['loggers']["stdAppLogger"]
            if "myfile" not in list(dictConfig['loggers']["fileAppLogger"]["handlers"]):
                del dictConfig['handlers']["myfile"]

            # log file name: use env[priority: AGENT_NAME > SERVICE_NAME]
            sys_name = os.getenv('AGENT_NAME', os.getenv('SERVICE_NAME', "app"))
            logpath = os.getenv('LOGPATH', './')
            filename = f"{logpath}/{sys_name}.log"
            os.makedirs(logpath) if not os.path.isdir(logpath) else None
            logging_max_size = os.getenv('LOGGING_MAX_SIZE', None)
            logging_max_file = os.getenv('LOGGING_MAX_FILE', None)
            if "myfile" in list(dictConfig['loggers']["fileAppLogger"]["handlers"]):
                # set filename, maxBytes, backupCount [priority: env > logging.yml]
                dictConfig['handlers']["myfile"]["filename"] = filename if filename else dictConfig['handlers']["myfile"]["filename"]
                dictConfig['handlers']["myfile"]["maxBytes"] = int(logging_max_size) if logging_max_size else dictConfig['handlers']["myfile"]["maxBytes"]
                dictConfig['handlers']["myfile"]["backupCount"] = int(logging_max_file) if logging_max_size else dictConfig['handlers']["myfile"]["backupCount"]

        # set config
        self._config = dictConfig
        logging.config.dictConfig(self._config)
        # set instance
        self.__logger_obj = logging.getLogger(self.__name__)
        self.debug("AppLog instance({}) is created".format(self.__name__))

    def set_user_setting(self, wsdb_instance):
        """
        set user-setting

        Arguments:
            wsdb_instance: class(DBConnectWs) instance
        Returns:
            log_level(str) or False
        """
        data_list = wsdb_instance.table_select('T_COMN_SYSTEM_CONFIG', 'WHERE `CONFIG_ID`=%s AND `DISUSE_FLAG`=0', ['LOG_LEVEL'])
        if len(data_list) == 1:
            log_level = data_list[0]['VALUE']
            self.set_level(log_level)
        else:
            log_level = False

        return log_level

    def set_level(self, level):
        """
        set user-setting log level

        Arguments:
            level: (str) "ERROR" | "INFO" | "DEBUG"
        """
        if level in self.__available_log_level:
            self.__logger_obj.setLevel(level)
            self._config['loggers'][self.__name__]['level'] = level

            self.debug("LOG-LEVEL({}) is set".format(level))

    def critical(self, message):
        """
        output critical log

        Arguments:
            message: message for output
        """
        self.__logger_obj.critical(self.__env_message + str(message))

    def exception(self, message):
        """
        output exception log

        Arguments:
            message: message for output
        """
        self.__logger_obj.exception(self.__env_message + str(message))

    def error(self, message):
        """
        output error log

        Arguments:
            message: message for output
        """
        self.__logger_obj.error(self.__env_message + str(message))

    def warning(self, message):
        """
        output warning log

        Arguments:
            message: message for output
        """
        self.__logger_obj.warning(self.__env_message + str(message))

    def info(self, message):
        """
        output info log

        Arguments:
            message: message for output
        """
        self.__logger_obj.info(self.__env_message + str(message))

    def debug(self, message):
        """
        output debug log

        Arguments:
            message: message for output
        """
        self.__logger_obj.debug(self.__env_message + str(message))

    def set_env_message(self):
        """
        set env info message

        """
        msg = ""

        if "ORGANIZATION_ID" in g:
            msg += "[ORGANIZATION_ID:{}]".format(g.ORGANIZATION_ID)

        if "WORKSPACE_ID" in g:
            msg += "[WORKSPACE_ID:{}]".format(g.WORKSPACE_ID)

        if "USER_ID" in g:
            msg += "[USER_ID:{}]".format(g.USER_ID)

        if self.__tag_message:
            msg += self.__tag_message

        self.__env_message = msg + " "

    def set_tag(self, tag_name, tag_val):
        """
        set tag message

        """
        self.__tag_message = "[%s=%s]" % (tag_name, tag_val)
        self.set_env_message()
