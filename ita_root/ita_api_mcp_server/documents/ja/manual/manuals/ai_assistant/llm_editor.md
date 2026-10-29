# LLMエディタの機能と設定

LLMエディタは、LLMモデルとの会話を通じて開発支援を行う機能です。使用にはLLMモデルの認証情報が必要です（例: Amazon Bedrock（Claude Code）を利用する場合）。

## 開発支援設定

- **設定登録**: AI選択でAmazon Bedrock（Claude Code）等を選択し、AWS Access Key ID・AWS Secret Access Key・AWS Session Token（SSO利用時は任意）・AWS Regionの認証情報を入力します。続けてモデル選択・モデル初期値を設定します。
- **設定削除**: 削除した設定は復活できないため、削除時は十分注意してください。

## 開発支援機能

- メッセージ送信時にエディタの内容を添付できます。
- コードブロックをクリックすると、その内容をエディタに反映できます（Exastro IT AutomationエンドポイントのプロトコルがHTTPの場合はこの機能を利用できません）。
- 会話履歴はすべてJSON形式ファイルとしてダウンロードできます。
