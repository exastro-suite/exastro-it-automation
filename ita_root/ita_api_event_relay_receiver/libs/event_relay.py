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


def get_event_collection_settings(wsDb, body):

    table_name = "T_EVRL_EVENT_COLLECTION_SETTINGS"

    where_str = "WHERE DISUSE_FLAG=0 AND EVENT_COLLECTION_SETTINGS_ID IN ({})".format(", ".join(["%s"] * len(body["event_collection_settings_ids"])))

    bind_values = tuple(body["event_collection_settings_ids"])
    print(bind_values)
    print(where_str)

    data = wsDb.table_select(
        table_name,
        where_str,
        bind_values
    )

    return data
