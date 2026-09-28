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

from flask import g

"""
処理順（子から親へ。参照を切らないため順序は固定）
    1. 消す多段変数メンバーに紐づく多段変数配列組合せ管理(T_ANSR_NESTVAR_MEMBER_COL_COMB)ごとに、
       残す多段変数メンバー側の同じ列順序(COL_SEQ_VALUE)のレコード(以下、統合先)を探す
         - 統合先あり: 代入値自動登録設定(T_ANSR_VALUE_AUTOREG)と代入値管理(T_ANSR_VALUE)の
                          COL_SEQ_COMBINATION_ID を統合先に UPDATE してから、消す側の COL_COMB を DELETE
         - 統合先なし: COL_COMB の ARRAY_MEMBER_ID を残す多段変数メンバーに UPDATE（DELETE しない）
    2. 多段変数最大繰返数管理(T_ANSR_NESTVAR_MEMBER_MAX_COL)も 1. と同じ規則で処理
    3. 消す多段変数メンバーを DELETE
"""

# 変数刈取が「同じメンバー変数か」を判定する同一性キー
COMPARE_KEYS = [
    "MVMT_VAR_LINK_ID",
    "VARS_NAME",
    "ARRAY_NEST_LEVEL",
    "ASSIGN_SEQ_NEED",
    "COL_SEQ_NEED",
    "MEMBER_DISP",
    "VRAS_NAME_PATH",
    "VRAS_NAME_ALIAS",
    "MAX_COL_SEQ",
]

T_MEMBER = "T_ANSR_NESTVAR_MEMBER"
T_COL_COMB = "T_ANSR_NESTVAR_MEMBER_COL_COMB"
T_MAX_COL = "T_ANSR_NESTVAR_MEMBER_MAX_COL"
T_AUTOREG = "T_ANSR_VALUE_AUTOREG"
T_VALUE = "T_ANSR_VALUE"

# IN 句に渡す ID の最大数（SQL 文が長くなりすぎないように分割する）
SELECT_CHUNK_SIZE = 500


def main(work_dir_path, ws_db):
    ###########################################################
    # 3084
    ###########################################################
    g.applogger.info("[Trace][start] bug fix issue3084")

    # トランザクション
    ws_db.db_transaction_start()
    try:
        summary = _remove_duplicate_members(ws_db)
        ws_db.db_commit()
    except Exception as e:
        ws_db.db_rollback()
        raise e

    if summary is not None:
        g.applogger.info(
            "[Trace] issue3084 summary: "
            f"duplicate_groups={summary['groups']}, "
            f"deleted_member={summary['deleted_member']}, "
            f"deleted_col_comb={summary['deleted_col_comb']}, "
            f"updated_col_comb={summary['updated_col_comb']}, "
            f"updated_autoreg={summary['updated_autoreg']}, "
            f"updated_value={summary['updated_value']}, "
            f"deleted_max_col={summary['deleted_max_col']}, "
            f"updated_max_col={summary['updated_max_col']}"
        )

    g.applogger.info("[Trace][end] bug fix issue3084")
    return 0


