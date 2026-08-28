# AWS SDK for JavaScript v3 - Bundled Files

このディレクトリには、AWS SDK for JavaScript v3のバンドルファイルが含まれています。

## ファイル

- `aws-bedrock-runtime.bundle.js` - Bedrock Runtime Client（モデル実行用）
- `aws-bedrock.bundle.js` - Bedrock Client（モデル一覧取得用）

## ライセンス

これらのファイルは、AWS SDK for JavaScript v3から派生したものです。

- **ライセンス**: Apache License 2.0
- **著作権**: Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
- **ソースコード**: https://github.com/aws/aws-sdk-js-v3
- **ライセンス全文**: [LICENSE](./LICENSE)

## バンドルの再生成

AWS SDKを更新する場合：

```bash
# 一時ディレクトリで作業
mkdir /tmp/aws-bundle && cd /tmp/aws-bundle
npm init -y
npm install @aws-sdk/client-bedrock-runtime @aws-sdk/client-bedrock esbuild

# エントリーポイント作成
echo "export * from '@aws-sdk/client-bedrock-runtime';" > runtime.js
echo "export * from '@aws-sdk/client-bedrock';" > bedrock.js

# バンドル生成
npx esbuild runtime.js --bundle --format=esm --outfile=aws-bedrock-runtime.bundle.js
npx esbuild bedrock.js --bundle --format=esm --outfile=aws-bedrock.bundle.js

# プロジェクトにコピー
cp *.bundle.js /path/to/this/directory/
```

## 使用方法

```javascript
// Bedrock Runtime (モデル実行)
import { BedrockRuntimeClient, InvokeModelCommand } from '/_/ita/lib/aws-bedrock/aws-bedrock-runtime.bundle.js';

// Bedrock (モデル一覧取得)
import { BedrockClient, ListInferenceProfilesCommand } from '/_/ita/lib/aws-bedrock/aws-bedrock.bundle.js';
```
