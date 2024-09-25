#!/bin/sh

set -ue

#########################################
# Environment variable
#########################################

### Set enviroment parameters
# DEPLOY_FLG="a"
# REMOVE_FLG=""
REQUIRED_MEM_TOTAL=4000000
REQUIRED_FREE_FOR_CONTAINER_IMAGE=25600
REQUIRED_FREE_FOR_EXASTRO_DATA=1024
# DOCKER_COMPOSE_VER="v2.20.3"
# PROJECT_DIR="${HOME}/exastro-docker-compose"
# COMPOSE_FILE="${PROJECT_DIR}/docker-compose.yml"
LOG_FILE="${HOME}/exastro-installation.log"
# ENV_FILE="${PROJECT_DIR}/.env"
# COMPOSE_PROFILES="base"
EXASTRO_UNAME=$(id -u -n)
# EXASTRO_UID=$(id -u)
# EXASTRO_GID=1000
# ENCRYPT_KEY='Q2hhbmdlTWUxMjM0NTY3ODkwMTIzNDU2Nzg5MDEyMzQ='
# SERVICE_TIMEOUT_SEC=1800
# GITLAB_PROTOCOL=http
# GITLAB_PORT=http
# GITLAB_ROOT_PASSWORD='Ch@ngeMeGL'
# GITLAB_ROOT_TOKEN='change-this-token'
# MONGO_INITDB_ROOT_PASSWORD=Ch@ngeMeDBAdm
# MONGO_HOST=mongo
# MONGO_ADMIN_PASSWORD=Ch@ngeMeDBAdm

# is_use_oase=true
# is_use_gitlab_container=false
# is_set_exastro_external_url=false
# is_set_exastro_mng_external_url=false
# is_set_gitlab_external_url=false
# if [ -f ${ENV_FILE} ]; then
#     . ${ENV_FILE}
# fi

SETUP_VERSION=""
EXECUTE_PATH=""
WORK_DIR=""
ENV_TMP_PATH=""
INSTALL_ID=`date +%Y%m%d%H%M%S%3N`
INSTALL_TYPE=1

SOURCE_REPOSITORY="https://github.com/exastro-suite/exastro-it-automation.git"
SOURCE_REPOSITORY="https://github.com/exastro-suite/exastro-it-automation-dev.git" #*****
SOURCE_REPOSITORY_NAME="exastro-it-automation"

SOURCE_DIR_NAME="ita_ag_ansible_execution"
SOURCE_DIR_PATH="ita_root/ita_ag_ansible_execution"

#########################################
# install config variable:
#########################################

# dnf install list: common
dnf_install_list_common=(
    # "podman-docker"
    "gcc"
    "openssh-clients"
    # "python39"
    # "python39-devel"
    "langpacks-en"
    "wget"
    # "zip"
    "unzip"
    "git"
)

# dnf install list: specific
dnf_install_list_rhel8=()
dnf_install_list_rhel9=()
dnf_install_list_almaLinux8=()

# install source_path src->dst
declare -A src_source_paths
declare -A dct_source_paths

src_source_paths["0"]="ita_root/ita_ag_ansible_execution/*"
src_source_paths["1"]="ita_root/messages"
src_source_paths["2"]="ita_root/agent"
src_source_paths["3"]="ita_root/common_libs/common"
src_source_paths["4"]="ita_root/common_libs/ag"
src_source_paths["5"]="ita_root/common_libs/ansible_driver"

dct_source_paths["0"]="/ita_ag_ansible_execution"
dct_source_paths["1"]="/ita_ag_ansible_execution/"
dct_source_paths["2"]="/ita_ag_ansible_execution/"
dct_source_paths["3"]="/ita_ag_ansible_execution/common_libs/"
dct_source_paths["4"]="/ita_ag_ansible_execution/common_libs/"
dct_source_paths["5"]="/ita_ag_ansible_execution/common_libs/"

dct_create_paths["0"]="/ita_ag_ansible_execution"
dct_create_paths["1"]="/ita_ag_ansible_execution/common_libs"

#########################################
# .env default variable:
#########################################
declare -A default_env_values

BASE_DIR=/exastro2 #*****
STORAG_DIR=/storage/
ENV_PATH=""
STORAGE_PATH=""
default_env_values=(
    # ita_root/ita_ag_ansible_execution/Dockerfile
    ["USERNAME"]=app_user
    ["GROUPNAME"]=app_user
    ["APP_PATH"]=${BASE_DIR}
    ["PYTHONPATH"]=${BASE_DIR}/
    ["LANGUAGE"]=en
    ["STORAGEPATH"]=${STORAG_DIR}
    ["SERVICE_NAME"]=ita-ag-ansible-execution
    ["USER_ID"]=ita-ag-ansible-execution
    # ita_root/ita_ag_ansible_execution/.env
    # common
    ["TZ"]=Asia/Tokyo
    ["DEFAULT_LANGUAGE"]=en
    # ag-agent
    ["AGENT_NAME"]=agent-ansible-execution-01
    ["EXASTRO_ORGANIZATION_ID"]=""
    ["EXASTRO_WORKSPACE_ID"]=""
    ["EXASTRO_REFRESH_TOKEN"]=""
    ["EXASTRO_URL"]=""
    ["ITERATION"]=10
    ["EXECUTE_INTERVAL"]=5
    ["LOG_LEVEL"]=INFO
    ["CHILD_PROCESS_RETRY_LIMIT"]=0
    ["EXECUTION_ENVIRONMENT_NAMES"]=""
    ["ENTRYPOINT"]=""
    ["REFERENCE_ENVPATH"]=""
)
# use .env key
output_env_values=(
    "USERNAME"
    "GROUPNAME"
    "APP_PATH"
    "PYTHONPATH"
    "LANGUAGE"
    "STORAGEPATH"
    "SERVICE_NAME"
    "USER_ID"
    "TZ"
    "DEFAULT_LANGUAGE"
    "AGENT_NAME"
    "EXASTRO_ORGANIZATION_ID"
    "EXASTRO_WORKSPACE_ID"
    "EXASTRO_REFRESH_TOKEN"
    "EXASTRO_URL"
    "ITERATION"
    "EXECUTE_INTERVAL"
    "LOG_LEVEL"
    "CHILD_PROCESS_RETRY_LIMIT"
    "EXECUTION_ENVIRONMENT_NAMES"
)

