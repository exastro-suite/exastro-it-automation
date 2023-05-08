////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Exastro IT Automation / ui.js
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

class Dashboard {

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Widgetデータ
//
////////////////////////////////////////////////////////////////////////////////////////////////////

/*
##################################################
   Widget scripts
##################################################
*/
static widgetScripts = {
    /*
        script name: class name
    */
    menu_group: 'WidgetMenuGroup',
    link_list: 'WidgetLinkList',
    pie_chart: 'WidgetPieChart',
    stacked_graph: 'WidgetStackedGraph',
    reserve_list: 'WidgetReserveList',
    image: 'WidgetImage'
};

/*
##################################################
   Widgetデータ
##################################################
*/
static widgetData = {
    /*
    0: {
        widget_id: 0, Widget ID
        widget_name: '', class名などに使用
        script_name: '', 使用するスクリプト名
        description: '', 説明
        set_id: null, 設置ID
        title: '', 表示する名称
        col: null, 列位置情報
        row: null, 行位置情報
        colspan: 1, 列結合数
        rowspan: 1, 行結合数
        display: 'show', Widgetを表示するか
        header: 'show', ヘッダーを表示するか
        background: 'show', 背景を表示するか
        unique_flag: 0, 複数設置できるか
        unique_setting: [ Widget固有設定
            {
                name: key
                title: '数値入力',
                type: 'number'
                min: 0,
                max: 10,
                value: 0
            }
        ],
        info_data_name: '' 使用するinfoデータのkey名
    },
    */
    /* temp
    0: {
        widget_id: 0,
        widget_name: '',
        script_name: '',
        description: '',
        set_id: null,
        title: '',
        col: null,
        row: null,
        colspan: 1,
        rowspan: 1,
        display: 'show',
        header: 'show',
        background: 'hide',
        unique_flag: 0,
        unique_setting: [],
        info_data_name: ''
    },
    */
    // メニューグループ
    0: {
        widget_id: 0,
        widget_name: 'menuGroup',
        script_name: 'menu_group',
        description: '',
        set_id: null,
        title: getMessage.FTE08001,
        col: null,
        row: null,
        colspan: 6,
        rowspan: 1,
        display: 'show',
        header: 'show',
        background: 'show',
        unique_flag: true,
        unique_setting: [
            {
                name: 'menu_number',
                title: getMessage.FTE08002,
                type: 'number',
                min: 1,
                max: 12
            },
            {
                name: 'list_type',
                attr: 'data-menu-grouup-display',
                title: getMessage.FTE08003,
                type: 'radio',
                list: [
                    { value: 'icon', text: getMessage.FTE08004 },
                    { value: 'list', text: getMessage.FTE08005 }
                ]
            },
            {
                name: 'name_flag',
                attr: 'data-menu-grouup-name',
                title: getMessage.FTE08006,
                type: 'radio',
                list: [
                    { value: 'show', text: getMessage.FTE08007 },
                    { value: 'hide', text: getMessage.FTE08008 }
                ]
            },
            {
                name: 'page_move',
                title: getMessage.FTE08082,
                type: 'radio',
                list: [
                    { value: 'same', text: getMessage.FTE08083 },
                    { value: 'blank', text: getMessage.FTE08084 },
                    { value: 'window', text: getMessage.FTE08085 },
                ]
            }
        ],
        menu_number: 6,
        list_type: 'icon',
        name_flag: 'show',
        info_data_name: 'menu',
        page_move: 'same'
    },
    // メニューセット
    1: {
        widget_id: 1,
        widget_name: 'menuSet',
        script_name: 'menu_group',
        description: getMessage.FTE08010,
        set_id: null,
        title: getMessage.FTE08009,
        col: null,
        row: null,
        colspan: 6,
        rowspan: 1,
        display: 'show',
        header: 'show',
        background: 'show',
        unique_flag: false,
        unique_setting: [
            {
                name: 'menu_number',
                title: getMessage.FTE08002,
                type: 'number',
                min: 1,
                max: 12
            },
            {
                name: 'list_type',
                attr: 'data-menu-grouup-display',
                title: getMessage.FTE08003,
                type: 'radio',
                list: [
                    { value: 'icon', text: getMessage.FTE08004 },
                    { value: 'list', text: getMessage.FTE08005 }
                ]
            },
            {
                name: 'name_flag',
                attr: 'data-menu-grouup-name',
                title: getMessage.FTE08006,
                type: 'radio',
                list: [
                    { value: 'show', text: getMessage.FTE08007 },
                    { value: 'hide', text: getMessage.FTE08008 }
                ]
            },
            {
                name: 'page_move',
                title: getMessage.FTE08082,
                type: 'radio',
                list: [
                    { value: 'same', text: getMessage.FTE08083 },
                    { value: 'blank', text: getMessage.FTE08084 },
                    { value: 'window', text: getMessage.FTE08085 },
                ]
            }
        ],
        menu_number: 6,
        list_type: 'icon',
        name_flag: 'show',
        info_data_name: 'menu',
        page_move: 'same'
    },
    // リンクリスト
    10: {
        widget_id: 10,
        widget_name: 'linkList',
        script_name: 'link_list',
        description: getMessage.FTE08012,
        set_id: null,
        title: getMessage.FTE08011,
        col: null,
        row: null,
        colspan: 6,
        rowspan: 1,
        display: 'show',
        header: 'show',
        background: 'show',
        unique_flag: false,
        unique_setting: [
            {
                name: 'menu_number',
                title: getMessage.FTE08002,
                type: 'number',
                min: 1,
                max: 8
            },
            {
                name: 'link_list',
                title: getMessage.FTE08013,
                type: 'list',
                list: {
                    name: getMessage.FTE08017,
                    url: getMessage.FTE08043
                }
            },
            {
                name: 'page_move',
                title: getMessage.FTE08082,
                type: 'radio',
                list: [
                    { value: 'same', text: getMessage.FTE08083 },
                    { value: 'blank', text: getMessage.FTE08084 },
                    { value: 'window', text: getMessage.FTE08085 },
                ]
            }
        ],
        menu_number: 2,
        link_list: [],
        page_move: 'same'
    },
    // Movement登録数
    100: {
        widget_id: 100,
        widget_name: 'movement',
        script_name: 'pie_chart',
        pie_chart_title: 'Movement',
        description: getMessage.FTE08019,
        set_id: null,
        title: getMessage.FTE08018,
        col: null,
        row: null,
        colspan: 2,
        rowspan: 1,
        display: 'show',
        header: 'show',
        background: 'show',
        unique_flag: true,
        unique_setting: [
            {
                name: 'page_move',
                title: getMessage.FTE08082,
                type: 'radio',
                list: [
                    { value: 'same', text: getMessage.FTE08083 },
                    { value: 'blank', text: getMessage.FTE08084 },
                    { value: 'window', text: getMessage.FTE08085 },
                ]
            }
        ],
        info_data_name: 'movement',
        page_move: 'same'
    },
    // 作業状況
    101: {
        widget_id: 101,
        widget_name: 'workStatus',
        script_name: 'pie_chart',
        pie_chart_title: getMessage.FTE08022,
        description: getMessage.FTE08021,
        set_id: null,
        title: getMessage.FTE08020,
        col: null,
        row: null,
        colspan: 2,
        rowspan: 1,
        display: 'show',
        header: 'show',
        background: 'show',
        unique_flag: true,
        unique_setting: [
            {
                name: 'page_move',
                title: getMessage.FTE08082,
                type: 'radio',
                list: [
                    { value: 'same', text: getMessage.FTE08083 },
                    { value: 'blank', text: getMessage.FTE08084 },
                    { value: 'window', text: getMessage.FTE08085 },
                ]
            }
        ],
        info_data_name: 'work_info',
        page_move: 'same'
    },
    // 作業結果
    102: {
        widget_id: 102,
        widget_name: 'workResult',
        script_name: 'pie_chart',
        pie_chart_title: getMessage.FTE08025,
        description: getMessage.FTE08024,
        set_id: null,
        title: getMessage.FTE08023,
        col: null,
        row: null,
        colspan: 2,
        rowspan: 1,
        display: 'show',
        header: 'show',
        background: 'show',
        unique_flag: true,
        unique_setting: [
            {
                name: 'page_move',
                title: getMessage.FTE08082,
                type: 'radio',
                list: [
                    { value: 'same', text: getMessage.FTE08083 },
                    { value: 'blank', text: getMessage.FTE08084 },
                    { value: 'window', text: getMessage.FTE08085 },
                ]
            }
        ],
        info_data_name: 'work_result',
        page_move: 'same'
    },
    // 作業履歴
    200: {
        widget_id: 200,
        widget_name: 'workHistory',
        script_name: 'stacked_graph',
        description: getMessage.FTE08027,
        set_id: null,
        title: getMessage.FTE08026,
        col: null,
        row: null,
        colspan: 6,
        rowspan: 1,
        display: 'show',
        header: 'show',
        background: 'show',
        unique_flag: true,
        unique_setting: [
            {
                name: 'period',
                title: getMessage.FTE08028,
                type: 'number',
                min: 7,
                max: 365,
                after: getMessage.FTE08029,
            },
            {
                name: 'page_move',
                title: getMessage.FTE08082,
                type: 'radio',
                list: [
                    { value: 'same', text: getMessage.FTE08083 },
                    { value: 'blank', text: getMessage.FTE08084 },
                    { value: 'window', text: getMessage.FTE08085 },
                ]
            }
        ],
        info_data_name: 'work_result',
        period: 28,
        page_move: 'same'
    },
    // Conductor予約リスト
    300: {
        widget_id: 300,
        widget_name: 'reserveList',
        script_name: 'reserve_list',
        description: getMessage.FTE08031,
        set_id: null,
        title: getMessage.FTE08030,
        col: null,
        row: null,
        colspan: 6,
        rowspan: 1,
        display: 'show',
        header: 'show',
        background: 'show',
        unique_flag: true,
        unique_setting: [
            {
                name: 'period',
                title: getMessage.FTE08028,
                type: 'number',
                min: 7,
                max: 365,
                after: getMessage.FTE08029,
            },
            {
                name: 'page_move',
                title: getMessage.FTE08082,
                type: 'radio',
                list: [
                    { value: 'same', text: getMessage.FTE08083 },
                    { value: 'blank', text: getMessage.FTE08084 },
                    { value: 'window', text: getMessage.FTE08085 },
                ]
            }
        ],
        info_data_name: 'work_reserve',
        period: 14,
        page_move: 'same'
    },
    // 画像
    500: {
        widget_id: 500,
        widget_name: 'image',
        script_name: 'image',
        description: getMessage.FTE08041,
        set_id: null,
        title: getMessage.FTE08040,
        col: null,
        row: null,
        colspan: 2,
        rowspan: 1,
        display: 'show',
        header: 'show',
        background: 'show',
        unique_flag: false,
        unique_setting: [
            {
                name: 'image_url',
                title: getMessage.FTE08042,
                type: 'text'
            },
            {
                name: 'link_url',
                title: getMessage.FTE08043,
                type: 'text'
            },
            {
                name: 'page_move',
                title: getMessage.FTE08082,
                type: 'radio',
                list: [
                    { value: 'same', text: getMessage.FTE08083 },
                    { value: 'blank', text: getMessage.FTE08084 },
                    { value: 'window', text: getMessage.FTE08085 },
                ]
            }
        ],
        image_url: '/_/ita/imgs/widget_default_image.png',
        link_url: '',
        page_move: 'same'
    },
    
}

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   初期設定
//
////////////////////////////////////////////////////////////////////////////////////////////////////

/*
##################################################
   Constructor
##################################################
*/
constructor( target ) {
    const db = this;
    
    db.target = target;
    
    db.scripts = {};
    db.instance = {};
    
    db.widgetPosition = [];
    db.maxColumn = 12;
    db.maxRow = 6;
    
    db.widgetCount = 0;
    db.widgetBlankCount = 0;
    db.widgetNumber = {};
    
    db.changeFlag = false;
    
    db.scrollTimer = false;
}
/*
##################################################
   Setup
##################################################
*/
setup() {
    const db = this;
    
    // jQueryオブジェクトキャッシュ
    db.$ = {};
    db.$.window = $( window );
    db.$.body = $('body');
    db.$.target = $( db.target );
    
    db.$.target.addClass('dashboard-loading');
    
    // DashBoardデータの読み込み
    fn.fetch('/user/dashboard/').then(function( result ){
        db.info = result;        
        
        // Widget import list
        const fileList = [],
              importList = [];
        for ( const widgetScript in Dashboard.widgetScripts ) {
            const scriptUrl = `/_/ita/js/widget/${widgetScript}.js`;
            importList.push( import( scriptUrl ) );
            fileList.push( widgetScript );
        }

        Promise.all( importList ).then(function( importWidget ){        
            const scriptLength = importWidget.length;
            for ( let i = 0; i < scriptLength; i++ ) {
                db.scripts[ fileList[i] ] = importWidget[i];
            }        
            db.init();        
        }).catch(function( error ){
            window.console.error( error );
            alert( error.message );
        });
    }).catch(function( error ){
        if ( error.message !== 'Failed to fetch') {
            window.console.error( error );
            alert( error.message );
        }
    });
}
/*
##################################################
   初期設定
##################################################
*/
init() {
    const db = this;
    
    db.$.body.addClass('body-overflow-hidden');
    db.$.target.removeClass('dashboard-loading');
    
    // DashBoad HTML
    const html = `
    <div class="dashboard" data-mode="view">
        <div class="contentHeader">
            <h1 class="contentTitle"><span class="contentTitleInner">DashBoard</span></h1>
            <p class="contentMenuInfo">
                <span class="contentMenuInfoInner">${getMessage.FTE00077}</span>
                ${fn.html.iconButton('edit', getMessage.FTE08044, 'editDashBoardButton itaButton')}
            </p>
        </div>
        <div class="contentBody">
            <div class="dashboard-menu"></div>
            <div class="dashboard-body commonScroll">
                <div class="dashboard-area"></div>
                <div class="add-blank"></div>
            </div>
            <style class="dashboard-grid-style"></style>
        </div>
    </div>`;
    db.$.target.html( html );

    db.$.container = db.$.target.find('.dashboard');
    db.$.dashboard = db.$.target.find('.dashboard-body');
    db.$.menu = db.$.target.find('.dashboard-menu');
    db.$.area = db.$.target.find('.dashboard-area');
    db.$.style = db.$.target.find('.dashboard-grid-style');

    db.$.editButton = db.$.target.find('.editDashBoardButton');
    
    // Widgetデータがない場合は初期データを入れる
    if ( Object.keys( db.info.widget ).length === 0 ) {
        db.setInitWidgetData();
    } else {
        db.widgetInfo = $.extend( true, {}, db.info.widget );
    }
    db.resetDashboadArea();

    db.$.editButton.on('click', function(){
        const $button = $( this ),
              mode = db.$.container.attr('data-mode');
        if ( mode === 'view') {
            $button.prop('disabled', true );
            db.changeEditMode();
        }
    });
    
    db.setLinkEvent();
}
/*
##################################################
   Widget ID作成
##################################################
*/
createWidgetId() {
    const db = this,
          setIdList = Object.keys( db.widgetInfo ),
          whileFlag = true;
    // 重複がないかチェックする
    let setID = 'w' + db.widgetCount++;
    while( whileFlag ) {
        if ( setIdList.indexOf( setID ) === -1 ) break;
        setID = 'w' + db.widgetCount++;
    }  
    return setID;
}
/*
##################################################
   Blank ID作成
##################################################
*/
createBlankId() {
    return 'b' + this.widgetBlankCount++;
}
/*
##################################################
   Widget 初期表示データ
##################################################
*/
setInitWidgetData() {
    const db = this;
    
    // 初期配置 Widget [ WidgetID, 行, 列, rowspan, colspan ]
    const initialWidget = [
        [   0, 0,  0, 2, 6],
        [ 100, 0,  6, 1, 2],
        [ 101, 0,  8, 1, 2],
        [ 102, 0, 10, 1, 2],
        [ 200, 1,  6, 1, 6],
    ];
    
    db.widgetInfo = {};
    
    const wi = db.widgetInfo,
          l = initialWidget.length;
    
    for ( let i = 0; i < l; i++ ) {
      const iw = initialWidget[i],
            id = db.createWidgetId();
      
      // Widgetデータコピー
      wi[ id ] = $.extend( true, {}, Dashboard.widgetData[ iw[0] ] );
      delete wi[ id ].description;
      
      // 初期値セット
      wi[ id ].set_id = id;
      wi[ id ].row = iw[1];
      wi[ id ].col = iw[2];
      wi[ id ].rowspan = iw[3];
      wi[ id ].colspan = iw[4];
    }
}
/*
##################################################
   Blank HTML
##################################################
*/
blankHtml( id ) {
    return `<div id="${id}" style="grid-area:${id}" class="widget-blank-grid" data-rowspan="1" data-colspan="1">`
        + `<div class="widget-blank"></div>`
    + `</div>`;
}
/*
##################################################
   位置情報のない部分のBlank HTMLを作成する
##################################################
*/
paddingBlankHtml() {
    const db = this;
    
    const wp = db.widgetPosition,
          l = wp.length,
          html = [];
    
    for ( let i = 0; i < l; i++ ) {
        if ( wp[ i ] === undefined ) wp[ i ] = [];
        for ( let j = 0; j < db.maxColumn; j++ ) {
            if ( wp[ i ] [ j ] === undefined ) {
                const blankID = db.createBlankId();
                wp[ i ] [ j] = blankID;
                html.push( db.blankHtml( blankID ) );
            }
        }
    }
    return html.join('');
}
/*
##################################################
   位置情報のない部分をBlankで埋める
##################################################
*/
paddingBlank() {
    const db = this;
    db.$.area.append( db.paddingBlankHtml() );
    db.updatePosition();
}
/*
##################################################
   位置情報を更新
##################################################
*/
updatePosition() {
    const db = this,
          wp = db.widgetPosition,
          ws = [];
    
    if ( wp !== undefined ) {
        const rows = wp.length;
        for ( let i = 0; i < rows; i++ ) {
            if ( wp[i] !== undefined ) {
                ws.push(`"${wp[i].join(' ')}"`);
            }
        } 
    }
    // Grid style
    const gs = `.dashboard-area{grid-template-areas:${ws.join(' ')};}`;
    db.$.style.html( gs );
}
/*
##################################################
   ダッシュボードエリアリセット
##################################################
*/
resetDashboadArea() {
    const db = this;
    
    db.$.area.empty().css(`grid-template-columns`, `repeat(${db.maxColumn},${100/db.maxColumn}%)`);
    db.setInitWidget();
}
/*
##################################################
   新しいWidgetの作成
##################################################
*/
newWidget( setId ) {
    const db = this;
    
    const scriptName = db.widgetInfo[ setId ].script_name,
          scriptClass = Dashboard.widgetScripts[ scriptName ];
    
    if ( scriptClass ) {
        db.instance[ setId ] = new db.scripts[ scriptName ][ scriptClass ](
            setId,
            db.widgetInfo[ setId ],
            db.widgetPosition,
            { col: db.maxColumn, row: db.maxColumn },
            db.info[ db.widgetInfo[ setId ].info_data_name ]
        );        
        
        const widgetId = db.widgetInfo[ setId ].widget_id;
        if ( db.widgetNumber[ widgetId ] === undefined ) db.widgetNumber[ widgetId ] = 0;
        db.widgetNumber[ widgetId ]++;
        
        const $widget = db.instance[ setId ].widget();
        
        if ( db.instance[ setId ].ready ) {
            $widget.ready(function(){
                db.instance[ setId ].ready();
            });
        }
        db.$.area.append( $widget );
        return $widget;
    } else {
        return false;
    }
}
/*
##################################################
   Widget 初期配置
##################################################
*/
setInitWidget() {
    const db = this;
    
    const wi = db.widgetInfo,
          wp = db.widgetPosition;
    
    // 編集差分確認用
    db.init = JSON.stringify( wi );

    for ( const setId in wi ) {        
        if ( db.newWidget( setId ) ) {
            // 位置情報
            const r = Number( wi[ setId ].row ),
                  c = Number( wi[ setId ].col ),
                  rs = Number( wi[ setId ].rowspan ),
                  cs = Number( wi[ setId ].colspan );

            for ( let j = 0; j < rs; j++ ) {
                const p = r + j;
                if ( wp[ p ] === undefined ) wp[ p ] = [];
                for ( let k = 0; k < cs; k++ ) {
                    const col = c + k;
                    if ( col > db.maxColumn ) break;
                    wp[ p ][ col ] = setId;
                }
            }
        } else {
            alert('Widget error.');
        }
    }
    
    db.$.area.append( db.paddingBlankHtml() );
    db.updatePosition();
}

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   モードチェンジ
//
////////////////////////////////////////////////////////////////////////////////////////////////////

/*
##################################################
   編集モードに変更
##################################################
*/
changeEditMode() {
    const db = this;
    
    db.$.container.attr('data-mode', 'edit');
    
    // 編集メニュー
    const menuList = {
        Main: [
            /*{ button: { type: 'setting', icon: 'gear', text: getMessage.FTE08044, action: 'default'}},*/
            { button: { type: 'add', icon: 'plus', text: getMessage.FTE08045, action: 'default'}},
            { button: { type: 'ok', icon: 'check', text: getMessage.FTE08046, minWidth: '200px', action: 'positive'}, separate: true },
            { button: { type: 'reset', icon: 'return', text: getMessage.FTE08047, action: 'normal'}, separate: true },
            { button: { type: 'cancel', icon: 'cross', text: getMessage.FTE08048, action: 'normal'} }
        ],
        Sub: []
    };
    db.$.menu.html( fn.html.operationMenu( menuList ) );
    
    db.$.menu.find('.operationMenuButton').on('click', function(){
        const $button = $( this ),
              type = $button.attr('data-type');
        
        $button.prop('disabled', true );
        switch ( type ) {
            case 'cancel':
                db.changeViewMode( $button );
            break;
            case 'add':
                db.widgetSelect( $button );
            break;
            case 'ok':
                db.saveWidget( $button );
            break;
            case 'reset':
                db.resetWidget( $button );
            break;
            case 'setting':
            break;
        }
    });
    
    // 編集用イベント
    db.setWidgetSettingEvent();
    db.setWidgetMoveEvent();
    db.setEditBlankEvent();
    db.setMenuItemMoveEvent();
}
/*
##################################################
   閲覧モードに変更
##################################################
*/
changeViewMode( $button ) {
    const db = this;
    
    // 差分を確認
    const info = JSON.stringify( db.widgetInfo );
    if ( db.init === info && db.changeFlag === false ) {
        // 変更がない場合確認なしで戻る
        db.$.container.attr('data-mode', 'view');
        db.$.editButton.prop('disabled', false );    

        db.$.menu.empty();

        db.$.menu.find('.operationMenuButton').off('click');

        // イベント削除
        db.removeWidgetSettingEvent()
        db.removeWidgetMoveEvent();
        db.removeEditBlankEvent();
        db.removeMenuItemMoveEvent();
    } else {
        // 変更がある場合は確認後ページリロード
        fn.alert(
            getMessage.FTE08053,
            getMessage.FTE08054,
            'confirm',
            {
                ok: { text: getMessage.FTE08055, action: 'default'},
                cancel: { text: getMessage.FTE08056, action: 'normal'}
            }).then(function( flag ){
                if ( flag ) {
                    window.location.reload();
                } else {
                    $button.prop('disabled', false );
                }
            }
        );
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   DashBoard設定
//
////////////////////////////////////////////////////////////////////////////////////////////////////

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Widget追加
//
////////////////////////////////////////////////////////////////////////////////////////////////////

/*
##################################################
   選択モーダルを開く
##################################################
*/
widgetSelect( $button ) {
    const db = this;
    
    const config = {
        mode: 'modeless',
        position: 'center',
        width: '640px',
        header: {
            title: getMessage.FTE08045,
        },
        footer: {
            button: {
                ok: { text: getMessage.FTE00087, action: 'default', /*className: 'dialogPositive'*/},
                cancel: { text: getMessage.FTE00088, action: 'normal'},
            }
        }
    };

    const functions =  {
        ok: function(){
            const selectWidgetId = modal.$.dbody.find('.db-widget-select-radio:checked').val();
            db.addWidget ( selectWidgetId );
            closeModal();
        },
        cancel: function(){
            closeModal();
        }
    }

    const closeModal = function(){
        modal.close();
        modal = null;
        $button.prop('disabled', false );
    }
    
    // Widget追加リスト
    const wd = Dashboard.widgetData,
          list = [];
    for ( const id in wd ) {
        const widgetId = wd[ id ].widget_id,
              unique = wd[ id ].unique_flag,
              disabledClass = ( unique === true && db.widgetNumber[ widgetId ] >= 1 )? ' commonInputTrDisabled': '',
              disabled = ( unique === true && db.widgetNumber[ widgetId ] >= 1 )? { disabled: 'disabled'}: {};        
        
        // メニューグループWidgetは表示しない
        if ( id !== '0') {
            const check = fn.html.radioText('db-widget-select-radio', id, 'widgetSelect', `widgetSelect_${wd[id].widget_name}`, disabled, wd[id].title ),
                  html = ``
            + `<tr class="commonInputTr${disabledClass}">`
                + `<th class="commonInputTh"><div class="commonInputTitle commonInputTitleRadio">${check}</div></th>`
                + `<td class="commonInputTd"><div class="commonInputText">${wd[id].description}</div></td>`
            + `</tr>`;
            list.push( html );
        }
    }
    
    const bodyHtml = ``
    + `<div class="commonSection">`
        + `<div class="commonTitle">Widget選択</div>`
        + `<div class="commonBody">`
            + `<table class="commonInputTable"><tbody class="commonInputTbody">`
                + list.join('')
            + `</tbody></table>`
        + `</div>`
    + `</div>`;
    
    let modal = new Dialog( config, functions );
    modal.open( bodyHtml );
}
/*
##################################################
   Widgetを追加する
##################################################
*/
addWidget( widgetId ) {
    const db = this;

    const wd = Dashboard.widgetData[ widgetId ],
          wi = db.widgetInfo,
          setId = db.createWidgetId();
    wi[ setId ] = $.extend( true, {}, wd );
    
    delete wi[ setId ].description;
    
    const targetBlankID = db.checkSetBlank( setId );
    
    if ( targetBlankID !== false ) {
      db.widgetPositionChange( targetBlankID, setId );
    } else {
      // 設置可能な場所がない場合新しい行に設置する
      db.setWidgetSpan( db.widgetPosition.length, 0, setId );
    }
    db.paddingBlank();
    
    const $widget = db.newWidget( setId );
    db.updatePosition();
    
    // 追加したWidgetまでスクロールする
    const scrollTop = $widget.position().top + db.$.dashboard.scrollTop();
    db.$.dashboard.animate({ scrollTop: scrollTop }, 300, 'swing');
}

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Widget設定
//
////////////////////////////////////////////////////////////////////////////////////////////////////

/*
##################################################
   Widget設定イベント
##################################################
*/
setWidgetSettingEvent() {
    const db = this;
    
    db.$.area.on('click.widgetSetting', '.widget-edit-button', function(){
        const $button = $( this ),
              $widget = $button.closest('.widget-grid'),
              id = $widget.attr('id'),
              type = $button.attr('data-type');
        
        switch ( type ) {
            case 'edit':
                db.widgetSetting( id );
            break;
            case 'delete':
                db.deleteWidget( $widget, id );
            break;
        }
    });
}
/*
##################################################
   Widget設定イベント削除
##################################################
*/
removeWidgetSettingEvent() {
    this.$.area.off('click.widgetSetting');
}
/*
##################################################
   Widget設定モーダルを開く
##################################################
*/
widgetSetting( id ) {
    const db = this,
          info = db.widgetInfo[ id ];
    
    db.instance[ id ].modalOpen( db.getWidgetPosition( id ) ).then(function( flag ){
        if ( flag ) db.updateWidget( id );
    });
}
/*
##################################################
   設置可能なBlankを調べる
##################################################
*/
checkSetBlank( id ) {
    const db = this,
          wi = db.widgetInfo[ id ],
          wp = db.widgetPosition,
          rows = wp.length;
    for ( let i = 0; i < rows; i++ ) {
      const cols = wp[i].length;
      for ( let j = 0; j < cols; j++ ) {
        if ( wp[i][j].match(/^b/) ) {
          const rowspan = wi.rowspan,
                colspan = wi.colspan;
          // 基準位置からrowspan,colspan分すべてBlankかチェックする
          const blankCheck = function(){
            for ( let k = 0; k < rowspan; k++ ) {
              const rowPlus = i + k;
              if ( wp[rowPlus] === undefined ) return true;
              for ( let l = 0; l < colspan; l++ ) {
                const colPlus = j + l;
                if ( colPlus >= db.maxColumn ||
                  ( wp[rowPlus][colPlus] !== undefined && wp[rowPlus][colPlus].match(/^w/))) {
                  return false;
                }
              }
            }
            return true;
          }
          if ( blankCheck() ) {
            return wp[i][j];
          }
        }
      }
    }
    // 設置不可
    return false;
}
/*
##################################################
   SetIDのWidgeを更新
##################################################
*/
updateWidget( id ) {
    const db = this;
    
    const p = db.getWidgetPosition( id );
    
    // 変更前を削除
    $(`#${id}`).remove();
    
    // Widgetを再セット
    const $widget = db.instance[ id ].widget();
    if ( db.instance[ id ].ready ) {
        $widget.ready(function(){
            db.instance[ id ].ready();
        });
    }
    db.$.area.append( $widget );
    
    db.widgetPositionDelete( id );
    db.paddingBlank();
    db.setWidgetSpan( p[0], p[1], id );
    
    db.updatePosition();
}
/*
##################################################
   Widget削除
##################################################
*/
deleteWidget( $widget, id ) {
    const db = this;
    
    const widgetId = db.widgetInfo[ id ].widget_id;
    
    // 対象がメニューセットの場合、中のメニューをメニューグループに移動する
    if ( widgetId === 1 ) {
        // 幅をメニューグループの設定に合わせる
        const menuNumber = db.widgetInfo['w0'].menu_number;
        $widget.find('.db-menu-group-item').css('width', `calc(100%/${menuNumber})`);
        
        db.$.area.find('#w0').find('.db-menu-group-list').append(
            $widget.find('.db-menu-group-list').html()
        );
    }
    
    db.widgetNumber[ widgetId ]--;
    
    db.widgetPositionDelete( id );
    db.paddingBlank();
    db.updatePosition();
    
    $widget.remove();
    delete db.widgetInfo[ id ];

    // 削除した後にメニュー情報を更新する
    if ( widgetId === 1 ) {
        db.updateMenuInfo();
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Widget移動
//
////////////////////////////////////////////////////////////////////////////////////////////////////

/*
##################################################
   移動可能なBlankを調べる
##################################################
*/
checkMovableBlank( id ) {
    const db = this,
          wi = db.widgetInfo[ id ],
          wp = db.widgetPosition,
          rows = wp.length;
    
    for ( let i = 0; i < rows; i++ ) {
        const cols = wp[i].length;
        for ( let j = 0; j < cols; j++ ) {
            if ( wp[i][j].match(/^b/) ) {
                const rowspan = wi.rowspan,
                      colspan = wi.colspan;
                // 基準位置からrowspan,colspan分すべてBlankかチェックする
                const blankCheck = function(){
                    for ( let k = 0; k < rowspan; k++ ) {
                        const rowPlus = i + k;
                        if ( wp[rowPlus] === undefined ) return false;
                        for ( let l = 0; l < colspan; l++ ) {
                            const colPlus = j + l;
                            if ( colPlus >= db.maxColumn ||
                                ( wp[rowPlus][colPlus] !== undefined && wp[rowPlus][colPlus].match(/^w/))) {
                                return false;
                            }
                        }
                    }
                    return true;
                }
                if ( blankCheck() ) {
                    $('#' + wp[i][j] ).addClass('movable-blank');
                }
            }
        }
    }
}
/*
##################################################
   SetIDから位置を返す
##################################################
*/
getWidgetPosition( id ) {
    const db = this,
          wp = db.widgetPosition,
          rows = wp.length;
    for ( let i = 0; i < rows; i++ ) {
        const cols = wp[i].length;
        for ( let j = 0; j < cols; j++ ) {
            if ( wp[i][j] === id ) return [ i, j ];
        }
    }
    return undefined;
}
/*
##################################################
   位置情報から指定のsetIDをundefinedに
##################################################
*/
widgetPositionDelete( id ) {
    const db = this,
          wp = db.widgetPosition,
          rows = wp.length;
    for ( let i = 0; i < rows; i++ ) {
        const cols = wp[i].length;
        for ( let j= 0; j < cols; j++ ) {
            if ( wp[i][j] === id ) wp[i][j] = undefined;
        }
    }
}
/*
##################################################
   指定blankにWidgetをセットする
##################################################
*/
widgetPositionChange( blankId, id ){
    const db = this;
    const p = db.getWidgetPosition( blankId );

    db.widgetInfo[ id ].row = p[0];
    db.widgetInfo[ id ].col = p[1];
    
    db.setWidgetSpan( p[0], p[1], id );
}
/*
##################################################
   指定位置からrow,col分埋める
##################################################
*/
setWidgetSpan( row, col, id ){
    const db = this,
          wp = db.widgetPosition,
          wd = db.widgetInfo[ id ],
          rs = wd.rowspan,
          cs = wd.colspan;
    for ( let i = 0; i < rs; i++ ) {
        const rp = row + i;
        if ( wp[rp] === undefined ) wp[rp] = [];
        for ( let j = 0; j < cs; j++ ) {
            const cp = col + j;
            if ( cp > db.maxColumn ) break;
            // 対象がBlankの場合要素を削除する
            const checkId = wp[rp][cp];
            if ( checkId !== undefined && checkId.match(/^b/) ) {
                $('#' + checkId ).remove();
            }
            wp[rp][cp] = id;
        }
    }
}
/*
##################################################
   Widget移動イベント
##################################################
*/
setWidgetMoveEvent(){
    const db = this;
    
    db.$.dashboard.on('mousedown.moveWidget', '.widget-move-knob', function( e1 ){
        const $widget = $( this ).closest('.widget-grid'),
              id = $widget.attr('id'),
              widgetData = db.widgetInfo[ id ],
              initialId = 'b' + db.widgetBlankCount,
              outerWidth = $widget.outerWidth(),
              height = $widget.height(),
              outerHeight = $widget.outerHeight(),
              positionTop = $widget.offset().top - db.$.window.scrollTop(),
              positionLeft = $widget.offset().left - db.$.window.scrollLeft();

        let targetId = initialId;

        db.onScrollEvent();
        db.removeEditBlankEvent(); // Blank周りのイベントオフ
        fn.deselection(); // 選択の解除
        db.widgetPositionDelete( id ); // 位置情報を削除
        db.paddingBlank(); // 隙間をBlankに 
        db.checkMovableBlank( id ); // 移動可能部分のチェック
        
        $widget.addClass('widget-move').css({
            'left': positionLeft,
            'top': positionTop,
            'width': outerWidth,
            'height': outerHeight,
        });

        // Rowspanが1の場合は置き換わるブランクの高さを調整する
        const $initialBlank = $('#' + initialId ).find('.widget-blank');
        if ( Number( widgetData['rowspan'] ) === 1 ) {
            $initialBlank.css('height', height+'px');
        }

        db.$.dashboard.find('.movable-blank').on({
            'mouseenter.widgetMove': function(){ targetId = $( this ).attr('id'); },
            'mouseleave.widgetMove': function(){ targetId = initialId; }
        });

        db.$.window.on({
            'mousemove.widgetMove': function( e2 ){
                const movePositionTop = e2.pageY - e1.pageY,
                      movePositionLeft = e2.pageX - e1.pageX;
                $widget.css({
                    'transform': 'translate3d(' + movePositionLeft + 'px,' + movePositionTop + 'px,0)'
                });
            },
            'mouseup.widgetMove': function(){
                db.$.window.off('mousemove.widgetMove mouseup.widgetMove');
                db.$.dashboard.find('.movable-blank')
                    .off('mouseenter.widgetMove mouseleave.widgetMove').removeClass('movable-blank');
                $widget.removeClass('widget-move').attr('style', 'grid-area:' + id );
                $initialBlank.removeAttr('style');
                
                db.removeScrollEvent();
                db.widgetPositionChange( targetId, id ); // 対象と位置を入れ替える
                db.updatePosition(); // 位置情報更新
                db.setEditBlankEvent(); // Blank周りのイベントセット
            }
        });
    });  
}
/*
##################################################
   Widget移動イベント削除
##################################################
*/
removeWidgetMoveEvent(){    
    this.$.dashboard.on('mousedown.moveWidget');
}

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   枠外移動スクロール
//
////////////////////////////////////////////////////////////////////////////////////////////////////

/*
##################################################
   スクロールイベントオン
##################################################
*/
onScrollEvent(){
    const db = this;
    
    const scrollSpeed = 80,
          scrollFrame = 1000 / 15;
    let vertical, horizontal;
    
    const dashboardScroll = function() {
        if ( db.scrollTimer === false ) {
            db.scrollTimer = setInterval( function() {
                const scrollTop = db.$.dashboard.scrollTop(),
                      scrollLeft = db.$.dashboard.scrollLeft(),
                      scrollVertical = ( vertical === 'bottom')? scrollSpeed : -scrollSpeed,
                      scrollHorizontal = ( horizontal === 'right')? scrollSpeed : -scrollSpeed;
                
                db.$.dashboard.stop(0,0).animate({
                    scrollTop : scrollTop + scrollVertical,
                    scrollLeft : scrollLeft + scrollHorizontal
                }, scrollSpeed, 'linear');
            }, scrollFrame );
        }
    };
    
    db.$.window.on('mousemove.dashboardScroll', function( e ){
      // 上下左右判定
      const width = db.$.dashboard.outerWidth(),
            height = db.$.dashboard.outerHeight(),
            offsetLeft = db.$.dashboard.offset().left,
            offsetTop = db.$.dashboard.offset().top;

      if ( e.pageY < offsetTop ) vertical = 'top';
      if ( e.pageY > offsetTop + height ) vertical = 'bottom';
      if ( e.pageX < offsetLeft ) horizontal = 'left';
      if ( e.pageX > offsetLeft + width ) horizontal = 'right';
      
      if ( $( e.target ).closest('.dashboard-body').length ) {
        clearInterval( db.scrollTimer );
        db.scrollTimer = false;
      } else {
        dashboardScroll();
      }
    });
}
/*
##################################################
   スクロールイベントオフ
##################################################
*/
removeScrollEvent(){
    const db = this;
    
    db.$.window.off('mousemove.dashboardScroll');
    clearInterval( db.scrollTimer );
    db.scrollTimer = false;
}

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Blank追加・削除
//
////////////////////////////////////////////////////////////////////////////////////////////////////

/*
##################################################
   Blank追加・削除イベントオン
##################################################
*/
setEditBlankEvent() {
    const db = this;
  
    let blankAddTopBottomFlag = '',
        blankAddWidgetSetID = '';
    
    // +Blank barを非表示
    const addWidgetBarHide = function() {
        db.$.dashboard.find('.add-blank').removeAttr('style');
        db.$.dashboard.find('.widget-grid, .widget-blank-grid').off('mousemove.blank');
        blankAddTopBottomFlag = '';
        blankAddWidgetSetID = '';
    };
    
    db.$.dashboard.on({
        'mouseenter.blank': function() {
            const $widget = $( this ),
                  $blankBar = db.$.dashboard.find('.add-blank'),
                  setID = $widget.attr('id'),
                  rowspan = Number( $widget.attr('data-rowspan') ),
                  widgetHeight = $widget.outerHeight(),
                  barLeft = db.$.dashboard.position().left,
                  barTop = $widget.position().top,
                  wp = db.widgetPosition,
                  position = db.getWidgetPosition( setID ),
                  row = position[0],
                  colLength = wp[row].length,
                  barShowArea = 8,
                  areaPadding = 8,
                  scrollTop = db.$.dashboard.scrollTop(),
                  scrollLeft = db.$.dashboard.scrollLeft()

            if ( blankAddWidgetSetID !== setID ) {
                blankAddWidgetSetID = setID;
                blankAddTopBottomFlag = '';
            }

            // 行すべてがBlankの場合削除可能とする
            if ( wp.length > 1 && wp[row].join('').indexOf('w') === -1 ) {
                for ( let i = 0; i < colLength; i++ ) {
                    $('#' + wp[row][i] ).addClass('remove-blank');
                }
            }

            // Widgetの上か下かそれ以外
            const middleBarHide = function() {
                $blankBar.css('display', 'none');
            }
            const topBottomBarSet = function( direction ) {
                const topBottomNum = ( direction === 'top')? -1 : rowspan,
                      topBottomAdd = ( direction === 'top')? 0 : rowspan,
                      topBottomPositionTop = ( direction === 'top')?
                        barTop - areaPadding + scrollTop :
                        barTop - areaPadding + scrollTop + widgetHeight;

                let addFlag = true;
                for ( let i = 0; i < colLength; i++ ) {
                    const currentCol = wp[row][i],
                          checkRow = wp[row+topBottomNum];
                    if ( checkRow !== undefined ) {
                        if ( currentCol === checkRow[i] ) {
                            addFlag = false;
                            break;
                        }
                    }
                }

                if ( addFlag === true ) {
                  $blankBar.css({
                      'display': 'block',
                      'width': 'calc( 100% - 32px)',
                      'left': ( scrollLeft + 16 ) + 'px',
                      'top': topBottomPositionTop
                  }).attr({
                      'data-row': row + topBottomAdd
                  });
                } else {
                    middleBarHide();
                }
            };
            $widget.on('mousemove.blank', function( e ){
              if ( e.pageY - $widget.offset().top > widgetHeight - barShowArea ) {
                      if ( blankAddTopBottomFlag !== 'bottom') {
                          blankAddTopBottomFlag = 'bottom';
                          topBottomBarSet( blankAddTopBottomFlag );
                      }
                  } else if ( e.pageY - $widget.offset().top < barShowArea ) {
                      if ( blankAddTopBottomFlag !== 'top') {
                          blankAddTopBottomFlag = 'top';
                          topBottomBarSet( blankAddTopBottomFlag );
                      }
                  } else {
                      if ( blankAddTopBottomFlag !== 'middle') {
                          blankAddTopBottomFlag = 'middle';
                          middleBarHide();
                      }
                  }
            }); 
        },
        'mouseleave.blank': function(){
            $( this ).off('mousemove.blank');
            db.$.dashboard.find('.remove-blank').removeClass('remove-blank');
        }
    }, '.widget-grid, .widget-blank-grid');
    
    // 枠の外に出たら消す
    db.$.dashboard.on({
        'mouseleave.blankbar': function(){
            addWidgetBarHide();
        },
        'mousemove.blankbar': function( e ){
            if ( e.target.className === 'dashboard-body' ||
                 e.target.className === 'dashboard-area' ) {
                addWidgetBarHide();
            }
        }
    });
    
    // Blankを追加
    db.$.dashboard.on('click.blankadd', '.add-blank', function(){
        const $addBlank = $( this ),
              row = $addBlank.attr('data-row'),
              scrollTop = db.$.dashboard.scrollTop();

        db.widgetPosition.splice( row, 0, []);
        db.paddingBlank();
        db.updatePosition();

        // スクロール位置をBlank追加前と同じにする
        db.$.dashboard.scrollTop( scrollTop );
    });

    // Blankを削除
    db.$.dashboard.on('click.blankremove', '.remove-blank', function(){
        const $blank = $( this ),
              setID = $blank.attr('id'),
              position = db.getWidgetPosition( setID ),
              row = position[0],
              colLength = db.widgetPosition[row].length;

        for ( let i = 0; i < colLength; i++ ) {  
            $('#' + db.widgetPosition[row][i] ).remove();
        }
        db.widgetPosition.splice( row, 1 );
        addWidgetBarHide();
        db.updatePosition();
    });
}
/*
##################################################
   Blank追加・削除イベントオフ
##################################################
*/
removeEditBlankEvent() {
    this.$.dashboard.off('mouseenter.blank mouseleave.blank mouseleave.blankbar mousemove.blankbar click.blankadd click.blankremove');
}

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   個別メニュー移動
//
////////////////////////////////////////////////////////////////////////////////////////////////////

setMenuItemMoveEvent() {
    const db = this;
    
    db.$.area.on({
        'click.moveMenuItem': function( e ) {
            e.preventDefault();
        },
        'mousedown.moveMenuItem': function( e ){
            e.preventDefault();
            
            if ( e.button !== 0 ) return;
            
            db.onScrollEvent();
            db.removeEditBlankEvent();
            fn.deselection();
            
            const $item = $( this ),
                  itemWidth = $item.outerWidth(),
                  itemHeight = $item.outerHeight();
            
            let $targetWidget = $item.closest('.widget-grid');
            $targetWidget.off('mousemove.blank');
            
            // Widgetタイプ
            let widgetId, listType, itemType;
            if ( $item.is('.db-menu-group-link') ) {
                db.$.dashboard.addClass('db-menu-group-moving');
                widgetId = ['0', '1'];
                listType = '.db-menu-group-list';
                itemType = '.db-menu-group-item';
            } else {
                db.$.dashboard.addClass('db-linklist-moving');
                widgetId = ['10'];
                listType = '.db-linklist-list';
                itemType = '.db-linklist-item';
            }
            
            const $list = $item.closest( listType ),
                  $wrap = $item.closest( itemType );
            
            const mouseDownLeft = e.pageX,
                  mouseDownTop = e.pageY,
                  clickPositionLeft = mouseDownLeft - $item.offset().left,
                  clickPositionTop = mouseDownTop - $item.offset().top;
            
            let scrollTop = db.$.window.scrollTop(),
                scrollLeft = db.$.window.scrollLeft(),
                left = mouseDownLeft - scrollLeft - clickPositionLeft,
                top = mouseDownTop - scrollTop - clickPositionTop;
            
            const $clone = $wrap.clone( false );
            $clone.addClass('move').css({
              'width': itemWidth,
              'height': itemHeight,
              'transform': 'translate3d(' + left + 'px,' + top + 'px,0)',
            });
            
            $item.addClass('move-wait');
            $wrap.addClass('current');
            
            $list.append( $clone );
            
            // どのリンクの上か
            let $target = null, leftRight = 0;
            db.$.area.find( itemType ).on({
                'mouseenter.menuItemMove1': function(){
                    $target = $( this );
                },
                'mousemove.menuItemMove1': function( e ){
                    // 左右どちらか判定
                    const $targetTemp = $( this ),
                          width = $targetTemp.width();
                    if ( !$targetTemp.is('.current') ) {
                        if ( e.pageX - $targetTemp.offset().left > width / 2 ) {
                            leftRight = 1;
                            $targetTemp.removeClass('left').addClass('right');
                        } else {
                            leftRight = 0;
                            $targetTemp.removeClass('right').addClass('left');
                        }
                    }
                },
                'mouseleave.menuItemMove1': function(){
                    $target = null;
                    $( this ).removeClass('left right');
                }
            });
            
            // どのWidgetの上か
            const beforeWidgetId = $targetWidget.attr('id');
            db.$.area.find('.widget-grid').on({
                'mouseenter.menuItemMove2': function(){
                    $targetWidget = $( this );
                },
                'mouseleave.menuItemMove2': function(){
                    $targetWidget = null;
                }
            });
            
            // 移動
            db.$.window.on({
                'mousemove.menuItemMove': function( e ) {
                    scrollTop = db.$.window.scrollTop();
                    scrollLeft = db.$.window.scrollLeft();
                    left = e.pageX - scrollLeft - clickPositionLeft;
                    top = e.pageY - scrollTop - clickPositionTop;
                    $clone.css({
                        'transform': 'translate3d(' + left + 'px,' + top + 'px,0)'
                    });
                },
                'mouseup.menuItemMove': function() {
                    db.$.dashboard.removeClass('db-menu-group-moving db-linklist-moving');
                    
                    db.removeScrollEvent();
                    db.setEditBlankEvent(); // Blank周りのイベントセット
                    
                    // イベント削除
                    db.$.window.off('mousemove.menuItemMove mouseup.menuItemMove');
                    db.$.area.find( itemType )
                      .off('mouseenter.menuItemMove1 mousemove.menuItemMove1 mouseleave.menuItemMove1');
                    db.$.area.find('.widget-grid')
                      .off('mouseenter.menuItemMove2 mouseleave.menuItemMove2');
                    
                    // クラス削除
                    $item.removeClass('move-wait');
                    $wrap.removeClass('current');
                    
                    // クローン削除
                    $clone.remove();
                    
                    // 対象があれば移動する
                    if ( $targetWidget !== null ) {
                        const afterWidgetId = $targetWidget.attr('id');
                        db.changeFlag = true;
                        
                        // 別のWidgetに移動した場合
                        if ( afterWidgetId !== beforeWidgetId && widgetId.indexOf( $targetWidget.attr('data-widget-id') ) !== -1 ) {
                            // 対象の１行項目数
                            const menuNumber = db.widgetInfo[ afterWidgetId ].menu_number;
                            $wrap.css('width', `calc(100%/${menuNumber})`);
                        }
                        
                        if ( $target !== null ) {
                            $target.removeClass('left right');
                            if ( leftRight === 0 ) {
                                $wrap.insertBefore( $target );
                            } else {
                                $wrap.insertAfter( $target );
                            }
                        } else {
                            $wrap.appendTo( $targetWidget.find( listType ) );
                        }
                        
                        // データ更新
                        if ( $item.is('.db-menu-group-link') ) {
                            db.updateMenuInfo();
                        } else {
                            const targetArray = [ beforeWidgetId ];
                            if ( beforeWidgetId !== afterWidgetId ) targetArray.push( afterWidgetId )
                            db.updateLinkListInfo( targetArray );
                        }
                    }
                }
              });      
        }
    }, '.db-menu-group-link, .db-linklist-link');
}
removeMenuItemMoveEvent() {
    this.$.area.off('click.moveMenuItem mousedown.moveMenuItem');
}
/*
##################################################
   メニュー情報を更新
##################################################
*/
updateMenuInfo() {
    const db = this;
    
    // ID・Widgetリストの作成
    const idList = {};
    db.$.area.find('.widget-grid[data-widget-id="0"],.widget-grid[data-widget-id="1"]').each(function(){
        const $widget = $( this ),
              setId = $widget.attr('id'),
              $items = $widget.find('.db-menu-group-item');
        $items.each(function(){
            const $item = $( this ),
                  menuId = $item.attr('data-menu-id');
            idList[ menuId ] = {
                position: setId,
                disp_seq: $items.index( $item )
            };
        });
    });
    
    const list = db.info.menu;
    for ( const group of list ) {
        if ( group.parent_id === null ) {
            group.disp_seq = idList[ group.id ].disp_seq;
            group.position = idList[ group.id ].position;
        }
    }
}
/*
##################################################
   リンクリスト情報を更新
##################################################
*/
updateLinkListInfo( targetArray ) {
    const db = this;
    
    for ( const setId of targetArray ) {
        const $widget = db.$.area.find(`#${setId}`),
              info = [];
        $widget.find('.db-linklist-link').each(function(){
            const $link = $( this ),
                  href = decodeURI( $link.attr('href') ),
                  text = $link.text();
            
            info.push({
                name: text,
                url: href
            })
        });
        db.widgetInfo[ setId ].link_list = info;
    }
}
/*
##################################################
   リンクイベント
##################################################
*/
setLinkEvent() {
    const db = this;
    
    db.$.area.on('click', '.db-link', function( e ){
        const $link = $( this ),
              href = $link.attr('href'),
              type = $link.attr('data-type');

        if ( type !== 'blank' && type !== 'same') {
            e.preventDefault();
        }
        
        if ( type === 'window') {
            const width = window.outerWidth - 32,
                  height = window.outerHeight - 32;
            window.open( href, null, `noreferrer=yes,width=${width},height=${height},top=16,left=16`);
        }
        
    });
}

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   データ更新
//
////////////////////////////////////////////////////////////////////////////////////////////////////

/*
##################################################
   リセット
##################################################
*/
resetWidget( $button ) {
    const db = this;
    
    fn.alert(
        getMessage.FTE08049,
        getMessage.FTE08050,
        'confirm',
        {
            ok: { text: getMessage.FTE08051, action: 'default'},
            cancel: { text: getMessage.FTE08052, action: 'normal'}
        }).then(function( flag ){            
            if ( flag ) {
                // リセットデータの登録
                const data = {
                    menu: [],
                    widget: {}
                }
                fn.fetch('/user/dashboard/', null, 'POST', data ).catch(function( error ){
                    alert( error.message );
                }).then(function(){
                    window.location.reload();
                });
            } else {
                $button.prop('disabled', false );
            }
        }
    );
}
/*
##################################################
   編集反映
##################################################
*/
saveWidget() {
    const db = this;
    
    // Widgetの位置をセット
    for ( const setId in db.widgetInfo ) {
        const position = db.getWidgetPosition( setId );
        db.widgetInfo[ setId ].row = position[0];
        db.widgetInfo[ setId ].col = position[1];
    }
    
    // 登録に必要なデータを抽出
    const editMenuData = [];
    for ( const menu of db.info.menu ) {
        if ( menu.parent_id === null ) {
            editMenuData.push({
                id: menu.id,
                disp_seq: menu.disp_seq,
                position: menu.position
            });
        }
    }    
    
    const data = {
        menu: editMenuData,
        widget: db.widgetInfo
    }
    
    fn.fetch('/user/dashboard/', null, 'POST', data ).catch(function( error ){
        alert( error.message );
    }).then(function(){
        window.location.reload();
    });
    
}

}