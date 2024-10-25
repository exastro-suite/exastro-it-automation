#!/bin/sh

set -ue

#########################################
# Environment variable
#########################################

### Set enviroment parameters
REQUIRED_MEM_TOTAL=4000000
REQUIRED_FREE_FOR_CONTAINER_IMAGE=25600
REQUIRED_FREE_FOR_EXASTRO_DATA=1024
DOCKER_COMPOSE_VER="v2.20.3"
LOG_FILE="${HOME}/exastro-installation.log"
EXASTRO_UNAME=$(id -u -n)
EXASTRO_UID=$(id -u)
EXASTRO_GID=1000
AGENT_INSTALLER_VERSION=2.5.1
AGENT_INSTALLER_VNC=20501

POETRY_VERSION=1.6.0

SETUP_VERSION=""
EXECUTE_PATH=""
WORK_DIR=""
ENV_TMP_PATH=""
SERVICE_ID=`date +%Y%m%d%H%M%S%3N`
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
    "zip"
    "unzip"
    "git"
)

# dnf install list: specific
dnf_install_list_rhel8=(
    "python3-requests"
)
dnf_install_list_rhel9=(
    "python3-requests"
)
dnf_install_list_almaLinux8=(
    "docker"
)

# install source_path src->dst
declare -A src_source_paths
declare -A dct_source_paths

src_source_paths["0"]="ita_root/ita_ag_ansible_execution/*"
src_source_paths["1"]="ita_root/messages"
src_source_paths["2"]="ita_root/agent/"
src_source_paths["3"]="ita_root/common_libs/common"
src_source_paths["4"]="ita_root/common_libs/ag"
src_source_paths["5"]="ita_root/common_libs/ansible_driver"
src_source_paths["6"]="ita_root/common_libs/ansible_execution"

dct_source_paths["0"]="/ita_ag_ansible_execution"
dct_source_paths["1"]="/ita_ag_ansible_execution/"
dct_source_paths["2"]="/ita_ag_ansible_execution/"
dct_source_paths["3"]="/ita_ag_ansible_execution/common_libs/"
dct_source_paths["4"]="/ita_ag_ansible_execution/common_libs/"
dct_source_paths["5"]="/ita_ag_ansible_execution/common_libs/"
dct_source_paths["6"]="/ita_ag_ansible_execution/common_libs/"

dct_create_paths["0"]="/ita_ag_ansible_execution"
dct_create_paths["1"]="/ita_ag_ansible_execution/common_libs"

declare -A dct_source_paths
xadd_source_paths["0"]="agent/agent_init.py"
xadd_source_paths["1"]="agent/agent_child_init.py"

#########################################
# .env default variable:
#########################################
declare -A default_env_values

BASE_DIR=/exastro
STORAG_DIR=/storage
LOG_PATH=/log
ENV_PATH=""
STORAGE_PATH=""
default_env_values=(
    ["IS_NON_CONTAINER_LOG"]="1"
    ["#LOGGING_MAX_SIZE"]="10485760"
    ["#LOGGING_MAX_FILE"]="30"
    # ita_root/ita_ag_ansible_execution/Dockerfile
    # ["USERNAME"]=app_user
    # ["GROUPNAME"]=app_user
    ["APP_PATH"]=${BASE_DIR}
    ["PYTHONPATH"]=${BASE_DIR}/
    ["LANGUAGE"]=en
    ["STORAGEPATH"]=${STORAG_DIR}
    ["LOGPATH"]=${LOG_PATH}
    ["SERVICE_NAME"]=ita-ag-ansible-execution
    ["USER_ID"]=ita-ag-ansible-execution
    # ita_root/ita_ag_ansible_execution/.env
    # common
    ["TZ"]=Asia/Tokyo
    ["DEFAULT_LANGUAGE"]=en
    # ag-agent
    ["AGENT_NAME"]=ita-agent-ansible-execution
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
    ["PYTHON_CMD"]=""
)
# use .env key
output_env_values=(
    # "USERNAME"
    # "GROUPNAME"
    "IS_NON_CONTAINER_LOG"
    "LOG_LEVEL"
    "#LOGGING_MAX_SIZE"
    "#LOGGING_MAX_FILE"
    "LANGUAGE"
    "TZ"
    "PYTHON_CMD"

    "PYTHONPATH"
    "APP_PATH"
    "STORAGEPATH"
    "LOGPATH"

    "EXASTRO_ORGANIZATION_ID"
    "EXASTRO_WORKSPACE_ID"
    "EXASTRO_URL"
    "EXASTRO_REFRESH_TOKEN"
    "EXECUTION_ENVIRONMENT_NAMES"

    "AGENT_NAME"
    "USER_ID"
    "ITERATION"
    "EXECUTE_INTERVAL"
    # "SERVICE_NAME"
)

