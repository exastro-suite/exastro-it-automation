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

    while true; do
        echo "Please make each event data"
        echo ""

        while true; do
            read -r -p "event_collection_settings_name : " EVENT_COLLECTION_SETTINGS_NAME
            if [ "${EVENT_COLLECTION_SETTINGS_NAME}" == "" ]; then
                echo "please enter event_collection_settings_name ... retry"
                echo ""
                continue
            fi
            echo ""
            break
        done

        while true; do
            read -r -p "agent_name : " AGENT_NAME
            if [ "${AGENT_NAME}" == "" ]; then
                echo "please enter agent_name ... retry"
                echo ""
                continue
            fi
            echo ""
            break
        done

            echo ""
            cat <<_EOF_
event_collection_settings_name:         ${EVENT_COLLECTION_SETTINGS_NAME}
agent_name:                             ${AGENT_NAME}
_EOF_
        read -r -p "May I send Event Data with these settings? (y/n) [default: n]: " confirm
        echo ""
        if echo "$confirm" | grep -q -e "[yY]" -e "[yY][eE][sS]"; then
            sendEvent "$EVENT_COLLECTION_SETTINGS_NAME" "$AGENT_NAME"
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

    EVENT_COLLECTION_SETTINGS_NAME=$1
    AGENT_NAME=$2

    # zabbixのイベント
    TIMESTAMP=$(date "+%s")
    EVENTID=$(shuf -i 0-99999 -n1)

    JSON_BODY="{
\"events\": [
    {
        \"event\": ["
for i in {1..2000}; do
JSON_BODY+="{
                \"eventid\": \"$((EVENTID+i))\",
                \"source\": \"0\",
                \"object\": \"0\",
                \"objectid\": \"16046\",
                \"clock\": \"$((TIMESTAMP+1))\",
                \"ns\": \"906955445\",
                \"r_eventid\": \"0\",
                \"r_clock\": \"0\",
                \"r_ns\": \"0\",
                \"correlationid\": \"0\",
                \"userid\": \"0\",
                \"name\": \"High CPU utilization (over 90% for 5m)\",
                \"acknowledged\": \"0\",
                \"severity\": \"2\",
                \"opdata\": \"Current utilization: 100 %\",
                \"suppressed\": \"0\",
                \"urls\": []
            },"
done
JSON_BODY=${JSON_BODY::-1}
JSON_BODY+="],
        \"event_collection_settings_name\": \"${EVENT_COLLECTION_SETTINGS_NAME}\",
        \"fetched_time\": $((TIMESTAMP+1)),
        \"agent\": {
            \"name\" : \"${AGENT_NAME}\",
            \"version\": \"2.7.0\"
        }
    },
    {
        \"event\": ["
for i in {1..2000}; do
JSON_BODY+="{
                \"eventid\": \"${EVENTID}\",
                \"source\": \"0\",
                \"object\": \"0\",
                \"objectid\": \"16046\",
                \"clock\": \"$((TIMESTAMP))\",
                \"ns\": \"906955445\",
                \"r_eventid\": \"0\",
                \"r_clock\": \"0\",
                \"r_ns\": \"0\",
                \"correlationid\": \"0\",
                \"userid\": \"0\",
                \"name\": \"High CPU utilization (over 90% for 5m)\",
                \"acknowledged\": \"0\",
                \"severity\": \"2\",
                \"opdata\": \"Current utilization: 100 %\",
                \"suppressed\": \"0\",
                \"urls\": []
            },"
done
JSON_BODY=${JSON_BODY::-1}
JSON_BODY+="],
        \"event_collection_settings_name\": \"${EVENT_COLLECTION_SETTINGS_NAME}\",
        \"fetched_time\": $((TIMESTAMP)),
        \"agent\": {
            \"name\" : \"${AGENT_NAME}\",
            \"version\": \"2.7.0\"
        }
    }
]
}"
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
