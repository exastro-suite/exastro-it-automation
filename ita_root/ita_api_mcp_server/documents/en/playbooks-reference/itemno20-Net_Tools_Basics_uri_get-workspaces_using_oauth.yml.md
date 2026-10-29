# Ansible Legacy Default Playbook - Net_Tools_Basics_uri_get-workspaces_using_oauth.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 20
- **playbook_name**: ~[Exastro standard] API call/OAuth authentication
- **playbook_file**: Net_Tools_Basics_uri_get-workspaces_using_oauth.yml
## Overview
Two `uri` tasks: POSTs a refresh_token grant to the platform-auth token endpoint to get an access token, then GETs the organization's workspace list with that token as a Bearer header.
## Description
"ITA_DFLT_Organization_ID": Exastro organization ID. It is substituted into the authentication realm URL, into the OAuth client ID (`_<organization ID>-api`), and into the workspace API path.
"ITA_DFLT_Refresh_Token": OAuth refresh token sent with the `refresh_token` grant type in order to obtain an access token.
The first task uses `register` to store the token response in "ITA_DFLT_Response", and the second task reads `ITA_DFLT_Response.json.access_token` from it to build the `Authorization: Bearer` header. The second task sends `Accept` and `Content-Type` of `application/json`, expects status code 200, and stores its own response with `register` in "ITA_DFLT_API_Response", which is available to later tasks. Both tasks set `no_log: true` because they handle credentials, so their parameters and results are suppressed in the log; change it to `false` when debugging.
## Keyword
- Keycloak realm authentication
- refresh token grant flow
- Exastro platform REST API
- machine-to-machine API client
## Playbook
```yaml
- name: Get access token
  ansible.builtin.uri:
    url: "http://platform-auth:8000/auth/realms/{{ ITA_DFLT_Organization_ID }}/protocol/openid-connect/token"
    method: POST
    body_format: form-urlencoded
    body:
      client_id: "_{{ ITA_DFLT_Organization_ID }}-api"
      grant_type: "refresh_token"
      refresh_token: "{{ ITA_DFLT_Refresh_Token }}"
  register: ITA_DFLT_Response
  no_log: true # 機密情報を含むため、ログを抑止（デバッグしたいときはfalseに変更してください）

- name: Interacts with webservices
  ansible.builtin.uri:
    url: "http://platform-auth:8000/api/{{ ITA_DFLT_Organization_ID }}/platform/workspaces" 
    headers:
      Accept: "application/json"
      Authorization: "Bearer {{ ITA_DFLT_Response.json.access_token }}"
      Content-Type: "application/json"
    status_code: 200
    method: GET
  register: ITA_DFLT_API_Response
  no_log: true # 機密情報を含むため、ログを抑止（デバッグしたいときはfalseに変更してください）
```
