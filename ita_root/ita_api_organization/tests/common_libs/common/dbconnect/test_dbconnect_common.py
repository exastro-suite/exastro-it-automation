import pytest
from unittest.mock import MagicMock

from common_libs.common.dbconnect.dbconnect_common import DBConnectCommon


@pytest.fixture(scope='function')
def dbconnect():
    """
    実際のDB接続を行わずに DBConnectCommon インスタンスを生成するフィクスチャ

    __init__ は環境変数の参照とDB接続を伴うため、__new__ でインスタンスのみ生成し、
    テスト対象メソッドが依存する下位メソッドをモック化する。
    """
    obj = DBConnectCommon.__new__(DBConnectCommon)

    # 下位メソッドをモック化
    obj.db_transaction_start = MagicMock(return_value=True)
    obj.sql_execute = MagicMock(return_value=[])
    obj.table_select = MagicMock(return_value=[])
    # UUIDを固定化(呼び出し毎にインクリメントする値を返す)
    obj._uuid_counter = 0

    def _uuid_side_effect():
        obj._uuid_counter += 1
        return "uuid-{}".format(obj._uuid_counter)

    obj._uuid_create = MagicMock(side_effect=_uuid_side_effect)

    return obj


# ---------------------------------------------------------------------------
# _insert_history
# ---------------------------------------------------------------------------
class TestInsertHistory:

    def test_execute_insert_sql_for_jnl_table(self, dbconnect):
        """履歴テーブル(_JNL)に対してINSERT文が発行されること"""
        history_data = {
            'PK': 'uuid-x',
            'NAME': 'name-value',
            'JOURNAL_SEQ_NO': 'jnl-1',
        }
        dbconnect.sql_execute.return_value = [history_data]

        result = dbconnect._insert_history('T_TEST', history_data)

        assert result == [history_data]
        assert dbconnect.sql_execute.call_count == 1

        sql, value_list = dbconnect.sql_execute.call_args[0]
        # _JNL テーブルへの INSERT であること
        assert sql.startswith("INSERT INTO `T_TEST_JNL`")
        # カラム/プレースホルダー/値の数が一致すること
        assert sql.count("%s") == len(history_data)
        assert value_list == list(history_data.values())
        # 全カラムがSQLに含まれること
        for col in history_data.keys():
            assert col in sql

    def test_returns_sql_execute_result(self, dbconnect):
        """sql_execute の戻り値をそのまま返却すること(失敗時 False)"""
        dbconnect.sql_execute.return_value = False

        result = dbconnect._insert_history('T_TEST', {'PK': 'uuid-x'})

        assert result is False