#########################################
# interactive
#########################################
# interactive default value
default_env_values["AGENT_VERSION"]="main"
default_env_values["ANSIBLE_SUPPORT"]="1"
default_env_values["INSTALLPATH"]=${HOME}${BASE_DIR}
default_env_values["DATAPATH"]=${HOME}${BASE_DIR}
default_env_values["AGENT_SERVICE_ID"]=""
default_env_values["AGENT_SERVICE_ID_YN"]="y"

#  interactive key
additional_env_keys=(
    "AGENT_VERSION"
    "AGENT_SERVICE_ID_YN"
    "AGENT_SERVICE_ID"
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
    # install
    ["INSTALL_TYPE_MSG0"]="実施する処理を選択してください。"
    ["INSTALL_TYPE_MSG1"]="    1: ENVの作成 + インストール(dnf, pip, ソース配置) + サービスの登録"
    ["INSTALL_TYPE_MSG2"]="    2: ENVの作成 + サービスの登録"
    ["INSTALL_TYPE_MSG3"]="    3: サービスの登録"
    ["INSTALL_TYPE_MSG4"]="    4: Envの作成"
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
    # uninstall
    ["UNINSTALL_TYPE_MSG0"]="実施する処理を選択してください。"
    ["UNINSTALL_TYPE_MSG1"]="    1: サービスの削除＋データの削除"
    ["UNINSTALL_TYPE_MSG2"]="    2: サービスの削除"
    ["UNINSTALL_TYPE_MSG3"]="    3: データの削除"
    ["UNINSTALL_TYPE_MSGq"]="    q: アンインストール終了"
    ["UNINSTALL_TYPE_MSGr"]="select value: (1, 2, 3, q)  :"
    ["SERVICE_ID"]="SERVICE_IDを入力してください。"
    ["STORAGE_PATH"]="STORAGE_PATHを入力してください。"

    # 環境情報
    ["AGENT_SERVICE_ID_YN"]="エージェントのサービス名は、ita-agent-ansible-execution-${SERVICE_ID}です。個別に指定する場合は、「n」を選択して指定ください。(y/n) "
    ["AGENT_SERVICE_ID"]="エージェントのサービス名を入力してください。ita-agent-ansible-execution-が接頭に付与されます。"
    ["AGENT_VERSION"]="エージェントバージョンを入力してください。タグ指定: X.Y.Z, ブランチ指定: X.Y [default: 未入力+Enter(最新のリリースバージョン)]"
    ["INSTALLPATH"]="インストール先をフルパスで指定してください。"
    ["DATAPATH"]="データ保存先をフルパスで指定してください。"
    ["ANSIBLE_SUPPORT"]="利用するAnsible-builder, Ansible-runnerを選択してください。(1, 2) [1=Ansible 2=Red Hat Ansible Automation Platform] "
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
    # アンインストール
    ["SERVICE_NAME"]="SERVICE_NAMEを入力してください。(e.g. ita-agent-ansible-execution-xxxxxxxxxxxxx)"
    ["STORAGE_PATH"]="STORAGE_PATHを入力してください。(e.g. /${HOME}${BASE_DIR}/<SERVICE_ID>"
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

### Installation container engine
installation_container_engine() {
    info "Installing container engine..."
    if [ "${DEP_PATTERN}" = "RHEL8" ] || [ "${DEP_PATTERN}" = "RHEL9" ]; then
        installation_podman_on_rhel8
    elif [ "${DEP_PATTERN}" = "AlmaLinux8" ]; then
        installation_docker_on_alamalinux8
    # elif [ "${DEP_PATTERN}" = "Ubuntu20" ]; then
    #     installation_docker_on_ubuntu
    # elif [ "${DEP_PATTERN}" = "Ubuntu22" ]; then
    #     installation_docker_on_ubuntu
    fi
}


### Installation Podman on RHEL8
installation_podman_on_rhel8() {
    # info "Enable the extras repository"
    # sudo subscription-manager repos --enable=rhel-8-for-x86_64-appstream-rpms --enable=rhel-8-for-x86_64-baseos-rpms

    if [ "${DEP_PATTERN}" = "RHEL8" ]; then
        info "Enable container-tools module"
        sudo dnf module enable -y container-tools:rhel8

        info "Install container-tools module"
        sudo dnf module install -y container-tools:rhel8
    fi

    # info "Update packages"
    # sudo dnf update -y

    info "Install fuse-overlayfs"
    sudo dnf install -y fuse-overlayfs

    info "Install Podman"
    sudo dnf install -y podman podman-docker git

    info "Check if Podman is installed"
    if ! command -v podman >/dev/null 2>&1; then
        error "Podman installation failed!"
    fi

    info "Install docker-compose command"
    if [ ! -f "/usr/local/bin/docker-compose" ]; then
        if [ -z "${PROXY}" ]; then
            sudo curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VER}/docker-compose-${OS_TYPE}-${ARCH}" -o /usr/local/bin/docker-compose
        else
            sudo curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VER}/docker-compose-${OS_TYPE}-${ARCH}" -o /usr/local/bin/docker-compose -x ${https_proxy}
        fi
        sudo chmod a+x /usr/local/bin/docker-compose
    fi

    info "Show Podman version"
    podman --version

    CONTAINERS_CONF=${HOME}/.config/containers/containers.conf
    info "Change container netowrk driver"
    mkdir -p ${HOME}/.config/containers/
    cp /usr/share/containers/containers.conf ${HOME}/.config/containers/
    sed -i.$(date +%Y%m%d-%H%M%S) -e 's|^network_backend = "cni"|network_backend = "netavark"|' ${CONTAINERS_CONF}

    if [ ! -z "${PROXY}" ]; then
        if ! (grep -q "^ *http_proxy *=" ${CONTAINERS_CONF}); then
            sed -i -e '/^#http_proxy = \[\]/a http_proxy = true' ${CONTAINERS_CONF}
        fi
        if ! (grep -q "^ *http_proxy *=" ${CONTAINERS_CONF}); then
            sed -i -e '/^#http_proxy *=.*/a http_proxy = true' ${CONTAINERS_CONF}
        fi
        if grep -q "^ *env *=" ${CONTAINERS_CONF}; then
            if grep "^ *env *=" ${CONTAINERS_CONF} | grep -q -v "http_proxy"; then
                sed -i -e 's/\(^ *env *=.*\)\]/\1,"http_proxy='${http_proxy//\//\\/}'"]/' ${CONTAINERS_CONF}
            fi
            if grep "^ *env *=" ${CONTAINERS_CONF} | grep -q -v "https_proxy"; then
                sed -i -e 's/\(^ *env *=.*\)\]/\1,"https_proxy='${https_proxy//\//\\/}'"]/' ${CONTAINERS_CONF}
            fi
        else
            sed -i -e '/^#env = \[\]/a env = ["http_proxy='${http_proxy}'","https_proxy='${https_proxy}'"]' ${CONTAINERS_CONF}
        fi
    fi

    export XDG_RUNTIME_DIR="/run/user/${EXASTRO_UID}"
    if grep -q "^export XDG_RUNTIME_DIR" ${HOME}/.bashrc; then
        sed -i -e "s|^export XDG_RUNTIME_DIR.*|export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR}|" ${HOME}/.bashrc
    else
        echo "export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR}" >> ${HOME}/.bashrc
    fi
    sudo systemctl start user@${EXASTRO_UID}

    info "Start and enable Podman socket service"
    systemctl --user enable --now podman.socket
    systemctl --user status podman.socket --no-pager
    podman unshare chown ${EXASTRO_UID}:${EXASTRO_GID} /run/user/${EXASTRO_UID}/podman/podman.sock

    DOCKER_HOST="unix:///run/user/${EXASTRO_UID}/podman/podman.sock"
    if grep -q "^export DOCKER_HOST" ${HOME}/.bashrc; then
        sed -i -e "s|^export DOCKER_HOST.*|export DOCKER_HOST=${DOCKER_HOST}|" ${HOME}/.bashrc
    else
        echo "export DOCKER_HOST=${DOCKER_HOST}" >> ${HOME}/.bashrc
        echo "alias docker-compose='podman unshare docker-compose'" >> ${HOME}/.bashrc
    fi
}

### Installation Docker on AlmaLinux
installation_docker_on_alamalinux8() {
    # info "Update packages"
    # sudo dnf update -y

    info "Add Docker repository"
    sudo dnf config-manager --add-repo=https://download.docker.com/linux/centos/docker-ce.repo

    info "Install Docker and additional tools"
    sudo dnf install -y docker-ce docker-ce-cli containerd.io git

    info "Start and enable Docker service"
    sudo systemctl enable --now docker

    info "Add current user to the docker group (optional)"
    sudo usermod -aG docker ${USER}
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
  uninstall   Uninstall Ansible Execution Agent
        1: Uninstall Service & Delete Data
        2: Uninstall Service
        3: Delete Data
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
            update_pip_rhel8
            ;;
        RHEL9 )
            dnf_install_rhel8
            update_pip_rhel8
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
            info "sudo dnf install -y ${install_pkg}"
            sudo sudo dnf install -y "${install_pkg}"
            info "${install_pkg} install end"
        else
            info "${install_pkg} installed. skip"
        fi
    done
}

