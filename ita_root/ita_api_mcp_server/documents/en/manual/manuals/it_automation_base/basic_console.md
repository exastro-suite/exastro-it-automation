# Basic Console Configuration and Usage

The Basic Console provides functions commonly required when working with ITA.

## Menu Structure

| Menu Group | Menu Screen | Description |
|---|---|---|
| ITA Basic Console | Operation List | Maintain (view/register/update/decommission) the list of registered operations. |
| ITA Basic Console | Movement List | View the list of registered Movements (view only). |

## Operation List

Manages operations (e.g. "Service addition work") to be executed against target hosts by the orchestrator.

| Item | Description | Required | Constraints |
|---|---|---|---|
| Operation ID | Automatically assigned unique ID | - | - |
| Operation Name | Any operation name | Yes | Max 256 bytes |
| Scheduled Date/Time | The scheduled date/time of the operation. Processing is not actually executed at this date/time. Work history records associated with an operation that has this date/time set are automatically deleted after the configured retention period. The actual date/time on which this operation was selected and executed via a Conductor run or a driver's work execution is displayed here. | Yes | - |
| Last Execution Date/Time | The most recent execution date/time (display only, blank if never executed) | - | - |
| Environment | Automatically populated with the environment registered when the workspace was created (used for integration with Exastro OASE and Exastro EPOCH) | - | - |
| Remarks | Free text | - | - |

## Movement List

Lets you view (read-only) the association between Movements and orchestrators when using the orchestrator. Movements themselves are registered from the ITA driver console menu of each orchestrator, following the usage manual for each driver.
