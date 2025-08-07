import os
import pytest
from unittest.mock import MagicMock
import connexion
from flask import g


@pytest.fixture(scope='session')
def app_context_with_mock_g():
    """
    Connexionで作成されたFlaskコンテキストとg.appmsgモックを生成するフィクスチャ
    """
    # Connexionを使ってFlaskアプリケーションインスタンスを作成
    app_root_dir = os.path.dirname(os.path.dirname(__file__))
    connexion_app = connexion.FlaskApp(__name__, specification_dir=f'{app_root_dir}/swagger/')
    connexion_app.add_api('swagger.yaml')

    # ここでbefore_request_handlerなどの設定を行う（必要に応じて）
    # from libs.organization_common import before_request_handler
    # connexion_app.app.before_request(before_request_handler)

    # Flaskアプリのコンテキストを作成
    ctx = connexion_app.app.app_context()
    ctx.push()

    # g.appmsgをモック化
    g.appmsg = MagicMock()

    yield  # ここでテスト関数を実行

    # テスト終了後にコンテキストをクリーンアップ
    ctx.pop()
