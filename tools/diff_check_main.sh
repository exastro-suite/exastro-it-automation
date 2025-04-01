#!/bin/bash -e
tmp_date=$(date '+%Y-%m-%d_%H-%M-%S')
if [ "$#" -eq 3 ];then
  if [ "$1" = "sql" ];then
    if [ -n ${2} ] && [ -n ${3} ]; then
      type git || sudo dnf install -y git || {
      echo "Need Git Command."
      exit 1
      }
      /bin/bash diff_check_reps.sh ${2} || {
      echo "diff_check_reps.sh Exited Non-Zero Code."
      exit 1
      }
      /bin/bash diff_check_reps.sh ${3} || {
      echo "diff_check_reps.sh Exited Non-Zero Code."
      exit 1
      }
      git diff --word-diff "${2}_reps" "${3}_reps"
      echo "Git Diff Result -> sql_simple-diff_${tmp_date}"
      git -P diff --word-diff "${2}_reps" "${3}_reps" > sql_git-diff_${tmp_date}
      echo "Simple Diff Result -> sql_simple-diff_${tmp_date}"
      diff -B -b -E -w "${2}_reps" "${3}_reps" > sql_simple-diff_${tmp_date}
      exit 0
    else
      echo "Target Files Param Error."
      exit 1
    fi
  elif [ "$1" = "tgz" ];then
    if [ -n ${2} ] && [ -n ${3} ]; then
      type tree || sudo dnf install -y tree || {
      echo "Need Tree Command."
      exit 1
      }
      mkdir -p ${2%.*}
      tar xzf ${2} -C ${2%.*} || {
      echo "Non-Zero Code Exited."
      exit 1
      }
      mkdir -p ${3%.*}
      tar xzf ${3} -C ${3%.*} || {
      echo "Non-Zero Code Exited."
      exit 1
      }
      tree ${2%.*} -a -o ${2%.*}_tree -n && tree ${3%.*} -a -o ${3%.*}_tree -n || {
        echo "Tree CMD Non-Zero Code Exited."
        exit 1
      }
      echo "Simple Diff Result -> simple-diff_${tmp_date}"
      diff -r --no-dereference "${2%.*}" "${3%.*}" > simple-diff_${tmp_date}
      echo "Tree Diff Result -> tree-diff_${tmp_date}"
      diff -y -B -b -E -w "${2%.*}_tree" "${3%.*}_tree" | expand > tree-diff_${tmp_date}
      exit 0
    else
      echo "Target Files Param Error."
      exit 1
    fi
  fi
else
  echo "USAGE: /bin/bash diff_check_main.sh [sql/tgz] Target_File1 Target_File2"
  exit 1
fi
exit 0