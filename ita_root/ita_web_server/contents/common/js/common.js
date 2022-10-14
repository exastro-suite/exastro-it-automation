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
    
    // インスタンス管理用
    const modalInstance = {},
          operationInstance = {},
          conductorInstance = {};
    let messageInstance = null;
    
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
    
    // iframeフラグ
    const iframeFlag = windowFlag? ( window.parent !== window ): false;
    
    const organization_id = ( windowFlag )? CommonAuth.getRealm(): null,
          workspace_id =  ( windowFlag )? window.location.pathname.split('/')[3]: null;
    
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
                const attrName = ['checked', 'disabled', 'title', 'placeholder', 'style', 'class']; // dataをつけない
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
   script, styleの読み込み
##################################################
*/
loadAssets: function( assets ){
    const f = function( type, url ){
        return new Promise(function( resolve, reject ){
            type = ( type === 'css')? 'link': 'script';
            
            const body = document.body,
                  asset = document.createElement( type );
            
            switch ( type ) {
                case 'script':
                    asset.src = url;
                break;
                case 'link':
                    asset.href = url;
                    asset.rel = 'stylesheet';
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
                return f( asset.type, asset.url );
            })
        );
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
fetch: function( url, token, method = 'GET', json ) {
    
    if ( !token ) {
        token = CommonAuth.getToken();
    }
    
    let errorCount = 0;
    
    const f = function( u ){
        return new Promise(function( resolve, reject ){
            
            if ( windowFlag ) u = cmn.getRestApiUrl( u );
            
            const init = {
                method: method,
                headers: {
                  'Authorization': `Bearer ${token}`,
                  'Content-Type': 'application/json'
                }
            };
            
            if ( ( method === 'POST' || method === 'PATCH' ) && json !== undefined ) {            
                try {
                    init.body = JSON.stringify( json );
                } catch ( e ) {
                    reject( e );
                }
            }
            
            fetch( u, init ).then(function( response ){
                if ( errorCount === 0 ) {
                    
                    if( response.ok ) {
                        //200の場合
                        response.json().then(function( result ){                            
                            resolve( result.data );
                        });
                    } else {
                        errorCount++;
                        
                        switch ( response.status ) {
                            //バリデーションエラーは呼び出し元に返す
                            case 499:
                                response.json().then(function( result ){
                                    reject( result );
                                }).catch(function( e ) {
                                    cmn.systemErrorAlert();
                                });
                            break;
                            // 権限無しの場合、トップページに戻す
                            case 401:
                                response.json().then(function( result ){
                                    if ( !iframeFlag ) {
                                        alert(result.message);
                                        location.replace('/' + organization_id + '/workspaces/' + workspace_id + '/ita/');
                                    } else {
                                        cmn.iframeMessage( result.message );
                                    }
                                }).catch(function( e ) {
                                    cmn.systemErrorAlert();
                                });
                            break;
                            // ワークスペース一覧に飛ばす
                            case 403:
                                response.json().then(function( result ){
                                    if ( !iframeFlag ) {
                                        alert(result.message);
                                        window.location.href = `/${organization_id}/platform/workspaces`;
                                    } else {
                                        cmn.iframeMessage( result.message );
                                    }
                                }).catch(function( e ) {
                                    cmn.systemErrorAlert();
                                });
                            break;
                            // その他のエラー
                            default:
                                cmn.systemErrorAlert();
                        }
                    }
                }
            }).catch(function( error ){
                if ( errorCount === 0 ) {
                    reject( error );
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
    
    flag.insert = ( menuInfo.row_insert_flag === '1')? true: false;
    flag.update = ( menuInfo.row_update_flag === '1')? true: false;
    flag.disuse = ( menuInfo.row_disuse_flag === '1')? true: false;
    flag.reuse = ( menuInfo.row_reuse_flag === '1')? true: false;
    flag.edit = ( menuInfo.row_insert_flag === '1' && menuInfo.row_update_flag === '1')? true: false;
    
    return flag;
},
/*
##################################################
   0埋め
##################################################
*/
zeroPadding: function( num, digit ){
    let zeroPaddingNumber = '0';
    for ( let i = 1; i < digit; i++ ) {
      zeroPaddingNumber += '0';
    }
    zeroPaddingNumber += String( num );
    return zeroPaddingNumber.slice( -digit );
},
/*
##################################################
   空値チェック
##################################################
*/
cv: function( value, subValue, escape ){
    const type = typeofValue( value );
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
   正規表現文字列エスケープ
##################################################
*/
regexpEscape: function( value ) {
    return value.replace(/[.*+\-?^${}()|[\]\\]/g, '\\$&');
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
   ダウンロード
##################################################
*/
download: function( type, data, fileName = 'noname') {
    
    let url;
    
    // URL形式に変換
    try {
        switch ( type ) {
        
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
                
        }
    } catch ( e ) {
        window.console.error( e );
    }
    
    const a = document.createElement('a');

    a.href = url;
    a.download = fileName;
    a.click();
    
    if ( type !== 'base64') URL.revokeObjectURL( url );

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

            if ( limitFileSize && file.size >= limitFileSize ) {
                reject('File size limit over.');
                return false;
            }
            
            if ( type === 'base64') {
                reader.readAsDataURL( file );

                reader.onload = function(){
                    resolve({
                        base64: reader.result.replace(/^data:.*\/.*;base64,|^data:$/, ''),
                        name: file.name,
                        size: file.size
                    });
                };

                reader.onerror = function(){
                    reject( reader.error );
                };
            } else if ( type === 'file') {
                const formData = new FormData();
                formData.append('file', file );
                resolve( formData );
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
    'set': function( key, value, type ) {
        if ( type === undefined ) type = 'local';
        key = cmn.createStorageKey( key );
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
    'get': function( key, type ) {
        if ( type === undefined ) type = 'local';
        key = cmn.createStorageKey( key );
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
    'remove': function( key, type ) {
        if ( type === undefined ) type = 'local';
        key = cmn.createStorageKey( key );
        const storage = ( type === 'local')? localStorage: ( type === 'session')? sessionStorage: undefined;
        if ( storage !== undefined ) {
            storage.removeItem( key )
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
    key = `${organization_id}_${workspace_id}_${key}`;
    return key;
},
/*
##################################################
   Alert, Confirm
##################################################
*/
alert: function( title, elements, type = 'alert', buttons = { ok: { text: getMessage.FTE10043, action: 'normal'}} ) {
    return new Promise(function( resolve ){
        const funcs = {};
        
        funcs.ok = function(){
            dialog.close();
            dialog = null;
            resolve( true );
        };
        if ( type === 'confirm') {
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
            footer: {
                button: buttons
            }
        };
        let dialog = new Dialog( config, funcs );
        dialog.open(`<div class="alertMessage">${elements}</div>`);
        
        setTimeout(function(){
            if ( dialog ) {
                dialog.buttonPositiveDisabled( false );
            }
        }, 500 )
    });
},
iconConfirm: function( icon, title, elements ) {
    elements = `
    <div class="alertMessageIconBlock">
        <div class="alertMessageIcon">${cmn.html.icon( icon )}</div>
        <div class="alertMessageBody">${cmn.escape( elements, true )}</div>
    </div>`;
    return cmn.alert( title, elements , 'confirm', {
        ok: { text: getMessage.FTE10058, action: 'default', style: 'width:120px', className: 'dialogPositive'},
        cancel: { text: getMessage.FTE10026, action: 'negative', style: 'width:120px'}
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
        const datePickerTime = [`<div class="datePickerHour">${cmn.html.inputFader('datePickerHourInput', hour, null, { min: 0, max: 23 }, { after: '時'} )}</div>`];
        if ( timeFlag === 'true' || timeFlag === true || timeFlag === 'hms' || timeFlag === 'hm') {
            datePickerTime.push(`<div class="datePickerMin">${cmn.html.inputFader('datePickerMinInput', min, null, { min: 0, max: 59 }, { after: '分'} )}</div>`);
        }
        if ( timeFlag === 'true' || timeFlag === true || timeFlag === 'hms') {
            datePickerTime.push(`<div class="datePickerSec">${cmn.html.inputFader('datePickerSecInput', sec, null, { min: 0, max: 59 }, { after: '秒'} )}</div>`);
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
   Date picker dialog
##################################################
*/
datePickerDialog: function( type, timeFlag, title, date ){
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
            $dataPicker.html( cmn.datePicker( timeFlag, 'datePickerDateText', date ) );
        }
        
        dialog.open( $dataPicker );
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
          $tooltip = $fader.find('.inputFaderRangeTooltip'),
          min = Number( $input.attr('data-min') ),
          max = Number( $input.attr('data-max') ),
          inputRange = max - min;

    let   width = $fader.width(),
          val = $input.val(),
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

    $input.on('input', function(){
      val = $input.val();
      width = $fader.width();
      if ( val !== '') {
        if ( val < min ) {
          $input.val( min ).change();
          val = min;
        }
        if ( val > max ) {
          $input.val( max ).change();
          val = max;
        }
      } else {
        val = '';
      }
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
        
        attr.push(`class="${className.join(' ')}"`);
        return `<button ${attr.join(' ')}><span class="inner">${html.join('')}</span></button>`;
    },
    iconButton: function( icon, element, className, attrs = {}, option = {}) {
        const html = `${cmn.html.icon( icon, 'iconButtonIcon')}<span class="iconButtonBody">${element}</span>`;
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
    checkboxText: function( className, value, name, id, attrs = {}) {
        const attr = inputCommon( value, name, attrs, id );
        attr.push(`class="${classNameCheck( className, 'checkboxText').join(' ')}"`);
        
        return ``
        + `<div class="checkboxTextWrap">`
            + `<input type="checkbox" ${attr.join(' ')}>`
            + `<label for="${id}" class="checkboxTextLabel"><span class="checkboxTextMark"></span>${value}</label>`
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
    'select': function( list, className, value, name, attrs = {}, option = {}) {
        const selectOption = [],
              attr = inputCommon( null, name, attrs );
        
        if ( !option.select2 === true ) {
            className = classNameCheck( className, 'select input');
        } else {
            className = classNameCheck( className );
        }
        attr.push(`class="${className.join(' ')}"`);
        
        // 必須じゃない場合空白を追加
        if ( attrs.required === '0') {
            selectOption.push(`<option value=""></option>`);
        }
        
        for ( const key in list ) {
            const val = cmn.escape( list[ key ] ),
                  optAttr = [`value="${val}"`];
            if ( value === val ) optAttr.push('selected', 'selected');
            selectOption.push(`<option ${optAttr.join(' ')}>${val}</option>`);
        }
        
        return ``
        + `<select ${attr.join(' ')}>`
            + selectOption.join('')
        + `</select>`;
    },
    'noSelect': function() {
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
    fileSelect: function( value, className, attrs = {}, option = {}) {
        className = classNameCheck( className, 'inputFile');

        let file = ''
        + `<div class="inputFileBody">`
                + cmn.html.button( value, className, attrs )
        + `</div>`
        + `<div class="inputFileClear">`
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
            itemHtml.push( cmn.html.inputText( inputClass, input.value, null, null, inputOption ) );            
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
            + `<span class="operationMenuMessageText">${item.message.text}</span></div>`)
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
    }
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
errorModal: function( error, pageName ) {
    return new Promise(function( resolve ){
        let errorMessage;
        try {
            errorMessage = JSON.parse(error.message);
        } catch ( e ) {
            //JSONを作成
            errorMessage = {"0":{"共通":[error.message]}};
        }
        const errorHtml = [];
        for ( const item in errorMessage ) {
            for ( const error in errorMessage[item] ) {
                const number = Number( item ) + 1,
                      name = cmn.cv( error, '', true ),
                      body = cmn.cv( errorMessage[item][error].join(''), '?', true );

                errorHtml.push(`<tr class="tBodyTr tr">`
                + cmn.html.cell( number, ['tBodyTh', 'tBodyLeftSticky'], 'th')
                + cmn.html.cell( name, 'tBodyTd')
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
                        <th class="tHeadTh th"><div class="ci">${getMessage.FTE10043}</div></th>
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

            const $p = $('<div/>', {
                'class': 'popupBlock',
                'html': fn.escape( ttl, true )
            }).append('<div class="popupArrow"><span></span></div>');
            
            const $arrow = $p.find('.popupArrow');
            
            if( $t.is('.darkPopup') ) $p.addClass('darkPopup');
            
            $body.append( $p );

            const r = $t[0].getBoundingClientRect(),
                  m = 8,
                  wW = $window.width(),
                  tW = $t.outerWidth(),
                  tH = $t.outerHeight(),
                  tL = r.left,
                  tT = r.top,
                  pW = $p.outerWidth(),
                  pH = $p.outerHeight(),
                  wsL = $window.scrollLeft();

            let l = ( tL + tW / 2 ) - ( pW / 2 ) - wsL,
                t = tT - pH - m;

            if ( t <= 0 ) {
                $p.addClass('popupBottom');
                t = tT + tH + m;
            } else {
                $p.addClass('popupTop');
            }
            if ( wW < l + pW ) l = wW - pW - m;
            if ( l <= 0 ) l = m;

            $p.css({
                'width': pW,
                'height': pH,
                'left': l,
                'top': t
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
                aL = ( tL + ( tW / 2 )) - l - wsL;
            }
            $arrow.css('left', aL );

            if ( $t.is('.popupHide') ) {
                $p.addClass('popupHide');
            }

            $t.on('pointerleave.popup', function(){
                const $p = $body.find('.popupBlock'),
                      title = ttl;
                $p.remove();
                $t.off('pointerleave.popup click.popup').attr('title', title );
            });
            
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
      title: モーダルタイトル、ボタンテキスト
      selectNameKey: 選択で返す名称Key
      info: Table構造info URL
      infoData: Table構造infoが取得済みの場合はこちらに
      filter: Filter URL
      filterPulldown: Filter pulldown URL
      sub: infoに複数のTable構造がある場合のKey
  }
##################################################
*/
selectModalOpen: function( modalId, title, menu, config ) {
    return new Promise(function( resolve, reject ){
        const modalFuncs = {
            ok: function() {
                modalInstance[ modalId ].modal.hide();   
                const selectId = modalInstance[ modalId ].table.select.select;
                resolve( selectId );
            },
            cancel: function() {
                modalInstance[ modalId ].modal.hide();
                resolve( null );
            }
        };
        
        if ( !modalInstance[ modalId ] ) {
            fn.initSelectModal( title, menu, config ).then(function( modalAndTable ){
                modalInstance[ modalId ] = modalAndTable;
                modalInstance[ modalId ].modal.btnFn = modalFuncs;
            });
        } else {
            modalInstance[ modalId ].modal.show();
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
initSelectModal: function( title, menu, selectConfig ) {
    
    return new Promise(function( resolve, reject ) {
        const modalConfig = {
            mode: 'modeless',
            width: 'auto',
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
            
            // 取得したinfoのSubキー確認
            if ( selectConfig.sub ) info = info[ selectConfig.sub ];

            const tableId = `SE_${menu.toUpperCase()}${( selectConfig.sub )? `_${selectConfig.sub}`: ``}`,
                  table = new DataTable( tableId, 'select', info, params );
            modal.setBody( table.setup() );
            
            // 選択チェック
            table.$.container.on(`${table.id}selectChange`, function(){
                if ( table.select.select.length ) {
                    modal.buttonPositiveDisabled( false);
                } else {
                    modal.buttonPositiveDisabled( true );
                }
            });
            
            // 初期表示の場合は読み込み完了後に表示
            $( window ).one( tableId + '__tableReady', function(){
                processingModal.close();
                modal.hide();
                modal.$.dialog.removeClass('hiddenDialog');
                modal.show();
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
  作業実行
##################################################
*/
executeModalOpen: function( modalId, menu, executeConfig ) {
    return new Promise(function( resolve ){
        const funcs = {
            ok: function(){
                modalInstance[ modalId ].hide();
                resolve({
                    selectName: executeConfig.selectName,
                    selectId: executeConfig.selectId,
                    id: modalInstance[ modalId ].$.dbody.find('.executeOperetionId').text(),
                    name: modalInstance[ modalId ].$.dbody.find('.executeOperetionName').text(),
                    schedule:  modalInstance[ modalId ].$.dbody.find('.executeSchedule').val()
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
                                <td class="commonTd">${executeConfig.selectId}</td>
                            </tr>
                            <tr class="commonTr">
                                <th class="commonTh">${getMessage.FTE10055}</th>
                                <td class="commonTd">${executeConfig.selectName}</td>
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
        if ( message ) {
            window.alert( message );
        } else {
            window.alert('Unknown error.');
        }
        window.location.href = './system_error/';
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

contentLoadingStart() {
    document.body.classList.add('loading');
    contentLoadingFlag = true;
},
contentLoadingEnd() {
    document.body.classList.remove('loading');
    contentLoadingFlag = false;
},
checkContentLoading() {
    return contentLoadingFlag;
},

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   iframeモーダル
// 
////////////////////////////////////////////////////////////////////////////////////////////////////

modalIframe: function( menu, title, option = {}){
    if ( !modalInstance[ menu ] ) {
        const modalFuncs = {
            cancel: function() {
                modalInstance[ menu ] = null;
                modal.close();
            }
        };
        const modalConfig = {
            mode: 'modeless',
            width: '100%',
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
        
        const filterEncode = function( json ) {
            try {
                return encodeURIComponent( JSON.stringify( json ) );
            } catch( error ) {
                return '';
            }
        };
        
        const url = [`?menu=${menu}`];
        if ( option.filter ) {
            url.push(`&filter=${filterEncode( option.filter )}`);
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
//   画面フルスクリーン
// 
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
   フルスクリーン
##################################################
*/
// フルスクリーンチェック
fullScreenCheck() {
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
fullScreen( elem ) {
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
}

}; // end cmn



    // 共通パラメーター
    const commonParams = {};
    commonParams.dir = '/_/ita';
    if ( windowFlag ) {
        commonParams.path = cmn.getPathname();
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
    
    lg.start = 0;
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
    if ( lg.lines - lg.start > lg.max ) {
        lg.start = lg.lines - lg.max;
    }
    
    // HTML
    const logHtml = [];
    for ( let i = lg.start; i < lg.lines; i++ ) {
        logHtml.push( lg.logLine( i ) );
    }
    lg.start = lg.lines;
    
    // スクロールチェック
    const logArea = lg.$.log.get(0),
          logHeight = logArea.clientHeight,
          scrollTop = logArea.scrollTop,
          scrollHeight = logArea.scrollHeight,
          scrollFlag = ( logHeight < scrollHeight && scrollTop >= scrollHeight - logHeight )? true: false;
    
    lg.$.logList.append( logHtml.join('') );  
    
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
    if ( title ) html.push(`<div class="messageTitle">${title}</div>`);
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