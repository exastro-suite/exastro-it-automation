# menu-filter tool reference

## file parameter
- 最初に「いいえ」と指定してください。
- ファイルが必須であるためオプションを「はい」に設定する場合は、オプションを「いいえ」に設定したときに取得したリストに基づいてレコード数を十分に絞り込む`filter_conditions`を指定する必要があります。

## Filter Conditions Format
このセクションでは、`.filter_conditions` のパラメータを指定する方法について説明します

### Supported Search Options
- **NORMAL**: 部分一致 - `{"column_name_rest": {"NORMAL": "exact_value"}}`
- **LIST**: 複数の値 (完全一致) - `{"column_name_rest": {"LIST": ["value1", "value2"]}}`
- **RANGE**: 範囲検索 - `{"column_name_rest": {"RANGE": {"START": "min", "END": "max"}}}`

### Examples
```json
// Exact match
{"operation_name": {"NORMAL": "operation name"}}

// Multiple values
{"status": {"LIST": ["Completed", "Executing"]}}

// Empty = get all records
{}
```
