////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Exastro IT Automation / compare.js
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

class Compare {
/*
##################################################
   Constructor
##################################################
*/
constructor( menu ) {
    const cp = this;

    cp.menu = menu;
    cp.setRestApiUrls();
}
/*
##################################################
   REST API URL
##################################################
*/
setRestApiUrls() {
    const cp = this;

    cp.rest = {};

    cp.rest.info = `/menu/${cp.menu}/compare/info/`;
    cp.rest.list = `/menu/${cp.menu}/compare/execute/info/`;
    cp.rest.compare = `/menu/${cp.menu}/compare/execute/`;
    cp.rest.download = `/menu/${cp.menu}/compare/execute/output/`;
}
/*
##################################################
   info読み込み開始
##################################################
*/
setup() {
    const cp = this;

    cp.$ = {};
    cp.$.content = $('#content').find('.sectionBody');

    // ローディング表示
    cp.$.content.addClass('nowLoading');

    fn.fetch( [ cp.rest.info, cp.rest.list ] ).then(function( result ){
        cp.info = result[0];
        cp.list = result[1];
        cp.init();
    }).catch(function( error ){
        console.error( error );
    });
}
/*
##################################################
   初期表示
##################################################
*/
init() {
    const cp = this;

    cp.compareData = {
        compare: '',
        host: []
    };

    cp.select = {
        host: cp.info.list.host
    };

    cp.$.content.removeClass('nowLoading').html( cp.compareHtml() );

    cp.$.setting = cp.$.content.find('.compareSetting');
    cp.$.host = cp.$.content.find('.compareHost');
    cp.$.result = cp.$.content.find('.compareResult');

    cp.$.compareButton = cp.$.content.find('.compareButton');
    cp.$.compareDownloadButton = cp.$.content.find('.compareDownloadButton');

    cp.compareEvents();

    // 結果ホスト切替
    cp.$.content.on('click', '.compareExecuteItem', function(){
        const $item = $( this ),
              host = cp.escape( $item.attr('data-id') );

        cp.$.content.find('.compareOpen').removeClass('compareOpen');
        $item.add( cp.$.result.find(`.comparaResultBlock[data-id="${host}"]`) ).addClass('compareOpen');
    });
}
/*
##################################################
   Text escape
##################################################
*/
escape( val ) {
    return val.replace(/[ !"#$%&'()*+,.\/:;<=>?@\[\\\]^`{|}~]/g, "\\$&")
}
/*
##################################################
   Button check
##################################################
*/
compareButtonCheck() {
    const cp = this;

    const flag = !( cp.compareData.compare !== '' );
    cp.$.compareButton.prop('disabled', flag );
    cp.$.compareDownloadButton.prop('disabled', flag );
}
/*
##################################################
   Compare HTML
##################################################
*/
compareHtml() {
    const cp = this;

    const menu = {
        Main: [
            { button: { icon: 'menuList', text: getMessage.FTE06001, type: 'compareSelect', action: 'default', minWidth: '160px'} },
            { button: { icon: 'menuList', text: getMessage.FTE06002, type: 'hostSelect', action: 'default', minWidth: '160px'} },
            { button: { icon: 'compare', text: getMessage.FTE06003, type: 'compare', action: 'positive', minWidth: '160px', disabled: true, className: 'compareButton' } },
            { button: { icon: 'download', text: getMessage.FTE06032, type: 'download', action: 'default', minWidth: '160px', disabled: true, className: 'compareDownloadButton' }, separate: true },
        ]
    };

    return '<div class="compareContainer">'
    + '<div class="compareHeader">'
        + fn.html.operationMenu( menu )
    + '</div>'
    + '<div class="compareBody">'
        + '<div class="compareSetting compareBodyBlock">'
            + cp.compareSettingMessageHtml()
        + '</div>'
        + '<div class="compareHost compareBodyBlock">'
            + cp.hostHtml( cp.select.host )
        + '</div>'
        + '<div class="compareResult compareBodyBlock">'
            + cp.compareResultMessageHtml()
        + '<div>'
    + '</div>';
}
/*
##################################################
   各メッセージHTML
##################################################
*/
compareSettingMessageHtml() {
    return ''
    + '<div class="commonMessage messageVertical">'
        + '<div class="commonMessageInner">'
            + '<span class="icon icon-circle_info"></span>' + getMessage.FTE06004
        + '</div>'
    + '</div>';
}
compareHostMessageHtml() {
    return ''
    + '<div class="commonMessage messageVertical">'
        + '<div class="commonMessageInner">'
            + '<span class="icon icon-circle_info"></span>' + getMessage.FTE06005
        + '</div>'
    + '</div>';
}
compareResultMessageHtml() {
    return ''
    + '<div class="commonMessage">'
        + '<div class="commonMessageInner">'
            + '<span class="icon icon-circle_info"></span>' + getMessage.FTE06006
        + '</div>'
    + '</div>';
}
/*
##################################################
   比較設定HTML
##################################################
*/
compareSettingHtml( info ) {
    return ''
    + '<div class="compareContentHeader">'
        + `<div class="commonTitle">${getMessage.FTE06007}</div>`
    + '</div>'
    + '<div class="compareContentBody commonScroll">'
        + '<div class="commonBody commonWrap">'
            + '<dl class="commonStatus">'
                + `<dt class="commonStatusKey">${getMessage.FTE06008}</dt>`
                + `<dd class="commonStatusValue">${fn.cv( info.name, '', true )}</dd>`
            + '</dl>'
            + '<dl class="commonStatus">'
                + `<dt class="commonStatusKey">${getMessage.FTE06009}</dt>`
                + `<dd class="commonStatusValue">${fn.cv( info.selectOtherKeys.detail_flg, '', true )}</dd>`
            + '</dl>'
        + '</div>'
        + '<div class="commonSubTitle">'
            + getMessage.FTE06015
        + '</div>'
        + '<div class="commonBody commonWrap">'
            + '<dl class="commonStatus">'
                + `<dt class="commonStatusKey">${getMessage.FTE06010}</dt>`
                + `<dd class="commonStatusValue">${fn.cv( info.selectOtherKeys.target_menu_1, '', true )}</dd>`
            + '</dl>'
            + '<dl class="commonStatus">'
                + `<dt class="commonStatusKey">${getMessage.FTE06011}</dt>`
                + '<dd class="commonStatusValue">'
                    + fn.html.dateInput( true, 'referenceDate', '', 'referenceDate1')
                + '</dd>'
            + '</dl>'
        + '</div>'
        + '<div class="commonSubTitle">'
            + getMessage.FTE06016
        + '</div>'
        + '<div class="commonBody commonWrap">'
            + '<dl class="commonStatus">'
                + `<dt class="commonStatusKey">${getMessage.FTE06010}</dt>`
                + `<dd class="commonStatusValue">${fn.cv( info.selectOtherKeys.target_menu_2, '', true )}</dd>`
            + '</dl>'
            + '<dl class="commonStatus">'
                + `<dt class="commonStatusKey">${getMessage.FTE06012}</dt><dd class="commonStatusValue">`
                    + fn.html.dateInput( true, 'referenceDate', '', 'referenceDate2')
                + '</dd>'
            + '</dl>'
        + '</div>'
        // + '<div class="commonSubTitle">'
        //     + getMessage.FTE06017
        // + '</div>'
        // + '<div class="commonBody commonWrap">'
        //     + fn.html.radioText('compareOutput', '1', 'compareOutput', 'compareOutputAll', {checked: 'checked'}, getMessage.FTE06013)
        //     + fn.html.radioText('compareOutput', '2', 'compareOutput', 'compareOutputDiff', null, getMessage.FTE06014)
        // + '</div>'
    + '</div>';
}
/*
##################################################
   対象ホスト一覧HTML
##################################################
*/
hostHtml( hostList ) {
    const cp = this;

    cp.compareData.host = [];

    if ( !hostList.length ) {
        return cp.compareHostMessageHtml();
    }

    const html = ['<ul class="compareHostList">'];
    for ( const host of hostList ) {
        const name = ( fn.typeof( host ) === 'string')? host: host.name,
              escapeName = fn.cv( name, '', true );
        html.push(``
        + `<li class="compareHostItem" data-id="${escapeName}">`
            + `<dl class="commonStatus"><dt class="commonStatusKey">${getMessage.FTE06018}</dt><dd class="commonStatusValue">${escapeName}</dd></dl>`
            + `<div class="compareHostDiff"><div class="compareHostDiffTitle">${getMessage.FTE06019}</div><div class="compareHostDiffFlag"></div></div>`
        + `</li>`);
        cp.compareData.host.push( name );
    }
    html.push('</ul>');

    return ''
    + '<div class="compareContentHeader">'
        + `<div class="commonTitle">${getMessage.FTE06020}</div>`
    + '</div>'
    + '<div class="compareContentBody commonScroll">'
        + html.join('')
    + '</div>';
}
/*
##################################################
   比較メニューボタン
##################################################
*/
compareEvents() {
    const cp = this;

    cp.$.content.find('.operationMenuButton').on('click', function(){
        const $button = $( this ),
              type = $button.attr('data-type');

        switch ( type ) {
            case 'compareSelect':
                cp.selectModalOpen('compare').then(function( result ){
                    if ( result ) {
                        cp.compareData.compare = result[0].name;
                        cp.$.setting.html( cp.compareSettingHtml( result[0] ) );
                        cp.$.result.html( cp.compareResultMessageHtml() );

                        cp.$.referenceDate1 = cp.$.setting.find('#referenceDate1');
                        cp.$.referenceDate2 = cp.$.setting.find('#referenceDate2');
                        cp.$.output = cp.$.setting.find('.compareOutput');

                        cp.compareSettingEvents();
                        cp.compareButtonCheck();
                        cp.restExeHost();
                    }
                });
            break;
            case 'hostSelect':
                cp.selectModalOpen('host').then(function( result ){
                    if ( result ) {
                        // 形式を合わせる
                        cp.select.host = result.map(function( item ){
                            if ( fn.typeof( item ) === 'object') {
                                return item.name;
                            } else {
                                return item;
                            }
                        });
                        cp.$.host.html( cp.hostHtml( cp.select.host ) );
                        cp.$.result.html( cp.compareResultMessageHtml() );
                        cp.$.host.removeClass('compareExecuteHost');
                        cp.compareButtonCheck();
                    }
                });
            break;
            case 'compare': {
                $button.prop('disabled', true );
                cp.getCompareSettingData();
                cp.$.result.addClass('nowLoading').empty();
                fn.fetch( cp.rest.compare, null, 'POST', cp.compareData ).then(function( result ){
                    cp.restExeHost();
                    cp.setCompareResult( result );
                }).catch(function( error ){
                    if ( fn.typeof( error ) === 'object') {
                        if ( fn.typeof( error.message ) === 'string') {
                            alert( error.message );
                        } else {
                            alert( getMessage.FTE06021 );
                        }
                    } else {
                        alert( getMessage.FTE06021 );
                    }
                    cp.$.result.html( cp.compareResultMessageHtml() );
                }).then(function(){
                    cp.$.result.removeClass('nowLoading');
                    $button.prop('disabled', false );
                });
            } break;
            case 'download': {
                $button.prop('disabled', true );
                cp.getCompareSettingData();
                fn.getFile( cp.rest.download, 'POST', cp.compareData, { title: getMessage.FTE00185 }).then(function( file ){
                    const fileName = fn.cv( file.name, '');
                    fn.download('file', file, fileName );
                }).catch(function( error ){
                    if ( fn.typeof( error ) === 'object') {
                        if ( fn.typeof( error.message ) === 'string') {
                            alert( error.message );
                        } else {
                            alert( getMessage.FTE06033 );
                        }
                    } else {
                        if ( error !== 'break') {
                            alert( getMessage.FTE06033 );
                        }
                    }
                }).then(function(){
                    $button.prop('disabled', false );
                });
            } break;
        }
    });
}
/*
##################################################
   比較設定欄イベント
##################################################
*/
compareSettingEvents() {
    const cp = this;

    // データピッカー
    fn.setDatePickerEvent( cp.$.referenceDate1, getMessage.FTE06022);
    fn.setDatePickerEvent( cp.$.referenceDate2, getMessage.FTE06023);
}
/*
##################################################
   比較設定、入力値の取得
##################################################
*/
getCompareSettingData() {
    const cp = this;

    const targetDate1 = fn.cv( cp.$.referenceDate1.val(), '');
    const targetDate2 = fn.cv( cp.$.referenceDate2.val(), '');
    cp.compareData.base_date_1 = targetDate1;
    cp.compareData.base_date_2 = targetDate2;
}
/*
##################################################
   選択用モーダルを開く
##################################################
*/
selectModalOpen( type ) {
    const cp = this;

    return new Promise(function( resolve ){

        const selectConfig = {};
        let title;

        if ( type === 'host') {
            title = getMessage.FTE06002;
            selectConfig.infoData = cp.list.device_list;
            selectConfig.selectNameKey = 'host_name';
            selectConfig.filter = `/menu/${cp.menu}/compare/execute/filter/device_list/`;
            selectConfig.filterPulldown = `/menu/${cp.menu}/compare/execute/filter/device_list/search/candidates/`;
            selectConfig.selectType = 'multi';
            selectConfig.unselected = true;
            selectConfig.selectTextArray = cp.select.host;
            selectConfig.selectTextArrayTextKey = 'host_name';
            selectConfig.selectTextArrayIdKey = 'managed_system_item_number';
        } else {
            title = getMessage.FTE06001;
            selectConfig.infoData = cp.list.compare_list;
            selectConfig.selectNameKey = 'compare_name';
            selectConfig.filter = `/menu/${cp.menu}/compare/execute/filter/compare_list/`;
            selectConfig.filterPulldown = `/menu/${cp.menu}/compare/execute/filter/compare_list/search/candidates/`;
            selectConfig.selectOtherKeys = ['target_menu_1', 'target_menu_2', 'detail_flg']
        }

        fn.selectModalOpen( type, title, cp.menu, selectConfig ).then(function( selectResut ){
            resolve( selectResut );
        });

    });
}
/*
##################################################
   ホスト状態リセット
##################################################
*/
restExeHost() {
    const cp = this;

    cp.$.host.removeClass('compareExecuteHost');
    cp.$.host.find('.compareHostItem').removeAttr('data-flag');
    cp.$.host.find('.compareOpen').removeClass('compareOpen');
    cp.$.host.find('.compareExecuteItem').removeClass('compareExecuteItem');
}
/*
##################################################
   比較結果
##################################################
*/
setCompareResult( info ) {
    const cp = this;

    let html = '';

    const hostList = cp.compareData.host,
          cols = info.config.target_column_info;

    let comapreCount = 0;

    cp.$.host.addClass('compareExecuteHost');

    for ( const host of hostList ) {
        const hostName = fn.escape( host ),
              compareData = ( info.compare_data )? info.compare_data[ host ]: null;
        if ( compareData ) {
            let compareFlag = info.compare_diff_flg[ host ];
            if ( fn.typeof( compareFlag ) !== 'boolean') compareFlag = false;
            comapreCount++;

            const t1Name = fn.cv( info.config.target_menus[0], '', true ),
                  t2Name = fn.cv( info.config.target_menus[1], '', true );

            const escapeHostName = host.replace(/[ !"#$%&'()*+,.\/:;<=>?@\[\\\]^`{|}~]/g, "\\$&"),
                  $host = cp.$.host.find(`.compareHostItem[data-id="${escapeHostName}"]`);

            $host.addClass('compareExecuteItem').attr('data-flag', compareFlag );
            $host.find('.compareHostDiffFlag').html( ( compareFlag )? fn.html.icon('check'): fn.html.icon('minus') );

            html += ''
            + `<div class="comparaResultBlock" data-id="${hostName}"><div class="commonSubTitle">${hostName}</div><div class="commonBody commonScroll">`
            + '<table class="table">'
            + '<thead class="thead">'
                + '<tr class="theadTr tr">'
                    + `<th class="tHeadTh th" rowspan="2"><div class="ci">${getMessage.FTE06024}</div></th>`
                    + `<th class="tHeadTh th" rowspan="2"><div class="ci">${getMessage.FTE06019}</div></th>`
                    + `<th class="tHeadGroup tHeadTh th"><div class="ci">${getMessage.FTE06015}</div></th>`
                    + `<th class="tHeadGroup tHeadTh th"><div class="ci">${getMessage.FTE06016}</div></th>`
                    + `<th class="tHeadTh th" rowspan="2"><div class="ci">${getMessage.FTE06025}</div></th>`
                + '</tr>'
                + '<tr class="theadTr tr">'
                    + `<th class="tHeadTh th"><div class="ci">${t1Name}</div></th>`
                    + `<th class="tHeadTh th"><div class="ci">${t2Name}</div></th>`
                + '</tr>'
            + '</thead>'
            + '<tbody class="tbody">';

            const valueCheck = function( checkValue ){
                if ( checkValue === null ) return `<span class="comparaNullValue">null</span>`;
                return fn.cv( checkValue, '', true );
            };

            // 項目出力
            for ( const col of cols ) {
                const colName = fn.cv( col.col_name, '');
                const escapeColName = fn.escape( colName );
                const diff = compareData._data_diff_flg[ colName ];
                if ( diff === null || diff === undefined) continue;

                const t1Value = valueCheck( compareData.target_data_1[ colName ] );
                const t2Value = valueCheck( compareData.target_data_2[ colName ] );

                let filediff = compareData._file_compare_execute_flg[ colName ];
                if ( fn.typeof( filediff ) !== 'boolean') filediff = undefined;

                const diffFlag = ( col.file_flg )? ( diff || filediff )? true: false: diff;

                html += `<tr class="tBodyTr tr${( !diffFlag )? ` differenceTr`: ``}">`
                + `<th class="tBodyTh th"><div class="ci">${escapeColName}</div></th>`
                + `<td class="tBodyTd td" data-flag="${diffFlag}"><div class="ci">`
                    + `<div class="compareItemDiffMark">${( diffFlag )? fn.html.icon('check'): fn.html.icon('minus')}</div>`
                + `</div></td>`
                + `<td class="tBodyTd td"><div class="ci">${t1Value}</div></td>`
                + `<td class="tBodyTd td"><div class="ci">${t2Value}</div></td>`
                + `<td class="tBodyTd td">`;

                if ( filediff ) {
                    if ( col.file_flg ) {
                        html += `<div class="ci bci">`
                        + fn.html.iconButton( 'detail', getMessage.FTE06026, 'itaButton fileDiffButton', { host: fn.escape( host ), colName: colName })
                        + `</div>`;
                    } else {
                        html += `<div class="ci">${getMessage.FTE06027}</div>`;
                    }
                } else {
                    html += '<div class="ci"></div>';
                }

                html += '</div></td></tr>';
            }
            html += '</tbody></table></div></div>';
        }
    }

    if ( comapreCount === 0 ) {
        html = ''
        + `<div class="commonMessage failedMessage"><div class="commonMessageInner">${fn.html.icon('compare') + getMessage.FTE06028}</div></div>`;
    }

    cp.$.result.html(''
    + '<div class="compareContentHeader">'
        + `<div class="commonTitle">${getMessage.FTE06029}</div>`
    + '</div>'
    + '<div class="compareContentBody commonScroll">'
        + html
    + '</div>');

    if ( comapreCount > 0 ) {
        cp.$.host.find('.compareExecuteItem').eq( 0 ).click();
    }

    // ファイル比較
    cp.$.result.find('.fileDiffButton').on('click', function(){
        const $button = $( this ),
              host = $button.attr('data-host'),
              name = $button.attr('data-colName');

        const fileDiffData = info.compare_data[ host ]._file_compare_execute_info[ name ];

        $button.prop('disabled', true );
        fn.fetch(`/menu/${cp.menu}/compare/execute/file/`, null, 'POST', fileDiffData.parameter ).then(function(result){
            const config = {
                className: 'diffModal',
                mode: 'modeless',
                position: 'center',
                header: {
                    title: getMessage.FTE06030
                },
                width: '1600px',
                footer: {
                    button: {
                        cancel: { text: getMessage.FTE06031, action: 'normal'},
                        print: { text: getMessage.FTE06034, action: 'normal'}
                    }
                }
            };
            const func = {
                print: function(){
                    modal.printBody();
                },
                cancel: function(){
                    $button.prop('disabled', false );
                    modal.close();
                    modal = null;
                }
            };
            let modal = new Dialog( config, func );

            const diffHtml = Diff2Html.html( result.unified_diff.diff_result, {
              drawFileList: false,
              matching: 'lines',
              outputFormat: 'side-by-side',
            });
            modal.open( diffHtml );
        }).catch(function( error ){
            if ( fn.typeof( error ) === 'object') {
                if ( fn.typeof( error.message ) === 'string') {
                    alert( error.message );
                }
            } else {
                window.console.error( error );
            }
            $button.prop('disabled', false );
        });
    });
}
}