# ---------------------------------------------------------------------------
# _table_insert_with_ids (本体ロジック)
# ---------------------------------------------------------------------------
class TestTableInsertWithIds:

    def test_insert_without_history(self, dbconnect):
        """履歴なし: PKとNoneのタプルが返ること"""
        dbconnect.sql_execute.return_value = [{'dummy': 1}]
        data = {'NAME': 'name-value'}

        data_list, uuids_list = dbconnect._table_insert_with_ids(
            'T_TEST', data, 'PK', is_register_history=False
        )

        # PKとタイムスタンプが自動付与される
        assert data['PK'] == 'uuid-1'
        assert dbconnect._COLUMN_NAME_TIMESTAMP in data
        # 履歴なしなので journal uuid は None
        assert uuids_list == [('uuid-1', None)]
        # 本体INSERTのみ(履歴INSERTなし)
        assert dbconnect.sql_execute.call_count == 1

    def test_insert_with_history(self, dbconnect):
        """履歴あり: PKとjournal uuidのタプルが返ること"""
        dbconnect.sql_execute.return_value = [{'dummy': 1}]
        data = {'NAME': 'name-value'}

        data_list, uuids_list = dbconnect._table_insert_with_ids(
            'T_TEST', data, 'PK', is_register_history=True
        )

        # PK=uuid-1, JOURNAL_SEQ_NO=uuid-2
        assert uuids_list == [('uuid-1', 'uuid-2')]
        # 本体INSERT + 履歴INSERT
        assert dbconnect.sql_execute.call_count == 2

    def test_insert_dict_is_converted_to_list(self, dbconnect):
        """dictで渡してもlistとして扱われること"""
        dbconnect.sql_execute.return_value = [{'dummy': 1}]

        data_list, uuids_list = dbconnect._table_insert_with_ids(
            'T_TEST', {'NAME': 'x'}, 'PK', is_register_history=False
        )

        assert isinstance(data_list, list)
        assert len(data_list) == 1

    def test_insert_keeps_specified_primary_key(self, dbconnect):
        """PKが指定済みの場合はそのまま利用されること"""
        dbconnect.sql_execute.return_value = [{'dummy': 1}]
        data = {'PK': 'specified-pk', 'NAME': 'x'}

        data_list, uuids_list = dbconnect._table_insert_with_ids(
            'T_TEST', data, 'PK', is_register_history=False
        )

        assert uuids_list == [('specified-pk', None)]

    def test_insert_failure_returns_false(self, dbconnect):
        """本体INSERTが失敗した場合 (False, []) が返ること"""
        dbconnect.sql_execute.return_value = False

        result = dbconnect._table_insert_with_ids(
            'T_TEST', {'NAME': 'x'}, 'PK', is_register_history=False
        )

        assert result == (False, [])

    def test_insert_multiple_rows(self, dbconnect):
        """複数件のデータが処理されること"""
        dbconnect.sql_execute.return_value = [{'dummy': 1}]
        data_list = [{'NAME': 'a'}, {'NAME': 'b'}]

        _data_list, uuids_list = dbconnect._table_insert_with_ids(
            'T_TEST', data_list, 'PK', is_register_history=False
        )

        assert len(uuids_list) == 2
        assert uuids_list == [('uuid-1', None), ('uuid-2', None)]

    @pytest.mark.parametrize("pk_value", ['', None])
    def test_insert_generates_pk_when_empty(self, dbconnect, pk_value):
        """PKが空文字/Noneの場合にUUIDが採番されること"""
        dbconnect.sql_execute.return_value = [{'dummy': 1}]
        data = {'PK': pk_value, 'NAME': 'x'}

        _data_list, uuids_list = dbconnect._table_insert_with_ids(
            'T_TEST', data, 'PK', is_register_history=False
        )

        assert data['PK'] == 'uuid-1'
        assert uuids_list == [('uuid-1', None)]

    def test_insert_main_sql_content(self, dbconnect):
        """本体INSERT文がテーブル名・カラム・値を正しく含むこと"""
        dbconnect.sql_execute.return_value = [{'dummy': 1}]

        dbconnect._table_insert_with_ids(
            'T_TEST', {'NAME': 'name-value'}, 'PK', is_register_history=False
        )

        sql, value_list = dbconnect.sql_execute.call_args_list[0][0]
        # 本体テーブルへの INSERT であること
        assert sql.startswith("INSERT INTO `T_TEST`")
        assert 'PK' in sql
        assert 'NAME' in sql
        # 値が含まれること
        assert 'name-value' in value_list

    def test_insert_second_row_failure_breaks(self, dbconnect):
        """複数件で2件目が失敗した場合、処理が中断し (False, []) になること"""
        # 1件目成功、2件目失敗
        dbconnect.sql_execute.side_effect = [[{'dummy': 1}], False]
        data_list = [{'NAME': 'a'}, {'NAME': 'b'}]

        result = dbconnect._table_insert_with_ids(
            'T_TEST', data_list, 'PK', is_register_history=False
        )

        assert result == (False, [])
        # 2回目で失敗して break するので呼び出しは2回まで
        assert dbconnect.sql_execute.call_count == 2

    def test_insert_empty_list(self, dbconnect):
        """空リストの場合 ([], []) が返ること"""
        result = dbconnect._table_insert_with_ids(
            'T_TEST', [], 'PK', is_register_history=False
        )

        assert result == ([], [])
        assert dbconnect.sql_execute.call_count == 0


