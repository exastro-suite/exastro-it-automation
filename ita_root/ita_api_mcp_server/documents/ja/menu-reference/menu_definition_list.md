# パラメータシート/データシートの廃止（削除）手順（重要）
## 削除概要
パラメーターシートを廃止（論理削除）するにあたって:
1. `menu_definition_list`のレコードは廃止できないのでそのままとする
   (`menu_definition_list`の定義一覧は「作成用の設定情報」に過ぎないため、残置しても影響はない)
2. `role_menu_link_list`(ロールメニュー紐付)のレコードについて廃止対象とする
3. `subst_value_auto_reg_setting_<driver>`(代入値自動登録設定)のレコードについて廃止対象とする
4. `menu_list`（メニュー管理）のレコードについて廃止対象とする

### 廃止対象となるメニュー実体（見落とし注意）
- `subst_value_auto_reg_setting_<driver>`(代入値自動登録設定)
  廃止対象:
    - `subst_value_auto_reg_setting_<driver>`の`menu_name_rest`が廃止対象のパラメータシートの`menu_name_rest` + `_subst`と一致するレコード

- `role_menu_link_list`(ロールメニュー紐付管理)
  1件のパラメータシートは、作成対象により複数のメニュー実体 *操作可能ロールで複数行`role_menu_link_list`に登録されるので全てのレコードを廃止する
  ただし、パラメーターシートタイプによって存在しないレコードもあるので注意
  廃止対象:
    - `role_menu_link_list`の`menu_name`が廃止対象のパラメータシートの`:` + `menu_name_en`で後方一致するレコード

- `menu_list`（メニュー管理）
  1件のパラメータシートは、作成対象により複数のメニュー実体に分かれて `menu_list` に登録されるので全てのレコードを廃止する
  ただし、パラメーターシートタイプによって存在しないレコードもあるので注意
  廃止対象:
    - `menu_list`の`menu_name_rest`が廃止対象のパラメータシートの`menu_name_rest`と一致するレコード
    - `menu_list`の`menu_name_rest`が廃止対象のパラメータシートの`menu_name_rest` + `_subst`と一致するレコード
    - `menu_list`の`menu_name_rest`が廃止対象のパラメータシートの`menu_name_rest` + `_ref`と一致するレコード

### 廃止手順（ツール操作）
- `role_menu_link_list`(ロールメニュー紐付管理)
  1. `menu-filter`（menu: "role_menu_link_list"）を`{discard: {NORMAL: "0"}, menu_name: {NORMAL: `:` + `menu_name_en`}}`で検索する。
  2. 検索結果からmenu_nameが後方一致で`:` + `menu_name_en`のレコードを対象として絞り込む
  3. `maintenance-all`（menu: "role_menu_link_list"）で絞り込んだレコードを type="Discard"（楽観ロックのため last_update_date_time 必須）。

- `subst_value_auto_reg_setting_<driver>`(代入値自動登録設定)
  1. `menu-filter`（menu: "subst_value_auto_reg_setting_<driver>"）でレコードを取得（最新の last_update_date_time を取得）。
  2. `menu_name_rest`が廃止対象のパラメータシートの`menu_name_rest` + `_subst`と一致するレコードで絞り込み
  3. `maintenance-all`（menu: "subst_value_auto_reg_setting_<driver>"）で絞り込んだレコードを type="Discard"（楽観ロックのため last_update_date_time 必須）。

- `menu_list`（メニュー管理）
  1. `menu-filter`（menu: "menu_list"）で対象の3メニュー実体を取得（最新の last_update_date_time を取得）。
  2. `maintenance-all`（menu: "menu_list"）で3件を type="Discard"（楽観ロックのため last_update_date_time 必須）。
  3. 併せて、そのパラメータシートに紐づく入力データ・Movement紐付・代入値自動登録設定なども子→親の順で廃止する。