def _remove_duplicate_members(ws_db):
    """
    重複した多段変数メンバーを 1 件に畳む

    Returns:
        dict: 件数サマリ。重複が無い場合は None
    """
    # 多段変数メンバー（廃止込み）のうち、同一性キーが重複している行だけを取得する
    # GROUP BY は NULL 同士を同じグループ、NULL と '' を別グループにするので、_compare_key の str() 比較と同じ区切りになる
    member_records = ws_db.sql_execute(_build_duplicate_member_sql())
    grouped_members = {}
    for record in member_records:
        key = _compare_key(record)
        if key not in grouped_members:
            grouped_members[key] = []
        grouped_members[key].append(record)

    duplicate_groups = []
    duplicate_member_ids = []
    for records in grouped_members.values():
        if len(records) >= 2:
            duplicate_groups.append(records)
            for record in records:
                duplicate_member_ids.append(record["ARRAY_MEMBER_ID"])

    if len(duplicate_groups) == 0:
        g.applogger.info(f"[Trace] issue3084: no duplicate records in {T_MEMBER}")
        return None

    g.applogger.info(f"[Trace] issue3084: {len(duplicate_groups)} duplicate groups found in {T_MEMBER}")

    # 多段変数配列組合せ管理（廃止込み）のうち重複メンバーにぶら下がる行だけを取得し、多段変数メンバー ID ごとに索引化
    col_comb_records = _select_in_chunks(ws_db, T_COL_COMB, "ARRAY_MEMBER_ID", duplicate_member_ids)
    col_comb_by_member_id = {}
    duplicate_comb_ids = []
    for record in col_comb_records:
        array_member_id = record["ARRAY_MEMBER_ID"]
        if array_member_id not in col_comb_by_member_id:
            col_comb_by_member_id[array_member_id] = []
        col_comb_by_member_id[array_member_id].append(record)
        duplicate_comb_ids.append(record["COL_SEQ_COMBINATION_ID"])
    # 同じ (MVMT_VAR_LINK_ID, 列順序) の行が複数あるとき、統合先・付け替え対象に選ばれる行を
    # 残す多段変数メンバーと同じ規則（有効 → ID 昇順）で決める。table_select の並び順に依存させない
    for array_member_id in col_comb_by_member_id:
        col_comb_by_member_id[array_member_id].sort(key=_col_comb_sort_key)

    # 多段変数最大繰返数管理（廃止込み）のうち重複メンバーにぶら下がる行だけを取得し、多段変数メンバー ID ごとに索引化
    max_col_records = _select_in_chunks(ws_db, T_MAX_COL, "ARRAY_MEMBER_ID", duplicate_member_ids)
    max_col_by_member_id = {}
    for record in max_col_records:
        array_member_id = record["ARRAY_MEMBER_ID"]
        if array_member_id not in max_col_by_member_id:
            max_col_by_member_id[array_member_id] = []
        max_col_by_member_id[array_member_id].append(record)
    for array_member_id in max_col_by_member_id:
        max_col_by_member_id[array_member_id].sort(key=_max_col_sort_key)

    # 代入値自動登録設定（廃止込み）のうち上記 COL_COMB を参照する行だけを取得し、COL_SEQ_COMBINATION_ID ごとに索引化
    autoreg_records = _select_in_chunks(ws_db, T_AUTOREG, "COL_SEQ_COMBINATION_ID", duplicate_comb_ids)
    autoreg_by_comb_id = {}
    for record in autoreg_records:
        comb_id = record["COL_SEQ_COMBINATION_ID"]
        if comb_id is None:
            continue
        if comb_id not in autoreg_by_comb_id:
            autoreg_by_comb_id[comb_id] = []
        autoreg_by_comb_id[comb_id].append(record)

    # {消す COL_SEQ_COMBINATION_ID: 統合先の COL_SEQ_COMBINATION_ID}
    comb_id_merge_map = {}
    # 統合先が無く、ARRAY_MEMBER_ID を付け替える COL_COMB [(COL_SEQ_COMBINATION_ID, 残す ARRAY_MEMBER_ID)]
    col_comb_reparent_list = []
    # 削除する MAX_COL [MAX_COL_SEQ_ID]
    max_col_delete_ids = []
    # ARRAY_MEMBER_ID を付け替える MAX_COL [(MAX_COL_SEQ_ID, 残す ARRAY_MEMBER_ID)]
    max_col_reparent_list = []
    # 削除する多段変数メンバー [ARRAY_MEMBER_ID]
    member_delete_ids = []

    for records in duplicate_groups:
        sorted_records = sorted(records, key=_survivor_sort_key)
        keep_record = sorted_records[0]
        keep_member_id = keep_record["ARRAY_MEMBER_ID"]

        # 残す側の COL_COMB を (MVMT_VAR_LINK_ID, 列順序) で索引化（統合先の探索用）
        keep_col_comb_by_seq = {}
        for record in col_comb_by_member_id.get(keep_member_id, []):
            seq_key = (record["MVMT_VAR_LINK_ID"], _normalize_col_seq_value(record["COL_SEQ_VALUE"]))
            if seq_key not in keep_col_comb_by_seq:
                keep_col_comb_by_seq[seq_key] = record["COL_SEQ_COMBINATION_ID"]

        # 残す側の MAX_COL を MVMT_VAR_LINK_ID で索引化
        keep_max_col_by_link = {}
        for record in max_col_by_member_id.get(keep_member_id, []):
            if record["MVMT_VAR_LINK_ID"] not in keep_max_col_by_link:
                keep_max_col_by_link[record["MVMT_VAR_LINK_ID"]] = record["MAX_COL_SEQ_ID"]

        for delete_record in sorted_records[1:]:
            delete_member_id = delete_record["ARRAY_MEMBER_ID"]

            # 多段変数配列組合せ管理
            for record in col_comb_by_member_id.get(delete_member_id, []):
                seq_key = (record["MVMT_VAR_LINK_ID"], _normalize_col_seq_value(record["COL_SEQ_VALUE"]))
                comb_id = record["COL_SEQ_COMBINATION_ID"]
                if seq_key in keep_col_comb_by_seq:
                    # 残す側に同じ組合せ (MVMT_VAR_LINK_ID, 列順序) の行がある: 参照をその行へ付け替えてから DELETE
                    comb_id_merge_map[comb_id] = keep_col_comb_by_seq[seq_key]
                else:
                    # 残す側に同じ組合せの行が無い: ARRAY_MEMBER_ID を残す側に付け替えて行は残す（以降の消す側はこの行を統合先にできる）
                    col_comb_reparent_list.append((comb_id, keep_member_id))
                    keep_col_comb_by_seq[seq_key] = comb_id

            # 多段変数最大繰返数管理
            for record in max_col_by_member_id.get(delete_member_id, []):
                if record["MVMT_VAR_LINK_ID"] in keep_max_col_by_link:
                    max_col_delete_ids.append(record["MAX_COL_SEQ_ID"])
                else:
                    max_col_reparent_list.append((record["MAX_COL_SEQ_ID"], keep_member_id))
                    keep_max_col_by_link[record["MVMT_VAR_LINK_ID"]] = record["MAX_COL_SEQ_ID"]

            member_delete_ids.append(delete_member_id)

    # ---------------------------------------------------------
    # 実行（子から親へ）
    # ---------------------------------------------------------
    summary = {
        "groups": len(duplicate_groups),
        "deleted_member": 0,
        "deleted_col_comb": 0,
        "updated_col_comb": 0,
        "updated_autoreg": 0,
        "updated_value": 0,
        "deleted_max_col": 0,
        "updated_max_col": 0,
    }

    # 1. 代入値自動登録設定 / 代入値管理の COL_SEQ_COMBINATION_ID を統合先へ UPDATE
    for old_comb_id, new_comb_id in comb_id_merge_map.items():
        for record in autoreg_by_comb_id.get(old_comb_id, []):
            data = {"COLUMN_ID": record["COLUMN_ID"], "COL_SEQ_COMBINATION_ID": new_comb_id}
            # 代入値自動登録設定はユーザーデータのため履歴(JNL)を残す
            ws_db.table_update(T_AUTOREG, [data], "COLUMN_ID")
            summary["updated_autoreg"] += 1

    value_records = _select_in_chunks(ws_db, T_VALUE, "COL_SEQ_COMBINATION_ID", list(comb_id_merge_map.keys()))
    for record in value_records:
        data = {"ASSIGN_ID": record["ASSIGN_ID"], "COL_SEQ_COMBINATION_ID": comb_id_merge_map[record["COL_SEQ_COMBINATION_ID"]]}
        # T_ANSR_VALUE には JNL が無い
        ws_db.table_update(T_VALUE, [data], "ASSIGN_ID", is_register_history=False)
        summary["updated_value"] += 1

    # 2. 多段変数配列組合せ管理の DELETE / ARRAY_MEMBER_ID の付け替え（JNL 無し）
    for old_comb_id in comb_id_merge_map.keys():
        ws_db.table_delete(T_COL_COMB, [{"COL_SEQ_COMBINATION_ID": old_comb_id}], "COL_SEQ_COMBINATION_ID", is_register_history=False)
        summary["deleted_col_comb"] += 1

    for comb_id, keep_member_id in col_comb_reparent_list:
        data = {"COL_SEQ_COMBINATION_ID": comb_id, "ARRAY_MEMBER_ID": keep_member_id}
        ws_db.table_update(T_COL_COMB, [data], "COL_SEQ_COMBINATION_ID", is_register_history=False)
        summary["updated_col_comb"] += 1

    # 3. 多段変数最大繰返数管理の DELETE（JNL は残す）/ ARRAY_MEMBER_ID の付け替え（JNL に履歴を残す）
    for max_col_seq_id in max_col_delete_ids:
        ws_db.table_delete(T_MAX_COL, [{"MAX_COL_SEQ_ID": max_col_seq_id}], "MAX_COL_SEQ_ID", is_register_history=False)
        summary["deleted_max_col"] += 1

    for max_col_seq_id, keep_member_id in max_col_reparent_list:
        data = {"MAX_COL_SEQ_ID": max_col_seq_id, "ARRAY_MEMBER_ID": keep_member_id}
        ws_db.table_update(T_MAX_COL, [data], "MAX_COL_SEQ_ID")
        summary["updated_max_col"] += 1

    # 4. 多段変数メンバーの DELETE（JNL 無し）
    for array_member_id in member_delete_ids:
        ws_db.table_delete(T_MEMBER, [{"ARRAY_MEMBER_ID": array_member_id}], "ARRAY_MEMBER_ID", is_register_history=False)
        summary["deleted_member"] += 1

    return summary