update_pip_rhel8(){
    pip3 install -U requests
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
            if [ "${env_key}" = "AGENT_SERVICE_ID" ] && [ "${default_env_values['AGENT_SERVICE_ID_YN']}" = "y" ];then
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
                elif [ ${env_key} = "AGENT_SERVICE_ID" ]; then
                    if echo $tmp_value | grep -q -e "^[0-9a-zA-Z\-_]*$"; then
                        default_env_values[$env_key]=$tmp_value
                        break
                    else
                        echo "${interactive_llist['INVALID_VALUE_E1']}"
                        continue
                    fi
                elif [ ${env_key} = "AGENT_SERVICE_ID_YN" ]; then
                    if echo $tmp_value | grep -q -e "[yYnN]"; then
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
                elif [ ${env_key} = "AGENT_VERSION" ]; then
                    INPUT_VERSION=$(echo ${tmp_value} | awk -F. '{printf "%2d%02d%02d", $1,$2,$3}')
                    if [ "$INPUT_VERSION" -gt $((AGENT_INSTALLER_VNC)) ]; then
                        info "${interactive_llist['INVALID_SETUP_VERSION']} main or <= ${AGENT_INSTALLER_VERSION}"
                        continue
                    fi
                fi
                default_env_values[$env_key]=$tmp_value
                break
            fi
        done
    done

    if [ "${default_env_values['AGENT_SERVICE_ID']}" = "" ];then
        default_env_values['AGENT_SERVICE_ID']="${SERVICE_ID}"
    fi

    # PATH関連
    default_env_values["APP_PATH"]=${default_env_values["INSTALLPATH"]}
    default_env_values["PYTHONPATH"]=${default_env_values["INSTALLPATH"]}/ita_ag_ansible_execution
    default_env_values["AGENT_NAME"]="ita-ag-ansible-execution-${default_env_values['AGENT_SERVICE_ID']}"
    default_env_values["USER_ID"]="${default_env_values['AGENT_SERVICE_ID']}"
    default_env_values["SERVICE_NAME"]="ita-ag-ansible-execution"

    # entrypoint.sh
    default_env_values["ENTRYPOINT"]="${default_env_values['INSTALLPATH']}/ita_ag_ansible_execution/agent/entrypoint.sh"

    # DATAPATH
    if [ "${default_env_values["DATAPATH"]}" = "${HOME}${BASE_DIR}" ]; then
        default_env_values["STORAGEPATH"]="${HOME}${BASE_DIR}/${default_env_values['AGENT_SERVICE_ID']}${STORAG_DIR}"
        default_env_values["LOGPATH"]="${HOME}${BASE_DIR}/${default_env_values['AGENT_SERVICE_ID']}${LOG_PATH}"
    else
        default_env_values["STORAGEPATH"]="${default_env_values["DATAPATH"]}/${default_env_values['AGENT_SERVICE_ID']}${STORAG_DIR}"
        default_env_values["LOGPATH"]="${default_env_values["DATAPATH"]}/${default_env_values['AGENT_SERVICE_ID']}${LOG_PATH}"
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
    for env_key in "${output_env_values[@]}"; do
        echo -e "${env_key}=${default_env_values[${env_key}]}" >> ${ENV_TMP_PATH}
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
    sudo pip3 install poetry==$POETRY_VERSION
    # poetry config --local virtualenvs.in-project true ###
    poetry config virtualenvs.in-project true ###
    poetry config virtualenvs.create true
    poetry install --only first_install
    poetry install --without develop_build

    which_poetry=`which poetry`
    poetry_path=`ls ${which_poetry}`
    default_env_values["PYTHON_CMD"]="${poetry_path} run python3"
    echo ${default_env_values["PYTHON_CMD"]}
}

