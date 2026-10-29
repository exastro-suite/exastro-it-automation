# SubValueAutoReg.getCMDBdata 全件実行 トレーサビリティ

自動生成物。`python3 -m tests...subvalue_autoreg_exhaustive --all` で再生成する。

- 実現可能な組合せ: **431,424 件**
- 相異なる出力: **1,224 通り**
- パターン表のどの行にも当たらない項番: **0 件**

## 1. 項番の定義

軸を下表の順に並べた mixed-radix（右端が最も速く回る）で全直積を列挙し、
軸間制約を満たすものだけに 1 から連番を振る。
**軸の順序・軸値の並びを変えると項番は総入れ替えになる**ので、
`AXIS_ORDER` と各軸の値定義は不変とみなして扱う。

| # | 軸キー | 軸名 | 値数 | 値 |
|---|---|---|---:|---|
| 1 | `route` | 経路 | 2 | `all`, `parameter_sheet` |
| 2 | `bundle` | バンドル（パラメータシート形態） | 2 | `no`, `yes` |
| 3 | `hostgroup` | ホストグループ | 2 | `no`, `yes` |
| 4 | `record_count` | レコード数 | 6 | `0`, `1`, `10_1host_nope`, `10_1host_1ope`, `10_nhost_1ope`, `10_nhost_nope` |
| 5 | `record_validity` | レコード有効性 | 3 | `valid`, `disused_ope`, `disused_host` |
| 6 | `column_value` | カラム具体値 | 21 | `present`, `none`, `tpf`, `cpf`, `disused_tpf`, `disused_cpf`, `fileupload_exists`, `fileupload_missing`, `item_none`, `name_tpf`, `name_cpf`, `ref_id`, `ref_id_disused`, `ps_ref`, `ps_ref_fileupload`, `ps_ref_pw`, `ps_ref_pw_disused`, `ps_ref_disused`, `ps_ref_datetime`, `col_deleted`, `row_missing` |
| 7 | `reg_type` | 登録方式 | 2 | `Value`, `Key` |
| 8 | `assign_seq` | 代入順序（設定側 ASSIGN_SEQ） | 2 | `none`, `value` |
| 9 | `null_setting` | NULL連携（設定） | 3 | `TRUE`, `FALSE`, `None` |
| 10 | `null_if` | NULL連携（IF情報） | 2 | `TRUE`, `FALSE` |
| 11 | `driver` | ドライバ | 3 | `L`, `P`, `R` |
| 12 | `var_type` | 変数タイプ / メンバ変数 | 3 | `STD`, `LIST`, `M_ARRAY` |
| 13 | `locale` | ロケール | 2 | `ja`, `en` |

## 2. パターン表のケースID -> 項番

