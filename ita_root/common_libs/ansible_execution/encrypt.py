# Copyright 2024 NEC Corporation#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# from Crypto.Random import get_random_bytes
from hashlib import pbkdf2_hmac
from common_libs.common.encrypt import encrypt_str, decrypt_str

# salt = get_random_bytes(16)
SALT = b'\xf1\xb7\xf3\xca\t\xc8\xb5\x84\xda\x83\x82\xbf\xc3\x82\x88\xd7'

def generate_key(pass_phrase):
    key = pbkdf2_hmac('sha256', bytes(pass_phrase, encoding='utf-8'), SALT, 50000, int(128 / 8))
    return key

def agent_encrypt(trg_str, pass_phrase):
    key = generate_key(pass_phrase)
    return encrypt_str(trg_str, key)

def agent_decrypt(trg_str, pass_phrase):
    key = generate_key(pass_phrase)
    return decrypt_str(trg_str, key)
