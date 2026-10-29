# OASE Management (Agent, Event Collection, Notification Templates) Configuration

## Agent Overview

The agent (Exastro OASE Agent) is independent of Exastro IT Automation (ITA) and acts as an intermediary between ITA OASE and external services. It retrieves event collection settings for the target external service from ITA, uses those settings to fetch events from the external service, and sends them to ITA.

## Agent Usage Procedure

1. **Event Collection Settings**: In the OASE Management Event Collection menu, register the settings for the target collection service.
2. **Label Settings**: In OASE Label Creation/Label Assignment, configure label assignment (deduplication can also be configured for redundant configurations).
3. **Install and Start the Agent**: Start the agent to begin event collection.

## Notification Template (Common) Usage Procedure

1. In OASE Management's Notification Template (Common), maintain (view/update) the templates used for OASE notifications.
2. Log in to the Exastro system as an organization administrator and register a notification destination under "Notification Management."
3. If the notification destination is email, also register the "Mail Sending Server Settings."

The Notification Template (Common) can be used without modification.

## Menu Structure

| No | Menu Group | Menu/Screen | Description |
|---|---|---|---|
| 1 | OASE Management | Event Collection | Manages information about event collection targets. |
| 2 | OASE Management | Notification Template (Common) | Manages the information used for OASE notifications. |

## Event Collection Settings

Under "OASE Management → Event Collection," maintain the connection method, authentication method, TTL, etc. for event collection targets.

| Field | Description | Constraints |
|---|---|---|
| Event Collection Setting Name | Arbitrary name | Max 255 bytes |
| Connection Method | Bearer authentication / Password authentication / Arbitrary authentication / IMAP password authentication / No agent used | - |
| Request Method | Bearer/Password/Arbitrary authentication: GET, POST. IMAP password authentication: IMAP: Plaintext | - |
| Connection Target | Enter a hostname for mail servers, a URL for APIs. Reserved variables in Jinja2 format can be used | Max 1024 bytes |
| Port | Port of the connection target | 0 to 65535 |
| Authentication Info (Request Header) | JSON format; Jinja2 reserved variables can be used | Max 4000 bytes |
| Authentication Info (Proxy) | Proxy URI | Max 255 bytes |
| Authentication Info (Auth Token) | Token for Bearer authentication | Max 1024 bytes |
| Authentication Info (Username/Password) | Login credentials | Username 255 bytes, password 4000 bytes |
| Authentication Info (Mailbox Name) | Default is INBOX | Max 255 bytes |
| Parameters | JSON format; Jinja2 reserved variables can be used. Used as query parameters for GET, or as the request payload for POST | Max 255 bytes |
| Response Key | Specifies, using JMESPath, the parent key of the property received as an event from the response payload | Max 255 bytes |
| Response List Flag | Whether the value obtained from the Response Key is an array (if True, the array is split into individual events) | - |
| Event ID Key | The key that uniquely identifies an event (specified with JMESPath, at a level below the Response Key) | Max 255 bytes |
| TTL | The period (seconds) during which the event is treated as subject to rule evaluation | Min 10, max 2147483647, default 3600 |
| Remarks | Free text | Max 4000 bytes |

Combinations of connection method, request method, and authentication info:

| Connection Method | Request Method | Authentication Info |
|---|---|---|
| IMAP password authentication | IMAP: Plaintext | Username/password |
| Bearer authentication | GET, POST | Auth token |
| Password authentication | GET, POST | Username/password |
| Arbitrary authentication | GET, POST | Written into parameters |

When the collection source is email, depending on the character encoding, some characters that cannot be decoded may be omitted when the collected event is saved (verified character encodings are described below).

## Notification Template (Common) Settings

Under "OASE Management → Notification Template (Common)," maintain the templates used by the OASE notification feature. The content must be modified and fields added according to the notification method in use, and format adjustments are required for any notification method other than email.

| Field | Description | Constraints |
|---|---|---|
| Event Type | New Event (on receipt/scheduled for consolidation/before evaluation), Known Event (at evaluation/TTL expired), Undetected Event (at evaluation) | Required |
| Template | Defaults are New(received).j2, New(consolidated).j2, New.j2, Known(evaluated).j2, Known(timeout).j2, Undetected.j2 | Max 2MB |
| Notification Destination | Cannot be set for the default template. For non-default templates, a unique destination is required within the same event type | - |
| Default | Uses the default template when sending to a destination not present in a record | - |
| Remarks | Free text | Max 4000 bytes |

Only the template and remarks can be updated for the default template, and it cannot be decommissioned. Templates are in Jinja2 format and can reference variables such as `labels.*` (system labels), `exastro_events`, `exastro_agents`, and `exastro_edit_count`. The **[TITLE]** and **[BODY]** elements are required; if they are missing or malformed, the notification will fail. Only edit the content inside the [TITLE] and [BODY] elements—do not delete or change the elements themselves.

## Appendix: OASE Agent .env Settings

