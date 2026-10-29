# 独自メニューの作成方法に関するリファレンス(custom_menu_creation.md)

Exastro IT Automation(ITA)の管理コンソールでは、初期メニュー以外に利用部門が独自の情報を管理するための「独自メニュー」を作成できる。
独自メニューは、メニュー上に表示させたいHTML/JavaScript/CSS等を「独自メニュー用素材」としてZIPに圧縮して登録することで実現する。
このリファレンスは独自メニューの作成手順、素材ZIPの仕様、利用可能なJavaScriptライブラリ、ITA標準のJavaScript/CSS(common.js, ui.js, table.js, dialog.js)の使い方をまとめたもの。

## 独自メニューの登録方法(重要)
- 独自メニューは、管理コンソールの**「メニュー管理」(menu_list) メニューへレコードを登録する**ことで作成する。この`menu_list`メニューはMCPから書き込み可能な通常のメニューであり、**MCPの`maintenance-all`ツールで登録できる**(画面での手動操作は必須ではない)。
- **`create-menu`ツールは使わない**。`create-menu`はパラメータシート/データシート(項目定義を持つメニュー)を新規作成する専用ツールであり、独自メニューの登録には使用しない。
- 登録の流れ:
    1. `main.html`を含む素材一式をZIPに圧縮する(下記「独自メニュー用素材(ZIP)の仕様」に従う)。エージェントが生成したZIPは`create-text-file`等で`file_id`を発行して渡す。
    2. `menu_list`メニューに対し`maintenance-all`でレコードを登録し、「独自メニュー用素材」項目に上記の`file_id`を連携する。
    3. 事前に`list-menu-info`で`menu_list`の書き込み可否(`row_insert_flag`/`row_update_flag`)と各項目の型を確認すること。

## 独自メニュー利用手順
1. **メニュー管理**(menu_list) メニューで「独自メニュー用素材」(ZIP)を登録し、新規メニューを作成する。
2. **ロール・メニュー紐付管理** メニューで、作成したメニューに対して「メンテナンス可」または「閲覧のみ」の権限を付与する。
   - 注意: ロールに紐付かないメニュー画面はメニューグループに表示されない。
3. 登録したメニューを表示する。

## 独自メニュー用素材(ZIP)の仕様
- メニュー管理でメニューを直接登録した場合にのみ使用される素材。既存メニューやパラメータシート作成機能で作成されたメニューには登録しても使用されない。
- メニュー上に表示させたいHTML、JavaScript、CSS等をZIPに圧縮して登録する。
- **メインで表示させるHTMLは「main.html」というファイル名固定**。
- 「main.html」内で使用されるその他のファイル名は任意。
- **ZIP内のファイルは全てフォルダ直下に配置する必要がある**(サブフォルダ不可)。
- 「独自メニュー用素材」が登録されていないメニューを表示しても何も表示されない。

### 素材サンプルの例
- サンプル①: 1枚の画像と「Hello」ボタンを表示し、押下すると「Hello」というアラートを表示する。
- サンプル②: 他のITAのメニューと同じようなメニュー(一覧テーブル等)を表示する。
- サンプル③: 「独自メニュー用素材」を登録せずにメニューを表示した場合(何も表示されない)。

## 利用可能なJavaScriptライブラリ
ITAで使用しているJavaScriptライブラリは以下から読み込める。パスの先頭は `/_/ita/lib/...`。

| ライブラリ | 説明 | バージョン | 読み込み |
| --- | --- | --- | --- |
| jQuery | JavaScriptコードを容易に記述できるライブラリ | 3.5.1 | `<script src="/_/ita/lib/jquery/jquery.js"></script>` |
| select2 | 選択ボックスを便利にするjQueryライブラリ(別途jQuery必須) | 4.0.13 | `<script defer src="/_/ita/lib/select2/select2.min.js"></script>` / `<link rel="stylesheet" href="/_/ita/lib/select2/select2.min.css">` |
| Ace | Web用の高機能テキストエディター(mode: json,python,terraform,text,yaml / theme: chrome,monokai) | v1.5.0 | `<script defer src="/_/ita/lib/ace/ace.js"></script>` |
| ExcelJS | スプレッドシートのデータ/スタイルの読み書き、XLSX・JSON出力 | 4.3.0 | `<script src="/_/ita/lib/exceljs/exceljs.js"></script>` |
| diff2html | git diff / unified diff からHTML差分を生成 | v2.11.3 | `<script src="/_/ita/lib/diff2html/diff2html.min.js"></script>` / `<link rel="stylesheet" href="/_/ita/lib/diff2html/diff2html.css">` |

