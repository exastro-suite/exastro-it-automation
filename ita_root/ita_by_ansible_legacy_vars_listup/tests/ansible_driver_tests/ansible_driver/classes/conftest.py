import pytest
import os
import sys
from unittest.mock import MagicMock, patch
from flask import Flask, g

# ita_rootをsys.pathに追加（pytest.iniのpythonpathが効かない場合の対策）
ita_root = '/workspace/exastro-it-automation-dev/ita_root'
if ita_root not in sys.path:
    sys.path.insert(0, ita_root)


@pytest.fixture
def flask_app_context():
    """Flaskアプリケーションコンテキストを作成"""
    flask_app = Flask(__name__)
    with flask_app.app_context():
        yield flask_app


@pytest.fixture
def mock_g(flask_app_context):
    """グローバル変数gをモック化"""
    g.LANGUAGE = "ja"
    g.USER_ID = "test_user_id"
    g.SERVICE_NAME = "test_service"
    g.WORKSPACE_ID = "test_workspace_id"
    g.ORGANIZATION_ID = "test_org_id"

    g.applogger = MagicMock()
    g.appmsg = MagicMock()
    g.appmsg.get_log_message.return_value = "Mocked log message"

    # get_api_message はメッセージコードを含む文字列を返す。
    #   - 本番コードは戻り値を文字列連結してログ出力するため MagicMock のままだと TypeError になる
    #   - コードを含めておくことで、どのメッセージがログ出力されたかをテストで検証できる
    def _get_api_message(code, args=None):
        if args:
            return "{}:{}".format(code, args)
        return "{}".format(code)

    g.appmsg.get_api_message.side_effect = _get_api_message

    return g


@pytest.fixture
def mock_db():
    """データベースアクセスクラスのモック"""
    mock = MagicMock()
    mock.table_update.return_value = True
    return mock


@pytest.fixture
def mock_ans_if_info():
    """Ansible Interface情報のモックデータ"""
    return {
        "SERVICE_ACCOUNT_INFO": None,
        "SERVICE_ACCOUNT_TOKEN": None,
        "ANSIBLE_EXEC_MODE": "1"  # 1: Ansible, 2: AAC, 3: AG, 4: AAP on Cloud
    }


@pytest.fixture
def mock_env_vars():
    """環境変数のモック"""
    with patch.dict(os.environ, {
        'PLATFORM_API_HOST': 'localhost',
        'PLATFORM_API_PORT': '8000',
        'EXTERNAL_URL': 'https://example.com'
    }):
        yield


@pytest.fixture
def create_ansible_exec_files_instance(mock_g, mock_db, mock_ans_if_info, mock_env_vars):
    """CreateAnsibleExecFilesインスタンスを作成するファクトリフィクスチャ"""
    from common_libs.ansible_driver.classes.CreateAnsibleExecFiles import CreateAnsibleExecFiles

    def _create_instance(ans_if_info=None):
        if ans_if_info is None:
            ans_if_info = mock_ans_if_info

        instance = CreateAnsibleExecFiles(
            in_driver_id="L",  # "L": Legacy, "R": Legacy-Role, "P": Pioneer
            in_ans_if_info=ans_if_info,
            in_exec_no="12345",
            in_engine_virtualenv_name="",
            in_ansible_cnf_file="",
            in_objDBCA=mock_db
        )
        return instance

    return _create_instance


# ======================================================================
# SubValueAutoReg.getCMDBdata 用フィクスチャ
# （ビルダー/モック本体は subvalue_autoreg_support.py を参照）
# ======================================================================
@pytest.fixture
def mock_ws_db():
    """WorkspaceDB(WS_DB) のモック。テストごとに新規生成する。"""
    from .subvalue_autoreg_support import MockWsDb
    return MockWsDb()


@pytest.fixture
def make_subvalue_autoreg(mock_g, mock_ws_db):
    """SubValueAutoReg インスタンスを生成するファクトリフィクスチャ。

    - load_table.loadTable を _FakeLoadTable に差し替え（実DBアクセス回避）
    - rest_filter を param_sheets を引くスタブに差し替え
        param_sheets = { menu_name_rest: { row_id(UUID): { COLUMN_NAME_REST: 具体値 } } }

    使い方:
        instance = make_subvalue_autoreg(
            driver_id=AnscConst.DF_LEGACY_ROLE_DRIVER_ID,
            param_sheets={'menu_a': {'row-001': {'column_a': 'value1'}}},
        )
    """
    from unittest.mock import patch
    from common_libs.ansible_driver.classes.SubValueAutoReg import SubValueAutoReg
    from .subvalue_autoreg_support import _FakeLoadTable

    patcher = patch(
        "common_libs.ansible_driver.classes.SubValueAutoReg.load_table.loadTable",
        side_effect=lambda ws_db, menu_name_rest: _FakeLoadTable(ws_db, menu_name_rest),
    )
    patcher.start()

    def _make(driver_id="R", param_sheets=None):
        instance = SubValueAutoReg(in_driver_name=driver_id, ws_db=mock_ws_db)
        sheets = param_sheets if param_sheets is not None else {}
        # rest_filter はテスト対象外の別ユニットのためスタブ化し、
        # 「紐付メニューから取得した具体値」を param_sheets 経由で差し込む。
        instance.rest_filter = \
            lambda WS_DB, obj_load_table: sheets.get(getattr(obj_load_table, 'menu_name_rest', None), {})
        return instance

    yield _make

    patcher.stop()


# ======================================================================
# SubValueAutoReg 結合テスト用フィクスチャ
# （実DBに接続する。基盤は subvalue_autoreg_integration_support.py を参照）
#
# 既定では実行しない。pytest.ini で deselect すると VSCode のテスト一覧から
# ケースごと消えて「テストが無い」と誤読されるため、収集はさせて
# ここで skip する(一覧には skip 理由付きで出る)。
# ======================================================================
@pytest.fixture(scope='module')
def integration_env():
    """実行ゲート + 実DBに接続できる環境変数を os.environ に反映する。

    pytest.ini の env は単体テスト用のダミー(`DB_HOST=unittest-ita-db`)なので、
    結合テストの間だけ実環境の値に差し替える(モジュール終了時に復元)。
    """
    from .subvalue_autoreg_integration_support import gate_reason, resolve_env, storage_root

    reason = gate_reason()
    if reason:
        pytest.skip(reason)

    resolved = resolve_env()
    resolved.setdefault('DB_PORT', '3306')
    mp = pytest.MonkeyPatch()
    for key, value in resolved.items():
        mp.setenv(key, value)
    mp.setenv('STORAGEPATH', storage_root())
    yield resolved
    mp.undo()


@pytest.fixture(scope='module')
def app_context(integration_env):
    """本物の MessageTemplate を載せた Flask アプリケーションコンテキスト。

    単体テストの `mock_g` と違い appmsg は本物にする。
    メッセージ定義そのもの(MSG-00001 の文言など)に依存した実装があるため。
    """
    app = Flask(__name__)
    with app.app_context():
        g.LANGUAGE = 'ja'
        g.USER_ID = '1'
        g.SERVICE_NAME = 'integration_test'
        g.applogger = MagicMock()   # ログ出力は捨てる(必要ならここを差し替える)

        from common_libs.common.message_class import MessageTemplate
        g.appmsg = MessageTemplate(g.LANGUAGE)
        yield app
