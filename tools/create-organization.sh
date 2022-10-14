#!/bin/bash

source "`dirname $0`/create-organization.conf"

if [ $# -gt 2 ]; then
    echo "Usage: `basename $0` [--retry] [organaization info json file]"
    exit 1
fi

PARAM_JSON_FILE=""
PARAM_RETRY="OFF"
while [ $# -gt 0 ]
do
    if [ "$1" == "--retry" ]; then
        PARAM_RETRY="ON"
        QUERY_STRING="?retry=1"
    else
        PARAM_JSON_FILE="$1"
    fi
    shift
done

# echo "PARAM_JSON_FILE :[${PARAM_JSON_FILE}]"
# echo "PARAM_RETRY     :[${PARAM_RETRY}]"

if [ ! -z "${PARAM_JSON_FILE}" ]; then
    if [ ! -f "${PARAM_JSON_FILE}" ]; then
        echo "Error: not found organaization info json file : ${PARAM_JSON_FILE}"
        exit 1
    fi
fi


if [ -z "${PARAM_JSON_FILE}" ]; then
    echo
    echo "Please enter the organization information to be created"
    echo
    read -p "organization id : " ORG_ID
    read -p "organization name : " ORG_NAME
    read -p "organization manager's username : " ORG_MNG_USERNAME
    read -p "organization manager's email : " ORG_MNG_EMAIL
    read -p "organization manager's first name : " ORG_MNG_FIRST_NAME
    read -p "organization manager's last name : " ORG_MNG_LAST_NAME
    read -p "organization manager's initial password : " ORG_MNG_PASSWORD

    BODY_JSON=$(
        cat << EOF
        {
            "id"    :   "${ORG_ID}",
            "name"  :   "${ORG_NAME}",
            "organization_managers" : [
                {
                    "username"  :   "${ORG_MNG_USERNAME}",
                    "email"     :   "${ORG_MNG_EMAIL}",
                    "firstName" :   "${ORG_MNG_FIRST_NAME}",
                    "lastName"  :   "${ORG_MNG_LAST_NAME}",
                    "credentials"   :   [
                        {
                            "type"      :   "password",
                            "value"     :   "${ORG_MNG_PASSWORD}",
                            "temporary" :   true
                        }
                    ],
                    "requiredActions": [
                        "UPDATE_PROFILE"
                    ],
                    "enabled": true
                }
            ],
            "options": {}
        }
EOF
    )
else
    BODY_JSON=$(cat "${PARAM_JSON_FILE}")
fi

echo
read -p "your username : " USERNAME
read -sp "your password : " PASSWORD

echo
read -p "Create an organization, are you sure? (Y/other) : " CONFIRM
if [ "${CONFIRM}" != "Y" -a "${CONFIRM}" != "y" ]; then
    exit 1
fi

# echo "POST JSON:"
# echo "${BODY_JSON}"
# echo

TEMPFILE_API_RESPONSE="/tmp/`basename $0`.$$.1"
TEMPFILE_API_CODE="/tmp/`basename $0`.$$.2"

touch "${TEMPFILE_API_RESPONSE}"
touch "${TEMPFILE_API_CODE}"

curl ${CURL_OPT} -X POST \
    -u ${USERNAME}:${PASSWORD} \
    -H 'Content-type: application/json' \
    -d "${BODY_JSON}" \
    -o "${TEMPFILE_API_RESPONSE}" \
    -w '%{http_code}\n' \
    "${CONF_BASE_URL}/api/platform/organizations${QUERY_STRING}" > "${TEMPFILE_API_CODE}"

RESULT_CURL=$?
RESULT_CODE=$(cat "${TEMPFILE_API_CODE}")

which jq &> /dev/null
if [ $? -eq 0 ]; then
    cat "${TEMPFILE_API_RESPONSE}" | jq
    if [ $? -ne 0 ]; then
        cat "${TEMPFILE_API_RESPONSE}"
    fi
else
    cat "${TEMPFILE_API_RESPONSE}"
fi

rm "${TEMPFILE_API_RESPONSE}" "${TEMPFILE_API_CODE}"

if [ ${RESULT_CURL} -eq 0 -a "${RESULT_CODE}" == "200" ]; then
    exit 0
else
    exit -1
fi
