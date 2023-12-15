////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Exastro IT Automation / messageid_ja.js
//
//   -----------------------------------------------------------------------------------------------
//
//   Copyright 2022 NEC Corporation
//
//   Licensed under the Apache License, Version 2.0 (the "License");
//   you may not use this file except in compliance with the License.
//   You may obtain a copy of the License at
//
//       http://www.apache.org/licenses/LICENSE-2.0
//
//   Unless required by applicable law or agreed to in writing, software
//   distributed under the License is distributed on an "AS IS" BASIS,
//   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//   See the License for the specific language governing permissions and
//   limitations under the License.
//
////////////////////////////////////////////////////////////////////////////////////////////////////

// メッセージIDの頭文字 FTE
// 標準メニュー        00001～01000
// メニュー定義・作成  01001～02000
// Conductorクラス編集 02001～03000
// Conductor作業確認   03001～04000
// 作業実行            04001～05000
// 作業状態確認        05001～06000
// 比較実行　　        06001～07000
// エクスポート/イン   07001～08000
// DashBoard           08001～09000
// Terraform          09001～10000
// UI共通              10001～11000
// パラメータ集         11001～12000
// 独自メニュー         12001～13000
// OASE                13001～14000


export function messageid_ja() {

    const message = {
        // 標準メニュー
        'FTE00001' : "フィルタ",
        'FTE00002' : "閉じる",
        'FTE00003' : "開く",
        'FTE00004' : "選択してください。",
        'FTE00005' : "作業実行",
        'FTE00006' : "ドライラン",
        'FTE00007' : "パラメータ確認",
        'FTE00008' : "登録",
        'FTE00009' : "編集",
        'FTE00010' : "このメニューは閲覧のみ可能です。",
        'FTE00011' : "編集確認",
        'FTE00012' : "追加",
        'FTE00013' : "複製",
        'FTE00014' : "削除",
        'FTE00015' : "廃止",
        'FTE00016' : "復活",
        'FTE00017' : "編集キャンセル",
        'FTE00018' : "キャンセル確認",
        'FTE00019' : "編集中のデータがありますが破棄しますか？",
        'FTE00020' : "破棄する",
        'FTE00021' : "編集に戻る",
        'FTE00022' : "編集反映",
        'FTE00023' : "登録・編集に戻る",
        'FTE00024' : "変更前",
        'FTE00025' : "非表示",
        'FTE00026' : "表示",
        'FTE00027' : "履歴表示",
        'FTE00028' : "履歴リセット",
        'FTE00029' : "対象の",
        'FTE00030' : "を入力し、",
        'FTE00031' : "履歴表示を押下してください。",
        'FTE00032' : "選択",
        'FTE00033' : "区分",
        'FTE00034' : "内容",
        'FTE00035' : "履歴通番",
        'FTE00036' : "変更日時",
        'FTE00037' : "必須",
        'FTE00038' : "廃止",
        'FTE00039' : "プルダウン検索",
        'FTE00040' : "全レコード",
        'FTE00041' : "廃止含まず",
        'FTE00042' : "廃止のみ",
        'FTE00043' : "フィルタ",
        'FTE00044' : "フィルタクリア",
        'FTE00045' : "オートフィルタ",
        'FTE00046' : "Excelダウンロード",
        'FTE00047' : "JSONダウンロード",
        'FTE00048' : "Excel出力最大行数",
        'FTE00049' : "行",
        'FTE00050' : "を超過しているためダウンロードできません。",
        'FTE00051' : "オペレーション",
        'FTE00052' : "パスワード入力",
        'FTE00053' : "入力済みパスワードの削除",
        'FTE00054' : "表示できる内容がありません。",
        'FTE00055' : "初期フィルタがオフです。",
        'FTE00056' : "表示するにはフィルタしてください。",
        'FTE00057' : "履歴",
        'FTE00058' : "フィルタ結果件数",
        'FTE00059' : "0 件",
        'FTE00060' : "1ページに表示する件数",
        'FTE00061' : "ページ",
        'FTE00062' : "編集件数",
        'FTE00063' : " 件",
        'FTE00064' : "共通",
        'FTE00065' : "バリデーションエラー",
        'FTE00066' : function( result, limit ){ return `表示前確認件数を超えていますが、表示してもよろしいですか?\n（表示前確認件数${limit}件、レコード件数${result}件）`},
        'FTE00067' : function( result, limit ){ return `表示最大件数を超えています。\nフィルタ条件で絞り込んで下さい。\n（表示最大件数${limit}件、レコード件数${result}件）`},
        'FTE00068' : "バリデーションエラーです。",
        'FTE00069' : "登録",
        'FTE00070' : "エラー列",
        'FTE00071' : "エラー内容",
        'FTE00072' : "登録",
        'FTE00073' : "更新",
        'FTE00074' : "廃止",
        'FTE00075' : "復活",
        'FTE00076' : "ファイルクリア",
        'FTE00077' : "ようこそIT Automationへ",
        'FTE00078' : "メニュー情報",
        'FTE00079' : "メニュー情報表示",
        'FTE00080' : "作業状態確認",
        'FTE00081' : "実行ログ",
        'FTE00082' : "エラーログ",
        'FTE00083' : "一括登録確認",
        'FTE00084' : "一括登録処理中",
        'FTE00085' : function( result, limit ){ return `Excel出力行数：${result}行\n\nExcel出力最大行数（${limit}行）を超過しているためダウンロードを中止します。`},
        'FTE00086' : "テーブル設定",
        'FTE00087' : "適用",
        'FTE00088' : "キャンセル",
        'FTE00089' : "個別設定リセット",
        'FTE00090' : "項目表示方向",
        'FTE00091' : "縦",
        'FTE00092' : "横",
        'FTE00093' : "",
        'FTE00094' : "フィルタ表示位置",
        'FTE00095' : "内側",
        'FTE00096' : "外側",
        'FTE00097' : "項目メニュー表示",
        'FTE00098' : "省略",
        'FTE00099' : "表示",
        'FTE00100' : "項目表示・非表示",
        'FTE00101' : "項目の表示方向を設定します。",
        'FTE00102' : "フィルタの表示位置を設定します。項目表示方向が横の場合は外側固定になります。",
        'FTE00103' : "項目メニューの表示方法を設定します。",
        'FTE00104' : "項目ごとに表示・非表示を設定します。",
        'FTE00105' : "共通設定",
        'FTE00106' : "標準",
        'FTE00107' : "カスタム",
        'FTE00108' : "個別設定",
        'FTE00109' : "入力欄 色設定",
        'FTE00110' : "入力欄の色を設定します。",
        'FTE00111' : "任意",
        'FTE00112' : "必須",
        'FTE00113' : "入力中",
        'FTE00114' : "入力済",
        'FTE00115' : "線",
        'FTE00116' : "背景",
        'FTE00117' : "文字",
        'FTE00118' : "確認",
        'FTE00119' : function( text ){ return `『${text}』を実行してよろしいですか？`;},
        'FTE00120' : "実行中",
        'FTE00121' : "実行結果",
        'FTE00122' : "実行する",
        'FTE00123' : "キャンセル",
        'FTE00124' : ['第一','第二','第三','第四','最終'],
        'FTE00125' : ['日曜日','月曜日','火曜日','水曜日','木曜日','金曜日','土曜日'],
        'FTE00126' : "時",
        'FTE00127' : "日",
        'FTE00128' : "週",
        'FTE00129' : "月(日付指定)",
        'FTE00130' : "月(曜日指定)",
        'FTE00131' : "月末",
        'FTE00132' : "間隔",
        'FTE00133' : "時間",
        'FTE00134' : "日ごと",
        'FTE00135' : "週ごと",
        'FTE00136' : "か月ごと",
        'FTE00137' : "日にち",
        'FTE00138' : "日",
        'FTE00139' : "曜日",
        'FTE00140' : "時",
        'FTE00141' : "分",
        'FTE00142' : "スケジュール設定",
        'FTE00143' : "反映",
        'FTE00144' : "キャンセル",
        'FTE00145' : "作業期間",
        'FTE00146' : "開始",
        'FTE00147' : "終了",
        'FTE00148' : "～",
        'FTE00149' : "スケジュール",
        'FTE00150' : "作業停止期間",
        'FTE00151' : "開始",
        'FTE00152' : "終了",
        'FTE00153' : "備考",
        'FTE00154' : "作業開始日付を入力してください。",
        'FTE00155' : "開始日付",
        'FTE00156' : "終了日付",
        'FTE00157' : "作業停止開始日付",
        'FTE00158' : "作業停止終了日付",
        'FTE00159' : function( text ){ return `${text}の値が不正です(yyyy/MM/dd HH:mm:ss形式の正式な日付時間のみ有効)`;},
        'FTE00160' : "開始日付は終了日付よりも過去である必要があります。",
        'FTE00161' : "作業停止期間の開始は終了よりも過去である必要があります。",
        'FTE00162' : "作業停止期間は開始と終了両方入力する必要があります。",
        'FTE00163' : "停止期間は作業期間内である必要があります。",
        'FTE00164' : "期間",
        'FTE00165' : "秒",
        'FTE00166' : "フィルタ バリデーションエラー",
        'FTE00167' : "Plan確認",
        'FTE00168' : "更新",
        'FTE00169' : "ダウンロード",
        'FTE00170' : "閉じる",
        'FTE00171' : "名称",
        'FTE00172' : "モード",
        'FTE00173' : "テーマ",
        'FTE00174' : "ITA独自変数",
        'FTE00175' : "編集",
        'FTE00176' : "プレビュー",
        'FTE00177' : "空白",

        // パラメータシート定義・作成
        'FTE01001' : "項目",
        'FTE01002' : "グループ",
        'FTE01003' : "取り消し",
        'FTE01004' : "やり直し",
        'FTE01005' : "プレビュー",
        'FTE01006' : "ログ",
        'FTE01007' : "一覧(プレビュー)",
        'FTE01008' : "パラメータシート作成情報",
        'FTE01009' : "基本情報",
        'FTE01010' : "項番",
        'FTE01011' : "自動入力",
        'FTE01012' : "パラメータシート名",
        'FTE01013' : "パラメータシート名（REST）",
        'FTE01014' : "作成対象",
        'FTE01015' : "表示順序",
        'FTE01016' : "バンドル",
        'FTE01017' : "最終更新日時",
        'FTE01018' : "最終更新者",
        'FTE01019' : "対象メニューグループ",
        'FTE01020' : "入力用",
        'FTE01021' : "代入値自動登録用",
        'FTE01022' : "参照用",
        'FTE01023' : "一意制約(複数項目)",
        'FTE01024' : "パターン",
        'FTE01025' : "アクセス許可ロール",
        'FTE01026' : "ロール",
        'FTE01027' : "説明",
        'FTE01028' : "備考",
        'FTE01029' : "作成するパラメータシート（パラメータシート/データシート）の名称を入力します。[最大長]255バイト\n※「メインメニュー」という名称はパラメータシート名に使用できません。\n※「&#92;&#47;&#58;&#42;&#63;&#34;&#60;&#62;&#124;&#91;&#93;：￥／＊［］」の記号は使用できません。",
        'FTE01030' : "作成するパラメータシート（パラメータシート/データシート）のREST API用の名称を入力します。[最大長]240バイト\n※半角英数字と「-_」の記号のみ利用できます。",
        'FTE01031' : "プルダウンから「パラメータシート(ホスト/オペレーションあり)」「パラメータシート(オペレーションあり)」「データシート」のいずれかを選択します。",
        'FTE01032' : "メニューグループにおける表示順序を入力します。昇順に表示されます。\n※0～2147483647の整数数値が入力できます。",
        'FTE01033' : "「利用する」チェックボックスにチェックをいれた場合、バンドルに対応したパラメータシートを作成します。",
        'FTE01034' : "利用する",
        'FTE01035' : "対象メニューグループを選択",
        'FTE01036' : "一意制約(複数項目)を選択",
        'FTE01037' : "アクセス許可ロールを選択",
        'FTE01038' : "説明を入力します。[最大長]1024バイト",
        'FTE01039' : "備考を入力します。[最大長]4000バイト",
        'FTE01040' : "は必須項目です。",
        'FTE01041' : "作成",
        'FTE01042' : "編集",
        'FTE01043' : "初期化",
        'FTE01044' : "流用新規",
        'FTE01045' : "パラメータシート作成履歴",
        'FTE01046' : "作成(初期化)",
        'FTE01047' : "再読込",
        'FTE01048' : "キャンセル",
        'FTE01049' : "作成(編集)",
        'FTE01050' : "閉じる",
        'FTE01051' : "決定",
        'FTE01052' : "取消",
        'FTE01053' : "項目",
        'FTE01054' : "グループ",
        'FTE01055' : "最大バイト数",
        'FTE01056' : "正規表現",
        'FTE01057' : "最小値",
        'FTE01058' : "最大値",
        'FTE01059' : "桁数",
        'FTE01060' : "選択項目",
        'FTE01061' : "必須",
        'FTE01062' : "一意制約",
        'FTE01063' : "説明",
        'FTE01064' : "備考",
        'FTE01065' : "ホスト名",
        'FTE01066' : "オペレーション",
        'FTE01067' : "パラメータ",
        'FTE01068' : "オペレーション名",
        'FTE01069' : "基準日時",
        'FTE01070' : "実施予定日",
        'FTE01071' : "最終実行日時",
        'FTE01072' : "備考",
        'FTE01073' : "最終更新日時",
        'FTE01074' : "最終更新者",
        'FTE01075' : "オペレーション",
        'FTE01076' : "システム管理者",
        'FTE01077' : "対象メニューグループ",
        'FTE01078' : "リピートが解除されます。",
        'FTE01079' : "リピートを含む項目はコピーできません。",
        'FTE01080' : "入力用",
        'FTE01081' : "代入値<br>自動登録用",
        'FTE01082' : "参照用",
        'FTE01083' : "メニューグループ名称",
        'FTE01084' : "バンドルについて",
        'FTE01085' : "利用する",
        'FTE01086' : "ファイル最大バイト数",
        'FTE01087' : "参照項目",
        'FTE01088' : "[参照した値]",
        'FTE01089' : "参照項目を選択",
        'FTE01090' : "作成",
        'FTE01091' : "一意制約(複数項目)",
        'FTE01092' : "アクセス許可ロール",
        'FTE01093' : "参照項目",
        'FTE01094' : "初期値",
        'FTE01095' : "メニュー",
        'FTE01096' : "項目",
        'FTE01097' : "文字列(単一行)",
        'FTE01098' : "文字列(複数行)",
        'FTE01099' : "パスワード",
        'FTE01100' : "ファイル",
        'FTE01101' : "リンク",
        'FTE01102' : "[参照した値]",
        'FTE01103' : "項目を移動します。",
        'FTE01104' : "項目の名称を入力します。[最大長]255バイト\n※項目名に「/」は使用禁止です。",
        'FTE01105' : "項目の名称(REST API用)を入力します。[最大長]255バイト\n※半角英数字と「_-」のみ使用可能です。",
        'FTE01106' : "項目を削除します。",
        'FTE01107' : "項目をコピーします。",
        'FTE01108' : "リピート数を入力します。\n※2～99の整数が入力できます。",
        'FTE01109' : "入力方式をプルダウンメニューの「文字列(単一行)」、「文字列(複数行)」、\n「整数」、「小数」、「日時」、「日付」、「プルダウン選択」、「パスワード」、\n「ファイルアップロード」、「リンク」のいずれかから選択します。",
        'FTE01110' : "最大バイト数を入力します。[最大長]8192バイト\n編集の場合、元の値より増加させることは可能です。\n※半角英数字なら文字数分となります。\n※全角文字ならば文字数×3＋2 バイト必要になります。",
        'FTE01111' : "正規表現による入力値チェックを行う場合は、正規表現を入力します。[最大長]8192バイト\n例：0バイト以上の半角数値項目の場合： ^[0-9]*$\n　　1バイト以上の半角英数字の場合： ^[a-zA-Z0-9]+$",
        'FTE01112' : "最小値を入力します。\n編集の場合、元の値より減少させることは可能です。\n※-2147483648～2147483647 の整数数値が入力できます。\n※未入力の場合は-2147483648 になります。\n※最小値は最大値より小さい数値を入力してください。",
        'FTE01113' : "最大値を入力します。\n編集の場合、元の値より増加させることは可能です。\n※-2147483648～2147483647 の整数数値が入力できます。\n※未入力の場合は 2147483647 になります。\n※最大値は最小値より大きい数値を入力してください。",
        'FTE01114' : "最小値を入力します。\n編集の場合、元の値より減少させることは可能です。\n※-99999999999999～99999999999999、整数・小数合計 14 桁以下の小数数値が入力できます。\n※未入力の場合は-99999999999999 になります。\n※最小値は最大値より小さい数値を入力してください。",
        'FTE01115' : "最大値を入力します。\n編集の場合、元の値より増加させることは可能です。\n※-99999999999999～99999999999999、整数・小数合計 14 桁以下の小数数値が入力できます。\n※未入力の場合は 99999999999999 になります。\n※最大値は最小値より大きい数値を入力してください。",
        'FTE01116' : "整数・小数の合計桁数上限を入力します。\n編集の場合、元の値より増加させることは可能です。\n例：0.123は4桁(整数1桁、小数3桁)\n　　11.1111は6桁(整数2桁、小数4桁)\n※1～14の整数数値が入力できます。\n※未入力の場合は14になります。",
        'FTE01117' : "作成したパラメータシート(パラメータシート/データシート)から参照する対象をプルダウンから選択します。\n「選択項目」欄の文字列は「メニューグループ：パラメータシート：項目」の構成です。",
        'FTE01118' : "「プルダウン選択」で選んだパラメータシート項目を元に、ほかの項目を参照します。",
        'FTE01119' : "アップロードするファイルの最大バイト数を入力します。\n編集の場合、元の値より増加させることは可能です。\n最大は104857600バイトです。",
        'FTE01120' : "作成対象「パラメータシート(オペレーションあり)」で作成したパラメータシートの項目の中から参照する項目を選択します。\n選択した項目の中から同一オペレーションの値を参照します。",
        'FTE01121' : "作成したパラメータシートから登録する際、デフォルトで入力欄に入る値を設定します。\n「最大バイト数」を超える値、「正規表現」に不一致な値は設定できません。",
        'FTE01122' : "作成したパラメータシートから登録する際、デフォルトで入力欄に入る値を設定します。\n「最大値」「最小値」の範囲外の値は設定できません。",
        'FTE01123' : "作成したパラメータシートから登録する際、デフォルトで入力欄に入る値を設定します。\n「最大値」「最小値」「桁数」の範囲外の値は設定できません。",
        'FTE01124' : "作成したパラメータシートから登録する際、デフォルトで入力欄に入る値を設定します。",
        'FTE01125' : "作成したパラメータシートから登録する際、デフォルトで入力欄に入る値を設定します。\n「最大バイト数」を超える値は設定できません。",
        'FTE01126' : "作成したパラメータシートから登録する際、デフォルトで選択される値を設定します。",
        'FTE01127' : "必須項目にする場合は、チェックボックスを選択します。",
        'FTE01128' : "一意制約項目にする場合は、チェックボックスを選択します。",
        'FTE01129' : "項目名をマウスオーバーした際に表示される説明を入力します。[最大長]1024バイト",
        'FTE01130' : "備考を入力します。[最大長]4000バイト",
        'FTE01131' : "Please Wait... Loading",
        'FTE01132' : "初期値の取得に失敗しました。",
        'FTE01133' : "ID変換失敗",
        'FTE01134' : "日時",
        'FTE01135' : "日付",
        'FTE01136' : "パラメータシート作成を実行しますか？\n※既に同じパラメータシート名のパラメータシートや「パラメータシート定義一覧」パラメータシートの項番が同じパラメータシートが存在する場合、上書きでパラメータシートが作成され、入力済みのデータは削除されます。\n入力済みのデータが必要な場合は、「キャンセル」を選択して、データをバックアップしてください。",
        'FTE01137' : "パラメータシートの初期化を実行しますか？\n※このパラメータシートの入力済みのデータは削除されます。\n入力済みのデータが必要な場合は、「キャンセル」を選択して、データをバックアップしてください。",
        'FTE01138' : "パラメータシートの編集を実行しますか？\n※既存の項目に入力されているデータは残りますが、既存の項目を削除していた場合、その項目に入力されていたデータは削除されます。\n既存の項目で「正規表現」を変更した場合、既存のデータと不整合が発生する可能性があります。\nまた、新たに追加した項目を「必須」や「一意制約」としていた場合、必須項目に空のデータが入り、データの不整合が発生する可能性があります。\n修正が必要な場合は「キャンセル」を選択してください。",
        'FTE01139' : "参照項目の取得に失敗しました",
        'FTE01140' : "パラメータシート作成を受付ました。\nパラメータシート作成履歴ボタンを押して、パラメータシート作成状況を確認してください。\nUUID：",
        'FTE01141' : "バリデーションエラーです。",
        'FTE01142' : "項目が一つもありません",
        'FTE01143' : "削除",
        'FTE01144' : "パターンを追加",
        'FTE01145' : "パターンが一つもありません。",
        'FTE01146' : "項目名",
        'FTE01147' : "項目名(rest)",
        'FTE01148' : "フルスクリーン",
        'FTE01149' : "フルスクリーン解除",
        'FTE01150' : "最大バイト数を入力します。[最大長]255バイト\n編集の場合、元の値より増加させることは可能です。\n※半角英数字なら文字数分となります。\n※全角文字ならば文字数×3＋2 バイト必要になります。",
        'FTE01151' : "作成(新規)",
        'FTE01152' : "参照可能な項目がありません。",
        'FTE01153' : "ホストグループ",
        'FTE01154' : "「利用する」チェックボックスにチェックをいれた場合、「入力用」メニューグループにて「ホスト名/ホストグループ名」単位のパラメータシートが作成されます。\n「利用する」チェックボックスにチェックを入れない場合は「ホスト名」単位のパラメータシートが作成されます。",

        // Conductor
        'FTE02001' : "ConductorインスタンスIDが未設定です。",
        'FTE02002' : "ConductorインスタンスIDを入力し作業確認ボタンを押下するか、",
        'FTE02003' : "Conductor作業一覧",
        'FTE02004' : "ページにて詳細ボタンを押下してください。",
        'FTE02005' : "選択",
        'FTE02006' : "登録",
        'FTE02007' : "リセット",
        'FTE02008' : "編集",
        'FTE02009' : "作業実行",
        'FTE02010' : "流用新規",
        'FTE02011' : "新規",
        'FTE02012' : "更新",
        'FTE02013' : "再読み込み",
        'FTE02014' : "キャンセル",
        'FTE02015' : "作業確認",
        'FTE02016' : "予約取消",
        'FTE02017' : "緊急停止",
        'FTE02018' : "ConductorインスタンスID",
        'FTE02019' : "フルスクリーン",
        'FTE02020' : "フルスクリーン解除",
        'FTE02021' : "JSON保存",
        'FTE02022' : "JSON読込",
        'FTE02023' : "操作取り消し",
        'FTE02024' : "操作やり直し",
        'FTE02025' : "選択ノード削除",
        'FTE02026' : "全体表示",
        'FTE02027' : "ログ",
        'FTE02028' : "の読み込みに失敗しました。",
        'FTE02029' : "作業実行に失敗しました。",
        'FTE02030' : "登録しますか？",
        'FTE02031' : "登録しました。",
        'FTE02032' : "登録に失敗しました。",
        'FTE02033' : "読み込み完了しました。",
        'FTE02034' : "リセットしますか？",
        'FTE02035' : "リセットしました。",
        'FTE02036' : "流用しますか？",
        'FTE02037' : "流用しました。",
        'FTE02038' : "更新しますか？",
        'FTE02039' : "更新しました。",
        'FTE02040' : "更新に失敗しました。",
        'FTE02041' : "再読込しますか？",
        'FTE02042' : "再読込しました。",
        'FTE02043' : "Conductorの予約を取り消してよろしいですか？",
        'FTE02044' : "緊急停止しますか？",
        'FTE02045' : "正常終了",
        'FTE02046' : "異常終了",
        'FTE02047' : "想定外エラー",
        'FTE02048' : "緊急停止",
        'FTE02049' : "準備エラー",
        'FTE02050' : "Skip終了",
        'FTE02051' : "警告終了",
        'FTE02052' : "Other",
        'FTE02053' : "条件分岐は最大６つです。",
        'FTE02054' : "接続先がありません。",
        'FTE02055' : "マージできません。",
        'FTE02056' : "正常",
        'FTE02057' : "異常",
        'FTE02058' : "警告",
        'FTE02059' : "フィルタ設定",
        'FTE02060' : "正規表現を使用しない",
        'FTE02061' : "正規表現を使用する",
        'FTE02062' : "オーケストレータ選択",
        'FTE02063' : "設定",
        'FTE02064' : "キャンセル",
        'FTE02065' : "備考",
        'FTE02066' : "説明を入力します。[最大長]4000バイト",
        'FTE02067' : "Conductor情報",
        'FTE02068' : "Conductor名称を入力します。[最大長]255バイト",
        'FTE02069' : "名称",
        'FTE02070' : "更新日時",
        'FTE02071' : "Movement情報",
        'FTE02072' : "ID",
        'FTE02073' : "スキップ",
        'FTE02074' : "個別オペレーション",
        'FTE02075' : "オペレーション選択",
        'FTE02076' : "クリア",
        'FTE02077' : "終了ステータス",
        'FTE02078' : "平行分岐設定",
        'FTE02079' : "分岐追加",
        'FTE02080' : "分岐削除",
        'FTE02081' : "平行マージ設定",
        'FTE02082' : "マージ追加",
        'FTE02083' : "マージ削除",
        'FTE02084' : "条件分岐設定",
        'FTE02085' : "分岐追加",
        'FTE02086' : "分岐削除",
        'FTE02087' : "Conductor call情報",
        'FTE02088' : "スキップ",
        'FTE02089' : "呼び出しConductor",
        'FTE02090' : "Conductor選択",
        'FTE02091' : "クリア",
        'FTE02092' : "個別オペレーション",
        'FTE02093' : "オペレーション選択",
        'FTE02094' : "クリア",
        'FTE02095' : "ステータスファイル分岐設定",
        'FTE02096' : "条件追加",
        'FTE02097' : "条件削除",
        'FTE02098' : "Node 整列",
        'FTE02099' : "整列",
        'FTE02100' : "水平方向左に整列",
        'FTE02101' : "水平方向中央に整列",
        'FTE02102' : "水平方向右に整列",
        'FTE02103' : "垂直方向上に整列",
        'FTE02104' : "垂直方向中央に整列",
        'FTE02105' : "垂直方向下に整列",
        'FTE02106' : "等間隔",
        'FTE02107' : "垂直方向等間隔に分布",
        'FTE02108' : "水平方向等間隔に分布",
        'FTE02109' : "Conductorインスタンス情報",
        'FTE02110' : "ステータス",
        'FTE02111' : "開始時間",
        'FTE02112' : "終了時間",
        'FTE02113' : "実行ユーザ",
        'FTE02114' : "予約日時",
        'FTE02115' : "緊急停止",
        'FTE02116' : "オペレーション",
        'FTE02117' : "Nodeインスタンス情報",
        'FTE02118' : "種別",
        'FTE02119' : "Node ID",
        'FTE02120' : "Stファイル",
        'FTE02121' : "開始日時",
        'FTE02122' : "終了日時",
        'FTE02123' : "作業状況確認",
        'FTE02124' : "確認",
        'FTE02125' : "個別オペレーション",
        'FTE02126' : "Conductorデータが正しくありません。",
        'FTE02127' : "読み込みに失敗しました。",
        'FTE02128' : "作業状態確認",
        'FTE02129' : "予約取消に失敗しました",
        'FTE02130' : "緊急停止に失敗しました",
        'FTE02131' : "一時停止を解除しますか？",
        'FTE02132' : "一時停止の解除に失敗しました",
        'FTE02133' : "編集モード",
        'FTE02134' : "閲覧モード",
        'FTE02135' : "更新モード",
        'FTE02136' : "確認モード",
        'FTE02137' : "接続済みの分岐は削除できません。",
        'FTE02138' : "分岐は最低２つです。",
        'FTE02139' : "ループする接続はできません。",
        'FTE02140' : "Conductor実行エラー",
        'FTE02141' : "Conductor実行ログ",
        'FTE02142' : "メニュー",
        'FTE02143' : "自動入力",
        'FTE02144' : "マウスホイール",
        'FTE02145' : "画面の拡大・縮小",
        'FTE02146' : "マウス右ドラッグ",
        'FTE02147' : "画面の移動",
        'FTE02148' : "マウス左クリック",
        'FTE02149' : "Node選択・接続線削除",
        'FTE02150' : "マウス左ドラッグ",
        'FTE02151' : "Node移動・複数選択",
        'FTE02152' : "Node選択",
        'FTE02153' : "Node選択・作業状態確認",
        'FTE02154' : "マウス操作",
        'FTE02155' : "キーボード操作",
        'FTE02156' : "全てのNodeを選択",
        'FTE02157' : "選択したNodeを削除",
        'FTE02158' : "選択したNodeの移動",
        'FTE02159' : "選択した分岐Nodeの分岐追加・削除",
        'FTE02160' : "方向キー",
        'FTE02161' : "読み込み中",
        'FTE02162' : "編集途中のデータがLocal storageから読み込まれました。",
        'FTE02163' : "Movement名",
        'FTE02164' : "通知先がありません。\nConductor通知先定義より通知先を登録してください。",
        'FTE02165' : "通知先がありません",
        'FTE02166' : "Conductor通知先定義へ",
        'FTE02167' : "閉じる",
        'FTE02168' : "通知設定",
        'FTE02169' : "決定",
        'FTE02170' : "キャンセル",
        'FTE02171' : "通知名称",
        'FTE02172' : "通知",
        'FTE02173' : "グリッドにスナップ",
        'FTE02174' : "Movement共通表示設定",
        'FTE02175' : "幅",
        'FTE02176' : "名称折り返し",
        'FTE02177' : "自動",
        'FTE02178' : "サークルのみ",
        'FTE02179' : "折り返す",
        'FTE02180' : "省略する",

        // 作業状態確認
        'FTE05001' : "作業No.",
        'FTE05002' : "作業状態確認",
        'FTE05003' : "予約取消",
        'FTE05004' : "緊急停止",
        'FTE05005' : "作業No.が未設定です。",
        'FTE05006' : "作業No.を入力し作業状態確認ボタンを押下するか、",
        'FTE05007' : "作業管理ページ",
        'FTE05008' : "にて詳細ボタンを押下してください。",
        'FTE05009' : "作業ステータス",
        'FTE05010' : "実行種別",
        'FTE05011' : "ステータス",
        'FTE05012' : "実行エンジン",
        'FTE05013' : "呼出元Conductor",
        'FTE05014' : "実行ユーザ",
        'FTE05015' : "投入データ",
        'FTE05016' : "結果データ",
        'FTE05017' : "作業状況",
        'FTE05018' : "予約日時",
        'FTE05019' : "開始日時",
        'FTE05020' : "終了日時",
        'FTE05021' : "オペレーション",
        'FTE05022' : "ID",
        'FTE05023' : "名称",
        'FTE05024' : "作業対象ホスト確認",
        'FTE05025' : "代入値確認",
        'FTE05026' : "Movement",
        'FTE05027' : "遅延タイマー(分)",
        'FTE05028' : "Movement詳細確認",
        'FTE05029' : "Ansible利用情報",
        'FTE05030' : "ホスト指定形式",
        'FTE05031' : "WinRM接続",
        'FTE05032' : "ansible.cfg",
        'FTE05033' : "Ansible Core利用情報",
        'FTE05034' : "virtualenv",
        'FTE05035' : "Ansible Automation Controller利用情報",
        'FTE05036' : "実行環境",
        'FTE05037' : "予約を取り消してよろしいですか？",
        'FTE05038' : "Terraform利用情報",

        // 比較実行
        'FTE06001' : "比較設定選択",
        'FTE06002' : "ホスト選択",
        'FTE06003' : "比較実行",
        'FTE06004' : "比較設定を選択してください。",
        'FTE06005' : "対象ホストを選択してください。",
        'FTE06006' : "比較実行をしてください。",
        'FTE06007' : "比較設定",
        'FTE06008' : "比較名称",
        'FTE06009' : "詳細設定フラグ",
        'FTE06010' : "パラメーターシート名",
        'FTE06011' : "基準日時1",
        'FTE06012' : "基準日時2",
        'FTE06013' : "全件出力",
        'FTE06014' : "差分のみ",
        'FTE06015' : "比較対象パラメーターシート1",
        'FTE06016' : "比較対象パラメーターシート2",
        'FTE06017' : "出力内容",
        'FTE06018' : "ホスト名",
        'FTE06019' : "差分",
        'FTE06020' : "対象ホスト",
        'FTE06021' : "比較実行に失敗しました。",
        'FTE06022' : "比較対象パラメーターシート1 基準日時",
        'FTE06023' : "比較対象パラメーターシート2 基準日時",
        'FTE06024' : "項目",
        'FTE06025' : "備考",
        'FTE06026' : "ファイル差分詳細",
        'FTE06027' : "ファイル差分無し",
        'FTE06028' : "比較結果がありません。",
        'FTE06029' : "比較結果",
        'FTE06030' : "ファイル比較",
        'FTE06031' : "閉じる",
        'FTE06032' : "比較結果ダウンロード（Excel）",
        'FTE06033' : "ダウンロードに失敗しました。",
        'FTE06034' : "ファイル比較結果プリント",

        // エクスポート・インポート
        'FTE07001' : "全てのメニュー",
        'FTE07002' : "詳細",
        'FTE07003' : "エクスポート時刻指定",
        'FTE07004' : "エクスポート設定",
        'FTE07005' : "下記の内容でエクスポートします。",
        'FTE07006' : "メニュー数",
        'FTE07007' : "モード",
        'FTE07008' : "時刻指定",
        'FTE07009' : "廃止情報",
        'FTE07010' : "エクスポート確認",
        'FTE07011' : "エクスポート開始",
        'FTE07012' : "キャンセル",
        'FTE07013' : "エクスポート",
        'FTE07014' : "エクスポート",
        'FTE07015' : "エクスポートメニュー選択",
        'FTE07016' : "環境移行",
        'FTE07017' : "廃止を含む",
        'FTE07018' : "廃止を除く",
        'FTE07019' : "全レコード",
        'FTE07020' : "廃止のみ",
        'FTE07021' : "インポート設定",
        'FTE07022' : "インポートメニュー選択",
        'FTE07023' : "選択したファイルを開くことができません。",
        'FTE07024' : "ファイル選択",
        'FTE07025' : "インポート",
        'FTE07026' : "インポートするファイルを選択してください。",
        'FTE07027' : "インポートファイル",
        'FTE07028' : "ファイルネーム",
        'FTE07029' : "下記の内容でインポートします。",
        'FTE07030' : "インポート確認",
        'FTE07031' : "インポート開始",
        'FTE07032' : "インポート",
        'FTE07033' : "インポートに失敗しました。",
        'FTE07034' : "不明なメニューグループ",
        'FTE07035' : "インポート出来ないメニューが含まれています。",
        'FTE07036' : "インポートファイル読み込み中",

        // DashBoard
        'FTE08001' : "メニューグループ",
        'FTE08002' : "1行項目数",
        'FTE08003' : "表示形式",
        'FTE08004' : "アイコン",
        'FTE08005' : "リスト",
        'FTE08006' : "メニュグループ名",
        'FTE08007' : "表示する",
        'FTE08008' : "表示しない",
        'FTE08009' : "メニューセット",
        'FTE08010' : "メニューグループとは別のメニューグループのセットを作成できます。",
        'FTE08011' : "リンクリスト",
        'FTE08012' : "リンクのリストを作成できます。",
        'FTE08013' : "項目",
        'FTE08014' : "項目を追加する",
        'FTE08015' : "リストダウンロード",
        'FTE08016' : "リスト読込",
        'FTE08017' : "名称",
        'FTE08018' : "Movement登録数",
        'FTE08019' : "登録済みMovementのグラフを表示します。",
        'FTE08020' : "Conductor作業状況",
        'FTE08021' : "Conductorの作業状況グラフを表示します。",
        'FTE08022' : "作業状況",
        'FTE08023' : "Conductor作業結果",
        'FTE08024' : "Conductorの作業結果グラフを表示します。",
        'FTE08025' : "作業結果",
        'FTE08026' : "Conductor作業履歴",
        'FTE08027' : "Conductorの日別作業結果グラフを表示します。",
        'FTE08028' : "期間",
        'FTE08029' : "日",
        'FTE08030' : "Conductor予約作業確認",
        'FTE08031' : "Conductorの実行予約中リストを表示します。",
        'FTE08032' : "インスタンスID",
        'FTE08033' : "オペレーション名",
        'FTE08034' : "ステータス",
        'FTE08035' : "予約日時",
        'FTE08036' : "実行まで残り",
        'FTE08037' : "日",
        'FTE08038' : "時間",
        'FTE08039' : "分",
        'FTE08040' : "画像",
        'FTE08041' : "画像を貼り付けます。",
        'FTE08042' : "画像URL",
        'FTE08043' : "リンクURL",
        'FTE08044' : "DashBoard編集",
        'FTE08045' : "Widget追加",
        'FTE08046' : "編集反映",
        'FTE08047' : "リセット",
        'FTE08048' : "編集取消",
        'FTE08049' : "リセット確認",
        'FTE08050' : "DashBoardを初期状態に戻しますか？",
        'FTE08051' : "初期状態に戻す",
        'FTE08052' : "キャンセル",
        'FTE08053' : "編集取消確認",
        'FTE08054' : "編集中ですが、取り消してもよろしいですか？",
        'FTE08055' : "編集を取り消す",
        'FTE08056' : "編集を続ける",
        'FTE08057' : "Widget編集",
        'FTE08058' : "Widget削除",
        'FTE08059' : "名称",
        'FTE08060' : "横 結合数",
        'FTE08061' : "縦 結合数",
        'FTE08062' : "Widget表示",
        'FTE08063' : "タイトルバー",
        'FTE08064' : "枠・背景",
        'FTE08065' : "Widget基本設定",
        'FTE08066' : "Widget固有設定",
        'FTE08067' : "計",
        'FTE08068' : "正常終了",
        'FTE08069' : "異常終了",
        'FTE08070' : "警告終了",
        'FTE08071' : "緊急停止",
        'FTE08072' : "予約取消",
        'FTE08073' : "想定外エラー",
        'FTE08074' : "件数",
        'FTE08075' : "日",
        'FTE08076' : "実行中",
        'FTE08077' : "未実行(予約)",
        'FTE08078' : "一時停止",
        'FTE08079' : "未実行",
        'FTE08080' : function( target, today ){ return `（${target}～${today}）`},
        'FTE08081' : function( period ){ return `（${period}日以内）`},
        'FTE08082' : "ページ移動",
        'FTE08083' : "同じタブ",
        'FTE08084' : "別タブ",
        'FTE08085' : "別ウインドウ",
        'FTE08086' : "モーダル",
        'FTE08087' : function( day ){ return `${day}日以内の予約作業はありません。`},

        // Terraform
        'FTE09001' : "Organization登録管理",
        'FTE09002' : "Workspace登録管理",
        'FTE09003' : "Policy登録管理",
        'FTE09004' : "PolicySet登録管理",
        'FTE09005' : "Organization登録一覧を取得",
        'FTE09006' : "Workspace登録一覧を取得",
        'FTE09007' : "Policy登録一覧を取得",
        'FTE09008' : "PolicySet登録一覧取得",
        'FTE09009' : "登録済み",
        'FTE09010' : "未登録",
        'FTE09011' : "紐付解除",
        'FTE09012' : "ITAの登録状態",
        'FTE09013' : "削除",
        'FTE09014' : "リソース削除",
        'FTE09015' : "ダウンロード",
        'FTE09016' : "紐付Workspace",
        'FTE09017' : "紐付Policy",
        'FTE09018' : function( text ){ return `${text}ボタンを押下してください。`;},
        'FTE09019' : "Organization Name",
        'FTE09020' : "Email address",
        'FTE09021' : "Workspace Name",
        'FTE09022' : "Terraform Version",
        'FTE09023' : "Policy Name",
        'FTE09024' : "Policy code",
        'FTE09025' : "Policy Set Name",

        // UI共通
        'FTE10001': 'メインメニュー',
        'FTE10002': 'メニューグループ',
        'FTE10003': 'お気に入り',
        'FTE10004': '履歴',
        'FTE10005': 'ワークスペース切替',
        'FTE10006': 'ロール一覧',
        'FTE10007': 'メニュー検索',
        'FTE10008': '一覧',
        'FTE10009': '変更履歴',
        'FTE10010': '全件ダウンロード・ファイル一括登録',
        'FTE10011': '全件ダウンロード（Excel）',
        'FTE10012': '登録している項目の一覧をエクセルシートでダウンロードします。',
        'FTE10013': '全件ダウンロード（JSON）',
        'FTE10014': '登録している項目の一覧をJSONでダウンロードします。',
        'FTE10015': '新規登録用ダウンロード（Excel）',
        'FTE10016': '新規登録用のエクセルシートをダウンロードします。',
        'FTE10017': 'ファイル一括登録（Excel）',
        'FTE10018': '全件ダウンロード・新規登録用ダウンロードでダウンロードしたエクセルシートを編集し、ここからアップロードすることで一括して追加・編集ができます。',
        'FTE10019': 'ファイル一括登録（JSON）',
        'FTE10020': 'JSONファイルをここからアップロードすることで一括して追加・編集ができます。',
        'FTE10021': 'JSONの形式が正しくありません。',
        'FTE10023': '変更履歴全件ダウンロード（Excel）',
        'FTE10024': '登録している項目一覧の変更履歴全件をエクセルシートでダウンロードします。',
        'FTE10025': '一括登録開始',
        'FTE10026': 'キャンセル',
        'FTE10027': 'ファイルネーム',
        'FTE10028': 'ファイルサイズ',
        'FTE10029': '件数',
        'FTE10030': 'システムエラー',
        'FTE10031': '全件ダウンロードでダウンロードしたエクセルシートを編集し、ここからアップロードすることで一括して編集ができます。',
        'FTE10032': 'JSONファイルをここからアップロードすることで一括して編集ができます。',
        'FTE10033': 'バージョン確認',
        'FTE10034': 'ログアウト',
        'FTE10035': 'インストール済みドライバ',
        'FTE10036': ['日','月','火','水','木','金','土'],
        'FTE10037': ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月'],
        'FTE10038': '反映',
        'FTE10039': '現在',
        'FTE10040': 'クリア',
        'FTE10041': '入力済みパスワードの削除',
        'FTE10042': '登録成功',
        'FTE10043': '閉じる',
        'FTE10044': 'エラー列',
        'FTE10045': 'エラー内容',
        'FTE10046': '登録失敗',
        'FTE10047': 'エラーログJSONダウンロード',
        'FTE10048': '選択決定',
        'FTE10049': 'オペレーション',
        'FTE10050': 'オペレーション選択',
        'FTE10051': '予約日時を指定する場合は、日時フォーマット(yyyy/MM/dd HH:mm:ss)で入力して下さい。<br>ブランクの場合は即時実行となります。',
        'FTE10052': 'スケジュール',
        'FTE10053': 'ログ検索',
        'FTE10054': '該当行のみ表示',
        'FTE10055': '名称',
        'FTE10056': '設定',
        'FTE10057': '必須',
        'FTE10058': 'OK',
        'FTE10059': '確認',
        'FTE10060' : function( size, limit ){ return `ファイルバイト数がファイル最大バイト数を超えています。\n\nファイルバイト数: ${ Number( size ).toLocaleString() } Byte\nファイル最大バイト数: ${ Number( limit ).toLocaleString() } Byte`},
        'FTE10061': '画面設定',
        'FTE10062': 'ワークスペース一覧',
        'FTE10063': 'テーマ',
        'FTE10064': 'テーマ選択',
        'FTE10065': 'Default（青色を基調とした初期デザイン）',
        'FTE10066': 'Red（赤色を基調としたデザイン）',
        'FTE10067': 'Green（緑色を基調としたデザイン）',
        'FTE10068': 'Blue（青色を基調としたデザイン）',
        'FTE10069': 'Orange（オレンジ色を基調としたデザイン）',
        'FTE10070': 'Yellow（黄色を基調としたデザイン）',
        'FTE10071': 'Purple（紫色を基調としたデザイン）',
        'FTE10072': 'Brown（茶色を基調としたデザイン）',
        'FTE10073': 'Gray（灰色を基調としたデザイン）',
        'FTE10074': 'Cool（寒色を基調としたデザイン）',
        'FTE10075': 'Cute（ピンク色を基調としたデザイン）',
        'FTE10076': 'Natural（自然をイメージしたデザイン）',
        'FTE10077': 'Gorgeous（赤と黒を基調としたゴージャスなデザイン）',
        'FTE10078': 'OASE（Exastro OASEをイメージしたデザイン）',
        'FTE10079': 'EPOCH（ExastroEPOCHをイメージしたデザイン）',
        'FTE10080': 'Dark mode（夜間などに最適な暗色デザイン）',
        'FTE10081': 'フィルター',
        'FTE10082': 'グレースケール',
        'FTE10083': 'セピア',
        'FTE10084': '明るさ',
        'FTE10085': 'コントラスト',
        'FTE10086': '彩度',
        'FTE10087': '色相環',
        'FTE10088': '階調の反転',
        'FTE10089': '時',
        'FTE10090': '分',
        'FTE10091': '秒',
        'FTE10092': '更新失敗',
        'FTE10093': '更新に失敗しました。リロード後にもう一度お試しください。',
        'FTE10094': 'フィルターリセット',
        'FTE10095': 'メンテナンス中のため、新たに登録したConductorおよび各ドライバの作業実行、パラメータシート作成、メニューエクスポート/インポート、Excel一括エクスポート/インポートは実行されません。',
        'FTE10096': 'メンテナンス中のため、データの登録/更新/廃止を行うことができません。また、Conductorおよび各ドライバの作業実行、パラメータシート作成、メニューエクスポート/インポート、Excel一括エクスポート/インポートも行うことができません。',

        // パラメータ集
        'FTE11001': 'パラメータモード',
        'FTE11002': 'ホスト',
        'FTE11003': 'オペレーション',
        'FTE11004': '表示設定',
        'FTE11005': 'プリセット登録',
        'FTE11006': 'オペレーションタイムライン',
        'FTE11007': '対象パラメータ',
        'FTE11008': '対象ホスト',
        'FTE11009': 'パラメータ表示',
        'FTE11010': '選択',
        'FTE11011': 'クリア',
        'FTE11012': '未選択',
        'FTE11013': 'パラメータ、ホスト、オペレーションを選択し<br>パラメータ表示ボタンを押下してください。',
        'FTE11014': 'ホスト無し',
        'FTE11015': 'パラメータ選択',
        'FTE11016': 'パラメータ編集',
        'FTE11017': '対象オペレーション',
        'FTE11018': 'プリント',
        'FTE11019': '読み込みに失敗しました。',
        'FTE11020': '削除中',
        'FTE11021': '登録中',
        'FTE11022': 'パラメータ集プリセット登録',
        'FTE11023': 'パラメータ集プリセット名称変更',
        'FTE11024': 'プリセット登録',
        'FTE11025': 'プリセット名称変更',
        'FTE11026': '保存',
        'FTE11027': '名称変更',
        'FTE11028': '削除',
        'FTE11029': 'プリセットの登録がありません。',
        'FTE11030': 'パラメータ集プリセット',
        'FTE11031': '管理システム項番',
        'FTE11032': 'ホスト名',
        'FTE11033': 'DNSホスト名',
        'FTE11034': 'IPアドレス',
        'FTE11035': 'メニューID',
        'FTE11036': 'メニューグループ',
        'FTE11037': 'メニュー名',
        'FTE11038': 'シートタイプ',
        'FTE11039': 'バンドル',
        'FTE11040': 'ホストグループ',
        'FTE11041': 'ホスト/オペレーションあり',
        'FTE11042': 'オペレーションあり',
        'FTE11043': '利用する',
        'FTE11044': 'ホスト選択',
        'FTE11045': '件のオペレーション',
        'FTE11046': 'パラメータ表示設定',
        'FTE11047': '代入順序',
        'FTE11048': '表示できるパラメータがありません。',
        'FTE11049': 'Excelダウンロード',
        'FTE11050': 'Excelダウンロードに失敗しました。',
        'FTE11051': 'パラメータ集プリセット保存確認',
        'FTE11052': '保存',
        'FTE11053': 'パラメータ集プリセット削除確認',
        'FTE11054': '削除',
        'FTE11055': 'キャンセル',
        'FTE11056': function( name ){ return `プリセット「${name}」に保存します。`},
        'FTE11057': function( name ){ return `プリセット「${name}」を削除します。`},
        'FTE11058': 'ホスト無しを表示',
        'FTE11059': 'メニュー名検索',
        'FTE11060': 'ホスト名検索',
        'FTE11061': 'パラメータ集_',

        // 独自メニュー
        'FTE12001': '独自メニューの表示に失敗しました。',

        // OASE
        'FTE13001': 'ラベル設定',
        'FTE13002': 'ラベル名',
        'FTE13003': '条件',
        'FTE13004': '条件値',
        'FTE13005': '結論ラベル設定',
        'FTE13006': '結論ラベル名',
        'FTE13007': '結論ラベル値',
        'FTE13008': '未知イベント',
        'FTE13009': '時間切れイベント',
        'FTE13010': '既知イベント',
        'FTE13011': '判断結果',
        'FTE13012': '新規イベント',
        'FTE13013': '実行アクション',
        'FTE13014': '範囲指定',
        'FTE13015': '設定',
        'FTE13016': '範囲指定履歴',
        'FTE13017': '表示パターン選択',
        'FTE13018': function( type ){ return `${type}の登録がありません。`},
        'FTE13019': function( num ){ return `${num}分間`},
        'FTE13020': function( num ){ return `${num}時間`},
        'FTE13021': function( num ){ return `${num}日間`},
        'FTE13022': function( num ){ return `${num}週間`},
        'FTE13023': function( num ){ return `${num}か月間`},
        'FTE13024': function( num ){ return `${num}年間`},
        'FTE13025': '',
        'FTE13026': '',
        'FTE13027': '',
        'FTE13028': '',
        'FTE13029': '',
    };

    return message;

}