ansible_additional_install(){
    if [ ${default_env_values["ANSIBLE_SUPPORT"]} != "1" ]; then
        echo "install redhat ansible"
        sudo pip3 uninstall -y ansible-builder ansible-runner
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
                sudo rm -rfd $source_path
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

    if [ "${DEP_PATTERN}" = "RHEL8" ] || [ "${DEP_PATTERN}" = "RHEL9" ]; then
        podman unshare chown ${EXASTRO_UID}:${EXASTRO_GID} "${source_path}"
        sudo chcon -R -h -t container_file_t "${base_path}"
    elif [ "${DEP_PATTERN}" = "AlmaLinux8" ]; then
        HOST_DOCKER_GID=$(grep docker /etc/group|awk -F':' '{print $3}')
        sudo chown -R ${EXASTRO_UID}:${HOST_DOCKER_GID} "${source_path}"
    fi

    for xadd_key in "${!xadd_source_paths[@]}"; do
        info "sudo chmod 755 ${source_path}/${xadd_source_paths[${xadd_key}]}"
        sudo chmod 755 ${source_path}/${xadd_source_paths[${xadd_key}]}
    done

    if [ "${DEP_PATTERN}" = "AlmaLinux8" ]; then
        echo "${source_path}/agent/entrypoint.sh"
        sudo chcon -R -h -t bin_t "${source_path}/agent/entrypoint.sh"
    fi

    info "install_agent_source end"
}