# ---------------------------------------------------------------------------
# _table_update_with_ids (本体ロジック)
# ---------------------------------------------------------------------------
class TestTableUpdateWithIds:

    def test_update_without_history(self, dbconnect):
        """履歴なし: PKとNoneのタプルが返ること"""
        dbconnect.sql_execute.return_value = [{'dummy': 1}]
        data = {'PK': 'target-pk', 'NAME': 'name-value'}

        data_list, uuids_list = dbconnect._table_update_with_ids(
            'T_TEST', data, 'PK', is_register_history=False
        )

        # タイムスタンプが自動付与される
        assert dbconnect._COLUMN_NAME_TIMESTAMP in data
        assert uuids_list == [('target-pk', None)]
        # 本体UPDATEのみ
        assert dbconnect.sql_execute.call_count == 1

    def test_update_with_history(self, dbconnect):
        """履歴あり: 再取得したデータのPKとjournal uuidが返ること"""
        dbconnect.sql_execute.return_value = [{'dummy': 1}]
        # 履歴用の再取得(table_select)結果
        dbconnect.table_select.return_value = [{'PK': 'target-pk', 'NAME': 'name-value'}]
        data = {'PK': 'target-pk', 'NAME': 'name-value'}

        data_list, uuids_list = dbconnect._table_update_with_ids(
            'T_TEST', data, 'PK', is_register_history=True
        )

        # JOURNAL_SEQ_NO は uuid_create(1回目) で生成
        assert uuids_list == [('target-pk', 'uuid-1')]
        # 本体UPDATE + 履歴INSERT
        assert dbconnect.sql_execute.call_count == 2
        dbconnect.table_select.assert_called_once()

    def test_update_with_history_no_record_returns_false(self, dbconnect):
        """履歴あり: 再取得で対象なしの場合 (False, []) が返ること"""
        dbconnect.sql_execute.return_value = [{'dummy': 1}]
        dbconnect.table_select.return_value = []
        data = {'PK': 'target-pk', 'NAME': 'x'}

        result = dbconnect._table_update_with_ids(
            'T_TEST', data, 'PK', is_register_history=True
        )

        assert result == (False, [])

    def test_update_failure_returns_false(self, dbconnect):
        """本体UPDATEが失敗した場合 (False, []) が返ること"""
        dbconnect.sql_execute.return_value = False
        data = {'PK': 'target-pk', 'NAME': 'x'}

        result = dbconnect._table_update_with_ids(
            'T_TEST', data, 'PK', is_register_history=False
        )

        assert result == (False, [])

    def test_update_without_timestamp(self, dbconnect):
        """last_timestamp=False の場合タイムスタンプが付与されないこと"""
        dbconnect.sql_execute.return_value = [{'dummy': 1}]
        data = {'PK': 'target-pk', 'NAME': 'x'}

        dbconnect._table_update_with_ids(
            'T_TEST', data, 'PK', is_register_history=False, last_timestamp=False
        )

        assert dbconnect._COLUMN_NAME_TIMESTAMP not in data

    def test_update_dict_is_converted_to_list(self, dbconnect):
        """dictで渡してもlistとして扱われること"""
        dbconnect.sql_execute.return_value = [{'dummy': 1}]

        data_list, uuids_list = dbconnect._table_update_with_ids(
            'T_TEST', {'PK': 'target-pk', 'NAME': 'x'}, 'PK', is_register_history=False
        )

        assert isinstance(data_list, list)
        assert len(data_list) == 1

    def test_update_main_sql_where_and_bind(self, dbconnect):
        """UPDATE文が WHERE PK=%s で、バインド値末尾にPKが付くこと"""
        dbconnect.sql_execute.return_value = [{'dummy': 1}]

        dbconnect._table_update_with_ids(
            'T_TEST', {'PK': 'target-pk', 'NAME': 'x'}, 'PK', is_register_history=False
        )

        sql, value_list = dbconnect.sql_execute.call_args_list[0][0]
        assert sql.startswith("UPDATE `T_TEST` SET")
        assert sql.endswith("WHERE `PK`=%s")
        # バインド値の末尾は WHERE 用の PK 値
        assert value_list[-1] == 'target-pk'

    def test_update_multiple_rows_with_history(self, dbconnect):
        """履歴あり複数件: 各行の (pk, journal uuid) が返ること"""
        dbconnect.sql_execute.return_value = [{'dummy': 1}]
        # 各行の再取得結果を順に返す
        dbconnect.table_select.side_effect = [
            [{'PK': 'pk-1', 'NAME': 'a'}],
            [{'PK': 'pk-2', 'NAME': 'b'}],
        ]
        data_list = [{'PK': 'pk-1', 'NAME': 'a'}, {'PK': 'pk-2', 'NAME': 'b'}]

        _data_list, uuids_list = dbconnect._table_update_with_ids(
            'T_TEST', data_list, 'PK', is_register_history=True
        )

        # 1件目: JOURNAL_SEQ_NO=uuid-1 / 2件目: JOURNAL_SEQ_NO=uuid-2
        assert uuids_list == [('pk-1', 'uuid-1'), ('pk-2', 'uuid-2')]
        # (本体UPDATE + 履歴INSERT) x 2件
        assert dbconnect.sql_execute.call_count == 4

    def test_update_second_row_failure_breaks(self, dbconnect):
        """複数件で2件目が失敗した場合、処理が中断し (False, []) になること"""
        dbconnect.sql_execute.side_effect = [[{'dummy': 1}], False]
        data_list = [{'PK': 'pk-1', 'NAME': 'a'}, {'PK': 'pk-2', 'NAME': 'b'}]

        result = dbconnect._table_update_with_ids(
            'T_TEST', data_list, 'PK', is_register_history=False
        )

        assert result == (False, [])
        assert dbconnect.sql_execute.call_count == 2

    def test_update_empty_list(self, dbconnect):
        """空リストの場合 ([], []) が返ること"""
        result = dbconnect._table_update_with_ids(
            'T_TEST', [], 'PK', is_register_history=False
        )

        assert result == ([], [])
        assert dbconnect.sql_execute.call_count == 0


