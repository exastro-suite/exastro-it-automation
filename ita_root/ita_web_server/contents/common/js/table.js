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
   Header hierarchy
   > ヘッダー階層データと列データをセット
##################################################
*/
setHeaderHierarchy() {
    const tb = this;
    
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
    
    const hierarchy = function( columns, row, col ){
        if ( !tb.data.hierarchy[ row ] ) tb.data.hierarchy[ row ] = [];
        for ( const columnKey of columns ) {            
            const type = columnKey.slice( 0, 1 );
            if ( type === 'g') {
                tb.data.hierarchy[ row ].push( columnKey );
                hierarchy( tb.info.column_group_info[ columnKey ][`columns_${tb.tableMode}`], row + 1, col );
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
    hierarchy( tb.info.menu_info[`columns_${tb.tableMode}`], 0, 0 );
    
    // 固定列用情報
    tb.data.sticky = {};
    tb.data.sticky.leftLast = specialHeadColumn[0];
    tb.data.sticky.rightFirst = specialFootColumn[0];
    tb.data.sticky.commonFirst = restOrder[0];
    tb.data.sticky.commonLast = restOrder[ restOrder.length - 1 ];

    // 特殊列を先頭に追加
    for ( const columnKey of specialHeadColumnKeys ) {
        tb.data.hierarchy[0].unshift( columnKey );
        tb.data.columnKeys.unshift( columnKey );
    }
    // 特殊列を末尾に追加
    for ( const columnKey of specialFootColumnKeys ) {
        tb.data.hierarchy[0].push( columnKey );
        tb.data.columnKeys.push( columnKey );
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
            <table class="table mainTable">
            </table>
        </div>
        <div class="tableFooter">
            ${tb.footerHtml()}
        </div>
        <div class="tableMessage"></div>
        <div class="tableErrorMessage"></div>
        <div class="tableLoading"></div>
        <style class="tableStyle"></style>
    </div>`;
    
    // jQueryオブジェクトキャッシュ
    tb.$ = {};
    tb.$.window = $( window );
    tb.$.container = $( html );
    tb.$.header = tb.$.container.find('.tableHeader');
    tb.$.body = tb.$.container.find('.tableBody');
    tb.$.footer = tb.$.container.find('.tableFooter');
    tb.$.table = tb.$.container.find('.table');
    tb.$.message = tb.$.container.find('.tableMessage');
    tb.$.errorMessage = tb.$.container.find('.tableErrorMessage');
    tb.$.style = tb.$.container.find('.tableStyle');

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
    
    tb.$.table.html( tb.tableHtml() );
    tb.$.table.attr('table-mode', tb.tableMode );
    
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
                const menuList = {
                    Main: [],
                    Sub: [{ button: { icon: 'filter', text: getMessage.FTE00001, type: 'filterToggle', action: 'default',
                        toggle: { init: 'off', on:getMessage.FTE00002, off:getMessage.FTE00003}}}]
                };
                if ( tb.mode === 'select') {
                    menuList.Main.push({ message: { text: getMessage.FTE00004 }});
                }
                if ( tb.mode === 'execute') {
                    menuList.Main.push({ button: { className: 'tableAdvance', icon: 'square_next', text: getMessage.FTE00005, type: 'tableRun', action: 'positive', minWidth: '160px', disabled: true }});
                    menuList.Main.push({ button: { className: 'tableAdvance',icon: 'square_next', text: getMessage.FTE00006, type: 'tableDryrun', action: 'positive', minWidth: '160px', disabled: true }});
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
                            tb.$.table.toggleClass('filterShow');
                            tb.stickyWidth();
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
    
    // Table内各種イベントセット
    tb.setTableEvents();    
}
/*
##################################################
   tHead HTML
##################################################
*/
tableHtml() {
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
    switch ( tb.mode ) {
        case 'view':
            if ( tb.flag.update ) {
                const selectButton = fn.html.button('', 'rowSelectButton');
                html[0] += fn.html.cell( selectButton, ['tHeadTh', 'tHeadLeftSticky', 'tHeadRowSelect'], 'th', headRowspan );
                tb.data.filterHeadColspan++;
            }
            html[0] += fn.html.cell( fn.html.icon('ellipsis_v'), ['tHeadTh', 'tHeadLeftSticky', 'tHeadRowMenu'], 'th', headRowspan );
            tb.data.filterHeadColspan++;
        break;
        case 'select': case 'execute':
            html[0] += fn.html.cell(getMessage.FTE00032, ['tHeadTh', 'tHeadLeftSticky'], 'th', headRowspan );
            tb.data.filterHeadColspan++;
        break;
        case 'edit': {
            if ( tb.flag.edit || tb.flag.disuse || tb.flag.reuse ) {
                const selectButton = fn.html.button('', 'rowSelectButton');
                html[0] += fn.html.cell( selectButton, ['tHeadTh', 'tHeadLeftSticky', 'tHeadRowSelect'], 'th', headRowspan );
            }
        } break;
        case 'diff':
            html[0] += fn.html.cell(getMessage.FTE00033, ['tHeadTh', 'tHeadLeftSticky'], 'th', headRowspan );
        break;
        case 'history':
            html[0] += fn.html.cell(getMessage.FTE00034, ['tHeadTh', 'tHeadLeftSticky', 'tHeadLeftStickyLast'], 'th', headRowspan );
            html[0] += fn.html.cell(getMessage.FTE00035, ['tHeadTh'], 'th', headRowspan );
            html[0] += fn.html.cell(getMessage.FTE00036, ['tHeadTh'], 'th', headRowspan );
        break;
    }

    for ( let i = rowLength; i >= 0 ; i-- ) {
        if ( !html[i] ) html[i] = '';
        
        for ( const columnKey of hierarchy[i] ) {
            if ( !groupColspan[ columnKey ] ) groupColspan[ columnKey ] = {};
            
            const type = columnKey.slice( 0, 1 );
            
            // Group
            if ( type === 'g') {
                const group = groupInfo[ columnKey ],
                      name = fn.cv( group.column_group_name, '', true ),
                      gCount = fn.cv( groupColspan[ columnKey ].group_count, 0 ),
                      gColspan = fn.cv( groupColspan[ columnKey ].group_colspan, 0 ),
                      colspan = group[`columns_${tb.tableMode}`].length + gColspan - gCount;
                
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
                      className = ['tHeadTh', 'popup'],
                      attr = {id: columnKey};
                
                let name = fn.cv( column.column_name, '', true );
                           
                // selectモードの場合ボタンカラムは非表示
                if ( ( tb.mode === 'select' || tb.mode === 'execute' || tb.mode === 'history') && column.column_type === 'ButtonColumn') {
                    continue;
                }
                // ソート
                if ( tb.mode === 'view' || tb.mode === 'select' || tb.mode === 'execute') {
                    const notSort = ['ButtonColumn', 'PasswordColumn', 'PasswordIDColumn', 'JsonPasswordIDColumn', 'MaskColumn', 'SensitiveSingleTextColumn', 'SensitiveMultiTextColumn'];
                    if ( notSort.indexOf( column.column_type ) === -1 ) {
                        className.push('tHeadSort');
                        name += `<span class="tHeadSortMark"></span>`
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
                if ( i === 0 && tb.mode !== 'history') {
                    if ( [ tb.idNameRest, 'discard'].indexOf( column.column_name_rest ) !== -1 ) {
                        className.push('tHeadLeftSticky');
                    }
                    // Border調整用class
                    if ( column.column_name_rest === tb.data.sticky.leftLast ) className.push('tHeadLeftStickyLast');
                    /*
                    if ( column.column_name_rest === tb.data.sticky.rightFirst ) className.push('tHeadRightStickyFirst');
                    if ( column.column_name_rest === tb.data.sticky.commonFirst ) className.push('tHeadCommonFirst');
                    if ( column.column_name_rest === tb.data.sticky.commonLast ) className.push('tHeadCommonEnd');
                    */
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
            html.push( tb.filterHtml() );
        }
    }
    
    return `
    <thead class="thead">
        ${html.join('')}
    </thead>
    <tbody class="tbody">
    </tbody>`;
}
/*
##################################################
   Filter HTML
##################################################
*/
filterHtml() {
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
    cells.push( fn.html.cell( filterIcon, className, 'th', 2, tb.data.filterHeadColspan ) );
    // rowClassName.push('filterNoHeaderTr'); // フィルタタイトルを消す場合
    
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
                    case 'JsonIDColumn':
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
                          return initSetFilter[ rest ].NORMAL;
                      break;
                      default:
                          return { start: initSetFilter[ rest ].START, end: initSetFilter[ rest ].END };
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
                            + fn.html.button('<span class="icon icon-cal"></span>', ['itaButton', 'filterInputDatePicker'], { rest: rest, action: 'normal'})
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
                            + fn.html.button('<span class="icon icon-cal"></span>', ['itaButton', 'filterInputDatePicker'], { rest: rest, action: 'normal'})
                        + `</div>`
                    + `</div>`);
                break;
                // 表示しない
                default:
                    className.push('tHeadFilterNone');
                    cellHtml.push('<div class="filterNone"></div>');
            }
        }

        if (  [ tb.idNameRest, 'discard'].indexOf( rest) !== -1 ) {
            className.push('tHeadLeftSticky');
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
    
    const thead = [ fn.html.cell( name, 'tHeadBlank tHeadLeftSticky tHeadLeftStickyLast', 'th') ];
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
                  rest = $a.attr('data-rest');
            
            const params = tb.data.body.find(function( item ){
                if ( tb.mode !== 'history') {
                    return String( item.parameter[ tb.idNameRest ] ) === id;
                } else {
                    return String( item.parameter.journal_id ) === id;
                }
            });
            
            let file;
            
            if ( params !== undefined ) {
                // 編集確認かつ入力データがない場合
                if ( tb.mode === 'diff' && params.file[rest] === undefined ) {
                    if ( tb.option && tb.option.before[ id ] && tb.option.before[ id ].file[ rest ] ) {
                        file = tb.option.before[ id ].file[ rest ];
                    }
                } else {
                    if ( params !== undefined && params.file[rest] !== undefined && params.file[rest] !== null ) {
                        file = params.file[rest];
                    }
                }            
            }
            
            if ( file ) {
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
                          rest = $button.attr('data-rest');

                    const $from = tb.$.thead.find(`.filterFromDate[data-rest="${rest}"]`),
                          $to = tb.$.thead.find(`.filterToDate[data-rest="${rest}"]`);

                    const from = $from.val(),
                          to = $to.val();

                    fn.datePickerDialog('fromTo', true, tb.data.restNames[ rest ], { from: from, to: to } ).then(function( result ){
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
        
        // アクションボタン
        tb.$.tbody.on('click', '.actionButton', function(){
            if ( !tb.checkWork ) {
                const $button = $( this ),
                      type = $button.attr('data-type');
                
                switch ( type ) {
                    case 'redirect': {
                        const redirect = $button.attr('data-redirect');
                        if ( redirect ) {
                            window.location.href = redirect;
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
            
            $value.remove();
            
            $select.select2({
                dropdownAutoWidth: false,
                width: width
            }).select2('open');
            
            $select.change();
        });
    }
    
    /*
    ------------------------------
    VIEW or EDIT モード
    ------------------------------
    */
    if ( tb.mode === 'view' || tb.mode === 'edit') {
        
        // 行選択チェックボックスの外がクリックされても変更する
        tb.$.thead.find('.tHeadRowSelect').on('click', function( e ){
            if ( !tb.checkWork ) {
                const $button = $( this ).find('.rowSelectButton');
                if ( !$( e.target ).closest('.rowSelectButton').length ) {
                    $button.focus().click();
                }
            }
        });
        tb.$.tbody.on('click', '.tBodyRowSelect', function( e ){
            if ( !tb.checkWork ) {
                const $check = $( this ).find('.tBodyRowCheck'),
                      checked = $check.prop('checked');

                if ( !$( e.target ).closest('.checkboxWrap').length ) {
                    $check.focus().prop('checked', !checked ).change();
                }
            }
        });
        
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
                      checkMode = ( tb.mode === 'edit')? 'edit': 'view';

                if ( checked ) {
                    tb.select[ checkMode ].push( id );
                } else {
                    const index = tb.select[ checkMode ].indexOf( id );
                    if ( index !== -1 ) {
                        tb.select[ checkMode ].splice( index, 1 );
                    }
                }

                tb.checkSelectStatus();

                // メニューボタンを活性化
                if ( checkMode === 'edit' ) {
                    tb.editModeMenuCheck();            
                }
            }
        });
    }
    /*
    ------------------------------
    SELECT or EXECUTEモード
    ------------------------------
    */
    if ( tb.mode === 'select' || tb.mode === 'execute') {
        // 行選択ラジオボタンの外がクリックされても変更する
        tb.$.tbody.on('click', '.tBodyRowRadioSelect', function( e ){
            if ( !tb.checkWork ) {
                const $radio = $( this ).find('.tBodyRowRadio'),
                      checked = $radio.prop('checked');
                      
                if ( !checked ) {
                    if ( !$( e.target ).closest('.radioWrap').length ) {
                        $radio.focus().prop('checked', true ).change();
                    }
                } else {
                    $radio.focus();
                }
            }
        });
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
            $tr.find('.input, .button').not('[data-key="remarks"]').prop('disabled', false );
        } else {
            $tr.addClass('tBodyTrDiscard');
            $tr.find('.input, .button').not('[data-key="remarks"]').prop('disabled', true );
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
    
    fn.fetch(`${tb.rest.filterPulldown}${rest}/`).then(function( result ){
        $select.html( tb.filterSelectBoxHtml( result, name, rest ) );
        $select.find('select').select2({
            placeholder: "Pulldown select",
            dropdownAutoWidth: false,
            width: width
        }).select2('open');
    }).catch( function( e ) {
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
                alert(getMessage.FTE00067);
                return false;
            //表示確認
            } else if ( printConfirmNum !== -1 && tb.data.count >= printConfirmNum ) {
                if ( !confirm(getMessage.FTE00066) ) {
                    return false;
                }
            }

            tb.workerPost('filter', tb.filterParams );
        }).catch(function( error ){
            fn.gotoErrPage( error.message );
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
                    filterParams[ rest ].RANGE.START = fn.date( value, 'yyyy/MM/dd HH:mm:ss');
                break;
                case 'toDate':
                    if ( !filterParams[ rest ].RANGE ) filterParams[ rest ].RANGE = {};
                    filterParams[ rest ].RANGE.END = fn.date( value, 'yyyy/MM/dd HH:mm:ss');
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
    for ( const item of list ) {
        const value = fn.cv( item, '', true );
        select.push(`<option value="${value}">${value}</option>`)
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
    }
    
    if ( tb.mode === 'edit' || tb.mode === 'view') {
        tb.checkSelectStatus();
    }
    
    tb.filterDownloadButtonCheck();
    tb.stickyWidth();
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
        tb.$.table.addClass('filterShow');
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
    
    tb.$.thead.find('.tHeadTr').eq(0).find('.tHeadLeftSticky').each(function( index ){
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
    
    if ( tb.option.sheetType !== 'reference') {
        style.push(`#${tb.id} .filterMenuList{left:${leftStickyFilterMenuWidth}px;}`);
    }
    style.push(`#${tb.id} .tHeadGroup>.ci{left:${leftStickyWidth}px;}`);    
    
    tb.$.style.html( style.join('') );
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
                attrs.selectname = fn.cv( rowParameter[ tb.params.selectNameKey ], '', true );
            }
            const idName = ( type === 'check')? `${tb.id}__ROWCHECK`: `${tb.id}__ROWRADIO`,
                  className = ( type === 'check')? 'tBodyRowCheck': 'tBodyRowRadio',
                  rowClassName = ( type === 'check')? 'tBodyRowSelect': 'tBodyRowRadioSelect';

            const checkboxId = `${idName}__${rowId}`,
                  checkbox = fn.html[ type ]( className, rowId, idName, checkboxId, attrs );
            return fn.html.cell( checkbox, ['tBodyLeftSticky', rowClassName, 'tBodyTh'], 'th');
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
                rowHtml.push( rowCheckInput('radio') );
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
    const buttonColumnHide = ['select', 'edit', 'history'];
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
    if ( tb.edit.input[ id ] && tb.edit.input[ id ].after.parameter.discard ) {
        return tb.edit.input[ id ].after.parameter.discard;
    } else if ( tb.data[ id ] && tb.data[ id ].parameter.discard ) {
        return tb.data[ id ].parameter.discard;
    } else {
        return '0';
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
        case 'IDColumn': case 'HostInsideLinkTextColumn': case 'LinkIDColumn':
        case 'LastUpdateUserColumn': case 'RoleIDColumn':
        case 'EnvironmentIDColumn': case 'TextColumn':
        case 'DateColumn': case 'DateTimeColumn':
        case 'FileUploadEncryptColumn': case 'JsonIDColumn':
            return checkJournal( value );
            
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
            if ( file[ columnName ] ) {
                return checkJournal(`<a href="${value}" class="tableViewDownload" data-id="${id}" data-rest="${columnName}">${value}</a>`);
            } else {
                return checkJournal( value );
            }
        }
        // ボタン
        case 'ButtonColumn':
            return tb.buttonAction( columnInfo, item );
        
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
   View mode Button action
##################################################
*/
buttonAction( columnInfo, item ) {    
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
                buttonAttrs.action = 'positive';
                buttonAttrs.redirect += action[1] + item.parameter[ action[2] ];
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
          autoInput = '<span class="tBodyAutoInput"></span>';

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
    if ( columnInfo.input_item === '0' || columnType === 'LastUpdateUserColumn') {
        if ( value !== '') {
            return value;
        } else {
            return autoInput;
        }
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
        case 'IDColumn': case 'LinkIDColumn': case 'RoleIDColumn':
        case 'EnvironmentIDColumn': case 'JsonIDColumn':
            if ( Object.keys( tb.data.editSelect[columnName] ).length ) {
                return `<div class="tableEditInputSelectContainer ${inputClassName.join(' ')}">`
                + `<div class="tableEditInputSelectValue">${value}</div>`
                + fn.html.select( fn.cv( tb.data.editSelect[columnName], {}), 'tableEditInputSelect', value, name, attr, { select2: true } )
                + `</div>`;
            } else {
                return fn.html.noSelect();
            }

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
    
    const valueCheck = function( val ) {
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
                return `<a href="${val}" class="tableViewDownload" data-id="${id}" data-rest="${columnName}">${val}</a>`;
            
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
            return beforeAfter( valueCheck( fn.cv( beforeData.parameter[ columnName ], '', true ) ), valueCheck( value) );
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
    const html = [];
    for ( const item of list ) {
        const button = fn.html.button( item.text, [ item.className, 'tableRowMenuButton', 'itaButton'],
            { type: item.type, action: item.action, id: item.id });
        html.push(`<li class="tableRowMenuItem">${button}</li>`);
    }
    return `${fn.html.icon('ellipsis_v')}
    <div class="tableRowMenu"><ul class="tableRowMenuList">${html.join('')}</ul></div>`;
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
    
    // テーブル構造を再セット
    tb.setHeaderHierarchy();
    
    const info = tb.info.column_info;
    
    tb.workStart('table', 0 );
    tb.paging.page = 1;
    tb.edit.addId = -1;
    
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
            const selectTarget = ['IDColumn', 'LinkIDColumn', 'AppIDColumn', 'RoleIDColumn', 'JsonIDColumn'];
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
        width: '100%',
        height: '100%',
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
                    title: getMessage.FTE00006,
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
                window.location.href = `?menu=check_operation_status_ansible_role&execution_no=${result.execution_no}`;
            }).catch(function( error ){
                fn.gotoErrPage( error.message );
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
        //errorMessage = {"0":{key:[error.message]}};
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
            const name = fn.cv( tb.data.restNames[ error ], error, true ),
                  body = fn.cv( errorMessage[item][error].join(''), '?', true );
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

}