install_agent_service(){
    info "install_agent_service :${DEP_PATTERN} start"

    # create ~/storage
    STORAGE_PATH="${default_env_values['STORAGEPATH']}"
    info "mkdir -m 777 -p ${STORAGE_PATH}"
    mkdir -m 777 -p "${STORAGE_PATH}"

    if [ "${DEP_PATTERN}" = "RHEL8" ] || [ "${DEP_PATTERN}" = "RHEL9" ]; then
        podman unshare chown ${EXASTRO_UID}:${EXASTRO_GID} "${STORAGE_PATH}/"
        sudo chcon -R -h -t container_file_t "${default_env_values["DATAPATH"]}"
    elif [ "${DEP_PATTERN}" = "AlmaLinux8" ]; then
        sudo chown -R ${EXASTRO_UID}:${HOST_DOCKER_GID} "${STORAGE_PATH}/"
    fi

    # cp .env
    ENV_PATH="${default_env_values["DATAPATH"]}/${default_env_values['AGENT_SERVICE_ID']}/.env"
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
            install_agent_service_almaLinux8
            ;;
        # Ubuntu20 )
        #     ;;
        # Ubuntu22 )
        #     ;;
        * )
            ;;
    esac
            cat <<_EOF_

Install Ansible Execution Agent Infomation:
    Agent Service id:   ${AGENT_SERVICE_ID}
    Agent Service Name: ${default_env_values['AGENT_NAME']}
    Storage Path:       ${STORAGE_PATH}
    Env Path:           ${ENV_PATH}

_EOF_

    info "install_agent_service :${DEP_PATTERN} end"
}

