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
    console.log(tempMenuGroups)
    // 親と子を分ける
    for ( const menuGroup of tempMenuGroups ) {
        if ( menuGroup.parent_id === null ) {
            menuGroupList.push( menuGroup );
        } else {
            childs.push( menuGroup );
        }
    }
    
    // 親に子を追加
    for ( const parent of menuGroupList ) {
        for ( const child of childs ) {
            if ( parent.id === child.parent_id ) {
                child.main_menu_rest = null;
                if ( child.menus && child.menus.length ) {
                    ex.dispSeqSort( child.menus );
                    if ( child.menus[0].menu_name_rest ) {
                         child.main_menu_rest = child.menus[0].menu_name_rest;
                    }
                }
                parent.menus.push( child );
            }
        }
        ex.dispSeqSort( parent.menus );
  
        parent.main_menu_rest = null;
        let subRest = null;
        for ( const menu of parent.menus ) {
            if ( menu.menu_name_rest && parent.main_menu_rest === null ) {
                parent.main_menu_rest = menu.menu_name_rest;
            } else if ( menu.menus && menu.menus.length && menu.menus[0].menu_name_rest ) {
                subRest = menu.menus[0].menu_name_rest;
            }
        }
        if ( !parent.main_menu_rest && subRest ) parent.main_menu_rest = subRest;
    }
    ex.dispSeqSort( menuGroupList );
    
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
    let html = ''
    + '<ul class="exportImportList">'
        + '<li class="exportImportItem exportImportAllMenu">'
            + '<div class="exportImportName exportImportAllMenuName">'
                + fn.html.checkboxText('exportImportCheck exportImportCheckAll', 'selectAll', 'selectAll', 'selectAll', {checked: 'checked'}, getMessage.FTE07001 )
            + '</div>'
            + '<ul class="exportImportList exportImportAllMenuList">';
    
    const menuGroup = function( item, className ) {
        const id = `menuGroup${item.id}`;
        html += ''
        + '<li class="exportImportItem ' + className + '">'
            + '<div class="exportImportName ' + className + 'Name">'
                + fn.html.checkboxText('exportImportCheck exportImportCheckList', id, 'menuSelectAll', id, {checked: 'checked'}, item.menu_group_name )
                + '<div class="exportImportToggleWrap">'
                    + fn.html.iconButton('plus', getMessage.FTE07002, 'menuGroupToggle')
                + '</div>'
            + '</div>'
            + '<ul class="exportImportList ' + className + 'List">';
        
        menuList( item.menus );
        
        html += '</ul>'
        + '</li>';
    };
    
    const menuList = function( list ) {
        for ( const item of list ) {
            if ( !item.parent_id ) {
                html += ''
                + '<li class="exportImportItem exportImportMenu">'
                    + '<div class="exportImportName exportImportMenuName">'
                        + fn.html.checkboxText('exportImportCheck exportImportCheckItem', item.menu_name_rest, 'exportItemt', item.menu_name_rest, {checked: 'checked'}, item.menu_name )
                    + '</div>'
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

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Export
//
////////////////////////////////////////////////////////////////////////////////////////////////////
export() {
    const ex = this;
    
    fn.contentLoadingStart();
    
    // エクスポートリスト取得
    fn.fetch('/menu/export/info/').then(function( result ){
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
              exportData = ex.createExportData();
        
        // 確認HTML
        const html = '<div class="commonSection">'
            + `<div class="commonTitle">${getMessage.FTE07004}</div>`
            + '<div class="commonBody">'
                + `<p class="commonParagraph">${getMessage.FTE07005}</p>`
                + '<table class="commonTable">'
                    + '<tbody class="commonTbody">'
                        + '<tr class="commonTr">'
                            + `<th class="commonTh">${getMessage.FTE07006}</th>`
                            + `<td class="commonTd">${exportData.rest.menu.length}</td>`
                        + '</tr>'
                        + `${( ex.type === 'menuExport')?
                            `<tr class="commonTr">`
                                + `<th class="commonTh">${getMessage.FTE07007}</th>`
                                + `<td class="commonTd">${exportData.text.mode}</td>`
                            + `</tr>`
                            + `${( exportData.rest.mode === '2')? `<tr class="commonTr"><th class="commonTh">${getMessage.FTE07008}</th><td class="commonTd">${fn.escape( exportData.rest.specified_timestamp )}</td></tr>`: ``}`: ``}`
                        + '<tr class="commonTr">'
                            + `<th class="commonTh">${getMessage.FTE07009}</th>`
                            + `<td class="commonTd">${exportData.text.abolished_type}</td>`
                        + '</tr>'
                    + '</tbody>'
                + '</table>'
            + '</div>'
        + '</div>';
        
        fn.alert( getMessage.FTE07010, html, 'common', {
            ok: { text: getMessage.FTE07011, action: 'default', style: 'width:160px', className: 'dialogPositive'},
            cancel: { text: getMessage.FTE07012, action: 'negative', style: 'width:120px'}
        }, '400px').then( function( flag ){
            if ( flag ) {
                const rest = ( ex.type === 'menuExport')? '/menu/bulk/export/execute/': '/excel/bulk/export/execute/',
                      manage = ( ex.type === 'menuExport')? 'menu_export_import_list': 'bulk_excel_export_import_list';
                const processing = fn.processingModal( getMessage.FTE07013 );
                fn.fetch( rest, null, 'POST', exportData.rest ).then(function( result ){
                    const filter = { execution_no: { NORMAL: result.execution_no } };
                    window.location.href = `?menu=${manage}&filter=${fn.filterEncode( filter )}`;
                }).catch(function( error ){
                    alert( error );
                    processing.close();
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
            + '<div class="commonBody">'
                + fn.html.radioText('exportMode', '1', 'exportMode', 'exportModeEnvironment', {checked: 'checked'}, getMessage.FTE07016 )
                + fn.html.radioText('exportMode', '2', 'exportMode', 'exportModeTime', null, getMessage.FTE07008 )
                + fn.html.dateInput('hm', 'exportModeTime', '', 'exportModeTime', { disabled: 'disabled'})
            + '</div>'
            + '<div class="commonSubTitle">'
                + getMessage.FTE07009
            + '</div>'
            + '<div class="commonBody">'
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
            + '<div class="commonBody">'
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
   Export Data
##################################################
*/
createExportData() {
    const ex = this;
    
    const data = {
              rest: {},
              text: {}
          },
          $setting = ex.$.content.find('.exportImportSetting');
    
    data.rest['menu'] = [];
    ex.$.content.find('.exportImportCheckItem:checked').each(function(){
        data.rest['menu'].push( $( this ).val() );
    });
    
    if ( ex.type === 'menuExport') {
        const $mode = $setting.find('.exportMode:checked');
        data.rest['mode'] = $mode.val();
        data.text['mode'] = $mode.next().text();
        if ( data.rest['mode'] === '2') {
            data.rest['specified_timestamp'] = $setting.find('.exportModeTime').val();
        }
    }
    const $discard = $setting.find('.exportDiscard:checked');
    data.rest['abolished_type'] = $discard.val();
    data.text['abolished_type'] = $discard.next().text();
    
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
    
    fn.fileSelect('base64', null, '.kym').then(function( selectFile ){
        const postData = ( ex.type === 'excelImport')? { excel: selectFile.base64 }: selectFile.json;
        
        fn.fetch('dummy').then(function(){
            const result = fileselectDummy.data; // ダミーデータ
            
            // インポートデータ
            ex.importData = result;
            
            // メニューグループリスト
            const menuGroupList = ex.createMenuGroupList( ex.importData.import_list.menu_groups );

            ex.$.importBody.html(
                ex.importSettingHtml()
                + '<div class="exportImportSelect">'
                    + '<div class="commonTitle">'
                        + getMessage.FTE07022
                    + '</div>'
                    + ex.menuGroupHtml( menuGroupList )
                +  '</div>');
            
            ex.commonEvents();
            ex.importButtonCheck();
            
        }).catch(function( error ){
            window.console.error( error );
            alert( getMessage.FTE07023 );
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
        + '<div class="commonMessage">'
            + '<div class="commonMessageInner">'
                + '<span class=" icon icon-circle_info"></span>' + getMessage.FTE07026
            + '</div>'
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
    
    const modeHtml = function(){
        if ( ex.importData.mode === '1') {
            return getMessage.FTE07016;
        } else {
            return getMessage.FTE07008;
        }
    };
    
    const discardHtml = function(){
        if ( ex.importData.abolished_type === '1') {
            return getMessage.FTE07017;
        } else {
            return getMessage.FTE07018;
        }
    };
    
    let html = ''
    + '<div class="exportImportSetting">'
        + '<div class="commonTitle">'
            + getMessage.FTE07027
        + '</div>'
        + '<div class="commonBody">'
            + '<dl class="commonStatus">'
                + `<dt class="commonStatusKey">${getMessage.FTE07028}</dt>`
                + '<dd class="commonStatusValue">'
                    + fn.cv( ex.importData.file_name, '', true )
                + '</dd>'
            + '</dl>';
    
    if ( ex.type === 'menuImport') {
        html += ''
            + '<dl class="commonStatus">'
                + `<dt class="commonStatusKey">${getMessage.FTE07007}</dt>`
                + '<dd class="commonStatusValue">'
                    + modeHtml()
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
    }
    
    html += ''
            + '<dl class="commonStatus">'
                + `<dt class="commonStatusKey">${getMessage.FTE07009}</dt>`
                + '<dd class="commonStatusValue">'
                    + discardHtml()
                + '</dd>'
            + '</dl>'
        + '</div>'
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
    
    const menu = [];
    ex.$.content.find('.exportImportCheckItem:checked').each(function(){
        menu.push( $( this ).val() );
    });
    
    
    // 確認HTML
    const html = '<div class="commonSection">'
        + `<div class="commonTitle">${getMessage.FTE07021}</div>`
        + '<div class="commonBody">'
            + `<p class="commonParagraph">${getMessage.FTE07029}</p>`
            + '<table class="commonTable">'
                + '<tbody class="commonTbody">'
                    + '<tr class="commonTr">'
                        + `<th class="commonTh">${getMessage.FTE07006}</th>`
                        + `<td class="commonTd">${menu.length}</td>`
                    + '</tr>'
                    + `${( ex.type === 'menuImport')?
                        `<tr class="commonTr">`
                            + `<th class="commonTh">${getMessage.FTE07007}</th>`
                            + `<td class="commonTd"></td>`
                        + `</tr>`
                        + `${( ex.importData.mode === '2')? `<tr class="commonTr"><th class="commonTh">${getMessage.FTE07008}</th><td class="commonTd"></td></tr>`: ``}`: ``}`
                    + '<tr class="commonTr">'
                        + `<th class="commonTh">${getMessage.FTE07009}</th>`
                        + `<td class="commonTd"></td>`
                    + '</tr>'
                + '</tbody>'
            + '</table>'
        + '</div>'
    + '</div>';

    fn.alert( getMessage.FTE07030, html, 'common', {
        ok: { text: getMessage.FTE07031, action: 'default', style: 'width:160px', className: 'dialogPositive'},
        cancel: { text: getMessage.FTE07012, action: 'negative', style: 'width:120px'}
    }, '400px').then( function( flag ){
        if ( flag ) {
            const restData = {
                menu: menu,
                upload_id: ex.importData.upload_id,
                file_name: ex.importData.file_name
            };
            const rest = ( ex.type === 'menuImport')? '/menu/import/execute/': '/excel/bulk/import/execute/',
                  manage = ( ex.type === 'menuImport')? 'menu_export_import_list': 'bulk_excel_export_import_list';
            const processing = fn.processingModal( getMessage.FTE07032 );
            fn.fetch( rest, null, 'POST', restData ).then(function( result ){
                const filter = { execution_no: { NORMAL: result.execution_no } };
                window.location.href = `?menu=${manage}&filter=${fn.filterEncode( filter )}`;
            }).catch(function( error ){
                window.console.error( error );
                alert( getMessage.FTE07033 );
                processing.close();
            });
        }        
    });
}

}