#########################################
# interactive
#########################################
# interactive default value
default_env_values["AGENT_VERSION"]="main"
default_env_values["ANSIBLE_SUPPORT"]="1"
default_env_values["INSTALLPATH"]=${HOME}${BASE_DIR}
default_env_values["DATAPATH"]=${HOME}${BASE_DIR}
default_env_values["AGENT_SERVICE_NAME"]=""
default_env_values["AGENT_SERVICE_NAME_YN"]="y"

#  interactive key
additional_env_keys=(
    "AGENT_SERVICE_NAME_YN"
    "AGENT_SERVICE_NAME"
    "AGENT_VERSION"
    "INSTALLPATH"
    "DATAPATH"
    "ANSIBLE_SUPPORT"
    "EXASTRO_URL"
    "EXASTRO_ORGANIZATION_ID"
    "EXASTRO_WORKSPACE_ID"
    "EXASTRO_REFRESH_TOKEN"
    # "EXECUTION_ENVIRONMENT_NAMES"
)

# interactive list
declare -A interactive_llist=(
    # msg
    ["INSTALL_TYPE_MSG0"]="実施する処理を選択してください。"
    ["INSTALL_TYPE_MSG1"]="    1: ENVの作成 + インストール(dnf, pip, ソース配置) + サービスの登録"
    ["INSTALL_TYPE_MSG2"]="    2: ENVの作成 + サービスの登録"
    ["INSTALL_TYPE_MSG3"]="    3: サービスの登録"
    ["INSTALL_TYPE_MSG4"]="    4: ソース配置"
    ["INSTALL_TYPE_MSGq"]="    q: インストーラ終了"
    ["INSTALL_TYPE_MSGr"]="select value: (1, 2, 3, q)  :"
    ["INVALID_VALUE_IT"]="Invalid value!! (1, 2, 3, q)"
    ["_TOP_MSG"]="以降、default値有りで、「未入力+Enter」の場合は、default値が適用されます。"
    ["INVALID_VALUE_YN"]="Invalid value!! (y/n)"
    ["INVALID_VALUE_AS"]="Invalid value!! (1, 2)"
    ["INVALID_VALUE_E1"]="Invalid value!! [0-9a-zA-Z-_]"
    ["INVALID_VALUE_URL"]="Invalid URL format"
    ["INVALID_SETUP_VERSION"]="指定したバージョンが不正です。"
    ["SERVICE_MSG_START"]="エージェントのサービスを開始しますか? (y/n)"
    ["INVALID_VALUE_F_ENV"]=".envファイルが存在しません。パスを確認してください。"

    # 環境情報
    ["AGENT_SERVICE_NAME_YN"]="エージェントのサービス名は、${INSTALL_ID}です。個別に指定する場合は、「n」を選択して指定ください。(y/n) "
    ["AGENT_SERVICE_NAME"]="エージェントのサービス名を入力してください。"
    ["AGENT_VERSION"]="エージェントバージョンを入力してください。タグ指定: X.Y.Z, ブランチ指定: X.Y [default: 未入力+Enter(最新のリリースバージョン)]"
    ["INSTALLPATH"]="インストール先をフルパスで指定してください。"
    ["DATAPATH"]="データ保存先をフルパスで指定してください。"
    ["ANSIBLE_SUPPORT"]="利用するAnsible-builder, Ansible-runnerを選択してください。(1, 2) [1=OSS 2=Enterprise] "
    ["EXASTRO_URL"]="ITAへの接続先URLを入力してください。"
    ["EXASTRO_ORGANIZATION_ID"]="ORGANIZATION_IDを入力してください。"
    ["EXASTRO_WORKSPACE_ID"]="WORKSPACE_IDを入力してください。"
    ["EXASTRO_REFRESH_TOKEN"]="ITAへログイン可能なユーザーのREFRESH_TOKENを入力してください。ここで入力しない場合、生成された.envファイルのEXASTRO_REFRESH_TOKENを変更してください。"
    # ["EXECUTION_ENVIRONMENT_NAMES"]="実行環境を入力してください。参照：Ansible共通->実行環境管理->実行環境名 複数の場合は「,」区切りで入力 ex) ag01,ag02"
    # サービス登録のみ
    ["REFERENCE_ENVPATH"]=".envファイルのフルパス入力してください。"
    # ソース先重複
    ["SOURCE_UPDATE"]="インストール先に、既にソースが存在します。クリアして、インストールしますか？ (y:再インストール/n:インストールせずに、次の処理へ)  (y/n)"
    ["SOURCE_UPDATE_E1"]="※登録済みのサービスが存在する場合、再インストールすると動作に影響が発生する可能性があります。(y/n): "
)

