# OASE (Operation Autonomy Support Engine) Overview

## Feature Overview

OASE is a feature that analyzes event information obtained from external sources and helps automate the response to those events. The feature flow is as follows:

1. **Event Collection**: Events are collected from external services. Events are collected by the Exastro OASE Agent and sent to the ITA core via API.
2. **Label Assignment**: Configured labels are attached to events received by ITA. This is intended to normalize event information from different applications for consistent handling within OASE.
3. **Evaluation**: Events are extracted (filtered) using the assigned labels, and it is determined whether they match the configured rules.
4. **Action Execution and Notification**: When a rule matches, the configured action (Conductor and Operation settings) is executed. Notifications before and after action execution can also be configured in the Rule menu.

## Glossary

| Term | Description |
|---|---|
| Monitoring System | Software/service that collects state changes in a system. Detects state changes and creates and sends events to OASE. |
| OASE | Operations automation support software that collects events created by monitoring systems and executes appropriate actions based on defined conditions. |
| Event | Information about a state change in a system, obtained from a monitoring system. |
| TTL (Time To Live) | The period (in seconds) during which an event is treated as subject to rule evaluation. Used for two purposes: ① to allow time for a complete set of conditions to be gathered so the highest-priority rule is applied when multiple rules could match, and ② to immediately exclude old events—those more than twice the TTL old—from evaluation as "timed out." Minimum 10 seconds, maximum 2147483647 seconds, default 3600 seconds. |
| Label | A property assigned to an event in a form (key-and-value) that is easy to handle within OASE, based on the label creation/assignment settings. Normalizes events from different applications. |
| Deduplication | A setting that, when essentially identical events are collected multiple times, ingests only the first one. Used to avoid handling duplicate data when the event collection system or OASE agent is redundant. |
| Filter | Extracting unique events based on label conditions, or the target of such extraction. Narrows events down before rule evaluation. |
| Rule | A condition for executing an action or generating a conclusion event, created by combining filters. |
| Action | The concrete response processing executed against an event when a rule matches. |
| Evaluation | The overall process in which collected events are extracted by filters, checked against rule conditions, and, if matched, the next action (action execution, conclusion event generation) is determined. |
| Conclusion Event | An event generated when a rule matches. It carries over information from the source event, including the processing/determination result, and can be re-evaluated by other rules, enabling chained automation. |

## Event States

| Type | Description |
|---|---|
| New | State after collection but not yet detected by the evaluation feature. After the evaluation time elapses, it transitions to either Known (Evaluated), Undetected, or Timed Out. |
| Known | State/target that has been detected by the evaluation feature. |
| Known (Evaluated) | State/target that matched a rule. |
| Timed Out | A target excluded from evaluation because it is too old (more than twice the TTL has elapsed), or because it failed to match by the evaluation timing immediately after the TTL elapsed. |
| Undetected | State/target that was not extracted by a filter (not detected by the evaluation feature). Needs to be reviewed as a candidate for future evaluation. |

## Notifications by Event Type

| Item | Description |
|---|---|
| New Event (on receipt) | Notified at the time the event is received. Events determined to be duplicates via deduplication are not notified. |
| New Event (scheduled for consolidation) | For a redundant group with deduplication settings, a consolidated notification is sent when the first event is received. Subsequent events are consolidated, but no new notification is sent. |
| New Event (before evaluation) | Notified for events that become subject to rule evaluation. |
| Known Event (at evaluation) | Notified when an event matches any rule. |
| Known Event (TTL expired) | Notified for events whose TTL has expired. |
| Undetected Event | Notified for events that did not match any rule/condition. |
