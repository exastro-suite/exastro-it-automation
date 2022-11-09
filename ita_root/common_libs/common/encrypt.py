#   Copyright 2022 NEC Corporation
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

import Crypto.Cipher.AES as AES
import Crypto.Util.Padding as Padding
from Crypto.Random import get_random_bytes
import base64
import os

# initialization vector legth
IV_LENGTH = 16

# AES Block Size
AES_PAD_BLOCK_SIZE = 16

# AES Padding algorithm
AES_PAD_STYLE = 'pkcs7'

# AES encrypt key
ENCRYPT_KEY = base64.b64decode(os.environ['ENCRYPT_KEY'])


def encrypt_str(strdata):
    """Encrypt the string

    Args:
        strdata (str): The string you want to encrypt - 暗号化したい文字列

    Returns:
        str: Encrypted string - 暗号化した文字列
    """
    iv = get_random_bytes(IV_LENGTH)
    aes = AES.new(ENCRYPT_KEY, AES.MODE_CBC, iv)
    encdata = iv + aes.encrypt(Padding.pad(strdata.encode(), AES_PAD_BLOCK_SIZE, AES_PAD_STYLE))
    return (base64.b64encode(encdata)).decode()


def decrypt_str(encstrdata):
    """Decrypt the Encrypted string

    Args:
        encstrdata (str): Encrypted string - 暗号化した文字列

    Returns:
        str: Decrypted string - 復号した文字列
    """
    encdata = base64.b64decode(encstrdata.encode())
    iv = encdata[:IV_LENGTH]
    aes = AES.new(ENCRYPT_KEY, AES.MODE_CBC, iv)
    return Padding.unpad(aes.decrypt(encdata[IV_LENGTH:]), AES_PAD_BLOCK_SIZE, AES_PAD_STYLE).decode()