declare -A interactive_llist_adv=(
    ["EXASTRO_REFRESH_TOKEN_1"]="後ほど、生成された.envファイルのEXASTRO_REFRESH_TOKENを変更してください。"
)

#########################################
# Utility functions
#########################################

### Logger functions
info() {
    echo `date`' [INFO]:' "$@" | tee -a "${LOG_FILE}"
}
warn() {
    echo `date`' [WARN]:' "$@" >&2 | tee -a "${LOG_FILE}"
}
error() {
    echo `date`' [ERROR]:' "$@" >&2 | tee -a "${LOG_FILE}"
    exit 1
}

### Convert to lowercase
to_lowercase() {
    echo "$1" | sed "y/ABCDEFGHIJKLMNOPQRSTUVWXYZ/abcdefghijklmnopqrstuvwxyz/"
}

### Generate password
generate_password() {
    # Specify the length of the password
    length="$1"
    # Generate a random password
    password=$(dd if=/dev/urandom bs=1 count=100 2>/dev/null | base64 | tr -dc 'a-zA-Z0-9' | fold -w $length | head -n 1)
    # Display the generated password
    echo $password
}

### Check System
get_system_info() {
    if [ $(to_lowercase $(uname)) != "linux" ]; then
        error "Not supported OS."
    fi

    ARCH=$(uname -p)
    OS_TYPE=$(uname)
    OS_NAME=$(awk -F= '$1=="NAME" { print $2; }' /etc/os-release | tr -d '"')
    VERSION_ID=$(awk -F= '$1=="VERSION_ID" { print $2; }' /etc/os-release | tr -d '"')
    if ( echo "${OS_NAME}" | grep -q -e "Red Hat Enterprise Linux" ); then
        if [ $(expr "${VERSION_ID}" : "^7\..*") != 0 ]; then
            DEP_PATTERN="RHEL7"
        fi
        if [ $(expr "${VERSION_ID}" : "^8\..*") != 0 ]; then
            if [ $(expr "${VERSION_ID}" : "^8\.[0-2]$") != 0 ]; then
                error "Not supported OS. Required Red Hat Enterprise Linux release 8.3 or later."
            fi
            DEP_PATTERN="RHEL8"
        fi
        if [ $(expr "${VERSION_ID}" : "^9\..*") != 0 ]; then
            DEP_PATTERN="RHEL9"
        fi
    elif [ "${OS_NAME}" = "AlmaLinux" ]; then
        if [ $(expr "${VERSION_ID}" : "^8\..*") != 0 ]; then
            DEP_PATTERN="AlmaLinux8"
        fi
    elif [ "${OS_NAME}" = "Ubuntu" ]; then
        if [ $(expr "${VERSION_ID}" : "^20\..*") != 0 ]; then
            DEP_PATTERN="Ubuntu20"
        elif [ $(expr "${VERSION_ID}" : "^22\..*") != 0 ]; then
            DEP_PATTERN="Ubuntu22"
        fi
    fi
}


### Check requirements
check_requirement() {
    check_system
    check_security
    check_command
    check_resource
}

### Check system requirements
check_system() {
    printf "$(date) [INFO]: Checking Operating System.....................\n" | tee -a "${LOG_FILE}"

    # Check CPU architecture
    if [ "${ARCH}" != "x86_64" ] && [ "${ARCH}" != "amd64" ]; then
        printf "\r\033[1F\033[K$(date) [INFO]: Checking Operating System......................ng" | tee -a "${LOG_FILE}"
        printf "\r\033[1E\033[K" | tee -a "${LOG_FILE}"
        error "CPU architecture not supported."
    fi

    # Check OS type
    OS_TYPE=$(to_lowercase $(uname))
    if [ "${OS_TYPE}" != "linux" ]; then
        error "OS not supported."
    fi
    OS_TYPE=$(uname)

    # Check OS
    info "NAME:         ${OS_NAME}"
    info "VERSION_ID:   ${VERSION_ID}"
    info "ARCH:         ${ARCH}"

    set +u
    PROXY=${http_proxy}
    sleep 1
    if [ -z "${PROXY}" ]; then
        info "PROXY:        None"
    else
        info "PROXY:        ${PROXY}"
    fi
    set -u

    case "${DEP_PATTERN}" in
        RHEL8 )
            ;;
        RHEL9 )
            ;;
        AlmaLinux8 )
            ;;
        Ubuntu20 )
            ;;
        Ubuntu22 )
            ;;
        * )
            printf "\r\033[5F\033[K$(date) [INFO]: Checking Operating System......................ng" | tee -a "${LOG_FILE}"
            printf "\r\033[5E\033[K" | tee -a "${LOG_FILE}"
            error "Unsupported OS."
            ;;
    esac

    sleep 1
    printf "\r\033[5F\033[K$(date) [INFO]: Checking Operating System......................ok" | tee -a "${LOG_FILE}"
    printf "\r\033[5E\033[K" | tee -a "${LOG_FILE}"
    echo ""

}