# ---------------------------------------------------------------------------
# table_insert_with_ids (_table_insert_with_ids へ委譲するラッパー)
# ---------------------------------------------------------------------------
class TestTableInsertWithIdsWrapper:

    def test_delegates_to_private(self, dbconnect):
        """_table_insert_with_ids に委譲し、その戻り値をそのまま返すこと"""
        expected = ([{'PK': 'uuid-1'}], [('uuid-1', None)])
        dbconnect._table_insert_with_ids = MagicMock(return_value=expected)

        result = dbconnect.table_insert_with_ids(
            'T_TEST', {'NAME': 'x'}, 'PK', is_register_history=True
        )

        assert result == expected
        dbconnect._table_insert_with_ids.assert_called_once_with(
            'T_TEST', {'NAME': 'x'}, 'PK', True
        )


# ---------------------------------------------------------------------------
# table_update_with_ids (_table_update_with_ids へ委譲するラッパー)
# ---------------------------------------------------------------------------
class TestTableUpdateWithIdsWrapper:

    def test_delegates_to_private(self, dbconnect):
        """_table_update_with_ids に委譲し、その戻り値をそのまま返すこと"""
        expected = ([{'PK': 'target-pk'}], [('target-pk', None)])
        dbconnect._table_update_with_ids = MagicMock(return_value=expected)

        result = dbconnect.table_update_with_ids(
            'T_TEST', {'PK': 'target-pk', 'NAME': 'x'}, 'PK', is_register_history=True
        )

        assert result == expected
        dbconnect._table_update_with_ids.assert_called_once_with(
            'T_TEST', {'PK': 'target-pk', 'NAME': 'x'}, 'PK', True
        )


