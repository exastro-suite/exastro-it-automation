# Ansible Legacy Default Playbook - Net_Tools_Basics_uri_get-workspaces_using_basic.yml
This playbook describes the playbooks initially registered in Exastro's playbook_list.
## Exastro Registration Info
- **item_no**: 10
- **playbook_name**: ~[Exastro standard] API call/Basic authentication
- **playbook_file**: Net_Tools_Basics_uri_get-workspaces_using_basic.yml
## Overview
Calls `uri` to GET http://platform-auth:8000/api/<organization>/platform/workspaces with forced HTTP basic authentication, requiring status 200 and registering the response.
## Description
"ITA_DFLT_Organization_ID": Exastro organization ID that is embedded in the request path. The URL itself is hard-coded as "http://platform-auth:8000/api/{{ ITA_DFLT_Organization_ID }}/platform/workspaces", so only this part of it can be controlled.
"ITA_DFLT_Basic_Username": User name used for HTTP basic authentication. force_basic_auth is set to true, so the credentials are sent on the very first request without waiting for a 401 challenge.
"ITA_DFLT_Basic_Password": Password that goes with the user name above.
The HTTP method is fixed to GET and status_code is fixed to 200, so the task fails if the service answers with any other status. The reply (status, headers and body) is stored in the registered variable "ITA_DFLT_API_Response" and can be referenced by later tasks. As the endpoint is fixed, this Playbook file mainly serves as a working sample of calling a REST API with basic authentication.
## Keyword
- REST API call sample
- HTTP basic authentication
- list Exastro workspaces
- query a web service from a playbook
## Playbook
```yaml
- name: Interacts with webservices using password
  ansible.builtin.uri:
    url: "http://platform-auth:8000/api/{{ ITA_DFLT_Organization_ID }}/platform/workspaces"
    force_basic_auth: true
    user: "{{ ITA_DFLT_Basic_Username }}"
    password: "{{ ITA_DFLT_Basic_Password }}"
    status_code: 200
    method: GET
  register: ITA_DFLT_API_Response
```