### Check system requirements
check_security() {
    printf "$(date) [INFO]: Checking running security services.............\n" | tee -a "${LOG_FILE}"
    SELINUX_STATUS=$(sudo getenforce 2>/dev/null || :)
    if [ "${SELINUX_STATUS}" = "Permissive" ]; then
        info "SELinux is now Permissive mode."
        if [ "${DEP_PATTERN}" != "RHEL8" ] && [ "${DEP_PATTERN}" != "RHEL9" ]; then
            printf "\r\033[2F\033[K$(date) [INFO]: Checking running security services.............check\n" | tee -a "${LOG_FILE}"
            printf "\r\033[2E\033[K" | tee -a "${LOG_FILE}"
        fi
    else
        info "SELinux is not Permissive mode."
        if [ "${DEP_PATTERN}" = "RHEL8" ] || [ "${DEP_PATTERN}" = "RHEL9" ]; then
            printf "\r\033[2F\033[K$(date) [INFO]: Checking running security services.............ng\n" | tee -a "${LOG_FILE}"
            printf "\r\033[2E\033[K" | tee -a "${LOG_FILE}"
            error "In Rootless Podman environment, SELinux only supports Permissive mode."
        fi
    fi

    FIREWALLD_STATUS=$(sudo firewall-cmd --state 2>/dev/null || :)
    if echo "${FIREWALLD_STATUS}" | grep -qi "running"; then
        printf "\r\033[2F\033[K$(date) [INFO]: Checking running security services.............check\n" | tee -a "${LOG_FILE}"
        printf "\r\033[2E\033[K" | tee -a "${LOG_FILE}"
        warn "Firewalld is now running."
        FIREWALLD_STATUS="active"
    else
        info "Firewalld is not running."
        FIREWALLD_STATUS="inactive"
    fi

    UFW_STATUS=$(sudo ufw status 2>/dev/null || :)
    if echo "${UFW_STATUS}" | grep -qi "status: active"; then
        printf "\r\033[3F\033[K$(date) [INFO]: Checking running security services.............check\n" | tee -a "${LOG_FILE}"
        printf "\r\033[3E\033[K" | tee -a "${LOG_FILE}"
        warn "UFW is now active."
        UFW_STATUS="active"
    else
        info "UFW is inactive."
        UFW_STATUS="inactive"
    fi

    sleep 1
    printf "\r\033[4F\033[K$(date) [INFO]: Checking running security services.............ok\n" | tee -a "${LOG_FILE}"
    printf "\r\033[4E\033[K" | tee -a "${LOG_FILE}"

    # if [ "${SELINUX_STATUS}" = "active" ] || [ "${FIREWALLD_STATUS}" = "active" ] || [ "${UFW_STATUS}" = "active" ]; then
    #     echo ""
    #     echo "Security service is active."
    #     read -r -p "Are you sure you want to continue processing? (y/n) [default: n]: " confirm
    #     echo ""
    #     if ! (echo $confirm | grep -q -e "[yY]" -e "[yY][eE][sS]"); then
    #         info "Cancelled."
    #         exit 0
    #     fi
    # fi
    echo ""
}

### Check required command
check_command() {
    printf "$(date) [INFO]: Checking required commands.....................\n" | tee -a "${LOG_FILE}"
    if command -v sudo >/dev/null; then
        info "'sudo' command already exist."
    else
        printf "\r\033[1F\033[K$(date) [INFO]: Checking required commands.....................ng\n" | tee -a "${LOG_FILE}"
        printf "\r\033[1E\033[K" | tee -a "${LOG_FILE}"
        error "Required 'sudo' command and ${EXASTRO_UNAME} is appended to sudoers."
    fi
    sleep 1
    printf "\r\033[2F\033[K$(date) [INFO]: Checking running security services.............ok\n" | tee -a "${LOG_FILE}"
    printf "\r\033[2E\033[K" | tee -a "${LOG_FILE}"
    echo ""
}

### Check required resources
check_resource() {
    printf "$(date) [INFO]: Checking required resource.....................\n" | tee -a "${LOG_FILE}"
    # Total Memory
    info "Total memory (KiB):           $(cat /proc/meminfo  | grep MemTotal | awk '{ print $2 }')"
    if [ $(cat /proc/meminfo  | grep MemTotal | awk '{ print $2 }') -lt ${REQUIRED_MEM_TOTAL} ]; then
        error "Lack of total memory! Required at least ${REQUIRED_MEM_TOTAL} Bytes total memory."
        printf "\r\033[2F\033[K$(date) [INFO]: Checking required resource.....................ng\n" | tee -a "${LOG_FILE}"
        printf "\r\033[2E\033[K" | tee -a "${LOG_FILE}"
    fi

    if [ "${DEP_PATTERN}" != "RHEL8" ] && [ "${DEP_PATTERN}" != "RHEL9" ]; then
        # Check free space of /var
        info "'/var' free space (MiB):      $(df -m /var | awk 'NR==2 {print $4}')"
        if [ $(df -m /var | awk 'NR==2 {print $4}') -lt ${REQUIRED_FREE_FOR_CONTAINER_IMAGE} ]; then
            printf "\r\033[3F\033[K$(date) [INFO]: Checking required resource.....................ng\n" | tee -a "${LOG_FILE}"
            printf "\r\033[3E\033[K" | tee -a "${LOG_FILE}"
            warn "Lack of free space! Required at least ${REQUIRED_FREE_FOR_CONTAINER_IMAGE} MBytes free space on /var directory."
        fi

        # Check free space of current directory
        info "'${HOME}' free space (MiB):         $(df -m "${HOME}" | awk 'NR==2 {print $4}')"
        if [ $(df -m "${HOME}"| awk 'NR==2 {print $4}') -lt ${REQUIRED_FREE_FOR_EXASTRO_DATA} ]; then
            printf "\r\033[4F\033[K$(date) [INFO]: Checking required resource.....................ng\n" | tee -a "${LOG_FILE}"
            printf "\r\033[4E\033[K" | tee -a "${LOG_FILE}"
            warn "Lack of free space! Required at least ${REQUIRED_FREE_FOR_EXASTRO_DATA} MBytes free space on current directory."
        fi
        sleep 1
        printf "\r\033[4F\033[K$(date) [INFO]: Checking required resource.....................ok\n" | tee -a "${LOG_FILE}"
        printf "\r\033[4E\033[K" | tee -a "${LOG_FILE}"
        echo ""
    else
        # Check free space of /var
        info "'${HOME}' free space (MiB):      $(df -m "${HOME}" | awk 'NR==2 {print $4}')"
        if [ $(df -m ${HOME} | awk 'NR==2 {print $4}') -lt ${REQUIRED_FREE_FOR_CONTAINER_IMAGE} ]; then
            printf "\r\033[3F\033[K$(date) [INFO]: Checking required resource.....................ng\n" | tee -a "${LOG_FILE}"
            printf "\r\033[3E\033[K" | tee -a "${LOG_FILE}"
            warn "Lack of free space! Required at least ${REQUIRED_FREE_FOR_CONTAINER_IMAGE} MBytes free space on ${HOME} directory."
        else
            sleep 1
            printf "\r\033[3F\033[K$(date) [INFO]: Checking required resource.....................ok\n" | tee -a "${LOG_FILE}"
            printf "\r\033[3E\033[K" | tee -a "${LOG_FILE}"
            echo ""
        fi
    fi
}


