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
FROM qdrant/qdrant:v1.19

ENV QDRANT__TELEMETRY_DISABLED true

RUN mkdir -p /exastro/snapshot/

COPY ./ita_root/ita_qdrant/snapshot/qdrant_common.snapshot /exastro/snapshot/

#
# --force-snapshotで起動時に必ずsnapshotから起動
# --snapshotで起動時に取り込むsnapshotを指定(スナップショットファイル名:コレクション名)
#
CMD [ \
    "./qdrant", \
    "--force-snapshot", \
    "--snapshot",   "/exastro/snapshot/qdrant_common.snapshot:_common" \
]
