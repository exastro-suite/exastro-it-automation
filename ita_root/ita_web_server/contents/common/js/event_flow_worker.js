////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Exastro IT Automation / event_flow_worker.js
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

class EventFlowWorker {
/*
##################################################
    Constructor
##################################################
*/
constructor() {
}
/*
##################################################
    message
##################################################
*/
async message( data ) {
    if ( data.type === 'init') {
        await this.init( data );
    } else {
        // type以外を追加
        for ( const key in data ) {
            if ( key === 'type') continue;
            this[ key ] = data[ key ];
        }
        const type = data.type ?? 'unknown';
        this[ type ] ? this[ type ]() : this.unknown( type );
    }
}
/*
##################################################
    初期設定
##################################################
*/
async init( data ) {
    // 初期値
    this.aggregateNumber = 12; // 集約モードの分割数
    this.blockMargin = 48; // ブロックごとの重なり判定マージン
    this.minFloor = 16; // 最小段数
    this.api = data.url; // 履歴取得API URL
    this.maxRate = data.maxRate; // 最大倍率

    // イベントカラー
    this.patternColor = [
        '255,170,0', // 再評価: 0
        '175,65,175', // 未知: 1
        '255,30,30', // 既知（時間切れ）: 2
        '189,204,212', // 既知（判定済）: 3
        '40,170,225', // 新規: 4
        '0,91,172', // アクション: 5
        '0,156,125' // ルール: 6
    ];

    // イベントアイコン
    this.patternIcon = [
        'e935', // 再評価: 0
        'e907', // 未知: 1
        'e939', // 既知（時間切れ）: 2
        'e906', // 既知（判定済）: 3
        'e93b', // 新規: 4
        'e913', // アクション: 5
        'e960', // ルール: 6
        'e961' // ルールバック: 7
    ];

    // パターンID
    this.patternId = [
        'conclusion', // 再評価: 0
        'unknown', // 未知: 1
        'timeout', // 既知（時間切れ）: 2
        'evaluated', // 既知（判定済）: 3
        'newEvent', // 新規: 4
        'action', // アクション: 5
        'rule' // ルール: 6
    ];

    // タイムスケール（日時）
    this.dateCanvas = data.date;
    this.dateCanvas.height = 48;
    this.dateCtx = this.dateCanvas.getContext('2d');

    // 列と区切り（線）
    this.lineCanvas = data.line;
    this.lineCtx = this.lineCanvas.getContext('2d');

    // インシデント（イベント）
    this.eventCanvas = data.incident;
    this.eventCtx = this.eventCanvas.getContext('2d');

    // 繋がり線（リンク）
    this.linkCanvas = data.link;
    this.linkCtx = this.linkCanvas.getContext('2d');

    // TTL
    this.ttlCanvas = data.block;
    this.ttlCtx = this.ttlCanvas.getContext('2d');

    // フォント
    const fontBuffer = data.fontBuffer;
    const blob = new Blob([fontBuffer]);
    const url = URL.createObjectURL(blob);

    // Worker内でフォントを登録
    const font = new FontFace('UiFont', `url(${url})`);
    await font.load();
    self.fonts.add(font);

    // 表示モード
    if ( !this.aggregate ) this.aggregate = true;

    // 繋がり線基準ブロック
    this.basisEventBlock = {
        current: null,
        click: null
    }

    // 表示用データ
    this.canvasData = [];

    // デバックモード
    this.debug = data.debug;

    // 自動モード変更フラグ
    this.autoModeChangeFlag = false;
    this.autoModeChangeNumber = 99;
    this.detailModeChangeFlag = false;
    this.detailModeChangeNumber = 50;

    self.postMessage({
        type: 'init'
    });
}
/*
##################################################
    Canvasサイズ更新
##################################################
*/
updateSize() {
    // width
    this.dateCanvas.width = this.w;
    this.lineCanvas.width = this.w;
    this.eventCanvas.width = this.w;
    this.linkCanvas.width = this.w;
    this.ttlCanvas.width = this.w;

    // height
    this.lineCanvas.height = this.h;
    this.eventCanvas.height = this.h;
    this.linkCanvas.height = this.h;
    this.ttlCanvas.height = this.h;
}
/*
##################################################
    ポーリング
##################################################
*/
async polling() {
    // タイマー
    if ( this.pollingTimerId ) {
        clearTimeout( this.pollingTimerId );
    }

    // すでに読み込み中なら停止する
    if ( this.controller ) this.controller.abort();
    this.controller = new AbortController();

    // 読み込み範囲を変えた場合は自動モード変更フラグをリセット
    if ( this.pollingStartMode !== 'interval' && this.pollingStartMode !== null ) {
        this.autoModeChangeFlag = false;
    }
    this.pollingStartMode = null;

    // 時間
    if ( this.selectDateRange ) {
        const newDate = this.updateDataTime( this.selectDateRange );
        this.loadStart = newDate[0].getTime();
        this.loadEnd = newDate[1].getTime();
    }

    // 範囲選択していない場合は読み込みと表示の時間を合わせる
    if ( this.rangeSelectFlag === false ) {
        this.start = this.loadStart;
        this.end = this.loadEnd;
    }

    // 範囲
    this.period = this.end - this.start;

    // 更新時の時間を画面に返す
    self.postMessage({
        type: 'updateDate',
        start: this.start,
        end: this.end,
        loadStart: this.loadStart,
        loadEnd: this.loadEnd,
        period: this.period
    });

    this.updateSize();

    try {
        // 読込開始
        this.history = await this.getData();
    } catch ( error ) {
        if ( error.name === 'AbortError') {            
            // Abortした場合は処理を中断
            console.warn('Fetch aborted.');
            return;
        } else {
            // エラーがあっても処理を止めない
            console.error( error );
            this.history = [];
        }
    }
    this.progress('process');
    this.createEventData();
    this.progress('end');

    // 表示
    this.setTimeScale();
    this.updateCanvas( true );

    if ( !this.interval ) return;
    this.pollingTimerId = setTimeout( () => {
        this.pollingTimerId = undefined;
        this.polling();
    }, this.interval );
}
/*
##################################################
    範囲変更
##################################################
*/
rangeChange( pollingMode ) {
    // 範囲
    this.period = this.end - this.start;    
    this.updateSize();
    this.setTimeScale();
    this.updateCanvas( pollingMode );
}
/*
##################################################
    範囲クリア
##################################################
*/
rangeClear() {
    this.start = this.loadStart;
    this.end = this.loadEnd;
    this.autoModeChangeFlag = false;
    this.rangeChange( true );

    // クリア時の時間を画面に返す
    self.postMessage({
        type: 'updateDate',
        start: this.start,
        end: this.end,
        loadStart: this.loadStart,
        loadEnd: this.loadEnd,
        period: this.period
    });
}
/*
##################################################
    Canvas更新
##################################################
*/
updateCanvas( pollingMode ) {
    this.progress('process');
    if ( this.aggregate ) {
        // 集約モード
        this.detailModeChangeFlag = false;
        this.createDetailEventData( pollingMode, true );
        // 表示範囲変更時50行以内なら詳細モードに変更する        
        if ( this.detailModeChangeFlag === true && this.rangeChangeFlag === true ) {
            this.detailModeChangeFlag = false;
            this.aggregate = false;
            this.updateCanvas();
            self.postMessage({
                type: 'detailModeChange'
            });
            return;
        }
        this.clearEventLinkLine();
        this.createAggregateEventData();
        this.setAggregateLine();
        this.createAggregateEventBlocks();
    } else {
        // 詳細モード
        this.createDetailEventData( pollingMode );
        if ( this.autoModeChangeFlag === true ) {
            this.autoModeChangeFlag = null;
            this.aggregate = true;
            this.updateCanvas();
            self.postMessage({
                type: 'autoModeChange'
            });
            return;
        }
        this.setLine();
        this.createDetailEventBlocks();
        this.updateLinkLine();
    }
    this.progress('end');
}
/*
##################################################
    Canvas更新（再計算無し）
##################################################
*/
updateCanvasPosition() {
    this.progress('process');
    this.setTimeScale();
    if ( this.aggregate ) {
        // 集約モード
        this.clearEventLinkLine();
        this.setAggregateLine();
        this.createAggregateEventBlocks();
    } else {
        // 詳細モード
        this.setLine();
        this.createDetailEventBlocks();
        this.updateLinkLine();
    }
    this.progress('end');
    self.postMessage({
        type: 'positionChange'
    });
}
/*
##################################################
    繋がり線更新
##################################################
*/
updateLinkLine() {
    this.currentBlock = this.basisEventBlock.current;
    this.clickBlock = this.basisEventBlock.click;

    const currentId = ( this.currentBlock && this.currentBlock.id )? this.currentBlock.id: null;
    const clickId = ( this.clickBlock && this.clickBlock.id )? this.clickBlock.id: null;

    this.clearEventLinkLine();
    if ( currentId !== null ) this.setEventLinkLine( this.currentBlock );
    if ( currentId !== clickId && clickId !== null ) this.setEventLinkLine( this.clickBlock );
}
/*
##################################################
    指定の範囲の時間を取得
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
    トークン更新
##################################################
*/
updateToken() {
    this.tokenResolve();
}
/*
##################################################
    モード変更
##################################################
*/
modeChange() {
    this.updateCanvas();

    self.postMessage({
        type: 'modeChange'
    });
}
/*
##################################################
    現在重なっているイベント判定
##################################################
*/
currentEnter() {
    const flag = this.blockEnterCheck( this.position.current, this.position );
    self.postMessage({
        type: 'currentEnter',
        flag: flag
    });
}
/*
##################################################
    マウスと重なっているイベントを返す
##################################################
*/
blockEnter() {
    for ( const e of this.canvasData ) {
        if ( this.blockEnterCheck( e.block, this.position ) ) {
            this.currentBlock = e;
            const postData = {
                type: 'blockEnter',
                currentBlock: this.currentBlock,
            };

            // グルーピングされている場合はグルーピングデータも返す
            const groupingId = (
                e.item
                && e.item.exastro_filter_group
                && e.item.exastro_filter_group.group_id
            )? e.item.exastro_filter_group.group_id: null;
            if ( groupingId ) {
                postData.grouping = {};
                postData.grouping[ groupingId ] = this.groupingEvents[ groupingId ];
            }

            self.postMessage( postData );
            return;
        }
    }
    self.postMessage({
        type: 'blockEnter',
        currentBlock: null 
    });
}
/*
##################################################
    判定
##################################################
*/
blockEnterCheck( block, pointer ) {
    if ( !block ) return;
    return (
        ( block.x <= pointer.x && block.x + block.w >= pointer.x )
        && ( block.y <= pointer.y && block.y + block.h >= pointer.y )
    );
}
/*
##################################################
    イベントの繋がりを更新
##################################################
*/
updateEventLink() {
    this.updateLinkLine();
    self.postMessage({
        type: 'updateEventLink'
    });
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//  データ読み込み
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    トークン取得
##################################################
*/
async getToken() {
    return new Promise((resolve) => {
        this.tokenResolve = resolve;

        self.postMessage({
            type: 'updateToken'
        });
    });
}
/*
##################################################
    進捗状況
##################################################
*/
progress( text, receivedLength, contentLength ) {
    self.postMessage({
        type: 'progress',
        text: text,
        receivedLength: receivedLength,
        contentLength: contentLength
    });
}
/*
##################################################
    データ読み込み（進捗あり）
##################################################
*/
async getData() {
    // トークン取得
    await this.getToken();

    // 読み込み範囲
    const postData = {
        start_time: fn.date( this.loadStart, 'yyyy/MM/dd HH:mm:ss'),
        end_time: fn.date( this.loadEnd, 'yyyy/MM/dd HH:mm:ss')
    };

    const init = {
        method: 'POST',
        headers: {
            Authorization: `Bearer ${this.token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify( postData )
    };

    // コントローラー
    if ( this.controller ) {
        init.signal = this.controller.signal;
    }

    // イベント処理を間引く
    const progress = this.rafThrottle( this.progress );

    // データ読込開始
    this.progress('start');
    const response = await fetch( this.api, init );

    if ( response.ok ) {
        const reader = response.body.getReader();
        const contentLength = response.headers.get('Content-Length');

        const chunks = [];
        let receivedLength = 0;
        while( true ) {
            const { done, value } = await reader.read();
            if ( done === true ) {
                break;
            } else {
                chunks.push( value );
                receivedLength += value.length;
                progress( null, receivedLength, contentLength );
            }
        }
        const blob = new Blob( chunks );
        const text = await fn.fileToText( blob );
        const json = JSON.parse( text );

        await this.sleep( 50 );
        this.progress('end');
        return json.data ?? [];
    } else {
        throw new Error('');
    }
}
/*
##################################################
    スリープ
##################################################
*/
sleep( ms = 1000 ) {
    return new Promise( resolve => setTimeout( resolve, ms ));
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//  履歴処理
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    イベント処理
##################################################
*/
createEventData() {
    // 履歴データを複製
    const events = fn.arrayCopy( this.history );

    const ruleList = [];
    const ruleIdList = [];
    this.groupingEvents = {};

    for ( const e of events ) {
        // ブロックのソートに使用
        const sortTime =
            // _exastro_fetched_time（イベント発生日時）
            ( e.item && e.item.labels && e.item.labels._exastro_fetched_time )? e.item.labels._exastro_fetched_time:
            // datetimeにはmsが無くAction=>Eventの順になる場合があるため.999を追加する
            ( e.datetime && e.type === 'action')? e.datetime + '.999':
            ( e.datetime )? e.datetime:
            // exastro_created_at（ITAイベント取得日時）
            ( e.item && e.item.exastro_created_at )? e.item.exastro_created_at:
            null;
        e._sortTime = this.parseToEpochMs( sortTime );

        const startTime =
            ( e.item && e.item.labels && e.item.labels._exastro_fetched_time )? e.item.labels._exastro_fetched_time:
            ( e.datetime )? e.datetime:
            null;
        e._startTime = this.parseToEpochMs( startTime );
        
        const endTime =
            ( e.item && e.item.labels && e.item.labels._exastro_end_time )? e.item.labels._exastro_end_time:
            startTime;
        e._endTime = this.parseToEpochMs( endTime );

        // パターン（event or action）
        if ( e.type === 'event') {
            e._pattern = this.checkEventPattern( e.item.labels );

            // グルーピングされたイベント（is_first_event === '0'）
            if (
                e._pattern !== 0
                && e.item
                && e.item.exastro_filter_group
                && e.item.exastro_filter_group.is_first_event === '0'
            ) {
                const groupingId = e.item.exastro_filter_group.group_id;
                if ( !this.groupingEvents[ groupingId ] ) {
                    this.groupingEvents[ groupingId ] = {
                        startTime: [],
                        lastStartTime: 0,
                        count: 0
                    }
                };
                const groupData = this.groupingEvents[ groupingId ];
                if ( e._startTime > groupData.lastStartTime ) groupData.lastStartTime = e._startTime;
                groupData.count++;
                groupData.startTime.push(e._startTime);

                // デバッグ時はグルーピングイベントを表示する
                if ( this.debug ) {
                    e._grouping = false;
                } else {
                    e._grouping = true;
                    continue;
                }
            }
        } else if ( e.type === 'action') {
            e._pattern = 5;
        }

        // ルール確認
        const eventList = this.getEventList(e);
        const ruleInfo = this.getRuleInfo(e);
        if ( eventList && ruleInfo ) {
            // ユニークルールID
            const ruleId = ruleInfo.id + eventList.toString();

            // Inイベント
            if ( !e._before ) e._before = [];
            if ( !e._before.includes( ruleId ) ) e._before.push( ruleId );

            // ルール枠の作成
            if ( ruleIdList.indexOf( ruleId ) === -1 ) {
                ruleList.push( this.createRuleData( e, eventList, ruleId, ruleInfo ) );
                ruleIdList.push( ruleId );
            } else {
                const rule = ruleList.find(function(r){
                    return ruleId === r.id;
                });

                if ( rule ) {
                    if ( rule.datetime > e.datetime ) {
                        rule.datetime = e.datetime;
                        rule._startTime = rule._endTime = e._startTime;
                        rule._sortTime = e._sortTime;
                    }
                    rule._after.push( e.id );
                }
            }

            // Outイベント
            for ( const id of eventList ) {
                const event = events.find(function(e){
                    return e.id === id;
                });
                if ( event !== undefined ) {
                    if ( !event._after ) event._after = [];
                    if ( event._after.indexOf( ruleId ) === -1 ) {
                        event._after.push( ruleId );
                    }
                }
            }
        }
    }
    // 繋がりのあるイベントをまとめる
    let linkCount = 1;
    this.linkEventList = {
        groupData: {},
        groupInfo: {},
        group: {}
    };

    // 繋がりの無いデータ
    this.singleEvent = [];

    // 履歴にルールを追加
    this.eventList = ruleList.concat( events );

    // データの振り分け
    for ( const e of this.eventList ) {
        // 繋がりがあるかどうか
        if ( e._after || e._before ) {
            this.eventLinkCheck( e.id, 'group' + linkCount++ );
        } else {
            if ( e._grouping ) continue;
            this.singleEvent.push( e );
        }
    }
}
/*
##################################################
    すでにいずれかのグループに入っているかチェック
##################################################
*/
eventGroupCheck( id ) {
    for ( const key in this.linkEventList.group ) {
        if ( this.linkEventList.group[ key ].includes( id ) ) return true;
    }
    return false;
}
/*
##################################################
    つながりのあるIDをチェック
##################################################
*/
eventLinkCheck( eventId, groupId ) {
    if ( this.eventGroupCheck( eventId ) ) return;

    // チェック用IDリスト
    if ( !this.linkEventList.group[ groupId ] ) this.linkEventList.group[ groupId ] = [];
    this.linkEventList.group[ groupId ].push( eventId );

    const e = this.eventList.find( i => eventId === i.id );
    if ( e !== undefined ) {
        e.group = groupId;

        // グループごとの範囲
        if ( !this.linkEventList.groupInfo[ groupId ] ) {
            this.linkEventList.groupInfo[ groupId ] = {};
        }
        if ( !this.linkEventList.groupInfo[ groupId ].minTime || this.linkEventList.groupInfo[ groupId ].minTime > e._startTime ) {
            this.linkEventList.groupInfo[ groupId ].minTime = e._startTime;
        }
        if ( !this.linkEventList.groupInfo[ groupId ].maxTime || this.linkEventList.groupInfo[ groupId ].maxTime < e._endTime ) {
            this.linkEventList.groupInfo[ groupId ].maxTime = e._endTime;
        }

        // イベントデータ
        if ( !this.linkEventList.groupData[ groupId ] ) this.linkEventList.groupData[ groupId ] = [];
        this.linkEventList.groupData[ groupId ].push( e );

        // 繋がり
        if ( e._after ) {
            for ( const id of e._after ) {
                this.eventLinkCheck( id, groupId );
            }
        }
        if ( e._before ) {
            for ( const id of e._before ) {
                this.eventLinkCheck( id, groupId );
            }
        }
    }
};
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
        _before: eventList,
        _after: [ e.id ],
        _sortTime: e._sortTime,
        _startTime: e._startTime,
        _endTime: e._endTime,
        info: ruleInfo,
        _pattern: 6
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
        return 0; // 'conclusion';
    }
    // 未知
    if ( labels._exastro_undetected === '1') {
        return 1; // 'unknown';
    }
    // 既知（時間切れ）
    if ( labels._exastro_timeout === '1') {
        return 2; // 'timeout';
    }
    // 既知（判定済）
    if ( labels._exastro_evaluated === '1') {
        return 3; // 'evaluated';
    }
    // 新規
    return 4; // 'newEvent';
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//  詳細モード
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    詳細データ作成
##################################################
*/
createDetailEventData( pollingMode, floorCheckMode = false ) {
    // 描画用イベント位置情報
    this.canvasData = [];

    // 階層
    const floor = [];

    // ソート順
    const patternNumber = {
        rule: 1,
        conclusion: 2,
        action: 3
    };

    // グループの階層データの作成
    for ( const groupId in this.linkEventList.groupData ) {
        const group = this.linkEventList.groupData[ groupId ];

        group.sort(function( a, b ){
            if ( a._sortTime < b._sortTime ) {
                return -1;
            } else if ( a._sortTime > b._sortTime ) {
                return 1;
            } else {
                // 同じ時間の場合
                const a2 = ( patternNumber[ a._pattern ] )? patternNumber[ a._pattern ]: 0;
                const b2 = ( patternNumber[ b._pattern ] )? patternNumber[ b._pattern ]: 0;
                if ( a2 < b2 ) {
                    return -1;
                } else if ( a2 > b2 ) {
                    return 1;
                } else {
                    return 0;
                }
            }
        });

        const minTime = this.linkEventList.groupInfo[ groupId ].minTime;
        const minX = this.getDatePositionX( minTime );
        const maxTime = this.linkEventList.groupInfo[ groupId ].maxTime;
        const maxX = this.getDatePositionX( maxTime );

        // 範囲外のグループは表示しない
        if ( maxTime < this.start || minTime > this.end ) continue;

        for ( const e of group ) {
            e.floor = undefined;
            this.createFloorData( floor, e, 0, minX, maxX, null, 'group', floorCheckMode );
            if ( this.autoModeChangeFlag === true ) return;
        }
    }

    // 100行超えているか？
    if ( this.autoModeChangeCheck( pollingMode, floor.length ) ) return;

    // 集約モードで50行超えた場合は処理終了
    if ( this.detailModeChangeCheck( floor.length ) ) return;

    // 単発イベント階層データの作成
    const singleLength = this.singleEvent.length;
    for ( let i = 0; i < singleLength; i++ ) {
        const e = this.singleEvent[i];
        // ひとつ前のイベントとの差が1000ms未満の場合はチェックする階層をその階層からにする
        const p = this.singleEvent[i-1];
        let f = 0;
        if ( p && e._sortTime - p._sortTime < 1000 ) {
            f = p.floor + 1;
        }
        this.createFloorData( floor, e, f, null, null, pollingMode, 'single', floorCheckMode );
        if ( this.autoModeChangeFlag === true ) return;
        if ( this.detailModeChangeCheck( floor.length ) ) return;
    }

    // 段数
    this.floorLength = ( floor.length > this.minFloor )? floor.length: this.minFloor;
    this.lineSpacing = Math.round( this.h / ( this.floorLength  ) * 10000 ) / 10000;
    if ( this.debug ) console.log('最大階数', this.floorLength );

    // 範囲変更時、集約モードで50行以内になるなら詳細モードに変更する
    if ( floorCheckMode === true && this.floorLength <= this.detailModeChangeNumber ) {
        this.detailModeChangeFlag = true;
    }
}
/*
##################################################
    イベントの階層データを調べる
##################################################
*/
createFloorData( floor, e, f, x1, x2, pollingMode, eventType, floorCheckMode ) {
    // 表示パターンチェック
    const patternId = this.patternId[ e._pattern ];
    if ( this.displayFlag[ patternId ] === false ) return;

    const start = e._startTime;
    const end = e._endTime; 

    // 繋がりの無いイベントは表示範囲外を除外する
    if ( eventType === 'single' && ( end < this.start || start > this.end ) ) return;

    e.x1 = this.getDateWidthPositionX( start );
    if ( end ) {
        e.x2 = this.getDateWidthPositionX( end );
    } else {
        e.x2 = e.x1;
    }
    if ( !x1 ) x1 = e.x1;
    if ( !x2 ) x2 = e.x2;

    // 重なり防止マージン
    const m = this.blockMargin;
    e.floor = undefined;
    while ( e.floor === undefined ) {
        if ( floor[f] === undefined ) floor[f] = -Infinity;        
        if ( floor[f] < x1 ) {
            floor[f] = x2 + m;
            e.floor = f;
        } else {
            f++;
        }
        if ( this.autoModeChangeCheck( pollingMode, f ) ) return;
        if ( floorCheckMode === true && this.detailModeChangeCheck( f ) ) return;
    }
    this.canvasData.push( e );
}
/*
##################################################
    段数チェック
##################################################
*/
autoModeChangeCheck( pollingMode, f ) {
    if ( pollingMode === true && this.autoModeChangeFlag === false && f > this.autoModeChangeNumber ) {
        console.warn('Event block exceeds 100 lines. Change to aggregate mode.');
        this.autoModeChangeFlag = true;
        return true;
    } else {
        return false
    }
}
/*
##################################################
    詳細モード段数チェック
##################################################
*/
detailModeChangeCheck( f ) {
    return this.aggregate === true && f > this.detailModeChangeNumber;
}
/*
##################################################
    間隔線を描画する
##################################################
*/
setLine() {
    const ctx = this.lineCtx;
    this.clear( ctx );

    this.vRateNum = this.vRate;
    const maxRate = this.h / 8 / this.lineSpacing;
    this.vRateNum = 1 + ( this.vRate - 1 ) * ((maxRate - 1) / this.maxRate );
    this.vPositionNum = this.vPosition * ((maxRate - 1) / this.maxRate);

    const lineSpacingWidth = this.lineSpacing * this.vRateNum;
    if ( lineSpacingWidth < 8 ) return;

    const fontSize = ( lineSpacingWidth / 2 > 12 )? 12: lineSpacingWidth / 2;
    const length = Math.floor( this.h / this.lineSpacing ) + 1;

    ctx.beginPath();
    ctx.lineWidth = 1;
    ctx.strokeStyle = this.getBorderColor();
    ctx.fillStyle = this.getTextColor();
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    ctx.font = `${fontSize}px Consolas`;
    ctx.setLineDash([]);
    for ( let i = 0; i <= length; i++ ) {
        const y = ( i * lineSpacingWidth ) - this.vPositionNum;
        if ( y < 0 || y > this.h ) continue;
        this.line( ctx, 0, y , this.w, y );
    }
    ctx.stroke();

    ctx.beginPath();
    ctx.lineWidth = 1;
    ctx.strokeStyle = this.getBorderColor();
    ctx.setLineDash([4,4]);
    for ( let i = 0; i <= length; i++ ) {
        const y = ( ( i * this.lineSpacing ) - ( this.lineSpacing / 2 ) ) * this.vRateNum - this.vPositionNum;
        if ( y < 0 || y > this.h ) continue;
        this.line( ctx, 0, y , this.w, y );
        ctx.fillText(i, this.w - 8, y );
    }
    ctx.stroke();
}
/*
##################################################
    イベントブロックを描画する
##################################################
*/
createDetailEventBlocks() {
    const er = this;

    const ico = er.eventCtx;
    er.clear( ico );

    const fontSize = er.lineSpacing * er.vRateNum * .5;
    ico.textAlign = 'center';
    ico.textBaseline = 'middle';
    ico.font = fontSize + 'px UiFont';

    const ttl = er.ttlCtx;
    er.clear( ttl );

    const lineSpacingWidth = this.lineSpacing * this.vRateNum;
    const lineWidth = ( lineSpacingWidth < 8 )? 1: 2;
    ttl.lineWidth = lineWidth;

    for ( const event of er.canvasData ) {
        const
        x1 = er.round( event.x1 * er.hRate - er.hPosition ) - ( lineWidth / 2 - 1 ),
        y = er.getFloorPositonY( event.floor );

        const blockHeight = er.round( er.lineSpacing * er.vRateNum * .7 );
        event.block = {
            x: er.round( x1 - blockHeight / 2 ),
            y: er.round( y - blockHeight / 2 ),
            w: blockHeight,
            h: blockHeight,
            centerX: x1,
            centerY: y
        };

        // 画面外は描画しない
        if ( y < 0 || y > this.h ) continue;

        // TTL 線
        if ( event.type === 'event') {
            const
            x2 = er.round( event.x2 * er.hRate - er.hPosition ) - ( lineWidth / 2 - 1 ),
            h = er.round( ( er.lineSpacing * er.vRateNum ) - ( er.lineSpacing * er.vRateNum * .4 ) );

            ttl.beginPath();

            ttl.strokeStyle = er.getPatternColor( event._pattern );

            er.line( ttl, x1, y, x2, y ); // 横線
            er.line( ttl, x1, y - h / 2, x1, y + h / 2 ); // 開始縦線
            er.line( ttl, x2, y - h / 2, x2, y + h / 2 ); // 終了縦線
            ttl.stroke();
        }

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
    if ( e._pattern !== 6 ) {
        if (
            e._pattern !== 0
            && e.item
            && e.item.exastro_filter_group
            && e.item.exastro_filter_group.is_first_event === '1'
            && er.groupingEvents[ e.item.exastro_filter_group.group_id ]
        ) {
            // グルーピングブロック
            const groupId = e.item.exastro_filter_group.group_id;
            const groupEvent = er.groupingEvents[ groupId ];
            const blockHeight = er.round( er.lineSpacing * er.vRateNum * .7 );
            const endX = er.getDatePositionX( groupEvent.lastStartTime );
            const block = {
                x: e.block.x,
                y: e.block.y,
                w: endX - e.block.x + blockHeight / 2,
                h: e.block.h,
                centerX: e.block.centerX,
                centerY: e.block.centerY,
            };
            er.roundRect( ctx, block, r, er.getPatternColor( e._pattern, .4 ) );

            // 各位置に丸を描画
            const arcHeight = er.round( er.lineSpacing * er.vRateNum * .06 );
            for ( const startTime of groupEvent.startTime ) {
                const setX = er.getDatePositionX( startTime );
                ctx.beginPath();
                er.arc( ctx, arcHeight, setX, e.block.centerY, er.getPatternColor( e._pattern, .8 ) );
                ctx.closePath();
                ctx.fill();
            }

            // 基本ブロック
            er.roundRect( ctx, e.block, r, er.getPatternColor( e._pattern, opacity ) );
        } else {
            // 基本ブロック
            er.roundRect( ctx, e.block, r, er.getPatternColor( e._pattern, opacity ) );
        }
    } else {
        er.roundRect( ctx, e.block, r, er.getPatternColor( e._pattern, opacity ), null, null, true );
    }

    ctx.fillStyle = "#FFF";
    ctx.fillText( er.getPatternIcon( e._pattern ), e.block.centerX, e.block.centerY );
}
/*
##################################################
    イベントの繋がりを描画する
##################################################
*/
setEventLinkLine( targetBlock ) {
    const er = this;
    if ( !targetBlock && !targetBlock.item ) return;    

    // 最新のデータに
    const eventData = er.canvasData.find( i => i.id === targetBlock.id );
    if ( !eventData ) return;

    const ctx = er.linkCtx;

    // グループ化されたイベントリスト
    const groupEventList = [ eventData ];

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
        const event  = er.canvasData.find( i => i.id === targetId );
        if ( event && event.block ) {
            groupEventList.push( event );
            setLine( 6, backLineColor, x, y, event.block.centerX, event.block.centerY );
            setLine( 2, lineColor, x, y, event.block.centerX, event.block.centerY );
            targetLink( event );
        }
    };
    const targetLink = function( event ){
        if ( event._before ) {
            for ( const id of event._before ) {
                linkLine( event.block.centerX, event.block.centerY, id );
            }
        }
        if ( event._after ) {
            for ( const id of event._after ) {
                linkLine( event.block.centerX, event.block.centerY, id );
            }
        }
    };
    targetLink( eventData );

    // 枠を描画する
    for ( const e of groupEventList ) {
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
/*
##################################################
    イベントの繋がりをクリア
##################################################
*/
clearEventLinkLine() {
    this.clear( this.linkCtx )
};
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//  集約モード
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    集約データ作成
##################################################
*/
createAggregateEventData() {
    const minAggregate = this.start;
    const maxAggregate = ( this.end < Date.now() )? this.end: Date.now();
    const sizeAggregate = ( maxAggregate - minAggregate ) / this.aggregateNumber;
    const typesAggregate = 7;
    this.countsAggregate = new Uint32Array( this.aggregateNumber * typesAggregate );

    for ( const e of this.eventList ) {
        // 範囲外は除外
        if ( e._sortTime < minAggregate || e._sortTime > maxAggregate ) continue;
        // どの位置にはいるか (|0は整数化)
        const position = (( e._sortTime - minAggregate) / sizeAggregate ) | 0;
        this.countsAggregate[ position + e._pattern * this.aggregateNumber ]++;
    }
}
/*
##################################################
    集約ブロック
##################################################
*/
createAggregateEventBlocks() {
    // 再評価: 0
    // 未知: 1
    // 既知（時間切れ）: 2
    // 既知（判定済）: 3
    // 新規: 4
    // アクション: 5
    // ルール: 6
    const viewOrder = [ 3, 6, 5, 0, 2, 4, 1 ];

    const ctx = this.eventCtx;
    this.clear( ctx );
    this.clear( this.ttlCtx );

    const endDate = ( this.end < Date.now() )? this.end: Date.now();    
    const areaWidth = this.getDatePositionX( endDate );
    const aggregateWidth = this.round( areaWidth / this.aggregateNumber );
    const w = Math.round( aggregateWidth * 0.6 );
    const r = w * .1;
    
    let fontSize = Math.round( w * .2 );
    if ( fontSize < 8 ) fontSize = 8;
    let borderFontSize = Math.round( aggregateWidth * .1 );
    if ( borderFontSize < 8 ) borderFontSize = 8;
    
    for ( let i = 0; i < this.aggregateNumber; i++ ) {
        const x = this.round( aggregateWidth * i + aggregateWidth / 2 ) - w / 2;

        let floor = 0; // 階層
        let y = w / 2 + borderFontSize;
        for ( const pattern of viewOrder ) {
            // 表示パターンチェック
            const patternId = this.patternId[ pattern ];
            if ( this.displayFlag[ patternId ] === false ) continue;

            const number = this.countsAggregate[ i + this.aggregateNumber * pattern ];
            if ( number > 0 ) {
                // ルールイベント
                const rotateFlag = ( pattern === 6 )? true: false;

                // ブロック
                this.roundRect( this.eventCtx, {
                    x: x,
                    y: y,
                    w: w,
                    h: w,
                }, r, this.getPatternColor( pattern, 1 ), null, null, rotateFlag );
    
                // 件数
                ctx.textAlign = 'center';
                ctx.textBaseline = 'top';
                ctx.font = `bold ${fontSize}px Consolas`;
                ctx.fillStyle = this.getPatternColor( pattern, 1 );
                ctx.fillText( number, x + w / 2, y + w + 8 );

                // アイコン
                const iconSize = w * .8;
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.font = iconSize + 'px UiFont';
                ctx.fillStyle = "#FFF";
                ctx.fillText( this.getPatternIcon( pattern ), x + w / 2, y + w / 2 );

                floor++;
                y += Math.round( w * 1.5 );
            }
        }
    }
}
/*
##################################################
    集約分割線
##################################################
*/
setAggregateLine() {
    const ctx = this.lineCtx;
    this.clear( ctx );

    const endDate = ( this.end < Date.now() )? this.end: Date.now();
    const areaWidth = this.getDatePositionX( endDate );
    const aggregateWidth = this.round( areaWidth / this.aggregateNumber );
    let borderX = 0;
    let borderFontSize = Math.round( aggregateWidth * .1 );
    if ( borderFontSize < 8 ) borderFontSize = 8;

    for ( let i = 0; i < this.aggregateNumber; i++ ) {
        // 分割時間
        const date = fn.date( this.getPositionDate( borderX ), 'yyyy/MM/dd-HH:mm:ss').split('-');
        ctx.fillStyle = this.getBorderColor();
        ctx.textAlign = 'left';
        ctx.textBaseline = 'top';
        ctx.font = `${borderFontSize}px Consolas`;
        ctx.fillText( date[0], borderX + 8, 8 );
        ctx.fillText( date[1], borderX + 8, 8 + borderFontSize );

        // 分割線
        if ( this.aggregateNumber - 1 !== i ) {
            borderX += aggregateWidth;
            ctx.beginPath();
            ctx.lineWidth = 1;
            ctx.strokeStyle = this.getBorderColor();
            ctx.setLineDash([2, 2]);
            ctx.moveTo( borderX + .5, .5 );
            ctx.lineTo( borderX + .5, this.h + .5 );
            ctx.stroke();
        }
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//  タイムスケール
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    タイムスケールを描画する
##################################################
*/
setTimeScale() {
    const ctx = this.dateCtx;

    this.dateCanvas.width = this.w;

    ctx.clearRect( 0, 0, this.w, this.h );
    ctx.beginPath();
    ctx.lineWidth = 1;
    ctx.strokeStyle = this.getBorderColor();

    // テキスト共通
    ctx.textBaseline = 'top';
    ctx.fillStyle = this.getTextColor();

    // 左端の線
    ctx.moveTo( .5, .5 );
    ctx.lineTo( .5, this.h + .5 );
    ctx.textAlign = 'left';
    ctx.font = 'bold 14px Consolas';

    const start = this.getPositionDate( 0 );
    ctx.fillText( fn.date( start, 'yyyy/MM/dd HH:mm:ss'), 8, 0 );

    // 右端の線
    ctx.moveTo( this.w - .5, .5 );
    ctx.lineTo( this.w - .5, this.h + .5 );
    ctx.textAlign = 'right';

    const end = this.getPositionDate( this.w );
    ctx.fillText( fn.date( end, 'yyyy/MM/dd HH:mm:ss'), this.w - 8, 0 );

    // 目盛り
    const diffDate = end - start;

    // 表示範囲からタイプを設定する
    const mode = this.checkTimeScaleMode( diffDate );

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
    const endLineDate = new Date( this.end );

    ctx.textAlign = 'center';
    ctx.font = 'normal 12px Consolas';

    let beforeTextX = -Infinity;
    while ( startLineDate < endLineDate ) {
        const startLineDateTime = startLineDate.getTime();
        const x = this.getDatePositionX( startLineDateTime );

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
        this.line( ctx, x, y, x, 48 );

    }
    ctx.stroke();

    // 現在時刻線
    const nowX = this.getDatePositionX( Date.now() );
    self.postMessage({
        type: 'nowLine',
        nowX: nowX
    });
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
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//  Canvas 描画
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    Allクリア
##################################################
*/
allClear() {
    this.clear( this.lineCtx );
    this.clear( this.ttlCtx );
    this.clear( this.eventCtx );
    this.clear( this.linkCtx );
}
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
    // 範囲外は描画しない
    if (( x1 >= this.w && x2 >= this.w ) || ( x1 <= 0 && x2 <= 0 )) return;
    if (( y1 >= this.h && y2 >= this.h ) || ( y1 <= 0 && y2 <= 0 )) return;

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
    パターンアイコン
##################################################
*/
getPatternIcon( pattern ) {
    const iconInt = parseInt( this.patternIcon[pattern], 16 );
    const iconStr = String.fromCharCode( iconInt );
    return iconStr;
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
    四捨五入
##################################################
*/
round( num ) {
    return Math.round( num * 100 ) / 100;
}
/*
##################################################
    階層からY座標を取得する
##################################################
*/
getFloorPositonY( floor ) {
    return this.round( floor * this.lineSpacing * this.vRateNum + ( this.lineSpacing * this.vRateNum / 2 ) - this.vPositionNum );
}
/*
##################################################
    X座標から時間を取得
##################################################
*/
getPositionDate( x ) {
    return this.start + this.period * ( ( x + this.hPosition ) / ( this.w * this.hRate ) );
}
/*
##################################################
    表示している範囲からX座標を取得する
##################################################
*/
getDatePositionX( date ) {
    return this.round( this.w * this.hRate * ( ( date - this.start ) / this.period ) - this.hPosition );
}
/*
##################################################
    全体の範囲からX座標を取得する
##################################################
*/
getDateWidthPositionX( date ) {
    return this.round( this.w * ( ( date - this.start ) / this.period ));
}
/*
##################################################
    new Dateを使用せずにdate形式に変換
##################################################
*/
parseToEpochMs(s, defaultOffsetMinutes = 540) {
    if (!s) return null;

    // 速判定：ISO(yyyy-mm-ddThh:mm:ssZ...) か？
    // 例: 2025-11-06T00:10:16.684000Z
    if (s.length >= 20 && s[4] === '-' && s[10] === 'T' && (s.endsWith('Z') || s.includes('Z'))) {
        const Y = (s.charCodeAt(0)-48)*1000 + (s.charCodeAt(1)-48)*100
            + (s.charCodeAt(2)-48)*10   + (s.charCodeAt(3)-48);
        const M = (s.charCodeAt(5)-48)*10 + (s.charCodeAt(6)-48);
        const D = (s.charCodeAt(8)-48)*10 + (s.charCodeAt(9)-48);
        const h = (s.charCodeAt(11)-48)*10 + (s.charCodeAt(12)-48);
        const m = (s.charCodeAt(14)-48)*10 + (s.charCodeAt(15)-48);
        const sec = (s.charCodeAt(17)-48)*10 + (s.charCodeAt(18)-48);

        // .ffffff の上位3桁のみを読む（なければ0）
        let ms = 0;
        const dot = s.indexOf('.', 19);
        if (dot !== -1) {
            const c1 = s.charCodeAt(dot+1);
            const c2 = s.charCodeAt(dot+2);
            const c3 = s.charCodeAt(dot+3);
            if (c1 >= 48 && c1 <= 57) ms += (c1 - 48) * 100;
            if (c2 >= 48 && c2 <= 57) ms += (c2 - 48) *  10;
            if (c3 >= 48 && c3 <= 57) ms += (c3 - 48);
            // 3桁未満なら、足りない桁は 0 埋め扱い（数字以外は無視）
        }
        return Date.UTC(Y, M-1, D, h, m, sec, ms); // そのままUTC
    }

    // スラッシュ形式 "YYYY/MM/DD HH:MM:SS[.fff]" をローカル(=defaultOffsetMinutes)として解釈
    // 例: 2025/11/06 09:10:16
    //     2025/11/06 09:10:16.999
    // 前提：秒までは必須・タイムゾーン表記なし
    if (s.length >= 19 && s[4] === '/' && s[7] === '/' && (s[10] === ' ' || s[10] === 'T')) {
        const Y  = (s.charCodeAt(0)-48)*1000 + (s.charCodeAt(1)-48)*100
            + (s.charCodeAt(2)-48)*10   + (s.charCodeAt(3)-48);
        const Mo = (s.charCodeAt(5)-48)*10 + (s.charCodeAt(6)-48);
        const D  = (s.charCodeAt(8)-48)*10 + (s.charCodeAt(9)-48);
        const h  = (s.charCodeAt(11)-48)*10 + (s.charCodeAt(12)-48);
        const m  = (s.charCodeAt(14)-48)*10 + (s.charCodeAt(15)-48);
        const sec= (s.charCodeAt(17)-48)*10 + (s.charCodeAt(18)-48);

        // ".fff" があればミリ秒として読む（上位3桁まで）
        let ms = 0;
        const dot = s.indexOf('.', 19); // "YYYY/MM/DD HH:MM:SS" までは19文字
        if (dot !== -1) {
            const c1 = s.charCodeAt(dot+1);
            const c2 = s.charCodeAt(dot+2);
            const c3 = s.charCodeAt(dot+3);
            if (c1 >= 48 && c1 <= 57) ms += (c1 - 48) * 100;
            if (c2 >= 48 && c2 <= 57) ms += (c2 - 48) *  10;
            if (c3 >= 48 && c3 <= 57) ms += (c3 - 48);
            // 2桁や1桁しかなくても、残りは 0 埋め扱い
        }

        // ローカル(既定オフセット)→UTC へ変換
        const utcLike = Date.UTC(Y, Mo-1, D, h, m, sec, ms);
        return utcLike - defaultOffsetMinutes * 60_000;
    }

    return null;
}

}