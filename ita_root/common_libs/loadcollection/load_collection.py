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
#

from flask import g
from common_libs.common.exception import AppException


class loadCollection():
    """
    MongoDBからデータを抽出する際の振る舞いを定義するクラス。
    loadTableの一部処理も利用するため、loadTableのインスタンスを引数で受け取っている。
    """

    def __init__(self, wsMongo, load_table):
        """
        初期化処理
        Args:
            wsMongo: MongoDBのコネクション
            load_table: loadTableのクラス
        """
        self.wsMongo = wsMongo
        self.load_table = load_table

    def rest_filter(self, parameter, mode, objdbca):
        """
            RESTAPI[filter]:メニューのレコード取得
            ARGS:
                parameter:検索条件
                mode
                    mongo:本体
                    count:件数
            RETRUN:
                status_code, result, msg,
        """
        status_code = '000-00000'  # 成功
        msg = ''
        result_list = []

        try:
            # get_table_nameではMariaDB側のテーブル名が取得されるためそのまま利用はできない。
            # get_table_nameで取得した値をMongoDBのコレクション名に変換が必要
            mariadb_table_name = self.load_table.get_table_name()
            mondodb_collection_name = self.wsMongo.get_collection_name(mariadb_table_name)
            collection = self.wsMongo.create_collection(mondodb_collection_name)
            where_str = collection.create_where(parameter, objdbca)
            # g.applogger.info(f"{where_str=}")

            # MongoDB向けの記法に変換が必要なため、DBから取得した値はそのまま利用しない
            # sort_key = collection.create_sort_key(self.load_table.get_sort_key())

            # if mode in ['mongo']:
            #     tmp_result = (self.wsMongo.collection(mondodb_collection_name)
            #                   .find(where_str)
            #                   .sort(sort_key))

            if mode in ['mongo']:
                # 暫定対応でsortはなし（cosmosDBが非対応だから）v2.4.0
                # tmp_result = self.wsMongo.collection(mondodb_collection_name).find(filter=where_str).sort(sort_key)
                tmp_result = self.wsMongo.collection(mondodb_collection_name).find(filter=where_str)
                result_list = collection.create_result(tmp_result, objdbca)
            elif mode in ['mongo_count']:
                tmp_result = self.wsMongo.collection(mondodb_collection_name).count_documents(where_str)
                result_list = tmp_result

        except AppException as e:
            raise e
        finally:
            result = result_list
        return status_code, result, msg,
