#!/bin/bash

EXASTRO_URL="http://platform-auth:38000"
EXASTRO_ORG_ID="org1"
EXASTRO_WS_ID="ws1"
EXASTRO_USERNAME="admin"
EXASTRO_PASSWORD=""


# SYSTEM
HTTP_STATUS=""
RESPONSE_BODY=""
API_RTN=""

main() {
    info "check the required commands (jq curl)"
    required_commands=("jq" "curl")
    for cmd in "${required_commands[@]}"; do
        check_command "${cmd}"
        ret=$?
        if [ $ret -ne 0 ]; then
            exit 1
        fi
    done

    setup

    while true; do # 全体（エージェント単位）
        echo "Please make each event data"
        echo ""

        JSON_BODY="{
\"events\": ["

        EVENTID=10000

        while true; do # eventブロックのループ（event_collection_settings_name×fetched_timeの単位）
            JSON_BODY_BLOCK=""
            while true; do
                read -r -p "event_collection_settings_name : " EVENT_COLLECTION_SETTINGS_NAME
                if [ "${EVENT_COLLECTION_SETTINGS_NAME}" == "" ]; then
                    echo "please enter event_collection_settings_name ... retry"
                    continue
                fi
                break
            done

            while true; do
                read -r -p "agent_name : " AGENT_NAME
                if [ "${AGENT_NAME}" == "" ]; then
                    echo "please enter agent_name ... retry"
                    continue
                fi
                break
            done

            TIMESTAMP=$(date "+%s")
            echo ""
#             cat <<_EOF_
# event_collection_settings_name:         ${EVENT_COLLECTION_SETTINGS_NAME}
# agent_name:                             ${AGENT_NAME}
# _EOF_

            JSON_BODY_BLOCK+="{
    \"event\": ["

            JSON_BODY_EVENT=""
            while true; do # eventのループ
                JSON_BODY_EVENT_TMP=""
                while true; do
                    read -r -p " eventid : " EVENTID
                    if [ "${EVENTID}" == "" ]; then
                        EVENTID=$((EVENTID+1))
                    fi
                    break
                done

                while true; do
                    read -r -p " event_name : " EVENT_NAME
                    if [ "${EVENT_NAME}" == "" ]; then
                        EVENT_NAME="High CPU utilization (over 90% for 5m)"
                    fi
                    break
                done

                while true; do
                    read -r -p " severity : " SEVERITY
                    if [ "${SEVERITY}" == "" ]; then
                        SEVERITY="3"
                    fi
                    break
                done

                while true; do
                    read -r -p " clock : " CLOCK
                    if [ "${CLOCK}" == "" ]; then
                        CLOCK=$(date "+%s")
                    fi
                    break
                done

                echo ""

                JSON_BODY_EVENT_TMP+="{
            \"eventid\": \"$((EVENTID))\",
            \"source\": \"0\",
            \"object\": \"0\",
            \"objectid\": \"16046\",
            \"clock\": \"${CLOCK}\",
            \"ns\": \"906955445\",
            \"r_eventid\": \"0\",
            \"r_clock\": \"0\",
            \"r_ns\": \"0\",
            \"correlationid\": \"0\",
            \"userid\": \"0\",
            \"name\": \"${EVENT_NAME}\",
            \"acknowledged\": \"0\",
            \"severity\": \"${SEVERITY}\",
            \"opdata\": \"Current utilization: 100 %\",
            \"suppressed\": \"0\",
            \"urls\": []
        },"
                read -r -p " May I Add this event data? (y/n) [default: n]: " confirm
                echo ""
                if echo "$confirm" | grep -q -e "[yY]" -e "[yY][eE][sS]"; then
                    JSON_BODY_EVENT+=${JSON_BODY_EVENT_TMP}
                else
                    echo "CANCEL event data"
                    continue
                fi

                read -r -p " Continue input event data? (y/n) [default: n]: " confirm
                echo ""
                if echo "$confirm" | grep -q -e "[yY]" -e "[yY][eE][sS]"; then
                    continue
                else
                    break
                fi
            done

            # read -r -p "May I send Event Data with these settings? (y/n) [default: n]: " confirm
            # echo ""
            # if echo "$confirm" | grep -q -e "[yY]" -e "[yY][eE][sS]"; then
            #     continue
            # fi

            JSON_BODY_EVENT=${JSON_BODY_EVENT::-1}

            JSON_BODY_BLOCK+=${JSON_BODY_EVENT}
            JSON_BODY_BLOCK+="],
        \"event_collection_settings_name\": \"${EVENT_COLLECTION_SETTINGS_NAME}\",
        \"fetched_time\": $((TIMESTAMP)),
        \"agent\": {
            \"name\" : \"${AGENT_NAME}\",
            \"version\": \"2.7.0\"
        }
    },"

            JSON_BODY+=${JSON_BODY_BLOCK}
            read -r -p "Continue input event blcok data? (y/n) [default: n]: " confirm
            echo ""
            if echo "$confirm" | grep -q -e "[yY]" -e "[yY][eE][sS]"; then
                continue
            else
                break
            fi
        done

        read -r -p "May I send Event Data? (y/n) [default: n]: " confirm
        echo ""
        if echo "$confirm" | grep -q -e "[yY]" -e "[yY][eE][sS]"; then
            JSON_BODY=${JSON_BODY::-1}
            JSON_BODY+="]
}"
            # echo "${JSON_BODY}"
            sendEvent
            echo ""
        fi
    done

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
        cat <<_EOF_
