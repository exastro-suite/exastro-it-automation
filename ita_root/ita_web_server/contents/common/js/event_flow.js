////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Exastro IT Automation / event_relay.js
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

class EventFlow {
/*
##################################################
  Constructor
##################################################
*/
constructor( id ) {
    this.id = id;
}
/*
##################################################
  初期値
##################################################
*/
setInitCanvasValue() {
    const er = this;
    
    const now = Date.now();
    er.loadStart = er.start = new Date( now - ( 60 * 60 * 1000 ) );
    er.loadEnd = er.end = new Date( now );

    er.initRange = '1h'; // 初期表示範囲

    er.intervalTime = 10000; // 更新間隔
    
    er.blockMargin = 16; // ブロックごとの重なり判定マージン
    er.minFloor = 16; // 最小段数
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
        unknown: '255,31,255', // 未知
        timeout: '255,30,30', // 既知（時間切れ）
        evaluated: '189,204,212', // 既知（対処済み）
        newEvent: '140,198,63', // NEW
        action: '0,91,172' // アクション
    };

    // 表示フラグ
    er.displayFlag = {
        conclusion: true, // 再評価
        unknown: true, // 未知
        timeout: true, // 既知（時間切れ）
        evaluated: true, // 既知（対処済み）
        newEvent: true, // NEW
        action: true // アクション
    };

    // パターンリスト
    er.patternList = {
        unknown: getMessage.FTE13008,
        timeout: getMessage.FTE13009,
        evaluated: getMessage.FTE13010,
        conclusion: getMessage.FTE13011,
        newEvent: getMessage.FTE13012,
        action: getMessage.FTE13013
    };

    // 各種フラグ
    er.flag = {
        rangeSelect: false
    } ;

