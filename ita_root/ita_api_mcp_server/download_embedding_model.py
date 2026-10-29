#!/usr/bin/env python3

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
Pre-download the fastembed embedding model for offline use.
Run this script when network is available to cache the model locally.
"""
import argparse
from fastembed import TextEmbedding

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "--model-name",
    required=True,
    help="Name of the fastembed model to download",
)
parser.add_argument(
    "--cache-path",
    required=True,
    help="Directory to cache the downloaded model in",
)
args = parser.parse_args()

MODEL_NAME = args.model_name
MODEL_CACHE_PATH = args.cache_path

print(f"Downloading model: {MODEL_NAME}")
print(f"Cache path: {MODEL_CACHE_PATH}")

try:
    model = TextEmbedding(model_name=MODEL_NAME, cache_dir=MODEL_CACHE_PATH)
    print(f"\n✓ Model downloaded successfully to {MODEL_CACHE_PATH}")

    # Test the model
    test_text = "This is a test sentence."
    embedding = next(model.embed([test_text]))
    print(f"✓ Model test successful (embedding dimension: {len(embedding)})")

except Exception as e:
    print(f"\n✗ ERROR: Failed to download model: {e}")
    raise
