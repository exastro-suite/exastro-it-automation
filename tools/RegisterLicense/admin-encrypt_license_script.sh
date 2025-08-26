#!/bin/bash
# Copyright 2025 NEC Corporation#
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

# set -ue

#########################################
# variable
#########################################

### USER SETTING
EXASTRO_URL=""
EXASTRO_ORG_ID=""
EXASTRO_WS_ID=""
EXASTRO_USERNAME=""
EXASTRO_PASSWORD=""

### VARIABLES
ITA_PROTCOL=""
ITA_HOST=""
ITA_PORT=""
ITA_EXASTRO_ORG_ID=""
ITA_EXASTRO_WS_ID=""
ITA_REFRESH_TOKEN=""
AAH_CONTAINER_IMAGE_REGISTRY=""

### SYSTEM
# DEPLOY_FLG="a"
LOG_FILE="${HOME}/exastro-admin-encrypt_license_script.log"

HTTP_STATUS=""
RESPONSE_BODY=""
API_RTN=""
ENCRYPTED_TEXT=""

##############################################
# MAIN FUNCTION
##############################################
main() {
    info "Process of Exastro-Admin-EncryptLicenseScript has Started"

    info "check the required commands (jq openssl curl)"
    required_commands=("jq" "openssl" "curl")
    for cmd in "${required_commands[@]}"; do
        check_command "${cmd}"
        ret=$?
        if [ $ret -ne 0 ]; then
            exit 1
        fi
    done

    setup
    info "Encyrpt license process has Started"

    # ITA接続情報の確認
    get_ita_connection_info
    ret=$?
    if [ $ret -ne 0 ]; then
        exit 1
    fi

    data=$(echo "${API_RTN}" | jq -r '.[0].parameter')

    ITA_PROTCOL=$(echo "${data}" | jq -r '.protocol')
    ITA_HOST=$(echo "${data}" | jq -r '.host')
    ITA_PORT=$(echo "${data}" | jq -r '.port')
    ITA_EXASTRO_ORG_ID=$(echo "${data}" | jq -r '.organization_id')
    ITA_EXASTRO_WS_ID=$(echo "${data}" | jq -r '.workspace_id')
    ITA_REFRESH_TOKEN=$(echo "${data}" | jq -r '.refresh_token')
    AAH_CONTAINER_IMAGE_REGISTRY=$(echo "${data}" | jq -r '.aah_container_image_registry')

    # ライセンス情報管理メニューを取得
    get_license_management
    ret=$?
    if [ $ret -ne 0 ]; then
        exit 1
    fi
    license_records=$API_RTN

    if [ "${license_records}" = "[]" ]; then
        echo ""
        info "Nothing to do. Because All 'License Management' records are encrypted"
        exit 0
    fi

    tmp_file_basepath="/tmp/Exastro-Admin-EncryptLicenseScript"
    info "mkdir ${tmp_file_basepath}"
    if ! mkdir -p "${tmp_file_basepath}"; then
        error "Erro occurred in crating ${tmp_file_basepath}"
        exit 1
    fi

    # 顧客のレコード毎に処理
    echo "$license_records" | jq -c '.[] | .parameter' | while IFS= read -r license_record; do
        echo ""

        disuse_flg=$(echo "$license_record" | jq -r '.discard')
        enc_flg=$(echo "$license_record" | jq -r '.enc_flg')
        kanri_id=$(echo "$license_record" | jq -r '.uuid')
        customer_name=$(echo "$license_record" | jq -r '.customer_name')
        refresh_token=$(echo "$license_record" | jq -r '.refresh_token')
        if [ "${refresh_token}" = "null" ]; then
            refresh_token="${ITA_REFRESH_TOKEN}"
        fi
        passphrase=$(echo "$license_record" | jq -r '.passphrase')
        aap_register_flg=$(echo "$license_record" | jq -r '.aap_register_flg')
        aah_login_flg=$(echo "$license_record" | jq -r '.aah_login_flg')
        license_record_last_update_date_time=$(echo "$license_record" | jq -r '.last_update_date_time')

        info "[${customer_name}] In the processing of encrypting license"

        # 廃止じゃないレコード
        if [ "${disuse_flg}" -eq 0 ]; then
            # 暗号化済み
            if [ "${enc_flg}" -eq 1 ]; then
                info "already encrypted"
                info "...skipping"
                continue
            fi
            # 暗号化対象がない
            if [ "${aap_register_flg}" -ne 1 ] && [ "${aah_login_flg}" -ne 1 ]; then
                warn "Ntohing to do. Because Both flags(aap_register_flg and aah_login_flg) are set to 0 (kanri_id=${kanri_id})"
                info "...skipping"
                continue
            fi

            # ecnrypt license
            if [ "${aap_register_flg}" -eq 1 ]; then
                # 暗号化対象
                aap_activationkey="$(echo "$license_record" | jq -r '.aap_activationkey')"
                if [ "${aap_activationkey}" = "null" ]; then
                    warn "Value( aap_activationkey ) is empty (kanri_id=${kanri_id})"
                    info "...skipping"
                    continue
                fi
                openssl_ecnrypt "${aap_activationkey}" "${passphrase}"
                encrypted_aap_activationkey="${ENCRYPTED_TEXT}"
            else
                encrypted_aap_activationkey=""
            fi
            if [ "${aap_register_flg}" -eq 1 ]; then
                # 暗号化対象
                aap_orgid="$(echo "$license_record" | jq -r '.aap_orgid')"
                if [ "${aap_orgid}" = "null" ]; then
                    warn "Value( aap_orgid ) is empty (kanri_id=${kanri_id})"
                    info "...skipping"
                    continue
                fi
                openssl_ecnrypt "${aap_orgid}" "${passphrase}"
                encrypted_aap_orgid="${ENCRYPTED_TEXT}"
            else
                encrypted_aap_orgid=""
            fi

            if [ "${aah_login_flg}" -eq 1 ]; then
                # 暗号化対象
                aah_username="$(echo "$license_record" | jq -r '.aah_username')"
                if [ "${aah_username}" = "null" ]; then
                    warn "Value( aah_username ) is empty (kanri_id=${kanri_id})"
                    info "...skipping"
                    continue
                fi
                openssl_ecnrypt "${aah_username}" "${passphrase}"
                encrypted_aah_username="${ENCRYPTED_TEXT}"
            else
                encrypted_aah_username=""
            fi
            if [ "${aah_login_flg}" -eq 1 ]; then
                # 暗号化対象
                aah_password="$(echo "$license_record" | jq -r '.aah_password')"
                if [ "${aah_password}" = "null" ]; then
                    warn "Value( aah_password ) is empty (kanri_id=${kanri_id})"
                    info "...skipping"
                    continue
                fi
                openssl_ecnrypt "${aah_password}" "${passphrase}"
                encrypted_aah_password="${ENCRYPTED_TEXT}"
            else
                encrypted_aah_password=""
            fi
        fi

        # 暗号化済ライセンス情報取得用メニューに暗号化した情報を反映する
        # 今の暗号化済ライセンス情報取得用メニューを確認
        get_encrypted_license_access "$kanri_id"
        ret=$?
        if [ $ret -ne 0 ]; then
            info "...skipping"
            continue
        fi

        encrypted_license_records=$API_RTN
        if [ "${disuse_flg}" -eq 1 ]; then
        # ライセンス管理メニュー上で廃止になっている
            if [ "${encrypted_license_records}" != "[]" ]; then
                # 廃止にする
                echo "$encrypted_license_records" | jq -c '.[] | .parameter' | while IFS= read -r encrypted_license_record; do
                    uuid=$(echo "$encrypted_license_record" | jq -r '.uuid')
                    last_update_date_time=$(echo "$encrypted_license_record" | jq -r '.last_update_date_time')

                    parameter="[{\"file\":{},\"parameter\":{\"uuid\":\"${uuid}\",\"last_update_date_time\":\"${last_update_date_time}\"},\"type\":\"Discard\"}]"
                    update_encrypted_license_access "$kanri_id" "$parameter"
                    ret=$?
                    if [ $ret -ne 0 ]; then
                        info "...skipping"
                        continue
                    fi
                done
            fi
            info "...skipping"
            continue
        else
            # 新規登録（廃止になっている場合は再登録）
            if [ "${encrypted_license_records}" = "[]" ]; then
                parameter="[{\"file\":{},\"parameter\":{\"kanri_id\":\"${kanri_id}\",\"aap_activationkey\":\"${encrypted_aap_activationkey}\",\"aap_orgid\":\"${encrypted_aap_orgid}\",\"aah_username\":\"${encrypted_aah_username}\",\"aah_password\":\"${encrypted_aah_password}\"},\"type\":\"Register\"}]"
                update_encrypted_license_access "$kanri_id" "$parameter"
                ret=$?
                if [ $ret -ne 0 ]; then
                    info "...skipping"
                    continue
                fi
            else
            # 更新
                uuid=$(echo "$encrypted_license_records" | jq -r '.[0].parameter.uuid')
                last_update_date_time=$(echo "$encrypted_license_records" | jq -r '.[0].parameter.last_update_date_time')

                # 更新の場合、必要な値しかupdateしない
                if [ "${aap_register_flg}" -eq 1 ] && [ "${aah_login_flg}" -eq 1 ]; then
                    parameter="[{\"file\":{},\"parameter\":{\"uuid\":\"${uuid}\",\"kanri_id\":\"${kanri_id}\",\"aap_activationkey\":\"${encrypted_aap_activationkey}\",\"aap_orgid\":\"${encrypted_aap_orgid}\",\"aah_username\":\"${encrypted_aah_username}\",\"aah_password\":\"${encrypted_aah_password}\",\"last_update_date_time\":\"${last_update_date_time}\"},\"type\":\"Update\"}]"
                elif [ "${aap_register_flg}" -eq 1 ]; then
                    parameter="[{\"file\":{},\"parameter\":{\"uuid\":\"${uuid}\",\"kanri_id\":\"${kanri_id}\",\"aap_activationkey\":\"${encrypted_aap_activationkey}\",\"aap_orgid\":\"${encrypted_aap_orgid}\",\"aah_username\":\"${encrypted_aah_username}\",\"aah_password\":\"${encrypted_aah_password}\",\"last_update_date_time\":\"${last_update_date_time}\"},\"type\":\"Update\"}]"
                elif [ "${aah_login_flg}" -eq 1 ]; then
                    parameter="[{\"file\":{},\"parameter\":{\"uuid\":\"${uuid}\",\"kanri_id\":\"${kanri_id}\",\"aah_username\":\"${encrypted_aah_username}\",\"aah_password\":\"${encrypted_aah_password}\",\"last_update_date_time\":\"${last_update_date_time}\"},\"type\":\"Update\"}]"
                fi

                update_encrypted_license_access "$kanri_id" "$parameter"
                ret=$?
                if [ $ret -ne 0 ]; then
                    info "...skipping"
                    continue
                fi
            fi
        fi

        # 暗号化済ライセンス情報取得用メニューへの更新に成功したので
        # 暗号化済みフラグと設定ファイルを更新する
        tmp_file_name="${customer_name}.env"
        tmp_file_fullpath="${tmp_file_basepath}/${tmp_file_name}"
        info "...Creating configuration file (${tmp_file_fullpath})"

        cat << EOF > "${tmp_file_fullpath}"
KANRI_ID=${kanri_id}
ITA_PROTCOL=${ITA_PROTCOL}
ITA_HOST=${ITA_HOST}
ITA_PORT=${ITA_PORT}
ITA_EXASTRO_ORG_ID=${ITA_EXASTRO_ORG_ID}
ITA_EXASTRO_WS_ID=${ITA_EXASTRO_WS_ID}
ITA_REFRESH_TOKEN=${refresh_token}
AAH_CONTAINER_IMAGE_REGISTRY=${AAH_CONTAINER_IMAGE_REGISTRY}
PASSPHRASE=${passphrase}
AAP_REGISTER_FLG=${aap_register_flg}
AAH_LOGIN_FLG=${aah_login_flg}
REPO_LIST=rhel-9-for-x86_64-baseos-rpms,rhel-9-for-x86_64-appstream-rpms,ansible-automation-platform-2.5-for-rhel-9-x86_64-rpms
EOF

        ret=$?
        if [ $ret -ne 0 ]; then
            error "Erro occurred in creating ${tmp_file_fullpath}"
            info "...skipping"
            continue
        fi
        info "Configuration file is temporarily output (${tmp_file_fullpath})"

        # ライセンス管理メニューに、設定ファイルをアップロードし、暗号化済みフラグに1をたてる
        parameter="json_parameters=[{\"parameter\":{\"uuid\":\"${kanri_id}\",\"config\":\"${tmp_file_name}\",\"enc_flg\":\"1\",\"last_update_date_time\":\"${license_record_last_update_date_time}\"},\"type\":\"Update\"}]"
        file_upload="0.config=@${tmp_file_fullpath}"

        update_get_license_management "$kanri_id" "$parameter" "$file_upload"
        ret=$?
        if [ $ret -ne 0 ]; then
            info "...skipping"
            continue
        fi

    done

    echo ""
    info "rm ${tmp_file_basepath}"
    if ! rm -fr "${tmp_file_basepath}"; then
        error "Erro occurred in removing ${tmp_file_basepath}"
        exit 1
    fi

    echo ""
    info "Process of Exastro-Admin-EncryptLicenseScript has End"
}


