////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Exastro IT Automation / common.js
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

/*
##################################################
   Common function
##################################################
*/
const fn = ( function() {
    'use strict';

    // バージョン
    const version = '2.5.0';

    // AbortController
    const controller = new AbortController();

    // インスタンス管理用
    const modalInstance = {},
          operationInstance = {},
          conductorInstance = {};

    let messageInstance = null,
        uiSettingInstance = null;

    // Contentローディングフラグ
    let contentLoadingFlag = false;

    // windowオブジェクトがあるかどうか
    const windowCheck = function() {
        try {
            window;
            return true;
        } catch( e ) {
            return false;
        }
    };
    const windowFlag = windowCheck();

    // CommonAuth check
    const commonAuthCheck = function() {
        try {
            CommonAuth;
            return true;
        } catch( e ) {
            return false;
        }
    };
    const cmmonAuthFlag = commonAuthCheck();

    // iframeフラグ
    const iframeFlag = windowFlag? ( window.parent !== window ): false;

    const
    organization_id = ( windowFlag && cmmonAuthFlag )? CommonAuth.getRealm():
        ( iframeFlag && window.parent.getToken )? window.parent.getRealm(): null,
    workspace_id =  ( windowFlag && cmmonAuthFlag )? window.location.pathname.split('/')[3]:
        ( iframeFlag && window.parent.getWorkspace )? window.parent.getWorkspace(): null;

    const typeofValue = function( value ) {
        return Object.prototype.toString.call( value ).slice( 8, -1 ).toLowerCase();
    };

    const classNameCheck = function( className, type ) {
        if ( fn.typeof( className ) === 'array') {
            className = className.concat([ type ]);
        } else {
            className = [ className, type ];
        }
        return className;
    };

    const bindAttrs = function( attrs ) {
        const attr = [];

        for ( const key in attrs ) {
            if ( attrs[key] !== undefined ) {
                const attrName = ['checked', 'disabled', 'title', 'placeholder', 'style', 'class', 'readonly', 'multiple']; // dataをつけない
                if ( attrName.indexOf( key ) !== -1) {
                    attr.push(`${key}="${attrs[key]}"`);
                } else {
                    attr.push(`data-${key}="${attrs[key]}"`);
                }
            }
        }
        return attr;
    };

    const inputCommon = function( value, name, attrs, id ) {
        const attr = bindAttrs( attrs );

        if ( value !== undefined && value !== null ) {
            attr.push(`value="${value}"`);
        }

        if ( name ) {
            if ( id ) {
                attr.push(`id="${id}"`);
            } else {
                attr.push(`id="${name}"`);
            }
            attr.push(`name="${name}"`);
        }

        return attr;
    };

const cmn = {
/*
##################################################
   共通パラメーター
##################################################
*/
getCommonParams: function() {
    return Object.assign( {}, commonParams );
},
/*
##################################################
   cmmonAuthが使えるか返す
##################################################
*/
getCmmonAuthFlag: function() {
    return cmmonAuthFlag;
},
/*
##################################################
   UIバージョンを返す
##################################################
*/
getUiVersion: function() {
    return version;
},
/*
##################################################
   script, styleの読み込み
##################################################
*/
loadAssets: function( assets ){
    const f = function( type, url, id ){
        return new Promise(function( resolve, reject ){
            type = ( type === 'css')? 'link': 'script';
            url = url + '?v=' + version;

            const body = document.getElementById('container'),
                  asset = document.createElement( type );

            switch ( type ) {
                case 'script':
                    asset.src = url;
                    if ( id ) asset.id = id;
                break;
                case 'link':
                    asset.href = url;
                    asset.rel = 'stylesheet';
                    if ( id ) asset.id = id;
                break;
            }

            body.appendChild( asset );

            asset.onload = function() {
                resolve();
            };

            asset.onerror = function( e ) {
                reject( e )
            };
        });
    };
    if ( typeofValue( assets ) === 'array') {
        return Promise.all(
            assets.map(function( asset ){
                return f( asset.type, asset.url, asset.id );
            })
        );
    } else {
        return f( assets.type, assets.url, assets.id );
    }
},
/*
##################################################
   ワークスペース切替用URL
##################################################
*/
getWorkspaceChangeUrl: function( changeId ) {
    return `/${organization_id}/workspaces/${changeId}/ita/`;
},
/*
##################################################
   REST API用のURLを返す
##################################################
*/
getRestApiUrl: function( url, orgId = organization_id, wsId = workspace_id ) {
    return `/api/${orgId}/workspaces/${wsId}/ita${url}`;
},
/*
##################################################
   データ読み込み
##################################################
*/
fetch: function( url, token, method = 'GET', data, option = {} ) {

    if ( !token ) {
        token = ( cmmonAuthFlag )? CommonAuth.getToken():
            ( iframeFlag && window.parent.getToken )? window.parent.getToken(): null;
    }

    let errorCount = 0;

    const fetchController = ( option.controller )? option.controller: controller;

    const f = function( u ){
        return new Promise(function( resolve, reject ){

            // ダミー用処理
            if ( u === 'dummy') {
                resolve('dummy');
                return;
            }

            if ( windowFlag ) u = cmn.getRestApiUrl( u );

            const init = {
                method: method,
                headers: {
                    Authorization: `Bearer ${token}`
                },
                signal: fetchController.signal
            };

            // Content-Type ※マルチパートの場合は指定しない
            if ( !option.multipart ) {
                init.headers['Content-Type'] = 'application/json';
            }

            // body
            if ( ( method === 'POST' || method === 'PATCH' ) && data !== undefined ) {
                if ( !option.multipart ) {
                    try {
                        init.body = JSON.stringify( data );
                    } catch ( e ) {
                        reject( e );
                    }
                } else {
                    init.body = data;
                }
            }

            fetch( u, init ).then(function( response ){
                if ( errorCount === 0 ) {
                    if( response.ok ) {
                        // 200の場合
                        response.json().then(function( result ){
                            if ( option.message ) {
                                resolve( [ result.data, result.message ] );
                            } else {
                                resolve( result.data );
                            }
                        }).catch(function( error ){
                            cmn.systemErrorAlert();
                        });
                    } else {
                        errorCount++;
                        response.json().then(function( json ){
                            cmn.responseError( response.status, json, fetchController, option ).then(function( result ){
                                reject( result );
                            });
                        }).catch(function( error ){
                            cmn.systemErrorAlert();
                        });
                    }
                }
            }).catch(function( error ){
                if ( error.name !== 'AbortError') {
                    console.error( error );
                    if ( errorCount === 0 ) {
                        reject( error );
                    }
                } else {
                    resolve();
                }
            });
        });
    };
    if ( typeofValue( url ) === 'array') {
        return Promise.all(
            url.map(function( u ){
                return f( u );
            })
        );
    } else if ( typeofValue( url ) === 'string') {
        return f( url );
    }
},
/*
##################################################
    データ読み込み エラー
##################################################
*/
responseError: function( status, responseJson, fetchController, option = {}) {
    return new Promise(function( resolve ){
        switch ( status ) {
            // 呼び出し元に返す
            case 498: // メンテナンス中
            case 499: // バリデーションエラー
                resolve( responseJson );
            break;
            // 権限無しの場合、トップページに戻す
            case 401:
                if ( option.authorityErrMove !== false ) {
                    if ( !iframeFlag ) {
                        if ( fetchController ) fetchController.abort();
                        alert( responseJson.message );
                        location.replace('/' + organization_id + '/workspaces/' + workspace_id + '/ita/');
                    } else {
                        cmn.iframeMessage( responseJson.message );
                    }
                } else {
                    resolve( responseJson );
                }
            break;
            // ワークスペース一覧に飛ばす
            case 403:
                if ( !iframeFlag ) {
                    if ( fetchController ) fetchController.abort();
                    alert( responseJson.message );
                    window.location.href = `/${organization_id}/platform/workspaces`;
                } else {
                    cmn.iframeMessage( responseJson.message );
                }
            break;
            // その他のエラー
            default:
                cmn.systemErrorAlert();
        }
    });
},
/*
##################################################
    システムエラーAleat
##################################################
*/
systemErrorAlert: function() {
    if ( windowFlag ) {
        cmn.gotoErrPage( getMessage.FTE10030 );
    } else {
        console.error( getMessage.FTE10030 );
        throw new Error( getMessage.FTE10030 );
    }
},
/*
##################################################
    編集フラグ
##################################################
*/
editFlag: function( menuInfo ) {
    const flag  = {};
    flag.initFilter = ( menuInfo.initial_filter_flg === '1')? true: false;
    flag.autoFilter = ( menuInfo.auto_filter_flg === '1')? true: false;
    flag.history = ( menuInfo.history_table_flag === '1')? true: false;

    flag.privilege = ( menuInfo.privilege === '1')? true: false;
    flag.insert = ( menuInfo.privilege === '1')? ( menuInfo.row_insert_flag === '1')? true: false: false;
    flag.update = ( menuInfo.privilege === '1')? ( menuInfo.row_update_flag === '1')? true: false: false;
    flag.disuse = ( menuInfo.privilege === '1')? ( menuInfo.row_disuse_flag === '1')? true: false: false;
    flag.reuse = ( menuInfo.privilege === '1')? ( menuInfo.row_reuse_flag === '1')? true: false: false;
    flag.edit = ( menuInfo.privilege === '1')? ( menuInfo.row_insert_flag === '1' && menuInfo.row_update_flag === '1')? true: false: false;

    return flag;
},
/*
##################################################
   0埋め
##################################################
*/
zeroPadding: function( num, digit, zeroSpan = false ){
    let zeroPaddingNumber = '0';
    for ( let i = 1; i < digit; i++ ) {
      zeroPaddingNumber += '0';
    }
    zeroPaddingNumber = ( zeroPaddingNumber + String( num ) ).slice( -digit );
    if ( zeroSpan ) {
        zeroPaddingNumber = zeroPaddingNumber.replace(/^(0+)/, '<span>$1</span>');
    }
    return zeroPaddingNumber;
},
/*
##################################################
   空値チェック
##################################################
*/
cv: function( value, subValue, escape ){
    const type = typeofValue( value );
    if ( type === 'boolean') {
        if ( value === true ) {
            value = 'true';
        } else if ( value === false ) {
            value = 'false';
        } else {
            value = '';
        }
    }
    if ( type === 'undefined' || type === 'null') value = subValue;
    if ( value && escape ) value = cmn.escape( value );

    return value;
},
/*
##################################################
   エスケープ
##################################################
*/
escape: function( value, br, space ) {
    br = ( br === undefined )? false: true;
    space = ( space === undefined )? false: true;
    const entities = [
        ['&', 'amp'],
        ['\"', 'quot'],
        ['\'', 'apos'],
        ['<', 'lt'],
        ['>', 'gt'],
        /*['\\(', '#040'],['\\)', '#041'],['\\[', '#091'],['\\]', '#093']*/
    ];
    const type = typeofValue( value );

    if ( value !== undefined && value !== null && type === 'string') {
        for ( var i = 0; i < entities.length; i++ ) {
            value = value.replace( new RegExp( entities[i][0], 'g'), `&${entities[i][1]};`);
        }
        value = value.replace( new RegExp(/\\/, 'g'), `&#092;`);
        if ( br ) value = value.replace(/\r?\n/g, '<br>');
        if ( space ) value = value.replace(/^\s+|\s+$/g, '');
    } else if ( type !== 'number') {
        value = '';
    }
    return value;
},
/*
##################################################
   JSON文字列変換（区切り文字「, 」）
##################################################
*/
jsonStringifyDelimiterSpace: function(vContent) {
    if (vContent instanceof Object) {
      var sOutput = "";
      if (vContent.constructor === Array) {
        for (var nId = 0; nId < vContent.length; sOutput += this.jsonStringifyDelimiterSpace(vContent[nId]) + ", ", nId++);
          return "[" + sOutput.substring(0, sOutput.length - 2) + "]";
      }
      if (vContent.toString !== Object.prototype.toString) {
        return "\"" + vContent.toString().replace(/"/g, "\\$&") + "\"";
      }
      for (var sProp in vContent) {
        sOutput += "\"" + sProp.replace(/"/g, "\\$&") + "\":" + this.jsonStringifyDelimiterSpace(vContent[sProp]) + ", ";
      }
      return "{" + sOutput.substring(0, sOutput.length - 2) + "}";
   }
   return typeof vContent === "string" ? "\"" + vContent.replace(/"/g, "\\$&") + "\"" : String(vContent);
},
/*
##################################################
   正規表現文字列エスケープ
##################################################
*/
regexpEscape: function( value ) {
    return value.replace(/[.*+\-?^${}()|[\]\\]/g, '\\$&');
},
/*
##################################################
   改行コードをエスケープ
##################################################
*/
nlcEscape: function( value ) {
    if (this.typeof( value ) === 'string') {
        const code = [
            ['\b', '\\b'],
            ['\t', '\\t'],
            ['\n', '\\n'],
            ['\f', '\\f'],
            ['\r', '\\r']
        ];
        for ( var i = 0; i < code.length; i++ ) {
            value = value.replace( new RegExp( code[i][0], 'g'), code[i][1] );
        }
        // value = value.replace(/\\[anrfRtvsSdDwWlLuU0]/g, '\\$&');
        return value;
    } else {
        return value;
    }
},
/*
##################################################
   対象が存在するか
##################################################
*/
exists: function( name ) {
    if ( name.match(/^\./) ) {
        return ( document.getElementsByClassName( name.replace(/^./, '') ) !== null )? true: false;
    } else if ( name.match(/^#/) ) {
        return ( document.getElementById( name.replace(/^#/, '') ) !== null )? true: false;
    } else {
        return ( document.getElementsByTagName( name ) !== null )? true: false;
    }
},
/*
##################################################
   型名
##################################################
*/
typeof: typeofValue,
/*
##################################################
   間引き処理 Throttle
##################################################
*/
throttle: function( func, interval ) {
    let lastTime = Date.now() - interval;
    return function() {
        const now = Date.now();
        if (( lastTime + interval ) < now ) {
            lastTime = now;
            func();
        }
    }
},
/*
##################################################
   間引き処理 Debounce
##################################################
*/
debounce: function( func, interval ) {
    let timer;
    return function() {
        clearTimeout( timer );
        timer = setTimeout( function() {
            func();
        }, interval );
    }
},
/*
##################################################
   選択解除
##################################################
*/
deselection: function() {
    if ( window.getSelection ) {
        window.getSelection().removeAllRanges();
    }
},
/*
##################################################
   日付フォーマット
##################################################
*/
date: function( date, format ) {

    if ( cmn.typeof( date ) === 'string' && date.match(/^[0-9]{4}\/(0[1-9]|1[0-2])\/(0[1-9]|[12][0-9]|3[01])\s/) ) {
        date = date.replace(/\//g,'-');
        date = date.replace(/\s/,'T');
    }

    if ( date ) {
        const d = new Date(date);
        if ( !Number.isNaN( d.getTime()) ) {
            format = format.replace(/yyyy/g, d.getFullYear());
            format = format.replace(/MM/g, ('0' + (d.getMonth() + 1)).slice(-2));
            format = format.replace(/dd/g, ('0' + d.getDate()).slice(-2));
            format = format.replace(/HH/g, ('0' + d.getHours()).slice(-2));
            format = format.replace(/mm/g, ('0' + d.getMinutes()).slice(-2));
            format = format.replace(/ss/g, ('0' + d.getSeconds()).slice(-2));
            format = format.replace(/SSS/g, ('00' + d.getMilliseconds()).slice(-3));
            return format;
        } else {
            return date;
        }
    } else {
        return '';
    }
},
/*
##################################################
   URLパス
##################################################
*/
getPathname: function(){
    return ( new URL( document.location ) ).pathname;
},
/*
/*
##################################################
   URLパラメータ
##################################################
*/
getParams: function() {
    const searchParams = ( new URL( document.location ) ).searchParams.entries(),
          params = {};
    for ( const [ key, val ] of searchParams ) {
        params[ key ] = val;
    }
    return params;
},
/*
##################################################
   クリップボード
##################################################
*/
clipboard: {
    set: function( text ) {
        if ( navigator && navigator.clipboard ) {
            return navigator.clipboard.writeText( text );
        }
    }
},
/*
##################################################
   ファイル名のチェック
##################################################
*/
fileNameCheck: function( fileName ) {
    // \ / : * ? " > < |
    if ( fileName && cmn.typeof( fileName ) === 'string' ) {
        return fileName.replace(/\\|\/|:|\*|\?|\"|>|<\|/g,'_');
    } else {
        return '';
    }
},
/*
##################################################
   配列コピー
##################################################
*/
arrayCopy: function( array ) {
    if ( fn.typeof( structuredClone ) === 'function') {
        return structuredClone( array );
    } else {
        return JSON.parse(JSON.stringify( array ));
    }
},
/*
##################################################
   ファイルの取得
   option.fileName: true ファイル名も返す
##################################################
*/
getFile: function( endPoint, method = 'GET', data, option = {} ) {
    return new Promise( async function( resolve, reject ){
        try {
            const getFileController = new AbortController();
            const title = ( option.title )? option.title: getMessage.FTE00180;
            let progressModal = cmn.progressModal( title, { close: true });

            // 閉じたときに処理を中断する
            progressModal.btnFn = {
                headerClose: function(){
                    $( window ).trigger('getFile_close');
                    getFileController.abort();
                    progressModal.close();
                    progressModal = null;
                    reject('break');
                }
            };
            const token = ( cmmonAuthFlag )? CommonAuth.getToken():
                ( iframeFlag && window.parent.getToken )? window.parent.getToken(): null;

            const init = {
                method: method,
                headers: {
                    Authorization: `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                signal: getFileController.signal
            };

            // body
            if ( ( method === 'POST' || method === 'PATCH' ) && data !== undefined ) {
                try {
                    init.body = JSON.stringify( data );
                } catch ( e ) {
                    reject( e );
                }
            }


            // データ読込開始
            if ( windowFlag ) endPoint = cmn.getRestApiUrl( endPoint );
            const response = await fetch( endPoint, init );

            if ( response.ok ) {
                // 成功
                const reader = response.body.getReader();
                const contentLength = response.headers.get('Content-Length');

                // ファイル名
                const disposition = response.headers.get('Content-Disposition');
                let fileName = 'noname';
                if ( disposition && disposition.indexOf('attachment') !== -1 ) {
                    const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
                    const matches = filenameRegex.exec( disposition );
                    if ( matches != null && matches[1] ) {
                        fileName = decodeURIComponent(matches[1].replace(/['"]/g, ''));
                    }
                }

                // オリジンプライベートファイルシステム（OPFS）が使えるかで処理を分岐する
                let fileData;
                if ('storage' in navigator === true ) {
                    // オリジンプライベートファイルシステム
                    const root = await navigator.storage.getDirectory();
                    const dirName = ( option.type === 'duplicat')? 'duplicat_temp': 'download_temp';
                    const temp = await root.getDirectoryHandle( dirName, { create: true });

                    let fileHandle;
                    if ( 'uuid' in option && 'columnNameRest' in option ) {
                        const uuidDir = await temp.getDirectoryHandle( option.uuid, { create: true });
                        const nameDir = await uuidDir.getDirectoryHandle( option.columnNameRest, { create: true });
                        fileHandle = await nameDir.getFileHandle( fileName, { create: true });
                    } else {
                        fileHandle = await temp.getFileHandle( fileName, { create: true });
                    }
                    const wstream = await fileHandle.createWritable();
                    const writer = wstream.getWriter();

                    // キャンセルした場合
                    $( window ).one('getFile_close', async function(){
                        await writer.close();
                        cmn.removeDownloadTemp( dirName );
                    });

                    // データ読込
                    let receivedLength = 0;
                    while( true ) {
                        const { done, value } = await reader.read();
                        if ( done === true ) {
                            await writer.close();
                            $( window ).off('getFile_close');
                            break;
                        } else {
                            await writer.write( value );
                            receivedLength += value.length;
                            progressModal.progress( receivedLength, contentLength );
                        }
                    }

                    // ファイル取得
                    fileData = await fileHandle.getFile();
                } else {
                    // データ読込
                    const chunks = [];
                    let receivedLength = 0;
                    while( true ) {
                        const { done, value } = await reader.read();
                        if ( done === true ) {
                            break;
                        } else {
                            chunks.push( value );
                            receivedLength += value.length;
                            progressModal.progress( receivedLength, contentLength );
                        }
                    }
                    // ファイルに変換
                    const blob = new Blob( chunks );
                    fileData = new File([blob], fileName, { type: blob.type });
                }

                // バーのtransition-duration: .2s;分ずらす
                setTimeout(function(){
                    if ( progressModal !== null ) {
                        progressModal.close();
                        progressModal = null;
                        if ( option.fileName ) {
                            resolve({
                                file: fileData,
                                fileName: fileName
                            });
                        } else {
                            resolve( fileData );
                        }
                    }
                }, 200 );
            } else {
                // 失敗
                response.json().then(function( json ){
                    cmn.responseError( response.status, json ).then(function( result ){
                        progressModal.close();
                        progressModal = null;
                        reject( result );
                    });
                }).catch(function( error ){
                    cmn.systemErrorAlert();
                });
            }
        } catch ( e ) {
            if ( e.message === 'network error') {
                reject('break');
            } else {
                reject( e );
            }
        }
    });
},
/*
##################################################
   OPFSに保存したファイルを削除
##################################################
*/
removeDownloadTemp: async function( target = 'download_temp') {
    if ('storage' in navigator === true ) {
        try {
            const root = await navigator.storage.getDirectory();
            const temp = await root.getDirectoryHandle( target, { create: true });
            await temp.remove({ recursive: true });
        } catch ( error ) {
            console.error( error )
        }
    }
},
/*
##################################################
   データ登録（進捗表示）
##################################################
*/
xhr: function( url, formData ) {
    return new Promise(function( resolve, reject ){
        let progressModal = cmn.progressModal( getMessage.FTE00184, { close: true });

        // 閉じたときに処理を中断する
        progressModal.btnFn = {
            headerClose: function(){
                ajax.abort();
                progressModal.close();
                progressModal = null;
                reject('break');
            }
        };

        const token = ( cmmonAuthFlag )? CommonAuth.getToken():
            ( iframeFlag && window.parent.getToken )? window.parent.getToken(): null;

        if ( windowFlag ) url = cmn.getRestApiUrl( url );

        const progress = function( e ) {
            progressModal.progress( e.loaded, e.total );
        };

        const ajax = $.ajax({
            url: url,
            method: 'post',
            dataType: 'json',
            data: formData,
            processData: false,
            contentType: false,
            headers: {
                Authorization: 'Bearer ' + token,
            },
            async: true,
            xhr: function() {
                const xhr = $.ajaxSettings.xhr();
                xhr.upload.addEventListener('progress', progress );
                return xhr;
            }
        }).done(function( result, status, jqXHR ){
            if ( status === 'success') {
                progressModal.close();
                progressModal = null;
                resolve( result.data, progressModal );
            } else {
                reject( null );
            }
        }).fail(function( jqXHR ){
            if ( jqXHR.statusText !== 'abort') {
                setTimeout(function(){
                    cmn.responseError( jqXHR.status, jqXHR.responseJSON ).then(function( result ){
                        progressModal.close();
                        progressModal = null;
                        reject( result );
                    });
                }, 200 );
            }
        });
    });
},
/*
##################################################
   ダウンロード
##################################################
*/
download: async function( type, data, fileName = 'noname') {
    let url;
    try {
        // URL形式に変換
        switch ( type ) {
            // ファイル
            case 'file': {
                // ファイルタイプが空の場合は application/octet-stream を指定する
                if ( data.type === '') {
                    data = new Blob([ data ], {
                        type: 'application/octet-stream',
                    });
                }
                url = URL.createObjectURL( data );
            } break;

            // エクセル
            case 'excel': {
                // BASE64 > Binary > Unicode変換
                const binary = window.atob( data ),
                    decode = new Uint8Array( Array.prototype.map.call( binary, function( c ){ return c.charCodeAt(); }));

                const blob = new Blob([ decode ], {
                    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                });
                fileName += '.xlsx';
                url = URL.createObjectURL( blob );
            } break;

            // テキスト
            case 'text': {
                const blob = new Blob([ data ], {'type': 'text/plain'});
                fileName += '.txt';
                url = URL.createObjectURL( blob );
            } break;

            // JSON
            case 'json': {
                const blob = new Blob([ JSON.stringify( data, null, '\t') ], {'type': 'application/json'});
                fileName += '.json';
                url = URL.createObjectURL( blob );
            } break;

            // BASE64
            case 'base64': {
                url = 'data:;base64,' + data;
            } break;

            // Exceljs
            case 'exceljs': {
                const blob = new Blob([ data ], {
                    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                });
                fileName += '.xlsx';
                url = URL.createObjectURL( blob );
            } break;

            // バイナリ
            case 'binary':
                const blob = new Blob([ data ], {
                    type: 'application/octet-stream',
                });
                url = URL.createObjectURL( blob );
        }
    } catch ( e ) {
        window.console.error( e );
    }

    const a = document.createElement('a');

    fileName = cmn.fileNameCheck( fileName );

    a.href = url;
    a.download = fileName;
    a.click();

    if ( type !== 'base64') URL.revokeObjectURL( url );
    if ( type === 'file') cmn.removeDownloadTemp();
},
/*
##################################################
   ファイルを選択
##################################################
*/
fileSelect: function( type = 'base64', limitFileSize, accept ){
    return new Promise( function( resolve, reject ) {
        const file = document.createElement('input');
        let cancelFlag = true;

        file.type = 'file';
        if ( accept !== undefined ) file.accept = accept;

        file.addEventListener('change', function(){
            const file = this.files[0],
                  reader = new FileReader();

            cancelFlag = false;

            if ( limitFileSize && file.size > limitFileSize ) {
                reject( getMessage.FTE10060( file.size, limitFileSize ) );
                return false;
            }

            if ( type === 'base64') {
                reader.readAsDataURL( file );

                reader.onload = function(){
                    let resultText = reader.result;
                    if ( resultText !== '' ) {
                        if ( resultText === 'data:') {
                            resultText = '';
                        } else {
                            resultText = resultText.split(';base64,')[1];
                        }
                    }
                    resolve({
                        base64: resultText,
                        name: file.name,
                        size: file.size
                    });
                };

                reader.onerror = function(){
                    reject( reader.error );
                };
            } else if ( type === 'file') {
                resolve( file );
            } else if ( type === 'json') {
                reader.readAsText( file );

                reader.onload = function(){
                    try {
                        const json = JSON.parse( reader.result );
                        resolve({
                            json: json,
                            name: file.name,
                            size: file.size
                        });
                    } catch( e ) {
                        reject( getMessage.FTE10021 );
                    }
                };

                reader.onerror = function(){
                    reject( reader.error );
                };
            }
        });

        file.click();

        // bodyフォーカスでダイアログを閉じたか判定
        document.body.onfocus = function(){
            setTimeout( function(){
                if ( cancelFlag ) reject('cancel');
                document.body.onfocus = null;
            }, 1000 );
        };
    });
},
/*
##################################################
   Disabled timer
##################################################
*/
disabledTimer: function( $element, flag, time ) {
    if ( time !== 0 ) {
        setTimeout( function(){
            $element.prop('disabled', flag );
        }, time );
    } else {
        $element.prop('disabled', flag );
    }
},
/*
##################################################
   Web storage
##################################################
*/
storage: {
    check: function( type ) {
        const storage = ( type === 'local')? localStorage:
                        ( type === 'session')? sessionStorage:
                        undefined;
        try {
            const storage = window[type],
            x = '__storage_test__';
            storage.setItem( x, x );
            storage.removeItem( x );
            return true;
        }
        catch( e ) {
            return e instanceof DOMException && (
            // everything except Firefox
            e.code === 22 ||
            // Firefox
            e.code === 1014 ||
            // test name field too, because code might not be present
            // everything except Firefox
            e.name === 'QuotaExceededError' ||
            // Firefox
            e.name === 'NS_ERROR_DOM_QUOTA_REACHED') &&
            // acknowledge QuotaExceededError only if there's something already stored
            storage.length !== 0;
        }
    },
    'set': function( key, value, type, keyFlag = true ) {
        if ( type === undefined ) type = 'local';
        if ( keyFlag ) key = cmn.createStorageKey( key );
        const storage = ( type === 'local')? localStorage: ( type === 'session')? sessionStorage: undefined;
        if ( storage !== undefined ) {
            try {
                storage.setItem( key, JSON.stringify( value ) );
            } catch( e ) {
                window.console.error('Web storage error: setItem( ' + key + ' ) / ' + e.message );
                storage.removeItem( key );
            }
        } else {
            return false;
        }
    },
    'get': function( key, type, keyFlag = true ) {
        if ( type === undefined ) type = 'local';
        if ( keyFlag ) key = cmn.createStorageKey( key );
        const storage = ( type === 'local')? localStorage: ( type === 'session')? sessionStorage: undefined;
        if ( storage !== undefined ) {
            if ( storage.getItem( key ) !== null  ) {
                return JSON.parse( storage.getItem( key ) );
            } else {
                return false;
            }
        } else {
            return false;
        }
    },
    'remove': function( key, type, storageKeyFlag = true ) {
        if ( type === undefined ) type = 'local';
        if ( storageKeyFlag === true ) key = cmn.createStorageKey( key );
        const storage = ( type === 'local')? localStorage: ( type === 'session')? sessionStorage: undefined;
        if ( storage !== undefined ) {
            storage.removeItem( key );
        } else {
            return false;
        }
    },
    getKeys: function( type ) {
        if ( type === undefined ) type = 'local';
        const storage = ( type === 'local')? localStorage: ( type === 'session')? sessionStorage: undefined,
              l = storage.length,
              keys = [];
        for ( let i = 0; i < l; i++ ) {
            keys.push( storage.key(i) );
        }
        return keys;
    }
},
createStorageKey: function( key ) {
    key = `ita_ui_${organization_id}_${workspace_id}_${key}`;
    return key;
},
/*
##################################################
   Alert, Confirm
##################################################
*/
alert: function( title, elements, type = 'alert', buttons = { ok: { text: getMessage.FTE10043, action: 'normal'}}, width = '640px') {
    return new Promise(function( resolve ){
        const funcs = {};

        funcs.ok = function(){
            dialog.close();
            dialog = null;
            resolve( true );
        };
        if ( type !== 'alert') {
            funcs.cancel = function(){
                dialog.close();
                dialog = null;
                resolve( false );
            };
        }
        const config = {
            mode: 'modeless',
            position: 'center',
            header: {
                title: title,
                close: false,
                move: false
            },
            width: width,
            footer: {
                button: buttons
            }
        };
        let dialog = new Dialog( config, funcs );
        dialog.open(`<div class="alertMessage ${type}Container">${elements}</div>`);

        setTimeout(function(){
            if ( dialog ) {
                dialog.buttonPositiveDisabled( false );
            }
        }, 500 )
    });
},
iconConfirm: function( icon, title, elements, okText = getMessage.FTE10058, cancelText = getMessage.FTE10026 ) {
    elements = `
    <div class="alertMessageIconBlock">
        <div class="alertMessageIcon">${cmn.html.icon( icon )}</div>
        <div class="alertMessageBody">${cmn.escape( elements, true )}</div>
    </div>`;
    return cmn.alert( title, elements , 'confirm', {
        ok: { text: okText, action: 'default', width: '120px', className: 'dialogPositive'},
        cancel: { text: cancelText, action: 'negative', width: '120px'}
    });
},
/*
##################################################
   Calendar
##################################################
*/
calendar: function( setDate, currentDate, startDate, endDate ){
    const weekText = getMessage.FTE10036,
          weekClass = ['sun','mon','tue','wed','thu','fri','sat'];

    if ( startDate ) startDate = fn.date( startDate, 'yyyy/MM/dd');
    if ( endDate ) endDate = fn.date( endDate, 'yyyy/MM/dd');

    // 今月
    const date = ( setDate )? new Date( setDate ): new Date(),
          year = date.getFullYear(),
          month = date.getMonth() + 1,
          end = new Date( year, month, 0 ).getDate();

    // 先月
    const lastMonthEndDate = new Date( year, month - 1 , 0 ),
          lastMonthYear = lastMonthEndDate.getFullYear(),
          lastMonth = lastMonthEndDate.getMonth() + 1,
          lastMonthEndDay = lastMonthEndDate.getDay(),
          lastMonthChangeNum = 7 + lastMonthEndDay,
          lastMonthStart = new Date( year, month - 1 , -lastMonthChangeNum ).getDate();

    // 来月
    const nextMonthDate = new Date( year, month + 1, 0 ),
          nextMonthYear = nextMonthDate.getFullYear(),
          nextMonth = nextMonthDate.getMonth() + 1;

    if ( currentDate ) currentDate = fn.date( currentDate, 'yyyy/MM/dd');

    // HTML
    const thead = function() {
        const th = [],
              l = weekText.length;
        for ( let i = 0; i < l; i++ ) {
            th.push(`<th class="calTh ${weekClass[i]}">${weekText[i]}</th>`)
        }
        return `<tr class="calRow">${th.join('')}</tr>`;
    };
    const cell = function( num, className, dataDate ) {
        return `<td class="${className}"><span class="calTdInner"><button class="calButton" data-date="${dataDate}">${num}</butto></span></td>`;
    };
    const disabledCell = function( num, className ) {
        return `<td class="${className} disabled"><span class="calTdInner"><button class="calButton calButtonDisabled" disabled>${num}</button></span></td>`;
    };

    const rowHtml = [];
    let count = 0;
    for ( let w = 0; w < 7; w++ ) {
        const cellHtml = [];
        for ( let d = 0; d < 7; d++ ) {
            let num, dataDate, className = 'calTd ' + weekClass[d];
            if ( lastMonthChangeNum >= count ) {
                // 先月
                num = lastMonthStart + count++;
                className += ' lastMonth';
                dataDate = `${lastMonthYear}/${cmn.zeroPadding( lastMonth, 2 )}/`;
            } else if ( count - lastMonthChangeNum > end ) {
                // 来月
                className += ' nextMonth';
                num = count++ - end - lastMonthChangeNum;
                dataDate = `${nextMonthYear}/${cmn.zeroPadding( nextMonth, 2 )}/`;
            } else {
                // 今月
                num = count++ - lastMonthChangeNum;
                dataDate = `${year}/${cmn.zeroPadding( month, 2 )}/`;
            }
            const cellDate = dataDate + cmn.zeroPadding( num, 2 );

            if ( currentDate ) {
                if ( currentDate === cellDate ) className += ' currentCell';
                if ( ( startDate === cellDate ) || ( endDate && currentDate === cellDate ) ) className += ' startCell';
                if ( ( endDate === cellDate ) || ( startDate && currentDate === cellDate ) ) className += ' endCell';
                if ( ( startDate && startDate < cellDate && currentDate > cellDate )
                    || ( endDate && endDate > cellDate && currentDate < cellDate )  ) className += ' periodCell';
            }

            if ( ( startDate && startDate > cellDate ) || ( endDate && endDate < cellDate ) ) {
                cellHtml.push( disabledCell( num, className ) );
            } else {
                cellHtml.push( cell( num, className, cellDate ) );
            }
        }
        rowHtml.push(`<tr class="calRow">${cellHtml.join('')}</tr>`);
    }

    return `<table class="calTable">`
        + `<thead class="calThead">`
            + thead()
        + `</thead>`
        + `<tbody class="calTbody">`
            + rowHtml.join('')
        + `</tbody>`
    + `</table>`;
},
/*
##################################################
   Date picker
##################################################
*/
datePicker: function( timeFlag, className, date, start, end ) {
    const monthText = getMessage.FTE10037;

    let initDate;
    if ( date && !isNaN( new Date( date ) ) ) {
        initDate = new Date( date )
    } else {
        initDate = new Date();
    }

    let monthCount = 0;

    let inputDate;

    let year = initDate.getFullYear(),
        month = initDate.getMonth(),
        day = initDate.getDate();

    let hour, min , sec;

    if ( date ) {
        hour = initDate.getHours(),
        min = initDate.getMinutes(),
        sec = initDate.getSeconds();
    } else if ( className === 'datePickerToDateText') {
        hour = 23;
        min = sec = 59;
    } else {
        hour = min = sec = 0;
    }

    let placeholder = 'yyyy/MM/dd';
    if ( timeFlag ) {
        if ( timeFlag === 'hm') {
            placeholder += ' HH:mm';
        } else if  ( timeFlag === 'h') {
            placeholder += ' HH';
        } else {
            placeholder += ' HH:mm:ss';
        }
    }

    if ( className === 'datePickerFromDateText' && !end ) {
        end = date;
        placeholder = 'From : ' + placeholder;
    }
    if ( className === 'datePickerToDateText' && !start ) {
        start = date;
        placeholder = 'To : ' + placeholder;
    }

    const $datePicker = $('<div/>', {
        'class': 'datePickerBlock'
    }).html(`
    <div class="datePickerDate">
        <input type="text" class="datePickerDateInput ${className}" tabindex="-1" placeholder="${placeholder}" readonly>
        <input type="hidden" class="datePickerDateHidden datePickerDateStart">
        <input type="hidden" class="datePickerDateHidden datePickerDateEnd">
    </div>
    <div class="datePickerSelectDate">
        <div class="datePickerYear">
            <div class="datePickerYearPrev"><button class="datePickerButton" data-type="prevYear"><span class="icon icon-prev"></span></button></div>
            <div class="datePickerYearText">${year}</div>
            <div class="datePickerYearNext"><button class="datePickerButton" data-type="nextYear"><span class="icon icon-next"></span></button></div>
        </div>
        <div class="datePickerMonth">
            <div class="datePickerMonthPrev"><button class="datePickerButton" data-type="prevMonth"><span class="icon icon-prev"></span></button></div>
            <div class="datePickerMonthText">${monthText[month]}</div>
            <div class="datePickerMonthNext"><button class="datePickerButton" data-type="nextMonth"><span class="icon icon-next"></span></button></div>
        </div>
    </div>
    <div class="datePickerCalendar">
        ${cmn.calendar( initDate, date, start, end )}
    </div>`);

    const setInputDate = function( changeFlag = true ) {
        inputDate = `${year}/${fn.zeroPadding( month + 1, 2 )}/${fn.zeroPadding( day, 2 )}`;
        if ( timeFlag ) {
            let timeValue;
            if ( timeFlag === 'hm') {
                timeValue = `${inputDate} ${fn.zeroPadding( hour, 2 )}:${fn.zeroPadding( min, 2 )}`;
            } else if  ( timeFlag === 'h') {
                timeValue = `${inputDate} ${fn.zeroPadding( hour, 2 )}`;
            } else {
                timeValue = `${inputDate} ${fn.zeroPadding( hour, 2 )}:${fn.zeroPadding( min, 2 )}:${fn.zeroPadding( sec, 2 )}`;
            }
            $date.val( timeValue );
        } else {
            $date.val( inputDate );
        }
        if ( changeFlag ) $date.change();
        $date.trigger('checkDate');
    };

    const $date = $datePicker.find('.datePickerDateInput'),
          $year = $datePicker.find('.datePickerYearText'),
          $month = $datePicker.find('.datePickerMonthText'),
          $cal = $datePicker.find('.datePickerCalendar');

    if ( date ) setInputDate( false );

    $datePicker.find('.datePickerButton').on('click', function(){
        const $button = $( this ),
              type = $button.attr('data-type');

        switch ( type ) {
            case 'prevYear': monthCount -= 12; break;
            case 'nextYear': monthCount += 12; break;
            case 'prevMonth': monthCount -= 1; break;
            case 'nextMonth': monthCount += 1; break;
        }
        const newData = new Date( initDate.getFullYear(), initDate.getMonth() + monthCount, 1 );

        year = newData.getFullYear();
        month = newData.getMonth();

        $year.text( year );
        $month.text( monthText[month] );

        $cal.html( cmn.calendar( newData, inputDate, start, end ) );
    });

    $datePicker.on('click', '.calButton', function(){
        const $button = $( this ),
              ckickDate = $button.attr('data-date').split('/');

        year = ckickDate[0];
        month = Number( ckickDate[1] ) - 1;
        day = ckickDate[2];

        if ( $button.closest('.nextMonth').length ) {
            monthCount += 1;
        }

        if ( $button.closest('.lastMonth').length ) {
            monthCount -= 1;
        }

        $year.text( year );
        $month.text( monthText[month] );

        setInputDate();
        $cal.html( cmn.calendar( inputDate, inputDate, start, end ) );
    });

    // FromTo用:片方のカレンダーの設定が変わった場合
    $datePicker.find('.datePickerDateHidden').on('change', function(){
        const $hidden = $( this ),
              value = $hidden.val();

        if ( $hidden.is('.datePickerDateStart') ) {
            start = value;
        } else {
            end = value;
        }

        const setDate = `${year}/${month+1}/1`;

        $cal.html( cmn.calendar( setDate, inputDate, start, end ) );
    });

    // 時間
    if ( timeFlag ) {
        const datePickerTime = [`<div class="datePickerHour">${cmn.html.inputFader('datePickerHourInput', hour, null, { min: 0, max: 23 }, { after: getMessage.FTE10089 } )}</div>`];
        if ( timeFlag === 'true' || timeFlag === true || timeFlag === 'hms' || timeFlag === 'hm') {
            datePickerTime.push(`<div class="datePickerMin">${cmn.html.inputFader('datePickerMinInput', min, null, { min: 0, max: 59 }, { after: getMessage.FTE10090 } )}</div>`);
        }
        if ( timeFlag === 'true' || timeFlag === true || timeFlag === 'hms') {
            datePickerTime.push(`<div class="datePickerSec">${cmn.html.inputFader('datePickerSecInput', sec, null, { min: 0, max: 59 }, { after: getMessage.FTE10091 } )}</div>`);
        }

        $datePicker.append(`
        <div class="datePickerTime">
            ${datePickerTime.join('')}
        </div>`);

        $datePicker.find('.inputFaderWrap').each(function(){
            cmn.faderEvent( $( this ) );
        });

        $datePicker.find('.inputFader').on('change', function(){
            const $input = $( this ),
                  value = $input.val();
            if ( $input.is('.datePickerHourInput') ) {
                hour = value;
            } else if ( $input.is('.datePickerMinInput') ) {
                min = value;
            } else {
                sec = value;
            }
            setInputDate( false );
        });
    }

    $datePicker.append(`<div class="datePickerMenu">
        <ul class="datePickerMenuList">
            <li class="datePickerMenuItem">${fn.html.button( getMessage.FTE10039, ['datePickerMenuButton', 'itaButton'], { type: 'current', action: 'normal', style: 'width:100%'})}</li>
            <li class="datePickerMenuItem">${fn.html.button( getMessage.FTE10040, ['datePickerMenuButton', 'itaButton'], { type: 'clear', action: 'normal', style: 'width:100%'})}</li>
        </ul>
    </div>`);

    const nowCalender = function( clearFlag ) {
        const now = new Date();

        const $h = $datePicker.find('.datePickerHourInput'),
              $m = $datePicker.find('.datePickerMinInput'),
              $s = $datePicker.find('.datePickerSecInput');

        year = now.getFullYear();
        month = now.getMonth();
        day =  now.getDate();

        $year.text( year );
        $month.text( monthText[month] );

        if ( clearFlag ) {
            inputDate = null;
            $date.val('').change();
            $cal.html( cmn.calendar( now ) );

            if ( timeFlag ) {
                if ( className === 'datePickerToDateText') {
                    hour = 23;
                    min = 59;
                    sec = 59;
                } else {
                    hour = min = sec = 0;
                }
            }
        } else {
            if ( timeFlag ) {
                hour = now.getHours();
                min = now.getMinutes();
                sec = now.getSeconds();
            }
            setInputDate();
            $cal.html( cmn.calendar( inputDate, inputDate, start, end ) );
        }

        if ( timeFlag ) {
            $h.val( hour ).trigger('input');
            $m.val( min ).trigger('input');
            $s.val( sec ).trigger('input');
        }
    };

    $datePicker.find('.datePickerMenuButton').on('click', function(){
        const $button = $( this ),
              type = $button.attr('data-type');
        switch ( type ) {
            case 'current':
                nowCalender( false );
            break;
            case 'clear':
                nowCalender( true );
            break;
        }
    });

    return $datePicker;
},
/*
##################################################
   Check date
##################################################
*/
checkDate: function( date ) {
    return !Number.isNaN( new Date( date ).getTime() );
},
/*
##################################################
   Date picker dialog
##################################################
*/
datePickerDialog: function( type, timeFlag, title, date, required = false ){
    return new Promise(function( resolve ){
        const funcs = {
            ok: function() {
                const result = {};

                if ( type === 'fromTo') {
                    result.from = $dataPicker.find('.datePickerFromDateText').val();
                    result.to = $dataPicker.find('.datePickerToDateText').val();
                } else {
                    result.date = $dataPicker.find('.datePickerDateText').val();
                }

                dialog.close().then(function(){
                    resolve( result );
                    dialog = null;
                });
            },
            cancel: function() {
                dialog.close().then(function(){
                    resolve('cancel');
                    dialog = null;
                });
            }
        };

        const buttons = {
            ok: { text: getMessage.FTE10038, action: 'default', style: 'width:160px;'},
            cancel: { text: getMessage.FTE10026, action: 'normal'}
        };

        if ( required === true ) {
            buttons.ok.className = 'dialogPositive';
        }

        const config = {
            mode: 'modeless',
            position: 'center',
            width: 'auto',
            header: {
                title: title,
                close: false,
                move: false
            },
            footer: {
                button: buttons
            }
        };

        let dialog = new Dialog( config, funcs );

        // Data picker
        const $dataPicker = $('<div/>', {
            'class': 'datePickerContainer'
        });

        if ( type === 'fromTo') {
            $dataPicker.addClass('datePickerFromToContainer').html(`<div class="datePickerFrom"></div>`
            + `<div class="datePickerTo"></div>`);

            if ( !cmn.checkDate( date.from ) ) date.from = '';
            if ( !cmn.checkDate( date.to ) ) date.to = '';

            $dataPicker.find('.datePickerFrom').html( cmn.datePicker( timeFlag, 'datePickerFromDateText', date.from, null, date.to ) );
            $dataPicker.find('.datePickerTo').html( cmn.datePicker( timeFlag, 'datePickerToDateText', date.to, date.from, null ) );

            // FromTo相互で日付の入力をチェックする
            $dataPicker.find('.datePickerFromDateText').on('change', function(){
                const val = $( this ).val();
                $dataPicker.find('.datePickerTo').find('.datePickerDateStart').val( val ).change();
            });
            $dataPicker.find('.datePickerToDateText').on('change', function(){
                const val = $( this ).val();
                $dataPicker.find('.datePickerFrom').find('.datePickerDateEnd').val( val ).change();
            });

        } else {
            if ( !cmn.checkDate( date ) ) date = '';
            $dataPicker.html( cmn.datePicker( timeFlag, 'datePickerDateText', date ) );
        }

        dialog.open( $dataPicker );

        // 必須の場合は値をチェックする
        if ( required === true ) {
            if ( type === 'fromTo') {
                const
                $from = $dataPicker.find('.datePickerFromDateText'),
                $to = $dataPicker.find('.datePickerToDateText');
                $from.add( $to ).on('checkDate', function(){
                    const from = $from.val(), to = $to.val();
                    dialog.buttonPositiveDisabled( !( from !== '' && to !== '' && from < to ) );
                });
            }
        }
    });
},
/*
##################################################
   Date picker Event
##################################################
*/
setDatePickerEvent: function( $target, title ) {
    const $container = $target.closest('.inputDateContainer'),
          $button = $container.find('.inputDateCalendarButton'),
          timeFlag = $button.attr('data-timeflag');

    $button.on('click', function(){
        const value = $target.val();
        fn.datePickerDialog('date', timeFlag, title, value ).then(function( result ){
            if ( result !== 'cancel') {
                $target.val( result.date ).change().focus().trigger('input');
            }
        });
    });

},
/*
##################################################
   Input fader event
##################################################
*/
faderEvent: function( $item ) {
    const $window = $( window ),
          $fader = $item.find('.inputFaderRange'),
          $input = $item.find('.inputFader'),
          $knob = $item.find('.inputFaderRangeKnob'),
          $lower = $fader.find('.inputFaderRangeLower'),
          $tooltip = $fader.find('.inputFaderRangeTooltip');

    let   width = $fader.width(),
          val = $input.val(),
          min = Number( $input.attr('data-min') ),
          max = Number( $input.attr('data-max') ),
          inputRange = max - min,
          ratio, positionX;

    // 位置をセット
    const setPosition = function(){
        const p =  Math.round( ratio * 100 ) + '%';
        $knob.css('left', p );
        $lower.css('width', p );
    };
    // 割合から位置と値をセット
    const ratioVal = function(){
      if ( ratio <= 0 ) ratio = 0;
      if ( ratio >= 1 ) ratio = 1;
      val = Math.round( inputRange * ratio ) + min;
      $input.val( val ).change();

      setPosition();
    };
    // 値から位置をセット
    const valPosition = function(){
      if ( val === '') val = min;
      if ( val < min ) val = min;
      if ( val > max ) val = max;
      ratio = ( val - min ) / inputRange;
      if ( Number.isNaN( ratio ) ) ratio = 0;
      positionX = Math.round( width * ratio );

      setPosition();
    };
    valPosition();

    $fader.on({
      'mousedown': function( mde ){
        if ( mde.button === 0 ) {
          getSelection().removeAllRanges();

          $fader.addClass('active');
          const clickX = mde.pageX - $fader.offset().left;

          width = $fader.width();
          ratio = clickX / width;
          positionX = Math.round( width * ratio );

          ratioVal();

          $window.on({
            'mouseup.faderKnob': function(){
              $fader.removeClass('active');
              $window.off('mouseup.faderKnob mousemove.faderKnob');
              valPosition();
            },
            'mousemove.faderKnob': function( mme ){
              const moveX = mme.pageX - mde.pageX;
              ratio = ( positionX + moveX ) / width;
              ratioVal();
            }
          });
        }
      },
      // ツールチップ
      'mouseenter': function(){
        const left =  $fader.offset().left,
              top = $fader.offset().top;
        $tooltip.show();
        width = $fader.width();
        $window.on({
          'mousemove.faderTooltip': function( mme ){
            const tRatio = ( mme.pageX - left ) / width;
            let   tVal = Math.round( inputRange * tRatio ) + min;
            if ( tVal < min ) tVal = min;
            if ( tVal > max ) tVal = max ;
            $tooltip.text( tVal );
            $tooltip.css({
              'left': mme.pageX,
              'top': top
            });
          }
        });
      },
      'mouseleave': function(){
        $tooltip.hide();
        $window.off('mousemove.faderTooltip');
      }
    });

    $input.on('change', function(){
        val = $input.val();
        width = $fader.width();
        if ( val !== '') {
          if ( val < min ) {
            val = min;
            $input.val( min );
          }
          if ( val > max ) {
            val = max;
            $input.val( max );
          }
        } else {
          val = '';
        }
    });

    // 最大値が変わった場合ノブの位置を更新する
    $input.on('maxChange', function(){
        max = Number( $input.attr('data-max') );
        inputRange = max - min;
        valPosition();
    });

    $input.on('input', function(){
        val = $input.val();
        valPosition();
    });
},
/*
##################################################
   HTML
##################################################
*/
html: {
    icon: function( type, className ) {
        className = classNameCheck( className, `icon icon-${type}`);
        return `<span class="${className.join(' ')}"></span>`;
    },
    button: function( element, className, attrs = {}, option = {}) {
        const attr = bindAttrs( attrs );
        className = classNameCheck( className, 'button');

        const html = [ element ];
        if ( option.toggle ) {
            className.push('toggleButton');
            attr.push(`data-toggle="${option.toggle.init}"`);
            html.push(`<span class="toggleButtonSwitch">`
                + `<span class="toggleButtonSwitchOn">${option.toggle.on}</span>`
                + `<span class="toggleButtonSwitchOff">${option.toggle.off}</span>`
            + `</span>`)
        }
        if ( option.minWidth ) {
            html.push(`<span class="buttonMinWidth" style="width:${option.minWidth}"></span>`);
        }
        if ( option.width ) {
            attr.push(`style="width:${option.width}"`)
        }

        attr.push(`class="${className.join(' ')}"`);
        return `<button ${attr.join(' ')}><span class="inner">${html.join('')}</span></button>`;
    },
    iconButton: function( icon, element, className, attrs = {}, option = {}) {
        const iconClass = ( element === '')? ' iconOnly': '';
        const html = `${cmn.html.icon( icon, `iconButtonIcon${iconClass}`)}<span class="iconButtonBody">${element}</span>`;
        className = classNameCheck( className, 'iconButton');
        return cmn.html.button( html, className, attrs, option );
    },
    inputHidden: function( className, value, name, attrs = {}) {
        const attr = inputCommon( value, name, attrs );
        attr.push(`class="${classNameCheck( className, 'inputHidden input').join(' ')}"`);

        return `<input type="hidden" ${attr.join(' ')}>`;
    },
    span: function( className, value, name, attrs = {}) {
        const attr = inputCommon( null, name, attrs );
        attr.push(`class="${classNameCheck( className, 'inputSpan').join(' ')}"`);

        return `<span ${attr.join(' ')}>${value}</span>`;
    },
    inputText: function( className, value, name, attrs = {}, option = {}) {
        const attr = inputCommon( value, name, attrs );

        className = classNameCheck( className, 'inputText input');
        if ( option.widthAdjustment ) className.push('inputTextWidthAdjustment')
        attr.push(`class="${className.join(' ')}"` );

        let input = `<input type="text" ${attr.join(' ')} autocomplete="off">`;

        if ( option.widthAdjustment ) {
            input = ``
            + `<div class="inputTextWidthAdjustmentWrap">`
                + input
                + `<div class="inputTextWidthAdjustmentText">${value}</div>`
            + `</div>`
        }

        if ( option.before || option.after ) {
          const before = ( option.before )? `<div class="inputTextBefore">${option.before}</div>`: '',
                after =  ( option.after )? `<div class="inputTextAfter">${option.after}</div>`: '';

          input = `<div class="inputTextWrap">${before}<div class="inputTextBody">${input}</div>${after}</div>`;
        }
        return  input;
    },
    inputPassword: function( className, value, name, attrs = {}, option = {} ) {
        const wrapClass = ['inputPasswordWrap'],
              attr = inputCommon( value, name, attrs );

        className = classNameCheck( className, 'inputPassword input');
        if ( option.widthAdjustment ) className.push('inputTextWidthAdjustment')
        attr.push(`class="${className.join(' ')}"` );

        let input = `<input type="password" ${attr.join(' ')} autocomplete="new-password">`;

        if ( option.widthAdjustment ) {
            input = ``
            + `<div class="inputTextWidthAdjustmentWrap">`
                + input
                + `<div class="inputTextWidthAdjustmentText">${value}</div>`
            + `</div>`
        }

        // パスワード表示
        const eyeAttrs = { action: 'default'};
        if ( attrs.disabled ) eyeAttrs.disabled = 'disabled';
        input = `<div class="inputPasswordBody">${input}</div>`
        + `<div class="inputPasswordToggle">${cmn.html.button( cmn.html.icon('eye_close'), 'itaButton inputPasswordToggleButton', eyeAttrs )}</div>`;

        // パスワード削除
        if ( option.deleteToggle ) {
            const deleteClass = ['itaButton', 'inputPasswordDeleteToggleButton', 'popup'],
                  deleteAttrs = { action: 'danger', title: getMessage.FTE10041 };
            let iconName = 'cross';

            if ( attrs.disabled ) deleteAttrs.disabled = 'disabled';
            if ( option.deleteFlag ) {
                deleteClass.push('on');
                deleteAttrs.action = 'restore';
                iconName = 'ellipsis';
                wrapClass.push('inputPasswordDelete');
            }
            input += `<div class="inputPasswordDeleteToggle">`
                + `<div class="inputPasswordDeleteToggleText"><span class="inner">${getMessage.FTE00014}</span></div>`
                + cmn.html.button( cmn.html.icon( iconName ), deleteClass, deleteAttrs )
            + `</div>`;
        }

        return `<div class="${wrapClass.join(' ')}">`
            + input
        + `</div>`;
    },
    inputNumber: function( className, value, name, attrs = {}) {
        const attr = inputCommon( value, name, attrs );
        attr.push(`class="${classNameCheck( className, 'inputNumber input').join(' ')}"`);

        return `<input type="number" ${attr.join(' ')}>`;
    },
    inputColor: function( className, value, name, attrs = {}, option = {}) {
        if ( option.mode === 'edit') {
            const selectColor = cmn.checkHexColorCode( value, false );
            return ``
            + `<div class="inputColorEditWrap">`
                + `<div class="inputColorEditSelect" style="background-color:${selectColor}">`
                    + `<input type="color" class="inputColorEdit" value="${selectColor}">`
                + `</div>`
                + `<div class="inputColorEditText">`
                    + cmn.html.inputText( className, value, name, attrs )
                + `</div>`
            + `</div>`;
        } else {
            const attr = inputCommon( value, name, attrs );

            className = classNameCheck( className, 'inputColor');
            attr.push(`class="${className.join(' ')}"` );

            let input = `<input type="color" ${attr.join(' ')}>`;

            if ( option.before || option.after ) {
            const
            before = ( option.before )? `<div class="inputColorBefore">${option.before}</div>`: '',
            after =  ( option.after )? `<div class="inputColorAfter">${option.after}</div>`: '';

            input = `<div class="inputColorWrap">${before}<div class="inputColorBody">${input}</div>${after}</div>`;
            }
            return  input;
        }
    },
    inputFader: function( className, value, name, attrs = {}, option = {}) {
        const attr = inputCommon( value, name, attrs );
        let bodyClass = 'inputFaderBody';
        className = classNameCheck( className, 'inputFader inputNumber input');
        if ( option.before ) bodyClass += ' inputFaderBeforeWrap';
        if ( option.after ) bodyClass += ' inputFaderAfterWrap';

        attr.push(`class="${className.join(' ')}"`);

        let input = `<div class="${bodyClass}">`
            + `<input type="number" ${attr.join(' ')}>`
        + `</div>`;

        if ( option.before || option.after ) {
            const before = ( option.before )? `<div class="inputFaderBefore">${option.before}</div>`: '',
                  after =  ( option.after )? `<div class="inputFaderAfter">${option.after}</div>`: '';

            input = `${before}${input}${after}`;
        }

        return `<div class="inputFaderWrap">`
            + input
            + `<div class="inputFaderRange">`
                + `<div class="inputFaderRangeKnob"></div>`
                + `<div class="inputFaderRangeLower"></div>`
                + `<div class="inputFaderRangeTooltip"></div>`
            + `</div>`
        + `</div>`;
    },
    inputButton: function( className, input, button ) {
        className = classNameCheck( className, 'inputButtonWrap');
        input.className = classNameCheck( input.className, 'inputButtonInput');
        button.className = classNameCheck( button.className, 'inputButtonButton');
        return `<div class="${className.join(' ')}">`
            + `<div class="inputButtonInputWrap">${cmn.html.inputText( input.className, input.value, input.name, input.attrs, input.option )}</div>`
            + `<div class="inputButtonButtonWrap">${cmn.html.iconButton( button.icon, button.element, button.className, button.attr, button.toggle )}</div>`
        + `</div>`;
    },
    textarea: function( className, value, name, attrs = {}, widthAdjustmentFlag ) {
        const attr = inputCommon( null, name, attrs );

        className = classNameCheck( className, 'textarea input');
        if ( widthAdjustmentFlag ) className.push('textareaAdjustment')
        attr.push(`class="${className.join(' ')}"` );

        if ( widthAdjustmentFlag ) {
            return ``
            + `<div class="textareaAdjustmentWrap">`
                + `<textarea wrap="soft" ${attr.join(' ')}>${value}</textarea>`
                + `<div class="textareaAdjustmentText textareaWidthAdjustmentText">${value}</div>`
                + `<div class="textareaAdjustmentText textareaHeightAdjustmentText">${value}</div>`
            + `</div>`
        } else {
            return `<textarea wrap="off" ${attr.join(' ')}>${value}</textarea>`;
        }
    },
    check: function( className, value, name, id, attrs = {}) {
        const attr = inputCommon( value, name, attrs, id );
        attr.push(`class="${classNameCheck( className, 'checkbox').join(' ')}"`);

        return ``
        + `<div class="checkboxWrap">`
            + `<input type="checkbox" ${attr.join(' ')}>`
            + `<label for="${id}" class="checkboxLabel"></label>`
        + `</div>`;
    },
    checkboxText: function( className, value, name, id, attrs = {}, text ) {
        const attr = inputCommon( value, name, attrs, id );
        attr.push(`class="${classNameCheck( className, 'checkboxText').join(' ')}"`);

        return ``
        + `<div class="checkboxTextWrap">`
            + `<input type="checkbox" ${attr.join(' ')}>`
            + `<label for="${id}" class="checkboxTextLabel"><span class="checkboxTextMark"></span><span class="checkboxTextText">${( text )? text: value}</span></label>`
        + `</div>`;
    },
    radio: function( className, value, name, id, attrs = {}) {
        const attr = inputCommon( value, name, attrs, id );
        attr.push(`class="${classNameCheck( className, 'radio').join(' ')}"`);

        return ``
        + `<div class="radioWrap">`
            + `<input type="radio" ${attr.join(' ')}>`
            + `<label for="${id}" class="radioLabel"></label>`
        + `</div>`;
    },
    radioText: function( className, value, name, id, attrs = {}, text, typeClass = 'defaultRadioTextWrap') {
        const attr = inputCommon( value, name, attrs, id );
        attr.push(`class="${classNameCheck( className, 'radioText').join(' ')}"`);

        return ``
        + `<div class="radioTextWrap ${typeClass}">`
            + `<input type="radio" ${attr.join(' ')}>`
            + `<label for="${id}" class="radioTextLabel"><span class="radioTextMark"></span><span class="radioTextText">${( text )? text: value}</span></label>`
        + `</div>`;
    },
    select: function( list, className, value, name, attrs = {}, option = {}) {
        const selectOption = [],
              attr = inputCommon( null, name, attrs );
        if ( option.select2 !== true ) {
            className = classNameCheck( className, 'select input');
        } else {
            className = classNameCheck( className );
        }
        attr.push(`class="${className.join(' ')}"`);

        if ( option.idText !== true ) {
            // listを名称順にソートする
            let sortList;
            if ( cmn.typeof(list) === 'object') {
                sortList = Object.keys( list ).map(function(key){
                    return list[key];
                });
            } else {
                sortList = $.extend( true, [], list );
                // リストにvalueが含まれてなければ追加する
                if ( fn.typeof( value ) === 'array') {
                    for ( const val of value ) {
                        if ( value !== null && sortList.indexOf( val ) === -1 ) {
                            sortList.push( val );
                        }
                    }
                } else {
                    if ( value !== null && sortList.indexOf( value ) === -1 ) {
                        sortList.push( value );
                    }
                }
            }

            if ( option.sort !== false ) {
                sortList.sort(function( a, b ){
                    if ( a === null || a === undefined ) a = '';
                    if ( b === null || b === undefined ) b = '';
                    if ( fn.typeof( a ) === 'number') a = String( a );
                    if ( fn.typeof( b ) === 'number') b = String( b );
                    return a.localeCompare( b );
                });
            }

            // option
            for ( const item of sortList ) {
                const
                val = cmn.escape( item ),
                optAttr = [`value="${val}"`];

                // selected
                if ( fn.typeof( value ) === 'array') {
                    if ( value.indexOf( item ) !== -1 ) optAttr.push('selected="selected"');
                } else {
                    if ( value === item ) optAttr.push('selected="selected"');
                }
                selectOption.push(`<option ${optAttr.join(' ')}>${val}</option>`);
            }
        } else {
            const optionHtml = function( item ) {
                const
                text = cmn.escape( item.text ),
                id = cmn.escape( item.id ),
                optAttr = [`value="${id}"`];
                if ( cmn.escape( value ) === id ) optAttr.push('selected="selected"');
                selectOption.push(`<option ${optAttr.join(' ')}>${text}</option>`);
            };
            for ( const item of list ) {
                if ( option.group ) {
                    const label = cmn.escape( item.label );
                    selectOption.push(`<optgroup label="${label}" class="${item.className}">`);
                    for ( const groupItem of item.list ) {
                        optionHtml( groupItem );
                    }
                    selectOption.push(`</optgroup>`);
                } else {
                    optionHtml( item );
                }
            }
        }

        return ``
        + `<select ${attr.join(' ')}>`
            + selectOption.join('')
        + `</select>`;
    },
    noSelect: function() {
        return '<div class="noSelect">No data</div>';
    },
    row: function( element, className ) {
        className = classNameCheck( className, 'tr');
        return `<tr class="${className.join(' ')}">${element}</tr>`;
    },
    cell: function( element, className, type = 'td', rowspan = 1, colspan = 1, attrs = {}) {
        const attr = bindAttrs( attrs );
        attr.push(`class="${classNameCheck( className, type ).join(' ')}"`);
        attr.push(`rowspan="${rowspan}"`);
        attr.push(`colspan="${colspan}"`);
        return ``
        + `<${type} ${attr.join(' ')}>`
            + `<div class="ci">${element}</div>`
        + `</${type}>`;
    },
    table: function( tableData, className, thNumber ) {
        className = classNameCheck( className, 'commonTable');

        const table = [];
        for ( const type in tableData ) {
            table.push(`<${type}>`);
            const row = [];
            for ( const cells of tableData[ type ] ) {
                const cellLength = cells.length,
                      cell = [];
                for ( let i = 0; i < cellLength; i++ ) {
                    const cellData = cells[i];
                    if ( type === 'thead') {
                        cell.push(`<th class="commonTh">${cellData}</th>`);
                    } else {
                        if ( i < thNumber ) {
                            cell.push(`<th class="commonTh">${cellData}</th>`);
                        } else {
                            cell.push(`<td class="commonTd">${cellData}</td>`);
                        }
                    }
                }
                const rowClass = ( type === 'thead')? 'tHeadTr': 'commonTr';
                row.push(`<tr class="${rowClass}">${cell.join('')}</tr>`);
            }
            table.push( row.join('') );
            table.push(`</${type}>`);
        }

        return `<table class="${className.join(' ')}">${table.join('')}</table>`;
    },
    dateInput: function( timeFlag, className, value, name, attrs = {} ) {
        className = classNameCheck( className, 'inputDate');

        let placeholder = 'yyyy/MM/dd';
        if ( timeFlag ) {
            if ( timeFlag === 'hm') {
                placeholder += ' HH:mm';
            } else if  ( timeFlag === 'h') {
                placeholder += ' HH';
            } else {
                placeholder += ' HH:mm:ss';
            }
        }
        attrs.timeFlag = timeFlag;
        attrs.placeholder = placeholder;

        const buttonAttrs = { action: 'normal', timeFlag: timeFlag };
        if ( attrs.disabled ) {
            buttonAttrs.disabled = 'disabled';
        }

        return `<div class="inputDateContainer">`
            + `<div class="inputDateBody">`
                + fn.html.inputText( className, value, name, attrs )
            + `</div>`
            + `<div class="inputDateCalendar">`
                + fn.html.button('<span class="icon icon-cal"></span>', ['itaButton', 'inputDateCalendarButton'], buttonAttrs )
            + `</div>`
        + `</div>`;
    },
    fileSelect: function( value, className, attrs = {}, edit = true ) {
        className = classNameCheck( className, 'inputFile');

        let file = ''
        + `<div class="inputFileBody">`
                + cmn.html.button( value, className, attrs )
        + `</div>`;

        if ( edit ) {
            file += `<div class="inputFileEdit">`
                + cmn.html.button( cmn.html.icon('edit'), 'itaButton inputFileEditButton popup', Object.assign( attrs, { action: 'positive', title: getMessage.FTE00175 }))
            + `</div>`
        }

        file += `<div class="inputFileClear">`
            + cmn.html.button( cmn.html.icon('clear'), 'itaButton inputFileClearButton popup', { action: 'restore', title: getMessage.FTE00076 })
        + `</div>`;

        return `<div class="inputFileWrap">`
            + file
        + `</div>`;
    },
    required: function() {
        return `<span class="required">${getMessage.FTE10057}</span>`;
    },
    operationItem: function( item ){
        const itemHtml = [],
              itemStyle = [],
              itemClass = ['operationMenuItem'],
              itemAttr = {};

        // item
        if ( item.className ) itemClass.push( item.className );
        if ( item.separate ) itemClass.push('operationMenuSeparate');
        if ( item.display ) itemStyle.push(`display:${item.display}`);
        if ( itemStyle.length ) itemAttr.style = itemStyle.join(';');
        itemAttr.class = itemClass.join(' ');

        const itemAttrs = bindAttrs( itemAttr );

        // button
        if ( item.button ) {
            const button = item.button,
                  buttonClass = ['itaButton', 'operationMenuButton'],
                  buttonStyle = [],
                  buttonAttr = { title: button.text, action: button.action, type: button.type },
                  buttonOption = {};
            if ( button.width ) buttonStyle.push(`width:${button.width}`);
            if ( button.minWidth ) buttonOption.minWidth = button.minWidth;
            if ( button.className ) buttonClass.push( button.className );
            if ( button.disabled ) buttonAttr.disabled = 'disabled';
            if ( buttonStyle.length ) buttonAttr.style = buttonStyle.join(';');
            if ( button.toggle ) buttonOption.toggle = button.toggle;
            if ( button.icon ) {
                itemHtml.push( cmn.html.iconButton( button.icon, button.text, buttonClass, buttonAttr, buttonOption ) );
            } else {
                itemHtml.push( cmn.html.button( button.text, buttonClass, buttonAttr, buttonOption ) );
            }
        }

        // input
        if ( item.input ) {
            const input = item.input,
                  inputClass = ['operationMenuInput'],
                  inputOption = { widthAdjustment: true, before: input.before, after: input.after };
            if ( input.className ) inputClass.push( input.className );
            itemHtml.push( cmn.html.inputText( inputClass, input.value, input.type, null, inputOption ) );
        }

        // select
        if ( item.select ) {
            const input = item.select,
                  inputClass = ['operationMenuSelect'],
                  inputOption = { idText: true };
            if ( !item.list ) item.list = [];
            if ( input.className ) inputClass.push( input.className );
            if ( input.group ) inputOption.group = input.group;
            itemHtml.push( cmn.html.select( input.list, inputClass, input.value, '', {}, inputOption ) );
        }

        // search
        if ( item.search ) {
            const placeholder = ( item.search.placeholder )? item.search.placeholder: '';
            itemHtml.push(`<div class="operationMenuSearch">`
                + `<span class="icon icon-search"></span>`
                + `<input class="operationMenuSearchText input" name="${item.search.tableId}_operationMenuSearchText" autocomplete="off" placeholder="${placeholder}">`
                + `<button class="operationMenuSearchClear"><span class="icon icon-cross"></span></button>`
            + `</div>`);
        }

        // check
        if ( item.check ) {
            const check = item.check,
                  checkClass = ['operationMenuInput'];
            if ( check.className ) checkClass.push( check.className );
            itemHtml.push( cmn.html.checkboxText( checkClass, check.value, check.name, check.name ) );
        }

        // message
        if ( item.message ) {
            const messageIcon = ( item.message.icon )? item.message.icon: 'circle_info';
            itemHtml.push(`<div class="operationMenuMessage">`
            + `<span class="operationMenuMessageIcon">${cmn.html.icon( messageIcon )}</span>`
            + `<span class="operationMenuMessageText">${item.message.text}</span></div>`);
        }

        // Radio list
        if ( item.radio ) {
            const title = item.radio.title;

            const listHtml = [];
            for ( const key in item.radio.list ) {
                const checked = ( key === item.radio.checked )? {checked: 'checked'}: {};
                listHtml.push(`<li class="operationMenuRadioItem">`
                + cmn.html.radioText('operationMenuRadio ' + item.radio.className, key, item.radio.name, 'operationMenuRadio_' + key, checked, item.radio.list[ key ], 'narrowRadioTextWrap')
                + `</li>`);
            }
            itemHtml.push(`<div class="operationMenuRadioWrap">`
            + `<div class="operationMenuRadioTitle">${title}</div>`
            + `<ul class="operationMenuRadioList">${listHtml.join('')}</ul></div>`)
        }

        // HTML
        if ( item.html ) {
            itemHtml.push( item.html.html );
        }

        return `<li ${itemAttrs.join(' ')}>${itemHtml.join('')}</li>`;
    },
    operationMenu: function( menu, className ) {
        className = classNameCheck( className, 'operationMenuList');

        const html = [];
        const list = {
            Main: [],
            Sub: []
        };

        for ( const menuType in list ) {
            if ( menu[ menuType ] ) {
                for ( const item of menu[ menuType ] ) {
                    list[ menuType ].push( cmn.html.operationItem( item ) );
                }
                if ( menu[ menuType ].length ) {
                    html.push(`<ul class="${className.join(' ')} operationMenu${menuType}">${list[ menuType ].join('')}</ul>`);
                }
            }
        }

        return `<div class="operationMenu">${html.join('')}</div>`;
    },
    labelListHtml: function( labels, labelData ) {
        const html = [];

        if ( !labelData ) labelData = [];

        // 文字列の場合はパースする
        labels = ( cmn.typeof( labels ) === 'string')? cmn.jsonParse( labels, 'array'): labels;

        // ラベルリストの形式
        if ( cmn.typeof( labels ) === 'array') {
            for ( const label of labels ) {
                if ( label.length === 2 ) {
                    html.push( this.labelHtml( labelData, label[0], label[1] ) );
                } else {
                    html.push( this.labelHtml( labelData, label[0], label[2], label[1] ) );
                }
            }
        } else if ( cmn.typeof( labels ) === 'object') {
            for ( const key in labels ) {
                html.push( this.labelHtml( labelData, key, labels[ key ] ) );
            }
        }

        return ``
        + `<ul class="eventFlowLabelList">`
            + html.join('')
        + `</ul>`;
    },
    labelHtml: function( labelData, key, value, condition ) {
        // 色の取得
        const label = labelData.find(function( item ){
            return key === item.parameter.label_key_name;
        });

        const exastroLabelColor = '#CCC'; // _exastro_xxxラベル
        const defaultLabelColor = '#002B62'; // ラベル設定の無いラベル

        const color = ( label && label.parameter && label.parameter.color_code )? label.parameter.color_code:
            ( key.indexOf('_exastro_') === 0 )? exastroLabelColor: defaultLabelColor;

        const
        keyColor = cmn.blackOrWhite( color, 1 ),
        conColor = cmn.blackOrWhite( color, 1 ),
        valColor = cmn.blackOrWhite( color, .5 );

        // 改行をエスケープ
        value = cmn.nlcEscape( value );

        return ``
        + `<li class="eventFlowLabelItem">`
            + `<div class="eventFlowLabel" style="background-color:${color}">`
                + `<div class="eventFlowLabelKey"><span class="eventFlowLabelText" style="color:${keyColor}">${fn.cv( key, '', true )}</span></div>`
                + ( ( condition )? `<div class="eventFlowLabelCondition" style="color:${conColor}">${fn.cv( condition, '', true )}</div>`: ``)
                + `<div class="eventFlowLabelValue"><span class="eventFlowLabelText" style="color:${valColor}">${fn.cv( value, '', true )}</span></div>`
            + `</div>`
        + `</li>`;
    }
},
/*
##################################################
   HEX colorチェック
##################################################
*/
checkHexColorCode: function( code, nullCheckFlag = true ) {
    if ( nullCheckFlag && ( code === '' || code === null || code === undefined ) ) return code;
    const regex = new RegExp(/^#[a-fA-F0-9]{6}$/);
    if ( regex.test( code ) ) {
        return code.toUpperCase();
    } else {
        return '#000000';
    }
},
/*
##################################################
    背景色からテキストカラーを判定
##################################################
*/
blackOrWhite: function( hexcolor, num ) {
    if ( !hexcolor ) return '';
	const
    r = parseInt( hexcolor.substring( 1, 3 ), 16 ),
    g = parseInt( hexcolor.substring( 3, 5 ), 16 ),
    b = parseInt( hexcolor.substring( 5, 7 ), 16 );

	return (((( r * 299 ) + ( g * 587 ) + ( b * 114 )) / 1000 ) < 180 * num )? '#FFFFFF': '#333333';
},
/*
##################################################
    処理中モーダル
##################################################
*/
processingModal: function( title ) {
    const config = {
        mode: 'modeless',
        position: 'center',
        header: {
            title: title
        },
        width: '320px'
    };

    const dialog = new Dialog( config );
    dialog.open();

    return dialog;
},
/*
##################################################
    進捗モーダル
##################################################
*/
progressModal: function( title, option = {}) {
    const config = {
        mode: 'modeless',
        position: 'center',
        header: {
            title: title
        },
        width: '320px'
    };

    // 閉じるボタン
    if ( option.close !== undefined ) {
        config.header.close = true;
    }

    const dialog = new Dialog( config );
    const html = ``
    + `<div class="progressConteinar">`
        + `<div class="progressWrap">`
            + `<div class="progressBar"></div>`
            + `<div class="progressPercentage"><span class="progressPercentageNumber">0</span><span class="progressPercentageUnit">%</span></div>`
        + `</div>`
        + `<div class="progressTimer">00:00:00</div>`
        + `<div class="progressText">0 Byte / 0 Byte</div>`
    + `</div>`;
    dialog.open( html );


    dialog.progress = function( receivedLength, contentLength ) {
        const rate = ( Number( receivedLength ) / Number( contentLength ) * 100 ).toFixed(2);
        dialog.$.dbody.find('.progressBar').css('width', rate + '%' );
        dialog.$.dbody.find('.progressPercentageNumber').text( rate );
        dialog.$.dbody.find('.progressText').text(`${Number( receivedLength ).toLocaleString()} Byte / ${Number( contentLength ).toLocaleString()} Byte`);
    };

    // HH:MM:SS 変換
    const convertTime = function( milliseconds ) {
        const totalSeconds = Math.floor( milliseconds / 1000 );
        const minutes = Math.floor( totalSeconds / 60 );
        const seconds = fn.zeroPadding( totalSeconds % 60, 2 );
        const hours = Math.floor( minutes / 60);
        const displayHours = ( hours < 100 )? fn.zeroPadding( hours, 2 ): hours;
        const remainingMinutes = fn.zeroPadding( minutes % 60, 2 );
        return `${displayHours}:${remainingMinutes}:${seconds}`;
    };

    const start = performance.now();
    const timer = function() {
        const now = performance.now();
        const time = now - start;
        dialog.$.dbody.find('.progressTimer').text( convertTime( time ) );
        if ( dialog.$.dialog.is(':visible') ) {
            setTimeout( timer, 1000 );
        };
    };
    timer();

    return dialog;
},
/*
##################################################
    登録成功モーダル
##################################################
*/
resultModal: function( result ) {
    return new Promise(function( resolve ){
        const funcs = {};
        funcs.ok = function(){
            dialog.close();
            resolve( true );
        };
        const config = {
            mode: 'modeless',
            position: 'center',
            header: {
                title: getMessage.FTE10042
            },
            width: '480px',
            footer: {
                button: { ok: { text: getMessage.FTE10043, action: 'normal'}}
            }
        };
        const html = []

        const listOrder = ['Register', 'Update', 'Discard', 'Restore'];
        for ( const key of listOrder ) {
              html.push(`<dl class="resultList resultType${key}">`
                  + `<dt class="resultType">${key}</dt>`
                  + `<dd class="resultNumber">${result[key]}</dd>`
              + `</dl>`);
        }

        const dialog = new Dialog( config, funcs );
        dialog.open(`<div class="resultContainer">${html.join('')}</div>`);
    });
},
/*
##################################################
   登録失敗エラーモーダル
##################################################
*/
errorModal: function( errors, pageName, info ) {
    return new Promise(function( resolve ){
        let errorMessage;
        try {
            errorMessage = JSON.parse(errors.message);
        } catch ( e ) {
            //JSONを作成
            errorMessage = {'0':{}};
            errorMessage['0'][ getMessage.FTE00064 ] = [ errors.message ];
        }
        const errorHtml = [];
        for ( const item in errorMessage ) {
            for ( const error in errorMessage[item] ) {
                const number = Number( item ) + 1,
                      name = cmn.cv( error, '', true ),
                      body = cmn.cv( errorMessage[item][error].join(''), '?', true );

                const columnId = Object.keys( info.column_info ).find(function( key ){
                    return info.column_info[ key ].column_name_rest === name;
                });

                const columnName = ( columnId )? info.column_info[ columnId ].column_name: error;

                errorHtml.push(`<tr class="tBodyTr tr">`
                + cmn.html.cell( number, ['tBodyTh', 'tBodyLeftSticky'], 'th')
                + cmn.html.cell( columnName, 'tBodyTd')
                + cmn.html.cell( body, 'tBodyTd')
                + `</tr>`);
            }
        }

        const html = `
        <div class="errorTableContainer">
            <table class="table errorTable">
                <thead class="thead">
                    <tr class="tHeadTr tr">
                        <th class="tHeadTh tHeadLeftSticky th"><div class="ci">No.</div></th>
                        <th class="tHeadTh th"><div class="ci">${getMessage.FTE10044}</div></th>
                        <th class="tHeadTh th"><div class="ci">${getMessage.FTE10045}</div></th>
                    </tr>
                </thead>
                <tbody class="tbody">
                    ${errorHtml.join('')}
                </tbody>
            </table>
        </div>`;

        const funcs = {};
        funcs.ok = function() {
            dialog.close();
            resolve( true );
        };
        funcs.download = function() {
            cmn.download('json', errorMessage, pageName + '_register_error_log');
        };
        const config = {
            mode: 'modeless',
            position: 'center',
            header: {
                title: getMessage.FTE10046
            },
            width: 'auto',
            footer: {
                button: {
                  download: { text: getMessage.FTE10047, action: 'default'},
                  ok: { text: getMessage.FTE10043, action: 'normal'}
              }
            }
        };

        const dialog = new Dialog( config, funcs );
        dialog.open(`<div class="errorContainer">${html}</div>`);
    });

},
/*
##################################################
   Common events
##################################################
*/
setCommonEvents: function() {
    const $window = $( window ),
          $body = $('body');

    // input textの幅を入力に合わせる
    $body.on('input.textWidthAdjustment', '.inputTextWidthAdjustment', function(){
        const $text = $( this ),
              value = $text.val();
        $text.next('.inputTextWidthAdjustmentText').text( value );
    });

    // textareaの幅と高さを調整する
    $body.on('input.textareaWidthAdjustment', '.textareaAdjustment', cmn.textareaAdjustment );

    // パスワード表示・非表示切替
    $body.on('click', '.inputPasswordToggleButton', function(){
        const $button = $( this ),
              $input = $button.closest('.inputPasswordWrap').find('.inputPassword');

        if ( !$button.is('.on') ) {
            $button.addClass('on');
            $button.find('.inner').html( cmn.html.icon('eye_open'));
            $input.attr('type', 'text');
        } else {
            $button.removeClass('on');
            $button.find('.inner').html( cmn.html.icon('eye_close'));
            $input.attr('type', 'password');
        }
    });

    // パスワード候補を初回クリックで出さないようにする
    $body.on('pointerdown', '.inputPassword', function( e ){
        e.preventDefault();
        const $input = $( this );

        setTimeout( function(){
            $input.focus();
        }, 1 );
    });

    // 切替ボタン
    $body.on('click', '.toggleButton', function(){
        const $button = $( this ),
              flag = ( $button.attr('data-toggle') === 'on')? 'off': 'on';
        if ( !$button.closest('.standBy').length ) {
            $button.attr('data-toggle', flag );
        }
    });

    // titel の内容をポップアップ
    $body.on('pointerenter.popup', '.popup', function(){
        const $t = $( this ),
              ttl = $t.attr('title');
        if ( ttl !== undefined ) {
            $t.removeAttr('title');

            const type = ( $t.is('.parameterCollectionPopup') )? 'parameterCollection': 'default';

            const $p = $('<div/>', {
                'class': 'popupBlock',
                'html': `<div class="popupInner">${fn.escape( ttl, true )}</div>`
            }).append('<div class="popupArrow"><span></span></div>');

            const $inner = $p.find('.popupInner'),
                  $arrow = $p.find('.popupArrow');

            if( $t.is('.darkPopup') ) $p.addClass('darkPopup');
            if( $t.is('.parameterCollectionPopup') ) $p.addClass('parameterCollectionPopup');

            $body.append( $p );

            const r = $t[0].getBoundingClientRect(),
                  wW = $window.width(),
                  wH = $window.height(),
                  tW = $t.outerWidth(),
                  tH = $t.outerHeight(),
                  tL = r.left,
                  tT = ( type === 'parameterCollection')? r.top - 92: r.top,
                  tB = wH - tT - tH,
                  pW = Math.ceil( $p.outerWidth() ) + 2,
                  wsL = $window.scrollLeft();

            let pL = ( tL + tW / 2 ) - ( pW / 2 ) - wsL,
                pH = Math.ceil( $p.outerHeight() ) + 2,
                pT = tT - pH;

            // 上か下か
            if ( pT <= 0 && tT < tB ) {
                $p.addClass('popupBottom');
                if ( tB < pH ) pH = tB;
                pT = tT + tH;
            } else {
                if ( tT < pH ) pH = tT;
                $p.addClass('popupTop');
            }
            if ( wW < pL + pW ) pL = wW - pW;
            if ( pL <= 0 ) pL = 0;

            $p.css({
                'width': pW,
                'height': pH,
                'left': pL,
                'top': pT
            });

            // 矢印の位置
            let aL = 0;
            if ( tL - wsL + tW > wW ) {
                const twW = tW - ( tL - wsL + tW - wW );
                if ( twW > pW || wW < twW ) {
                    aL = pW / 2;
                } else {
                    aL = pW - ( twW / 2 );
                    if ( pW - aL < 20 ) aL = pW - 20;
                }
            } else if ( tL < wsL ) {
                const twW = tL + tW - wsL;
                if ( twW > pW ) {
                    aL = pW / 2;
                } else {
                    aL = twW / 2;
                    if (aL < 20 ) aL = 20;
                }
            } else {
                aL = ( tL + ( tW / 2 )) - pL - wsL;
            }
            $arrow.css('left', aL );

            if ( $t.is('.popupHide') ) {
                $p.addClass('popupHide');
            }


            // ホイールでポップアップ内をスクロール
            $t.on('wheel.popup', function( e ){
                if ( !$t.is('.popupScroll') ) {
                    $t.trigger('pointerleave');
                }
                e.preventDefault();

                const delta = e.originalEvent.deltaY ? - ( e.originalEvent.deltaY ) : e.originalEvent.wheelDelta ? e.originalEvent.wheelDelta : - ( e.originalEvent.detail );

                if ( delta < 0 ) {
                    $inner.scrollTop( $inner.scrollTop() + 16 );
                } else {
                    $inner.scrollTop( $inner.scrollTop() - 16 );
                }
            });

            $t.on('pointerleave.popup', function(){
                const $p = $body.find('.popupBlock'),
                      title = ttl;
                $p.remove();
                $t.off('pointerleave.popup click.popup wheel.popup').attr('title', title );
            });

            // data-popupがclickの場合クリック時に一旦非表示
            $t.on('click.popup', function(){
                if ( $t.attr('data-popup') === 'click') {
                   if ( $t.is('.popupHide') ) {
                        $t.add( $p ).removeClass('popupHide');
                    } else {
                        $t.add( $p ).addClass('popupHide');
                    }
                }
            });

            const targetCheck = function(){
                if ( $t.is(':visible') ) {
                    if ( $p.is(':visible') ) {
                        setTimeout( targetCheck, 200 );
                    }
                } else {
                    $p.remove();
                }
            };
            targetCheck();
        }
    });
},
/*
##################################################
   textareaの幅と高さを調整する
##################################################
*/
textareaAdjustment: function() {
    const $text = $( this ),
          $parent = $text.parent('.textareaAdjustmentWrap'),
          $width = $parent.find('.textareaWidthAdjustmentText'),
          $height = $parent.find('.textareaHeightAdjustmentText');

    // 空の場合、高さを求めるためダミー文字を入れる
    let value = fn.escape( $text.val() ).replace(/\n/g, '<br>').replace(/<br>$/g, '<br>!');
    if ( value === '') value = '!';

    $width.add( $height ).html( value );

    if ( $width.get(0).scrollWidth > 632 ) {
        $parent.addClass('textareaOverWrap');
    } else {
        $parent.removeClass('textareaOverWrap');
    }

    $parent.css('height', $height.outerHeight() + 1 );

},
/*
##################################################
  選択用モーダル
  config: {
      title: モーダルタイトル
      selectNameKey: 選択で返す名称Key
      info: Table構造info URL
      infoData: Table構造infoが取得済みの場合はこちらに
      filter: Filter URL
      filterPulldown: Filter pulldown URL
      sub: infoに複数のTable構造がある場合のKey
      option: テーブル用オプション
      select: 選択状態の変更値,
      unselected: ture, 未選択も可にする
  }
##################################################
*/
selectModalOpen: function( modalId, title, menu, config ) {
    return new Promise(function( resolve ){
        const modalFuncs = {
            ok: function() {
                modalInstance[ modalId ].modal.hide();
                const selectId = cmn.arrayCopy( modalInstance[ modalId ].table.select.select );
                resolve( selectId );
            },
            cancel: function() {
                modalInstance[ modalId ].modal.hide();
                resolve( null );
            }
        };

        if ( !modalInstance[ modalId ] ) {
            fn.initSelectModal( modalId, title, menu, config ).then(function( modalAndTable ){
                modalInstance[ modalId ] = modalAndTable;
                modalInstance[ modalId ].modal.btnFn = modalFuncs;
            });
        } else {
            modalInstance[ modalId ].modal.show();
            // 選択状態をセットする
            cmn.setSelectArray( modalInstance[ modalId ].table, config, modalInstance[ modalId ].modal );

            modalInstance[ modalId ].modal.btnFn = modalFuncs;
        }
    });
},
/*
##################################################
   選択用モーダルの初期設定
   tableとmodalのインスタンスを返す
##################################################
*/
initSelectModal: function( modalId, title, menu, selectConfig ) {

    return new Promise(function( resolve ) {
        const modalConfig = {
            mode: 'modeless',
            width: ( selectConfig.width )? selectConfig.width: 'auto',
            position: 'center',
            visibility: false,
            header: {
                title: title
            },
            footer: {
                button: {
                    ok:  { text: getMessage.FTE10048, action: 'positive', className: 'dialogPositive', style: `width:200px`},
                    cancel: { text: getMessage.FTE10026, action: 'normal'}
                }
            }
        };

        const processingModal = cmn.processingModal( title );

        const modal = new Dialog( modalConfig );
        modal.open();

        const resolveModal = function( info ) {
            const params = cmn.getCommonParams();
            params.menuNameRest = menu;
            params.selectNameKey = selectConfig.selectNameKey;
            params.restFilter = selectConfig.filter;
            params.restFilterPulldown = selectConfig.filterPulldown;
            if ( selectConfig.selectOtherKeys ) params.selectOtherKeys = selectConfig.selectOtherKeys;
            if ( selectConfig.selectType ) params.selectType = selectConfig.selectType;

            let option = {};
            if ( selectConfig.option ) option = selectConfig.option;

            // 取得したinfoのSubキー確認
            if ( selectConfig.sub ) info = info[ selectConfig.sub ];

            const tableId = `${modalId}_${menu.toUpperCase()}${( selectConfig.sub )? `_${selectConfig.sub}`: ``}`,
                  table = new DataTable( tableId, 'select', info, params, option );
            if ( selectConfig.select ) table.select.select = selectConfig.select;
            modal.setBody( table.setup() );

            // 選択チェック
            if ( !selectConfig.unselected ) {
                table.$.container.on(`${table.id}selectChange`, function(){
                    if ( table.select.select.length ) {
                        modal.buttonPositiveDisabled( false );
                    } else {
                        modal.buttonPositiveDisabled( true );
                    }
                });
            }

            // 初期表示の場合は読み込み完了後に表示
            $( window ).one( tableId + '__tableReady', function(){
                // 選択状態（名称リストからIDリストを作成）
                cmn.setSelectArray( table, selectConfig, modal );

                processingModal.close();
                modal.hide();
                modal.$.dialog.removeClass('hiddenDialog');
                modal.show();

                if ( selectConfig.unselected && table.data.count > 0 ) {
                    modal.buttonPositiveDisabled( false );
                }
            });

            resolve({
                modal: modal,
                table: table
            });
        };

        // Table info確認
        if ( selectConfig.infoData ) {
            resolveModal( selectConfig.infoData );
        } else {
            // infoが無ければ読み込む
            fn.fetch( selectConfig.info ).then(function( info ){
                resolveModal( info );
            });
        }
    });
},
/*
##################################################
  選択状態をセットする
##################################################
*/
setSelectArray( table, config, modal ) {
    if ( cmn.typeof( config.selectTextArray ) === 'array' ) {
        table.select.select = config.selectTextArray.map(function( text ){
            const param = table.data.body.find(function( item ){
                return item.parameter[ config.selectTextArrayTextKey ] === text;
            });
            if ( param ) {
                return {
                    id: param.parameter[ config.selectTextArrayIdKey ],
                    name: text
                };
            } else {
                return undefined;
            }
        }).filter( Boolean );

        table.setTbody();
    }

    if ( cmn.typeof( config.select ) === 'array' ) {
        table.select.select = cmn.arrayCopy( config.select );
        table.setTbody();
    }

    const checkFlag = ( table.select.select.length === 0 );
    if ( !config.unselected ) {
        modal.buttonPositiveDisabled( checkFlag );
    }
},
/*
##################################################
  作業実行
##################################################
*/
executeModalOpen: function( modalId, menu, executeConfig ) {
    return new Promise(function( resolve ){
        const funcs = {
            ok: function(){
                const $dialog = modalInstance[ modalId ].$.dbody;
                modalInstance[ modalId ].hide();
                resolve({
                    selectName: executeConfig.selectName,
                    selectId: executeConfig.selectId,
                    id: $dialog.find('.executeOperetionId').text(),
                    name: $dialog.find('.executeOperetionName').text(),
                    schedule: $dialog.find('.executeSchedule').val()
                });
            },
            cancel: function(){
                modalInstance[ modalId ].hide();
                resolve('cancel');
            }
        };

        if ( !modalInstance[ modalId ] ) {
            const html = `
            <div class="commonSection">
                <div class="commonTitle">${executeConfig.title} ${executeConfig.itemName}</div>
                <div class="commonBody">
                    <table class="commonTable">
                        <tbody class="commonTbody">
                            <tr class="commonTr">
                                <th class="commonTh">ID</th>
                                <td class="commonTd selectId"></td>
                            </tr>
                            <tr class="commonTr">
                                <th class="commonTh">${getMessage.FTE10055}</th>
                                <td class="commonTd selectName"></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <div class="commonTitle">${getMessage.FTE10049} ${cmn.html.required()}</div>
                <div class="commonBody">
                    <table class="commonTable">
                        <tbody class="commonTbody">
                            <tr class="commonTr">
                                <th class="commonTh">ID</th>
                                <td class="commonTd executeOperetionId"></td>
                            </tr>
                            <tr class="commonTr">
                                <th class="commonTh">${getMessage.FTE10055}</th>
                                <td class="commonTd executeOperetionName"></td>
                            </tr>
                        </tbody>
                    </table>
                    <ul class="commonMenuList">
                        <li class="commonMenuItem">
                            ${fn.html.button( fn.html.icon('menuList') + ' ' + getMessage.FTE10050, ['itaButton', 'commonButton executeOperetionSelectButton'], { action: 'default', style: `width:100%`})}
                        </li>
                    </ul>
                </div>
                <div class="commonTitle">${getMessage.FTE10052}</div>
                <div class="commonBody">
                    <div class="commonInputArea">
                        ${fn.html.dateInput( true, 'executeSchedule', '')}
                    </div>
                    <p class="commonParagraph">${getMessage.FTE10051}</p>
                </div>
            </div>`;

            const config = {
                mode: 'modeless',
                position: 'center',
                header: {
                    title: executeConfig.title + getMessage.FTE10056
                },
                width: '480px',
                footer: {
                    button: {
                        ok: { text: executeConfig.title, action: 'positive', className: 'dialogPositive',  style: `width:200px`},
                        cancel: { text: getMessage.FTE10043, action: 'normal'}
                    }
                }
            };
            modalInstance[ modalId ] = new Dialog( config, funcs );

            modalInstance[ modalId ].open( html );
            cmn.setDatePickerEvent( modalInstance[ modalId ].$.dbody.find('.executeSchedule'), getMessage.FTE10052 );

            // 選択しているItemをセット
            modalInstance[ modalId ].$.dbody.find('.selectId').text( executeConfig.selectId );
            modalInstance[ modalId ].$.dbody.find('.selectName').text( executeConfig.selectName );

            // オペレーション選択
            modalInstance[ modalId ].$.dbody.find('.executeOperetionSelectButton').on('click', function(){
                cmn.selectModalOpen( 'operation', getMessage.FTE10050, menu, executeConfig.operation ).then(function( selectResult ){
                    if ( selectResult && selectResult[0] ) {
                        modalInstance[ modalId ].$.dbody.find('.executeOperetionId').text( selectResult[0].id );
                        modalInstance[ modalId ].$.dbody.find('.executeOperetionName').text( selectResult[0].name );

                        modalInstance[ modalId ].buttonPositiveDisabled( false );
                    }
                });
            });

        } else {
            modalInstance[ modalId ].btnFn = funcs;
            modalInstance[ modalId ].show();

            // 選択しているItemをセット
            modalInstance[ modalId ].$.dbody.find('.selectId').text( executeConfig.selectId );
            modalInstance[ modalId ].$.dbody.find('.selectName').text( executeConfig.selectName );
        }
    });
},
/*
##################################################
   メッセージを出す
##################################################
*/
message: function( type, message, title, icon, closeTime ) {
    if ( !messageInstance ) {
        messageInstance = new Message();
    }
    messageInstance.add( type, message, title, icon, closeTime );
},
messageClear: function() {
    if ( messageInstance ) {
        messageInstance.clear();
    }
},
/*
##################################################
   共通エラー処理
##################################################
*/
commonErrorAlert: function( error ) {

    console.error( error );

    if ( error.message ) {
        if ( e.message !== 'Failed to fetch' && windowFlag ) {
            alert( error.message );
        }
    }
},
/*
##################################################
   エラーページへ移動
##################################################
*/
gotoErrPage: function( message ) {
    // windowFlagでWorker内か判定
    if ( windowFlag ) {
        controller.abort();
        if ( message !== 'Failed to fetch') {
            if ( message ) {
                window.alert( message );
            } else {
                window.alert('Unknown error.');
            }
            window.location.href = './system_error/';
        }
    } else {
        if ( message ) {
            console.error( message );
        } else {
            console.error('Unknown error.');
        }
    }
},

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Contentローディング
//
////////////////////////////////////////////////////////////////////////////////////////////////////

contentLoadingStart: function() {
    document.body.classList.add('loading');
    contentLoadingFlag = true;
},
contentLoadingEnd: function() {
    document.body.classList.remove('loading');
    contentLoadingFlag = false;
},
checkContentLoading: function() {
    return contentLoadingFlag;
},

filterEncode: function( json ) {
    try {
        return encodeURIComponent( JSON.stringify( json ) );
    } catch( error ) {
        return '';
    }
},

jsonStringify: function( json, space ) {
    try {
        if ( space ) {
            return JSON.stringify( json, null, space );
        } else {
            return JSON.stringify( json );
        }
    } catch( error ) {
        return '';
    }
},

jsonParse: function( json, type = 'object') {
    try {
        return JSON.parse( json );
    } catch( error ) {
        if ( type === 'object') {
            return {};
        } else if ( type === 'array') {
            return [];
        } else {
            return null;
        }
    }
},

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   iframeモーダル
//
////////////////////////////////////////////////////////////////////////////////////////////////////

modalIframe: function( menu, title, option){
    if ( !option ) option = {};
    if ( !modalInstance[ menu ] ) {
        const modalFuncs = {
            cancel: function() {
                modalInstance[ menu ] = null;
                modal.close();
            }
        };

        let width = '100%';
        if ( option.width ) width = option.width;

        const modalConfig = {
            mode: 'modeless',
            width: width,
            height: '100%',
            header: {
                title: title
            },
            footer: {
                button: {
                    cancel: { text: getMessage.FTE10043, action: 'normal'}
                }
            }
        };

        const url = [`?menu=${menu}`];
        if ( option.filter ) {
            url.push(`&filter=${cmn.filterEncode( option.filter )}`);
        }
        if ( option.iframeMode ) {
            url.push(`&iframeMode=${option.iframeMode}`);
        }

        // モーダル作成
        modalInstance[ menu ] = new Dialog( modalConfig, modalFuncs );

        const modal = modalInstance[ menu ];
        modal.open(`<iframe class="iframe" src="${url.join('')}"></iframe>`);
    }
},

iframeMessage( message ) {
    const html = `<div class="iframeMessage">
        <div class="contentMessage">
            <div class="contentMessageInner">${message}</div>
        </div>
    </div>`
    $('#container').html( html );
},

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   作業状態確認管理
//
////////////////////////////////////////////////////////////////////////////////////////////////////

/*
##################################################
   新しい作業状態確認を作成する
##################################################
*/
createCheckOperation: function( menu, operationId ) {
    if ( !operationInstance[ operationId ] ) {
        operationInstance[ operationId ] = new Status( menu, operationId );
        operationInstance[ operationId ].setup();
        return operationInstance[ operationId ];
    }
},
/*
##################################################
   作業状態確認をクリアする
##################################################
*/
clearCheckOperation: function( operationId ) {
    if ( operationInstance[ operationId ] ) {
        operationInstance[ operationId ] = null;
    }
},

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Conductor管理
//
////////////////////////////////////////////////////////////////////////////////////////////////////

/*
##################################################
   新しいConductorを作成する
##################################################
*/
createConductor: function( menu, target, mode, conductorId, option ) {
    if ( !conductorInstance[ conductorId ] ) {
        conductorInstance[ conductorId ] = new Conductor( menu, target, mode, conductorId, option );
        return conductorInstance[ conductorId ];
    }
},
/*
##################################################
   Conductorを削除する
##################################################
*/
removeConductor: function( conductorId ) {
    if ( conductorInstance[ conductorId ] ) {
        $(`.conductor[data-conductor="${conductorId}"]`).remove();
        conductorInstance[ conductorId ] = null;
    }
},
/*
##################################################
   新しいConductorをモーダルで表示する
##################################################
*/
modalConductor: function( menu, mode, conductorId, option ) {
    if ( !conductorInstance[ conductorId ] ) {
        const modalFuncs = {
            cancel: function() {
                cd.$.body.find(`[id^="cd-${cd.id}-popup-node-"]`).remove();
                modalInstance[ conductorId ] = null;
                conductorInstance[ conductorId ] = null;
                modal.close();
            }
        };
        const modalConfig = {
            mode: 'modeless',
            width: '100%',
            height: '100%',
            header: {
                title: 'Conductor'
            },
            footer: {
                button: {
                    cancel: { text: getMessage.FTE10043, action: 'normal'}
                }
            }
        };
        const target = `cd-${conductorId}-area`;

        // モーダル作成
        modalInstance[ conductorId ] = new Dialog( modalConfig, modalFuncs );
        const modal = modalInstance[ conductorId ];
        modal.open(`<div id="${target}" class="modalConductor"></div>`);

        // Conductor作成
        conductorInstance[ conductorId ] = new Conductor( menu, '#' + target, mode, conductorId, option );
        const cd = conductorInstance[ conductorId ];
        cd.setup();

    }
},

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//  設定リストモーダル
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
   設定リストモーダルを開く
##################################################
*/
settingListModalOpen: function( settingData ) {
    const _this = this;

    return new Promise(function( resolve ){
        // モーダル作成
        const modalFuncs = {
            ok: function() {
                const data = getInputData();
                modal.close();
                resolve( data );
            },
            cancel: function() {
                modal.close();
                resolve( undefined );
            }
        };
        const modalConfig = {
            mode: 'modeless',
            height: '100%',
            width: settingData.width,
            header: {
                title: _this.cv( settingData.title, '', true )
            },
            footer: {
                button: {
                    ok: { text: getMessage.FTE00143, action: 'default', width: '200px'},
                    cancel: { text: getMessage.FTE00144, action: 'normal'}
                }
            }
        };
        // 入力値を取得
        const getInputData = function() {
            const inputDate = [];
            modal.$.body.find('.settingListTr').each(function( index ){
                const $tr = $( this );
                inputDate[ index ] = [];
                $tr.find('.input').each(function(){
                    const $input = $( this );
                    const val = fn.cv( $input.val(), '');
                    if ( settingData.escape ) {
                        // タブと円マーク（バックスラッシュ）エスケープ
                        inputDate[ index ].push( val.replace(/\t/g, '\\t').replace(/\\(?![btnfr])/g, '\\\\') );
                    } else {
                        inputDate[ index ].push( val );
                    }
                });
                // 全ての入力が空ならnull
                if ( inputDate[ index ].join('') === '') inputDate[ index ] = null;
            });
            return inputDate.filter( Boolean );
        };
        const modal = new Dialog( modalConfig, modalFuncs );

        // Head
        const headHtml = [];
        for ( const item of settingData.info ) {
            const width = ( item.width )? item.width: 'auto';
            const required = ( item.required )? _this.html.required(): '';
            headHtml.push(`<th class="settingListTh" style="width:${width}"><div class="settingListHeader">${_this.cv( item.title, '', true )}${required}</div></th>`);

            // 必須じゃない場合は空白を追加する
            if ( item.type === 'select' && settingData.required === '0') {
                item.list.unshift('');
            }
        }

        // Body
        const bodyHtml = [];
        if ( settingData.values.length > 0 ) {
            const valueLength = settingData.values.length;
            for ( let i = 0; i < valueLength; i++ ) {
                bodyHtml.push( _this.settingListRowHtml( settingData, i, settingData.values[i] ) );
            }
        } else {
            bodyHtml.push( _this.settingListRowHtml( settingData ) );
        }

        const settingListHtml = ``
        + `<div class="commonSection settingList">`
            + `<div class="commonBody">`
                + `<table class="settingListTable">`
                    + `<thead class="settingListThead">`
                        + `<tr>`
                            + `<th class="settingListTh settingListAction">`
                                + _this.html.button( _this.html.icon('plus'), 'settingListAddButton itaButton popup', { action: 'default', title: '項目を追加する'})
                            + `</th>`
                            + headHtml.join('')
                            + `<th class="settingListTh settingListAction">`
                                + _this.html.button( _this.html.icon('clear'), 'settingListClearButton itaButton popup', { action: 'danger', title: '項目をリセットする'})
                            + `</th>`
                        + `</tr>`
                    + `</thead>`
                    + `<tbody class="settingListTbody">`
                        + bodyHtml.join('')
                    + `</tbody>`
                + `</table>`
            + `</div>`
        + `</div>`;

        modal.open( settingListHtml );

        _this.setSettingListEvents( modal, settingData );
        _this.setSettingListSelect2( modal );
        _this.settingListCheckListDisabled( modal );
    });
},
/*
##################################################
   設定リスト行HTML
##################################################
*/
settingListRowHtml( settingData, index = 0, value = [] ) {
    const row = [`<tr class="settingListTr">`];
    if ( settingData.move ) {
        row.push(`<td class="settingListTd"><div class="settingListMove"></div></td>`);
    } else {
        row.push(`<td class="settingListTd"><div class="settingListBlank"></div></td>`)
    }

    const infoLength = settingData.info.length;
    for ( let i = 0; i < infoLength; i++ ) {
        const item = settingData.info[i];

        const
        width = ( item.width )? item.width: 'auto',
        idName = `${item.id}_${item.type}_${Date.now()}_${index}`,
        val = ( value[i] !== undefined )? value[i]: null,
        rVal = ( val !== null )? cmn.nlcEscape( cmn.escape( val ) ): val,
        input = ( item.type === 'text')? this.html.inputText('settingListInputText', rVal, idName ):
            this.html.select( item.list, 'settingListInputSelect', val, idName, {}, { sort: false } );

        row.push(``
        + `<td class="settingListTd" style="width:${width}"><div class="settingListInput">`
            + input
        + `</div></td>`);
    }

    row.push(`<td class="settingListTd"><div class="settingListDelete">${this.html.icon('cross')}</div></td></tr>`);
    return row.join('');
},
/*
##################################################
   項目が１つの場合は移動と削除を無効化する
##################################################
*/
settingListCheckListDisabled: function( modal ) {
    const $tr = modal.$.dbody.find('.settingListTr');

    if ( $tr.length === 1 ) {
        $tr.find('.settingListMove, .settingListDelete').addClass('disabled');
    } else {
        $tr.find('.settingListMove, .settingListDelete').removeClass('disabled');
    }
},
/*
##################################################
   select2をセット
##################################################
*/
setSettingListSelect2: function( modal ) {
    modal.$.dbody.find('.settingListInputSelect').not('.select2-hidden-accessible').select2();
},
/*
##################################################
   設定リストイベント
##################################################
*/
setSettingListEvents: function( modal, settingData ) {
    const _this = this;
    modal.$.dbody.find('.settingList').each(function(){
        const $listBlock = $( this );

        // 追加
        $listBlock.find('.settingListAddButton').on('click', function(){
            $listBlock.find('.settingListTbody').append( _this.settingListRowHtml( settingData) );
            _this.settingListCheckListDisabled( modal );
            _this.setSettingListSelect2( modal );
        });

        // クリア
        $listBlock.find('.settingListClearButton').on('click', function(){
            $listBlock.find('.settingListTbody').html( _this.settingListRowHtml( settingData ) );
            _this.settingListCheckListDisabled( modal );
            _this.setSettingListSelect2( modal );
        });

        // 削除
        $listBlock.on('click', '.settingListDelete', function(){
            $( this ).closest('.settingListTr').remove();
            _this.settingListCheckListDisabled( modal );
        });

        // 移動
        if ( settingData.move ) {
            $listBlock.on('pointerdown', '.settingListMove', function( mde ){
                const $move = $( this ),
                    $window = $( window );

                if ( !$move.is('.disabled') ) {
                    const $line = $move.closest('.settingListTr'),
                        $list = $line.closest('.settingListTbody'),
                        height = $line.outerHeight(),
                        defaultY = $line.position().top,
                        maxY = $list.outerHeight() - height,
                        $dummy = $('<tr class="settingListDummy"></tr>'),
                        $body = $move.closest('.commonBody'),
                        defaultScroll = $body.scrollTop();

                    // 幅を固定
                    $line.find('.settingListTd').each(function(){
                        const $td = $( this );
                        $td.css('width', $td.outerWidth() );
                    });

                    $list.addClass('active');
                    $line.addClass('move').css('top', defaultY ).after( $dummy )
                    $dummy.css('height', height );

                    cmn.deselection();

                    let positionY = defaultY;
                    const listPosition = function(){
                        let setPostion = positionY - ( defaultScroll - $body.scrollTop() );
                        if ( setPostion < 0 ) setPostion = 0;
                        if ( setPostion > maxY ) setPostion = maxY;
                        $line.css('top', setPostion );
                    };

                    $body.on('scroll.freeMove', function(){
                        listPosition();
                    });

                    $window.on({
                        'pointermove.freeMove': function( mme ){
                            positionY = defaultY + mme.pageY - mde.pageY;
                            listPosition();
                            if ( $( mme.target ).closest('.settingListTr').length ) {
                                const $target = $( mme.target ).closest('.settingListTr'),
                                    targetNo = $target.index(),
                                    dummyNo = $dummy.index();
                                if ( targetNo < dummyNo ) {
                                    $target.before( $dummy );
                                } else {
                                    $target.after( $dummy );
                                }
                            }
                        },
                        'pointerup.freeUp': function(){
                            $body.off('scroll.freeMove');
                            $window.off('pointermove.freeMove pointerup.freeUp');
                            $list.removeClass('active');
                            $line.removeClass('move');
                            $line.find('.settingListTd').removeAttr('style');
                            $dummy.replaceWith( $line );
                        }
                    });
                }
            });
        }
    });
},

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//  画面設定
//
////////////////////////////////////////////////////////////////////////////////////////////////////

setUiSetting: function() {
    const uiSettingData = cmn.storage.get('ui_setting');
    // テーマ
    if ( uiSettingData && uiSettingData.theme ) {
        cmn.setTheme( uiSettingData.theme );
    } else {
        cmn.setTheme('default');
    }
    // フィルター
    if ( uiSettingData && uiSettingData.filter ) {
        cmn.setFilter( uiSettingData.filter );
    } else {
        $('body').removeAttr('style');
    }
},

setTheme: function( theme ) {
    const $theme = $('#thema'),
          src = `/_/ita/thema/${theme}.css?v=${version}`;
    $theme.attr('href', src );

    // ダークモード
    if ( theme === 'darkmode') {
        $('body').addClass('darkmode');
    } else {
        $('body').removeClass('darkmode');
    }
},

setFilter: function( filterList ) {
    const style = [];
    for ( const type in filterList ) {
        const value = filterList[ type ];
        switch ( type ) {
            case 'brightness': case 'contrast': case 'saturate':
                if ( value !== 100 ) style.push(`${type}(${value/100})`);
            break;
            case 'grayscale': case 'invert': case 'sepia':
                if ( value !== 0 ) style.push(`${type}(${value/100})`);
            break;
            case 'huerotate':
                if ( value !== 0 ) style.push(`hue-rotate(${value}deg)`);
            break;
        }
    }
    const filter = ( style.length )? { filter: style.join(' ')}: { filter: 'none'};
    $('body').css( filter );
},

uiSetting: function() {
    return new Promise(function( resolve ){
        const funcs = {
            ok: function(){
                setUiSettingData();
            },
            cancel: function(){
                cmn.setUiSetting();
                uiSettingInstance.buttonPositiveDisabled( true );
                uiSettingInstance.hide();
                resolve('cancel');
            }
        };

        // データ更新
        const setUiSettingData = function() {

            // ユーザー情報取得
            const sessionUserData = cmn.storage.get('restUser', 'session');
            if ( sessionUserData ) {
                const process = cmn.processingModal();

                const uiSettingData = {
                    theme: uiSettingInstance.$.dbody.find('.displaySettingTheme').val(),
                    filter: getFilterValue()
                };

                if ( !sessionUserData.web_table_settings ) sessionUserData.web_table_settings = {};
                sessionUserData.web_table_settings.ui = uiSettingData;
                cmn.fetch('/user/table_settings/', null, 'POST', sessionUserData.web_table_settings ).then(function(){
                    cmn.storage.set('ui_setting', uiSettingData );
                    cmn.setUiSetting();
                }).catch(function(){
                    cmn.alert( getMessage.FTE10092, getMessage.FTE10093 );
                }).then(function(){
                    process.close();
                    uiSettingInstance.buttonPositiveDisabled( true );
                    uiSettingInstance.hide();
                    resolve();
                });
            } else {
                // session storageの取得に失敗した場合はエラー
                cmn.alert( getMessage.FTE10092, getMessage.FTE10093 );
            }
        };
        const getFilterValue = function() {
            // フィルター
            const $colorSetting = uiSettingInstance.$.dbody.find('.displaySettingColor'),
                  filterList = {};

            $colorSetting.each(function(){
                const $input = $( this ),
                      value = Number( $input.val() ),
                      type = $input.attr('data-type');
                filterList[type] = value;
            });

            return filterList;
        };

        if ( !uiSettingInstance ) {
            const themeList = {
                default: getMessage.FTE10065,
                red: getMessage.FTE10066,
                green: getMessage.FTE10067,
                blue: getMessage.FTE10068,
                orange: getMessage.FTE10069,
                yellow: getMessage.FTE10070,
                purple: getMessage.FTE10071,
                brown: getMessage.FTE10072,
                gray: getMessage.FTE10073,
                cool: getMessage.FTE10074,
                cute: getMessage.FTE10075,
                natural: getMessage.FTE10076,
                gorgeous: getMessage.FTE10077,
                oase: getMessage.FTE10078,
                epoch: getMessage.FTE10079,
                darkmode: getMessage.FTE10080,
            };

            const restUser = cmn.storage.get('restUser', 'session'),
                  uiSettingData = ( restUser && restUser.web_table_settings )? restUser.web_table_settings: {},
                  theme = ( uiSettingData && uiSettingData.ui )? uiSettingData.ui.theme: '';

            const select = [];
            for ( const key in themeList ) {
                const selected = ( theme === key )? ' selected': '';
                select.push(`<option value="${key}"${selected}>${themeList[key]}</option>`);
            }

            const filterList = function( type = 'html') {
                // [ 名称, className, min, max, 単位, 初期値 ]
                const list = {
                    grayscale: [ getMessage.FTE10082, 'displaySettingGrayScale', 0, 100, '%', 0 ],
                    sepia: [ getMessage.FTE10083, 'displaySettingSepia', 0, 100, '%', 0 ],
                    brightness: [ getMessage.FTE10084, 'displaySettingBrightness', 50, 150, '%', 100 ],
                    contrast: [ getMessage.FTE10085, 'displaySettingContrast', 50, 150, '%', 100 ],
                    saturate: [ getMessage.FTE10086, 'displaySettingSaturate', 10, 200, '%', 100 ],
                    huerotate: [ getMessage.FTE10087, 'displaySettingHueRotate', 0, 360, 'Deg', 0 ],
                    invert: [ getMessage.FTE10088, 'displaySettingInvert', 0, 100, '%', 0 ],
                };
                if ( type !== 'reset') {
                    let html = '';
                    for ( const key in list ) {
                        const value = ( uiSettingData && uiSettingData.ui && uiSettingData.ui.filter )? uiSettingData.ui.filter[ key ]: list[key][5];
                        html += ``
                        + `<tr class="commonInputTr">`
                            + `<th class="commonInputTh"><div class="commonInputTitle">${list[key][0]}</div></th>`
                            + `<td class="commonInputTd">${fn.html.inputFader('displaySettingColor', value, list[key][1], { min: list[key][2], max: list[key][3], type: key }, { after: list[key][4] })}</td>`
                        + `</tr>`;
                    }
                    return html;
                } else {
                    for ( const key in list ) {
                        $(`#${list[key][1]}`).val( list[key][5] ).trigger('input');
                    }
                }
            };

            const html = ``
            + `<div class="commonSection">`
                + `<div class="commonTitle">${getMessage.FTE10063}</div>`
                + `<div class="commonBody"><div class="commonInputGroup" data-type="theme">`
                    + `<table class="commonInputTable">`
                        + `<tbody class="commonInputTbody">`
                            + `<tr class="commonInputTr">`
                                + `<th class="commonInputTh"><div class="commonInputTitle">${getMessage.FTE10064}</div></th>`
                                + `<td class="commonInputTd"><select class="displaySettingTheme input select" data-type="theme">${select.join('')}</select></td>`
                            + `</tr>`
                        + `</tbody>`
                    + `</table></div>`
                + `</div>`
                + `<div class="commonTitle">${getMessage.FTE10081}</div>`
                + `<div class="commonBody"><div class="commonInputGroup" data-type="filter">`
                    + `<table class="commonInputTable">`
                        + `<tbody class="commonInputTbody">`
                            + filterList()
                        + `</tbody>`
                    + `</table></div>`
                + `</div>`
                + `<div class="commonBody"><ul class="commonMenuList">`
                    + `<li class="commonMenuItem">`
                        + fn.html.button(`${fn.html.icon('return')} ${getMessage.FTE10094}`, ['itaButton', 'commonButton displaySettingReset'], { action: 'normal', style: `width:100%`})
                    + `</li>`
                + `</ul></div>`
            + `</div>`;

            const config = {
                mode: 'modeless',
                position: 'center',
                header: {
                    title: getMessage.FTE10061
                },
                footer: {
                    button: {
                        ok: { text: getMessage.FTE10038, action: 'positive', className: 'dialogPositive',  style: `width:200px`},
                        cancel: { text: getMessage.FTE10043, action: 'normal'}
                    }
                }
            };
            uiSettingInstance = new Dialog( config, funcs );
            uiSettingInstance.open( html );

            const $body = uiSettingInstance.$.dbody;

            // 反映ボタン
            $body.find('.input').on('change', function(){
                uiSettingInstance.buttonPositiveDisabled( false );
            });

            // テーマ変更
            $body.find('.displaySettingTheme').on('change', function(){
                cmn.setTheme( $( this ).val() );
            });

            // フェーダー
            $body.find('.inputFaderWrap').each(function(){
                cmn.faderEvent( $( this ) );
            });

            // フィルター
            const setFilterevent = function() {
                $body.find('.displaySettingColor').on('change.filter', function(){
                    cmn.setFilter( getFilterValue() );
                });
            };
            const removeFitlerEvent = function() {
                $body.find('.displaySettingColor').off('change.filter');
            }
            setFilterevent();

            // フィルターリセット
            $body.find('.displaySettingReset').on('click', function(){
                removeFitlerEvent();
                filterList('reset');
                cmn.setFilter( getFilterValue() );
                setFilterevent();
                uiSettingInstance.buttonPositiveDisabled( false );
            })

        } else {
            uiSettingInstance.btnFn = funcs;
            uiSettingInstance.show();
        }
    });
},

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//  テキストエディター
//
////////////////////////////////////////////////////////////////////////////////////////////////////

/*
##################################################
   BASE64をテキストに変換
##################################################
*/
base64Decode: function( base64Text, charset = 'utf-8') {
    return fetch(`data:text/plain;charset=${charset};base64,${base64Text}`).then(function( result ) {
        return result.text();
    });
},
/*
##################################################
   テキストをBASE64に変換
##################################################
*/
base64Encode: function( text ) {
    return new Promise(function( resolve ){
        const reader = new FileReader();
        reader.onload = function(){
            resolve( reader.result.split(';base64,')[1] );
        };
        reader.readAsDataURL( new Blob([text]) );
    });
},
/*
##################################################
   ファイルをテキストに変換
##################################################
*/
fileToText: function( file ) {
    return new Promise(function( resolve ){
        const reader = new FileReader();
        reader.onload = function(){
            resolve( reader.result );
        };
        reader.readAsText( file );
    });
},
/*
##################################################
   ファイルをBASE64に変換
##################################################
*/
fileToBase64: function( file ) {
    return new Promise(function( resolve ){
        const reader = new FileReader();
        reader.onload = function(){
            resolve( reader.result.split(';base64,')[1] );
        };
        reader.readAsDataURL( file );
    });
},
/*
##################################################
   テキストをファイルに変換
##################################################
*/
textToFile: function( text, fileName ) {
    return new File([text], fileName, { type: 'text/plain'} );
},
/*
##################################################
   BASE64をファイルに変換
##################################################
*/
base64ToFile: function( base64, fileName ) {
    if ( cmn.typeof( base64 ) !== 'string') return null;
    const
    bin = atob( base64.replace(/^.*,/, '')),
    length = bin.length,
    buffer = new Uint8Array( length );

    for (let i = 0; i < length; i++) {
        buffer[i] = bin.charCodeAt(i);
    }
    return  new File([buffer.buffer], fileName );
},
/*
##################################################
   ファイルタイプ拡張子
##################################################
*/
fileTypeCheck: function( fileName ) {
    const extension = cmn.cv( fileName.split('.').pop(), '');

    const fileTypes = {
        image: ['gif','jpe','jpg','jpeg','png','svg','webp','bmp','ico'],
        text: ['txt','yaml','yml','json','hc','hcl','tf','sentinel','py','j2','css','html','htm']
    }

    for ( const fileType in fileTypes ) {
        if ( fileTypes[fileType].indexOf( extension ) !== -1 ) {
            return fileType;
        }
    }
    return false;
},
/*
##################################################
   独自メニューファイルタイプ拡張子
##################################################
*/
customMenufileTypeCheck: function( fileName ) {
    const extension = cmn.cv( fileName.split('.').pop(), '');

    const fileTypes = {
        image: ['gif','jpe','jpg','jpeg','png','svg','webp','bmp','ico'],
        text: ['txt','yaml','yml','json','hc','hcl','tf','sentinel','py','j2','html','htm'],
        style: ['css'],
        script: ['js']
    }

    for ( const fileType in fileTypes ) {
        if ( fileTypes[fileType].indexOf( extension ) !== -1 ) {
            return fileType;
        }
    }
    return false;
},
/*
##################################################
   画像ファイルのMIMEタイプ
##################################################
*/
imageMimeTypeCheck: function( fileName ) {
    const extension = cmn.cv( fileName.split('.').pop(), '');

    const fileTypes = {
        'png': ['png'],
        'jpeg': ['jpe','jpg','jpeg'],
        'gif': ['gif'],
        'vnd.microsoft.icon': ['ico'],
        'webp': ['webp'],
        'svg+xml': ['svg'],
    }

    for ( const mimeType in fileTypes ) {
        if ( fileTypes[mimeType].indexOf( extension ) !== -1 ) {
            return mimeType;
        }
    }
    return '';
},
/*
##################################################
   Aceエディターモードチェック
##################################################
*/
fileModeCheck: function( fileName ) {
    const extension = cmn.cv( fileName.split('.').pop(), '');

    const fileTypes = {
        yaml: ['yaml','yml'],
        terraform: ['hc', 'hcl', 'sentinel', 'tf'],
        python: ['j2','py'],
        json: ['json'],
        text: ['txt'],
    };

    for ( const fileType in fileTypes ) {
        if ( fileTypes[fileType].indexOf( extension ) !== -1 ) {
            return fileType;
        }
    }
    return 'text';
},
/*
##################################################
   ITA独自変数一覧
##################################################
*/
itaOriginalVariable: function() {
    return [
        '__loginprotocol__',
        '__loginpassword__',
        '__inventory_hostname__',
        '__workflowdir__',
        '__conductor_workflowdir__',
        '__operation__',
        '__parameters_dir_for_epc__',
        '__parameters_file_dir_for_epc__',
        '__parameter_dir__',
        '__parameters_file_dir__',
        '__movement_status_filepath__',
        '__conductor_id__',
        '__dnshostname__',
        '__ipaddress__'
    ];
},
/*
##################################################
   ファイル or BASE64をテキストに変換
##################################################
*/
fileOrBase64ToText: function( data ) {
    return new Promise(function( resolve ){
        if ( cmn.typeof( data ) === 'file') {
            cmn.fileToText( data ).then(function( result ){
                resolve( result );
            }).catch(function( error ){
                resolve('');
            });
        } else if ( data === '') {
            resolve('');
        } else {
            cmn.base64Decode( data ).then(function( result ){
                resolve( result );
            }).catch(function( error ){
                resolve( data );
            });
        }
    });
},
/*
##################################################
   ファイル or BASE64をチェックしBASE64を返す
##################################################
*/
fileOrBase64ToBase64: function( data ) {
    return new Promise(function( resolve ){
        if ( cmn.typeof( data ) === 'file') {
            cmn.fileToBase64( data ).then(function( result ){
                resolve( result );
            }).catch(function( error ){
                resolve('');
            });
        } else {
            resolve( data );
        }
    });
},
/*
##################################################
   Aceエディター
##################################################
*/
fileEditor: function( fileData, fileName, mode = 'edit', option = {} ) {
    return new Promise( function( resolve ){
        const fileType = cmn.fileTypeCheck( fileName );
        let fileMode = cmn.fileModeCheck( fileName );

        // モーダル設定
        const height = ( mode === 'edit' && fileType === false )? 'auto': '100%';
        const config = {
            position: 'center',
            width: '960px',
            height: height,
            header: {
                title: cmn.cv( fileName, '', true ),
            },
            footer: {
                button: {}
            }
        };
        // モーダルボタン
        const funcs = {};

        // 編集モード
        if ( mode === 'edit') {
            config.footer.button.update = { text: getMessage.FTE00168, action: 'positive', width: '160px'};
        }

        config.footer.button.download = { text: getMessage.FTE00169, action: 'restore', width: '88px'};
        config.footer.button.close = { text: getMessage.FTE00170, action: 'normal', width: '88px'};
        funcs.close = function() {
            modal.close();
            modal = null;

            resolve( null );
        };

        const modeSelectList = {
            text: 'Text(txt)',
            yaml: 'YAML(yaml,yml)',
            terraform: 'Terraform(tf,hc,hcl,sentinel)',
            json: 'JSON(json)',
            python: 'Python(py,j2)'
        };

        const themeSelectList = {
            chrome: 'Bright',
            monokai: 'Dark'
        };

        const modalHtmlSelect = function() {
            let html = ``;

            const nameInputTr = `<tr class="commonInputTr">`
                + `<th class="commonInputTh">`
                    + `<div class="commonInputTitle">${getMessage.FTE00171}</div>`
                + `</th><td class="commonInputTd" colspan="3">`
                    + cmn.html.inputText('editorFileName', '', 'editorFileName')
                + `</td>`
            + `</tr>`;

            const modeSelectTr = `<tr class="commonInputTr">`
                + `<th class="commonInputTh">`
                    + `<div class="commonInputTitle">${getMessage.FTE00172}</div>`
                + `</th><td class="commonInputTd">`
                    + cmn.html.select( modeSelectList, 'editorModeSelect', '', 'editorModeSelect')
                + `</td>`
                + `<th class="commonInputTh">`
                    + `<div class="commonInputTitle">${getMessage.FTE00173}</div>`
                + `</th><td class="commonInputTd">`
                    + cmn.html.select( themeSelectList, 'editorThemeSelect', '', 'editorThemeSelect')
                + `</td>`
            + `</tr>`;

            if ( mode === 'edit') {
                html += `<div class="editorHeader"><table class="commonInputTable">${nameInputTr}`;
                if ( fileType === 'text') {
                    html += modeSelectTr;
                }
                html += `</table></div>`;
            } else if ( fileType === 'text') {
                html += `<div class="editorHeader"><table class="commonInputTable">${modeSelectTr}</table></div>`;
            }

            if ( fileType === 'text') {
                html += `<div id="aceEditor" class="editorBody"></div>`;
            } else if ( fileType === 'image') {
                html += `<div class="editorImageBody editorBody"><img class="editorImage"></div>`;
            }
            return `<div class="fileEditor">${html}</div>`;
        };

        let modal = new Dialog( config, funcs );
        modal.open();

        if ( fileType === 'text') {
            if ( fileData === null ) fileData = '';
            cmn.fileOrBase64ToText( fileData ).then(function( text ){
                modal.setBody( modalHtmlSelect() );
                if ( mode === 'edit') {
                    modal.$.dbody.find('.editorFileName').val( fileName );
                }
                modal.$.dbody.find('.editorBody').text( text );
                cmn.removeDownloadTemp();

                // Ace editor
                const storageTheme = fn.storage.get('editorTheme', 'local', false ),
                      aceTheme = ( storageTheme )? storageTheme: ( $('body').is('.darkmode') )? 'monokai': 'chrome';

                const langTools = ace.require('ace/ext/language_tools');

                const aceEditor = ace.edit('aceEditor', {
                    theme: `ace/theme/${aceTheme}`,
                    mode: `ace/mode/${fileMode}`,
                    displayIndentGuides: true,
                    fontSize: '14px',
                    minLines: 2,
                    showPrintMargin: false,
                    readOnly: ( mode !== 'edit' ),
                    wrapBehavioursEnabled: false,
                    enableBasicAutocompletion: true,
                    enableLiveAutocompletion: true
                });
                modal.$.dbody.find('.ace_scrollbar').addClass('commonScroll');

                // Ace editor mode
                modal.$.dbody.find('.editorModeSelect').val( modeSelectList[fileMode] ).on('change', function() {
                    const value = $( this ).val();
                    for ( const mode in modeSelectList ) {
                        if ( modeSelectList[ mode ] === value ) {
                            fileMode = mode;
                            aceEditor.session.setMode(`ace/mode/${mode}`);
                            break;
                        }
                    }
                });

                // Ace editor theme
                modal.$.dbody.find('.editorThemeSelect').val( themeSelectList[aceTheme] ).on('change', function() {
                    const value = $( this ).val();
                    for ( const theme in themeSelectList ) {
                        if ( themeSelectList[ theme ] === value ) {
                            aceEditor.setTheme(`ace/theme/${theme}`);
                            fn.storage.set('editorTheme', theme, 'local', false );
                            break;
                        }
                    }
                });

                // 端で折り返す
                aceEditor.session.setUseWrapMode( true );

                // ITA独自変数
                const rhymeCompleter = {
                    getCompletions: function( editor, session, pos, prefix, callback ) {
                        callback( null, cmn.itaOriginalVariable().map(function( val ){
                            return { value: val, meta: getMessage.FTE00174 };
                        }));
                    }
                };
                langTools.addCompleter(rhymeCompleter);

                // ダウンロード
                modal.btnFn.download = function() {
                    const value = aceEditor.getValue();

                    cmn.base64Encode( value ).then(function( base64 ){
                        if ( mode === 'edit') {
                            fileName = modal.$.dbody.find('.editorFileName').val();
                        }
                        cmn.download('base64', base64, fileName );
                    });
                };

                // 変更時
                aceEditor.session.on('change', function(){
                    // yamlチェック
                    if ( fileMode === 'yaml') {
                        const value = aceEditor.getValue(),
                              session = aceEditor.getSession();
                        try {
                            const result = jsyaml.load( value );
                            session.setAnnotations([]);
                        } catch( error ) {
                            session.setAnnotations([{
                                row: error.mark.line,
                                column: error.mark.column,
                                text: error.reason,
                                type: "error"
                            }]);
                        }
                    }
                });

                // 更新
                modal.btnFn.update = function() {
                    const value = aceEditor.getValue();

                    fileName = modal.$.dbody.find('.editorFileName').val();
                    modal.close();
                    modal = null;

                    resolve({
                        name: fileName,
                        file: cmn.textToFile( value, fileName )
                    });
                };
            });
        } else if ( fileType === 'image') {
            if ( fileData === null ) fileData = '';
            cmn.fileOrBase64ToBase64( fileData ).then(function( base64 ){
                // ダウンロード
                modal.btnFn.download = function() {
                    if ( mode === 'edit') {
                        fileName = modal.$.dbody.find('.editorFileName').val();
                    }
                    cmn.download('base64', base64, fileName );
                };

                modal.setBody( modalHtmlSelect() );
                if ( mode === 'edit') {
                    modal.$.dbody.find('.editorFileName').val( fileName );

                    // 更新
                    modal.btnFn.update = function() {
                        fileName = modal.$.dbody.find('.editorFileName').val();
                        modal.close();
                        modal = null;

                        resolve({
                            name: fileName,
                            file: cmn.base64ToFile( base64, fileName )
                        });
                    };
                }

                // imageの場合画像をセットする
                if ( fileType === 'image') {
                    const
                    mime = cmn.imageMimeTypeCheck( fileName ),
                    src = `data:image/${mime};base64,${base64}`;

                    modal.$.dbody.find('.editorImage').attr('src', src );
                    cmn.removeDownloadTemp();
                }
            });
        } else {
            // 編集不可ファイル
            // ファイル名のみ変更可能

            // ダウンロード
            modal.btnFn.download = async function() {
                if ( mode === 'edit') {
                    fileName = modal.$.dbody.find('.editorFileName').val();
                }
                if ( fileData !== null ) {
                    cmn.download('file', fileData, fileName );
                } else {
                    try {
                        const file = await fn.getFile( option.endPoint, 'GET', null, { title: getMessage.FTE00185 } );
                        cmn.download('file', file, fileName );
                    } catch ( e ) {
                        if ( e !== 'break') {
                            console.error( e );
                            alert( getMessage.FTE00179 );
                        }
                    }
                }
            };

            modal.setBody( modalHtmlSelect() );
            if ( mode === 'edit') {
                modal.$.dbody.find('.editorFileName').val( fileName );

                // 更新
                modal.btnFn.update = function() {
                    fileName = modal.$.dbody.find('.editorFileName').val();
                    modal.close();
                    modal = null;

                    resolve({
                        name: fileName,
                        file: fileData
                    });
                };
            }
        }
    });

},
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   画面フルスクリーン
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
   フルスクリーン
##################################################
*/
// フルスクリーンチェック
fullScreenCheck: function() {
    if (
        ( document.fullScreenElement !== undefined && document.fullScreenElement === null ) ||
        ( document.msFullscreenElement !== undefined && document.msFullscreenElement === null ) ||
        ( document.mozFullScreen !== undefined && !document.mozFullScreen ) ||
        ( document.webkitIsFullScreen !== undefined && !document.webkitIsFullScreen )
    ) {
        return false;
    } else {
        return true;
    }
},
// フルスクリーン切り替え
fullScreen: function( elem ) {
    if ( elem === undefined ) elem = document.body;

    if ( !this.fullScreenCheck() ) {
      if ( elem.requestFullScreen ) {
        elem.requestFullScreen();
      } else if ( elem.mozRequestFullScreen ) {
        elem.mozRequestFullScreen();
      } else if ( elem.webkitRequestFullScreen ) {
        elem.webkitRequestFullScreen( Element.ALLOW_KEYBOARD_INPUT );
      } else if (elem.msRequestFullscreen) {
        elem.msRequestFullscreen();
      }
    } else {
      if ( document.cancelFullScreen ) {
        document.cancelFullScreen();
      } else if ( document.mozCancelFullScreen ) {
        document.mozCancelFullScreen();
      } else if ( document.webkitCancelFullScreen ) {
        document.webkitCancelFullScreen();
      } else if ( document.msExitFullscreen ) {
        document.msExitFullscreen();
      }
    }
},

/*
##################################################
   タブ
##################################################
*/
commonTab: function( $target ) {
    $target.find('.commonTabItem').eq(0).add( $target.find('.commonTabSection').eq(0) ).addClass('open');

    $target.find('.commonTabItem').on('click', function(){
        const $item = $( this );

        if ( !$item.is('.open') ) {
            const index = $target.find('.commonTabItem').index( this );
            $target.find('.open').removeClass('open');
            $( this ).add( $target.find('.commonTabSection').eq( index ) ).addClass('open');
        }
    });
}

}; // end cmn

    // document.referrerが空の場合、WebStorageをクリア
    if ( windowFlag && !document.referrer.length ) {
        // Local storage
        const localKeys = cmn.storage.getKeys('local');
        for ( const key of localKeys ) {
            if ( key.indexOf('ita_ui_') === 0 ) {
                cmn.storage.remove( key, 'local', false );
            }
        }
        // Session storage
        const sessionKeys = cmn.storage.getKeys('session');
        for ( const key of sessionKeys ) {
            if ( key.indexOf('ita_ui_') === 0 ) {
                cmn.storage.remove( key, 'session', false );
            }
        }
    }

    // 共通パラメーター
    const commonParams = {};
    commonParams.dir = '/_/ita';
    if ( windowFlag ) {
        commonParams.path = cmn.getPathname();
        commonParams.organizationId = organization_id;
        commonParams.workspaceId = workspace_id;
    }

    return cmn;

}());

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Log
//
////////////////////////////////////////////////////////////////////////////////////////////////////
class Log {
/*
##################################################
   Constructor
##################################################
*/
constructor( id, max ) {
    const lg = this;
    lg.max = fn.cv( max, 1000 );
    lg.id = id;
}
/*
##################################################
   Setup
##################################################
*/
setup( className ) {
    const lg = this;

    const menu = {
        Main: [
            { input: { className: 'logSearchInput', before: getMessage.FTE10053 } },
            { check: { className: 'logSearchHidden', value: getMessage.FTE10053, name: lg.id + 'logSearchHidden'} }
        ],
        Sub: []
    };

    lg.searchString = '';

    const containerClassName = ['operationLogContainer'];
    if ( className ) containerClassName.push( className );

    const $log = $(`
    <div class="${containerClassName.join(' ')}"${( lg.id )? ` id="${lg.id}"`: ``}>
        ${fn.html.operationMenu( menu, 'operationLogMenu')}
        <div class="operationLogBody">
            <div class="operationLog">
                <ol class="operationLogList" data-search="">
                </ol>
            </div>
        </div>
        <div class="operationLogFooter">
            <div class="operationLogFooterInner">
                <div class="operationLogFooterBlock">
                    <dl class="operationLogFooterList">
                        <dt class="operationLogFooterTitle"><span class="operationLogFooterText">ログ行数</span></dt>
                        <dd class="operationLogFooterItem"><span class="operationLogFooterText operationLogLinesNumber">0</span></dd>
                    </dl>
                </div>
                <div class="operationLogFooterBlock">
                    <dl class="operationLogFooterList">
                        <dt class="operationLogFooterTitle"><span class="operationLogFooterText">進行状態表示行数</span></dt>
                        <dd class="operationLogFooterItem"><span class="operationLogFooterText operationLogMaxLinesNumber">${lg.max.toLocaleString()}</span></dd>
                    </dl>
                </div>
            </div>
        </div>
    </div>`);

    lg.$ = {};
    lg.$.log = $log.find('.operationLog');
    lg.$.logList = $log.find('.operationLogList');
    lg.$.max = $log.find('.operationLogMaxLinesNumber');
    lg.$.num = $log.find('.operationLogLinesNumber');
    lg.$.search = $log.find('.logSearchInput');
    lg.$.filter = $log.find('.logSearchHidden ');


    lg.$.search.on('change', function(){
        lg.searchString = $( this ).val();
        if ( lg.searchString !== '') {
            lg.regexp = new RegExp(`(${fn.regexpEscape( fn.escape( lg.searchString ) )})`, 'gi')
        } else {
            lg.regexp = null;
        }
        lg.search();
    });

    lg.$.filter.on('change', function(){
        const flag = $( this ).prop('checked');
        lg.$.logList.attr('data-filter', flag );
    });


    return $log;
}
/*
##################################################
   Log 検索
##################################################
*/
search() {
    const lg = this;

    if ( lg.$.logList.attr('data-search') !== lg.searchString ) {
        lg.$.logList.find('.operationLogItem').each(function(){
            const $list = $( this ),
                  $text = $list.find('.operationLogText'),
                  id = $text.attr('data-id'),
                  text = fn.cv( lg.logSplit[id], '', true );

            if ( lg.regexp && lg.regexp.test( text ) ) {
                $list.addClass('logSearchMatch');
                $text.html( text.replace( lg.regexp, lg.replacer ) );
            } else if ( $list.is('.logSearchMatch') ) {
                $list.removeClass('logSearchMatch');
                $text.html( text );
            }
        });
        lg.$.logList.attr('data-search', lg.searchString );
    }
}
/*
##################################################
   Log 検索置換関数
##################################################
*/
replacer( match, p1, offset, str ) {
    // Check &xxx;
    const entitieGreater = str.indexOf(';', offset ),
          entitieLesser = str.indexOf('&', offset );

    if( entitieGreater < entitieLesser || ( entitieGreater != -1 && entitieLesser == -1 ) ) {
        return match;
    } else {
        return '<span class="logSearch">' + match + '</span>';
    }
}
/*
##################################################
   Log line
##################################################
*/
logLine( id ) {
    const lg = this;

    const itemClass = ['operationLogItem'];
    let log = fn.cv( lg.logSplit[id], '', true );
    if ( lg.regexp && lg.regexp.test( log ) ) {
        log = log.replace( lg.regexp, lg.replacer );
        itemClass.push('logSearchMatch');
    }

    return `<li class="${itemClass.join(' ')}">
        <div class="operationLogNumber">${(id + 1).toLocaleString()}</div>
        <div class="operationLogText" data-id="${id}">${log}</div>
    </li>`
}
/*
##################################################
   Update
##################################################
*/
update( log ) {
    const lg = this;

    // ログを改行で分割
    lg.logSplit = log.split(/\r\n|\n/);
    lg.lines = lg.logSplit.length;

    // 最後の行が空白の場合削除
    if ( lg.logSplit[ lg.lines - 1 ] === '') {
        lg.logSplit.pop();
        lg.lines -= 1;
    }

    // 行数表示
    lg.$.num.text( lg.lines.toLocaleString() );

    // 進行状態表示行数内にする
    let start = 0;
    if ( lg.lines > lg.max ) {
        start = lg.lines - lg.max;
    }

    // HTML
    const logHtml = [];
    for ( let i = start; i < lg.lines; i++ ) {
        logHtml.push( lg.logLine( i ) );
    }

    // スクロールチェック
    const logArea = lg.$.log.get(0),
          logHeight = logArea.clientHeight,
          scrollTop = logArea.scrollTop,
          scrollHeight = logArea.scrollHeight,
          scrollFlag = ( logHeight < scrollHeight && scrollTop >= scrollHeight - logHeight )? true: false;

    lg.$.logList.html( logHtml.join('') );

    // 追加後進行状態表示行数を超えた部分を削除
    if ( lg.lines > lg.max ) {
        const itemLength = lg.$.logList.find('.operationLogItem').length;
        lg.$.logList.find('.operationLogItem').slice( 0, itemLength - lg.max ).remove();
    }

    // 検索
    lg.search();

    // 追加後にスクロール可能になった場合スクロール
    // 最下部にいる場合のみ追加分スクロール
    const afterScrollHeight = logArea.scrollHeight;
    if ( ( logHeight === scrollHeight && logHeight < afterScrollHeight ) || scrollFlag ) {
        lg.$.log.animate({ scrollTop:  afterScrollHeight - logHeight }, 200 );
    }
}
/*
##################################################
   Update
##################################################
*/
clear() {
    const lg = this;
    lg.logSplit = null;
    lg.lines = 0;
    lg.searchString = '';
    lg.regexp = null;

    lg.$.num.text( 0 );
    lg.$.logList.empty();
}

}

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Message
//
////////////////////////////////////////////////////////////////////////////////////////////////////
class Message {
/*
##################################################
   Constructor
##################################################
*/
constructor( type, title, message, icon, closeTime = 5000 ) {
    const ms = this;

    ms.$ = {};
    ms.$.window = $( window );
    ms.$.body = $('body');

    ms.message = {};
    ms.number = 0;
}
/*
##################################################
   Open
##################################################
*/
add( type, title, message, icon, closeTime = 5000 ) {
    const ms = this;

    const num = ms.number++;
    ms.message[ num ] = {};

    if ( !icon ) {
        switch ( type ) {
            case 'success': icon = 'check'; break;
            case 'warning': icon = 'attention'; break;
            case 'danger': icon = 'attention'; break;
            case 'unkown': icon = 'circle_question'; break;
            default: icon = 'circle_info';
        }
    }

    // Container
    if ( !fn.exists('#messageContainer') ) {
        ms.$.body.append('<div id="messageContainer"></div>');
    }

    const html = [];
    html.push(`<div class="messageTime">${fn.date( new Date(), 'yyyy/MM/dd HH:mm:ss')}</div>`);
    if ( icon ) html.push(`<div class="messageIcon">${fn.html.icon( icon )}</div>`);
    if ( title ) html.push(`<div class="messageTitle">${fn.escape( title )}</div>`);
    if ( message ) html.push(`<div class="messageBody">${message}</div>`);
    html.push(`<div class="messageClose"><button class="messageCloseButton">${fn.html.icon('cross')}</button></div>`
    + `<div class="messageTimer"><div class="messageTimerBar"></div></div>`);

    ms.message[ num ].$ = $(`<div class="messageItem" data-message="${type}">${html.join('')}</div>`);
    $('#messageContainer').append( ms.message[ num ].$ );

    if ( closeTime !== 0 ) {
        ms.message[ num ].$.find('.messageTimerBar').animate({width: '100%'}, closeTime );
        ms.message[ num ].timer = setTimeout(function(){
            ms.close( num );
        }, closeTime );
    } else {
        ms.message[ num ].$.find('.messageTimer').addClass('messageTimerZero');
    }

    ms.message[ num ].$.find('.messageCloseButton').on('click', function(){
        if ( ms.message[ num ].timer ) clearTimeout( ms.message[ num ].timer );
        ms.close( num );
    });
}
/*
##################################################
   Close
##################################################
*/
close( number ) {
    const ms = this;
    ms.message[ number ].$.fadeOut( 300 );
    delete ms.message[ number ];

    /*
    ms.$.message.fadeOut( 300, function(){
        ms.$.message.remove();

        if ( !ms.$.container.find('.messageItem').length ) {
            ms.$.container.remove();
        }
    });
    */
}
/*
##################################################
   Clear
##################################################
*/
clear() {
    const ms = this;
    for ( const key in ms.message ) {
        ms.close( key );
    }
}

}