### Check args
check_args() {
    if [ "$1" = 0 ]; then
        cat <<'_EOF_'

Usage:
  sh <(curl -Ssf https://ita.exastro.org/setup) COMMAND [options]
     or
  setup.sh COMMAND [options]

Commands:
  install     Install Ansible Execution Agent
        1: Create .env & Install & Service Register, Start
        2: Create .env & Service Register, Start
        3: Create .env & Service Register, Start
#   uninstall   Uninstall Ansible Execution Agent

_EOF_
        exit 2
    fi
}

dnf_install(){
    echo ""
    info "Install additional tools: ${DEP_PATTERN}"
    case "${DEP_PATTERN}" in
        RHEL8 )
            dnf_install_rhel8
            ;;
        RHEL9 )
            dnf_install_rhel8
            ;;
        AlmaLinux8 )
            dnf_install_almaLinux8
            ;;
        # Ubuntu20 )
        #     ;;
        # Ubuntu22 )
        #     ;;
        * )
            ;;
    esac

    for install_pkg in "${install_list[@]}" ; do
        chk=`dnf list git | grep git | wc -l`
        if [ $chk -eq 0 ]; then
            info "${install_pkg} install start"
            info "dnf install -y ${install_pkg}"
            sudo dnf install -y "${install_pkg}"
            info "${install_pkg} install end"
        else
            info "${install_pkg} installed. skip"
        fi
    done
}
dnf_install_rhel8(){
    install_list=${dnf_install_list_common}
    install_list+=(${dnf_install_list_rhel8[@]})
}

dnf_install_rhel9(){
    install_list=${dnf_install_list_common}
    install_list+=(${dnf_install_list_rhel9[@]})
}

dnf_install_almaLinux8(){
    install_list=${dnf_install_list_common}
    install_list+=(${dnf_install_list_almaLinux8[@]})
}

git_clone(){
    echo ""
    cd "${WORK_DIR}"
    # check git global
    git_global_user_name=`sudo git config --global user.name | wc -c`
    git_global_user_email=`sudo git config --global user.email | wc -c`
    if [ ${git_global_user_name} -le 1 ]; then
        echo "set git config --global user.name user.email"
        sudo git config --global user.name dummyuser
        sudo git config --global user.email dummy@dummy.com
    fi

    # check workdir
    if [ ! -e "${WORK_DIR}/${SOURCE_REPOSITORY_NAME}" ]; then
        info "rm -rfd ${WORK_DIR}/${SOURCE_REPOSITORY_NAME}"
        rm -rfd "${WORK_DIR}/${SOURCE_REPOSITORY_NAME}"
    fi
    # git clone
    info "clone ${SOURCE_REPOSITORY} ${SOURCE_REPOSITORY_NAME}"
    git clone ${SOURCE_REPOSITORY} ${SOURCE_REPOSITORY_NAME}

    # git switch version: tag > branch
    cd "./${SOURCE_REPOSITORY_NAME}"
    SETUP_VERSION=${default_env_values["AGENT_VERSION"]}
    if [ "${SETUP_VERSION}" != "main" ]; then
        git_branch_cnt=`git branch -a | grep "${SETUP_VERSION}" | wc -l`
        git_tag_cnt=`git tag | grep "${SETUP_VERSION}" | wc -l`
        if [ $git_tag_cnt -ge 1 ]; then
            info "git checkout -f -b dummy_${SETUP_VERSION} ${SETUP_VERSION}"
            git checkout -f -b "dummy_${SETUP_VERSION}" "${SETUP_VERSION}"
        elif [ $git_branch_cnt -ge 1 ]; then
            info "git switch ${SETUP_VERSION}"
            git switch ${SETUP_VERSION}
        else
            info "${interactive_llist['INVALID_SETUP_VERSION']} ${SETUP_VERSION}"
            exit 2
        fi
    fi
}

