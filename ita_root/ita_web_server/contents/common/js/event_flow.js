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

    er.intervalTime = fn.storage.get('eventflow_interval_time', 'local', false ); // 更新間隔
    if ( er.intervalTime === false ) er.intervalTime = 5000;

    er.blockMargin = 48; // ブロックごとの重なり判定マージン
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

    // パターンアイコン
    er.patternIcon = {
        newEvent: 'e93b',
        evaluated: 'e906',
        unknown: 'e907',
        timeout: 'e939',
        conclusion: 'e935',
        action: 'e913',
        rule: 'e960',
        ruleBack: 'e961'
    };

    // 各種フラグ
    er.flag = {
        rangeSelect: false,
        buttonInvalid: false
    } ;

    // 履歴データ用
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
        nowDate: $target.find('.eventFlowNowDate'),
        info: $target.find('.eventFlowEventInformation'),
        parts: $target.find('.eventFlowParts'),
    };

    // Chart canvas
    er.chartCanvas = {
        line: er.$.body.find('.eventFlowChartPositionLineCanvas').get(0),
        block: er.$.body.find('.eventFlowChartBlockCanvas').get(0),
        incident: er.$.body.find('.eventFlowChartIncidentCanvas').get(0),
        link: er.$.body.find('.eventFlowChartLinkCanvas').get(0)
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
            { html: { html: rangeSelectHtml }, separate: true, className: 'eventFlowChartRangeItem', display: 'none'},
            { html: { html: er.patternSelectHTML() }, separate: true }
        ],
        Sub: [
            { html: { html: er.updateIntervalSelectHTML() } }
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
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//  Canvas
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    四捨五入
##################################################
*/
round( num ) {
    return Math.round( num * 100 ) / 100;
}
/*
##################################################
    表示データの作成
##################################################
*/
createCanvasData() {
    const er = this;

    // 履歴データを複製
    const history = fn.arrayCopy( er.history );

    const ruleList = [];
    const ruleIdList = [];

    // イベントのつながりを作成
    // ルールリストの作成
    for ( const e of history ) {
        // パターン
        if ( e.type === 'event') {
            e.pattern = er.checkEventPattern( e.item.labels );
        } else {
            e.pattern = e.type;
        }

        const eventList = er.getEventList(e);
        const ruleInfo = er.getRuleInfo(e);

        // 座標
        if ( e.type === 'event') {
            e.x1 = er.getDateWidthPositionX( e.item.labels._exastro_fetched_time );
            e.x2 = er.getDateWidthPositionX( e.item.labels._exastro_end_time );
        } else {
            e.x1 = e.x2 = er.getDateWidthPositionX( e.datetime );
        }

        if ( eventList && ruleInfo ) {
            // ユニークルールID
            const ruleId = ruleInfo.id + eventList.toString();

            // Inイベント
            if ( !e.before ) e.before = [];
            if ( e.before.indexOf( ruleId ) === -1 ) {
                e.before.push( ruleId );
            }

            // ルール枠の作成
            if ( ruleIdList.indexOf( ruleId ) === -1 ) {
                ruleList.push( er.createRuleData( e, eventList, ruleId, ruleInfo ) );
                ruleIdList.push( ruleId );
            } else {
                const rule = ruleList.find(function(r){
                    return ruleId === r.id;
                });

                if ( rule ) {
                    if ( rule.datetime > e.datetime ) {
                        rule.datetime = e.datetime;
                        rule.x1 = rule.x2 = e.x1;
                    }
                    rule.after.push( e.id );
                }
            }

            // Outイベント
            for ( const id of eventList ) {
                const event = history.find(function(e){
                    return e.id === id;
                });
                if ( event !== undefined ) {
                    if ( !event.after ) event.after = [];
                    if ( event.after.indexOf( ruleId ) === -1 ) {
                        event.after.push( ruleId );
                    }
                }
            }
        }
    }

    // イベントをグループ化する
    er.groupList = {
        groupData: {},
        groupInfo: {},
        group: {},
        singleData: []
    };
    let groupCount = 1;

    // すでにいずれかのグループに入っているかチェック
    const eventGroupCheck = function( id ){
        for ( const key in er.groupList.group ) {
            if ( er.groupList.group[ key ].indexOf( id ) !== -1 ) return true;
        }
        return false;
    };

    // つながりのあるIDをチェック
    const eventLinkCheck = function( eventId, groupId ){
        if ( eventGroupCheck( eventId ) ) return;

        // チェック用IDリスト
        if ( !er.groupList.group[ groupId ] ) er.groupList.group[ groupId ] = [];
        er.groupList.group[ groupId ].push( eventId );

        const e = list.find(function( item ){
            return eventId === item.id;
        });

        if ( e ) {
            e.group = groupId;

            // グループごとの範囲
            if ( !er.groupList.groupInfo[ groupId ] ) er.groupList.groupInfo[ groupId ] = {};
            if ( !er.groupList.groupInfo[ groupId ].minX || er.groupList.groupInfo[ groupId ].minX > e.x1 ) er.groupList.groupInfo[ groupId ].minX = e.x1;
            if ( !er.groupList.groupInfo[ groupId ].maxX || er.groupList.groupInfo[ groupId ].maxX < e.x2 ) er.groupList.groupInfo[ groupId ].maxX = e.x2;

            // イベントデータ
            if ( !er.groupList.groupData[ groupId ] ) er.groupList.groupData[ groupId ] = [];
            er.groupList.groupData[ groupId ].push( e );

            // 繋がり
            if ( e.after ) {
                for ( const id of e.after ) {
                    eventLinkCheck( id, groupId );
                }
            }
            if ( e.before ) {
                for ( const id of e.before ) {
                    eventLinkCheck( id, groupId );
                }
            }
        }
    };

    // 履歴にルールを追加
    const list = ruleList.concat( history );

    // データの振り分け
    for ( const e of list ) {
        // 繋がりがあるかどうか
        if ( e.after || e.before ) {
            eventLinkCheck( e.id, 'group' + groupCount++ );
        } else {
            er.groupList.singleData.push( e );
        }
    }

    // 描画用イベント位置情報
    er.canvasData = [];

    // 階層
    const floor = [];

    const createFloorData = function( e, x1, x2 ){
        // 表示パターンチェック
        if ( er.displayFlag[ e.pattern ] === false ) return;

        if ( !x1 ) x1 = e.x1;
        if ( !x2 ) x2 = e.x2;

        // 何段目のどの位置に入るか調べる
        const m = er.blockMargin;
        let f = 0;
        while ( e.floor === undefined ) {
            if ( !floor[f] ) floor[f] = [];

            const l = floor[f].length;
            if ( l === 0 || floor[f][l-1].x2 + m < x1 ) {
                floor[f].push({ x1: x1, x2: x2 });
                e.floor = f;
            } else if ( floor[f][0].x1 - m > x2 ) {
                floor[f].unshift({ x1: x1, x2: x2 });
                e.floor = f;
            } else if ( floor[f][0].x2 + m < x1 && x2 < floor[f][l-1].x1 - m ) {
                for ( let i = 0; i <= l - 1; i++ ) {
                    if ( floor[f][i].x2 + m < x1 && x2 < floor[f][i+1].x1 - m ) {
                        floor[f].splice( i + 1, 0, { x1: x1, x2: x2 });
                        e.floor = f;
                        break;
                    }
                }
            }
            f++;
        }
        er.canvasData.push( e );
    };

    // グループの階層データの作成
    const patternNumber = {
        rule: 1,
        conclusion: 2,
        action: 3
    };
    for ( const groupId in er.groupList.groupData ) {
        const group = er.groupList.groupData[ groupId ];

        group.sort(function( a, b ){
            if ( a.datetime < b.datetime ) {
                return -1;
            } else if ( a.datetime > b.datetime ) {
                return 1;
            } else {
                // 同じ時間の場合
                const a2 = ( patternNumber[ a.pattern ] )? patternNumber[ a.pattern ]: 0;
                const b2 = ( patternNumber[ b.pattern ] )? patternNumber[ b.pattern ]: 0;
                if ( a2 < b2 ) {
                    return -1;
                } else if ( a2 > b2 ) {
                    return 1;
                } else {
                    return 0;
                }
            }
        });

        const
        minX = er.groupList.groupInfo[ groupId ].minX,
        maxX = er.groupList.groupInfo[ groupId ].maxX;

        for ( const e of group ) {
            createFloorData( e, minX, maxX );
        }
    }

    // 単発イベント階層データの作成
    for ( const e of er.groupList.singleData ) {
        createFloorData( e );
    }

    // 段数
    const floors = ( floor.length > er.minFloor )? floor.length: er.minFloor;
    er.lineSpacing = Math.round( er.h / floors * 100 ) / 100;
}
/*
##################################################
    イベントデータからイベントリストを返す
##################################################
*/
getEventList( e ) {
    const exastro_events = (function(){
        if ( e.type === 'action' && e.item && e.item.EVENT_ID_LIST ) {
            // "EVENT_ID_LIST": "ObjectId('XXX1'),ObjectId('XXX2')"
            return e.item.EVENT_ID_LIST.split(',');
        } else if ( e.type === 'event' && e.item && e.item.exastro_events ) {
            // "exastro_events": [
            //    "ObjectId('XXX1')",
            //    "ObjectId('XXX2')",
            // ],
            return e.item.exastro_events;
        }
        return null;
    })();

    if ( exastro_events ) {
        const list = [];
        for ( const id of exastro_events ) {
            if ( fn.typeof( id ) === 'string' && id.match(/^ObjectId/) ) {
                const rId = id.replace(/ObjectId\(\'(.+)\'\)/, "$1");
                list.push( rId );
            }
        }
        return list.sort();
    } else {
        return null;
    }
}
/*
##################################################
    イベントデータからルール情報を返す
##################################################
*/
getRuleInfo( e ) {
    if ( e.type === 'action' && e.item && e.item.RULE_ID && e.item.RULE_NAME ) {
        return {
            id: e.item.RULE_ID,
            name: e.item.RULE_NAME
        };
    } else if ( e.type === 'event' && e.item && e.item.exastro_rules && e.item.exastro_rules[0] ) {
        const id = ( e.item.exastro_rules[0].id )? e.item.exastro_rules[0].id: '';
        const name = ( e.item.exastro_rules[0].name )? e.item.exastro_rules[0].name: '';
        return {
            id: id,
            name: name
        };
    } else {
        return null;
    }
}
/*
##################################################
    ルールデータの作成
##################################################
*/
createRuleData( e, eventList, ruleId, ruleInfo ) {
    const ruleData = {
        id: ruleId,
        type: 'rule',
        datetime: e.datetime,
        before: eventList,
        after: [ e.id ],
        x1: e.x1,
        x2: e.x2,
        info: ruleInfo,
        pattern: 'rule'
    };
    return ruleData;
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

    er.colorMode = ( $('body').is('.darkmode') )? 'darkmode': '';

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

    if (er.ignoreErrorCount == undefined) {
        er.ignoreErrorCount = 0
    }

    fn.fetch('/oase/event_flow/history/', null, 'POST', postData, { controller: er.controller }, true, er.ignoreErrorCount ).then(function( history ){
        if ( history === undefined ) return;

        if ( initFlag ) {
            er.$.target.removeClass('nowLoading');
            er.setEvents();
        }

        if (history.errorIgnored == true) {
            // エラーを無視した場合は、イベント情報の更新をしない
            er.ignoreErrorCount += 1
        } else {
            er.ignoreErrorCount = undefined // エラーを無視した回数をリセット
            er.history = history;
        }

        er.controller = null;
        er.updateDate = Date.now();

        // キャンバス
        er.resetCanvas();

        // 自動更新
        if ( er.intervalTime !== 0 ) {
            er.timerId = setTimeout(function(){
                er.updateCanvas();
            }, er.intervalTime );
        } else {
            er.timerId = null;
        }
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

    // 読み込み中の場合は停止
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
        // window.console.warn('resumeAutoUpdate() warning.');
        return;
    }

    if ( er.intervalTime !== 0 ) {
        er.timerId = setTimeout(function(){
            er.updateCanvas();
        }, er.resumeDate );
    } else {
        er.timerId = null;
    }
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

    // 繋がり線
    if ( er.clickBlock ) er.setEventLink( er.clickBlock );
    if ( er.currentBlock ) er.setEventLink( er.currentBlock );
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
    表示している範囲からX座標を取得する
##################################################
*/
getDatePositionX( date ) {
    const er = this;
    return er.round( er.w * er.hRate * ( ( new Date( date ).getTime() - er.start.getTime() ) / er.period ) - er.hPosition );
}
/*
##################################################
    全体の範囲からX座標を取得する
##################################################
*/
getDateWidthPositionX( date ) {
    const er = this;
    return er.round( er.w * ( ( new Date( date ).getTime() - er.start.getTime() ) / er.period ));
}
/*
##################################################
    階層からY座標を取得する
##################################################
*/
getFloorPositonY( floor ) {
    const er = this;
    return er.round( floor * er.lineSpacing * er.vRate + ( er.lineSpacing * er.vRate / 2 ) - er.vPosition );
}
/*
##################################################
    線の色
##################################################
*/
getBorderColor() {
    return ( this.colorMode === 'darkmode')? '#666': '#CCC';
}
/*
##################################################
    テキストの色
##################################################
*/
getTextColor() {
    return ( this.colorMode === 'darkmode')? '#AAA': '#666';
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
    ctx.strokeStyle = er.getBorderColor();

    // テキスト共通
    ctx.textBaseline = 'top';
    ctx.fillStyle = er.getTextColor();

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

    // 現在時刻線
    const paddingLeft = 16; // .eventFlowBodyInner
    const nowX = er.getDatePositionX( Date.now() );
    if ( nowX > er.w ) {
        er.$.nowDate.hide();
    } else if ( nowX < 0 ) {
        er.$.nowDate.show().addClass('noBorder').css({
            left: paddingLeft,
            width: er.w
        });
    } else {
        er.$.nowDate.show().removeClass('noBorder').css({
            left: nowX + paddingLeft,
            width: er.w - nowX
        });
    }
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
    } else if ( rangeDate >= 1000 * 60 * 60 * 6 ) {
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

    const lineSpacingWidth = er.lineSpacing * er.vRate;
    if ( lineSpacingWidth < 8 ) return;

    const length = Math.floor( er.h / er.lineSpacing ) + 1;

    ctx.beginPath();
    ctx.lineWidth = 1;
    ctx.strokeStyle = er.getBorderColor();
    ctx.setLineDash([]);
    for ( let i = 0; i <= length; i++ ) {
        const y = ( i * lineSpacingWidth ) - er.vPosition;
        er.line( ctx, 0, y , er.w, y );
    }
    ctx.stroke();

    ctx.beginPath();
    ctx.lineWidth = 1;
    ctx.strokeStyle = er.getBorderColor();
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

    const ico = er.chartContext.incident;
    er.clear( ico );

    const fontSize = er.lineSpacing * er.vRate * .5;
    ico.textAlign = 'center';
    ico.textBaseline = 'middle';
    ico.font = fontSize + 'px exastro-ui-icons';

    const ttl = er.chartContext.block;
    er.clear( ttl );
    ttl.lineWidth = 2;

    for ( const event of er.canvasData ) {
        const
        x1 = er.round( event.x1 * er.hRate - er.hPosition ),
        y = er.getFloorPositonY( event.floor );

        if ( event.type === 'event') {
            const
            x2 = er.round( event.x2 * er.hRate - er.hPosition ),
            h = er.round( ( er.lineSpacing * er.vRate ) - ( er.lineSpacing * er.vRate * .4 ) );

            ttl.beginPath();

            ttl.strokeStyle = er.getPatternColor(event.pattern);

            er.line( ttl, x1, y, x2, y ); // 横線
            er.line( ttl, x1, y - h / 2, x1, y + h / 2 ); // 開始縦線
            er.line( ttl, x2, y - h / 2, x2, y + h / 2 ); // 終了縦線
            ttl.stroke();
        }

        const blockHeight = er.round( er.lineSpacing * er.vRate * .7 );
        event.block = {
            x: er.round( x1 - blockHeight / 2 ),
            y: er.round( y - blockHeight / 2 ),
            w: blockHeight,
            h: blockHeight,
            centerX: x1,
            centerY: y
        };
        er.eventBlock( ico, event );
    }
}
/*
##################################################
    ブロックを描画する
##################################################
*/
eventBlock( ctx, e, opacity = 1 ) {
    const er = this;

    const r = e.block.h *.1;
    if ( e.pattern !== 'rule') {
        er.roundRect( ctx, e.block, r, er.getPatternColor( e.pattern, opacity ) );
    } else {
        er.roundRect( ctx, e.block, r, er.getPatternColor( e.pattern, opacity ), null, null, true );
    }

    ctx.fillStyle = "#FFF";
    ctx.fillText( er.getPatternIcon( e.pattern ), e.block.centerX, e.block.centerY );
}
/*
##################################################
    パターンアイコン
##################################################
*/
getPatternIcon( pattern ) {
    const er = this;

    const
    iconInt = parseInt( er.patternIcon[pattern], 16 ),
    iconStr = String.fromCharCode( iconInt );

    return iconStr;
}
/*
##################################################
    イベントの繋がりを描画する
##################################################
*/
setEventLink( targetBlock ) {
    if ( !targetBlock && !targetBlock.item ) return;

    const er = this;

    const groupData = (function(){
        if ( targetBlock.group ) {
            if ( er.groupList.groupData[ targetBlock.group ] ) {
                return er.groupList.groupData[ targetBlock.group ];
            } else {
                return [];
            }
        } else {
            const e = er.groupList.singleData.find(function(event){
                return event.id === targetBlock.id;
            });
            if ( e !== undefined ) {
                return [ e ]
            } else {
                return [];
            }
        }
    }());

    // 最新のデータに
    const eventData = groupData.find(function( item ){
        return item.id === targetBlock.id;
    });
    if ( !eventData ) return;

    const ctx = er.chartContext.link;

    // 線を描画する
    const doneList = [];
    const backLineColor = ( er.colorMode === 'darkmode')? '#111': '#FFF';
    const lineColor = ( er.colorMode === 'darkmode')? '#577397': '#005BAC';
    const lineColor2 = ( er.colorMode === 'darkmode')? '#99AAC0': '#577397';
    const setLine = function( width, color, x1, y1 , x2, y2 ){
        const lX = ( x1 < x2 )? x1: x2;
        const lY = ( y1 > y2 )? y1: y2;
        ctx.beginPath();
        ctx.moveTo( x1, y1 );
        ctx.lineTo( lX, lY );
        ctx.lineTo( x2, y2 );
        ctx.lineWidth = width;
        ctx.strokeStyle = color;
        ctx.stroke();
        ctx.closePath();
    };
    const linkLine = function( x, y, targetId ){
        if ( doneList.indexOf( targetId ) !== -1 ) return;
        doneList.push( targetId );
        const event  = groupData.find(function( e ){
            return e.id === targetId;
        });

        if ( event && event.block ) {
            setLine( 6, backLineColor, x, y, event.block.centerX, event.block.centerY );
            setLine( 2, lineColor, x, y, event.block.centerX, event.block.centerY );

            targetLink( event );
        }
    };
    const targetLink = function( event ){
        if ( event.before ) {
            for ( const id of event.before ) {
                linkLine( event.block.centerX, event.block.centerY, id );
            }
        }
        if ( event.after ) {
            for ( const id of event.after ) {
                linkLine( event.block.centerX, event.block.centerY, id );
            }
        }
    };
    targetLink( eventData );

    // 枠を描画する
    for ( const e of groupData ) {
        if ( e.block ) {
            const ruleFlag = ( e.type === 'rule');
            er.roundRect( ctx, e.block, e.block.h * .1, backLineColor, null, null, ruleFlag, true );


            const hover = ( er.currentBlock && e.id === er.currentBlock.id )? ( er.colorMode !== 'darkmode')? 'rgba(255,255,255,.5)': 'rgba(0,0,0,.3)' : null;
            if ( er.clickBlock && e.id === er.clickBlock.id ) {
                er.roundRect( ctx, e.block, e.block.h * .1, null, backLineColor, 8, ruleFlag );
                er.roundRect( ctx, e.block, e.block.h * .1, hover, lineColor, 4, ruleFlag );
                er.roundRect( ctx, e.block, e.block.h * .1, hover, lineColor2, 2, ruleFlag );
            } else {
                er.roundRect( ctx, e.block, e.block.h * .1, null, backLineColor, 6, ruleFlag );
                er.roundRect( ctx, e.block, e.block.h * .1, hover, lineColor, 2, ruleFlag );
            }
        }
    }
}
clearEventLink() {
    const er = this;

    const ctx = er.chartContext.link;
    er.clear( ctx )
};
/*
##################################################
    クリア
##################################################
*/
clear( ctx ) {
    ctx.clearRect( 0, 0, this.w, this.h );
}
/*
##################################################
    四角形
##################################################
*/
rect( ctx, position, color ) {
    ctx.fillStyle = color;
    ctx.fillRect( position.x, position.y, position.w, position.h );
}
/*
##################################################
    四角形（角丸）
##################################################
*/
roundRect( ctx, p, r, fill = null, stroke = null, lineWidth = 1, rotateFlag = false, clearFlag = false ) {
    ctx.beginPath();

    // 図形部分を消去する
    if ( clearFlag ) ctx.globalCompositeOperation = 'destination-out';

    // 菱形にする（45度回転）
    let rotate = {};
    if ( rotateFlag ) {
        ctx.save();
        ctx.translate( p.x + p.w / 2, p.y + p.h / 2 );
        ctx.rotate( ( Math.PI / 180 ) * 45 );
        ctx.scale( .85, .85);
        ctx.translate( - ( p.x + p.w / 2 ), - ( p.y + p.h / 2 ) );
    }

    // 角丸四角形
    ctx.moveTo( p.x + r, p.y );
    ctx.lineTo( p.x + p.w - r, p.y );
    ctx.arc( p.x + p.w - r, p.y + r, r, Math.PI * ( 3 / 2 ), 0, false );
    ctx.lineTo( p.x + p.w, p.y + p.h - r );
    ctx.arc( p.x + p.w - r, p.y + p.h - r, r, 0, Math.PI * ( 1 / 2 ), false );
    ctx.lineTo( p.x + r, p.y + p.h );
    ctx.arc( p.x + r, p.y + p.h - r, r, Math.PI * ( 1 / 2 ), Math.PI, false );
    ctx.lineTo( p.x, p.y + r );
    ctx.arc( p.x + r, p.y + r, r, Math.PI, Math.PI * ( 3 / 2 ), false );

    // 塗り
    if ( fill ) {
        ctx.fillStyle = fill;
        ctx.fill();
    }

    // 線
    if ( stroke ) {
        ctx.lineWidth = lineWidth;
        ctx.strokeStyle = stroke;
        ctx.stroke();
    }

    // 回転を戻す
    if ( rotateFlag ) {
        ctx.restore();
    }

    // 合成方法をデフォルトに戻す
    if ( clearFlag ) ctx.globalCompositeOperation = 'source-over';

    ctx.closePath();
}
/*
##################################################
    四角形クリア
##################################################
*/
clearRect( ctx, position ) {
    ctx.clearRect( position.x, position.y, position.w, position.h );
}
/*
##################################################
    線
##################################################
*/
line( ctx, x1, y1, x2, y2 ) {
    const er = this;

    // 範囲外は描画しない
    if (( x1 >= er.w && x2 >= er.w ) || ( x1 <= 0 && x2 <= 0 )) return;
    if (( y1 >= er.h && y2 >= er.h ) || ( y1 <= 0 && y2 <= 0 )) return;

    // 1px線の描画がボケるため、位置を調整する
    ctx.moveTo( x1 + .5, y1 + .5 );
    ctx.lineTo( x2 + .5, y2 + .5 );
}
/*
##################################################
    円
##################################################
*/
arc( ctx, size, x, y, color ) {
    ctx.fillStyle = color;
    ctx.arc( x, y, size, 0, 360 * Math.PI / 180, false );
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
    er.fetchSettings('eventCollectionSettings');
    er.fetchSettings('filterSettings');
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

        const option = {
            parts: partsData
        };

        er[ partsData.id ].table = new DataTable( partsData.id, 'view', er[ partsData.id ].info, params, option );

        // ソートセット
        er[ partsData.id ].table.sort = [{ ASC: partsData.partsRestName }];

        er.$.parts.find( partsData.target ).html( er[ partsData.id ].table.setup() );

        // Filter及びRule場合ラベルデータを渡す
        if ( type === 'filter' || type === 'rule') {
            er[ partsData.id ].table.label = er.label;
        }

        // モードチェンジ
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

    }).catch(function( error ){
        if ( error.message ) {
            const message = `<div class="eventFlowPartsNoDate"><div class="eventFlowPartsNoDateInner">${error.message}</div></div>`;
            er.$.parts.find( partsData.target ).html( message );
        }
    });
}

// ID変換用にイベント収集設定・フィルター設定を取得
fetchSettings( type ) {
    const er = this;
    const settingsData = er.getSettingsData( type );
    fn.fetch( settingsData.info, null, 'POST', settingsData.data ).then(function( data ){
        er[ type ] = data;

    }).catch(function( error ){
        er[ type ] = { error }
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
                er.resetCanvas();
            }, 500 );
        }
        er.observeInit = false;
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

    const
    $window = $( window ),
    $rangeDate = er.$.header.find('.eventFlowChartRangeItem'),
    $hRange = er.$.hScroll.find('.eventFlowRange');

    // leave
    const blockLeave = function() {
        // 最新のデータに更新
        er.currentBlock = er.canvasData.find(function(item){
            return item.id === er.currentBlock.id;
        });
        if ( er.currentBlock ) {
            er.$.chart.css('cursor', 'default');
        }
        er.currentBlock = null;

        // 繋がり線
        er.clearEventLink();
        if ( er.clickBlock ) er.setEventLink( er.clickBlock );
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

            er.clearEventLink();
            if ( er.clickBlock ) er.setEventLink( er.clickBlock );

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
            er.clearEventLink();

            // イベント詳細情報表示
            if ( !dateRangeSelectMode && er.currentBlock ) {
                er.viewEventInfo( x );
                er.clickBlock = er.currentBlock;
                er.setEventLink( er.clickBlock );
            } else {
                er.hideEventInfo( x );
                if ( !dateRangeSelectMode ) er.clickBlock = null;
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
                for ( const e of er.canvasData ) {
                    if ( er.blockEnterCheck( e.block, pointerPosition ) ) {
                        er.currentBlock = e;
                        er.$.chart.css('cursor', 'pointer');

                        er.setEventLink( er.currentBlock );
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
    $dateRangeButton = er.$.header.find('.eventFlowDateRangeButton');

    // 絞り込みクリア
    $rangeDate.find('.eventFlowChartRangeClear').on('click', function(){
        const date = er.$.header.find('.eventFlowDateRangeRadio').filter(':checked').val();
        $rangeDate.hide().find('.eventFlowChartRangeDate').text('');
        er.updateDataRange( date, true );
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
        html.push( er.eventInfoRowHtml('Pattern', fn.cv( er.patternList[ er.currentBlock.pattern ], '')));
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
            html.push( er.eventInfoRowHtml('Group', '', 'eventInfoTableLabelsBlank'));
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
    const er = this;

    const d = er.clickBlock;

    er.$.info.hide();
    er.$.parts.find('.eventFlowPartsShow').removeClass('eventFlowPartsShow').show();
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

    // 現在時刻から範囲の1/10を追加する
    const endDate = function( start ) {
        const now = Date.now();
        return new Date( now + ( ( now - start.getTime() ) / 10 ) );
    }

    switch ( range ) {
        case '5M': case '15M': case '30M': {
            const m = Number( range.slice( 0, -1 ) );
            s = new Date( e.getTime() - m * ( 60 * 1000 ) );
            e = endDate(s);
        } break;
        case '1h': case '3h': case '6h': case '12h': case '24h': {
            const h = Number( range.slice( 0, -1 ) );
            s = new Date( e.getTime() - h * ( 60 * 60 * 1000 ) );
            e = endDate(s);
        } break;
        case '2d': {
            const h = Number( range.slice( 0, -1 ) ) * 24;
            s = new Date( e.getTime() - h * ( 60 * 60 * 1000 ) );
            e = endDate(s);
        } break;
        case '1w': {
            const h = Number( range.slice( 0, -1 ) ) * 24 * 7;
            s = new Date( e.getTime() - h * ( 60 * 60 * 1000 ) );
            e = endDate(s);
        } break;
        case '1m': case '3m': case '6m':{
            const m = Number( range.slice( 0, -1 ) );
            const now = new Date();
            s = new Date( now.setMonth( now.getMonth() - m ) );
            e = endDate(s);
        } break;
        case '1y': case '2y': case '5y':{
            const y = Number( range.slice( 0, -1 ) );
            const now = new Date();
            s = new Date( now.setFullYear( now.getFullYear() - y ) );
            e = endDate(s);
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
    選択している時間から更新
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

            if ( $button.is('.eventFlowIntervalSelectButton') ) {
                er.stopAutoUpdate();
            }
        } else {
            $window.off('pointerdown.eventFlowSelect');
            if ( $button.is('.eventFlowIntervalSelectButton') ) {
                er.resumeAutoUpdate();
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

            er.resetCanvas();
        });
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
                er.vRate = Math.round( 1 / ( afterWidth / barWidth ) * 100 ) / 100;
                er.vPosition = Math.round( er.h * ( afterPosittion / barWidth ) * er.vRate * 100 ) / 100;

                er.setLine();
            } else {
                er.hRate = Math.round( 1 / ( afterWidth / barWidth ) * 100 ) / 100;
                er.hPosition = Math.round( er.w * ( afterPosittion / barWidth ) * er.hRate * 100 ) / 100;

                er.setTimeScale();
            }

            er.clearEventLink();
            er.setEventBlock();
            er.$.chart.click();

            if ( er.clickBlock ) er.setEventLink( er.clickBlock );
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