install_agent_service_rhel8(){

    if [ "${DEP_PATTERN}" = "RHEL8" ] || [ "${DEP_PATTERN}" = "RHEL9" ]; then
        HOST_DOCKER_GID=${EXASTRO_GID}
        HOST_DOCKER_SOCKET_PATH="/run/user/${EXASTRO_UID}/podman/podman.sock"
    else
        HOST_DOCKER_GID=$(grep docker /etc/group|awk -F':' '{print $3}')
        HOST_DOCKER_SOCKET_PATH="/var/run/docker.sock"
    fi

    ENTRYPOINT=${default_env_values["ENTRYPOINT"]}
    PYTHONPATH=${default_env_values["PYTHONPATH"]}
    PYTHON_CMD=${default_env_values["PYTHON_CMD"]}
    AGENT_SERVICE_ID=${default_env_values['AGENT_SERVICE_ID']}
    SERVICE_PATH="${default_env_values["DATAPATH"]}/${default_env_values['AGENT_SERVICE_ID']}/${default_env_values['AGENT_NAME']}.service"
    info "create ${SERVICE_PATH}"
    cat << _EOF_ >${SERVICE_PATH}
[Unit]
Description=Ansible Execution agent for Exastro IT Automation (${SERVICE_ID})

[Service]
WorkingDirectory=${PYTHONPATH}
ExecStart=${ENTRYPOINT} ${ENV_PATH} ${PYTHONPATH} ${STORAGE_PATH} "${PYTHON_CMD}"
ExecReload=/bin/kill -HUP \$MAINPID
ExecStop=/bin/kill \$MAINPID
Restart=always

[Install]
WantedBy=default.target

_EOF_

    #*****
    #
    info "cp -p ${SERVICE_PATH}  ${HOME}/.config/systemd/user/"
    cat "${SERVICE_PATH}"
    sudo cp -p ${SERVICE_PATH}  ${HOME}/.config/systemd/user/
    info "systemctl --user daemon-reload"
    systemctl --user daemon-reload
    info "systemctl --user enable ${default_env_values['AGENT_NAME']}"
    systemctl --user enable "${default_env_values['AGENT_NAME']}"

    read -r -p  "${interactive_llist['SERVICE_MSG_START']}" confirm
    echo ""
    if ! (echo $confirm | grep -q -e "[yY]" -e "[yY][eE][sS]"); then
        info "systemctl daemon-reload & enable ${default_env_values['AGENT_NAME']}"
        info "Run manually!!! : systemctl start ${default_env_values['AGENT_NAME']}"
    else
        info "systemctl --user start ${default_env_values['AGENT_NAME']}"
        systemctl --user start "${default_env_values['AGENT_NAME']}"
    fi
}

install_agent_service_rhel9(){
    echo "install_agent_service_rhel9 :${DEP_PATTERN}"
}

install_agent_service_almaLinux8(){
    ENTRYPOINT=${default_env_values["ENTRYPOINT"]}
    PYTHONPATH=${default_env_values["PYTHONPATH"]}
    PYTHON_CMD=${default_env_values["PYTHON_CMD"]}
    AGENT_SERVICE_ID=${default_env_values['AGENT_SERVICE_ID']}
    SERVICE_PATH="${default_env_values["DATAPATH"]}/${default_env_values['AGENT_SERVICE_ID']}/${default_env_values['AGENT_NAME']}.service"
    info "create ${SERVICE_PATH}"
    cat << _EOF_ >${SERVICE_PATH}
[Unit]
Description=Ansible Execution agent for Exastro IT Automation (${SERVICE_ID})

[Service]
WorkingDirectory=${PYTHONPATH}
ExecStart=${ENTRYPOINT} ${ENV_PATH} ${PYTHONPATH} ${STORAGE_PATH} "${PYTHON_CMD}"
ExecReload=/bin/kill -HUP \$MAINPID
ExecStop=/bin/kill \$MAINPID
Restart=always

[Install]
WantedBy=default.target

_EOF_
    #*****
    info "cp -p ${SERVICE_PATH} /usr/lib/systemd/system/"
    cat "${SERVICE_PATH}"
    sudo cp -p ${SERVICE_PATH} /usr/lib/systemd/system/
    info "sudo systemctl daemon-reload"
    sudo systemctl daemon-reload
    info "systemctl enable ${default_env_values['AGENT_NAME']}"
    sudo systemctl enable "${default_env_values['AGENT_NAME']}"

    read -r -p  "${interactive_llist['SERVICE_MSG_START']}" confirm
    echo ""
    if ! (echo $confirm | grep -q -e "[yY]" -e "[yY][eE][sS]"); then
        info "systemctl daemon-reload & enable ${default_env_values['AGENT_NAME']}"
        info "Run manually!!! : systemctl start ${default_env_values['AGENT_NAME']}"
    else
        info "systemctl start ${default_env_values['AGENT_NAME']}"
        sudo systemctl start "${default_env_values['AGENT_NAME']}"
    fi

}