init_workdir(){
    echo ""
    info "init_workdir ${WORK_DIR} start"
    if [ ! -e "${WORK_DIR}" ]; then
        info "create ${WORK_DIR}"
        mkdir -m 777 -p "${WORK_DIR}"
    else
        info "clear & create ${WORK_DIR}"
        rm -rfd "${WORK_DIR}"
        mkdir -m 777 -p "${WORK_DIR}"
    fi
    info "init_workdir ${WORK_DIR} end"
}

clean_workdir(){
    echo ""
    info "clean_workdir ${WORK_DIR} start"
    if [ -d "${WORK_DIR}" ]; then
        info "clear ${WORK_DIR}"
        rm -rfd "${WORK_DIR}"
    fi
    info "clean_workdir ${WORK_DIR} end"
}

inquiry_env(){
    echo ""
    info "inquiry_env :${DEP_PATTERN} start"

    echo "${interactive_llist['_TOP_MSG']}"
    read -r -p "->  Enterで開始" tmp_value

    for env_key in "${additional_env_keys[@]}"; do
        while true; do
            if [ "${env_key}" = "AGENT_SERVICE_NAME" ] && [ "${default_env_values['AGENT_SERVICE_NAME_YN']}" = "y" ];then
                break
            fi

            echo "${interactive_llist[${env_key}]}: "
            if [ -n "${default_env_values[${env_key}]}" ] && [ "${default_env_values[${env_key}]}" != "" ]; then
                read -r -p "Input Value [default: ${default_env_values[${env_key}]} ]: " tmp_value
                echo ""
            else
                read -r -p "Input Value : " tmp_value
                echo ""
            fi

            if [ "$tmp_value" = "" ]; then
                if [ -n "${default_env_values[${env_key}]}" ]; then
                    if [ "${default_env_values[${env_key}]}" != "" ]; then
                        echo ""
                        break
                    fi
                else
                    if [ "${env_key}" = "EXASTRO_REFRESH_TOKEN" ]; then
                        echo ""
                        echo "${interactive_llist_adv[EXASTRO_REFRESH_TOKEN_1]}"
                        break
                    fi
                fi
            else
                # tmp_value valid
                if [ "${env_key}" = "ANSIBLE_SUPPORT" ]; then
                    if echo $tmp_value | grep -q -e "[12]"; then
                        default_env_values[$env_key]=$tmp_value
                        break
                    else
                        echo "${interactive_llist['INVALID_VALUE_AS']}"
                        continue
                    fi
                elif [ ${env_key} = "EXASTRO_URL" ]; then
                    if ! $(echo "${tmp_value}" | grep -q "http://.*") && ! $(echo "${tmp_value}" | grep -q "https://.*") ; then
                        echo "${interactive_llist['INVALID_VALUE_URL']}"
                        continue
                    fi
                elif [ ${env_key} = "AGENT_SERVICE_NAME" ]; then
                    if echo $tmp_value | grep -q -e "^[0-9a-zA-Z\-_]*$"; then
                        default_env_values[$env_key]=$tmp_value
                        break
                    else
                        echo "${interactive_llist['INVALID_VALUE_E1']}"
                        continue
                    fi
                elif [ ${env_key} = "AGENT_SERVICE_NAME_YN" ]; then
                    if echo $tmp_value | grep -q -e "[yY]" -e "[yY][eE][sS]"; then
                        default_env_values[$env_key]=$tmp_value
                        break
                    else
                        echo "${interactive_llist['INVALID_VALUE_YN']}"
                        continue
                    fi
                elif [ ${env_key} = "REFERENCE_ENVPATH" ]; then
                    if [ -f $tmp_value ]; then
                        default_env_values[$env_key]=$tmp_value
                        break
                    else
                        echo "${interactive_llist['INVALID_VALUE_F_ENV']}"
                        continue
                    fi
                fi
                default_env_values[$env_key]=$tmp_value
                break
            fi
        done
    done

    if [ "${default_env_values['AGENT_SERVICE_NAME']}" = "" ];then
        default_env_values['AGENT_SERVICE_NAME']="${INSTALL_ID}"
    fi

    #
    default_env_values["APP_PATH"]=${default_env_values["INSTALLPATH"]}
    default_env_values["PYTHONPATH"]=${default_env_values["INSTALLPATH"]}/ita_ag_ansible_execution/
    default_env_values["AGENT_NAME"]="agent-ansible-execution-${default_env_values['AGENT_SERVICE_NAME']}"
    default_env_values["USER_ID"]="ita-ag-ansible-execution-${default_env_values['AGENT_SERVICE_NAME']}"
    default_env_values["SERVICE_NAME"]="ita-ag-ansible-execution"
    #
    default_env_values["ENTRYPOINT"]="${default_env_values['INSTALLPATH']}/ita_ag_ansible_execution/agent/entrypoint.sh"

    #
    if [ "${default_env_values["DATAPATH"]}" = "${HOME}${BASE_DIR}" ]; then
        default_env_values["STORAGEPATH"]="${HOME}${BASE_DIR}/${default_env_values['AGENT_SERVICE_NAME']}${STORAG_DIR}"
    else
        default_env_values["STORAGEPATH"]="${default_env_values["DATAPATH"]}/${default_env_values['AGENT_SERVICE_NAME']}${STORAG_DIR}"
    fi

    info "inquiry_env :${DEP_PATTERN} end"
}