# ---------------------------------------------------------------------------
# table_insert (_table_insert_with_ids へ委譲するラッパー)
# ---------------------------------------------------------------------------
class TestTableInsert:

    def test_delegates_to_with_ids_and_returns_result(self, dbconnect):
        """_table_insert_with_ids に委譲し、戻り値の1つ目(data_list)を返すこと"""
        expected_data_list = [{'PK': 'uuid-1', 'NAME': 'x'}]
        dbconnect._table_insert_with_ids = MagicMock(
            return_value=(expected_data_list, [('uuid-1', None)])
        )

        result = dbconnect.table_insert(
            'T_TEST', {'NAME': 'x'}, 'PK', is_register_history=True
        )

        # data_listのみが返り、uuids は返らないこと
        assert result == expected_data_list
        # 引数がそのまま委譲されること
        dbconnect._table_insert_with_ids.assert_called_once_with(
            'T_TEST', {'NAME': 'x'}, 'PK', True
        )

    def test_returns_false_on_failure(self, dbconnect):
        """_table_insert_with_ids が (False, []) の場合 False を返すこと"""
        dbconnect._table_insert_with_ids = MagicMock(return_value=(False, []))

        result = dbconnect.table_insert('T_TEST', {'NAME': 'x'}, 'PK')

        assert result is False

    def test_default_is_register_history_false(self, dbconnect):
        """is_register_history 未指定時は False で委譲されること"""
        dbconnect._table_insert_with_ids = MagicMock(return_value=([], []))

        dbconnect.table_insert('T_TEST', {'NAME': 'x'}, 'PK')

        dbconnect._table_insert_with_ids.assert_called_once_with(
            'T_TEST', {'NAME': 'x'}, 'PK', False
        )

    def test_insert_integration_returns_data_list(self, dbconnect):
        """実際の _table_insert_with_ids 経由(モックせず)で data_list が返ること"""
        dbconnect.sql_execute.return_value = [{'dummy': 1}]

        result = dbconnect.table_insert(
            'T_TEST', {'NAME': 'x'}, 'PK', is_register_history=False
        )

        assert isinstance(result, list)
        assert result[0]['PK'] == 'uuid-1'


# ---------------------------------------------------------------------------
# table_update (_table_update_with_ids へ委譲するラッパー)
# ---------------------------------------------------------------------------
class TestTableUpdate:

    def test_delegates_to_with_ids_and_returns_result(self, dbconnect):
        """_table_update_with_ids に委譲し、戻り値の1つ目(data_list)を返すこと"""
        expected_data_list = [{'PK': 'target-pk', 'NAME': 'x'}]
        dbconnect._table_update_with_ids = MagicMock(
            return_value=(expected_data_list, [('target-pk', None)])
        )

        result = dbconnect.table_update(
            'T_TEST', {'PK': 'target-pk', 'NAME': 'x'}, 'PK', is_register_history=True
        )

        # data_listのみが返り、uuids は返らないこと
        assert result == expected_data_list
        # 引数がそのまま委譲されること
        dbconnect._table_update_with_ids.assert_called_once_with(
            'T_TEST', {'PK': 'target-pk', 'NAME': 'x'}, 'PK', True
        )

    def test_returns_false_on_failure(self, dbconnect):
        """_table_update_with_ids が (False, []) の場合 False を返すこと"""
        dbconnect._table_update_with_ids = MagicMock(return_value=(False, []))

        result = dbconnect.table_update('T_TEST', {'PK': 'target-pk'}, 'PK')

        assert result is False

    def test_default_is_register_history_false(self, dbconnect):
        """is_register_history 未指定時は False で委譲されること"""
        dbconnect._table_update_with_ids = MagicMock(return_value=([], []))

        dbconnect.table_update('T_TEST', {'PK': 'target-pk'}, 'PK')

        dbconnect._table_update_with_ids.assert_called_once_with(
            'T_TEST', {'PK': 'target-pk'}, 'PK', False
        )

    def test_update_integration_returns_data_list(self, dbconnect):
        """実際の _table_update_with_ids 経由(モックせず)で data_list が返ること"""
        dbconnect.sql_execute.return_value = [{'dummy': 1}]

        result = dbconnect.table_update(
            'T_TEST', {'PK': 'target-pk', 'NAME': 'x'}, 'PK', is_register_history=False
        )

        assert isinstance(result, list)
        assert result[0]['PK'] == 'target-pk'
