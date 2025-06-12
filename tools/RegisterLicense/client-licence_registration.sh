#!/bin/bash
LOG_FILE=$HOME/exastro-ansible-licence-registration.log
ENV_FILE="$HOME/.env"

### ログ出力
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

get_licence_information() {
    local base_url=$ITA_PROTCOL://$ITA_HOST:$ITA_PORT

    info "Getting licence information from Exastro IT Automation."

    # アクセストークン取得
    local token_response=$(
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
    local access_token=$(echo "$token_response" | sed -n 's/.*"access_token": *"\([^"]*\)".*/\1/p')


    # API呼び出し
    local api_url="/api/$ITA_EXASTRO_ORG_ID/workspaces/$ITA_EXASTRO_WS_ID/ita/menu/EncryptedLicenseAccess/filter/?file=no"
    local request_body='{"discard": {"NORMAL": "0"}, "kanri_id": {"LIST": ["__KANRI_ID__"]}}'
    request_body="${request_body/__KANRI_ID__/$KANRI_ID}"
    local response=$(
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

    licence_information="$response"
}


# AAPライセンス投入
register_aap_licence() {
    if [[ "$AAP_REGISTER_FLG" -eq 0 ]]; then
        info "Ansible Automation Platform license registration process skipped.."
    elif [[ "$AAP_REGISTER_FLG" -eq 1 ]]; then

        # ライセンス初期化
        info "Unregistering current Ansible Automation Platform (AAP) licence"
        sudo subscription-manager unregister 2>&1 | tee -a $LOG_FILE
        if [ $? -eq 0 ]; then
            info "AAP license unregistration completed successfully."
        else
            info "System is not registered. Skipping unregistration."
        fi

        # キャッシュ削除
        info "Cleaning up subscripton manager cache data"
        sudo subscription-manager clean 2>&1 | tee -a $LOG_FILE
        if [ $? -eq 0 ]; then
            info "Cache cleaned successfully."
        else
            error "Failed to clean cache."
        fi

        # ライセンス情報複合化
        local aap_activationkey=$(extract_json_value "$licence_information" "aap_activationkey")
        local aap_orgid=$(extract_json_value "$licence_information" "aap_orgid")
        aap_activationkey=$(decrypt_with_key "$aap_activationkey" "$PASSPHRASE")
        aap_orgid=$(decrypt_with_key "$aap_orgid" "$PASSPHRASE")

        # ライセンス投入
        info "Starting AAP licence registration..."
        sudo subscription-manager register --activationkey="$aap_activationkey" --org="$aap_orgid" 2>&1 | tee -a $LOG_FILE
        if [ $? -eq 0 ]; then
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
        IFS=',' read -ra ITEMS <<< "$REPOSITORY_LIST"
        for item in "${ITEMS[@]}"; do
            info "Enabling repository: $item"
            sudo subscription-manager repos --enable=$item
            if [ $? -eq 1 ]; then
                error "Failed to enable repository: $item"
            fi
        done

        # Podmanインストール
        info "Installing Podman."
        sudo dnf install -y podman podman-docker 2>&1 | tee -a $LOG_FILE

        # ログアウト
        info "Logging out from Ansible Automation Hub (AAH) container image registry"
        podman logout $AAH_CONTAINER_IMAGE_REGISTRY 2>&1 | tee -a $LOG_FILE

        # ログイン情報複合化
        local aah_username=$(extract_json_value "$licence_information" "aah_username")
        local aah_password=$(extract_json_value "$licence_information" "aah_password")
        aah_username=$(decrypt_with_key "$aah_username" "$PASSPHRASE")
        aah_password=$(decrypt_with_key "$aah_password" "$PASSPHRASE")

        # ログイン
        info "Logging in to AAH container image registry."
        podman login $AAH_CONTAINER_IMAGE_REGISTRY --username=$aah_username --password=$aah_password 2>&1 | tee -a $LOG_FILE
        if [ $? -eq 0 ]; then
            info "Logged in successfully."
        else
            error "Login failed."
        fi


    else
        error "Invalid Settings. Check .env." # 設定エラー
    fi
}


load_setting_file
get_licence_information
register_aap_licence
login_to_aah