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
Base64エンコード・デコードツール ("base64-encode" / "base64-decode")

テキストとBase64文字列を相互変換する、DBアクセスや外部API呼び出しを
伴わない単純なツール。他ツールと異なり実行権限のチェックは不要なため、
@tool デコレーターの required_roles / required_menu は指定していない
(誰でも実行可能)。
  - base64-encode : text(生テキスト)を受け取り、Base64エンコードした
    文字列を返す。
  - base64-decode : text(Base64文字列)を受け取り、デコードした
    生テキストを返す。

--------------------------------------------------------------------------
Base64 encode/decode tools ("base64-encode" / "base64-decode")

Simple tools that convert between raw text and Base64 strings, with no DB
access or external API calls involved. Unlike other tools, no permission
check is required here, so the @tool decorator's required_roles /
required_menu are left unset (callable by anyone).
  - base64-encode : accepts text (raw text) and returns its Base64-encoded
    string.
  - base64-decode : accepts text (a Base64 string) and returns the decoded
    raw text.
"""
import base64
import binascii

from flask import g

from libs import tool


@tool(
    name="base64-encode",
    description="Encode raw text content into a Base64 string.",
    input_schema={
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "Raw text content to encode into Base64."
            }
        },
        "required": ["text"]
    }
)
def tool_base64_encode(arguments: dict, payload: dict) -> dict:
    """
    テキストをBase64形式にエンコードする

    Encode raw text content into a Base64 string.

    Parameters:
        arguments (dict): ツールの引数
            - text (str): エンコード対象の生テキスト / raw text content to encode
        payload (dict): 呼び出しコンテキスト情報(このツールでは未使用)
            / call context information (unused by this tool)

    Returns:
        dict: エンコード結果
            - result (str): Base64エンコードされた文字列 / the Base64-encoded string
            - message (str): 処理結果メッセージ / result message

    Raises:
        Exception: エンコードに失敗した場合 / if encoding fails
    """
    text = arguments.get("text", "")

    # 生テキストをUTF-8のバイト列に変換した上でBase64エンコードする
    # Encode after converting the raw text into UTF-8 bytes
    try:
        encoded = base64.b64encode(text.encode("utf-8")).decode("ascii")
    except Exception as e:
        g.applogger.info("base64-encode failed: {}".format(e))
        raise Exception("Failed to encode text to Base64: {}".format(str(e)))

    return {
        "result": encoded,
        "message": "Text encoded to Base64 successfully."
    }


@tool(
    name="base64-decode",
    description="Decode a Base64 string back into raw text content.",
    input_schema={
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "Base64 string to decode."
            }
        },
        "required": ["text"]
    }
)
def tool_base64_decode(arguments: dict, payload: dict) -> dict:
    """
    Base64形式の文字列をデコードする

    Decode a Base64 string back into raw text content.

    Parameters:
        arguments (dict): ツールの引数
            - text (str): デコード対象のBase64文字列 / Base64 string to decode
        payload (dict): 呼び出しコンテキスト情報(このツールでは未使用)
            / call context information (unused by this tool)

    Returns:
        dict: デコード結果
            - result (str): デコードされた生テキスト / the decoded raw text
            - message (str): 処理結果メッセージ / result message

    Raises:
        Exception: Base64として不正な形式の場合、またはデコード結果が
            UTF-8として解釈できない場合 / if the input is not valid Base64,
            or the decoded content cannot be interpreted as UTF-8
    """
    text = arguments.get("text", "")

    # Base64文字列をデコードし、UTF-8のテキストとして解釈する
    # Decode the Base64 string and interpret the result as UTF-8 text
    try:
        decoded = base64.b64decode(text, validate=True).decode("utf-8")
    except UnicodeDecodeError as e:
        # UnicodeDecodeError は ValueError のサブクラスのため、下の except より先に置く
        # (先に置かないと、常に下のexceptで捕捉されてしまい、このブロックに到達しない)
        g.applogger.info("base64-decode failed: decoded content is not valid UTF-8: {}".format(e))
        raise Exception("Decoded content is not valid UTF-8 text: {}".format(str(e)))
    except (binascii.Error, ValueError) as e:
        g.applogger.info("base64-decode failed: invalid Base64 string: {}".format(e))
        raise Exception("Failed to decode Base64 string: {}".format(str(e)))

    return {
        "result": decoded,
        "message": "Base64 string decoded successfully."
    }
