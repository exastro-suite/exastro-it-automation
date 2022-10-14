////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Exastro IT Automation / table_worker.js
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

importScripts('common.js');

class TableWorker {
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
message( data ) {
    const tw = this;
    
    tw.data = data;
    
    switch ( tw.data.type ) {
        case 'filter': {
            fn.fetch( tw.data.rest.url, tw.data.rest.token, 'POST', tw.data.rest.filter ).then(function( result ){
                tw.result = result;   
                tw.sort();
                tw.setDiscardIdList();
                tw.postPageData();
            }).catch(function( error ){
                tw.postError( error );
            });
        } break;
        case 'page':
            tw.postPageData();
        break;
        case 'sort':
            tw.sort();
            tw.postPageData();
        break;
        case 'edit':
            if ( tw.data.select.length > 0 ) {
                tw.postSelectPageData();
            } else {
                tw.postPageData();
            }
        break;
        case 'add':
            tw.result.unshift( tw.data.add );
            tw.postPageData();
        break;
        case 'dup':
            tw.duplicatSelectData();
            tw.postPageData();
        break;
        case 'del':
            tw.deleteSelectData();
            tw.postPageData();
        break;
        case 'discard':
        case 'restore':
            tw.postSelectData();
        break;
        case 'normal':
            tw.result = tw.data.tableData;
            tw.postPageData();
        break;
        case 'history': {
            fn.fetch( tw.data.rest.url, tw.data.rest.token ).then(function( result ){
                tw.result = result;
                tw.historyDiff();
                tw.postPageData();
            }).catch(function( error ){
                tw.postError( error );
            });
        } break;
        case 'changeEditRegi':
            tw.result = [ tw.data.add ];
            tw.postPageData();
        break;
        case 'changeEditDup':
            tw.duplicatSelectData();
            tw.postPageData();
        break;
    }
}
/*
##################################################
   ページング情報をセット
##################################################
*/
setPagingStatus( list ) {
    const tw = this;
    
    // フィルタ結果件数
    tw.data.paging.num = list.length;
    // 最大ページ数
    tw.data.paging.pageMaxNum = Math.ceil( tw.data.paging.num / tw.data.paging.onePageNum );
    // 範囲内に調整
    if ( tw.data.paging.pageNum <= 0 ) tw.data.paging.pageNum = 1;
    if ( tw.data.paging.pageNum > tw.data.paging.pageMaxNum  ) tw.data.paging.pageNum = tw.data.paging.pageMaxNum;
    // 開始ページ
    tw.data.paging.startPageNum = ( tw.data.paging.pageNum === 0 )?
        tw.data.paging.pageNum: tw.data.paging.onePageNum * ( tw.data.paging.pageNum - 1 );
    // 終了ページ
    tw.data.paging.endPageNum = ( tw.data.paging.num > tw.data.paging.startPageNum + tw.data.paging.onePageNum - 1 )?
        tw.data.paging.startPageNum + tw.data.paging.onePageNum: tw.data.paging.num;
    // IDリストの作成
    tw.data.order = tw.result.map(function( val ){
        return val.parameter[ tw.data.idName ];
    });
}
/*
##################################################
   ソート
##################################################
*/
sort() {
    const tw = this;
    
    for ( const sort of tw.data.sort ) {
        for ( const order in sort ) {
            const name = sort[ order ],
                  flag = ( order === 'ASC')? -1: 1;
            tw.result.sort(function( a, b ){
                let paramA = fn.cv( a.parameter[ name ], ''),
                    paramB = fn.cv( b.parameter[ name ], '');
                
                if ( fn.typeof( paramA ) === 'object' ||  fn.typeof( paramA ) === 'array' ||
                     fn.typeof( paramB ) === 'object' ||  fn.typeof( paramB ) === 'array') {
                    try {
                        paramA = ( paramA !== '')? JSON.stringify( paramA ): '';
                        paramB = ( paramB !== '')? JSON.stringify( paramB ): '';
                    } catch ( error ) {
                        paramA = '';
                        paramB = '';
                        console.warn('journal error. (JSON.stringify error)');
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
                    return flag;
                } else if ( paramA > paramB ) {
                    return -flag;
                } else {
                    return 0;
                }
            });
        }
    }
}
/*
##################################################
   表示するページデータを返す
##################################################
*/
postPageData() {
    const tw = this;
    
    tw.setPagingStatus( tw.result );
    
    self.postMessage({
        type: tw.data.type,
        result: tw.result.slice( tw.data.paging.startPageNum, tw.data.paging.endPageNum ),
        discard: tw.data.discard, 
        paging: tw.data.paging,
        order: tw.data.order
    });
}
/*
##################################################
   選択データを返す
##################################################
*/
postSelectData() {
    const tw = this;

    const filter = tw.result.filter(function( val ){
        const id = String( val.parameter[ tw.data.idName ] );
        return tw.data.select.indexOf( id ) !== -1;
    });
    
    self.postMessage({
        type: tw.data.type,
        selectData: filter
    });
}
/*
##################################################
   エラーメッセージを返す
##################################################
*/
postError( result ) {
    self.postMessage({
        type: 'error',
        result: result
    });
}
/*
##################################################
   選択済みページデータを返す
##################################################
*/
postSelectPageData() {
    const tw = this;
    
    tw.result = tw.result.filter(function( val ){
        const id = String( val.parameter[ tw.data.idName ] );
        return tw.data.select.indexOf( id ) !== -1;
    });
    
    tw.postPageData();
}
/*
##################################################
   選択データを複製
##################################################
*/
duplicatSelectData() {
    const tw = this;
    
    const newData = [],
          exclusion = ['last_update_date_time', 'last_updated_user'];

   tw.result.forEach(function( val ){
        const id = String( val.parameter[ tw.data.idName ] );
        if ( tw.data.select.indexOf( id ) !== -1 ) {
            const parameters = {},
                  files = {};
            for ( const key in val.parameter ) {
                if ( key === tw.data.idName ) {
                    parameters[ key ] = String( tw.data.addId-- );
                } else if ( exclusion.indexOf( key ) === -1 ) {
                    // 入力済みのデータがあるか
                    if ( tw.data.input && tw.data.input[id] && tw.data.input[id].after.parameter[ key ] ) {
                        parameters[ key ] = tw.data.input[id].after.parameter[ key ];
                    } else {
                        parameters[ key ] = val.parameter[ key ];
                    }
                } else {
                    parameters[ key ] = null;
                }
            }
            for ( const key in val.file ) {
                // 入力済みのデータがあるか
                if ( tw.data.input && tw.data.input[id] && tw.data.input[id].after.file[ key ] ) {
                    files[ key ] = tw.data.input[id].after.file[ key ];
                } else {
                    files[ key ] = val.file[ key ];
                }
            }
            newData.unshift({
                file: files,
                parameter: parameters
            });
        }
    });    
    
    if ( tw.data.type === 'changeEditDup') {
        tw.result = newData;
    } else {
        tw.result = newData.concat( tw.result );
    }
}
/*
##################################################
   変更履歴差分
##################################################
*/
historyDiff() {
    const tw = this,
          r = tw.result,
          l = r.length;
    for ( let i = 0; i < l; i++ ) {
        // 次があるか
        if ( r[ i + 1 ] ) {
            const a = r[ i ].parameter,
                  b = r[ i + 1 ].parameter;
            for ( const k in a ) {
                // チェック用に一旦変換する
                let pa = fn.cv( a[ k ], ''),
                    pb = fn.cv( b[ k ], '');
                // 配列、オブジェクトの場合は文字列化
                if ( fn.typeof( pa ) === 'object' || fn.typeof( pb ) === 'array' ||
                     fn.typeof( pb ) === 'object' || fn.typeof( pb ) === 'array') {
                    try {
                        pa = ( pa !== '')? JSON.stringify( pa ): '',
                        pb = ( pb !== '')? JSON.stringify( pb ): '';
                        if ( pa !== pb ) {
                            if ( !r[ i ].journal ) r[ i ].journal = {};
                            r[ i ].journal[ k ] = b[ k ];
                        }
                    } catch ( error ) {
                        console.warn('journal error. (JSON.stringify error)');
                    }
                } else {
                    if ( pa !== pb ) {
                        if ( !r[ i ].journal ) r[ i ].journal = {};
                        r[ i ].journal[ k ] = b[ k ];
                    }
                }
            }
        }
    }
}
/*
##################################################
   選択データを削除
##################################################
*/
deleteSelectData() {
    const tw = this;
    
    for( const rowId of tw.data.select ) {
        const index = tw.result.findIndex(function( val ){
            const id = val.parameter[ tw.data.idName ];
            if ( !isNaN( id ) && Number( id ) < 0 ) {
                return rowId === val.parameter[ tw.data.idName ];
            }
        });
        if ( index !== -1 ) {
            tw.result.splice( index, 1 );
        }
    }
}
/*
##################################################
   廃止IDの一覧
##################################################
*/
setDiscardIdList() {
    const tw = this;
    
    const filter = tw.result.filter(function( val ){
        return val.parameter.discard === '1';
    });    
    
    tw.data.discard = filter.map(function( val ){
        if ( val.parameter.discard === '1') {
            return val.parameter[ tw.data.idName ];
        } else {
            return null;
        }
    });    
}

}

(function(){

    const tw = new TableWorker();

    self.addEventListener('message', function( message ){
        tw.message( message.data );
    });

}());