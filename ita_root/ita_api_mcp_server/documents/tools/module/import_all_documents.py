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

from pathlib import Path

import common
import settings


model = common.init_model()
client = common.init_client()


def main():
    print("Starting document indexing process...")
    print(f"Contents path: {settings.DOCUMENT_PATH}")
    print(f"Qdrant host: {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
    print(f"Collection name: {settings.COMMON_COLLECTION_NAME}")

    print("\nEnsuring collection exists...")
    common.ensure_collection(client, model)
    print("Collection ready.")

    base = Path(settings.DOCUMENT_PATH)
    print(f"\nScanning for .md files in {base}...")
    files = sorted(base.rglob("*.md"))
    print(f"Found {len(files)} files to process.")

    points = []

    for file_idx, file in enumerate(files, 1):
        print(f"\n[{file_idx}/{len(files)}] Processing: {file.name}")
        _, file_points = common.build_points_for_file(model, base, file)
        points.extend(file_points)
        print(f"  - Added {len(file_points)} points (total: {len(points)})")

    common.upsert_points(client, points)

    print(f"\n✓ Indexing complete: {len(points)} chunks from {len(files)} files.")


if __name__ == "__main__":
    main()
