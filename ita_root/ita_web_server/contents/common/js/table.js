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
      parameter: パラメータ集
##################################################
*/
constructor( tableId, mode, info, params, option = {}) {
    const tb = this;
    tb.id = tableId;
    tb.mode = mode;
    tb.initMode = mode;
    tb.info = info;
    tb.params = params;

    // 選択データ（ID）
    tb.select = {
        view: [],
        edit: [],
        select: [],
        execute: []
    };

    // 選択データ
    tb.selectedData = {};

    // 特殊表示用データ
    tb.option = option;

    // ファイルフラグをオフにする
    tb.option.fileFlag = false;

    // REST API URLs
    tb.rest = {};

    // パーツ用テーブルフラグ
    tb.partsFlag = ( tb.option.parts !== undefined );

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
    if ( tb.workType ) {
        // window.console.warn('"table.js" workStart() warning.');
        return;
    }

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
        if ( tb.mode === 'parameter') {
            // パラメータ以外は非表示にする
            const hideItem = [
                'uuid', 'input_order', 'discard', 'host_name', 'operation_name_disp',
                'base_datetime', 'operation_date', 'last_execute_timestamp',
                'remarks', 'last_update_date_time', 'last_updated_user'
            ];

            if ( tb.info.column_info[key] ) {
                return hideItem.indexOf( tb.info.column_info[key].column_name_rest ) === -1;
            } else {
                return true;
            }
        } else {
            const hideItem = tb.getTableSettingValue('hideItem');
            if ( hideItem.length ) {
                return ( hideItem.indexOf( key ) === -1 );
            } else {
                return true;
            }
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
          specialFootColumnKeys = [],
          fileColumns = ['FileUploadColumn'];

    tb.data.hierarchy = [];
    tb.data.columnKeys = [];
    tb.data.restNames = {};
    tb.data.fileRestNames = [];

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
                const columnRest = tb.info.column_info[ columnKey ].column_name_rest;
                const columnType = tb.info.column_info[ columnKey ].column_type;
                tb.data.restNames[ columnRest ] = tb.info.column_info[ columnKey ].column_name;
                if ( fileColumns.indexOf( columnType ) !== -1 ) tb.data.fileRestNames.push( columnRest );
                if ( columnRest === tb.idNameRest ) tb.idName = tb.info.column_info[ columnKey ].column_name;
                if ( specialHeadColumn.indexOf( columnRest ) !== -1 ) {
                    specialHeadColumnKeys[ specialHeadColumn.indexOf( columnRest ) ] = columnKey;
                } else if ( specialFootColumn.indexOf( columnRest ) !== -1 ) {
                    specialFootColumnKeys[ specialFootColumn.indexOf( columnRest ) ] = columnKey;
                } else {
                    restOrder.push( columnRest );
                    tb.data.hierarchy[ row ].push( columnKey );
                    tb.data.columnKeys.push( columnKey );
                    if ( referenceFilterColumn.indexOf( columnRest ) !== -1 ) {
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
   Main html
##################################################
*/
mainHtml() {
    const tb = this;

    tb.option.sheetType = fn.cv( tb.option.sheetType, 'standard');
    if ( tb.mode !== 'parameter') {
        if ( !tb.partsFlag ) {
            // Default table
            return `<div id="${tb.id}" class="tableContainer ${tb.mode}Table ${tb.option.sheetType}Table">`
                + `<div class="tableHeader">`
                + `</div>`
                + `<div class="tableBody">`
                    + `<div class="tableFilter"></div>`
                    + `<div class="tableWrap">`
                        + `<div class="tableBorder">`
                            + `<table class="table mainTable"></table>`
                        + `</div>`
                    + `</div>`
                    + `<div class="tableMessage"></div>`
                + `</div>`
                + `<div class="tableFooter">${tb.footerHtml()}</div>`
                + `<div class="tableErrorMessage"></div>`
                + `<div class="tableLoading"></div>`
                + `<style class="tableStyle"></style>`
                + `<style class="tableCustomStyle"></style>`
            + `</div>`;
        } else {
            // Parts table
            return `<div id="parts${tb.id}" class="tableContainer ${tb.mode}Table ${tb.option.sheetType}Table">`
                + tb.partsBlockHtml()
                + `<div class="tableLoading"></div>`
            + `</div>`;
        }
    } else {
        // Parameter collection
        return ``
            + `<div class="parameterBlockTableBody">`
                + `<div id="${tb.id}" class="tableContainer ${tb.mode}Table ${tb.option.sheetType}Table">`
                    + `<div class="tableBody">`
                        + `<div class="tableWrap">`
                            + `<div class="tableBorder">`
                                + `<table class="table mainTable"></table>`
                            + `</div>`
                        + `</div>`
                    + `</div>`
                    + `<div class="tableMessage"></div>`
                + `</div>`
                + `<div class="tableLoading"></div>`
                + `<style class="tableStyle"></style>`
            + `</div>`;
    }
}
/*
##################################################
   Setup
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
    tb.$.filter = tb.$.container.find('.tableFilter');
    tb.$.footer = tb.$.container.find('.tableFooter');
    tb.$.table = tb.$.container.find('.table');
    tb.$.message = tb.$.container.find('.tableMessage');
    tb.$.errorMessage = tb.$.container.find('.tableErrorMessage');
    tb.$.style = tb.$.container.find('.tableStyle');
    tb.$.custom = tb.$.container.find('.tableCustomStyle');

    // パーツテーブル
    if ( tb.partsFlag ) {
        tb.$.thead = tb.$.container.find('.eventFlowPartsBlockHeader');
    }

    // 固有ID
    tb.idNameRest = tb.info.menu_info.pk_column_name_rest;

    // テーブルデータ
    tb.data = {};
    tb.data.count = 0;

    // 複製用ファイル
    tb.data.tempFile = {};

    // テーブル表示モード "input" or "view"
    // カラム（column_input or colum_view）
    const tableViewModeList = ['view', 'select', 'execute', 'history', 'parameter'];
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
    if ( tb.mode !== 'parameter' && !tb.partsFlag ) {
        const onePageNum = fn.storage.get('onePageNum', 'local', false );
        if ( onePageNum ) {
            tb.paging.onePageNum = onePageNum;
        } else {
            tb.paging.onePageNum = 25;
        }
    } else {
        tb.paging.onePageNum = 10000;
        if ( tb.option.parameterBundle === '1') tb.menuMode = 'bundle';
    }

    // ソート
    if ( !tb.sort ) tb.sort = [];

    // ドライバータイプ
    tb.driver = null;
    if ( tb.params && fn.typeof( tb.params.menuNameRest ) === 'string') {
        if (  tb.params.menuNameRest.match('_ansible_') ) {
            tb.driver = 'ansible';
        } else if (  tb.params && tb.params.menuNameRest.match('_terraform_') ) {
            tb.driver = 'terraform';
        }
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
        case 'parameter':
            tb.workStart('table', 0 );
        case 'select': case 'execute':
            tb.flag.initFilter = true;
            tb.flag.countSkip = true;
        break;
    }

    // パーツテーブル用
    if ( tb.partsFlag ) {
        tb.flag.initFilter = true;
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

    // パーツテーブル
    if ( tb.partsFlag ) {
        tb.setPartsTable( mode );
        return;
    }

    tb.mode = mode;

    tb.$.table.attr('table-mode', tb.tableMode );

    // フィルター位置
    if ( tb.mode !== 'parameter') {
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
    } else {
        tb.$.table.html( tb.commonTableHtml( false ) );
    }

    tb.$.thead = tb.$.container.find('.thead');
    tb.$.tbody = tb.$.container.find('.tbody');

    // 項目メニュー表示
    if ( tb.getTableSettingValue('menu') === 'show') {
        tb.$.body.addClass('tableItemMenuShow');
    } else {
        tb.$.body.removeClass('tableItemMenuShow');
    }

    if ( tb.mode !== 'parameter') {
        tb.$.thead.find('.filterInputDiscard').select2({
            width: '120px',
            minimumResultsForSearch: 5
        });
        tb.setInitSort();
    }

    // 縦・横
    if ( tb.getTableSettingValue('direction') === 'horizontal') {
        tb.$.body.addClass('tableHorizontal');
        tb.$.body.removeClass('tableVertical');
    } else {
        tb.$.body.addClass('tableVertical');
        tb.$.body.removeClass('tableHorizontal');
    }

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
                    if ( tb.option.data ) {
                        // フィルターボタンを削除
                        menuList.Sub.shift(-1);
                        // 検索
                        menuList.Sub[0].separate = true;
                        menuList.Sub.unshift({ search: { placeholder: tb.option.searchText, tableId: tb.id }});
                    }
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
                            $button.prop('disabled', true );
                            tb.tableSettingOpen().then(function(){
                                $button.prop('disabled', false );
                            });
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
                            $button.prop('disabled', true );
                            tb.execute('dryrun').then(function(){
                                $button.prop('disabled', false );
                            });
                        break;
                        // 作業実行
                        case 'tableRun':
                            $button.prop('disabled', true );
                            tb.execute('run').then(function(){
                                $button.prop('disabled', false );
                            });
                        break;
                        // パラメータ確認
                        case 'tableParameter':
                            $button.prop('disabled', true );
                            tb.execute('parameter').then(function(){
                                $button.prop('disabled', false );
                            });
                        break;
                    }
                }
            });

            // 検索
            if ( tb.option.data ) {
                const search = function( text ){
                    if ( !tb.checkWork ) {
                        tb.workStart('search');
                        tb.workerPost('search', {
                            text: text,
                            keys: tb.option.searchKeys
                        });
                    }
                };
                const $input = tb.$.header.find('.operationMenuSearchText');
                $input.on({
                    change: function( e ){
                        search( $( this ).val() );
                    }
                });
                tb.$.header.find('.operationMenuSearchClear').on({
                    click: function( e ){
                        $input.val('');
                        search('');
                    }
                });
            }

            // tbody表示
            if ( !tb.option.data ) {
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
            } else {
                tb.workerPost('normal', tb.option.data );
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
                            $button.prop('disabled', true );
                            tb.reflectEdits.call( tb ).then(function(){
                                $button.prop('disabled', false );
                            });
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
                            $button.prop('disabled', true );
                            tb.tableSettingOpen().then(function(){
                                $button.prop('disabled', false );
                            });
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
        case 'parameter': {
            tb.requestTbody();
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
        html[0] = '';
        switch ( tb.mode ) {
            case 'view': {
                if ( tb.flag.update ) {
                    const selectButton = fn.html.button('', 'rowSelectButton');
                    html[0] += fn.html.cell( selectButton, ['tHeadTh', 'tHeadLeftSticky', 'tHeadRowSelect'], 'th', headRowspan );
                    tb.data.filterHeadColspan++;
                }
                const itemText = ( tb.getTableSettingValue('menu') === 'show')? getMessage.FTE00178: fn.html.icon('ellipsis_v');
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
                if ( tb.mode === 'parameter' && i === 0 ) continue;
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
        // オペレーション or ホストの追加
        if ( tb.mode === 'parameter' && i === 1 ) {
            if ( tb.menuMode === 'bundle') {
                html[i] = fn.html.cell( getMessage.FTE11047, 'tHeadTh', 'th', rowLength, 1 ) + html[i];
            }
            html[i] = fn.html.cell('', 'parameterTheadTh tHeadTh tHeadLeftSticky', 'th', rowLength, 1 ) + html[i];
        }
        // 行追加
        if ( html[i] !== '') {
            html[i] = fn.html.row( html[i], ['tHeadTr', 'headerTr']);
        }
    }

    // フィルター入力欄
    if ( tb.mode === 'view' || tb.mode === 'select' || tb.mode === 'execute') {
        if ( tb.option.sheetType !== 'reference' && !tb.option.data ) {
            if ( filterFlag === true ) html.push( tb.filterHtml( filterHeaderFlag ) );
        }
    }

    return html.join('');
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
              name = tb.id + '_' + column.col_name,
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
                    case 'JsonIDColumn': case 'UserIDColumn': case 'NotificationIDColumn':
                    case 'FilterConditionSettingColumn': case 'ConclusionEventSettingColumn':
                    case 'ColorCodeColumn': case 'ExecutionEnvironmentDefinitionIDColumn':
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
                          return '0';
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
                '0': getMessage.FTE00041,
                '1': getMessage.FTE00042,
                '2': getMessage.FTE00040
            };
            const listNum = ( initValue === '')? '2': initValue;
            cellHtml.push( fn.html.select( list, ['filterInput', 'filterInputDiscard'], list[ listNum ], name, { type: 'discard', rest: rest } ) );
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
                            + fn.html.inputNumber(['filterInput', 'filterFromNumber'], initValue.start, name + '_from', { type: 'fromNumber', rest: rest, placeholder: 'From' })
                        + `</div>`
                        + `<div class="filterInputToNumberWrap">`
                            + fn.html.inputNumber(['filterInput', 'filterToNumber'], initValue.end, name + '_to', { type: 'toNumber', rest: rest, placeholder: 'To' })
                        + `</div>`
                    + `</div>`);
                break;
                // 日時のFROM,TO
                case 'fromToDateTime':
                    cellHtml.push(`<div class="filterInputFromToDate">`
                        + `<div class="filterInputFromDateWrap">`
                            + fn.html.inputText(['filterInput', 'filterFromDate'], initValue.start, name + '_from', { type: 'fromDate', rest: rest, placeholder: 'From' })
                        + `</div>`
                        + `<div class="filterInputToDateWrap">`
                            + fn.html.inputText(['filterInput', 'filterToDate'], initValue.end, name + '_to', { type: 'toDate', rest: rest, placeholder: 'To' })
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
                            + fn.html.inputText(['filterInput', 'filterFromDate'], initValue.start, name + '_from', { type: 'fromDate', rest: rest, placeholder: 'From' })
                        + `</div>`
                        + `<div class="filterInputToDateWrap">`
                            + fn.html.inputText(['filterInput', 'filterToDate'], initValue.end, name + '_to', { type: 'toDate', rest: rest, placeholder: 'To' })
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
        if ( tb.option.dataType === 'n') {
            menuList.push({ name: 'excel', title: getMessage.FTE00046, action: 'default', separate: true, disabled: true });
            menuList.push({ name: 'json', title: getMessage.FTE00047, action: 'default', disabled: true });
            menuList.push({ name: 'jsonNoFile', title: getMessage.FTE00183, action: 'default', disabled: true });
        }
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
          $json =  $filterTarget.find('.filterMenuButton[data-type="json"], .filterMenuButton[data-type="jsonNoFile"]');

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

    if ( params !== undefined ) {
        // 編集画面で入力済みデータがある場合
        if ( tb.mode === 'edit' && tb.edit && tb.edit.input[ id ] && tb.edit.input[ id ].after.file[ name ] ) {
            return tb.edit.input[ id ].after.file[ name ];
        }
        // 確認画面かつ変更前のデータがある場合
        if ( tb.mode === 'diff') {
            if ( (type === 'beforeValue' || ( !params.file[ name ] && type === '')) && tb.option && tb.option.before[ id ] ) {
                return tb.option.before[ id ].file[ name ];
            }
        }
        return params.file[ name ];
    } else {
        return null;
    }
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

            const $a = $( this );
            if ( $a.is('.nowDownload') ) return;

            const fileName = $a.text();
            const rest = $a.attr('data-rest');
            const type = $a.attr('data-type');

            const id = $a.attr('data-id');
            const journalId = $a.attr('data-journalId');
            const fileId = ( tb.mode !== 'history')? id: journalId;

            let file = tb.getFileData( fileId, rest, type );

            // ファイルモード
            if ( tb.option.fileFlag === false && fileName !== '' && file === undefined ) {
                const restType = $a.attr('data-restType');
                let endPoint = `/menu/${tb.params.menuNameRest}/${id}/${rest}/file/`;
                if ( restType === 'history' && tb.mode === 'history') {
                    const journalId = $a.attr('data-journalId');
                    endPoint += `journal/${journalId}/`;
                }
                $a.addClass('nowDownload');
                fn.getFile( endPoint, 'GET', null, { title: getMessage.FTE00185 }).then(function( file ){
                    fn.download('file', file, fileName );
                    $a.removeClass('nowDownload');
                }).catch(function( e ){
                    if ( e !== 'break') {
                        console.error( e );
                        alert( getMessage.FTE00179 );
                    }
                    $a.removeClass('nowDownload');
                });
            } else {
                if ( file !== undefined && file !== null ) {
                    const fileType = ( fn.typeof( file ) === 'file')? 'file': 'base64';
                    fn.download( fileType, file, fileName );
                } else {
                    alert( getMessage.FTE06033 );
                }
            }
        });

        // ファイルプレビュー
        tb.$.tbody.on('click', '.filePreview', async function(e){
            // ファイルモーダルが開いているときは無効
            if ( tb.modalFlag ) {
                e.preventDefault();
                return false;
            }

            const $button = $( this );
            const $a = $( this ).prev();
            const fileName = $a.text();
            const rest = $a.attr('data-rest');
            const type = $a.attr('data-type');

            const id = $a.attr('data-id');
            const journalId = $a.attr('data-journalId');
            const fileId = ( tb.mode !== 'history')? id: journalId;

            $button.prop('disabled', true );
            tb.modalFlag = true;
            let file = tb.getFileData( fileId, rest, type );

            const option = {
                endPoint: `/menu/${tb.params.menuNameRest}/${id}/${rest}/file/`
            };

            // ファイルモード
            if ( tb.option.fileFlag === false && fileName !== '' && file === undefined ) {
                const restType = $a.attr('data-restType');
                if ( restType === 'history' && tb.mode === 'history') {
                    const journalId = $a.attr('data-journalId');
                    option.endPoint += `journal/${journalId}/`;
                }
                try {
                    file = await fn.getFile( option.endPoint, 'GET', null );
                } catch ( e ) {
                    if ( e !== 'break') {
                        console.error( e );
                        alert( getMessage.FTE00179 );
                    }
                    $button.prop('disabled', false );
                    tb.modalFlag = false;
                    return;
                }
                fn.fileEditor( file, fileName, 'preview', option ).then(function(){
                    $button.prop('disabled', false );
                    tb.modalFlag = false;
                });
            } else {
                if ( !file ) file = '';
                fn.fileEditor( file, fileName, 'preview', option ).then(function(){
                    $button.prop('disabled', false );
                    tb.modalFlag = false;
                });
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
        const downloadFile = async function( $button, type, url ){
            tb.filterParams = tb.getFilterParameter();
            const ext = ( type === 'excel')? '.xlsx': '.json';
            const fileName = fn.cv( tb.info.menu_info.menu_name, 'file') + '_filter' + ext;

            $button.prop('disabled', true );
            try {
                const file = await fn.getFile( url, 'POST', tb.filterParams, { title: getMessage.FTE00185, fileType: type });
                if ( type !== 'json') type = 'file';
                fn.download( type, file, fileName );
            } catch ( error ) {
                if ( error !== 'break') {
                    fn.gotoErrPage( error.message );
                }
            }
            fn.disabledTimer( $button, false, 1000 );
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
                        if ( window.confirm( getMessage.FTE00181 ) ) {
                            downloadFile( $button, 'json', tb.rest.jsonDownload );
                        }
                    break;
                    case 'jsonNoFile':
                        downloadFile( $button, 'json', tb.rest.jsonDownload + '?file=no');
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

                const findData = tb.data.body.find(function( data ){
                    return String( data.parameter[ tb.idNameRest ] ) === String( itemId );
                });
                if ( findData ) {
                    tb.selectedData[ itemId ] = findData;
                }

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
        tb.$.tbody.on('click', '.tableEditSelectFile', function(e){
            if ( tb.modalFlag ) {
                e.preventDefault();
                return false;
            }

            const
            $button = $( this ),
            id = $button.attr('data-id'),
            key = $button.attr('data-key'),
            maxSize = $button.attr('data-upload-max-size');

            $button.prop('disabled', true );

            fn.fileSelect('file', maxSize ).then(function( result ){

                const changeFlag = tb.setInputFile( result.name, result, id, key, tb.data.body );

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
            }).then(function(){
                $button.prop('disabled', false );
            });
        });

        // ファイル編集
        tb.$.tbody.on('click', '.inputFileEditButton',async function(e){
            if ( tb.modalFlag ) {
                e.preventDefault();
                return false;
            }

            const
            $button = $( this ),
            id = $button.attr('data-id'),
            rest = $button.attr('data-key'),
            $fileBox = $button.closest('.inputFileEdit').prev().find('.tableEditSelectFile');

            $button.prop('disabled', true );
            tb.modalFlag = true;

            let file = tb.getFileData( id, rest );
            let fileName = $fileBox.text();

            const fileType = fn.fileTypeCheck( fileName );
            const option = {
                endPoint: `/menu/${tb.params.menuNameRest}/${id}/${rest}/file/`
            };

            // ファイルが空、かつ編集可能の場合はファイルを取得する
            if ( tb.option.fileFlag === false && fileName !== '' && file === undefined && ( fileType === 'text' || fileType === 'image') ) {
                try {
                    file = await fn.getFile( option.endPoint, 'GET', null );
                } catch ( e ) {
                    if ( e !== 'break') {
                        console.error( e );
                        alert( getMessage.FTE00179 );
                    }
                    $button.prop('disabled', false );
                    tb.modalFlag = false;
                    return;
                }
            } else {
                if ( !file ) file = null;
            }
            if ( !fileName ) fileName = 'noname.txt';

            fn.fileEditor( file, fileName, 'edit', option ).then(function( result ){
                if ( result !== null ) {
                    const changeFlag = tb.setInputFile( result.name, result.file, id, rest, tb.data.body );

                    $fileBox.find('.inner').text( result.name );
                    if ( changeFlag ) {
                        $fileBox.addClass('tableEditChange');
                    } else {
                        $fileBox.removeClass('tableEditChange');
                    }
                }

                $button.prop('disabled', false );
                tb.modalFlag = false;
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
                    $input.parent('.tableEditInputSelectContainer, .tableEditInputMultipleSelectContainer').addClass('tableEditChange');
                }
                if ( $input.is('.tableEditMultipleHiddenColmun') ) {
                    $input.prev('.tableEditMultipleColmun').addClass('tableEditChange');
                }
            } else {
                $input.removeClass('tableEditChange');
                if ( $input.is('.tableEditInputSelect') ) {
                    $input.parent('.tableEditInputSelectContainer, .tableEditInputMultipleSelectContainer').removeClass('tableEditChange');
                }
                if ( $input.is('.tableEditMultipleHiddenColmun') ) {
                    $input.prev('.tableEditMultipleColmun').removeClass('tableEditChange');
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
                    $input.removeClass('tableEditRequiredError');
                } else {
                    $input.addClass('tableEditRequiredError');
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
        tb.$.tbody.on('click', '.inputPasswordDeleteToggleButton', function(e){
            if ( tb.modalFlag ) {
                e.preventDefault();
                return false;
            }

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
        tb.$.tbody.on('click', '.inputFileClearButton', function(e){
            if ( tb.modalFlag ) {
                e.preventDefault();
                return false;
            }

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

        // select2が隠れている場合スクロールで調整する
        const select2ScrollCheck = function( $element ) {
            if ( tb.partsFlag ) return;

            const
            width = $element.closest('.ci').width(),
            left = $element.closest('.ci').offset().left,
            wrapLeft = tb.$.wrap.offset().left,
            wrapWidth = tb.$.wrap.width(),
            wrapScroll = tb.$.wrap.scrollLeft();

            if ( left - wrapLeft + width - wrapScroll > wrapWidth - wrapScroll ) {
                tb.$.wrap.scrollLeft( ( left - wrapLeft + width ) - ( wrapWidth - wrapScroll ) );
            }
        };

        // select欄クリック時にselect2を適用する
        tb.$.tbody.on('click', '.tableEditInputSelectValue, .tableEditInputMultipleSelectValue', function(){
            const
            $value = $( this ),
            $select = $value.next('.tableEditInputSelect'),
            restName = $select.attr('data-key'),
            required = $select.attr('data-required'),
            multiple = $select.is('.tableEditInputMultipleSelect');

            if ( $value.is('.tableEditInputSelectValueDisabled') ) return false;

            const list = Object.keys( tb.data.editSelect[ restName ] ).map(function(key){
                return tb.data.editSelect[ restName ][ key ];
            });

            // 必須じゃない場合は空白を追加する
            if ( required === '0' && multiple !== true ) list.unshift('');

            tb.setSelect2( null, $select, list, true, null, $value, multiple ).then(function(){
                $select.change();
            });
        });

        // select2が開いているときはスクロールさせない
        tb.$.tbody.on({
            'select2:opening': function( e ){
                select2ScrollCheck( $( e.target ) );
                $( this ).closest('.tableWrap').on('wheel.select2Scroll', function(){
                    e.preventDefault();
                });
            },
            'select2:closing': function(){
                $( this ).closest('.tableWrap').off('wheel.select2Scroll');
            }
        });

        // select欄フォーカス時にselect2を適用する
        tb.$.tbody.on('focus.select2', '.tableEditInputSelect', function(){
            const
            $select = $( this ),
            flag = $select.is('.tableEditInputMultipleSelect'),
            container = ( flag )? '.tableEditInputMultipleSelectContainer': '.tableEditInputSelectContainer',
            value = ( flag )? '.tableEditInputMultipleSelectValue': '.tableEditInputSelectValue';

            // フォーカス時のスクロールを0に
            $select.closest( container ).scrollTop(0);

            // クリックイベント
            $select.prev( value ).click();
        });

        // input hidden変更時にテキストも変更する
        tb.$.tbody.on('change', '.tableEditInputHidden', function(){
            const $input = $( this ),
                  value = $input.val(),
                  $text = $input.prev('.tableEditInputHiddenText');
            $text.text( value );
        });

        // カラーピッカー クリックしたときに値をinputに入れる
        let colorFlag = false;
        const colorChange = function( $color ) {
            const
            $wrap = $color.closest('.inputColorEditWrap'),
            $mark = $wrap.find('.inputColorEditSelect'),
            $text = $wrap.find('.inputText'),
            value = fn.checkHexColorCode( $color.val() );

            $text.val( value ).change();
            $mark.css('background-color', value );
        };
        tb.$.tbody.on({
            'click': function(){
                colorChange( $(this) );
            },
            'change': function(){
                colorChange( $(this) );
            }
        }, '.inputColorEdit');

        // テキスト入力をカラーピッカーに反映する
        tb.$.tbody.on('change', '.tableEditSColorCode', function(){
            const
            $text = $( this ),
            $wrap = $text.closest('.inputColorEditWrap'),
            $mark = $wrap.find('.inputColorEditSelect'),
            $color = $wrap.find('.inputColorEdit'),
            value = fn.checkHexColorCode( $text.val(), false ),
            text = fn.checkHexColorCode( $text.val() );

            $color.val( value );
            $mark.css('background-color', value );

            $text.val( text );
        });

        // tableEditMultipleColmun
        tb.$.tbody.on('click', '.tableEditMultipleColmun', function(){
            const
            $block = $( this ),
            $input = $block.next('.inputHidden'),
            restName = $input.attr('data-key'),
            columnType = $input.attr('data-column-type'),
            required = $input.attr('data-required'),
            value = $input.val();

            tb.multipleColmunSetting( columnType, restName, value, required ).then(function( result ){
                if ( result !== undefined ) {
                    const resultValue = ( fn.typeof( result ) === 'array' && result.length )? fn.jsonStringifyDelimiterSpace( result ): '';
                    $input.val( resultValue ).change();

                    // 表示欄の幅の調整
                    if ( !tb.partsFlag ) {
                        $block.find('span').text( resultValue );
                        tb.tableInputMaxWidthCheck( $block );
                    } else {
                        $block.html( fn.html.labelListHtml( resultValue, tb.label ) );
                    }
                }
            });
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
                        fn.getFile( url, method, null, { title: getMessage.FTE00185 }).then(function( file ){
                            const fileName = fn.cv( file.name, '');
                            fn.download('file', file, fileName );
                        }).catch(function( error ){
                            if ( error !== 'break') {
                                alert( error.message );
                                window.console.error( error );
                            }
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
                        if ( fn.typeof( tb.params.selectNameKey ) !== 'array') {
                            const selectName = $check.attr('data-selectname');
                            if ( selectName ) {
                                const item = {
                                    id: id,
                                    name: selectName
                                };
                                tb.select[tb.mode].push( item );
                            } else {
                                tb.select[tb.mode].push( id );
                            }
                        } else {
                            const checkItem = {
                                id: id,
                                parameter: {}
                            };
                            const findData = tb.data.body.find(function( data ){
                                return String( data.parameter[ tb.idNameRest ] ) === String( id );
                            });
                            if ( findData ) {
                                for ( const key of tb.params.selectNameKey ) {
                                    checkItem.parameter[ key ] = findData.parameter[ key ];
                                }
                            }
                            tb.select[tb.mode].push( checkItem );
                        }
                    } else {
                        const index = tb.select[tb.mode].findIndex(function( item ){
                            if ( fn.typeof( item ) === 'object') {
                                return item.id === id;
                            } else {
                                return item === id;
                            }
                        });
                        if ( index !== -1 ) {
                            tb.select[ checkMode ].splice( index, 1 );
                        }
                    }
                } else {
                    if ( checked ) {
                        const findData = tb.data.body.find(function( data ){
                            return String( data.parameter[ tb.idNameRest ] ) === String( id );
                        });
                        if ( findData ) {
                            tb.selectedData[ id ] = findData;
                        }
                        tb.select[ checkMode ].push( id );
                    } else {
                        const index = tb.select[ checkMode ].indexOf( id );
                        if ( index !== -1 ) {
                            tb.select[ checkMode ].splice( index, 1 );
                        }
                        if ( id in tb.selectedData === true ) {
                            delete tb.selectedData[ id ];
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

    // 配列の場合文字列に変換する（複数選択セレクト）
    if ( fn.typeof( value ) === 'array') {
        value.sort(function( a, b ){
            if ( a === null || a === undefined ) a = '';
            if ( b === null || b === undefined ) b = '';
            if ( fn.typeof( a ) === 'number') a = String( a );
            if ( fn.typeof( b ) === 'number') b = String( b );
            return a.localeCompare( b );
        });
        if ( value.length > 0 ) {
            value = fn.jsonStringifyDelimiterSpace( value );
        } else {
            value = null;
        }
    }

    tb.checkNewInputDataSet( id, beforeData );

    // 変更があれば追加、なければ削除
    const beforeParamter = tb.edit.input[id]['before'].parameter[rest];
    const beforeValue = ( beforeParamter === undefined )? null: beforeParamter;

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
setInputFile( fileName, fileData, id, rest, beforeData ) {
    const tb = this;

    tb.checkNewInputDataSet( id, beforeData );

    // 変更があれば追加、なければ削除
    const beforeFileName = tb.edit.input[id]['before'].parameter[rest];

    let changeFlag = false;
    if ( fileData !== undefined || beforeFileName !== fileName ) {
        tb.edit.input[id]['after'].file[rest] = fileData;
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
        const $discard = tb.$.tbody.find(`.inputSpan[data-key="discard"][data-id="${id}"]`);
        const $tr = $discard.closest('.tBodyTr');

        if ( value === '0') {
            $tr.removeClass('tBodyTrDiscard');
            if ( changeFlag ) {
                $tr.find('[data-key="remarks"]').prop('disabled', false );
            } else {
                $tr.find('.input, .button, .tableEditInputSelect').prop('disabled', false );
                $tr.find('.tableEditInputSelectValue, .tableEditInputMultipleSelectValue, .tableEditMultipleColmun').removeClass('tableEditInputSelectValueDisabled');
            }
        } else {
            $tr.addClass('tBodyTrDiscard');
            if ( changeFlag ) {
                $tr.find('.input, .button, .tableEditInputSelect').not('[data-key="remarks"]').prop('disabled', true );
            } else {
                $tr.find('.input, .button, .tableEditInputSelect').prop('disabled', true );
            }
            $tr.find('.tableEditInputSelectValue, .tableEditInputMultipleSelectValue, .tableEditMultipleColmun').addClass('tableEditInputSelectValueDisabled');
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

    if ( tb.partsFlag ) {
        const $button =  tb.$.thead.find('.eventFlowPartsBlockMenuButton');
        $button.filter('[data-type="tableOk"]').prop('disabled', confirmFlag );
    } else {
        const $button = tb.$.header.find('.operationMenuButton');
        // $button.filter('[data-type="tableOk"]').prop('disabled', confirmFlag );
        $button.filter('[data-type="tableDup"]').prop('disabled', duplicatFlag );
        $button.filter('[data-type="tableDel"]').prop('disabled', deleteFlag );

        $button.filter('[data-type="tableDiscard"]').prop('disabled', discardFlag );
        $button.filter('[data-type="tableRestore"]').prop('disabled', restoreFlag );
    }
}
/*
##################################################
   [Event] Filter pulldown open
   > プルダウン検索セレクトボックスを表示する
##################################################
*/
filterSelectOpen( $button ) {
    const tb = this;

    const $selectArea = $button.parent('.filterSelectArea'),
        name = $button.attr('data-type') + '_RF',
        rest = $button.attr('data-rest');

    const $selectBox = $('<select/>' , {
        'class': 'filterSelect filterInput',
        'name': name,
        'data-type': 'select',
        'data-rest': rest,
        'multiple': 'multiple'
    });

    $button.addClass('buttonWaiting').prop('disabled', true );

    fn.fetch(`${tb.rest.filterPulldown}${rest}/`).then(function( selectList ){
        tb.setSelect2( $selectArea, $selectBox, selectList, true );
    }).catch( function( e ) {
        window.console.error( e.message );
        fn.gotoErrPage( e.message );
    });
}
/*
##################################################
   select2
##################################################
*/
setSelect2( $selectArea, $selectBox, optionlist, openFlag = false, selected, $removeObj, multipel = false ) {
    const tb = this;
    return new Promise(function( resolve ){
        // listをソートする
        optionlist.sort( tb.pulldownSort );

        // select2データ形式
        const selectedData = [];
        optionlist = optionlist.map(function( item ){
            const data = {};

            if ( item === null ) {
                data.id = '{blank}';
                data.text = `{${getMessage.FTE00177}}`;
            } else {
                data.id = data.text = item;
            }

            if ( selected && selected.indexOf( item ) !== -1 ) {
                data.selected = true;
                selectedData.push( data );
            }

            return data;
        });

        $.fn.select2.amd.require([
            'select2/data/array',
            'select2/utils'
        ], function ( ArrayData, Utils ) {
            function CustomData ( $element, options ) {
                CustomData.__super__.constructor.call( this, $element, options );
            }

            Utils.Extend( CustomData, ArrayData );

            CustomData.prototype.query = function ( params, callback ) {
                let options;
                if ( params.term && params.term !== '') {
                    options = optionlist.filter(function( item ){
                        return String( item.text ).indexOf( params.term ) !== -1;
                    });
                } else {
                    options = optionlist;
                }

                // ページネーション
                if ( !('page' in params) ) params.page = 1;
                const pageSize = 50;
                const results = {
                    results: options.slice(( params.page - 1 ) * pageSize, params.page * pageSize ),
                    pagination: {
                        more: ( params.page * pageSize < options.length )
                    }
                };

                callback( results );
            };

            const select2Option = {
                dropdownAutoWidth: false,
                ajax: {},
                dataAdapter: CustomData
            };

            if ( multipel ) {
                select2Option.closeOnSelect = false;
            }

            // Filter or Data
            let width;
            if ( $selectArea ) {
                $selectArea.html( $selectBox );
                select2Option.data = selectedData;
                select2Option.placeholder = 'Pulldown select';
                width = $selectArea.width();
            } else if ( $removeObj ) {
                width = $removeObj.outerWidth();
                $removeObj.remove();
            }
            if ( optionlist.length === 0 ) {
                select2Option.width = 120;
            } else if ( !multipel ) {
                select2Option.width = width;
            }
            $selectBox.select2( select2Option );

            if ( multipel ) {
                const $container = $selectBox.closest('.tableEditInputMultipleSelectContainer');
                $container.addClass('tableEditInputMultipleSelectOpen');
                if ( optionlist.length !== 0 ) {
                    $container.find('.select2').css({
                        'min-width': width + 20, // ×分の幅
                        'width': 'auto'
                    });
                }
            }

            if ( openFlag ) {
                $selectBox.select2('open');
            }

            resolve();
        });
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
            if ( filterParams[ rest ].LIST && rest in tb.data.restNames ) {
                filterRestUrls.push(`${tb.rest.filterPulldown}${rest}/`);
                filterKeys.push( rest );
                filterList[ rest ] = filterParams[ rest ].LIST;
            }
        }
        const length = filterKeys.length;

        if ( length ) {
            // 各セレクトリストの取得
            fn.fetch( filterRestUrls ).then(function( result ){
                let count = 0;
                for ( let i = 0; i < length; i++ ) {
                    const
                    $button = tb.$.thead.find(`.filterPulldownOpenButton[data-rest="${filterKeys[i]}"]`),
                    name = $button.attr('data-type') + '_RF',
                    $selectArea = $button.parent('.filterSelectArea');

                    const $selectBox = $('<select/>' , {
                        'class': 'filterSelect filterInput',
                        'name': name,
                        'data-type': 'select',
                        'data-rest': filterKeys[i],
                        'multiple': 'multiple'
                    });

                    tb.setSelect2( $selectArea, $selectBox, result[i], false, filterList[ filterKeys[i] ] ).then(function(){
                        // 全てのselect2の適用が終わったら
                        if ( ++count === length ) {
                            resolve();
                        }
                    });
                }
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
   名前リストを返す
   [{name: ***1},{name: ***2}] > [***1,***2]
##################################################
*/
getNameList( list ) {
    const nameList = [];
    for ( const item of list ) {
        nameList.push( item.name );
    }
    return nameList;
}
/*
##################################################
   tbodyデータのリクエスト
##################################################
*/
requestTbody() {
    const tb = this;

    if ( tb.mode !== 'parameter') {
        if ( !tb.partsFlag ) {
            tb.filterParams = tb.getFilterParameter();
        } else {
            tb.filterParams = {
                discard: {
                    NORMAL: '0'
                }
            };
        }
    } else {
        // パラメータ集フィルタ設定
        tb.filterParams = {
            discard: {
                NORMAL: '0'
            }
        };
        if ( tb.option.parameterMode === 'host') {
            // ホスト指定でオペレーションのみの場合はIDに__nohost_を入れて表示しない
            if ( tb.option.parameterHostList &&
            (
                ( tb.option.parameterHostList.length && tb.option.parameterSheetType === '3') ||
                ( tb.option.parameterHostList.length === 0 && tb.option.parameterSheetType !== '3')
            ) ) {
                tb.filterParams.uuid = {
                    NORMAL: '__nohost__'
                }
            } else {
                tb.filterParams.host_name = {
                    LIST: tb.getNameList( tb.option.parameterHostList )
                }
            }
        } else if ( tb.option.parameterMode === 'operation') {
            const operationFilterList = [];

            tb.filterParams.operation_name_disp = {
                LIST: tb.getNameList( tb.option.parameterOperationList )
            }
            if ( tb.option.parameterSheetType !== '3') {
                tb.filterParams.host_name = {
                    LIST: tb.getNameList( tb.option.parameterHostList )
                }
            }
        }
    }

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
                case 'select': {
                    const selected = [];
                    // 空白の判定をするためvalueを別で取得する
                    $input.find(':selected').each(function(){
                        const
                        $option = $( this ),
                        optionValue = $option.val(),
                        optionText = $option.text();

                        // {空白}の場合はnullを入れる
                        if ( optionValue === '{blank}' && optionText === `{${getMessage.FTE00177}}` ) {
                            selected.push( null );
                        } else {
                            selected.push( optionValue );
                        }

                    });
                    filterParams[ rest ].LIST = selected;
                } break;
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
   Worker post
   > Workerにmessageを送信
##################################################
*/
async workerPost( type, data ) {
    const tb = this;

    const post = {
        tableInfo: tb.info,
        type: type,
        paging: tb.paging,
        sort: tb.sort,
        idName: tb.idNameRest
    };

    // 送信タイプ別
    switch ( type ) {
        case 'filter': {
            const filterRest = ( tb.option.fileFlag === false )? tb.rest.filter + '?file=no': tb.rest.filter;

            const url = fn.getRestApiUrl(
                filterRest,
                tb.params.orgId,
                tb.params.wsId );

            const token = ( fn.getCmmonAuthFlag() )? CommonAuth.getToken():
                ( window.parent && window.parent.getToken )? window.parent.getToken(): null;

            post.rest = {
                token: token,
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
            try {
                await tb.duplicatFileCheck( data.select, data.input );
                post.select = data.select;
                post.addId = data.id;
                post.input = data.input;
                post.tempFile = tb.data.tempFile;
            } catch( error ) {
                tb.workEnd();
                tb.resetTable();
                return;
            }
        break;
        case 'changeEditDup':
            try {
                await tb.duplicatFileCheck( data.target, {});
                post.select = data.target;
                post.addId = data.id;
                post.tempFile = tb.data.tempFile;
            } catch( error ) {
                tb.workEnd();
                tb.resetTable();
                return;
            }
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

            const token = ( fn.getCmmonAuthFlag() )? CommonAuth.getToken():
                ( window.parent && window.parent.getToken )? window.parent.getToken(): null;

            post.rest = {
                token: token,
                url: ( tb.option.fileFlag === false )? url  + '?file=no': url
            };
        } break;
        case 'search':
            post.searchText = data.text;
            post.searchKeys = data.keys;
        break;
    }
    tb.worker.postMessage( post );
}
/*
##################################################
   複製時のファイル確認
   入力済みデータが無ければデータを取得する
##################################################
*/
duplicatFileCheck( selectId, inputData ) {
    const tb = this;
    return new Promise(async function( resolve, reject ){
        // 読込データにファイルが存在するか？
        for ( const id of selectId ) {
            if ( id in tb.selectedData === true ) {
                const data = tb.selectedData[ id ];
                for ( const fileColumn of tb.data.fileRestNames ) {
                    if (
                        fileColumn in data.parameter === true &&
                        data.parameter[ fileColumn ] !== null &&
                        data.parameter[ fileColumn ] !== ''
                    ) {
                        // 入力済みのデータがある場合
                        if (
                            id in inputData === true &&
                            fileColumn in inputData[ id ].after.parameter === true &&
                            inputData[ id ].after.parameter[ fileColumn ] !== null &&
                            inputData[ id ].after.parameter[ fileColumn ] !== '' &&
                            fileColumn in inputData[ id ].after.file === true &&
                            inputData[ id ].after.file[ fileColumn ] !== null
                        ) {
                            continue;
                        }
                        // すでに取得済みの場合
                        if ( id in tb.data.tempFile === true && fileColumn in tb.data.tempFile[ id ] === true ) {
                            continue;
                        }

                        // ファイル読込
                        try {
                            const file = await fn.getFile(`/menu/${tb.params.menuNameRest}/${id}/${fileColumn}/file/`, 'GET', null, {
                                type: 'duplicat',
                                uuid: id,
                                columnNameRest: fileColumn
                            });
                            if ( id in tb.data.tempFile === false ) tb.data.tempFile[ id ] = {};
                            tb.data.tempFile[ id ][ fileColumn ] = file;
                        } catch ( error ) {
                            if ( error !== 'break') {
                                console.error( error );
                            }
                            reject( error );
                        }
                    }
                }
            }
        }
        resolve();
    });
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

    const nodataHtml = `<div class="noDataMessage">`
    + fn.html.icon('stop')
    + getMessage.FTE00054
    + `</div>`;

    // 表示するものがない
    if ( tb.mode !== 'edit' && tb.data.body.length === 0 && !tb.partsFlag ) {
        tb.$.container.addClass('noData');
        tb.$.message.html( nodataHtml );
    } else {
        tb.$.container.removeClass('noData');
        if ( tb.mode === 'view' && tb.flag.update ) {
            tb.$.header.find('.itaButton[data-type="tableEdit"]').prop('disabled', false );
        }
        if ( tb.mode === 'diff' ) {
            tb.advanceButtonCheck( false );
        }
    }

    if ( tb.mode !== 'parameter') {
        if ( !tb.partsFlag ) {
            tb.$.tbody.html( tb.tbodyHtml() );
            tb.updateFooterStatus();
        } else {
            tb.$.tbody.html( tb.tbodyPartsHtml() );
        }
    } else {
        const body = tb.parameterBody();
        if ( body !== '') {
            tb.$.container.removeClass('noData');
            tb.$.tbody.html( body );
        } else {
            tb.$.container.addClass('noData');
            tb.$.message.html( nodataHtml );
        }
    }
    tb.$.body.scrollTop(0);
    tb.workEnd();

    tb.$.table.addClass('tableReady');

    if ( !tb.partsFlag ) {
        if ( tb.mode !== 'edit') {
            tb.tableMaxWidthCheck('tbody');
        } else {
            tb.tableInputMaxWidthCheck('tbody');
            tb.$.tbody.find('.textareaAdjustment').each( fn.textareaAdjustment );
            tb.editModeMenuCheck();
        }

        if ( ( tb.mode === 'select' && tb.params.selectType === 'multi') || tb.mode === 'edit' || tb.mode === 'view') {
            tb.checkSelectStatus();
        }

        if ( tb.option.dataType === 'n') tb.filterDownloadButtonCheck();
        tb.stickyWidth();
    }
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
   編集時　特殊入力欄の幅をチェック
##################################################
*/
tableInputMaxWidthCheck( target ) {
    const tb = this;

    const $target = ( target instanceof jQuery )? target: tb.$[ target ].find('.tableEditMultipleColmun, .tableEditInputMultipleSelectValueInner');

    $target.each(function(){
        const $culumn = ( $( this ).is('.tableEditMultipleColmun') )? $( this ).find('span'): $( this );
        const culumn = $culumn.get(0);

        if ( $culumn.is('.textOverWrap') ) {
            $culumn.css('width', 'auto').removeClass('textOverWrap');
            if ( $culumn.is('.tableEditInputMultipleSelectValueInner') ) {
                $culumn.closest('.tableEditInputMultipleSelectContainer').css('height', 'auto');
            }
        }

        if ( culumn.clientWidth < culumn.scrollWidth ) {
            $culumn.css('width', culumn.clientWidth ).addClass('textOverWrap');
            if ( $culumn.is('.tableEditInputMultipleSelectValueInner') ) {
                $culumn.closest('.tableEditInputMultipleSelectContainer').css('height', $culumn.closest('.tableEditInputMultipleSelectValue').outerHeight() );
            }
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
                if ( fn.typeof( tb.select[ tb.mode ] ) === 'array' && tb.select[ tb.mode ].length ) {
                    const selectId = tb.select[ tb.mode ].find(function( item ){
                        if ( fn.typeof( item ) === 'object') {
                            return item.id === rowId;
                        } else {
                            return item === rowId;
                        }
                    });
                    if ( selectId ) attrs['checked'] = 'checked';
                }
            } else {
                if ( tb.select[ tb.mode ].indexOf( rowId ) !== -1 ) {
                    attrs['checked'] = 'checked';
                }
            }
            // selectモード
            if ( tb.mode === 'select' || tb.mode === 'execute') {
                rowClassName.push('tBodyTrRowSelect');
                if ( tb.params.selectNameKey && fn.typeof( tb.params.selectNameKey ) !== 'array') {
                    attrs.selectname = fn.cv( rowParameter[ tb.params.selectNameKey ], '', true );
                }
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
    const buttonColumnHide = ['select', 'history'];
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
        case 'view': case 'parameter':
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
        case 'UserIDColumn': case 'NotificationIDColumn':
        case 'FilterConditionSettingColumn': case 'ConclusionEventSettingColumn':
        case 'ExecutionEnvironmentDefinitionIDColumn':
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
            if ( value !== '') {
                if ( file[ columnName ] !== null ) {
                    const attrs = [`data-id="${parameter[ tb.idNameRest ]}"`, `data-rest="${columnName}"`];
                    if ( tb.mode === 'history') attrs.push(`data-journalId="${parameter.journal_id}"`);
                    const restType = ( tb.mode !== 'history')? 'default': 'history';
                    attrs.push(`data-restType="${restType}"`);
                    const fileHtml = [`<a href="${value}" class="tableViewDownload" ${attrs.join(' ')}>${value}</a>`];
                    if ( ['text', 'image'].indexOf( fn.fileTypeCheck( value ) ) !== -1 ) {
                        fileHtml.push(`<button class="button filePreview popup" title="${getMessage.FTE00176}">${fn.html.icon('search')}</button>`);
                    }
                    return checkJournal( fileHtml.join('') );
                }
            }
            return checkJournal( value );
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

        // カラーコード
        case 'ColorCodeColumn':
            const colorCode = fn.checkHexColorCode( value );
            if ( colorCode ) {
                return ''
                + `<div class="tableColorCodeWrap">`
                    + `<span class="tableColorCodeMark" style="background-color:${colorCode}"></span>`
                    + checkJournal( colorCode )
                + `</div>`;
            } else {
                return '';
            }

        // パラメータ集用
        case 'ParameterCollectionSheetType':
            if ( value === '1') {
                return getMessage.FTE11041;
            } else if ( value === '3') {
                return getMessage.FTE11042;
            } else {
                return '';
            }

        case 'ParameterCollectionUse':
            if ( value === '1') {
                return getMessage.FTE11043;
            } else {
                return '';
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

    const
    parameter = item.parameter,
    file = item.file;

    const rowId = parameter[ tb.idNameRest ],
          columnInfo = tb.info.column_info[ columnKey ],
          columnName = fn.escape( columnInfo.column_name_rest ),
          columnType = fn.escape( columnInfo.column_type ),
          inputClassName = [],
          inputRequired = fn.cv( columnInfo.required_item, '0'),
          autoInput = '<span class="tBodyAutoInput"></span>',
          inputItem = columnInfo.input_item,
          name = `${columnName}_${columnType}_${rowId}`;

    const setValue = function( v ) {
        switch ( columnType ) {
            // JsonColumn、プルダウン選択はここでエスケープしない
            case 'JsonColumn':
            case 'IDColumn': case 'LinkIDColumn': case 'RoleIDColumn': case 'UserIDColumn':
            case 'EnvironmentIDColumn': case 'JsonIDColumn': case 'NotificationIDColumn':
            case 'ExecutionEnvironmentDefinitionIDColumn':
                return fn.cv( v, '');
            case 'FilterConditionSettingColumn': case 'ConclusionEventSettingColumn':
                if ( !tb.partsFlag ) {
                    return fn.cv( v, '', true );
                } else {
                    return fn.cv( v, '');
                }
            default:
                return fn.cv( v, '', true );
        }
    };
    let value = setValue( parameter[ columnName ] );

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
        const afterParameter = tb.edit.input[ rowId ].after.parameter[ columnName ];
        if ( afterParameter !== undefined ) {
            value = setValue( afterParameter );

            const beforeParameter = tb.edit.input[ rowId ].before.parameter[ columnName ];
            if ( afterParameter !== beforeParameter ) {
                inputClassName.push('tableEditChange');
            } else {
                if ( tb.data.fileRestNames.indexOf( columnName ) !== -1 ) {
                    // 同名ファイルの場合は変更後のファイルの存在で変更したか判断する
                    if (
                        columnName in tb.edit.input[ rowId ].after.file &&
                        tb.edit.input[ rowId ].after.file[ columnName ] !== null
                    ) {
                        inputClassName.push('tableEditChange');
                    }
                }
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
        // JsonColumn
        case 'JsonColumn':
            if ( fn.typeof( value ) === 'object' || fn.typeof( value ) === 'array') {
                value = fn.escape( fn.jsonStringify( value ) );
            } else {
                value = fn.escape( value );
            }

        // 文字列入力（単一行）
        case 'SingleTextColumn': case 'HostInsideLinkTextColumn':
        case 'TextColumn': case 'SensitiveSingleTextColumn':
            inputClassName.push('tableEditInputText');
            const widthAdjustment = ( tb.partsFlag )? {}: { widthAdjustment: true };
            return fn.html.inputText( inputClassName, value, name, attr, widthAdjustment );

        // 文字列入力（複数行）
        case 'MultiTextColumn': case 'NoteColumn': case 'SensitiveMultiTextColumn':
            inputClassName.push('tebleEditTextArea');
            const sizeChangeFlag = ( tb.partsFlag )? false: true;
            if ( tb.partsFlag ) inputClassName.push('teblePartsEditTextArea');
            return fn.html.textarea( inputClassName, value, name, attr, sizeChangeFlag );

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
        case 'EnvironmentIDColumn': case 'JsonIDColumn': case 'ExecutionEnvironmentDefinitionIDColumn': {
            const displayValue = fn.cv( value, '', true );
            const pulldownClassName = ['tableEditInputSelectValue'];
            if ( attr.disabled === 'disabled') pulldownClassName.push('tableEditInputSelectValueDisabled');
            inputClassName.push('tableEditInputSelectContainer');
            return `<div class="${inputClassName.join(' ')}">`
            + `<div class="${pulldownClassName.join(' ')}"><span class="tableEditInputSelectValueInner">${displayValue}</span></div>`
                + fn.html.select( fn.cv( tb.data.editSelectLength[ columnName ], []), 'tableEditInputSelect', value, name, attr, { select2: true } )
            + `</div>`;
        }

        // 複数選択プルダウン
        case 'NotificationIDColumn':  {
            const displayValue = fn.cv( value, '', true );
            const pulldownClassName = ['tableEditInputMultipleSelectValue'];
            if ( attr.disabled === 'disabled') pulldownClassName.push('tableEditInputSelectValueDisabled');
            value = fn.jsonParse( value, 'array');
            attr.multiple = 'multiple';
            inputClassName.push('tableEditInputMultipleSelectContainer');
            return `<div class="${inputClassName.join(' ')}">`
            + `<div class="${pulldownClassName.join(' ')}"><span class="tableEditInputMultipleSelectValueInner">${displayValue}</span></div>`
                + fn.html.select( fn.cv( tb.data.editSelectLength[ columnName ], []), 'tableEditInputSelect tableEditInputMultipleSelect', value, name, attr, { select2: true } )
            + `</div>`;
        }

        // パスワード
        case 'PasswordColumn': case 'PasswordIDColumn': case 'JsonPasswordIDColumn': case 'MaskColumn': {
            const deleteToggleFlag = ( !isNaN( rowId ) && Number( rowId ) < 0 )? false: true,
                deleteFlag = ( inputData && inputData.after.parameter[ columnName ] === null )? true: false;
            inputClassName.push('tableEditInputText');

            return fn.html.inputPassword( inputClassName, value, name, attr, { widthAdjustment: true, deleteToggle: deleteToggleFlag, deleteFlag: deleteFlag });
        }

        // ファイルアップロード
        case 'FileUploadColumn':
            inputClassName.push('tableEditSelectFile');
            return fn.html.fileSelect( value, inputClassName, attr );

        // ファイルアップロード（機器一覧：ssh秘密鍵ファイルなど）
        case 'FileUploadEncryptColumn':
            inputClassName.push('tableEditSelectFile');
            return fn.html.fileSelect( value, inputClassName, attr, false );

        // ボタン
        case 'ButtonColumn':
            return tb.buttonAction( columnInfo, item, columnKey );

        // カラーコード
        case 'ColorCodeColumn':
            inputClassName.push('tableEditSColorCode');
            return fn.html.inputColor( inputClassName, value, name, attr, { mode: 'edit'});

        // 特殊複数選択
        case 'FilterConditionSettingColumn': case 'ConclusionEventSettingColumn': {
            attr['column-type'] = columnType;
            inputClassName.push('tableEditMultipleHiddenColmun');
            const viewClassName = ['tableEditFilterCondition', 'tableEditMultipleColmun', 'input'];
            if ( inputClassName.indexOf('tableEditChange') !== -1 ) viewClassName.push('tableEditChange');
            if ( attr.disabled === 'disabled') viewClassName.push('tableEditInputSelectValueDisabled');

            // イベントフロー画面の場合はラベル表示する
            if ( !tb.partsFlag ) {
                return `<div class="${viewClassName.join(' ')}"><span>${value}</span></div>`
                + fn.html.inputHidden( inputClassName, value, name, attr );
            } else {
                return `<div class="${viewClassName.join(' ')}">${fn.html.labelListHtml( value, tb.label )}</div>`
                + fn.html.inputHidden( inputClassName, fn.escape(value), name, attr );
            }
        }

        // 不明
        default:
            return '?';
    }
}
/*
##################################################
   複数選択セレクト表示用HTML
##################################################
*/
multipleSelectDisplayHtml( list ) {
    const html = [];
    if ( fn.typeof( list ) === 'array') {
        for ( const item of list ) {
            const value = fn.cv( item, '', true );
            html.push(`<li class="tableEditInputMultipleSelectValueItem">${value}</li>`);
        }
    }
    return `<ul class="tableEditInputMultipleSelectValueList">${html.join('')}</ul>`;
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
                if ( val !== '') {
                    const fileHtml = [`<a href="${val}" class="tableViewDownload" data-type="${data}" data-id="${id}" data-rest="${columnName}">${val}</a>`];
                    if ( ['text', 'image'].indexOf( fn.fileTypeCheck( val ) ) !== -1 ) fileHtml.push(`<button class="button filePreview popup" title="${getMessage.FTE00176}">${fn.html.icon('search')}</button>`);
                    return fileHtml.join('');
                } else {
                    return '';
                }

            // カラーコード
            case 'ColorCodeColumn':
                const colorCode = fn.checkHexColorCode( val );
                if ( colorCode ) {
                    return ''
                    + `<div class="tableColorCodeWrap">`
                        + `<span class="tableColorCodeMark" style="background-color:${colorCode}"></span>`
                        + colorCode
                    + `</div>`;
                } else {
                    return '';
                }

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
            fn.storage.set('onePageNum', selectNo, 'local', false );
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
                $( window ).off('pointerdown.pagingOnePageNum');
            }
        }
    });
}
/*
##################################################
   changeEditMode
##################################################
*/
async changeEdtiMode( changeMode ) {
    const tb = this;

    // Tempデータの削除
    fn.removeDownloadTemp('duplicat_temp');
    tb.data.tempFile = {};

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
    if ( changeMode === 'changeEditRegi') {
        tb.select.edit = [];
    } else {
        tb.select.edit = tb.select.view.concat();
    }

    tb.$.container.removeClass('viewTable autoFilterStandBy initFilterStandBy');
    tb.$.container.addClass('editTable');

    // フィルタの入力を取得
    if ( !tb.partsFlag ) {
        const filterParameter = tb.getFilterParameter(),
            filterLength = Object.keys( filterParameter ).length;

        if ( ( filterLength === 1 && filterParameter.discard !== undefined )
            || filterLength === 0 ) {
            // tb.flag.initFilter = (tb.info.menu_info.initial_filter_flg === '1');
            tb.option.initSetFilter = undefined;
        } else {
            tb.option.initSetFilter = tb.getFilterParameter();
        }
    }

    if ( tb.partsFlag ) {
        tb.$.container.trigger('changePartsEditMode', tb.option.parts.id );
    }

    // 編集から戻った際はinitial_filter_flgに関係なく表示
    tb.flag.initFilter = true;

    // セレクトデータを取得後に表示する
    fn.fetch( tb.rest.inputPulldown ).then(function( result ){

        // 選択項目
        tb.data.editSelect = result;

        // 配列に変換
        tb.data.editSelectArray = {};
        tb.data.editSelectLength = {};
        for ( const restName in result ) {
            tb.data.editSelectArray[ restName ] = [];
            for ( const id in result[ restName ] ) {
                const data = result[ restName ][ id ];
                if ( fn.typeof ( data ) === 'object') continue;
                tb.data.editSelectArray[ restName ].push( result[ restName ][ id ] );
            }
            // ソート
            tb.data.editSelectArray[ restName ].sort( tb.pulldownSort );

            // バイト数の多い順に並べる
            tb.data.editSelectLength[ restName ] = $.extend( true, [], tb.data.editSelectArray[ restName ] );
            tb.data.editSelectLength[ restName ].sort(function( a, b ) {
                return encodeURIComponent(b).replace(/%../g, 'x').length - encodeURIComponent(a).replace(/%../g, 'x').length;
            });
            tb.data.editSelectLength[ restName ] = tb.data.editSelectLength[ restName ].slice( 0, 5 );
        }


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
            const selectTarget = ['IDColumn', 'LinkIDColumn', 'AppIDColumn', 'RoleIDColumn', 'JsonIDColumn', 'UserIDColumn', 'NotificationIDColumn', 'ExecutionEnvironmentDefinitionIDColumn'];
            if ( selectTarget.indexOf( columnInfo.column_type ) !== -1
              && columnInfo.required_item === '1'
              && columnInfo.initial_value === null ) {
                const select = tb.data.editSelectArray[ columnInfo.column_name_rest ];
                if ( select !== undefined ) {
                    if ( columnInfo.column_type === 'NotificationIDColumn') {
                        tb.edit.blank.parameter[ columnInfo.column_name_rest ] = fn.jsonStringify([select[0]]);
                    } else {
                        tb.edit.blank.parameter[ columnInfo.column_name_rest ] = select[0];
                    }
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
                case 'changeEditDup': {
                    const addId = String( tb.edit.addId-- );
                    const targetId = tb.select.edit[0];
                    tb.select.edit = [ addId ];
                    tb.workerPost('changeEditDup', { target: [ targetId ], id: addId });
                } break;
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
   プルダウン項目のソート
##################################################
*/
pulldownSort( a, b ) {
    let paramA = fn.cv( a, ''),
        paramB = fn.cv( b, '');

    if ( fn.typeof( paramA ) === 'object' ||  fn.typeof( paramA ) === 'array' ||
            fn.typeof( paramB ) === 'object' ||  fn.typeof( paramB ) === 'array') {
        try {
            paramA = ( paramA !== '')? JSON.stringify( paramA ): '';
            paramB = ( paramB !== '')? JSON.stringify( paramB ): '';
        } catch ( error ) {
            paramA = '';
            paramB = '';
            console.warn('JSON.stringify error');
        }
    } else {
        if ( !isNaN( paramA ) && !isNaN( paramB ) ) {
            paramA = Number( paramA );
            paramB = Number( paramB );
        } else {
            paramA = String( paramA );
            paramB = String( paramB );
        }
    }

    if ( paramA < paramB ) {
        return -1;
    } else if ( paramA > paramB ) {
        return 1;
    } else {
        return 0;
    }
}
/*
##################################################
   changeViewMode
##################################################
*/
changeViewMode() {
    const tb = this;

    // Tempデータの削除
    fn.removeDownloadTemp('duplicat_temp');
    tb.data.tempFile = {};

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

    if ( tb.partsFlag ) {
        tb.$.container.trigger('changePartsViewMode', tb.option.parts.id );
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

    return new Promise(function( resolve ){
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

        let
        modalTable = new DataTable('DT', 'diff', tb.info, tb.params, diffData ),
        modal = new Dialog( config );

        modal.open( modalTable.setup() );

        // カラムキー
        tb.data.regiColumnKeys = modalTable.data.columnKeys;

        const end = function(){
            modalTable.worker.terminate();
            modal = null;
            modalTable = null;
        };

        // メニューボタン
        modalTable.$.header.find('.itaButton').on('click', function(){
            if ( !tb.checkWork ) {
                const $button = $( this ),
                    type = $button.attr('data-type');
                switch ( type ) {
                    // 編集反映
                    case 'tableOk':
                        $button.prop('disabled', true );
                        modalTable.workStart('table', 0 );
                        tb.editOk.call( tb ).then(function( result ){
                            modal.close().then( function(){
                                end();
                                fn.resultModal( result ).then(function(){
                                    // Session Timeoutの設定を戻す
                                    if ( fn.getCmmonAuthFlag() ) {
                                        CommonAuth.tokenRefreshPermanently( false );
                                    } else if ( window.parent && window.parent.tokenRefreshPermanently ) {
                                        window.parent.tokenRefreshPermanently( false );
                                    }

                                    tb.changeViewMode.call( tb );
                                    resolve();
                                });
                            });
                        }).catch(function( result ){
                            modal.close().then( function(){
                                end();
                                if ( result !== null ) {
                                    tb.editError( result );
                                }
                                resolve();
                            });
                        });
                    break;
                    case 'tableCancel':
                        modal.close();
                        end();
                        resolve();
                    break;
                    case 'tableChangeValue':
                        modalTable.$.container.toggleClass('tableShowChangeValue');
                        modalTable.tableMaxWidthCheck.call( modalTable, 'tbody');
                    break;
                }
            }
        });
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
            if ( !tb.data.regiColumnKeys ) tb.data.regiColumnKeys = tb.data.columnKeys;

            for ( const columnKey of tb.data.regiColumnKeys ) {
                const columnNameRest = info[ columnKey ].column_name_rest,
                      columnType = info[ columnKey ].column_type;

                // ファイルがフォームデータではない場合は変換する
                const fileCheck = function( file ) {
                    if ( fn.typeof( file ) === 'file') {
                        return file;
                    } else if ( fn.typeof( file ) === 'string') {
                        return fn.base64ToFile( file );
                    } else {
                        return null;
                    }
                };

                // 入力済みがあるか？
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

                            const fileAfterValue = item.after.parameter[ columnNameRest ];
                            if ( ( fileAfterValue !== undefined && fileAfterValue !== '') || itemData.type === 'Register'){
                                itemData.file[ columnNameRest ] = fileCheck( setData('file') );
                            }
                        break;
                        // File（機器一覧：ssh秘密鍵ファイルなど）
                        case 'FileUploadEncryptColumn': {
                            const fileAfterValue = item.after.parameter[ columnNameRest ];
                            // 変更があるか？（更新時、変更がなければ値をセットしない）
                            if ( fileAfterValue !== undefined && fileAfterValue !== '') {
                                itemData.parameter[ columnNameRest ] = setData('parameter');
                                // nullじゃなければファイルもセット
                                if ( fileAfterValue !== null ) {
                                    itemData.file[ columnNameRest ] = setData('file');
                                }
                                // { key: null } の場合は削除とする
                            } else if ( itemData.type === 'Register') {
                                // 登録時（複製時など）
                                const
                                name = setData('parameter'),
                                file = fileCheck( setData('file') );
                                if ( name && file ) {
                                    itemData.parameter[ columnNameRest ] = name;
                                    itemData.file[ columnNameRest ] = file;
                                }
                            }
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
                            } else if ( passwordAfterValue !== '' && passwordAfterValue !== null && passwordAfterValue !== undefined ){
                                // 値有 -> 更新 { key: value }
                                itemData.parameter[ columnNameRest ] = passwordAfterValue;
                            } else if ( itemData.type === 'Register') {
                                // 登録時（複製時など）
                                const password = setData('parameter');
                                if ( password ) itemData.parameter[ columnNameRest ] = password;
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

    // パラメータとファイルを分ける
    const
    formData = new FormData(),
    editDataParam = [],
    paramLength = editData.length;

    for ( let i = 0; i < paramLength; i++ ) {
        const item = editData[i];
        // パラメータ
        editDataParam.push({
            parameter: item.parameter,
            type: item.type
        });

        // ファイルをFormDataに追加
        // Parameter No. + . + Rest Name Key
        for ( const key in item.file ) {
            if ( item.parameter[ key ] !== undefined && item.parameter[ key ] !== null ) {
                formData.append(`${i}.${key}`, item.file[ key ] );
            }
        }
    }

    // パラメータをFormDataに追加
    formData.append('json_parameters', fn.jsonStringify( editDataParam ) );

    return new Promise(async function( resolve, reject ){
        // アップロードの間はSession Timeoutしないように設定
        if ( fn.getCmmonAuthFlag() ) {
            CommonAuth.tokenRefreshPermanently( true );
        } else if ( window.parent && window.parent.tokenRefreshPermanently ) {
            window.parent.tokenRefreshPermanently( true );
        }

        // トークンを強制リフレッシュ
        try {
            if ( fn.getCmmonAuthFlag() ) {
                await CommonAuth.refreshTokenForce();
            } else if ( window.parent && window.parent.refreshTokenForce ) {
                await window.parent.refreshTokenForce();
            }
        } catch ( e ) {
            window.console.error( error );
            if ( error.message ) alert( error.message );
            reject( null );
            return;
        }

        fn.xhr( tb.rest.maintenance, formData )
            .then(function( result ){
                resolve( result );
            })
            .catch(function( result ){
                if ( fn.typeof( result ) === 'object') {
                    if ( result.result && result.result.match(/^498/) ) {
                        if ( fn.typeof( result.message ) === 'string') alert( result.message );
                        reject( null );
                    } else {
                        result.data = editData;
                        reject( result );
                        //バリデーションエラー
                        alert(getMessage.FTE00068);
                    }
                } else {
                    reject( null );
                }
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

    return new Promise(function( resolve ){

        const dryrunText = ( tb.driver === 'ansible')? getMessage.FTE00006: getMessage.FTE00167;

        const setConfig = function() {
            switch ( type ) {
                case 'run':
                    return {
                        title: getMessage.FTE00005,
                        rest: `/menu/${tb.params.menuNameRest}/driver/execute/`
                    };
                case 'dryrun':
                    return {
                        title: dryrunText,
                        rest: `/menu/${tb.params.menuNameRest}/driver/execute_dry_run/`
                    };
                case 'parameter':
                    return {
                        title: getMessage.FTE00007,
                        rest: `/menu/${tb.params.menuNameRest}/driver/execute_check_parameter/`
                    };
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
                    tb.workEnd();
                    resolve();
                });
            } else {
                tb.workEnd();
                resolve();
            }
        });
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
        console.error( e );
        //JSONを作成
        if ( !errorMessage ) errorMessage = [];
        if ( !errorMessage['0'] ) errorMessage['0'] = [];
        errorMessage['0'][ getMessage.FTE00064 ] = error.message;
    }

    const errorHtml = [];

    for ( const item in errorMessage ) {
        for ( const error in errorMessage[item] ) {
            const name = fn.cv( tb.data.restNames[ error ], error, true );
            const message = ( fn.typeof( errorMessage[item][error] ) === 'array')? errorMessage[item][error].join(''): errorMessage[item][error];
            let   body = fn.cv( message, '?', true );

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
        console.error( e );
        //JSONを作成
        let key = getMessage.FTE00064;
        errorMessage = {
            '0': {}
        };
        errorMessage['0'][key] = error.message;
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
            const errorArray = errorMessage[item][error];

            if ( fn.typeof( errorArray ) === 'array') {
                for ( const errorText of errorArray ) {
                    let body = fn.cv( errorText, '?', true );
                    body = body.replace(/\r?\n/g, '<br>');

                    // 編集項目か否か
                    if ( param[item] !== null ) {
                        editRowNum = param[item];
                        errorHtml.push(`<tr class="tBodyTr tr">`
                            + (( tb.partsFlag )? ``: fn.html.cell( auto_input, ['tBodyTh', 'tBodyLeftSticky'], 'th') )
                            + (( tb.partsFlag )? ``: fn.html.cell( editRowNum, ['tBodyTh', 'tBodyErrorId'], 'th') )
                            + fn.html.cell( name, 'tBodyTh', 'th')
                            + fn.html.cell( body, 'tBodyTd')
                        + `</tr>`);
                    } else {
                        editRowNum = '<span class="tBodyAutoInput"></span>';
                        errorHtml.push(`<tr class="tBodyTr tr">`
                            + (( tb.partsFlag )? ``:fn.html.cell( newRowNum + 1, ['tBodyTh', 'tBodyLeftSticky'], 'th') )
                            + (( tb.partsFlag )? ``:fn.html.cell( editRowNum, ['tBodyTh', 'tBodyErrorId'], 'th') )
                            + fn.html.cell( name, 'tBodyTh', 'th')
                            + fn.html.cell( body, 'tBodyTd')
                        + `</tr>`);
                    }
                }
            }
        }
    }

    tb.$.container.addClass('tableError');

    const errorTable = ``
    + `<table class="table errorTable">`
        + `<thead class="thead">`
            + `<tr class="tHeadTr tr">`
                + (( tb.partsFlag )? ``:`<th class="tHeadTh tHeadLeftSticky th"><div class="ci">${getMessage.FTE00069}</div></th>`)
                + (( tb.partsFlag )? ``:`<th class="tHeadTh tHeadLeftSticky th"><div class="ci">${id_name}</div></th>`)
                + `<th class="tHeadTh th tHeadErrorColumn"><div class="ci">${getMessage.FTE00070}</div></th>`
                + `<th class="tHeadTh th tHeadErrorBody"><div class="ci">${getMessage.FTE00071}</div></th>`
            + `</tr>`
        + `</thead>`
        + `<tbody class="tbody">`
            + errorHtml.join('')
        + `</tbody>`
    + `</table>`;

    if ( tb.partsFlag ) {
        return errorTable;
    } else {
        tb.$.errorMessage.html(`<div class="errorBorder"></div>`
        + `<div class="errorTableContainer">`
            + `<div class="errorTitle"><span class="errorTitleInner">${fn.html.icon('circle_exclamation')}` + getMessage.FTE00065 + `</span></div>`
            + errorTable
        + `</div>`);
    }
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
    if ( tb.mode !== 'parameter') {
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
    } else {
        if ( key === 'direction') {
            if ( tb.option.parameterDirection ) {
                return tb.option.parameterDirection;
            } else {
                return 'vertical';
            }
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

    return new Promise(function( resolve ){
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

        tb.saveTableSetting().then(function(){
            resolve();
        });
    });
}
/*
##################################################
   テーブル設定更新 ＞ 再表示
##################################################
*/
saveTableSetting() {
    const tb = this;

    return new Promise(function( resolve ){
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
            }).catch(function( error ){
                if ( fn.typeof( error ) === 'object') {
                    if ( fn.typeof( error.message ) === 'string') alert( error.message );
                } else {
                    fn.alert( getMessage.FTE10092, getMessage.FTE10093 );
                }
            }).then(function(){
                process.close();
                resolve();
            });
        } else {
            // session storageの取得に失敗した場合はエラー
            fn.alert( getMessage.FTE10092, getMessage.FTE10093 );
            resolve();
        }
    });
}
/*
##################################################
   テーブル設定モーダルを開く
##################################################
*/
tableSettingOpen() {
    const tb = this;

    return new Promise(function( resolve ){

        if ( !tb.tableSettingModal ) tb.tableSettingModal = {};

        // モーダルOK、キャンセル
        const funcs = {
            ok: function() {
                tb.tableSettingOk().then(function(){
                    tb.tableSettingModal[ tb.tableMode ].hide();
                    resolve();
                });
            },
            cancel: function() {
                tb.tableSettingModal[ tb.tableMode ].hide();
                resolve();
            },
            reset: function() {
                tb.tableSettingReset().then(function(){
                    tb.tableSettingModal[ tb.tableMode ].close();
                    tb.tableSettingModal[ tb.tableMode ] = null;
                    resolve();
                });
            }
        };

        if ( tb.tableSettingModal[ tb.tableMode ] ) {
            tb.tableSettingModal[ tb.tableMode ].btnFn = funcs;
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
                    if ( !tb.option.data ) {
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

            tb.tableSettingGroupCheck();
            tb.tableSettingEvents();
            fn.commonTab( tb.tableSettingModal[ tb.tableMode ].$.dbody.find(`.commonTab`) );
        }
    });
}
/*
##################################################
   テーブル設定リセット
##################################################
*/
tableSettingReset() {
    const tb = this;

    return new Promise(function( resolve ){
        tb.tableSetting.individual[ tb.tableMode ] = {
            check: {},
            color: {}
        };

        tb.saveTableSetting().then(function(){
            resolve();
        });
    });
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
   グループチェック状態を確認
##################################################
*/
tableSettingGroupCheck() {
    const tb = this;

    const $dBody = tb.tableSettingModal[ tb.tableMode ].$.dbody;
    $dBody.find('.tableSettingCheckGroup:checked').each(function(){
        const
        $checkGroup = $( this ),
        $checkWrap = $checkGroup.closest('.checkboxTextWrap'),
        $unchecked = $checkGroup.closest('.tableSettingItemName').next('.tableSettingList').find('.tableSettingCheckItem').not(':checked');

        if ( $unchecked.length ) $checkWrap.addClass('checkboxTextOneOrMore');
    });
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
                $check.add( $checks ).prop('checked', checked );
            } else {
                $checks.prop('checked', checked );
            }

            $wrap.add( $parent.find('.checkboxTextOneOrMore') ).removeClass('checkboxTextOneOrMore');

            if ( !checked ) {
                // グループのチェック状態を確認
                $wrap.add( $parent.find('.checkboxTextWrap') ).find('.tableSettingCheckGroup').each(function(){
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
//   複数項目選択カラム（OASE）
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
   複数選択項目設定モーダルを開く
##################################################
*/
multipleColmunSetting( columnType, restName, value, required ) {
    const tb = this;

    return new Promise(function( resolve ){
        // プルダウンセレクトリスト
        const multipleList = tb.data.editSelect[ restName ];

        // 配列に変換
        const multipleArray = [];
        for ( const key in multipleList ) {
            if ( fn.typeof(multipleList[key]) === 'string' ) {
                multipleArray.push( multipleList[key] );
            } else {
                multipleArray[key] = [];
                for ( const id in multipleList[key]) {
                    multipleArray[key].push(multipleList[key][id]);
                }
            }
        }

        const settingData = tb.columnTypeSettingData( columnType, multipleArray );
        settingData.values = fn.jsonParse( value, 'array');
        settingData.required = required;
        settingData.escape = true;

        fn.settingListModalOpen( settingData ).then(function( result ){
            if ( result !== 'cancel') {
                resolve( result )
            } else {
                resolve( null );
            }
        });
    });
}
/*
##################################################
   カラムタイプごとの設定
##################################################
*/
columnTypeSettingData( columnType, list ) {
    switch ( columnType ) {
        case 'FilterConditionSettingColumn':
            return {
                title: getMessage.FTE13001,
                width: '960px',
                move: false,
                info: [
                    {
                        id: 'label_name',
                        type: 'select',
                        title: getMessage.FTE13002,
                        list: list.label_name,
                        width: '360px',
                    },
                    {
                        id: 'condition_type',
                        type: 'select',
                        title: getMessage.FTE13003,
                        list: list.condition_type,
                        width: '80px',
                    },
                    {
                        id: 'condition_value',
                        type: 'text',
                        title: getMessage.FTE13004,
                        required: true
                    },
                ]
            };
        case 'ConclusionEventSettingColumn':
            return {
                title: getMessage.FTE13005,
                width: '808px',
                move: false,
                info: [
                    {
                        id: 'conclusion_label_name',
                        type: 'select',
                        title: getMessage.FTE13006,
                        list: list,
                        width: '360px',
                    },
                    {
                        id: 'conclusion_label_value',
                        type: 'text',
                        title: getMessage.FTE13007,
                        required: true
                    },
                ]
            };
    }
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   パラメーター集
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
   parameter table html
##################################################
*/
parameterTableHtml() {
    const tb = this;

    return ``
    + `<thead class="thead">`
    + `</thead>`
    + `<tbody class="tbody"></tbody>`;
}
/*
##################################################
   tbody
##################################################
*/
parameterBody() {
    const tb = this,
    list = tb.data.body;

    const html = [];

    list.sort(function( a, b ){
        a = String( fn.cv( a.parameter.input_order, 0 ) );
        b = String( fn.cv( b.parameter.input_order, 0 ) );
        return a.localeCompare( b );
    });

    const listName = ( tb.option.parameterMode === 'host')? 'parameterOperationList': 'parameterHostList',
          nameKey = ( tb.option.parameterMode === 'host')? 'operation_name_disp': 'host_name';

    const length = tb.option[ listName ].length;
    if ( tb.option.parameterMode === 'host' && length > 1 ) {
        tb.option[ listName ].sort(function( a, b ){
            return a.date.localeCompare( b.date );
        });
    }
    for ( let i = 0; i < length; i++ ) {
        // オペレーション名 or ホスト名
        const parameter = fn.cv( tb.option[ listName ][i].name, '');

        const rows = [];
        let rowspan = 0;

        for ( const item of list ) {
            // 対象が一致するものを表示
            if (
                ( item.parameter[ nameKey ] === parameter ) ||
                // ホスト無しを表示
                (
                    tb.option.parameterSheetType === '3' // オペレーションのみ
                    && tb.option.operationNoHost === true // ホスト無しを表示フラグ
                    && tb.option.parameterMode === 'operation' // オペレーションモード
                    && i + 1 === length // 配列の最後
                )
            ) {
                const rowHtml = [];
                if ( tb.menuMode === 'bundle') {
                    rowHtml.push( fn.html.cell( item.parameter.input_order, 'tBodyTd', 'td') );
                }
                for ( const columnKey of tb.data.columnKeys ) {
                    rowHtml.push( tb.cellHtml( item, columnKey ) );
                }
                rows.push( rowHtml );
                rowspan++;
            }
        }

        // 登録がない場合空行を追加する
        if ( !rows[0] ) {
            const rowHtml = [];
            const cell = fn.html.cell('', 'parameterBlankTd tBodyTd', 'td');
            if ( tb.menuMode === 'bundle') {
                rowHtml.push( cell );
            }
            for ( const columnKey of tb.data.columnKeys ) {
                rowHtml.push( cell );
            }
            rows.push( rowHtml );
            rowspan++;
        }

        // タイトル
        const parameterClass = ['parameterTh', 'tBodyLeftSticky', 'tBodyTh', 'parameterMainTh' + i ];
        if ( i === length - 1 ) parameterClass.push('parameterLast');
        const parameterName = fn.escape( parameter );
        const parameterTitle = ( tb.option.parameterMode === 'host')?
            `${parameterName}<div class="parameterThOperationDate"><span>\n</span>${fn.cv( tb.option[ listName ][i].date, '', true )}</div>`:
            parameterName;
        rows[0].unshift( fn.html.cell( parameterTitle, parameterClass.join(' '), 'th', rowspan ) );

        const rowsLength = rows.length;
        for ( let j = 0; j < rowsLength; j++ ) {
            const rowClass = ['tBodyTr'];
            if ( j === rowsLength - 1 ) rowClass.push('parameterSeparateTr')
            html.push( fn.html.row( rows[j].join(''), rowClass.join(' ')) );
        }
    }
    return html.join('');
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
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   パーツ管理テーブル
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
   Parts table
##################################################
*/
setPartsTable( mode ) {
    const tb = this;
    tb.mode = mode;

    tb.$.container.attr('table-mode', tb.tableMode );

    // メニュー
    tb.$.thead.find('.eventFlowPartsBlockMenu').html( tb.partsBlockMenuHtml() );
    tb.$.container.find('.eventFlowPartsBlockBody').html('<div class="eventFlowPartsBlockBodyInner"></div>');

    tb.$.tbody = tb.$.container.find('.eventFlowPartsBlockBodyInner');

    if ( tb.mode === 'view') {
        // メニューボタン
        tb.$.container.find('.eventFlowPartsBlockMenuButton').on('click', function(){
            if ( !tb.checkWork ) {
                const $button = $( this ),
                    type = $button.attr('data-type');
                switch ( type ) {
                    // 追加
                    case 'tableNew':
                        tb.changeEdtiMode.call( tb, 'changeEditRegi');
                        $button.closest('.eventFlowPartsBlock').removeClass('eventFlowPartsTableClose');
                    break;
                    // 開閉
                    case 'tableToggle':
                        $button.closest('.eventFlowPartsBlock').toggleClass('eventFlowPartsTableClose');
                    break
                }
            }
        });
        // パーツメニューボタン
        tb.$.tbody.on('click', '.eventFlowPartsMenuButton', function(){
            if ( !tb.checkWork ) {
                const
                $button = $( this ),
                type = $button.attr('data-type'),
                itemId = $button.attr('data-id');

                tb.select.view = [ itemId ];

                switch ( type ) {
                    // 追加
                    case 'tableEdit':
                        tb.changeEdtiMode.call( tb );
                    break;
                    // 開閉
                    case 'tableToggle':
                        $button.closest('.eventFlowPartsItem').toggleClass('eventFlowPartsItemOpen');
                    break
                }
            }
        });
        tb.requestTbody();
    } else if ( tb.mode === 'edit') {
        // メニューボタン
        tb.$.container.find('.eventFlowPartsBlockMenuButton').on('click', function(){
            if ( tb.flag.dragAndDrop === true ) return;
            if ( !tb.checkWork ) {
                const $button = $( this ),
                    type = $button.attr('data-type');
                switch ( type ) {
                    // 登録
                    case 'tableOk':
                        $button.prop('disabled', true );
                        tb.workStart('table', 0 );
                        tb.editOk.call( tb ).then(function( result ){
                            fn.resultModal( result ).then(function(){
                                // Session Timeoutの設定を戻す
                                if ( fn.getCmmonAuthFlag() ) {
                                    CommonAuth.tokenRefreshPermanently( false );
                                } else if ( window.parent && window.parent.tokenRefreshPermanently ) {
                                    window.parent.tokenRefreshPermanently( false );
                                }

                                tb.workEnd();
                                tb.changeViewMode.call( tb );
                            });
                        }).catch(function( result ){
                            if ( result !== null ) {
                                tb.partsEditError( getMessage.FTE00065, tb.editError( result ) ).then(function(){
                                    tb.workEnd();
                                });
                            }
                        });
                    break;
                    // キャンセル
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
                }
            }
        });
        tb.workerPost('edit', tb.select.view );
    }

    // Table内各種イベントセット
    tb.setTableEvents();
}
/*
##################################################
   Body HTML
##################################################
*/
tbodyPartsHtml() {
    const tb = this;

    const html = [];

    if ( tb.mode === 'view') {
        const
        list = tb.data.body,
        parts = tb.option.parts;

        if ( list.length ) {
            for ( const item of list ) {
                html.push( tb.partsItemHtml( parts.id, parts.name, parts.partsRestId, parts.partsRestName, item ) );
            }
            return tb.partsListHtml( html.join('') );
        } else {
            const name = fn.cv( parts.name, '', true );
            return `<div class="eventFlowPartsNoDate"><div class="eventFlowPartsNoDateInner">${getMessage.FTE13018(name)}</div></div>`;
        }
    } else if ( tb.mode === 'edit') {
        //
        const
        itemData = tb.data.body[0],
        columnInfo = tb.info.column_info,
        groupInfo = tb.info.column_group_info;

        const displayNone = [ tb.idNameRest, 'discard', 'last_update_date_time', 'last_updated_user'];

        const editTable = function( list ){
            for ( const columnKey of list ) {
                const
                type = columnKey.slice(0,1);
                if ( type === 'c') {
                    const column = columnInfo[columnKey];
                    if ( displayNone.indexOf( columnInfo[columnKey].column_name_rest ) !== -1 ) continue;
                    let columnName = fn.cv( columnInfo[columnKey].column_name, '', true );
                    // 必須
                    if ( tb.mode === 'edit' && columnInfo[columnKey].required_item === '1') {
                        columnName += `<span class="partsRquired">*</span>`;
                    }
                    const attr = {};
                    if ( column.column_name_rest ) attr.rest = column.column_name_rest;
                    if ( column.description ) attr.title = fn.cv( column.description, '', true );

                    if ( column.column_name_rest === 'conclusion_label_settings' || column.column_name_rest === 'filter_condition_json') {
                        html.push( fn.html.row( fn.html.cell( columnName, 'tHeadTh popup popupScroll', 'th', 1, 1, attr) + fn.html.cell('', 'blankTd', 'td') ) );
                        html.push( fn.html.row( tb.cellPartsHtml( itemData, columnKey, 2 ) ) );
                    } else {
                        html.push( fn.html.row( fn.html.cell( columnName, 'tHeadTh popup popupScroll', 'th', 1, 1, attr) + tb.cellPartsHtml( itemData, columnKey ) ) );
                    }
                } else {
                    const groupName = fn.cv( groupInfo[columnKey].column_group_name, '', true );
                    html.push( fn.html.row( fn.html.cell( groupName, 'tHeadGroup tHeadTh', 'th', 1, 2 ) ) );

                    html.push('<tr><td class="eventFlowPartsTableGroupTd" colspan="2"><table class="eventFlowPartsTable eventFlowPartsGroupTable"><tbody>');
                    editTable( groupInfo[columnKey].columns_view);
                    html.push('</tbody></table></td></tr>');
                }
            }
        };
        html.push('<div class="eventFlowPartsTableWrap"><table class="eventFlowPartsTable"><tbody>');
        editTable( tb.info.menu_info.columns_view );
        html.push('</tbody></table></div>');

        return html.join('');
    }
}
/*
##################################################
   Cell HTML
##################################################
*/
cellPartsHtml( item, columnKey, colspan = 1 ) {
    const tb = this;

    const columnInfo = tb.info.column_info[ columnKey ],
          columnName = columnInfo.column_name_rest,
          columnType = columnInfo.column_type;

    const className = [];
    if ( columnType === 'NumColumn') className.push('tBodyTdNumber');
    if ( columnName === 'discard') className.push('tBodyTdMark discardCell');

    switch ( tb.mode ) {
        case 'view':
            if ( columnInfo.column_type === 'ButtonColumn') {
                className.push('tBodyTdButton');
            }
            return fn.html.cell( tb.viewCellHtml( item, columnKey ), className, 'td');
        case 'edit':
            if ( ( columnName !== 'discard' && item.discard === '1' ) && columnName !== 'remarks' ) {
                return fn.html.cell( tb.viewCellHtml( item, columnKey ), className, 'td', 1, colspan );
            } else {
                className.push('tBodyTdInput');
                return fn.html.cell( tb.editCellHtml( item, columnKey ), className, 'td', 1, colspan );
            }
    }
}
/*
##################################################
  パーツブロックHTML
##################################################
*/
partsBlockHtml( type ) {
    const tb = this;

    const name = fn.cv( tb.option.parts.className, '', true );
    return ``
    + `<div class="eventFlowPartsTableBlock eventFlowPartsTableBlock${name}">`
        + `<div class="eventFlowPartsBlockHeader">`
            + `<div class="eventFlowPartsBlockName">${name}</div>`
            + `<div class="eventFlowPartsBlockMenu"></div>`
        + `</div>`
        + `<div class="eventFlowPartsBlockBody">`
        + `</div>`
    + `</div>`;
}
/*
##################################################
  パーツブロックメニューHTML
##################################################
*/
partsBlockMenuHtml() {
    const tb = this;

    const html = [`<ul class="eventFlowPartsBlockMenuList">`];
    if ( tb.mode === 'view') {
        html.push( tb.partsBlockMenuItemHtml('tableNew', 'plus') );
        html.push( tb.partsBlockMenuItemHtml('tableToggle', 'arrow02_top') );
    } else if ( tb.mode === 'edit') {
        html.push( tb.partsBlockMenuItemHtml('tableOk', 'download', true ) );
        html.push( tb.partsBlockMenuItemHtml('tableCancel', 'cross') );
    }
    html.push(`</ul>`);

    return html.join('');
}
/*
##################################################
  パーツブロックメニューアイテムHTML
##################################################
*/
partsBlockMenuItemHtml( type, icon, disabledFlag = false ) {
    const disabled = ( disabledFlag )? ' disabled="disabled"': '';
    return `<li class="eventFlowPartsBlockMenuItem">`
        + `<button class="eventFlowPartsBlockMenuButton" data-type="${type}"${disabled}><span class="icon icon-${icon}"></span></button>`
    + `</li>`;
}
/*
##################################################
  パーツリストHTML
##################################################
*/
partsListHtml( items ) {
    return `<ul class="eventFlowPartsList">${items}</ul>`;
}
/*
##################################################
  パーツアイテムHTML
##################################################
*/
partsItemHtml( type, name, idRest, nameRest, item ) {
    const tb = this;

    const parameter = item.parameter;

    const
    partsName = fn.cv( parameter[nameRest], '', true ),
    partsId = fn.cv( parameter[idRest], '', true ),
    flag = fn.cv( parameter.available_flag, '', true );

    return ``
    + `<li class="eventFlowPartsItem eventFlowParts${name}" data-available-flag="${flag}" data-id="${partsId}">`
        + `<div class="eventFlowPartsHeader">`
            + `<div class="eventFlowPartsName"><span class="eventFlowPartsNameText">${partsName}</span></div>`
            + `<div class="eventFlowPartsMenu">${tb.partsMenuHtml( partsId )}</div>`
        + `</div>`
        + `<div class="eventFlowPartsBody">`
            + tb.partsBodyHtml( type, parameter )
        + `</div>`
    + `</li>`;
}
/*
##################################################
  パーツメニューHTML
##################################################
*/
partsMenuHtml( id ) {
    const tb = this;

    const html = [];
    html.push( tb.partsMenuItemHtml('tableEdit', 'edit', id ) );
    html.push( tb.partsMenuItemHtml('tableToggle', 'arrow02_bottom') );

    return `<ul class="eventFlowPartsMenuList">${html.join('')}</ul>`;
}
/*
##################################################
  パーツメニューアイテムHTML
##################################################
*/
partsMenuItemHtml( type, icon, id ) {
    const attr = [];
    if ( type ) attr.push(`data-type="${type}"`);
    if ( id ) attr.push(`data-id="${id}"`);
    return `<li class="eventFlowPartsMenuItem">`
        + `<button class="eventFlowPartsMenuButton" ${attr.join(' ')}><span class="icon icon-${icon}"></span></button>`
    + `</li>`;
}
/*
##################################################
  パーツボディHTML
##################################################
*/
partsBodyHtml( type, parameter ) {
    switch ( type ) {
        case 'filter':
            return `<div class="eventFlowPartsInfo">${this.partsFilterHtml( parameter )}</div>`;
        case 'action':
            return `<div class="eventFlowPartsInfo">${this.partsActionHtml( parameter )}</div>`;
        case 'rule':
            return `<div class="eventFlowPartsInfo">${this.partsRuleHtml( parameter )}</div>`;
        default:
            return `<div class="eventFlowPartsInfo"></div>`;
    }
}
/*
##################################################
  フィルターHTML
##################################################
*/
partsFilterHtml( parameter ) {
    const labelList = parameter.filter_condition_json;
    return fn.html.labelListHtml( labelList, this.label );
}
/*
##################################################
  アクションHTML
##################################################
*/
partsActionHtml( parameter ) {
    const
    conductor = fn.cv( parameter.conductor_class_id, '', true ),
    operation = fn.cv( parameter.operation_id, '', true );
    return `<div class="eventFlowPartsActionTableWrap"><table class="eventFlowPartsActionTable">`
        + `<tr><th class="eventFlowPartsActionTh">Conductor</th><td class="eventFlowPartsActionTd">${conductor}</td></tr>`
        + `<tr><th class="eventFlowPartsActionTh">Operation</th><td class="eventFlowPartsActionTd">${operation}</td></tr>`
    + `</table></div>`;
}
/*
##################################################
  ルールHTML
##################################################
*/
partsRuleHtml( parameter ) {
    const tb = this;

    const
    filterA = fn.cv( parameter.filter_a, '', true ),
    filterB = fn.cv( parameter.filter_b, null, true ),
    operator = fn.cv( parameter.filter_operator, null, true ),
    actionName = fn.cv( parameter.action_id, null, true ),
    labels = fn.cv( parameter.conclusion_label_settings, null );

    const html = [];

    // Filter
    const filterHtml = [];
    let filterAddClass = null;
    if ( filterB ) {
        filterHtml.push( tb.partsRuleListHtml('Filters', '<span class="filtersNum">A</span>' + filterA ) );
        filterHtml.push(`<div class="eventFlowPartsRuleOperator">${operator}</div>`);
        filterHtml.push( tb.partsRuleListHtml('Filters', '<span class="filtersNum">B</span>' + filterB ) );
        filterAddClass = 'eventFlowPartsRuleOperatorMode';
    } else {
        filterHtml.push( tb.partsRuleListHtml('Filter', filterA ) );
    }

    html.push( tb.partsRuleBlockHtml('Filter', filterHtml.join(''), filterAddClass ) );

    // Action
    if ( actionName ) {
        const actionHtml = tb.partsRuleListHtml('Action', actionName );
        html.push( tb.partsRuleBlockHtml('Action', actionHtml ) );
    }

    // 再評価Label
    if ( labels ) {
        const ruleLabelName = fn.cv( parameter.rule_label_name, null, true );

        const listHtml = fn.html.labelListHtml( labels, tb.label );

        const ruleHtml = ``
        + `<div class="eventFlowPartsRuleCnclusion">`
            + `<div class="eventFlowPartsHeader">`
                + `<div class="eventFlowPartsName"><span class="eventFlowPartsNameText">${ruleLabelName}</span></div>`
            + `</div>`
            + `<div class="eventFlowPartsBody">`
                + listHtml
            + `</div>`
        + `</div>`;

        html.push( tb.partsRuleBlockHtml('Label', ruleHtml ) );
    }

    return `<div class="eventFlowPartsRuleContainer">${html.join('')}</div>`;
}
partsRuleBlockHtml( name, body, addClassName ) {
    const className = [`eventFlowPartsRule${name}`];
    if ( addClassName ) className.push( addClassName );
    return `<div class="eventFlowPartsRuleBlock ${className.join(' ')}">`
        //+ `<div class="eventFlowPartsRuleBlockHeader">${name}</div>`
        + `<div class="eventFlowPartsRuleBlockBody">`
        + body
    + `</div></div>`;
}
partsRuleListHtml( type, name ) {
    return `<div class="eventFlowPartsItem eventFlowParts${type}">`
        + `<div class="eventFlowPartsHeader">`
            + `<div class="eventFlowPartsName"><span class="eventFlowPartsNameText">${name}</span></div>`
        + `</div>`
    + `</div>`;
}
/*
##################################################
  エラーHTML
##################################################
*/
partsEditError ( title, elements ) {
    return new Promise(function( resolve ){
        const funcs = {};

        funcs.ok = function(){
            dialog.close();
            dialog = null;
            resolve( true );
        };
        const config = {
            position: 'center',
            header: {
                title: title
            },
            footer: {
                button: {
                    ok: { text: getMessage.FTE10043, action: 'normal'}
                }
            }
        };
        let dialog = new Dialog( config, funcs );
        dialog.open( elements );
    });
}

}