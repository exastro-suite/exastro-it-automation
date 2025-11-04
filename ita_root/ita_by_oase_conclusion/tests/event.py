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


def create_events(event_ids: list[str], pattern_name: str) -> list[dict]:
    """eventリスト作成

    Args:
        event_ids (list[str]): イベント番号
        pattern_name (str): 試験パターン

    Returns:
        list[dict]: eventリスト
    """
    events = []
    for event_id in event_ids:
        event = create_event(
            pattern_name,
            event_id,
            fetched_time_offset=event_templates[event_id]['fetched_time_offset'],
            ttl=event_templates[event_id]['ttl'],
            custom_labels=event_templates[event_id]['custom_labels'].deepcopy(),
        )
        events.append(event)
    return events


# pytest用イベント定義
event_templates = {}
event_templates["e001"] = {
    "ttl": 20,
    "fetched_time_offset": -15,
    "custom_labels": {
        "node": "z01",
        "msg": "[systemA] Httpd Down",
        "_exastro_host": "systemA",
        "service": "Httpd",
        "status": "Down",
        "severity": "3",
        "excluded_flg": "0",
    },
}
event_templates["e002"] = {
    "ttl": 20,
    "fetched_time_offset": -10,
    "custom_labels": {
        "node": "z01",
        "msg": "[systemA] Httpd Down",
        "_exastro_host": "systemA",
        "service": "Httpd",
        "status": "Down",
        "severity": "3",
        "excluded_flg": "0",
    },
}
event_templates["e003"] = {
    "ttl": 20,
    "fetched_time_offset": -5,
    "custom_labels": {
        "node": "z01",
        "msg": "[systemA] Httpd Down",
        "_exastro_host": "systemA",
        "service": "Httpd",
        "status": "Down",
        "severity": "3",
        "excluded_flg": "0",
    },
}
event_templates["e003a"] = {
    "ttl": 20,
    "fetched_time_offset": -5,
    "custom_labels": {
        "node": "z01",
        "msg": "[systemA] Httpd Down",
        "_exastro_host": "systemA",
        "service": "Httpd",
        "status": "Down",
        "severity": "3",
        "excluded_flg": "0",
    },
}
event_templates["e004"] = {
    "ttl": 20,
    "fetched_time_offset": -15,
    "custom_labels": {
        "node": "z01",
        "msg": "[systemB] Httpd Down",
        "_exastro_host": "systemB",
        "service": "Httpd",
        "status": "Down",
        "severity": "3",
        "excluded_flg": "0",
    },
}
event_templates["e005"] = {
    "ttl": 20,
    "fetched_time_offset": -10,
    "custom_labels": {
        "node": "z01",
        "msg": "[systemB] Httpd Down",
        "_exastro_host": "systemB",
        "service": "Httpd",
        "status": "Down",
        "severity": "3",
        "excluded_flg": "0",
    },
}
event_templates["e005a"] = {
    "ttl": 20,
    "fetched_time_offset": 15,
    "custom_labels": {
        "node": "z01",
        "msg": "[systemB] Httpd Down",
        "_exastro_host": "systemB",
        "service": "Httpd",
        "status": "Down",
        "severity": "3",
        "excluded_flg": "0",
    },
}
event_templates["e005b"] = {
    "ttl": 20,
    "fetched_time_offset": 15,
    "custom_labels": {
        "node": "z01",
        "msg": "[systemB] Httpd Down",
        "_exastro_host": "systemB",
        "service": "Httpd",
        "status": "Down",
        "severity": "3",
        "excluded_flg": "0",
    },
}
event_templates["e005c"] = {
    "ttl": 20,
    "fetched_time_offset": 15,
    "custom_labels": {
        "node": "z01",
        "msg": "[systemB] Httpd Down -exclude",
        "_exastro_host": "systemB",
        "service": "Httpd",
        "status": "Down",
        "severity": "3",
        "excluded_flg": "1",
    },
}
event_templates["e005d"] = {
    "ttl": 20,
    "fetched_time_offset": 15,
    "custom_labels": {
        "node": "z01",
        "msg": "[systemB] Httpd Down -exclude",
        "_exastro_host": "systemB",
        "service": "Httpd",
        "status": "Down",
        "severity": "3",
        "excluded_flg": "1",
    },
}
event_templates["e005e"] = {
    "ttl": 20,
    "fetched_time_offset": 0,
    "custom_labels": {
        "node": "z01",
        "msg": "[systemB] Httpd Down -exclude",
        "_exastro_host": "systemB",
        "service": "Httpd",
        "status": "Down",
        "severity": "3",
        "excluded_flg": "1",
    },
}
event_templates["e005f"] = {
    "ttl": 20,
    "fetched_time_offset": 0,
    "custom_labels": {
        "node": "z01",
        "msg": "[systemB] Httpd Down -exclude",
        "_exastro_host": "systemB",
        "service": "Httpd",
        "status": "Down",
        "severity": "3",
        "excluded_flg": "1",
    },
}
event_templates["e006"] = {
    "ttl": 20,
    "fetched_time_offset": -19,
    "custom_labels": {
        "node": "Z02",
        "msg": "[systemC] Mysqld Down",
        "_exastro_host": "systemC",
        "service": "Mysqld",
        "status": "Down",
        "severity": "3",
        "excluded_flg": "0",
    },
}
event_templates["e007"] = {
    "ttl": 20,
    "fetched_time_offset": -15,
    "custom_labels": {
        "node": "Z02",
        "msg": "[systemC] Mysqld Down",
        "_exastro_host": "systemC",
        "service": "Mysqld",
        "status": "Down",
        "severity": "3",
        "excluded_flg": "0",
    },
}
event_templates["e008"] = {
    "ttl": 20,
    "fetched_time_offset": 6,
    "custom_labels": {
        "node": "Z02",
        "msg": "[systemC] Mysqld Down",
        "_exastro_host": "systemC",
        "service": "Mysqld",
        "status": "Down",
        "severity": "3",
        "excluded_flg": "0",
    },
}
event_templates["e009"] = {
    "ttl": 20,
    "fetched_time_offset": 7,
    "custom_labels": {
        "node": "Z02",
        "msg": "[systemC] Mysqld Down -exclude",
        "_exastro_host": "systemC",
        "service": "Mysqld",
        "status": "Down",
        "severity": "3",
        "excluded_flg": "1",
    },
}
event_templates["e014a"] = {
    "ttl": 20,
    "fetched_time_offset": -40,
    "custom_labels": {
        "node": "Z02",
        "msg": "[systemC] Mysqld Down",
        "_exastro_host": "systemC",
        "service": "Mysqld",
        "status": "Down",
        "severity": "3",
        "excluded_flg": "0",
    },
}
event_templates["e014b"] = {
    "ttl": 20,
    "fetched_time_offset": -34,
    "custom_labels": {
        "node": "Z02",
        "msg": "[systemC] Mysqld Down",
        "_exastro_host": "systemC",
        "service": "Mysqld",
        "status": "Down",
        "severity": "3",
        "excluded_flg": "0",
    },
}
event_templates["e014c"] = {
    "ttl": 20,
    "fetched_time_offset": -34,
    "custom_labels": {
        "node": "Z02",
        "msg": "[systemC] Mysqld Down",
        "_exastro_host": "systemC",
        "service": "Mysqld",
        "status": "Down",
        "severity": "3",
        "excluded_flg": "0",
    },
}
event_templates["e014d"] = {
    "ttl": 20,
    "fetched_time_offset": -5,
    "custom_labels": {
        "node": "Z02",
        "msg": "[systemC] Mysqld Down",
        "_exastro_host": "systemC",
        "service": "Mysqld",
        "status": "Down",
        "severity": "3",
        "excluded_flg": "0",
    },
}
event_templates["e014e"] = {
    "ttl": 20,
    "fetched_time_offset": -5,
    "custom_labels": {
        "node": "Z02",
        "msg": "[systemC] Mysqld Down",
        "_exastro_host": "systemC",
        "service": "Mysqld",
        "status": "Down",
        "severity": "3",
        "excluded_flg": "0",
    },
}
event_templates["e010"] = {
    "ttl": 20,
    "fetched_time_offset": -30,
    "custom_labels": {
        "node": "Z02",
        "msg": "[systemC] Disk Full",
        "_exastro_host": "systemC",
        "service": "Disk",
        "status": "Full",
        "severity": "3",
        "excluded_flg": "0",
    },
}
event_templates["e011"] = {
    "ttl": 20,
    "fetched_time_offset": -25,
    "custom_labels": {
        "node": "Z02",
        "msg": "[systemC] Disk Full (95%)",
        "_exastro_host": "systemC",
        "service": "Disk",
        "status": "Full",
        "severity": "3",
        "excluded_flg": "0",
    },
}
event_templates["e012"] = {
    "ttl": 20,
    "fetched_time_offset": -10,
    "custom_labels": {
        "node": "Z02",
        "msg": "[systemC] Disk Full (95%) -exclude",
        "_exastro_host": "systemC",
        "service": "Disk",
        "status": "Full",
        "severity": "3",
        "excluded_flg": "1",
    },
}
event_templates["e013"] = {
    "ttl": 20,
    "fetched_time_offset": -5,
    "custom_labels": {
        "node": "Z02",
        "msg": "[systemC] Disk Full (95%)",
        "_exastro_host": "systemC",
        "service": "Disk",
        "status": "Full",
        "severity": "3",
        "excluded_flg": "0",
    },
}
event_templates["e014"] = {
    "ttl": 20,
    "fetched_time_offset": 0,
    "custom_labels": {
        "node": "Z02",
        "msg": "[systemC] Disk Full",
        "_exastro_host": "systemC",
        "service": "Disk",
        "status": "Full",
        "severity": "3",
        "excluded_flg": "0",
    },
}
event_templates["e015"] = {
    "ttl": 20,
    "fetched_time_offset": -30,
    "custom_labels": {"node": "z10", "type": "a"},
}
event_templates["e015a"] = {
    "ttl": 20,
    "fetched_time_offset": -30,
    "custom_labels": {"node": "z10", "type": "a"},
}
event_templates["e016"] = {
    "ttl": 20,
    "fetched_time_offset": -5,
    "custom_labels": {"node": "z11", "type": "a"},
}
event_templates["e017"] = {
    "ttl": 20,
    "fetched_time_offset": 7,
    "custom_labels": {"node": "z11", "type": "a"},
}
event_templates["e017a"] = {
    "ttl": 20,
    "fetched_time_offset": -2,
    "custom_labels": {"node": "z11", "type": "a"},
}
event_templates["e017b"] = {
    "ttl": 20,
    "fetched_time_offset": -2,
    "custom_labels": {"node": "z11", "type": "a"},
}
event_templates["e018"] = {
    "ttl": 20,
    "fetched_time_offset": -15,
    "custom_labels": {"node": "z11", "type": "b"},
}
event_templates["e018a"] = {
    "ttl": 20,
    "fetched_time_offset": -15,
    "custom_labels": {"node": "z11", "type": "b"},
}
event_templates["e018b"] = {
    "ttl": 20,
    "fetched_time_offset": 10,
    "custom_labels": {"node": "z11", "type": "b"},
}
event_templates["e018c"] = {
    "ttl": 20,
    "fetched_time_offset": 15,
    "custom_labels": {"node": "z11", "type": "b"},
}
event_templates["e018d"] = {
    "ttl": 20,
    "fetched_time_offset": 15,
    "custom_labels": {"node": "z11", "type": "b"},
}
event_templates["e018e"] = {
    "ttl": 20,
    "fetched_time_offset": 25,
    "custom_labels": {"node": "z11", "type": "b"},
}
event_templates["e019"] = {
    "ttl": 20,
    "fetched_time_offset": -5,
    "custom_labels": {"node": "z11", "type": "b"},
}
event_templates["e019a"] = {
    "ttl": 20,
    "fetched_time_offset": -5,
    "custom_labels": {"node": "z11", "type": "b"},
}
event_templates["e019b"] = {
    "ttl": 20,
    "fetched_time_offset": -25,
    "custom_labels": {"node": "z11", "type": "b"},
}
event_templates["e020"] = {
    "ttl": 20,
    "fetched_time_offset": -32,
    "custom_labels": {"node": "z11", "type": "c"},
}
event_templates["e021"] = {
    "ttl": 20,
    "fetched_time_offset": -5,
    "custom_labels": {"node": "z11", "type": "c"},
}
event_templates["e022"] = {
    "ttl": 20,
    "fetched_time_offset": -5,
    "custom_labels": {"node": "z11", "type": "c"},
}
event_templates["e023"] = {
    "ttl": 20,
    "fetched_time_offset": -30,
    "custom_labels": {"node": "z11", "type": "d"},
}
event_templates["e023a"] = {
    "ttl": 20,
    "fetched_time_offset": -20,
    "custom_labels": {"node": "z11", "type": "c"},
}
event_templates["e023b"] = {
    "ttl": 20,
    "fetched_time_offset": 5,
    "custom_labels": {"node": "z11", "type": "c"},
}
event_templates["e023b2"] = {
    "ttl": 20,
    "fetched_time_offset": 20,
    "custom_labels": {"node": "z11", "type": "c"},
}
event_templates["e023c"] = {
    "ttl": 20,
    "fetched_time_offset": -10,
    "custom_labels": {"node": "z11", "type": "c"},
}
event_templates["e023d"] = {
    "ttl": 20,
    "fetched_time_offset": 40,
    "custom_labels": {"node": "z11", "type": "c"},
}
event_templates["e023e"] = {
    "ttl": 20,
    "fetched_time_offset": 5,
    "custom_labels": {"node": "z11", "type": "c"},
}
event_templates["e023f"] = {
    "ttl": 20,
    "fetched_time_offset": 7,
    "custom_labels": {"node": "z11", "type": "c"},
}
event_templates["e024"] = {
    "ttl": 20,
    "fetched_time_offset": -30,
    "custom_labels": {"node": "z10", "type": "qa", "mode": "q1"},
}
event_templates["e024a"] = {
    "ttl": 20,
    "fetched_time_offset": -30,
    "custom_labels": {"node": "z10", "type": "qa", "mode": "q1"},
}
event_templates["e025"] = {
    "ttl": 20,
    "fetched_time_offset": -5,
    "custom_labels": {"node": "z11", "type": "qa", "mode": "q2"},
}
event_templates["e026"] = {
    "ttl": 20,
    "fetched_time_offset": 7,
    "custom_labels": {"node": "z11", "type": "qa", "mode": "q3"},
}
event_templates["e026a"] = {
    "ttl": 20,
    "fetched_time_offset": 16,
    "custom_labels": {"node": "z11", "type": "qa", "mode": "q3"},
}
event_templates["e026b"] = {
    "ttl": 20,
    "fetched_time_offset": -5,
    "custom_labels": {"node": "z11", "type": "qa", "mode": "q3"},
}
event_templates["e026c"] = {
    "ttl": 20,
    "fetched_time_offset": 7,
    "custom_labels": {"node": "z11", "type": "qa", "mode": "q3"},
}
event_templates["e026d"] = {
    "ttl": 20,
    "fetched_time_offset": 16,
    "custom_labels": {"node": "z11", "type": "qa", "mode": "q3"},
}
event_templates["e026e"] = {
    "ttl": 20,
    "fetched_time_offset": 30,
    "custom_labels": {"node": "z11", "type": "qa", "mode": "q3"},
}
event_templates["e026f"] = {
    "ttl": 20,
    "fetched_time_offset": 30,
    "custom_labels": {"node": "z11", "type": "qa", "mode": "q3"},
}
event_templates["e027"] = {
    "ttl": 20,
    "fetched_time_offset": -15,
    "custom_labels": {"node": "z11", "type": "qb", "mode": "q4"},
}
event_templates["e027a"] = {
    "ttl": 20,
    "fetched_time_offset": -15,
    "custom_labels": {"node": "z11", "type": "qb", "mode": "q4"},
}
event_templates["e028"] = {
    "ttl": 20,
    "fetched_time_offset": -5,
    "custom_labels": {"node": "z11", "type": "qb", "mode": "q1"},
}
event_templates["e028a"] = {
    "ttl": 20,
    "fetched_time_offset": -5,
    "custom_labels": {"node": "z11", "type": "qb", "mode": "q1"},
}
event_templates["e028b"] = {
    "ttl": 20,
    "fetched_time_offset": 30,
    "custom_labels": {"node": "z11", "type": "qb", "mode": "q1"},
}
event_templates["e029"] = {
    "ttl": 20,
    "fetched_time_offset": -32,
    "custom_labels": {"node": "z11", "type": "qc", "mode": "q2"},
}
event_templates["e030"] = {
    "ttl": 20,
    "fetched_time_offset": -5,
    "custom_labels": {"node": "z11", "type": "qc", "mode": "q3"},
}
event_templates["e030a"] = {
    "ttl": 20,
    "fetched_time_offset": -5,
    "custom_labels": {"node": "z11", "type": "qc", "mode": "q3"},
}
event_templates["e030b"] = {
    "ttl": 20,
    "fetched_time_offset": -5,
    "custom_labels": {"node": "z11", "type": "qc"},
}
event_templates["e030c"] = {
    "ttl": 20,
    "fetched_time_offset": -5,
    "custom_labels": {"node": "z11", "type": "qc"},
}
event_templates["e031"] = {
    "ttl": 20,
    "fetched_time_offset": -5,
    "custom_labels": {"node": "z11", "type": "qd", "mode": "q4"},
}
event_templates["e031a"] = {
    "ttl": 20,
    "fetched_time_offset": -5,
    "custom_labels": {"node": "z11", "type": "qd", "mode": "q4"},
}
event_templates["e032"] = {
    "ttl": 20,
    "fetched_time_offset": -30,
    "custom_labels": {"node": "z11", "type": "qd", "mode": "q1"},
}
event_templates["e032a"] = {
    "ttl": 20,
    "fetched_time_offset": -15,
    "custom_labels": {"node": "z11", "type": "qd", "mode": "q1"},
}
event_templates["e032b"] = {
    "ttl": 20,
    "fetched_time_offset": -15,
    "custom_labels": {"node": "z11", "type": "qd", "mode": "q1"},
}
event_templates["e033"] = {
    "ttl": 20,
    "fetched_time_offset": -5,
    "custom_labels": {"node": "z11", "type": "qa", "mode": "q2"},
}
event_templates["e034"] = {
    "ttl": 20,
    "fetched_time_offset": -32,
    "custom_labels": {"node": "z11", "type": "qa", "mode": "q2"},
}
event_templates["e035"] = {
    "ttl": 20,
    "fetched_time_offset": 15,
    "custom_labels": {"node": "z11", "type": "qa", "mode": "q2"},
}
event_templates["e036"] = {
    "ttl": 20,
    "fetched_time_offset": 15,
    "custom_labels": {"node": "z11", "type": "qb", "mode": "q2"},
}
event_templates["e036a"] = {
    "ttl": 20,
    "fetched_time_offset": 15,
    "custom_labels": {"node": "z11", "type": "qb", "mode": "q2"},
}
event_templates["e037"] = {
    "ttl": 20,
    "fetched_time_offset": -13,
    "custom_labels": {"node": "z11", "type": "qa", "mode": "q2"},
}
#
#
event_templates["e999"] = {
    "ttl": 20,
    "fetched_time_offset": 0,
    "custom_labels": {
        "node": "z01",
        "msg": "[systemZ]未知の事態が発生しました。",
        "_exastro_host": "systemZ",
    },
}
#
# pytest用イベント定義