| Parameter | Description |
|---|---|
| AGENT_NAME | The name of the OASE agent to start. Also used as the internal database filename. |
| EXASTRO_URL | The destination for API requests to ITA. |
| EXASTRO_ORGANIZATION_ID | The Organization identifier used in API requests. |
| EXASTRO_WORKSPACE_ID | The workspace identifier used in API requests. Must be a workspace linked to EXASTRO_ORGANIZATION_ID. |
| EXASTRO_REFRESH_TOKEN | Token for Bearer authentication. The user's role must be able to maintain the OASE - Event - Event History menu. |
| EXASTRO_USERNAME / EXASTRO_PASSWORD | Basic authentication credentials (used when REFRESH_TOKEN is not used; not recommended). |
| EVENT_COLLECTION_SETTINGS_NAMES | Names of the event collection settings to retrieve. |
| ITERATION | Number of loop iterations. |
| EXECUTE_INTERVAL | Loop execution interval. |

To apply configuration changes to the agent immediately, delete `event_collection_settings.json` inside the container (if the file does not exist, the latest settings are re-fetched from ITA). If not deleted, changes are not applied until the loop finishes the number of iterations set in ITERATION.

## Appendix: Response Key, JMESPath, and Event ID Key

- **Response Key**: The parent key of the item extracted as an event from the response payload. Specified in JMESPath format. Only JSON-format responses from monitoring software are supported.
- **JMESPath**: A query language for JSON. JSON keys are joined with ".", and `[]` is appended for arrays (e.g., `value[].name`, `value[].timeseries[].metadatavalues[].name`).
- **Response List Flag**: True if the value extracted by the Response Key is an array, False otherwise (a scalar value or object).
- **Event ID Key**: The key that uniquely identifies an event within the result extracted by the Response Key. Specified in JMESPath format, at the level below the Response Key extraction. Specifying a nonexistent key results in an empty value and incorrect behavior.

## Appendix: Example Event Collection Settings by Monitoring Software

**Zabbix** (e.g., v6.4.12): Calls the `problem.get` API via POST. Connection method "Arbitrary authentication," Response Key `result`, Response List Flag `True`, Event ID Key `eventid`. The auth token is obtained via `user.login` for a Zabbix user (a dedicated user is recommended).

**Grafana** (e.g., v10.3, with Prometheus 2.49 as the data source): Calls the alerts API via GET. Connection method "Bearer authentication," Response Key `data.alerts`, Response List Flag `True`, Event ID Key `activeAt`. The auth token is obtained via a Grafana Service account token (Administration > Service accounts).

HTTP API specifications differ by monitoring software version, so check the specification for the version in use.

## Appendix: Available Reserved Variables

Reserved variables available in "Connection Target," "Request Header," and "Parameters":

| Variable Name | Description |
|---|---|
| EXASTRO_LAST_FETCHED_TIMESTAMP | Date/time of the previous fetch (UNIX timestamp) |
| EXASTRO_LAST_FETCHED_DD_MM_YY / EXASTRO_LAST_FETCHED_YY_MM_DD | Date/time of the previous fetch (in each respective format) |
| EXASTRO_LAST_FETCHED_EVENT_IS_EXIST | Flag (True/False) indicating whether an event was fetched previously |
| EXASTRO_LAST_FETCHED_EVENT | Raw data of the previously fetched event. Properties can be referenced in JMESPath format (e.g., `EXASTRO_LAST_FETCHED_EVENT.clock`) |
| EXASTRO_EVENT_COLLECTION_SETTING | References each field of the event collection settings (`.URL`, `.PORT`, `.AUTH_TOKEN`, `.USERNAME`, `.PASSWORD`, `.PARAMETER`, `.RESPONSE_KEY`, `.RESPONSE_LIST_FLAG`, `.EVENT_ID_KEY`, `.TTL`, etc.) |
| EXASTRO_LAST_FETCHED_TIME / EXASTRO_CURRENT_TIME | Previous fetch time / current time (in YYYY-MM-DD HH:MM:SS format) |

Usage examples: embedding an auth token in the connection URL (`?token={{ EXASTRO_EVENT_COLLECTION_SETTING.AUTH_TOKEN | urlencode() }}`), embedding a Bearer token in the request header, specifying filter conditions in parameters based on the current/previous date-time, and branching based on whether a previous event was fetched (`{% if EXASTRO_LAST_FETCHED_EVENT_IS_EXIST %}`).

## Appendix: Example Notification Template Configuration (ServiceNow Record Registration)

When ServiceNow (record registration) is used as the notification method, the TITLE content is not used, and the BODY should be written in the request body format for ServiceNow's REST API record registration. If embedded data contains double quotes or backslashes, an error will occur, so use filters such as `replace('\\', '\\\\')` and `replace('"', '\\\"')` to avoid this. Control codes other than TAB/LF/CR (\x01–\x1f) will also cause an error, so remove them with a filter such as `replace('\x01', '')`.