def _build_duplicate_member_sql():
    """
    同一性キーが重複している多段変数メンバー行だけを取得する SQL を組み立てる
    """
    key_columns = []
    join_conditions = []
    for column in COMPARE_KEYS:
        key_columns.append(f"`{column}`")
        join_conditions.append(f"`m`.`{column}` <=> `d`.`{column}`")
    key_column_str = ", ".join(key_columns)
    join_condition_str = " AND ".join(join_conditions)
    sql = (
        f"SELECT `m`.* FROM `{T_MEMBER}` `m` "
        f"JOIN (SELECT {key_column_str} FROM `{T_MEMBER}` GROUP BY {key_column_str} HAVING COUNT(*) >= 2) `d` "
        f"ON {join_condition_str}"
    )
    return sql


def _compare_key(record):
    """
    多段変数メンバーの同一性キー（変数刈取と同じく str() で比較する）
    """
    key_list = []
    for column in COMPARE_KEYS:
        key_list.append(str(record.get(column)))
    return tuple(key_list)


def _active_first_sort_key(record, id_column):
    """
    「残す行」を選ぶときの共通の並び順キー（先頭に来たものを残す）
    優先順: 有効(DISUSE_FLAG='0') → id_column の昇順
    """
    disuse_order = 0 if str(record.get("DISUSE_FLAG")) == "0" else 1
    return (disuse_order, str(record[id_column]))


def _survivor_sort_key(record):
    """
    残す多段変数メンバーの並び順キー
    """
    return _active_first_sort_key(record, "ARRAY_MEMBER_ID")


def _col_comb_sort_key(record):
    """
    多段変数配列組合せ管理の並び順キー
    """
    return _active_first_sort_key(record, "COL_SEQ_COMBINATION_ID")


def _max_col_sort_key(record):
    """
    多段変数最大繰返数管理の並び順キー
    """
    return _active_first_sort_key(record, "MAX_COL_SEQ_ID")


def _normalize_col_seq_value(col_seq_value):
    """
    列順序の NULL / 空文字を None に揃える
    """
    if col_seq_value is None or col_seq_value == "":
        return None
    return str(col_seq_value)


def _select_in_chunks(ws_db, table_name, column_name, id_list):
    """
    指定カラムが id_list に含まれるレコードを分割して SELECT する
    """
    result = []
    for index in range(0, len(id_list), SELECT_CHUNK_SIZE):
        chunk = id_list[index:index + SELECT_CHUNK_SIZE]
        rows = ws_db.table_select(table_name, f"WHERE `{column_name}` IN %s", [chunk])
        result.extend(rows)
    return result
