#   Copyright 2026 NEC Corporation
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

"""DBConnectWs の代わりにテストで使うダミー DB クラス（DummyDB）

backyard_main.py を丸ごと動かすために、件数取得（table_count）・生 SQL（sql_execute）・
コミット／トランザクション終了／切断 も備える（呼ばれたことを記録するだけ）。
"""
import copy


class DummyDB:
    """データベース接続(DBConnectWs)のダミークラス（テーブルの中身をメモリに保持する）

    Attributes:
        rows_by_table: {table_name: [row(dict), ...]} テーブルの実体
        select_calls: table_select の呼び出し履歴 [(table_name, where_str), ...]
        update_calls: table_update の呼び出し履歴 [{'table', 'pkey', 'data_list'}, ...]
        insert_calls: table_insert の呼び出し履歴 [{'table', 'pkey', 'data_list'}, ...]
        call_log: table_select / table_insert / table_update の呼び出し順 [(kind, table_name), ...]
        fail_update_on_call: 指定回数目(1 origin)の table_update を False で返す
        fail_insert_on_call: 指定回数目(1 origin)の table_insert を False で返す
        sql_results: sql_execute が返す行リスト
        committed: db_commit が呼ばれた回数
        disconnected: db_disconnect が呼ばれた回数
    """

    COLUMN_NAME_TIMESTAMP = 'LAST_UPDATE_TIMESTAMP'

    # 本物の DB では文字列型（VARCHAR / TEXT）の列。解析器が数値で渡してきても文字列で保存される
    # （ita_api_admin/sql/ansible.sql:1595-1614）。INT 列はそのまま保持する
    STRING_COLUMNS_BY_TABLE = {
        'T_ANSR_NESTVAR_MEMBER': ('VARS_NAME', 'VRAS_NAME_PATH', 'VRAS_NAME_ALIAS'),
    }

    def __init__(self, rows_by_table=None, timestamp='2026-08-19 12:00:00'):
        """
        constructor

        Arguments:
            rows_by_table: {table_name: [row(dict), ...]}
            timestamp: table_insert / table_update が自動設定するタイムスタンプ
        """
        self.rows_by_table = copy.deepcopy(rows_by_table) if rows_by_table else {}
        self.select_calls = []
        self.update_calls = []
        self.insert_calls = []
        self.call_log = []
        self.fail_update_on_call = None
        self.fail_insert_on_call = None
        self.sql_results = []
        self.transaction_started = 0
        self.transaction_ended = 0
        self.committed = 0
        self.disconnected = 0
        self._timestamp = timestamp
        self._uuid_seq = 0

    # - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +
    # DBConnectWs 互換 API
    # - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +

    def table_select(self, table_name, where_str="", bind_value_list=[]):
        """
        select table

        `WHERE DISUSE_FLAG = '0'`（TableBase.store_dbdata_in_memory が組み立てる唯一の WHERE）だけを解釈する。
        本物の DB と同様、呼ぶたびに独立した dict を返す（メモリ上の書き換えが実体に伝播しない）。
        """
        self.select_calls.append((table_name, where_str))
        self.call_log.append(('select', table_name))

        rows = self.rows_by_table.get(table_name, [])
        if "DISUSE_FLAG = '0'" in where_str:
            active_rows = []
            for row in rows:
                if row.get('DISUSE_FLAG') == '0':
                    active_rows.append(row)
            rows = active_rows
        elif where_str:
            raise AssertionError(f"DummyDB does not support this where clause: {where_str}")

        return copy.deepcopy(rows)

    def table_count(self, table_name, where_str="", bind_value_list=[]):
        """
        count table

        backyard_main.has_changes_related_tables が組み立てる
        `WHERE ROW_ID = %s AND (LOADED_FLG is NULL OR LOADED_FLG <> '1')` だけを解釈する。
        """
        self.call_log.append(('count', table_name))

        if "LOADED_FLG" not in where_str:
            raise AssertionError(f"DummyDB does not support this where clause: {where_str}")

        row_id = bind_value_list[0]
        count = 0
        for row in self.rows_by_table.get(table_name, []):
            if row.get('ROW_ID') != row_id:
                continue
            if row.get('LOADED_FLG') != '1':
                count += 1

        return count

    def sql_execute(self, sql, bind_value_list=[]):
        """
        execute sql

        管理対象外変数リストの取得（WrappedStringReplaceAdmin）に使われる。テストが用意した結果を返す。
        """
        self.call_log.append(('sql', sql))
        return copy.deepcopy(self.sql_results)

    def table_insert(self, table_name, data_list, primary_key_name, is_register_history=False):
        """
        insert table

        本物と同様に、主キーが未設定なら払い出して data_list を書き換えてから返す。
        """
        if isinstance(data_list, dict):
            data_list = [data_list]

        self.insert_calls.append({
            'table': table_name,
            'pkey': primary_key_name,
            'data_list': copy.deepcopy(data_list),
        })
        self.call_log.append(('insert', table_name))

        if self.fail_insert_on_call is not None and len(self.insert_calls) == self.fail_insert_on_call:
            return False

        rows = self.rows_by_table.setdefault(table_name, [])
        for data in data_list:
            if primary_key_name not in data or not data[primary_key_name]:
                data[primary_key_name] = self._create_uuid()
            data[self.COLUMN_NAME_TIMESTAMP] = self._timestamp
            rows.append(self._as_stored(table_name, copy.deepcopy(data)))

        return data_list

    def table_update(self, table_name, data_list, primary_key_name, is_register_history=False, last_timestamp=True):
        """
        update table

        本物（dbconnect_common.py:_table_update_with_ids）と同じく
        **data の全キーを SET し、その中の主キーで WHERE を作る**。
        「更新しないカラムも渡しておけば安全」ではないという、Issue #2618 の温床をそのまま再現する。
        """
        if isinstance(data_list, dict):
            data_list = [data_list]

        self.update_calls.append({
            'table': table_name,
            'pkey': primary_key_name,
            'data_list': copy.deepcopy(data_list),
        })
        self.call_log.append(('update', table_name))

        if self.fail_update_on_call is not None and len(self.update_calls) == self.fail_update_on_call:
            return False

        rows = self.rows_by_table.setdefault(table_name, [])
        for data in data_list:
            data = dict(data)
            if last_timestamp is True:
                data[self.COLUMN_NAME_TIMESTAMP] = self._timestamp

            # 本物は data に主キーが無いと KeyError になる
            pkey_value = data[primary_key_name]

            targets = []
            for row in rows:
                if row.get(primary_key_name) == pkey_value:
                    targets.append(row)
            if not targets:
                raise AssertionError(
                    f"DummyDB: no row matched {table_name}.{primary_key_name} = {pkey_value}"
                )
            for row in targets:
                # SET 句に載るのは data のキー全部（本物と同じ）
                row.update(self._as_stored(table_name, data))

        return data_list

    def db_transaction_start(self):
        """トランザクション開始"""
        self.transaction_started += 1

    def db_transaction_end(self, flag=True):
        """トランザクション終了"""
        self.transaction_ended += 1

    def db_commit(self):
        """コミット（呼ばれたことを記録するだけ）"""
        self.committed += 1

    def db_disconnect(self):
        """切断（呼ばれたことを記録するだけ）"""
        self.disconnected += 1

    # - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +
    # テスト用ヘルパ
    # - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - +

    def rows(self, table_name):
        """テーブルの実体（DB に入っている状態）を返す"""
        return self.rows_by_table.get(table_name, [])

    def find_row(self, table_name, **conditions):
        """条件に一致する行を 1 件返す（0 件 / 複数件は AssertionError）"""
        matched = self.find_rows(table_name, **conditions)
        assert len(matched) == 1, f"expected exactly 1 row for {conditions}, got {len(matched)}"
        return matched[0]

    def find_rows(self, table_name, **conditions):
        """条件に一致する行を全部返す"""
        matched = []
        for row in self.rows(table_name):
            is_match = True
            for key, value in conditions.items():
                if row.get(key) != value:
                    is_match = False
                    break
            if is_match:
                matched.append(row)
        return matched

    def update_data_list(self, index):
        """index 回目(0 origin)の table_update に渡された data_list を返す"""
        return self.update_calls[index]['data_list']

    def insert_data_list(self, index):
        """index 回目(0 origin)の table_insert に渡された data_list を返す"""
        return self.insert_calls[index]['data_list']

    def update_calls_for(self, table_name):
        """指定テーブルへの table_update の呼び出しだけを返す"""
        result = []
        for call in self.update_calls:
            if call['table'] == table_name:
                result.append(call)
        return result

    def insert_calls_for(self, table_name):
        """指定テーブルへの table_insert の呼び出しだけを返す"""
        result = []
        for call in self.insert_calls:
            if call['table'] == table_name:
                result.append(call)
        return result

    def _as_stored(self, table_name, data):
        """本物の DB に保存されたときの値に揃える（文字列列に来た数値は文字列になる）"""
        string_columns = self.STRING_COLUMNS_BY_TABLE.get(table_name, ())
        for column in string_columns:
            if column in data and data[column] is not None and not isinstance(data[column], str):
                data[column] = str(data[column])
        return data

    def _create_uuid(self):
        """主キーの払い出し（テストで追跡できるよう連番にする）"""
        self._uuid_seq += 1
        return f"generated-uuid-{self._uuid_seq}"
