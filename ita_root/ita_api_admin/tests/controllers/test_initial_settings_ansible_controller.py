# TODO: Write tests for /workspace/exastro-it-automation-dev/ita_root/ita_api_admin/controllers/initial_settings_ansible_controller.py: post_initial_setting_ansible
"""
post_initial_setting_ansibleのpytestを作成して

以下、APIのパラメータのサンプル

{
    "input_limit_setting": false,
    "execution_engine_list": [
        "Ansible-Core",
        "Ansible Automation Controller",
        "Ansible Execution Agent",
        "Ansible Automation Controller"
    ],
    "initial_data": {
    "ansible_automation_controller_host_list": [
        {
            "file": {
                "ssh_private_key_file": "eHh4"
            },
            "parameter": {
                "host": "aap_dummy_host",
                "authentication_method": "パスワード認証",
                "user": "aws",
                "password": "aws",
                "ssh_private_key_file": "dummy.key",
                "execution_node": "False",
                "remarks": "テスト"
            }
        }
    ],
    "interface_info_ansible": {
        "file": {
        },
        "parameter": {
            "execution_engine": "Ansible Execution Agent",
            "representative_server": "aap_dummy_host",
            "ansible_automation_controller_protocol": "http",
            "ansible_automation_controller_port": "80",
            "authentication_token": "xxxxxxxxxxxxx",
            "delete_runtime_data": "False"
            }
        }
    }
}

execution_engine_list
execution_engine
で使用できるパターンは以下のみ
'Ansible-Core', 'Ansible Automation Controller', 'Ansible Execution Agent', 'Ansible Automation Platform (Cloud)'



"""
import pytest
from unittest.mock import MagicMock
from flask import Flask, g

from controllers.initial_settings_ansible_controller import post_initial_setting_ansible


# mocker.patch のターゲットになるコントローラーモジュールのパス
CONTROLLER = "controllers.initial_settings_ansible_controller"


# ---------------------------------------------------------------------------
# テストデータ生成ヘルパー
# ---------------------------------------------------------------------------
def _valid_body():
    """バリデーションを全て通過する有効なリクエストボディを返す"""
    return {
        "input_limit_setting": False,
        "execution_engine_list": [
            "Ansible-Core",
            "Ansible Automation Controller",
            "Ansible Execution Agent",
            "Ansible Automation Controller"
        ],
        "initial_data": {
            "ansible_automation_controller_host_list": [
                {
                    "file": {
                        "ssh_private_key_file": "eHh4"
                    },
                    "parameter": {
                        "host": "aap_dummy_host",
                        "authentication_method": "パスワード認証",
                        "user": "aws",
                        "password": "aws",
                        "ssh_private_key_file": "dummy.key",
                        "execution_node": "False",
                        "remarks": "テスト",
                    },
                }
            ],
            "interface_info_ansible": {
                "file": {},
                "parameter": {
                    "execution_engine": "Ansible Execution Agent",
                    "representative_server": "aap_dummy_host",
                    "ansible_automation_controller_protocol": "http",
                    "ansible_automation_controller_port": "80",
                    "authentication_token": "xxxxxxxxxxxxx",
                    "delete_runtime_data": "False",
                },
            },
        },
    }


def _org_db_info():
    """T_COMN_ORGANIZATION_DB_INFO の1レコード相当のdictを返す"""
    return {
        "PRIMARY_KEY": "org-pk-0001",
        "ORGANIZATION_ID": "org1",
        "DB_HOST": "localhost",
        "DB_PORT": 3306,
        "DB_USER": "org_user",
        "DB_PASSWORD": "org_pass",
        "DB_ADMIN_USER": "org_admin",
        "DB_ADMIN_PASSWORD": "org_admin_pass",
        "DB_DATABASE": "org_db",
        "INITIAL_DATA_ANSIBLE_IF": None,
        "DISUSE_FLAG": "0",
    }


