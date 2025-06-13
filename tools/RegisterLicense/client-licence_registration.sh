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

LOG_FILE=$HOME/exastro-ansible-license-registration.log
ENV_FILE="$HOME/.env"

# ログ出力
info() {
    echo "$(date) [INFO]: ${*}" | tee -a "${LOG_FILE}"
}
warn() {
    echo "$(date) [WARN]: ${*}" | tee -a "${LOG_FILE}"
}
error() {
    echo "$(date) [ERROR]: ${*}" | tee -a "${LOG_FILE}"
    exit 1
}


# JSON解析
extract_json_value() {
    echo "$1" | tr -d '\n' | sed -n "s/.*\"$2\": *\"\([^\"]*\)\".*/\1/p"
}

# 情報複合化
decrypt_with_key() {
    echo "$1" | openssl enc -d -aes-256-cbc -pbkdf2 -iter 100 -base64 -k "$2"
}


# 設定ファイル読み込み
load_setting_file() {

    if [ -f "$ENV_FILE" ]; then
        info "Loading enviroment variables from .env."
        set -a
        source "$ENV_FILE"
        set +a
    else
        error ".env not found."
    fi
}

get_license_information() {
    local base_url=$ITA_PROTCOL://$ITA_HOST:$ITA_PORT

    info "Getting license information from Exastro IT Automation."

    # アクセストークン取得
    local token_response
    token_response=$(
        curl -s -X POST "$base_url/auth/realms/$ITA_EXASTRO_ORG_ID/protocol/openid-connect/token" \
            -d "client_id=_$ITA_EXASTRO_ORG_ID-api" \
            -d "grant_type=refresh_token" \
            -d "refresh_token=$ITA_REFRESH_TOKEN" \
            -w '\n%{http_code}'
    )
    local http_code="${token_response: -3}"
    if [[ "$http_code" -ne 200 ]]; then
        error "Received error response from Exastro IT Automation API: $token_response"
    fi
    local access_token
    access_token=$(echo "$token_response" | sed -n 's/.*"access_token": *"\([^"]*\)".*/\1/p')


    # API呼び出し
    local api_url="/api/$ITA_EXASTRO_ORG_ID/workspaces/$ITA_EXASTRO_WS_ID/ita/menu/EncryptedLicenseAccess/filter/?file=no"
    local request_body='{"discard": {"NORMAL": "0"}, "kanri_id": {"NORMAL": "__KANRI_ID__"}}'
    request_body="${request_body/__KANRI_ID__/$KANRI_ID}"
    local response
    response=$(
        curl -s -X POST -k "$base_url$api_url" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $access_token" \
            -d "$request_body" \
            -w '\n%{http_code}'
    )
    http_code="${response: -3}"
    if [[ "$http_code" -ne 200 ]]; then
        error "Received error response from Exastro IT Automation API: $response"
    fi

    license_information="$response"
}


# AAPライセンス投入
register_aap_license() {
    if [[ "$AAP_REGISTER_FLG" -eq 0 ]]; then
        info "Ansible Automation Platform license registration process skipped.."
    elif [[ "$AAP_REGISTER_FLG" -eq 1 ]]; then

        # ライセンス初期化
        info "Unregistering current Ansible Automation Platform (AAP) license"
        if sudo subscription-manager unregister 2>&1 | tee -a "$LOG_FILE"; then
            info "AAP license unregistration completed successfully."
        else
            info "System is not registered. Skipping unregistration."
        fi


        # キャッシュ削除
        info "Cleaning up subscripton manager cache data"
        if sudo subscription-manager clean 2>&1 | tee -a "$LOG_FILE"; then
            info "Cache cleaned successfully."
        else
            error "Failed to clean cache."
        fi

        # ライセンス情報複合化
        local aap_activationkey
        local aap_orgid
        aap_activationkey=$(extract_json_value "$license_information" "aap_activationkey")
        aap_orgid=$(extract_json_value "$license_information" "aap_orgid")
        aap_activationkey=$(decrypt_with_key "$aap_activationkey" "$PASSPHRASE")
        aap_orgid=$(decrypt_with_key "$aap_orgid" "$PASSPHRASE")

        # ライセンス投入
        info "Starting AAP license registration..."
        if sudo subscription-manager register --activationkey="$aap_activationkey" --org="$aap_orgid"; then
            info "AAP license registration completed successfully."
        else
            error "AAP license registration unsuccessful."
        fi

    else
        error "Invalid Settings. Check .env." # 設定エラー
    fi
}

# AAHログイン
login_to_aah() {
    if [[ "$AAH_LOGIN_FLG" -eq 0 ]]; then
        info "Login process to Ansible Automation Hub container image registry skipped."
    elif [[ "$AAH_LOGIN_FLG" -eq 1 ]]; then

        # リポジトリ有効化
        IFS=',' read -ra ITEMS <<< "$REPO_LIST"
        for item in "${ITEMS[@]}"; do
            info "Enabling repository: $item"
            sudo subscription-manager repos --enable="$item"
            if [ $? -eq 1 ]; then
                error "Failed to enable repository: $item"
            fi
        done

        # Podmanインストール
        info "Installing Podman."
        if sudo dnf install -y podman podman-docker 2>&1 | tee -a "$LOG_FILE"; then
            :
        else
            error "Failed to install podman."
        fi

        # ログアウト
        info "Logging out from Ansible Automation Hub (AAH) container image registry"
        if podman logout "$AAH_CONTAINER_IMAGE_REGISTRY"; then
            :
        else
            error "Logout failed."
        fi

        # ログイン情報複合化
        local aah_username=
        local aah_password=
        aah_username=$(extract_json_value "$license_information" "aah_username")
        aah_password=$(extract_json_value "$license_information" "aah_password")
        aah_username=$(decrypt_with_key "$aah_username" "$PASSPHRASE")
        aah_password=$(decrypt_with_key "$aah_password" "$PASSPHRASE")

        # ログイン
        info "Logging in to AAH container image registry."
        if podman login "$AAH_CONTAINER_IMAGE_REGISTRY" --username="$aah_username" --password="$aah_password"; then
            info "Logged in successfully."
        else
            error "Login failed."
        fi


    else
        error "Invalid Settings. Check .env." # 設定エラー
    fi
}


load_setting_file
get_license_information
register_aap_license
login_to_aah
info "Process completed successfully."