setup() {
    info "Setup script..."
    echo "Please register settings."
    echo ""

    while true; do
        while true; do
            read -r -p "Input the Exastro service URL (ex. http://hoge.exastro.com:30080): " EXASTRO_URL
            if [ "${EXASTRO_URL}" = "" ]; then
                echo "Exastro service URL is required."
                echo ""
                continue
            else
                if ! echo "${EXASTRO_URL}" | grep -q "http://.*" && ! echo "${EXASTRO_URL}" | grep -q "https://.*" ; then
                    echo "Invalid URL format"
                    echo ""
                    continue
                fi
            fi
            echo ""
            break
        done

        while true; do
            read -r -p "organization id : " EXASTRO_ORG_ID
            if [ "${EXASTRO_ORG_ID}" == "" ]; then
                echo "please enter organization id ... retry"
                echo ""
                continue
            fi
            echo ""
            break
        done

        while true; do
            read -r -p "workspace id : " EXASTRO_WS_ID
            if [ "${EXASTRO_WS_ID}" == "" ]; then
                echo "please enter workspace id ... retry"
                echo ""
                continue
            fi
            echo ""
            break
        done

        while true; do
            read -r -p "your username : " EXASTRO_USERNAME
            if [ "${EXASTRO_USERNAME}" == "" ]; then
                echo "please enter your username ... retry"
                echo ""
                continue
            fi
            echo ""
            break
        done

        while true; do
            read -rsp "your password : " EXASTRO_PASSWORD
            if [ "${EXASTRO_PASSWORD}" == "" ]; then
                echo "please enter your password ... retry"
                echo ""
                continue
            fi
            echo ""
            break
        done

        echo ""
        echo ""
        cat <<_EOF_
The Exastro system parameters are as follows.

Service URL:                    ${EXASTRO_URL}
Organization ID:                ${EXASTRO_ORG_ID}
Workspace ID:                   ${EXASTRO_WS_ID}
USERNAME:                       ${EXASTRO_USERNAME}
PASSWORD:                       ********
_EOF_

        read -r -p "Start the encyrpt license process with these settings? (y/n) [default: n]: " confirm
        echo ""
        if echo "$confirm" | grep -q -e "[yY]" -e "[yY][eE][sS]"; then
            break
        fi
    done
}

