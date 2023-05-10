////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Exastro IT Automation / table.js
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

class DataTable {
/*
##################################################
   Constructor
   params {
      menuNameRest: menu
   }
   mode:
      view: 閲覧
      history: 履歴表示
      diff: 結果確認（差分あり）
      select: 選択
      execute: 選択して実行
##################################################
*/
constructor( tableId, mode, info, params, option = {}) {
    const tb = this;
    tb.id = tableId;
    tb.mode = mode;
    tb.initMode = mode;
    tb.info = info;
    tb.params = params;

    // 特殊表示用データ
    tb.option = option;

    // REST API URLs
    tb.rest = {};

    // Filter
    tb.rest.filter = ( tb.params.restFilter )?
         tb.params.restFilter:
        `/menu/${tb.params.menuNameRest}/filter/`;

    // Filter pulldown
    tb.rest.filterPulldown = ( tb.params.restFilterPulldown )?
        tb.params.restFilterPulldown:
        `/menu/${tb.params.menuNameRest}/info/search/candidates/`;

    // Input pulldown
    tb.rest.inputPulldown = ( tb.params.restInputPulldown )?
        tb.params.restInputPulldown:
        `/menu/${tb.params.menuNameRest}/info/pulldown/`;

    // Excel download
    tb.rest.excelDownload = ( tb.params.restExcelDownload )?
        tb.params.restExcelDownload:
        `/menu/${tb.params.menuNameRest}/excel/`;

    // JSON download
    tb.rest.jsonDownload = ( tb.params.restJsonDownload )?
        tb.params.restJsonDownload:
        `/menu/${tb.params.menuNameRest}/filter/`;

    // Maintenance
    tb.rest.maintenance = ( tb.params.restMaintenance )?
        tb.params.restMaintenance:
        `/menu/${tb.params.menuNameRest}/maintenance/all/`;
}
/*
##################################################
   Work check
   > 非同期イベントの状態
##################################################
*/
workStart( type, time = 50 ) {
    const tb = this;
    if ( tb.workType ) window.console.warn('"table.js" workStart() warning.');

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

    tb.workType = undefined;
}
get checkWork() {
    return ( this.workType )? true: false;
}
/*
##################################################
   Table構造データ
##################################################
*/
tableStructuralData() {
    const tb = this;

    tb.structural = {
        column_group_info: {},
        menu_info: []
    };

    const check = function( key ) {
        const hideItem = tb.getTableSettingValue('hideItem');
        if ( hideItem.length ) {
            return ( hideItem.indexOf( key ) === -1 );
        } else {
            return true;
        }
    };

    // menu_info
    for ( const key of tb.info.menu_info[`columns_${tb.tableMode}`] ) {
        if ( check( key ) ) tb.structural.menu_info.push( key );
    }

    // column_group_info
    for ( const itemId in tb.info.column_group_info ) {
        tb.structural.column_group_info[ itemId ] = [];
        for ( const key of tb.info.column_group_info[ itemId ][`columns_${tb.tableMode}`] ) {
            // 特定のモードの場合はボタンカラムを除外する
            const column = tb.info.column_info[ key ];
            if ( ( tb.mode === 'select' || tb.mode === 'execute' || tb.mode === 'history') && column && column.column_type === 'ButtonColumn') {
                continue;
            }
            if ( check( key ) ) tb.structural.column_group_info[itemId].push( key );
        }
        if ( tb.structural.column_group_info[ itemId ].length === 0 ) {
            delete tb.structural.column_group_info[ itemId ];
        }
    }
}
/*
##################################################
   Header hierarchy
   > ヘッダー階層データと列データをセット
##################################################
*/
setHeaderHierarchy() {
    const tb = this;

    // テーブル構造データ
    tb.tableStructuralData();

    // 特殊列
    const specialHeadColumn = [ tb.idNameRest, 'discard'],
          specialFootColumn = ['last_update_date_time', 'last_updated_user'],
          specialHeadColumnKeys = [],
          specialFootColumnKeys = [];

    tb.data.hierarchy = [];
    tb.data.columnKeys = [];
    tb.data.restNames = {};

    // 参照用フィルター
    const referenceFilterColumn = ['host_name', 'base_datetime'];
    tb.data.referenceFilterKeys = [];

    const restOrder = [];

    const hierarchy = function( columns, row ){
        if ( fn.typeof( columns ) !== 'array') return;
        if ( !tb.data.hierarchy[ row ] ) tb.data.hierarchy[ row ] = [];    
        for ( const columnKey of columns ) {
            const type = columnKey.slice( 0, 1 );
            if ( type === 'g') {
                tb.data.hierarchy[ row ].push( columnKey );
                hierarchy( tb.structural.column_group_info[ columnKey ], row + 1 );
            } else if ( type === 'c') {
                const culumnRest =  tb.info.column_info[ columnKey ].column_name_rest;
                tb.data.restNames[ culumnRest ] = tb.info.column_info[ columnKey ].column_name;
                if ( culumnRest === tb.idNameRest ) tb.idName = tb.info.column_info[ columnKey ].column_name;
                if ( specialHeadColumn.indexOf( culumnRest ) !== -1 ) {
                    specialHeadColumnKeys[ specialHeadColumn.indexOf( culumnRest ) ] = columnKey;
                } else if ( specialFootColumn.indexOf( culumnRest ) !== -1 ) {
                    specialFootColumnKeys[ specialFootColumn.indexOf( culumnRest ) ] = columnKey;
                } else {
                    restOrder.push( culumnRest );
                    tb.data.hierarchy[ row ].push( columnKey );
                    tb.data.columnKeys.push( columnKey );
                    if ( referenceFilterColumn.indexOf( culumnRest ) !== -1 ) {
                        tb.data.referenceFilterKeys.push( columnKey );
                    }
                }
            }
        }
    };
    hierarchy( tb.structural.menu_info, 0 );

    // 固定列用情報
    tb.data.sticky = {};
    tb.data.sticky.leftLast = specialHeadColumn[0];
    tb.data.sticky.rightFirst = specialFootColumn[0];
    tb.data.sticky.commonFirst = restOrder[0];
    tb.data.sticky.commonLast = restOrder[ restOrder.length - 1 ];

    // 特殊列を先頭に追加
    for ( const columnKey of specialHeadColumnKeys ) {
        if ( columnKey ) {
            tb.data.hierarchy[0].unshift( columnKey );
            tb.data.columnKeys.unshift( columnKey );
        }
    }
    // 特殊列を末尾に追加
    for ( const columnKey of specialFootColumnKeys ) {
        if ( columnKey ) {
            tb.data.hierarchy[0].push( columnKey );
            tb.data.columnKeys.push( columnKey );
        }
    }
}
/*
##################################################
   Setup
##################################################
*/
setup() {
    const tb = this;

    const html = `
    <div id="${tb.id}" class="tableContainer ${tb.mode}Table ${tb.option.sheetType}Table">
        <div class="tableHeader">
        </div>
        <div class="tableBody">
            <div class="tableFilter"></div>
            <div class="tableWrap">
                <div class="tableBorder">
                    <table class="table mainTable">
                    </table>
                </div>
            </div>
            <div class="tableMessage"></div>
        </div>
        <div class="tableFooter">
            ${tb.footerHtml()}
        </div>
        <div class="tableErrorMessage"></div>
        <div class="tableLoading"></div>
        <style class="tableStyle"></style>
        <style class="tableCustomStyle"></style>
    </div>`;

    // jQueryオブジェクトキャッシュ
    tb.$ = {};
    tb.$.window = $( window );
    tb.$.container = $( html );
    tb.$.header = tb.$.container.find('.tableHeader');
    tb.$.body = tb.$.container.find('.tableBody');
    tb.$.filter = tb.$.container.find('.tableFilter');
    tb.$.footer = tb.$.container.find('.tableFooter');
    tb.$.table = tb.$.container.find('.table');
    tb.$.message = tb.$.container.find('.tableMessage');
    tb.$.errorMessage = tb.$.container.find('.tableErrorMessage');
    tb.$.style = tb.$.container.find('.tableStyle');
    tb.$.custom = tb.$.container.find('.tableCustomStyle');

    // 固有ID
    tb.idNameRest = tb.info.menu_info.pk_column_name_rest;

    // テーブルデータ
    tb.data = {};
    tb.data.count = 0;

    // テーブル表示モード "input" or "view"
    // カラム（column_input or colum_view）
    const tableViewModeList = ['view', 'select', 'execute', 'history'];
    if ( tableViewModeList.indexOf( tb.mode ) !== -1 ) {
        tb.tableMode = 'view';
    } else {
        tb.tableMode = 'input';
    }

    // テーブル設定
    tb.initTableSettingValue();
    tb.setTableSettingValue();

    // tHead階層
    tb.setHeaderHierarchy();

    // Worker
    tb.worker = new Worker(`${tb.params.dir}/js/table_worker.js`);
    tb.setWorkerEvent();

    // ページング
    tb.paging = {};
    tb.paging.num = 0; // 件数
    tb.paging.pageNum = 1; // 表示するページ
    tb.paging.pageMaxNum = 1; // 最大ページ数
    tb.setPagingEvent(); // イベント

    // 1頁に表示する数
    const onePageNum = fn.storage.get('onePageNum');
    if ( onePageNum ) {
        tb.paging.onePageNum = onePageNum;
    } else {
        tb.paging.onePageNum = 25;
    }

    // ソート
    tb.sort = [];

    // 選択データ
    tb.select = {
        view: [],
        edit: [],
        select: [],
        execute: []
    };

    // ドライバータイプ
    if ( tb.params.menuNameRest.match('_ansible_') ) {
        tb.driver = 'ansible';
    } else if ( tb.params.menuNameRest.match('_terraform_') ) {
        tb.driver = 'terraform';
    } else {
        tb.driver = null;
    }

    // 編集データ
    tb.edit = {};
    tb.edit.input = {};
    tb.edit.blank = {};

    // 待機中
    tb.workType = '';
    tb.workTimer = null;

    // フラグ
    tb.flag = fn.editFlag( tb.info.menu_info );

    // 初期フィルタが文字列の場合はパースする
    if ( tb.option.initSetFilter && fn.typeof( tb.option.initSetFilter ) === 'string') {
        try {
            tb.option.initSetFilter = JSON.parse( tb.option.initSetFilter );
            tb.flag.initFilter = true;
        } catch( e ) {
            // 変換に失敗したら無効化
            tb.option.initSetFilter = undefined;
        }
    }

    // モード別
    switch ( tb.mode ) {
        case 'view': case 'edit':
            tb.workStart('table', 0 );
        break;
        case 'select': case 'execute':
            tb.flag.initFilter = true;
            tb.flag.countSkip = true;
        break;
    }

    tb.setTable( tb.mode );

    return tb.$.container;
}
/*
##################################################
   ソート初期値
##################################################
*/
setInitSort() {
    const tb = this;
    if ( tb.info.menu_info.sort_key ) {
        try {
            tb.sort = JSON.parse( tb.info.menu_info.sort_key );
        } catch( e ) {
            window.console.group('JSON parse error.')
            window.console.warn(`menu_info.sort_key : ${tb.info.menu_info.sort_key}`);
            window.console.warn( e );
            window.console.groupEnd('JSON parse error.')
        }
    }
    tb.$.thead.find('.tHeadSort').removeAttr('data-sort');

    const lastSort = tb.sort[ tb.sort.length - 1 ];
    if ( lastSort !== undefined ) {
        const order = Object.keys( lastSort )[0],
              rest = lastSort[ order ];
        tb.$.thead.find(`.tHeadSort[data-rest="${rest}"]`).attr('data-sort', order );
    }
}
/*
##################################################
   Set table
##################################################
*/
setTable( mode ) {
    const tb = this;
    tb.mode = mode;

    tb.$.table.attr('table-mode', tb.tableMode );

    // フィルター位置
    if ( tb.getTableSettingValue('direction') === 'horizontal' || tb.getTableSettingValue('filter') === 'out') {
        tb.$.table.html( tb.commonTableHtml( false ) );
        if ( tb.mode !== 'edit') {
            tb.$.filter.html( tb.filterTableHtml() );
            tb.$.body.addClass('tableFilterOut');
        } else {
            tb.$.filter.empty();
            tb.$.body.removeClass('tableFilterOut');
        }
    } else {
        tb.$.table.html( tb.commonTableHtml( true ) );
        tb.$.filter.empty();
        tb.$.body.removeClass('tableFilterOut');
    }

    // 項目メニュー表示
    if ( tb.getTableSettingValue('menu') === 'show') {
        tb.$.body.addClass('tableItemMenuShow');
    } else {
        tb.$.body.removeClass('tableItemMenuShow');
    }

    // 縦・横
    if ( tb.getTableSettingValue('direction') === 'horizontal') {
        tb.$.body.addClass('tableHorizontal');
    } else {
        tb.$.body.removeClass('tableHorizontal');
    }

    tb.$.thead = tb.$.container.find('.thead');
    tb.$.tbody = tb.$.container.find('.tbody');
    tb.$.thead.find('.filterInputDiscard').select2({
        width: '120px',
        minimumResultsForSearch: 5
    });
    tb.setInitSort();

    // Table headerメニュー
    switch ( tb.mode ) {
        case 'view': case 'select': case 'execute': {
            if ( tb.option.sheetType !== 'reference') {
                const filterInit = ( tb.$.body.is('.filterShow') )? `on`: `off`;
                const menuList = {
                    Main: [],
                    Sub: [
                        { button: { icon: 'filter', text: getMessage.FTE00001, type: 'filterToggle', action: 'default',
                        toggle: { init: filterInit, on:getMessage.FTE00002, off:getMessage.FTE00003}}},
                        { button: { icon: 'gear', text: getMessage.FTE00086, type: 'tableSetting', action: 'default'}}
                    ]
                };
                if ( tb.mode === 'select') {
                    menuList.Main.push({ message: { text: getMessage.FTE00004 }});
                }
                if ( tb.mode === 'execute') {
                    const dryrunText = ( tb.driver === 'ansible')? getMessage.FTE00006: getMessage.FTE00167;
                    menuList.Main.push({ button: { className: 'tableAdvance', icon: 'square_next', text: getMessage.FTE00005, type: 'tableRun', action: 'positive', minWidth: '160px', disabled: true }});
                    menuList.Main.push({ button: { className: 'tableAdvance',icon: 'square_next', text: dryrunText, type: 'tableDryrun', action: 'positive', minWidth: '160px', disabled: true }});
                    menuList.Main.push({ button: { className: 'tableAdvance',icon: 'detail', text: getMessage.FTE00007, type: 'tableParameter', action: 'positive', minWidth: '160px', disabled: true }});
                }
                if ( tb.mode === 'view') {
                    // 権限チェック
                    if ( tb.flag.insert ) {
                        menuList.Main.push({ button: { icon: 'plus', text: getMessage.FTE00008, type: 'tableNew', action: 'positive', minWidth: '200px'}});
                    }
                    if ( tb.flag.update ) {
                        menuList.Main.push({ button: { icon: 'edit', text: getMessage.FTE00009, type: 'tableEdit', action: 'positive', minWidth: '200px', 'disabled': true }});
                    }
                    if ( menuList.Main.length === 0 ) {
                        menuList.Main.push({ message: { text: getMessage.FTE00010 }});
                    }
                }
                tb.$.header.html( fn.html.operationMenu( menuList ) );
            } else {
                // 参照用メニューは専用のフィルターをセット
                tb.$.header.html( tb.referenceFilter() );
            }

            // メニューボタン
            tb.$.header.find('.itaButton').on('click', function(){
                if ( !tb.checkWork ) {
                    const $button = $( this ),
                          type = $button.attr('data-type');
                    switch ( type ) {
                        // フィルタ開閉
                        case 'filterToggle':
                            tb.$.body.toggleClass('filterShow');
                            tb.stickyWidth();
                        break;
                        // テーブル設定
                        case 'tableSetting':
                            tb.tableSettingOpen();
                        break;
                        // 編集モードに移行
                        case 'tableEdit':
                            tb.changeEdtiMode.call( tb );
                        break;
                        // 編集モード（新規登録）
                        case 'tableNew':
                            tb.changeEdtiMode.call( tb, 'changeEditRegi');
                        break;
                        // ドライラン
                        case 'tableDryrun':
                            tb.execute('dryrun');
                        break;
                        // 作業実行
                        case 'tableRun':
                            tb.execute('run');
                        break;
                        // パラメータ確認
                        case 'tableParameter':
                            tb.execute('parameter');
                        break;
                    }
                }
            });
            // tbody表示
            if ( tb.flag.initFilter ) {
                if ( tb.data.body ) {
                    // データがセット済みの場合は表示
                    tb.setTbody();
                } else {
                    // 初期フィルタ設定（プルダウン検索）
                    if ( tb.option.initSetFilter ) {
                        tb.filterSelectParamsOpen( tb.option.initSetFilter ).then( function(){
                            tb.requestTbody();
                        });
                    } else {
                        tb.requestTbody();
                    }
                }
            } else {
                tb.setInitFilterStandBy();
            }
        } break;
        case 'edit': {
            const menuList = {
                Main: [
                    { button: { type: 'tableOk', icon: 'detail', text: getMessage.FTE00011, action: 'positive', minWidth: '200px'}}
                ],
                Sub: [
                    { button: { icon: 'gear', text: getMessage.FTE00086, type: 'tableSetting', action: 'default'}}
                ]
            };
            if ( tb.flag.insert ) {
                menuList.Main.push({ button: { type: 'tableAdd',icon: 'plus', text: getMessage.FTE00012, action: 'default'}, separate: true });
                menuList.Main.push({ button: { type: 'tableDup', icon: 'copy', text: getMessage.FTE00013, action: 'duplicat', disabled: true }});
                menuList.Main.push({ button: { type: 'tableDel', icon: 'minus', text: getMessage.FTE00014, action: 'danger', disabled: true }});
            }
            if ( tb.flag.disuse ) {
                menuList.Main.push({ button: { type: 'tableDiscard', icon: 'cross', text: getMessage.FTE00015, action: 'warning', disabled: true }});
            }
            if ( tb.flag.reuse ) {
                menuList.Main.push({ button: { type: 'tableRestore', icon: 'circle', text: getMessage.FTE00016, action: 'restore', disabled: true }});
            }
            menuList.Main.push({ button: { type: 'tableCancel', icon: 'cross', text: getMessage.FTE00017, action: 'normal'}, separate: true });
            tb.$.header.html( fn.html.operationMenu( menuList ) );

            // メニューボタン
            tb.$.header.find('.itaButton').on('click', function(){
                if ( !tb.checkWork ) {
                    const $button = $( this ),
                          type = $button.attr('data-type');
                    switch ( type ) {
                        // 編集確認
                        case 'tableOk':
                            tb.reflectEdits.call( tb );
                        break;
                        // 行追加
                        case 'tableAdd':
                            const addId = String( tb.edit.addId-- );
                            tb.workStart('add');
                            tb.paging.pageNum = 1;
                            tb.$.body.scrollTop(0);
                            tb.edit.blank.parameter[ tb.idNameRest ] = addId;
                            tb.addRowInputData( addId );
                            tb.workerPost('add', tb.edit.blank );
                        break;
                        // 選択行複製
                        case 'tableDup': {
                            tb.workStart('dup');
                            tb.workerPost('dup', { select: tb.select.edit, id: tb.edit.addId, input: tb.edit.input });
                            tb.edit.addId -= tb.select.edit.length;
                        } break;
                        // 行削除
                        case 'tableDel':
                            tb.workStart('del');
                            tb.workerPost('del', tb.select.edit );
                            tb.addRowInputDataDelete();
                            tb.select.edit = [];
                            tb.editModeMenuCheck();
                        break;
                        // 廃止
                        case 'tableDiscard':
                            tb.workStart('discard');
                            tb.workerPost('discard', tb.select.edit );
                        break;
                        // 復活
                        case 'tableRestore':
                            tb.workStart('restore');
                            tb.workerPost('restore', tb.select.edit );
                        break;
                        // 編集キャンセル
                        case 'tableCancel':
                            if ( Object.keys( tb.edit.input ).length ) {
                                fn.alert(
                                    getMessage.FTE00018,
                                    getMessage.FTE00019,
                                    'confirm', {
                                        ok: { text: getMessage.FTE00020, action: 'danger'},
                                        cancel: { text: getMessage.FTE00021, action: 'normal'}
                                    }).then(function( flag ){
                                    if ( flag ) {
                                        tb.changeViewMode.call( tb );
                                    }
                                });
                            } else {
                                tb.changeViewMode.call( tb );
                            }
                        break;
                        // テーブル設定
                        case 'tableSetting':
                            tb.tableSettingOpen();
                        break;
                    }
                }
            });
            // tbody表示
            if ( tb.data.body && tb.select.view.length > 0 ) {
                tb.workerPost('edit', tb.select.view );
            } else if ( tb.data.body ) {
                tb.setTbody();
            } else {
                tb.requestTbody();
            }
        } break;
        case 'diff': {
            const menuList = {
                Main: [
                    { button: { className: 'tableAdvance', type: 'tableOk', icon: 'check', text: getMessage.FTE00022, action: 'positive', minWidth: '200px', disabled: true }},
                    { button: { type: 'tableCancel', icon: 'arrow01_left', text: getMessage.FTE00023, action: 'normal'}, separate: true}
                ],
                Sub: [
                    { button: { type: 'tableChangeValue', icon: 'circle_info', text: getMessage.FTE00024, action: 'default',
                        toggle: { init: 'off', on:getMessage.FTE00025, off:getMessage.FTE00026}}}
                ]
            };
            tb.$.header.html( fn.html.operationMenu( menuList ) );
            tb.workerPost('normal', tb.option.after );
        } break;
        case 'history': {
            const menuList = {
                Main: [
                    { input: { className: 'tableHistoryId', type: 'tableInputHistoryId', before: tb.idName }},
                    { button: { type: 'tableShowHistory', icon: 'clock', text: getMessage.FTE00027, action: 'default', disabled: true, minWidth: '200px'}},
                    { button: { type: 'tableResetHistory', icon: 'clear', text: getMessage.FTE00028, action: 'normal', disabled: true, minWidth: '200px'}}
                ]
            };
            tb.$.header.html( fn.html.operationMenu( menuList ) );

            const historyMessage = `<div class="historyStandByMessage">`
            + fn.html.icon('clock')
            + getMessage.FTE00029 + `${tb.idName}` + getMessage.FTE00030 + `<br>`
            + getMessage.FTE00031 + `</div>`;
            tb.$.container.addClass('historyStandBy');
            tb.$.message.html( historyMessage );

            // メニューボタン
            const $show = tb.$.header.find('.itaButton[data-type="tableShowHistory"]'),
                  $reset = tb.$.header.find('.itaButton[data-type="tableResetHistory"]'),
                  $input = tb.$.header.find('.tableHistoryId');

            $show.on('click', function(){
                const uuid = $input.val();
                tb.workStart('filter');
                tb.workerPost('history', uuid );
                $reset.prop('disabled', false );
            });

            // 履歴リセット
            $reset.on('click', function(){
                tb.$.container.addClass('historyStandBy');
                tb.$.message.html( historyMessage );

                tb.$.tbody.empty();
                tb.data.body = null;
                $input.val('').trigger('input');
                $reset.prop('disabled', true );
                $show.prop('disabled', true );
            });

            $input.on('input', function(){
                const value = $( this ).val();
                if ( value === '') {
                    $show.prop('disabled', true );
                } else {
                    $show.prop('disabled', false );
                }
            });
        } break;
    }

    // テーブル設定 カスタムCSS
    if ( tb.mode === 'edit') {
        tb.$.custom.html( tb.tableSettingCustomCSS() );
    }

    // Table内各種イベントセット
    tb.setTableEvents();
}
/*
##################################################
   tHead HTML
##################################################
*/
theadHtml( filterFlag = true, filterHeaderFlag = true ) {
    const tb = this;

    const info = tb.info,
          groupInfo = info.column_group_info,
          columnInfo = info.column_info,
          hierarchy = tb.data.hierarchy;

    const html = [['']],
          groupColspan = {};

    // parent_column_group_idからkeyを返す
    const groupIdToKey = function( id ) {
        for ( const key in info.column_group_info ) {
            if ( id === info.column_group_info[ key ].column_group_id ) return key;
        }
    };

    // 配列階層からthead HTML作成
    const rowLength = hierarchy.length - 1;

    // colspan
    tb.data.filterHeadColspan = 0;

    // モード別列
    const headRowspan = rowLength + 1;
    if ( filterHeaderFlag ) {
        switch ( tb.mode ) {
            case 'view': {
                if ( tb.flag.update ) {
                    const selectButton = fn.html.button('', 'rowSelectButton');
                    html[0] += fn.html.cell( selectButton, ['tHeadTh', 'tHeadLeftSticky', 'tHeadRowSelect'], 'th', headRowspan );
                    tb.data.filterHeadColspan++;
                }
                const itemText = ( tb.getTableSettingValue('menu') === 'show')? '項目メニュー': fn.html.icon('ellipsis_v');
                html[0] += fn.html.cell( itemText, ['tHeadTh', 'tHeadLeftSticky', 'tHeadRowMenu'], 'th', headRowspan );
                tb.data.filterHeadColspan++;
            } break;
            case 'select': case 'execute': {
                if ( tb.mode === 'select' && tb.params.selectType === 'multi') {
                    const selectButton = fn.html.button('', 'rowSelectButton');
                    html[0] += fn.html.cell( selectButton, ['tHeadTh', 'tHeadLeftSticky', 'tHeadRowSelect'], 'th', headRowspan );
                } else {
                    html[0] += fn.html.cell(getMessage.FTE00032, ['tHeadTh', 'tHeadLeftSticky'], 'th', headRowspan );
                }
                tb.data.filterHeadColspan++;
            } break;
            case 'edit': {
                if ( tb.flag.edit || tb.flag.disuse || tb.flag.reuse ) {
                    const selectButton = fn.html.button('', 'rowSelectButton');
                    html[0] += fn.html.cell( selectButton, ['tHeadTh', 'tHeadLeftSticky', 'tHeadRowSelect'], 'th', headRowspan );
                }
            } break;
            case 'diff': {
                html[0] += fn.html.cell(getMessage.FTE00033, ['tHeadTh', 'tHeadLeftSticky'], 'th', headRowspan );
            } break;
            case 'history': {
                html[0] += fn.html.cell(getMessage.FTE00034, ['tHeadTh', 'tHeadLeftSticky'], 'th', headRowspan );
                html[0] += fn.html.cell(getMessage.FTE00035, ['tHeadTh'], 'th', headRowspan );
                html[0] += fn.html.cell(getMessage.FTE00036, ['tHeadTh'], 'th', headRowspan );
            } break;
        }
    }

    for ( let i = rowLength; i >= 0 ; i-- ) {
        if ( !html[i] ) html[i] = '';

        for ( const columnKey of hierarchy[i] ) {
            if ( !groupColspan[ columnKey ] ) groupColspan[ columnKey ] = {};

            const type = columnKey.slice( 0, 1 );

            // Group
            if ( type === 'g') {
                if ( tb.structural.column_group_info[ columnKey ] === undefined ) continue;
                const group = groupInfo[ columnKey ],
                      name = fn.cv( group.column_group_name, '', true ),
                      gCount = fn.cv( groupColspan[ columnKey ].group_count, 0 ),
                      gColspan = fn.cv( groupColspan[ columnKey ].group_colspan, 0 ),
                      colspan = tb.structural.column_group_info[ columnKey ].length + gColspan - gCount;

                // 親グループにcolspanを追加する
                if ( group.parent_column_group_id !== null ) {
                    const parentId = groupIdToKey( group.parent_column_group_id );
                    if ( !groupColspan[ parentId ] ) groupColspan[ parentId ] = {};
                    // group count
                    if ( !groupColspan[ parentId ].group_count ) groupColspan[ parentId ].group_count = 0;
                    groupColspan[ parentId ].group_count += 1;
                    // colspan
                    if ( !groupColspan[ parentId ].group_colspan ) groupColspan[ parentId ].group_colspan = 0;
                    groupColspan[ parentId ].group_colspan += colspan;
                }

                html[i] += fn.html.cell( name, ['tHeadGroup', 'tHeadTh'], 'th', 1, colspan );

            // Column
            } else if ( type === 'c') {
                const column = info.column_info[ columnKey ],
                      rowspan = rowLength - i + 1,
                      className = ['tHeadTh', 'popup', 'popupScroll'],
                      attr = {id: columnKey};

                let name = fn.cv( column.column_name, '', true );

                // selectモードの場合ボタンカラムは非表示
                if ( ( tb.mode === 'select' || tb.mode === 'execute' || tb.mode === 'history') && column.column_type === 'ButtonColumn') {
                    continue;
                }
                // ソート
                if ( filterHeaderFlag ) {
                    if ( tb.mode === 'view' || tb.mode === 'select' || tb.mode === 'execute') {
                        const notSort = ['ButtonColumn', 'PasswordColumn', 'PasswordIDColumn', 'JsonPasswordIDColumn', 'MaskColumn', 'SensitiveSingleTextColumn', 'SensitiveMultiTextColumn'];
                        if ( notSort.indexOf( column.column_type ) === -1 ) {
                            className.push('tHeadSort');
                            name += `<span class="tHeadSortMark"></span>`
                        }
                    }
                }
                // 必須
                if ( tb.mode === 'edit' && column.required_item === '1') {
                    // 必須を付けない要素
                    const autoInputColumns = [ tb.idNameRest, 'last_update_date_time', 'last_updated_user', 'discard'];
                    if ( autoInputColumns.indexOf( column.column_name_rest ) === -1 ) {
                        name += '<span class="tHeadRequired">' + getMessage.FTE00037 + '</span>';
                    }
                }
                // 廃止、ID列を固定
                if ( filterHeaderFlag ) {
                    if ( i === 0 && tb.mode !== 'history') {
                        if ( [ tb.idNameRest, 'discard'].indexOf( column.column_name_rest ) !== -1 ) {
                            className.push('tHeadLeftSticky');
                        }
                    }
                }
                if ( column.column_name_rest ) attr.rest = column.column_name_rest;
                if ( column.description ) attr.title = fn.cv( column.description, '', true );
                if ( column.column_name_rest === 'discard') {
                    name = getMessage.FTE00038;
                    className.push('discardCell');
                }
                html[i] += fn.html.cell( name, className, 'th', rowspan, 1, attr );
            }

        }
        html[i] = fn.html.row( html[i], ['tHeadTr', 'headerTr']);
    }

    // フィルター入力欄
    if ( tb.mode === 'view' || tb.mode === 'select' || tb.mode === 'execute') {
        if ( tb.option.sheetType !== 'reference') {
            if ( filterFlag === true ) html.push( tb.filterHtml( filterHeaderFlag ) );
        }
    }

    return html.join('');

    if ( mode === 'filter') {
        return ``
        + `<table class="table">`
            + `<thead class="thead">`
            +
            + `</thead>`
        + `</table>`;
    } else {
        return ``
        + `<thead class="thead">`
            + html.join('')
        + `</thead>`
        + `<tbody class="tbody"></tbody>`;
    }
}
/*
##################################################
   common table html
##################################################
*/
commonTableHtml( filterFlag ) {
    const tb = this;

    return ``
    + `<thead class="thead">`
        + tb.theadHtml( filterFlag )
    + `</thead>`
    + `<tbody class="tbody"></tbody>`;
}
/*
##################################################
   filter table html
##################################################
*/
filterTableHtml() {
    const tb = this;

    return ``
    + `<table class="table">`
        + `<thead class="thead">`
            + tb.theadHtml( true, false )
        + `</thead>`
    + `</table>`;
}
/*
##################################################
   Filter HTML
##################################################
*/
filterHtml( filterHeaderFlag = true ) {
    const tb = this;

    const info = tb.info.column_info,
          keys = ( tb.option.sheetType !== 'reference')? tb.data.columnKeys: tb.data.referenceFilterKeys,
          initSetFilter = tb.option.initSetFilter;

    const filterIcon = `${fn.html.icon('filter')}<span class="tHeadFilterTitle">` + getMessage.FTE00001 + `</span>`,
          rows = [],
          rowClassName = ['tHeadTr', 'filterTr'],
          className = ['tHeadFilter', 'tHeadLeftSticky', 'tHeadFilterHeader'];

    // 選択欄がない場合はフィルタタイトルを細くする
    if ( tb.data.filterHeadColspan === 1 ) className.push('tHeadFilterHeaderNarrow');
    const cells = [];

    if ( filterHeaderFlag ) {
        cells.push( fn.html.cell( filterIcon, className, 'th', 2, tb.data.filterHeadColspan ) );
    }

    const pulldownOpen = function( name, rest ) {
        return ``
        + `<div class="filterSelectArea">`
            + fn.html.button(`${fn.html.icon('menuList')}` + getMessage.FTE00039, ['filterPulldownOpenButton', 'itaButton'], { type: name, rest: rest })
        + `</div>`;
    }

    for ( const key of keys ) {
        const column = info[ key ],
              name = column.col_name,
              rest = column.column_name_rest,
              type = column.column_type;

        // view_item
        if ( column.view_item === '0' && column.column_name_rest !== 'discard') {
            continue;
        }
        // 選択モードの場合ボタンカラムは表示しない
        if ( ( tb.mode === 'select' || tb.mode === 'execute') && type === 'ButtonColumn') {
            continue;
        }
        // フィルタータイプ
        const getFilterType = function() {
            if ( rest === 'discard') {
                return 'discard';
            } else {
                switch ( type ) {
                    // 文字列検索
                    case 'SingleTextColumn': case 'MultiTextColumn': case 'IDColumn':
                    case 'HostInsideLinkTextColumn': case 'LinkIDColumn': case 'NoteColumn':
                    case 'LastUpdateUserColumn': case 'AppIDColumn': case 'JsonColumn':
                    case 'FileUploadColumn': case 'FileUploadEncryptColumn':
                    case 'EnvironmentIDColumn': case 'TextColumn': case 'RoleIDColumn':
                    case 'JsonIDColumn': case 'UserIDColumn':
                        return 'text';
                    break;
                    // 数値のFROM,TO
                    case 'NumColumn': case 'FloatColumn':
                        return 'number';
                    break;
                    // 日時のFROM,TO
                    case 'DateTimeColumn': case 'LastUpdateDateColumn':
                        if ( tb.option.sheetType !== 'reference') {
                            return 'fromToDateTime';
                        } else {
                            return 'dateTime';
                        }
                    break;
                    // 日付のFROM,TO
                    case 'DateColumn':
                        if ( tb.option.sheetType !== 'reference') {
                            return 'fromToDate';
                        } else {
                            return 'dateTime';
                        }
                    break;
                    // 表示しない
                    default:
                        return 'none';
                }
            }
        };
        const filterType = getFilterType();

        // フィルター初期値
        const getInitValue = function() {
              if ( initSetFilter && initSetFilter[ rest ] ) {
                  switch ( filterType ) {
                      case 'discard': case 'text':
                          return fn.escape( initSetFilter[ rest ].NORMAL );
                      break;
                      default:
                          if ( initSetFilter[ rest ].RANGE ) {
                              return { start: fn.escape( initSetFilter[ rest ].RANGE.START ), end: fn.escape( initSetFilter[ rest ].RANGE.END )};
                          } else {
                              return { start: fn.escape( initSetFilter[ rest ].START ), end: fn.escape( initSetFilter[ rest ].END )};
                          }
                  }
              } else {
                  switch ( filterType ) {
                      case 'discard':
                          return '1';
                      break;
                      case 'dateTime':
                      case 'text':
                          return '';
                      break;
                      default:
                          return { start: '', end: ''};
                  }
              }
        };
        const initValue = getInitValue();

        const className = ['tHeadFilter','tHeadFilterInput'],
              cellHtml = [];

        if ( rest === 'discard') {
            const list = {
                '0': getMessage.FTE00040,
                '1': getMessage.FTE00041,
                '2': getMessage.FTE00042
            };
            cellHtml.push( fn.html.select( list, ['filterInput', 'filterInputDiscard'], list[initValue], name, { type: 'discard', rest: rest } ) );
        } else {
            switch ( filterType ) {
                // 文字列検索
                case 'text':
                    cellHtml.push(`<div class="filterInputArea">`
                    + fn.html.inputText(['filterInput', 'filterInputText'], initValue, name, { type: 'text', rest: rest })
                    + `</div>`);
                    cellHtml.push( pulldownOpen( name, rest ) );
                break;
                // 数値のFROM,TO
                case 'number':
                    cellHtml.push(`<div class="filterInputFromToNumber">`
                        + `<div class="filterInputFromNumberWrap">`
                            + fn.html.inputNumber(['filterInput', 'filterFromNumber'], initValue.start, name, { type: 'fromNumber', rest: rest, placeholder: 'From' })
                        + `</div>`
                        + `<div class="filterInputToNumberWrap">`
                            + fn.html.inputNumber(['filterInput', 'filterToNumber'], initValue.end, name, { type: 'toNumber', rest: rest, placeholder: 'To' })
                        + `</div>`
                    + `</div>`);
                break;
                // 日時のFROM,TO
                case 'fromToDateTime':
                    cellHtml.push(`<div class="filterInputFromToDate">`
                        + `<div class="filterInputFromDateWrap">`
                            + fn.html.inputText(['filterInput', 'filterFromDate'], initValue.start, name, { type: 'fromDate', rest: rest, placeholder: 'From' })
                        + `</div>`
                        + `<div class="filterInputToDateWrap">`
                            + fn.html.inputText(['filterInput', 'filterToDate'], initValue.end, name, { type: 'toDate', rest: rest, placeholder: 'To' })
                        + `</div>`
                        + `<div class="filterInputDateCalendar">`
                            + fn.html.button('<span class="icon icon-cal"></span>', ['itaButton', 'filterInputDatePicker'], { type: 'dateTime', rest: rest, action: 'normal'})
                        + `</div>`
                    + `</div>`);
                break;
                // 日時
                case 'dateTime':
                    cellHtml.push(`<div class="filterInputDate">`
                        + fn.html.dateInput( true, 'filterInput filterDate', initValue, name, { type: 'text', rest: rest })
                    + `</div>`);
                break;
                // 日付のFROM,TO
                case 'fromToDate':
                    cellHtml.push(`<div class="filterInputFromToDate">`
                        + `<div class="filterInputFromDateWrap">`
                            + fn.html.inputText(['filterInput', 'filterFromDate'], initValue.start, name, { type: 'fromDate', rest: rest, placeholder: 'From' })
                        + `</div>`
                        + `<div class="filterInputToDateWrap">`
                            + fn.html.inputText(['filterInput', 'filterToDate'], initValue.end, name, { type: 'toDate', rest: rest, placeholder: 'To' })
                        + `</div>`
                        + `<div class="filterInputDateCalendar">`
                            + fn.html.button('<span class="icon icon-cal"></span>', ['itaButton', 'filterInputDatePicker'], { type: 'date', rest: rest, action: 'normal'})
                        + `</div>`
                    + `</div>`);
                break;
                // 表示しない
                default:
                    className.push('tHeadFilterNone');
                    cellHtml.push('<div class="filterNone"></div>');
            }
        }

        if ( filterHeaderFlag ) {
            if (  [ tb.idNameRest, 'discard'].indexOf( rest) !== -1 ) {
                className.push('tHeadLeftSticky');
            }
        }

        cells.push( fn.html.cell( cellHtml.join(''), className, 'th', 1, 1, { rest: rest, type: filterType } ) );
    }

    // フィルタメニュー
    const createFilterMenuHtml = function( filterMenuList ) {
        const filterMenuListHtml = [];
        for ( const item of filterMenuList ) {
            const listClassName = ['filterMenuItem'];
            if ( item.separate ) listClassName.push('filterMenuItemSeparate');
            if ( item.name === 'auto') {
                // オートフィルターチェックボックス
                const attr = { type: item.name }
                if ( tb.flag.autoFilter ) attr.checked = 'checked';
                filterMenuListHtml.push(`<li class="${listClassName.join(' ')}">${fn.html.checkboxText('filterMenuAutoFilter', item.title, tb.id + '_AutoFilter', tb.id + '_AutoFilter', attr )}</li>`)
            } else {
                const attrs = { type: item.name, action: item.action };
                if ( item.disabled ) attrs.disabled = 'disabled';
                filterMenuListHtml.push(`<li class="${listClassName.join(' ')}">${fn.html.button( item.title,
                    ['filterMenuButton', 'itaButton'], attrs )}</li>`);
            }
        }
        return `<ul class="filterMenuList">${filterMenuListHtml.join('')}</ul>`;
    };

    const menuList = [
        { name: 'filter', title: getMessage.FTE00043, action: 'restore'},
        { name: 'clear', title: getMessage.FTE00044, action: 'negative'},
        { name: 'auto', title: getMessage.FTE00045}
    ];

    if ( tb.mode === 'view') {
        menuList.push({ name: 'excel', title: getMessage.FTE00046, action: 'default', separate: true, disabled: true }),
        menuList.push({ name: 'json', title: getMessage.FTE00047, action: 'default', disabled: true })
    };

    const filterMenuHtml = fn.html.cell( createFilterMenuHtml( menuList ),
        ['tHeadFilter', 'tHeadFilterMenu'], 'th', 1, keys.length );

    if ( tb.option.sheetType !== 'reference') {
        rows.push( fn.html.row( cells.join(''), rowClassName ) );
        rows.push( fn.html.row( filterMenuHtml, rowClassName ) );
    } else {
        rows.push( fn.html.row( cells.join('') + filterMenuHtml, rowClassName ) );
    }
    return rows.join('');
}
/*
##################################################
   フィルタダウンロードボタンチェック
##################################################
*/
filterDownloadButtonCheck() {
    const tb = this;

    const $filterTarget = ( tb.option.sheetType !== 'reference')? tb.$.thead: tb.$.header;

    const $excel = $filterTarget.find('.filterMenuButton[data-type="excel"]'),
          $json =  $filterTarget.find('.filterMenuButton[data-type="json"]');

    const excelLimit = tb.info.menu_info.xls_print_limit;

    if ( ( excelLimit === null || tb.data.count <= excelLimit ) && tb.data.count >= 1 ) {
        $excel.removeClass('popup').prop('disabled', false ).removeAttr('title');
    } else if ( excelLimit !== null ) {
        $excel.addClass('popup').attr('title', getMessage.FTE00048 + `（${excelLimit}` + getMessage.FTE00049 + `）` + getMessage.FTE00050).prop('disabled', true );
    } else {
        $excel.prop('disabled', true );
    }

    if ( tb.data.count >= 1 ) {
        $json.prop('disabled', false );
    } else {
        $json.prop('disabled', true );
    }
}
/*
##################################################
   参照用メニューフィルター
##################################################
*/
referenceFilter() {
    const tb = this;

    const thead = [ fn.html.cell( name, 'tHeadBlank tHeadLeftSticky', 'th') ];
    for ( const key of tb.data.referenceFilterKeys ) {
        const column = tb.info.column_info[ key ];
        let name = fn.cv( column.column_name, '', true );

        if ( column.column_name_rest === 'base_datetime') name = getMessage.FTE00051 + name;

        thead.push(  fn.html.cell( name, 'tHeadTh', 'th') );
    }
    thead.push( fn.html.cell( name, 'tHeadBlank', 'th') );

    return `<div class="referenceFilter">
    <table class="table referenceFilterTable">
        <thead class="thead">
            ${fn.html.row( thead.join(''), 'tHeadTr')}
            ${tb.filterHtml()}
        </tbody
    </table></div>`;
}
/*
##################################################
   指定のファイルデータを返す
##################################################
*/
getFileData( id, name, type ) {
    const tb = this;

    const params = tb.data.body.find(function( item ){
        if ( tb.mode !== 'history') {
            return String( item.parameter[ tb.idNameRest ] ) === id;
        } else {
            return String( item.parameter.journal_id ) === id;
        }
    });

    let file;
    if ( params !== undefined ) {
        if ( tb.mode === 'diff' && type === 'beforeValue' && tb.option && tb.option.before[ id ] && tb.option.before[ id ].file[ name ]) {
            // 編集確認画面、変更前データ
            file = tb.option.before[ id ].file[ name ];
        } else if ( tb.mode === 'edit' && tb.edit && tb.edit.input[ id ]) {
            // 編集画面、入力済みのデータがある場合
            if ( tb.edit.input[ id ].after.file ) {
                file = tb.edit.input[ id ].after.file[ name ];
            }
        } else if ( params.file[ name ] !== undefined && params.file[ name ] !== null ) {
            file = params.file[ name ];
        }
    }

    return file;
}
/*
##################################################
   Set table events
##################################################
*/
setTableEvents() {
    const tb = this;

    /*
    ------------------------------
    EDIT以外
    ------------------------------
    */
    if ( tb.mode !== 'edit') {
        // リンクファイルダウンロード
        tb.$.tbody.on('click', '.tableViewDownload', function(e){
            e.preventDefault();

            const $a = $( this ),
                  fileName = $a.text(),
                  id = $a.attr('data-id'),
                  rest = $a.attr('data-rest'),
                  type = $a.attr('data-type');

            const file = tb.getFileData( id, rest, type );

            if ( file !== undefined && file !== null ) {
                fn.download('base64', file, fileName );
            }
        });
    }
    /*
    ------------------------------
    VIEW モード
    ------------------------------
    */
    if ( tb.mode === 'view' || tb.mode === 'select' || tb.mode === 'execute') {
        const $eventTarget = ( tb.option.sheetType !== 'reference')? tb.$.thead: tb.$.header.find('.referenceFilterTable');

        // フィルタプルダウン検索ボタン
        $eventTarget.on('click', '.filterPulldownOpenButton', function(){
            if ( !tb.checkWork ) {
                tb.filterSelectOpen.call( tb, $( this ));
            }
        });

        // フィルター欄、ファイルダウンロード
        const downloadFile = function( $button, type, url ){
            tb.filterParams = tb.getFilterParameter();
            const fileName = fn.cv( tb.info.menu_info.menu_name, 'file') + '_filter';

            $button.prop('disabled', true );

            // filter
            fn.fetch( url, null, 'POST', tb.filterParams ).then(function( result ){
                fn.download( type, result, fileName );
            }).catch(function( error ){
                fn.gotoErrPage( error.message );
            }).then(function(){
                fn.disabledTimer( $button, false, 1000 );
            });
        };

        // オートフィルター
        $eventTarget.on({
            'change': function(){
                tb.flag.autoFilter = $( this ).prop('checked');
            },
            'click': function( e ){
                if ( !tb.checkWork ) return;
                e.preventDefault();
            }
        }, '.filterMenuAutoFilter');

        $eventTarget.on('change', '.filterInput', function(){
            if ( !tb.checkWork && tb.flag.autoFilter ) {
                $eventTarget.find('.filterMenuButton[data-type="filter"]').click();
            }
        });

        // フィルタボタン
        $eventTarget.on('click', '.filterMenuButton', function(){
            if ( !tb.checkWork ) {

                tb.$.container.removeClass('tableError');
                tb.$.errorMessage.empty();

                const $button = $( this ),
                      type = $button.attr('data-type');
                switch ( type ) {
                    case 'filter':
                        tb.workStart('filter');
                        tb.setInitSort();
                        tb.requestTbody.call( tb, 'filter');
                    break;
                    case 'clear':
                        tb.workStart('table', 0 );
                        tb.clearFilter.call( tb );
                    break;
                    case 'excel':
                        downloadFile( $button, 'excel', tb.rest.excelDownload );
                    break;
                    case 'json':
                        downloadFile( $button, 'json', tb.rest.jsonDownload );
                    break;
                }
            }
        });

        // フィルタカレンダー
        if ( tb.option.sheetType !== 'reference') {
            $eventTarget.find('.filterInputDatePicker').on('click', function(){
                if ( !tb.checkWork ) {
                    const $button = $( this ),
                          rest = $button.attr('data-rest'),
                          type = $button.attr('data-type');

                    const $from = tb.$.thead.find(`.filterFromDate[data-rest="${rest}"]`),
                          $to = tb.$.thead.find(`.filterToDate[data-rest="${rest}"]`);

                    const from = $from.val(),
                          to = $to.val();

                    const dateFlag = ( type === 'dateTime')? true: false;

                    fn.datePickerDialog('fromTo', dateFlag, tb.data.restNames[ rest ], { from: from, to: to } ).then(function( result ){
                        if ( result !== 'cancel') {
                            $from.val( result.from );
                            $to.val( result.to ).trigger('change');
                        }
                    });
                }
            });
        } else {
            const $input = $eventTarget.find('.filterDate'),
                  rest = $input.attr('data-rest'),
                  title = tb.data.restNames[ rest ];
            fn.setDatePickerEvent( $eventTarget.find('.filterDate'), title );
        }

        // ソート
        tb.$.thead.on('click', '.tHeadSort', function(){
            if ( !tb.checkWork && tb.data.count ) {
                tb.workStart('sort', 100 );

                const $sort = $( this ),
                      id = $sort.attr('data-id'),
                      sort = tb.info.column_info[ id ].column_name_rest;

                let order = $sort.attr('data-sort');
                if ( !order || order === 'ASC') {
                    order = 'DESC';
                } else {
                    order = 'ASC';
                }
                tb.$.thead.find('.tHeadSort').removeAttr('data-sort');
                $sort.attr('data-sort', order );

                tb.sort = [{}];
                tb.sort[0][ order ] = sort;
                tb.workerPost('sort');
            }
        });

        // 個別メニュー
        tb.$.tbody.on('click', '.tBodyRowMenu', function(){
            if ( tb.getTableSettingValue('menu') === 'show') return;

            if ( !tb.checkWork ) {
                const $row = $( this );
                if ( $row.is('.open') ) {
                    $row.removeClass('open');
                    tb.$.window.off('pointerdown.rowMenu');
                } else {
                    $row.addClass('open');
                    tb.$.window.on('pointerdown.rowMenu', function( e ){
                        const $target = $( e.target );
                        if ( !$target.closest( $row ).length ) {
                            $row.removeClass('open');
                            tb.$.window.off('pointerdown.rowMenu');
                        }
                    });
                }
            }
        });

        // 編集、複製
        tb.$.tbody.on('click', '.tBodyRowMenuTb', function(){
            if ( !tb.checkWork ) {
                const $button = $( this ),
                      type = $button.attr('data-type'),
                      itemId = $button.attr('data-id');

                tb.select.view = [ itemId ];

                switch ( type ) {
                    case 'rowEdit':
                        tb.changeEdtiMode.call( tb );
                    break;
                    case 'rowDup':
                        tb.changeEdtiMode.call( tb, 'changeEditDup');
                    break;
                }
            }
        });
    }

    /*
    ------------------------------
    EDIT モード
    ------------------------------
    */
    if ( tb.mode === 'edit') {
        // ファイル選択
        tb.$.tbody.on('click', '.tableEditSelectFile', function(){
            const $button = $( this ),
                  id = $button.attr('data-id'),
                  key = $button.attr('data-key'),
                  maxSize = $button.attr('data-upload-max-size');

            fn.fileSelect('base64', maxSize ).then(function( result ){

                const changeFlag = tb.setInputFile( result.name, result.base64, id, key, tb.data.body );

                $button.find('.inner').text( result.name );
                if ( changeFlag ) {
                    $button.addClass('tableEditChange');
                } else {
                    $button.removeClass('tableEditChange');
                }
            }).catch(function( error ){
                if ( error !== 'cancel') {
                    alert( error );
                }
            });
        });
        
        // 入力データを配列へ
        tb.$.tbody.on('change', '.input, .tableEditInputSelect', function(){
            const $input = $( this ),
                  value = ( $input.val() !== '')? $input.val(): null,
                  id = $input.attr('data-id'),
                  key = $input.attr('data-key');

            const changeFlag = tb.setInputData( value, id, key, tb.data.body );

            if ( changeFlag ) {
                $input.addClass('tableEditChange');
                if ( $input.is('.tableEditInputSelect') ) {
                    $input.parent('.tableEditInputSelectContainer').addClass('tableEditChange');
                }
            } else {
                $input.removeClass('tableEditChange');
                if ( $input.is('.tableEditInputSelect') ) {
                    $input.parent('.tableEditInputSelectContainer').removeClass('tableEditChange');
                }
            }
        });

        // 入力チェック
        tb.$.tbody.on('input', '.input', function(){
            const $input = $( this ),
                  value = $input.val();
            // 必須
            if ( $input.attr('data-required') === '1') {
                if ( value !== '') {
                    $input.removeClass('tableEditRequiredError ');
                } else {
                    $input.addClass('tableEditRequiredError ');
                }
            }
        });

        // データピッカー
        tb.$.tbody.on('click', '.inputDateCalendarButton', function(){
            const $button = $( this ),
                  $input = $button.closest('.inputDateContainer').find('.inputDate'),
                  rest = $input.attr('data-key'),
                  value = $input.val(),
                  timeFlag = $input.attr('data-timeFlag') === 'true';

            fn.datePickerDialog('date', timeFlag, tb.data.restNames[ rest ], value ).then(function( result ){
                if ( result !== 'cancel') {
                    $input.val( result.date ).change().focus().trigger('input');
                }
            });
        });

        // 変更があるときの離脱確認
        tb.$.window.on('beforeunload', function( e ){
            if ( Object.keys( tb.edit.input ).length ) {
                e.preventDefault();
                return '';
            }
        });

        // パスワード削除ボタン
        tb.$.tbody.on('click', '.inputPasswordDeleteToggleButton', function(){
            const $button = $( this ),
                  $wrap = $button.closest('.inputPasswordWrap'),
                  $input = $wrap.find('.inputPassword'),
                  value = $input.val(),
                  id = $input.attr('data-id'),
                  key = $input.attr('data-key');

            let flag;

            $button.trigger('pointerleave');

            if ( !$button.is('.on') ) {
                $button.addClass('on').attr({
                    'data-action': 'restore',
                    'title': getMessage.FTE00052
                });
                $button.find('.inner').html( fn.html.icon('ellipsis'));
                $wrap.addClass('inputPasswordDelete');
                flag = true;
            } else {
                $button.removeClass('on').attr({
                    'data-action': 'danger',
                    'title': getMessage.FTE00053
                });
                $button.find('.inner').html( fn.html.icon('cross'));
                $wrap.removeClass('inputPasswordDelete');
                flag = false;
            }

            // パスワードを削除する場合は false を入れる
            const inputValue = ( flag )? false: value;
            tb.setInputData( inputValue, id, key, tb.data.body );
        });

        // ファイル選択クリア
        tb.$.tbody.on('click', '.inputFileClearButton', function(){
            const $button = $( this ),
                  $wrap = $button.closest('.inputFileWrap'),
                  $input = $wrap.find('.inputFile'),
                  id = $input.attr('data-id'),
                  key = $input.attr('data-key');

            const changeFlag = tb.setInputFile( null, undefined, id, key, tb.data.body );

            $input.find('.inner').text('');
            if ( changeFlag ) {
                $input.addClass('tableEditChange');
            } else {
                $input.removeClass('tableEditChange');
            }
        });

        // select欄クリック時にselect2を適用する
        tb.$.tbody.on('click', '.tableEditInputSelectValue', function(){
            const $value = $( this ),
                  $select = $value.next('.tableEditInputSelect'),
                  width = $value.outerWidth();

            if ( $value.is('.tableEditInputSelectValueDisabled') ) return false;

            $value.remove();

            $select.select2({
                dropdownAutoWidth: false,
                width: width
            }).select2('open');

            $select.change();
        });

        // select欄フォーカス時にselect2を適用する
        tb.$.tbody.on('focus.select2', '.tableEditInputSelect', function(){
            const $select = $( this );
            if ( !$select.is('.select2-hidden-accessible') ) {
                const $value = $select.prev('.tableEditInputSelectValue'),
                      width = $value.outerWidth();

                $select.off('focus.select2');
                $value.remove();

                $select.select2({
                    dropdownAutoWidth: false,
                    width: width
                }).select2('open');

                $select.change();
            }
        });

        // input hidden変更時にテキストも変更する
        tb.$.tbody.on('change', '.tableEditInputHidden', function(){
            const $input = $( this ),
                  value = $input.val(),
                  $text = $input.prev('.tableEditInputHiddenText');
            $text.text( value );
        });

    }

    /*
    ------------------------------
    VIEW or EDIT モード
    ------------------------------
    */
    if ( ( tb.mode === 'select' && tb.params.selectType === 'multi') || tb.mode === 'view' || tb.mode === 'edit') {

        // アクションボタン
        tb.$.tbody.on('click', '.actionButton', function(){
            if ( !tb.checkWork ) {
                const $button = $( this ),
                      type = $button.attr('data-type');

                switch ( type ) {
                    case 'redirect': case 'redirect2': {
                        const redirect = $button.attr('data-redirect');
                        if ( redirect ) {
                            window.location.href = redirect;
                        }
                    } break;
                    case 'redirect_filter': {
                        const itemId = $button.attr('data-item'),
                            columnKey = $button.attr('data-columnkey');

                        const itemData = tb.data.body.find(function( item ){
                            return item.parameter[ tb.idNameRest ] === itemId;
                        });

                        if ( itemData ) {
                            let buttonAction;
                            try {
                                buttonAction = JSON.parse( tb.info.column_info[ columnKey ].button_action );
                            } catch( e ) {
                                buttonAction = [];
                            }

                            const redirectUrl = buttonAction[0][1],
                                filter = {};

                            for ( const f of buttonAction[0][2] ) {
                                const parameterKey = f[0],
                                    filterSetKey = f[1],
                                    filterType = f[2];

                                let value;
                                if ( filterType === 'LIST') {
                                    value = [ itemData.parameter[ parameterKey ] ];
                                } else if ( filterType === 'RANGE') {
                                    //
                                } else {
                                    value = itemData.parameter[ parameterKey ];
                                }
                                filter[ filterSetKey ] = {};
                                filter[ filterSetKey ][ filterType ] = value;
                            }
                            if ( redirectUrl ) {
                                window.location.href = `?${redirectUrl}&filter=${fn.filterEncode( filter )}`;
                            }
                        } else {
                            alert('Button action error.');
                        }
                    } break;
                    case 'download': {
                        $button.prop('disabled', true );
                        const url = $button.attr('data-url'),
                              method = $button.attr('data-method'),
                              nameKey = $button.attr('data-filename'),
                              dataKey = $button.attr('data-filedata');
                        fn.fetch( url, null, method ).then(function( result ){
                            if ( result[ dataKey ] && result[ nameKey] ) {
                                fn.download('base64', result[ dataKey ], result[ nameKey]);
                            } else {
                                alert('Download error.');
                            }
                        }).catch(function( error ){
                            alert( error.message );
                            window.console.error( error );
                        }).then(function(){
                            $button.prop('disabled', false );
                        });
                    } break;
                    case 'modal': {
                        $button.prop('disabled', true );
                        const modalType = $button.attr('data-modal'),
                              dataId = $button.attr('data-id'),
                              buttonText = $button.text();
                        tb.actionModalOpen( modalType, dataId, buttonText ).then(function(){
                            $button.prop('disabled', false );
                        });
                    } break;
                    case 'restapi':
                    case 'restapi_redirect': {
                        $button.prop('disabled', true );
                        const text = $button.text(),
                              method = $button.attr('data-method'),
                              endpoint = $button.attr('data-restapi'),
                              option = {};

                        let body = $button.attr('data-body');
                        if ( body !== '') {
                            try {
                                body = JSON.parse( body );
                            } catch( error ) {
                                body = {};
                            }
                        }
                        if ( type === 'restapi_redirect') {
                            option.redirect = $button.attr('data-redirect');
                            option.redirect_key = $button.attr('data-redirect-key');
                        }
                        tb.restApi( text, method, endpoint, body, option ).then(function(){
                            $button.prop('disabled', false );
                        });
                    } break;
                }
            }
        });

        // 行選択チェックボックスの外がクリックされても変更する
        tb.$.thead.find('.tHeadRowSelect').on('click', function( e ){
            if ( !tb.checkWork ) {
                const $button = $( this ).find('.rowSelectButton');
                if ( !$( e.target ).closest('.rowSelectButton').length ) {
                    $button.focus().click();
                }
            }
        });
        const rowSelect = function( e ) {
            if ( !tb.checkWork ) {
                const $wrap = $( this ),
                      $check = ( $wrap.is('.tBodyTrRowSelect') )?
                          $wrap.find('.tBodyRowSelect').find('.tBodyRowCheck'):
                          $wrap.find('.tBodyRowCheck'),
                      checked = $check.prop('checked');

                if ( !$( e.target ).closest('.checkboxWrap').length ) {
                    $check.focus().prop('checked', !checked ).change();
                }
            }
        };
        const target = ( tb.mode === 'select' || tb.mode === 'execute')? '.tBodyTrRowSelect': '.tBodyRowSelect';
        tb.$.tbody.on('click', target, rowSelect );

        // 一括選択
        tb.$.thead.find('.rowSelectButton').on('click', function(){
            if ( !tb.checkWork && tb.data.count ) {
                const $button = $( this ),
                      selectStatus = $button.attr('data-select');

                tb.$.tbody.find('.tBodyRowCheck').each(function(){
                    const $check = $( this ),
                          checked = $check.prop('checked'),
                          id = $check.val();
                    if ( selectStatus === 'not' && checked === false ) $check.prop('checked', true ).change();
                    if ( ( selectStatus === 'all' || selectStatus === 'oneOrMore')
                        && checked === true ) $check.prop('checked', false ).change();
                });

                tb.checkSelectStatus();
            }
        });

        // 行選択チェックボックス
        tb.$.tbody.on('change', '.tBodyRowCheck', function(){
            if ( !tb.checkWork ) {
                const $check = $( this ),
                      checked = $check.prop('checked'),
                      id = $check.val(),
                      checkMode = ( tb.mode === 'edit')? 'edit': ( tb.mode === 'select')? 'select': 'view';


                if ( tb.mode === 'select') {
                    if ( checked ) {
                        tb.select[tb.mode].push({
                            id: id,
                            name: $check.attr('data-selectname')
                        });
                    } else {
                        const index = tb.select[tb.mode].findIndex(function(obj){ return obj.id === id });
                        if ( index !== -1 ) {
                            tb.select[ checkMode ].splice( index, 1 );
                        }
                    }
                } else {
                    if ( checked ) {
                        tb.select[ checkMode ].push( id );
                    } else {
                        const index = tb.select[ checkMode ].indexOf( id );
                        if ( index !== -1 ) {
                            tb.select[ checkMode ].splice( index, 1 );
                        }
                    }
                }

                tb.checkSelectStatus();

                // メニューボタンを活性化
                if ( checkMode === 'edit' ) {
                    tb.editModeMenuCheck();
                } else if ( tb.mode === 'select') {
                    tb.selectModeMenuCheck();
                    tb.$.container.trigger(`${tb.id}selectChange`);
                }
            }
        });
    }
    /*
    ------------------------------
    SELECT or EXECUTEモード
    ------------------------------
    */
    if ( ( tb.mode === 'select' && tb.params.selectType === undefined ) || tb.mode === 'execute') {
        // 行選択ラジオボタンの外がクリックされても変更する
        const radioRowSelect = function( e ) {
            if ( !tb.checkWork ) {
                const $wrap = $( this ),
                      $radio = ( $wrap.is('.tBodyTrRowSelect') )?
                          $wrap.find('.tBodyRowRadioSelect').find('.tBodyRowRadio'):
                          $wrap.find('.tBodyRowRadio'),
                      checked = $radio.prop('checked');

                if ( !checked ) {
                    if ( !$( e.target ).closest('.radioWrap').length ) {
                        $radio.focus().prop('checked', true ).change();
                    }
                } else {
                    $radio.focus();
                }
            }
        };
        const target = ( tb.mode === 'select' || tb.mode === 'execute')? '.tBodyTrRowSelect': '.tBodyRowRadioSelect';
        tb.$.tbody.on('click', target, radioRowSelect );

        // 行選択ラジオ
        tb.$.tbody.on('change', '.tBodyRowRadio', function(){
            if ( !tb.checkWork ) {
                const $radio = $( this ),
                      checked = $radio.prop('checked'),
                      id = $radio.val(),
                      name = $radio.attr('data-selectname');

                tb.select[tb.mode][0] = {
                    id: id,
                    name: name
                };

                if ( tb.params.selectOtherKeys ) {
                    tb.select[tb.mode][0].selectOtherKeys = {};
                    for ( const selectKey of tb.params.selectOtherKeys ) {
                        tb.select[tb.mode][0].selectOtherKeys[ selectKey ] = $radio.attr(`data-${selectKey}`);
                    }
                }

                tb.selectModeMenuCheck();
                tb.$.container.trigger(`${tb.id}selectChange`);
            }
        });
    }
}
/*
##################################################
   表示しているページの選択状態をチェック
##################################################
*/
checkSelectStatus() {
    const tb = this;

    if ( tb.data.count ) {

        const $button = tb.$.thead.find('.rowSelectButton');

        const $check = tb.$.tbody.find('.tBodyRowCheck'),
              length = $check.length;

        let checkCount = 0;

        tb.$.tbody.find('.tBodyRowCheck').each(function(){
            if ( $( this ).prop('checked') ) checkCount++;
        });

        if ( length === checkCount ) {
            $button.attr('data-select', 'all');
        } else if ( checkCount === 0 ) {
            $button.attr('data-select', 'not');
        } else {
            $button.attr('data-select', 'oneOrMore');
        }
    }
}
/*
##################################################
   新規入力データチェック
##################################################
*/
checkNewInputDataSet( id, beforeData ) {
    const tb = this;

    if ( !tb.edit.input[id] ) {
        // 変更前データ
        const before = beforeData.find(function( item ){
            return String( item.parameter[ tb.idNameRest ] ) === id;
        });
        tb.edit.input[id] = {
            after: {
                file: {},
                parameter: {}
            },
            before: before
        };
        tb.edit.input[id].after.parameter[ tb.idNameRest ] = id;
    }
}
checkNewInputDataDelete( id ) {
    const tb = this;

    // 変更が一つもない場合（パラメータが固有IDのみの場合）
    if ( tb.edit.input[id] && Object.keys( tb.edit.input[id]['after'].parameter ).length <= 1 ) {
        delete tb.edit.input[id];
    }

    // 編集確認ボタンを活性化
    tb.editModeMenuCheck();
}
/*
##################################################
   入力データ
##################################################
*/
setInputData( value, id, rest, beforeData ) {
    const tb = this;

    tb.checkNewInputDataSet( id, beforeData );

    // 変更があれば追加、なければ削除
    const beforeValue = tb.edit.input[id]['before'].parameter[rest];
    let changeFlag = false;
    if ( beforeValue !== value ) {
        tb.edit.input[id]['after'].parameter[rest] = value;
        changeFlag = true;
    } else {
        if ( tb.edit.input[id]['after'].parameter[rest] !== undefined ) {
             delete tb.edit.input[id]['after'].parameter[rest];
        }
    }

    tb.checkNewInputDataDelete( id );

    return changeFlag;
}
/*
##################################################
   入力ファイル
##################################################
*/
setInputFile( fileName, fileBase64, id, rest, beforeData ) {
    const tb = this;

    tb.checkNewInputDataSet( id, beforeData );

    // 変更があれば追加、なければ削除
    const beforeFileName = tb.edit.input[id]['before'].parameter[rest],
          beforeFile = tb.edit.input[id]['before'].file[rest];
    let changeFlag = false;
    if ( beforeFile !== fileBase64 || beforeFileName !== fileName ) {
        tb.edit.input[id]['after'].file[rest] = fileBase64;
        tb.edit.input[id]['after'].parameter[rest] = fileName;
        changeFlag = true;
    } else {
        if ( tb.edit.input[id]['after'].parameter[rest] !== undefined ) {
             delete tb.edit.input[id]['after'].parameter[rest];
        }
    }

    tb.checkNewInputDataDelete( id );

    return changeFlag;
}
/*
##################################################
   廃止復活変更
##################################################
*/
changeDiscard( beforeData, type ) {
    const tb = this;

    for ( const id of tb.select.edit ) {
        // 入力データの更新
        const value = ( type === 'discard')? '1': '0';
        tb.setInputData( value, id, 'discard', beforeData );

        // 初期値から変更があるかチェック
        let changeFlag = false;
        const before = beforeData.find(function( item ){
            return String( item.parameter[ tb.idNameRest ] ) === id;
        });
        if ( before !== undefined && value !== before.parameter.discard ) changeFlag = true;

        // 画面に表示されている分の更新
        const $discard = tb.$.tbody.find(`.inputSpan[data-key="discard"][data-id="${id}"]`),
              $tr = $discard.closest('.tBodyTr');

        if ( value === '0') {
            $tr.removeClass('tBodyTrDiscard');
            $tr.find('.input, .button, .tableEditInputSelect').not('[data-key="remarks"]').prop('disabled', false );
            $tr.find('.tableEditInputSelectValue').removeClass('tableEditInputSelectValueDisabled');
        } else {
            $tr.addClass('tBodyTrDiscard');
            $tr.find('.input, .button, .tableEditInputSelect').not('[data-key="remarks"]').prop('disabled', true );
            $tr.find('.tableEditInputSelectValue').addClass('tableEditInputSelectValueDisabled');
        }

        const discardMark = tb.discardMark( value );
        $discard.html( discardMark );
        if ( changeFlag ) {
            $discard.addClass('tableEditChange');
        } else {
            $discard.removeClass('tableEditChange');
        }
    }
    tb.workEnd();
}
/*
##################################################
   追加データ処理
##################################################
*/
addRowInputData( addId ) {
    const tb = this;

    if ( !tb.edit.input[ addId ] ) {
        tb.edit.input[ addId ] = {
            before: {
                file: {},
                parameter: {
                    discard: '0'
                }
            },
            after: {
                file: {},
                parameter: {}
            },
        };

        // 初期値を入力済みへ
        for ( const key in tb.edit.blank.parameter ) {
            const beforeValue = tb.edit.input[ addId ].before.parameter[ key ],
                  afterValue = tb.edit.blank.parameter[ key ];
            if ( beforeValue !== afterValue && afterValue !== '' && afterValue !== null ) {
                tb.edit.input[ addId ].after.parameter[ key ] = afterValue;
            }
        }
     }
     tb.checkNewInputDataDelete( addId );
}
/*
##################################################
   追加行削除時に入力データを削除する
##################################################
*/
addRowInputDataDelete() {
    const tb = this;
    for ( const rowId of tb.select.edit ) {
        delete tb.edit.input[ rowId ];
    }
}
/*
##################################################
   選択、実行時のメニューボタン活性・非活性
##################################################
*/
advanceButtonCheck( flag ) {
    this.$.header.find('.tableAdvance').prop('disabled', flag );
}
/*
##################################################
   選択、実行時のメニューボタン活性・非活性
##################################################
*/
selectModeMenuCheck() {
    const tb = this;

    const $button = tb.$.header.find('.tableAdvance');
    if ( tb.select[ tb.mode ].length ) {
        $button.prop('disabled', false );
    } else {
        $button.prop('disabled', true );
    }
}
/*
##################################################
   編集モードのメニューボタン活性・非活性
##################################################
*/
editModeMenuCheck() {
    const tb = this;

    const selectCount = tb.select[tb.mode].length;
    let confirmFlag = true,
        duplicatFlag = true,
        deleteFlag = true,
        discardFlag = true,
        restoreFlag = true;

    if ( tb.edit.input && Object.keys( tb.edit.input ).length ) {
        confirmFlag = false;
    }

    if ( selectCount !== 0 ) {
        let addCount = 0,
            discardCount = 0;
        for ( const columnKey of tb.select[tb.mode] ) {
            // 廃止フラグの数を調べる
            // （入力済みから調べ、無い場合は廃止リストから）
            if ( tb.edit.input[ columnKey ] !== undefined ) {
                if ( tb.edit.input[ columnKey ].after.parameter.discard === '1') {
                    discardCount++;
                }
            } else if ( tb.data.discard && tb.data.discard.indexOf( columnKey ) !== -1 ) {
                discardCount++;
            }
            // 追加項目の数を調べる（IDがマイナス値の場合）
            if ( !isNaN( columnKey ) && columnKey < 0 ) addCount++;
        }
        if ( discardCount === 0 && addCount === 0) discardFlag = false;
        if ( discardCount === 0 ) duplicatFlag = false;
        if ( selectCount === discardCount ) restoreFlag = false;
        if ( selectCount === addCount ) deleteFlag = false;
    }
    const $button = tb.$.header.find('.operationMenuButton');
    // $button.filter('[data-type="tableOk"]').prop('disabled', confirmFlag );
    $button.filter('[data-type="tableDup"]').prop('disabled', duplicatFlag );
    $button.filter('[data-type="tableDel"]').prop('disabled', deleteFlag );

    $button.filter('[data-type="tableDiscard"]').prop('disabled', discardFlag );
    $button.filter('[data-type="tableRestore"]').prop('disabled', restoreFlag );
}
/*
##################################################
   [Event] Filter pulldown open
   > プルダウン検索セレクトボックスを表示する
##################################################
*/
filterSelectOpen( $button ) {
    const tb = this;

    const $select = $button.parent('.filterSelectArea'),
        width = $select.width() + 'px',
        name = $button.attr('data-type') + '_RF',
        rest = $button.attr('data-rest');

    $button.addClass('buttonWaiting').prop('disabled', true );

    fn.fetch(`${tb.rest.filterPulldown}${rest}/`).then(function( selectList ){
        // listをソートする
        selectList.sort(function( a, b ){
            a = fn.cv( a, '');
            b = fn.cv( b, '');
            return a.localeCompare( b );
        });

        // Select box
        const $selectBox = $(`<select class="filterSelect filterInput" name="${name}" data-type="select" data-rest="${rest}" multiple="multiple"></select>`);

         // Option
        const option = [];
        for ( const item of selectList ) {
            const $option = $(`<option></option>`),
                value = fn.cv( item, '', true );
            if ( value !== '') {
                $option.val( value ).text( value );
            } else {
                $option.val('').text('{空白}');
            }
            $selectBox.append( $option );
        }

        $select.html( $selectBox );

        // select2
        const $first = $select.find('option').eq(0);
        if ( $first.val() === '') {
            $first.val('_blank_');
            setTimeout(function(){ $first.val(''); },1);
        }
        $select.find('select').select2({
            placeholder: "Pulldown select",
            dropdownAutoWidth: false,
            width: width,
            closeOnSelect: false
        }).select2('open');
    }).catch( function( e ) {
        window.console.error( e.message );
        fn.gotoErrPage( e.message );
    });
}
/*
##################################################
   フィルタパラメータを元にプルダウン検索を開く
##################################################
*/
filterSelectParamsOpen( filterParams ) {
    if ( !filterParams ) return false;

    const tb = this;

    return new Promise(function( resolve ){
        const filterRestUrls = [],
              filterKeys = [],
              filterList = {};

        // フィルタリストの作成
        for ( const rest in filterParams ) {
            if ( filterParams[ rest ].LIST ) {
                filterRestUrls.push(`${tb.rest.filterPulldown}${rest}/`);
                filterKeys.push( rest );
                filterList[ rest ] = filterParams[ rest ].LIST;
            }
        }
        const length = filterKeys.length;

        if ( length ) {
            // 各セレクトリストの取得
            fn.fetch( filterRestUrls ).then(function( result ){
                for ( let i = 0; i < length; i++ ) {
                    const $button = tb.$.thead.find(`.filterPulldownOpenButton[data-rest="${filterKeys[i]}"]`),
                          name = $button.attr('data-type') + '_RF',
                          $selectArea = $button.parent('.filterSelectArea');

                    $selectArea.html( tb.filterSelectBoxHtml( result[i], name, filterKeys[i] ) );
                    const $select = $selectArea.find('select');

                    $select.val( filterList[ filterKeys[i] ]);

                    // 対象が存在しない場合は文字列フィルターに入れる
                    if ( $select.val().length === 0 ) {
                        const $input = tb.$.thead.find(`.filterInputText[data-rest="${filterKeys[i]}"]`);
                        $input.val( filterList[ filterKeys[i] ][0] );
                    }

                    $select.select2({
                        placeholder: "Pulldown select",
                        dropdownAutoWidth: false,
                    });
                }
                resolve();
            }).catch( function( e ) {
                fn.gotoErrPage( e.message );
            });
        } else {
            resolve();
        }
    });
}
/*
##################################################
   tbodyデータのリクエスト
##################################################
*/
requestTbody() {
    const tb = this;

    tb.filterParams = tb.getFilterParameter();

    if ( tb.flag.countSkip ) {
        // 件数を確認しない
        tb.workerPost('filter', tb.filterParams );
    } else {
        // 件数を確認する
        fn.fetch( tb.rest.filter + `count/`, null, 'POST', tb.filterParams ).then(function( countResult ){
            tb.data.count = Number( fn.cv( countResult, 0 ) );

            const printLimitNum = Number( fn.cv( tb.info.menu_info.web_print_limit, -1 ) ),
                  printConfirmNum = Number( fn.cv( tb.info.menu_info.web_print_confirm, -1 ) );

            // リミットチェック
            if ( printLimitNum !== -1 && tb.data.count > printLimitNum ) {
                alert( getMessage.FTE00067( tb.data.count, printLimitNum ) );
                tb.limitSetBody();
                return false;
            //表示確認
            } else if ( printConfirmNum !== -1 && tb.data.count >= printConfirmNum ) {
                if ( !confirm( getMessage.FTE00066( tb.data.count, printConfirmNum ) ) ) {
                    tb.limitSetBody();
                    return false;
                }
            }

            tb.workerPost('filter', tb.filterParams );
        }).catch(function( error ){
            tb.filterError( error );
            setTimeout( function() {
                tb.workEnd();
            }, 300 );
        });
    }
}
/*
##################################################
   Filterの内容を取得
##################################################
*/
getFilterParameter() {
    const tb = this;

    // フィルターの内容を取得
    const $filterTarget = ( tb.option.sheetType !== 'reference')? tb.$.thead: tb.$.header,
          filterParams = {};
    $filterTarget.find('.filterInput').each(function(){
        const $input = $( this ),
              value = $input.val(),
              rest = $input.attr('data-rest'),
              type = $input.attr('data-type');

        if ( ( fn.typeof( value ) === 'string' && value ) || ( fn.typeof( value ) === 'array' && value.length ) ) {
            if ( !filterParams[ rest ] ) filterParams[ rest ] = {};

            switch( type ) {
                case 'text':
                    filterParams[ rest ].NORMAL = value;
                break;
                case 'select':
                    filterParams[ rest ].LIST = value;
                    // 空白がある場合nullに変換
                    for ( let i = 0; i < filterParams[ rest ].LIST.length; i++ ) {
                        if ( filterParams[ rest ].LIST[i] === '' ) filterParams[ rest ].LIST[i] = null;
                    }
                break;
                case 'fromNumber':
                    if ( !filterParams[ rest ].RANGE ) filterParams[ rest ].RANGE = {};
                    filterParams[ rest ].RANGE.START = String( value );
                break;
                case 'toNumber':
                    if ( !filterParams[ rest ].RANGE ) filterParams[ rest ].RANGE = {};
                    filterParams[ rest ].RANGE.END = String( value );
                break;
                case 'fromDate':
                    if ( !filterParams[ rest ].RANGE ) filterParams[ rest ].RANGE = {};
                    filterParams[ rest ].RANGE.START = String( value );
                break;
                case 'toDate':
                    if ( !filterParams[ rest ].RANGE ) filterParams[ rest ].RANGE = {};
                    filterParams[ rest ].RANGE.END = String( value );
                break;
                case 'discard':
                    if ( value === getMessage.FTE00040) {
                        filterParams[ rest ].NORMAL = '';
                    } else if ( value === getMessage.FTE00041) {
                        filterParams[ rest ].NORMAL = '0';
                    } else {
                        filterParams[ rest ].NORMAL = '1';
                    }
                break;
            }
        }
    });

    return filterParams;
}
/*
##################################################
   FilterをクリアしてTableを表示する
##################################################
*/
clearFilter() {
    const tb = this;
    tb.$.message.empty();
    tb.data.body = null;
    tb.setInitSort();
    tb.option.initSetFilter = undefined;
    tb.flag.initFilter = ( tb.info.menu_info.initial_filter_flg === '1');
    tb.setTable( tb.mode );
}
/*
##################################################
   Filter select box HTML
##################################################
*/
filterSelectBoxHtml( list, name, rest ) {
    const select = [];

    // listをソートする
    list.sort(function( a, b ){
        a = fn.cv( a, '');
        b = fn.cv( b, '');
        return a.localeCompare( b );
    });

    for ( const item of list ) {
        const value = fn.cv( item, '', true );
        if ( value !== '') {
            select.push(`<option value="${value}">${value}</option>`)
        } else {
            select.push(`<option value="">{空白}</option>`)
        }
    }
    return `<select class="filterSelect filterInput" name="${name}" data-type="select" data-rest="${rest}" multiple="multiple">${select.join('')}</select>`;
}
/*
##################################################
   Worker post
   > Workerにmessageを送信
##################################################
*/
workerPost( type, data ) {
    const tb = this;

    const post = {
        type: type,
        paging: tb.paging,
        sort: tb.sort,
        idName: tb.idNameRest
    };

    // 送信タイプ別
    switch ( type ) {
        case 'filter': {
            const url = fn.getRestApiUrl(
                tb.rest.filter,
                tb.params.orgId,
                tb.params.wsId );

            post.rest = {
                token: CommonAuth.getToken(),
                url: url,
                filter: data
            };
        } break;
        case 'edit':
            post.select = data;
        break;
        case 'add':
        case 'changeEditRegi':
            post.add = data;
        break;
        case 'dup':
            post.select = data.select;
            post.addId = data.id;
            post.input = data.input;
        break;
        case 'changeEditDup':
            post.select = data.target;
            post.addId = data.id;
        break;
        case 'del':
            post.select = data;
        break;
        case 'normal':
            post.tableData = data;
        break
        case 'discard':
        case 'restore':
            post.select = data;
        break;
        case 'history': {
            const url = fn.getRestApiUrl(
                `${tb.rest.filter}journal/${data}/`,
                tb.params.orgId,
                tb.params.wsId );

            post.rest = {
                token: CommonAuth.getToken(),
                url: url
            };
        } break;
    }
    tb.worker.postMessage( post );
}
/*
##################################################
   Workerイベント
##################################################
*/
setWorkerEvent() {
    const tb = this;
    tb.worker.addEventListener('message', function( message ){
        const type = message.data.type;

        switch ( type ) {
            case 'discard':
            case 'restore':
                tb.changeDiscard( message.data.selectData, type );
                tb.workEnd();
            break;
            case 'error':
                tb.workEnd();
                alert( message.data.result.message );
                location.replace('system_error/');
            break;
            default:
                tb.data.body =  message.data.result;

                if ( message.data.order ) tb.data.order = message.data.order;
                if ( message.data.discard ) tb.data.discard = message.data.discard;
                if ( message.data.paging ) {
                    tb.paging = message.data.paging;
                    tb.data.count = message.data.paging.num;
                }

                if ( type === 'changeEditDup' || type === 'changeEditRegi') {
                    tb.select.view = [];
                    tb.setTable('edit');
                } else {
                    tb.setTbody();
                }
        }
    });
}
/*
##################################################
   Set Body
   // HTMLセット後、Tableの調整をする
##################################################
*/
setTbody() {
    const tb = this;

    if ( !tb.flag.initFilter ) {
        tb.$.container.removeClass('initFilterStandBy');
    }

    if ( tb.mode === 'history') {
        tb.$.container.removeClass('historyStandBy');
    }

    // 表示するものがない
    if ( tb.mode !== 'edit' && tb.data.body.length === 0 ) {
        tb.$.container.addClass('noData');
        tb.$.message.html(`<div class="noDataMessage">`
        + fn.html.icon('stop')
        + getMessage.FTE00054
        + `</div>`);
    } else {
        tb.$.container.removeClass('noData');
        if ( tb.mode === 'view' && tb.flag.update ) {
            tb.$.header.find('.itaButton[data-type="tableEdit"]').prop('disabled', false );
        }
        if ( tb.mode === 'diff' ) {
            tb.advanceButtonCheck( false );
        }
    }

    tb.$.tbody.html( tb.tbodyHtml() );
    tb.updateFooterStatus();
    tb.$.body.scrollTop(0);
    tb.workEnd();

    tb.$.table.addClass('tableReady');

    if ( tb.mode !== 'edit') {
        tb.tableMaxWidthCheck('tbody');
    } else {
        tb.$.tbody.find('.textareaAdjustment').each( fn.textareaAdjustment );
        tb.editModeMenuCheck();
    }

    if ( ( tb.mode === 'select' && tb.params.selectType === 'multi') || tb.mode === 'edit' || tb.mode === 'view') {
        tb.checkSelectStatus();
    }

    tb.filterDownloadButtonCheck();
    tb.stickyWidth();
}
/*
##################################################
   表示可能件数を超えた場合の表示
##################################################
*/
limitSetBody() {
    const tb = this;

    const limitNumber = Number( fn.cv( tb.info.menu_info.web_print_limit, -1 ) );

    tb.$.container.addClass('noData');
    tb.$.message.html(`<div class="noDataMessage">`
    + fn.html.icon('stop')
    + fn.escape( getMessage.FTE00067( tb.data.count, limitNumber ), true )
    + `</div>`);

    tb.workEnd();
    tb.$.table.addClass('tableReady');
}
/*
##################################################
   Set filter standby
   > 初期フィルターオフ用
##################################################
*/
setInitFilterStandBy() {
    const tb = this;

    if ( tb.option.sheetType !== 'reference') {
        tb.$.body.addClass('filterShow');
    }

    tb.$.header.find('.itaButton[data-type="filterToggle"]').attr('data-toggle', 'on');
    tb.$.container.addClass('initFilterStandBy');

    tb.$.message.html(`<div class="initFilterStandByMessage">`
    + fn.html.icon('circle_info')
    + getMessage.FTE00055 + `<br>`
    + getMessage.FTE00056 + `</div>`);

    tb.workEnd();
    tb.$.table.addClass('tableReady');

    tb.$.table.ready(function(){
        tb.stickyWidth();
    });
}
/*
##################################################
   Headerの調整
##################################################
*/
stickyWidth() {
    const tb = this;

    if ( tb.getTableSettingValue('direction') !== 'horizontal') {

        const style = [];

        // left sticky
        let leftStickyWidth = 0,
            leftStickyFilterMenuWidth = 0;

        let filterHeaderFlag = true,
            filterHeaderColspan = Number( tb.$.thead.find('.tHeadFilterHeader').attr('colspan') );
        if ( isNaN( filterHeaderColspan ) ) {
            filterHeaderColspan = 1;
            filterHeaderFlag = false;
        }

        tb.$.body.find('.tableWrap').find('.tHeadTr').eq(0).find('.tHeadLeftSticky').each(function( index ){
            const $th = $( this ),
                  rest = $th.attr('data-rest'),
                  width = $th.outerWidth();
            if ( $( this ).is(':visible') ) {
                if ( index !== 0 ) {
                    style.push(`#${tb.id} .headerTr .tHeadLeftSticky:nth-child(${ index + 1 }){left:${leftStickyWidth}px}`);
                    if ( index >= filterHeaderColspan ) {
                        style.push(`#${tb.id} .filterTr .tHeadLeftSticky.tHeadFilter:nth-child(${ index + 1 - filterHeaderColspan + 1 }){left:${leftStickyWidth}px}`);
                    }
                    style.push(`#${tb.id} .tBodyLeftSticky:nth-child(${ index + 1 }){left:${leftStickyWidth}px}`);
                }
                leftStickyWidth += width;
                if ( [ tb.idNameRest, 'discard'].indexOf( rest ) === -1 ) {
                    leftStickyFilterMenuWidth += width;
                }
            }
        });

        if ( !filterHeaderFlag ) leftStickyFilterMenuWidth += 1;

        if ( tb.option.sheetType !== 'reference' && tb.getTableSettingValue('filter') !== 'out') {
            style.push(`#${tb.id} .filterMenuList{left:${leftStickyFilterMenuWidth}px;}`);
        }
        style.push(`#${tb.id} .tHeadGroup>.ci{left:${leftStickyWidth}px;}`);

        tb.$.style.html( style.join('') );
    } else {
        const style = [];
        let topStickyHeight = 0;

        tb.$.body.find('.tableWrap').find('.tHeadTr').eq(0).find('.tHeadLeftSticky').each(function( index ){
            const $th = $( this ),
                  height = $th.outerHeight();
            if ( $( this ).is(':visible') ) {
                if ( index !== 0 ) {
                    style.push(`#${tb.id} .tableWrap .headerTr .tHeadLeftSticky:nth-child(${ index + 1 }){top:${topStickyHeight}px}`);
                    style.push(`#${tb.id} .tableWrap .tBodyLeftSticky:nth-child(${ index + 1 }){top:${topStickyHeight}px}`);
                }
                topStickyHeight += height;
            }
        });
        style.push(`#${tb.id} .tableWrap .tHeadGroup>.ci{top:${topStickyHeight}px;}`);
        tb.$.style.html( style.join('') );
    }
}
/*
##################################################
   Table width check
   > 最大幅を超えた場合調整する
##################################################
*/
tableMaxWidthCheck( target ) {
    const tb = this;
    tb.$[ target ].find('.ci').each(function(){
        const $ci = $( this ),
              ci = $ci.get(0);

        if ( $ci.is('.textOverWrap') ) {
            $ci.css('width', 'auto').removeClass('textOverWrap');
        }

        if ( ci.clientWidth < ci.scrollWidth ) {
            $ci.css('width', ci.clientWidth ).addClass('textOverWrap');
        }

    });
}
/*
##################################################
   Body HTML
##################################################
*/
tbodyHtml() {
    const tb = this,
          list = tb.data.body;

    const html = [];

    for ( const item of list ) {
        const rowHtml = [],
              rowParameter = item.parameter,
              rowId = String( rowParameter[ tb.idNameRest ] ),
              rowClassName = ['tBodyTr'],
              journal = item.journal;

        // 廃止Class
        if ( tb.discardCheck( rowId ) === '1') {
            rowClassName.push('tBodyTrDiscard');
        }

        // モード別列
        const rowCheckInput = function( type = 'check') {
            // チェック状態
            const attrs = {};
            if ( tb.mode === 'select' || tb.mode === 'execute') {
                const selectId = tb.select[ tb.mode ].find(function( item ){
                    return item.id === rowId;
                });
                if ( selectId ) {
                    attrs['checked'] = 'checked';
                }
            } else {
                if ( tb.select[ tb.mode ].indexOf( rowId ) !== -1 ) {
                    attrs['checked'] = 'checked';
                }
            }
            // selectモード
            if ( tb.mode === 'select' || tb.mode === 'execute') {
                rowClassName.push('tBodyTrRowSelect');
                attrs.selectname = fn.cv( rowParameter[ tb.params.selectNameKey ], '', true );
                if ( tb.params.selectOtherKeys ) {
                    const selectParams = {};
                    for ( const selectKey of tb.params.selectOtherKeys ) {
                        attrs[selectKey] = fn.cv( rowParameter[ selectKey ], '', true );
                    }
                }
            }
            const idName = ( type === 'check')? `${tb.id}__ROWCHECK`: `${tb.id}__ROWRADIO`,
                  className = ( type === 'check')? 'tBodyRowCheck': 'tBodyRowRadio',
                  rowSelectClassName = ( type === 'check')? 'tBodyRowSelect': 'tBodyRowRadioSelect';

            const checkboxId = `${idName}__${rowId}`,
                  checkbox = fn.html[ type ]( className, rowId, idName, checkboxId, attrs );
            return fn.html.cell( checkbox, ['tBodyLeftSticky', rowSelectClassName, 'tBodyTh'], 'th');
        };

        switch ( tb.mode ) {
            case 'view': {
                const viewMenu = [];
                if ( tb.flag.update ) {
                    viewMenu.push({ type: 'rowEdit', text: getMessage.FTE00009, action: 'default', id: rowId, className: 'tBodyRowMenuTb'});
                }
                if ( tb.flag.insert ) {
                    viewMenu.push({ type: 'rowDup', text: getMessage.FTE00013, action: 'duplicat', id: rowId, className: 'tBodyRowMenuTb'});
                }
                if ( tb.flag.history ) {
                    viewMenu.push({ type: 'rowHistory', text: getMessage.FTE00057, action: 'history', id: rowId, className: 'tBodyRowMenuUi'});
                }
                if ( tb.flag.update ) {
                    rowHtml.push( rowCheckInput() );
                }
                const viewMenuHtml = ( viewMenu.length )? tb.rowMenuHtml( viewMenu ): '<span class="tBodyAutoInput"></span>';
                rowHtml.push( fn.html.cell( viewMenuHtml, ['tBodyLeftSticky', 'tBodyRowMenu', 'tBodyTh'], 'th'));
            } break;
            case 'edit':
                if ( tb.flag.edit || tb.flag.disuse || tb.flag.reuse ) {
                    rowHtml.push( rowCheckInput() );
                }
            break;
            case 'diff': {
                const typeText = {
                    register: getMessage.FTE00072,
                    update: getMessage.FTE00073,
                    discard: getMessage.FTE00074,
                    restore: getMessage.FTE00075
                };
                const type = fn.html.span(`editType ${tb.option.type[rowId]}`, typeText[ tb.option.type[rowId] ]);
                rowHtml.push( fn.html.cell( type, ['tBodyLeftSticky', 'tBodyRowEditType', 'tBodyTh'], 'th') );
            } break;
            case 'history':
                const num = fn.cv( rowParameter.journal_id, '', true ),
                      date = fn.date( fn.cv( rowParameter.journal_datetime, '', true ), 'yyyy/MM/dd HH:mm:ss'),
                      action = fn.cv( rowParameter.journal_action, '', true );
                rowHtml.push( fn.html.cell( action, ['tBodyLeftSticky', 'tBodyTh'], 'th') );
                rowHtml.push( fn.html.cell( num, ['tBodyTd'], 'td') );
                rowHtml.push( fn.html.cell( date, ['tBodyTd'], 'td') );
            break;
            case 'select': case 'execute':
                if ( tb.params.selectType !== 'multi' ) {
                    rowHtml.push( rowCheckInput('radio') );
                } else {
                    rowHtml.push( rowCheckInput('check') );
                }
            break;
        }

        for ( const columnKey of tb.data.columnKeys ) {
            rowHtml.push( tb.cellHtml( item, columnKey, journal ) );
        }
        html.push( fn.html.row( rowHtml.join(''), rowClassName ) );

    }
    return html.join('');
}
/*
##################################################
   Cell HTML
##################################################
*/
cellHtml( item, columnKey, journal ) {
    const tb = this;

    const columnInfo = tb.info.column_info[ columnKey ],
          columnName = columnInfo.column_name_rest,
          columnType = columnInfo.column_type;

    // 一部のモードではボタンカラムを表示しない
    const buttonColumnHide = ['select',  'history'];
    if ( columnInfo.column_type === 'ButtonColumn' && buttonColumnHide.indexOf( tb.mode ) !== -1 ) {
        return '';
    }

    const className = [];
    if ( columnType === 'NumColumn') className.push('tBodyTdNumber');
    if ( columnName === 'discard') className.push('tBodyTdMark discardCell');

    // 廃止、ID列を固定
    let cellClass = 'tBodyTd',
        cellType = 'td';
    if ( tb.mode !== 'history') {
        if ( [ tb.idNameRest, 'discard'].indexOf( columnName ) !== -1 ) {
            className.push('tBodyLeftSticky');
            cellType = 'th';
            cellClass = 'tBodyTh';
        }
    }
    className.push( cellClass );

    switch ( tb.mode ) {
        case 'view':
            if ( columnInfo.column_type === 'ButtonColumn') {
                className.push('tBodyTdButton');
            }
            return fn.html.cell( tb.viewCellHtml( item, columnKey ), className, cellType );
        case 'select': case 'execute':
            return fn.html.cell( tb.viewCellHtml( item, columnKey ), className, cellType );
        break;
        case 'history':
            return fn.html.cell( tb.viewCellHtml( item, columnKey, journal ), className, cellType );
        case 'edit':
            if ( ( columnName !== 'discard' && item.discard === '1' ) && columnName !== 'remarks' ) {
                return fn.html.cell( tb.viewCellHtml( item, columnKey ), className, cellType );
            } else {
                className.push('tBodyTdInput');
                return fn.html.cell( tb.editCellHtml( item, columnKey ), className, cellType );
            }
        case 'diff':
            return fn.html.cell( tb.editConfirmCellHtml( item, columnKey ), className, cellType );
    }
}
/*
##################################################
   Discard mark
##################################################
*/
discardMark( value ) {
    return ( value === '0')? '<span class="discardMark false">0</span>': '<span class="discardMark true">1</span>';
}
/*
##################################################
   Discard check
##################################################
*/
discardCheck( id ) {
    const tb = this;

    // 編集データがある場合
    if ( tb.edit.input[ id ] && tb.edit.input[ id ].after.parameter.discard ) {
        return tb.edit.input[ id ].after.parameter.discard;
    }

    if ( tb.data.body ) {
        const target = tb.data.body.find(function( item ){
            return id === item.parameter[ tb.idNameRest ];
        });

        if ( target !== undefined && target.parameter.discard ) {
            return target.parameter.discard;
        } else {
            return '0';
        }
    }
}
/*
##################################################
   View mode cell HTML
##################################################
*/
viewCellHtml( item, columnKey, journal ) {
    const tb = this;

    const parameter = item.parameter,
          file = item.file;

    const columnInfo = tb.info.column_info[ columnKey ],
          columnName = columnInfo.column_name_rest,
          autoInput = '<span class="tBodyAutoInput"></span>';

    let columnType = columnInfo.column_type,
        value =  fn.cv( parameter[ columnName ], '');

    if ( fn.typeof( value ) === 'string') {
        value = fn.escape( value );
    }

    // 変更履歴
    const checkJournal = function( val ) {
        if ( journal && journal[ columnName ] !== undefined ) {
            val = `<span class="journalChange">${val}</span>`;
        }
        return val;
    }

    // 廃止列
    if ( columnName === 'discard') {
        value = tb.discardMark( value );
        return checkJournal( value );
    }

    // ID列処理
    if ( columnName === tb.idNameRest && !isNaN( value ) && Number( value ) < 0 ) {
        return autoInput;
    }

    // Sensitiveカラムはフラグによって表示を分ける
    if ( ['SensitiveSingleTextColumn', 'SensitiveMultiTextColumn'].indexOf( columnType ) !== -1 ) {
        const flagTarget = columnInfo.sensitive_coloumn_name,
              sensitiveFlag = parameter[ flagTarget ];
        if ( sensitiveFlag === 'True') {
            columnType = 'PasswordColumn';
        } else {
            if ( columnType === 'SensitiveSingleTextColumn') {
                columnType = 'SingleTextColumn';
            } else {
                columnType = 'MultiTextColumn';
            }
        }
    }

    switch ( columnType ) {
        // そのまま表示
        case 'SingleTextColumn': case 'NumColumn': case 'FloatColumn':
        case 'IDColumn': case 'LinkIDColumn':
        case 'LastUpdateUserColumn': case 'RoleIDColumn':
        case 'EnvironmentIDColumn': case 'TextColumn':
        case 'DateColumn': case 'DateTimeColumn':
        case 'FileUploadEncryptColumn': case 'JsonIDColumn':
        case 'UserIDColumn':
            return checkJournal( value );

        // リンク
        case 'HostInsideLinkTextColumn':
            if ( value !== '') {
                return checkJournal(`<a href="${value}" target="_blank">${value}</a>`);
            } else {
                return checkJournal( value );
            }

        // 最終更新日
        case 'LastUpdateDateColumn':
            return checkJournal( fn.date( value, 'yyyy/MM/dd HH:mm:ss') );

        // 改行を<br>に置換
        case 'MultiTextColumn': case 'NoteColumn':
            if ( !isNaN( value ) ) {
                return checkJournal( value );
            } else {
                return checkJournal( value.replace(/\n/g, '<br>') );
            }

        // ********で表示
        case 'PasswordColumn': case 'PasswordIDColumn': case 'JsonPasswordIDColumn': case 'MaskColumn':
            return `<div class="passwordColumn">********</div>`;

        // ファイル名がリンクになっていてダウンロード可能
        case 'FileUploadColumn': {
            const id = ( tb.mode !== 'history')? parameter[ tb.idNameRest ]: parameter.journal_id;
            if ( file[ columnName ] !== null ) {
                return checkJournal(`<a href="${value}" class="tableViewDownload" data-id="${id}" data-rest="${columnName}">${value}</a>`);
            } else {
                return checkJournal( value );
            }
        }
        // ボタン
        case 'ButtonColumn':
            return tb.buttonAction( columnInfo, item, columnKey );

        // JSON
        case 'JsonColumn':
            if ( value !== '') {
                try {
                    value = JSON.stringify( value );
                    //if ( value.length > 64 ) value = value.substr( 0, 64 ) + '...';
                    return checkJournal( value );
                } catch ( error ) {
                    return `<div class="jsonError">${error.essage}</div>`
                }
            } else {
                return checkJournal( value );
            }

        // 不明
        default:
            return '?';
    }
}
/*
##################################################
  Button action
##################################################
*/
buttonAction( columnInfo, item, columnKey ) {
    const tb = this;

    // ボタンアクション
    let buttonAction;
    try {
        buttonAction = JSON.parse( columnInfo.button_action );
    } catch( e ) {
        buttonAction = [];
    }

    const buttonAttrs = {
        rest: columnInfo.column_name_rest,
    };
    for ( const action of buttonAction ) {

        // タイプ
        buttonAttrs.type = fn.cv( action[0], '');
        switch ( buttonAttrs.type ) {
            // 別ページにリダイレクト
            case 'redirect':
                if ( !buttonAttrs.redirect ) {
                    buttonAttrs.redirect = '?';
                } else {
                    buttonAttrs.redirect += '&';
                }
                const param = fn.cv( item.parameter[ action[2] ], '', true );
                buttonAttrs.action = 'positive';
                buttonAttrs.redirect += action[1] + param;
                // 値が無い場合はボタンを無効化
                if ( param === '') buttonAttrs.disabled = 'disabled';
            break;
            case 'redirect_filter':
                buttonAttrs.item = item.parameter[ tb.idNameRest ];
                buttonAttrs.columnkey = columnKey;
                buttonAttrs.action = 'positive';
            break;
            // ファイルダウンロード
            case 'download': {
                const endPoint = action[2].replace('{menu}', tb.params.menuNameRest ),
                      valueKeys = action[3];

                buttonAttrs.method = action[1];
                buttonAttrs.fileName = action[4][0];
                buttonAttrs.fileData = action[4][1];

                if ( endPoint ) {
                    let api = endPoint.replace(/^\/ita/, '');
                    for ( const key of valueKeys ) {
                        const value = item.parameter[ key ];
                        if ( value ) {
                            // keyを値に置換
                            api = api.replace(`{${key}}`, value );
                        }
                    }
                    buttonAttrs.url = api;
                    buttonAttrs.action = 'default';
                } else {
                    buttonAttrs.disabled = 'disabled';
                }
            } break;
            // モーダル
            case 'modal': {
                buttonAttrs.modal = action[1];
                buttonAttrs.action = 'default';
                buttonAttrs.id = item.parameter[ tb.idNameRest ];
            } break;
            // REST API
            case 'restapi_redirect':
            case 'restapi': {
                const method = action[1],
                      endPoint = action[2],
                      valueKeys = action[3],
                      bodyKeys = action[4];

                if ( endPoint && valueKeys ) {
                    let api = endPoint.replace(/^\/ita/, '');
                    const replaceTarget = api.match(/\{[^\{\}]*\}/g);
                    if ( replaceTarget !== null ) {
                        const replaceLength = replaceTarget.length;
                        for ( let i = 0; i < replaceLength; i++ ) {
                            const value = ( valueKeys[i] )? fn.cv( item.parameter[ valueKeys[i] ] ): '';
                            if ( value ) api = api.replace( replaceTarget[i], value );
                        }
                    }
                    buttonAttrs.restapi = api;
                }

                if ( endPoint && bodyKeys ) {
                    const body = {};
                    for ( const key of bodyKeys ) {
                        const value = item.parameter[ key ];
                        if ( value ) {
                            // keyを値に置換
                            body[ key ] = value;
                        }
                    }
                    buttonAttrs.body = fn.escape( JSON.stringify( body ) );
                }
                buttonAttrs.action = 'default';
                buttonAttrs.key = columnKey;
                buttonAttrs.method = method;
                if ( buttonAttrs.type === 'restapi_redirect') {
                    buttonAttrs.redirect = action[5];
                    buttonAttrs['redirect-key'] = action[6]
                }
            } break;
        }
    }

    const text = fn.cv( columnInfo.column_name, '', true );
    return fn.html.button( text, ['actionButton', 'itaButton'], buttonAttrs );
}
/*
##################################################
   Edit mode cell HTML
##################################################
*/
editCellHtml( item, columnKey ) {
    const tb = this;

    const parameter = item.parameter,
          file = item.file;

    const rowId = parameter[ tb.idNameRest ],
          columnInfo = tb.info.column_info[ columnKey ],
          columnName = columnInfo.column_name_rest,
          columnType = columnInfo.column_type,
          inputClassName = [],
          inputRequired = fn.cv( columnInfo.required_item, '0'),
          autoInput = '<span class="tBodyAutoInput"></span>',
          inputItem = columnInfo.input_item,
          name = '';

    let value = fn.cv( parameter[ columnName ], '', true );

    const attr = {
        key: columnName,
        id: rowId,
        required: inputRequired
    };

    // 廃止チェック
    if ( tb.discardCheck( rowId ) === '1') {
        attr.disabled = 'disabled';
    }

    // 入力済みのデータがある？
    const inputData = tb.edit.input[ rowId ];
    if ( inputData !== undefined ) {

        const afterParameter = tb.edit.input[ rowId ]['after'].parameter[ columnName ];
        if ( afterParameter !== undefined ) {
            value =  fn.escape( afterParameter );

            const beforeParameter = tb.edit.input[ rowId ]['before'].parameter[ columnName ];
            if ( afterParameter !== beforeParameter ) {
                inputClassName.push('tableEditChange');
            }
        }
    }

    // required_item
    if ( inputRequired === '1') {
        attr['required'] = inputRequired;
        if ( value === '') inputClassName.push('tableEditRequiredError');
    }

    // validate_option
    if ( columnInfo.validate_option ) {
        try {
            const validates = JSON.parse( columnInfo.validate_option );
            for ( const validate in validates ) {
                attr[ validate.replace(/_/g, '-').toLowerCase() ] = validates[ validate ];
            }
        } catch ( e ) {
            window.console.group('JSON parse error.')
            window.console.warn(`validate_option : ${columnInfo.validate_option}`);
            window.console.warn( e );
            window.console.groupEnd('JSON parse error.')
        }
    }

    // ID列処理
    if ( columnName === tb.idNameRest ) {
        if ( !isNaN( value ) && Number( value ) < 0 ) {
            return autoInput;
        } else {
            return value;
        }
    }

    // 廃止列
    if ( columnName === 'discard') {
        value = tb.discardMark( value );
        return fn.html.span( inputClassName, value, name, attr );
    }

    // 最終更新日時
    if ( columnType === 'LastUpdateDateColumn') {
        if ( value !== '') {
            return fn.date( value, 'yyyy/MM/dd HH:mm:ss');
        } else {
            return autoInput;
        }
    }

    // 編集不可（input_item）
    if ( inputItem === '0' || columnType === 'LastUpdateUserColumn') {
        if ( value !== '') {
            return value;
        } else {
            return autoInput;
        }
    }

    // input_item 3
    if ( inputItem === '3') {
        inputClassName.push('tableEditInputHidden');
        return `<div class="tableEditInputHiddenText">${value}</div>` + fn.html.inputHidden( inputClassName, value, name, attr );
    }

    switch ( columnType ) {
        // 文字列入力（単一行）
        case 'SingleTextColumn': case 'HostInsideLinkTextColumn': case 'JsonColumn':
        case 'TextColumn': case 'SensitiveSingleTextColumn':
            inputClassName.push('tableEditInputText');
            return fn.html.inputText( inputClassName, value, name, attr, { widthAdjustment: true });

        // 文字列入力（複数行）
        case 'MultiTextColumn': case 'NoteColumn': case 'SensitiveMultiTextColumn':
            inputClassName.push('tebleEditTextArea');
            return fn.html.textarea( inputClassName, value, name, attr, true );

        // 整数値
        case 'NumColumn':
            inputClassName.push('tableEditInputNumber');
            return fn.html.inputNumber( inputClassName, value, name, attr );

        // 小数値
        case 'FloatColumn':
            inputClassName.push('tableEditInputNumber');
            return fn.html.inputNumber( inputClassName, value, name, attr );

        // 日付
        case 'DateColumn':
            inputClassName.push('tableEditInputText');
            return fn.html.dateInput( false, inputClassName, value, name, attr );

        // 日時
        case 'DateTimeColumn':
            inputClassName.push('tableEditInputText');
            return fn.html.dateInput( true, inputClassName, value, name, attr );

        // プルダウン
        case 'IDColumn': case 'LinkIDColumn': case 'RoleIDColumn': case 'UserIDColumn':
        case 'EnvironmentIDColumn': case 'JsonIDColumn':
            return `<div class="tableEditInputSelectContainer ${inputClassName.join(' ')}">`
            + `<div class="tableEditInputSelectValue"><span class="tableEditInputSelectValueInner">${value}</span></div>`
            + fn.html.select( fn.cv( tb.data.editSelect[columnName], {}), 'tableEditInputSelect', value, name, attr, { select2: true } )
            + `</div>`;

        // パスワード
        case 'PasswordColumn': case 'PasswordIDColumn': case 'JsonPasswordIDColumn': case 'MaskColumn': {
            const deleteToggleFlag = ( !isNaN( rowId ) && Number( rowId ) < 0 )? false: true,
                  deleteFlag = ( inputData && inputData.after.parameter[ columnName ] === null )? true: false;
            inputClassName.push('tableEditInputText');

            return fn.html.inputPassword( inputClassName, value, name, attr, { widthAdjustment: true, deleteToggle: deleteToggleFlag, deleteFlag: deleteFlag });
        }

        // ファイルアップロード
        case 'FileUploadColumn': case 'FileUploadEncryptColumn':
            inputClassName.push('tableEditSelectFile');
            return fn.html.fileSelect( value, inputClassName, attr );

        // ボタン
        case 'ButtonColumn':
            return tb.buttonAction( columnInfo, item, columnKey );

        // 不明
        default:
            return '?';
    }
}
/*
##################################################
   Edit mode confirmation cell HTML
##################################################
*/
editConfirmCellHtml( item, columnKey ) {
    const tb = this;

    const parameter = item.parameter,
          file = item.file;

    const columnInfo = tb.info.column_info[ columnKey ],
          columnName = columnInfo.column_name_rest,
          rowId = parameter[ tb.idNameRest ],
          type = ( !isNaN( rowId ) && Number( rowId ) < 0 )? 'registration': 'update',
          beforeData = tb.option.before[ rowId ],
          autoInput = '<span class="tBodyAutoInput"></span>';

    let columnType = columnInfo.column_type,
        value = fn.cv( parameter[ columnName ], '', true );

    // ID列処理
    if ( columnName === tb.idNameRest ) {
        if ( type === 'registration') {
            return autoInput;
        } else {
            return value;
        }
    }

    const valueCheck = function( val, data = '' ) {
        if ( columnName === 'discard' ) {
            return tb.discardMark( val );
        }
        switch ( columnType ) {
            // 最終更新日
            case 'LastUpdateDateColumn':
                return fn.date( val, 'yyyy/MM/dd HH:mm:ss')

            // 改行を<br>に置換
            case 'MultiTextColumn': case 'NoteColumn':
                if ( isNaN( val ) ) {
                    return val.replace(/\n/g, '<br>');
                } else {
                    return val;
                }

            // ファイル名がリンクになっていてダウンロード可能
            case 'FileUploadColumn':
                const id = parameter[ tb.idNameRest ];
                return `<a href="${val}" class="tableViewDownload" data-type="${data}" data-id="${id}" data-rest="${columnName}">${val}</a>`;

            default:
                return val;
        }
    }

    const beforeAfter = function( before, after ) {
        return `<div class="tBodyAfterValue">${after}</div>`
            + `<div class="tBodyBeforeValue">${before}</div>`;
    };

    // 廃止の場合は変更前を表示する（廃止、備考以外）
    if ( parameter.discard === '1' && columnName !== 'discard' && columnName !== 'remarks') {
        if ( beforeData !== undefined ) {
            return valueCheck( fn.cv( beforeData.parameter[ columnName ], '', true ) );
        } else {
            return '';
        }
    }

    // パスワードカラム
    const password = ['PasswordColumn', 'PasswordIDColumn', 'JsonPasswordIdColumn', 'MaskColumn'];
    if ( password.indexOf( columnType ) !== -1 ) {
        if ( parameter[ columnName ] === false ) {
            return '<span class="confirmDeleteText">' + getMessage.FTE00014 + '</span>';
        } else if ( value !== '' && type !== 'registration') {
            return beforeAfter(`<div class="passwordColumn">********</div>`, `<div class="passwordColumn">********</div>`);
        } else {
            return `<div class="passwordColumn">********</div>`;
        }
    }

    // 基本
    if ( parameter[ columnName ] !== undefined ) {
        if ( beforeData !== undefined && type === 'update') {
            return beforeAfter( valueCheck( fn.cv( beforeData.parameter[ columnName ], '', true ), 'beforeValue' ), valueCheck( value, 'afterValue')  );
        } else {
            return valueCheck( value );
        }
    } else {
        if ( beforeData !== undefined ) {
            return valueCheck( fn.cv( beforeData.parameter[ columnName ], '', true ) );
        } else {
            return '';
        }
    }
}
/*
##################################################
   Row menu
   > 行メニュー（履歴など）
##################################################
*/
rowMenuHtml( list ) {
    const tb = this;

    const html = [];
    for ( const item of list ) {
        const button = fn.html.button( item.text, [ item.className, 'tableRowMenuButton', 'itaButton'],
            { type: item.type, action: item.action, id: item.id });
        html.push(`<li class="tableRowMenuItem">${button}</li>`);
    }

    if ( tb.getTableSettingValue('menu') === 'show') {
        return `<div class="tableRowMenu"><ul class="tableRowMenuList">${html.join('')}</ul></div>`;
    } else {
        return `${fn.html.icon('ellipsis_v')}<div class="tableRowMenu"><ul class="tableRowMenuList">${html.join('')}</ul></div>`;
    }
}
/*
##################################################
   Footer HTML
##################################################
*/
footerHtml() {
    const tb = this;

    const onePageNumList = [ 10, 25, 50, 75, 100 ];
    const onePageNumOptions = [];
    for ( const item of onePageNumList ) {
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
                <dt class="tableFooterTitle"><span class="footerText pagingAllTitle">` + getMessage.FTE00058 + `</span></dt>
                <dd class="tableFooterItem tableFooterData"><span class="footerText pagingAllNumNumber">` + getMessage.FTE00059 + `</span></dd>
            </dl>
        </div>
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
/*
##################################################
   Update footer status
   > Table情報を更新する
##################################################
*/
updateFooterStatus() {
    const tb = this;


    if ( tb.mode === 'edit' || tb.mode === 'diff') {
        tb.$.footer.find('.pagingAllTitle').text(getMessage.FTE00062);
    } else {
        tb.$.footer.find('.pagingAllTitle').text(getMessage.FTE00058);
    }
    tb.$.footer.find('.pagingAllNumNumber').text( tb.paging.num.toLocaleString() + getMessage.FTE00063);
    tb.$.footer.find('.pagingOnePageNumSelectRadio').val([tb.paging.onePageNum]);
    tb.$.footer.find('.pagingOnePageNumSelectNumber').text( tb.paging.onePageNum );

    const $paging = tb.$.footer.find('.pagingMove');
    $paging.find('.pagingCurrentPage').text( tb.paging.pageNum );
    $paging.find('.pagingMaxPageNumber').text( tb.paging.pageMaxNum.toLocaleString() );

    const prevFlag = ( tb.paging.pageNum <= 1 )? true: false;
    $paging.find('.pagingMoveButton[data-type="first"], .pagingMoveButton[data-type="prev"]')
        .prop('disabled', prevFlag );

    const nextFlag = ( tb.paging.pageMaxNum === tb.paging.pageNum )? true: false;
    $paging.find('.pagingMoveButton[data-type="last"], .pagingMoveButton[data-type="next"]')
        .prop('disabled', nextFlag );

}
setPagingEvent() {
    const tb = this;

    const $list = tb.$.footer.find('.pagingOnePageNumSelectList');

    tb.$.footer.find('.pagingMoveButton').on('click', function(){
        if ( !tb.checkWork ) {
            tb.workStart('paging');
            const $b = $( this ),
                  b = $b.attr('data-type');
            switch ( b ) {
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
            tb.workerPost('page');
        }
    });
    tb.$.footer.find('.pagingOnePageNumSelectRadio').on('change', function(){
        if ( !tb.checkWork ) {
            const selectNo = Number( $( this ).val() );
            tb.workStart('paging');
            tb.paging.onePageNum = selectNo;
            tb.$.footer.find('.pagingOnePageNumSelectNumber').text( selectNo );
            $list.removeClass('pagingOnePageOpen');
            tb.workerPost('page');
            fn.storage.set('onePageNum', selectNo );
        }
    });

    tb.$.footer.find('.pagingOnePageNumSelectNumber').on('click', function(){
        if ( !tb.checkWork ) {
            if ( !$list.is('.pagingOnePageOpen') ) {
                const height = tb.$.header.outerHeight() + tb.$.body.outerHeight();
                $list.addClass('pagingOnePageOpen').css('max-height', height );
                $( window ).on('pointerdown.pagingOnePageNum', function(e){
                    if ( !$( e.target ).closest('.pagingOnePageNumSelect').length ) {
                        $( this ).off('pointerdown.pagingOnePageNum');
                        $list.removeClass('pagingOnePageOpen');
                    }
                });
            } else {
                $list.removeClass('pagingOnePageOpen');
            }
        }
    });
}
/*
##################################################
   changeEditMode
##################################################
*/
changeEdtiMode( changeMode ) {
    const tb = this;

    // テーブルモードの変更
    tb.tableMode = 'input';

    // エラーリセット
    tb.$.container.removeClass('tableError');
    tb.$.errorMessage.empty();

    // テーブル構造を再セット
    tb.setHeaderHierarchy();

    const info = tb.info.column_info;

    tb.workStart('table', 0 );
    tb.paging.page = 1;
    tb.edit.addId = -1;

    // 選択状態
    tb.select.edit = tb.select.view.concat();

    tb.$.container.removeClass('viewTable autoFilterStandBy initFilterStandBy');
    tb.$.container.addClass('editTable');

    // フィルタの入力を取得
    const filterParameter = tb.getFilterParameter(),
          filterLength = Object.keys( filterParameter ).length;

    if ( ( filterLength === 1 && filterParameter.discard !== undefined )
         || filterLength === 0 ) {
        // tb.flag.initFilter = (tb.info.menu_info.initial_filter_flg === '1');
        tb.option.initSetFilter = undefined;
    } else {
        tb.option.initSetFilter = tb.getFilterParameter();
    }

    // 編集から戻った際はinitial_filter_flgに関係なく表示
    tb.flag.initFilter = true;

    // セレクトデータを取得後に表示する
    fn.fetch( tb.rest.inputPulldown ).then(function( result ){

        // 選択項目
        tb.data.editSelect = result;

        // 追加用空データ
        tb.edit.blank = {
            file: {},
            parameter: {
                discard: '0'
            }
        };

        // 初期値
        for ( const key of tb.data.columnKeys ) {
            const columnInfo = info[ key ];

            // セレクト必須選択項目
            const selectTarget = ['IDColumn', 'LinkIDColumn', 'AppIDColumn', 'RoleIDColumn', 'JsonIDColumn', 'UserIDColumn'];
            if ( selectTarget.indexOf( columnInfo.column_type ) !== -1
              && columnInfo.required_item === '1'
              && columnInfo.initial_value === null ) {
                const select = tb.data.editSelect[ columnInfo.column_name_rest ];
                if ( select !== undefined ) {
                    tb.edit.blank.parameter[ columnInfo.column_name_rest ] = select[ Object.keys( select )[0] ];
                }
            } else {
                if ( info[ key ].column_name_rest !== 'discard') {
                    tb.edit.blank.parameter[ columnInfo.column_name_rest ] = columnInfo.initial_value;
                }
            }
        }

        if ( changeMode ) {
            switch ( changeMode ) {
                case 'changeEditRegi': {
                    const addId = String( tb.edit.addId-- );
                    tb.edit.blank.parameter[ tb.idNameRest ] = addId;
                    tb.addRowInputData( addId );
                    tb.workerPost('changeEditRegi', tb.edit.blank );
                } break;
                case 'changeEditDup':
                    tb.workerPost('changeEditDup', { target: tb.select.view, id: tb.edit.addId-- });
                break;
            }
        } else {
            tb.setTable('edit');
        }
    }).catch( function( e ) {
        fn.gotoErrPage( e.message );
    });
}
/*
##################################################
   changeViewMode
##################################################
*/
changeViewMode() {
    const tb = this;

    // テーブルモードの変更
    tb.tableMode = 'view';

    // テーブル構造を再セット
    tb.setHeaderHierarchy();

    tb.$.window.off('beforeunload');
    tb.$.container.removeClass('tableError');
    tb.$.table.removeClass('tableReady');
    tb.$.errorMessage.empty();

    tb.$.container.addClass('viewTable');
    tb.$.container.removeClass('editTable');

    tb.workStart('table', 0 );
    tb.select.edit = [];
    tb.select.view = [];
    tb.select.select = [];
    tb.data.body = null;
    tb.data.editSelect = null;
    tb.edit.input = {};
    tb.paging.page = 1;

    if ( tb.initMode === 'select') {
        tb.setTable('select');
    } else {
        tb.setTable('view');
    }
}
/*
##################################################
   resetTable
##################################################
*/
resetTable() {
    const tb = this;

    // テーブル構造を再セット
    tb.setHeaderHierarchy();

    tb.$.container.removeClass('tableError');
    tb.$.table.removeClass('tableReady');
    tb.$.errorMessage.empty();

    tb.workStart('table', 0 );
    tb.select.edit = [];
    tb.select.view = [];
    tb.select.select = [];
    tb.select.execute = [];
    tb.paging.page = 1;

    tb.setTable( tb.mode );
}
/*
##################################################
   Reflect edits
   編集確認ボタン
##################################################
*/
reflectEdits() {
    const tb = this;

    // 表示用データ
    const diffData = {
        before: {},
        after: [],
        type: {}
    };
    for ( const id of tb.data.order ) {
        if ( tb.edit.input[id] ) {
            diffData.before[id] = tb.edit.input[id].before;
            diffData.after.push( tb.edit.input[id].after );
            // 編集タイプを調べる
            if ( tb.edit.input[id].after.parameter.discard ) {
                diffData.type[id] = ( tb.edit.input[id].after.parameter.discard === '0')? 'restore': 'discard';
            } else if ( !isNaN( id ) && Number( id ) < 0 ) {
                diffData.type[id] = 'register';
            } else {
                diffData.type[id] = 'update';
            }
        }
    }

    // モーダル表示
    const config = {
        mode: 'modeless',
        className: 'reflectEditsModal',
        position: 'center',
        width: 'auto',
        header: {
            title: getMessage.FTE00011,
        }
    };

    const modalTable = new DataTable('DT', 'diff', tb.info, tb.params, diffData ),
          modal = new Dialog( config );

    modal.open( modalTable.setup() );

    // メニューボタン
    modalTable.$.header.find('.itaButton ').on('click', function(){
        if ( !tb.checkWork ) {
            const $button = $( this ),
                  type = $button.attr('data-type');
            switch ( type ) {
                // 編集反映
                case 'tableOk':
                    modalTable.workStart('table', 0 );
                    tb.editOk.call( tb ).then(function( result ){
                        modal.close().then( function(){
                            fn.resultModal( result ).then(function(){
                                tb.changeViewMode.call( tb );
                            });
                        });
                    }).catch(function( result ){
                        modal.close().then( function(){
                            tb.editError( result );
                        });
                    });
                break;
                case 'tableCancel':
                    modal.close();
                break;
                case 'tableChangeValue':
                    modalTable.$.container.toggleClass('tableShowChangeValue');
                    modalTable.tableMaxWidthCheck.call( modalTable, 'tbody');
                break;
            }
        }
    });
}
/*
##################################################
   Edit OK ( Modal )
   送信用編集データを作成し送信
##################################################
*/
editOk() {
    const tb = this;

    tb.data.editOrder = [];

    // エラーリセット
    tb.$.container.removeClass('tableError');
    tb.$.errorMessage.empty();

    const editData = [];

    for ( const itemId of tb.data.order ) {
        if ( tb.edit.input[ itemId ] !== undefined ) {
            const info = tb.info.column_info,
                  item = tb.edit.input[ itemId ];

            const itemData = {
                file: {},
                parameter: {}
            };

            tb.data.editOrder.push( itemId );

            for ( const columnKey of tb.data.columnKeys ) {
                const columnNameRest = info[ columnKey ].column_name_rest,
                      columnType = info[ columnKey ].column_type;

                const setData = function( type ) {
                    if ( item.after[ type ][ columnNameRest ] !== undefined ) {
                        return item.after[ type ][ columnNameRest ]
                    } else {
                        return fn.cv( item.before[ type ][ columnNameRest ], null );
                    }
                };

                // 登録か更新か？
                if ( !isNaN( itemId ) && Number( itemId ) < 0 ) {
                    itemData.type = 'Register';
                } else {
                    itemData.type = 'Update';
                }

                if ( tb.idNameRest === columnNameRest && itemData.type === 'Register') {
                    // 登録の場合、IDカラムはnull
                    itemData.parameter[ columnNameRest ] = null;
                } else {
                    switch ( columnType ) {
                        // File
                        case 'FileUploadColumn':
                            itemData.parameter[ columnNameRest ] = setData('parameter');
                            itemData.file[ columnNameRest ] = setData('file');
                        break;
                        case 'FileUploadEncryptColumn': {
                            const fileAfterValue = item.after.parameter[ columnNameRest ];
                            // 変更があるか？
                            if ( fileAfterValue !== undefined && fileAfterValue !== '') {
                                itemData.parameter[ columnNameRest ] = setData('parameter');
                                // nullじゃなければファイルもセット
                                if ( fileAfterValue !== null ) {
                                    itemData.file[ columnNameRest ] = setData('file');
                                }
                                // { key: null } の場合は削除とする
                            }
                            // 変更がなければ値をセットしない
                        } break;
                        // 最終更新日時と最終更新者
                        case 'LastUpdateDateColumn': case 'LastUpdateUserColumn':
                            if ( itemData.type === 'Register' ) {
                                itemData.parameter[ columnNameRest ] = null;
                            } else {
                                itemData.parameter[ columnNameRest ] = setData('parameter');
                            }
                        break;
                        // パスワード
                        case 'PasswordColumn': case 'PasswordIDColumn': case 'JsonPasswordIDColumn': case 'MaskColumn':
                        case 'SensitiveSingleTextColumn': case 'SensitiveMultiTextColumn': {
                            const passwordAfterValue = item.after.parameter[ columnNameRest ];
                            if ( passwordAfterValue === false ) {
                                // false -> 削除 { key: null }
                                itemData.parameter[ columnNameRest ] = null;
                            } else if ( passwordAfterValue !== '' && passwordAfterValue !== null ){
                                // 値有 -> 更新 { key: value }
                                itemData.parameter[ columnNameRest ] = passwordAfterValue;
                            }
                            // null or 空白 -> そのまま（keyをセットしない）
                        } break;
                        // 基本
                        default:
                            itemData.parameter[ columnNameRest ] = setData('parameter');
                    }
                }
            }
            editData.push( itemData );
        }
    }

    return new Promise(function( resolve, reject ){
        fn.fetch( tb.rest.maintenance, null, 'POST', editData )
            .then(function( result ){
                resolve( result );
            })
            .catch(function( result ){
                result.data = editData;
                reject( result );
                //バリデーションエラー
                alert(getMessage.FTE00068);
            });
    });
}
/*
##################################################
   作業実行
##################################################
*/
execute( type ) {
    const tb = this;

    const dryrunText = ( tb.driver === 'ansible')? getMessage.FTE00006: getMessage.FTE00167;

    const setConfig = function() {
        switch ( type ) {
            case 'run':
                return {
                    title: getMessage.FTE00005,
                    rest: `/menu/${tb.params.menuNameRest}/driver/execute/`
                };
            break;
            case 'dryrun':
                return {
                    title: dryrunText,
                    rest: `/menu/${tb.params.menuNameRest}/driver/execute_dry_run/`
                };
            break;
            case 'parameter':
                return {
                    title: getMessage.FTE00007,
                    rest: `/menu/${tb.params.menuNameRest}/driver/execute_check_parameter/`
                };
            break;
        }
    };

    const executeConfig = setConfig();
    executeConfig.itemName = 'Movement';
    executeConfig.selectName = tb.select.execute[0].name;
    executeConfig.selectId = tb.select.execute[0].id;
    executeConfig.operation = tb.params.operation;

    tb.workStart( type );
    fn.executeModalOpen( tb.id + '_' + type, tb.params.menuNameRest, executeConfig ).then(function( result ){
        if ( result !== 'cancel') {
            const postData = {
              movement_name: result.selectName,
              operation_name: result.name,
              schedule_date: result.schedule
            };
            // 作業実行開始
            fn.fetch( executeConfig.rest, null, 'POST', postData ).then(function( result ){
                window.location.href = `?menu=check_operation_status_${tb.params.operationType}&execution_no=${result.execution_no}`;
            }).catch(function( error ){
                if ( error.message ) alert( error.message );
            }).then(function(){
                tb.workEnd();
            });
        } else {
            tb.workEnd();
        }
    });
}
/*
##################################################
   Filter error
   エラー表示
##################################################
*/
filterError( error ) {
    const tb = this;

    let errorMessage;
    try {
        errorMessage = JSON.parse( error.message );
    } catch ( e ) {
        //JSONを作成
        errorMessage["0"][ getMessage.FTE00064 ] = error.message;
    }

    const errorHtml = [];

    for ( const item in errorMessage ) {
        for ( const error in errorMessage[item] ) {
            const name = fn.cv( tb.data.restNames[ error ], error, true );
            let   body = fn.cv( errorMessage[item][error].join(''), '?', true );

            if ( fn.typeof( body ) === 'string') body = body.replace(/\r?\n/g, '<br>');
            errorHtml.push(`<tr class="tBodyTr tr">`
                + fn.html.cell( name, 'tBodyTh', 'th')
                + fn.html.cell( body, 'tBodyTd')
            + `</tr>`);
        }
    }

    tb.$.container.addClass('tableError');
    tb.$.errorMessage.html(`
    <div class="errorBorder"></div>
    <div class="errorTableContainer">
        <div class="errorTitle"><span class="errorTitleInner">${fn.html.icon('circle_exclamation')}${getMessage.FTE00166}</span></div>
        <table class="table errorTable">
            <thead class="thead">
                <tr class="tHeadTr tr">
                <th class="tHeadTh th tHeadErrorColumn"><div class="ci">${getMessage.FTE00070}</div></th>
                <th class="tHeadTh th tHeadErrorBody"><div class="ci">${getMessage.FTE00071}</div></th>
                </tr>
            </thead>
            <tbody class="tbody">
                ${errorHtml.join('')}
            </tbody>
        </table>
    </div>`);
}
/*
##################################################
   Edit error
   エラー表示
##################################################
*/
editError( error ) {
    const tb = this;

    const id_name = tb.data.restNames[ tb.idNameRest ];
    const target = tb.idNameRest;
    let errorMessage;
    try {
        errorMessage = JSON.parse(error.message);
    } catch ( e ) {
        //JSONを作成
        let key = getMessage.FTE00064;
        errorMessage["0"][key] = error.message;
    }

    //一意のキーの値を取り出す
    const param = error.data.map(function(result) {
        const params = result.parameter;
        return params[target];
    });

    const errorHtml = [];

    let newRowNum;
    let editRowNum;
    const auto_input = '<span class="tBodyAutoInput"></span>';

    for ( const item in errorMessage ) {
        newRowNum = parseInt(item);
        for ( const error in errorMessage[item] ) {
            const name = fn.cv( tb.data.restNames[ error ], error, true );
            let   body = fn.cv( errorMessage[item][error].join(''), '?', true );

            if ( fn.typeof( body ) === 'string') body = body.replace(/\r?\n/g, '<br>');

            // 編集項目か否か
            if(param[item] != null) {
                editRowNum = param[item];
                errorHtml.push(`<tr class="tBodyTr tr">`
                    + fn.html.cell( auto_input, ['tBodyTh', 'tBodyLeftSticky'], 'th')
                    + fn.html.cell( editRowNum, ['tBodyTh', 'tBodyErrorId'], 'th')
                    + fn.html.cell( name, 'tBodyTh', 'th')
                    + fn.html.cell( body, 'tBodyTd')
                + `</tr>`);
            }else{
                editRowNum = '<span class="tBodyAutoInput"></span>';
                errorHtml.push(`<tr class="tBodyTr tr">`
                    + fn.html.cell( newRowNum + 1, ['tBodyTh', 'tBodyLeftSticky'], 'th')
                    + fn.html.cell( editRowNum, ['tBodyTh', 'tBodyErrorId'], 'th')
                    + fn.html.cell( name, 'tBodyTh', 'th')
                    + fn.html.cell( body, 'tBodyTd')
                + `</tr>`);
            }
        }
    }

    tb.$.container.addClass('tableError');
    tb.$.errorMessage.html(`
    <div class="errorBorder"></div>
    <div class="errorTableContainer">
        <div class="errorTitle"><span class="errorTitleInner">${fn.html.icon('circle_exclamation')}` + getMessage.FTE00065 + `</span></div>
        <table class="table errorTable">
            <thead class="thead">
                <tr class="tHeadTr tr">
                <th class="tHeadTh tHeadLeftSticky th"><div class="ci">${getMessage.FTE00069}</div></th>
                <th class="tHeadTh tHeadLeftSticky th"><div class="ci">${id_name}</div></th>
                <th class="tHeadTh th tHeadErrorColumn"><div class="ci">${getMessage.FTE00070}</div></th>
                <th class="tHeadTh th tHeadErrorBody"><div class="ci">${getMessage.FTE00071}</div></th>
                </tr>
            </thead>
            <tbody class="tbody">
                ${errorHtml.join('')}
            </tbody>
        </table>
    </div>`);
}

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Table setting
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
   テーブル設定初期値
##################################################
*/
initTableSettingValue() {
    const tb = this;

    tb.tableSettingInitValue = {
        individual: {
            check: {
                direction: 'common',
                filter: 'common',
                menu: 'common',
                color: 'common'
            },
            color: {
                color_any_bd: '#A3A4A4',
                color_any_bg: '#FFFFFF',
                color_any_tx: '#000000',
                color_req_bd: '#C80000',
                color_req_bg: '#F4CCCC',
                color_req_tx: '#000000',
                color_typ_bd: '#0070FF',
                color_typ_bg: '#E5F1FF',
                color_typ_tx: '#000000',
                color_don_bd: '#60C60D',
                color_don_bg: '#DFF4CF',
                color_don_tx: '#000000'
            }
        },
        general: {
            check: {
                direction: 'vertical',
                filter: 'in',
                menu: 'hide',
                color: 'default'
            },
            color: {
                color_any_bd: '#A3A4A4',
                color_any_bg: '#FFFFFF',
                color_any_tx: '#000000',
                color_req_bd: '#C80000',
                color_req_bg: '#F4CCCC',
                color_req_tx: '#000000',
                color_typ_bd: '#0070FF',
                color_typ_bg: '#E5F1FF',
                color_typ_tx: '#000000',
                color_don_bd: '#60C60D',
                color_don_bg: '#DFF4CF',
                color_don_tx: '#000000'
            }
        }
    };
}
/*
##################################################
   テーブル設定値をセット
##################################################
*/
setTableSettingValue() {
    const tb = this;

    const restUser = fn.storage.get('restUser', 'session'),
          tableSetting = ( restUser.web_table_settings && restUser.web_table_settings.table )? restUser.web_table_settings.table: {};

    const general = fn.cv( tableSetting.general, {}),
          individual = ( tableSetting.individual && tableSetting.individual[ tb.params.menuNameRest ] && tableSetting.individual[ tb.params.menuNameRest ][ tb.id ] )?
              tableSetting.individual[ tb.params.menuNameRest ][ tb.id ]: {};

    // 値をセット
    if ( !tb.tableSetting ) tb.tableSetting = {};
    tb.tableSetting = {
        individual: individual,
        general: general
    };
}
/*
##################################################
   テーブル設定値チェック
##################################################
*/
checkTableSettingValue() {
    const tb = this;

    const data = tb.tableSetting;

    if ( !data.individual[ tb.tableMode ] ) data.individual[ tb.tableMode ] = {};
    if ( !data.individual[ tb.tableMode ].check ) data.individual[ tb.tableMode ].check = {};
    if ( !data.individual[ tb.tableMode ].color ) data.individual[ tb.tableMode ].color = {};
    if ( !data.individual[ tb.tableMode ].hideItem ) data.individual[ tb.tableMode ].hideItem = [];

    if ( !data.general[ tb.tableMode ] ) data.general[ tb.tableMode ] = {};
    if ( !data.general[ tb.tableMode ].check ) data.general[ tb.tableMode ].check = {};
    if ( !data.general[ tb.tableMode ].color ) data.general[ tb.tableMode ].color = {};
}
/*
##################################################
   テーブル設定取得
##################################################
*/
getTableSettingValue( key ) {
    const tb = this;

    const data = tb.tableSetting;
    tb.checkTableSettingValue();

    // 個別か共通か
    if ( key !== 'color' && key !== 'hideItem') {
        if ( !data.individual[ tb.tableMode ].check[ key ] || data.individual[ tb.tableMode ].check[ key ] === 'common') {
            return data.general[ tb.tableMode ].check[ key ];
        } else {
            return data.individual[ tb.tableMode ].check[ key ];
        }
    } else if( key === 'hideItem') {
        if ( data.individual[ tb.tableMode ].hideItem ) {
            return data.individual[ tb.tableMode ].hideItem;
        } else {
            return [];
        }
    } else {
        if ( data.individual[ tb.tableMode ].check.color === 'custom') {
             return data.individual[ tb.tableMode ].color;
        } else if ( data.general[ tb.tableMode ].check.color === 'custom') {
            return data.general[ tb.tableMode ].color;
        } else {
            return null;
        }
    }
}
/*
##################################################
   テーブル設定初期値取得
##################################################
*/
getTableSettingInitValue( target, type, key ) {
    const tb = this;

    return ( tb.tableSetting[ target ][ tb.tableMode ][ type ] && tb.tableSetting[ target ][ tb.tableMode ][ type ][ key ] )?
        tb.tableSetting[ target ][ tb.tableMode ][ type ][ key ]:
        tb.tableSettingInitValue[ target ][ type ][ key ];
}
/*
##################################################
   テーブル設定適用
##################################################
*/
tableSettingOk() {
    const tb = this;

    // 値をセット
    const settingData = tb.tableSetting,
          $dBody = tb.tableSettingModal[ tb.tableMode ].$.dbody;

    for ( const target in tb.tableSettingInitValue ) {
        for ( const type in tb.tableSettingInitValue[ target ] ) {
            for ( const key in tb.tableSettingInitValue[ target ][ type ] ) {
                const $input = $dBody.find(`.${target}TabBody`).find(`.ts_${key}`);
                if ( !$input.length ) continue;

                switch ( type ) {
                    case 'check':
                        settingData[ target ][ tb.tableMode ][ type ][ key ] = $input.filter(':checked').val();
                    break;
                    case 'color':
                        settingData[ target ][ tb.tableMode ][ type ][ key ] = $input.val();
                    break;
                }
            }
        }
    }

    // 表示・非表示
    const $check = tb.tableSettingModal[ tb.tableMode ].$.dbody.find('.tableSettingCheck').not(':checked'),
          unCheckList = [];
    $check.each(function(){
        unCheckList.push( $( this ).val() );
    });
    settingData.individual[ tb.tableMode ].hideItem = unCheckList;

    tb.saveTableSetting();
}
/*
##################################################
   テーブル設定更新 ＞ 再表示
##################################################
*/
saveTableSetting() {
    const tb = this;

    const settingData = tb.tableSetting;

    const sessionUserData = fn.storage.get('restUser', 'session');
    if ( sessionUserData ) {
        const process = fn.processingModal(),
              set = fn.cv( sessionUserData.web_table_settings, {} );

        if ( !set.table ) set.table = {};

        // 全般
        if ( !set.table.general ) set.table.general = {};
        set.table.general[ tb.tableMode ] = settingData.general[ tb.tableMode ];

        // 共通
        if ( !set.table.individual ) set.table.individual = {};
        if ( !set.table.individual[ tb.params.menuNameRest ] ) set.table.individual[ tb.params.menuNameRest ] = {};
        if ( !set.table.individual[ tb.params.menuNameRest ][ tb.id ] ) set.table.individual[ tb.params.menuNameRest ][ tb.id ] = {};
        set.table.individual[ tb.params.menuNameRest ][ tb.id ][ tb.tableMode ]  = settingData.individual[ tb.tableMode ];

        fn.fetch('/user/table_settings/', null, 'POST', set ).then(function(){
            tb.resetTable();
        }).catch(function(){
            fn.alert( getMessage.FTE10092, getMessage.FTE10093 );
        }).then(function(){
            process.close();
        });
    } else {
        // session storageの取得に失敗した場合はエラー
        fn.alert( getMessage.FTE10092, getMessage.FTE10093 );
    }
}
/*
##################################################
   テーブル設定モーダルを開く
##################################################
*/
tableSettingOpen() {
    const tb = this;

    if ( !tb.tableSettingModal ) tb.tableSettingModal = {};

    if ( tb.tableSettingModal[ tb.tableMode ] ) {
        tb.tableSettingModal[ tb.tableMode ].show();
    } else {
        // モーダル表示
        const config = {
            mode: 'modeless',
            position: 'top',
            width: '640px',
            header: {
                title: getMessage.FTE00086,
            },
            footer: {
                button: {
                    ok: { text: getMessage.FTE00087, action: 'default', /*className: 'dialogPositive'*/},
                    cancel: { text: getMessage.FTE00088, action: 'normal'},
                    reset: { text: getMessage.FTE00089, action: 'danger', separate: true }
                }
            }
        };

        // モーダルOK、キャンセル
        const funcs = {
            ok: function() {
                tb.tableSettingOk();
                tb.tableSettingModal[ tb.tableMode ].hide();
            },
            cancel: function() {
                tb.tableSettingModal[ tb.tableMode ].hide();
            },
            reset: function() {
                tb.tableSettingReset();
                tb.tableSettingModal[ tb.tableMode ].close();
                tb.tableSettingModal[ tb.tableMode ] = null;
            }
        };
        const checkStatus = function( target, key, value ) {
            const attr = {};

            if ( key === 'filter') {
                const direction = tb.getTableSettingInitValue( target, 'check', 'direction');
                if ( direction === 'horizontal') {
                    attr.disabled = 'disabled'
                }
            }

            if ( value === tb.getTableSettingInitValue( target, 'check', key ) ) {
                attr.checked = 'checked';
            }

            return attr;
        };

        const tableSettingHtml = function( id, target ) {
            let tableSettingHtml = ``
            + `<div class="commonSection ${target}TabBody">`
                + `<div class="commonTitle">${getMessage.FTE00090}</div>`
                + `<div class="commonBody">`
                    + `<p class="commonParagraph">`
                        + getMessage.FTE00101
                    + `</p>`
                    + `<ul class="commonRadioList">`
                        + `${( target === 'individual')?
                            `<li class="commonRadioItem">${fn.html.radioText('ts_direction', 'common', id + 'tableDirection', id + 'tableDirectionCommon', checkStatus( target, 'direction', 'common'), getMessage.FTE00105 )}</li>`: ``}`
                        + `<li class="commonRadioItem">${fn.html.radioText('ts_direction', 'vertical', id + 'tableDirection', id + 'tableDirectionVertical', checkStatus( target, 'direction', 'vertical'), getMessage.FTE00091 )}</li>`
                        + `<li class="commonRadioItem">${fn.html.radioText('ts_direction', 'horizontal', id + 'tableDirection', id + 'tableDirectionHorizontal', checkStatus( target, 'direction', 'horizontal'), getMessage.FTE00092 )}</li>`
                    + `</ul>`
                + `</div>`;

            if ( tb.mode === 'view' || tb.mode === 'select' || tb.mode === 'execute') {
                tableSettingHtml += ``
                + `<div class="commonTitle">${getMessage.FTE00094}</div>`
                + `<div class="commonBody">`
                    + `<p class="commonParagraph">`
                        + getMessage.FTE00102
                    + `</p>`
                    + `<ul class="commonRadioList">`
                        + `${( target === 'individual')?
                            `<li class="commonRadioItem">${fn.html.radioText('ts_filter', 'common', id + 'tableFilterPosition', id + 'tableFilterPositionCommon', checkStatus( target, 'filter', 'common'), getMessage.FTE00105 )}</li>`: ``}`
                        + `<li class="commonRadioItem">${fn.html.radioText('ts_filter', 'in', id + 'tableFilterPosition', id + 'tableFilterPositionIn', checkStatus( target, 'filter', 'in'), getMessage.FTE00095 )}</li>`
                        + `<li class="commonRadioItem">${fn.html.radioText('ts_filter', 'out', id + 'tableFilterPosition', id + 'tableFilterPositionOut', checkStatus( target, 'filter', 'out'), getMessage.FTE00096 )}</li>`
                    + `</ul>`
                + `</div>`
                + `<div class="commonTitle">${getMessage.FTE00097}</div>`
                + `<div class="commonBody">`
                    + `<p class="commonParagraph">`
                        + getMessage.FTE00103
                    + `</p>`
                    + `<ul class="commonRadioList">`
                        + `${( target === 'individual')?
                            `<li class="commonRadioItem">${fn.html.radioText('ts_menu', 'common', id + 'tableItemMenu', id + 'tableItemMenuCommon', checkStatus( target, 'menu', 'common'), getMessage.FTE00105 )}</li>`: ``}`
                        + `<li class="commonRadioItem">${fn.html.radioText('ts_menu', 'hide', id + 'tableItemMenu', id + 'tableItemMenuHide', checkStatus( target, 'menu', 'hide'), getMessage.FTE00098 )}</li>`
                        + `<li class="commonRadioItem">${fn.html.radioText('ts_menu', 'show', id + 'tableItemMenu', id + 'tableItemMenuShow', checkStatus( target, 'menu', 'show'), getMessage.FTE00099 )}</li>`
                    + `</ul>`
                + `</div>`;
            }

            if ( tb.mode === 'edit') {
                const colorTable = ( tb.getTableSettingInitValue( target, 'check', 'color') === 'custom')? ' colorOpen': '';
                tableSettingHtml += ``
                    + `<div class="commonTitle">${getMessage.FTE00109}</div>`
                    + `<div class="commonBody">`
                        + `<p class="commonParagraph">`
                            + getMessage.FTE00110
                        + `</p>`
                        + `<ul class="commonRadioList">`
                            + `${( target === 'individual')?
                                `<li class="commonRadioItem">${fn.html.radioText('ts_color', 'common', id + 'tableItemMenu', id + 'tableColorCommon', checkStatus( target, 'color', 'common'), getMessage.FTE00105 )}</li>`: ``}`
                            + `<li class="commonRadioItem">${fn.html.radioText('ts_color', 'default', id + 'tableItemMenu', id + 'tableColorDefault', checkStatus( target, 'color', 'default'), getMessage.FTE00106 )}</li>`
                            + `<li class="commonRadioItem">${fn.html.radioText('ts_color', 'custom', id + 'tableItemMenu', id + 'tableColorCustom', checkStatus( target, 'color', 'custom'), getMessage.FTE00107 )}</li>`
                        + `</ul>`
                        + `<div class="commonInputGroup tableInputColorTable${colorTable}">`
                            + `<table class="commonInputTable">`
                                + `<tbody class="commonInputTbody">`
                                    + `<tr class="commonInputTr">`
                                        + `<th class="commonInputTh"><div class="commonInputTitle">${getMessage.FTE00111}</div></th>`
                                        + `<td class="commonInputTd">${fn.html.inputColor('ts_colorInput ts_color_any_bd', tb.getTableSettingInitValue( target, 'color', 'color_any_bd'), 'tableInputColor', {}, { before: getMessage.FTE00115 })}</td>`
                                        + `<td class="commonInputTd">${fn.html.inputColor('ts_colorInput ts_color_any_bg', tb.getTableSettingInitValue( target, 'color', 'color_any_bg'), 'tableInputColor', {}, { before: getMessage.FTE00116 })}</td>`
                                        + `<td class="commonInputTd">${fn.html.inputColor('ts_colorInput ts_color_any_tx', tb.getTableSettingInitValue( target, 'color', 'color_any_tx'), 'tableInputColor', {}, { before: getMessage.FTE00117 })}</td>`
                                    + `</tr>`
                                    + `<tr class="commonInputTr">`
                                        + `<th class="commonInputTh"><div class="commonInputTitle">${getMessage.FTE00112}</div></th>`
                                        + `<td class="commonInputTd">${fn.html.inputColor('ts_colorInput ts_color_req_bd', tb.getTableSettingInitValue( target, 'color', 'color_req_bd'), 'tableInputColor', {}, { before: getMessage.FTE00115 })}</td>`
                                        + `<td class="commonInputTd">${fn.html.inputColor('ts_colorInput ts_color_req_bg', tb.getTableSettingInitValue( target, 'color', 'color_req_bg'), 'tableInputColor', {}, { before: getMessage.FTE00116 })}</td>`
                                        + `<td class="commonInputTd">${fn.html.inputColor('ts_colorInput ts_color_req_tx', tb.getTableSettingInitValue( target, 'color', 'color_req_tx'), 'tableInputColor', {}, { before: getMessage.FTE00117 })}</td>`
                                    + `</tr>`
                                    + `<tr class="commonInputTr">`
                                        + `<th class="commonInputTh"><div class="commonInputTitle">${getMessage.FTE00113}</div></th>`
                                        + `<td class="commonInputTd">${fn.html.inputColor('ts_colorInput ts_color_typ_bd', tb.getTableSettingInitValue( target, 'color', 'color_typ_bd'), 'tableInputColor', {}, { before: getMessage.FTE00115 })}</td>`
                                        + `<td class="commonInputTd">${fn.html.inputColor('ts_colorInput ts_color_typ_bg', tb.getTableSettingInitValue( target, 'color', 'color_typ_bg'), 'tableInputColor', {}, { before: getMessage.FTE00116 })}</td>`
                                        + `<td class="commonInputTd">${fn.html.inputColor('ts_colorInput ts_color_typ_tx', tb.getTableSettingInitValue( target, 'color', 'color_typ_tx'), 'tableInputColor', {}, { before: getMessage.FTE00117 })}</td>`
                                    + `</tr>`
                                    + `<tr class="commonInputTr">`
                                        + `<th class="commonInputTh"><div class="commonInputTitle">${getMessage.FTE00114}</div></th>`
                                        + `<td class="commonInputTd">${fn.html.inputColor('ts_colorInput ts_color_don_bd', tb.getTableSettingInitValue( target, 'color', 'color_don_bd'), 'tableInputColor', {}, { before: getMessage.FTE00115 })}</td>`
                                        + `<td class="commonInputTd">${fn.html.inputColor('ts_colorInput ts_color_don_bg', tb.getTableSettingInitValue( target, 'color', 'color_don_bg'), 'tableInputColor', {}, { before: getMessage.FTE00116 })}</td>`
                                        + `<td class="commonInputTd">${fn.html.inputColor('ts_colorInput ts_color_don_tx', tb.getTableSettingInitValue( target, 'color', 'color_don_tx'), 'tableInputColor', {}, { before: getMessage.FTE00117 })}</td>`
                                    + `</tr>`
                                + `</tbody>`
                            + `</table>`
                        + `</div>`
                    + `</div>`;
            }

            if ( target === 'individual') {
                tableSettingHtml += ``
                    + `<div class="commonTitle">${getMessage.FTE00100}</div>`
                    + `<div class="commonBody">`
                        + `<p class="commonParagraph">`
                            + getMessage.FTE00104
                        + `</p>`
                        + tb.tableSettingListHtml()
                    + `</div>`;
            }
            tableSettingHtml += `</div>`;

            return tableSettingHtml;
        };

        const html = ``
        + `<div class="commonTab">`
            + `<div class="commonTabMenu">`
                + `<ul class="commonTabList">`
                    + `<li class="commonTabItem">${getMessage.FTE00108}</li>`
                    + `<li class="commonTabItem">${getMessage.FTE00105}</li>`
                + `</ul>`
            + `</div>`
            + `<div class="commonTabBody">`
                + `<div class="commonTabSection commonScroll">`
                    + tableSettingHtml(`individual_${tb.id}_${tb.tableMode}`, 'individual')
                + `</div>`
                + `<div class="commonTabSection commonScroll">`
                    + tableSettingHtml(`general_${tb.id}_${tb.tableMode}`, 'general')
                + `</div>`
            + `</div>`
        + `<div>`;

        tb.tableSettingModal[ tb.tableMode ] = new Dialog( config, funcs );
        tb.tableSettingModal[ tb.tableMode ].open( html );

        tb.tableSettingEvents();
        fn.commonTab( tb.tableSettingModal[ tb.tableMode ].$.dbody.find(`.commonTab`) );
    }
}
/*
##################################################
   テーブル設定リセット
##################################################
*/
tableSettingReset() {
    const tb = this;

    tb.tableSetting.individual[ tb.tableMode ] = {
        check: {},
        color: {}
    };

    tb.saveTableSetting();
}
/*
##################################################
   項目一覧HTML
##################################################
*/
tableSettingListHtml() {
    const tb = this;

    const id = tb.id + '_' + tb.tableMode;

    let html = '';
    const tableSettingList = function( list, className ) {
        for ( const key of list ) {
            const type = key.slice( 0, 1 ),
                  attr = ( tb.tableSetting.individual[ tb.tableMode ].hideItem && tb.tableSetting.individual[ tb.tableMode ].hideItem.indexOf( key ) !== -1 )? {}: {checked: 'checked'};

            html += `<li class="${className}">`;
            if ( type === 'c') {
                const data = tb.info.column_info[ key ];

                // 表示しない項目
                const exclusion = ['discard'];

                let text = data.column_name;
                if ( tb.mode === 'edit') {
                    const noRequiredMark = [ tb.idNameRest, 'last_update_date_time', 'last_updated_user'];
                    if ( data.required_item === '1' && noRequiredMark.indexOf( data.column_name_rest ) === -1 ) {
                        text += fn.html.required();
                        attr.disabled = 'disabled';
                    }
                    if ( data.input_item === '3') {
                        attr.disabled = 'disabled';
                    }
                }

                if ( exclusion.indexOf( data.column_name_rest ) === -1 ) {
                    html += `<div class="tableSettingItemName">`
                    + fn.html.checkboxText('tableSettingCheck tableSettingCheckItem', key, id + '_itemSelect', id + '_' + data.column_name_rest, attr, text )
                    + `</div>`;
                }
            } else {
                const data = tb.info.column_group_info[ key ];
                html += `<div class="tableSettingItemName tableSettingGroupName">`
                + fn.html.checkboxText('tableSettingCheck tableSettingCheckGroup', key, id + '_groupSelect', id + '_' + data.column_group_id, attr, data.column_group_name )
                + `</div>`
                + `<ul class="tableSettingList">`;
                tableSettingList( data['columns_' + tb.tableMode ], 'tableSettingItem tableSettingItemChild');
                html += `</ul>`;
            }
            html += `</li>`;
        }
    };
    tableSettingList( tb.info.menu_info['columns_' + tb.tableMode ], 'tableSettingItem');

    return `<ul class="tableSettingList">${html}</ul>`;
}

/*
##################################################
   テーブル設定モーダルイベント
##################################################
*/
tableSettingEvents() {
    const tb = this;

    const $dBody = tb.tableSettingModal[ tb.tableMode ].$.dbody;

    if ( tb.mode === 'view' || tb.mode === 'select' || tb.mode === 'execute') {
        // フィルタ表示位置
        $dBody.find('.ts_direction').on('change', function() {
            const $check = $( this ),
                  check = $check.val();
            $check.closest('.commonSection').find('.ts_filter').prop('disabled', ( check === 'horizontal') );
        });
    }

    if ( tb.mode === 'edit') {
        // 入力欄色設定
        $dBody.find('.ts_color').on('change', function() {
            const $check = $( this ),
                  value = $check.val();
            if ( value === 'custom') {
                $check.closest('.commonSection').find('.tableInputColorTable').addClass('colorOpen');
            } else {
                $check.closest('.commonSection').find('.tableInputColorTable').removeClass('colorOpen');
            }
        });
    }

    // 親兄弟子要素の状態をチェック
    const parentCheck = function( $check ) {

        // 兄弟要素のチェック
        const $checks = $check.closest('.tableSettingList').children('.tableSettingItem').children('.tableSettingItemName').find('.tableSettingCheck'),
              checkLength = $checks.length;

        let checkNum = 0, oneOrMoreNum = 0;
        $checks.each(function(){
            const $eachCheck = $( this );
            if ( $eachCheck.prop('checked') ) checkNum++;
            if ( $eachCheck.closest('.checkboxTextWrap').is('.checkboxTextOneOrMore') ) oneOrMoreNum++;
        });

        // 親要素のチェック
        const $parentCheckWrap = $check.closest('.tableSettingList').prev('.tableSettingItemName').find('.checkboxTextWrap'),
              $parentCheck = $parentCheckWrap.find('.tableSettingCheck').not(':disabled');

        $parentCheckWrap.removeClass('checkboxTextOneOrMore');
        if ( $parentCheck.length ) {
            if ( checkLength === checkNum && oneOrMoreNum === 0 ) {
                $parentCheck.prop('checked', true );
            } else if ( checkNum > 0 ) {
                $parentCheck.prop('checked', true );
                $parentCheckWrap.addClass('checkboxTextOneOrMore');
            } else {
                $parentCheck.prop('checked', false );
            }
            parentCheck( $parentCheck );
        }

    };
    $dBody.find('.tableSettingCheck').on('change', function() {

        const $check = $( this );

        // 子要素のチェックを全て変更する
        if ( $check.is('.tableSettingCheckGroup') ) {
            const $wrap = $check.closest('.checkboxTextWrap'),
                $parent = $check.closest('.tableSettingItemName').next('.tableSettingList'),
                $checks = $parent.find('.tableSettingCheck').not(':disabled');

            let   checked = $check.prop('checked');

            if ( $wrap.is('.checkboxTextOneOrMore') && !$checks.not('.tableSettingCheckGroup').filter(':checked').length ) {
                checked = true;
                $([ $check, $checks ]).prop('checked', checked );
            } else {
                $checks.prop('checked', checked );
            }

            $([ $wrap, $parent.find('.checkboxTextOneOrMore') ]).removeClass('checkboxTextOneOrMore');

            if ( !checked ) {
                // グループのチェック状態を確認
                $([ $wrap, $parent.find('.checkboxTextWrap') ]).find('.tableSettingCheckGroup').each(function(){
                    const $checkGroup = $( this ),
                        $checked = $checkGroup.closest('.tableSettingItemName').next('.tableSettingList').find('.tableSettingCheckItem:checked');

                    if ( $checked.length ) {
                        $checkGroup.prop('checked', true ).closest('.checkboxTextWrap').addClass('checkboxTextOneOrMore');
                    }
                });
            }
        }

        // 親要素のチェック
        parentCheck( $check );

    });
}
/*
##################################################
   テーブル設定カスタムCSS
##################################################
*/
tableSettingCustomCSS() {
    const tb = this;

    let style = '';

    // 入力欄色設定
    const color = tb.getTableSettingValue('color');

    if ( color ) {
        style += ``
        + `#${tb.id} .tbody .input,`
        + `#${tb.id} .noSelect,`
        + `#${tb.id} .tableEditInputSelectValue,`
        + `#${tb.id} .select2-container--default .select2-selection--single,`
        + `#${tb.id} .tbody .tableEditSelectFile{background-color:${color.color_any_bg};border-color:${color.color_any_bd};color:${color.color_any_tx}}`
        + `#${tb.id} .input.tableEditRequiredError{background-color:${color.color_req_bg};border-color:${color.color_req_bd};color:${color.color_req_tx}}`
        + `#${tb.id} .input.tableEditChange,`
        + `#${tb.id} .tableEditSelectFile.tableEditChange,`
        + `#${tb.id} .tableEditInputSelectContainer.tableEditChange .tableEditInputSelectValue,`
        + `#${tb.id} .tableEditInputSelectContainer.tableEditChange .select2-selection{background-color:${color.color_don_bg};border-color:${color.color_don_bd};color:${color.color_don_tx}}`
        + `#${tb.id} .input:focus{background-color:${color.color_typ_bg};border-color:${color.color_typ_bd};color:${color.color_typ_tx}}`;
        return style;
    } else {
        return '';
    }
}
/*
##################################################
   アクションボタンモーダル
##################################################
*/
actionModalOpen( type, itemId, text ) {
    const tb = this;

    return new Promise(function( resolve ){
        switch( type ){
            case 'schedule_regulary':
                tb.scheduleSettingOpen( itemId, text ).then( function(){
                    resolve();
                });
            break;
        }
    });
}
/*
##################################################
   REST API
##################################################
*/
restApi( buttonText, method, endpoint, body, option = {}) {
    return new Promise(function( resolve ){
        const text = getMessage.FTE00119( buttonText );

        fn.alert(`${buttonText}${getMessage.FTE00118}`, text, 'confiarm', {
            ok: { text: getMessage.FTE00122, action: 'default', style: 'width:160px', className: 'dialogPositive'},
            cancel: { text: getMessage.FTE00123, action: 'negative', style: 'width:120px'}
        }, '400px').then( function( flag ){
            if ( flag ) {
                let process = fn.processingModal( getMessage.FTE00120 );
                fn.fetch( endpoint, null, method, body, { message: true } ).then(function( result ){
                    if ( option.redirect ) {
                        if ( fn.typeof( result ) === 'array') {
                            const value = result[0][ option['redirect_key'] ];
                            if ( value ) {
                                window.location.href = `?${option.redirect + value}`;
                            }
                        }
                    } else {
                        const message = ( fn.typeof( result ) === 'array')? result[1]: result;
                        fn.alert( getMessage.FTE00121, message );
                    }
                }).catch(function( error ){
                    const errorMessage = ( error.message )? error.message: 'Error!';
                    fn.alert( getMessage.FTE00121, errorMessage );
                }).then(function(){
                    process.close();
                    process = null;
                    resolve();
                });
            } else {
                resolve();
            }
        });
    });
}

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   個別対応
//
////////////////////////////////////////////////////////////////////////////////////////////////////

/*
##################################################
   Conductor定期作業実行 スケジュール設定
##################################################
*/
scheduleSettingData() {
    return {
        input: ['start_date', 'end_date', 'period', 'interval', 'week_number', 'day_of_week', 'day', 'time', 'execution_stop_start_date', 'execution_stop_end_date', 'remarks'],
        period: {
            period_1: getMessage.FTE00126,
            period_2: getMessage.FTE00127,
            period_3: getMessage.FTE00128,
            period_4: getMessage.FTE00129,
            period_5: getMessage.FTE00130,
            period_6: getMessage.FTE00131,
        },
        schedule: {
            scheduleIntervalHourInput: [ getMessage.FTE00132, 1, 99, getMessage.FTE00133, 1, 'period_1', 'interval'],
            scheduleIntervalDayInput: [ getMessage.FTE00132, 1, 99, getMessage.FTE00134, 1, 'period_2', 'interval'],
            scheduleIntervalWeekInput: [ getMessage.FTE00132,  1, 99, getMessage.FTE00135, 1, 'period_3', 'interval'],
            scheduleIntervalMonthInput: [ getMessage.FTE00132, 1, 99, getMessage.FTE00136, 1 ,'period_4 period_5 period_6', 'interval'],
            scheduleDayInput: [ getMessage.FTE00137, 1, 31, getMessage.FTE00138, 1, 'period_4', 'day'],
            scheduleDayWeekInput: [ getMessage.FTE00139, 0, 0, null, 0, 'period_3', 'day_of_week'],
            scheduleMonthDayWeekInput: [ getMessage.FTE00139, 0, 0, null, 0, 'period_5', 'week_number'],
            scheduleHourInput: [ getMessage.FTE00140, 0, 23, getMessage.FTE00140, 0, 'period_T', 'time'],
            scheduleMinutesInput: [ getMessage.FTE00141, 0, 59, getMessage.FTE00141, 0, 'period_T', 'time_minutes'],
            scheduleSecondsInput: [ getMessage.FTE00165, 0, 59, getMessage.FTE00165, 0, 'period_T', 'time_seconds'],
        }
    };
}
scheduleSettingOpen( itemId, buttonText ) {
    const tb = this;

    return new Promise(function( resolve ){

        // モーダル function
        const funcs = {
            ok: function(){
                setSchedule();
                closeFunc();
            },
            cancel: function(){
                closeFunc();
            }
        };

        // モーダル設定
        const config = {
            mode: 'modeless',
            position: 'top',
            header: {
                title: buttonText
            },
            width: '640px',
            footer: {
                button: {
                    ok: { text: getMessage.FTE00143, action: 'default', width: '160px', className: 'dialogPositive'},
                    cancel: { text: getMessage.FTE00144, action: 'normal'}
                }
            }
        };

        // スケジュールデータ
        const data = tb.scheduleSettingData();

        // モーダルを閉じる
        const closeFunc = function() {
            modal.close();
            modal = null;
            resolve();
        };

        // 初期値を取得
        const initScheduleValue = {};
        for ( const key of data.input ) {
            const $target = tb.$.tbody.find(`.tableEditInputHidden[data-id="${itemId}"][data-key="${key}"]`),
                  value = $target.val();
            initScheduleValue[ key ] = value;
        }

        // モーダルで設定したスケジュールをセットする
        const setSchedule = function() {
            for ( const key of data.input ) {
                const $target = tb.$.tbody.find(`.tableEditInputHidden[data-id="${itemId}"][data-key="${key}"]`),
                      before = $target.val();

                let after = '';
                if ( key === 'period') {
                    after = $mbody.find(`.schedulePeriodType:checked`).val();
                } else if ( key === 'time') {
                    const h = $mbody.find(`.input[data-key="${key}"]:visible`).val(),
                          m = $mbody.find(`.input[data-key="${key}_minutes"]:visible`).val(),
                          s = $mbody.find(`.input[data-key="${key}_seconds"]:visible`).val();
                    if ( h && m && s ) {
                        after = `${fn.zeroPadding(h,2)}:${fn.zeroPadding(m,2)}:${fn.zeroPadding(s,2)}`;
                    }
                } else {
                    after = $mbody.find(`.input[data-key="${key}"]:visible`).val();
                }
                after = fn.cv( after, '');
                if ( before !== after ) {
                    $target.val( after ).change();
                }
            }
        };

        // 曜日選択
        const weekSelect = function( type, key ) {
            const week = ( type === 'num')? getMessage.FTE00124: getMessage.FTE00125,
                  weekHtml = [];
            for ( const val of week ) {
                if ( val === initScheduleValue[ key ] ) {
                    weekHtml.push(`<option value="${val}" selected>${val}</option>`)
                } else {
                    weekHtml.push(`<option value="${val}">${val}</option>`)
                }
            }
            return `<select class="scheduleSelect input" data-key="${key}">${weekHtml.join('')}</select>`;
        };

        // スケジュール欄個別HTML
        const schedulePeriodItemHtml = function( type, item ) {
            switch( type ) {
                case 'scheduleDayWeekInput':
                    return weekSelect('day', 'day_of_week');
                case 'scheduleMonthDayWeekInput':
                    return weekSelect('num', 'week_number') + '&nbsp;' +  weekSelect('day', 'day_of_week');
                default:
                    return fn.html.inputFader('schedulePeriodInput', item[4], item[1], { min: item[1], max: item[2], key: item[6] }, { after: item[3] });
            }
        };

        // 周期選択
        let selectPeriod = '';
        if ( !initScheduleValue.period ) {
            initScheduleValue.period = data.period.period_1;
            selectPeriod = 'period_1';
        }
        const schedulePeriodRadio = function() {
            const list = [];
            for ( const key in data.period ) {
                const attr = { type: key };
                if ( initScheduleValue.period === data.period[key] ){
                    attr.checked = 'checked';
                    selectPeriod = key;
                }
                const id = itemId + '_schedulePeriodType',
                      html = `<li class="commonRadioItem schedulePeriodRadioItem">`
                    + fn.html.radioText('schedulePeriodType', data.period[key], id, id + key, attr, data.period[key] )
                + `</li>`;
                list.push( html );
            }
            return list.join('');
        };

        // スケジュール欄
        const feaderList = function() {
            let html = '';
            for ( const type in data.schedule ) {
                const sc = data.schedule[type];
                // 初期値を設定
                if ( sc[6] === 'interval' && initScheduleValue.interval ) {
                    if ( sc[5].indexOf( selectPeriod ) !== -1 ) {
                        sc[4] = initScheduleValue.interval;
                    }
                } else if ( sc[6] === 'time' && initScheduleValue.time ) {
                    sc[4] = Number( fn.cv( initScheduleValue.time.split(':')[0], 0 ) );
                } else if ( sc[6] === 'time_minutes' && initScheduleValue.time ) {
                    sc[4] = Number( fn.cv( initScheduleValue.time.split(':')[1], 0 ) );
                } else if ( sc[6] === 'time_seconds' && initScheduleValue.time ) {
                    sc[4] = Number( fn.cv( initScheduleValue.time.split(':')[2], 0 ) );
                } else {
                    if ( initScheduleValue[ sc[6] ] ) {
                        sc[4] = initScheduleValue[ sc[6] ];
                    }
                }
                html += ``
                + `<tr class="commonInputTr schedulePeriodDetailTr ${sc[5]}">`
                    + `<th class="commonInputTh"><div class="commonInputTitle">${sc[0]}</div></th>`
                    + `<td class="commonInputTd">${schedulePeriodItemHtml( type, sc )}</td>`
                + `</tr>`;
            }
            return html;
        };

        // モーダルHTML
        const html = ``
        + `<div class="commonSection">`
            + `<div class="commonTitle">${getMessage.FTE00145}</div>`
            + `<div class="commonBody scheduleInputFromToDate">`
                + `<div class="commonInputGroup">`
                    + `<table class="commonInputTable">`
                        + `<tbody class="commonInputTbody">`
                            + `<tr class="commonInputTr">`
                                + `<th class="commonInputTh"><div class="commonInputTitle">${getMessage.FTE00146}${fn.html.required()}</div></th>`
                                + `<td class="commonInputTd">`
                                    + `<div class="scheduleInputFromDateWrap">`
                                        + fn.html.inputText(['scheduleInput', 'scheduleFromDate'], fn.cv( initScheduleValue.start_date, ''), 'start_date_' + itemId, { placeholder: 'yyyy/MM/dd HH:mm:ss', type: 'fromDate', key: 'start_date'})
                                    + `</div>`
                                + `</td>`
                                + `<td class="commonInputTd">${getMessage.FTE00148}</td>`
                                + `<th class="commonInputTh">${getMessage.FTE00147}</th>`
                                + `<td class="commonInputTd">`
                                    + `<div class="scheduleInputFromDateWrap">`
                                        + fn.html.inputText(['scheduleInput', 'scheduleToDate'], fn.cv( initScheduleValue.end_date, ''), 'end_date_' + itemId, { placeholder: 'yyyy/MM/dd HH:mm:ss', type: 'toDate', key: 'end_date'})
                                    + `</div>`
                                + `</td>`
                                + `<td class="commonInputTd">`
                                    + `<div class="scheduleInputDateCalendar">`
                                        + fn.html.button('<span class="icon icon-cal"></span>', ['itaButton', 'scheduleInputDatePicker'], { action: 'normal'})
                                    + `</div>`
                                + `</td>`
                            + `</tr>`
                        + `</tbody>`
                    + `</table>`
                + `</div>`
                + `<div class="commonBody periodErrorBlock"></div>`
            + `</div>`
            + `<div class="commonTitle">${getMessage.FTE00149}</div>`
            + `<div class="commonBody">`
                + `<div class="scheduleType">`
                    + `<div class="scheduleDetaile">`
                        + `<div class="commonInputGroup">`
                            + `<ul class="commonRadioList schedulePeriodRadioList">`
                                + schedulePeriodRadio()
                            + `</ul>`
                            + `<table class="commonInputTable" data-type="${selectPeriod}">`
                                + `<tbody class="commonInputTbody">`
                                    + feaderList()
                                + `</tbody>`
                            + `</table>`
                        + `</div>`
                    + `</div>`
                + `</div>`
            + `</div>`
            + `<div class="commonTitle">${getMessage.FTE00150}</div>`
            + `<div class="commonBody scheduleInputFromToDate">`
                + `<div class="commonInputGroup">`
                    + `<table class="commonInputTable">`
                        + `<tbody class="commonInputTbody">`
                            + `<tr class="commonInputTr">`
                                + `<th class="commonInputTh"><div class="commonInputTitle">${getMessage.FTE00151}</div></th>`
                                + `<td class="commonInputTd">`
                                    + `<div class="scheduleInputFromDateWrap">`
                                        + fn.html.inputText(['scheduleInput', 'scheduleFromDate'], fn.cv( initScheduleValue.execution_stop_start_date, ''), 'execution_stop_start_date_' + itemId, { placeholder: 'yyyy/MM/dd HH:mm:ss', type: 'fromDate', key: 'execution_stop_start_date'})
                                    + `</div>`
                                + `</td>`
                                + `<td class="commonInputTd">${getMessage.FTE00148}</td>`
                                + `<th class="commonInputTh">${getMessage.FTE00152}</th>`
                                + `<td class="commonInputTd">`
                                    + `<div class="scheduleInputFromDateWrap">`
                                        + fn.html.inputText(['scheduleInput', 'scheduleToDate'], fn.cv( initScheduleValue.execution_stop_end_date, ''), 'execution_stop_end_date_' + itemId, { placeholder: 'yyyy/MM/dd HH:mm:ss', type: 'toDate', key: 'execution_stop_end_date'})
                                    + `</div>`
                                + `</td>`
                                + `<td class="commonInputTd">`
                                    + `<div class="scheduleInputDateCalendar">`
                                        + fn.html.button('<span class="icon icon-cal"></span>', ['itaButton', 'scheduleInputDatePicker'], { action: 'normal'})
                                    + `</div>`
                                + `</td>`
                            + `</tr>`
                        + `</tbody>`
                    + `</table>`
                + `</div>`
                + `<div class="commonBody stopErrorBlock"></div>`
            + `</div>`
            + `<div class="commonTitle">${getMessage.FTE00153}</div>`
            + `<div class="commonBody">`
                + fn.html.textarea('scheduleNote',  fn.cv( initScheduleValue.remarks, ''), null, {key: 'remarks'})
            + `</div>`
        + `</div>`;

        // モーダル作成
        let modal = new Dialog( config, funcs );
        modal.open( html );

        const $mbody = modal.$.dbody;

        // 周期選択
        $mbody.find('.schedulePeriodType').on('change', function(){
            const $radio = $( this ),
                  type = $radio.attr('data-type');
            $mbody.find('.commonInputTable').attr('data-type', type );
        });

        // フェーダー
        $mbody.find('.inputFaderWrap').each(function(){
            fn.faderEvent( $( this ) );
        });

        // フェーダー未入力の場合はmin値を入れる
        $mbody.find('.schedulePeriodInput').on('change', function(){
            const $input = $( this ),
                  value = $input.val(),
                  min = $input.attr('data-min');
            if ( value === '') {
                $input.val( min ).change();
            }
        });

        // 日付欄入力チェック
        const $scheduleInput = $mbody.find('.scheduleInput'),
              $errorPeriod = $mbody.find('.periodErrorBlock'),
              $errorStop = $mbody.find('.stopErrorBlock');

        const errorListHtml = function( text ) {
            return `<li class="commonErrorItem">${fn.html.icon('circle_exclamation')}${text}</li>`;
        };

        const checkPeriod = function() {
            const scheduleInputValue = {},
                  periodErrorHtml = [],
                  stopErrorHtml = [];

            let errorCount = 0;

            $scheduleInput.each(function(){
                const $input = $( this ),
                      value = $input.val(),
                      key = $input.attr('data-key');

                // 必須チェック
                if ( key === 'start_date' && value === '') {
                    periodErrorHtml.push( errorListHtml(getMessage.FTE00154) );
                    errorCount++;
                }

                // 形式チェック
                const dateValidationRule = /^\d{4}\/\d{2}\/\d{2} \d{2}:\d{2}:\d{2}$/;

                const checkPeriodText = {
                    start_date: getMessage.FTE00155,
                    end_date: getMessage.FTE00156,
                    execution_stop_start_date: getMessage.FTE00157,
                    execution_stop_end_date: getMessage.FTE00158
                };
                if ( value !== '' && ( !dateValidationRule.test( value ) || Number.isNaN(new Date( value ).getTime()) ) ) {
                    const error = errorListHtml( getMessage.FTE00159( checkPeriodText[ key ] ) );
                    if ( key === 'start_date' || key === 'end_date') {
                        periodErrorHtml.push( error );
                    } else {
                        stopErrorHtml.push( error );
                    }
                    errorCount++;
                } else {
                    scheduleInputValue[ key ] = value;
                }
            });

            // 作業期間チェック
            if ( scheduleInputValue.start_date && scheduleInputValue.end_date ) {
                if ( scheduleInputValue.start_date >= scheduleInputValue.end_date ) {
                    periodErrorHtml.push( errorListHtml(getMessage.FTE00160) );
                    errorCount++;
                }
            }
            // 作業停止期間チェック
            if ( scheduleInputValue.execution_stop_start_date && scheduleInputValue.execution_stop_end_date ) {
                if ( scheduleInputValue.execution_stop_start_date >= scheduleInputValue.execution_stop_end_date ) {
                    stopErrorHtml.push( errorListHtml(getMessage.FTE00161) );
                    errorCount++;
                }
            }
            // 両方入力されているかチェック
            if ( ( scheduleInputValue.execution_stop_start_date && !scheduleInputValue.execution_stop_end_date ) ||
                 ( !scheduleInputValue.execution_stop_start_date && scheduleInputValue.execution_stop_end_date ) ) {
                stopErrorHtml.push( errorListHtml(getMessage.FTE00162) );
                errorCount++;
            }
            // 作業期間内かチェック
            if ( scheduleInputValue.execution_stop_start_date && scheduleInputValue.execution_stop_end_date ) {
                if ( ( scheduleInputValue.start_date > scheduleInputValue.execution_stop_start_date ) ||
                     ( scheduleInputValue.end_date < scheduleInputValue.execution_stop_end_date ) ) {
                    stopErrorHtml.push( errorListHtml(getMessage.FTE00163) );
                    errorCount++;
                }
            }

            // 作業期間エラー表示
            if ( periodErrorHtml.length ) {
                $errorPeriod.html(`<ul class="commonErrorList">${periodErrorHtml.join('')}</ul>`);
            } else {
                $errorPeriod.empty();
            }

            // 作業停止期間エラー表示
            if ( stopErrorHtml.length ) {
                $errorStop.html(`<ul class="commonErrorList">${stopErrorHtml.join('')}</ul>`);
            } else {
                $errorStop.empty();
            }

            // 反映ボタン活性化チェック
            const errorFlag = ( errorCount > 0 )? true: false;
            modal.buttonPositiveDisabled( errorFlag );
        };
        checkPeriod();

        $scheduleInput.on('change', function(){
            checkPeriod();
        });

        // データピッカー
        $mbody.find('.scheduleInputDatePicker').on('click', function(){
            const $button = $( this );

            const $from = $button.closest('.scheduleInputFromToDate').find('.scheduleFromDate'),
                  $to = $button.closest('.scheduleInputFromToDate').find('.scheduleToDate');

            const from = $from.val(),
                  to = $to.val();

            fn.datePickerDialog('fromTo', true, getMessage.FTE00164, { from: from, to: to } ).then(function( result ){
                if ( result !== 'cancel') {
                    $from.val( result.from );
                    $to.val( result.to ).change();
                }
            });
        });
    });
}

}