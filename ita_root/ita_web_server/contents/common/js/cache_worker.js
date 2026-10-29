////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Exastro IT Automation / cache_worker.js
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
//
//   複数タブ間で共有するメモリ上のキャッシュ
//
//   ・SharedWorkerとして同一オリジンの全タブから接続され、値をこのワーカーの変数として保持する
//   ・ディスクには一切書き出さないため、全タブを閉じるとキャッシュも破棄される
//   ・値はJSON文字列で保持する（postMessageの構造化クローンを軽くし、サイズを測るため）
//   ・データの読み込み自体は行わない。メインスレッド側でキャッシュを問い合わせ、
//     なければ従来どおり読み込み、結果をsetで預ける
//
//   ・同一オリジンに別ユーザ（別組織）のタブが同時に存在し得るため、接続ごとに
//     オーナー（ユーザID）を登録し、オーナーが一致しないエントリは返さない
//
////////////////////////////////////////////////////////////////////////////////////////////////////

(function(){
'use strict';

// キャッシュ本体（Mapの挿入順を利用してLRUを実現する）
// key -> { owner, json, expires }
const store = new Map();

// 接続ポートごとのオーナー（ユーザID）
// port -> owner
const owners = new Map();

// 保持するJSON文字列の合計長の上限
const limitLength = 64 * 1024 * 1024;

// 保持しているJSON文字列の合計長
let totalLength = 0;

/*
##################################################
   キャッシュを削除する
##################################################
*/
const drop = function( key ) {
    const entry = store.get( key );
    if ( entry !== undefined ) {
        totalLength -= entry.json.length;
        store.delete( key );
    }
};

/*
##################################################
   上限を超えている分を古い順に削除する
##################################################
*/
const trim = function() {
    for ( const key of [ ...store.keys() ] ) {
        if ( totalLength <= limitLength ) break;
        drop( key );
    }
};

/*
##################################################
   キャッシュを取得する
##################################################
*/
const get = function( owner, key ) {
    const entry = store.get( key );

    // 未登録
    if ( entry === undefined ) return null;

    // 別のユーザが登録したエントリは返さない
    if ( entry.owner !== owner ) return null;

    // 期限切れ
    if ( entry.expires <= Date.now() ) {
        drop( key );
        return null;
    }

    // 参照されたので末尾に移動する（LRUの更新）
    store.delete( key );
    store.set( key, entry );

    return entry.json;
};

/*
##################################################
   キャッシュを登録する
##################################################
*/
const set = function( owner, key, json, ttl ) {
    if ( typeof json !== 'string') return;

    drop( key );

    store.set( key, {
        owner: owner,
        json: json,
        expires: Date.now() + ttl
    });
    totalLength += json.length;

    trim();
};

/*
##################################################
   前方一致でまとめて削除する（自分のオーナーのみ）
##################################################
*/
const invalidate = function( owner, prefix ) {
    for ( const [ key, entry ] of [ ...store.entries() ] ) {
        if ( entry.owner === owner && key.indexOf( prefix ) === 0 ) drop( key );
    }
};

/*
##################################################
   指定したオーナーのキャッシュをすべて削除する
   ※ログアウト時に呼ばれる。別ユーザのタブに影響を与えない
##################################################
*/
const clear = function( owner ) {
    for ( const [ key, entry ] of [ ...store.entries() ] ) {
        if ( entry.owner === owner ) drop( key );
    }
};

/*
##################################################
   現在の状態を返す（デバッグ用）
   ※キーの一覧は自分のオーナーの分だけ返す
##################################################
*/
const status = function( owner ) {
    const keys = [];
    for ( const [ key, entry ] of store.entries() ) {
        if ( entry.owner === owner ) keys.push( key );
    }
    return {
        count: store.size,
        length: totalLength,
        limit: limitLength,
        ports: owners.size,
        keys: keys
    };
};

/*
##################################################
   メッセージ処理
##################################################
*/
const message = function( port, data ) {
    if ( data === undefined || data === null ) return;

    const owner = owners.get( port );

    switch ( data.type ) {
        // オーナー（ユーザID）を登録する。接続直後に一度だけ送られる
        case 'attach':
            owners.set( port, data.owner );
            if ( data.id !== undefined ) port.postMessage({ id: data.id });
        break;

        // キャッシュを問い合わせる（未登録・期限切れの場合もhit:falseを返す）
        case 'get': {
            const json = get( owner, data.key );
            if ( json !== null ) {
                port.postMessage({ id: data.id, hit: true, json: json });
            } else {
                port.postMessage({ id: data.id, hit: false });
            }
        } break;

        // キャッシュを預ける
        case 'set':
            set( owner, data.key, data.json, data.ttl );
            if ( data.id !== undefined ) port.postMessage({ id: data.id });
        break;

        // 前方一致で破棄する（更新系の処理を行ったあとなど）
        case 'invalidate':
            invalidate( owner, data.prefix );
            if ( data.id !== undefined ) port.postMessage({ id: data.id });
        break;

        // 自分のオーナーのキャッシュをすべて破棄する（ログアウト時）
        case 'clear':
            clear( owner );
            if ( data.id !== undefined ) port.postMessage({ id: data.id });
        break;

        // 状態を返す
        case 'status':
            port.postMessage({ id: data.id, status: status( owner ) });
        break;
    }
};

/*
##################################################
   タブからの接続
##################################################
*/
self.addEventListener('connect', function( event ){
    const port = event.ports[0];

    owners.set( port, null );

    port.addEventListener('message', function( e ){
        try {
            message( port, e.data );
        } catch( error ) {
            console.error( error );
            // 呼び出し元を待たせないように応答する
            if ( e.data && e.data.id !== undefined ) {
                port.postMessage({ id: e.data.id, hit: false, error: true });
            }
        }
    });

    port.start();
});

}());