additional_ansible(){
    for env_key in "${additional_redhat_keys[@]}"; do
        while true; do
            read -r -p "${additional_redhat_values[${env_key}]}: " tmp_value
            echo ""
            if [ "$tmp_value" = "" ]; then
                echo "Invalid value!!"
                continue
            else
                redhat_values[$env_key]=$tmp_value
                break
            fi
        done
    done
}

create_env(){
    echo ""
    info "create_env :${DEP_PATTERN} start"

    # .env作成
    for env_key in "${!default_env_values[@]}"; do
        if printf '%s\n' "${output_env_values[@]}" | grep -qx $env_key; then
            echo -e "${env_key}=${default_env_values[${env_key}]}" >> ${ENV_TMP_PATH}
        fi
    done

    info "create_env :${DEP_PATTERN} end"
}

init_appdir(){
    echo ""
    info "init_workdir ${WORK_DIR} start"
    if [ ! -e "${WORK_DIR}" ]; then
        info "create ${WORK_DIR}"
        mkdir -m 777 -p "${WORK_DIR}"
    else
        info "clear & create ${WORK_DIR}"
        rm -rfd "${WORK_DIR}"
        mkdir -m 777 -p "${WORK_DIR}"
    fi

    info "init_workdir ${WORK_DIR} end"
}

poetry_install(){
    echo ""
    cd "${default_env_values['PYTHONPATH']}"
    # poetry
    pip3.9 install poetry==1.6.0
    poetry config virtualenvs.create true
    poetry install --only first_install
    poetry install --without develop_build
}

ansible_additional_install(){
    if [ ${default_env_values["ANSIBLE_SUPPORT"]} != "1" ]; then
        echo "install redhat ansible"
        sudo pip3.9 uninstall -y ansible-builder ansible-runner
        case "${DEP_PATTERN}" in
            RHEL8 )
                shift
                sudo dnf install ansible-builder ansible-runner
                ;;
            RHEL9 )
                shift
                sudo dnf install ansible-builder ansible-runner
                ;;
            * )
                #*****
                ;;
        esac
    fi
}

install_agent_source(){
    echo ""
    info "install_agent_source start"
    base_path=${default_env_values['APP_PATH']}
    sourcedir_path="${WORK_DIR}/${SOURCE_REPOSITORY_NAME}"

    source_path="${base_path}/${SOURCE_DIR_NAME}"
    echo $source_path
    install_flg=1
    if [ -e $source_path ]; then
        while true; do
            echo "${interactive_llist['SOURCE_UPDATE']}"
            read -r -p  "${interactive_llist['SOURCE_UPDATE_E1']}" confirm
            if echo $confirm | grep -q -e "[yY]" -e "[yY][eE][sS]"; then
                rm -rfd $source_path
                break
            elif echo $confirm | grep -q -e "[nN]" -e "[nN][oO]"; then
                install_flg=2
                break
            else
                echo "Invalid value!! (y/n)"
                continue
            fi
        done
    fi

    if [ $install_flg -eq 1 ]; then
        for dct_create_path in "${!dct_create_paths[@]}"; do
            mkdir -p ${base_path}${dct_create_paths[${dct_create_path}]}
            info "mkdir -p ${base_path}${dct_create_paths[${dct_create_path}]}"
        done

        for src_source_path in "${!src_source_paths[@]}"; do
            cp -rfa ${sourcedir_path}/${src_source_paths[${src_source_path}]} ${base_path}${dct_source_paths[${src_source_path}]}
        done
    else
        echo "install skip"
    fi
    info "install_agent_source end"
}


install_agent_service(){
    info "install_agent_service :${DEP_PATTERN} start"

    # create ~/storage
    STORAGE_PATH="${default_env_values['STORAGEPATH']}"
    info "mkdir -m 777 -p ${STORAGE_PATH}"
    mkdir -m 777 -p "${STORAGE_PATH}"

    # cp .env
    ENV_PATH="${default_env_values["DATAPATH"]}/${default_env_values['AGENT_SERVICE_NAME']}/.env"
    if [ "${default_env_values['REFERENCE_ENVPATH']}" != "" ]; then
        ENV_TMP_PATH="${default_env_values['REFERENCE_ENVPATH']}"
    fi
    info "cp -rf $ENV_TMP_PATH $ENV_PATH"
    cp -rf $ENV_TMP_PATH $ENV_PATH

    case "${DEP_PATTERN}" in
        RHEL8 )
            install_agent_service_rhel8
            ;;
        RHEL9 )
            install_agent_service_rhel8
            ;;
        AlmaLinux8 )
            install_agent_service_rhel8
            ;;
        # Ubuntu20 )
        #     ;;
        # Ubuntu22 )
        #     ;;
        * )
            ;;
    esac
    info "install_agent_service :${DEP_PATTERN} end"
}

