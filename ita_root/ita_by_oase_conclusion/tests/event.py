#   Copyright 2025 NEC Corporation
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

from tests.common import create_event

# 参考データ
e001 = create_event(
    "pattern",
    "e001",
    fetched_time_offset=-15,
    ttl=20,
    custom_labels={
        "node": "z01",
        "msg": "[systemA] Httpd Down",
        "_exastro_host": "systemA",
        "service": "Httpd",
        "status": "Down",
        "severity": "3",
        "excluded_flg": "0",
    },
)
e002 = create_event(
    "pattern",
    "e002",
    fetched_time_offset=-10,
    ttl=20,
    custom_labels={
        "node": "z01",
        "msg": "[systemA] Httpd Down",
        "_exastro_host": "systemA",
        "service": "Httpd",
        "status": "Down",
        "severity": "3",
        "excluded_flg": "0",
    },
)
e003 = create_event(
    "pattern",
    "e003",
    fetched_time_offset=-5,
    ttl=20,
    custom_labels={
        "node": "z01",
        "msg": "[systemA] Httpd Down",
        "_exastro_host": "systemA",
        "service": "Httpd",
        "status": "Down",
        "severity": "3",
        "excluded_flg": "0",
    },
)
e004 = create_event(
    "pattern",
    "e004",
    fetched_time_offset=-15,
    ttl=20,
    custom_labels={
        "node": "z01",
        "msg": "[systemA] Httpd Down",
        "_exastro_host": "systemB",
        "service": "Httpd",
        "status": "Down",
        "severity": "3",
        "excluded_flg": "0",
    },
)
e005 = create_event(
    "pattern",
    "e005",
    fetched_time_offset=-10,
    ttl=20,
    custom_labels={
        "node": "z01",
        "msg": "[systemA] Httpd Down",
        "_exastro_host": "systemB",
        "service": "Httpd",
        "status": "Down",
        "severity": "3",
        "excluded_flg": "0",
    },
)
