import pytest
from unittest.mock import MagicMock, Mock
import datetime
from flask import Flask

from libs.ansible_execution import check_driver, update_timestamp, unexecuted_instance, get_populated_data_path, get_execution_limit


"""
    check_driver
    update_timestamp
    unexecuted_instance
    get_execution_status
    get_populated_data_path
    get_execution_limit
"""


# テスト対象の関数と定数を定義します。
# 実際には、別のファイルからインポートしてください。
class AnscConst:
    DF_ANSL_EXEC_STS_INST = "T_ANSL_EXEC_STS_INST"
    DF_ANSP_EXEC_STS_INST = "T_ANSP_EXEC_STS_INST"
    DF_ANSR_EXEC_STS_INST = "T_ANSR_EXEC_STS_INST"
    DF_LEGACY_DRIVER_ID = "legacy"
    DF_PIONEER_DRIVER_ID = "pioneer"
    DF_LEGACY_ROLE_DRIVER_ID = "legacy_role"


# Flaskアプリケーションのインスタンスを作成
@pytest.fixture(scope="session")
def app_context():
    from flask import Flask
    app = Flask(__name__)
    with app.app_context():
        yield


# gオブジェクトをモックするためのフィクスチャ
@pytest.fixture
def mock_g(mocker):
    """
    gオブジェクトをモックし、appmsgとapploggerを置き換える
    """
    mock_g_object = mocker.MagicMock()
    mock_g_object.appmsg = mocker.MagicMock()
    mock_g_object.applogger = mocker.MagicMock()

    # gオブジェクトを直接モックする
    mocker.patch('libs.ansible_execution.g', new=mock_g_object)

    return mock_g_object


@pytest.mark.parametrize(
    "driver_id, expected_driver_mode_id, expected_t_exec_sts_inst",
    [
        ("legacy", "L", "T_ANSL_EXEC_STS_INST"),
        ("pioneer", "P", "T_ANSP_EXEC_STS_INST"),
        ("legacy_role", "R", "T_ANSR_EXEC_STS_INST"),
        ("invalid_id", None, None),  # 存在しないIDのテストケース
    ],
)
def test_check_driver(mock_g, driver_id, expected_driver_mode_id, expected_t_exec_sts_inst):
    """
    check_driver関数の動作をテストします。
    """
    driver_mode_id, t_exec_sts_inst = check_driver(driver_id)
    assert driver_mode_id == expected_driver_mode_id
    assert t_exec_sts_inst == expected_t_exec_sts_inst


@pytest.fixture
def mock_wsdb(mocker):
    """
    wsDbオブジェクトのモックを作成するフィクスチャ。
    table_selectメソッドの戻り値を定義します。
    """
    wsdb_mock = mocker.MagicMock()
    wsdb_mock.table_select.side_effect = []
    return wsdb_mock


@pytest.mark.parametrize(
    "driver_name, expected_table_name, execution_no",
    [
        ("legacy", "T_ANSL_EXEC_STS_INST", "00000000-0000-0000-0000-00000000000l"),
        ("pioneer", "T_ANSP_EXEC_STS_INST", "00000000-0000-0000-0000-00000000000p"),
        ("legacy_role", "T_ANSR_EXEC_STS_INST", "00000000-0000-0000-0000-00000000000r"),
    ],
)
def test_update_timestamp_success(driver_name, expected_table_name, execution_no):
    """
    正常なdriver_nameとexecution_noが渡された場合に、
    各メソッドが正しく呼び出されることをテストします。
    """
    ws_db = MagicMock()
    update_timestamp(ws_db, driver_name, execution_no)

    # ws_db.db_transaction_startが1回呼び出されたことを検証
    ws_db.db_transaction_start.assert_called_once()

    # ws_db.table_updateが正しく呼び出されたことを検証
    expected_update_data = {'EXECUTION_NO': execution_no}
    ws_db.table_update.assert_called_once_with(
        expected_table_name,
        expected_update_data,
        'EXECUTION_NO',
        False,
        True
    )

    # ws_db.db_transaction_endが正しく呼び出されたことを検証
    ws_db.db_transaction_end.assert_called_once_with(True)


@pytest.mark.parametrize(
    "driver_name, expected_table_name, execution_no",
    [
        ("invalid_driver", "T_XXXXX_EXEC_STS_INST", "00000000-0000-0000-0000-0000000000ng"),
    ],
)
def test_update_timestamp_invalid_driver(driver_name, expected_table_name, execution_no):
    """
    無効なdriver_nameが渡された場合に、
    ws_dbのメソッドが一切呼び出されないことをテストします。
    """
    ws_db = MagicMock()
    update_timestamp(ws_db, driver_name, execution_no)

    # ws_dbのどのメソッドも呼び出されなかったことを検証
    ws_db.db_transaction_start.assert_not_called()
    ws_db.table_update.assert_not_called()
    ws_db.db_transaction_end.assert_not_called()


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    yield app


