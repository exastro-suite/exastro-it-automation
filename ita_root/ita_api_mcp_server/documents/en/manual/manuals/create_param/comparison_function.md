# Configuring and Using the Parameter Sheet Comparison Function

The comparison function compares parameter sheets (with host/operation) created via the parameter sheet creation function and outputs the differences.

## About the reference date/time

The reference date/time refers to the "last execution date/time" if the target operation has been executed at least once in the past, or the "scheduled execution date/time" if it has never been executed. If you specify a reference date/time when running a comparison, the comparison uses the latest data as of that point in time (if left blank, the data for the most recent reference date/time is used).

## Requirements for running the comparison function

- A parameter sheet (with host/operation) has been created.
- The parameter sheets to be compared are linked to each other in the comparison settings.
- The items to be compared are linked to each other in the comparison detail settings (only needed when the comparison setting's detail-setting flag is "True"; not needed when set to False, which requires the number and names of items to match exactly).

## Comparable item types and their combinations

Comparable item types: string (single-line/multi-line), integer, decimal, date-time, date, pulldown selection (shown as "ID conversion failed (X)" if the referenced target has been discarded), file upload (compared by file name and content), link, parameter sheet reference (shown as "ID conversion failed (X)" if the referenced target has been discarded).

Items of different types can also be compared. When comparing a file upload item with another item type, if either the file name or the content differs, it is judged as "has a difference" (for non-file-upload items, the file content is treated as empty for the comparison).

## Menu structure

| No | Menu/Screen | Description |
|---|---|---|
| 1 | Comparison Settings | Create a named setting for running a comparison and link the parameter sheets to be compared. Setting the detail-setting flag to True enables the Comparison Detail Settings. |
| 2 | Comparison Detail Settings | Configure item-level links between the parameter sheets to be compared. |
| 3 | Run Comparison | Run the comparison based on the Comparison Settings and Comparison Detail Settings. |

## Workflow

1. Create parameter sheets (with host/operation) and register data.
2. Create a Comparison Setting (link target parameter sheets 1 and 2, and set the detail-setting flag to True if needed).
3. If needed, link items to each other in the Comparison Detail Settings.
4. Select the comparison setting in Run Comparison and execute the comparison.

## Comparison Settings

Register and update the setting information used when running a comparison (links between the target parameter sheets).

| Item | Description | Required | Constraints |
|---|---|---|---|
| Comparison name | Arbitrary name | Yes | Max 255 bytes |
| Target parameter sheet 1/2 | The parameter sheets to compare | Yes | - |
| Detail-setting flag | False = Comparison Detail Settings not needed (the number and names of items in both parameter sheets must match exactly), True = Comparison Detail Settings required | - | - |
| Remarks | Free text | - | - |

## Comparison Detail Settings

Configure the links between the comparison item name and the items of each parameter sheet (only comparison settings with the detail-setting flag set to True are selectable here).

| Item | Description | Required | Constraints |
|---|---|---|---|
| Comparison name | Select from comparison settings with the detail-setting flag set to True | Yes | - |
| Comparison item name | The item name shown in the comparison result | Yes | Max 255 bytes |
| Target item 1/2 | Select from the items within target parameter sheets 1 and 2 of the comparison setting | Yes | - |
| Display order | The ascending order in which items are shown in the comparison result | Yes | 0 to 2147483647 |
| Remarks | Free text | - | - |

## Run Comparison

Runs the parameter sheet comparison based on the definitions in the Comparison Settings and Comparison Detail Settings. For parameter sheets used with a bundle, comparison is performed between items with the same item name, or between items linked in the Comparison Detail Settings that share the same substitution order.

Parameters for running the comparison: comparison setting selection (required), reference date/time 1 and 2 (the latest reference date/time is used if left blank), host selection (no filtering by default, results for all hosts are output).

The comparison result consists of a list of target hosts (host name and a "✓" indicating whether there is a difference) and, for each host, comparison result details (item name, whether there is a difference, the values of target parameter sheets 1 and 2, remarks). For file upload items, content differences can be viewed if the file is text-based, but content differences cannot be viewed for binary files. Comparison items used with a bundle are displayed in the form "item name[substitution order]"; the record number, host name, operation name, and reference date/time are not shown in the comparison result.
