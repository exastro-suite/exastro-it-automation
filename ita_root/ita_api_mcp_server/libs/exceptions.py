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
#
"""
mcp_server 用の独自例外定義モジュール

--------------------------------------------------------------------------
Custom exception definitions for mcp_server.
"""


class HTTPException(Exception):
    """
    ダウンストリームのHTTP APIを呼び出した際のエラーを表すカスタム例外。

    Custom exception representing an error returned by a downstream HTTP API call.

    Attributes:
        tool_name (str): ツール名 / tool name
        status_code (int): HTTPステータスコード / HTTP status code
        message (str): エラーメッセージ / error message
        response_body (dict): レスポンスボディ(JSON) / response body (JSON)
    """

    def __init__(self, tool_name: str, response):
        """
        Parameters:
            tool_name (str): ツール名 / tool name
            response (requests.Response): HTTPレスポンスオブジェクト / HTTP response object
        """
        # 呼び出し元のツール名とHTTPステータスコードを保存する
        # Store the caller's tool name and the HTTP status code
        self.tool_name = tool_name
        self.status_code = response.status_code
        self.response_body = {}

        # レスポンスボディをJSONとして解釈できるか試す
        # Try to parse the response body as JSON
        try:
            self.response_body = response.json()
        except Exception:
            # JSONとして解釈できない場合は、テキストのまま保持する
            # ここでは g.applogger が使えない可能性(リクエストコンテキスト外)も
            # 考慮し、ログ出力は行わずテキストを保持するだけにする。
            #
            # If it cannot be parsed as JSON, keep the raw text instead.
            # We avoid logging here because g.applogger may not be available
            # outside of a Flask request context; we simply keep the text.
            self.response_body = {"text": response.text}

        # レスポンスボディの内容からエラーメッセージを組み立てる
        # Build the error message from the response body contents
        error_message = f"HTTP {self.status_code}"

        # response_body に message と result が含まれている場合は、それを使う
        # If response_body contains "message" and "result", use them
        body_message = self.response_body.get("message")
        body_result = self.response_body.get("result")

        if body_message and body_result:
            # messageとresultの両方がある場合はその2つを組み合わせる
            # If both message and result are present, combine them
            error_message = f"{body_message} ({body_result})"
        elif body_message:
            # messageのみある場合はそれを使う
            # If only message is present, use it as-is
            error_message = body_message
        else:
            # どちらもない場合はtool_nameとstatus_codeから組み立てる
            # If neither is present, fall back to tool_name and status_code
            error_message = f"{tool_name} failed: HTTP {self.status_code}"

        self.message = error_message
        super().__init__(error_message)

    def to_dict(self) -> dict:
        """
        例外情報を辞書形式で返す

        Return the exception information as a dict.

        Returns:
            dict: {tool_name, status_code, message, result}
        """
        return {
            "tool_name": self.tool_name,
            "status_code": self.status_code,
            "message": str(self),
            "result": self.response_body
        }
