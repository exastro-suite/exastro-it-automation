#!/bin/bash -e
IFS=$',\n'
TARGET="$1"
if [ -n ${TARGET} ]; then
  cp -p "${TARGET}" "${TARGET}_bak"
  cp -p "${TARGET}" "${TARGET}_reps"
else
  echo "PLEASE Define TARGET Files."
  exit 1
fi
TARGET="${TARGET}_reps"
echo "TARGET FILE  : ${TARGET}"
echo "BACKUP COMPLETE."
target_lines=($(grep -n -E -e '^INSERT INTO' ${TARGET} | grep -E -e '(LAST_UPDATE_TIMESTAMP|LAST_UPDATE_USER)' | sed -e 's/:.*//g'))
parent_counter=1
for tmp_lns in ${target_lines[@]}
do
  printf '\r\033[KTARGET LINES : '${tmp_lns}' -> InProgress...('${parent_counter}'/'${#target_lines[@]}')'
  IFS=','
  column_def=($(sed -n "${tmp_lns}p" ${TARGET} | awk 'match($0,/\(.*\) VALU/,a) {gsub(/\(/,"", a[0]);gsub(/\) VALU/,"", a[0]);gsub(/`/,"\047", a[0]);gsub(/\047, \047/,"\047,\047", a[0]);print a[0]}'))
  values_def=($(sed -n "${tmp_lns}p" ${TARGET} | tr '\\' 'y' | awk 'match($0,/VALUES \(.*\)/,a) {gsub(/VALUES \(/,"", a[0]);gsub(/\047, \047/,"\047,\047", a[0]);gsub(/[^0-9|\047|L],/,"c", a[0]);gsub(/TTL,/,"c", a[0]);gsub(/, y/,"cy", a[0]);gsub(/,y/,"cy", a[0]);gsub(/, [a-zA-Z][^U]/,"c C", a[0]);gsub(/,[a-zA-Z][^U]/,"cC", a[0]);gsub(/, 最/,"c 最", a[0]);gsub(/, \}/,"c }", a[0]);gsub(/,\}/,"c}", a[0]);print substr(a[0], 1, length(a[0])-1)}'))
  tmp_counter=0
  ts_counter=0
  is_ts_found=false
  us_counter=0
  is_us_found=false
  jnlts_counter=0
  is_jnlts_found=false
  for tmp_var in ${column_def[@]}
  do
    if [ ${tmp_var} = ''\''LAST_UPDATE_TIMESTAMP'\''' ];then
      ts_counter=${tmp_counter}
      is_ts_found=true
    elif [ ${tmp_var} = ''\''LAST_UPDATE_USER'\''' ];then
      us_counter=${tmp_counter}
      is_us_found=true
    elif [ ${tmp_var} = ''\''JOURNAL_REG_DATETIME'\''' ];then
      jnlts_counter=${tmp_counter}
      is_jnlts_found=true
    elif [ ${tmp_var} = ''\''LAST_UPDATE_TIMESTAMP'\'' ' ];then
      ts_counter=${tmp_counter}
      is_ts_found=true
    elif [ ${tmp_var} = ''\''LAST_UPDATE_USER'\'' ' ];then
      us_counter=${tmp_counter}
      is_us_found=true
    elif [ ${tmp_var} = ''\''JOURNAL_REG_DATETIME'\'' ' ];then
      jnlts_counter=${tmp_counter}
      is_jnlts_found=true
    fi
    tmp_counter=$((tmp_counter + 1))
  done
  values_def_tmp=(${values_def[@]})
  if "${is_ts_found}";then
    values_def_tmp[${ts_counter}]=''\''NOTCOMPARE'\'''
  fi
  if "${is_us_found}";then
    values_def_tmp[${us_counter}]=''\''NOTCOMPARE'\'''
  fi
  if "${is_jnlts_found}";then
    values_def_tmp[${jnlts_counter}]=''\''NOTCOMPARE'\'''
  fi
  values_def_rep="VALUES ( "
  tmp_counter=0
  for tmp_var in ${values_def_tmp[@]}
  do
    if [ ${tmp_counter} -ne 0 ];then
      values_def_rep=${values_def_rep}", "
    fi
    tmp_var=${tmp_var}
    values_def_rep=${values_def_rep}${tmp_var}
    tmp_counter=$((tmp_counter + 1))
  done
  values_def_rep=${values_def_rep}" )"
  IFS=$' '
  sed -i "${tmp_lns} c `sed -n "${tmp_lns}p" ${TARGET} | awk 'match($0,/VALUES \(.*\)/,a) {print substr($0, 1, RSTART-1)}'`${values_def_rep}`sed -n "${tmp_lns}p" ${TARGET} | awk 'match($0,/VALUES \(.*\)/,a) {print substr($0, RSTART+RLENGTH, length($0))}'`" ${TARGET}
  printf '\r\033[KTARGET LINES : '${tmp_lns}' -> REPLACE COMPLETE.'
  parent_counter=$((parent_counter + 1))
done
printf '\r\033[KINSERT REPLACE COMPLETE.\n'
IFS=$',\n'
target_lines=($(grep -n -E -e '(DEFINER|WORKSPACE_ID)' ${TARGET} | sed -e 's/:.*//g'))
parent_counter=1
for tmp_lns in ${target_lines[@]}
do
  printf '\r\033[KTARGET LINES : '${tmp_lns}' -> InProgress...('${parent_counter}'/'${#target_lines[@]}')'
  tmp_out=$(echo $(sed -n "${tmp_lns}p" ${TARGET} | awk '{gsub(/DEFINER=`.*`@/,"DEFINER=`NOTCOMPARE`@", $0);gsub(/`WORKSPACE_ID`,\047ITA_WS_.*\047 AS `WORKSPACE_DB`/,"`WORKSPACE_ID`,\047ITA_WS_NOTCOMPARE\047 AS `WORKSPACE_DB`", $0); print $0;}'))
  sed -i "${tmp_lns} c ${tmp_out}" ${TARGET}
  printf '\r\033[KTARGET LINES : '${tmp_lns}' -> REPLACE COMPLETE.'
  parent_counter=$((parent_counter + 1))
done
printf '\r\033[KDEFINER REPLACE COMPLETE.\n'
IFS=$' '
echo "ACTION COMPLETE."
exit 0