| ケースID | 概要 | 該当件数 | 代表項番 | 代表項番の軸値 |
|---|---|---:|---:|---|
| 1-1 | 有効 | 20,160 | 5041 | all/no/no/1/valid/present/Value/none/TRUE/TRUE/L/STD/ja |
| 1-2 | 廃止オペ | 137,088 | 10081 | all/no/no/1/disused_ope/present/Value/none/TRUE/TRUE/L/STD/ja |
| 1-3 | 廃止ホスト | 137,088 | 15121 | all/no/no/1/disused_host/present/Value/none/TRUE/TRUE/L/STD/ja |
| 1-4 | ホストID未登録 | — | — | 全件モデルでは表現不可（§3参照） |
| 2-1 | 0件 | 20,160 | 1 | all/no/no/0/valid/present/Value/none/TRUE/TRUE/L/STD/ja |
| 2-2 | 1件 | 60,480 | 5041 | all/no/no/1/valid/present/Value/none/TRUE/TRUE/L/STD/ja |
| 2-3 | 10件(同一ホスト・複数オペ) | 60,480 | 20161 | all/no/no/10_1host_nope/valid/present/Value/none/TRUE/TRUE/L/STD/ja |
| 2-4 | 10件(同一ホスト・同一オペ) | 48,384 | 35281 | all/no/no/10_1host_1ope/valid/present/Value/none/TRUE/TRUE/L/STD/ja |
| 2-5 | 10件(複数ホスト・同一オペ) | 120,960 | 47377 | all/no/no/10_nhost_1ope/valid/present/Value/none/TRUE/TRUE/L/STD/ja |
| 2-6 | 10件(複数ホスト・複数オペ) | 120,960 | 62497 | all/no/no/10_nhost_nope/valid/present/Value/none/TRUE/TRUE/L/STD/ja |
| 3-1 | 有(通常文字列) | 20,544 | 1 | all/no/no/0/valid/present/Value/none/TRUE/TRUE/L/STD/ja |
| 3-2 | TPF(id) | 20,544 | 481 | all/no/no/0/valid/tpf/Value/none/TRUE/TRUE/L/STD/ja |
| 3-3 | CPF(id) | 20,544 | 721 | all/no/no/0/valid/cpf/Value/none/TRUE/TRUE/L/STD/ja |
| 3-4 | 廃止TPF(id) | 20,544 | 961 | all/no/no/0/valid/disused_tpf/Value/none/TRUE/TRUE/L/STD/ja |
| 3-5 | 廃止CPF(id) | 20,544 | 1201 | all/no/no/0/valid/disused_cpf/Value/none/TRUE/TRUE/L/STD/ja |
| 3-6 | FileUploadColumn(ファイル有) | 20,544 | 1441 | all/no/no/0/valid/fileupload_exists/Value/none/TRUE/TRUE/L/STD/ja |
| 3-7 | FileUpload(ファイル無) | 20,544 | 1681 | all/no/no/0/valid/fileupload_missing/Value/none/TRUE/TRUE/L/STD/ja |
| 3-8 | 項目なし | 20,544 | 1921 | all/no/no/0/valid/item_none/Value/none/TRUE/TRUE/L/STD/ja |
| 3-9 | TPF(名前指定) | 20,544 | 2161 | all/no/no/0/valid/name_tpf/Value/none/TRUE/TRUE/L/STD/ja |
| 3-10 | CPF(名前指定)・廃止 | 20,544 | 2401 | all/no/no/0/valid/name_cpf/Value/none/TRUE/TRUE/L/STD/ja |
| 3-11 | ID指定(CPF/TPF以外) | 20,544 | 2641 | all/no/no/0/valid/ref_id/Value/none/TRUE/TRUE/L/STD/ja |
| 3-12 | ID指定(CPF/TPF以外)・廃止 | 20,544 | 2881 | all/no/no/0/valid/ref_id_disused/Value/none/TRUE/TRUE/L/STD/ja |
| 3-13 | パラメータシート参照 | 20,544 | 3121 | all/no/no/0/valid/ps_ref/Value/none/TRUE/TRUE/L/STD/ja |
| 3-14 | パラメータシート参照(参照先=ファイルアップロード列) | 20,544 | 3361 | all/no/no/0/valid/ps_ref_fileupload/Value/none/TRUE/TRUE/L/STD/ja |
| 3-15 | パラメータシート参照(参照先=日時/日付列) | 20,544 | 4321 | all/no/no/0/valid/ps_ref_datetime/Value/none/TRUE/TRUE/L/STD/ja |
| 3-16 | パラメータシート参照(パスワード列) | 20,544 | 3601 | all/no/no/0/valid/ps_ref_pw/Value/none/TRUE/TRUE/L/STD/ja |
| 3-17 | パラメータシート参照(パスワード列)・廃止 | 20,544 | 3841 | all/no/no/0/valid/ps_ref_pw_disused/Value/none/TRUE/TRUE/L/STD/ja |
| 3-18 | パラメータシート参照・廃止 | 20,544 | 4081 | all/no/no/0/valid/ps_ref_disused/Value/none/TRUE/TRUE/L/STD/ja |
| 3-19 | 項目削除 | 20,544 | 4561 | all/no/no/0/valid/col_deleted/Value/none/TRUE/TRUE/L/STD/ja |
| 3-20 | レコードが具体値取得結果に無い | 20,544 | 4801 | all/no/no/0/valid/row_missing/Value/none/TRUE/TRUE/L/STD/ja |
| 4-1 | Value | 215,712 | 1 | all/no/no/0/valid/present/Value/none/TRUE/TRUE/L/STD/ja |
| 4-2 | Key | 215,712 | 121 | all/no/no/0/valid/present/Key/none/TRUE/TRUE/L/STD/ja |
| 4-3 | Key(具体値None) | 10,272 | 361 | all/no/no/0/valid/none/Key/none/TRUE/TRUE/L/STD/ja |
| 4b-1 | Key × FileUpload | 30,816 | 1561 | all/no/no/0/valid/fileupload_exists/Key/none/TRUE/TRUE/L/STD/ja |
| 5-1 | 無(横メニュー) | 215,712 | 1 | all/no/no/0/valid/present/Value/none/TRUE/TRUE/L/STD/ja |
| 5-2 | 有(縦メニュー・一致) | 215,712 | 107857 | all/yes/no/0/valid/present/Value/none/TRUE/TRUE/L/STD/ja |
| 5-3 | 有(縦メニュー・不一致) | — | — | 全件モデルでは表現不可（§3参照） |
| 5b-1 | 代入順序 無 | 215,712 | 1 | all/no/no/0/valid/present/Value/none/TRUE/TRUE/L/STD/ja |
| 5b-2 | 代入順序 有 | 215,712 | 61 | all/no/no/0/valid/present/Value/value/TRUE/TRUE/L/STD/ja |
| 6-1 | 設定TRUE / IF TRUE | 3,424 | 241 | all/no/no/0/valid/none/Value/none/TRUE/TRUE/L/STD/ja |
| 6-2 | 設定TRUE / IF FALSE | 3,424 | 251 | all/no/no/0/valid/none/Value/none/TRUE/FALSE/L/STD/ja |
| 6-3 | 設定FALSE / IF TRUE | 3,424 | 261 | all/no/no/0/valid/none/Value/none/FALSE/TRUE/L/STD/ja |
| 6-4 | 設定FALSE / IF FALSE | 3,424 | 271 | all/no/no/0/valid/none/Value/none/FALSE/FALSE/L/STD/ja |
| 6-5 | 設定None / IF TRUE | 3,424 | 281 | all/no/no/0/valid/none/Value/none/None/TRUE/L/STD/ja |
| 6-6 | 設定None / IF FALSE | 3,424 | 291 | all/no/no/0/valid/none/Value/none/None/FALSE/L/STD/ja |
| 6-7 | NULL連携TRUE × メンバ変数(多次元) | 1,216 | 249 | all/no/no/0/valid/none/Value/none/TRUE/TRUE/R/M_ARRAY/ja |
| 6-8 | NULL連携FALSE × メンバ変数(多次元) | 1,216 | 269 | all/no/no/0/valid/none/Value/none/FALSE/TRUE/R/M_ARRAY/ja |
| 7-1 | L / STD | 88,704 | 1 | all/no/no/0/valid/present/Value/none/TRUE/TRUE/L/STD/ja |
| 7-2 | P / STD | 88,704 | 3 | all/no/no/0/valid/present/Value/none/TRUE/TRUE/P/STD/ja |
| 7-3 | R / STD | 88,704 | 5 | all/no/no/0/valid/present/Value/none/TRUE/TRUE/R/STD/ja |
| 7-4 | R / LIST | 88,704 | 7 | all/no/no/0/valid/present/Value/none/TRUE/TRUE/R/LIST/ja |
| 7-5 | R / M_ARRAY | 76,608 | 9 | all/no/no/0/valid/present/Value/none/TRUE/TRUE/R/M_ARRAY/ja |
| 8-1 | all | 215,712 | 1 | all/no/no/0/valid/present/Value/none/TRUE/TRUE/L/STD/ja |
| 8-2 | parameter_sheet | 215,712 | 215713 | parameter_sheet/no/no/0/valid/present/Value/none/TRUE/TRUE/L/STD/ja |
| 9-1 | 一般変数レコード(16キー) | 83,328 | 5041 | all/no/no/1/valid/present/Value/none/TRUE/TRUE/L/STD/ja |
| 9-2 | 多次元レコード(16キー) | 8,064 | 5049 | all/no/no/1/valid/present/Value/none/TRUE/TRUE/R/M_ARRAY/ja |
| 9-3 | skip レコード(7キー) | 6,528 | 6961 | all/no/no/1/valid/item_none/Value/none/TRUE/TRUE/L/STD/ja |
| 10-1 | 同一ホスト・同一オペ×10 で行ごとの値を保持 | 4,992 | 35281 | all/no/no/10_1host_1ope/valid/present/Value/none/TRUE/TRUE/L/STD/ja |
| 10-2 | 複数ホスト・同一オペ×10 で行ごとの値を保持 | 9,984 | 47377 | all/no/no/10_nhost_1ope/valid/present/Value/none/TRUE/TRUE/L/STD/ja |
| 10-3 | 同一ホスト・複数オペ×10 で行ごとの値を保持 | 4,992 | 20161 | all/no/no/10_1host_nope/valid/present/Value/none/TRUE/TRUE/L/STD/ja |
| 10-4 | 縦メニュー: INPUT_ORDER 1/2/3 × 設定 1/2/3 の総当たり | — | — | 全件モデルでは表現不可（§3参照） |
| 10-5 | 2レコードのうち片方だけ具体値取得結果に不在 | — | — | 全件モデルでは表現不可（§3参照） |
| 10-6 | 3レコードの COL_ROW_ID(既知の不具合・xfail) | — | — | 全件モデルでは表現不可（§3参照） |
| 11-1 | 別メニューの2テーブル | — | — | 全件モデルでは表現不可（§3参照） |
| 11-2 | 1テーブル目が0件 / 2テーブル目に1件 | — | — | 全件モデルでは表現不可（§3参照） |
| 11-3 | 2テーブルが同一の紐付メニューを参照 | — | — | 全件モデルでは表現不可（§3参照） |
| 12-1 | 2000レコード × 設定1件 | — | — | 全件モデルでは表現不可（§3参照） |
| 12-2 | 2000レコード × 設定25件 | — | — | 全件モデルでは表現不可（§3参照） |
| 12-3 | 50レコード × 設定4件 の辞書引き線形性 | — | — | 全件モデルでは表現不可（§3参照） |

