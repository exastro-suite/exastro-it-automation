////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Exastro IT Automation / table_pf.js
//
//   -----------------------------------------------------------------------------------------------
//
//   Copyright 2026 NEC Corporation
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

// プラットフォームAPIの一覧を表示するTable。
//
// ・HTML構造・CSSクラス名は table.js（DataTable）に合わせているため、common.cssのTable用スタイルが
//   そのまま適用される。メニュー情報（menu_info / column_info）は使わず、カラム定義を渡して組み立てる。
// ・ページの切り替えは、その都度APIから該当ページ分だけを取得する（サーバーサイドページング）。
//   table.js のようにWorkerへ全件を渡して絞り込む方式は取らない。
//   option.paging を false にするとページングをやめ、1回の取得（params.limit 件まで）で全件を表示する。
// ・件数・最大ページ数はAPIが返す総件数から求めるため、総件数の取り出し方を params.total で渡す
//   （総件数を返すAPIのみ対応）。
//
// AIアシスタントの会話一覧（GET /conversations）・学習事項の一覧（GET /lessons）は
// staticメソッドでインスタンスを作れる。
//
//   const table = DataTablePF.conversationList('conversationTable');
//   $target.html( table.setup() );
//
// 任意の一覧を表示する場合はカラム定義とAPIを渡す。
//
//   const table = new DataTablePF('someTable', {
//       columns: [
//           { key: 'name', name: '名前', width: '240px'},
//           { key: 'date', name: '日時', type: 'datetime'}
//       ],
//       rest: ( limit, offset ) => `/api/.../items?limit=${limit}&offset=${offset}`,
//       list: ( data ) => data.items,
//       total: ( data ) => data.total_count
//   });
//
// カラム定義（columns）で指定できるもの
//   key       … 表示するデータのキー（cellを指定する場合は列の識別子としてのみ使われる）
//   name      … 見出しの文言
//   type      … 'text'（既定） / 'number'（右寄せ） / 'date' / 'datetime'
//   width     … 列の最大幅（CSSの値）。列の幅は内容物に合わせて決まり、表示領域が広くなっても変わらない
//   minWidth  … 列の最小幅（CSSの値）。指定した列は表示領域の余った幅を受け持って広がる
//                （widthとは併用しない。widthを指定した他の列は内容物の幅で固定される）
//   wrap      … trueで折り返して表示する（既定は1行で省略表示）
//   className … セルに追加するクラス名
//   cell      … セルのHTMLを返す関数 ( item, column ) => html（値は呼び出し側でエスケープする）
//   sort      … falseで見出しをクリックしても並び替えないようにする（option.sortが有効な場合のみ関係する）
//
// option で指定できるもの
//   onePageNum       … 1ページに表示する件数（省略時は前回選択した件数）
//   paging           … falseでページングをやめ、1回の取得（params.limit 件まで）で全件を表示する
//   sort             … trueで見出しのクリックによる並び替えを行う（降順→昇順で切り替わる）
//                      取得済みの一覧を画面側で並び替えるため、全件を持っている
//                      （paging: false の）Tableでのみ有効になる
//   rowMenu          … 行ごとのボタン [{ type, text, icon, action }]（先頭にボタン1つにつき1列を作る）
//   rowMenuAction    … 行のボタンを押したときの処理 ( type, item ) => void
//   headerMenu       … 行の選択によらないボタン [{ type, text, icon, action }]（再読込の右側に追加する）
//   headerMenuAction … headerMenuのボタンを押したときの処理 ( type ) => Promise
//                      処理のあと一覧を取得しなおす。falseを返すと取得しなおさない
//   importAction     … インポートの処理 () => Promise（メニューの右側にインポートボタンを追加する）
//                      行の選択によらず押せる。処理のあと一覧を取得しなおす。falseを返すと
//                      取得しなおさない（ファイルの選択・確認をキャンセルした場合など）
//   exportAction     … 選択した行のエクスポートの処理 ( items ) => Promise
//                      （メニューの右側にエクスポートボタンを追加する）
//                      一覧の内容は変わらないため、falseを返して取得しなおしを省ける
//   select           … trueで一番左にチェックボックスの列を追加する
//                      （selectMenu・exportAction・deleteAction指定時は自動で追加）
//   selectMenu       … 選択した行に対するボタン [{ type, text, icon, action }]（メニューに追加する）
//   selectMenuAction … 選択した行に対するボタンを押したときの処理 ( type, items ) => Promise
//                      処理のあと一覧を取得しなおす。falseを返すと取得しなおさない
//   deleteAction     … 選択した行の削除処理 ( items ) => Promise（メニューに削除ボタンを追加する）
//                      処理のあと一覧を取得しなおす。falseを返すと取得しなおさない（確認をキャンセルした場合など）
//   notice           … フッターの件数の右側に表示する案内 ( total ) => { icon, text, alert } / null（textはHTML）
//                      一覧を取得しなおすたびに、そのときの総件数で作りなおす
//   errorTitle       … 取得に失敗したときの見出し
class DataTablePF {
/*
##################################################
   1ページに表示する件数
##################################################
*/
static get onePageNumList() {
    return [ 10, 25, 50, 75, 100 ];
}
static get defaultOnePageNum() {
    return 25;
}
// ページングを行わない場合に、1回の取得で取りに行く件数（params.limit 省略時）
static get defaultFetchLimit() {
    return 200;
}
/*
##################################################
   再送するHTTPステータス（一過性のエラーのみ）
##################################################
*/
static get retryStatuses() {
    return [ 425, 429, 500, 502, 503 ];
}
/*
##################################################
   会話一覧のTable
##################################################
*/
// AIアシスタントの会話（T_CHAT_CONVERSATION）の一覧を表示するTableを作る。
// 会話に対する操作（再開など）は option.rowMenu / option.rowMenuAction で渡す。
static conversationList( tableId, option = {}) {
    const { organizationId, workspaceId } = fn.getCommonParams();
    const endPoint = `/api/${organizationId}/platform/workspaces/${workspaceId}/conversations`;

    // 会話一覧はprompt_profileでの絞り込みが必須。省略時はAIアシスタントが使うプロファイル。
    const promptProfile = fn.cv( option.promptProfile,
        ( typeof AiAssistantLlm !== 'undefined')? AiAssistantLlm.promptProfile: '');

    return new DataTablePF( tableId, {
        columns: DataTablePF.conversationColumns,
        rest: ( limit, offset ) => `${endPoint}?prompt_profile=${encodeURIComponent( promptProfile )}`
            + `&limit=${limit}&offset=${offset}`,
        list: ( data ) => ( Array.isArray( data?.conversations ) )? data.conversations: [],
        // total_countは絞り込み条件（prompt_profile・status）に合致する総件数（limit/offset適用前）。
        // countは取得したページの件数なので使わない。
        total: ( data ) => data?.total_count
    }, option );
}
/*
##################################################
   会話一覧のカラム定義
##################################################
*/
static get conversationColumns() {
    return [
        // タイトルは他の列より長くなるため、余った幅を受け持って広がる列にする
        { key: 'title', name: getMessage.FTE14028, minWidth: '320px', wrap: true},
        //{ key: 'status', name: getMessage.FTE14029, width: '100px'},
        //{ key: 'model_id', name: getMessage.FTE14025, width: '320px'},
        // message_countは最新のスナップショットに含まれる発言（ターン）の数
        { key: 'message_count', name: getMessage.FTE14030, type: 'number', width: '100px'},
        // current_token_countは問い合わせのたびに積算される値のため、問い合わせを経ていない会話
        // （インポートした会話など）では0のまま返ってくる。0トークンと数えられたわけではないので、
        // 0の場合は数値を出さず、不明であることが分かる表示（ハイフン）にする
        { key: 'current_token_count', name: getMessage.FTE14031, type: 'number', width: '120px',
            cell: ( item ) => {
                const count = Number( item.current_token_count );
                return ( Number.isFinite( count ) && count > 0 )
                    ? fn.escape( count.toLocaleString() )
                    : `<span class="pfTableUnknownValue" title="${fn.escape( getMessage.FTE14094 )}">-</span>`;
            }},
        { key: 'created_at', name: getMessage.FTE14026, type: 'datetime', width: '180px'},
        { key: 'updated_at', name: getMessage.FTE01017, type: 'datetime', width: '180px'},
        { key: 'conversation_id', name: getMessage.FTE14032, width: '240px'}
    ];
}
/*
##################################################
   学習事項の一覧のTable
##################################################
*/
// AIアシスタントの学習事項（T_USER_LESSON）の一覧を表示するTableを作る。
// ページングは行わず、1回の取得（lessonsFetchLimit 件まで）で全件を表示する。
// 全件を持っているため、見出しのクリックによる並び替え（option.sort）を行う。
// 新規登録・1件ごとの編集・選択した行の有効化・無効化・削除は option.headerMenu / option.rowMenu /
// option.selectMenu / option.deleteAction で渡す。
static lessonList( tableId, option = {}) {
    const { organizationId, workspaceId } = fn.getCommonParams();
    const endPoint = `/api/${organizationId}/platform/workspaces/${workspaceId}/lessons`;

    // 学習事項の一覧はprompt_profileでの絞り込みが必須。省略時はAIアシスタントが使うプロファイル。
    const promptProfile = fn.cv( option.promptProfile,
        ( typeof AiAssistantLlm !== 'undefined')? AiAssistantLlm.promptProfile: '');

    return new DataTablePF( tableId, {
        columns: DataTablePF.lessonColumns,
        // 全件を1回で取得するため、1回のリクエストで取得する件数を上限として渡す
        limit: ( typeof AiAssistantLlm !== 'undefined')? AiAssistantLlm.lessonsFetchLimit: 200,
        // 有効・無効や分類での絞り込みは行わない（そのプロファイルに登録されているものをすべて表示する）
        rest: ( limit, offset ) => `${endPoint}?prompt_profile=${encodeURIComponent( promptProfile )}`
            + `&limit=${limit}&offset=${offset}`,
        list: ( data ) => ( Array.isArray( data?.lessons ) )? data.lessons: [],
        total: ( data ) => data?.total_count
    }, { paging: false, sort: true, ...option });
}
/*
##################################################
   学習事項の一覧のカラム定義
##################################################
*/
static get lessonColumns() {
    return [
        // 有効な学習事項だけが、AIへの前提知識としてシステムプロンプトへ反映される
        { key: 'enabled', name: getMessage.FTE14046, width: '80px',
            cell: ( item ) => `<span class="aiLessonStatus" data-enabled="${( item.enabled )? 'true': 'false'}">`
                + `${( item.enabled )? getMessage.FTE14047: getMessage.FTE14048}</span>`},
        { key: 'priority', name: getMessage.FTE14045, type: 'number', width: '100px'},
        { key: 'category', name: getMessage.FTE14044, width: '160px'},
        // 内容は複数行になるため折り返して表示する（CSSで数行までに抑えている）。
        // 他の列より長くなるため、余った幅を受け持って広がる列にする
        { key: 'lesson', name: getMessage.FTE14043, minWidth: '320px', wrap: true},
        { key: 'created_at', name: getMessage.FTE14026, type: 'datetime', width: '180px'},
        { key: 'updated_at', name: getMessage.FTE01017, type: 'datetime', width: '180px'},
        { key: 'lesson_id', name: getMessage.FTE14049, width: '240px'}
    ];
}
/*
##################################################
   行ごとのボタンの列
##################################################
*/
// option.rowMenu で渡されたボタンを1つずつ列に分けて作る（見出しはボタンの文言）。
// 押されたボタンの種別（type）は setTableEvents() が option.rowMenuAction へ渡す。
static rowMenuColumns( rowMenu ) {
    const columns = [];
    for ( const item of rowMenu ) {
        const text = fn.cv( item.text, '', true );
        columns.push({
            key: `rowMenu_${item.type}`,
            name: item.text,
            className: 'tBodyTdButton',
            // ボタンの列は並び替えの対象にしない
            sort: false,
            // 何のボタンかは見出しで分かるため、セルのボタンはアイコンのみにする
            // （文言はマウスオーバーで見えるようにtitleへ入れる）。
            cell: () => fn.html.iconButton( item.icon, '',
                ['itaButton', 'actionButton', 'pfTableRowMenuButton'],
                { type: item.type, action: fn.cv( item.action, 'default'), title: text })
        });
    }
    return columns;
}
/*
##################################################
   選択用の列
##################################################
*/
// 一番左に置くチェックボックスの列。見出しは一括選択ボタン、セルは行ごとのチェックボックスで、
// HTML・クラス名はtable.jsの選択列（.tHeadRowSelect / .tBodyRowSelect）に合わせている。
static get selectColumn() {
    return { key: 'pfTableSelect', select: true };
}
/*
##################################################
   Constructor
   params {
      columns: カラム定義の配列
      rest: ( limit, offset ) => 一覧取得のURL
      list: ( data ) => 一覧の配列（省略時は応答をそのまま配列として扱う）
      total: ( data ) => 総件数
   }
   option {
      onePageNum: 1ページに表示する件数（省略時は前回選択した件数）
      paging: falseでページングをやめ、1回の取得で全件を表示する
      sort: trueで見出しのクリックによる並び替えを行う（paging: false のTableのみ）
      rowMenu: 行ごとに並べるボタン [{ type, text, icon, action }]
      rowMenuAction: ( type, item ) => void（行のボタンを押したときの処理）
      headerMenu: 行の選択によらないボタン [{ type, text, icon, action }]（再読込の右側）
      headerMenuAction: ( type ) => Promise（headerMenuのボタンを押したときの処理）
      select: trueで選択用のチェックボックスの列を追加する
      selectMenu: 選択した行に対するボタン [{ type, text, icon, action }]
      selectMenuAction: ( type, items ) => Promise（選択した行に対するボタンの処理）
      importAction: () => Promise（インポートの処理）
      exportAction: ( items ) => Promise（選択した行のエクスポートの処理）
      deleteAction: ( items ) => Promise（選択した行の削除処理）
      notice: ( total ) => { icon, text, alert }（フッターの件数の右側に表示する案内）
      errorTitle: 取得に失敗したときの見出し
   }
##################################################
*/
constructor( tableId, params, option = {}) {
    const tb = this;
    tb.id = tableId;
    tb.params = params;
    tb.option = option;

    // 選択した行に対するボタン（有効化・無効化など。削除は deleteAction が受け持つ）
    tb.selectMenu = ( fn.typeof( option.selectMenu ) === 'array')? option.selectMenu: [];

    // 行の選択によらないボタン（登録など。行を選択していなくても押せる）
    tb.headerMenu = ( fn.typeof( option.headerMenu ) === 'array')? option.headerMenu: [];

    // 選択した行に対する処理があれば、行を選択できるようにする
    tb.selectFlag = ( option.select === true || tb.selectMenu.length > 0
        || fn.typeof( option.exportAction ) === 'function'
        || fn.typeof( option.deleteAction ) === 'function');

    // ページングを行うか（falseの場合は1回の取得で全件を表示する）
    tb.pagingFlag = ( option.paging !== false );

    // 見出しのクリックで並び替えを行うか。取得済みの一覧を画面側で並び替えるため、
    // ページングを行う（1ページ分しか持っていない）Tableでは行わない
    tb.sortFlag = ( option.sort === true && !tb.pagingFlag );

    // 案内をフッターへ表示するか
    tb.noticeFlag = ( fn.typeof( option.notice ) === 'function');

    tb.columns = ( fn.typeof( params.columns ) === 'array')? params.columns: [];

    // 行ごとのボタンは先頭の列に表示する（ボタン1つにつき1列）
    if ( fn.typeof( option.rowMenu ) === 'array' && option.rowMenu.length ) {
        tb.columns = DataTablePF.rowMenuColumns( option.rowMenu ).concat( tb.columns );
    }

    // 選択用のチェックボックスは一番左の列
    if ( tb.selectFlag ) {
        tb.columns = [ DataTablePF.selectColumn ].concat( tb.columns );
    }

    // テーブルデータ
    tb.data = {
        body: null
    };

    // 並び替えの設定（keyがnullのときはAPIから取得した順のまま）。
    // 再読込・処理後の取得しなおしでも同じ設定で並び替える（画面を開きなおすと初期状態に戻る）
    tb.sort = {
        key: null,
        order: null // 'ASC' / 'DESC'
    };

    // ページング
    tb.paging = {
        pageNum: 1, // 表示するページ
        pageMaxNum: 1, // 最大ページ数
        num: 0, // 件数
        onePageNum: DataTablePF.defaultOnePageNum
    };

    // 1頁に表示する数（table.jsと同じ設定を引き継ぐ）
    // ページングを行わない場合は、1回の取得件数（params.limit）をそのまま使う
    if ( !tb.pagingFlag ) {
        tb.paging.onePageNum = Number( params.limit ) || DataTablePF.defaultFetchLimit;
    } else if ( option.onePageNum ) {
        tb.paging.onePageNum = Number( option.onePageNum );
    } else {
        const onePageNum = fn.storage.get('onePageNum', 'local', false );
        if ( onePageNum ) tb.paging.onePageNum = Number( onePageNum );
    }

    // 待機中
    tb.workType = '';
    tb.workTimer = null;
    // 選択した行に対する処理中（確認中も含む。処理が終わるまでボタンを押せないようにする）
    tb.selectBusy = false;
}
/*
##################################################
    Work check
    > 非同期イベントの状態
##################################################
*/
// type … 'table'で行を隠して読み込み中を表示する（初回の読み込み）
//        'update'で行を残したまま読み込み中を重ねる（ページの切り替え・再読込）
// time … 読み込みが早く終わったときに読み込み中を見せないための遅延（0で即時）
workStart( type, time = 50 ) {
    const tb = this;
    if ( tb.workType ) return;

    // 読み込み中になったら
    tb.$.window.trigger( tb.id + '__tableStandBy');

    tb.workType = type;

    const standBy = function() {
        tb.$.container.removeClass('noData');
        tb.$.message.empty();
        tb.$.container.addClass(`standBy ${tb.workType}StandBy`);
    };

    if ( time > 0 ) {
        // 画面上の待機状態タイミングを遅らせる
        tb.workTimer = setTimeout( function() {
            standBy();
        }, time );
    } else {
        standBy();
    }
}
workEnd() {
    const tb = this;
    if ( tb.workTimer ) clearTimeout( tb.workTimer );
    tb.$.container.removeClass(`standBy ${tb.workType}StandBy`);

    // 完了したら
    tb.$.window.trigger( tb.id + '__tableReady');

    tb.workType = '';
}
get checkWork() {
    return ( this.workType !== '');
}
/*
##################################################
    Main HTML
##################################################
*/
mainHtml() {
    const tb = this;

    return ``
    + `<div id="${tb.id}" class="tableContainer viewTable standardTable pfTable">`
        + `<div class="tableHeader"></div>`
        + `<div class="tableBody tableVertical">`
            + `<div class="tableWrap">`
                + `<div class="tableBorder">`
                    + `<table class="table mainTable">`
                        + `<thead class="thead">${tb.theadHtml()}</thead>`
                        + `<tbody class="tbody"></tbody>`
                    + `</table>`
                + `</div>`
            + `</div>`
            + `<div class="tableMessage"></div>`
        + `</div>`
        + `<div class="tableFooter${( tb.noticeFlag )? ' tableFooterNotice': ''}">${tb.footerHtml()}</div>`
        + `<div class="tableErrorMessage"></div>`
        + `<div class="tableLoading"></div>`
        + `<style class="tableStyle">${tb.styleHtml()}</style>`
    + `</div>`;
}
/*
##################################################
    Setup
    > $containerを返すので、呼び出し側で画面へ追加する
##################################################
*/
setup() {
    const tb = this;

    // jQueryオブジェクトキャッシュ
    tb.$ = {};
    tb.$.window = $( window );
    tb.$.container = $( tb.mainHtml() );
    tb.$.header = tb.$.container.find('.tableHeader');
    tb.$.body = tb.$.container.find('.tableBody');
    tb.$.wrap = tb.$.container.find('.tableWrap');
    tb.$.table = tb.$.container.find('.table');
    tb.$.thead = tb.$.container.find('.thead');
    tb.$.tbody = tb.$.container.find('.tbody');
    tb.$.footer = tb.$.container.find('.tableFooter');
    tb.$.message = tb.$.container.find('.tableMessage');
    tb.$.errorMessage = tb.$.container.find('.tableErrorMessage');
    tb.$.style = tb.$.container.find('.tableStyle');

    // Table headerメニュー（再読込・行の選択によらないボタン・選択した行に対するボタン・削除）
    const menuMainList = [
        { button: { icon: 'update01', text: getMessage.FTE01047, type: 'tableReload', action: 'default'}}
    ];
    // インポート・エクスポートのボタンはメニューの右側（Sub）へ置く。
    // エクスポートは選択した行が対象のため、行が選択されるまで押せない（updateSelectStatusで切り替える）
    const menuSubList = [];
    if ( fn.typeof( tb.option.importAction ) === 'function') {
        menuSubList.push({ button: { icon: 'import', text: getMessage.FTE14073, type: 'tableImport',
            action: 'default', className: 'pfTableImportButton'}});
    }
    if ( fn.typeof( tb.option.exportAction ) === 'function') {
        menuSubList.push({ button: { icon: 'export', text: getMessage.FTE14074, type: 'tableExport',
            action: 'default', className: 'pfTableSelectButton', disabled: true}});
    }
    // 行の選択によらないボタン（登録など）は、再読込の右側に置く
    for ( const item of tb.headerMenu ) {
        menuMainList.push({ button: { icon: item.icon, text: item.text, type: item.type,
            action: fn.cv( item.action, 'default'), className: 'pfTableHeaderMenuButton'}, separate: true});
    }
    // 選択した行に対するボタンは、行が選択されるまで押せない（updateSelectStatusで切り替える）
    for ( const item of tb.selectMenu ) {
        menuMainList.push({ button: { icon: item.icon, text: item.text, type: item.type,
            action: fn.cv( item.action, 'default'), className: 'pfTableSelectButton',
            disabled: true}});
    }
    if ( fn.typeof( tb.option.deleteAction ) === 'function') {
        menuMainList.push({ button: { icon: 'trash', text: getMessage.FTE00188, type: 'tableDelete',
            action: 'danger', className: 'pfTableSelectButton', disabled: true }, separate: true });
    }
    tb.$.header.html( fn.html.operationMenu({ Main: menuMainList, Sub: menuSubList }));

    tb.$.header.find('.itaButton[data-type="tableReload"]').on('click', function(){
        if ( !tb.checkWork ) tb.reload();
    });
    tb.setHeaderMenuActionEvent();
    tb.setSelectActionEvent();

    tb.setPagingEvent();
    tb.setTableEvents();
    tb.updateFooterStatus();

    tb.workStart('table', 0 );
    tb.requestBody();

    return tb.$.container;
}
/*
##################################################
    Table内各種イベント
##################################################
*/
setTableEvents() {
    const tb = this;

    // 行の選択（チェックボックス）
    if ( tb.selectFlag ) tb.setSelectEvent();

    // 見出しのクリックによる並び替え
    if ( tb.sortFlag ) tb.setSortEvent();

    // 行ごとのボタン（rowMenuActionが指定された場合のみ）
    if ( fn.typeof( tb.option.rowMenuAction ) !== 'function') return;

    tb.$.tbody.on('click', '.pfTableRowMenuButton', function(){
        if ( tb.checkWork ) return;

        const $button = $( this ),
              index = Number( $button.closest('.tBodyTr').attr('data-index') ),
              item = tb.data.body?.[ index ];
        if ( item !== undefined ) tb.option.rowMenuAction( $button.attr('data-type'), item );
    });
}
/*
##################################################
    行の選択
##################################################
*/
setSelectEvent() {
    const tb = this;

    // 見出しの一括選択（ボタンの外側がクリックされた場合もボタンを押したことにする）
    tb.$.thead.on('click', '.tHeadRowSelect', function( e ){
        if ( tb.checkWork ) return;
        if ( !$( e.target ).closest('.rowSelectButton').length ) {
            $( this ).find('.rowSelectButton').focus().click();
        }
    });
    tb.$.thead.on('click', '.rowSelectButton', function(){
        if ( tb.checkWork ) return;

        // 選択されていないときは全選択、それ以外（一部・すべて選択）は選択を解除する
        const checked = ( $( this ).attr('data-select') === 'not');
        tb.$.tbody.find('.pfTableRowCheck').prop('checked', checked );
        tb.updateSelectStatus();
    });

    // セルのどこをクリックしてもチェックを切り替える
    tb.$.tbody.on('click', '.tBodyRowSelect', function( e ){
        if ( tb.checkWork ) return;
        if ( !$( e.target ).closest('.checkboxWrap').length ) {
            const $check = $( this ).find('.pfTableRowCheck');
            $check.focus().prop('checked', !$check.prop('checked') ).change();
        }
    });
    tb.$.tbody.on('change', '.pfTableRowCheck', function(){
        tb.updateSelectStatus();
    });
}
// 一括選択ボタンの見た目と、選択した行に対するボタン（有効化・無効化・削除など）の活性状態を更新する
updateSelectStatus() {
    const tb = this;
    if ( !tb.selectFlag ) return;

    const length = tb.$.tbody.find('.pfTableRowCheck').length,
          checkedLength = tb.$.tbody.find('.pfTableRowCheck:checked').length;

    tb.$.thead.find('.rowSelectButton').attr('data-select',
        ( length && length === checkedLength )? 'all': ( checkedLength )? 'oneOrMore': 'not');

    // 行を1つでも選択している場合のみ実行できる（処理中は押せない）
    tb.$.header.find('.pfTableSelectButton')
        .prop('disabled', ( tb.selectBusy || checkedLength === 0 ) );
}
// 選択されている行のデータ（表示しているページ内のみ）
get selectedItems() {
    const tb = this;

    const items = [];
    tb.$.tbody.find('.pfTableRowCheck:checked').each(function(){
        const item = tb.data.body?.[ Number( $( this ).val() ) ];
        if ( item !== undefined ) items.push( item );
    });
    return items;
}
/*
##################################################
    行の選択によらない処理（登録・インポートなど）
##################################################
*/
// 処理そのものは option.headerMenuAction / option.importAction（ダイアログ・API呼び出し）に任せ、
// 処理の前後のボタン制御と、結果を反映するための取得しなおしを行う。
// インポートも行の選択によらない処理のため、同じ流れで扱う（ボタンの位置だけが違う）。
setHeaderMenuActionEvent() {
    const tb = this;

    tb.$.header.on('click', '.pfTableHeaderMenuButton, .pfTableImportButton', async function(){
        if ( tb.checkWork || tb.selectBusy ) return;

        const $button = $( this ),
              importFlag = $button.is('.pfTableImportButton'),
              action = ( importFlag )? tb.option.importAction: tb.option.headerMenuAction;
        if ( fn.typeof( action ) !== 'function') return;

        // 処理の間は続けて押されないようにする（Tableは待機状態にせず一覧は表示したままにする）
        tb.selectBusy = true;
        tb.headerMenuDisabled();
        tb.updateSelectStatus();
        tb.rowMenuDisabled();

        let result;
        try {
            // インポートは対象が一覧の中に無いため、どのボタンかは渡さない
            result = ( importFlag )? await action(): await action( $button.attr('data-type') );
        } catch ( error ) {
            console.error( error );
            result = false;
        }
        tb.selectBusy = false;
        tb.headerMenuDisabled( false );
        tb.rowMenuDisabled( false );
        tb.updateSelectStatus();

        // 処理した内容が反映されるように取得しなおす（キャンセルされた場合はそのままにする）
        if ( result !== false ) tb.reload();
    });
}
/*
##################################################
    選択した行に対する処理（有効化・無効化・エクスポート・削除など）
##################################################
*/
// 処理そのものは option.selectMenuAction / option.exportAction / option.deleteAction
// （確認・API呼び出し）に任せ、処理の前後のボタン制御と、結果を反映するための取得しなおしを行う。
setSelectActionEvent() {
    const tb = this;

    tb.$.header.on('click', '.pfTableSelectButton', async function(){
        if ( tb.checkWork || tb.selectBusy ) return;

        const type = $( this ).attr('data-type'),
              items = tb.selectedItems;
        if ( !items.length ) return;

        // 削除・エクスポートは選択した行だけを渡す（どのボタンかは渡さない）
        const itemsOnly = ( type === 'tableDelete' || type === 'tableExport'),
              action = ( type === 'tableDelete')? tb.option.deleteAction
                  : ( type === 'tableExport')? tb.option.exportAction
                  : tb.option.selectMenuAction;
        if ( fn.typeof( action ) !== 'function') return;

        // 処理の間は続けて押されないようにする（Tableは待機状態にせず一覧は表示したままにする）
        tb.selectBusy = true;
        tb.updateSelectStatus();
        tb.headerMenuDisabled();
        tb.rowMenuDisabled();

        let result;
        try {
            result = ( itemsOnly )? await action( items ): await action( type, items );
        } catch ( error ) {
            console.error( error );
            result = false;
        }
        tb.selectBusy = false;
        tb.headerMenuDisabled( false );
        tb.rowMenuDisabled( false );

        // 処理した内容が反映されるように取得しなおす（キャンセルされた場合は選択したままにする）
        if ( result !== false ) {
            tb.reload();
        } else {
            tb.updateSelectStatus();
        }
    });
}
// 行の選択によらないボタン（登録・インポートなど）を使用不可にする。
// 他の処理中に押されるのを防ぐために使う。
headerMenuDisabled( disabled = true ) {
    this.$.header.find('.pfTableHeaderMenuButton, .pfTableImportButton').prop('disabled', !!disabled );
}
// 行のボタンをまとめて使用不可にする。ボタンを押したあとの処理中に、続けて押されるのを
// 防ぐために使う（Tableを待機状態にすると一覧が見えなくなるため、ボタンだけを止める）。
rowMenuDisabled( disabled = true ) {
    this.$.tbody.find('.pfTableRowMenuButton').prop('disabled', !!disabled );
}
/*
##################################################
    Style（カラム幅）
##################################################
*/
// 列の幅はセルの中身（.ci）の幅で決める（列そのものの幅指定はCSSの .pfTable .mainTable が受け持つ）。
//   width指定の列    … 最大幅（内容物がそれより短ければ内容物の幅、超えれば省略表示）
//   minWidth指定の列 … 最小幅（表示領域が広い場合は余った幅に合わせて広がる）
styleHtml() {
    const tb = this;

    const style = [];
    for ( const column of tb.columns ) {
        if ( column.minWidth ) {
            // 広がる列は既定の最大幅（common.cssの .tbody .ci）で止まらないようにする
            style.push(`#${tb.id} .tbody .ci[data-key="${column.key}"]`
            + `{min-width:${column.minWidth};max-width:none}`);
        } else if ( column.width ) {
            style.push(`#${tb.id} .tbody .ci[data-key="${column.key}"]{max-width:${column.width}}`);
        }
    }
    return style.join('');
}
/*
##################################################
    tHead HTML
##################################################
*/
theadHtml() {
    const tb = this;

    const html = [];
    for ( const column of tb.columns ) {
        // 選択用の列の見出しは一括選択ボタン
        if ( column.select ) {
            html.push( fn.html.cell( fn.html.button('', 'rowSelectButton', { select: 'not'}),
                ['tHeadTh', 'tHeadLeftSticky', 'tHeadRowSelect'], 'th'));
            continue;
        }

        const className = ['tHeadTh'];
        if ( column.type === 'number') className.push('tBodyTdNumber');
        // 余った幅を受け持つ列（見出しと本体の両方に付ける）
        if ( column.minWidth ) className.push('pfTableFlexColumn');

        const attrs = { key: column.key };

        let name = fn.cv( column.name, '', true );
        // 並び替えできる列には、現在の並び順を表す記し（table.jsと同じ .tHeadSort）を付ける
        if ( tb.isSortColumn( column ) ) {
            className.push('tHeadSort');
            name += `<span class="tHeadSortMark"></span>`;
            if ( tb.sort.key === column.key ) attrs.sort = tb.sort.order;
        }
        html.push( fn.html.cell( name, className, 'th', 1, 1, attrs ));
    }
    return fn.html.row( html.join(''), ['tHeadTr', 'headerTr']);
}
/*
##################################################
    並び替え
##################################################
*/
// 見出しをクリックして並び替えできる列か
// （選択用の列・行のボタンの列など、sort: false を指定した列は並び替えできない）
isSortColumn( column ) {
    return ( this.sortFlag && column.select !== true && column.sort !== false );
}
// 見出しをクリックするたびに降順→昇順で切り替え、取得済みの一覧を並び替えて表示しなおす
// （APIからの取得はしない）。
setSortEvent() {
    const tb = this;

    tb.$.thead.on('click', '.tHeadSort', function(){
        // 他の処理中（登録・削除など）は、行を作りなおすとボタンの制御が戻ってしまうため並び替えない
        if ( tb.checkWork || tb.selectBusy || !tb.data.body ) return;

        const $th = $( this ),
              order = ( $th.attr('data-sort') === 'DESC')? 'ASC': 'DESC';

        // 並び替えは1つの列のみ（他の列の記しは消す）
        tb.$.thead.find('.tHeadSort').removeAttr('data-sort');
        $th.attr('data-sort', order );

        tb.sort = { key: $th.attr('data-key'), order: order };

        // 行を作りなおすとチェックが外れるため、選択していた行は選びなおす
        const selectedItems = tb.selectedItems;

        // 並び替えは取得済みの一覧に対して行うためすぐ終わる（setBodyの中でworkEndする）
        tb.workStart('sort', 0 );
        tb.setBody();
        tb.restoreSelect( selectedItems );
    });
}
// 取得済みの一覧（tb.data.body）を並び替えの設定に従って並べ替える。
// 表示のたびに呼ぶため、再読込や処理後の取得しなおしでも同じ並び順になる。
sortBody() {
    const tb = this;
    if ( !tb.sortFlag || !tb.sort.key || fn.typeof( tb.data.body ) !== 'array') return;

    const column = tb.columns.find( ( item ) => item.key === tb.sort.key );
    if ( !column || !tb.isSortColumn( column ) ) return;

    // 値が同じ行はAPIから取得した順のまま（Array#sortは安定）
    const sign = ( tb.sort.order === 'ASC')? 1: -1;
    tb.data.body.sort( ( a, b ) => sign * DataTablePF.compareValue( a[ column.key ], b[ column.key ], column ) );
}
// 昇順で並べたときの前後を返す（aが先なら負の数）。値が無いものは一番小さいものとして扱うため、
// 降順のときは末尾に集まる。
static compareValue( a, b, column ) {
    const emptyA = ( a === null || a === undefined || a === ''),
          emptyB = ( b === null || b === undefined || b === '');
    if ( emptyA || emptyB ) return ( emptyA && emptyB )? 0: ( emptyA )? -1: 1;

    if ( column.type === 'number') {
        const numberA = Number( a ),
              numberB = Number( b );
        if ( !Number.isNaN( numberA ) && !Number.isNaN( numberB ) ) return numberA - numberB;
    } else if ( column.type === 'date' || column.type === 'datetime') {
        const timeA = DataTablePF.sortTime( a ),
              timeB = DataTablePF.sortTime( b );
        if ( timeA !== null && timeB !== null ) return timeA - timeB;
    } else if ( typeof a === 'boolean' && typeof b === 'boolean') {
        // 有効・無効などの真偽値はfalseを小さいものとして扱う
        return ( a === b )? 0: ( a )? 1: -1;
    }

    // 上記で比べられないもの（日付として読めない値など）は文字列として比べる
    // （大文字・小文字は区別せず、文字列中の数値は数値として扱う）
    return String( a ).localeCompare( String( b ), undefined, { numeric: true, sensitivity: 'base'});
}
// 日付の比較に使う時刻（数値）。読めない場合はnullを返す
static sortTime( value ) {
    let date = value;
    // fn.dateと同じ形式（yyyy/MM/dd HH:mm:ss）も読めるようにする
    if ( typeof date === 'string' && date.match(/^[0-9]{4}\/(0[1-9]|1[0-2])\/(0[1-9]|[12][0-9]|3[01])\s/) ) {
        date = date.replace(/\//g, '-').replace(/\s/, 'T');
    }
    const time = new Date( date ).getTime();
    return ( Number.isNaN( time ) )? null: time;
}
// 並び替えのあとに、選択していた行（並び替える前のデータ）を選びなおす
restoreSelect( items ) {
    const tb = this;
    if ( !tb.selectFlag || !items.length ) return;

    tb.$.tbody.find('.pfTableRowCheck').each(function(){
        const item = tb.data.body?.[ Number( $( this ).val() ) ];
        if ( item !== undefined && items.indexOf( item ) !== -1 ) $( this ).prop('checked', true );
    });
    tb.updateSelectStatus();
}
/*
##################################################
    tBody HTML
##################################################
*/
tbodyHtml() {
    const tb = this,
          list = tb.data.body;

    const html = [];
    for ( let i = 0; i < list.length; i++ ) {
        const rowHtml = [];
        for ( const column of tb.columns ) {
            rowHtml.push( tb.cellHtml( list[i], column, i ) );
        }
        // 行のボタン（rowMenu）から元データを引けるよう、行番号を持たせる
        html.push(`<tr class="tBodyTr tr" data-index="${i}">${rowHtml.join('')}</tr>`);
    }
    return html.join('');
}
/*
##################################################
    Cell HTML
##################################################
*/
cellHtml( item, column, index ) {
    const tb = this;

    // 選択用の列はチェックボックス（値は行番号。選択した行のデータは selectedItems で引く）
    if ( column.select ) {
        const name = `${tb.id}__ROWCHECK`,
              checkbox = fn.html.check('pfTableRowCheck', index, name, `${name}__${index}`);
        return fn.html.cell( checkbox, ['tBodyLeftSticky', 'tBodyRowSelect', 'tBodyTh'], 'th');
    }

    const className = ['tBodyTd'];
    if ( column.type === 'number') className.push('tBodyTdNumber');
    if ( column.minWidth ) className.push('pfTableFlexColumn');
    if ( column.className ) className.push( column.className );

    // セルの中身（.ci）はカラム幅のstyleで参照するためkeyを持たせる
    const ciClassName = ['ci'];
    if ( column.wrap ) ciClassName.push('textOverWrap');

    let value;
    if ( fn.typeof( column.cell ) === 'function') {
        // 独自描画（エスケープはカラム定義側の責任）
        value = column.cell( item, column );
    } else {
        value = tb.cellValue( item[ column.key ], column );
    }

    return ``
    + `<td class="${className.join(' ')} td" data-key="${fn.escape( column.key )}">`
        + `<div class="${ciClassName.join(' ')}" data-key="${fn.escape( column.key )}">${value}</div>`
    + `</td>`;
}
// 値をカラムの型に合わせた表示文字列（エスケープ済み）へ変換する
cellValue( value, column ) {
    switch ( column.type ) {
        case 'date':
            return fn.escape( fn.date( fn.cv( value, ''), 'yyyy/MM/dd') );
        case 'datetime':
            return fn.escape( fn.date( fn.cv( value, ''), 'yyyy/MM/dd HH:mm:ss') );
        case 'number': {
            const number = Number( value );
            return ( value === null || value === undefined || value === '' || Number.isNaN( number ) )
                ? '': String( number.toLocaleString() );
        }
        default:
            return fn.cv( value, '', true );
    }
}
/*
##################################################
    Footer HTML
##################################################
*/
footerHtml() {
    const tb = this;

    // ページングを行わない場合は件数だけを表示する（1ページの件数・ページ移動は置かない）
    if ( !tb.pagingFlag ) {
        return `
        <div class="tableFooterInner">
            <div class="tableFooterBlock pagingAllNum">
                <dl class="tableFooterList">
                    <dt class="tableFooterTitle"><span class="footerText pagingAllTitle">` + getMessage.FTE10029 + `</span></dt>
                    <dd class="tableFooterItem tableFooterData"><span class="footerText pagingAllNumNumber">` + getMessage.FTE00059 + `</span></dd>
                </dl>
            </div>
            ${tb.footerNoticeHtml()}
        </div>`;
    }

    const onePageNumOptions = [];
    for ( const item of DataTablePF.onePageNumList ) {
        const id = `${tb.id}_pagingOnePageNumSelectRadio_${item}`,
              name = `${tb.id}_pagingOnePageNumSelectRadio`;
        onePageNumOptions.push(`<li class="pagingOnePageNumSelectItem">`
        + `<input class="pagingOnePageNumSelectRadio" type="radio" id="${id}" name="${name}" value="${item}">`
        + `<label class="pagingOnePageNumSelectLabel" for="${id}">${item}</label></li>`);
    }

    return `
    <div class="tableFooterInner">
        <div class="tableFooterBlock pagingAllNum">
            <dl class="tableFooterList">
                <dt class="tableFooterTitle"><span class="footerText pagingAllTitle">` + getMessage.FTE10029 + `</span></dt>
                <dd class="tableFooterItem tableFooterData"><span class="footerText pagingAllNumNumber">` + getMessage.FTE00059 + `</span></dd>
            </dl>
        </div>
        ${tb.footerNoticeHtml()}
        <div class="tableFooterBlock pagingOnePageNum">
            <dl class="tableFooterList">
                <dt class="tableFooterTitle"><span class="footerText">` + getMessage.FTE00060 + `</span></dt>
                <dd class="tableFooterItem tableFooterData">
                    <div class="pagingOnePageNumSelect">
                        <div class="pagingOnePageNumSelectNumber"></div>
                        <ul class="pagingOnePageNumSelectList">
                            ${onePageNumOptions.join('')}
                        </ul>
                    </div>
                </dd>
            </dl>
        </div>
        <div class="tableFooterBlock pagingMove">
            <ul class="tableFooterList">
                <li class="tableFooterItem">
                    <button class="pagingMoveButton" data-type="first" disabled>${fn.html.icon('first')}</button>
                </li>
                <li class="tableFooterItem">
                    <button class="pagingMoveButton" data-type="prev" disabled>${fn.html.icon('prev')}</button>
                </li>
                <li class="tableFooterItem">
                    <div class="pagingPage">
                        <span class="pagingCurrentPage">0</span>
                        <span class="pagingSeparate">/</span>
                        <span class="pagingMaxPageNumber">0</span>
                        <span class="pagingPageJumpNumber">` + getMessage.FTE00061 + `</span>
                    </div>
                </li>
                <li class="tableFooterItem">
                    <button class="pagingMoveButton" data-type="next" disabled>${fn.html.icon('next')}</button>
                </li>
                <li class="tableFooterItem">
                    <button class="pagingMoveButton" data-type="last" disabled>${fn.html.icon('last')}</button>
                </li>
            </ul>
        </div>
    </div>`;
}
// 件数の右側に置く案内（件数に応じた文言は、一覧を取得しなおすたびに updateNotice で入れ替える）。
// 件数が分かるまで（取得できなかった場合も）表示しない
footerNoticeHtml() {
    const tb = this;
    if ( !tb.noticeFlag ) return '';

    return `
        <div class="tableFooterBlock pfTableNotice" style="display: none;">
            <div class="tableFooterList">
                <div class="tableFooterItem pfTableNoticeInner">
                    <span class="pfTableNoticeIcon"></span>
                    <span class="footerText pfTableNoticeText"></span>
                </div>
            </div>
        </div>`;
}
/*
##################################################
   Update footer status
   > Table情報を更新する
##################################################
*/
updateFooterStatus() {
    const tb = this;

    tb.$.footer.find('.pagingAllNumNumber')
        .text( tb.paging.num.toLocaleString() + getMessage.FTE00063 );

    // ページングを行わない場合は件数以外の表示が無い
    if ( !tb.pagingFlag ) return;

    tb.$.footer.find('.pagingOnePageNumSelectRadio').val([ tb.paging.onePageNum ]);
    tb.$.footer.find('.pagingOnePageNumSelectNumber').text( tb.paging.onePageNum );

    const $paging = tb.$.footer.find('.pagingMove');
    $paging.find('.pagingCurrentPage').text( tb.paging.pageNum );
    $paging.find('.pagingMaxPageNumber').text( tb.paging.pageMaxNum.toLocaleString() );

    const prevFlag = ( tb.paging.pageNum <= 1 );
    $paging.find('.pagingMoveButton[data-type="first"], .pagingMoveButton[data-type="prev"]')
        .prop('disabled', prevFlag );

    const nextFlag = ( tb.paging.pageMaxNum === tb.paging.pageNum );
    $paging.find('.pagingMoveButton[data-type="last"], .pagingMoveButton[data-type="next"]')
        .prop('disabled', nextFlag );
}
/*
##################################################
   Paging event
##################################################
*/
setPagingEvent() {
    const tb = this;

    // ページングを行わない場合は操作する要素そのものが無い
    if ( !tb.pagingFlag ) return;

    const $list = tb.$.footer.find('.pagingOnePageNumSelectList');

    tb.$.footer.find('.pagingMoveButton').on('click', function(){
        if ( tb.checkWork ) return;

        const type = $( this ).attr('data-type');
        switch ( type ) {
            case 'first':
                tb.paging.pageNum = 1;
            break;
            case 'last':
                tb.paging.pageNum = tb.paging.pageMaxNum;
            break;
            case 'prev':
                tb.paging.pageNum -= 1;
            break;
            case 'next':
                tb.paging.pageNum += 1;
            break;
        }
        // ページの切り替えは、その都度APIから該当ページ分を取得する
        // 取得中も表示中の行はそのまま残す（一瞬テーブルが消えるのを防ぐ）
        tb.workStart('update', 200 );
        tb.requestBody();
    });

    tb.$.footer.find('.pagingOnePageNumSelectRadio').on('change', function(){
        if ( tb.checkWork ) return;

        const selectNo = Number( $( this ).val() );
        tb.paging.onePageNum = selectNo;
        tb.$.footer.find('.pagingOnePageNumSelectNumber').text( selectNo );
        $list.removeClass('pagingOnePageOpen');
        fn.storage.set('onePageNum', selectNo, 'local', false );

        // 1ページの件数が変わるとページの区切りも変わるため、先頭ページから取得しなおす
        tb.paging.pageNum = 1;
        tb.workStart('update', 200 );
        tb.requestBody();
    });

    tb.$.footer.find('.pagingOnePageNumSelectNumber').on('click', function(){
        if ( tb.checkWork ) return;

        if ( !$list.is('.pagingOnePageOpen') ) {
            const height = tb.$.header.outerHeight() + tb.$.body.outerHeight();
            $list.addClass('pagingOnePageOpen').css('max-height', height );
            $( window ).on(`pointerdown.${tb.id}_pagingOnePageNum`, function(e){
                if ( !$( e.target ).closest('.pagingOnePageNumSelect').length ) {
                    $( this ).off(`pointerdown.${tb.id}_pagingOnePageNum`);
                    $list.removeClass('pagingOnePageOpen');
                }
            });
        } else {
            $list.removeClass('pagingOnePageOpen');
            $( window ).off(`pointerdown.${tb.id}_pagingOnePageNum`);
        }
    });
}
/*
##################################################
   一覧の取得（サーバーサイドページング）
##################################################
*/
// 表示するページ（tb.paging.pageNum）の分だけAPIから取得して表示する。
// retryFlag … 表示中のページが無くなっていた場合に、別のページへ移して取得しなおしたか（1度だけ）
async requestBody( retryFlag = false ) {
    const tb = this;

    const onePageNum = tb.paging.onePageNum,
          offset = ( tb.paging.pageNum - 1 ) * onePageNum;

    try {
        const data = await tb.request( tb.params.rest( onePageNum, offset ) );

        const list = ( fn.typeof( tb.params.list ) === 'function')
            ? tb.params.list( data )
            : data;
        const rows = ( fn.typeof( list ) === 'array')? list: [];

        const total = Number( fn.cv( tb.params.total( data ), 0 ) );

        // 削除などで表示中のページが無くなっていた場合は、存在する最後のページへ移して取得しなおす
        if ( !rows.length && tb.paging.pageNum > 1 && !retryFlag ) {
            tb.paging.pageNum = ( total > 0 )? Math.ceil( total / onePageNum ): 1;
            return tb.requestBody( true );
        }

        tb.data.body = rows;
        tb.paging.num = total;
        tb.paging.pageMaxNum = Math.max( Math.ceil( total / onePageNum ), 1 );

        tb.setBody();
    } catch ( error ) {
        tb.error( error );
    }
}
/*
##################################################
   Set tBody
##################################################
*/
setBody() {
    const tb = this;

    tb.$.container.removeClass('tableError');
    tb.$.errorMessage.empty();

    // 並び替えの設定があれば、行を作る前に並べ替える（再読込したあとも同じ並び順にする）
    tb.sortBody();

    // 表示するものがない
    if ( !tb.data.body.length ) {
        tb.$.container.addClass('noData');
        tb.$.message.html(`<div class="noDataMessage">`
        + fn.html.icon('stop')
        + getMessage.FTE00054
        + `</div>`);
    } else {
        tb.$.container.removeClass('noData');
        tb.$.message.empty();
    }

    tb.$.tbody.html( tb.tbodyHtml() );
    // 行を作りなおすと選択は解除されるため、選択に応じたボタンの状態も戻す
    tb.updateSelectStatus();
    tb.updateFooterStatus();
    tb.updateNotice();

    tb.$.wrap.scrollTop(0);
    tb.workEnd();

    tb.$.table.addClass('tableReady');
}
/*
##################################################
   案内（フッターの件数の右側に表示する件数などのお知らせ）
##################################################
*/
// option.notice が返す内容をフッターへ表示する（一覧を取得しなおすたびに呼ぶ）。
//   { icon, text, alert } … text は呼び出し側でエスケープしたHTML。
//                           alert が true のときは注意を促す表示にする。
// 何も返さない場合は表示しない。
updateNotice() {
    const tb = this;
    if ( !tb.noticeFlag ) return;

    const $notice = tb.$.footer.find('.pfTableNotice');
    const notice = tb.option.notice( tb.paging.num );
    if ( !notice || !notice.text ) {
        $notice.hide();
        return;
    }
    $notice.find('.pfTableNoticeIcon').html( fn.html.icon( fn.cv( notice.icon, 'circle_info') ) );

    // フッターは1行のため、幅が足りない場合は末尾を省略する（全文はツールチップで見られるようにする）
    const $text = $notice.find('.pfTableNoticeText').html( notice.text );
    $text.attr('title', $text.text() );

    $notice.toggleClass('pfTableNoticeAlert', notice.alert === true ).show();
}
/*
##################################################
   再読込
##################################################
*/
reload() {
    const tb = this;

    // ボタンを押したことが分かるようにすぐ読み込み中にするが、行は残したままにする
    tb.workStart('update', 0 );
    tb.requestBody();
}
/*
##################################################
   エラー表示
##################################################
*/
error( error ) {
    const tb = this;

    console.error( error );

    tb.data.body = [];
    tb.$.tbody.empty();
    tb.updateSelectStatus();
    tb.$.container.addClass('tableError');
    tb.$.errorMessage.html(``
    + `<div class="errorBorder"></div>`
    + `<div class="errorTableContainer">`
        + `<div class="errorTitle">`
            + `<span class="errorTitleInner">${fn.html.icon('circle_exclamation')}`
                + `${fn.cv( tb.option.errorTitle, getMessage.FTE14034, true )}</span>`
        + `</div>`
        + `<table class="table errorTable">`
            + `<tbody class="tbody">`
                + `<tr class="tBodyTr tr">`
                    + `<td class="tBodyTd td">`
                        + `<div class="ci textOverWrap">${fn.escape( fn.cv( error?.message, ''), true )}</div>`
                    + `</td>`
                + `</tr>`
            + `</tbody>`
        + `</table>`
    + `</div>`);

    tb.workEnd();
    tb.$.table.addClass('tableReady');
}
/*
##################################################
   プラットフォームAPIへのリクエスト
##################################################
*/
// 応答の data だけを返す。
async request( url ) {
    const options = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${DataTablePF.getToken()}`
        }
    };

    // AIアシスタントと同じ条件で再送する（AiAssistantChatが読み込まれていない画面では素のfetch）
    const response = ( typeof AiAssistantChat !== 'undefined')
        ? await AiAssistantChat.fetchWithRetry( url, options, { retryStatuses: DataTablePF.retryStatuses })
        : await fetch( url, options );

    const json = await response.json().catch( () => null );
    if ( !response.ok ) {
        // platform APIはエラー時も message を返すため、あればそれを利用する
        const error = new Error( json?.message ?? `DataTablePF request failed: ${response.status}`);
        error.status = response.status;
        throw error;
    }
    // 応答は { result, message, ts, data } の形なので data のみを返す
    return json?.data ?? {};
}
static getToken() {
    return ( fn.getCmmonAuthFlag() )? CommonAuth.getToken():
        ( window.parent !== window && window.parent.getToken )? window.parent.getToken(): null;
}

}
