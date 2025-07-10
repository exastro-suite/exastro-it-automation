#   Copyright 2024 NEC Corporation
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

from flask import g
import os

from common_libs.common.dbconnect import *  # noqa: F403

def main(work_dir_path, wsdb):
    ###########################################################
    # 2701
    ###########################################################
    g.applogger.info("[Trace] bug fix issue2701")

    # execution_environment_parameter_definition_sheet - bindep_file
    base_target_dir = f'{work_dir_path}/uploadfiles/8df96afe-552a-4a2a-b370-cb3888b27dee/bindep_file/'

    # target: [(id, jnl)]
    _target_uuid = [
        ("0c884e3e-e945-45a7-aa87-1cc671a2f8c3", "b3d3ed5b-378b-459e-803b-a797f89982b8"),
        ("7e391140-0143-4d35-a460-03afd843a7e5", "255f60f2-9d1e-480c-a807-b4a3944f0688"),
    ]

    for _target in _target_uuid:
        _id, _jnlid = _target
        # link path
        x_link_path = f"{base_target_dir}{_id}/biuder.txt"
        # file path
        x_old_file_path = f"{base_target_dir}{_id}/old/{_jnlid}/biuder.txt"

        # unlink
        if os.path.islink(x_link_path):
            g.applogger.info(f"unlink {x_link_path}")
            os.unlink(x_link_path)
        if os.path.isfile(x_old_file_path):
            g.applogger.info(f"remove {x_old_file_path}")
            os.remove(x_old_file_path)

    return 0