## IT Automation JavaScript/CSS情報
独自メニューでITAと同様の画面を表示したい場合に使用できる。使用時は別途jQueryと言語ファイルの読み込みが必要。

```html
<script src="/_/ita/lib/jquery/jquery.js"></script>
<script>let getMessage;</script>
<script type="module">
    import {messageid_ja} from '/_/ita/js/messageid_ja.js';
    getMessage = messageid_ja();
</script>
```

### common.js
変数 `fn` に基本的な各種関数をまとめたもの。他のITA JavaScriptを使用する際に必須。

```html
<script src="/_/ita/js/common.js"></script>
```

#### fn.fetch
ITA APIにリクエストを送信する。

```javascript
const result = await fn.fetch( URL, TOKEN, METHOD, BODY );
```
- **URL**: APIエンドポイント。先頭の `/api/{organization_id}/workspaces/{workspace_id}/ita` は省略する。
- **TOKEN**: 基本的に `null` を指定。Worker内などで使用する場合は別途Tokenを取得して渡す。
- **METHOD**: `POST`, `GET` などのメソッド。省略時は `GET`。
- **BODY**: POSTの場合のbodyデータ。省略可。

使用例(オペレーション一覧を取得):
```javascript
async function operationList(){
    const result = await fn.fetch('/menu/operation_list/filter/', null, 'POST', {"discard": {"NORMAL": "0"}});
    console.log( result );
}
```

#### fn.xhr
データの登録を行う。fn.fetchでも登録可能だが、fn.xhrはデータ登録に機能を絞り登録時の進捗が表示される。

```javascript
const result = await fn.xhr( URL, FORMDATA );
```
- **URL**: APIエンドポイント。`/menu/{menu_name_rest}/maintenance/all/`。
- **FORMDATA**: 登録用データをフォームデータに変換して渡す。

使用例(オペレーションを1件登録):
```javascript
window.addEventListener('DOMContentLoaded', () => {
    registerOperation();
});

async function registerOperation(){
    // フォームデータ
    const formData = new FormData();

    // 登録データ
    const regsterData = [
        {
            parameter: {
                discard: '0',
                operation_name: 'オペレーション名',
                scheduled_date_for_execution: '2024/12/31 00:00:00'
            },
            file: {},
            type: 'Register'
        }
    ];

    // パラメータをフォームデータに追加（regsterDataを文字列に変換する）
    formData.append('json_parameters', JSON.stringify( regsterData ) );

    // 登録
    const result = await fn.xhr('/menu/operation_list/maintenance/all/', formData );

    console.log( result );
}
```

### common.css
ITAの基本的な画面のスタイル。ITA JavaScriptを使用する場合は読み込み必須。

```html
<link rel="stylesheet" href="/_/ita/css/common.css">
```

### ui.js
ITAの基本的な画面(タブ、コンテナ等)を生成する。

```html
<script defer src="/_/ita/js/ui.js"></script>
```

使用例(タブが3つある画面を作成):
```javascript
window.addEventListener('DOMContentLoaded', () => {
    // 対象
    const $content = $('#content');

    // ui.js
    const ui = new CommonUi();

    // メニュー情報
    ui.info = {
        menu_info: {
            menu_name: 'タブメニューサンプル',
            menu_info: 'タブメニューサンプルです。'
        }
    };

    // タブ内部のHTML
    ui.tab1 = function(){ return 'Tab1 Contents'};
    ui.tab2 = function(){ return 'Tab2 Contents'};

    // タブ定義
    // nameで上記で設定した関数が呼ばれます。タブのIDにもなります。
    // titleがタブに表示されます。
    // type: 'blank'を指定すると空のタブが作成されます。
    const tabs = [
      { name: 'tab1', title: 'タブ１'},
      { name: 'tab2', title: 'タブ２'},
      { name: 'tab3', title: 'タブ３', type: 'blank'}
    ];

    // タブHTML作成
    const tabHtml = ui.contentTab( tabs );

    // メニュータイトル・説明欄
    const menuHtml = ui.commonContainer( ui.info.menu_info.menu_name, ui.info.menu_info.menu_info, tabHtml );

    // 対象にtabContentクラスをセットしHTMLをセット
    $content.addClass('tabContent').html( menuHtml );

    // タブ３はblankで作成したため、別途HTMLをセットする
    $('#tab3').find('.sectionBody').html('Tab3 Contents');

    // タブイベントをセット。引数に最初に開いてあるタブのnameを指定。
    ui.contentTabEvent('#tab1');

    // メニュー詳細ボタンイベントをセット
    ui.setCommonEvents();
});
```

