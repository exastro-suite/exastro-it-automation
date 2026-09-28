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
ドキュメント検索ツール ("search-docs" / "get-document")

Qdrantにベクトル登録済みのITAドキュメント("_common"コレクション)を、
ベクトル検索とキーワードマッチングを組み合わせたハイブリッド検索で
検索する"search-docs"、および検索結果のsourceパスから元ドキュメントの
全文を取得する"get-document"の2つのツールを提供するモジュール。

登録されているドキュメントは、documents/tools/module/import_document.py・
import_all_documents.py によって documents/en 配下のMarkdownファイルから
チャンク分割・ベクトル化されたものであり、"search-docs"はこれと同じ
環境変数(QDRANT_HOST・QDRANT_PORT・EMBEDDING_MODEL・
EMBEDDING_MODEL_CACHE_PATH)とコレクション名("_common")を使用する。
"get-document"は、search-docsが返すsourceパス(documents/en配下からの
相対パス)から、チャンクではなく元ファイルをそのまま読み込んで全文を返す。
検索対象のパス(DOCUMENT_PATH)は documents/tools/module/settings.py の
DOCUMENT_PATH と同じ値を使用する(値を変更する場合は両方を修正すること)。

ドキュメントの内容自体はユーザーやオーガナイゼーションに関わらず共通
(オーガナイゼーション横断で共有される一般的なITAドキュメント)であり、
アクセス制御が必要な情報を含まないため、@tool デコレーターの
required_roles / required_menu はいずれのツールも指定していない
(誰でも実行可能)。

