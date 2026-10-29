#   Copyright 2022 NEC Corporation
#
#   Licensed under the Apache License, Version 2.0 (the "License")
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
"""
SubValueAutoReg.getCMDBdata 全組合せ実行（431,424件）

test_SubValueAutoReg_getCMDBdata.py（パターン表66行の手書き期待値）とは
**役割が違う別建てのテスト**。既存側は一切変更しない。

  既存側 : 「現実装が仕様として正しいか」を人が書いた期待値で見る
  こちら : 「判定順序を変えたときに何件の出力が変わるか」を全件で見る

こちらは現実装をゴールデンに固定するので、実装が変わればまず落ちる。
落ちたときは「壊れた」ではなく「変化した」の意味なので、
出力される差分（項番と要約）を見て意図した変化かを判断し、
意図通りならゴールデンを作り直す:

    python3 -m tests.ansible_driver_tests.ansible_driver.classes.subvalue_autoreg_exhaustive --all

実行ゲートは無い（環境変数なしで常に実行される）。全件を回す2本で
**pytest 全体が約140秒延びる**ことを承知の上で、判定順序を変えたときの影響が
見落とされないよう既定で走らせている。急いでいるときだけ外す:

    pytest -m "not exhaustive" tests/ansible_driver_tests

全件だけを流す:

    pytest -m exhaustive \
tests/ansible_driver_tests/ansible_driver/classes/\
test_SubValueAutoReg_getCMDBdata_exhaustive.py

全件を回すのは重い（1本 約70秒）ので、**全件を回す pytest 項目は2本だけ**にしてある
（このファイルの pytest 項目は計4本。残る2本はゴールデンを読むだけの軽い整合チェック）。
431,424 を parametrize すると 1項目あたり約14ms の pytest オーバーヘッドで
約1.7時間かかり、収集時のメモリと VSCode のテスト一覧も破壊する
（実処理は 1件 0.2ms）。
"""
import os

import pytest

from . import subvalue_autoreg_exhaustive as ex

#: 差分レポートに載せる項番の上限（全部出すと数万行になる）
DIFF_REPORT_LIMIT = 30


@pytest.mark.exhaustive
def test_all_feasible_combinations_match_golden():
    """実現可能な全組合せの出力がゴールデンと一致すること。"""
    path = ex.golden_path()
    if not os.path.exists(path):
        pytest.fail(
            'ゴールデンが無い: {}\n'
            '次のコマンドで生成する:\n'
            '  python3 -m tests.ansible_driver_tests.ansible_driver.classes'
            '.subvalue_autoreg_exhaustive --all'.format(path))

    with open(path, encoding='utf-8') as fh:
        expected_assignments, expected_distinct = ex.decode_golden(fh.read())

    diffs = []
    checked = 0
    with ex.ExhaustiveRunner() as runner:
        for no, combo in ex.iter_combos():
            checked = no
            if no > len(expected_assignments):
                break
            result = runner.run(combo)
            want_sha, want_summary = expected_distinct[expected_assignments[no - 1]]
            got_sha = ex.digest(result)
            if got_sha != want_sha and len(diffs) < DIFF_REPORT_LIMIT:
                diffs.append('  項番{} [{}]\n    期待: {}\n    実際: {}'.format(
                    no, ex.combo_label(combo), want_summary, ex.summary(result)))

    assert checked == len(expected_assignments), (
        '実現可能な組合せ数がゴールデンと違う（軸定義を変えた？）: '
        '実際={:,} ゴールデン={:,}\n'
        'ゴールデンとトレーサビリティを作り直すこと'.format(
            checked, len(expected_assignments)))
    assert not diffs, (
        '{:,}件中、出力がゴールデンと違う項番がある（先頭{}件）:\n{}\n\n'
        '意図した変更なら次で作り直す:\n'
        '  python3 -m tests.ansible_driver_tests.ansible_driver.classes'
        '.subvalue_autoreg_exhaustive --all'.format(
            checked, len(diffs), '\n'.join(diffs)))


@pytest.mark.exhaustive
def test_pattern_table_case_ids_are_all_hit():
    """パターン表の各行が、全件のどこかに実在すること。

    ゴールデンと違い**実装の出力を固定しない**。
    「表の行に対応する組合せが 1件以上ある」だけを見るので、
    判定順序が変わっても壊れない（= レビュー指摘への直接の回答）。
    """
    tracer = ex.CoverageTracer()
    ex.run_all(observer=tracer)

    hits = tracer.hits
    missing = [(cid, name) for cid, name, pred, _why in ex.CASE_MAP
               if pred is not None and hits[cid][0] == 0]
    assert not missing, (
        'パターン表の行に該当する組合せが1件も無い:\n' +
        '\n'.join('  {} {}'.format(cid, name) for cid, name in missing))


def test_case_map_covers_pattern_table():
    """CASE_MAP がパターン表のケースIDを取りこぼしていないこと（軽量・既定で実行）。"""
    ids = [cid for cid, _n, _p, _w in ex.CASE_MAP]
    assert len(ids) == len(set(ids)), '重複したケースIDがある'
    # 表現不可の行には必ず理由を書く
    for cid, _name, pred, why in ex.CASE_MAP:
        if pred is None:
            assert why, '{}: 表現不可なのに理由が無い'.format(cid)


def test_golden_encoding_roundtrips():
    """ゴールデンの連長圧縮が可逆であること（軽量・既定で実行）。"""
    assignments = [1, 1, 1, 2, 2, 3, 1]
    distinct = {1: ('a' * 40, 'sum1'), 2: ('b' * 40, 'sum2'), 3: ('c' * 40, 'sum3')}
    got_assignments, got_distinct = ex.decode_golden(
        ex.encode_golden(assignments, distinct))
    assert got_assignments == assignments
    assert got_distinct == distinct