## 3. 全件モデルで表現できない/部分的にしか当たらない行

| ケースID | 概要 | 状態 | 理由 |
|---|---|---|---|
| 1-4 | ホストID未登録 | 表現不可 | HOST_ID が dict_hostinfo に無い状態は現実装の上流では起こらない(※2-2)ためパターン表・軸値の双方から削除した。MSG-10361 の分岐と判定順序は既存 pytest の防御的テストにのみ置く |
| 5-3 | 有(縦メニュー・不一致) | 表現不可 | バンドル軸に「不一致」の値が無い(INPUT_ORDER と COLUMN_ASSIGN_SEQ は常に一致させている) |
| 10-4 | 縦メニュー: INPUT_ORDER 1/2/3 × 設定 1/2/3 の総当たり | 表現不可 | 設定を複数件持つ必要がある(全件モデルは設定1件固定) |
| 10-5 | 2レコードのうち片方だけ具体値取得結果に不在 | 表現不可 | レコードごとに有効性/具体値の有無を変える必要がある(全件モデルは全レコード一律) |
| 10-6 | 3レコードの COL_ROW_ID(既知の不具合・xfail) | 表現不可 | 全件実行は現実装をゴールデンに固定するので「あるべき姿」の期待値を持てない |
| 11-1 | 別メニューの2テーブル | 表現不可 | 複数テーブルは軸になっていない(全件モデルは1テーブル固定) |
| 11-2 | 1テーブル目が0件 / 2テーブル目に1件 | 表現不可 | 同上 |
| 11-3 | 2テーブルが同一の紐付メニューを参照 | 表現不可 | 同上 |
| 12-1 | 2000レコード × 設定1件 | 表現不可 | 性能軸(2000件)は機能ケースの直積に入れていない |
| 12-2 | 2000レコード × 設定25件 | 表現不可 | 同上(設定件数も性能専用軸) |
| 12-3 | 50レコード × 設定4件 の辞書引き線形性 | 表現不可 | 同上 |
| 3-14 | パラメータシート参照(参照先=ファイルアップロード列) | 部分的 | ファイル有(os.path.exists=True)側のみ。ファイル無側は軸の値になっていない |
| 5-2 | 有(縦メニュー・一致) | 部分的 | 表は「レコード2件 × 設定2件」で対応関係まで見る行。全件モデルは設定1件固定なので、「縦で突合が成立する形態」までしか当たらない |