embeddingモデルのロードとQdrantへの接続は、リクエストごとに行うと
コストが高いため、他のtools/*.pyとは異なりモジュールのimport時
(tools/__init__.py 経由、プロセス起動時に一度だけ)に行い、以降は
モジュールレベルの `model` / `client` を再利用する。この初期化処理は
Flaskのリクエストコンテキスト外で実行されるため、g.applogger は
まだ利用できない(libs/tools_decorator.py のNOTE参照)。そのため、
初期化時のログには標準の `logging.getLogger(__name__)` を使用し、
初期化に失敗した場合はエラー内容を `init_error` に保持しておき、
実際にツールが呼び出された時点(リクエストコンテキスト内、
g.applogger が利用可能)でその内容を含む例外を発生させる
(get-documentはこの初期化に依存しないため、初期化失敗の影響を受けない)。

--------------------------------------------------------------------------
Document search tools ("search-docs" / "get-document")

This module provides two tools: "search-docs", which searches the ITA
documentation already vectorized into Qdrant's "_common" collection using a
hybrid of vector search and keyword matching; and "get-document", which
retrieves the full content of the original document from the "source" path
returned by a search-docs result.

The indexed documents are produced from the Markdown files under
documents/en by documents/tools/module/import_document.py /
import_all_documents.py, chunked and embedded there; "search-docs" searches
that same collection ("_common") using the same environment variables
(QDRANT_HOST, QDRANT_PORT, EMBEDDING_MODEL, EMBEDDING_MODEL_CACHE_PATH).
"get-document" instead reads the original file directly, given the
"source" path (relative to documents/en) returned by search-docs. The path
it searches under (DOCUMENT_PATH) uses the same value as DOCUMENT_PATH in
documents/tools/module/settings.py (keep both in sync if you change it).

The document content itself is common to every user/organization (shared,
general ITA documentation across organizations) and contains no
access-controlled information, so the @tool decorator's required_roles /
required_menu are left unset for both tools (callable by anyone).

Loading the embedding model and connecting to Qdrant on every request would
be expensive, so unlike the other tools/*.py modules, this is done once at
module import time (via tools/__init__.py, once per process startup)
instead, and the module-level `model` / `client` are reused afterwards.
Because this initialization runs outside of a Flask request context,
g.applogger is not yet available (see the NOTE in
libs/tools_decorator.py). Initialization therefore logs through the
standard `logging.getLogger(__name__)`, and if it fails, the error is kept
in `init_error` and only raised as an exception once the tool is actually
invoked (inside a request context, where g.applogger is available).
get-document does not depend on this initialization, so it is unaffected
by an initialization failure.
"""
import logging
import os
import re
from pathlib import Path

from flask import g
from fastembed import TextEmbedding
from qdrant_client import QdrantClient

from libs import tool

logger = logging.getLogger(__name__)

# Qdrant / embeddingモデルの設定。documents/tools/module/settings.py と
# 同じ環境変数名・コレクション名("_common")を使用し、同じインデックスを検索する。
#
# Qdrant / embedding-model configuration. Uses the same environment variable
# names and collection name ("_common") as documents/tools/module/settings.py,
# so this searches the very same index.
QDRANT_HOST = os.environ.get("QDRANT_HOST", "ita_qdrant")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", 6333))
COLLECTION_NAME = "_common"
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL")
EMBEDDING_MODEL_CACHE_PATH = os.environ.get("EMBEDDING_MODEL_CACHE_PATH")

# ハイブリッドスコアにおけるベクトルスコアの重み(0.0-1.0)。値が大きいほど
# ベクトル検索(意味的な類似度)を重視し、小さいほどキーワードマッチングを重視する。
#
# Weight (0.0-1.0) given to the vector score in the hybrid score. The higher
# it is, the more weight is given to vector search (semantic similarity)
# over keyword matching.
HYBRID_SEARCH_ALPHA = float(os.environ.get("HYBRID_SEARCH_ALPHA", "0.9"))

# キーワードスコア計算において、タイトルへのマッチをテキストへのマッチの
# 何倍重視するかの重み。
#
# Weight applied to a title match relative to a text match, when
# calculating the keyword score.
TITLE_MATCH_WEIGHT = float(os.environ.get("TITLE_MATCH_WEIGHT", "3"))

# get-documentがsourceパスの解決に使う検索対象パス。
# documents/tools/module/settings.py の DOCUMENT_PATH と同じ値
# (値を変更する場合は両方を修正すること)。
#
# Path get-document searches to resolve a source path. Same value as
# DOCUMENT_PATH in documents/tools/module/settings.py (keep both in sync if
# you change it).
DOCUMENT_PATH = "/exastro/documents/en"

# モデルのロード・Qdrantへの接続はプロセス起動時に一度だけ行う。
# 失敗した場合はinit_errorに内容を保持し、ツール呼び出し時にエラーとする。
#
# The model load and Qdrant connection are performed once at process
# startup. On failure, the error is kept in init_error and raised when the
# tool is actually invoked.
init_error = None
model = None
client = None

try:
    logger.info("Loading embedding model: %s (cache: %s)...", EMBEDDING_MODEL, EMBEDDING_MODEL_CACHE_PATH)
    model = TextEmbedding(model_name=EMBEDDING_MODEL, cache_dir=EMBEDDING_MODEL_CACHE_PATH)
    logger.info("Embedding model loaded successfully")
except Exception as e:
    init_error = "Failed to load embedding model: {}: {}".format(type(e).__name__, e)
    logger.error(init_error)

try:
    logger.info("Connecting to Qdrant at %s:%s...", QDRANT_HOST, QDRANT_PORT)
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    client.get_collections()
    logger.info("Connected to Qdrant successfully")
except Exception as e:
    error_msg = "Failed to connect to Qdrant: {}: {}".format(type(e).__name__, e)
    init_error = "{}; {}".format(init_error, error_msg) if init_error else error_msg
    logger.error(error_msg)
    client = None


def _extract_keywords(text: str) -> list:
    """
    テキストから英数字(2文字以上)の単語を抽出する。クエリ・ドキュメントとも
    英語のみを対象とするツールのため、日本語の抽出は行わない。

    Extract alphanumeric words (2+ chars) from text. This tool only deals
    with English queries/documents, so Japanese word extraction is not needed.
    """
    return list(set(re.findall(r'\b[a-zA-Z0-9]{2,}\b', text.lower())))


def _calculate_keyword_score(query_keywords: list, text: str, title: str) -> float:
    """
    クエリキーワードがテキスト・タイトルにマッチする度合いをスコア化する
    (タイトルへのマッチはテキストへのマッチよりTITLE_MATCH_WEIGHT倍重視する)

    Score how well the query keywords match the text/title (a title match
    is weighted TITLE_MATCH_WEIGHT times more heavily than a text match).

    Returns:
        float: 0.0-1.0のスコア / a 0.0-1.0 score
    """
    if not query_keywords:
        return 0.0

    text_lower = text.lower()
    title_lower = title.lower()

    match_count = 0
    title_match_count = 0
    for keyword in query_keywords:
        keyword_lower = keyword.lower()
        if keyword_lower in text_lower or keyword in text:
            match_count += 1
        if keyword_lower in title_lower or keyword in title:
            title_match_count += 1

    total_matches = match_count + (title_match_count * TITLE_MATCH_WEIGHT)
    max_possible = len(query_keywords) * (1 + TITLE_MATCH_WEIGHT)
    return min(total_matches / max_possible, 1.0) if max_possible else 0.0


def _hybrid_score(vector_score: float, keyword_score: float, alpha: float) -> float:
    """
    ベクトルスコアとキーワードスコアをalphaの重みで合成する

    Combine the vector score and keyword score, weighted by alpha.
    """
    return alpha * vector_score + (1 - alpha) * keyword_score


def _extract_title(text: str, file: Path) -> str:
    """
    ドキュメントの先頭行からタイトルを取り出す(documents/tools/module/common.py
    の extract_title と同じロジック)。先頭行が空、またはMarkdown見出し記号
    (# ## ### など)を除いた結果が空の場合は、ファイル名(拡張子なし)を使う。

    Extract the title from the document's first line (same logic as
    documents/tools/module/common.py's extract_title). Falls back to the
    filename (without extension) if the first line is empty, or becomes
    empty once Markdown heading markers (# ## ### etc.) are stripped.
    """
    first_line = text.split("\n", 1)[0].strip()
    title = first_line.lstrip("#").strip() if first_line else ""
    return title or file.stem


def _resolve_document_source(source: str) -> Path:
    """
    search-docsが返すsourceパス(documents/en配下からの相対パス)を、
    DOCUMENT_PATH配下の実ファイルに解決する。DOCUMENT_PATH配下に収まらない
    場合(パストラバーサル)はValueErrorを、配下には収まるがファイルが
    存在しない場合はFileNotFoundErrorを送出する。

    Resolve the source path returned by search-docs (relative to
    documents/en) to an actual file under DOCUMENT_PATH. Raises ValueError
    if it escapes DOCUMENT_PATH (path traversal), or FileNotFoundError if
    it stays under DOCUMENT_PATH but the file does not exist.

    Returns:
        Path: 解決済みファイルパス / the resolved file path
    """
    base = Path(DOCUMENT_PATH).resolve()
    target = (base / source).resolve()

    if target != base and base not in target.parents:
        raise ValueError("Invalid source path: '{}'".format(source))

    if not target.is_file():
        raise FileNotFoundError("Document not found: '{}'".format(source))

    return target


@tool(
    name="search-docs",
    description=(
        "Search ITA documentation using semantic search (RAG). Returns relevant document chunks "
        "based on the query. The indexed documents are English, so queries must be written in "
        "English."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query text"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results to return (default: 5, max: 20)",
                "default": 5
            },
            "score_threshold": {
                "type": "number",
                "description": "Minimum similarity score threshold (0.0-1.0, default: 0.6)",
                "default": 0.6
            }
        },
        "required": ["query"]
    }
)
def tool_search_documents(arguments: dict, payload: dict) -> dict:
    """
    ITAドキュメントをハイブリッド検索(ベクトル検索+キーワードマッチング)する

    Search ITA documentation with a hybrid of vector search and keyword matching.

    Parameters:
        arguments (dict): ツールの引数
            - query (str): 検索クエリテキスト(英語) / search query text (English)
            - limit (int, optional): 返す結果の最大数(デフォルト: 5、最大: 20)
                / maximum number of results to return (default: 5, max: 20)
            - score_threshold (float, optional): 最小類似度スコア閾値(デフォルト: 0.6)
                / minimum similarity score threshold (default: 0.6)
        payload (dict): 呼び出しコンテキスト情報 / call context information
            - user_id (str): ユーザーID / user id

    Returns:
        dict: 検索結果 / search results
            - results (list): 検索結果のリスト / list of search results
                - text (str): ドキュメントのテキスト / document chunk text
                - source (str): ソースファイルパス / source file path
                - filename (str): ファイル名 / file name
                - title (str): ドキュメントタイトル / document title
                - directory (str): ディレクトリパス / directory path
                - chunk (int): チャンク番号 / chunk index
                - score (float): ハイブリッド類似度スコア / hybrid similarity score
            - query (str): 検索クエリ / the search query
            - count (int): 結果の数 / number of results
            - message (str): 処理結果メッセージ / result message

    Raises:
        Exception: 初期化に失敗している場合、または検索に失敗した場合
            / if initialization failed, or if the search itself fails
    """
    if model is None or client is None:
        g.applogger.info("search-docs is not properly initialized: {}".format(init_error))
        raise Exception("search-docs tool is not properly initialized: {}".format(init_error))

    query = arguments.get("query", "")
    limit = min(arguments.get("limit", 5), 20)
    score_threshold = arguments.get("score_threshold", 0.6)

    user_id = payload.get("user_id", "unknown")

    g.applogger.info("Parameter query='{}', limit={}, threshold={}".format(
        query, limit, score_threshold
    ))

    try:
        query_keywords = _extract_keywords(query)

        # クエリをベクトル化する
        # Embed the query into a vector
        query_vector = next(model.query_embed(query)).tolist()

        # 再ランキング用に、実際に返す件数より多めに取得する
        # Fetch more results than we will actually return, for re-ranking
        search_limit = min(limit * 3, 60)
        search_result = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=search_limit,
            score_threshold=max(score_threshold - 0.1, 0.4)
        )

        hybrid_results = []
        for hit in search_result.points:
            text = hit.payload.get("text", "")
            title = hit.payload.get("title", "")
            vector_score = hit.score
            keyword_score = _calculate_keyword_score(query_keywords, text, title)
            score = _hybrid_score(vector_score, keyword_score, alpha=HYBRID_SEARCH_ALPHA)

            hybrid_results.append({
                "text": text,
                "source": hit.payload.get("source", ""),
                "filename": hit.payload.get("filename", ""),
                "title": title,
                "directory": hit.payload.get("directory", ""),
                "chunk": hit.payload.get("chunk", 0),
                "score": score
            })

        hybrid_results.sort(key=lambda r: r["score"], reverse=True)
        filtered_results = [r for r in hybrid_results if r["score"] >= score_threshold]

        # 上位スコアから大きく離れた結果は除外する(ただし最低3件は残す)
        # Drop results whose score trails far behind the top score (but keep at least 3 if available)
        results = []
        if filtered_results:
            top_score = filtered_results[0]["score"]
            score_gap_threshold = 0.1

            for result in filtered_results[:limit]:
                if top_score - result["score"] <= score_gap_threshold:
                    results.append(result)
                else:
                    break

            if len(results) < 3 and len(filtered_results) >= 3:
                results = filtered_results[:3]
            elif not results:
                results = filtered_results[:1]

        g.applogger.info("Search completed: {} initial -> {} filtered -> {} final for user={}".format(
            len(search_result.points), len(filtered_results), len(results), user_id
        ))

        return {
            "results": results,
            "query": query,
            "count": len(results),
            "message": "Found {} relevant document chunks.".format(len(results))
        }
    except Exception as e:
        g.applogger.info("search-docs failed: {}".format(e))
        raise Exception("Failed to search documents: {}".format(str(e)))


@tool(
    name="get-document",
    description=(
        "Retrieve the full content of a document by its source path, instead of a "
        "search-relevant chunk. Use the 'source' value returned by search-docs to fetch the "
        "entire original document."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "source": {
                "type": "string",
                "description": "Document source path, as returned in the 'source' field of search-docs results"
            }
        },
        "required": ["source"]
    }
)
def tool_get_document(arguments: dict, payload: dict) -> dict:
    """
    ドキュメントの全文を取得する

    Retrieve the full content of a document.

    Parameters:
        arguments (dict): ツールの引数
            - source (str): ドキュメントのソースパス(search-docsのsourceフィールドと同じ値)
                / the document source path (same value as search-docs' source field)
        payload (dict): 呼び出しコンテキスト情報 / call context information
            - user_id (str): ユーザーID / user id

    Returns:
        dict: 取得結果 / retrieval result
            - source (str): ソースファイルパス / source file path
            - filename (str): ファイル名 / file name
            - title (str): ドキュメントタイトル / document title
            - directory (str): ディレクトリパス / directory path
            - text (str): ドキュメントの全文 / the full document text
            - message (str): 処理結果メッセージ / result message

    Raises:
        Exception: sourceが未指定、パスが不正、ファイルが存在しない、
            または読み込みに失敗した場合 / if source is missing, the path
            is invalid, the file does not exist, or reading it fails
    """
    source = arguments.get("source", "")
    user_id = payload.get("user_id", "unknown")

    g.applogger.info("Parameter source={}".format(source))

    if not source:
        raise Exception("Parameter 'source' is required.")

    try:
        target = _resolve_document_source(source)
    except ValueError as e:
        g.applogger.info("Rejected invalid source path: source='{}'".format(source))
        raise Exception(str(e))
    except FileNotFoundError as e:
        raise Exception(str(e))

    try:
        text = target.read_text(encoding="utf-8")
    except Exception as e:
        g.applogger.info("Failed to read document '{}': {}".format(source, e))
        raise Exception("Failed to read document: {}".format(str(e)))

    g.applogger.info("Document retrieved: source='{}', length={}".format(source, len(text)))

    return {
        "source": source,
        "filename": target.name,
        "title": _extract_title(text, target),
        "directory": target.parent.relative_to(Path(DOCUMENT_PATH).resolve()).as_posix(),
        "text": text,
        "message": "Document retrieved successfully."
    }