def _workspace_data(workspace_id="ws1"):
    """T_COMN_WORKSPACE_DB_INFO の1レコード相当のdictを返す"""
    return {
        "WORKSPACE_ID": workspace_id,
        "DB_HOST": "localhost",
        "DB_PORT": 3306,
        "DB_USER": "ws_user",
        "DB_PASSWORD": "ws_pass",
        "DB_DATABASE": "ws_db",
        "DISUSE_FLAG": "0",
    }


# ---------------------------------------------------------------------------
# フィクスチャ
# ---------------------------------------------------------------------------
@pytest.fixture
def app_context():
    """
    Flaskのrequest contextを生成し、g.appmsg / g.applogger をモック化する。

    post_initial_setting_ansible は @api_filter_admin でラップされており、
    戻り値は make_response() により (res_body(dict), status_code) のタプルになる。
    make_response() は request.url / g.applogger / g.appmsg を参照するため、
    request context と各モックが必要となる。
    """
    app = Flask(__name__)
    with app.test_request_context("/"):
        g.appmsg = MagicMock()
        # get_api_message は result_code をそのまま埋め込んだ文字列を返し、検証を容易にする
        g.appmsg.get_api_message.side_effect = lambda code, *a, **k: f"msg:{code}"
        g.applogger = MagicMock()
        yield


@pytest.fixture
def db_mocks(mocker):
    """DB接続クラスと初期設定処理をモック化する"""
    mock_common_db = MagicMock()
    mock_common_db.table_select.return_value = [_org_db_info()]

    mock_org_db = MagicMock()
    mock_org_db.table_select.return_value = [_workspace_data()]

    mock_ws_db = MagicMock()

    mocker.patch(f"{CONTROLLER}.DBConnectCommon", return_value=mock_common_db)
    mocker.patch(f"{CONTROLLER}.DBConnectOrg", return_value=mock_org_db)
    mocker.patch(f"{CONTROLLER}.DBConnectWs", return_value=mock_ws_db)
    mock_initial = mocker.patch(f"{CONTROLLER}.initial_settings_ansible")

    return {
        "common_db": mock_common_db,
        "org_db": mock_org_db,
        "ws_db": mock_ws_db,
        "initial_settings_ansible": mock_initial,
    }


# ---------------------------------------------------------------------------
# 正常系
# ---------------------------------------------------------------------------
def test_post_success(app_context, db_mocks):
    """全ての値が有効な場合、200 / 000-00000 を返し、各処理が呼ばれる"""
    body = _valid_body()

    res_body, status_code = post_initial_setting_ansible("org1", body)

    assert status_code == 200
    assert res_body["result"] == "000-00000"
    assert res_body["data"] == ""

    # Workspaceごとに初期データ設定が呼ばれる
    db_mocks["initial_settings_ansible"].assert_called_once_with(db_mocks["ws_db"], body)
    # Workspace-DBのトランザクション制御
    db_mocks["ws_db"].db_transaction_start.assert_called_once()
    db_mocks["ws_db"].db_commit.assert_called_once()
    # 共通DBの初期設定データが更新される
    db_mocks["common_db"].table_update.assert_called_once()
    db_mocks["common_db"].db_commit.assert_called_once()


def test_post_success_multiple_workspaces(app_context, db_mocks):
    """Workspaceが複数の場合、Workspace分だけ初期データ設定が呼ばれる"""
    db_mocks["org_db"].table_select.return_value = [
        _workspace_data("ws1"),
        _workspace_data("ws2"),
    ]
    body = _valid_body()

    res_body, status_code = post_initial_setting_ansible("org1", body)

    assert status_code == 200
    assert res_body["result"] == "000-00000"
    assert db_mocks["initial_settings_ansible"].call_count == 2


def test_post_success_without_optional_keys(app_context, db_mocks):
    """任意キー(input_limit_setting/execution_engine_list/initial_data)が無くても成功する"""
    body = {}

    res_body, status_code = post_initial_setting_ansible("org1", body)

    assert status_code == 200
    assert res_body["result"] == "000-00000"