### GET ITA CONNECTION INFOMATION
get_ita_connection_info() {
    info "...Try to get ITA Connection Infomation"

    URL="$EXASTRO_URL/api/$EXASTRO_ORG_ID/workspaces/$EXASTRO_WS_ID/ita/menu/ITA-ConnectionInfomation/filter/?file=no"
    JSON_BODY='{"discard":{"NORMAL":"0"}}'

    post_json_api "$URL" "$JSON_BODY"
    ret=$?
    if [ $ret -eq 0 ] && [ "${HTTP_STATUS}" -eq 200 ]; then
        API_RTN=$(echo "${RESPONSE_BODY}" | jq -r '.data')

        if [ "${API_RTN}" != "[]" ]; then
            info "Get 'ITA Connection Infomation' Successfully"
            return 0
        fi
    fi

    error "Failed to get 'ITA Connection Infomation' (status_code=${HTTP_STATUS} response=${RESPONSE_BODY})"
    return 1
}

### GET License Management
get_license_management() {
    info "...Try to get License Management"

    URL="$EXASTRO_URL/api/$EXASTRO_ORG_ID/workspaces/$EXASTRO_WS_ID/ita/menu/LicenseManagement/filter/?file=no"
    # JSON_BODY='{"enc_flg":{"LIST":[0,2]}}'
    JSON_BODY=''

    post_json_api "$URL" "$JSON_BODY"
    ret=$?
    if [ $ret -eq 0 ] && [ "${HTTP_STATUS}" -eq 200 ]; then
        API_RTN=$(echo "${RESPONSE_BODY}" | jq -r '.data')

        info "Get 'License Management' Successfully"
        return 0
    fi

    error "Failed to get 'License Management' (status_code=${HTTP_STATUS} response=${RESPONSE_BODY})"
    return 1
}