### table.js
指定したパラメータシートのTable表示・編集ができる。

```html
<script defer src="/_/ita/js/table.js"></script>
```

```javascript
const table = new DataTable( ID, MODE, INFO, PARAMS );
const $table = table.setup();
```
- **ID**: ユニークなIDを指定。
- **MODE**: `view`(基本) または `history`(履歴表示)。
- **INFO**: メニュー情報。`/menu/{menuNameRest}/info/` で取得した情報を渡す。
- **PARAMS**: 必須パラメータ指定。

使用例(オペレーション一覧を表示):
```javascript
window.addEventListener('DOMContentLoaded', async () => {
    // 対象
    const $content = $('#content');

    // オペレーション一覧メニュー名（REST）
    const menuNanmeRest = 'operation_list';

    // メニュー情報を取得
    const info = await fn.fetch(`/menu/${menuNanmeRest}/info/`);

    // 必須パラメータ取得
    const params = fn.getCommonParams();
    params.menuNameRest = menuNanmeRest;

    // テーブル作成
    // table.setup()でTableのjQueryオブジェが返ってきます。
    const table = new DataTable('operationList', 'view', info, params );
    $content.html( table.setup() );
});
```

### dialog.js
ダイアログを表示する。

```html
<script defer src="/_/ita/js/dialog.js"></script>
<link rel="stylesheet" href="/_/ita/css/dialog.css">
```

```javascript
const dialog = new Dialog( CONFIG, FUNCTIONS );
dialog.open( CONTENTS );
```
- **CONFIG**: ダイアログ構成情報。
- **FUNCTIONS**: ダイアログのボタンを押したときの関数。
- **CONTENTS**: ダイアログボディHTML。

使用例(Hello worldを表示し、OKと閉じるで処理を分ける):
```javascript
window.addEventListener('DOMContentLoaded', async () => {
    const flag = await helloWorld();
    if ( flag ) {
        console.log('OK!');
    } else {
        console.log('CLOSE!!')
    }
});

function helloWorld(){
    return new Promise(function( resolve ){
        // ボタンを押したときの動作
        const functions = {
            // OKを押した場合の関数
            ok: function(){
                this.close();
                resolve( true );
            },
            // 閉じるを押した場合の関数
            close: function(){
                this.close();
                resolve( false );
            }
        };
        // ダイアログ表示定義
        const config = {
            // モーダルの位置 top or center
            position: 'center',
            // ヘッダー情報
            header: {
                title: 'ダイアログテスト'
            },
            // 幅
            width: '640px',
            // フッター情報
            footer: {
                // ボタン情報
                button: {
                    // functionsと同じキー名で紐づけ。
                    // text: 表示テキスト。
                    // action: ボタンの役割（positive,restore,duplicat,warning,danger,history,normal,negative）※色が変わるだけです。
                    // style: スタイルを指定。
                    ok: { text: 'OK', action: 'default', style: 'width:160px;'},
                    close: { text: '閉じる', action: 'normal'}
                }
            }
        };
        const dialog = new Dialog( config, functions );
        dialog.open('<div style="padding:24px;text-align:center;font-size:24px;">Hello World</div>');
    });
}
```

## main.html の最小サンプル
`main.html` にHTML/JS/CSSをまとめて記述する例(サンプル①相当)。ZIP直下に `main.html` として配置する。

```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>独自メニューサンプル</title>
    <script src="/_/ita/lib/jquery/jquery.js"></script>
    <link rel="stylesheet" href="/_/ita/css/common.css">
</head>
<body>
    <div id="content">
        <button id="helloButton" type="button">Hello</button>
    </div>
    <script>
        $('#helloButton').on('click', function(){
            alert('Hello');
        });
    </script>
</body>
</html>
```