@pytest.fixture
def mock_dbca():
    """
    objdbcaのモックオブジェクトを作成するフィクスチャ
    """
    mock = Mock()
    # デフォルトのtable_selectの戻り値を設定
    mock.table_select.side_effect = [
        # T_ANSC_IF_INFO の戻り値
        [
            {
                'ANSIBLE_IF_INFO_ID': '1',
                'ANSIBLE_EXEC_MODE': '3',
                'ANSTWR_HOST_ID': None,
                'ANSTWR_PROTOCOL': 'https',
                'ANSTWR_PORT': 443, 'ANSTWR_ORGANIZATION': None,
                'ANSTWR_AUTH_TOKEN': None,
                'ANSTWR_DEL_RUNTIME_DATA': '1',
                'ANSTWR_REST_TIMEOUT': 60, 'ANSIBLE_PROXY_ADDRESS': None,
                'ANSIBLE_PROXY_PORT': None,
                'ANSIBLE_VAULT_PASSWORD': None,
                'ANSIBLE_CORE_PATH': '/usr/local/bin',
                'ANS_GIT_HOSTNAME': None,
                'ANS_GIT_USER': None,
                'ANS_GIT_SSH_KEY_FILE': None,
                'ANS_GIT_SSH_KEY_FILE_PASS': None,
                'ANSIBLE_STORAGE_PATH_LNX': None,
                'ANSIBLE_STORAGE_PATH_ANS': None,
                'CONDUCTOR_STORAGE_PATH_ANS': None,
                'ANSIBLE_EXEC_OPTIONS': '-v',
                'NULL_DATA_HANDLING_FLG': '0',
                'ANSIBLE_NUM_PARALLEL_EXEC': 5, 'ANSIBLE_REFRESH_INTERVAL': 1000, 'ANSIBLE_TAILLOG_LINES': 1000, 'NOTE': None,
                'DISUSE_FLAG': '0',
                'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 27, 8, 48, 18, 849960), 'LAST_UPDATE_USER': '90e06bc4-1b64-457f-9d0e-1cbdd9ad4716'}
        ],
        # T_ANSC_EXECDEV の戻り値
        [
            {
                'ROW_ID': '1',
                'EXECUTION_ENVIRONMENT_NAME': '~[Exastro standard] default',
                'BUILD_TYPE': '2',
                'TAG_NAME': 'default',
                'EXECUTION_ENVIRONMENT_ID': 'T_CMDB_f7a294e8-a7a7-4d03-8a76-e2f910db55d7,a2bfccfd-0a29-45cb-bc54-b48bf6f51d71',
                'TEMPLATE_ID': '1',
                'NOTE': None,
                'DISUSE_FLAG': '0',
                'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 21, 11, 20, 14, 50376), 'LAST_UPDATE_USER': '1'}
        ],
        # 最初のtable_select (legacy)
        [
            {
                'EXECUTION_NO': '00000000-0000-0000-0000-0000000000l1',
                'RUN_MODE': '1',
                'STATUS_ID': '11',
                'EXEC_MODE': '3',
                'ABORT_EXECUTE_FLAG': '0',
                'CONDUCTOR_NAME': None,
                'EXECUTION_USER': 'y y',
                'TIME_REGISTER': datetime.datetime(2025, 8, 27, 14, 7, 11), 'MOVEMENT_ID': '00000000-0000-0000-0000-0000000000mv1',
                'I_MOVEMENT_NAME': 'MV1',
                'I_TIME_LIMIT': None,
                'I_ANS_HOST_DESIGNATE_TYPE_ID': '1',
                'I_ANS_PARALLEL_EXE': None,
                'I_ANS_WINRM_ID': None,
                'I_ANS_PLAYBOOK_HED_DEF': '- hosts: all\n  remote_user: "{{ __loginuser__ }}"\n  gather_facts: no',
                'I_AG_EXECUTION_ENVIRONMENT_NAME': '~[Exastro standard] default',
                'I_AG_BUILDER_OPTIONS': None,
                'I_EXECUTION_ENVIRONMENT_NAME': None,
                'I_ANSIBLE_CONFIG_FILE': None,
                'OPERATION_ID': '00000000-0000-0000-0000-0000000000op1',
                'I_OPERATION_NAME': 'OP_HOST',
                'FILE_INPUT': 'InputData_00000000-0000-0000-0000-0000000000l1.zip',
                'FILE_RESULT': None,
                'TIME_BOOK': None,
                'TIME_START': datetime.datetime(2025, 8, 27, 14, 7, 15), 'TIME_END': None,
                'COLLECT_STATUS': None,
                'COLLECT_LOG': None,
                'CONDUCTOR_INSTANCE_NO': None,
                'I_ANS_EXEC_OPTIONS': None,
                'LOGFILELIST_JSON': None,
                'MULTIPLELOG_MODE': None,
                'EXECUTE_HOST_NAME': 'dd6e223f2be3',
                'NOTE': None,
                'DISUSE_FLAG': '0',
                'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 27, 14, 7, 15, 61810), 'LAST_UPDATE_USER': '20101'},
            {
                'EXECUTION_NO': '00000000-0000-0000-0000-0000000000l2',
                'RUN_MODE': '1',
                'STATUS_ID': '11',
                'EXEC_MODE': '3',
                'ABORT_EXECUTE_FLAG': '0',
                'CONDUCTOR_NAME': None,
                'EXECUTION_USER': 'y y',
                'TIME_REGISTER': datetime.datetime(2025, 8, 27, 14, 7, 11), 'MOVEMENT_ID': '00000000-0000-0000-0000-0000000000mv1',
                'I_MOVEMENT_NAME': 'MV1',
                'I_TIME_LIMIT': None,
                'I_ANS_HOST_DESIGNATE_TYPE_ID': '1',
                'I_ANS_PARALLEL_EXE': None,
                'I_ANS_WINRM_ID': None,
                'I_ANS_PLAYBOOK_HED_DEF': '- hosts: all\n  remote_user: "{{ __loginuser__ }}"\n  gather_facts: no',
                'I_AG_EXECUTION_ENVIRONMENT_NAME': '~[Exastro standard] default',
                'I_AG_BUILDER_OPTIONS': None,
                'I_EXECUTION_ENVIRONMENT_NAME': None,
                'I_ANSIBLE_CONFIG_FILE': None,
                'OPERATION_ID': '00000000-0000-0000-0000-0000000000op1',
                'I_OPERATION_NAME': 'OP_HOST',
                'FILE_INPUT': 'InputData_00000000-0000-0000-0000-0000000000l2.zip',
                'FILE_RESULT': None,
                'TIME_BOOK': None,
                'TIME_START': datetime.datetime(2025, 8, 27, 14, 7, 15), 'TIME_END': None,
                'COLLECT_STATUS': None,
                'COLLECT_LOG': None,
                'CONDUCTOR_INSTANCE_NO': None,
                'I_ANS_EXEC_OPTIONS': None,
                'LOGFILELIST_JSON': None,
                'MULTIPLELOG_MODE': None,
                'EXECUTE_HOST_NAME': 'dd6e223f2be3',
                'NOTE': None,
                'DISUSE_FLAG': '0',
                'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 27, 14, 7, 15, 61810), 'LAST_UPDATE_USER': '20101'}
        ],
        # 2番目のtable_select (pioneer)
        [],
        # 3番目のtable_select (legacy_role)
        [],
    ]
    mock._is_transaction = True
    return mock


def test_unexecuted_instance_no_body(app, mocker, mock_dbca):
    """
    bodyが空の場合の正常動作をテスト
    """

    # gオブジェクトの属性をモック
    mock_g = MagicMock()
    mock_g.maintenance_mode.get.return_value = '0'
    mock_g.appmsg.get_log_message.return_value = "dummy log message"
    mock_g.dbConnectError = False
    mock_g.applogger = MagicMock()

    # gにアクセスするすべてのモジュールをパッチする
    mocker.patch('libs.ansible_execution.g', new=mock_g)

    mocker.patch('libs.ansible_execution.get_execution_limit', return_value=1)

    body = {}
    with app.test_request_context('/ansible/api/v1/agent/agent/'):
        result = unexecuted_instance(mock_dbca, body)

    # 期待される戻り値の検証
    assert len(result) == 2

    # 00000000-0000-0000-0000-0000000000l1
    _execution_no = "00000000-0000-0000-0000-0000000000l1"
    assert result[_execution_no]['driver_id'] == 'legacy'
    assert result[_execution_no]['anstwr_del_runtime_data'] == '1'
    assert result[_execution_no]['build_type'] == '2'

    # 00000000-0000-0000-0000-0000000000l2
    _execution_no = "00000000-0000-0000-0000-0000000000l2"
    assert result[_execution_no]['driver_id'] == 'legacy'
    assert result[_execution_no]['anstwr_del_runtime_data'] == '1'
    assert result[_execution_no]['build_type'] == '2'

    # メソッド呼び出しの検証
    mock_dbca.db_transaction_start.assert_called_once()
    assert mock_dbca.table_select.call_count == 5
    assert mock_dbca.sql_execute.call_count == 1
    assert mock_dbca.table_update.call_count == 2
    mock_dbca.db_transaction_end.assert_called_once_with(True)


def test_unexecuted_instance_with_env_names(app, mocker, mock_dbca):
    """
    特定のexecution_environment_namesが指定された場合の正常動作をテスト
    """

    # gオブジェクトの属性をモック
    mock_g = MagicMock()
    mock_g.maintenance_mode.get.return_value = '0'
    mock_g.appmsg.get_log_message.return_value = "dummy log message"
    mock_g.dbConnectError = False
    mock_g.applogger = MagicMock()

    # gにアクセスするすべてのモジュールをパッチする
    mocker.patch('libs.ansible_execution.g', new=mock_g)

    mocker.patch('libs.ansible_execution.get_execution_limit', return_value=1)

    execution_environment_name = "~[Exastro standard] default"
    body = {"execution_environment_names": [execution_environment_name]}
    with app.test_request_context('/ansible/api/v1/agent/agent/'):
        result = unexecuted_instance(mock_dbca, "org1", body)

    # 期待される戻り値の検証
    assert len(result) == 2

    # 00000000-0000-0000-0000-0000000000l1
    _execution_no = "00000000-0000-0000-0000-0000000000l1"
    assert result[_execution_no]['driver_id'] == 'legacy'
    assert result[_execution_no]['anstwr_del_runtime_data'] == '1'
    assert result[_execution_no]['build_type'] == '2'

    # 00000000-0000-0000-0000-0000000000l2
    _execution_no = "00000000-0000-0000-0000-0000000000l2"
    assert result[_execution_no]['driver_id'] == 'legacy'
    assert result[_execution_no]['anstwr_del_runtime_data'] == '1'
    assert result[_execution_no]['build_type'] == '2'

    # table_selectの引数が正しいか検証
    where_expected = 'WHERE DISUSE_FLAG=%s AND STATUS_ID = %s AND I_AG_EXECUTION_ENVIRONMENT_NAME IN (%s) ORDER BY TIME_REGISTER ASC  LIMIT %s'
    parameter_expected = ['0', '11', execution_environment_name, 1]

    # mock_dbca.table_select.assert_any_call("T_ANSL_EXEC_STS_INST", where_expected, parameter_expected)
    # mock_dbca.table_select.assert_any_call("T_ANSP_EXEC_STS_INST", where_expected, parameter_expected)
    mock_dbca.table_select.assert_any_call("T_ANSR_EXEC_STS_INST", where_expected, parameter_expected)


@pytest.mark.parametrize(
    "execution_limit",
    [
        (1),
        (25),
    ],
)
def test_unexecuted_instance_with_execution_limit(app, mocker, mock_dbca, execution_limit):
    """
    execution_limitが指定された場合の正常動作をテスト
    """
    mock_dbca.table_select.side_effect = [
        # T_ANSC_IF_INFO の戻り値
        [
            {
                'ANSIBLE_IF_INFO_ID': '1',
                'ANSIBLE_EXEC_MODE': '3',
                'ANSTWR_HOST_ID': None,
                'ANSTWR_PROTOCOL': 'https',
                'ANSTWR_PORT': 443, 'ANSTWR_ORGANIZATION': None,
                'ANSTWR_AUTH_TOKEN': None,
                'ANSTWR_DEL_RUNTIME_DATA': '1',
                'ANSTWR_REST_TIMEOUT': 60, 'ANSIBLE_PROXY_ADDRESS': None,
                'ANSIBLE_PROXY_PORT': None,
                'ANSIBLE_VAULT_PASSWORD': None,
                'ANSIBLE_CORE_PATH': '/usr/local/bin',
                'ANS_GIT_HOSTNAME': None,
                'ANS_GIT_USER': None,
                'ANS_GIT_SSH_KEY_FILE': None,
                'ANS_GIT_SSH_KEY_FILE_PASS': None,
                'ANSIBLE_STORAGE_PATH_LNX': None,
                'ANSIBLE_STORAGE_PATH_ANS': None,
                'CONDUCTOR_STORAGE_PATH_ANS': None,
                'ANSIBLE_EXEC_OPTIONS': '-v',
                'NULL_DATA_HANDLING_FLG': '0',
                'ANSIBLE_NUM_PARALLEL_EXEC': 5, 'ANSIBLE_REFRESH_INTERVAL': 1000, 'ANSIBLE_TAILLOG_LINES': 1000, 'NOTE': None,
                'DISUSE_FLAG': '0',
                'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 27, 8, 48, 18, 849960), 'LAST_UPDATE_USER': '90e06bc4-1b64-457f-9d0e-1cbdd9ad4716'}
        ],
        # T_ANSC_EXECDEV の戻り値
        [
            {
                'ROW_ID': '1',
                'EXECUTION_ENVIRONMENT_NAME': '~[Exastro standard] default',
                'BUILD_TYPE': '2',
                'TAG_NAME': 'default',
                'EXECUTION_ENVIRONMENT_ID': 'T_CMDB_f7a294e8-a7a7-4d03-8a76-e2f910db55d7,a2bfccfd-0a29-45cb-bc54-b48bf6f51d71',
                'TEMPLATE_ID': '1',
                'NOTE': None,
                'DISUSE_FLAG': '0',
                'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 21, 11, 20, 14, 50376), 'LAST_UPDATE_USER': '1'}
        ],
        # 最初のtable_select (legacy)
        [
            {
                'EXECUTION_NO': '00000000-0000-0000-0000-0000000000l1',
                'RUN_MODE': '1',
                'STATUS_ID': '11',
                'EXEC_MODE': '3',
                'ABORT_EXECUTE_FLAG': '0',
                'CONDUCTOR_NAME': None,
                'EXECUTION_USER': 'y y',
                'TIME_REGISTER': datetime.datetime(2025, 8, 27, 14, 7, 11), 'MOVEMENT_ID': '00000000-0000-0000-0000-0000000000mv1',
                'I_MOVEMENT_NAME': 'MV1',
                'I_TIME_LIMIT': None,
                'I_ANS_HOST_DESIGNATE_TYPE_ID': '1',
                'I_ANS_PARALLEL_EXE': None,
                'I_ANS_WINRM_ID': None,
                'I_ANS_PLAYBOOK_HED_DEF': '- hosts: all\n  remote_user: "{{ __loginuser__ }}"\n  gather_facts: no',
                'I_AG_EXECUTION_ENVIRONMENT_NAME': '~[Exastro standard] default',
                'I_AG_BUILDER_OPTIONS': None,
                'I_EXECUTION_ENVIRONMENT_NAME': None,
                'I_ANSIBLE_CONFIG_FILE': None,
                'OPERATION_ID': '00000000-0000-0000-0000-0000000000op1',
                'I_OPERATION_NAME': 'OP_HOST',
                'FILE_INPUT': 'InputData_00000000-0000-0000-0000-0000000000l1.zip',
                'FILE_RESULT': None,
                'TIME_BOOK': None,
                'TIME_START': datetime.datetime(2025, 8, 27, 14, 7, 15), 'TIME_END': None,
                'COLLECT_STATUS': None,
                'COLLECT_LOG': None,
                'CONDUCTOR_INSTANCE_NO': None,
                'I_ANS_EXEC_OPTIONS': None,
                'LOGFILELIST_JSON': None,
                'MULTIPLELOG_MODE': None,
                'EXECUTE_HOST_NAME': 'dd6e223f2be3',
                'NOTE': None,
                'DISUSE_FLAG': '0',
                'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 27, 14, 7, 15, 61810), 'LAST_UPDATE_USER': '20101'},
        ],
        # 2番目のtable_select (pioneer)
        [],
        # 3番目のtable_select (legacy_role)
        [],
    ]

    # gオブジェクトの属性をモック
    mock_g = MagicMock()
    mock_g.maintenance_mode.get.return_value = '0'
    mock_g.appmsg.get_log_message.return_value = "dummy log message"
    mock_g.dbConnectError = False
    mock_g.applogger = MagicMock()

    # gにアクセスするすべてのモジュールをパッチする
    mocker.patch('libs.ansible_execution.g', new=mock_g)

    mocker.patch('libs.ansible_execution.get_execution_limit', return_value=execution_limit)

    body = {"execution_limit": execution_limit}
    with app.test_request_context('/ansible/api/v1/agent/agent/'):
        result = unexecuted_instance(mock_dbca, "org1", body)

    # 期待される戻り値の検証
    assert len(result) == 1

    # table_selectの引数が正しいか検証
    where_expected = 'WHERE DISUSE_FLAG=%s AND STATUS_ID = %s ORDER BY TIME_REGISTER ASC  LIMIT %s'
    parameter_expected = ['0', '11', execution_limit]
    mock_dbca.table_select.assert_any_call("T_ANSL_EXEC_STS_INST", where_expected, parameter_expected)


@pytest.mark.parametrize(
    "execution_limit",
    [
        ("10"),
        (None),
        (0),
        (-10),
        ("１０"),
    ],
)
def test_unexecuted_instance_with_execution_limit_other(app, mocker, mock_dbca, execution_limit):
    """
    execution_limitで文字列が指定された場合の正常動作をテスト
    """
    mock_dbca.table_select.side_effect = [
        # T_ANSC_IF_INFO の戻り値
        [
            {
                'ANSIBLE_IF_INFO_ID': '1',
                'ANSIBLE_EXEC_MODE': '3',
                'ANSTWR_HOST_ID': None,
                'ANSTWR_PROTOCOL': 'https',
                'ANSTWR_PORT': 443, 'ANSTWR_ORGANIZATION': None,
                'ANSTWR_AUTH_TOKEN': None,
                'ANSTWR_DEL_RUNTIME_DATA': '1',
                'ANSTWR_REST_TIMEOUT': 60, 'ANSIBLE_PROXY_ADDRESS': None,
                'ANSIBLE_PROXY_PORT': None,
                'ANSIBLE_VAULT_PASSWORD': None,
                'ANSIBLE_CORE_PATH': '/usr/local/bin',
                'ANS_GIT_HOSTNAME': None,
                'ANS_GIT_USER': None,
                'ANS_GIT_SSH_KEY_FILE': None,
                'ANS_GIT_SSH_KEY_FILE_PASS': None,
                'ANSIBLE_STORAGE_PATH_LNX': None,
                'ANSIBLE_STORAGE_PATH_ANS': None,
                'CONDUCTOR_STORAGE_PATH_ANS': None,
                'ANSIBLE_EXEC_OPTIONS': '-v',
                'NULL_DATA_HANDLING_FLG': '0',
                'ANSIBLE_NUM_PARALLEL_EXEC': 5, 'ANSIBLE_REFRESH_INTERVAL': 1000, 'ANSIBLE_TAILLOG_LINES': 1000, 'NOTE': None,
                'DISUSE_FLAG': '0',
                'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 27, 8, 48, 18, 849960), 'LAST_UPDATE_USER': '90e06bc4-1b64-457f-9d0e-1cbdd9ad4716'}
        ],
        # T_ANSC_EXECDEV の戻り値
        [
            {
                'ROW_ID': '1',
                'EXECUTION_ENVIRONMENT_NAME': '~[Exastro standard] default',
                'BUILD_TYPE': '2',
                'TAG_NAME': 'default',
                'EXECUTION_ENVIRONMENT_ID': 'T_CMDB_f7a294e8-a7a7-4d03-8a76-e2f910db55d7,a2bfccfd-0a29-45cb-bc54-b48bf6f51d71',
                'TEMPLATE_ID': '1',
                'NOTE': None,
                'DISUSE_FLAG': '0',
                'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 21, 11, 20, 14, 50376), 'LAST_UPDATE_USER': '1'}
        ],
        # 最初のtable_select (legacy)
        [
            {
                'EXECUTION_NO': '00000000-0000-0000-0000-0000000000l1',
                'RUN_MODE': '1',
                'STATUS_ID': '11',
                'EXEC_MODE': '3',
                'ABORT_EXECUTE_FLAG': '0',
                'CONDUCTOR_NAME': None,
                'EXECUTION_USER': 'y y',
                'TIME_REGISTER': datetime.datetime(2025, 8, 27, 14, 7, 11), 'MOVEMENT_ID': '00000000-0000-0000-0000-0000000000mv1',
                'I_MOVEMENT_NAME': 'MV1',
                'I_TIME_LIMIT': None,
                'I_ANS_HOST_DESIGNATE_TYPE_ID': '1',
                'I_ANS_PARALLEL_EXE': None,
                'I_ANS_WINRM_ID': None,
                'I_ANS_PLAYBOOK_HED_DEF': '- hosts: all\n  remote_user: "{{ __loginuser__ }}"\n  gather_facts: no',
                'I_AG_EXECUTION_ENVIRONMENT_NAME': '~[Exastro standard] default',
                'I_AG_BUILDER_OPTIONS': None,
                'I_EXECUTION_ENVIRONMENT_NAME': None,
                'I_ANSIBLE_CONFIG_FILE': None,
                'OPERATION_ID': '00000000-0000-0000-0000-0000000000op1',
                'I_OPERATION_NAME': 'OP_HOST',
                'FILE_INPUT': 'InputData_00000000-0000-0000-0000-0000000000l1.zip',
                'FILE_RESULT': None,
                'TIME_BOOK': None,
                'TIME_START': datetime.datetime(2025, 8, 27, 14, 7, 15), 'TIME_END': None,
                'COLLECT_STATUS': None,
                'COLLECT_LOG': None,
                'CONDUCTOR_INSTANCE_NO': None,
                'I_ANS_EXEC_OPTIONS': None,
                'LOGFILELIST_JSON': None,
                'MULTIPLELOG_MODE': None,
                'EXECUTE_HOST_NAME': 'dd6e223f2be3',
                'NOTE': None,
                'DISUSE_FLAG': '0',
                'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 27, 14, 7, 15, 61810), 'LAST_UPDATE_USER': '20101'},
        ],
        # 2番目のtable_select (pioneer)
        [],
        # 3番目のtable_select (legacy_role)
        [],
    ]

    # gオブジェクトの属性をモック
    mock_g = MagicMock()
    mock_g.maintenance_mode.get.return_value = '0'
    mock_g.appmsg.get_log_message.return_value = "dummy log message"
    mock_g.dbConnectError = False
    mock_g.applogger = MagicMock()

    # gにアクセスするすべてのモジュールをパッチする
    mocker.patch('libs.ansible_execution.g', new=mock_g)

    mocker.patch('libs.ansible_execution.get_execution_limit', return_value=25)

    body = {"execution_limit": execution_limit}
    with app.test_request_context('/ansible/api/v1/agent/agent/'):
        result = unexecuted_instance(mock_dbca, "org1", body)

    # 期待される戻り値の検証
    assert len(result) == 1

    # table_selectの引数が正しいか検証
    where_expected = 'WHERE DISUSE_FLAG=%s AND STATUS_ID = %s ORDER BY TIME_REGISTER ASC  LIMIT %s'
    parameter_expected = ['0', '11', 25]
    mock_dbca.table_select.assert_any_call("T_ANSL_EXEC_STS_INST", where_expected, parameter_expected)


def test_unexecuted_instance_with_env_names_and_execution_limit(app, mocker, mock_dbca):
    """
    特定のexecution_environment_names、execution_limiが指定された場合の正常動作をテスト
    """
    mock_dbca.table_select.side_effect = [
        # T_ANSC_IF_INFO の戻り値
        [
            {
                'ANSIBLE_IF_INFO_ID': '1',
                'ANSIBLE_EXEC_MODE': '3',
                'ANSTWR_HOST_ID': None,
                'ANSTWR_PROTOCOL': 'https',
                'ANSTWR_PORT': 443, 'ANSTWR_ORGANIZATION': None,
                'ANSTWR_AUTH_TOKEN': None,
                'ANSTWR_DEL_RUNTIME_DATA': '1',
                'ANSTWR_REST_TIMEOUT': 60, 'ANSIBLE_PROXY_ADDRESS': None,
                'ANSIBLE_PROXY_PORT': None,
                'ANSIBLE_VAULT_PASSWORD': None,
                'ANSIBLE_CORE_PATH': '/usr/local/bin',
                'ANS_GIT_HOSTNAME': None,
                'ANS_GIT_USER': None,
                'ANS_GIT_SSH_KEY_FILE': None,
                'ANS_GIT_SSH_KEY_FILE_PASS': None,
                'ANSIBLE_STORAGE_PATH_LNX': None,
                'ANSIBLE_STORAGE_PATH_ANS': None,
                'CONDUCTOR_STORAGE_PATH_ANS': None,
                'ANSIBLE_EXEC_OPTIONS': '-v',
                'NULL_DATA_HANDLING_FLG': '0',
                'ANSIBLE_NUM_PARALLEL_EXEC': 5, 'ANSIBLE_REFRESH_INTERVAL': 1000, 'ANSIBLE_TAILLOG_LINES': 1000, 'NOTE': None,
                'DISUSE_FLAG': '0',
                'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 27, 8, 48, 18, 849960), 'LAST_UPDATE_USER': '90e06bc4-1b64-457f-9d0e-1cbdd9ad4716'}
        ],
        # T_ANSC_EXECDEV の戻り値
        [
            {
                'ROW_ID': '1',
                'EXECUTION_ENVIRONMENT_NAME': '~[Exastro standard] default',
                'BUILD_TYPE': '2',
                'TAG_NAME': 'default',
                'EXECUTION_ENVIRONMENT_ID': 'T_CMDB_f7a294e8-a7a7-4d03-8a76-e2f910db55d7,a2bfccfd-0a29-45cb-bc54-b48bf6f51d71',
                'TEMPLATE_ID': '1',
                'NOTE': None,
                'DISUSE_FLAG': '0',
                'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 21, 11, 20, 14, 50376), 'LAST_UPDATE_USER': '1'}
        ],
        # 最初のtable_select (legacy)
        [
            {
                'EXECUTION_NO': '00000000-0000-0000-0000-0000000000l1',
                'RUN_MODE': '1',
                'STATUS_ID': '11',
                'EXEC_MODE': '3',
                'ABORT_EXECUTE_FLAG': '0',
                'CONDUCTOR_NAME': None,
                'EXECUTION_USER': 'y y',
                'TIME_REGISTER': datetime.datetime(2025, 8, 27, 14, 7, 11), 'MOVEMENT_ID': '00000000-0000-0000-0000-0000000000mv1',
                'I_MOVEMENT_NAME': 'MV1',
                'I_TIME_LIMIT': None,
                'I_ANS_HOST_DESIGNATE_TYPE_ID': '1',
                'I_ANS_PARALLEL_EXE': None,
                'I_ANS_WINRM_ID': None,
                'I_ANS_PLAYBOOK_HED_DEF': '- hosts: all\n  remote_user: "{{ __loginuser__ }}"\n  gather_facts: no',
                'I_AG_EXECUTION_ENVIRONMENT_NAME': '~[Exastro standard] default',
                'I_AG_BUILDER_OPTIONS': None,
                'I_EXECUTION_ENVIRONMENT_NAME': None,
                'I_ANSIBLE_CONFIG_FILE': None,
                'OPERATION_ID': '00000000-0000-0000-0000-0000000000op1',
                'I_OPERATION_NAME': 'OP_HOST',
                'FILE_INPUT': 'InputData_00000000-0000-0000-0000-0000000000l1.zip',
                'FILE_RESULT': None,
                'TIME_BOOK': None,
                'TIME_START': datetime.datetime(2025, 8, 27, 14, 7, 15), 'TIME_END': None,
                'COLLECT_STATUS': None,
                'COLLECT_LOG': None,
                'CONDUCTOR_INSTANCE_NO': None,
                'I_ANS_EXEC_OPTIONS': None,
                'LOGFILELIST_JSON': None,
                'MULTIPLELOG_MODE': None,
                'EXECUTE_HOST_NAME': 'dd6e223f2be3',
                'NOTE': None,
                'DISUSE_FLAG': '0',
                'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 27, 14, 7, 15, 61810), 'LAST_UPDATE_USER': '20101'},
        ],
        # 2番目のtable_select (pioneer)
        [],
        # 3番目のtable_select (legacy_role)
        [],
    ]

    # gオブジェクトの属性をモック
    mock_g = MagicMock()
    mock_g.maintenance_mode.get.return_value = '0'
    mock_g.appmsg.get_log_message.return_value = "dummy log message"
    mock_g.dbConnectError = False
    mock_g.applogger = MagicMock()

    # gにアクセスするすべてのモジュールをパッチする
    mocker.patch('libs.ansible_execution.g', new=mock_g)

    mocker.patch('libs.ansible_execution.get_execution_limit', return_value=1)

    execution_environment_name = "~[Exastro standard] default"
    body = {"execution_environment_names": [execution_environment_name], "execution_limit": 1}
    with app.test_request_context('/ansible/api/v1/agent/agent/'):
        result = unexecuted_instance(mock_dbca, "org1", body)

    # 期待される戻り値の検証
    assert len(result) == 1

    # 00000000-0000-0000-0000-0000000000l1
    _execution_no = "00000000-0000-0000-0000-0000000000l1"
    assert result[_execution_no]['driver_id'] == 'legacy'
    assert result[_execution_no]['anstwr_del_runtime_data'] == '1'
    assert result[_execution_no]['build_type'] == '2'

    # table_selectの引数が正しいか検証
    where_expected = 'WHERE DISUSE_FLAG=%s AND STATUS_ID = %s AND I_AG_EXECUTION_ENVIRONMENT_NAME IN (%s) ORDER BY TIME_REGISTER ASC  LIMIT %s'
    parameter_expected = ['0', '11', execution_environment_name, 1]

    mock_dbca.table_select.assert_any_call("T_ANSL_EXEC_STS_INST", where_expected, parameter_expected)


def test_unexecuted_instance_with_env_names_and_execution_limit_all_driver(app, mocker, mock_dbca):
    """
    特定のexecution_environment_namesが指定された場合の正常動作をテスト
        legacy、pioneer、legacy_role
    """
    mock_dbca.table_select.side_effect = [
        # T_ANSC_IF_INFO の戻り値
        [
            {
                'ANSIBLE_IF_INFO_ID': '1',
                'ANSIBLE_EXEC_MODE': '3',
                'ANSTWR_HOST_ID': None,
                'ANSTWR_PROTOCOL': 'https',
                'ANSTWR_PORT': 443, 'ANSTWR_ORGANIZATION': None,
                'ANSTWR_AUTH_TOKEN': None,
                'ANSTWR_DEL_RUNTIME_DATA': '1',
                'ANSTWR_REST_TIMEOUT': 60, 'ANSIBLE_PROXY_ADDRESS': None,
                'ANSIBLE_PROXY_PORT': None,
                'ANSIBLE_VAULT_PASSWORD': None,
                'ANSIBLE_CORE_PATH': '/usr/local/bin',
                'ANS_GIT_HOSTNAME': None,
                'ANS_GIT_USER': None,
                'ANS_GIT_SSH_KEY_FILE': None,
                'ANS_GIT_SSH_KEY_FILE_PASS': None,
                'ANSIBLE_STORAGE_PATH_LNX': None,
                'ANSIBLE_STORAGE_PATH_ANS': None,
                'CONDUCTOR_STORAGE_PATH_ANS': None,
                'ANSIBLE_EXEC_OPTIONS': '-v',
                'NULL_DATA_HANDLING_FLG': '0',
                'ANSIBLE_NUM_PARALLEL_EXEC': 5, 'ANSIBLE_REFRESH_INTERVAL': 1000, 'ANSIBLE_TAILLOG_LINES': 1000, 'NOTE': None,
                'DISUSE_FLAG': '0',
                'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 27, 8, 48, 18, 849960), 'LAST_UPDATE_USER': '90e06bc4-1b64-457f-9d0e-1cbdd9ad4716'}
        ],
        # T_ANSC_EXECDEV の戻り値
        [
            {
                'ROW_ID': '1',
                'EXECUTION_ENVIRONMENT_NAME': '~[Exastro standard] default',
                'BUILD_TYPE': '2',
                'TAG_NAME': 'default',
                'EXECUTION_ENVIRONMENT_ID': 'T_CMDB_f7a294e8-a7a7-4d03-8a76-e2f910db55d7,a2bfccfd-0a29-45cb-bc54-b48bf6f51d71',
                'TEMPLATE_ID': '1',
                'NOTE': None,
                'DISUSE_FLAG': '0',
                'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 21, 11, 20, 14, 50376), 'LAST_UPDATE_USER': '1'}
        ],
        # 最初のtable_select (legacy)
        [
            {
                'EXECUTION_NO': '00000000-0000-0000-0000-0000000000l1',
                'RUN_MODE': '1',
                'STATUS_ID': '11',
                'EXEC_MODE': '3',
                'ABORT_EXECUTE_FLAG': '0',
                'CONDUCTOR_NAME': None,
                'EXECUTION_USER': 'y y',
                'TIME_REGISTER': datetime.datetime(2025, 8, 27, 14, 7, 11), 'MOVEMENT_ID': '00000000-0000-0000-0000-0000000000mv1',
                'I_MOVEMENT_NAME': 'MV1',
                'I_TIME_LIMIT': None,
                'I_ANS_HOST_DESIGNATE_TYPE_ID': '1',
                'I_ANS_PARALLEL_EXE': None,
                'I_ANS_WINRM_ID': None,
                'I_ANS_PLAYBOOK_HED_DEF': '- hosts: all\n  remote_user: "{{ __loginuser__ }}"\n  gather_facts: no',
                'I_AG_EXECUTION_ENVIRONMENT_NAME': '~[Exastro standard] default',
                'I_AG_BUILDER_OPTIONS': None,
                'I_EXECUTION_ENVIRONMENT_NAME': None,
                'I_ANSIBLE_CONFIG_FILE': None,
                'OPERATION_ID': '00000000-0000-0000-0000-0000000000op1',
                'I_OPERATION_NAME': 'OP_HOST',
                'FILE_INPUT': 'InputData_00000000-0000-0000-0000-0000000000l1.zip',
                'FILE_RESULT': None,
                'TIME_BOOK': None,
                'TIME_START': datetime.datetime(2025, 8, 27, 14, 7, 15), 'TIME_END': None,
                'COLLECT_STATUS': None,
                'COLLECT_LOG': None,
                'CONDUCTOR_INSTANCE_NO': None,
                'I_ANS_EXEC_OPTIONS': None,
                'LOGFILELIST_JSON': None,
                'MULTIPLELOG_MODE': None,
                'EXECUTE_HOST_NAME': 'dd6e223f2be3',
                'NOTE': None,
                'DISUSE_FLAG': '0',
                'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 27, 14, 7, 15, 61810), 'LAST_UPDATE_USER': '20101'},
        ],
        # 2番目のtable_select (pioneer)
        [
            {
                'EXECUTION_NO': '00000000-0000-0000-0000-0000000000p1',
                'RUN_MODE': '1',
                'STATUS_ID': '11',
                'EXEC_MODE': '3',
                'ABORT_EXECUTE_FLAG': '0',
                'CONDUCTOR_NAME': None,
                'EXECUTION_USER': 'y y',
                'TIME_REGISTER': datetime.datetime(2025, 8, 27, 14, 7, 11), 'MOVEMENT_ID': '00000000-0000-0000-0000-0000000000mv2',
                'I_MOVEMENT_NAME': 'MV2',
                'I_TIME_LIMIT': None,
                'I_ANS_HOST_DESIGNATE_TYPE_ID': '1',
                'I_ANS_PARALLEL_EXE': None,
                'I_ANS_WINRM_ID': None,
                'I_ANS_PLAYBOOK_HED_DEF': '- hosts: all\n  remote_user: "{{ __loginuser__ }}"\n  gather_facts: no',
                'I_AG_EXECUTION_ENVIRONMENT_NAME': '~[Exastro standard] default',
                'I_AG_BUILDER_OPTIONS': None,
                'I_EXECUTION_ENVIRONMENT_NAME': None,
                'I_ANSIBLE_CONFIG_FILE': None,
                'OPERATION_ID': '00000000-0000-0000-0000-0000000000op1',
                'I_OPERATION_NAME': 'OP_HOST',
                'FILE_INPUT': 'InputData_00000000-0000-0000-0000-0000000000p1.zip',
                'FILE_RESULT': None,
                'TIME_BOOK': None,
                'TIME_START': datetime.datetime(2025, 8, 27, 14, 7, 15), 'TIME_END': None,
                'COLLECT_STATUS': None,
                'COLLECT_LOG': None,
                'CONDUCTOR_INSTANCE_NO': None,
                'I_ANS_EXEC_OPTIONS': None,
                'LOGFILELIST_JSON': None,
                'MULTIPLELOG_MODE': None,
                'EXECUTE_HOST_NAME': 'dd6e223f2be3',
                'NOTE': None,
                'DISUSE_FLAG': '0',
                'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 27, 14, 7, 15, 61810), 'LAST_UPDATE_USER': '20101'},
        ],
        # 3番目のtable_select (legacy_role)
        [
            {
                'EXECUTION_NO': '00000000-0000-0000-0000-0000000000r1',
                'RUN_MODE': '1',
                'STATUS_ID': '11',
                'EXEC_MODE': '3',
                'ABORT_EXECUTE_FLAG': '0',
                'CONDUCTOR_NAME': None,
                'EXECUTION_USER': 'y y',
                'TIME_REGISTER': datetime.datetime(2025, 8, 27, 14, 7, 11), 'MOVEMENT_ID': '00000000-0000-0000-0000-0000000000mv3',
                'I_MOVEMENT_NAME': 'MV3',
                'I_TIME_LIMIT': None,
                'I_ANS_HOST_DESIGNATE_TYPE_ID': '1',
                'I_ANS_PARALLEL_EXE': None,
                'I_ANS_WINRM_ID': None,
                'I_ANS_PLAYBOOK_HED_DEF': '- hosts: all\n  remote_user: "{{ __loginuser__ }}"\n  gather_facts: no',
                'I_AG_EXECUTION_ENVIRONMENT_NAME': '~[Exastro standard] default',
                'I_AG_BUILDER_OPTIONS': None,
                'I_EXECUTION_ENVIRONMENT_NAME': None,
                'I_ANSIBLE_CONFIG_FILE': None,
                'OPERATION_ID': '00000000-0000-0000-0000-0000000000op1',
                'I_OPERATION_NAME': 'OP_HOST',
                'FILE_INPUT': 'InputData_00000000-0000-0000-0000-0000000000r1.zip',
                'FILE_RESULT': None,
                'TIME_BOOK': None,
                'TIME_START': datetime.datetime(2025, 8, 27, 14, 7, 15), 'TIME_END': None,
                'COLLECT_STATUS': None,
                'COLLECT_LOG': None,
                'CONDUCTOR_INSTANCE_NO': None,
                'I_ANS_EXEC_OPTIONS': None,
                'LOGFILELIST_JSON': None,
                'MULTIPLELOG_MODE': None,
                'EXECUTE_HOST_NAME': 'dd6e223f2be3',
                'NOTE': None,
                'DISUSE_FLAG': '0',
                'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 27, 14, 7, 15, 61810), 'LAST_UPDATE_USER': '20101'},
        ],
    ]

    # gオブジェクトの属性をモック
    mock_g = MagicMock()
    mock_g.maintenance_mode.get.return_value = '0'
    mock_g.appmsg.get_log_message.return_value = "dummy log message"
    mock_g.dbConnectError = False
    mock_g.applogger = MagicMock()

    # gにアクセスするすべてのモジュールをパッチする
    mocker.patch('libs.ansible_execution.g', new=mock_g)

    mocker.patch('libs.ansible_execution.get_execution_limit', return_value=1)

    execution_environment_name = "~[Exastro standard] default"
    body = {"execution_environment_names": [execution_environment_name], "execution_limit": 1}
    with app.test_request_context('/ansible/api/v1/agent/agent/'):
        result = unexecuted_instance(mock_dbca, "org1", body)

    # 期待される戻り値の検証
    assert len(result) == 3

    # 00000000-0000-0000-0000-0000000000l1
    _execution_no = "00000000-0000-0000-0000-0000000000l1"
    assert result[_execution_no]['driver_id'] == 'legacy'
    assert result[_execution_no]['anstwr_del_runtime_data'] == '1'
    assert result[_execution_no]['build_type'] == '2'

    # table_selectの引数が正しいか検証
    where_expected = 'WHERE DISUSE_FLAG=%s AND STATUS_ID = %s AND I_AG_EXECUTION_ENVIRONMENT_NAME IN (%s) ORDER BY TIME_REGISTER ASC  LIMIT %s'
    parameter_expected = ['0', '11', execution_environment_name, 1]

    mock_dbca.table_select.assert_any_call("T_ANSL_EXEC_STS_INST", where_expected, parameter_expected)
    mock_dbca.table_select.assert_any_call("T_ANSP_EXEC_STS_INST", where_expected, parameter_expected)
    mock_dbca.table_select.assert_any_call("T_ANSR_EXEC_STS_INST", where_expected, parameter_expected)


@pytest.mark.parametrize(
    "organization_id, workspace_id, execution_no, driver_id",
    [
        ("org1", "ws1", "00000000-0000-0000-0000-00000000000l", "legacy"),
    ],
)
def test_get_populated_data_path(app, mocker, mock_dbca, organization_id, workspace_id, execution_no, driver_id):
    """
    Conductorで作業実行しない場合の正常動作をテスト
    """
    mock_dbca.table_select.side_effect = [
        # T_ANSC_IF_INFO の戻り値
        [
            {
                'EXECUTION_NO': '00000000-0000-0000-0000-00000000000l',
                'RUN_MODE': '1',
                'STATUS_ID': '11',
                'EXEC_MODE': '3',
                'ABORT_EXECUTE_FLAG': '0',
                'CONDUCTOR_NAME': None,
                'EXECUTION_USER': 'y y',
                'TIME_REGISTER': datetime.datetime(2025, 8, 27, 14, 7, 11), 'MOVEMENT_ID': '00000000-0000-0000-0000-0000000000mv1',
                'I_MOVEMENT_NAME': 'MV1',
                'I_TIME_LIMIT': None,
                'I_ANS_HOST_DESIGNATE_TYPE_ID': '1',
                'I_ANS_PARALLEL_EXE': None,
                'I_ANS_WINRM_ID': None,
                'I_ANS_PLAYBOOK_HED_DEF': '- hosts: all\n  remote_user: "{{ __loginuser__ }}"\n  gather_facts: no',
                'I_AG_EXECUTION_ENVIRONMENT_NAME': '~[Exastro standard] default',
                'I_AG_BUILDER_OPTIONS': None,
                'I_EXECUTION_ENVIRONMENT_NAME': None,
                'I_ANSIBLE_CONFIG_FILE': None,
                'OPERATION_ID': '00000000-0000-0000-0000-0000000000op1',
                'I_OPERATION_NAME': 'OP_HOST',
                'FILE_INPUT': 'InputData_00000000-0000-0000-0000-00000000000l.zip',
                'FILE_RESULT': None,
                'TIME_BOOK': None,
                'TIME_START': datetime.datetime(2025, 8, 27, 14, 7, 15), 'TIME_END': None,
                'COLLECT_STATUS': None,
                'COLLECT_LOG': None,
                'CONDUCTOR_INSTANCE_NO': None,
                'I_ANS_EXEC_OPTIONS': None,
                'LOGFILELIST_JSON': None,
                'MULTIPLELOG_MODE': None,
                'EXECUTE_HOST_NAME': 'dd6e223f2be3',
                'NOTE': None,
                'DISUSE_FLAG': '0',
                'LAST_UPDATE_TIMESTAMP': datetime.datetime(2025, 8, 27, 14, 7, 15, 61810), 'LAST_UPDATE_USER': '20101'
            },
        ]
    ]

    # gオブジェクトの属性をモック
    mock_g = MagicMock()
    mock_g.maintenance_mode.get.return_value = '0'
    mock_g.appmsg.get_log_message.return_value = "dummy log message"
    mock_g.dbConnectError = False
    mock_g.applogger = MagicMock()

    mock_tar = mocker.MagicMock()
    mock_tar.tar.open = MagicMock()

    _path = f"/tmp/org1/ws1/driver/ansible/legacy/{execution_no}/{execution_no}.tar.gz"
    # gにアクセスするすべてのモジュールをパッチする
    mocker.patch('libs.ansible_execution.g', new=mock_g)
    mocker.patch('common_libs.common.util.g', new=mock_g)
    mocker.patch('libs.ansible_execution.tarfile.open', return_value=MagicMock())
    # mocker.patch('libs.ansible_execution.tar.add', new=MagicMock())

    mock_tar = mocker.MagicMock()
    mock_open = mocker.patch('libs.ansible_execution.tarfile.open')
    mock_open.return_value.__enter__.return_value = mock_tar

    mock_shutil = mocker.MagicMock()
    mock_shutil_open = mocker.patch('libs.ansible_execution.shutil.move')
    mock_shutil_open.return_value.__enter__.return_value = mock_shutil

    with app.test_request_context('/ansible/api/v1/agent/agent/'):
        result = get_populated_data_path(mock_dbca, organization_id, workspace_id, execution_no, driver_id)

    # 期待される戻り値の検証
    assert result == _path


@pytest.mark.parametrize(
    "organization_id, sys_count, org_count, execution_limit, _return_val",
    [
        ("org1", 25, "25", 10, 10),
        ("org1", 25, "25", 1, 1),
        ("org1", 25, "25", 100, 25),
        ("org1", 25, "25", None, 25),
        ("org1", 25, "25", 0, 25),
    ],
)
def test_get_execution_limit(app, mocker, mock_dbca, organization_id, sys_count, org_count, execution_limit, _return_val):
    """
    get_execution_limitのテスト
    """

    # gオブジェクトの属性をモック
    mock_g = MagicMock()
    mock_g.maintenance_mode.get.return_value = '0'
    mock_g.appmsg.get_log_message.return_value = "dummy log message"
    mock_g.dbConnectError = False
    mock_g.applogger = MagicMock()

    mock_tar = mocker.MagicMock()
    mock_tar.tar.open = MagicMock()

    # gにアクセスするすべてのモジュールをパッチする
    mocker.patch('libs.ansible_execution.g', new=mock_g)
    mocker.patch('common_libs.common.util.g', new=mock_g)
    mocker.patch('libs.ansible_execution.get_all_execution_limit', return_value=sys_count)
    mocker.patch('libs.ansible_execution.get_org_execution_limit', return_value={organization_id: org_count})

    with app.test_request_context('/ansible/api/v1/agent/agent/'):
        result = get_execution_limit(organization_id, execution_limit)

    # 期待される戻り値の検証
    assert result == _return_val
