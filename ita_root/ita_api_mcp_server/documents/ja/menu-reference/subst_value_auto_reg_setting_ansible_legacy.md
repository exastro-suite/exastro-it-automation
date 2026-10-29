# 代入値自動登録設定(subst_value_auto_reg_setting_ansible_legacy)
## 代入値自動登録設定の変数の型について
- substitution_order を指定すると変数はリスト型（例: ["値"]）、空欄にするとスカラー（単一値）になる。
- Playbook側の変数の受け方に型を合わせること:
    - with_items 等でループする変数 → substitution_order を指定
    - copy の dest など単一値を渡す変数 → substitution_order を空欄
- `'_AnsibleTaggedList' object has no attribute ...` のエラーは、スカラー期待箇所にリスト型が渡っている兆候。substitution_order を疑う。

## column_substitution_orderの指定について
- `menu_group_menu_item`で選択したパラメータシートがバンドル形式でない場合は指定しないこと
- `menu_group_menu_item`で選択したパラメータシートに登録したレコードの代入順序`input_order`を指定します

## バンドル項目を1つのリスト変数へ連携する場合の設定件数について
- **重要**: バンドルの1つの項目に複数行（値）を入力し、それらを1つのリスト変数の
  複数要素として渡す場合、代入値自動登録設定は「行数分」のレコードが必要になる。
  1レコード = バンドルの1行分の連携であり、1レコードで複数行がまとめて連携されるわけではない。
- 具体的には、同一の `menu_group_menu_item`（From項目）× 同一の `variable_name`（To変数）に対して、
  連携したい行数だけレコードを作成し、各レコードで以下をペアで指定する:
    - `column_substitution_order`: 拾い上げるバンドル行の代入順序（input_order）
    - `substitution_order`: リスト変数における要素の並び順
- 例: バンドル項目「インストールパッケージ」に 行1=httpd(input_order=1) / 行2=unzip(input_order=2)
  を入力し、`ITA_DFLT_Install_Target_packages`（with_items でループするリスト変数）へ渡す場合、
  必要な代入値自動登録設定は2レコード:
    | From項目 | To変数 | column_substitution_order | substitution_order |
    |---|---|---|---|
    | インストールパッケージ | ITA_DFLT_Install_Target_packages | 1 | 1 |
    | インストールパッケージ | ITA_DFLT_Install_Target_packages | 2 | 2 |
- チェック観点: バンドル項目をリスト変数へ連携する際は、
  「入力予定の行数 == その変数への代入値自動登録設定レコード数」になっているか必ず確認すること。

## 【登録前チェック】バンドル行数と代入値設定件数の整合（リスト変数連携時は必須）

リスト型変数へバンドル（vertical:1）の複数行を連携する作業では、パラメータシートへ行を
登録する前に、次の手順で件数整合を検証すること。

手順:
1. 対象の代入値自動登録設定を `menu-filter`（menu: `subst_value_auto_reg_setting_ansible_legacy`）で取得する。
2. 「同一の From項目（`menu_group_menu_item`）× 同一の To変数（`variable_name`）」に
   紐づく既存レコード数を数える。
3. 突合する：「今回入力する行数（バンドルの `input_order` の件数）」
   ==「上記で数えた代入値設定レコード数」になっているか確認する。
4. 不足している場合は、不足分の代入値設定レコードを **先に追加** してから、
   パラメータシートの行を登録すること。各追加レコードでは以下をペアで指定する：
   - `column_substitution_order`: 拾い上げるバンドル行の代入順序（`input_order`）
   - `substitution_order`: リスト変数における要素の並び順
5. 突合結果（入力予定行数 / 既存設定件数 / 過不足）をユーザーへ明示してから登録・実行に進むこと。

タイミング:
- この検証は「パラメータシートへの行登録」および「Movement実行（execute-driver / dryrun-driver）」の
  **前** に必ず行うこと。

補足:
- 1レコード = バンドルの1行分の連携であり、1レコードで複数行がまとめて連携されるわけではない。
- 代入値設定が不足していると、後半の `input_order` 分が **エラーにならず静かに欠落** することがあるため、
  件数突合を省略しないこと。

---

## 症状逆引き：バンドルの一部の行だけ処理されない／後半が欠落する

- 症状: パラメータシートに N 行登録したのに、実行ログ上の `item`（with_items のループ対象）が
        N 未満しか現れない。後半の `input_order` 分が丸ごと欠落する。多くの場合エラーにならず
        静かに欠けるため気づきにくい。
- 原因: リスト変数（`substitution_order` を指定したリスト型変数）への代入値自動登録設定レコードが
        行数分そろっていない（例: 4行登録に対し設定が2件のみ → 後半2件が変数リストに載らない）。
- 確認: `menu-filter` で対象 From項目（`menu_group_menu_item`）× To変数（`variable_name`）の
        レコード数を数え、登録行数（`input_order` の件数）と一致するか突合する。
- 対処: 不足分の `(column_substitution_order, substitution_order)` レコードを追加してから再実行する。

関連キーワード: 欠落 / 後半 / 行数 / 件数 / 一致 / input_order / レコード数 / with_items / リスト変数
