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
import copy

from tests.common import create_event


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
            fetched_time_offset=event_templates[event_id]["fetched_time_offset"],
            ttl=event_templates[event_id]["ttl"],
            custom_labels=copy.deepcopy(event_templates[event_id]["custom_labels"]),
        )
        events.append(event)
    return events


def create_events_p130(event_num: int) -> list[dict]:
    """p130用のeventリスト作成

    Args:
        event_num (int): イベント数

    Returns:
        list[dict]: eventリスト
    """
    events = []
    for i in range(0, event_num):
        event = create_event(
            "p130",
            f"e{1001 + i}",
            fetched_time_offset=event_templates["e1001"]["fetched_time_offset"],
            ttl=event_templates["e1001"]["ttl"],
            custom_labels=copy.deepcopy(event_templates["e1001"]["custom_labels"]),
        )
        events.append(event)
    return events


# pytest用イベント定義
event_templates = {}
event_templates["e001"] = {
    "ttl": 20,
    "fetched_time_offset": -15,
    "custom_labels": {
        "eventid": "e001",
        "node": "z01",
        "clock": "9985",
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
        "eventid": "e002",
        "node": "z01",
        "clock": "9990",
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
        "eventid": "e003",
        "node": "z01",
        "clock": "9995",
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
        "eventid": "e003a",
        "node": "z01",
        "clock": "9995",
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
        "eventid": "e004",
        "node": "z01",
        "clock": "9985",
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
        "eventid": "e005",
        "node": "z01",
        "clock": "9990",
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
        "eventid": "e005a",
        "node": "z01",
        "clock": "10015",
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
        "eventid": "e005b",
        "node": "z01",
        "clock": "10015",
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
        "eventid": "e005c",
        "node": "z01",
        "clock": "10015",
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
        "eventid": "e005d",
        "node": "z01",
        "clock": "10015",
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
        "eventid": "e005e",
        "node": "z01",
        "clock": "10000",
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
        "eventid": "e005f",
        "node": "z01",
        "clock": "10000",
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
        "eventid": "e006",
        "node": "Z02",
        "clock": "9981",
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
        "eventid": "e007",
        "node": "Z02",
        "clock": "9985",
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
        "eventid": "e008",
        "node": "Z02",
        "clock": "10006",
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
        "eventid": "e009",
        "node": "Z02",
        "clock": "10007",
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
        "eventid": "e014a",
        "node": "Z02",
        "clock": "9960",
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
        "eventid": "e014b",
        "node": "Z02",
        "clock": "9966",
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
        "eventid": "e014c",
        "node": "Z02",
        "clock": "9966",
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
        "eventid": "e014d",
        "node": "Z02",
        "clock": "9995",
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
        "eventid": "e014e",
        "node": "Z02",
        "clock": "9995",
        "msg": "[systemC] Mysqld Down",
        "_exastro_host": "systemC",
        "service": "Mysqld",
        "status": "Down",
        "severity": "3",
        "excluded_flg": "0",
    },
}
event_templates["e014f"] = {
    "ttl": 20,
    "fetched_time_offset": 15,
    "custom_labels": {
        "eventid": "e014f",
        "node": "Z02",
        "clock": "10015",
        "msg": "[systemC] Mysqld Down",
        "_exastro_host": "systemC",
        "service": "Mysqld",
        "status": "Down",
        "severity": "3",
        "excluded_flg": "0",
    },
}
event_templates["e014g"] = {
    "ttl": 20,
    "fetched_time_offset": 15,
    "custom_labels": {
        "eventid": "e014g",
        "node": "Z02",
        "clock": "10015",
        "msg": "[systemC] Mysqld Down",
        "_exastro_host": "systemC",
        "service": "Mysqld",
        "status": "Down",
        "severity": "3",
        "excluded_flg": "0",
    },
}
event_templates["e014i"] = {
    "ttl": 20,
    "fetched_time_offset": -41,
    "custom_labels": {
        "eventid": "e014i",
        "node": "Z02",
        "clock": "9959",
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
        "eventid": "e010",
        "node": "Z02",
        "clock": "9970",
        "msg": "[systemC] Disk Full",
        "_exastro_host": "systemC",
        "service": "Disk",
        "status": "Full",
        "severity": "3",
        "excluded_flg": "0",
    },
}
event_templates["e010a"] = {
    "ttl": 20,
    "fetched_time_offset": -28,
    "custom_labels": {
        "eventid": "e010a",
        "node": "Z02",
        "clock": "9972",
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
        "eventid": "e011",
        "node": "Z02",
        "clock": "9975",
        "msg": "[systemC] Disk Full (95%)",
        "_exastro_host": "systemC",
        "service": "Disk",
        "status": "Full",
        "severity": "3",
        "used_space": "95%",
        "excluded_flg": "0",
    },
}
event_templates["e012"] = {
    "ttl": 20,
    "fetched_time_offset": -10,
    "custom_labels": {
        "eventid": "e012",
        "node": "Z02",
        "clock": "9990",
        "msg": "[systemC] Disk Full (95%) -exclude",
        "_exastro_host": "systemC",
        "service": "Disk",
        "status": "Full",
        "severity": "3",
        "used_space": "95%",
        "excluded_flg": "1",
    },
}
event_templates["e013"] = {
    "ttl": 20,
    "fetched_time_offset": -5,
    "custom_labels": {
        "eventid": "e013",
        "node": "Z02",
        "clock": "9995",
        "msg": "[systemC] Disk Full (95%)",
        "_exastro_host": "systemC",
        "service": "Disk",
        "status": "Full",
        "severity": "3",
        "used_space": "95%",
        "excluded_flg": "0",
    },
}
event_templates["e014"] = {
    "ttl": 20,
    "fetched_time_offset": 0,
    "custom_labels": {
        "eventid": "e014",
        "node": "Z02",
        "clock": "10000",
        "msg": "[systemC] Disk Full",
        "_exastro_host": "systemC",
        "service": "Disk",
        "status": "Full",
        "severity": "3",
        "excluded_flg": "0",
    },
}
event_templates["e014h"] = {
    "ttl": 20,
    "fetched_time_offset": 0,
    "custom_labels": {
        "eventid": "e014h",
        "node": "Z02",
        "clock": "10000",
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
    "custom_labels": {"eventid": "e015", "node": "z10", "clock": "9970", "type": "a"},
}
event_templates["e015a"] = {
    "ttl": 20,
    "fetched_time_offset": -30,
    "custom_labels": {"eventid": "e015a", "node": "z10", "clock": "9970", "type": "a"},
}
event_templates["e015b"] = {
    "ttl": 20,
    "fetched_time_offset": -35,
    "custom_labels": {"eventid": "e015b", "node": "z10", "clock": "9965", "type": "a"},
}
event_templates["e016"] = {
    "ttl": 20,
    "fetched_time_offset": -5,
    "custom_labels": {"eventid": "e016", "node": "z11", "clock": "9995", "type": "a"},
}
event_templates["e017"] = {
    "ttl": 20,
    "fetched_time_offset": 7,
    "custom_labels": {"eventid": "e017", "node": "z11", "clock": "10007", "type": "a"},
}
event_templates["e017a"] = {
    "ttl": 20,
    "fetched_time_offset": -2,
    "custom_labels": {"eventid": "e017a", "node": "z11", "clock": "9998", "type": "a"},
}
event_templates["e017b"] = {
    "ttl": 20,
    "fetched_time_offset": -2,
    "custom_labels": {"eventid": "e017b", "node": "z11", "clock": "9998", "type": "a"},
}
event_templates["e018"] = {
    "ttl": 20,
    "fetched_time_offset": -15,
    "custom_labels": {"eventid": "e018", "node": "z11", "clock": "9985", "type": "b"},
}
event_templates["e018a"] = {
    "ttl": 20,
    "fetched_time_offset": -15,
    "custom_labels": {"eventid": "e018a", "node": "z11", "clock": "9985", "type": "b"},
}
event_templates["e018b"] = {
    "ttl": 20,
    "fetched_time_offset": 10,
    "custom_labels": {"eventid": "e018b", "node": "z11", "clock": "10010", "type": "b"},
}
event_templates["e018c"] = {
    "ttl": 20,
    "fetched_time_offset": 15,
    "custom_labels": {"eventid": "e018c", "node": "z11", "clock": "10015", "type": "b"},
}
event_templates["e018d"] = {
    "ttl": 20,
    "fetched_time_offset": 15,
    "custom_labels": {"eventid": "e018d", "node": "z11", "clock": "10015", "type": "b"},
}
event_templates["e018e"] = {
    "ttl": 20,
    "fetched_time_offset": 25,
    "custom_labels": {"eventid": "e018e", "node": "z11", "clock": "10025", "type": "b"},
}
event_templates["e019"] = {
    "ttl": 20,
    "fetched_time_offset": -5,
    "custom_labels": {"eventid": "e019", "node": "z11", "clock": "9995", "type": "b"},
}
event_templates["e019a"] = {
    "ttl": 20,
    "fetched_time_offset": -5,
    "custom_labels": {"eventid": "e019a", "node": "z11", "clock": "9995", "type": "b"},
}
event_templates["e019b"] = {
    "ttl": 20,
    "fetched_time_offset": -25,
    "custom_labels": {"eventid": "e019b", "node": "z11", "clock": "9975", "type": "b"},
}
event_templates["e019c"] = {
    "ttl": 20,
    "fetched_time_offset": 10,
    "custom_labels": {"eventid": "e019c", "node": "z11", "clock": "10010", "type": "b"},
}
event_templates["e019d"] = {
    "ttl": 20,
    "fetched_time_offset": -35,
    "custom_labels": {"eventid": "e019d", "node": "z11", "clock": "9965", "type": "b"},
}
event_templates["e020"] = {
    "ttl": 20,
    "fetched_time_offset": -32,
    "custom_labels": {"eventid": "e020", "node": "z11", "clock": "9968", "type": "c"},
}
event_templates["e021"] = {
    "ttl": 20,
    "fetched_time_offset": -5,
    "custom_labels": {"eventid": "e021", "node": "z11", "clock": "9995", "type": "c"},
}
event_templates["e022"] = {
    "ttl": 20,
    "fetched_time_offset": -5,
    "custom_labels": {"eventid": "e022", "node": "z11", "clock": "9995", "type": "c"},
}
event_templates["e023"] = {
    "ttl": 20,
    "fetched_time_offset": -30,
    "custom_labels": {"eventid": "e023", "node": "z11", "clock": "9970", "type": "d"},
}
event_templates["e023a"] = {
    "ttl": 20,
    "fetched_time_offset": -20,
    "custom_labels": {"eventid": "e023a", "node": "z11", "clock": "9980", "type": "c"},
}
event_templates["e023b"] = {
    "ttl": 20,
    "fetched_time_offset": 5,
    "custom_labels": {"eventid": "e023b", "node": "z11", "clock": "10005", "type": "c"},
}
event_templates["e023b2"] = {
    "ttl": 20,
    "fetched_time_offset": 20,
    "custom_labels": {
        "eventid": "e023b2",
        "node": "z11",
        "clock": "10020",
        "type": "c",
    },
}
event_templates["e023c"] = {
    "ttl": 20,
    "fetched_time_offset": -10,
    "custom_labels": {"eventid": "e023c", "node": "z11", "clock": "9990", "type": "c"},
}
event_templates["e023d"] = {
    "ttl": 20,
    "fetched_time_offset": 40,
    "custom_labels": {"eventid": "e023d", "node": "z11", "clock": "10040", "type": "c"},
}
event_templates["e023e"] = {
    "ttl": 20,
    "fetched_time_offset": 5,
    "custom_labels": {"eventid": "e023e", "node": "z11", "clock": "10005", "type": "c"},
}
event_templates["e023f"] = {
    "ttl": 20,
    "fetched_time_offset": 7,
    "custom_labels": {"eventid": "e023f", "node": "z11", "clock": "10007", "type": "c"},
}
event_templates["e024"] = {
    "ttl": 20,
    "fetched_time_offset": -30,
    "custom_labels": {
        "eventid": "e024",
        "node": "z10",
        "clock": "9970",
        "type": "qa",
        "mode": "q1",
    },
}
event_templates["e024a"] = {
    "ttl": 20,
    "fetched_time_offset": -30,
    "custom_labels": {
        "eventid": "e024a",
        "node": "z10",
        "clock": "9970",
        "type": "qa",
        "mode": "q1",
    },
}
event_templates["e025"] = {
    "ttl": 20,
    "fetched_time_offset": -5,
    "custom_labels": {
        "eventid": "e025",
        "node": "z11",
        "clock": "9995",
        "type": "qa",
        "mode": "q2",
    },
}
event_templates["e025a"] = {
    "ttl": 20,
    "fetched_time_offset": -30,
    "custom_labels": {
        "eventid": "e025a",
        "node": "z11",
        "clock": "9970",
        "type": "qa",
        "mode": "q2",
    },
}
event_templates["e025b"] = {
    "ttl": 20,
    "fetched_time_offset": -30,
    "custom_labels": {
        "eventid": "e025b",
        "node": "z11",
        "clock": "9970",
        "type": "qa",
        "mode": "q2",
    },
}
event_templates["e026"] = {
    "ttl": 20,
    "fetched_time_offset": 7,
    "custom_labels": {
        "eventid": "e026",
        "node": "z11",
        "clock": "10007",
        "type": "qa",
        "mode": "q3",
    },
}
event_templates["e026a"] = {
    "ttl": 20,
    "fetched_time_offset": 16,
    "custom_labels": {
        "eventid": "e026a",
        "node": "z11",
        "clock": "10016",
        "type": "qa",
        "mode": "q3",
    },
}
event_templates["e026b"] = {
    "ttl": 20,
    "fetched_time_offset": -5,
    "custom_labels": {
        "eventid": "e026b",
        "node": "z11",
        "clock": "9995",
        "type": "qa",
        "mode": "q3",
    },
}
event_templates["e026c"] = {
    "ttl": 20,
    "fetched_time_offset": 7,
    "custom_labels": {
        "eventid": "e026c",
        "node": "z11",
        "clock": "10007",
        "type": "qa",
        "mode": "q3",
    },
}
event_templates["e026d"] = {
    "ttl": 20,
    "fetched_time_offset": 16,
    "custom_labels": {
        "eventid": "e026d",
        "node": "z11",
        "clock": "10016",
        "type": "qa",
        "mode": "q3",
    },
}
event_templates["e026e"] = {
    "ttl": 20,
    "fetched_time_offset": 30,
    "custom_labels": {
        "eventid": "e026e",
        "node": "z11",
        "clock": "10030",
        "type": "qa",
        "mode": "q3",
    },
}
event_templates["e026f"] = {
    "ttl": 20,
    "fetched_time_offset": 30,
    "custom_labels": {
        "eventid": "e026f",
        "node": "z11",
        "clock": "10030",
        "type": "qa",
        "mode": "q3",
    },
}
event_templates["e026g"] = {
    "ttl": 20,
    "fetched_time_offset": 9,
    "custom_labels": {
        "eventid": "e026g",
        "node": "z11",
        "clock": "10009",
        "type": "qa",
        "mode": "q3",
    },
}
event_templates["e027"] = {
    "ttl": 20,
    "fetched_time_offset": -15,
    "custom_labels": {
        "eventid": "e027",
        "node": "z11",
        "clock": "9985",
        "type": "qb",
        "mode": "q4",
    },
}
event_templates["e027a"] = {
    "ttl": 20,
    "fetched_time_offset": -15,
    "custom_labels": {
        "eventid": "e027a",
        "node": "z11",
        "clock": "9985",
        "type": "qb",
        "mode": "q4",
    },
}
event_templates["e028"] = {
    "ttl": 20,
    "fetched_time_offset": -5,
    "custom_labels": {
        "eventid": "e028",
        "node": "z11",
        "clock": "9995",
        "type": "qb",
        "mode": "q1",
    },
}
event_templates["e028a"] = {
    "ttl": 20,
    "fetched_time_offset": -5,
    "custom_labels": {
        "eventid": "e028a",
        "node": "z11",
        "clock": "9995",
        "type": "qb",
        "mode": "q1",
    },
}
event_templates["e028b"] = {
    "ttl": 20,
    "fetched_time_offset": 30,
    "custom_labels": {
        "eventid": "e028b",
        "node": "z11",
        "clock": "10030",
        "type": "qb",
        "mode": "q1",
    },
}
event_templates["e028c"] = {
    "ttl": 20,
    "fetched_time_offset": -2,
    "custom_labels": {
        "eventid": "e028c",
        "node": "z11",
        "clock": "9998",
        "type": "qb",
        "mode": "q1",
    },
}
event_templates["e029"] = {
    "ttl": 20,
    "fetched_time_offset": -32,
    "custom_labels": {
        "eventid": "e029",
        "node": "z11",
        "clock": "9968",
        "type": "qc",
        "mode": "q2",
    },
}
event_templates["e030"] = {
    "ttl": 20,
    "fetched_time_offset": -5,
    "custom_labels": {
        "eventid": "e030",
        "node": "z11",
        "clock": "9995",
        "type": "qc",
        "mode": "q3",
    },
}
event_templates["e030a"] = {
    "ttl": 20,
    "fetched_time_offset": -5,
    "custom_labels": {
        "eventid": "e030a",
        "node": "z11",
        "clock": "9995",
        "type": "qc",
        "mode": "q3",
    },
}
event_templates["e030b"] = {
    "ttl": 20,
    "fetched_time_offset": -5,
    "custom_labels": {"eventid": "e030b", "node": "z11", "clock": "9995", "type": "qc"},
}
event_templates["e030c"] = {
    "ttl": 20,
    "fetched_time_offset": -5,
    "custom_labels": {"eventid": "e030c", "node": "z11", "clock": "9995", "type": "qc"},
}
event_templates["e031"] = {
    "ttl": 20,
    "fetched_time_offset": -5,
    "custom_labels": {
        "eventid": "e031",
        "node": "z11",
        "clock": "9995",
        "type": "qd",
        "mode": "q4",
    },
}
event_templates["e031a"] = {
    "ttl": 20,
    "fetched_time_offset": -5,
    "custom_labels": {
        "eventid": "e031a",
        "node": "z11",
        "clock": "9995",
        "type": "qd",
        "mode": "q4",
    },
}
event_templates["e032"] = {
    "ttl": 20,
    "fetched_time_offset": -30,
    "custom_labels": {
        "eventid": "e032",
        "node": "z11",
        "clock": "9970",
        "type": "qd",
        "mode": "q1",
    },
}
event_templates["e032a"] = {
    "ttl": 20,
    "fetched_time_offset": -15,
    "custom_labels": {
        "eventid": "e032a",
        "node": "z11",
        "clock": "9985",
        "type": "qd",
        "mode": "q1",
    },
}
event_templates["e032b"] = {
    "ttl": 20,
    "fetched_time_offset": -15,
    "custom_labels": {
        "eventid": "e032b",
        "node": "z11",
        "clock": "9985",
        "type": "qd",
        "mode": "q1",
    },
}
event_templates["e033"] = {
    "ttl": 20,
    "fetched_time_offset": -5,
    "custom_labels": {
        "eventid": "e033",
        "node": "z11",
        "clock": "9995",
        "type": "qa",
        "mode": "q2",
    },
}
event_templates["e034"] = {
    "ttl": 20,
    "fetched_time_offset": -32,
    "custom_labels": {
        "eventid": "e034",
        "node": "z11",
        "clock": "9968",
        "type": "qa",
        "mode": "q2",
    },
}
event_templates["e035"] = {
    "ttl": 20,
    "fetched_time_offset": 15,
    "custom_labels": {
        "eventid": "e035",
        "node": "z11",
        "clock": "10015",
        "type": "qa",
        "mode": "q2",
    },
}
event_templates["e036"] = {
    "ttl": 20,
    "fetched_time_offset": 15,
    "custom_labels": {
        "eventid": "e036",
        "node": "z11",
        "clock": "10015",
        "type": "qb",
        "mode": "q2",
    },
}
event_templates["e036a"] = {
    "ttl": 20,
    "fetched_time_offset": 15,
    "custom_labels": {
        "eventid": "e036a",
        "node": "z11",
        "clock": "10015",
        "type": "qb",
        "mode": "q2",
    },
}
event_templates["e037"] = {
    "ttl": 20,
    "fetched_time_offset": -13,
    "custom_labels": {
        "eventid": "e037",
        "node": "z11",
        "clock": "9987",
        "type": "qa",
        "mode": "q2",
    },
}
event_templates["e038"] = {
    "ttl": 20,
    "fetched_time_offset": -15,
    "custom_labels": {"eventid": "e038", "node": "", "clock": "9985", "status": "true"},
}
event_templates["e039"] = {
    "ttl": 20,
    "fetched_time_offset": -15,
    "custom_labels": {"eventid": "e039", "node": "", "clock": "9985", "status": "true"},
}
event_templates["e040"] = {
    "ttl": 20,
    "fetched_time_offset": -15,
    "custom_labels": {
        "eventid": "e040",
        "node": "z22",
        "clock": "9985",
        "service": "mail",
    },
}
event_templates["e041"] = {
    "ttl": 20,
    "fetched_time_offset": -15,
    "custom_labels": {"eventid": "e041", "node": "z22", "clock": "9985"},
}
event_templates["e042"] = {
    "ttl": 20,
    "fetched_time_offset": -15,
    "custom_labels": {
        "eventid": "e042",
        "node": "z21",
        "clock": "9985",
        "status": "false",
    },
}
event_templates["e043"] = {
    "ttl": 20,
    "fetched_time_offset": -15,
    "custom_labels": {
        "eventid": "e043",
        "node": "z21",
        "clock": "9985",
        "status": "false",
    },
}
#
event_templates["e999"] = {
    "ttl": 20,
    "fetched_time_offset": 0,
    "custom_labels": {
        "eventid": "e999",
        "node": "z01",
        "clock": "10000",
        "msg": "[systemZ]未知の事態が発生しました。",
        "_exastro_host": "systemZ",
    },
}
#
event_templates["e1001"] = {
    "ttl": 60,
    "fetched_time_offset": -10,
    "custom_labels": {
        "eventid": "e1001",
        "node": "VALUE",
        "clock": "9990",
        "status": "false",
    },
}
# pytest用イベント定義