### GET Encrypted License Access
get_encrypted_license_access() {
    info "...Try to get Encrypted License Access"

    kanri_id=$1
    URL="$EXASTRO_URL/api/$EXASTRO_ORG_ID/workspaces/$EXASTRO_WS_ID/ita/menu/EncryptedLicenseAccess/filter/?file=no"
    JSON_BODY="{\"discard\":{\"NORMAL\":\"0\"},\"kanri_id\":{\"NORMAL\":\"${kanri_id}\"}}"

    post_json_api "$URL" "$JSON_BODY"
    ret=$?
    if [ $ret -eq 0 ] && [ "${HTTP_STATUS}" -eq 200 ]; then
        API_RTN=$(echo "${RESPONSE_BODY}" | jq -r '.data')

        info "Get 'Encrypted License Access(kanri_id=${kanri_id})' Successfully"
        return 0
    fi

    error "Failed to get 'Encrypted License Access(kanri_id=${kanri_id})' (status_code=${HTTP_STATUS} response=${RESPONSE_BODY})"
    return 1
}

## UPDATE Encrypted License Access
update_encrypted_license_access() {
    info "...Try to update Encrypted License Access"

    kanri_id=$1
    JSON_BODY=$2

    URL="$EXASTRO_URL/api/$EXASTRO_ORG_ID/workspaces/$EXASTRO_WS_ID/ita/menu/EncryptedLicenseAccess/maintenance/all/"
    cmd_type=$(echo "${JSON_BODY}" | jq -r '.[0].type')

    post_json_api "$URL" "$JSON_BODY"
    ret=$?
    if [ $ret -eq 0 ] && [ "${HTTP_STATUS}" -eq 200 ]; then
        API_RTN=$(echo "${RESPONSE_BODY}" | jq -r '.data')

        info "${cmd_type} 'Encrypted License Access(kanri_id=${kanri_id})' Successfully"
        return 0
    fi

    error "Failed to ${cmd_type} 'Encrypted License Access(kanri_id=${kanri_id})' (status_code=${HTTP_STATUS} response=${RESPONSE_BODY})"
    return 1
}

