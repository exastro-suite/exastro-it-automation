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
tools/search_documents.py (search-docs / get-document) のユニットテスト

tests/conftest.py が fastembed / qdrant_client を sys.modules レベルで
MagicMockに差し替えているため、tools.search_documents は import時に実際の
モデルロード・Qdrant接続を行わない(module-levelの model / client には
MagicMockが入る)。各テストでは monkeypatch.setattr を使って
search_documents.model / search_documents.client、および必要に応じて
search_documents.DOCUMENT_PATH を個別に上書きし、期待する挙動を設定する。

異常系では、g.applogger.info の呼び出し回数はチェックせず、送出される
例外のメッセージ内容で検証する。
"""
from pathlib import Path
from unittest import mock

import pytest

from tools import search_documents


def _make_hit(text="", title="", source="src.md", filename="src.md", directory="dir", chunk=0, score=0.9):
    """client.query_points(...).points の要素を模したオブジェクトを作る"""
    payload = {
        "text": text,
        "title": title,
        "source": source,
        "filename": filename,
        "directory": directory,
        "chunk": chunk,
    }
    hit = mock.Mock()
    hit.payload = payload
    hit.score = score
    return hit


def _make_search_result(hits):
    result = mock.Mock()
    result.points = hits
    return result


def _make_model(vector=None):
    """model.query_embed(query) が呼ばれた際に next(...).tolist() で
    ベクトルを返すダミーmodelを作る"""
    vector = vector if vector is not None else [0.1, 0.2, 0.3]
    vector_obj = mock.Mock()
    vector_obj.tolist.return_value = vector
    model = mock.Mock()
    model.query_embed = mock.Mock(return_value=iter([vector_obj]))
    return model


class TestExtractKeywords:
    def test_extracts_alnum_words_lowercased_deduplicated(self):
        result = search_documents._extract_keywords("Hello World hello, WORLD! foo-bar 1a")
        assert set(result) == {"hello", "world", "foo", "bar", "1a"}

    def test_ignores_single_char_words(self):
        result = search_documents._extract_keywords("a b cd e")
        assert result == ["cd"]

    def test_empty_string_returns_empty_list(self):
        assert search_documents._extract_keywords("") == []

    def test_no_alnum_words_returns_empty_list(self):
        assert search_documents._extract_keywords("!!! --- ...") == []


class TestCalculateKeywordScore:
    def test_no_keywords_returns_zero(self):
        assert search_documents._calculate_keyword_score([], "some text", "some title") == 0.0

    def test_all_keywords_match_title_only(self):
        # タイトルにのみマッチする場合、テキストにもマッチした場合より低いスコアになる
        # (スコア = title_match_count * TITLE_MATCH_WEIGHT / (keyword数 * (1 + TITLE_MATCH_WEIGHT)))
        score = search_documents._calculate_keyword_score(["foo", "bar"], "unrelated text", "foo bar title")
        weight = search_documents.TITLE_MATCH_WEIGHT
        expected = min((2 * weight) / (2 * (1 + weight)), 1.0)
        assert score == pytest.approx(expected)

    def test_all_keywords_match_text_and_title_returns_one(self):
        score = search_documents._calculate_keyword_score(["foo", "bar"], "foo bar text", "foo bar title")
        assert score == 1.0

    def test_all_keywords_match_text_only(self):
        # テキストにのみマッチする場合は最大値(タイトルマッチ込み)より小さいスコアになる
        score = search_documents._calculate_keyword_score(["foo", "bar"], "foo bar text", "unrelated title")
        weight = search_documents.TITLE_MATCH_WEIGHT
        expected = min((2 / (2 * (1 + weight))), 1.0)
        assert score == pytest.approx(expected)

    def test_no_match_returns_zero(self):
        score = search_documents._calculate_keyword_score(["zzz"], "some text", "some title")
        assert score == 0.0

    def test_case_insensitive_match(self):
        score = search_documents._calculate_keyword_score(["Foo"], "this has FOO in it", "title")
        assert score > 0.0

    def test_partial_match(self):
        score = search_documents._calculate_keyword_score(["foo", "zzz"], "foo text", "title")
        assert 0.0 < score < 1.0


class TestHybridScore:
    def test_alpha_one_uses_only_vector_score(self):
        assert search_documents._hybrid_score(0.8, 0.2, alpha=1.0) == pytest.approx(0.8)

    def test_alpha_zero_uses_only_keyword_score(self):
        assert search_documents._hybrid_score(0.8, 0.2, alpha=0.0) == pytest.approx(0.2)

    def test_alpha_midpoint_averages(self):
        assert search_documents._hybrid_score(1.0, 0.0, alpha=0.5) == pytest.approx(0.5)


class TestExtractTitle:
    def test_heading_line_is_used_as_title(self):
        text = "# My Title\nsome body text"
        title = search_documents._extract_title(text, Path("/tmp/doc.md"))
        assert title == "My Title"

    def test_plain_first_line_used_as_title(self):
        text = "Plain Title\nbody"
        title = search_documents._extract_title(text, Path("/tmp/doc.md"))
        assert title == "Plain Title"

    def test_empty_first_line_falls_back_to_filename(self):
        text = "\nbody text here"
        title = search_documents._extract_title(text, Path("/tmp/fallback_name.md"))
        assert title == "fallback_name"

    def test_heading_only_symbols_falls_back_to_filename(self):
        text = "###\nbody text"
        title = search_documents._extract_title(text, Path("/tmp/heading_only.md"))
        assert title == "heading_only"

    def test_empty_text_falls_back_to_filename(self):
        title = search_documents._extract_title("", Path("/tmp/empty.md"))
        assert title == "empty"


class TestResolveDocumentSource:
    def test_resolves_file_within_document_path(self, tmp_path, monkeypatch):
        monkeypatch.setattr(search_documents, "DOCUMENT_PATH", str(tmp_path))
        target_file = tmp_path / "doc.md"
        target_file.write_text("hello")

        resolved = search_documents._resolve_document_source("doc.md")
        assert resolved == target_file.resolve()

    def test_resolves_nested_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(search_documents, "DOCUMENT_PATH", str(tmp_path))
        nested_dir = tmp_path / "sub"
        nested_dir.mkdir()
        nested_file = nested_dir / "doc.md"
        nested_file.write_text("hello")

        resolved = search_documents._resolve_document_source("sub/doc.md")
        assert resolved == nested_file.resolve()

    def test_path_traversal_raises_value_error(self, tmp_path, monkeypatch):
        monkeypatch.setattr(search_documents, "DOCUMENT_PATH", str(tmp_path))
        with pytest.raises(ValueError, match="Invalid source path"):
            search_documents._resolve_document_source("../../etc/passwd")

    def test_missing_file_raises_file_not_found(self, tmp_path, monkeypatch):
        monkeypatch.setattr(search_documents, "DOCUMENT_PATH", str(tmp_path))
        with pytest.raises(FileNotFoundError, match="Document not found"):
            search_documents._resolve_document_source("does_not_exist.md")

    def test_directory_is_not_a_valid_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(search_documents, "DOCUMENT_PATH", str(tmp_path))
        (tmp_path / "subdir").mkdir()
        with pytest.raises(FileNotFoundError, match="Document not found"):
            search_documents._resolve_document_source("subdir")


class TestToolSearchDocuments:
    def test_model_none_raises(self, mock_flask_g, monkeypatch):
        monkeypatch.setattr(search_documents, "model", None)
        monkeypatch.setattr(search_documents, "client", mock.Mock())
        monkeypatch.setattr(search_documents, "init_error", "boom init failure")

        with pytest.raises(Exception, match="search-docs tool is not properly initialized"):
            search_documents.tool_search_documents({"query": "test"}, {"user_id": "u1"})

    def test_client_none_raises(self, mock_flask_g, monkeypatch):
        monkeypatch.setattr(search_documents, "model", mock.Mock())
        monkeypatch.setattr(search_documents, "client", None)
        monkeypatch.setattr(search_documents, "init_error", "qdrant unreachable")

        with pytest.raises(Exception, match="qdrant unreachable"):
            search_documents.tool_search_documents({"query": "test"}, {"user_id": "u1"})

    def test_success_returns_filtered_sorted_results(self, mock_flask_g, monkeypatch):
        hits = [
            _make_hit(text="apple banana", title="Fruit Guide", source="a.md", score=0.95),
            _make_hit(text="something else", title="Other", source="b.md", score=0.7),
        ]
        monkeypatch.setattr(search_documents, "model", _make_model())
        fake_client = mock.Mock()
        fake_client.query_points = mock.Mock(return_value=_make_search_result(hits))
        monkeypatch.setattr(search_documents, "client", fake_client)

        result = search_documents.tool_search_documents(
            {"query": "apple", "limit": 5, "score_threshold": 0.5}, {"user_id": "u1"}
        )

        assert result["query"] == "apple"
        assert result["count"] == len(result["results"])
        assert result["message"] == "Found {} relevant document chunks.".format(result["count"])
        # 結果はスコアの降順であること
        scores = [r["score"] for r in result["results"]]
        assert scores == sorted(scores, reverse=True)
        for r in result["results"]:
            assert set(r.keys()) == {"text", "source", "filename", "title", "directory", "chunk", "score"}

    def test_default_limit_and_threshold(self, mock_flask_g, monkeypatch):
        hits = [_make_hit(text="foo", title="Foo Title", score=0.9)]
        monkeypatch.setattr(search_documents, "model", _make_model())
        fake_client = mock.Mock()
        fake_client.query_points = mock.Mock(return_value=_make_search_result(hits))
        monkeypatch.setattr(search_documents, "client", fake_client)

        result = search_documents.tool_search_documents({"query": "foo"}, {})

        assert result["query"] == "foo"
        # デフォルトのscore_threshold(0.6)を上回るのでヒットが1件返る
        assert result["count"] == 1

        # query_pointsに渡されたlimit/score_thresholdの計算値を確認する
        _, kwargs = fake_client.query_points.call_args
        assert kwargs["limit"] == min(5 * 3, 60)
        assert kwargs["score_threshold"] == max(0.6 - 0.1, 0.4)

    def test_limit_is_clamped_to_max_20(self, mock_flask_g, monkeypatch):
        hits = [_make_hit(text="foo", title="Foo", score=0.9)]
        monkeypatch.setattr(search_documents, "model", _make_model())
        fake_client = mock.Mock()
        fake_client.query_points = mock.Mock(return_value=_make_search_result(hits))
        monkeypatch.setattr(search_documents, "client", fake_client)

        result = search_documents.tool_search_documents({"query": "foo", "limit": 1000}, {})

        _, kwargs = fake_client.query_points.call_args
        # limit自体は20にクランプされ、search_limitはlimit*3(=60)を超えないように60にもクランプされる
        assert kwargs["limit"] == 60
        assert result["count"] <= 20

    def test_no_results_above_threshold_returns_empty(self, mock_flask_g, monkeypatch):
        hits = [_make_hit(text="foo", title="Foo", score=0.2)]
        monkeypatch.setattr(search_documents, "model", _make_model())
        fake_client = mock.Mock()
        fake_client.query_points = mock.Mock(return_value=_make_search_result(hits))
        monkeypatch.setattr(search_documents, "client", fake_client)

        result = search_documents.tool_search_documents({"query": "foo", "score_threshold": 0.6}, {})

        assert result["results"] == []
        assert result["count"] == 0
        assert result["message"] == "Found 0 relevant document chunks."

    def test_gap_filtering_keeps_close_scores_only(self, mock_flask_g, monkeypatch):
        # top scoreに近い(gap<=0.1)結果だけがresultsに残り、それが既に3件以上なので
        # 「最低3件は残す」バックフィルは働かず、乖離した結果はそのまま除外されることを確認する
        hits = [
            _make_hit(text="a", title="A", source="a.md", score=0.99),
            _make_hit(text="b", title="B", source="b.md", score=0.95),
            _make_hit(text="c", title="C", source="c.md", score=0.90),
            _make_hit(text="d", title="D", source="d.md", score=0.60),
        ]
        monkeypatch.setattr(search_documents, "model", _make_model())
        fake_client = mock.Mock()
        fake_client.query_points = mock.Mock(return_value=_make_search_result(hits))
        monkeypatch.setattr(search_documents, "client", fake_client)

        result = search_documents.tool_search_documents(
            {"query": "xy", "limit": 5, "score_threshold": 0.5}, {}
        )

        sources = [r["source"] for r in result["results"]]
        assert sources == ["a.md", "b.md", "c.md"]

    def test_gap_filtering_backfills_to_minimum_three(self, mock_flask_g, monkeypatch):
        # gapフィルタで1件しか残らなくても、filtered_resultsが3件以上あれば
        # 上位3件まで復元されることを確認する
        hits = [
            _make_hit(text="a", title="A", source="a.md", score=0.99),
            _make_hit(text="b", title="B", source="b.md", score=0.75),
            _make_hit(text="c", title="C", source="c.md", score=0.60),
        ]
        monkeypatch.setattr(search_documents, "model", _make_model())
        fake_client = mock.Mock()
        fake_client.query_points = mock.Mock(return_value=_make_search_result(hits))
        monkeypatch.setattr(search_documents, "client", fake_client)

        result = search_documents.tool_search_documents(
            {"query": "xy", "limit": 5, "score_threshold": 0.5}, {}
        )

        sources = {r["source"] for r in result["results"]}
        assert sources == {"a.md", "b.md", "c.md"}

    def test_gap_filtering_keeps_at_least_one_when_fewer_than_three_available(self, mock_flask_g, monkeypatch):
        # filtered_resultsが2件しかなく、gapフィルタで0件になった場合は上位1件が返る
        hits = [
            _make_hit(text="a", title="A", source="a.md", score=0.99),
            _make_hit(text="b", title="B", source="b.md", score=0.55),
        ]
        monkeypatch.setattr(search_documents, "model", _make_model())
        fake_client = mock.Mock()
        fake_client.query_points = mock.Mock(return_value=_make_search_result(hits))
        monkeypatch.setattr(search_documents, "client", fake_client)

        result = search_documents.tool_search_documents(
            {"query": "a", "limit": 5, "score_threshold": 0.5}, {}
        )

        assert result["count"] == 1
        assert result["results"][0]["source"] == "a.md"

    def test_limit_zero_falls_back_to_top_one_result(self, mock_flask_g, monkeypatch):
        # limit=0の場合、gapフィルタのループ自体が実行されずresultsが空のままとなり、
        # filtered_resultsが3件未満なので「最低3件に復元」は働かず、
        # 代わりに上位1件だけが返る分岐(results = filtered_results[:1])を確認する
        hits = [_make_hit(text="a", title="A", source="a.md", score=0.9)]
        monkeypatch.setattr(search_documents, "model", _make_model())
        fake_client = mock.Mock()
        fake_client.query_points = mock.Mock(return_value=_make_search_result(hits))
        monkeypatch.setattr(search_documents, "client", fake_client)

        result = search_documents.tool_search_documents(
            {"query": "xy", "limit": 0, "score_threshold": 0.5}, {}
        )

        assert result["count"] == 1
        assert result["results"][0]["source"] == "a.md"

    def test_query_embed_failure_raises_wrapped_exception(self, mock_flask_g, monkeypatch):
        broken_model = mock.Mock()
        broken_model.query_embed = mock.Mock(side_effect=RuntimeError("embed exploded"))
        monkeypatch.setattr(search_documents, "model", broken_model)
        monkeypatch.setattr(search_documents, "client", mock.Mock())

        with pytest.raises(Exception, match="Failed to search documents: embed exploded"):
            search_documents.tool_search_documents({"query": "foo"}, {})

    def test_query_points_failure_raises_wrapped_exception(self, mock_flask_g, monkeypatch):
        monkeypatch.setattr(search_documents, "model", _make_model())
        fake_client = mock.Mock()
        fake_client.query_points = mock.Mock(side_effect=RuntimeError("qdrant down"))
        monkeypatch.setattr(search_documents, "client", fake_client)

        with pytest.raises(Exception, match="Failed to search documents: qdrant down"):
            search_documents.tool_search_documents({"query": "foo"}, {})

    def test_missing_query_defaults_to_empty_string(self, mock_flask_g, monkeypatch):
        monkeypatch.setattr(search_documents, "model", _make_model())
        fake_client = mock.Mock()
        fake_client.query_points = mock.Mock(return_value=_make_search_result([]))
        monkeypatch.setattr(search_documents, "client", fake_client)

        result = search_documents.tool_search_documents({}, {})

        assert result["query"] == ""
        assert result["results"] == []


class TestToolGetDocument:
    def test_missing_source_raises(self, mock_flask_g):
        with pytest.raises(Exception, match="Parameter 'source' is required."):
            search_documents.tool_get_document({}, {"user_id": "u1"})

    def test_empty_source_raises(self, mock_flask_g):
        with pytest.raises(Exception, match="Parameter 'source' is required."):
            search_documents.tool_get_document({"source": ""}, {"user_id": "u1"})

    def test_path_traversal_raises(self, mock_flask_g, tmp_path, monkeypatch):
        monkeypatch.setattr(search_documents, "DOCUMENT_PATH", str(tmp_path))
        with pytest.raises(Exception, match="Invalid source path"):
            search_documents.tool_get_document({"source": "../outside.md"}, {"user_id": "u1"})

    def test_missing_file_raises(self, mock_flask_g, tmp_path, monkeypatch):
        monkeypatch.setattr(search_documents, "DOCUMENT_PATH", str(tmp_path))
        with pytest.raises(Exception, match="Document not found"):
            search_documents.tool_get_document({"source": "nope.md"}, {"user_id": "u1"})

    def test_success_returns_full_document(self, mock_flask_g, tmp_path, monkeypatch):
        monkeypatch.setattr(search_documents, "DOCUMENT_PATH", str(tmp_path))
        sub_dir = tmp_path / "guides"
        sub_dir.mkdir()
        doc_file = sub_dir / "intro.md"
        doc_file.write_text("# Intro Title\nSome content here.")

        result = search_documents.tool_get_document({"source": "guides/intro.md"}, {"user_id": "u1"})

        assert result["source"] == "guides/intro.md"
        assert result["filename"] == "intro.md"
        assert result["title"] == "Intro Title"
        assert result["directory"] == "guides"
        assert result["text"] == "# Intro Title\nSome content here."
        assert result["message"] == "Document retrieved successfully."

    def test_success_root_level_document_directory_is_empty(self, mock_flask_g, tmp_path, monkeypatch):
        monkeypatch.setattr(search_documents, "DOCUMENT_PATH", str(tmp_path))
        doc_file = tmp_path / "root.md"
        doc_file.write_text("Root Doc\ncontent")

        result = search_documents.tool_get_document({"source": "root.md"}, {"user_id": "u1"})

        assert result["directory"] == "."
        assert result["title"] == "Root Doc"

    def test_read_failure_raises_wrapped_exception(self, mock_flask_g, tmp_path, monkeypatch):
        monkeypatch.setattr(search_documents, "DOCUMENT_PATH", str(tmp_path))
        doc_file = tmp_path / "bad_encoding.md"
        # 有効なUTF-8として読めないバイト列を書き込み、read_text(encoding="utf-8")で
        # UnicodeDecodeErrorが発生する状況を作る
        doc_file.write_bytes(b"\xff\xfe\x00invalid")

        with pytest.raises(Exception, match="Failed to read document"):
            search_documents.tool_get_document({"source": "bad_encoding.md"}, {"user_id": "u1"})

    def test_missing_user_id_defaults_to_unknown(self, mock_flask_g, tmp_path, monkeypatch):
        monkeypatch.setattr(search_documents, "DOCUMENT_PATH", str(tmp_path))
        doc_file = tmp_path / "doc.md"
        doc_file.write_text("Doc Title\nbody")

        result = search_documents.tool_get_document({"source": "doc.md"}, {})

        assert result["title"] == "Doc Title"
