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

import common
import settings


client = common.init_client()


def clean_document(bases, arg: str):
    try:
        base, file = common.resolve_relative_path(bases, arg)
    except ValueError as e:
        print(f"\nSkipping '{arg}': {e}")
        return

    rel_path = file.relative_to(base).as_posix()
    print(f"\nDeleting points for: {rel_path}")
    common.delete_points_by_source(client, rel_path)
    print(f"  - Done: points for '{rel_path}' removed.")


def main():
    if len(sys.argv) < 2:
        print(f"Usage: python {Path(sys.argv[0]).name} <document path> [<document path> ...]")
        print(f"  <document path> is a .md file path, absolute or relative to '{settings.DOCUMENT_PATH}'")
        print(f"  or '{settings.DOCUMENT_PATH_MIRROR}'.")
        print("  The file does not need to still exist on disk.")
        sys.exit(1)

    print(f"Contents path: {settings.DOCUMENT_PATH} (mirror: {settings.DOCUMENT_PATH_MIRROR})")
    print(f"Qdrant host: {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
    print(f"Collection name: {settings.COMMON_COLLECTION_NAME}")

    bases = [Path(settings.DOCUMENT_PATH), Path(settings.DOCUMENT_PATH_MIRROR)]

    for arg in sys.argv[1:]:
        clean_document(bases, arg)

    print("\n✓ Clean complete.")


if __name__ == "__main__":
    main()