※ここに挙げた行は `test_SubValueAutoReg_getCMDBdata.py`（手書き期待値・122項目）側でカバーする。全件実行と既存 pytest は互いの穴を埋める2枚構成。

## 4. どのケースIDにも当たらない項番

**0件**。実現可能な 431,424 件すべてがパターン表のいずれかの行に該当する。

ただしこれは表が強いという意味ではない。パターン表の各行は基本的に
「ある1軸がある値である」という主張なので、行の和集合は当然に全件を覆う。
表が言えていないのは**軸の組合せ**であり、その差は §7 で数える。

## 5. 相異なる出力の一覧（先頭50件）

全 1,224 通りは `subvalue_autoreg_getCMDBdata_exhaustive_golden.txt` の `[distinct]` 節を参照。

| 出力id | 初出項番 | 要約 |
|---:|---:|---|
| 1 | 1 | vars=0 array=0 status=- logs=MSG-10368,MSG-10806 |
| 2 | 5041 | vars=1 array=0 status=True logs=MSG-10806 first={REG_TYPE='Value' VARS_ENTRY='value1' COL_CLASS='SingleTextColumn' COL_FILEUPLOAD_PATH='' SENSITIVE_FLAG='0'} |
| 3 | 5047 | vars=1 array=0 status=True logs=MSG-10806 first={REG_TYPE='Value' VARS_ENTRY='value1' COL_CLASS='SingleTextColumn' COL_FILEUPLOAD_PATH='' SENSITIVE_FLAG='0'} |
| 4 | 5049 | vars=0 array=1 status=True logs=MSG-10806 first={REG_TYPE='Value' VARS_ENTRY='value1' COL_CLASS='SingleTextColumn' COL_FILEUPLOAD_PATH='' SENSITIVE_FLAG='0'} |
| 5 | 5101 | vars=1 array=0 status=True logs=MSG-10806 first={REG_TYPE='Value' VARS_ENTRY='value1' COL_CLASS='SingleTextColumn' COL_FILEUPLOAD_PATH='' SENSITIVE_FLAG='0'} |
| 6 | 5107 | vars=1 array=0 status=True logs=MSG-10806 first={REG_TYPE='Value' VARS_ENTRY='value1' COL_CLASS='SingleTextColumn' COL_FILEUPLOAD_PATH='' SENSITIVE_FLAG='0'} |
| 7 | 5109 | vars=0 array=1 status=True logs=MSG-10806 first={REG_TYPE='Value' VARS_ENTRY='value1' COL_CLASS='SingleTextColumn' COL_FILEUPLOAD_PATH='' SENSITIVE_FLAG='0'} |
| 8 | 5161 | vars=1 array=0 status=True logs=MSG-10806 first={REG_TYPE='Key' VARS_ENTRY='カラムA' COL_CLASS='SingleTextColumn' COL_FILEUPLOAD_PATH='' SENSITIVE_FLAG='0'} |
| 9 | 5162 | vars=1 array=0 status=True logs=MSG-10806 first={REG_TYPE='Key' VARS_ENTRY='ColumnA' COL_CLASS='SingleTextColumn' COL_FILEUPLOAD_PATH='' SENSITIVE_FLAG='0'} |
| 10 | 5169 | vars=1 array=0 status=True logs=MSG-10806 first={REG_TYPE='Key' VARS_ENTRY='カラムA' COL_CLASS='SingleTextColumn' COL_FILEUPLOAD_PATH='' SENSITIVE_FLAG='0'} |
| 11 | 5170 | vars=1 array=0 status=True logs=MSG-10806 first={REG_TYPE='Key' VARS_ENTRY='ColumnA' COL_CLASS='SingleTextColumn' COL_FILEUPLOAD_PATH='' SENSITIVE_FLAG='0'} |
| 12 | 5221 | vars=1 array=0 status=True logs=MSG-10806 first={REG_TYPE='Key' VARS_ENTRY='カラムA' COL_CLASS='SingleTextColumn' COL_FILEUPLOAD_PATH='' SENSITIVE_FLAG='0'} |
| 13 | 5222 | vars=1 array=0 status=True logs=MSG-10806 first={REG_TYPE='Key' VARS_ENTRY='ColumnA' COL_CLASS='SingleTextColumn' COL_FILEUPLOAD_PATH='' SENSITIVE_FLAG='0'} |
| 14 | 5229 | vars=1 array=0 status=True logs=MSG-10806 first={REG_TYPE='Key' VARS_ENTRY='カラムA' COL_CLASS='SingleTextColumn' COL_FILEUPLOAD_PATH='' SENSITIVE_FLAG='0'} |
| 15 | 5230 | vars=1 array=0 status=True logs=MSG-10806 first={REG_TYPE='Key' VARS_ENTRY='ColumnA' COL_CLASS='SingleTextColumn' COL_FILEUPLOAD_PATH='' SENSITIVE_FLAG='0'} |
| 16 | 5281 | vars=1 array=0 status=True logs=MSG-10806 first={REG_TYPE='Value' VARS_ENTRY=None COL_CLASS='SingleTextColumn' COL_FILEUPLOAD_PATH='' SENSITIVE_FLAG='0'} |
| 17 | 5287 | vars=1 array=0 status=True logs=MSG-10806 first={REG_TYPE='Value' VARS_ENTRY=None COL_CLASS='SingleTextColumn' COL_FILEUPLOAD_PATH='' SENSITIVE_FLAG='0'} |
| 18 | 5289 | vars=0 array=1 status=True logs=MSG-10806 first={REG_TYPE='Value' VARS_ENTRY=None COL_CLASS='SingleTextColumn' COL_FILEUPLOAD_PATH='' SENSITIVE_FLAG='0'} |
| 19 | 5301 | vars=0 array=0 status=- logs=MSG-10375,MSG-10806 |
| 20 | 5341 | vars=1 array=0 status=True logs=MSG-10806 first={REG_TYPE='Value' VARS_ENTRY=None COL_CLASS='SingleTextColumn' COL_FILEUPLOAD_PATH='' SENSITIVE_FLAG='0'} |
| 21 | 5347 | vars=1 array=0 status=True logs=MSG-10806 first={REG_TYPE='Value' VARS_ENTRY=None COL_CLASS='SingleTextColumn' COL_FILEUPLOAD_PATH='' SENSITIVE_FLAG='0'} |
| 22 | 5349 | vars=0 array=1 status=True logs=MSG-10806 first={REG_TYPE='Value' VARS_ENTRY=None COL_CLASS='SingleTextColumn' COL_FILEUPLOAD_PATH='' SENSITIVE_FLAG='0'} |
| 23 | 5401 | vars=0 array=0 status=- logs=MSG-10377,MSG-10806 |
| 24 | 5521 | vars=1 array=0 status=True logs=MSG-10806 first={REG_TYPE='Value' VARS_ENTRY="'{{ TPF_X }}'" COL_CLASS='SingleTextColumn' COL_FILEUPLOAD_PATH='' SENSITIVE_FLAG='0'} |
| 25 | 5527 | vars=1 array=0 status=True logs=MSG-10806 first={REG_TYPE='Value' VARS_ENTRY="'{{ TPF_X }}'" COL_CLASS='SingleTextColumn' COL_FILEUPLOAD_PATH='' SENSITIVE_FLAG='0'} |
| 26 | 5529 | vars=0 array=1 status=True logs=MSG-10806 first={REG_TYPE='Value' VARS_ENTRY="'{{ TPF_X }}'" COL_CLASS='SingleTextColumn' COL_FILEUPLOAD_PATH='' SENSITIVE_FLAG='0'} |
| 27 | 5581 | vars=1 array=0 status=True logs=MSG-10806 first={REG_TYPE='Value' VARS_ENTRY="'{{ TPF_X }}'" COL_CLASS='SingleTextColumn' COL_FILEUPLOAD_PATH='' SENSITIVE_FLAG='0'} |
| 28 | 5587 | vars=1 array=0 status=True logs=MSG-10806 first={REG_TYPE='Value' VARS_ENTRY="'{{ TPF_X }}'" COL_CLASS='SingleTextColumn' COL_FILEUPLOAD_PATH='' SENSITIVE_FLAG='0'} |
| 29 | 5589 | vars=0 array=1 status=True logs=MSG-10806 first={REG_TYPE='Value' VARS_ENTRY="'{{ TPF_X }}'" COL_CLASS='SingleTextColumn' COL_FILEUPLOAD_PATH='' SENSITIVE_FLAG='0'} |
| 30 | 5761 | vars=1 array=0 status=True logs=MSG-10806 first={REG_TYPE='Value' VARS_ENTRY="'{{ CPF_X }}'" COL_CLASS='SingleTextColumn' COL_FILEUPLOAD_PATH='' SENSITIVE_FLAG='0'} |
| 31 | 5767 | vars=1 array=0 status=True logs=MSG-10806 first={REG_TYPE='Value' VARS_ENTRY="'{{ CPF_X }}'" COL_CLASS='SingleTextColumn' COL_FILEUPLOAD_PATH='' SENSITIVE_FLAG='0'} |
| 32 | 5769 | vars=0 array=1 status=True logs=MSG-10806 first={REG_TYPE='Value' VARS_ENTRY="'{{ CPF_X }}'" COL_CLASS='SingleTextColumn' COL_FILEUPLOAD_PATH='' SENSITIVE_FLAG='0'} |
| 33 | 5821 | vars=1 array=0 status=True logs=MSG-10806 first={REG_TYPE='Value' VARS_ENTRY="'{{ CPF_X }}'" COL_CLASS='SingleTextColumn' COL_FILEUPLOAD_PATH='' SENSITIVE_FLAG='0'} |
| 34 | 5827 | vars=1 array=0 status=True logs=MSG-10806 first={REG_TYPE='Value' VARS_ENTRY="'{{ CPF_X }}'" COL_CLASS='SingleTextColumn' COL_FILEUPLOAD_PATH='' SENSITIVE_FLAG='0'} |
| 35 | 5829 | vars=0 array=1 status=True logs=MSG-10806 first={REG_TYPE='Value' VARS_ENTRY="'{{ CPF_X }}'" COL_CLASS='SingleTextColumn' COL_FILEUPLOAD_PATH='' SENSITIVE_FLAG='0'} |
| 36 | 6001 | vars=0 array=0 status=- logs=MSG-10806 |
| 37 | 6481 | vars=1 array=0 status=True logs=MSG-10806 first={REG_TYPE='Value' VARS_ENTRY='file.txt' COL_CLASS='FileUploadColumn' COL_FILEUPLOAD_PATH='/exhaustive-storage/test_org_id/test_workspace_id/uploadfiles/out-menu-1/column_a/row-001/file.txt' SENSITIVE_FLAG='0'} |
| 38 | 6487 | vars=1 array=0 status=True logs=MSG-10806 first={REG_TYPE='Value' VARS_ENTRY='file.txt' COL_CLASS='FileUploadColumn' COL_FILEUPLOAD_PATH='/exhaustive-storage/test_org_id/test_workspace_id/uploadfiles/out-menu-1/column_a/row-001/file.txt' SENSITIVE_FLAG='0'} |
| 39 | 6489 | vars=0 array=1 status=True logs=MSG-10806 first={REG_TYPE='Value' VARS_ENTRY='file.txt' COL_CLASS='FileUploadColumn' COL_FILEUPLOAD_PATH='/exhaustive-storage/test_org_id/test_workspace_id/uploadfiles/out-menu-1/column_a/row-001/file.txt' SENSITIVE_FLAG='0'} |
| 40 | 6541 | vars=1 array=0 status=True logs=MSG-10806 first={REG_TYPE='Value' VARS_ENTRY='file.txt' COL_CLASS='FileUploadColumn' COL_FILEUPLOAD_PATH='/exhaustive-storage/test_org_id/test_workspace_id/uploadfiles/out-menu-1/column_a/row-001/file.txt' SENSITIVE_FLAG='0'} |
| 41 | 6547 | vars=1 array=0 status=True logs=MSG-10806 first={REG_TYPE='Value' VARS_ENTRY='file.txt' COL_CLASS='FileUploadColumn' COL_FILEUPLOAD_PATH='/exhaustive-storage/test_org_id/test_workspace_id/uploadfiles/out-menu-1/column_a/row-001/file.txt' SENSITIVE_FLAG='0'} |
| 42 | 6549 | vars=0 array=1 status=True logs=MSG-10806 first={REG_TYPE='Value' VARS_ENTRY='file.txt' COL_CLASS='FileUploadColumn' COL_FILEUPLOAD_PATH='/exhaustive-storage/test_org_id/test_workspace_id/uploadfiles/out-menu-1/column_a/row-001/file.txt' SENSITIVE_FLAG='0'} |
| 43 | 6601 | vars=1 array=0 status=True logs=MSG-10806 first={REG_TYPE='Key' VARS_ENTRY='カラムA' COL_CLASS='FileUploadColumn' COL_FILEUPLOAD_PATH='' SENSITIVE_FLAG='0'} |
| 44 | 6602 | vars=1 array=0 status=True logs=MSG-10806 first={REG_TYPE='Key' VARS_ENTRY='ColumnA' COL_CLASS='FileUploadColumn' COL_FILEUPLOAD_PATH='' SENSITIVE_FLAG='0'} |
| 45 | 6609 | vars=1 array=0 status=True logs=MSG-10806 first={REG_TYPE='Key' VARS_ENTRY='カラムA' COL_CLASS='FileUploadColumn' COL_FILEUPLOAD_PATH='' SENSITIVE_FLAG='0'} |
| 46 | 6610 | vars=1 array=0 status=True logs=MSG-10806 first={REG_TYPE='Key' VARS_ENTRY='ColumnA' COL_CLASS='FileUploadColumn' COL_FILEUPLOAD_PATH='' SENSITIVE_FLAG='0'} |
| 47 | 6661 | vars=1 array=0 status=True logs=MSG-10806 first={REG_TYPE='Key' VARS_ENTRY='カラムA' COL_CLASS='FileUploadColumn' COL_FILEUPLOAD_PATH='' SENSITIVE_FLAG='0'} |
| 48 | 6662 | vars=1 array=0 status=True logs=MSG-10806 first={REG_TYPE='Key' VARS_ENTRY='ColumnA' COL_CLASS='FileUploadColumn' COL_FILEUPLOAD_PATH='' SENSITIVE_FLAG='0'} |
| 49 | 6669 | vars=1 array=0 status=True logs=MSG-10806 first={REG_TYPE='Key' VARS_ENTRY='カラムA' COL_CLASS='FileUploadColumn' COL_FILEUPLOAD_PATH='' SENSITIVE_FLAG='0'} |
| 50 | 6670 | vars=1 array=0 status=True logs=MSG-10806 first={REG_TYPE='Key' VARS_ENTRY='ColumnA' COL_CLASS='FileUploadColumn' COL_FILEUPLOAD_PATH='' SENSITIVE_FLAG='0'} |

## 6. 項番から中身を引く

項番は AXIS_ORDER と各軸の値定義だけで決まるので、431,424行の一覧を
リポジトリに置く必要は無い（TSVにすると約39MB、markdownの表なら数十MBで閲覧不能）。
1件だけ引きたいときは:

```
python3 -m tests.ansible_driver_tests.ansible_driver.classes.subvalue_autoreg_exhaustive --lookup 8161
```

全件のTSVが必要なときは `--all --index` を付ける（`subvalue_autoreg_getCMDBdata_exhaustive_index.tsv` に出る）。

## 7. 1軸戦略との差（なぜ全件やるのか）

既存 pytest と同じ戦略、つまり「ベースライン値で固定して1軸だけ動かす」で
到達できる組合せは **40 件**（全 431,424 件の 0.009%）。
その 40 件が到達する出力は **30 通り**で、
全件が到達する 1,224 通りのうち **2.5%** にとどまる。

残る **1,194 通り**の出力は、2軸以上を同時に動かさないと現れない。
しかも1軸戦略の「ベースライン値」は現実装の判定順序を読んで決めた値なので、
判定順序が変わればこの 2.5% という数字自体が変わる。
全件実行はベースライン値を一切使わないので、この依存が無い。