@pytest.mark.parametrize("engine", [
    "Ansible-Core",
    "Ansible Automation Controller",
    "Ansible Execution Agent",
    "Ansible Automation Platform (Cloud)",
])
def test_post_valid_execution_engine(app_context, db_mocks, engine):
    """execution_engine_list に許可された値のみが含まれる場合は成功する"""
    body = _valid_body()
    body["execution_engine_list"] = [engine]

    res_body, status_code = post_initial_setting_ansible("org1", body)

    assert status_code == 200
    assert res_body["result"] == "000-00000"


@pytest.mark.parametrize("input_limit_setting", [True, False])
def test_post_valid_input_limit_setting(app_context, db_mocks, input_limit_setting):
    """input_limit_setting が True/False の場合は成功する"""
    body = _valid_body()
    body["input_limit_setting"] = input_limit_setting

    res_body, status_code = post_initial_setting_ansible("org1", body)

    assert status_code == 200
    assert res_body["result"] == "000-00000"


# ---------------------------------------------------------------------------
# 異常系
# ---------------------------------------------------------------------------
def test_post_organization_not_exist(app_context, db_mocks):
    """organization_id が存在しない場合は 490 / 490-02001 を返す"""
    db_mocks["common_db"].table_select.return_value = []

    res_body, status_code = post_initial_setting_ansible("org_not_exist", _valid_body())

    assert status_code == 490
    assert res_body["result"] == "490-02001"
    # 後続処理は呼ばれない
    db_mocks["initial_settings_ansible"].assert_not_called()
    db_mocks["common_db"].table_update.assert_not_called()


def test_post_invalid_input_limit_setting(app_context, db_mocks):
    """input_limit_setting が True/False 以外の場合は 490 / 490-02002 を返す"""
    body = _valid_body()
    body["input_limit_setting"] = "invalid"

    res_body, status_code = post_initial_setting_ansible("org1", body)

    assert status_code == 490
    assert res_body["result"] == "490-02002"
    db_mocks["initial_settings_ansible"].assert_not_called()


def test_post_empty_execution_engine_list(app_context, db_mocks):
    """execution_engine_list が空の場合は 490 / 490-02003 を返す"""
    body = _valid_body()
    body["execution_engine_list"] = []

    res_body, status_code = post_initial_setting_ansible("org1", body)

    assert status_code == 490
    assert res_body["result"] == "490-02003"
    db_mocks["initial_settings_ansible"].assert_not_called()


def test_post_invalid_execution_engine(app_context, db_mocks):
    """execution_engine_list に許可されない値が含まれる場合は 490 / 490-02003 を返す"""
    body = _valid_body()
    body["execution_engine_list"] = ["InvalidEngine"]

    res_body, status_code = post_initial_setting_ansible("org1", body)

    assert status_code == 490
    assert res_body["result"] == "490-02003"
    db_mocks["initial_settings_ansible"].assert_not_called()


def test_post_missing_parameter(app_context, db_mocks):
    """initial_data のホストに parameter が無い場合は 490 / 490-02004 を返す"""
    body = _valid_body()
    body["initial_data"]["ansible_automation_controller_host_list"] = [
        {"file": {}}
    ]

    res_body, status_code = post_initial_setting_ansible("org1", body)

    assert status_code == 490
    assert res_body["result"] == "490-02004"
    db_mocks["initial_settings_ansible"].assert_not_called()


def test_post_missing_host(app_context, db_mocks):
    """initial_data のホストの parameter に host が無い場合は 490 / 490-02004 を返す"""
    body = _valid_body()
    body["initial_data"]["ansible_automation_controller_host_list"] = [
        {"parameter": {"user": "aws"}}
    ]

    res_body, status_code = post_initial_setting_ansible("org1", body)

    assert status_code == 490
    assert res_body["result"] == "490-02004"
    db_mocks["initial_settings_ansible"].assert_not_called()