The Exastro system parameters are as follows.

Service URL:                    ${EXASTRO_URL}
Organization ID:                ${EXASTRO_ORG_ID}
Workspace ID:                   ${EXASTRO_WS_ID}
USERNAME:                       ${EXASTRO_USERNAME}
PASSWORD:                       ********
_EOF_

        read -r -p "Start the process with these settings? (y/n) [default: n]: " confirm
        echo ""
        if echo "$confirm" | grep -q -e "[yY]" -e "[yY][eE][sS]"; then
            break
        fi
    done
}


sendEvent() {
    info "...Try to post events to OASE EVENT RECEIVER"

    # 送信
    URL="$EXASTRO_URL/api/$EXASTRO_ORG_ID/workspaces/$EXASTRO_WS_ID/oase_agent/events"

    post_json_api "$URL" "$JSON_BODY"
    ret=$?
    if [ $ret -eq 0 ] && [ "${HTTP_STATUS}" -eq 200 ]; then
        API_RTN=$(echo "${RESPONSE_BODY}" | jq -r '.data')

        if [ "${API_RTN}" != "[]" ]; then
            info "post events to OASE EVENT RECEIVER Successfully"
            return 0
        fi
    fi

    error "Failed to post events to OASE EVENT RECEIVER (status_code=${HTTP_STATUS} response=${RESPONSE_BODY})"
    return 1
}


#########################################
# Utility functions
#########################################

### Logger functions
info() {
    echo "$(date) [INFO]: ${*}"
}
warn() {
    echo "$(date) [WARN]: ${*}"
}
error() {
    echo "$(date) [ERROR]: ${*}"
}


### api functions (post application/json)
post_json_api() {
    URL=$1
    JSON_BODY=$2
    HTTP_STATUS=""
    RESPONSE_BODY=""

    # CURL_OUTPUT=$(curl -s -X POST -k "$URL" \
    #     -u "${EXASTRO_USERNAME}:${EXASTRO_PASSWORD}" \
    #     -H "accept: application/json" \
    #     -H "Content-Type: application/json" \
    #     -w '\n%{http_code}' \
    #     -d "${JSON_BODY}")
    CURL_OUTPUT=$(cat << EOF | curl -s -X POST -k "$URL" \
        -u "${EXASTRO_USERNAME}:${EXASTRO_PASSWORD}" \
        -H "accept: application/json" \
        -H "Content-Type: application/json" \
        -w '\n%{http_code}' \
        --data-binary @-
${JSON_BODY}
EOF
)
    API_RTN=$?
    if [ $API_RTN -ne 0 ]; then
        error "curl command failed (${CURL_OUTPUT})"
        return 1
    fi

    # 最後の行がステータスコードと仮定して抽出
    HTTP_STATUS=$(echo "$CURL_OUTPUT" | tail -n 1)
    # 最後の行以外
    RESPONSE_BODY=$(echo -e "$CURL_OUTPUT" | head -n -1)

    return 0
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
