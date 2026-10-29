#!/bin/bash
#
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

BASEDIR=$(dirname $0)
BASENAME=$(basename $0)

. $BASEDIR/config.sh

if [ -z "$1" ]; then
    echo "Usage: $BASENAME document.md [document.md ...]"
    exit 1
fi

#
# ドキュメントのインポート(複数指定された場合は1件ずつ実行する)
#
for doc in "$@"; do
    python3 $BASEDIR/module/import_document.py "$doc"
done

#
# スナップショットの出力
#
python3 $BASEDIR/module/snapshot_all_documents.py "${QDRANT_SNAPSHOT_FILE_PATH}"
