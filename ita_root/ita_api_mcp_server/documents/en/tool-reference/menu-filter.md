# menu-filter tool reference

## file parameter
- Specify "No" first.
- If you need to set the option to "Yes" because the file is required, you must specify `filter_conditions` that sufficiently narrow down the number of records, based on the list obtained when the option was set to "No".

## Filter Conditions Format
This section describes how to specify the `.filter_conditions` parameter.

### Supported Search Options
- **NORMAL**: Partial match - `{"column_name_rest": {"NORMAL": "exact_value"}}`
- **LIST**: Multiple values (exact match) - `{"column_name_rest": {"LIST": ["value1", "value2"]}}`
- **RANGE**: Range search - `{"column_name_rest": {"RANGE": {"START": "min", "END": "max"}}}`

### Examples
```json
// Exact match
{"operation_name": {"NORMAL": "operation name"}}

// Multiple values
{"status": {"LIST": ["Completed", "Executing"]}}

// Empty = get all records
{}
```