    // 履歴用
    er.history = [];
    
}
/*
##################################################
  Setup
##################################################
*/
setup( target ) {
    const er = this;
    
    er.target = target;
    
    // Canvas初期値設定
    er.setInitCanvasValue();
    
    const $target = $( er.target );
    $target.html( er.mainHtml( er.id ) ).addClass('nowLoading');
    
    // jQuery object
    er.$ = {
        target: $target,
        header: $target.find('.eventFlowHeader'),
        body: $target.find('.eventFlowBody'),
        footer: $target.find('.eventFlowFooter'),
        chart: $target.find('.eventFlowChart'),
        scroll: $target.find('.eventFlowChartBar'),
        vScroll: $target.find('.eventFlowChartBar[data-type="vertical"]'),
        hScroll: $target.find('.eventFlowChartBar[data-type="horizontal"]'),
        positionBorder: $target.find('.eventFlowPositionBorder'),
        positionDate: $target.find('.eventFlowPositionDate'),
        info: $target.find('.eventFlowEventInformation'),
        parts: $target.find('.eventFlowParts'),
    };
    
    // Chart canvas
    er.chartCanvas = {
        line: er.$.body.find('.eventFlowChartPositionLineCanvas').get(0),
        block: er.$.body.find('.eventFlowChartBlockCanvas').get(0),
        incident: er.$.body.find('.eventFlowChartIncidentCanvas').get(0),
    };
    
    // Chart canvas context
    er.chartContext = {};
    for ( const type in er.chartCanvas ) {
        er.chartContext[ type ] = er.chartCanvas[ type ].getContext('2d');
    }
    
    // Date canvas
    er.dateCanvas = er.$.body.find('.eventFlowDateCanvas').get(0);
    er.dateContext = er.dateCanvas.getContext('2d');

    // イベントフロー表示
    const setEventFlow = function( label = []) {
        er.label = label;
        er.updateCanvas( true );
        er.setupParts();
    }

    // ラベルデータを読み込む
    const
    data = { discard: { NORMAL: '0'}},
    option = { authorityErrMove: false };

    fn.fetch('/menu/label_creation/filter/', null, 'POST', data, option ).then(function( label ){
        setEventFlow( label );
    }).catch(function( error ){
        console.error( error );
        setEventFlow();
    });
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
    
    const menuList = {
        Main: [
            { html: { html: er.dateRangeSelectHTML() }},
            { button: { icon: 'cal', text: getMessage.FTE13014, type: 'timeRange', action: 'default'}},
            { html: { html: rangeSelectHtml }, separate: true, className: 'eventFlowChartRangeItem', display: 'none' },
            { html: { html: er.patternSelectHTML() }, separate: true }
        ],
        Sub: [
            //{ button: { icon: 'gear', text: getMessage.FTE13015, type: 'setting', action: 'default'}}
        ]
    };
    
    return ``
    + `<div id="${id}_eventFlow" class="eventFlowContainer">`
        + `<div class="eventFlow">`
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
                + `<div class="eventFlowEventInformation"><div class="eventFlowEventInformationInner"></div></div>`
                + `<div class="eventFlowPositionDate"></div>`
            + `</div>`
            // + `<div class="eventFlowFooter"></div>`
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
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//  Canvas
// 
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
  表示データの作成
##################################################
*/
createCanvasData() {
    const er = this;
    
    er.canvasData = [];    
    
    // 幅とマージンから何段目に表示できるかチェック
    const floor = [];
    const floorCheck = function( x1, x2, f ) {
        if ( !floor[f] ) floor[f] = [];
        
        const l = floor[f].length;
        if ( l === 0 || floor[f][ l - 1 ] + er.blockMargin < x1 ) {
            floor[f].push( x1 );
            floor[f].push( x2 );
            return f;
        } else {
            return floorCheck( x1, x2, ++f );
        }
    };

    er.history.sort(function( a, b ){
        return a.datetime.localeCompare( b.datetime );
    });
    
    for ( const item of er.history ) {
        const data = {
            id: item.id,
            type: item.type,
            date: item.datetime,
            original: item
        };

        // パターン
        if ( item.type === 'event') {
            data.pattern = er.checkEventPattern( item.item.labels );
        } else {
            data.pattern = item.type;
        }

        // 表示パターンチェック
        if ( er.displayFlag[ data.pattern ] === false ) continue;
        
        // X座標
        if ( item.type === 'event') {
            data.x1 = er.getDateWidthPositionX( item.item.labels._exastro_fetched_time );
            data.x2 = er.getDateWidthPositionX( item.item.labels._exastro_end_time );
        } else {
            data.x1 = er.getDateWidthPositionX( item.datetime );
        }
        const x2 = ( data.x2 )? data.x2: data.x1;

        // 表示範囲内かチェック
        if ( ( data.x1 < 0 && x2 < 0 ) || ( data.x1 > er.w && x2 > er.w ) ) continue;
        
        // 何段目に表示するか
        data.floor = floorCheck( data.x1, x2, 0 );        
        
        er.canvasData.push( data );
    }

    // 段数
    const floors = ( floor.length > er.minFloor )? floor.length: er.minFloor;
    er.lineSpacing = er.h / floors;
}
/*
##################################################
  イベントパターンを調べる
##################################################
*/
checkEventPattern( labels ) {
    // 再評価
    if ( labels._exastro_type === 'conclusion') {
        return 'conclusion';
    }
    // 未知
    if ( labels._exastro_undetected === '1') {
        return 'unknown';
    }
    // 既知（時間切れ）
    if ( labels._exastro_timeout === '1') {
        return 'timeout';
    }
    // 既知（判定済）
    if ( labels._exastro_evaluated === '1') {
        return 'evaluated';
    }
    // 新規
    return 'newEvent';
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
  更新
##################################################
*/
updateCanvas( initFlag = false ) {
    const er = this;

    if ( er.controller ) er.controller.abort();
    er.controller = new AbortController();    

    // 時間を再セット
    const selectDate = er.$.header.find('.eventFlowDateRangeRadio:checked').val();
    const newDate = er.updateDataTime( selectDate );

    if ( er.flag.rangeSelect === false ) {
        er.start = er.loadStart = newDate[0];
        er.end = er.loadEnd = newDate[1];
    } else {
        er.loadStart = newDate[0];
        er.loadEnd = newDate[1];
    }
    
    const postData = {
        start_time: fn.date( er.loadStart, 'yyyy/MM/dd HH:mm:ss'),
        end_time: fn.date( er.loadEnd, 'yyyy/MM/dd HH:mm:ss')
    };
    fn.fetch('/oase/event_flow/history/', null, 'POST', postData, { controller: er.controller } ).then(function( history ){
        
        if ( initFlag ) {
            er.$.target.removeClass('nowLoading');
            er.setEvents();
            er.setPartsEvents();
        }

        er.history = history;
        er.controller = null;
        er.updateDate = Date.now();

        er.$.footer.text('自動更新:ON');
        er.timerId = setTimeout(function(){
            er.updateCanvas();
        }, er.intervalTime );
        
        er.resetCanvas();
    }).catch(function(error){
        console.error( error );
    });
}
/*
##################################################
  自動更新停止
##################################################
*/
stopAutoUpdate() {
    const er = this;

    // 再開する際の時間
    if ( er.updateDate ) {
        const diff = Date.now() - er.updateDate;
        er.resumeDate = ( er.intervalTime > diff )? ( diff < 1000 )? 1000: diff: er.intervalTime;
    }

    // クリアタイム
    if ( er.timerId ) {
        clearInterval( er.timerId );
        er.timerId = null;
    }

    // 読み込み停止
    if ( er.controller ) {
        er.controller.abort();
        er.controller = null;
    }
}
/*
##################################################
  自動更新再開
##################################################
*/
resumeAutoUpdate() {
    const er = this;

    if ( er.checkAutoUpdate() ) {
        window.console.warn('resumeAutoUpdate() warning.');
        return;
    }

    er.timerId = setTimeout(function(){
        er.updateCanvas();
    }, er.resumeDate );
}
/*
##################################################
  自動更新中チェック
##################################################
*/
checkAutoUpdate() {
    return this.timerId !== null;
}
/*
##################################################
  再表示
##################################################
*/
resetCanvas( canvasSizeChangeFlag = false ) {
    const er = this;
    
    er.period = er.end.getTime() - er.start.getTime();
    
    // Chart canvasサイズ
    er.w = er.$.chart.outerWidth();
    er.h = er.$.chart.outerHeight();
    
    for ( const type in er.chartCanvas ) {
        er.chartCanvas[ type ].width = er.w;
        er.chartCanvas[ type ].height = er.h;
    }
    
    // Date canvasサイズ
    er.dateCanvas.width = er.w;
    
    // 表示用データ
    if ( canvasSizeChangeFlag === false ) {
        er.createCanvasData();
    }
    
    // 描画
    er.setTimeScale();
    er.setLine();
    
    // 各種イベントブロック
    er.setEventBlock();
}
/*
##################################################
  範囲変更
##################################################
*/
changeDateReset( startDate, endDate, rangeFlag = false ) {
    const er = this;
    
    if ( rangeFlag ) {
        er.start = startDate;
        er.end = endDate;
    } else {
        er.loadStart = er.start = startDate;
        er.loadEnd= er.end = endDate;
    }
    
    er.hRate = 1;
    er.hPosition = 0;
    er.$.hScroll.find('.eventFlowRange').css({
        width: '100%',
        left: 0
    });
    
    er.vRate = 1;
    er.vPosition = 0;
    er.$.vScroll.find('.eventFlowRange').css({
        height: '100%',
        top: 0
    });
    
    if ( rangeFlag ) {
        er.resetCanvas();
    } else {
        er.updateCanvas();
    }
}
/*
##################################################
  X座標から時間を取得
##################################################
*/
getPositionDate( x ) {
    const er = this;
    
    return new Date( er.start.getTime() + er.period * ( ( x + er.hPosition ) / ( er.w * er.hRate ) ) );
}
/*
##################################################
  表jいしている範囲からX座標を取得する
##################################################
*/
getDatePositionX( date ) {
    const er = this;
    return ( er.w * er.hRate * ( ( new Date( date ).getTime() - er.start.getTime() ) / er.period ) - er.hPosition );
}
/*
##################################################
  全体の範囲からX座標を取得する
##################################################
*/
getDateWidthPositionX( date ) {
    const er = this;
    return ( er.w * ( ( new Date( date ).getTime() - er.start.getTime() ) / er.period ));
}
/*
##################################################
  階層からY座標を取得する
##################################################
*/
getFloorPositonY( floor ) {
    const er = this;
    return floor * er.lineSpacing * er.vRate + ( er.lineSpacing * er.vRate / 2 ) - er.vPosition;
}
/*
##################################################
  タイムスケールを描画する
##################################################
*/
setTimeScale() {
    const er = this;
    
    const ctx = er.dateContext;
    ctx.clearRect( 0, 0, er.dateCanvas.width, er.dateCanvas.height );
    
    ctx.beginPath();
    ctx.lineWidth = 1;
    ctx.strokeStyle = '#CCC';
    
    // テキスト共通
    ctx.textBaseline = 'top';
    ctx.fillStyle = "#666" ;
    
    // 左端の線
    ctx.moveTo( .5, .5 );
    ctx.lineTo( .5, er.dateCanvas.height + .5 );
    ctx.textAlign = 'left';
    ctx.font = 'bold 14px Consolas';
    
    const start = er.getPositionDate( 0 );
    ctx.fillText( fn.date( start, 'yyyy/MM/dd HH:mm:ss'), 8, 0 );
    
    // 右端の線
    ctx.moveTo( er.dateCanvas.width - .5, .5 );
    ctx.lineTo( er.dateCanvas.width - .5, er.dateCanvas.height + .5 );
    ctx.textAlign = 'right';
    
    const end = er.getPositionDate( er.w );
    ctx.fillText( fn.date( end, 'yyyy/MM/dd HH:mm:ss'), er.w - 8, 0 );

    // 目盛り
    const diffDate = end.getTime() - start.getTime();

    // 表示範囲からタイプを設定する
    const mode = er.checkTimeScaleMode( diffDate );

    const type = mode.slice(-1);
    const interval = Number( mode.slice(0,-1) );

    // 目盛り開始時間
    const roundDate = function() {
        switch( type ) {
            case 'y': return 'yyyy/01/01 00:00:00';
            case 'M': return 'yyyy/MM/01 00:00:00';
            case 'w': case 'd': return 'yyyy/MM/dd 00:00:00';
            case 'H': return 'yyyy/MM/dd HH:00:00';
            case 'm': return 'yyyy/MM/dd HH:mm:00';
            default: return 'yyyy/MM/dd HH:mm:ss';
        }
    };
    const startLineDate = new Date( fn.date( start, roundDate() ) );

    ctx.textAlign = 'center';
    ctx.font = 'normal 12px Consolas';

    let beforeTextX = -9999999;
    while ( startLineDate < er.end ) {
        const x = er.getDatePositionX( startLineDate );

        let num = 0, text = '', y = 40;
        switch( type ) {
            case 'y':
              num = startLineDate.getMonth();
              text = fn.date( startLineDate, 'yyyy/MM/dd');
              startLineDate.setMonth( num + interval );
              break;
            case 'M': case 'w':
              num = startLineDate.getDate();
              text = fn.date( startLineDate, 'yyyy/MM/dd');
              startLineDate.setDate( num + interval );
              break;
            case 'd': case 'H':
              num = startLineDate.getHours();
              text = fn.date( startLineDate, 'HH:mm:ss');
              startLineDate.setHours( num + interval );
              break;
            case 'm':
              num = startLineDate.getMinutes();
              text = fn.date( startLineDate, 'HH:mm:ss');
              startLineDate.setMinutes( num + interval );
              break;
            default:
              num = startLineDate.getSeconds();
              text = fn.date( startLineDate, 'HH:mm:ss');
              startLineDate.setSeconds( num + interval );
        };

        // テキストが重ならないかチェック
        const size = ctx.measureText( text );
        if ( beforeTextX < x - size.width / 2 ) {
            ctx.fillText( text, x, 20 );
            beforeTextX = x + size.width / 2 + 24;
            y = 34;
        }        
        er.line( ctx, x, y, x, 48 );
        
    }
    ctx.stroke();
}
/*
##################################################
  表示範囲で目盛りをどうするか判定する
##################################################
*/
checkTimeScaleMode( rangeDate ) {
    if ( rangeDate >= 1000 * 60* 60 * 24 * 365 ) {
        return '1y';
    } else if ( rangeDate >= 1000 * 60 * 60 * 24 * 365 ) {
        return '6M';
    } else if ( rangeDate >= 1000 * 60 * 60 * 24 * 182.5 ) {
        return '3M';
    } else if ( rangeDate >= 1000 * 60 * 60 * 24 * 91.2501 ) {
        return '1M';
    } else if ( rangeDate >= 1000 * 60 * 60 * 24 * 7 ) {
        return '1w';
    } else if ( rangeDate >= 1000 * 60 * 60 * 24 * 3 ) {
        return '1d';
    } else if ( rangeDate >= 1000 * 60 * 60 * 3 ) {
        return '1H';
    } else if ( rangeDate >= 1000 * 60 * 3 ) {
        return '1m';
    } else {
        return '1s';
    }
}
/*
##################################################
  間隔線を描画する
##################################################
*/
setLine() {
    const er = this;
    
    const ctx = er.chartContext.line;
    er.clear( ctx );
    
    const length = Math.floor( er.h / er.lineSpacing ) + 1;
    
    ctx.beginPath();
    ctx.lineWidth = 1;
    ctx.strokeStyle = '#CCC';
    ctx.setLineDash([]);
    for ( let i = 0; i <= length; i++ ) {
        const y = ( i * er.lineSpacing * er.vRate ) - er.vPosition;
        er.line( ctx, 0, y , er.w, y );
    }
    ctx.stroke();
    
    ctx.beginPath();
    ctx.lineWidth = 1;
    ctx.strokeStyle = '#DDD';
    ctx.setLineDash([4,4]);
    for ( let i = 0; i <= length; i++ ) {
        const y = ( ( i * er.lineSpacing ) - ( er.lineSpacing / 2 ) ) * er.vRate - er.vPosition;
        er.line( ctx, 0, y , er.w, y );
    }
    ctx.stroke();
}
/*
##################################################
  イベントブロックを描画する
##################################################
*/
setEventBlock() {
    const er = this;
    
    const
    ctxB = er.chartContext.block,
    ctxE = er.chartContext.incident;
    
    er.clear( ctxB );
    er.clear( ctxE );

    ctxE.strokeStyle = '#FFF';
    
    for ( const event of er.canvasData ) {
        ctxE.beginPath();

        const
        x1 = event.x1 * er.hRate - er.hPosition,
        x2 = ( event.type === 'event')? event.x2 * er.hRate - er.hPosition: x1,
        y = er.getFloorPositonY( event.floor );
        
        const height = er.lineSpacing * er.vRate;
        
        const eventHeight = height - height * .4;
        
        const rectHeight = height - height * .2;
        
        event.block = {
            x: x1 - 8,
            y: y - rectHeight / 2,
            w: x2 - x1 + 16,
            h: rectHeight
        };
        
        const pattern = ( event.type === 'event')? event.pattern: 'action';
        
        // ブロック
        if ( er.currentBlock && er.currentBlock.id === event.id ) {
            er.rect( ctxB, event.block, er.getPatternColor( pattern, 0.5 ) );
        } else {
            er.rect( ctxB, event.block, er.getPatternColor( pattern ) );
        }
        
        if ( event.type === 'event') {
            er.line( ctxE, x1, y, x2, y ); // 開始終了線
            er.line( ctxE, x1, y - eventHeight / 2, x1, y + eventHeight / 2 ); // 開始線
            er.line( ctxE, x2, y - eventHeight / 2, x2, y + eventHeight / 2 ); // 終了線
        } else {
            er.arc( ctxE, x1, y, '#FFF'); // アクション円
        }
        ctxE.fill();
        ctxE.stroke();
    }
}
/*
##################################################
  クリア
##################################################
*/
clear( canvas ) {
    canvas.clearRect( 0, 0, this.w, this.h );
}
/*
##################################################
  四角形
##################################################
*/
rect( canvas, position, color ) {
    canvas.fillStyle = color;
    canvas.fillRect( position.x, position.y, position.w, position.h );
}
/*
##################################################
  四角形クリア
##################################################
*/
clearRect( canvas, position ) {
    canvas.clearRect( position.x, position.y, position.w, position.h );
}
/*
##################################################
  線
##################################################
*/
line( canvas, x1, y1, x2, y2 ) {
    const er = this;
    
    // 範囲外は描画しない
    if (( x1 >= er.w && x2 >= er.w ) || ( x1 <= 0 && x2 <= 0 )) return;
    if (( y1 >= er.h && y2 >= er.h ) || ( y1 <= 0 && y2 <= 0 )) return;
    
    // 1px線の描画がボケるため、位置を調整する    
    canvas.moveTo( x1 + .5, y1 + .5 );
    canvas.lineTo( x2 + .5, y2 + .5 );
}
/*
##################################################
  円
##################################################
*/
arc( canvas, x, y, color ) {
    canvas.fillStyle = color;
    canvas.arc( x, y, 2, 0, 360 * Math.PI / 180, false );
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
setupParts() {
    const er = this;

    er.fetchParts('filter');
    er.fetchParts('action');
    er.fetchParts('rule');
}
/*
##################################################
  各種読み込み
##################################################
*/
fetchParts( type ) {
    const er = this;

    const partsData = er.getPartsData( type );

    fn.fetch( partsData.info ).then(function( info ){
        const params = fn.getCommonParams();
        params.menuNameRest = partsData.rest
        er[ partsData.id ] = { info: info };

        er[ partsData.id ].table = new DataTable( partsData.id, 'view', er[ partsData.id ].info, params, { parts: partsData } );

        er.$.parts.find( partsData.target ).html( er[ partsData.id ].table.setup() );

        // Filterの場合ラベルデータを渡す
        if ( type == 'filter' || type === 'rule') {
            er[ partsData.id ].table.label = er.label;
        }

        // モードチェンジ
        er[ partsData.id ].table.$.container.on({
            'changePartsEditMode': function( e, type ){
                er.$.target.addClass( type + 'EventFlowEditMode');
            },
            'changePartsViewMode': function( e, type ){
                er.$.target.removeClass( type + 'EventFlowEditMode');
            }
        });
        
    }).catch(function( error ){
        if ( error.message ) {
            const message = `<div class="eventFlowPartsNoDate"><div class="eventFlowPartsNoDateInner">${error.message}</div></div>`;
            er.$.parts.find( partsData.target ).html( message );
        }
    });
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
/*
##################################################
  Events
##################################################
*/
setPartsEvents() {
    const er = this;
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
    er.setScrollBarEvent();
    er.canvasSizeResizeObserver();

    er.setMenuButtonEvent();
}
/*
##################################################
  Canvasサイズの変更を監視
##################################################
*/
canvasSizeResizeObserver() {
    const er = this;

    let timer;
    const observer = new ResizeObserver(function(){
        clearTimeout( timer );
        timer = setTimeout( function() {
            er.resetCanvas();
        }, 500 );
    });

    observer.observe( er.$.chart.get(0) );
}
/*
##################################################
  判定
##################################################
*/
blockEnterCheck( block, pointer ) {
    if ( !block ) return;
    return ( ( block.x <= pointer.x && block.x + block.w >= pointer.x ) && ( block.y <= pointer.y && block.y + block.h >= pointer.y ) );
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
  Chart events
##################################################
*/
setChartEvents() {
    const er = this;
    
    er.currentBlock = null;
    
    const
    $window = $( window ),
    $rangeDate = er.$.header.find('.eventFlowChartRangeItem'),
    $hRange = er.$.hScroll.find('.eventFlowRange');
    
    // leave
    const blockLeave = function() {
        er.rect( er.chartContext.block, er.currentBlock.block, er.getPatternColor( er.currentBlock.pattern ) );
        er.currentBlock = null;
        er.$.chart.css('cursor', 'default');
    };
    
    // 範囲指定モードフラグ
    let dateRangeSelectMode = false;
    
    er.$.chart.on({
        'wheel': function( e ) {
            e.preventDefault();
            
            const
            chart = $( this ).get(0),
            x = e.pageX - chart.getBoundingClientRect().left;
            
            // 位置割合
            const positionRate = ( x + er.hPosition ) / ( er.w * er.hRate );
            
            // ホイール向き
            const delta = e.originalEvent.deltaY ? - ( e.originalEvent.deltaY ) : e.originalEvent.wheelDelta ? e.originalEvent.wheelDelta : - ( e.originalEvent.detail );
            
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
            const right = afterWidth - ( afterWidth * positionRate );
            er.hPosition = afterWidth - right - x;
            
            // はみ出る場合の調整
            if ( er.hPosition < 0 ) er.hPosition = 0;
            if ( afterWidth - er.hPosition < er.w ) er.hPosition = afterWidth - er.w;
            
            // Canvas更新
            er.setTimeScale();
            er.setEventBlock();
            
            // スクロールバーサイズ
            $hRange.css({
                width: ( 100 / er.hRate ) + '%',
                left: ( er.hPosition / ( er.w * er.hRate ) * 100 ) + '%'
            })
        },
        'pointerdown': function( e ) {
            const
            chart = $( this ).get(0),
            x = e.pageX - chart.getBoundingClientRect().left;
            
            fn.deselection();

            // 自動更新ストップ
            er.stopAutoUpdate();

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
                        const diff = ( er.end.getTime() - er.start.getTime() ) / 1000;
                        if ( diff <= 1 ) start = new Date( end.getTime() - 1000 );
                        
                        const
                        startText = fn.date( start, 'yyyy/MM/dd HH:mm:ss'),
                        endText = fn.date( end, 'yyyy/MM/dd HH:mm:ss');
                        $rangeDate.show().find('.eventFlowChartRangeDate').text(`${startText} to ${endText}`);
                        
                        er.changeDateReset( start, end, true );
                        er.flag.rangeSelect = true;
                    }

                    if ( er.checkAutoUpdate ) {
                        // 自動更新再開
                        er.resumeAutoUpdate();
                    }
                }
            });
        },
        'pointerup': function( e ) {
            const
            chart = $( this ).get(0),
            x = e.pageX - chart.getBoundingClientRect().left;

            // イベント詳細情報表示
            if ( !dateRangeSelectMode && er.currentBlock ) {
                er.viewEventInfo( x );
            } else {
                er.$.info.hide();
            }
        },
        'pointerenter': function() {
            er.$.positionBorder.css('display', 'block');
            er.$.positionDate.css('display', 'block');
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
        'pointermove': function( e ) {
            const
            chart = $( this ).get(0),
            x = e.pageX - chart.getBoundingClientRect().left,
            y = e.pageY - chart.getBoundingClientRect().top;
            
            if ( !dateRangeSelectMode ) {
                // ポインター位置Xバー
                er.$.positionBorder.css({
                    transform: `translateX(${x-1}px)`
                });
                
                er.viewCurrentInfo( x, e.pageX, e.pageY );
                
                const pointerPosition = {
                    x: x,
                    y: y
                };
                
                // Block leave
                if ( er.currentBlock && !er.blockEnterCheck( er.currentBlock, pointerPosition ) ) {
                    blockLeave();
                }

                // Block enter
                for ( const item of er.canvasData ) {
                    if ( er.blockEnterCheck( item.block, pointerPosition ) ) {
                        er.currentBlock = item;
                        // 描画
                        er.clearRect( er.chartContext.block, item.block );
                        er.rect( er.chartContext.block, item.block, er.getPatternColor( item.pattern, 0.5 ));
                        er.$.chart.css('cursor', 'pointer');
                        break;
                    }
                }
            } else {
                // Block leave
                if ( er.currentBlock ) blockLeave();
            }
        }
    });

    const
    $dateRange = er.$.header.find('.eventFlowDateRangeBlock'),
    $dataRangeRadio = er.$.header.find('.eventFlowDateRangeRadio'),
    $dateRangeButton = er.$.header.find('.eventFlowDateRangeButton');    
    
    // 絞り込みクリア
    $rangeDate.find('.eventFlowChartRangeClear').on('click', function(){
        $rangeDate.hide().find('.eventFlowChartRangeDate').text('');
        er.updateDataRange( $dataRangeRadio.filter(':checked').val(), true );
        er.flag.rangeSelect = false;
    });
    
    // 表示範囲切替
    $dateRange.on('change', '.eventFlowDateRangeRadio', function(){
        const $input = $( this );
        $dateRangeButton.text( $input.next('.radioTextLabel').text() );

        er.stopAutoUpdate();
        er.updateCanvas();

        // リストが開いていたら閉じる
        if ( $dateRangeButton.is('.open') ) {
            $dateRangeButton.click();
        }
    });
}
/*
##################################################
  イベントの詳細情報を表示
##################################################
*/
viewEventInfo( x ) {
    const er = this;

    const d = er.currentBlock.original;

    const css = {display: 'flex'};

    // 表示位置（左右）
    if ( x / er.w > .5 ) {
      css.left = 0;
      css.right = 'auto';
    } else {
      css.right = 0;
      css.left = 'auto';
    }

    er.$.info.css(css);

    const html = [];
    html.push( er.eventInfoRowHtml('Type', d.type ) );
    html.push( er.eventInfoRowHtml('Datetime', d.datetime ) );
    html.push( er.eventInfoRowHtml('ID', d.id ) );

    if ( d.type === 'action') {
        html.push( er.eventInfoRowHtml('Conductor', fn.cv( d.item.CONDUCTOR_INSTANCE_NAME, '')));
        html.push( er.eventInfoRowHtml('Operation', fn.cv( d.item.OPERATION_NAME, '')));
    } else {
        html.push( er.eventInfoRowHtml('Pattern', fn.cv( er.patternList[ er.currentBlock.pattern ], '')));
        html.push( er.eventInfoRowHtml('Labels', '', 'eventInfoTableLabelsBlank') );
        html.push(`<tr class="eventInfoTableTr"><td class="eventInfoTableTd eventInfoTableLabels" colspan="2">${fn.html.labelListHtml( d.item.labels, er.label )}</td></tr>`);
    }

    er.$.info.find('.eventFlowEventInformationInner').html(`<table class="eventInfoTable">${html.join('')}</table>`);
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
/*
##################################################
  指定の範囲で再描画する
##################################################
*/
updateDataTime( range ) {
    let s, e = new Date();
    switch ( range ) {
        case '5M': case '15M': case '30M': {
            const m = Number( range.slice( 0, -1 ) );
            s = new Date( e.getTime() - m * ( 60 * 1000 ) );
        } break;
        case '1h': case '3h': case '6h': case '12h': case '24h': {
            const h = Number( range.slice( 0, -1 ) );
            s = new Date( e.getTime() - h * ( 60 * 60 * 1000 ) );
        } break;
        case '2d': {
            const h = Number( range.slice( 0, -1 ) ) * 24;
            s = new Date( e.getTime() - h * ( 60 * 60 * 1000 ) );
        } break;
        case '1w': {
            const h = Number( range.slice( 0, -1 ) ) * 24 * 7;
            s = new Date( e.getTime() - h * ( 60 * 60 * 1000 ) );
        } break;
        case '1m': case '3m': case '6m':{
            const m = Number( range.slice( 0, -1 ) );
            const now = new Date();
            s = new Date( now.setMonth( now.getMonth() - m ) );
        } break;
        case '1y': case '2y': case '5y':{
            const y = Number( range.slice( 0, -1 ) );
            const now = new Date();
            s = new Date( now.setFullYear( now.getFullYear() - y ) );
        } break;
        default:
            const date = range.split(' to ');
            s = new Date( date[0] );
            e = new Date( date[1] );
    }
    return [ s, e ];
}
/*
##################################################
  選択られている時間から更新
##################################################
*/
updateDataRange( range, rangeFlag = false ) {
    const er = this;

    const newRange = er.updateDataTime( range );
    er.changeDateReset( newRange[0], newRange[1], rangeFlag );
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

            er.resetCanvas();
        });
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
            const
            id = Date.now(),
            value = `${date.from} to ${date.to}`;

            // リスト追加
            const
            $list = er.$.header.find('.eventFlowDateRangeLog'),
            $wrap = $list.closest('.eventFlowDateRangeLogWrap');

            if ( $list.find(`[value="${value}"]`).length === 0 ) {
                $list.prepend( er.addSelectRange( id, value, value ) );
                if ( $wrap.is(':hidden') ) $wrap.addClass('setDate');
            }

            er.$.header.find('.eventFlowDateRangeRadio').val([ value ]).filter(`[value="${value}"]`).change();
        }
    });
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

        const updateCanvasPosition = function() {            
            if ( barType === 'vertical') {
                er.vRate = 1 / ( afterWidth / barWidth );
                er.vPosition = er.h * ( afterPosittion / barWidth ) * er.vRate;
                
                er.setLine();
            } else {
                er.hRate = 1 / ( afterWidth / barWidth );
                er.hPosition = er.w * ( afterPosittion / barWidth ) * er.hRate;
                
                er.setTimeScale();
            }
            er.setEventBlock();
            er.$.chart.click();
        };

        $window.on({
            'pointermove.eventFlow': function( moveEvent ){
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
                
            },
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

}