install_agent_service_rhel8(){
    ENTRYPOINT=${default_env_values["ENTRYPOINT"]}
    PYTHONPATH=${default_env_values["PYTHONPATH"]}
    AGENT_SERVICE_NAME=${default_env_values['AGENT_SERVICE_NAME']}
    SERVICE_PATH="${default_env_values["DATAPATH"]}/${default_env_values['AGENT_SERVICE_NAME']}/${default_env_values['AGENT_NAME']}.service"
    info "create ${SERVICE_PATH}"
    cat << _EOF_ >${SERVICE_PATH}
[Unit]
Description=Ansible Execution agent for Exastro IT Automation

[Service]
WorkingDirectory=${PYTHONPATH}
ExecStart=${ENTRYPOINT} ${ENV_PATH} ${PYTHONPATH} ${STORAGE_PATH}
ExecReload=/bin/kill -HUP \$MAINPID
ExecStop=/bin/kill \$MAINPID
Restart=always

[Install]
WantedBy=default.target

_EOF_
    # After=syslog.target network.target
    # Requires=syslog.target network.target
    # EnvironmentFile=-${ENV_PATH}

    #*****
    # info "cp -p ${SERVICE_PATH} /usr/lib/systemd/system/"
    # cat "${SERVICE_PATH}"
    # sudo cp -p ${SERVICE_PATH} /usr/lib/systemd/system/
    # info "sudo systemctl daemon-reload"
    # sudo systemctl daemon-reload
    # info "systemctl enable ${default_env_values['AGENT_NAME']}"
    # sudo systemctl enable "${default_env_values['AGENT_NAME']}"

    # read -r -p  "${interactive_llist['SERVICE_MSG_START']}" confirm
    # echo ""
    # if ! (echo $confirm | grep -q -e "[yY]" -e "[yY][eE][sS]"); then
    #     info "systemctl daemon-reload & enable ${default_env_values['AGENT_NAME']}"
    #     info "Run manually!!! : systemctl start ${default_env_values['AGENT_NAME']}"
    # else
    #     info "systemctl start ${default_env_values['AGENT_NAME']}"
    #     sudo systemctl start "${default_env_values['AGENT_NAME']}"
    # fi
}

install_agent_service_rhel9(){
    echo "install_agent_service_rhel9 :${DEP_PATTERN}"
}

install_agent_service_almaLinux8(){
    echo "install_agent_service_almaLinux8 :${DEP_PATTERN}"
}

install_type(){
    while true; do
        echo "${interactive_llist['INSTALL_TYPE_MSG0']}"
        echo "${interactive_llist['INSTALL_TYPE_MSG1']}"
        echo "${interactive_llist['INSTALL_TYPE_MSG2']}"
        echo "${interactive_llist['INSTALL_TYPE_MSG3']}"
        # echo "${interactive_llist['INSTALL_TYPE_MSG4']}"
        echo "${interactive_llist['INSTALL_TYPE_MSGq']}"
        read -r -p  "${interactive_llist['INSTALL_TYPE_MSGr']}" confirm

        if echo $confirm | grep -q -e "[123]"; then
            INSTALL_TYPE=$confirm
            break
        elif echo $confirm | grep -q -e "[q]"; then
            exit 0
        else
            echo "${interactive_llist['INVALID_VALUE_IT']}"
            continue
        fi
    done
}

install(){
    case "${INSTALL_TYPE}" in
        1 )
            install_all
            ;;
        2 )
            install_env_service
            ;;
        3 )
            install_service
            ;;
        4 )
            install_source
            ;;
        * )
            info "no install type ${INSTALL_TYPE}"
            ;;
    esac
}
install_all(){

    # 設定の入力
    inquiry_env

    # dnfインストール:
    dnf_install

    # 作業領域のセットアップ
    init_workdir

    # .envファイルの作成
    create_env

    # Git Clone
    git_clone

    # agentインストール
    install_agent_source

    # pipインストール: poetry
    poetry_install

    # ansibleインストール: redhat
    ansible_additional_install

    # service
    install_agent_service

    # 作業領域の削除
    clean_workdir
}

install_env_service(){
    additional_env_keys=(
        "AGENT_SERVICE_NAME"
        "DATAPATH"
        "EXASTRO_URL"
        "EXASTRO_ORGANIZATION_ID"
        "EXASTRO_WORKSPACE_ID"
        "EXASTRO_REFRESH_TOKEN"
    )
    # 設定の入力
    inquiry_env

    # 作業領域のセットアップ
    init_workdir

    # .envファイルの作成
    create_env

    # service
    install_agent_service

    # 作業領域の削除
    clean_workdir
}
install_service(){
    additional_env_keys=(
        "AGENT_SERVICE_NAME"
        "DATAPATH"
        "REFERENCE_ENVPATH"
    )
    # 設定の入力
    inquiry_env

    # 作業領域のセットアップ
    init_workdir

    # service
    install_agent_service

    # 作業領域の削除
    clean_workdir
}

install_source(){
    additional_env_keys=(
        "AGENT_VERSION"
        "INSTALLPATH"
        "ANSIBLE_SUPPORT"
    )

    # 設定の入力
    inquiry_env

    # 作業領域のセットアップ
    init_workdir

    # Git Clone
    git_clone

    # agentインストール
    install_agent_source

    # pipインストール: poetry
    poetry_install

    # ansibleインストール: redhat
    ansible_additional_install

    # 作業領域の削除
    clean_workdir
}
#########################################
# Main functions
#########################################
main() {
    # 引数チェック
    check_args "$#"

    SUB_COMMAND=$1
    EXECUTE_PATH=${HOME}
    WORK_DIR="${EXECUTE_PATH}/_ag_install_work"
    ENV_TMP_PATH="${WORK_DIR}/.env"
    if [ "$#" -ge 2 ]; then
        SETUP_VERSION=$2
    fi

    get_system_info
    # モード判定
    case "$SUB_COMMAND" in
        install)
            shift
            check_requirement
            install_type
            install "$@"
            break
            ;;
        # uninstall)
        #     shift
        #     uninstall "$@"
        #     break
        #     ;;
        *)
            exit 2
            ;;
    esac
}

main "$@"