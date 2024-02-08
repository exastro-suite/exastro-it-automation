#   Copyright 2023 NEC Corporation
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
import shutil


def main(work_dir_path, db_conn):
    """
        メニューグループ管理のディレクトリ構造変更
        /uploadfiles/10102/menu_group_icon/<id>/_old
        ->
        /uploadfiles/10102/menu_group_icon/<id>/old
    """

    g.applogger.info("[Trace] Begin Menu Group migrate(specific).")

    # 対象ディレクトリ取得
    base_target_dir = f'{work_dir_path}/uploadfiles/10102/menu_group_icon/'
    menu_group_dirs = os.listdir(base_target_dir)
    menu_group_dirs_list = [f'{base_target_dir}{mgid}' for mgid in menu_group_dirs if os.path.isdir(f'{base_target_dir}{mgid}')]

    for menu_group_base_path in menu_group_dirs_list:
        g.applogger.info(f"[Trace] Target Menu Group Path: {menu_group_base_path}")

        # ディレクトリ/シンボリックリンクの対象取得
        _files = os.listdir(menu_group_base_path)
        _dir_list = [f'{menu_group_base_path}/{_f}' for _f in _files if os.path.isdir(f'{menu_group_base_path}/{_f}')]
        _symlink_list = [f'{menu_group_base_path}/{_f}' for _f in _files if os.path.islink(f'{menu_group_base_path}/{_f}')]

        # oldディレクトリ対応
        for _f in _dir_list:
            g.applogger.info(f"[Trace] target path (old): {_f}.")
            _old_dir_path = f'{menu_group_base_path}/_old'
            _new_dir_path = f'{menu_group_base_path}/old'
            _is_old_dir_path = os.path.isdir(_old_dir_path)
            _is_new_dir_path = os.path.isdir(_new_dir_path)

            if _is_old_dir_path is True and _is_new_dir_path is False:
                # ディレクトリ変更(_oldのみ存在): _old -> old
                try:
                    g.applogger.info(f"[Trace] rename({_old_dir_path}, {_new_dir_path})")
                    os.rename(_old_dir_path, _new_dir_path)
                except Exception as e:
                    g.applogger.info(f"[Trace] rename Exception: {e}")

            elif _is_old_dir_path is True and _is_new_dir_path is True:
                # ディレクトリ移動(old,_old存在): _oldh配下 -> old配下へ
                _old_files = os.listdir(_old_dir_path)
                for _jnl_id in _old_files:
                    _old_id_dir_path = f'{_old_dir_path}/{_jnl_id}'
                    _new_id_dir_path = f'{_new_dir_path}/{_jnl_id}'
                    # 移動先重複チェック
                    if os.path.isdir(_old_id_dir_path) and os.path.isdir(_new_id_dir_path) is False:
                        # ディレクトリ移動
                        try:
                            g.applogger.info(f"[Trace] move({_old_id_dir_path}, {_new_dir_path})")
                            shutil.move(_old_id_dir_path, _new_dir_path)
                        except Exception as e:
                            g.applogger.info(f"[Trace] move Exception: {e}")

                    else:
                        g.applogger.info(f"[Trace] Duplication path _old:{_old_id_dir_path}, old{_new_id_dir_path}")

                # ディレクトリ削除: _old
                _old_files = os.listdir(_old_dir_path)
                if len(_old_files) == 0:
                    try:
                        g.applogger.info(f"[Trace] _old rmtree({_old_dir_path})")
                        shutil.rmtree(_old_dir_path)
                    except Exception as e:
                        g.applogger.info(f"[Trace] _old rmtree Exception: {e}")

        # Symbolic link　対応
        for _f in _symlink_list:
            g.applogger.info(f"[Trace] Symbolic link: {_f}")
            _readlink = os.readlink(_f)
            _jnl_id = _f.split("/")[-2]
            _file_name = _f.split("/")[-1]
            _new_dir_path = f'{menu_group_base_path}/old'
            _new_sylink_path = f'{_new_dir_path}/{_jnl_id}/{_file_name}'
            if '/_old/' in _readlink:
                try:
                    # Symbolic link削除
                    g.applogger.info(f"[Trace] unlink({_f})")
                    os.unlink(_f)
                except Exception as e:
                    g.applogger.info(f"[Trace] unlink Exception: {e}")
                try:
                    # Symbolic link生成
                    g.applogger.info(f"[Trace] symlink({_new_sylink_path}, {_f})")
                    os.symlink(_new_sylink_path, _f)
                except Exception as e:
                    g.applogger.info(f"[Trace] symlink Exception: {e}")

    g.applogger.info("[Trace] End Menu Group migrate(specific).")

    return 0
