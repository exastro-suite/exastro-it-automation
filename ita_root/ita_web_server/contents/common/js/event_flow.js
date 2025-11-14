////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Exastro IT Automation / event_flow.js
//
//   -----------------------------------------------------------------------------------------------
//
//   Copyright 2025 NEC Corporation
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

class EventFlow {
/*
##################################################
    Constructor
##################################################
*/
constructor( id ) {
    this.id = id;
    this.uiVersion = fn.getUiVersion();
}
/*
##################################################
    初期値
##################################################
*/
setInitCanvasValue() {
    const er = this;

    const initRange = 1;
    er.initRange = initRange + 'h'; // 初期表示範囲

    er.intervalTime = fn.storage.get('eventflow_interval_time', 'local', false ); // 更新間隔
    if ( er.intervalTime === false ) er.intervalTime = 5000;

    
    er.maxRate = 50; // 最大拡大倍数

    // 倍率
    er.vRate = 1;
    er.hRate = 1;

    // 位置
    er.vPosition = 0;
    er.hPosition = 0;

    // 色
    er.patternColor = {
        conclusion: '255,170,0', // 再評価
        unknown: '175,65,175', // 未知
        timeout: '255,30,30', // 既知（時間切れ）
        evaluated: '189,204,212', // 既知（対処済み）
        newEvent: '40,170,225', // NEW
        action: '0,91,172', // アクション
        rule: '0,156,125' // ルール
    };

    // 表示フラグ
    er.displayFlag = {
        conclusion: true, // 再評価
        unknown: true, // 未知
        timeout: true, // 既知（時間切れ）
        evaluated: true, // 既知（対処済み）
        newEvent: true, // NEW
        action: true, // アクション
        rule: true // ルール
    };

    // パターンリスト
    er.patternList = {
        newEvent: getMessage.FTE13012,
        evaluated: getMessage.FTE13010,
        unknown: getMessage.FTE13008,
        timeout: getMessage.FTE13009,
        conclusion: getMessage.FTE13011,
        action: getMessage.FTE13013,
        rule: getMessage.FTE13030
    };

    // パターンID
    er.patternId = [
        'conclusion', // 再評価: 0
        'unknown', // 未知: 1
        'timeout', // 既知（時間切れ）: 2
        'evaluated', // 既知（判定済）: 3
        'newEvent', // 新規: 4
        'action', // アクション: 5
        'rule' // ルール: 6
    ];

    // 各種フラグ
    er.flag = {
        aggregate: false, // 集約モード
        rangeSelect: false // 範囲選択モード
    };
    
    er.canvasData = [];

    // テーマ
    this.colorMode = ( $('body').is('.darkmode') )? 'darkmode': '';

    // デバッグ用
    er.debug = fn.getParams().debug ?? false;
}
/*
##################################################
    Setup
##################################################
*/
async setup( target ) {
    const er = this;

    er.target = target;

    // Canvas初期値設定
    er.setInitCanvasValue();

    const $target = $( er.target );
    $target.html( er.mainHtml( er.id ) ).addClass('nowLoading');

    // jQuery object
    er.$ = {
        target: $target,
        eventFrow: $target.find('.eventFlow'),
        header: $target.find('.eventFlowHeader'),
        status: $target.find('.eventFlowStatus'),
        body: $target.find('.eventFlowBody'),
        footer: $target.find('.eventFlowFooter'),
        chart: $target.find('.eventFlowChart'),
        scroll: $target.find('.eventFlowChartBar'),
        vScroll: $target.find('.eventFlowChartBar[data-type="vertical"]'),
        hScroll: $target.find('.eventFlowChartBar[data-type="horizontal"]'),
        positionBorder: $target.find('.eventFlowPositionBorder'),
        positionDate: $target.find('.eventFlowPositionDate'),
        nowDate: $target.find('.eventFlowNowDate'),
        info: $target.find('.eventFlowEventInformation'),
        parts: $target.find('.eventFlowParts'),
    };

    // ラベルデータを読み込む
    const data = { discard: { NORMAL: '0'}};
    const option = { authorityErrMove: false };

    // メッセージ表示
    this.message = new Message();

    try {
        er.label = await fn.fetch('/menu/label_creation/filter/', null, 'POST', data, option );
    } catch( error ) {
        console.error( error );
        er.label = null;
    } finally {
        await er.setupParts();
        $target.removeClass('nowLoading');
        await er.initCanvas();
        er.setEvents();
        er.statusWaiting();
    }

    return;
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//  HTML
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    Main HTML
##################################################
*/
mainHtml( id ) {
    const er = this;

    const rangeSelectHtml = ``
    + `<div class="eventFlowChartRange">`
        + `<span class="icon icon-search"></span>`
        + `<div class="eventFlowChartRangeDate"></div>`
        + `<button class="eventFlowChartRangeClear"><span class="icon icon-cross"></span></button>`
    + `</div>`;

    const aggregateFlag = ( er.flag.aggregate )? 'on': 'off';

    const menuList = {
        Main: [
            { html: { html: er.dateRangeSelectHTML() }},
            { button: { icon: 'cal', text: getMessage.FTE13014, type: 'timeRange', action: 'default'}},
            { html: { html: rangeSelectHtml }, separate: true, className: 'eventFlowChartRangeItem', display: 'none'},
            { html: { html: er.patternSelectHTML() }, separate: true }
        ],
        Sub: [
            { html: { html: er.statusBarHTML() }},
            { html: { html: er.updateIntervalSelectHTML() } },
            { button: { icon: 'menuGroup', text: getMessage.FTE13036, type: 'modeToggle', action: 'default',
                toggle: { init: aggregateFlag, on: getMessage.FTE13038, off: getMessage.FTE13037 }}},
        ]
    };

    return ``
    + `<div id="${id}_eventFlow" class="eventFlowContainer">`
        + `<div class="eventFlow tableLoading eventFlowAggregate_${aggregateFlag}">`
            + `<div class="eventFlowInner">`
                + `<div class="eventFlowHeader">`
                    + fn.html.operationMenu( menuList )
                + `</div>`
                + `<div class="eventFlowBody">`
                    + `<div class="eventFlowBodyInner">`
                        + `<div class="eventFlowDate">`
                            + `<canvas class="eventFlowDateCanvas"></canvas>`
                        + `</div>`
                        + `<div class="eventFlowChart">`
                            + `<div class="eventFlowChartCanvas">`
                                + `<canvas class="eventFlowChartPositionLineCanvas"></canvas>`
                                + `<canvas class="eventFlowChartBlockCanvas"></canvas>`
                                + `<canvas class="eventFlowChartIncidentCanvas"></canvas>`
                                + `<canvas class="eventFlowChartLinkCanvas"></canvas>`
                            + `</div>`
                            + `<div class="eventFlowCurrentBorder"></div>`
                            + `<div class="eventFlowPositionBorder"></div>`
                        + `</div>`
                        + `<div class="eventFlowChartBar" data-type="vertical">`
                            + `<div class="eventFlowRange">`
                                + `<div class="eventFlowRangeStart"></div>`
                                + `<div class="eventFlowRangeEnd"></div>`
                            + `</div>`
                        + `</div>`
                        + `<div class="eventFlowChartBar" data-type="horizontal">`
                            + `<div class="eventFlowRange">`
                                + `<div class="eventFlowRangeStart"></div>`
                                + `<div class="eventFlowRangeEnd"></div>`
                            + `</div>`
                        + `</div>`
                    + `</div>`
                    + `<div class="eventFlowEventInformation"></div>`
                    + `<div class="eventFlowPositionDate"></div>`
                    + `<div class="eventFlowNowDate"></div>`
                + `</div>`
                //+ `<div class="eventFlowFooter"></div>`
            + `</div>`
        + `</div>`
        + `<div class="eventFlowWidthResizeBar"></div>`
        + `<div class="eventFlowParts">`
            + `<div class="eventFlowPartsBlock eventFlowPartsBlockFilter"></div>`
            + `<div class="eventFlowPartsBlock eventFlowPartsBlockAction"></div>`
            + `<div class="eventFlowPartsBlock eventFlowPartsBlockRule"></div>`
        + `</div>`
    + `</div>`
}
/*
##################################################
    Header 期間選択HTML
##################################################
*/
dateRangeSelectHTML() {
    const er = this;

    const commonClassName = 'eventFlowDateRange';

    const list = [
        {id: '5M', text: getMessage.FTE13019(5) },
        {id: '15M', text: getMessage.FTE13019(15) },
        {id: '30M', text: getMessage.FTE13019(30) },
        {id: '1h', text: getMessage.FTE13020(1) },
        {id: '3h', text: getMessage.FTE13020(3) },
        {id: '6h', text: getMessage.FTE13020(6) },
        {id: '12h', text: getMessage.FTE13020(12) },
        {id: '24h', text: getMessage.FTE13020(24) },
        {id: '2d', text: getMessage.FTE13021(2) },
        {id: '1w', text: getMessage.FTE13022(1) },
        {id: '1m', text: getMessage.FTE13023(1) },
        {id: '3m', text: getMessage.FTE13023(3) },
        {id: '6m', text: getMessage.FTE13023(6) },
        {id: '1y', text: getMessage.FTE13024(1) },
        {id: '2y', text: getMessage.FTE13024(2) },
        {id: '5y', text: getMessage.FTE13024(5) }
    ];

    const initItem = list.find(function( item ){
        return item.id === er.initRange;
    });

    const listHtml = [];

    for ( const item of list ) {
        const html = er.addSelectRange( item.id, item.id, item.text, ( item.id === initItem.id ) );
        listHtml.push( html );
    }

    return ``
    + `<div class="${commonClassName} eventFlowSelectWrap">`
        + `<button class="${commonClassName}Button eventFlowSelectButton">${initItem.text}</button>`
        + `<div class="${commonClassName}Block eventFlowOpenBlock">`
            + `<div class="${commonClassName}BlockInner">`
                + `<div class="${commonClassName}ListWrap">`
                    + `<ul class="${commonClassName}List">`
                        + listHtml.join('')
                    + `</ul>`
                + `</div>`
                + `<div class="${commonClassName}LogWrap">`
                + `<div class="${commonClassName}LogTitle">${getMessage.FTE13016}</div>`
                + `<ul class="${commonClassName}Log">`
                + `</ul>`
                + `</div>`
            + `</div>`
        + `</div>`
    + `</div>`;
}
/*
##################################################
    範囲Radio HTML
##################################################
*/
addSelectRange( id, value, text, checked = false ) {
    const er = this;

    const commonClassName = 'eventFlowDateRange';

    const
    name = `${er.id}_${commonClassName}Radio`,
    nameid = `${name}_${id}`;

    checked = ( checked )? { checked: 'checked'}: {};

    return `<li class="${commonClassName}Item">`
        + fn.html.radioText(`${commonClassName}Radio`, value, name, nameid, checked, text )
    + `</li>`;
}
/*
##################################################
    Header パターン選択HTML
##################################################
*/
patternSelectHTML() {
    const er = this;

    const commonClassName = 'eventFlowPatternSelect';

    const listHtml = [];
    for ( const key in er.patternList ) {
        const
        name = `${er.id}_${commonClassName}Checkbox`,
        id = `${name}_${key}`,
        text = `<span class="${commonClassName}Bar" style="background:${er.getPatternColor(key)};"></span>${fn.cv( er.patternList[key], '', true )}`;

        const checked = ( er.displayFlag[key] )? {checked: 'checked'}: {};

        listHtml.push(`<li class="${commonClassName}Item">`
            + fn.html.checkboxText(`${commonClassName}Checkbox`, key, name, id, checked, text )
        + `</li>`);
    }

    return ``
    + `<div class="${commonClassName} eventFlowSelectWrap">`
        + `<button class="${commonClassName}Button eventFlowSelectButton">${getMessage.FTE13017}</button>`
        + `<div class="${commonClassName}ListBlock eventFlowOpenBlock">`
            + `<ul class="${commonClassName}List">`
                + listHtml.join('')
            + `</ul>`
        + `</div>`
    + `</div>`;
}
/*
##################################################
    Header 更新間隔選択HTML
##################################################
*/
updateIntervalSelectHTML() {
    const er = this;

    const commonClassName = 'eventFlowIntervalSelect';

    const intervalList = {
        '0': getMessage.FTE13027,
        '1000': getMessage.FTE13028(1),
        '5000': getMessage.FTE13028(5),
        '10000': getMessage.FTE13028(10),
        '30000': getMessage.FTE13028(30),
        '60000': getMessage.FTE13028(60),
    };

    const listHtml = [];
    for ( const key in intervalList ) {
        const
        name = `${er.id}_${commonClassName}Radio`,
        id = `${name}_${key}`;

        const checked = ( er.intervalTime === Number( key ) )? {checked: 'checked'}: {};

        listHtml.push(`<li class="${commonClassName}Item">`
            + fn.html.radioText(`${commonClassName}Radio`, key, name, id, checked, intervalList[ key ] )
        + `</li>`);
    }

    const initNum = ( er.intervalTime !== 0 )? getMessage.FTE13028( er.intervalTime / 1000 ): getMessage.FTE13027;

    return ``
    + `<div class="${commonClassName} eventFlowSelectWrap">`
        + `<button class="${commonClassName}Button eventFlowSelectButton">`
            + `<span class="${commonClassName}Name">${getMessage.FTE13029}</span><span class="${commonClassName}Number">${initNum}</span>`
        + `</button>`
        + `<div class="${commonClassName}ListBlock eventFlowOpenBlock">`
            + `<ul class="${commonClassName}List">`
                + listHtml.join('')
            + `</ul>`
        + `</div>`
    + `</div>`;
}
/*
##################################################
    Header ステータスバー
##################################################
*/
statusBarHTML() {
    this.statusResponseFlag = false;
    return `<div class="eventFlowStatus"><div class="eventFlowStatusText"></div><div class="eventFlowStatusBar"></div></div>`;
}
statusWaiting() {
    this.$.status.find('.eventFlowStatusBar').hide();
    this.$.status.hide().find('.eventFlowStatusText').text('');
    // 応答待機中の場合は表示する
    if ( this.statusResponseFlag === true ) {
        this.statusResponse();
    }
}
statusProcessing() {
    this.$.status.find('.eventFlowStatusBar').hide();
    this.$.status.show().find('.eventFlowStatusText').text( getMessage.FTE13039 );
}
statusResponse() {
    this.statusResponseFlag = true;
    this.$.status.find('.eventFlowStatusBar').hide();
    this.$.status.show().find('.eventFlowStatusText').text( getMessage.FTE13040 );
}
statusNone() {
    this.$.status.find('.eventFlowStatusBar').hide();
    this.$.status.hide().find('.eventFlowStatusText').text('');
}
statusProgress( result ) {
    this.statusResponseFlag = false;
    const per = Math.round( result.receivedLength / result.contentLength * 100 )  + '%';
    this.$.status.show();
    this.$.status.find('.eventFlowStatusText').text(`${getMessage.FTE13041}(${per})`);
    this.$.status.find('.eventFlowStatusBar').show().css('width', per );
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Worker
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    Create WebWorker
##################################################
*/
createWebWorker() {
    const workerCode = this.createWorkerCode();
    const blob = new Blob([ workerCode ], { type: "text/javascript" });
    const url  = URL.createObjectURL( blob );
    this.worker = new Worker( url );
    this.worker.onmessage = e => this.workerOnMessage( e );
    this.worker.init = false;
}
// Worker Code
createWorkerCode() {
    const commonUrl = new URL(`/_/ita/js/common.js?v=${this.uiVersion}`, location.href ).href;
    const workerClassUrl = new URL(`/_/ita/js/event_flow_worker.js?v=${this.uiVersion}`, location.href ).href;
    return ``
    + `importScripts('${commonUrl}');`
    + `importScripts('${workerClassUrl}');`
    + `(function(){`
        + `const eventFlowWorker = new EventFlowWorker();`
        + `self.addEventListener('message', function( message ){`
            + `eventFlowWorker.message( message.data );`
        + `});`
    + `}());`
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//  WebWorker on message
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    Workerメッセージ受信
##################################################
*/
async workerOnMessage( e ) {
    const result = e.data;
    switch ( result.type ) {
        case 'autoModeChange':
            this.autoModeChange();
            break;
        case 'progress': 
            this.progress( result );
            break;
        case 'updateToken':
            this.workerMessageUpdateToken();
            break;
        case 'updateDate':
            this.workerMessageUpdateDate( result );
            break;
        case 'nowLine': 
            this.workerMessageNowLine( result.nowX );
            break;
        
        // Resolve
        case 'currentEnter':
            this.worker.currentEnter.resolve( result.flag );
            break;
        case 'positionChange':
            this.worker.positionChange.resolve();
            break;
        case 'blockEnter':
            this.worker.blockEnter.resolve({
                currentBlock: result.currentBlock,
                grouping: result.grouping
            });
            break;
        case 'modeChange':
            this.worker.modeChange.resolve();
            break;
        case 'updateEventLink':
            this.worker.updateEventLink.resolve();
            break;
        default: this.worker.resolve()
    }
}
/*
##################################################
    進捗表示
##################################################
*/
progress( result ) {
    if ( result.text === 'start') {
        this.statusResponse();
    } else if ( result.text === 'end') {
        this.statusWaiting();
    } else if ( result.text === 'process') {
        this.statusProcessing();
    } else if ( result.receivedLength !== undefined && result.contentLength !== undefined ) {
        this.statusProgress( result );
    } else {
        this.statusNone();
    }
}
/*
##################################################
    集約モードに変更する
##################################################
*/
autoModeChange() {
    this.message.add('warning', getMessage.FTE13035 );
    this.modeAggregateOn( this.$.header.find('.toggleButton') );
}
/*
##################################################
    トークンをWorkerに返す
##################################################
*/
workerMessageUpdateToken() {
    // Token
    const token = ( fn.getCmmonAuthFlag() )? CommonAuth.getToken():
        ( window.parent && window.parent.getToken )? window.parent.getToken(): null;    

    this.worker.postMessage(
        {
            type: 'updateToken',
            token: token
        }
    );
}
/*
##################################################
    現在時刻線
##################################################
*/
workerMessageNowLine( nowX ) {
    const paddingLeft = 16; // .eventFlowBodyInner
    
    if ( nowX > this.w ) {
        this.$.nowDate.hide();
    } else if ( nowX < 0 ) {
        this.$.nowDate.show().addClass('noBorder').css({
            left: paddingLeft,
            width: this.w
        });
    } else {
        this.$.nowDate.show().removeClass('noBorder').css({
            left: nowX + paddingLeft,
            width: this.w - nowX
        });
    }
}
/*
##################################################
    範囲時間更新
##################################################
*/
workerMessageUpdateDate( date ) {
    this.start = date.start;
    this.end = date.end;
    this.period = date.period;
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//  Web Worker post message
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    Worker Post
##################################################
*/
workerPost( type, option, reslveType = false ) {
    return new Promise(( resolve, reject ) => {
        if ( reslveType === false ) {
            this.worker.resolve = resolve;
            this.worker.reject = reject;
        } else {
            this.worker[ type ] = {
                resolve: resolve,
                reject: reject
            };
        }
        switch ( type ) {
            case 'modeChange':
                this.workerModeChange();
                break;
            case 'positionChange':
                this.workerPositionChange();
                break;
            case 'currentEnter':
                this.workerCurrentEnter( option );
                break;
            case 'blockEnter':
                this.workerBlockEnter( option );
                break;
            case 'updateEventLink':
                this.workerUpdateEventLink();
                break;
        }
    });
}
/*
##################################################
    ポーリング開始
##################################################
*/
workerPollingStart( mode ) {
    // 時間をセット
    const selectDateRange = this.$.header.find('.eventFlowDateRangeRadio:checked').val();

    this.getCanvasSize();

    this.worker.postMessage(
        {
            type: 'polling',
            pollingStartMode: mode,
            interval: this.intervalTime,
            w: this.w,
            h: this.h,
            vRate: this.vRate,
            vPosition: this.vPosition,
            hRate: this.hRate,
            hPosition: this.hPosition,
            selectDateRange: selectDateRange,
            rangeSelectFlag: this.flag.rangeSelect,
            displayFlag: this.displayFlag,
            aggregate: this.flag.aggregate
        }
    );
}
/*
##################################################
    モード変更
##################################################
*/
workerModeChange() {
    this.clickBlock = null;
    this.currentBlock = null;
    this.hideEventInfo();
    this.positionReset();
    this.worker.postMessage(
        {
            type: 'modeChange',
            aggregate: this.flag.aggregate,
            vRate: this.vRate,
            vPosition: this.vPosition,
            hRate: this.hRate,
            hPosition: this.hPosition,
            basisEventBlock: {
                current: this.currentBlock,
                click: this.clickBlock
            } 
        }
    );
}
/*
##################################################
    範囲変更
##################################################
*/
workerRangeChange() {
    this.getCanvasSize();
    this.worker.postMessage(
        {
            type: 'rangeChange',
            start: this.start,
            end: this.end,
            w: this.w,
            h: this.h,
            rangeSelectFlag: this.flag.rangeSelect,
            vRate: this.vRate,
            vPosition: this.vPosition,
            hRate: this.hRate,
            hPosition: this.hPosition,
            displayFlag: this.displayFlag
        }
    );
}
/*
##################################################
    範囲クリア
##################################################
*/
workerRangeClear() {
    this.worker.postMessage(
        {
            type: 'rangeClear',
            start: null,
            end: null,
            rangeSelectFlag: this.flag.rangeSelect,
            vRate: this.vRate,
            vPosition: this.vPosition,
            hRate: this.hRate,
            hPosition: this.hPosition
        }
    );
}
/*
##################################################
    位置変更
##################################################
*/
workerPositionChange() {
    this.worker.postMessage(
        {
            type: 'updateCanvasPosition',
            vRate: this.vRate,
            vPosition: this.vPosition,
            hRate: this.hRate,
            hPosition: this.hPosition
        }
    );
}
/*
##################################################
    現在ホバーしているイベント判定
##################################################
*/
workerCurrentEnter( position ) {
    this.worker.postMessage(
        {
            type: 'currentEnter',
            position: position
        }
    );
}
/*
##################################################
    ホバーイベント判定
##################################################
*/
workerBlockEnter( position ) {
    this.worker.postMessage(
        {
            type: 'blockEnter',
            position: position
        }
    );
}
/*
##################################################
    イベント繋がり線を描画
##################################################
*/
workerUpdateEventLink( event ) {
    this.worker.postMessage(
        {
            type: 'updateEventLink',
            basisEventBlock: {
                current: this.currentBlock,
                click: this.clickBlock
            } 
        }
    );
}
/*
##################################################
    Canvasサイズ取得
##################################################
*/
getCanvasSize() {
    this.w = this.$.chart.outerWidth();
    this.h = this.$.chart.outerHeight();
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//  Canvas
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    初期設定
##################################################
*/
async initCanvas() {
    // Chart canvas
    this.chartCanvas = {
        line: this.$.body.find('.eventFlowChartPositionLineCanvas').get(0), // スケールライン
        block: this.$.body.find('.eventFlowChartBlockCanvas').get(0), // 囲い
        incident: this.$.body.find('.eventFlowChartIncidentCanvas').get(0), // イベント
        link: this.$.body.find('.eventFlowChartLinkCanvas').get(0) // 繋がり線
    };

    // 目盛り Date canvas
    this.dateCanvas = this.$.body.find('.eventFlowDateCanvas').get(0);

    // ワーカー初期化
    this.createWebWorker();

    // フォントデータをArrayBufferとして転送
    const fontResponse = await fetch('/_/ita/fonts/exastro-ui-icons.woff');
    const fontBuffer = await fontResponse.arrayBuffer();

    await new Promise(( resolve, reject ) => {
        this.worker.resolve = resolve;
        this.worker.reject = reject;

        // 履歴取得API
        const historyUrl = fn.getRestApiUrl('/oase/event_flow/history/');
        const url = new URL( historyUrl, location.href ).href;

        // Canvas要素の描画コントロールをOffscreenCanvasに委譲する
        const line = this.chartCanvas.line.transferControlToOffscreen();
        const block = this.chartCanvas.block.transferControlToOffscreen();
        const incident = this.chartCanvas.incident.transferControlToOffscreen();
        const link = this.chartCanvas.link.transferControlToOffscreen();
        const date = this.dateCanvas.transferControlToOffscreen();

        this.worker.postMessage(
            {
                type: 'init',
                line: line,
                block: block,
                incident: incident,
                link: link,
                date: date,
                url: url,
                fontBuffer: fontBuffer,
                debug: this.debug
            },
            [ line, block, incident, link, date, fontBuffer ]
        );
    });

    this.workerPollingStart('init');
    this.$.eventFrow.removeClass('tableLoading');
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//  Events
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    Events
##################################################
*/
setEvents() {
    const er = this;

    er.setChartEvents();
    er.setSelectButtonToggleEvent();
    er.setPatternSelectEvent();
    er.setUpdateIntervalEvent();
    er.setScrollBarEvent();
    er.canvasSizeResizeObserver();

    er.setMenuButtonEvent();
    er.setTabEvent();
    er.modeChangeEvent();
}
/*
##################################################
    Canvasサイズの変更を監視
##################################################
*/
canvasSizeResizeObserver() {
    const er = this;

    er.observeInit = true;

    let timer;
    const observer = new ResizeObserver(function(){
        if ( er.observeInit === false ) {
            clearTimeout( timer );
            timer = setTimeout( function() {
                er.workerRangeChange();
            }, 500 );
        }
        er.observeInit = false;
    });

    observer.observe( er.$.chart.get(0) );
}
/*
##################################################
    現在位置の情報を表示
##################################################
*/
viewCurrentInfo( dateX, x, y ) {
    const er = this;

    const positionDate = er.getPositionDate( dateX );
    er.$.positionDate.css({
        left: x + 16,
        top: y + 16
    }).text( fn.date( positionDate, 'yyyy/MM/dd HH:mm:ss'));
}
/*
##################################################
    イベント情報タブ切り替え
##################################################
*/
setTabEvent() {
    const er = this;

    er.$.info.on('click', '.eventInfoTabItem', function(){
        const $item = $( this ), $wrap = $item.closest('.eventInfoContainer');

        if ( !$item.is('.open') ) {
            const index = $wrap.find('.eventInfoTabItem').index( this );
            $wrap.find('.open').removeClass('open');
            $( this ).add( $wrap.find('.eventInfoTabBlock').eq( index ) ).addClass('open');
        }
    });
}
/*
##################################################
    Chart events
##################################################
*/
setChartEvents() {
    const er = this;

    er.currentBlock = null;

    const $window = $( window );
    const $rangeDate = er.$.header.find('.eventFlowChartRangeItem');
    const $vRange = er.$.vScroll.find('.eventFlowRange');
    const $hRange = er.$.hScroll.find('.eventFlowRange');

    // leave
    const blockLeave = async function() {
        if ( er.currentBlock ) {
            er.$.chart.css('cursor', 'default');
        }
        er.currentBlock = null;

        // 繋がり線
        await er.workerPost('updateEventLink', null, true );
    };

    // 範囲指定モードフラグ
    let dateRangeSelectMode = false;

    // 図の上に乗っているか
    let chartEnterFlag = false;

    // ホイールで拡大・縮小
    const rafWheelEvent =  er.rafThrottle( async function( e ) {
        e.preventDefault();

        // 集約モードの場合は停止
        if ( er.flag.aggregate ) return;

        const chart = $( this ).get(0);
        const delta = e.originalEvent.deltaY ?
            - ( e.originalEvent.deltaY ):
                e.originalEvent.wheelDelta?
                    e.originalEvent.wheelDelta:
                    - ( e.originalEvent.detail ); // ホイール向き

        if ( e.shiftKey ){
            const y = e.pageY - chart.getBoundingClientRect().top; // y
            const positionRate = ( y + er.vPosition ) / ( er.h * er.vRate ); // 位置割合

            // 拡大縮小
            const rateNumber = Math.floor( er.vRate * 0.2 * 10 ) / 10;
            if ( delta < 0 ) {
                er.vRate -= rateNumber;
            } else {
                er.vRate += rateNumber;
            }
            if ( er.vRate <= 1 ) er.vRate = 1;
            if ( er.vRate >= er.maxRate ) er.vRate = er.maxRate;

            // 拡縮後サイズ
            const afterHeight = er.h * er.vRate;

            // 拡縮後の位置
            const position = afterHeight - ( afterHeight * positionRate );
            er.vPosition = afterHeight - position - y;

            // はみ出る場合の調整
            if ( er.vPosition < 0 ) er.vPosition = 0;
            if ( afterHeight - er.vPosition < er.h ) er.vPosition = afterHeight - er.h;

            // スクロールバーサイズ
            $vRange.css({
                height: ( 100 / er.vRate ) + '%',
                top: ( er.vPosition / ( er.h * er.vRate ) * 100 ) + '%'
            });
            
        } else {
            const x = e.pageX - chart.getBoundingClientRect().left; // X
            const positionRate = ( x + er.hPosition ) / ( er.w * er.hRate ); // 位置割合

            // 拡大縮小
            const rateNumber = Math.floor( er.hRate * 0.2 * 10 ) / 10;
            if ( delta < 0 ) {
                er.hRate -= rateNumber;
            } else {
                er.hRate += rateNumber;
            }
            if ( er.hRate <= 1 ) er.hRate = 1;
            if ( er.hRate >= er.maxRate ) er.hRate = er.maxRate;

            // 拡縮後サイズ
            const afterWidth = er.w * er.hRate;

            // 拡縮後の位置
            const position = afterWidth - ( afterWidth * positionRate );
            er.hPosition = afterWidth - position - x;

            // はみ出る場合の調整
            if ( er.hPosition < 0 ) er.hPosition = 0;
            if ( afterWidth - er.hPosition < er.w ) er.hPosition = afterWidth - er.w;

            // スクロールバーサイズ
            $hRange.css({
                width: ( 100 / er.hRate ) + '%',
                left: ( er.hPosition / ( er.w * er.hRate ) * 100 ) + '%'
            });
        }

        // Canvas更新
        await er.workerPost('positionChange', null, true );
    } );

    // ポインタームーブ
    const rafPointerMoveEvent = er.rafThrottle( async function( e ) {
        const
        chart = $( this ).get(0),
        x = e.pageX - chart.getBoundingClientRect().left,
        y = e.pageY - chart.getBoundingClientRect().top;

        if ( chartEnterFlag === false ) {
            er.$.positionBorder.css('display', 'block');
            er.$.positionDate.css('display', 'block');
            chartEnterFlag = true;
        }

        if ( !dateRangeSelectMode ) {
            // ポインター位置Xバー
            er.$.positionBorder.css({
                transform: `translateX(${x-1}px)`
            });

            er.viewCurrentInfo( x, e.pageX, e.pageY );

            // 集約モードの場合は停止
            if ( er.flag.aggregate ) return;

            const position = {
                x: x,
                y: y,
                current: er.currentBlock
            };

            // Block leave
            if ( er.currentBlock ) {
                const enterFlag = await er.workerPost('currentEnter', position, true );
                if ( !enterFlag ) blockLeave();
            }

            const enterEvent = await er.workerPost('blockEnter', position, true );
            if ( enterEvent.currentBlock !== null ) {
                er.$.chart.css('cursor', 'pointer');
                er.currentBlock = enterEvent.currentBlock;
                if ( enterEvent.grouping ) er.currentGrouping = enterEvent.grouping;

                await er.workerPost('updateEventLink', null, true );
            }
        } else {
            // Block leave
            if ( er.currentBlock ) blockLeave();
        }
    });

    er.$.chart.on({
        'wheel': rafWheelEvent,
        'pointerdown': function( e ) {
            const
            chart = $( this ).get(0),
            x = e.pageX - chart.getBoundingClientRect().left;
            fn.deselection();

            let pX, pW;
            $window.on({
                'pointermove.dateRangeSelect': function( moveEvent ){
                    let moveX = moveEvent.pageX - chart.getBoundingClientRect().left;
                    if ( moveX <= 0 ) moveX = 0;
                    if ( moveX >= er.w ) moveX = er.w;

                    pX = ( moveX > x )? x: moveX,
                    pW = ( moveX > x )? moveX - x: x - moveX;
                    er.$.positionBorder.css({
                        transform: `translateX(${pX}px)`,
                        width: pW
                    });

                    // 4px移動したら範囲指定モードに移行する
                    if ( pW > 4 ) {
                        dateRangeSelectMode = true;
                        er.$.positionBorder.addClass('dateRangeSelect');
                        er.viewCurrentInfo( pX + pW, moveEvent.pageX, moveEvent.pageY );
                    }
                },
                'pointerup.dateRangeSelect': function(){
                    $window.off('pointermove.dateRangeSelect pointerup.dateRangeSelect');

                    if ( dateRangeSelectMode ) {
                        er.$.positionBorder.removeClass('dateRangeSelect').css('width', 1 );
                        dateRangeSelectMode = false;

                        const end = er.getPositionDate( pX + pW );
                        let start = er.getPositionDate( pX );

                        // 範囲が1秒未満の場合は１秒にする
                        const diff = ( er.end - er.start ) / 1000;
                        if ( diff <= 1 ) start = new Date( end.getTime() - 1000 );

                        const
                        startText = fn.date( start, 'yyyy/MM/dd HH:mm:ss'),
                        endText = fn.date( end, 'yyyy/MM/dd HH:mm:ss');
                        $rangeDate.show().find('.eventFlowChartRangeDate').text(`${startText} to ${endText}`);

                        er.changeDateReset( start.getTime(), end.getTime(), true );
                        er.flag.rangeSelect = true;
                    }
                }
            });
        },
        'pointerup': async function( e ) {
            const
            chart = $( this ).get(0),
            x = e.pageX - chart.getBoundingClientRect().left;

            // イベント詳細情報表示
            if ( !dateRangeSelectMode && er.currentBlock ) {
                er.clickBlock = er.currentBlock;
                er.clickGrouping = er.currentGrouping;
                er.viewEventInfo( x );
            } else if ( !dateRangeSelectMode ) {
                er.clickBlock = null;
                er.clickGrouping = null;
                er.hideEventInfo();
            }

            // 集約モードの場合は停止
            if ( er.flag.aggregate ) return;

            await er.workerPost('updateEventLink', null, true );
        },
        'pointerenter': function() {
            er.$.positionBorder.css('display', 'block');
            er.$.positionDate.css('display', 'block');
            chartEnterFlag = true;
        },
        'pointerleave': function() {
            if ( !dateRangeSelectMode ) {
                er.$.positionBorder.css('display', 'none');
                er.$.positionDate.css('display', 'none');
            }

            // Block leave
            if ( er.currentBlock ) {
                blockLeave();
            }
        },
        'pointermove': rafPointerMoveEvent            
    });

    const
    $dateRange = er.$.header.find('.eventFlowDateRangeBlock'),
    $dateRangeButton = er.$.header.find('.eventFlowDateRangeButton');

    // 絞り込みクリア
    $rangeDate.find('.eventFlowChartRangeClear').on('click', function(){
        const date = er.$.header.find('.eventFlowDateRangeRadio').filter(':checked').val();
        $rangeDate.hide().find('.eventFlowChartRangeDate').text('');
        er.clearDataRange( date, true );
        er.flag.rangeSelect = false;
    });

    // 表示範囲切替
    $dateRange.on('change', '.eventFlowDateRangeRadio', function(){
        const $input = $( this );
        $dateRangeButton.text( $input.next('.radioTextLabel').text() );

        er.workerPollingStart('rangeChange');

        // リストが開いていたら閉じる
        if ( $dateRangeButton.is('.open') ) {
            $dateRangeButton.click();
        }
    });
}
/*
##################################################
    Header select button
##################################################
*/
setSelectButtonToggleEvent() {
    const er = this;

    er.$.header.find('.eventFlowSelectButton').on('click', function(){
        const
        $window = $( window ),
        $button = $( this ),
        $wrap = $button.closest('.eventFlowSelectWrap'),
        $block = $button.next('.eventFlowOpenBlock');

        $button.toggleClass('open');
        $block.toggle();

        if ( $button.is('.open') ) {
            $window.on('pointerdown.eventFlowSelect', function( e ){
                if ( !$( e.target ).closest( $wrap ).length ) {
                    $window.off('pointerdown.eventFlowSelect');
                    $button.removeClass('open');
                    $block.hide();
                }
            });

            // 画面内に収まるように高さを調整
            $block.css('height', 'auto'); // サイズリセット

            const
            margin = 8,
            y = $block.get(0).getBoundingClientRect().top,
            h = $block.outerHeight() + margin,
            wH = window.innerHeight;

            if ( y + h > wH ) {
                let height = wH - y - margin;
                if ( height < 160 ) height = 160;
                $block.outerHeight( height );
            }
        } else {
            $window.off('pointerdown.eventFlowSelect');
            if ( $button.is('.eventFlowIntervalSelectButton') ) {
                er.workerPollingStart('interval');
            }
        }
    });
}
/*
##################################################
    パターン選択
##################################################
*/
setPatternSelectEvent() {
    const er = this;

    const $patternCheckbox = er.$.header.find('.eventFlowPatternSelectCheckbox');

    $patternCheckbox.on('change', function(){
        $patternCheckbox.each(function(){
            const
            $check = $( this ),
            value = $check.val(),
            flag = $check.prop('checked');

            er.displayFlag[ value ] = flag;
        });
        er.workerRangeChange();
    });
}
/*
##################################################
    更新間隔選択
##################################################
*/
setUpdateIntervalEvent() {
    const er = this;

    const
    $button = er.$.header.find('.eventFlowIntervalSelectButton'),
    $Num = er.$.header.find('.eventFlowIntervalSelectNumber'),
    $radio = er.$.header.find('.eventFlowIntervalSelectRadio');

    $radio.on('change', function(){
        const val = Number( $( this ).val() );
        er.intervalTime = er.resumeDate = val;

        fn.storage.set('eventflow_interval_time', val, 'local', false );

        const text = ( val !== 0 )? getMessage.FTE13028( val / 1000 ): getMessage.FTE13027;
        $Num.text( text );
        $button.click();
    });
}
/*
##################################################
    Menu button
##################################################
*/
setMenuButtonEvent() {
    const er = this;
    er.$.header.find('.operationMenuButton').on('click', function(){
        const
        $button = $( this ),
        type = $button.attr('data-type');

        switch ( type ) {
            case 'timeRange':
                er.selectDateRange();
                break;
        }
    });
}
/*
##################################################
    日時指定
##################################################
*/
selectDateRange() {
    const er = this;

    const checkedValue = er.$.header.find('.eventFlowDateRangeRadio:checked').val();

    const date = { from: '', to: ''};
    if ( checkedValue && checkedValue.match(/ to /) ) {
        const fromto = checkedValue.split(' to ');
        date.from = fromto[0];
        date.to = fromto[1];
    }

    fn.datePickerDialog('fromTo', true, getMessage.FTE13014, date, true ).then(function( date ){
        if ( date !== 'cancel') {
            const value = `${date.from} to ${date.to}`;
            er.addDateRadioList( value );
        }
    });
}
/*
##################################################
    範囲追加
##################################################
*/
addDateRadioList( value ) {
    const er = this;
    const id = Date.now()
    // リスト追加
    const $list = er.$.header.find('.eventFlowDateRangeLog');
    const $wrap = $list.closest('.eventFlowDateRangeLogWrap');

    if ( $list.find(`[value="${value}"]`).length === 0 ) {
        $list.prepend( er.addSelectRange( id, value, value ) );
        if ( $wrap.is(':hidden') ) $wrap.addClass('setDate');
    }

    er.$.header.find('.eventFlowDateRangeRadio').val([ value ]).filter(`[value="${value}"]`).change();
}
/*
##################################################
    範囲設定
##################################################
*/
setSelectDateRange() {
    const er = this;

    const value = $('.eventFlowChartRangeDate').text();
    er.addDateRadioList( value );

    er.$.header.find('.eventFlowChartRangeClear').click();
}
/*
##################################################
    Scroll bar event
##################################################
*/
setScrollBarEvent() {
    const er = this;

    er.$.scroll.on('pointerdown.eventFlow', function( downEvent ){

        // 選択を解除
        getSelection().removeAllRanges();

        // 集約モードの場合は停止
        if ( er.flag.aggregate ) return;

        const
        $bar = $( this ),
        $range = $bar.find('.eventFlowRange'),
        $window = $( window );

        const
        barType = $bar.attr('data-type'),
        partsType = downEvent.target.className;

        const
        barWidth = ( barType === 'vertical')? $bar.height(): $bar.width(),
        rangeWidth = ( barType === 'vertical')? $range.height(): $range.width(),
        rangePosition = ( barType === 'vertical')? $range.position().top: $range.position().left,
        rangeMinWidth = Math.floor( barWidth / er.maxRate );

        let
        afterWidth = rangeWidth,
        afterPosittion = rangePosition;

        const widthCheck = function( width, max ) {
            if ( max < width ) width = max;
            if ( rangeMinWidth > width ) width = rangeMinWidth;
            return width;
        };

        const positionCheck = function( position, max ) {
            if ( position < 0 ) position = 0;
            if ( position > max ) position = max;
            return position;
        };

        const updateCanvasPosition = async function() {
            if ( barType === 'vertical') {
                er.vRate = Math.round( 1 / ( afterWidth / barWidth ) * 100 ) / 100;
                er.vPosition = Math.round( er.h * ( afterPosittion / barWidth ) * er.vRate * 100 ) / 100;
            } else {
                er.hRate = Math.round( 1 / ( afterWidth / barWidth ) * 100 ) / 100;
                er.hPosition = Math.round( er.w * ( afterPosittion / barWidth ) * er.hRate * 100 ) / 100;
            }

            await er.workerPost('positionChange', null, true );

            er.$.chart.click();

            if ( er.clickBlock ) {
                await er.workerPost('updateEventLink', null, true );
            }
        };

        const moveEvent = function( moveEvent ){
            // 移動距離
            const move = ( barType === 'vertical')? moveEvent.pageY - downEvent.pageY: moveEvent.pageX - downEvent.pageX;

            if ( partsType === 'eventFlowRangeStart') {
                // 開始位置移動
                afterWidth = widthCheck( rangeWidth - move, barWidth - ( barWidth - afterPosittion - afterWidth ) );
                afterPosittion = positionCheck( rangePosition + move, barWidth - ( barWidth - rangeWidth - rangePosition + rangeMinWidth ) );

                if ( barType === 'vertical') {
                    $range.css({
                        top: afterPosittion,
                        height: afterWidth
                    });
                } else {
                    $range.css({
                        left: afterPosittion,
                        width: afterWidth
                    });
                }
            } else if ( partsType === 'eventFlowRangeEnd') {
                // 終了位置移動
                afterWidth = widthCheck( rangeWidth + move, barWidth - afterPosittion );

                if ( barType === 'vertical') {
                    $range.css({
                        height: afterWidth
                    });
                } else {
                    $range.css({
                        width: afterWidth
                    });
                }
            } else {
                // 位置移動
                afterPosittion = positionCheck( rangePosition + move, barWidth - afterWidth );

                if ( barType === 'vertical') {
                    $range.css({
                        top: afterPosittion
                    });
                } else {
                    $range.css({
                        left: afterPosittion
                    });
                }
            }

            updateCanvasPosition();
        };

        // 間引き処理
        const rafMoveEvent = er.rafThrottle( moveEvent );

        $window.on({
            'pointermove.eventFlow': rafMoveEvent,
            'pointerup.eventFlow': function(){
                $window.off('pointermove.eventFlow pointerup.eventFlow');

                // 幅のサイズを割合に変更する
                if ( barType === 'vertical') {
                    $range.css({
                       height: ( afterWidth / barWidth * 100 ) + '%',
                       top: ( afterPosittion / barWidth * 100 ) + '%'
                    });
                } else {
                    $range.css({
                       width: ( afterWidth / barWidth * 100 ) + '%',
                       left: ( afterPosittion / barWidth * 100 ) + '%'
                    });
                }
            }
        });
    });
}
/*
##################################################
    モード切替
##################################################
*/
modeChangeEvent() {
    this.$.header.find('.toggleButton').off('click').on('click', async ( e ) => {
        const $button = $( e.currentTarget );
        $button.prop('disabled', true );

        const mode = $button.attr('data-toggle');
        if ( mode === 'on') {
            this.flag.aggregate = false;
            $button.attr('data-toggle', 'off');
            this.$.eventFrow.removeClass('eventFlowAggregate_on');
            this.$.eventFrow.addClass('eventFlowAggregate_off');
        } else {
            this.modeAggregateOn( $button );
        }
        await this.workerPost('modeChange', null, true );
        
        $button.prop('disabled', false );
    });
}
modeAggregateOn( $button ) {
    this.flag.aggregate = true;
    $button.attr('data-toggle', 'on');
    this.$.eventFrow.removeClass('eventFlowAggregate_off');
    this.$.eventFrow.addClass('eventFlowAggregate_on');
}
/*
##################################################
    範囲変更
##################################################
*/
changeDateReset( startDate, endDate, rangeFlag = false ) {
    this.positionReset();

    if ( rangeFlag ) {
        this.start = startDate;
        this.end = endDate;
        this.period = this.end - this.start;
        this.workerRangeChange();
    } else {
        this.workerPollingStart('rangeChange');
    }
}
/*
##################################################
    範囲をクリア
##################################################
*/
clearDataRange() {
    this.positionReset();
    this.workerRangeClear();
}
/*
##################################################
    ポジションリセット
##################################################
*/
positionReset() {
    this.hRate = 1;
    this.hPosition = 0;
    this.$.hScroll.find('.eventFlowRange').css({
        width: '100%',
        left: 0
    });

    this.vRate = 1;
    this.vPosition = 0;
    this.$.vScroll.find('.eventFlowRange').css({
        height: '100%',
        top: 0
    });
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//  イベント情報表示
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    イベントの詳細情報を表示
##################################################
*/
viewEventInfo( x ) {
    const er = this;

    const d = er.currentBlock;

    const css = {display: 'flex'};

    // 表示位置（左右）
    if ( x / er.w > .5 ) {
        css.left = 0;
        css.right = 'auto';
    } else {
        css.right = 40;
        css.left = 'auto';
    }

    er.$.info.css(css);

    // クリックしたアクション、ルールと関連するパーツを表示する
    er.$.parts.find('.eventFlowPartsShow').removeClass('eventFlowPartsShow').show();
    if ( d.type === 'action' || d.type === 'rule') {
        const className = ( d.type === 'action')? 'Action': 'Rule';
        const id = ( d.type === 'action')? d.item.ACTION_ID: ( d.info )? d.info.id: '';
        er.$.parts.find(`li.eventFlowParts${className}`).addClass('eventFlowPartsShow').show()
            .not(`[data-id="${fn.escape(id)}"]`).hide();
    }

    const html = [];
    html.push( er.eventInfoRowHtml('Type', d.type ) );

    if ( d.type === 'action') {
        html.push( er.eventInfoRowHtml('Datetime', d.datetime ) );
        html.push( er.eventInfoRowHtml('ID', d.id ) );
        html.push( er.eventInfoRowHtml('Action Name', fn.cv( d.item.ACTION_NAME, '')));
        html.push( er.eventInfoRowHtml('Conductor', fn.cv( d.item.CONDUCTOR_INSTANCE_NAME, '')));
        html.push( er.eventInfoRowHtml('Operation', fn.cv( d.item.OPERATION_NAME, '')));
        html.push( er.eventInfoRowHtml('Rule ID', fn.cv( d.item.RULE_ID, '')));
        html.push( er.eventInfoRowHtml('Rule Name', fn.cv( d.item.RULE_NAME, '')));
    } else if ( d.type === 'rule') {
        if ( d.info ) {
            html.push( er.eventInfoRowHtml('Rule ID', d.info.id ) );
            html.push( er.eventInfoRowHtml('Rule Name', d.info.name ) );
        }
    } else {
        html.push( er.eventInfoRowHtml('Datetime', d.datetime ) );
        html.push( er.eventInfoRowHtml('ID', d.id ) );
        const pattern = er.patternList[ er.patternId[ er.currentBlock._pattern ] ];
        html.push( er.eventInfoRowHtml('Pattern', fn.cv( pattern, '')));
        if ( d.item.exastro_rules && d.item.exastro_rules[0] ) {
            html.push( er.eventInfoRowHtml('Rule ID', fn.cv( d.item.exastro_rules[0].id, ''), '') );
            html.push( er.eventInfoRowHtml('Rule name', fn.cv( d.item.exastro_rules[0].name, ''), '') );
        }
        // ラベル
        html.push( er.eventInfoRowHtml('Labels', '', 'eventInfoTableLabelsBlank') );
        html.push(`<tr class="eventInfoTableTr"><td class="eventInfoTableTd eventInfoTableLabels" colspan="2">${fn.html.labelListHtml( d.item.labels, er.label )}</td></tr>`);

        // 重複排除（イベントにexastro_duplicate_checkが付与されている時のみ表示）
        if ( d.item.exastro_duplicate_check ) {
            let eventCollectionSettingsExchange
            if (er['eventCollectionSettings'].error ) {
                eventCollectionSettingsExchange = null
            } else {
                eventCollectionSettingsExchange = er.eventCollectionSettings.reduce((acc, cur) => {
                    acc[cur.parameter.event_collection_settings_id] = cur.parameter.event_collection_settings_name;
                    return acc;
                }, {});
            }
            html.push( er.eventInfoRowHtml('Deduplication', '', 'eventInfoTableLabelsBlank'));
            html.push(`<tr class="eventInfoTableTr"><td class="eventInfoTableTd eventInfoTableLabels" colspan="2">${fn.html.deduplicationListHtml( d.item.exastro_duplicate_check, eventCollectionSettingsExchange )}</td></tr>`);
        }

        // グループ（イベントにexastro_filter_groupが付与されている時のみ表示）
        if ( d.item.exastro_filter_group ) {
            const targetFilter = ( er.filterSettings.error ) ? null : er.filterSettings.find(data => data.parameter.filter_id === d.item.exastro_filter_group.filter_id );
            const groupData = {
                group_id: d.item.exastro_filter_group.group_id,
                filter_name: (targetFilter) ? targetFilter.parameter.filter_name : d.item.exastro_filter_group.filter_id,
                first_event: d.item.exastro_filter_group.is_first_event.toString()
            };
            // グルーピングされている場合は件数を表示する
            const groupId = d.item.exastro_filter_group.group_id;
            const count = ( er.clickGrouping && er.clickGrouping[ groupId ] )? `(${er.clickGrouping[ groupId ].count})`: '';
            html.push( er.eventInfoRowHtml(`Group${count}`, '', 'eventInfoTableLabelsBlank'));
            html.push(`<tr class="eventInfoTableTr"><td class="eventInfoTableTd eventInfoTableLabels" colspan="2">${fn.html.labelListHtml( groupData, null, true )}</td></tr>`);
        }
    }

    const tableHtml = `<table class="eventInfoTable">${html.join('')}</table>`;

    if ( d.type === 'action') {
        er.$.info.html(`<div class="eventFlowEventInformationInner">${tableHtml}</div>`);
    } else if ( d.type === 'event' && d.item.event ) {
        const json = fn.jsonStringify( d.item.event, '\t');

        // 行数から高さを決める
        const
        lineHeight = 17,
        match = json.match(/\n/g),
        height = ( match.length + 2 ) * lineHeight;

        // HTML
        const infoHtml = `<div class="eventInfoContainer">`
            + `<div class="eventInfoTabBlocks">`
                + `<div class="eventInfoTabBlock open"><table class="eventInfoTable">${html.join('')}</table></div>`
                + `<div class="eventInfoTabBlock"><div id="eventInfoJson"></div></div>`
            + `</div>`
            + `<div class="eventInfoTabs">`
                + `<ul class="eventInfoTabList">`
                    + `<li class="eventInfoTabItem open">${getMessage.FTE13026}</li>`
                    + `<li class="eventInfoTabItem">${getMessage.FTE13025}</li>`
                + `</ul>`
            + `</div>`
        + `</div>`;
        er.$.info.html( infoHtml );
        er.$.info.find('#eventInfoJson').height( height );

        // テーマ
        const aceTheme = ( $('body').is('.darkmode') )? 'monokai': 'chrome';

        // Ace editor
        const aceEditor = ace.edit('eventInfoJson', {
            theme: `ace/theme/${aceTheme}`,
            mode: `ace/mode/json`,
            displayIndentGuides: true,
            fontSize: '14px',
            minLines: 2,
            showPrintMargin: false,
            readOnly: true,
            wrapBehavioursEnabled: false,
            enableBasicAutocompletion: true,
            enableLiveAutocompletion: true
        });
        er.$.info.find('.ace_scrollbar').addClass('commonScroll');

        // 値をセット
        aceEditor.session.setValue( json );
    } else {
        er.$.info.html(`<div class="eventFlowEventInformationInner">${tableHtml}</div>`);
    }
}
/*
##################################################
    イベントの詳細情報を表示
##################################################
*/
hideEventInfo() {
    this.$.info.hide();
    this.$.parts.find('.eventFlowPartsShow').removeClass('eventFlowPartsShow').show();
}
/*
##################################################
    イベントの詳細情報　行HTML
##################################################
*/
eventInfoRowHtml( thText, tdText, addClassName, escape = true ) {
    const className = ['eventInfoTableTd'];
    if ( addClassName ) className.push( addClassName );
    return ``
    + `<tr class="eventInfoTableTr">`
        + `<th class="eventInfoTableTh">${fn.cv( thText, '', true )}</th>`
        + `<td class="${className.join(' ')}">${fn.cv( tdText, '', escape )}</td>`
    + `</tr>`;
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//  パーツ管理
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    各種読み込み開始
##################################################
*/
async setupParts() {
    const er = this;

    await Promise.all([
        er.fetchParts('filter'),
        er.fetchParts('action'),
        er.fetchParts('rule'),
        er.fetchSettings('eventCollectionSettings'),
        er.fetchSettings('filterSettings')
    ]);

    return;
}
/*
##################################################
    各種読み込み
##################################################
*/
async fetchParts( type ) {
    const er = this;

    const partsData = er.getPartsData( type );

    try {
        const info = await fn.fetch( partsData.info );
        const params = fn.getCommonParams();
        params.menuNameRest = partsData.rest
        er[ partsData.id ] = { info: info };

        const option = {
            parts: partsData
        };

        // パーツテーブル
        er[ partsData.id ].table = new DataTable( partsData.id, 'view', er[ partsData.id ].info, params, option );

        // ソートセット
        er[ partsData.id ].table.sort = [{ ASC: partsData.partsRestName }];

        // HTMLセット
        er.$.parts.find( partsData.target ).html( er[ partsData.id ].table.setup() );

        // Filter及びRule場合ラベルデータを渡す
        if ( type === 'filter' || type === 'rule') {
            er[ partsData.id ].table.label = er.label;
        }

        // モードチェンジイベント
        er[ partsData.id ].table.$.container.on({
            'changePartsEditMode': function( e, type ){
                er.$.target.addClass( type + 'EventFlowEditMode');
                if ( type === 'rule') {
                    er.ruleEditEventOn();
                }
                if ( type === 'rule' ||  type === 'filter') {
                    er.labelSetEventOn( type );
                }
            },
            'changePartsViewMode': function( e, type ){
                er.$.target.removeClass( type + 'EventFlowEditMode');
                if ( type === 'rule') {
                    er.ruleEditEventOff();
                }
                if ( type === 'rule' ||  type === 'filter') {
                    er.labelSetEventOff( type );
                }
            }
        });
    } catch ( error ) {
        if ( error.message ) {
            const message = `<div class="eventFlowPartsNoDate"><div class="eventFlowPartsNoDateInner">${error.message}</div></div>`;
            er.$.parts.find( partsData.target ).html( message );
        }
    };

    return;
}
// ID変換用にイベント収集設定・フィルター設定を取得
async fetchSettings( type ) {
    const er = this;
    const settingsData = er.getSettingsData( type );
    try {
        er[ type ] = await fn.fetch( settingsData.info, null, 'POST', settingsData.data );
    } catch ( error ) {
        er[ type ] = { error }
    };
    return;
}
/*
##################################################
    パーツデータ
##################################################
*/
getPartsData( type ) {
    switch ( type ) {
        case 'filter':
            return {
                name: 'Filter',
                className: 'Filter',
                id: 'filter',
                rest: 'filter',
                info: '/menu/filter/info/',
                target: '.eventFlowPartsBlockFilter',
                partsRestId: 'filter_id',
                partsRestName: 'filter_name'
            };
        case 'action':
            return {
                name: 'Action',
                className: 'Action',
                id: 'action',
                rest: 'action',
                info: '/menu/action/info/',
                target: '.eventFlowPartsBlockAction',
                partsRestId: 'action_id',
                partsRestName: 'action_name'
            };
        case 'rule':
            return {
                name: 'Rule',
                className: 'Rule',
                id: 'rule',
                rest: 'rule',
                info: '/menu/rule/info/',
                target: '.eventFlowPartsBlockRule',
                partsRestId: 'rule_id',
                partsRestName: 'rule_name'
            };
    }
}
// イベント収集設定・フィルター設定取得用パラメータ
getSettingsData(type) {
    switch ( type ) {
        case 'eventCollectionSettings':
            return {
                info: '/menu/event_collection/filter/',
                data: {
                    discard: { NORMAL: '0'}
                }
            };
        case 'filterSettings':
            return {
                info: '/menu/filter/filter/',
                data: {
                    discard: { NORMAL: '0'}
                }
            };
    }
}
/*
##################################################
    Drag and Drop
##################################################
*/
ruleEditEventOn() {
    const er = this;

    const $window = $( window );

    // Rule Edit Tableの準備ができたら
    $window.on('rule__tableReady.setFilter', function(){
        er.$.parts.find('.eventFlowPartsTableBlockFilter, .eventFlowPartsTableBlockAction')
            .on('mousedown.setFilter', '.eventFlowPartsName', function( pde ){
            if ( pde.button !== 0 || er.rule.table.flag.dragAndDrop === true ) return;
            er.rule.table.flag.dragAndDrop = true;

            const $item = $( this ).closest('.eventFlowPartsItem');
            $item.addClass('nowMoving');

            const type = ( $( this ).closest('.eventFlowPartsTableBlockFilter').length )? 'filter': 'action';
            const selectKey = ( type === 'filter')? '[data-key="filter_a"], [data-key="filter_b"]': '[data-key="action_id"]';

            const $targetArea = er.rule.table.$.tbody.find('.tableEditInputSelect').filter( selectKey ).closest('.ci');
            $targetArea.addClass('dragAndDropArea');

            const
            $filter = $( this ),
            value = $filter.find('.eventFlowPartsNameText').text();

            // 移動用ダミー
            const className = ( type === 'filter')? 'eventFlowPartsFilter': 'eventFlowPartsAction';
            const $dummy = $('<div/>', {
                text: value,
                class: 'eventFlowPartsMove eventFlowPartsName ' + className
            }).css({
                top: pde.pageY,
                left: pde.pageX
            });
            er.$.target.append( $dummy );

            fn.deselection();

            $window.on({
                'mousemove.setFilter': function( pme ){
                    const
                    x = pme.pageX - pde.pageX,
                    y = pme.pageY - pde.pageY;
                    $dummy.css({
                        transform: `translate( ${x}px, ${y}px )`
                    });
                },
                'mouseup.setFilter': function( pme ){
                    $window.off('mousemove.setFilter mouseup.setFilter');
                    er.rule.table.flag.dragAndDrop = false;

                    // mouseupしたのが対象の上かどうか
                    const $target = $( pme.target ).closest('.dragAndDropArea');
                    if ( $target.length ) {
                        const $select = $target.find('.tableEditInputSelect');

                        // select2が適用されているか
                        if ( $select.is('.select2-hidden-accessible') ) {
                            $select.select2('trigger', 'select', { data: { id: value, text: value }});
                        } else {
                            $select.val([value]);

                            // 値が無い場合は追加する
                            if ( !$select.val() ) {
                                $select.append( $('<option/>', { value: value, text: value }) ).val([value]);
                            }
                            $select.change();
                            $select.prev('.tableEditInputSelectValue').find('.tableEditInputSelectValueInner').text( value );
                        }
                    }

                    $dummy.remove();
                    $item.removeClass('nowMoving');
                    $targetArea.removeClass('dragAndDropArea');
                }
            });

        });
    });
}
ruleEditEventOff() {
    const er = this;
    $( window ).off('rule__tableReady.setFilter');
    er.$.parts.find('.eventFlowPartsTableBlockFilter, .eventFlowPartsBlockAction').off('mousedown.setFilter');
}
labelSetEventOn( type ) {
    const er = this;

    const $window = $( window );

    // Rule Edit Tableの準備ができたら
    $window.on(`${type}__tableReady.setFilter`, function(){
        er.$.info.addClass('labelDragMode');
        er.$.info.on('mousedown.setLabel', '.eventFlowLabel', function( pde ){
            if ( pde.button !== 0 || er[ type ].table.flag.dragAndDrop === true ) return;
            er[ type ].table.flag.dragAndDrop = true;

            const $item = $( this );

            const selectKey = ( type === 'filter')? '[data-key="filter_condition_json"]': '[data-key="conclusion_label_settings"]';

            const $targetArea = er[ type ].table.$.tbody.find('.inputHidden').filter( selectKey ).closest('.ci');
            $targetArea.addClass('dragAndDropArea');

            const $dummy = $item.clone();
            er.$.target.append( $dummy );
            $dummy.addClass('eventFlowLabelMove').css({
                top: pde.pageY,
                left: pde.pageX
            });

            $item.addClass('nowMoving');

            fn.deselection();

            $window.on({
                'mousemove.setFilter': function( pme ){
                    const
                    x = pme.pageX - pde.pageX,
                    y = pme.pageY - pde.pageY;
                    $dummy.css({
                        transform: `translate( ${x}px, ${y}px )`
                    });
                },
                'mouseup.setLabel': function( pme ){
                    $window.off('mousemove.setLabel mouseup.setLabel');
                    er[ type ].table.flag.dragAndDrop = false;

                    const $target = $( pme.target ).closest('.dragAndDropArea');
                    if ( $target.length ) {
                        const
                        $input = $target.find('.tableEditMultipleHiddenColmun'),
                        $text = $target.find('.tableEditMultipleColmun'),
                        value = fn.jsonParse( $input.val(), 'array'),
                        array = [];

                        array.push($item.find('.eventFlowLabelKey').text());
                        if ( type === 'filter') array.push('==');
                        array.push($item.find('.eventFlowLabelValue').text());
                        value.push( array );

                        const text = fn.jsonStringifyDelimiterSpace( value );
                        $input.val( fn.nlcEscape(text) ).change();

                        const labelHtml = fn.html.labelListHtml( value, er.label );
                        $text.html( labelHtml );
                    }

                    $dummy.remove();
                    $item.removeClass('nowMoving');
                    $targetArea.removeClass('dragAndDropArea');
                }
            });

        });
    });
}
labelSetEventOff( type ) {
    const er = this;
    $( window ).off(`${type}__tableReady.setFilter`);
    er.$.info.off('mousedown.setLabel');
    er.$.info.removeClass('labelDragMode');
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//  ユーティリティ
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    間引き処理
##################################################
*/
rafThrottle( f ) {
    let ticking = false, lastArgs, lastThis;
    return function(...args) {
        lastArgs = args;
        lastThis = this;
        if ( !ticking ) {
            ticking = true;
            requestAnimationFrame(() => {
                ticking = false;
                f.apply( lastThis, lastArgs );
            });
        }
    };
}
/*
##################################################
    パターンカラー
##################################################
*/
getPatternColor( pattern, opacity = 1 ) {
    return `rgba(${this.patternColor[ pattern ]},${opacity})`;
}
/*
##################################################
    X座標から時間を取得
##################################################
*/
getPositionDate( x ) {
    return new Date( this.start + this.period * ( ( x + this.hPosition ) / ( this.w * this.hRate ) ) );
}

}