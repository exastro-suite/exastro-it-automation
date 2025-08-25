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
database connection agent module for workspace-db on mongodb
"""
from flask import g
import os
import uuid
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from ..dbconnect.dbconnect_org import DBConnectOrg
from common_libs.common.exception import AppException
from common_libs.common.util import ky_decrypt, ky_encrypt, generate_secrets
from . import collection
from .collection_base import CollectionBase
from .const import Const


class MONGOConnectCommon():
    """
    database connection agnet class for root-user on mongodb
    """
    _client = None  # database connection clinet
    _db = None  # database connection

    def __init__(self):
        """
        constructor
        """
        # MongoDBに接続
        self._connection_string = ''
        self._option_ssl_flg = True if os.environ.get("MONGO_OPTION_SSL", "FALSE").upper() == "TRUE" else False
        self._scheme = os.environ.get("MONGO_SCHEME", "mongodb")
        self._host = os.environ.get("MONGO_HOST")
        self._port = int(os.environ.get("MONGO_PORT", 0) or 0)
        self._db_user = os.environ.get("MONGO_ADMIN_USER")
        self._db_passwd = ky_encrypt(os.environ.get("MONGO_ADMIN_PASSWORD"))
        self._db_name = 'admin'

        # connect database
        self.connect()

    def __del__(self):
        """
        destructor
        """
        self.disconnect()

    def connect(self):
        """
        connect database

        Returns:
            is success:(bool)
        """
        if self._client is not None:
            return True

        try:
            if not self._connection_string:
                self._client = MongoClient(
                    ssl=self._option_ssl_flg,
                    host='{}://{}'.format(self._scheme, self._host),
                    port=self._port,
                    username=self._db_user,
                    password=ky_decrypt(self._db_passwd),
                    authSource=self._db_name,
                )
            else:
                self._client = MongoClient(ky_decrypt(self._connection_string))
        except PyMongoError as mongo_error:
            raise AppException("999-00002", ["mongodb.{}".format(self._db_name), mongo_error])

        if self._client is None:
            raise AppException("999-00002", ["mongodb.{}".format(self._db_name), "mongodb client is invalid"])

        # server_info()メソッドでサーバー情報を取得
        server_info = self._client.server_info()
        # バージョンを取得
        version = server_info.get('version')
        g.mongoVersion = version

        self._db = self._client[self._db_name]

        return True

    def connect_check(self):
        """
         接続チェック（接続できない場合は例外を投げる）
        """

        try:
            self._client.server_info()
        except PyMongoError as mongo_error:
            # タイムアウト
            raise AppException("499-00011", [mongo_error], [])

    def disconnect(self):
        """
        disconnect database
        """
        if self._client is not None:
            self._client.close()

        self._client = None
        self._db = None

    def create_database(self, db_name):
        """
        create database
        """
        pass

    def drop_database(self, db_name):
        """
        drop database
        """
        self._client.drop_database(db_name)

    def create_user(self, user_name, user_password, db_name='', role_list=['dbAdmin', 'readWrite']):
        """
        create user

        Arguments:
            user_name: user name
            user_password: user_password
            db_name: database name
            role: role_name array
        """
        role = []
        for role_name in role_list:
            role.append({'role': role_name, 'db': db_name})

        self.db(db_name).command('createUser', user_name, pwd=user_password, roles=role)

    def drop_user(self, user_name, db_name='admin'):
        """
        drop user
        """
        self.db(db_name).command('dropUser', user_name)

    def db(self, db_name=None):
        if db_name is None:
            return self._db
        else:
            return self._client[db_name]

    def collection(self, collection_name):
        return self._db[collection_name]

    def _check_res(self, res):
        # g.applogger.debug(res)

        if 'ok' in res and res['ok'] == 1:
            return True

        errmsg = res['errmsg'] if 'errmsg' in res else ''
        code = res['code'] if 'code' in res else ''
        codeName = res['codeName'] if 'codeName' in res else ''

        raise AppException("999-00002", [self._db_name, errmsg, code, codeName])

    def _uuid_create(self):
        """
        make uuid of version4

        Returns:
            uuid
        """
        return uuid.uuid4()

    def userinfo_generate(self, prefix=""):
        """
        create user for workspace

        Arguments:
            db_name: database name(uuid)
        Returns:
            db_name, user_name, user_password: tuple
        """
        db_name = prefix + "_" + str(self._uuid_create()).upper()

        # 利用可能文字は？
        db_user_name = prefix + "_" + generate_secrets(20, "-_$+")
        db_user_password = self.password_generate()

        return db_name, db_user_name, db_user_password

    def password_generate(self):
        """
        generate password

        Arguments:
            escape or not: bool
        Returns:
            password string: str
        """
        length = 16
        available_symbol = "-_$+"
        password = generate_secrets(length, available_symbol)

        return password


class MONGOConnectOrg(MONGOConnectCommon):
    """
    database connection root user agnet class for organization on mongodb
    """

    def __init__(self, org_db: DBConnectOrg=None):
        """
        constructor
        """
        if self._client is not None:
            return True

        organization_id = g.get('ORGANIZATION_ID')
        self._organization_id = organization_id

        # get db-connect-infomation from environment-variables
        self._option_ssl_flg = True if os.environ.get("MONGO_OPTION_SSL", "FALSE").upper() == "TRUE" else False
        self._scheme = os.environ.get("MONGO_SCHEME", "mongodb")
        self._host = os.environ.get("MONGO_HOST")
        self._port = int(os.environ.get("MONGO_PORT", 0) or 0)

        self._db_name = "admin"
        if "db_connect_info" not in g:
            # get db-connect-infomation from organization-db
            connect_info = org_db.get_connect_info()
            if connect_info is False:
                db_info = "ORGANIZATION_ID=" + organization_id
                raise AppException("999-00001", [db_info])

            self._mongo_owner = connect_info["MONGO_OWNER"]
            self._connection_string = connect_info["MONGO_CONNECTION_STRING"]
            self._db_user = connect_info["MONGO_ADMIN_USER"]
            self._db_passwd = connect_info["MONGO_ADMIN_PASSWORD"]
        else:
            self._mongo_owner = g.db_connect_info["ORG_MONGO_OWNER"]
            self._connection_string = g.db_connect_info["ORG_MONGO_CONNECTION_STRING"]
            self._db_user = g.db_connect_info["ORG_MONGO_ADMIN_USER"]
            self._db_passwd = g.db_connect_info["ORG_MONGO_ADMIN_PASSWORD"]

        # connect database
        self.connect()


class MONGOConnectWs(MONGOConnectCommon):
    """
    database connection root user agnet class for workspace-db on mongodb
    """

    def __init__(self, workspace_id=None, organization_id=None):
        """
        constructor
        """
        if self._client is not None:
            return True

        organization_id = g.get('ORGANIZATION_ID')
        self._organization_id = organization_id

        workspace_id = g.get('WORKSPACE_ID')
        self._workspace_id = workspace_id

        # get db-connect-infomation from environment-variables
        self._option_ssl_flg = True if os.environ.get("MONGO_OPTION_SSL", "FALSE").upper() == "TRUE" else False
        self._scheme = os.environ.get("MONGO_SCHEME", "mongodb")
        self._host = os.environ.get("MONGO_HOST")
        self._port = int(os.environ.get("MONGO_PORT", 0) or 0)

        if "db_connect_info" not in g:
            # get db-connect-infomation from organization-db
            org_db = DBConnectOrg(organization_id)
            connect_info = org_db.get_wsdb_connect_info(workspace_id)
            org_db.db_disconnect()
            if connect_info is False:
                db_info = "WORKSPACE_ID=" + workspace_id
                db_info = "ORGANIZATION_ID=" + organization_id + "," + db_info if organization_id else db_info
                raise AppException("999-00001", [db_info])

            self._connection_string = connect_info['MONGO_CONNECTION_STRING']
            self._db_name = connect_info["MONGO_DATABASE"]
            self._db_user = connect_info["MONGO_USER"]
            self._db_passwd = connect_info["MONGO_PASSWORD"]
        else:
            self._connection_string = g.db_connect_info['WS_MONGO_CONNECTION_STRING']
            self._db_name = g.db_connect_info["WS_MONGO_DATABASE"]
            self._db_user = g.db_connect_info["WS_MONGO_USER"]
            self._db_passwd = g.db_connect_info["WS_MONGO_PASSWORD"]

        # connect database
        self.connect()

    def create_collection(self, collection_name: str):
        '''
        コレクション名に対応したCollectionBaseの具象クラスを生成する。
        Arguments:
            collection_name: 生成するクラスに対応したコレクション名

        Raises:
            TypeError:未定義のコレクション名を受け取った場合に発生

        Returns:
            CollectionBaseの具象クラス
        '''

        return self.CollectionFactory.create(collection_name)

    def get_collection_name(self, table_name):
        """
        MariaDBのテーブル名に対応するMongoDBのコレクション名を返却する

        Arguments:
            table_name (str): MariaDBのテーブル名

        Returns:
            str: コレクション名
        """
        return self.CollectionFactory.get_collection_name(table_name)

    class CollectionFactory():
        """
        CollectionFactory
        利便性を考慮してMONGOConnectWsのインナークラスとして定義
            CollectionBaseの具象クラスをコレクション名を与えて生成するために定義したクラス。
            定義のメンテナンスを行う際は以下を確認すること。
            ・CollectionFactory.FACTORY_MAP
            ・collection/__init__.py
            ・const.py

        """

        # MongoDBのコレクション名と対応するクラスの対応表
        FACTORY_MAP: [str, CollectionBase] = {
            Const.LABELED_EVENT_COLLECTION: collection.LabeledEventCollection
        }

        @classmethod
        def create(cls, collection_name: str) -> CollectionBase:
            '''
            コレクション名に対応したCollectionBaseの具象クラスを生成する。
            Arguments:
                collection_name: 生成するクラスに対応したコレクション名

            Raises:
                TypeError:未定義のコレクション名を受け取った場合に発生

            Returns:
                CollectionBaseの具象クラス
            '''

            if collection_name in cls.FACTORY_MAP:
                return cls.FACTORY_MAP[collection_name]()
            raise TypeError

        @classmethod
        def get_collection_name(cls, table_name: str) -> str:
            """
            MariaDBのテーブル名に対応するMongoDBのコレクション名を返却する

            Arguments:
                table_name (str): テーブル名

            Returns:
                str: コレクション名
            """

            return Const.NAME_MAP[table_name]
