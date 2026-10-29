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

import sys
from pathlib import Path

import httpx

import common
import settings


client = common.init_client()


def resolve_output_path(arg: str, snapshot_name: str) -> Path:
    path = Path(arg)
    # Treat the argument as a directory (existing dir, or path ending with
    # a separator) and place the snapshot under it using its own filename;
    # otherwise treat it as the exact output file path.
    if path.is_dir() or arg.endswith(("/", "\\")):
        path.mkdir(parents=True, exist_ok=True)
        return path / snapshot_name
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def download_snapshot(collection_name: str, snapshot_name: str, output_path: Path):
    url = (
        f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}"
        f"/collections/{collection_name}/snapshots/{snapshot_name}"
    )
    with httpx.stream("GET", url, timeout=None) as response:
        response.raise_for_status()
        with output_path.open("wb") as f:
            for chunk in response.iter_bytes():
                f.write(chunk)


def main():
    if len(sys.argv) < 2:
        print(f"Usage: python {Path(sys.argv[0]).name} <output path>")
        print("  <output path> is either a directory (the snapshot's own filename is used)")
        print("  or the exact file path to save the snapshot to.")
        sys.exit(1)

    output_arg = sys.argv[1]

    print(f"Qdrant host: {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
    print(f"Collection name: {settings.COMMON_COLLECTION_NAME}")

    print("\nCreating snapshot...")
    snapshot = client.create_snapshot(collection_name=settings.COMMON_COLLECTION_NAME)
    if snapshot is None:
        print("ERROR: Failed to create snapshot.")
        sys.exit(1)
    print(f"  - Snapshot created: {snapshot.name} ({snapshot.size} bytes)")

    output_path = resolve_output_path(output_arg, snapshot.name)
    print(f"\nDownloading snapshot to '{output_path}'...")
    download_snapshot(settings.COMMON_COLLECTION_NAME, snapshot.name, output_path)

    print(f"\n✓ Snapshot saved: {output_path}")


if __name__ == "__main__":
    main()
