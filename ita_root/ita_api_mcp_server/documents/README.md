# 本ディレクトリについて
本ディレクトリ配下にはRAGに登録するドキュメントや、RAG(qdrant)にドキュメントを登録するツールを格納しています

# ディレクトリの説明
| ディレクトリ | 説明 |
| ------------ | ---- |
| ./en         | 英語翻訳済みのドキュメント・この配下のドキュメントをRAGに登録します |
| ./ja         | 翻訳前の日本語ドキュメント　※この配下のドキュメントはRAGに登録しません |
| ./ja/manual  | Exastroのコミュニティーサイトのマニュアルを要約・Markdown化したドキュメント |
| ./ja/menu-reference | 各メニューの使用方法などについてのドキュメント |
| ./ja/openapi | Exastro IT Automationのopen apiのドキュメント |
| ./ja/playbooks-reference-add | デフォルトPlaybookの追加説明ドキュメント |
| ./ja/tool-reference | 各MCPツールの使用方法などについてのドキュメント |
| ./tools   | RAGへの登録用ツール |

# 各ドキュメントの作成・修正
## 英語版ドキュメント(./en配下)の修正
- Claudeのskillで作成します
- 作成内容の変更については日本語ドキュメントの修正やskillの修正で対応すること

## 日本語版マニュアル(./ja/manual)の修正
- Claudeのskillで作成します
- 作成内容の変更についてはマニュアル自体(it-automation-docs)の修正やskillの修正で対応すること

## Menuリファレンスドキュメント（日本語版）の修正
- 各メニュー（menuのrest名.md）毎に作成する
- ただし、内容が膨大になる場合はファイルを分割しても可

## OpenAPIドキュメント（日本語版）の修正
- `exastro-it-automation-dev/ita_root/ita_api_organization/swagger/swagger.yaml`をそのまま格納します

## デフォルトPlaybookの追加説明ドキュメントの修正
- Playbook毎にitemnoXX-{Playbookファイル名}.mdを作成する
- Claudeのskillで英語版のドキュメントを作成する際に、このドキュメントの内容が取り込まれます

## Toolリファレンスドキュメント（日本語版）の修正
- 各ツール(tool名.md)毎に作成する
- ただし、内容が膨大になる場合はファイルを分割しても可


## スナップショット（qdrant_common.snapshot）のコンフリクト
- 複数名でドキュメントの修正を行うと、Qdrantのスナップショットがコンフリクトすることが予想されます<br>
  (exastro-it-automation-dev/ita_root/ita_qdrant/snapshot/qdrant_common.snapshot)
- コンフリクトした場合は、どちらかの修正を破棄して、`tools/import_all_documents.sh`で、スナップショットを再作成してください


# 各ツールについて

| ファイル | 説明 |
| -------- | ---- |
| ./tools/config.sh | 設定情報（Qdrantのスナップショット出力先など） |
| ./tools/import_all_document.sh | すべてのドキュメントを再取り込みし、スナップショットを再作成します ※Qdrant再起動は不要 |
| ./tools/import_document.sh | 指定したドキュメントを取り込み、スナップショットを再作成します ※Qdrant再起動は不要 |
| ./tools/restart_qdrant.sh | スナップショットからQdrantを再起動します |

