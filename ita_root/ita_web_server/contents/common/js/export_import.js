////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Exastro IT Automation / status.js
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

class ExportImport {
/*
##################################################
   Constructor
   menu: メニューREST名
   id: 作業実行ID
##################################################
*/
constructor( menu, type ) {
    const ex = this;
    
    ex.menu = menu;
    ex.type = type;    
}

setup() {
    const ex = this;
    
    ex.$ = {};
    ex.$.content = $('#content').find('.sectionBody');
    
    switch ( ex.type ) {
        case 'menuExport':
        case 'excelExport':
            ex.export();
        break;
        case 'menuImport':
        case 'excelImport':
            ex.import();
        break;
    }
    
}
/*
##################################################
   階層データの作成
##################################################
*/
createMenuGroupList( list ) {
    const ex = this;

    // メニューグループリストの作成    
    const menuGroupList = [],
          childs = [];
    
    // 配列のディープコピー
    const tempMenuGroups = $.extend( true, [], list );
    
    // 親と子を分ける
    const unknownParents = [];
    for ( const menuGroup of tempMenuGroups ) {
        if ( menuGroup.parent_id === null ) {
            menuGroupList.push( menuGroup );
        } else {
            // 親が存在するか？
            const parent = tempMenuGroups.find(function( mg ){
                return ( mg.id === menuGroup.parent_id );
            });
            childs.push( menuGroup );
            if ( !parent ) unknownParents.push( menuGroup.parent_id );
        }
    }
    
    // 親が見つからない場合は不明の親を追加する
    for ( const id of unknownParents ) {
        menuGroupList.push({
            disp_seq: -1,
            id: id,
            menu_group_name: getMessage.FTE07034,
            menus: [],
            parent_id: null,
            unknown: true
        });
    }
    
    // 親に子を追加
    for ( const parent of menuGroupList ) {
        for ( const child of childs ) {
            if ( parent.id === child.parent_id ) {
                child.main_menu_rest = null;
                if ( child.menus && child.menus.length ) {
                    ex.dispSeqSort( child.menus );
                }
                parent.menus.push( child );
            }
        }
        ex.dispSeqSort( parent.menus );
    }
    ex.dispSeqSort( menuGroupList );

    // 子のエラーカウントを調べる
    for ( const parent of menuGroupList ) {
        for ( const menu of parent.menus ) {
            if ( menu.error_count !== undefined ) {
                if ( !parent.error_count ) parent.error_count = 0;
                parent.error_count += menu.error_count;
            }
        }
    }
    
    return menuGroupList;
}
/*
##################################################
   Sort : disp_seq
##################################################
*/
dispSeqSort( data ) {
    data.sort(function( a, b ){
        if ( a.disp_seq < b.disp_seq ) {
            return -1;
        } else if ( a.disp_seq > b.disp_seq ) {
            return 1;
        } else {
            // disp_seqが同じ場合は名前で判定する
            const aa = ( a.menu_group_name )? a.menu_group_name: ( a.menu_name )? a.menu_name: '',
                  bb = ( b.menu_group_name )? b.menu_group_name: ( b.menu_name )? b.menu_name: '';
            if ( aa < bb ) {
                return -1;
            } else if ( aa > bb ) {
                return 1;
            } else {
                return 0;
            }
        }
    });
}
/*
##################################################
   Menu group HTML
##################################################
*/
menuGroupHtml( menuGroupList ) {
    const ex = this;
    
    let html = ''
    + '<ul class="exportImportList">'
        + '<li class="exportImportItem exportImportAllMenu">'
            + '<div class="exportImportName exportImportAllMenuName">'
                + fn.html.checkboxText('exportImportCheck exportImportCheckAll', 'selectAll', 'selectAll', 'selectAll', {checked: 'checked'}, getMessage.FTE07001 )
            + '</div>'
            + '<ul class="exportImportList exportImportAllMenuList">';
    
    const menuGroup = function( item, className ) {
        const value = item.id,
              id = `menuGroup${item.id}`,
              text = ( !item.error_count )? fn.cv( item.menu_group_name, '', true ):
                      `${fn.cv( item.menu_group_name, '', true )}<span class="exportImportErrorMessage">${fn.html.icon('attention')}${getMessage.FTE07035}</span>`;
        
        
        const openFlag = ( item.unknown || item.error_count )? true: false,
              unknownClass = ( item.unknown )? ' exportImportMenuGroupNameUnkown': '',
              buttonIcon = ( openFlag )? 'minus': 'plus',
              display = ( openFlag )? 'block': 'hidden';
        
        html += ''
        + `<li class="exportImportItem ${className}">`
            + `<div class="exportImportName ${className}Name${unknownClass}">`
                + fn.html.checkboxText(`exportImportCheck exportImportCheckList`, value, 'menuSelectAll', id, {checked: 'checked'}, text )
                + '<div class="exportImportToggleWrap">'
                    + fn.html.iconButton( buttonIcon, getMessage.FTE07002, 'menuGroupToggle')
                + '</div>'
            + '</div>'
            + `<ul class="exportImportList ${className}List" style="display:${display}">`;
        
        menuList( item.menus, value );
        
        html += '</ul>'
        + '</li>';
    };
    
    const menuList = function( list, menuGroupId ) {
        for ( const item of list ) {
            if ( !item.parent_id ) {
                const value = ( ex.type !== 'excelImport')? item.menu_name_rest: item.id,
                      id = `menuItem${item.id}`,
                      text = ( ex.type !== 'excelImport')? fn.cv( item.menu_name, '', true ):
                          `${fn.cv( item.menu_name, '', true )}<span class="exportImportMenuFileName">${fn.cv( item.file_name, '', true )}</span>`;
                
                html += ''
                + '<li class="exportImportItem exportImportMenu">'
                    + '<div class="exportImportName exportImportMenuName">';
                
                if ( ex.type === 'excelImport' && item.error !== null ) {
                    html += `<div class="exportImportError">${text} <div class="exportImportErrorMessage">${fn.html.icon('cross')}${fn.escape( item.error )}</div></div>`;
                } else {
                    html += fn.html.checkboxText('exportImportCheck exportImportCheckItem', value, 'exportItem', id, {checked: 'checked', menuGroup: menuGroupId }, text );
                }

                html += '</div>'
                + '</li>';

            } else {
                menuGroup( item, 'exportImportSubMenuGroup');
            }
        }
    };
    for ( const item of menuGroupList ) {
        menuGroup( item, 'exportImportMenuGroup');
    }
    html += '</ul></li></ul>';
    
    return html;
}
/*
##################################################
   Common Events
##################################################
*/
commonEvents() {
    const ex = this;
    
    // 親兄弟子要素の状態をチェック
    const parentCheck = function( $check ) {
        if ( !$check.is('.exportImportCheckAll') ) {
            // 兄弟要素のチェック
            const $checks = $check.closest('.exportImportList').children('.exportImportItem').children('.exportImportName').find('.exportImportCheck'),
                  checkLength = $checks.length;

            let checkNum = 0, oneOrMoreNum = 0;
            $checks.each(function(){
                const $eachCheck = $( this );
                if ( $eachCheck.prop('checked') ) checkNum++;
                if ( $eachCheck.closest('.checkboxTextWrap').is('.checkboxTextOneOrMore') ) oneOrMoreNum++;
                
            });

            // 親要素のチェック
            const $parentCheckWrap = $check.closest('.exportImportList').prev('.exportImportName').find('.checkboxTextWrap'),
                  $parentCheck = $parentCheckWrap.find('.exportImportCheck');
            $parentCheckWrap.removeClass('checkboxTextOneOrMore');
            if ( $parentCheck.length ) {
                if ( checkLength === checkNum && oneOrMoreNum === 0 ) {
                    $parentCheck.prop('checked', true );
                } else if ( checkNum > 0 ) {
                    $parentCheck.prop('checked', true );
                    $parentCheckWrap.addClass('checkboxTextOneOrMore');
                } else {
                    $parentCheck.prop('checked', false );
                }
                parentCheck( $parentCheck );
            }
        }
    };
    ex.$.content.find('.exportImportCheck').on('change', function() {
        
        const $check = $( this );
        
        parentCheck( $check );
        
        // 子要素のチェックを全て変更する
        if ( $check.is('.exportImportCheckList, .exportImportCheckAll') ) {
            const $wrap = $check.closest('.checkboxTextWrap'),
                  $parent = $check.closest('.exportImportName').next('.exportImportList'),
                  checked = $check.prop('checked');
            $wrap.add( $parent.find('.checkboxTextOneOrMore') ).removeClass('checkboxTextOneOrMore');
            $parent.find('.exportImportCheck').prop('checked', checked );
        }
        
        // ボタン活性化
        if ( ex.type === 'menuExport' || ex.type === 'excelExport') {
            ex.exportButtonCheck();
        } else {
            ex.importButtonCheck();
        }
        
    });
    
    // 詳細ボタン
    ex.$.content.find('.menuGroupToggle').on('click', function(){
        const $button = $( this ),
              $icon = $button.find('.iconButtonIcon'),
              $list = $button.closest('.exportImportName').next('.exportImportList');
        
        if ( $list.is(':visible') ) {
            $list.slideUp( 200 );
            $icon.removeClass('icon-minus');
            $icon.addClass('icon-plus');
        } else {
            $list.slideDown( 200 );
            $icon.removeClass('icon-plus');
            $icon.addClass('icon-minus');
        }
        
    });
}
/*
##################################################
   エクスポート設定　モードテキスト
##################################################
*/
exportModeText( mode ) {
    if ( mode === '1') {
        return getMessage.FTE07016;
    } else {
        return getMessage.FTE07008;
    }
}
/*
##################################################
   エクスポート設定　廃止情報
##################################################
*/
exportDiscardText( discard ) {
    if ( discard === '1') {
        return getMessage.FTE07017;
    } else {
        return getMessage.FTE07018;
    }
}
/*
##################################################
   エクスポート Excel設定　廃止情報
##################################################
*/
exportExcelDiscardText( discard ) {
    if ( discard === '1') {
        return getMessage.FTE07019;
    } else if ( discard === '2') {
        return getMessage.FTE07018;
    } else {
        return getMessage.FTE07020;
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Export
//
////////////////////////////////////////////////////////////////////////////////////////////////////
export() {
    const ex = this;
    
    fn.contentLoadingStart();
    
    // エクスポートリスト取得
    const rest = ( ex.type === 'menuExport')? '/menu/export/info/': '/excel/bulk/export/info/';
    fn.fetch( rest ).then(function( result ){
        if ( result.menu_groups ) {
            ex.$.content.html( ex.exportHtml( ex.createMenuGroupList( result.menu_groups ) ) );
            ex.commonEvents();
            ex.exportEvents();
            ex.exportButtonCheck();
            fn.contentLoadingEnd();
        }
    }).catch(function( error ){
        window.console.error( error );
        fn.gotoErrPage( error.message );
    });
}
/*
##################################################
   Export Events
##################################################
*/
exportEvents() {
    const ex = this;
    
    // 時刻指定
    const $modeTimeInput = ex.$.content.find('.exportModeTime'),
          $modeTimeButton = ex.$.content.find('.inputDateCalendarButton');
    fn.setDatePickerEvent( $modeTimeInput, getMessage.FTE07003 );
    
    // エクスポートモード
    ex.$.content.find('.exportMode').on('change', function(){
        const mode = $( this ).val();
        if ( mode === '2') {
            $modeTimeInput.prop('disabled', false );
            $modeTimeButton.prop('disabled', false );
        } else {
            $modeTimeInput.prop('disabled', true );
            $modeTimeButton.prop('disabled', true );
        }
    });
    
    // エクスポートボタン
    ex.$.content.find('.operationMenu').find('.operationMenuButton').on('click', function(){
        const $button = $( this ),
              exportData = ex.getExportData();
        
        // 確認HTML
        const html = '<div class="commonSection">'
            + `<div class="commonTitle">${getMessage.FTE07004}</div>`
            + '<div class="commonBody">'
                + `<p class="commonParagraph">${getMessage.FTE07005}</p>`
                + '<table class="commonTable">'
                    + '<tbody class="commonTbody">'
                        + '<tr class="commonTr">'
                            + `<th class="commonTh">${getMessage.FTE07006}</th>`
                            + `<td class="commonTd">${exportData.menu.length}</td>`
                        + '</tr>'
                        + `${( ex.type === 'menuExport')?
                            `<tr class="commonTr">`
                                + `<th class="commonTh">${getMessage.FTE07007}</th>`
                                + `<td class="commonTd">${ex.exportModeText( exportData.mode )}</td>`
                            + `</tr>`
                            + `${( exportData.mode === '2')? `<tr class="commonTr"><th class="commonTh">${getMessage.FTE07008}</th><td class="commonTd">${fn.escape( exportData.specified_timestamp )}</td></tr>`: ``}`: ``}`
                        + '<tr class="commonTr">'
                            + `<th class="commonTh">${getMessage.FTE07009}</th>`
                            + `<td class="commonTd">${( ex.type === 'menuExport')? ex.exportDiscardText( exportData.abolished_type ): ex.exportExcelDiscardText( exportData.abolished_type )}</td>`
                        + '</tr>'
                    + '</tbody>'
                + '</table>'
            + '</div>'
        + '</div>';
        
        // エクスポート確認
        fn.alert( getMessage.FTE07010, html, 'common', {
            ok: { text: getMessage.FTE07011, action: 'default', style: 'width:160px', className: 'dialogPositive'},
            cancel: { text: getMessage.FTE07012, action: 'negative', style: 'width:120px'}
        }, '480px').then( function( flag ){
            if ( flag ) {
                const rest = ( ex.type === 'menuExport')? '/menu/bulk/export/execute/': '/excel/bulk/export/execute/',
                      manage = ( ex.type === 'menuExport')? 'menu_export_import_list': 'bulk_excel_export_import_list';
                
                // 読み込み中
                let process = fn.processingModal( getMessage.FTE07013 );
                fn.fetch( rest, null, 'POST', exportData ).then(function( result ){
                    const filter = { execution_no: { NORMAL: result.execution_no } };
                    window.location.href = `?menu=${manage}&filter=${fn.filterEncode( filter )}`;
                }).catch(function( error ){
                    alert( error );
                    process.close();
                    process = null;
                });
            }        
        });
    });
}
/*
##################################################
   Export HTML
##################################################
*/
exportHtml( menuGroupList ) {    
    const ex = this;

    const menu = {
        Main: [
            { button: { icon: 'export', text: getMessage.FTE07014, type: 'export', action: 'positive', width: '200px', disabled: true } },
        ],
        Sub: []
    };
    
    return '<div class="exportImportContainer">'
    + '<div class="exportImportHeader">'
      + fn.html.operationMenu( menu )
    + '</div>'
    + '<div class="exportImportBody">'
        + ex.exportSettingHtml()
        + '<div class="exportImportSelect commonScroll">'
            + '<div class="commonTitle">'
                + getMessage.FTE07015
            + '</div>'
            + ex.menuGroupHtml( menuGroupList )
        +  '</div>'
    + '</div>';
}
/*
##################################################
   Export Setting HTML
##################################################
*/
exportSettingHtml() {
    const ex = this;
    
    if ( ex.type === 'menuExport') {
        return '<div class="exportImportSetting">'
            + '<div class="commonTitle">'
                + getMessage.FTE07004
            + '</div>'
            + '<div class="commonSubTitle">'
                + getMessage.FTE07007
            + '</div>'
            + '<div class="commonBody commonWrap">'
                + fn.html.radioText('exportMode', '1', 'exportMode', 'exportModeEnvironment', {checked: 'checked'}, getMessage.FTE07016 )
                + fn.html.radioText('exportMode', '2', 'exportMode', 'exportModeTime', null, getMessage.FTE07008 )
                + fn.html.dateInput('hm', 'exportModeTime', '', 'exportModeTime', { disabled: 'disabled'})
            + '</div>'
            + '<div class="commonSubTitle">'
                + getMessage.FTE07009
            + '</div>'
            + '<div class="commonBody commonWrap">'
                + fn.html.radioText('exportDiscard', '1', 'exportDiscard', 'exportDiscardInclude', {checked: 'checked'}, getMessage.FTE07017 )
                + fn.html.radioText('exportDiscard', '2', 'exportDiscard', 'exportDiscardNot', null, getMessage.FTE07018 )
            + '</div>'
        + '</div>';
    } else {
        return '<div class="exportImportSetting">'
            + '<div class="commonTitle">'
                + getMessage.FTE07004
            + '</div>'
            + '<div class="commonSubTitle">'
                + getMessage.FTE07009
            + '</div>'
            + '<div class="commonBody commonWrap">'
                + fn.html.radioText('exportDiscard', '1', 'exportDiscard', 'exportDiscardAll', {checked: 'checked'}, getMessage.FTE07019 )
                + fn.html.radioText('exportDiscard', '2', 'exportDiscard', 'exportDiscardNot', null, getMessage.FTE07018 )
                + fn.html.radioText('exportDiscard', '3', 'exportDiscard', 'exportDiscardOnly', null, getMessage.FTE07020 )
            + '</div>'
        + '</div>';
    }
}
/*
##################################################
   Export button check
##################################################
*/
exportButtonCheck() {
    const ex = this;
    
    const flag = ex.$.content.find('.exportImportCheckItem:checked').length? false: true;    
    ex.$.content.find('.operationMenu').find('.operationMenuButton').prop('disabled', flag );
}
/*
##################################################
   Export Data取得
##################################################
*/
getExportData() {
    const ex = this;
    
    const data = {};
    
    const $setting = ex.$.content.find('.exportImportSetting');
          
    data.menu = [];
    ex.$.content.find('.exportImportCheckItem:checked').each(function(){
        data.menu.push( $( this ).val() );
    });
    
    if ( ex.type === 'menuExport') {
        const $mode = $setting.find('.exportMode:checked');
        data.mode = $mode.val();
        if ( data.mode === '2') {
            data.specified_timestamp = $setting.find('.exportModeTime').val();
        }
    }
    const $discard = $setting.find('.exportDiscard:checked');
    data.abolished_type = $discard.val();
    
    return data;
}

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Import
//
////////////////////////////////////////////////////////////////////////////////////////////////////
import() {
    const ex = this;
    
    ex.$.content.html( ex.importHtml() );
    ex.$.importBody = ex.$.content.find('.exportImportBody');
    
    ex.importEvents();
    fn.contentLoadingEnd();
}
/*
##################################################
   Import Events
##################################################
*/
importEvents() {
    const ex = this;
    
    // インポートメニューボタン
    ex.$.content.find('.operationMenu').find('.operationMenuButton').on('click', function(){
        const $button = $( this ),
              type = $button.attr('data-type');
        
        switch ( type ) {
            case 'fileSelect':
                ex.fileSelect();
            break;
            case 'import':
                ex.importModal();
            break;
        }
        
    });
}
/*
##################################################
   File select
##################################################
*/
fileSelect() {
    const ex = this;
    
    const fileExt = ( ex.type === 'excelImport')? '.zip': '.kym',
          fileRest = ( ex.type === 'excelImport')? '/excel/bulk/upload/': `/menu/import/upload/`;
    
    
    fn.fileSelect('base64', null, fileExt ).then(function( selectFile ){
        const postData = ( ex.type === 'excelImport')?
            // エクセルインポート
            { 
                zipfile: {
                    name: selectFile.name,
                    base64: selectFile.base64
                }
            }:
            // メニューインポート
            {
                file: {
                    name: selectFile.name,
                    base64: selectFile.base64
                }
            };
        
        let process = fn.processingModal( getMessage. FTE07036 );
        
        fn.fetch( fileRest, null, 'POST', postData ).then(function( result ){
                        
            // インポートデータ
            ex.importData = result;
            
            let listHtml = '';
            if ( ex.type === 'excelImport') {
                const importList = ex.createMenuGroupList( ex.changeExcelImportList( ex.importData.import_list, ex.importData.umimport_list ) );
                listHtml += ex.menuGroupHtml( importList );
            } else {
                const importList = ex.createMenuGroupList( ex.importData.import_list.menu_groups );
                listHtml += ex.menuGroupHtml( importList );
            }
            
            ex.$.importBody.html(
                ex.importSettingHtml()
                + '<div class="exportImportSelect">'
                    + '<div class="commonTitle">'
                        + getMessage.FTE07022
                    + '</div>'
                    + listHtml
                +  '</div>');
            
            ex.commonEvents();            
        }).catch(function( error ){
            window.console.error( error );
            if ( error.message ) {
                alert( error.message );
            } else {
                alert( getMessage.FTE07023 );
            }
            ex.$.importBody.html( ex.initBodyHtml() );
        }).then(function(){
            process.close();
            process = null;
            
            ex.importButtonCheck();
        });
    }).catch(function( error ){
        if ( error !== 'cancel') {
        
        }
    });
    
}
/*
##################################################
   Import HTML
##################################################
*/
importHtml() {    
    const ex = this;

    const menu = {
        Main: [
            { button: { icon: 'note', text: getMessage.FTE07024, type: 'fileSelect', action: 'default', width: '200px'} },
            { button: { icon: 'import', text: getMessage.FTE07025, type: 'import', action: 'positive', width: '200px', disabled: true } },
        ],
        Sub: []
    };
    
    return '<div class="exportImportContainer">'
    + '<div class="exportImportHeader">'
      + fn.html.operationMenu( menu )
    + '</div>'
    + '<div class="exportImportBody">'
        + ex.initBodyHtml()
    + '</div>';
}
/*
##################################################
   Message HTML
##################################################
*/
initBodyHtml() {
    return ''
    + '<div class="commonMessage">'
        + '<div class="commonMessageInner">'
            + '<span class=" icon icon-circle_info"></span>' + getMessage.FTE07026
        + '</div>'
    + '</div>';
}
/*
##################################################
   Import Setting HTML
##################################################
*/
importSettingHtml() {
    const ex = this;
    
    const fileName = ( ex.type === 'menuImport')? ex.importData.file_name: ex.importData.data_portability_upload_file_name;
    
    let html = ''
    + '<div class="exportImportSetting">'
        + '<div class="commonTitle">'
            + getMessage.FTE07027
        + '</div>'
        + '<div class="commonBody commonWrap">'
            + '<dl class="commonStatus">'
                + `<dt class="commonStatusKey">${getMessage.FTE07028}</dt>`
                + '<dd class="commonStatusValue">'
                    + fn.cv( fileName, '', true )
                + '</dd>'
            + '</dl>';
    
    if ( ex.type === 'menuImport') {
        html += ''
            + '<dl class="commonStatus">'
                + `<dt class="commonStatusKey">${getMessage.FTE07007}</dt>`
                + '<dd class="commonStatusValue">'
                    + ex.exportModeText( ex.importData.mode )
                + '</dd>'
            + '</dl>';
        if ( ex.importData.specified_time ) {
            html += ''
            + '<dl class="commonStatus">'
                + `<dt class="commonStatusKey">${getMessage.FTE07008}</dt>`
                + '<dd class="commonStatusValue">'
                    + fn.cv( ex.importData.specified_time, '', true )
                + '</dd>'
            + '</dl>';
        }
        html += ''
            + '<dl class="commonStatus">'
                + `<dt class="commonStatusKey">${getMessage.FTE07009}</dt>`
                + '<dd class="commonStatusValue">'
                    + ex.exportDiscardText( ex.importData.abolished_type )
                + '</dd>'
            + '</dl>';
    }
    html += '</div>'
    + '</div>';
    
    return html;
}
/*
##################################################
   Import button check
##################################################
*/
importButtonCheck() {
    const ex = this;
    
    const flag = ex.$.importBody.find('.exportImportCheckItem:checked').length? false: true;    
    ex.$.content.find('.operationMenu').find('.operationMenuButton[data-type="import"]').prop('disabled', flag );
}
/*
##################################################
   Import
##################################################
*/
importModal() {
    const ex = this;
    
    // Importリスト作成
    const restData = {};
    
    let fileName = '',
        menuCount = 0;
    
    if ( ex.type === 'excelImport') {
        // Excel インポート
        const menu = {};
        ex.$.content.find('.exportImportCheckItem:checked').each(function(){
            const $item = $( this ),
                  value = $item.val(),
                  group = $item.attr('data-menuGroup');
            
            if ( !menu[ group ] ) menu[ group ] = [];
            menu[ group ].push( value );
            menuCount++;
        });
        restData.menu = menu;
        restData.upload_id = ex.importData.upload_id;
        restData.data_portability_upload_file_name = ex.importData.data_portability_upload_file_name;
        fileName = ex.importData.data_portability_upload_file_name;
    } else {
        // Menu インポート
        const menu = [];
        ex.$.content.find('.exportImportCheckItem:checked').each(function(){
            menu.push( $( this ).val() );
            menuCount++;
        });
        restData.menu = menu;
        restData.upload_id = ex.importData.upload_id;
        restData.file_name = ex.importData.file_name;
        fileName = ex.importData.file_name;
    }
    
    // 確認HTML
    let html = ``
    + `<div class="commonSection">`
        + `<div class="commonTitle">${getMessage.FTE07021}</div>`
        + `<div class="commonBody">`
            + `<p class="commonParagraph">${getMessage.FTE07029}</p>`
            + `<table class="commonTable">`
                + `<tbody class="commonTbody">`
                    + `<tr class="commonTr">`
                        + `<th class="commonTh">${getMessage.FTE07028}</th>`
                        + `<td class="commonTd">${fn.escape( fileName )}</td>`
                    + `</tr>`
                    + `<tr class="commonTr">`
                        + `<th class="commonTh">${getMessage.FTE07006}</th>`
                        + `<td class="commonTd">${menuCount}</td>`
                    + `</tr>`;
    if ( ex.type === 'menuImport') {
        html += ``
                    + `<tr class="commonTr">`
                        + `<th class="commonTh">${getMessage.FTE07007}</th>`
                        + `<td class="commonTd">${ex.exportModeText( ex.importData.mode )}</td>`
                    + `</tr>`
                    + `${( ex.importData.mode === '2')? `<tr class="commonTr"><th class="commonTh">${getMessage.FTE07008}</th><td class="commonTd"></td></tr>`: ``}`
                    + `<tr class="commonTr">`
                        + `<th class="commonTh">${getMessage.FTE07009}</th>`
                        + `<td class="commonTd">${ex.exportDiscardText( ex.importData.abolished_type )}</td>`
                    + `</tr>`;
    }
    html += ``
                + `</tbody>`
            + `</table>`
        + `</div>`
    + `</div>`;
    
    // インポート確認
    fn.alert( getMessage.FTE07030, html, 'common', {
        ok: { text: getMessage.FTE07031, action: 'default', style: 'width:160px', className: 'dialogPositive'},
        cancel: { text: getMessage.FTE07012, action: 'negative', style: 'width:120px'}
    }, '480px').then( function( flag ){
        if ( flag ) {
            const rest = ( ex.type === 'menuImport')? '/menu/import/execute/': '/excel/bulk/import/execute/',
                  manage = ( ex.type === 'menuImport')? 'menu_export_import_list': 'bulk_excel_export_import_list';
            let process = fn.processingModal( getMessage.FTE07032 );
            fn.fetch( rest, null, 'POST', restData ).then(function( result ){
                const filter = { execution_no: { NORMAL: result.execution_no } };
                window.location.href = `?menu=${manage}&filter=${fn.filterEncode( filter )}`;
            }).catch(function( error ){
                window.console.error( error );
                alert( getMessage.FTE07033 );
                process.close();
                process = null;
            });
        }        
    });
}
/*
##################################################
   Excelインポートリストの形式を変更
##################################################
*/
changeExcelImportList( importList, unImportList ) {
    const afterList = [];
    
    // 二つのリストを結合する
    const unImporOnlyKeys = [],
          importKeys = Object.keys( importList ),
          unImportKeys = Object.keys( unImportList );
    
    for ( const key of unImportKeys ) {
        if ( importKeys.indexOf( key ) === -1 ) unImporOnlyKeys.push( key );
    }
    
    for ( const key in importList ) {
        if ( unImportList[ key ] ) {
            for ( const num in unImportList[ key ].menu ) {
                const menuId = 'un_import_' + unImportList[ key ].menu[ num ].menu_id;
                importList[ key ].menu[ menuId ] = unImportList[ key ].menu[ num ];
            }
        }
    }
    
    for ( const key of unImporOnlyKeys ) {
        importList[ key ] = unImportList[ key ];
    }    

    for ( const key in importList ) {
        const menus = [];
        let errorCount = 0;
        if ( importList[ key ].menu ) {
            for ( const menu in importList[ key ].menu ) {
                const data = importList[ key ].menu[ menu ],
                      error = fn.cv( data.error, null );
                
                if ( error !== null ) errorCount++;
                menus.push({
                    disp_seq: fn.cv( data.disp_seq, null ),
                    id: fn.cv( data.menu_id, null ),
                    menu_name: fn.cv( data.menu_name, null ),
                    file_name: fn.cv( data.file_name, null ),
                    error: fn.cv( data.error, null )
                })
            }
        }
        afterList.push({
            disp_seq: fn.cv( importList[ key ].disp_seq, null ),
            id: key,
            menu_group_name: fn.cv( importList[ key ].menu_group_name, null ),
            menus: menus,
            parent_id: fn.cv( importList[ key ].parent_id, null ),
            error_count: errorCount
        });
    }
    
    return afterList;
}

}