## UPDATE License Management
update_get_license_management() {
    info "...Try to update License Management"

    kanri_id=$1
    JSON_BODY=$2
    FILE_TO_UPLOAD=$3

    URL="$EXASTRO_URL/api/$EXASTRO_ORG_ID/workspaces/$EXASTRO_WS_ID/ita/menu/LicenseManagement/maintenance/all/"
    cmd_type="Update"

    post_form_api "$URL" "$JSON_BODY" "$FILE_TO_UPLOAD"
    ret=$?
    if [ $ret -eq 0 ] && [ "${HTTP_STATUS}" -eq 200 ]; then
        API_RTN=$(echo "${RESPONSE_BODY}" | jq -r '.data')

        info "${cmd_type} 'License Management(uuid=${kanri_id})' Successfully"
        return 0
    fi

    error "Failed to ${cmd_type} 'License Management(uuid=${kanri_id})' (status_code=${HTTP_STATUS} response=${RESPONSE_BODY})"
    return 1
}


#########################################
# Utility functions
#########################################

### Logger functions
info() {
    echo "$(date) [INFO]: ${*}" | tee -a "${LOG_FILE}"
}
warn() {
    echo "$(date) [WARN]: ${*}" | tee -a "${LOG_FILE}"
}
error() {
    echo "$(date) [ERROR]: ${*}" | tee -a "${LOG_FILE}"
}