set_vars_for_env(){
    info "set_vars_for_env :${DEP_PATTERN} start"
    default_env_values['STORAGEPATH']=`cat "${default_env_values['REFERENCE_ENVPATH']}" | grep "STORAGEPATH=" | awk -F"STORAGEPATH=" '{print $2}'`
    default_env_values['AGENT_SERVICE_ID']=`basename ${default_env_values['REFERENCE_ENVPATH']} | awk -F"." '{print $1}'`
    default_env_values["AGENT_NAME"]="ita-ag-ansible-execution-${default_env_values['AGENT_SERVICE_ID']}"
    SERVICE_ID=${default_env_values['AGENT_SERVICE_ID']}
    DP_PATH=${default_env_values['STORAGEPATH']%$STORAG_DIR}
    default_env_values["DATAPATH"]=${DP_PATH%/$SERVICE_ID}

    which_poetry=`which poetry`
    poetry_path="`ls ${which_poetry}`"" run python3"
    default_env_values["PYTHON_CMD"]=$poetry_path
    sed -i "/PYTHON_CMD=/c PYTHON_CMD=${poetry_path}" ${default_env_values['REFERENCE_ENVPATH']}

    info "set_vars_for_env :${DEP_PATTERN} end"
}

install_type(){
    while true; do
        echo "${interactive_llist['INSTALL_TYPE_MSG0']}"
        echo "${interactive_llist['INSTALL_TYPE_MSG1']}"
        echo "${interactive_llist['INSTALL_TYPE_MSG2']}"
        echo "${interactive_llist['INSTALL_TYPE_MSG3']}"
        echo "${interactive_llist['INSTALL_TYPE_MSG4']}"
        echo "${interactive_llist['INSTALL_TYPE_MSGq']}"
        read -r -p  "${interactive_llist['INSTALL_TYPE_MSGr']}" confirm

        if echo $confirm | grep -q -e "[1234]"; then
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
            create_envfile
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

    # Installation container engine
    installation_container_engine

    # 作業領域のセットアップ
    init_workdir


    # Git Clone
    git_clone

    # agentインストール
    install_agent_source

    # pipインストール: poetry
    poetry_install

    # .envファイルの作成
    create_env

    # ansibleインストール: redhat
    ansible_additional_install

    # service
    install_agent_service

    # 作業領域の削除
    clean_workdir
}

install_env_service(){
    additional_env_keys=(
        "AGENT_SERVICE_ID_YN"
        "AGENT_SERVICE_ID"
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
        "AGENT_SERVICE_ID"
        "REFERENCE_ENVPATH"
    )
    # 設定の入力
    inquiry_env

    # 作業領域のセットアップ
    init_workdir

    # envから、設定値取得
    set_vars_for_env

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

create_envfile(){
    additional_env_keys=(
        "AGENT_SERVICE_ID_YN"
        "AGENT_SERVICE_ID"
        "DATAPATH"
        "EXASTRO_URL"
        "EXASTRO_ORGANIZATION_ID"
        "EXASTRO_WORKSPACE_ID"
        "EXASTRO_REFRESH_TOKEN"
    )
    # 設定の入力
    inquiry_env

    ENV_TMP_PATH="./${default_env_values['AGENT_SERVICE_ID']}.env"

    # .envファイルの作成
    create_env

}

uninstall_type(){
    while true; do
        echo "${interactive_llist['UNINSTALL_TYPE_MSG0']}"
        echo "${interactive_llist['UNINSTALL_TYPE_MSG1']}"
        echo "${interactive_llist['UNINSTALL_TYPE_MSG2']}"
        echo "${interactive_llist['UNINSTALL_TYPE_MSG3']}"
        echo "${interactive_llist['UNINSTALL_TYPE_MSGq']}"
        read -r -p  "${interactive_llist['UNINSTALL_TYPE_MSGr']}" confirm

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

    UNINSTALL_TYPE=$confirm
    SERVICE_ID=""
    SERVICE_NAME=""
    STORAGE_PATH=""
    additional_uninstall_keys=(
    )
    case "${UNINSTALL_TYPE}" in
        1 )
            additional_uninstall_keys=(
                "SERVICE_NAME"
                "STORAGE_PATH"
            )
            ;;
        2 )
            additional_uninstall_keys=(
                "SERVICE_NAME"
            )
            ;;
        3 )
            additional_uninstall_keys=(
                "STORAGE_PATH"
            )
            ;;
    esac

    for env_key in "${additional_uninstall_keys[@]}"; do
        while true; do
            read -r -p "${interactive_llist[${env_key}]}: " tmp_value
            echo ""
            if [ "$tmp_value" = "" ]; then
                echo "Invalid value!!"
                continue
            else
                if [ ${env_key} = "STORAGE_PATH" ]; then
                    if [ ! -d $tmp_value ]; then
                        echo "not found storage path: ${tmp_value}"
                        continue
                    fi
                elif [ ${env_key} = "SERVICE_NAME" ]; then
                    if [ "${DEP_PATTERN}" = "RHEL8" ] || [ "${DEP_PATTERN}" = "RHEL9" ]; then
                        chk_service=`ls ${HOME}/.config/systemd/user/ | grep "ita-ag-ansible-execution-" | grep ${tmp_value} | wc -l`
                    else
                        chk_service=`ls /usr/lib/systemd/system/ | grep "ita-ag-ansible-execution-" | grep ${tmp_value} | wc -l`
                    fi
                    if [ ${chk_service} -eq 0 ]; then
                        echo "not found service id: ${tmp_value}"
                        continue
                    fi
                fi
                default_env_values[$env_key]=$tmp_value
                break
            fi
        done
    done
}

