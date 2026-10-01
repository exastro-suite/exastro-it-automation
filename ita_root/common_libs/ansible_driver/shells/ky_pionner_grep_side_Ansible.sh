#!/bin/bash
# Copyright 2022 NEC Corporation#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
######################################################################
##
##  【概要】
##      pioneer ansibleモジュール デフォルト文字列検索
##
##  【特記事項】
##      <<引数>>
##       $1    :検索ファイル
##       $2～  :検索文字列(複数指定可能)
##
##      <<返却値>>
##       0      検索文字列あり(複数指定時は全ての検索文字列が検索できた場合)
##       1      検索文字列なし
##
######################################################################
STDERR='/tmp/ita_stderr.'$$
# 検索ファイルを取得
GREP_FILE="${1}"
shift
# 検索文字列が指定されていない場合は異常終了
if [ ${#} -eq 0 ]; then
    exit 1
fi
EXIT_CODE=0
# 検索文字列毎に検索ファイルを検索し、全ての検索文字列が検索できた場合のみ正常終了(AND条件)
for ARG in "$@"
do
    # 検索された行数取得
    CNT=`grep -c -- "${ARG}" "${GREP_FILE}" 2>${STDERR}`
    RET=$?
    # grepコマンドが実行出来なかった場合(検索文字列なしは1)
    if [ ${RET} -gt 1 ]; then
        EXIT_CODE=${RET}
        break
    fi
    # grepコマンドでエラーになった場合
    if [ -s ${STDERR} ]; then
        EXIT_CODE=1
        break
    fi
    # 0行の場合は異常終了
    if [ ${CNT} -eq 0 ]; then
        EXIT_CODE=1
        break
    fi
done
/bin/rm -rf ${STDERR} >/dev/null 2>&1
exit ${EXIT_CODE}
