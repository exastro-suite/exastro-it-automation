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

class TerraformManagement {
/*
##################################################
   Constructor
##################################################
*/
constructor( menu ) {
    const tm = this;

    tm.menu = menu;
    tm.setRestApiUrls();
}
/*
##################################################
   REST API URL
##################################################
*/
setRestApiUrls() {
    const tm = this;

    tm.rest = {};

    tm.rest.organization = `/terraform/organization/`;
    tm.rest.workspace = `/terraform/workspace/`;
    tm.rest.policy = `/terraform/policy/`;
    tm.rest.policyset = `/terraform/policyset/`;
}
/*
##################################################
   Setup
##################################################
*/
setup() {
    const tm = this;

    tm.$ = {},
    tm.$.content = $('#content');

    tm.setting = {
        terraformOrganization: {
            type: 'organization',
            rest: tm.rest.organization,
            button: getMessage.FTE09005
        },
        terraformWorkspace: {
            type: 'workspace',
            rest: tm.rest.workspace,
            button: getMessage.FTE09006
        },
        terraformPolicy: {
            type: 'policy',
            rest: tm.rest.policy,
            button: getMessage.FTE09007
        },
        terraformPolicyset: {
            type: 'policyset',
            rest: tm.rest.policyset,
            button: getMessage.FTE09008
        }
    };

    // HTMLセット
    tm.$.content.find('.section').each(function(){
        const $section = $( this ),
              id = $section.attr('id');
        
        tm.$[ id ] = $section;

        const button = {
            icon: 'menuList',
            text: tm.setting[ id ].button,
            type: id,
            action: 'default',
            minWidth: '160px'
        };
        
        $section.find('.sectionBody').html(``
        + `<div class="tableContainer noFilter noData">`
            + `<div class="tableHeader">`
                + fn.html.operationMenu({Main: [{ button: button }]})
            + `</div>`
            + `<div class="tableBody">`
                + `<div class="tableWrap">`
                    + `<div class="tableBorder">`
                    + `</div>`
                + `</div>`
                + `<div class="tableMessage">`
                    + `<div class="message"><span class=" icon icon-circle_info"></span>${getMessage.FTE09018( tm.setting[ id ].button )}</div>`
                + `</div>`
            + `</div>`
        + `</div>`);
    });

    // 一覧ボタンイベント
    tm.$.content.find('.operationMenuButton').on('click', function(){
        const $button = $( this ),
              type = $button.attr('data-type');
        
        $button.prop('disabled', true );
        tm.getSet( type ).then(function(){
            $button.prop('disabled', false );
        });

    });

    // 一覧ボタンイベント
    tm.$.content.on('click', '.actionButton', function(){
        const $button = $( this ),
              buttonText = $button.text(),
              tabType = $button.attr('data-tab'),
              type = $button.attr('data-type');
        
        $button.prop('disabled', true );

        const set = { rest: null, method: null, body: null, option: {}};
        switch ( type ) {
            // Organization削除
            case 'organization_delete': {
                const tf_organization_name = $button.attr('data-tf_organization_name');
                set.rest = `/terraform/organization/${tf_organization_name}/`;
                set.method = `DELETE`;
            } break;
            // Workspace削除
            case 'workspace_delete': {
                const tf_organization_name = $button.attr('data-tf_organization_name'),
                    tf_workspace_name = $button.attr('data-tf_workspace_name');
                set.rest = `/terraform/workspace/${tf_organization_name}/${tf_workspace_name}/`;
                set.method = `DELETE`;
            } break;
            // Workspaceリソース削除
            case 'workspace_resource_delete': {
                const tf_workspace_name = $button.attr('data-tf_workspace_name');
                set.rest = `/menu/execution_terraform_cloud_ep/driver/execute_delete_resource/`;
                set.method = `POST`;
                set.body = {
                    tf_workspace_name: tf_workspace_name
                };
                set.option = {
                    redirect: `menu=check_operation_status_terraform_cloud_ep&execution_no=`,
                    redirect_key: `execution_no`
                }
            } break;
            // Policyダウンロード
            case 'policy_download': {
                const download_path = $button.attr('data-download_path'),
                    tf_organization_name = $button.attr('data-tf_organization_name'),
                    policy_name = $button.attr('data-policy_name');
                set.rest = `/terraform/policy/${tf_organization_name}/download/${policy_name}/`;
                set.method = `POST`;
                set.body = {
                    download_path: download_path
                };
                set.option.download = `menu=check_operation_status_terraform_cloud_ep&execution_no=`;
            } break;
            // Policy削除
            case 'policy_delete': {
                const tf_organization_name = $button.attr('data-tf_organization_name'),
                    policy_name = $button.attr('data-policy_name');
                set.rest = `/terraform/policy/${tf_organization_name}/delete/${policy_name}/`;
                set.method = `DELETE`;
            } break;
            // Policy set Workspace紐付解除
            case 'workspace_unlink': {
                const tf_organization_name = $button.attr('data-tf_organization_name'),
                    policy_set_name = $button.attr('data-policy_set_name'),
                    tf_workspace_name = $button.attr('data-unlink_name');
                set.rest = `/terraform/policyset/${tf_organization_name}/relationship/${policy_set_name}/workspace/${tf_workspace_name}/`;
                set.method = `DELETE`;
            } break;
            // Policy set Policy紐付解除
            case 'policy_unlink': {
                const tf_organization_name = $button.attr('data-tf_organization_name'),
                    policy_set_name = $button.attr('data-policy_set_name'),
                    policy_name = $button.attr('data-unlink_name');
                set.rest = `/terraform/policyset/${tf_organization_name}/relationship/${policy_set_name}/policy/${policy_name}/`;
                set.method = `DELETE`;
            } break;
            // Policy set 削除
            case 'policyset_delete': {
                const tf_organization_name = $button.attr('data-tf_organization_name'),
                    policy_set_name = $button.attr('data-policy_set_name');
                set.rest = `/terraform/policyset/${tf_organization_name}/delete/${policy_set_name}/`;
                set.method = `DELETE`;
            } break;
        }

        tm.exeRestApi( buttonText, set.rest, set.method, set.body, set.option ).then(function( flag ){
            if ( flag !== 'noUpdate') {
                tm.getSet( tabType );
            } else {
                $button.prop('disabled', false );
            }
        });
    });
}
/*
##################################################
   リストを取得し表を表示する
##################################################
*/
getSet( type ) {
    const tm = this;

    return new Promise(function( resolve ){
        let process = fn.processingModal( tm.setting[ type ].button );
        fn.fetch( tm.setting[ type ].rest ).then(function( result ){
            tm.$[ type ].find('.noData').removeClass('noData');
            tm.$[ type ].find('.tableBorder').html( tm[ tm.setting[ type ].type ].call( tm, result ) );
        }).catch(function( error ){
            window.console.error( error );
            alert( error.message );
        }).then(function(){
            process.close();
            process = null;
            resolve();
        });
    });
}
/*
##################################################
   REST
##################################################
*/
exeRestApi( buttonText, rest, method, body, option ) {
    return new Promise(function( resolve ){
        if ( option.download ) {
            let process = fn.processingModal( getMessage.FTE00120 );
            fn.fetch( rest, null, method, body ).then(function( result ){
                fn.download('base64', result.file, result.file_name );
            }).catch(function( error ){
                window.console.error( error );
                alert( error.message );
            }).then(function(){
                process.close();
                process = null;
                resolve('noUpdate');
            });
        } else {
            const text = getMessage.FTE00119( buttonText );
                
            fn.alert(`${buttonText}${getMessage.FTE00118}`, text, 'confiarm', {
                ok: { text: getMessage.FTE00122, action: 'default', style: 'width:160px', className: 'dialogPositive'},
                cancel: { text: getMessage.FTE00123, action: 'negative', style: 'width:120px'}
            }, '400px').then( function( flag ){
                if ( flag ) {
                    let process = fn.processingModal( getMessage.FTE00120 );
                    fn.fetch( rest, null, method, body, { message: true } ).then(function( result ){
                        if ( option.redirect ) {
                            if ( fn.typeof( result ) === 'array') {
                                const value = result[0][ option['redirect_key'] ];
                                if ( value ) {
                                    window.location.href = `?${option.redirect + value}`;
                                }
                            }
                        } else {
                            const message = ( fn.typeof( result ) === 'array')? result[1]: result;
                            fn.alert( getMessage.FTE00121, message ).then(function(){
                                resolve();
                            });
                        }
                    }).catch(function( error ){
                        window.console.error( error );
                        alert( error.message );
                        resolve();
                    }).then(function(){
                        process.close();
                        process = null;
                    });
                } else {
                    resolve('noUpdate');
                }
            });
        }
    });
}
/*
##################################################
   Table HTML
##################################################
*/
table( thead, tbody, className = '') {
    return `<table class="table ${className}">`
        + `<thead class="thead">${thead}</thead>`
        + `<tbody class="tbody">${tbody}</tbody>`
    + `</table>`;
}
/*
##################################################
   Table header HTML
##################################################
*/
tableHeader( thead ) {
    const thHtml = [];
    for ( const th of thead ) {
        thHtml.push( fn.html.cell( th, `tHeadTh`, 'th') );
    }
    return `<tr class="tHeadTr tr">${thHtml.join('')}</tr>`;
}
/*
##################################################
   Table body HTML
##################################################
*/
talbeBody( tbody, info ) {
    const tm = this;

    const trHtml = [],
          infoLength = info.length;
    for ( let i = 0; i < infoLength; i++ ) {
        const row = info[i],
              tdHtml = [[]];
        let rowspan = 1;
        // Policy set
        if ( row.policy && row.workspace ) {
            const policyLength = Object.keys( row.policy ).length,
                  workspaceLength = Object.keys( row.workspace ).length;
            rowspan = ( policyLength < workspaceLength )? workspaceLength: policyLength;
            if ( rowspan <= 0 ) rowspan = 1;
        }
        for ( const item of tbody ) {
            switch ( item.type ) {
                case 'text':
                    tdHtml[0].push( tm.tbodyTd( row[ item.name ], rowspan ) );
                break;
                case 'flag':
                    tdHtml[0].push( tm.tbodyTd( tm.itaFlag( row[ item.name ] ), rowspan ) );
                break;
                case 'button':
                    tdHtml[0].push( tm.tbodyTd( tm.button( row, item ), rowspan ) );
                break;
                case 'workspace': case 'policy': {
                    const data = ( item.type === 'workspace')? row.workspace: row.policy,
                          tds = tm.linkList( row, item, data, rowspan ),
                          tdsLength = tds.length;
                    for ( let j = 0; j < tdsLength; j++ ) {
                        if ( !tdHtml[j] ) tdHtml[j] = [];
                        tdHtml[j].push( tds[j].join('') );
                    }
                } break;
            }
        }
        const tdHtmlLength = tdHtml.length;
        for ( let j = 0; j < tdHtmlLength; j++ ) {
            const rowClassName = [];
            if ( ( i + 1 ) % 2 === 0 ) {
                rowClassName.push('multipleEven');
            } else {
                rowClassName.push('multipleOdd');
            }
            if ( rowspan > 1 && j < rowspan - 1 ) rowClassName.push('multipleRow');
            if ( rowspan > 1 && j === rowspan - 1 ) rowClassName.push('lastRow');
            trHtml.push( tm.tbodyTr( tdHtml[j].join(''), rowClassName.join(' ') ) );
        }
    }
    return trHtml.join('');
}

tbodyTr( html, className = '') {
    return `<tr class="tBodyTr tr ${className}">${html}</tr>`;
}

tbodyTd( text, rowspan ) {
    return fn.html.cell( text, `tBodyTd`, 'td', rowspan );
}

itaFlag( flag ) {
    return ( flag )?
        `<span class="registered">${fn.html.icon('check')} ${getMessage.FTE09009}</span>`:
        `<span class="unregistered">${fn.html.icon('minus')} ${getMessage.FTE09010}</span>`;
}

button( row, item, setAttr = {}) {
    const attr = {
        tab: item.button.tab,
        type: item.button.type,
        action: ( item.button.action )? item.button.action: 'danger'
    };
    if ( row[ item.name ] === false ) attr.disabled = 'disabled';
    for ( const key of item.button.set ) {
        attr[ key ] = fn.cv( row[ key ], '', true );
    }
    for ( const key in setAttr ) {
        attr[ key ] = fn.cv( setAttr[ key ], '', true );
    }
    return fn.html.button( item.button.text, 'actionButton itaButton', attr );
}


linkList( row, itemData, list, rowspan ) {
    const tm = this;

    const tdHtml = [];

    // 配列に変換
    const listArray = [];
    for ( const item in list ) {
        listArray.push({
            name: item,
            ita_registered: list[ item ].ita_registered
        });
    }

    const tbody = [
        { name: 'name', type: 'text'},
        { name: 'ita_registered', type: 'flag'},
        { name: 'ita_registered', type: 'button', button: {
                tab: 'terraformPolicyset',
                type: `${itemData.type}_unlink`,
                text: getMessage.FTE09011,
                set: [`tf_organization_name`, `policy_set_name`]
            }
        }
    ];

    for ( let i = 0; i < rowspan; i++ ) {
        for ( const item of tbody ) {
            if ( !tdHtml[i] ) tdHtml[i] = [];
            if ( listArray[i] ) {
                switch ( item.type ) {
                    case 'text':
                        tdHtml[i].push( tm.tbodyTd( listArray[i][ item.name ] ) );
                    break;
                    case 'flag':
                        tdHtml[i].push( tm.tbodyTd( tm.itaFlag( row[ item.name ] ) ) );
                    break;
                    case 'button': {
                        const attr = {
                            unlink_name: listArray[i].name
                        };
                        tdHtml[i].push( tm.tbodyTd( tm.button( row, item, attr ) ) );
                    } break;
                }
            } else {
                tdHtml[i].push( tm.tbodyTd('<span class="tBodyAutoInput"></span>') );
            }
        }
    }
    
    return tdHtml;
}

/*
##################################################
   organization
##################################################
*/
organization( info ) {
    const tm = this;

    const thead = [
        getMessage.FTE09019,
        getMessage.FTE09020,
        getMessage.FTE09012,
        getMessage.FTE09013
    ];

    const tbody = [
        { name: 'tf_organization_name', type: 'text'},
        { name: 'email_address', type: 'text'},
        { name: 'ita_registered', type: 'flag'},
        { name: 'ita_registered', type: 'button', button: {
                tab: 'terraformOrganization',
                type: 'organization_delete',
                text: getMessage.FTE09013,
                set: [`tf_organization_name`]
            }
        }
    ];

    return tm.table( tm.tableHeader( thead ), tm.talbeBody( tbody, info ) );
}
/*
##################################################
   workspace
##################################################
*/
workspace( info ) {
    const tm = this;

    const thead = [
        getMessage.FTE09019,
        getMessage.FTE09021,
        getMessage.FTE09022,
        getMessage.FTE09012,
        getMessage.FTE09014,
        getMessage.FTE09013
    ];

    const tbody = [
        { name: 'tf_organization_name', type: 'text'},
        { name: 'tf_workspace_name', type: 'text'},
        { name: 'terraform_version', type: 'text'},
        { name: 'ita_registered', type: 'flag'},
        { name: 'ita_registered', type: 'button', button: {
                tab: 'terraformWorkspace',
                type: 'workspace_resource_delete',
                text: getMessage.FTE09014,
                set: [`tf_workspace_name`],
                action: 'warning'
            }
        },
        { name: 'ita_registered', type: 'button', button: {
                tab: 'terraformWorkspace',
                type: 'workspace_delete',
                text: getMessage.FTE09013,
                set: [`tf_organization_name`, `tf_workspace_name`]
            }
        }
    ];

    return tm.table( tm.tableHeader( thead ), tm.talbeBody( tbody, info ) );
}
/*
##################################################
   policy
##################################################
*/
policy( info ) {
    const tm = this;

    const thead = [
        getMessage.FTE09019,
        getMessage.FTE09023,
        getMessage.FTE09012,
        getMessage.FTE09024,
        getMessage.FTE09013
    ];

    const tbody = [
        { name: 'tf_organization_name', type: 'text'},
        { name: 'policy_name', type: 'text'},
        { name: 'ita_registered', type: 'flag'},
        { name: 'ita_registered', type: 'button', button: {
                tab: 'terraformPolicy',
                type: 'policy_download',
                text: getMessage.FTE09015,
                set: [`tf_organization_name`, `policy_name`, `download_path`],
                action: 'default'
            }
        },
        { name: 'ita_registered', type: 'button', button: {
                tab: 'terraformPolicy',
                type: 'policy_delete',
                text: getMessage.FTE09013,
                set: [`tf_organization_name`, `policy_name`]
            }
        }
    ];

    return tm.table( tm.tableHeader( thead ), tm.talbeBody( tbody, info ) );
}
/*
##################################################
   policyset
##################################################
*/
policyset( info ) {
    const tm = this;

    const thead = ``
    + `<tr class="tHeadTr tr">`
        + fn.html.cell( getMessage.FTE09019, `tHeadTh th`, 'th', 2 )
        + fn.html.cell( getMessage.FTE09025, `tHeadTh th `, 'th', 2 )
        + fn.html.cell( getMessage.FTE09016, `tHeadTh th tHeadGroup `, 'th', 1, 3 )
        + fn.html.cell( getMessage.FTE09017, `tHeadTh th tHeadGroup `, 'th', 1, 3 )
        + fn.html.cell( getMessage.FTE09012, `tHeadTh th`, 'th', 2 )
        + fn.html.cell( getMessage.FTE09013, `tHeadTh th`, 'th', 2 )
    + `</tr>`
    + `<tr class="tHeadTr tr">`
        + fn.html.cell( getMessage.FTE09021, `tHeadTh th`, 'th', 1 )
        + fn.html.cell( getMessage.FTE09012, `tHeadTh th`, 'th', 1 )
        + fn.html.cell( getMessage.FTE09011, `tHeadTh th`, 'th', 1 )
        + fn.html.cell( getMessage.FTE09023, `tHeadTh th`, 'th', 1 )
        + fn.html.cell( getMessage.FTE09012, `tHeadTh th`, 'th', 1 )
        + fn.html.cell( getMessage.FTE09011, `tHeadTh th`, 'th', 1 )
    + `</tr>`;

    const tbody = [
        { name: 'tf_organization_name', type: 'text'},
        { name: 'policy_set_name', type: 'text'},
        { name: 'workspace', type: 'workspace'},
        { name: 'policy', type: 'policy'},
        { name: 'ita_registered', type: 'flag'},
        { name: 'ita_registered', type: 'button', button: {
                tab: 'terraformPolicyset',
                type: 'policyset_delete',
                text: getMessage.FTE09013,
                set: [`tf_organization_name`, `policy_set_name`]
            }
        }
    ];
    return tm.table( thead, tm.talbeBody( tbody, info ), 'multipleTable');
}

}