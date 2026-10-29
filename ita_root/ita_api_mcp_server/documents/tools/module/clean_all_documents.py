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

from qdrant_client import QdrantClient

import settings


print("Connecting to Qdrant...")
client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
print("Connected to Qdrant.")


def main():
    print(f"Qdrant host: {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
    print(f"Collection name: {settings.COMMON_COLLECTION_NAME}")

    collections = [c.name for c in client.get_collections().collections]
    if settings.COMMON_COLLECTION_NAME not in collections:
        print(f"\nCollection '{settings.COMMON_COLLECTION_NAME}' does not exist. Nothing to clean.")
        return

    print(f"\nDeleting collection '{settings.COMMON_COLLECTION_NAME}'...")
    client.delete_collection(collection_name=settings.COMMON_COLLECTION_NAME)
    print("Collection deleted.")

    print("\n✓ All registered documents have been removed.")


if __name__ == "__main__":
    main()
