# Main Menu (Dashboard) Widget Configuration

Widgets are displayed on the main menu, and their content and layout can be customized per user. The customized Dashboard configuration is saved per user on the system, so the same settings are available even when logging in from a different environment.

## Widget List

| No | Widget Name | Description | Default |
|---|---|---|---|
| 1 | Menu Group | Displays panels for each menu group (only installed drivers are shown). Cannot be removed. | Shown |
| 2 | Movement | Displays a pie chart of Movement counts per orchestration. | Shown |
| 3 | Work Status | Displays a pie chart of Conductor work counts by status. | Shown |
| 4 | Work Result | Displays a pie chart of Conductor work counts by result status. | Shown |
| 5 | Work History | Displays a bar chart of Conductor work history by day. | Shown |
| 6 | Menu Set | Creates a menu group set separate from the main menu. | Hidden |
| 7 | Link | Creates a list of links. | Hidden |
| 8 | Scheduled Work Confirmation | Displays the list of Conductors with status "Not executed (reserved)" (instance ID, Conductor name, operation name, scheduled date/time, remaining time). | Hidden |
| 9 | Image | Pastes an image. | Hidden |

## Editing the Dashboard

In edit mode you can add, edit, and delete widgets, apply edits (confirm changes), reset (return to the initial state), and cancel edits (revert to the pre-change state). You can add or remove a "Blank" (empty row) above or below an existing widget. Panels in the "Menu Group" widget can be moved into the "Menu Set" widget via drag and drop.

## Common Widget Settings

Name, horizontal/vertical span, widget display (show/hide), title bar (show/hide), border/background (show/hide).

## Widget-Specific Settings

| Widget | Settings |
|---|---|
| Menu Group / Menu Set | Items per row, display format (icon/list), show/hide menu group name, page navigation method (same tab/new tab/new window) |
| Movement Count / Conductor Work Status / Conductor Work Result | Page navigation method |
| Conductor Work History / Conductor Scheduled Work Confirmation | Period, page navigation method |
| Link List | Items per row, page navigation method, items (name and link URL can be added, reordered, and removed) |
| Image | Image URL, link URL, page navigation method |
