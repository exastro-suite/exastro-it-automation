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
    # 2616
    ###########################################################
    g.applogger.info("[Trace] bug fix issue2616")

    # execution_environment_parameter_definition_sheet - bindep_file
    base_target_dir = f'{work_dir_path}/uploadfiles/8df96afe-552a-4a2a-b370-cb3888b27dee/bindep_file/'

    # target: [(id, jnl)]
    _target_uuid = [
        ("6455ab8a-aaf8-40a3-8692-7a2f2605512a", "06536f39-a68a-4628-8213-f43b6437c63a"),
        ("d233c7eb-f7d1-4aa3-8aa7-50b63cd601c8", "9465faf0-5ee3-4383-b439-14a943718344"),
        ("4481b6fb-7262-4c3e-a6bb-c2c681f12e21", "f528132b-aa41-46f8-ad36-47d9430b959d"),
        ("62f1215c-0d9d-4af6-bcad-0b7eaac934a8", "e5820a22-2658-4fe3-9cc7-792c929d3606"),
        ("a2bfccfd-0a29-45cb-bc54-b48bf6f51d71", "f15bbe12-dcf2-46c8-9ab6-43f6e0d0f5d5"),
    ]

    for _target in _target_uuid:
        _id, _jnlid = _target
        # link path
        x_link_path = f"{base_target_dir}{_id}/biuder.txt"
        o_link_path = f"{base_target_dir}{_id}/builder.txt"
        # file path
        x_old_file_path = f"{base_target_dir}{_id}/old/{_jnlid}/biuder.txt"
        o_old_file_path = f"{base_target_dir}{_id}/old/{_jnlid}/builder.txt"

        # rename
        if os.path.isfile(x_old_file_path):
            g.applogger.info(f"rename {x_old_file_path}->{o_old_file_path}")
            os.rename(x_old_file_path, o_old_file_path)
        else:
            g.applogger.info(f"continue: {os.path.isfile(x_old_file_path)=}")
            continue

        # unlink
        if os.path.islink(x_link_path):
            g.applogger.info(f"unlink {x_link_path}")
            os.unlink(x_link_path)

        # link
        if os.path.isfile(o_old_file_path):
            g.applogger.info(f"rename {o_old_file_path}->{o_link_path}")
            os.symlink(o_old_file_path, o_link_path)  # noqa: F405
        else:
            g.applogger.info(f"continue: {os.path.isfile(x_old_file_path)=}")
            continue

    return 0