uninstall(){
    case "${UNINSTALL_TYPE}" in
        1 )
            uninstall_service
            uninstall_data
            ;;
        2 )
            uninstall_service
            ;;
        3 )
            S_NAME=${default_env_values['STORAGE_PATH']}
            SERVICE_NAME=${S_NAME##*/}
            default_env_values['SERVICE_NAME']="ita-ag-ansible-execution-${SERVICE_NAME}"
            uninstall_data
            ;;
        * )
            info "no install type ${INSTALL_TYPE}"
            ;;
    esac
}

uninstall_service(){
    SERVICE_NAME="${default_env_values['SERVICE_NAME']}"
    if [ "${DEP_PATTERN}" = "RHEL8" ] || [ "${DEP_PATTERN}" = "RHEL9" ]; then
        info "systemctl --user disable --now ${SERVICE_NAME}"
        systemctl --user disable --now ${SERVICE_NAME}
        info "rm ${HOME}/.config/systemd/user/${SERVICE_NAME}.service"
        rm ${HOME}/.config/systemd/user/${SERVICE_NAME}.service
        info "systemctl --user daemon-reload"
        systemctl --user daemon-reload
    else
        info "sudo systemctl stop ${SERVICE_NAME}"
        sudo systemctl stop ${SERVICE_NAME}
        info "sudo systemctl disable ${SERVICE_NAME}"
        sudo systemctl disable ${SERVICE_NAME}
        info "sudo rm /usr/lib/systemd/system/${SERVICE_NAME}.service"
        sudo rm /usr/lib/systemd/system/${SERVICE_NAME}.service
        info "sudo systemctl daemon-reload"
        sudo systemctl daemon-reload
    fi
}

uninstall_data(){
    SERVICE_NAME="${default_env_values['SERVICE_NAME']}"
    SERVICE_ID=${SERVICE_NAME/ita-ag-ansible-execution-/}
    # STORAGE_PATH="/home/almalinux/exastro/${SERVICE_ID}/storage/"
    STORAGE_PATH="${default_env_values['STORAGE_PATH']}"
    if [[ "$STORAGE_PATH" == *"$SERVICE_ID"* ]]; then
        echo ""
    else
        error "no exist SERVICE_ID storage path: ${STORAGE_PATH}"
        exit 2
    fi

    if [ "${DEP_PATTERN}" = "RHEL8" ] || [ "${DEP_PATTERN}" = "RHEL9" ]; then
        info "rm -rd ${STORAGE_PATH}"
        rm -rfd  ${STORAGE_PATH}
    else
        info "rm -rd ${STORAGE_PATH}"
        sudo rm -rfd  ${STORAGE_PATH}
    fi
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
        uninstall)
            shift
            uninstall_type
            uninstall "$@"
            break
            ;;
        *)
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
  uninstall   Uninstall Ansible Execution Agent
        1: Uninstall Service & Delete Data
        2: Uninstall Service
        3: Delete Data
_EOF_
            exit 2
            ;;
    esac
}

main "$@"