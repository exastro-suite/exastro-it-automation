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
"""
tools/base64.py (base64-encode / base64-decode) のユニットテスト

異常系では、g.applogger.info の呼び出し回数はチェックしない
(ログ出力を増減しただけでテストが壊れるのは望ましくないため)。
代わりに、送出される例外のメッセージに元のエラー内容が含まれているかどうかで検証する。
"""

import pytest

from tools import base64 as base64_tool


class TestToolBase64Encode:
    def test_encode_success(self, mock_flask_g):
        # 正常系: 通常のテキストがBase64エンコードされること
        result = base64_tool.tool_base64_encode({"text": "hello"}, {})

        assert result["result"] == "aGVsbG8="
        assert result["message"] == "Text encoded to Base64 successfully."

    def test_encode_empty_text(self, mock_flask_g):
        # 境界値: textが未指定の場合は空文字として扱われ、空文字がエンコードされること
        result = base64_tool.tool_base64_encode({}, {})

        assert result["result"] == ""

    def test_encode_failure_raises(self, mock_flask_g):
        # 異常系: text.encode()が失敗した場合、元の例外メッセージ("boom")を含む
        # 例外が発生すること
        class _BadStr:
            def encode(self, *_a, **_kw):
                raise ValueError("boom")

        with pytest.raises(Exception, match="Failed to encode text to Base64: boom"):
            base64_tool.tool_base64_encode({"text": _BadStr()}, {})


class TestToolBase64Decode:
    def test_decode_success(self, mock_flask_g):
        # 正常系: 有効なBase64文字列が元のテキストにデコードされること
        result = base64_tool.tool_base64_decode({"text": "aGVsbG8="}, {})

        assert result["result"] == "hello"
        assert result["message"] == "Base64 string decoded successfully."

    def test_decode_invalid_base64_raises(self, mock_flask_g):
        # 異常系: Base64として不正な文字列の場合に例外が発生すること
        # (binascii.Error / ValueError を捕捉して独自メッセージへ変換する分岐)
        with pytest.raises(Exception, match="Failed to decode Base64 string"):
            base64_tool.tool_base64_decode({"text": "not-valid-base64!!"}, {})

    def test_decode_non_utf8_raises(self, mock_flask_g):
        # 異常系: Base64としては正しいが、デコード結果がUTF-8として解釈できない場合に
        # 例外が発生すること(UnicodeDecodeError を捕捉する分岐)
        import base64 as b64

        invalid_utf8 = b64.b64encode(b"\xff\xfe").decode("ascii")

        with pytest.raises(Exception, match="Decoded content is not valid UTF-8 text"):
            base64_tool.tool_base64_decode({"text": invalid_utf8}, {})