### api functions (post application/json)
post_json_api() {
    URL=$1
    JSON_BODY=$2
    HTTP_STATUS=""
    RESPONSE_BODY=""

    CURL_OUTPUT=$(curl -s -X POST -k "$URL" \
        -u "${EXASTRO_USERNAME}:${EXASTRO_PASSWORD}" \
        -H "accept: application/json" \
        -H "Content-Type: application/json" \
        -w '\n%{http_code}' \
        -d "${JSON_BODY}")
    API_RTN=$?
    if [ $API_RTN -ne 0 ]; then
        error "curl command failed ({$CURL_OUTPUT})"
        return 1
    fi

    # 最後の行がステータスコードと仮定して抽出
    HTTP_STATUS=$(echo "$CURL_OUTPUT" | tail -n 1)
    # 最後の行以外
    RESPONSE_BODY=$(echo "$CURL_OUTPUT" | head -n -1)

    return 0
}


### api functions (post multipart/form-data)
post_form_api() {
    URL=$1
    JSON_BODY=$2
    FILE_TO_UPLOAD=$3
    HTTP_STATUS=""
    RESPONSE_BODY=""

    CURL_OUTPUT=$(curl -s -X POST -k "$URL" \
        -u "${EXASTRO_USERNAME}:${EXASTRO_PASSWORD}" \
        -H "Content-Type: multipart/form-data" \
        -w '\n%{http_code}' \
        -F "${JSON_BODY}" \
        -F "${FILE_TO_UPLOAD}")
    API_RTN=$?
    if [ $API_RTN -ne 0 ]; then
        error "curl command failed"
        error "{$CURL_OUTPUT}"
        return 1
    fi

    # 最後の行がステータスコードと仮定して抽出
    HTTP_STATUS=$(echo "$CURL_OUTPUT" | tail -n 1)
    # 最後の行以外
    RESPONSE_BODY=$(echo "$CURL_OUTPUT" | head -n -1)

    return 0
}

openssl_ecnrypt() {
    local text="$1"
    local passphrase="$2"
    ENCRYPTED_TEXT=$(echo -n "${text}" | openssl enc -e -aes-256-cbc -pbkdf2 -iter 100 -base64 -k "${passphrase}")
}

check_command() {
    local cmd_name="$1"
    if ! command -v "${cmd_name}" &> /dev/null; then
        error "${cmd_name}: command not found"
        return 1
    fi
    return 0
}

main "$@"
