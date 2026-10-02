////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Exastro IT Automation / create_menu.js
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
class CreateMenu {
/*
##################################################
    Constructor
##################################################
*/
constructor( target, userInfo ) {
    this.target = target;
    this.menuCreateUserInfo = userInfo;
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Setup
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    初期値
##################################################
*/
columnMinWidth = 260
stringMaxByte = 65536
linkMaxByte = 8192
maxItem = 1000
/*
##################################################
    Setup
##################################################
*/
async setup() {
    // クエリパラメータ
    const params = fn.getParams();
    this.menu = params.menu ?? ''; // メニュー
    this.loadMenuID = params.menu_name_rest ?? ''; // 対象メニュー
    this.editorMode = 'new'; // 初期モード
    this.createManagementMenuID = params.history_id ?? ''; // 履歴ID

    // モード
    if ( this.loadMenuID !== '') {
        if ( params.mode !== undefined ) {
            this.editorMode = params.mode;
        } else {
            this.editorMode = 'view';
        }
    }

    // HTMLセット
    const $target = $( this.target );
    $target.html( this.createMainHtml() );

    // 必要なデータ読み込み
    const url = ( this.loadMenuID !== '')? `/create/define/${this.loadMenuID}`: `/create/define/`;
    try {
        this.menuEditorArray = await fn.fetch( url );
        this.nameConvertList = this.menuEditorArray.name_convert_list;
    } catch ( error ) {
        console.error( error );
        if ( error.message ) alert( error.message );
        return;
    }

    // jQueryオブジェクト
    this.$ = {
        target: $target,
        body: $('body'),
        editor: $target.find('#menu-editor'),
        menuEditWindow: $target.find('#menu-editor-edit'),
        menuTable: $target.find('.menu-table'),
        previewWrap: $target.find('.tableWrap'),
        previewTable: $target.find('.previewBodyGroupBody'),
        property: $('#property'),
        style: $('#menu-editor-style'),
        menuType: $('#create-menu-type'),
        counter: $target.find('.menu-editor-item-counter-number')
    };

    // 作成対象選択HTML
    if ( this.editorMode !== 'view') {
        this.$.menuType.html( this.panelMenuTypeHtml() );
    }

    // 共通パラメータ
    this.commonParams = fn.getCommonParams();

    // メニュー表示データ
    this.menuMap = new Map();

    // 最大ファイルサイズ
    this.fileMaxSize = this.menuEditorArray.org_upload_file_size_limit ?? 104857600;

    // メニュー階層データ
    this.floor = [];

    // 一意制約(複数項目)
    this.menuEditorArray['unique-constraints-current'] = null;

    // モード別無効フラグ
    this.modeDisabled = ( this.editorMode === 'view');
    this.modeKeepData = ( this.editorMode === 'edit');

    // プルダウン選択初期値
    this.pulldownSelectionDefaultValue = {};

    // カウンター
    this.columnCounter = 1;
    this.groupCounter = 1;

    // 初期設定
    this.createItemIntersectionObserver();
    this.setTemplates();
    this.setEditorEvents();
    this.initUndoRedo();
    this.history.clear();

    if ( this.editorMode === 'new' ) {
        this.initialMenuGroup();
        this.addItem('column');
        this.updatePreviewType();
        this.setColumnHeaderStyle();
        this.$.editor.removeClass('load-wait');
    } else {
        await this.setMenu();
    }
    this.$.editor.find('.textareaAdjustment').each( fn.textareaAdjustment );
}
// メニューグループ初期値
initialMenuGroup() {
    const forInputID = '502', // 入力用
        forSubstitutionID = '503', // 代入値自動登録用
        forReference = '504', // 参照用
        forInputName = this.listIdName( 'group', forInputID ),
        forSubstitutionName = this.listIdName( 'group', forSubstitutionID ),
        forReferenceName = this.listIdName( 'group', forReference );

    // 入力用
    if ( forInputName !== null ) {
        $('#create-menu-for-input')
            .attr('data-id', forInputID )
            .text( forInputName );
    }
    // 代入値自動登録用
    if ( forSubstitutionName !== null ) {
        $('#create-menu-for-substitution')
            .attr('data-id', forSubstitutionID )
            .text( forSubstitutionName );
    }
    // 参照用
    if ( forReferenceName !== null ) {
        $('#create-menu-for-reference')
            .attr('data-id', forReference )
            .text( forReferenceName );
    }
    // ロールの初期値を入れる
    if ( this.menuEditorArray.role_list !== undefined ) {
        const roleDefault = new Array;
        const roleLength = this.menuEditorArray.role_list.length;
        const roleCheckList = this.menuCreateUserInfo.roles;
        for (let i = 0; i < roleCheckList.length; i++) {
            for (let j = 0; j < roleLength; j++) {
                if (roleCheckList[i] === this.menuEditorArray.role_list[j]) {
                    roleDefault.push(this.menuEditorArray.role_list[j]);
                }
            }
        }
        const newRoleList = roleDefault.join(',');
        $('#permission-role-name-list').text( newRoleList ).attr('data-role-id', newRoleList );
    }
}
// 各種IDから名称を返す
listIdName( type, id ) {
    let list, idKey, nameKey, name;
    if ( type === 'input') {
        list = this.menuEditorArray.column_class_list;
        idKey = 'column_class_id';
        nameKey = 'column_class_disp_name';
    } else if ( type === 'pulldown') {
        list = this.menuEditorArray.pulldown_item_list;
        idKey = 'link_id';
        nameKey = 'link_pulldown';
    } else if ( type === 'target') {
        list = this.menuEditorArray.sheet_type_list;
        idKey = 'sheet_type_id';
        nameKey = 'sheet_type_name';
    } else if ( type === 'group') {
        list = this.menuEditorArray.target_menu_group_list;
        idKey = 'menu_group_id';
        nameKey = 'full_menu_group_name';
    } else if ( type === 'role') {
        list = this.menuEditorArray.role_list;
    }

    const listLength = list.length;
    for ( let i = 0; i < listLength; i++ ) {
        if( type !== 'role' ){
            if ( String( list[i][idKey] ) === String( id ) ) {
                name = list[i][nameKey];
                return name;
            }
        } else {
            if ( list[i] === id ) {
                name = list[i]
                return name;
            }
        }
    }
    return null;
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   操作モード
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    操作モード変更
    operationMode:
        blockResize or columnResize or columnMove
##################################################
*/
operationModeChange( operationMode ) {
    if ( operationMode !== undefined ) {
        this.$.body.attr('data-mode', operationMode );
        this.$.menuTable.addClass('hover-disabled');
    } else {
        this.$.body.attr('data-mode', '');
        this.$.menuTable.removeClass('hover-disabled');
    }
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   イベント
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    イベントセット
##################################################
*/
setEditorEvents() {
    this.editorMenuEvent();
    this.editorTabEvent();
    this.editotWindowResizeEvent();
    this.editorFullScreen();

    // 項目
    this.itemWidthChengeEvent();
    this.itemHoverEvent();
    this.itemNoteEvent();
    this.itemCalendarEvent();
    this.itemTitleInputEvent();
    this.itemCopyDeleteEvent();
    this.itemReferenceItemSelectEvent();
    this.itemDisplaySettingEvent();

    this.itemInputChangeEvent();
    this.itemSetSelect2Event();
    this.itemMoveEvent();

    // パネル
    this.setPanelEvents();
}
/*
##################################################
    登録チェック
##################################################
*/
checkErrorMenuTable() {
    // 空のグループ
    const emptySize = this.$.menuTable.find('.menu-column-group-body > .column-empty').length;
    if ( emptySize > 0 ) {
        alert( getMessage.FTE01160 );
        return true;
    }
    // グループ・項目数
    const itemSize = this.getItemSize();
    if ( itemSize > this.maxItem ) {
        alert( getMessage.FTE01161( this.maxItem ) );
        return true;
    }
    return false;
}
/*
##################################################
    メニュー
##################################################
*/
editorMenuEvent() {
    this.$.editor.find('.menu-editor-menu-button').on('click', ( e ) => {
        const $button = $( e.currentTarget );
        const type = $button.attr('data-type');

        switch ( type ) {
            // 作成
            case 'registration': {
                if ( this.checkErrorMenuTable() ) return;
                $button.prop('disabled', true );
                fn.iconConfirm('plus', getMessage.FTE10059, getMessage.FTE01136 ).then( ( flag ) => {
                    if ( flag ) {
                        this.registrationMenu('create_new').catch( ( e ) => {
                            if ( e ) console.error( e );
                            $button.prop('disabled', false );
                        });
                    } else {
                        $button.prop('disabled', false );
                    }
                });
                } break;
            // 作成(初期化)
            case 'update-initialize': {
                if ( this.checkErrorMenuTable() ) return;
                $button.prop('disabled', true );
                // メニュー作成状態が「未作成」の場合、windowメッセージを変更
                if ( this.menuEditorArray.menu_info.menu.menu_create_done_status_id == 1 ){
                    fn.iconConfirm('plus', getMessage.FTE10059, getMessage.FTE01136 ).then( ( flag ) => {
                        if ( flag ) {
                            this.registrationMenu('create_new').catch( ( e ) => {
                                if ( e ) console.error( e );
                                $button.prop('disabled', false );
                            });
                        } else {
                            $button.prop('disabled', false );
                        }
                    });
                } else {
                    fn.iconConfirm('plus', getMessage.FTE10059, getMessage.FTE01137 ).then( ( flag ) => {
                        if ( flag ) {
                            this.registrationMenu('initialize').catch( ( e ) => {
                                if ( e ) console.error( e );
                                $button.prop('disabled', false );
                            });
                        } else {
                            $button.prop('disabled', false );
                        }
                    });
                }
                } break;
            // 作成(編集)
            case 'update': {
                if ( this.checkErrorMenuTable() ) return;
                $button.prop('disabled', true );
                fn.iconConfirm('plus', getMessage.FTE10059, getMessage.FTE01138 ).then( ( flag ) => {
                    if ( flag ) {
                        this.registrationMenu('edit').catch( ( e ) => {
                            if ( e ) console.error( e );
                            $button.prop('disabled', false );
                        });
                    } else {
                        $button.prop('disabled', false );
                    }
                });
                } break;
            // uuidでフィルターされたメニュー作成履歴画面へ移動
            case 'management':
                this.pageMoveHistory();
                break;
            // 初期化モードで開きなおす
            case 'initialize':
            case 'reload-initialize':
                this.pageMoveModeChange('initialize');
                break;
            // 編集モードで開きなおす
            case 'edit':
            case 'reload':
                this.pageMoveModeChange('edit');
                break;
            // 流用新規モードで開きなおす
            case 'diversion':
                this.pageMoveModeChange('diversion');
                break;
            // 閲覧モードで開きなおす
            case 'cancel':
                this.pageMoveModeChange();
                break;
            // エディタメニュー
            case 'newColumn': this.addItem('column'); break;
            case 'newColumnGroup': this.addItem('group'); break;
            case 'jsonRead': this.jsonRead(); break;
            case 'jsonSave': this.jsonSave(); break;
            case 'undo': this.history.undo(); break;
            case 'redo': this.history.redo(); break;
            case 'fullscreen': fn.fullScreen(); break;
        }
    });
}
// ページ移動（履歴）
pageMoveHistory() {
    const menu = 'menu_creation_history';
    const uuid = fn.getParams().history_id;
    const filter = fn.filterEncode({"uuid":{"NORMAL": uuid }} );
    const orgId = this.commonParams.organizationId;
    const wsId = this.commonParams.workspaceId;
    const href = `/${orgId}/workspaces/${wsId}/ita/?menu=${menu}&filter=${filter}`;
    location.replace( href );
}
// ページ移動（モード変更）
pageMoveModeChange( mode ) {
    const targetId = $('#menu-editor').attr('data-load-menu-id');
    const menu = fn.getParams().menu;
    const orgId = this.commonParams.organizationId;
    const wsId = this.commonParams.workspaceId;
    const href = `/${orgId}/workspaces/${wsId}/ita/?menu=${menu}&menu_name_rest=${targetId}`;
    const modeParam = ( mode )? `&mode=${mode}`: '';
    window.location.href = href + modeParam;
}
/*
##################################################
    フルスクリーン
##################################################
*/
editorFullScreen() {
    document.onfullscreenchange = document.onmozfullscreenchange = document.onwebkitfullscreenchange = document.onmsfullscreenchange = () => {
        if( fn.fullScreenCheck() ){
            this.$.body.addClass('editor-full-screen');
        } else {
            this.$.body.removeClass('editor-full-screen');
        }
    }
}
/*
##################################################
    タブ切り替え
##################################################
*/
editorTabEvent() {
    $('.editor-tab').each( function() {
        const $tab = $( this );
        const $tabItem = $tab.find('.editor-tab-menu-item');
        const $tabBody = $tab.find('.editor-tab-body');

        $tabItem.eq(0).addClass('selected');
        $tabBody.eq(0).addClass('selected');

        $tabItem.on('click', function() {
            const $clickTab = $( this );
            const $openTab = $('#' + $clickTab.attr('data-tab') );
            $tab.find('.selected').removeClass('selected');
            $clickTab.add( $openTab ).addClass('selected');
        });
    });
}
/*
##################################################
    エディターウインドウリサイズ
##################################################
*/
editotWindowResizeEvent() {
    $('#menu-editor-row-resize').on('mousedown', ( e1 ) => {
        // 全ての選択を解除する
        getSelection().removeAllRanges();
        this.operationModeChange('blockResize');

        const $window = $( window );
    
        const $resizeBar = $( e1.currentTarget );
        const $resizeBlocks = this.$.editor.find('.menu-editor-block');
        const $section1 = $resizeBlocks.eq(0);
        const $section2 = $resizeBlocks.eq(1);
        const initialPoint = e1.clientY;
        const minHeight = 64;
    
        let movePoint = 0;
        let newSection1Height = 0;
    
        // 高さを一旦固定値に
        $resizeBlocks.each( function() {
            const $resizeBlock = $( this );
            $resizeBlock.css('height', $resizeBlock.outerHeight() );
        });
    
        const initialSection1Height = newSection1Height = $section1.outerHeight();
        const initialHeight = initialSection1Height + $section2.outerHeight();
        const maxHeight = initialHeight - minHeight;
    
        $window.on({
            'mousemove.sizeChange' : ( e2 ) => {
                movePoint = e2.clientY - initialPoint;
                newSection1Height = initialSection1Height + movePoint;
    
                if ( newSection1Height < minHeight ) {
                    newSection1Height = minHeight;
                    movePoint = minHeight - initialSection1Height;
                } else if ( newSection1Height > maxHeight ) {
                    newSection1Height = maxHeight;
                    movePoint = maxHeight - initialSection1Height;
                }
        
                $section1.css('height', newSection1Height );
                $section2.css('height', initialHeight - newSection1Height );
                $resizeBar.css('transform','translateY(' + movePoint + 'px)');
            },    
            'mouseup.sizeChange' : () => {
                $window.off('mousemove.sizeChange mouseup.sizeChange');
                this.operationModeChange();
        
                // 高さを割合に戻す
                const section1Ratio = newSection1Height / initialHeight * 100;
                $section1.css('height', section1Ratio + '%' );
                $section2.css('height', ( 100 - section1Ratio ) + '%' );
                $resizeBar.css({
                    'transform' : 'translateY(0)',
                    'top' : section1Ratio + '%'
                });
            }
        });
    });
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   エディタベント
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    項目横幅変更
##################################################
*/
itemWidthChengeEvent() {
    const $columnResizeLine = $('#column-resize');
    this.$.menuTable.on('mousedown.itemWidthChange', '.column-resize', ( e ) => {
        // 左クリックチェック
        if ( e.which !== 1 ) return false;

        this.operationModeChange('columnResize');

        const $window = $( window );
        const $column = $( e.currentTarget ).closest('.menu-column');
        const width = $column.outerWidth();
        const positionX = $column.offset().left - this.$.editor.offset().left - 1;
        const mouseDownX = e.pageX;
        let minWidth;

        $columnResizeLine.show().css({
            'left' : positionX,
            'width' : width
        });

        $window.on({
            'mousemove.columnResize' : ( e ) => {
                const moveX = e.pageX - mouseDownX;
                minWidth = width + moveX;
                if ( this.columnMinWidth > minWidth ) minWidth = this.columnMinWidth;
                $columnResizeLine.show().css({
                    'width' : minWidth
                });
            },
            'mouseup.columnResize' : () => {
                $window.off('mouseup.columnResize mousemove.columnResize');
                this.operationModeChange();
                $columnResizeLine.hide();
                $column.css('min-width', minWidth );
            }
        });
    });
}
/*
##################################################
    要素ホバー
##################################################
*/
itemHoverEvent() {
    this.$.menuTable.on({
        'mouseenter.onHover': ( e ) => {
            if ( this.editorMode !== 'view') $( e.currentTarget ).addClass('hover');
        },
        'mouseleave.onHover': ( e ) => {
            if ( this.editorMode !== 'view') $( e.currentTarget ).removeClass('hover');
        }
    }, '.on-hover');
}
/*
##################################################
    説明・備考欄プレースホルダー
##################################################
*/
itemNoteEvent() {
    this.$.menuTable.on({
        'focus' : function() {
            $( this ).addClass('text-in');
        },
        'blur' : function() {
            if ( $( this ).val() === '' ) {
                $( this ).removeClass('text-in');
            }
        }
    }, '.config-textarea');
}
/*
##################################################
    タイトル入力欄
##################################################
*/
itemTitleInputEvent() {
    this.$.menuTable.on({
        'input': ( e ) => {
            const $input = $( e.currentTarget );
            if ( $input.is('.menu-column-title-input') ) {
                this.titleInputChange( $input );
            } else if ( $input.is('.menu-column-title-rest-input') ) {
                this.titleInputChange( $input );
            }
        },
        'focus': function() {
            $( this ).click( function(){
                $( this ).select();
            });
        },
        'blur': function() {
            getSelection().removeAllRanges();
        },
        'mousedown': function( e ) {
            e.stopPropagation();
        }
    }, '.menu-column-title-input, .menu-column-title-rest-input');
    
        // input欄外でも選択可能にする
    this.$.menuTable.on({
        'mousedown': ( e ) => {
            if ( this.editorMode !== 'view') {
                const $input = $( e.currentTarget );
                requestAnimationFrame( () => {
                    $input.find('.menu-column-title-input, .menu-column-title-rest-input, .menu-column-repeat-number-input').focus().select();
                });
            }
        }
    }, '.menu-column-title, .menu-column-repeat-number');
}
// 入力欄幅調整
titleInputChange( $input ) {
    const inputValue = $input.val();
    $input.next().text( inputValue );
    const inputWidth = $input.next().outerWidth() + 6;
    $input.attr('value', inputValue ).css('width', inputWidth );
}
/*
##################################################
    コピー・削除
##################################################
*/
itemCopyDeleteEvent() {
    this.$.menuTable.on('click.itemCopy', '.menu-column-copy, .menu-column-delete', ( e ) => {
        const $button = $( e.currentTarget );
        const buttonType = ( $button.is('.menu-column-copy') )? 'copy': 'delete';
        const $item = $button.closest('.menu-column, .menu-column-group');
        const itemId =  $item.attr('id');
        const $previewItem = this.$.previewTable.find(`[data-id="${itemId}"]`);

        if ( buttonType === 'copy') {
            // コピー
            const $clone = $item.clone();
            const $previewClone = $previewItem.clone();

            $clone.add( $clone.find('.menu-column-group, .menu-column') ).each( ( index, element ) => {
                const $eachItem = $( element );
                const eachItemType = ( $eachItem.is('.menu-column') )? 'column': 'group';
                const id = $eachItem.attr('id');
                if ( id === undefined ) {
                    console.warn(`item delete erorr. ${id}`);
                    return
                }
                const data = this.menuMap.get( id );
                if ( data === null ) {
                    console.warn(`item copy erorr. ${id}`);
                    return
                }
                const $preview = ( $previewClone.is(`[data-id="${id}"]`) )
                    ? $previewClone
                    : $previewClone.find(`[data-id="${id}"]`);
                const copyData = fn.arrayCopy( this.menuMap.get( id ) );
                let newId;
                if ( eachItemType === 'column') {
                    // コピーしない要素は削除
                    copyData.create_column_id = undefined;
                    copyData.last_update_date_time = undefined;
                    copyData.display_order = undefined;

                    // ID
                    const columnCounter = this.columnCounter++;
                    newId = `c${this.addItemIdCheck('c', columnCounter )}`;
                    $eachItem.attr('id', newId ).empty();

                    // 画面表示設定の開閉状態を引き継ぐ
                    if ( this.displaySettingOpenIds.has( id ) ) this.displaySettingOpenIds.add( newId );
                    $preview.attr('data-id', newId ).empty();

                    // 階層
                    if ( this.floor[ data.floor ] === undefined ) this.floor[ data.floor ] = 0;
                    this.floor[ data.floor ]++;
                } else {
                    // コピーしない要素は削除
                    copyData.group_id = undefined;

                    // ID
                    const groupCounter = this.groupCounter++;
                    newId = `g${this.addItemIdCheck('g', groupCounter )}`;
                    const newIdNum = newId.slice(1);
                    // タイトルの最後に番号(n)を付与
                    let title = copyData.group_name;
                    if ( title.match(/\((\d+)\)$/) ) {
                        // (n)で終わる場合は置き換える
                        title = title.replace(/\((\d+)\)$/, `(${newIdNum})`);
                    } else {
                        title += `(${newIdNum})`;
                    }
                    copyData.group_name = title;
                    $eachItem.attr('id', newId ).find('.menu-column-group-header').empty();
                    $preview.attr('data-id', newId ).find('.previewGroupHeader .ci').empty();
                }

                // データ複製
                this.menuMap.set( newId, copyData );

                // 交差監視    
                this.itemIO.observe( $eachItem.get(0) );
                this.previewIO.observe( $preview.get(0) );
            });
            $item.after( $clone );
            $previewItem.after( $previewClone );
            $clone.find('.hover').removeClass('hover');

            // コピーした項目に合わせスクロールさせる
            const $scrollArea = this.$.menuEditWindow.children();
            const scrollElement = $scrollArea.get(0);
            const scrollAreaWidth = $scrollArea.outerWidth();
            const scrollLeft = $scrollArea.scrollLeft();
            const scrollWidth = scrollElement.scrollWidth;
            const clientWidth = scrollElement.clientWidth;
            const editorLeft = scrollElement.getBoundingClientRect().left;
            const cloneLeft = $clone.get(0).getBoundingClientRect().left + scrollLeft - editorLeft;
            const cloneWidth = $clone.outerWidth();
            const padding = 8;
            // スクロール可能か？
            if ( clientWidth < scrollWidth && scrollLeft + scrollAreaWidth < cloneLeft + cloneWidth ) {
                const left = ( cloneLeft + cloneWidth ) - scrollAreaWidth + padding;
                // this.$.menuEditWindow.children().get(0).scrollTo( left, 0 );
                this.$.menuEditWindow.children().stop(0,0).animate({'scrollLeft': left }, 200 );
            }
        } else {
            // 削除
            $item.add( $item.find('.menu-column-group, .menu-column') ).each( ( index, element ) => {
                const $eachItem = $( element );
                const eachItemType = ( $eachItem.is('.menu-column') )? 'column': 'group';
                const id = $eachItem.attr('id');
                if ( id === undefined ) {
                    console.warn(`item delete erorr. ${id}`);
                    return
                }
                const data = this.menuMap.get( id );
                if ( data === null ) {
                    console.warn(`item delete erorr. ${id}`);
                    return
                }

                // 階層情報
                if ( eachItemType === 'column') {
                    const floor = data.floor ?? null;
                    if ( floor !== null && this.floor[ floor ] !== undefined ) {
                        this.floor[ floor ]--;
                    }
                }

                // データ削除
                this.menuMap.delete( id );
                this.deleteUniqueConstraintDispData( id );
                this.displaySettingOpenIds.delete( id );
            });

            // 親グループが空になる場合
            const $parentGroup = $item.parent().closest('.menu-column-group');
            if ( $parentGroup.length && $item.siblings().length === 0 ) {
                const empty = this.getElement('columnEmptyHtml');
                $parentGroup.find('.menu-column-group-body').html( empty );
                const $previewParentGroup = $previewItem.closest('.previewGroupContainer');
                const previewEmpty = this.getElement('previewEmptyHtml');
                $previewParentGroup.find('.previewGroupBody').html( previewEmpty );
            }

            $item.remove();
            $previewItem.remove();
            this.setColumnHeaderStyle();

            // 全て空になる場合
            if ( this.$.menuTable.children().length === 0 ) {
                const empty = this.getElement('columnEmptyHtml');
                this.$.menuTable.html( empty );
                const previewEmpty = this.getElement('previewEmptyHtml');
                this.$.previewTable.html( previewEmpty );
            }
        }

        this.history.add();
        this.updateCounter();
    });
}
/*
##################################################
    入力
##################################################
*/
itemInputChangeEvent() {
    const target = '.input, .menu-column-title-rest-input, .menu-column-title-input, .menu-column-title-input, .config-checkbox';
    this.$.menuTable.on('change.itemTypeChange', target, async ( e ) => {
        const $input = $( e.currentTarget );
        let value = $input.val();
        const $item = $input.closest('.menu-column, .menu-column-group');
        const id = $item.attr('id');
        const key = $input.attr('data-key');
        const data = this.menuMap.get( id );

        // データが存在しない場合アラート
        if ( data === undefined ) {
            alert('input error.');
            return;
        }

        $input.prop('disabled', true );

        // 数値の場合はmin,maxチェック
        if ( $input.is('.config-number') ) {
            const min = $input.attr('data-min');
            const max = $input.attr('data-max');

            // 桁数が未入力の場合、最大値を入れる
            if ( $input.is('.digit-number') && value === '') {
                value = max;
            }
            if ( min !== undefined && value < Number( min ) ) value = Number( min );
            if ( max !== undefined && value > Number( max ) ) value = Number( max );
            $input.val( value );
        }

        // タイプ選択の場合はHTML変更
        if ( $input.is('.menu-column-type-select') ) {
            const configTable = $item.find('.menu-column-config-table tbody').get(0);
            this.setColumnType( configTable, id, value, data );
            // クラス名
            data.column_class = this.getColumnClassName( value );
        }

        // 値をセット
        if ( key === 'display_settings') {
            // 画面表示設定
            const settingKey = $input.attr('data-setting-key');
            const displaySettings = ( fn.typeof( data.display_settings ) === 'object')? data.display_settings: {};
            if ( $input.is('.config-color') ) {
                // 色選択
                data.display_settings = { ...displaySettings, [ settingKey ]: value };
                this.setDisplaySettingColor( $input.get(0), value );
            } else {
                // チェックボックス
                data.display_settings = { ...displaySettings, [ settingKey ]: $input.prop('checked') };
            }
        } else if ( key === 'required' || key === 'uniqued') {
            // 必須・一意
            data[ key ] = ( $input.prop('checked') )? '1': '0';
        } else if ( key === 'reference_item') {
            // プルダウン選択 参照項目
            data[ key ] = $input.text().split(',');
        } else {
            data[ key ] = String( value );
        }

        // selectの場合は名称もセット
        if ( $input.is('.config-select') ) {
            const name = $input.find('option:selected').text();
            const nameKey = $input.attr('data-nameKey');
            data[ nameKey ] = name;
        }

        // プルダウン選択が変更されたら参照項目と初期値をリセット
        if ( key === 'pulldown_selection_id') {
            const $referenceValue = $item.find('.reference-item');
            const $defaultValue = $item.find('.pulldown-default-select-body');
            try {
                $defaultValue.html(`<div class="pulldownDefaultLoading">${getMessage.FTE01131}</div>`);
                await this.itemGetPulldownSelectionDefaultValueList( value );
                $defaultValue.html( this.typePulldownDefaultValueHtml() );
            } catch ( error ) {
                $defaultValue.html(`<div class="pulldownDefaultError">${getMessage.FTE01132}</div>`);
            }
            data.reference_item = null;
            data.pulldown_selection_default_value = null;
            $defaultValue.find('.pulldown-default-select').attr('data-menuId', value );
            $referenceValue.empty();
        }

        // 一意制約(複数項目)項目名セット
        if ( key === 'item_name' || key === 'item_name_rest') {
            this.updateUniqueConstraintDispData();
        }

        // プレビュー更新
        const type = id.slice( 0, 1 );
        if ( type === 'c') {
            this.updatePreviewColumn( id );
        } else {
            this.updatePreviewGroup( id );
        }

        this.history.add();
        $input.prop('disabled', false );
    });
}
// プルダウン選択初期値読込
async itemGetPulldownSelectionDefaultValueList( id ) {
    if ( !this.pulldownSelectionDefaultValue[ id ] ) {
        const item = this.menuEditorArray.pulldown_item_list.find( i => i.link_id === id );
        if ( item ) {
            const menu = item.menu_name_rest;
            const column = item.column_name_rest;
            const restInitialUrl = `/create/define/pulldown/initial/${menu}/${column}/`;
            try {
                this.pulldownSelectionDefaultValue[ id ] = await fn.fetch( restInitialUrl );
            } catch ( error ) {
                console.error( error );
                if ( error.message ) alert( error.message );
                this.pulldownSelectionDefaultValue[ id ] = null;
                throw error;
            }
        }
    }
}
/*
##################################################
    参照項目セレクト
##################################################
*/
itemReferenceItemSelectEvent() {
    this.$.menuTable.on('click.itemReferenceItemSelect', '.reference-item-select', ( e ) => {
        this.itaModalOpen( getMessage.FTE01093, this.modalReferenceItemList, 'reference' , $( e.currentTarget ));
    });
}
/*
##################################################
    画面表示設定 開閉
##################################################
*/
itemDisplaySettingEvent() {
    this.$.menuTable.on('click.itemDisplaySetting', '.display-setting-toggle', ( e ) => {
        const $toggle = $( e.currentTarget );
        const $table = $toggle.closest('.menu-column-config-table').toggleClass('display-setting-open');
        // 開閉状態を保持（画面外に出て再描画、コピーした場合に復元するため）
        const id = $toggle.closest('.menu-column').attr('id');
        if ( id === undefined ) return;
        if ( $table.is('.display-setting-open') ) {
            this.displaySettingOpenIds.add( id );
        } else {
            this.displaySettingOpenIds.delete( id );
        }
    });

    // 色の設定を解除
    this.$.menuTable.on('click.itemDisplaySettingColorClear', '.display-setting-color-clear', ( e ) => {
        if ( this.editorMode === 'view') return;
        const $button = $( e.currentTarget );
        const input = $button.siblings('.config-color').get(0);
        const id = $button.closest('.menu-column').attr('id');
        const data = this.menuMap.get( id );
        if ( !input || data === undefined ) return;

        if ( fn.typeof( data.display_settings ) === 'object') {
            const displaySettings = { ...data.display_settings };
            delete displaySettings[ input.dataset.settingKey ];
            data.display_settings = displaySettings;
        }
        this.setDisplaySettingColor( input, null );
        this.updatePreviewColumn( id );
        this.history.add();
    });
}
// 画面表示設定：いずれかが設定済みか
hasDisplaySetting( data ) {
    const displaySettings = ( fn.typeof( data.display_settings ) === 'object')? data.display_settings: {};
    return Object.values( displaySettings ).some( value => value !== false && value !== null && value !== undefined && value !== '');
}
// 画面表示設定：色の判定（#rrggbb形式のみ有効）
isDisplaySettingColor( color ) {
    return fn.typeof( color ) === 'string' && /^#[0-9a-fA-F]{6}$/.test( color );
}
// 画面表示設定：色選択の表示を更新
setDisplaySettingColor( input, color ) {
    const wrap = input.parentElement;
    const text = wrap.querySelector('.display-setting-color-value');
    if ( this.isDisplaySettingColor( color ) ) {
        input.value = color;
        wrap.classList.remove('color-unset');
        text.textContent = color;
    } else {
        wrap.classList.add('color-unset');
        text.textContent = getMessage.FTE01170;
    }
}
// 参照項目一覧取得・選択
modalReferenceItemList( $target ) {
    const $input = $target.closest('.menu-column-config-table').find('.reference-item');
    const initItemList = ( $input.attr('data-reference-item-id') === undefined )? '': $input.attr('data-reference-item-id');
    let selectLinkId;
    const $select = $target.closest('.menu-column-config-table').find('.pulldown-select');
    if ( $select.is('.select2-hidden-accessible') ) {
        // select2適用済み
        selectLinkId = $select.find('option:selected').val();
    } else {
        selectLinkId = $select.attr('data-id');
    }

    // 決定時の処理
    const okEvent = ( newItemList ) => {
        $input.attr('data-reference-item-id', newItemList );
        //newItemListのIDから項目名に変換
        const newItemListArray = newItemList.split(',');
        const newItemNameListArray = [];
        newItemListArray.forEach(function(data){
            newItemNameListArray.push(data);
        });

        //カンマ区切りの文字列に変換に参照項目上に表示
        var newItemNameList = newItemNameListArray.join(',');
        $input.html( newItemNameList ).change();

        this.itaModalClose();
    };
    // キャンセル時の処理
    const cancelEvent = () => {
        this.itaModalClose();
    };
    // 閉じる時の処理
    const closeEvent = () => {
        this.itaModalClose();
    }

    // 選択されている「プルダウン選択」で選択可能な参照項目のみを取得する
    const item = this.menuEditorArray.pulldown_item_list.find( i => i.link_id === selectLinkId );

    // 選択可能な参照項目の一覧を取得
    if ( item ) {
        const menu = item.menu_name_rest;
        const column = item.column_name_rest;
        const printReferenceItemURL = '/create/define/reference/item/' + menu + '/' + column + '/';
        fn.fetch( printReferenceItemURL ).then( ( result ) => {
            this.setRerefenceItemSelectModalBody( result, initItemList, okEvent, cancelEvent, closeEvent );
        }).catch( ( e ) => {
            console.errpr( e );
            this.setRerefenceItemSelectModalBody( null, initItemList, okEvent, cancelEvent, closeEvent );
        });
    } else {
        this.setRerefenceItemSelectModalBody( [], initItemList, okEvent, cancelEvent, closeEvent );
    }
}
// 参照項目一覧取得・選択モーダル
setRerefenceItemSelectModalBody( itemList, initData, okCallback, cancelCallBack, closeCallBack, valueType ) {
    if ( valueType === undefined ) valueType = 'id';
    const $modalBody = $('.editor-modal-body');
    const $modalFooterMenu = $('.editor-modal-footer-menu');

    let itemSelectHTML;

    // 入力値を取得する
    const checkList = ( fn.typeof( initData ) === 'string')? initData.split(','): [''];

    if ( itemList && itemList.length !== 0 ) {
        itemSelectHTML = '<div class="modal-table-wrap">'
        + '<form id="modal-reference-item-select">'
        + '<table class="modal-table modal-select-table">'
            + '<thead>'
            + '<th class="selectTh">Select</th><th class="name">' + getMessage.FTE01146 + '</th><th class="name">' + getMessage.FTE01147 + '</th>'
            + '</thead>'
            + '<tbody>';

        itemList.forEach(itemName => {
            const itemID = itemName['reference_id'],
                //checkValue = ( valueType === 'name')? itemName: itemID,
                checkValue = itemName,
                checkedFlag = ( checkList.indexOf( checkValue['column_name_rest'] ) !== -1 )? ' checked': '',
                //value = ( valueType === 'name')? itemName: itemID;
                value = itemID;
            itemSelectHTML += '<tr>'
            + '<th><input value="' + itemName['column_name_rest'] + '" class="modal-checkbox" type="checkbox"' + checkedFlag + '></th>'
            + '<td>' + itemName['column_name'] + '</td><td>' + itemName['column_name_rest'] + '</td></tr>';
        });

        itemSelectHTML += ''
            + '</tbody>'
            + '</table>'
            + '</form>'
        + '</div>';
    } else {
        // ボタンを「閉じる」に変更
        $modalFooterMenu.children().remove();
        $modalFooterMenu.append('<li class="editor-modal-footer-menu-item"><button class="editor-modal-footer-menu-button negative" data-button-type="close">' + getMessage.FTE01050 + '</li>');

        // 表示メッセージ
        const noDataMessage = ( itemList && itemList.length === 0 )? getMessage.FTE01152: getMessage.FTE01139;
        itemSelectHTML = '<p class="modal-one-message">' + noDataMessage + '</p>';
    }
    $modalBody.html( itemSelectHTML );

    // 行で選択
    $modalBody.find('.modal-select-table').on('click', 'tr', function(){
        const $tr = $( this );
        const checked = $tr.find('.modal-checkbox').prop('checked');
        if ( checked ) {
            $tr.find('.modal-checkbox').prop('checked', false );
        } else {
            $tr.find('.modal-checkbox').prop('checked', true );
        }
    });

    // 決定・取り消しボタン
    const $modalButton = $('.editor-modal-footer-menu-button');
    $modalButton.prop('disabled', false ).on('click', function() {
        const $button = $( this );
        const btnType = $button.attr('data-button-type');
        switch( btnType ) {
        case 'ok':
            // 選択しているチェックボックスを取得
            let checkboxArray = new Array;
            $modalBody.find('.modal-checkbox:checked').each( function(){
                checkboxArray.push( $( this ).val() );
            });
            const newItemList = checkboxArray.join(',');
            okCallback( newItemList, itemList );
            break;
        case 'cancel':
            cancelCallBack();
            break;
        case 'close':
            closeCallBack();
            break;
        }
    });
}
/*
##################################################
    選択欄select2適用
##################################################
*/
itemSetSelect2Event() {
    this.$.menuTable.on('click.itemSetSelect2', '.select-dummy', async ( e ) => {
        const $dummy = $( e.currentTarget );
        if ( $dummy.is('.disabled-select') ) return;

        const $select = $dummy.next('.config-select');
        const key = $select.attr('data-key');
        const selectedId = $dummy.attr('data-id');

        let select2List = [];
        if ( key === 'parameter_sheet_reference_id') {
            // パラメータシート参照
            const list = this.menuEditorArray.parameter_sheet_reference_list ?? [];
            select2List = this.convertSelect2List( list, 'column_definition_id', 'select_full_name', selectedId );
        } else if ( key === 'pulldown_selection_id') {
            // プルダウン選択
            const list = this.menuEditorArray.pulldown_item_list ?? [];
            select2List = this.convertSelect2List( list, 'link_id', 'link_pulldown', selectedId );
        } else if ( key === 'pulldown_selection_default_value') {
            // プルダウン選択初期値
            const menuId = $select.attr('data-menuId');
            const list = this.pulldownSelectionDefaultValue[ menuId ] ?? [];
            select2List = this.convertPulldownDefaultSelect2List( list, selectedId );
        }
        await this.setSelect2( $select, select2List );

        $dummy.remove();
    });

    // select2が開いているときはスクロールさせない
    this.$.menuTable.on({
        'select2:opening': function(){
            $( this ).closest('.editor-block-inner').on('wheel.select2Scroll', function( e ){
                e.preventDefault();
            });

            // 開いたselect2コンテナに対してもスクロール禁止
            // :openingのタイミングだと対象が存在しないのでタイミングをずらす
            requestAnimationFrame( () => {
                const select2Container = document.querySelector('body > .select2-container');
                // 検索枠
                const search = select2Container.querySelector('.select2-search');
                search.addEventListener('wheel', ( e ) => {
                    e.preventDefault();
                }, { passive: false });
                // オプションリストはスクロールバーが出てない場合のみホイールを禁止する
                const options = select2Container.querySelector('.select2-results__options');
                if ( options.offsetWidth - options.clientWidth === 0 ) {
                    options.addEventListener('wheel', ( e ) => {
                        e.preventDefault();
                    }, { passive: false });
                }
            });
        },
        'select2:closing': function(){
            $( this ).closest('.editor-block-inner').off('wheel.select2Scroll');
        }
    });

}
// ITAリストからselect2リストに変換
convertSelect2List( list, idKey, nameKey, selectedId ) {
    const selectedList = [];
    const optionList = list.map( ( item ) => {
        const id = item[ idKey ] ?? '';
        const text = item[ nameKey ] ?? '';
        const data = {
            id: id,
            text: text
        };
        if ( id === selectedId ) {
            data.selected = true;
            selectedList.push( data );
        }
        return data;
    });
    return {
        optionList: optionList,
        selectedList: selectedList
    };
}
// プルダウン選択初期値select2用リスト変換
convertPulldownDefaultSelect2List( list, selectedId ) {
    const optionList = [{id: '', text: ''}];
    const selectedList = [];
    for ( const id in list ) {
        const text = list[ id ];
        const data = {
            id: id,
            text: text
        };
        if ( id === selectedId ) {
            data.selected = true;
            selectedList.push( data );
        }
        optionList.push( data );
    }
    // デフォルト値を持っているが一致するレコードが無い場合、ID変換失敗(ID)の選択肢を追加
    if ( selectedId && selectedList.length === 0 ) {
        const data = {
            id: selectedId,
            text: `${getMessage.FTE01133}{0:${selectedId}}`,
            selected: true
        };
        selectedList.push( data );
        optionList.push( data );
    }
    return {
        optionList: optionList,
        selectedList: selectedList
    };
}
/*
##################################################
    項目（カラム・グループ）移動
##################################################
*/
itemMoveEvent() {
    this.$.editor.on('mousedown.itemMoveMouseDown', '.menu-column-move', ( e ) => {
        // 左クリックチェック
        if ( e.button !== 0 ) return false;
    
        // 選択を解除
        getSelection().removeAllRanges();
    
        // エディターモード変更
        this.operationModeChange('columnMove');
    
        const $window = $( window );
        const $knob = $( e.currentTarget );
        const $column = $knob.closest('.menu-column, .menu-column-group, .menu-column-repeat');
        const $columnClone = $column.clone( false );
        const $targetArea = $('.menu-column, .menu-column-group-header, .menu-column-repeat-header, .menu-column-repeat-footer, .column-empty');
        const scrollTop = $window.scrollTop();
        const scrollLeft = $window.scrollLeft();
        const knobWidth = $knob.outerWidth();
        const knobHeight = $knob.outerHeight();
        const mousedownPositionX = e.pageX;
        const mousedownPositionY = e.pageY;
    
        // 何を移動するか
        const moveColumnType = $column.attr('class');
        this.$.menuTable.attr('data-move-type', moveColumnType );
    
        let $hoverTarget = null;
        let hoverTargetWidth, hoverTargetLeft;
        let moveX, moveY;
        let isDragging = true;
    
        $column.addClass('move-wait');

        // 自動スクール
        const scrollEdge = 40; // 端から 40px 以内でスクロール開始
        const scrollMaxSpeed = 60; // 最大スクロール速度(px/frame)
        const scrollContainer = document.querySelector('.menu-editor-block-inner');
        let pointerX = mousedownPositionX;
        const autoScroll = () => {
            if ( !isDragging ) return;
            const rect = scrollContainer.getBoundingClientRect();
            
            let dx = 0;
            if ( pointerX < rect.left + scrollEdge ) {
                dx = -(( rect.left + scrollEdge - pointerX ) / scrollEdge ) * scrollMaxSpeed;
            } else if ( pointerX > rect.right - scrollEdge ) {
                dx = (( pointerX - (rect.right - scrollEdge )) / scrollEdge ) * scrollMaxSpeed;
            }

            if ( dx !== 0 ) {
                scrollContainer.scrollBy( dx, 0 );
            }

            requestAnimationFrame( autoScroll );
        };
        autoScroll();
    
        // 移動用ダミーオブジェ追加
        this.$.editor.append( $columnClone );
        $columnClone.addClass('move').css({
            'left' : ( mousedownPositionX - scrollLeft - knobWidth / 2 ) + 'px',
            'top' : ( mousedownPositionY - scrollTop - knobHeight / 2 ) + 'px'
        });
    
        // ターゲットの左か右かチェックする
        const leftRightCheck = ( mouseX ) => {
            if ( $hoverTarget !== null ) {
                if ( !$hoverTarget.is('.column-empty') ) {
                    const mousePositionX = mouseX - hoverTargetLeft;
                    if ( hoverTargetWidth / 2 > mousePositionX ) {
                        $hoverTarget.removeClass('right');
                        if ( !$hoverTarget.prev().is( $column ) ) {
                        $hoverTarget.addClass('left');
                        }
                    } else {
                        $hoverTarget.removeClass('left');
                        if ( !$hoverTarget.next().is( $column ) ) {
                        $hoverTarget.addClass('right');
                        }
                    }
                }
            }
        }
    
        // どこの上にいるか
        $targetArea.on({
            'mouseenter.columnMove' : ( mee ) => {
                mee.stopPropagation();
                // 対象情報
                $hoverTarget = $( mee.currentTarget );
                hoverTargetWidth = $hoverTarget.outerWidth();
                hoverTargetLeft = scrollLeft + $hoverTarget.offset().left;
                // 対象が自分以外かどうか
                if ( !$hoverTarget.is( $column ) ) {
                    if ( $hoverTarget.is('.menu-column-group-header') ) {
                        $hoverTarget = $hoverTarget.closest('.menu-column-group');
                    }
                    $hoverTarget.addClass('hover');
                    $hoverTarget.parents('.menu-column-group, .menu-column-repeat-body').eq(0).addClass('hover-parent');
                } else {
                    $hoverTarget = null;
                }
        
                leftRightCheck( mee.pageX );
            },
            'mouseleave.columnMove' : () => {
                $hoverTarget = null;
                this.$.menuTable.find('.hover, .hover-parent, .left, .right').removeClass('hover hover-parent left right');
            }
        });

        $window.on({
            'mousemove.columnMove' : ( mme ) => {
                pointerX = mme.pageX;
                // 仮移動
                moveX = mme.pageX - mousedownPositionX;
                moveY = mme.pageY - mousedownPositionY;
                $columnClone.css('transform', 'translate(' + moveX + 'px,' + moveY + 'px)');
                leftRightCheck( mme.pageX );
            },
            'mouseup.columnMove' : () => {
                isDragging = false;
                // 対象があれば移動する
                if ( $hoverTarget !== null ) {
                    // プレビュー用
                    const previewId = $column.attr('id');
                    const $previewColumn = this.$.previewTable.find(`[data-id="${previewId}"]`);
                    const targetPreviewId = ( $hoverTarget.is('.column-empty') )
                        ? $hoverTarget.closest('.menu-column-group').attr('id')
                        : $hoverTarget.attr('id');
                    const $targetPreviewItem = this.$.previewTable.find(`[data-id="${targetPreviewId}"]`);

                    // 移動した際にグループの中身が空になるか判定
                    const $parentGroup = $column.parent().closest('.menu-column-group');
                    const $previewParentGroup = $previewColumn.parent().closest('.previewGroup');
                    let emptyFlag = false;
                    if ( $parentGroup.length && $column.siblings().length === 0 ) {
                        emptyFlag = true;
                    }
                    // 移動する or 空のグループに追加
                    if ( $hoverTarget.is('.column-empty') ) {
                        $hoverTarget.closest('.menu-column-group-body').empty().append( $column );
                        $targetPreviewItem.find('.previewGroupBody').empty().append( $previewColumn );
                    } else {
                        // 右か左か
                        if ( $hoverTarget.is('.left') ) {
                            $column.insertBefore( $hoverTarget );
                            $previewColumn.insertBefore( $targetPreviewItem );
                        } else if ( $hoverTarget.is('.right') ) {
                            $column.insertAfter( $hoverTarget );
                            $previewColumn.insertAfter( $targetPreviewItem );
                        }
                    }
                    // グループが空ならEmpty追加
                    if ( emptyFlag === true ) {
                        const empty = this.getElement('columnEmptyHtml');
                        $parentGroup.find('.menu-column-group-body').html( empty );
                        const previewEmpty = this.getElement('previewEmptyHtml');
                        $previewParentGroup.find('.previewGroupBody').html( previewEmpty );
                    }

                    // 移動後に親グループの数を調べる
                    if ( moveColumnType === 'menu-column') {
                        this.moveCheckFloor( $column );
                    } else {
                        // グループ内のカラムをチェックする
                        $column.find('.menu-column').each( ( index, element ) => {
                            this.moveCheckFloor( $( element ) );
                        });
                    }
                    this.setColumnHeaderStyle();
                }
                $column.removeClass('move-wait');
                $columnClone.remove();
                this.$.menuTable.find('.hover, .hover-parent, .left, .right').removeClass('hover hover-parent left right');
                this.$.menuTable.removeAttr('data-move-type', moveColumnType );
                $window.off('mousemove.columnMove mouseup.columnMove');
                $targetArea.off('mouseenter.columnMove mouseleave.columnMove');
                this.operationModeChange();
                // 移動した場合のみ履歴追加
                if ( $hoverTarget !== null ) {
                    this.history.add();
                }
            }
        });    
    });
}
/*
##################################################
    移動時に階層をチェックする
##################################################
*/
moveCheckFloor( $item ) {
    const floor = $item.parents('.menu-column-group').length;
    const id = $item.attr('id');
    const data = this.menuMap.get(id) ?? {};

    // 同じ階層なら何もしない
    if ( data.floor === floor ) return;

    // 階層が変わったらセットしなおす
    if ( this.floor[ floor ] === undefined ) this.floor[ floor ] = 0;
    this.floor[ floor ]++;
    this.floor[ data.floor ]--;
    data.floor = floor;
    $item.find('.menu-column-header').attr('data-floor', floor );
    // プレビューの階層も変更する
    this.$.previewTable.find(`[data-id="${id}"] .previewColumnHeader`).attr('data-floor', floor + 1 );
}
/*
##################################################
    カラムヘッダー高さ設定
##################################################
*/
setColumnHeaderStyle() {
    if ( !this.floor.some( v => v !== 0 )) {
        // 0のみの場合は配列をクリア
        this.floor.length = 0;
    } else {
        // 階層配列の長さを調整（後ろから続く1以上になる前の0を削除）
        const length = this.floor.length;
        for ( let i = length - 1; i >= 0; i-- ) {
            if ( this.floor[i] >= 1 ) {
                this.floor.length = i + 1;
                break;
            }
        }
    }    
    
    const newLength = this.floor.length;
    const style = [];
    const value = 64;
    const floorValue = 32;
    for ( let i = 0; i < newLength; i++ ) {
        const height = value + ( newLength - i - 1 ) * floorValue;
        style.push(`.menu-column-header[data-floor="${i}"]{height:${height}px !important;}`);
    }

    const previewFloorValue = 30;
    const previewFloorType = ( this.$.menuType.val() !== '2')? 0: 1;
    const previewFloorLength =
        ( previewFloorType === 1 && newLength < 1 )
        ? 1
        : ( previewFloorType === 0 && newLength < 2 )
            ? 2
            : ( previewFloorType === 1 )
                ? newLength
                : newLength + 1;
    const previewStart = ( previewFloorType === 0 )? 0: 1;
    for ( let i = previewStart; i < previewFloorLength; i++ ) {
        const previewHeight = previewFloorValue * ( previewFloorLength - i + previewStart );
        style.push(`.previewColumnHeader[data-floor="${i}"]{height:${previewHeight}px !important;}`);
    }
    this.$.style.html( style.join('') );
}
/*
##################################################
    カレンダーイベント
##################################################
*/
itemCalendarEvent() {
    this.$.menuTable.on('click', '.inputDateCalendarButton', function(){
        const $button = $( this );
        const $input = $button.closest('.inputDateContainer').find('.callDateTimePicker'); // 対象のinput textを指定する
        const value = $input.val();
        const flagText = $input.attr('data-timeflag') ?? 'false';
        const flag = flagText === 'true';
        const name = ( flag === true )? getMessage.FTE01134: getMessage.FTE01135;
    
        fn.datePickerDialog('date', flag, name, value ).then(function( result ){
            if ( result !== 'cancel') {
                $input.val( result.date ).change().focus().trigger('input');
            }
        });
    });
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   パネルイベント
//
////////////////////////////////////////////////////////////////////////////////////////////////////
setPanelEvents() {
    this.panelTargetMenuGroupChangeEvent();
    this.panelOpenTargetMenuGroupModalEvent();
    this.panelRoleSelectEvent();
    this.panelUniqueConstraintEvent();
}
/*
##################################################
    対象メニューグループ変更
##################################################
*/
panelTargetMenuGroupChangeEvent() {
    $('#create-menu-type').on('change', ( e ) => {
        const $select = $( e.currentTarget );
        const menuType = $select.val();
        this.$.property.attr('data-menu-type', menuType );

        this.updatePreviewType();
        this.setColumnHeaderStyle();
    });
}
// 対象メニューグループ モーダルを開く
panelOpenTargetMenuGroupModalEvent() {
    const $menuGroupSlectButton = $('#create-menu-group-select');
    $menuGroupSlectButton.on('click', () => {
        let type;
        // パラメータシートorデータシート
        if ( $('#create-menu-type').val() === '1' || $('#create-menu-type').val() === '3' ) {
            type = 'parameter-sheet';
        } else {
            type = 'data-sheet';
        }
        this.itaModalOpen( getMessage.FTE01077, this.panelOpenTargetMenuGroupModal, type );
    });
}
// 対象メニューグループ モーダル
panelOpenTargetMenuGroupModal() {
    const menuGroupData = this.menuEditorArray.target_menu_group_list,
            menuListRowLength = menuGroupData.length,
            menuGroupType = ['for-input','for-substitution','for-reference'],
            menuGroupAbbreviation = [getMessage.FTE01080,getMessage.FTE01081,getMessage.FTE01082],
            menuGroupTypeLength = menuGroupType.length;

    let html = ''
    + '<div id="menu-group-list" class="modal-table-wrap">'
        + '<table class="modal-table">'
        + '<thead>'
            + '<tr>';

    // header Radio
    for ( let i = 0; i < menuGroupTypeLength; i++ ) {
        html += '<th class="th-radio ' + menuGroupType[i] + '" checked>' + menuGroupAbbreviation[i] + '</th>'
    }
    // header Title
    html += '<th class="id">ID</th>'
            + '<th class="name">' + getMessage.FTE01083 + '</th>';

    html += '</tr></thead><tbody><tr>';

    // Unselected Radio
    for ( let i = 0; i < menuGroupTypeLength; i++ ) {
        const radioID = 'radio-' + menuGroupType[i] + '-0';
        html += ''
        + '<th class="th-radio ' + menuGroupType[i] + '">'
        + '<span class="menu-group-radio">'
            + '<input type="radio" class="select-menu radio-number-0" id="' + radioID + '" name="' + menuGroupType[i] + '" value="unselected" data-name="unselected" checked>'
            + '<label class="select-menu-label" for="' + radioID + '"></label>'
        + '</span>'
        + '</th>'
    }

    html += '<td class="unselected" >-</td>'
            + '<td class="unselected" >Unselected</td></tr>';

    // body List
    for ( let i = 0; i < menuListRowLength; i++ ) {
        html += '<tr>';
        // body Radio
        for ( let j = 0; j < menuGroupTypeLength; j++ ) {
        const radioClass = 'select-menu radio-number-' + menuGroupData[i]['menu_group_id'],
                radioID = 'radio-' + menuGroupType[j] + '-' + menuGroupData[i]['menu_group_id'];
        html += ''
        + '<th class="th-radio ' + menuGroupType[j] + '">'
            + '<span class="menu-group-radio">'
            + '<input type="radio" class="' + radioClass +'" id="' + radioID + '" name="' + menuGroupType[j] + '" value="' + menuGroupData[i]['menu_group_id'] + '" data-name="' + menuGroupData[i]['full_menu_group_name'] + '">'
            + '<label class="select-menu-label" for="' + radioID + '"></label>'
            + '</span>'
        + '</th>'
        }
        // Menu group Data
        html += '<td class="id">' + menuGroupData[i]['menu_group_id'] + '</td>'
            + '<td class="name">' + fn.escape( menuGroupData[i]['full_menu_group_name'] ) + '</td>';

        html += '</tr>';
    }

    html += '</tbody></table></div>'

    // モーダルにBodyをセット
    const $modalBody = $('.editor-modal-body');
    $modalBody.html( html ).on('change', '.select-menu', function(){
        const $input = $( this ),
            menuID = $input.attr('value'),
            neme = $input.attr('name'),
            checkClass = 'checked-row checked-' + neme;
        $('.checked-' + neme ).removeClass( checkClass )
        .find('.select-menu').prop('disabled', false );

        if ( menuID !== 'unselected' ) {
        $('.radio-number-' + menuID ).closest('tr').addClass( checkClass )
            .find('.select-menu').not(':checked').prop('disabled', true );
        }
    });

    // 選択状態をRadioボタンに反映する
    $('#menu-group').find('.panel-span:visible').each( function(){
        const $item = $( this ),
            type = $item.attr('id').replace('create-menu-',''),
            id = $item.attr('data-id');
        if ( id !== '' ) {
        $modalBody.find('input[name="' + type + '"]').filter('[value="' + id + '"]').prop('checked', true).change();
        }
    });

    // 決定・取り消しボタン
    const $modalButton = $('.editor-modal-footer-menu-button');
    $modalButton.on('click', ( e ) => {
        const $button = $( e.currentTarget ),
            type = $button.attr('data-button-type');
        switch( type ) {
        case 'ok':
            // チェック状態を対象メニューグループ選択に反映する
            $('.select-menu:checked').each( function() {
            const $checked = $( this ),
                    checkedType = $checked.attr('name');
            let checkedID = $checked.val(),
                checkedName = $checked.attr('data-name');
            if ( checkedID === 'unselected'){
                checkedID = checkedName = '';
            }
            $('#create-menu-' + $checked.attr('name') ).text( checkedName ).attr({
                'data-id' :  checkedID,
                'data-value' : checkedName
            });
            // 縦メニュー値があるか確認
            if ( checkedType === 'vertical' ) {
                if ( checkedID !== '') {
                $property.attr('data-vertical-menu', true );
                } else {
                $property.attr('data-vertical-menu', false );
                }
            }
            });
            this.itaModalClose();
            break;
        case 'cancel':
            this.itaModalClose();
            break;
        }
    });
}
/*
##################################################
    ロール一覧取得・選択
##################################################
*/
panelRoleSelectEvent() {
    $('#permission-role-select').on('click', ( e ) => {
        this.itaModalOpen( getMessage.FTE01092, this.panelRoleListModalOpen, 'role');
    });
}
// ロール一覧
panelRoleListModalOpen() {
    const $input = $('#permission-role-name-list');
    const initRoleList = ( $input.attr('data-role-id') === undefined )? '': $input.attr('data-role-id');
    // 決定時の処理
    const okEvent = ( newRoleList ) => {
        $input.text( newRoleList ).attr('data-role-id', newRoleList );
        this.itaModalClose();
    };
    // キャンセル時の処理
    const cancelEvent = () => {
        this.itaModalClose();
    };

    this.panelSetRoleSelectModalBody( this.menuEditorArray.role_list, initRoleList, okEvent, cancelEvent );
}
// ロール一覧モーダルボディ
panelSetRoleSelectModalBody( roleList, initData, okCallback, cancelCallBack, valueType ) {
    if ( valueType === undefined ) valueType = 'id';
    const $modalBody = $('.editor-modal-body');
    
    let roleSelectHTML = ''
    + '<div class="modal-table-wrap">'
        + '<form id="modal-role-select">'
        + '<table class="modal-table modal-select-table">'
        + '<thead>'
            + '<th class="selectTh">Select</th><th class="name">Name</th>'
        + '</thead>'
        + '<tbody>';
    
    // 入力値を取得する
    const checkList = ( initData !== null || initData !== undefined )? initData.split(','): [''];
    
    const roleLength = roleList.length;
    for ( let i = 0; i < roleLength; i++ ) {
        const roleName = roleList[i],
            hideRoleName = "********";
        // ********は表示しない
        if ( roleName !== hideRoleName ) {
        //const roleID = String(i),
                //checkValue = ( valueType === 'name')? roleName: roleID,
        const checkValue = roleName,
                checkedFlag = ( checkList.indexOf( checkValue ) !== -1 )? ' checked': '',
                //value = ( valueType === 'name')? roleName: roleID;
                value = roleName;
        roleSelectHTML += '<tr>'
        + '<th><input value="' + value + '" class="modal-checkbox" type="checkbox"' + checkedFlag + '></th>'
        + '<td>' + roleName + '</td></tr>';
        }
    }
    
    roleSelectHTML += ''
        + '</tbody>'
        + '</table>'
        + '</form>'
    + '</div>';
    
    $modalBody.html( roleSelectHTML );
    
    // 行で選択
    $modalBody.find('.modal-select-table').on('click', 'tr', function(){
        const $tr = $( this ),
            checked = $tr.find('.modal-checkbox').prop('checked');
        if ( checked ) {
        $tr.find('.modal-checkbox').prop('checked', false );
        } else {
        $tr.find('.modal-checkbox').prop('checked', true );
        }
    });
    
    // 決定・取り消しボタン
    const $modalButton = $('.editor-modal-footer-menu-button');
    $modalButton.prop('disabled', false ).on('click', function() {
        const $button = $( this ),
            btnType = $button.attr('data-button-type');
        switch( btnType ) {
        case 'ok':
            // 選択しているチェックボックスを取得
            let checkboxArray = new Array;
            $modalBody.find('.modal-checkbox:checked').each( function(){
            checkboxArray.push( $( this ).val() );
            });
            const newRoleList = checkboxArray.join(',');
            okCallback( newRoleList );
            break;
        case 'cancel':
            cancelCallBack();
            break;
        }
    });
}
/*
##################################################
    一意制約(複数項目)
##################################################
*/
panelUniqueConstraintEvent() {
    $('#unique-constraint-select').on('click', ( e ) => {
        this.itaModalOpen( getMessage.FTE01091, this.panelUniqueConstraintModalOpen, 'unique');
    });
}
// 一意制約モーダルを開く
panelUniqueConstraintModalOpen() {
    //現在の設定値
    const $input = $('#unique-constraint-list');
    const initmodalUniqueConstraintList = $input.attr('data-unique-list') ?? '';

    // 決定時の処理
    const okEvent = ( currentUniqueConstraintArray ) => {
        this.panelSetUniqueConstraint( currentUniqueConstraintArray );
        this.itaModalClose();
    };
    // キャンセル時の処理
    const cancelEvent = () => {
        this.itaModalClose();
    };
    // 閉じる時の処理
    const closeEvent = () => {
        this.itaModalClose();
    }

    this.panelSetUniqueConstraintModalBody( initmodalUniqueConstraintList, okEvent, cancelEvent, closeEvent);
}
// 一意制約(複数項目)の値をセット
panelSetUniqueConstraint( currentUniqueConstraintArray ) {
    // 空の配列を削除
    const newList = currentUniqueConstraintArray.filter( i => i.length > 0 );

    const uniqueConstraintData = this.panelGetUniqueConstraintDispData( newList );
    const uniqueConstraintConv = uniqueConstraintData.conv;
    const uniqueConstraintName = uniqueConstraintData.name;
    $('#unique-constraint-list')
        .attr('data-unique-list', uniqueConstraintConv) // 一意制約のIDの組み合わせをセット
        .text(uniqueConstraintName); // 一意制約の項目名の組み合わせをセット

    // 現在の設定値を更新
    this.menuEditorArray['unique-constraints-current'] = ( newList.length )? newList: null;
}
//一意制約の登録用のcolumnID連結文字列と、表示用の項目名を作成する
panelGetUniqueConstraintDispData( uniqueConstraintArrayData ) {
    const uniqueConstraintDispData = {
        conv: '',
        name: ''
    };
    if ( uniqueConstraintArrayData.length === 0 ) return uniqueConstraintDispData;

    const uniqueConstraintConv = [];
    const uniqueConstraintName = [];
    for ( const data of uniqueConstraintArrayData ) {
        const keyList = [];
        const idList = [];
        for ( const unique of data ) {
            for ( const key in unique ) {
                // Column key確認
                if ( !this.menuMap.has( key ) ) continue;
                const id = unique[ key ];
                keyList.push( key );
                idList.push( id );
            }
        }
        uniqueConstraintConv.push( keyList.join('-') );
        uniqueConstraintName.push(`[${idList.join(',')}]`);
    }

    uniqueConstraintDispData.conv = ( uniqueConstraintConv.length )? uniqueConstraintConv.join(','): '';
    uniqueConstraintDispData.name = ( uniqueConstraintName.length )? uniqueConstraintName.join(','): '';
    return uniqueConstraintDispData;
}
// 一意制約モーダル Body HTML
panelSetUniqueConstraintModalBody( initmodalUniqueConstraintList, okCallback, cancelCallBack, closeCallBack ) {
    const $modalBody = $('.editor-modal-body');
    const $modalFooterMenu = $('.editor-modal-footer-menu');
    const initUniqueConstraintArray = ( initmodalUniqueConstraintList === '') ? [] : initmodalUniqueConstraintList.split(',');
    const initUniqueConstraintLength = initUniqueConstraintArray.length;

    if ( this.menuMap.size === 0 ) {
        // 項目が0個の場合、メッセージを表示
        const noColumnHTML = '<div class="column-none-message">' + getMessage.FTE01142 + '</div>';
        $modalBody.html( noColumnHTML );

        //ボタンを「閉じる」に変更
        $modalFooterMenu.children().remove();
        $modalFooterMenu.append('<li class="editor-modal-footer-menu-item"><button class="editor-modal-footer-menu-button negative" data-button-type="close">' + getMessage.FTE01050 + '</li>');
    } else {
        //項目の数だけチェックボックスを作成する「パターン」のテンプレート        
        const itemCheckboxHtml = [];
        for ( const [ key, value ] of this.menuMap.entries() ) {
            const type = key.slice( 0, 1 );
            if ( type === 'g') continue;
            const columnID = key;
            const itemName = value.item_name_rest ?? '';
            const itemID = value.create_column_id ?? '';
            itemCheckboxHtml.push('<div class="unique-edit-check-wrap">'
                + '<input type="checkbox" id="" class="unique-constraint-checkbox unique-edit-check" data-item-id="'+ itemID +'" data-column-id="'+ columnID +'">'
                + '<label class="unique-constraint-label unique-edit-label" for="">' + itemName + '</label>'
            + '</div>');
        }
        const uniqueConstraintLineTemplate = ''
        +'<div id="modal-unique-constraint-area" class="">'
            + '<div class="unique-constraint-pattern-tmp unique-constraint-box" data-unique-ptn="">'
                +'<span>'
                    + itemCheckboxHtml.join('')
                + '</span>'
                +'<div class="line-delete-button-wrap"><button type="button" class="line-delete-button">' + getMessage.FTE01143 + '</button></div>'
            + '</div>'
            + '<ul class="add-unique-pattern">'
                + '<li class=""><button class="add-unique-pattern-button positive" data-button-type="add">' + getMessage.FTE01144 + '</li>'
            + '</ul>'
            + '<form id="modal-unique-constraint-select">'
                + '<div class="unique-none-message" hidden>' + getMessage.FTE01145 + '</div><br>'
            + '</form>'
        + '</div>';
        $modalBody.html( uniqueConstraintLineTemplate );

        //初期表示およびパターン追加処理
        const $uniqueConstraintArea = $('#modal-unique-constraint-area');
        const $addPatternButton = $uniqueConstraintArea.find('.add-unique-pattern-button');
        const $patternTemplate = $uniqueConstraintArea.find('.unique-constraint-pattern-tmp');
        const $addArea = $('#modal-unique-constraint-select');
        const $noneMsg = $uniqueConstraintArea.find('.unique-none-message');
        let patternCount = 0;

        //パターン追加関数
        function addPattern($newPattern){
            $newPattern.show(); //非表示を解除
            $newPattern.removeClass('unique-constraint-pattern-tmp').addClass('unique-constraint-pattern'); //Class入れ替え
            patternCount++;
            $newPattern.attr('data-unique-ptn', 'p'+patternCount); //連番を設定
            $newPattern.find('.unique-constraint-checkbox').each(function(){
                let itemId = $(this).attr('data-column-id');
                $(this).attr('id', 'p'+patternCount+itemId); //idを設定
                $(this).next('label').attr('for', 'p'+patternCount+itemId); //forを設定
            });
            $addArea.append($newPattern);

            //「削除」ボタンにイベント追加
            $newPattern.find('.line-delete-button').on('click', function(){
                //対象のパターンを削除
                $(this).parents('.unique-constraint-box').remove();

                //パターンが0の場合はメッセージを表示
                const $pattern = $addArea.find('.unique-constraint-box');
                if($pattern.length == 0){
                    $noneMsg.show();
                }
            });
        }

        if(initUniqueConstraintLength == 0){
            //一意制約の設定値がない場合、メッセージを表示
            $noneMsg.show();
        }else{
            ///一意制約の設定値がある場合、パターンの数だけループ処理
            for (let i = 0; i < initUniqueConstraintLength; i++){
                //パターンを生成
                let $newPattern = $patternTemplate.clone(true);
                addPattern($newPattern);

                //初期チェック状態を設定
                const patternStr = initUniqueConstraintArray[i];
                const patternArray = patternStr.split('-'); //「-」で連結したIDを配列化
                const patternLength = patternArray.length;
                for(let j = 0; j < patternLength; j++){
                    //入力済みの設定値を反映
                    const patternId = patternArray[j];
                    const $target = $newPattern.find('[data-column-id="'+patternId+'"]'); //対象をdata-column-idで検索
                    if($target.length != 0){
                        $target.prop('checked', true);
                    }
                }
            }
        }

        //「パターンを追加」ボタン
        $addPatternButton.on('click', function(){
            //パターンが無い場合のメッセージを非表示
            if(!$noneMsg.is('hidden')){
                $noneMsg.hide();
            }

            //新しいパターンを生成
            let $newPattern = $patternTemplate.clone(true);
            addPattern($newPattern);
        });
    }

    // 決定・取り消しボタン
    const $modalButton = $('.editor-modal-footer-menu-button');
    $modalButton.prop('disabled', false ).on('click', function() {
        const $button = $( this ),
                btnType = $button.attr('data-button-type');
        switch( btnType ) {
                case 'ok':
                //設定値を格納する配列を定義
                let currentUniqueConstraintArray = new Array;
                // 選択しているチェックボックスを取得
                $modalBody.find('.unique-constraint-box').each(function(){
                    const $targetPattern = $(this);
                    if($targetPattern.hasClass('unique-constraint-pattern-tmp') == true){
                        return true;
                    }
                    let currentPatternArray = new Array;
                    $targetPattern.find('.unique-constraint-checkbox:checked').each(function(){
                        let columnId = $(this).attr('data-column-id');
                        let itemName = $(this).next('label').html();
                        let idName = {[columnId] : itemName};
                        currentPatternArray.push(idName);
                    });

                    currentUniqueConstraintArray.push(currentPatternArray);
                });

                okCallback( currentUniqueConstraintArray );
                break;
            case 'cancel':
                cancelCallBack();
                break;
            case 'close':
                closeCallBack();
                break;
        }
    });
}
// 項目を削除したとき、一意制約(複数項目)にその項目が含まれていた場合削除する。
deleteUniqueConstraintDispData( deleteColumnKey ) {
    const tmpList = this.menuEditorArray['unique-constraints-current'];
    if ( tmpList === null ) return;

    const currentUniqueConstraintData = [];
    for ( const data of tmpList ) {
        const uniqueList = [];
        for ( const unique of data ) {
            for ( const key in unique ) {
                if ( key === deleteColumnKey ) continue;
                uniqueList.push({
                    [ key ]: unique[ key ]
                });
            }
        }
        currentUniqueConstraintData.push( uniqueList );
    }

    // 更新後の値をページに反映
    this.panelSetUniqueConstraint( currentUniqueConstraintData );
}
// 項目名が変更されるアクションがあったとき、一意制約(複数項目)で表示している項目名をセットしなおす。
updateUniqueConstraintDispData() {
    const tmpList = this.menuEditorArray['unique-constraints-current'];
    if ( tmpList === null ) return;

    const currentUniqueConstraintData = [];
    for ( const data of tmpList ) {
        const uniqueList = [];
        for ( const unique of data ) {
            for ( const key in unique ) {
                const itemData = this.menuMap.get( key );
                if ( itemData ) {
                    const itemName = itemData.item_name_rest ?? '';
                    uniqueList.push({
                        [ key ]: itemName
                    });
                } else {
                    console.warn(`unique constraints change error. key:${key}`);
                }
            }
        }
        currentUniqueConstraintData.push( uniqueList );
    }

    // 更新後の値をページに反映
    this.panelSetUniqueConstraint( currentUniqueConstraintData );
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   モーダル
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    モーダルを開く
##################################################
*/
itaModalOpen( headerTitle, bodyFunc, modalType, target ) {
    if ( typeof bodyFunc !== 'function' ) return false;

    // 初期値
    if ( headerTitle === undefined ) headerTitle = 'Undefined title';
    if ( modalType === undefined ) modalType = 'default';

    const $window = $( window ),
            $body = $('body');

    let footerHTML;

    if ( modalType === 'help' ) {
        footerHTML = ''
        + '<div class="editor-modal-footer">'
        + '<ul class="editor-modal-footer-menu">'
            + '<li class="editor-modal-footer-menu-item"><button class="editor-modal-footer-menu-button negative" data-button-type="close">' + getMessage.FTE01050 + '</li>'
        + '</ul>'
        + '</div>'
    } else {
        footerHTML = ''
        + '<div class="editor-modal-footer">'
        + '<ul class="editor-modal-footer-menu">'
            + '<li class="editor-modal-footer-menu-item"><button class="editor-modal-footer-menu-button positive" data-button-type="ok">' + getMessage.FTE01051 + '</li>'
            + '<li class="editor-modal-footer-menu-item"><button class="editor-modal-footer-menu-button negative" data-button-type="cancel">' + getMessage.FTE01052 + '</li>'
        + '</ul>'
        + '</div>'
    }

    let modalHTML = ''
        + '<div id="editor-modal" class="' + modalType + '">'
        + '<div class="editor-modal-container">'
            + '<div class="editor-modal-header">'
            + '<span class="editor-modal-title">' + headerTitle + '</span>'
            + '<button class="editor-modal-header-close"></button>'
            + '</div>'
            + '<div class="editor-modal-body">'
            + '<div class="editor-modal-loading"></div>'
            + '</div>'
            + footerHTML
        + '</div>'
        + '</div>';

    const $editorModal = $( modalHTML ),
            $firstFocus = $editorModal.find('.editor-modal-header-close'),
            $lastFocus = $editorModal.find('.editor-modal-footer-menu-button[data-button-type="cancel"]');

    $body.append( $editorModal );
    $firstFocus.focus();

    $window.on('keydown.modal', ( e ) => {
        switch ( e.keyCode ) {
            case 9: // Tabでの移動をモーダル内に制限する
            {
                const $focusElement = $( document.activeElement );
                if ( $focusElement.is( $firstFocus ) && e.shiftKey ) {
                    e.preventDefault();
                    $lastFocus.focus();
                } else if ( $focusElement.is( $lastFocus ) && !e.shiftKey ) {
                    e.preventDefault();
                    $firstFocus.focus();
                }
            }
            break;
            case 27: // Escでモーダルを閉じる
                this.itaModalClose();
                break;
        }
    });

    $firstFocus.on('click', () => {
        this.itaModalClose();
    });
    if ( modalType === 'help' ) {
        $editorModal.find('.editor-modal-footer-menu-button[data-button-type="close"]').on('click', cm.itaModalClose );
    }

    if ( target !== undefined ){
        bodyFunc.call( this, target );
    } else {
        bodyFunc.call( this );
    }
}
/*
##################################################
    モーダルを閉じる
##################################################
*/
itaModalClose() {
    const $window = $( window );
    const $editorModal = $('#editor-modal');

    if ( $editorModal.length ) {
        $window.off('keyup.modal');
        $editorModal.remove();
    }
}
/*
##################################################
    モーダルエラー表示
##################################################
*/
itaModalError( message ) {
    const $modalBody = $('.editor-modal-body');
    $modalBody.html('<div class="editor-modal-error"><p>' + message + '</p></div>');
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   カラム・グループ
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    項目（カラム・グループ）追加
##################################################
*/
addItem( type, id ) {
    // Templateから取得
    const target = ( type === 'column')? 'commonColumnContainerHtml': 'commonGroupContainerHtml';
    const clone = this.getFlagment( target );
    const element = clone.firstElementChild;

    // IDの指定が無い場合は新規    
    if ( id === undefined ) {
        if ( type === 'column') {
            const columnCounter = this.columnCounter++;
            id = `c${this.addItemIdCheck('c', columnCounter )}`;
            if ( !this.menuMap.has( id ) ) this.menuMap.set( id, this.initColumnData( columnCounter ) );
            if ( this.floor[0] === undefined ) this.floor[0] = 0;
            this.floor[0]++;
        } else {
            const groupCounter = this.groupCounter++;
            id = `g${this.addItemIdCheck('g', groupCounter )}`;
            if ( !this.menuMap.has( id ) ) this.menuMap.set( id, this.initGroupData( groupCounter ) );
            const empty = this.getFlagment('columnEmptyHtml');
            clone.querySelector('.menu-column-group-body').appendChild( empty );
        }
    }
    element.setAttribute('id', id );

    // emptyのみの場合は空にする
    if ( this.$.menuTable.children('.column-empty').length === 1 ) {
        this.$.menuTable.empty();
        this.$.previewTable.empty();
    }

    // 追加
    this.$.menuTable.append( clone );

    // 交差監視    
    this.itemIO.observe( element );

    // プレビュー
    const previewTarget = ( type === 'column')? 'previewColumnContainerHtml': 'previewGroupContainerHtml';
    const previewClone = this.getFlagment( previewTarget );
    const previewElement = previewClone.firstElementChild;
    previewElement.setAttribute('data-id', id );
    if ( type === 'group') {
        const previewEmpty = this.getFlagment('previewEmptyHtml');
        previewClone.querySelector('.previewGroupBody').appendChild( previewEmpty );
    }
    this.$.previewTable.append( previewElement );

    // プレビュー交差監視
    this.previewIO.observe( previewElement );

    this.history.add();

    // 追加した項目に合わせスクロールさせる
    const $scrollArea = this.$.menuEditWindow.children();
    const scrollElement = $scrollArea.get(0);
    const scrollWidth = scrollElement.scrollWidth;
    const clientWidth = scrollElement.clientWidth;
    if ( clientWidth < scrollWidth ) {
        $scrollArea.stop(0,0).animate({'scrollLeft': scrollWidth - clientWidth }, 200 );
    }

    this.updateCounter();
}
/*
##################################################
    IDチェック
##################################################
*/
addItemIdCheck( type, number ) {
    let id = `${type}${number}`;
    while ( this.menuMap.has( id ) ) {
        id = `${type}${++number}`;
    }
    return number;
}
/*
##################################################
    グループ内容セット
##################################################
*/
setGroupContents( id ) {
    const data = this.menuMap.get(id) ?? {};
    const clone = this.getFlagment('commonGroupHtml');

    const title = clone.querySelector('.menu-column-title-input');
    const titleDummy = title.nextElementSibling;
    const itemName = data.group_name ?? '';
    title.value = itemName;
    titleDummy.innerText = itemName;
    title.disabled = this.modeDisabled;

    return clone;
}
/*
##################################################
    グループ初期値
##################################################
*/
initGroupData( groupCounter ) {
    return {
        group_name: `${getMessage.FTE01002} ${groupCounter}`
    };
}
/*
##################################################
    項目・グループ数
##################################################
*/
updateCounter() {
    const size = this.getItemSize();
    this.$.counter.text( size );
    if ( size[0] > this.maxItem ) {
        this.$.counter.addClass('menu-editor-counter-over');
    } else {
        this.$.counter.removeClass('menu-editor-counter-over');
    }
}
getItemSize() {
    // グループと項目数
    return this.menuMap.size;
    /*
    // グループと項目数を別々にカウントする
    let countC = 0;
    let countG = 0;
    for (const key of this.menuMap.keys()) {
        const c = key[0];
        if ( c === 'c') countC++;
        else if ( c === 'g') countG++;
    }
    return [ countC, countG ];
    */
}
/*
##################################################
    カラム内容セット
##################################################
*/
setColumnContents( id ) {
    const data = this.menuMap.get(id) ?? {};
    const clone = this.getFlagment('commonColumnHtml');

    // 共通
    const header = clone.querySelector('.menu-column-header');
    const floor = data.floor ?? 0;
    header.setAttribute('data-floor', floor );

    const title = clone.querySelector('.menu-column-title-input');
    const titleDummy = title.nextElementSibling;
    const itemName = data.item_name ?? '';
    title.value = itemName;
    title.setAttribute('name', `${id}_menu_column_title_input`);
    titleDummy.innerText = itemName;
    title.disabled = this.modeDisabled;

    const rest = clone.querySelector('.menu-column-title-rest-input');
    const restDummy = rest.nextElementSibling;
    const itemNameRest = data.item_name_rest ?? '';
    rest.value = itemNameRest;
    rest.setAttribute('name', `${id}_menu_column_title_rest_input`);
    restDummy.innerText = itemNameRest;
    rest.disabled = this.modeDisabled;

    const classId = data.column_class_id ?? '1';
    const select = clone.querySelector('.menu-column-type-select');
    select.setAttribute('name', `${id}_column_class_id`);
    select.value = classId;
    select.disabled = ( this.modeDisabled || ( this.modeKeepData && typeof data.create_column_id === 'string') );

    // タイプ別
    const configTable = clone.querySelector('.menu-column-config-table tbody');
    this.setColumnType( configTable, id, classId, data )

    // 画面表示設定の開閉状態を復元
    if ( this.displaySettingOpenIds.has( id ) ) {
        clone.querySelector('.menu-column-config-table').classList.add('display-setting-open');
    }

    return clone;
}
/*
##################################################
    カラムタイプセット
##################################################
*/
setColumnType( configTable, id, classId, data ) {
    // 選択項目別
    const itemFlangment = this.getSelectTypeFlagment( classId );
    configTable.innerHTML = '';
    configTable.appendChild( itemFlangment );

    const target = '.input, .config-checkbox';
    const inputs = configTable.querySelectorAll( target );
    inputs.forEach( ( input ) => {
        const key = input.dataset.key;
        const nodeName = input.nodeName;
        input.setAttribute('name', `${id}_${key}`);

        const value = data[ key ] ?? null;
        if ( value === null ) {
            if ( this.editorMode === 'view' ) {
                input.disabled = true;
            }
            return;
        }

        if ( key === 'display_settings') {
            // 画面表示設定
            const settingKey = input.dataset.settingKey;
            const settingValue = ( fn.typeof( value ) === 'object')? value[ settingKey ]: null;
            if ( input.type === 'color') {
                // 色選択
                this.setDisplaySettingColor( input, settingValue );
                // 編集不可
                if ( this.editorMode === 'view' ) {
                    input.disabled = true;
                }
            } else {
                // チェックボックス
                if ( settingValue === true ) input.checked = true;
                // 編集不可
                if ( this.editorMode === 'view' ) {
                    input.disabled = true;
                    input.classList.add('disabled-checkbox');
                    const label = input.parentElement;
                    label.setAttribute('disabled', 'disabled');
                    label.classList.remove('on-hover');
                }
            }
        } else if ( key === 'required' || key === 'uniqued') {
            // チェックボックス
            if ( value === '1') input.checked = true;
            // 編集不可
            if ( this.modeDisabled || ( this.modeKeepData && typeof data.create_column_id === 'string') ) {
                input.disabled = true;
                input.classList.add('disabled-checkbox');
                const label = input.parentElement;
                label.setAttribute('disabled', 'disabled');
                label.classList.remove('on-hover');
            }
        } else if ( nodeName == 'SELECT') {
            // 選択リストはダミーDIVに値をセット
            const nameKey = input.dataset.namekey;
            let name;
            if ( key === 'pulldown_selection_default_value') {
                const menuId = data.pulldown_selection_id ?? null;
                if ( menuId === null ) return;
                input.setAttribute('data-menuId', menuId );
                if ( this.pulldownSelectionDefaultValue[ menuId ] ) {
                    name = this.pulldownSelectionDefaultValue[ menuId ][ value ]?? '';
                } else {
                    name = '';
                }
            } else {
                name = data[ nameKey ] ?? null;
            }
            if ( name === null ) return;

            const dummy = input.previousElementSibling;
            dummy.querySelector('.select-dummy-inner').innerText = name;
            dummy.setAttribute('data-id', value );
            input.setAttribute('data-id', value );
            // 編集不可
            const keepList = ['parameter_sheet_reference_id', 'pulldown_selection_id', 'pulldown_selection_default_value'];            
            if ( this.modeKeepData && keepList.includes( key ) && typeof data.create_column_id === 'string') {
                input.disabled = true;
                dummy.classList.add('disabled-select');
            }
        } else if ( key === 'reference_item') {
            // プルダウン選択：参照項目
            const setValue = fn.typeof( value ) === 'array'? value.join(','): '';
            if ( this.editorMode !== 'view') {
                input.innerText = setValue;
                input.setAttribute('data-reference-item-id', setValue );
                if ( this.modeKeepData && typeof data.create_column_id === 'string') {
                    input.classList.add('disabled-reference');
                    const button = input.nextElementSibling;
                    button.disabled = true;
                }
            } else {
                input.value = setValue;
                input.disabled = true;
            }
        } else {
            if ( key === 'pulldown_selection_default_value') {
                const menuId = data.pulldown_selection_id ?? null;
                if ( menuId === null ) return;
                let setValue;
                if ( this.pulldownSelectionDefaultValue[ menuId ] ) {
                    setValue = this.pulldownSelectionDefaultValue[ menuId ][ value ]?? '';
                } else {
                    setValue = '';
                }                
                input.value = setValue;
            } else {
                if ( value !== '' && ( key === 'description' || key === 'remarks') ) {
                    input.classList.add('text-in');
                }
                input.value = value;
            }
            // 編集不可
            if ( this.editorMode === 'view' ) {
                input.disabled = true;
            }
        }
    });
}
/*
##################################################
    選択項目別HTML
##################################################
*/
getSelectTypeFlagment( classId ) {
    const type = {
        '1': 'typeSingleTextHtml',
        '2': 'typeMultipleTextHtml',
        '3': 'typeIntegerHtml',
        '4': 'typeFloatHtml',
        '5': 'typeDateHtml',
        '6': 'typeDayHtml',
        '7': 'typePulldownHtml',
        '8': 'typePasswordHtml',
        '9': 'typeFileuploadHtml',
        '10': 'typeLinkHtml',
        '11': 'typeParameterSheetHtml',
    };
    const flagment = this.getFlagment( type[ classId ] );
    return flagment;
}
/*
##################################################
    カラム初期値
##################################################
*/
initColumnData( columnCounter ) {
    const column_class_id = '1';
    return {
        column_class_id: column_class_id,
        column_class: this.getColumnClassName( column_class_id ),
        item_name: `${getMessage.FTE01001} ${columnCounter}`,
        item_name_rest: `item_${columnCounter}`,
        // single_string_maximum_bytes: 16,
        floor: 0
    };
}
// クラスIDからクラス名を取得
getColumnClassName ( classId ) {
    const column_class = this.menuEditorArray.column_class_list.find( i => i.column_class_id === classId );
    return ( column_class && column_class.column_class_name ) ? column_class.column_class_name : '';
}
/*
##################################################
    カラムプレビュー内容セット
##################################################
*/
setPreviewColumnContents( id ) {
    const data = this.menuMap.get(id) ?? {};
    const clone = this.getFlagment('previewColumnHtml');
    const classId = data.column_class_id ?? '0';

    const header = clone.querySelector('.previewColumnHeader');
    const floor = data.floor ?? 0;
    header.setAttribute('data-floor', floor + 1 );
    const popup = data.description ?? '';
    if ( popup !== '') {
        header.setAttribute('title', popup );
        header.classList.add('popup');
    }

    const title = clone.querySelector('.previewColumnHeader .ci');
    const itemName = data.item_name ?? '';
    title.innerText = itemName;

    const contents = clone.querySelectorAll('.previewColumnBody .ci');
    contents.forEach( item => {
        let text;
        if ( classId === '7') {
            text = data.pulldown_selection ?? '';
        } else {
            text = this.selectDummyText[ classId ][0];
        }
        const type = this.selectDummyText[ classId ][1];
        item.innerHTML = text;
        item.classList.add( type );
    });

    // 画面表示設定の色
    const displaySettings = ( fn.typeof( data.display_settings ) === 'object')? data.display_settings: {};
    if ( this.isDisplaySettingColor( displaySettings.header_color ) ) {
        const headerCell = clone.querySelector('.previewColumnHeader > div');
        const textColor = fn.contrastTextColor( displaySettings.header_color );
        headerCell.style.backgroundColor = displaySettings.header_color;
        headerCell.style.color = textColor;
        // 黒文字の場合は白の影を消す
        if ( textColor !== '#FFFFFF') headerCell.style.textShadow = 'none';
    }
    if ( this.isDisplaySettingColor( displaySettings.body_color ) ) {
        // 奇数行はそのまま、偶数行はうっすら濃くする
        const oddColor = displaySettings.body_color;
        const evenColor = fn.darkenColor( oddColor );
        const oddTextColor = fn.contrastTextColor( oddColor );
        const evenTextColor = fn.contrastTextColor( evenColor );
        clone.querySelectorAll('.previewColumnBody > div').forEach( ( cell, index ) => {
            const isEven = ( index % 2 === 1 );
            cell.style.backgroundColor = ( isEven )? evenColor: oddColor;
            cell.style.color = ( isEven )? evenTextColor: oddTextColor;
        });
    }

    // 参照項目があれば追加して返す
    if ( classId === '7') {
        const list = data.reference_item ?? [];
        const flagment = document.createDocumentFragment();
        flagment.appendChild( clone );
        for ( const item of list ) {
            const refClone = this.getFlagment('previewColumnHtml');
            const refHeader = refClone.querySelector('.previewColumnHeader');
            refHeader.setAttribute('data-floor', floor + 1 );
            const refTitle = refClone.querySelector('.previewColumnHeader .ci');
            refTitle.innerText = `${getMessage.FTE01093}(${item})`;

            const refContents = refClone.querySelectorAll('.previewColumnBody .ci');
            refContents.forEach( item => {
                const text = getMessage.FTE01102;
                const type = this.selectDummyText[ classId ][1];
                item.innerHTML = text;
                item.classList.add( type );
            });
            flagment.appendChild( refClone );
        }
        return flagment;
    } else {
        return clone;
    }
}
getPreviewColumnPreviewContents( id ) {
    let text;
    const data = this.menuMap.get(id) ?? {};
    const classId = data.column_class_id ?? '0';
    if ( classId === '7') {
        text = data.pulldown_selection ?? '';
    } else {
        text = this.selectDummyText[ classId ][0];
    }
    return text;
}
// 画面表示設定を開いている項目ID
displaySettingOpenIds = new Set();
// 内容テキスト
selectDummyText = {
    '0' : ['',''],
    '1' : [getMessage.FTE01097,'string'],
    '2' : [getMessage.FTE01098 + '<br>' + getMessage.FTE01098,'string'],
    '3' : ['0',,'number'],
    '4' : ['0.0','number'],
    '5' : ['2020/01/01 00:00','string'],
    '6' : ['2020/01/01','string'],
    '7' : ['','select'],
    '8' : [getMessage.FTE01099,'string'],
    '9' : [getMessage.FTE01100,'string'],
    '10' : [getMessage.FTE01101,'string'],
    '11' : [getMessage.FTE01102,'string']
}
// プレビュー更新
updatePreviewColumn( id ) {
    const $item = this.$.previewTable.find(`[data-id="${id}"]`);
    $item.html( this.setPreviewColumnContents( id ) );
}
/*
##################################################
    グループプレビュー内容セット
##################################################
*/
setPreviewGroupContents( id ) {
    const data = this.menuMap.get(id) ?? {};
    const itemName = data.group_name ?? '';
    return itemName;
}
// プレビュー更新
updatePreviewGroup( id ) {
    const $item = this.$.previewTable.find(`[data-id="${id}"]`);
    $item.find('.previewGroupHeader .ci').first().text( this.setPreviewGroupContents( id ) );
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   カラム・グループの交差監視
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    交差監視作成
##################################################
*/
createItemIntersectionObserver() {
    const _this = this;
    const itemIntersectionObserver = this.rafThrottle( ( entries ) => {
        for ( const entry of entries ) {
            const el = entry.target;
            const id = el.getAttribute('id');
            const type = id[0];
            if ( entry.isIntersecting ) {
                // 画面内に入ったら
                if ( type === 'c') {
                    el.style.width = 'auto';
                    el.style.height = 'auto';
                    el.replaceChildren( _this.setColumnContents( id ) );
                } else {
                    el.querySelector('.menu-column-group-header').replaceChildren( _this.setGroupContents( id ) );
                }
            } else {
                // 画面外に出たら
                if ( type === 'c') {
                    const data = this.menuMap.get( id );
                    if ( data ) {
                        const name = data.item_name ?? '';
                        const rest = data.item_name_rest ?? '';
                        const rect = el.getBoundingClientRect()
                        const width = rect.width;
                        const height = rect.height;
                        el.style.width = `${width}px`;
                        el.style.height = `${height}px`;
                        el.innerHTML = `<span class="column-dummy">${fn.escape(name)}<br>${fn.escape(rest)}</span>`;
                    }
                } else {
                    el.querySelector('.menu-column-group-header').innerHTML = '';
                }                
            }
        }
    });
    this.itemIO = new IntersectionObserver( itemIntersectionObserver, {
        root: document.querySelector('.menu-editor-block-inner'),
        rootMargin: '0px 100px 0px 100px'
    });

    const previewIntersectionObserver = this.rafThrottle( ( entries ) => {
        for ( const entry of entries ) {
            const el = entry.target;
            const id = el.getAttribute('data-id');
            const type = id[0];
            if ( entry.isIntersecting ) {
                if ( type === 'c') {
                    el.replaceChildren( _this.setPreviewColumnContents( id ) );
                } else {
                    el.querySelector('.previewGroupHeader .ci').innerText = _this.setPreviewGroupContents( id );
                }
            } else {
                if ( type === 'c') {
                    const data = this.menuMap.get( id );
                    if ( data ) {
                        const name = data.item_name ?? '';
                        const dummy = this.getPreviewColumnPreviewContents( id );
                        el.innerHTML = `<span class="column-dummy">${fn.escape(name)}<br>${dummy}</span>`;;
                    }
                } else {
                    el.querySelector('.previewGroupHeader .ci').innerText = '';
                }
            }
        }
    });
    this.previewIO = new IntersectionObserver( previewIntersectionObserver, {
        root: document.querySelector('.tableWrap'),
        rootMargin: '0px 100px 0px 100px'
    });
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   JSON読込・保存
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    JSON読み込み
##################################################
*/
jsonRead() {
    fn.fileSelect('json').then( ( result ) => {
        try {
            // リセット
            this.menuEditorArray.menu_info = result.json;
            this.setMenu('jsonRead');
        } catch ( e ) {
            console.error( e );
            alert( getMessage.FTE01157 );
            clearTable();
        }
    }).catch( ( e ) => {
        if ( e === 'cancel') return;
        console.error( e );
        alert( e );
        clearTable();
    });
}
/*
##################################################
    JSON保存（ダウンロード）
##################################################
*/
jsonSave() {
    const inputName = $('#create-menu-name').val();
    const fileName = ( inputName !== '')? inputName: 'parameter_sheet';
    fn.download('json', this.createJsonData('file'), fileName );
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Template
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    Templateセット
##################################################
*/
setTemplates() {
    const templates = [
        'commonGroupContainerHtml',
        'commonGroupHtml',
        'commonColumnContainerHtml',
        'commonColumnHtml',
        'columnEmptyHtml',

        'typeSingleTextHtml',
        'typeMultipleTextHtml',
        'typeIntegerHtml',
        'typeFloatHtml',
        'typeDateHtml',
        'typeDayHtml',
        'typePulldownHtml',
        'typePasswordHtml',
        'typeFileuploadHtml',
        'typeLinkHtml',
        'typeParameterSheetHtml',

        'previewGroupContainerHtml',
        'previewColumnContainerHtml',
        'previewColumnHtml',
        'previewEmptyHtml'
    ];
    for ( const key of templates ) {
        if ( key !== 'previewColumnHtml') {
            this.$.body.append( this.createTemplate( key, this[ key ]() ) );
        } else {
            this.$.body.append( this.createTemplate( key, this[ key ]('tHeadTh th', '', '', 0 )));
        }
    }
}
/*
##################################################
    Template作成
##################################################
*/
createTemplate( id, html ) {
    return `<template id="${id}">${html}</template>`;
}
/*
##################################################
    Flagment取得
##################################################
*/
getFlagment( type ) {
    const flagment = document.getElementById( type ).content.cloneNode( true );
    return flagment;
}
/*
##################################################
    Element取得
##################################################
*/
getElement( type ) {
    const flagment = this.getFlagment( type );
    const element = flagment.firstElementChild;
    return element;
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   メインHTML
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    Main HTML
##################################################
*/
createMainHtml() {
    return `
    <div id="menu-editor" class="editor load-wait" data-editor-mode="${this.editorMode}" data-load-menu-id="${this.loadMenuID}">
        <div class="editor-inner">
            <div id="menu-editor-main" class="editor-main">
                <div id="menu-editor-menu" class="editor-menu">
                    ${this.editorOperationMenuHtml()}
                </div>
                <div id="menu-editor-header" class="editor-header">
                    ${this.editorMenuHtml()}
                </div>
                <div id="menu-editor-body" class="editor-body editor-row-resize">
                    <div id="menu-editor-edit" class="editor-block menu-editor-block">
                        <div class="editor-block-inner menu-editor-block-inner">
                            <div class="menu-table-wrapper">
                                <div class="menu-table">
                                    ${this.columnEmptyHtml()}
                                </div>
                            </div>
                        </div>
                        <div id="column-resize"></div>
                    </div>
                    <div id="menu-editor-row-resize" class="editor-row-resize-bar"></div>
                    <div id="menu-editor-info" class="editor-block menu-editor-block">
                        <div class="editor-block-inner">
                            <div class="editor-tab">
                                <div class="editor-tab-menu">
                                    <ul class="editor-tab-menu-list">
                                        <li class="editor-tab-menu-item" data-tab="menu-editor-preview">${getMessage.FTE01005}</li>
                                        <li class="editor-tab-menu-item" data-tab="menu-editor-log">${getMessage.FTE01006}</li>
                                    </ul>
                                </div>
                                <div class="editor-tab-contents">
                                    <div id="menu-editor-preview" class="editor-tab-body">
                                        ${this.previewContainerHtml()}
                                    </div>
                                    <div id="menu-editor-log" class="editor-tab-body">
                                        <div class="editor-log">
                                            <table class="editor-log-table">
                                                <tbody></tbody>
                                            </table>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="eritor-panel">
                ${this.panelContainerHtml( this.editorMode )}
            </div>
        </div>
        <style id="menu-editor-style"></style>
    </div>
    `;
}
/*
##################################################
    作業メニューHTML
##################################################
*/
editorOperationMenuHtml() {
    const menuList = {
        Sub: [
            { className: 'fullscreen-on', button: { className: 'menu-editor-menu-button', icon: 'expansion', text: getMessage.FTE01148, type: 'fullscreen', action: 'default', minWidth: '120px'}},
            { className: 'fullscreen-off', button: { className: 'menu-editor-menu-button', icon: 'shrink', text: getMessage.FTE01149, type: 'fullscreen', action: 'default', minWidth: '120px'}}
        ]
    };
    if ( this.editorMode === 'new' || this.editorMode === 'diversion'){
        menuList.Main = [
            { button: { className: 'menu-editor-menu-button', icon: 'plus', text: getMessage.FTE01041, type: 'registration', action: 'positive', minWidth: '160px'}},
        ];
    } else if ( this.editorMode === 'view' ){
        if ( this.createManagementMenuID !== '' ) {
            menuList.Main = [
                { button: { className: 'menu-editor-menu-button', icon: 'edit', text: getMessage.FTE01042, type: 'edit', action: 'positive', minWidth: '160px'}},
                { button: { className: 'menu-editor-menu-button', icon: 'clear', text: getMessage.FTE01043, type: 'initialize', action: 'negative', minWidth: '120px'}, separate: true },
                { button: { className: 'menu-editor-menu-button', icon: 'copy', text: getMessage.FTE01044, type: 'diversion', action: 'negative', minWidth: '120px'}},
                { button: { className: 'menu-editor-menu-button', icon: 'check', text: getMessage.FTE01045, type: 'management', action: 'default', minWidth: '160px'}, separate: true },
            ];
        } else {
            menuList.Main = [
                { button: { className: 'menu-editor-menu-button', icon: 'edit', text: getMessage.FTE01042, type: 'edit', action: 'positive', minWidth: '160px'}},
                { button: { className: 'menu-editor-menu-button', icon: 'clear', text: getMessage.FTE01043, type: 'initialize', action: 'negative', minWidth: '120px'}, separate: true },
                { button: { className: 'menu-editor-menu-button', icon: 'copy', text: getMessage.FTE01044, type: 'diversion', action: 'negative', minWidth: '120px'}},
            ];
        }
    } else if ( this.editorMode === 'initialize' ){
        menuList.Main = [
            { button: { className: 'menu-editor-menu-button', icon: 'plus', text: getMessage.FTE01046, type: 'update-initialize', action: 'positive', minWidth: '160px'}},
            { button: { className: 'menu-editor-menu-button', icon: 'update01', text: getMessage.FTE01047, type: 'reload-initialize', action: 'negative', minWidth: '120px'}, separate: true },
            { button: { className: 'menu-editor-menu-button', icon: 'cross', text: getMessage.FTE01048, type: 'cancel', action: 'negative', minWidth: '120px'}},
        ];
    } else if ( this.editorMode === 'edit' ){
        menuList.Main = [
            { button: { className: 'menu-editor-menu-button', icon: 'plus', text: getMessage.FTE01049, type: 'update', action: 'positive', minWidth: '160px'}},
            { button: { className: 'menu-editor-menu-button', icon: 'update01', text: getMessage.FTE01047, type: 'reload', action: 'negative', minWidth: '120px'}, separate: true },
            { button: { className: 'menu-editor-menu-button', icon: 'cross', text: getMessage.FTE01048, type: 'cancel', action: 'negative', minWidth: '120px'}},
        ];
    }
    return fn.html.operationMenu( menuList );
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   エディタHTML
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    エディターメニューHTML
##################################################
*/
editorMenuHtml() {
    if ( this.editorMode !== 'view' ){
        const jsonButton = [`<li class="editor-menu-item menu-editor-menu-li"><button class="editor-menu-button menu-editor-menu-button" data-type="jsonSave">${getMessage.FTE02021}</button></li>`];
        if ( this.editorMode === 'new' || this.editorMode === 'diversion') {
            jsonButton.unshift(`<li class="editor-menu-item menu-editor-menu-li"><button class="editor-menu-button menu-editor-menu-button" data-type="jsonRead">${getMessage.FTE02022}</button></li>`)
        }
        return `
        <div class="menu-editor-menu">
            <ul class="editor-menu-list menu-editor-menu-ul">
                ${jsonButton.join('')}
                <li class="editor-menu-separate editor-menu-item menu-editor-menu-li"><button class="editor-menu-button menu-editor-menu-button" data-type="newColumn">${getMessage.FTE01001}</button></li>
                <li class="editor-menu-item menu-editor-menu-li"><button class="editor-menu-button menu-editor-menu-button" data-type="newColumnGroup">${getMessage.FTE01002}</button></li>
                <li class="editor-menu-separate editor-menu-item menu-editor-menu-li"><button id="button-undo" class="editor-menu-button menu-editor-menu-button" data-type="undo">${getMessage.FTE01003}</button></li>
                <li class="editor-menu-item menu-editor-menu-li"><button id="button-redo" class="editor-menu-button menu-editor-menu-button" data-type="redo">${getMessage.FTE01004}</button></li>
            </ul>
        </div>`;
    }
    return '';
}
/*
##################################################
    グループコンテナHTML
##################################################
*/
commonGroupContainerHtml() {
    return `
    <div class="menu-column-group">
        <div class="menu-column-group-header">
        </div>
        <div class="menu-column-group-body">
        </div>
    </div>`;
}
/*
##################################################
    グループHTML
##################################################
*/
commonGroupHtml() {
    return `
    <div class="menu-column-move" title="${fn.escape(getMessage.FTE01103)}"></div>
    <div class="menu-column-title on-hover" title="${fn.escape(getMessage.FTE01104)}">
        <input class="menu-column-title-input" type="text" data-key="group_name" autocomplete="off">
        <span class="menu-column-title-dummy"></span>
    </div>
    <div class="menu-column-function">
        <div class="menu-column-delete on-hover" title="${fn.escape(getMessage.FTE01106)}"></div>
        <div class="menu-column-copy on-hover" title="${fn.escape(getMessage.FTE01107)}"></div>
    </div>`;
}
/*
##################################################
    カラムコンテナHTML
##################################################
*/
commonColumnContainerHtml() {
    return `<div class="menu-column" style="min-width:${this.columnMinWidth}px"></div>`;
}
/*
##################################################
    カラムHTML
##################################################
*/
commonColumnHtml() {
    return `
    <div class="menu-column-header">
        <div class="menu-column-move" title="${fn.escape(getMessage.FTE01103)}"></div>
        <div class="menu-column-title-wrap">
            <div class="menu-column-title on-hover" title="${fn.escape(getMessage.FTE01104)}">
                <input class="menu-column-title-input" type="text" data-key="item_name" autocomplete="off">
                <span class="menu-column-title-dummy"></span>
            </div>
            <div class="menu-column-title on-hover" title="${fn.escape(getMessage.FTE01105)}">
                <input class="menu-column-title-rest-input" type="text" data-key="item_name_rest" autocomplete="off">
                <span class="menu-column-title-dummy"></span>
            </div>
        </div>
        <div class="menu-column-function">
            <div class="menu-column-delete on-hover" title="${fn.escape(getMessage.FTE01106)}"></div>
            <div class="menu-column-copy on-hover" title="${fn.escape(getMessage.FTE01107)}"></div>
        </div>
    </div>
    <div class="menu-column-body">
        <div class="menu-column-type" title="${fn.escape(getMessage.FTE01109)}">
            <select class="input menu-column-type-select" data-key="column_class_id">
                ${this.editColumnTypeSelectHtml()}
            </select>
        </div>
        <div class="menu-column-config">
            <table class="menu-column-config-table">
                <tbody></tbody>
            </table>
        </div>
    </div>
    <div class="column-resize"></div>`;
}
/*
##################################################
    編集カラムタイプ選択HTML
##################################################
*/
editColumnTypeSelectHtml() {
    const columnClassListHtml = [];
    const columnClassList = this.menuEditorArray.column_class_list;
    const columnClassListLength = columnClassList.length;
    for ( let i = 0; i < columnClassListLength ; i++ ) {
        const classID = columnClassList[i].column_class_id;
        columnClassListHtml.push(`<option value="${classID}" data-value="${columnClassList[i].column_class_name}">${columnClassList[i].column_class_disp_name}</option>`);
    }
    return columnClassListHtml.join('');
}
/*
##################################################
    カラムタイプ別HTML
##################################################
*/
// 文字列(単一行)
typeSingleTextHtml() {
    return `
    <!-- 最大バイト数 single -->
    <tr title="${fn.escape(getMessage.FTE01110)}">
        <th class="half-cell"><span class="config-title">${getMessage.FTE01055 + fn.html.required()}</span></th>
        <td class="half-cell">
            <input class="input config-number max-byte" type="number" data-min="1" data-max="${this.stringMaxByte}" data-key="single_string_maximum_bytes" autocomplete="off">
        </td>
    </tr>
    <!-- 正規表現 single -->
    <tr title="${fn.escape(getMessage.FTE01111)}">
        <th class="full-head"><span class="config-title">${getMessage.FTE01056}</span></th>
        <td class="full-body">
            <input class="input config-text regex" type="text" data-key="single_string_regular_expression" autocomplete="off">
        </td>
    </tr>
    <!-- 初期値 -->
    <tr title="${fn.escape(getMessage.FTE01121)}">
        <th class="full-head"><span class="config-title">${getMessage.FTE01094}</span></th>
        <td class="full-body">
            <input class="input config-text single-default-value" type="text" data-key="single_string_default_value" autocomplete="off">
        </td>
    </tr>
    ${this.typeCommonRequiredUniquehtml()}
    ${this.typeCommonExplanationNotehtml()}
    ${this.typeCommonDisplaySettingHtml()}`;
}
// 文字列(複数行)
typeMultipleTextHtml() {
    return `
    <!-- 最大バイト数 multiple -->
    <tr title="${fn.escape(getMessage.FTE01110)}">
        <th class="half-cell"><span class="config-title">${getMessage.FTE01055 + fn.html.required()}</span></th>
        <td class="half-cell">
            <input class="input config-number multiple-max-byte" type="number" data-min="1" data-max="${this.stringMaxByte}" data-key="multi_string_maximum_bytes" autocomplete="off">
        </td>
    </tr>
    <!-- 正規表現 multiple -->
    <tr title="${fn.escape(getMessage.FTE01111)}">
        <th class="full-head"><span class="config-title">${getMessage.FTE01056}</span></th>
        <td class="full-body">
            <input class="input config-text multiple-regex" type="text" data-key="multi_string_regular_expression" autocomplete="off">
        </td>
    </tr>
    <!-- 初期値 複数行 -->
    <tr class="multiple" title="${fn.escape(getMessage.FTE01121)}">
        <th class="full-head"><span class="config-title">${getMessage.FTE01094}</span></th>
        <td class="full-body">
            <textarea class="input config-textarea multiple-default-value" data-key="multi_string_default_value"></textarea>
        </td>
    </tr>
    ${this.typeCommonRequiredUniquehtml()}
    ${this.typeCommonExplanationNotehtml()}
    ${this.typeCommonDisplaySettingHtml()}`;
}
// 整数
typeIntegerHtml() {
    return `
    <!-- 最小値 int -->
    <tr title="${fn.escape(getMessage.FTE01112)}">
        <th class="half-cell"><span class="config-title">${getMessage.FTE01057}</span></th>
        <td class="half-cell">
            <input class="input config-number int-min-number" data-min="-2147483648" data-max="2147483647" type="number" data-key="integer_minimum_value" autocomplete="off">
        </td>
    </tr>
    <!-- 最大値 int -->
    <tr title="${fn.escape(getMessage.FTE01113)}">
        <th class="half-cell"><span class="config-title">${getMessage.FTE01058}</span></th>
        <td class="half-cell">
            <input class="input config-number int-max-number" data-min="-2147483648" data-max="2147483647" type="number" data-key="integer_maximum_value" autocomplete="off">
        </td>
    </tr>
    <!-- 初期値 int -->
    <tr title="${fn.escape(getMessage.FTE01122)}">
        <th class="half-cell"><span class="config-title">${getMessage.FTE01094}</span></th>
        <td class="half-cell">
            <input class="input config-number int-default-value" data-min="-2147483648" data-max="2147483647" type="number" data-key="integer_default_value" autocomplete="off">
        </td>
    </tr>
    ${this.typeCommonRequiredUniquehtml()}
    ${this.typeCommonExplanationNotehtml()}
    ${this.typeCommonDisplaySettingHtml()}`;
}
// 小数
typeFloatHtml() {
    return `
    <!-- 最小値 froat -->
    <tr title="${fn.escape(getMessage.FTE01114)}">
        <th class="half-cell"><span class="config-title">${getMessage.FTE01057}</span></th>
        <td class="half-cell">
            <input class="input config-number float-min-number" data-min="-99999999999999" data-max="99999999999999" type="number" data-key="decimal_minimum_value" autocomplete="off">
        </td>
    </tr>
    <!-- 最大値 froat -->
    <tr title="'${fn.escape(getMessage.FTE01115)}">
        <th class="half-cell"><span class="config-title">${getMessage.FTE01058}</span></th>
        <td class="half-cell">
            <input class="input config-number float-max-number" data-min="-99999999999999" data-max="99999999999999" type="number" data-key="decimal_maximum_value" autocomplete="off">
        </td>
    </tr>
    <!-- 桁数 -->
    <tr title="${fn.escape(getMessage.FTE01116)}">
        <th class="half-cell"><span class="config-title">${getMessage.FTE01059}</span></th>
        <td class="half-cell">
            <input class="input config-number digit-number" data-min="1" data-max="14" type="number" data-key="decimal_digit" autocomplete="off">
        </td>
    </tr>
    <!-- 初期値 float -->
    <tr title="${fn.escape(getMessage.FTE01123)}">
        <th class="half-cell"><span class="config-title">${getMessage.FTE01094}</span></th>
        <td class="half-cell">
            <input class="input config-number float-default-value" data-min="-99999999999999" data-max="99999999999999" type="number" data-key="decimal_default_value" autocomplete="off">
        </td>
    </tr>
    ${this.typeCommonRequiredUniquehtml()}
    ${this.typeCommonExplanationNotehtml()}
    ${this.typeCommonDisplaySettingHtml()}`;
}
// 日時
typeDateHtml() {
    return `
    <!-- 初期値 日時 -->
    <tr title="${fn.escape(getMessage.FTE01124)}">
        <th class="full-head"><span class="config-title">${getMessage.FTE01094}</span></th>
        <td class="full-body">${( this.editorMode !== 'view')?
            fn.html.dateInput( true, 'callDateTimePicker datetime-default-value config-text', '', '', {'key':'datetime_default_value'}):
            `<input class="input datetime-default-value config-text" data-key="datetime_default_value" autocomplete="off">`
        }</td>
    </tr>
    ${this.typeCommonRequiredUniquehtml()}
    ${this.typeCommonExplanationNotehtml()}
    ${this.typeCommonDisplaySettingHtml()}`;
}
// 日付
typeDayHtml() {
    return `
    <!-- 初期値 日付 -->
    <tr class="date" title="${fn.escape(getMessage.FTE01124)}">
        <th class="full-head"><span class="config-title">${getMessage.FTE01094}</span></th>
        <td class="full-body">${( this.editorMode !== 'view')?
            fn.html.dateInput( false, 'callDateTimePicker date-default-value config-text', '', '', {'key':'date_default_value'}):
            `<input class="input date-default-value config-text" data-key="date_default_value" autocomplete="off">`
        }</td>
    </tr>
    ${this.typeCommonRequiredUniquehtml()}
    ${this.typeCommonExplanationNotehtml()}
    ${this.typeCommonDisplaySettingHtml()}`;
}
// プルダウン選択
typePulldownHtml() {
    return `
    <!-- プルダウン選択項目 -->
    <tr title="${fn.escape(getMessage.FTE01117)}">
        <th class="full-head"><span class="config-title">${getMessage.FTE01060 + fn.html.required()}</span></th>
        <td class="full-body">${( this.editorMode !== 'view')?
            `<div class="select-container tableEditInputSelectContainer">
                <div class="select-dummy tableEditInputSelectValue">
                    <span class="select-dummy-inner tableEditInputSelectValueInner"></span>
                </div>
                <select class="input config-select pulldown-select" data-key="pulldown_selection_id" data-nameKey="pulldown_selection"></select>
            </div>`:
            `<input class="input config-text" data-key="pulldown_selection">`}
        </td>
    </tr>
    <!-- 参照項目 -->
    <tr title="${fn.escape(getMessage.FTE01118)}">
        <th class="full-head"><span class="config-title">${getMessage.FTE01087}</span></th>
        <td class="full-body">${( this.editorMode !== 'view')?
            `<div class="reference-block">
                <span type="text" class="input config-text reference-item" type="text" data-key="reference_item"></span>
                <button class="itaButton button reference-item-select property-button popup" data-action="normal" title="${fn.escape(getMessage.FTE01089)}">
                    <div class="inner">${fn.html.icon('menuList')}</div>
                </button>
            </div>`:
            `<input class="input config-text" data-key="reference_item">`}
        </td>
    </tr>
    <!-- 初期値 選択 -->
    <tr title="${fn.escape(getMessage.FTE01126)}">
        <th class="full-head">${getMessage.FTE01094}</th>
        <td class="full-body pulldown-default-select-body">${( this.editorMode !== 'view')?
            this.typePulldownDefaultValueHtml():
            `<input class="input config-text" data-key="pulldown_selection_default_value" data-nameKey="pulldown_selection_default_value_name">`}
        </td>
    </tr>
    ${this.typeCommonRequiredUniquehtml()}
    ${this.typeCommonExplanationNotehtml()}
    ${this.typeCommonDisplaySettingHtml()}`;
}
typePulldownDefaultValueHtml() {
    return `
    <div class="select-container tableEditInputSelectContainer">
        <div class="select-dummy tableEditInputSelectValue">
            <span class="select-dummy-inner tableEditInputSelectValueInner"></span>
        </div>
        <select class="input config-select pulldown-default-select" data-key="pulldown_selection_default_value" data-nameKey="pulldown_selection_default_value_name"></select>
    </div>`;
}
// パスワード
typePasswordHtml() {
    return `
    <!-- 最大バイト数 パスワード -->
    <tr class="password" title="${fn.escape(getMessage.FTE01158)}">
        <th class="full-head"><span class="config-title">${getMessage.FTE01055 + fn.html.required()}</span></th>
        <td class="full-body">
            <input class="input config-number password-max-byte" type="number" data-min="1" data-max="8192" data-key="password_maximum_bytes" autocomplete="off">
        </td>
    </tr>
    ${this.typeCommonRequiredUniquehtml()}
    ${this.typeCommonExplanationNotehtml()}
    ${this.typeCommonDisplaySettingHtml()}`;
}
// ファイルアップロード
typeFileuploadHtml() {
    return `
    <!-- 最大バイト数 ファイル -->
    <tr title="${fn.escape(getMessage.FTE01119(this.fileMaxSize))}">
        <th class="full-head"><span class="config-title">${getMessage.FTE01086 + fn.html.required()}</span></th>
        <td class="full-body">
            <input class="input config-number file-max-size" data-min="1" data-max="${this.fileMaxSize}" type="number" data-key="file_upload_maximum_bytes" autocomplete="off">
        </td>
    </tr>
    ${this.typeCommonRequiredUniquehtml()}
    ${this.typeCommonExplanationNotehtml()}
    ${this.typeCommonDisplaySettingHtml()}`;
}
// リンク
typeLinkHtml() {
    return `
    <!-- 最大バイト数 link -->
    <tr class="link" title="${fn.escape(getMessage.FTE01158)}">
        <th class="half-cell"><span class="config-title">${getMessage.FTE01055 + fn.html.required()}</span></th>
        <td class="half-cell">
            <input class="input config-number link-max-byte" type="number" data-min="1" data-max="8192" data-key="link_maximum_bytes" autocomplete="off">
        </td>
    </tr>
    <!-- 初期値 リンク -->
    <tr class="link" title="${fn.escape(getMessage.FTE01125)}">
        <th class="full-head"><span class="config-title">${getMessage.FTE01094}</span></th>
        <td class="full-body">
            <input class="input config-text link-default-value" type="text" data-key="link_default_value" autocomplete="off">
        </td>
    </tr>
    ${this.typeCommonRequiredUniquehtml()}
    ${this.typeCommonExplanationNotehtml()}
    ${this.typeCommonDisplaySettingHtml()}`;
}
// パラメータシート参照
typeParameterSheetHtml() {
    return `
    <!-- パラメータシート参照項目 -->
    <tr class="param-sheet-ref" title="${fn.escape(getMessage.FTE01117)}">
        <th class="full-head"><span class="config-title">${getMessage.FTE01060 + fn.html.required()}</span></th>
        <td class="full-body">${( this.editorMode !== 'view')?
            `<div class="select-container tableEditInputSelectContainer">
                <div class="select-dummy tableEditInputSelectValue">
                    <span class="select-dummy-inner tableEditInputSelectValueInner"></span>
                </div>
                <select class="input config-select reference-parameter-sheet" data-key="parameter_sheet_reference_id" data-nameKey="parameter_sheet_reference"></select>
            </div>`:
            `<input class="input config-text" type="text" data-key="parameter_sheet_reference">`}
        </td>
    </tr>
    ${this.typeCommonExplanationNotehtml()}
    ${this.typeCommonDisplaySettingHtml()}`;
}
/*
##################################################
    カラムタイプ共通HTML
##################################################
*/
// 一意・必須
typeCommonRequiredUniquehtml() {
    return `
    <!-- 必須・一意 -->
    <tr>
        <td colspan="2">
            <label class="required-label on-hover" title="${fn.escape(getMessage.FTE01127)}">
                <input class="config-checkbox required" type="checkbox" data-key="required">
                <span></span>${getMessage.FTE01061}
            </label>
            <label class="unique-label on-hover" title="${fn.escape(getMessage.FTE01128)}">
            <input class="config-checkbox unique" type="checkbox" data-key="uniqued">
                <span></span>${getMessage.FTE01062}
            </label>
        </td>
    </tr>`;
}
// 説明・備考
typeCommonExplanationNotehtml() {
    return `
    <!-- 説明 -->
    <tr title="${fn.escape(getMessage.FTE01129)}">
        <td colspan="2">
            <div class="config-textarea-wrapper">
                <textarea class="input config-textarea explanation" data-key="description"></textarea>
                <span>${getMessage.FTE01063}</span>
            </div>
        </td>
    </tr>
    <!-- 備考 -->
    <tr title="${fn.escape(getMessage.FTE01130)}">
        <td colspan="2">
            <div class="config-textarea-wrapper">
                <textarea class="input config-textarea note" data-key="remarks"></textarea>
                <span>${getMessage.FTE01064}</span>
            </div>
        </td>
    </tr>`;
}
// 画面表示設定
typeCommonDisplaySettingHtml() {
    return `
    <!-- 画面表示設定 -->
    <tr class="display-setting-toggle-row">
        <td colspan="2">
            <button type="button" class="display-setting-toggle" title="${fn.escape(getMessage.FTE01163)}">
                <span class="display-setting-toggle-mark"></span>${getMessage.FTE01162}
            </button>
        </td>
    </tr>
    <!-- 画面表示設定：画面からの編集を禁止 -->
    <tr class="display-setting-row">
        <td colspan="2">
            <label class="display-setting-label on-hover" title="${fn.escape(getMessage.FTE01165)}">
                <input class="config-checkbox display-setting" type="checkbox" data-key="display_settings" data-setting-key="disable_edit">
                <span></span>${getMessage.FTE01164}
            </label>
        </td>
    </tr>
    <!-- 画面表示設定：ヘッダー色 -->
    <tr class="display-setting-row" title="${fn.escape(getMessage.FTE01167)}">
        <th class="half-cell"><span class="config-title">${getMessage.FTE01166}</span></th>
        <td class="half-cell">${this.typeCommonDisplaySettingColorHtml('header_color')}</td>
    </tr>
    <!-- 画面表示設定：ボディ色 -->
    <tr class="display-setting-row" title="${fn.escape(getMessage.FTE01169)}">
        <th class="half-cell"><span class="config-title">${getMessage.FTE01168}</span></th>
        <td class="half-cell">${this.typeCommonDisplaySettingColorHtml('body_color')}</td>
    </tr>`;
}
// 画面表示設定：色選択
typeCommonDisplaySettingColorHtml( settingKey ) {
    const disabled = ( this.editorMode === 'view')? ' disabled': '';
    return `
    <div class="display-setting-color color-unset">
        <input class="input config-color" type="color" data-key="display_settings" data-setting-key="${settingKey}" value="#ffffff">
        <span class="display-setting-color-value">${getMessage.FTE01170}</span>
        <button type="button" class="display-setting-color-clear" title="${fn.escape(getMessage.FTE01171)}"${disabled}></button>
    </div>`;
}
/*
##################################################
    空HTML
##################################################
*/
columnEmptyHtml() {
    return `<div class="column-empty"><p>Empty</p></div>`;
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//  プレビューHTML
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    プレビューHTML
##################################################
*/
previewContainerHtml() {
    return `
    <div class="tableWrap">
        <div class="previewTable">
            <div class="previewContainer previewCommon"></div>
            <div class="previewContainer previewCommonFront"></div>
            <div class="previewContainer">
                <div class="previewGroup">
                    <div class="previewGroupHeader previewBodyGroupHeader">
                        <div class="tHeadGroup tHeadTh th"><div class="ci">${getMessage.FTE01067}</div></div>
                    </div>
                    <div class="previewGroupBody previewBodyGroupBody">
                        ${this.previewEmptyHtml()}
                    </div>
                </div>
            </div>
            <div class="previewContainer previewCommonRear"></div>
        </div>
    </div>`;
}
// 共通
previewCommonHtml( type ) {
    const button = '<button class="rowSelectButton button"><span class="inner"></span></button>';
    const icon = '<span class="icon icon-ellipsis_v"></span>';
    const floor = ( type === '2')? 1: 0;
    return `
    ${this.previewColumnHtml('tHeadTh tHeadLeftSticky th', button, button, floor )}
    ${this.previewColumnHtml('tHeadTh tHeadLeftSticky th', icon, icon, floor )}
    ${this.previewColumnHtml('tHeadTh tHeadLeftSticky th', getMessage.FTE01010, 'XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX', floor )}`;
}
// フロントHTML
previewFrontHtml( type ) {
    const operationFlag = ( type === '2')? false: true;
    const hostFlag = ( type === '1')? true: false;
    
    const floor = ( type === '2')? 1: 0;
    const operationBody = `
    ${this.previewColumnHtml('tHeadTh th', getMessage.FTE01068, getMessage.FTE01066, 1 )}
    ${this.previewColumnHtml('tHeadTh th', getMessage.FTE01069, '2020/01/01 00:00', 1 )}
    ${this.previewColumnHtml('tHeadTh th', getMessage.FTE01070, '2020/01/01 00:00', 1 )}
    ${this.previewColumnHtml('tHeadTh th', getMessage.FTE01071, '', 1 )}`;

    return `
    ${( hostFlag )? this.previewColumnHtml('tHeadTh th', getMessage.FTE01065, '192.168.0.1', floor ): ''}
    ${( operationFlag )? this.previewGroupHtml( getMessage.FTE01066, operationBody, floor ): ''}`;
}
// リアHTML
previewRearHtml( type ) {
    const floor = ( type === '2')? 1: 0;
    return `
    ${this.previewColumnHtml('tHeadTh th', '備考', '', floor )}
    ${this.previewColumnHtml('tHeadTh th', '最終更新日時', '2020/01/01 00:00:00', floor )}
    ${this.previewColumnHtml('tHeadTh th', '最終更新者', getMessage.FTE01076, floor )}`;
}
// グループ
previewGroupHtml( title, body ) {
    return `
    <div class="previewGroup">
        <div class="previewGroupHeader">
            <div class="tHeadGroup tHeadTh th"><div class="ci">${title}</div></div>
        </div>
        <div class="previewGroupBody">${body}</div>
    </div>`;
}
// カラム
previewColumnHtml( type, title, contents, floor ) {
    const tbodyType = ( type === 'tHeadTh tHeadLeftSticky th')
        ? 'tBodyLeftSticky tBodyTh th'
        : 'tBodyTd td';
    return `
    <div class="previewColumn">
        <div class="previewColumnHeader" data-floor="${floor}">
            ${this.previewCellHtml( type, title )}
        </div>
        <div class="previewColumnBody">
            ${this.previewCellHtml( tbodyType, contents, 3 )}
        </div>
    </div>`;
}
// セル
previewCellHtml( type, contents, repeat = 1 ) {
    const div = `<div class="${type}"><div class="ci">${contents}</div></div>`;
    const html = [];
    for ( let i = 0; i < repeat; i++ ) {
        html.push( div );
    }
    return html.join('');
}
// グループコンテナ
previewGroupContainerHtml() {
    return `<div class="previewGroupContainer">${this.previewGroupHtml('', '')}</div>`;
}
// カラムコンテナ
previewColumnContainerHtml() {
    return `<div class="previewColumnContainer"></div>`;
}
// empty
previewEmptyHtml() {
    return `<div class="previewEmpty"><div class="previewEmptyInner">Empty</div></div>`;
}
// プレビュータイプ更新
updatePreviewType() {
    let type;
    try {
        if ( this.editorMode === 'view') {
            type = this.menuEditorArray.menu_info.menu.sheet_type_id;
        } else {
            type = this.$.menuType.val();
        }
    } catch( error ) {
        console.error( error );
        type = '2';
    }
    this.$.previewWrap.attr('data-menuGroup', type );
    this.$.previewWrap.find('.previewCommon').html( this.previewCommonHtml( type ) );
    this.$.previewWrap.find('.previewCommonFront').html( this.previewFrontHtml( type ) );
    this.$.previewWrap.find('.previewCommonRear').html( this.previewRearHtml( type ) );
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   パネルHTML
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    パネルメイン
##################################################
*/
panelContainerHtml( editorMode ) {
    const panelType = {
        menuType: '',
        hostType: '',
        verticalMenu: ''
    };
    let html = '';

    if ( editorMode === 'view' ){
        html += `
        <div class="panel-group">
            <div class="panel-group-title">${getMessage.FTE01009}</div>
            <table class="panel-table">
                <tbody>
                    <tr>
                        <th class="panel-th">` + getMessage.FTE01010 + `</th>
                        <td class="panel-td"><span id="create-menu-id" class="panel-span"><span class="editorAutoInput">${getMessage.FTE01011}</span></span></td>
                    </tr>
                </tbody>
            </table>
            <hr class="panel-hr">
            <table class="panel-table">
                <tbody>
                    <tr>
                        <th class="panel-th panel-th-only">` + getMessage.FTE01012 + `</th>
                    </tr>
                    <tr>
                        <td class="panel-td"><span id="create-menu-name" class="panel-span"></span></td>
                    </tr>
                    <tr>
                        <th class="panel-th panel-th-only">` + getMessage.FTE01013 + `</th>
                    </tr>
                    <tr>
                        <td class="panel-td"><span id="create-menu-name-rest" class="panel-span"></span></td>
                    </tr>
                    <tr>
                        <th class="panel-th panel-th-only">` + getMessage.FTE01014 + `</th>
                    </tr>
                    <tr>
                        <td class="panel-td"><span id="create-menu-type" class="panel-span"></span></td>
                    </tr>
                </tbody>
            </table>
            <hr class="panel-hr">
            <table class="panel-table">
                <tbody>
                    <tr>
                        <th class="panel-th">` + getMessage.FTE01015 + `</th>
                        <td class="panel-td"><span id="create-menu-order" class="panel-span"></span></td>
                    </tr>
                    <tr class="parameter-sheet">
                        <th class="panel-th"">` + getMessage.FTE01153 + `</th>
                        <td class="panel-td"><span id="create-menu-use-host-group" class="panel-span"></span></td>
                    </tr>
                    <tr class="parameter-sheet parameter-operation">
                        <th class="panel-th"">` + getMessage.FTE01016 + `</th>
                        <td class="panel-td"><span id="create-menu-use-vertical" class="panel-span"></span></td>
                    </tr>
                    <tr>
                        <th class="panel-th">` + getMessage.FTE01017 + `</th>
                        <td class="panel-td"><span id="create-menu-last-modified" class="panel-span"><span class="editorAutoInput">${getMessage.FTE01011}</span></span></td>
                    </tr>
                    <tr>
                        <th class="panel-th">` + getMessage.FTE01018 + `</th>
                        <td class="panel-td"><span id="create-last-update-user" class="panel-span"><span class="editorAutoInput">${getMessage.FTE01011}</span></span></td>
                    </tr>
                </tbody>
            </table>
            <table class="panel-table">
                <tbody>
                    <tr>
                        <th class="panel-th">${getMessage.FTE01159}</th>
                        <td class="panel-td" colspan="3"><span class="panel-span"><span class="menu-editor-item-counter-number"></span></span></td>
                    </tr>
                </tbody>
            </table>
        </div>
        <div id="menu-group" class="panel-group">
            <div class="panel-group-title">${getMessage.FTE01019}</div>
            <table class="panel-table">
                <tbody>
                    <tr class="data-sheet parameter-sheet parameter-operation">
                        <th class="panel-th">` + getMessage.FTE01020 + `</th>
                        <td class="panel-td"><span id="create-menu-for-input" type="text" class="panel-span"></span></td>
                    </tr>
                    <tr class="parameter-sheet parameter-operation">
                        <th class="panel-th">` + getMessage.FTE01021 + `</th>
                        <td class="panel-td"><span id="create-menu-for-substitution" type="text" class="panel-span"></span></td>
                    </tr>
                    <tr class="parameter-sheet parameter-operation">
                        <th class="panel-th">` + getMessage.FTE01022 + `</th>
                        <td class="panel-td"><span id="create-menu-for-reference" type="text" class="panel-span"></span></td>
                    </tr>
                </tbody>
            </table>
        </div>
        <div id="unique-constraint" class="panel-group">
            <div class="panel-group-title">${getMessage.FTE01023}</div>
            <table class="panel-table">
                <tbody>
                    <tr class="data-sheet parameter-sheet parameter-operation">
                        <th class="panel-th">` + getMessage.FTE01024 + `</th>
                        <td class="panel-td"><span id="unique-constraint-list" type="text" class="panel-span"></span></td>
                    </tr>
                </tbody>
            </table>
        </div>
        <div id="permission-role" class="panel-group">
            <div class="panel-group-title">${getMessage.FTE01025}</div>
            <table class="panel-table">
                <tbody>
                    <tr class="data-sheet parameter-sheet parameter-operation">
                        <th class="panel-th">` + getMessage.FTE01026 + `</th>
                        <td class="panel-td"><span id="permission-role-name-list" type="text" class="panel-span"></span></td>
                    </tr>
                </tbody>
            </table>
        </div>
        <div id="permission-role" class="panel-group">
            <div class="panel-group-title">${getMessage.FTE01027}</div>
            <span id="create-menu-explanation" type="text" class="panel-span"></span>
        </div>
        <div id="permission-role" class="panel-group">
            <div class="panel-group-title">${getMessage.FTE01028}</div>
            <span id="create-menu-note" type="text" class="panel-span"></span>
        </div>`;
    } else if (editorMode === 'edit'){
        panelType.menuType = '1';
        panelType.hostType = '1';
        panelType.verticalMenu = 'false';
        html += `
        <div class="panel-group">
            <div class="panel-group-title">` + getMessage.FTE01009 + `</div>
            <table class="panel-table">
                <tbody>
                    <tr>
                        <th class="panel-th">` + getMessage.FTE01010 + `</th>
                        <td class="panel-td"><span id="create-menu-id" class="panel-span" data-value=""><span class="editorAutoInput">${getMessage.FTE01011}</span></span></td>
                    </tr>
                </tbody>
            </table>
            <hr class="panel-hr">
            <table class="panel-table">
                <tbody>
                    <tr title="` + getMessage.FTE01029 + `">
                        <th class="panel-th panel-th-only">${getMessage.FTE01012 + fn.html.required()}</th>
                    </tr>
                    <tr title="` + getMessage.FTE01029 + `">
                        <td class="panel-td"><input id="create-menu-name" class="panel-text" type="text" autocomplete="off"></td>
                    </tr>
                    <tr title="` + getMessage.FTE01030 + `">
                        <th class="panel-th panel-th-only">${getMessage.FTE01013 + fn.html.required()}</th>
                    </tr>
                    <tr title="` + getMessage.FTE01030 + `">
                        <td class="panel-td"><input id="create-menu-name-rest" class="panel-text" type="text" autocomplete="off"></td>
                    </tr>
                    <tr title="` + getMessage.FTE01031 + `">
                        <th class="panel-th panel-th-only">` + getMessage.FTE01014 + `</th>
                    </tr>
                    <tr title="` + getMessage.FTE01031 + `">
                        <td class="panel-td">
                            <select id="create-menu-type" class="panel-select" disabled>
                            </select>
                        </td>
                    </tr>
                </tbody>
            </table>
            <hr class="panel-hr">
            <table class="panel-table">
                <tbody>
                    <tr title="` + getMessage.FTE01032 + `">
                        <th class="panel-th">${getMessage.FTE01015 + fn.html.required()}</th>
                        <td class="panel-td"><input id="create-menu-order" class="panel-number" type="number" data-min="0" data-max="2147483647" autocomplete="off"></td>
                    </tr>
                </tbody>
            </table>
            <table class="panel-table">
                <tbody>
                    <tr class="parameter-sheet parameter-operation panel-check-tr" title="` + getMessage.FTE01154 + `">
                        <th class="panel-th">${getMessage.FTE01153}</th>
                        <td class="panel-td">
                            ${fn.html.checkboxText('panel-check', getMessage.FTE01034, 'create-menu-use-host-group', 'create-menu-use-host-group', {disabled: 'disabled'})}
                        </td>
                    </tr>
                    <tr class="parameter-sheet parameter-operation panel-check-tr" title="` + getMessage.FTE01033 + `">
                        <th class="panel-th">` + getMessage.FTE01016 + `</th>
                        <td class="panel-td">
                            ${fn.html.checkboxText('panel-check', getMessage.FTE01034, 'create-menu-use-vertical', 'create-menu-use-vertical', {disabled: 'disabled'})}
                        </td>
                    </tr>
                </tbody>
            </table>
            <table class="panel-table">
                <tbody>
                    <tr>
                        <th class="panel-th">` + getMessage.FTE01017 + `</th>
                        <td class="panel-td" colspan="3"><span id="create-menu-last-modified" class="panel-span" data-value=""><span class="editorAutoInput">${getMessage.FTE01011}</span></span></td>
                    </tr>
                    <tr>
                        <th class="panel-th">` + getMessage.FTE01018 + `</th>
                        <td class="panel-td" colspan="3"><span id="create-last-update-user" class="panel-span" data-value=""><span class="editorAutoInput">${getMessage.FTE01011}</span></span></td>
                    </tr>
                </tbody>
            </table>
            <table class="panel-table">
                <tbody>
                    <tr>
                        <th class="panel-th">${getMessage.FTE01159}</th>
                        <td class="panel-td" colspan="3"><span class="panel-span"><span class="menu-editor-item-counter-number"></span></span></td>
                    </tr>
                </tbody>
            </table>
        </div>
        <div id="menu-group" class="panel-group">
            <div class="panel-group-title">${getMessage.FTE01019  + fn.html.required()}</div>
            <table class="panel-table">
                <tbody>
                    <tr class="data-sheet parameter-sheet parameter-operation">
                        <th class="panel-th">${getMessage.FTE01020}</th>
                        <td class="panel-td" colspan="3"><span id="create-menu-for-input" type="text" class="panel-span" data-id="" data-value=""></span></td>
                    </tr>
                    <tr class="parameter-sheet parameter-operation">
                        <th class="panel-th">${getMessage.FTE01021}</th>
                        <td class="panel-td" colspan="3"><span id="create-menu-for-substitution" type="text" class="panel-span" data-id="" data-value=""></span></td>
                    </tr>
                    <tr class="parameter-sheet parameter-operation">
                        <th class="panel-th">${getMessage.FTE01022}</th>
                        <td class="panel-td" colspan="3"><span id="create-menu-for-reference" type="text" class="panel-span" data-id="" data-value=""></span></td>
                    </tr>
                </tbody>
            </table>
            <ul class="panel-button-group">
                <li><button id="create-menu-group-select" class="panel-button">` + getMessage.FTE01035 + `</button></li>
            </ul>
        </div>
        <div id="unique-constraint" class="panel-group">
            <div class="panel-group-title">` + getMessage.FTE01023 + `</div>
            <table class="panel-table">
                <tbody>
                    <tr class="data-sheet parameter-sheet parameter-operation">
                        <th class="panel-th">` + getMessage.FTE01024 + `</th>
                        <td class="panel-td" colspan="3"><span id="unique-constraint-list" type="text" class="panel-span"></span></td>
                    </tr>
                </tbody>
            </table>
            <ul class="panel-button-group">
                <li><button id="unique-constraint-select" class="panel-button">` + getMessage.FTE01036 + `</button></li>
            </ul>
        </div>
        <div id="permission-role" class="panel-group">
            <div class="panel-group-title">` + getMessage.FTE01025 + `</div>
            <table class="panel-table">
                <tbody>
                    <tr class="data-sheet parameter-sheet parameter-operation">
                        <th class="panel-th">` + getMessage.FTE01026 + `</th>
                        <td class="panel-td" colspan="3"><span id="permission-role-name-list" type="text" class="panel-span"></span></td>
                    </tr>
                </tbody>
            </table>
            <ul class="panel-button-group">
                <li><button id="permission-role-select" class="panel-button">` + getMessage.FTE01037 + `</button></li>
            </ul>
        </div>
        <div class="panel-group" title="` + getMessage.FTE01038 + `">
            <div class="panel-group-title">` + getMessage.FTE01027 + `</div>
            ${fn.html.textarea(['panel-note', 'panel-textarea', 'popup'], '', 'create-menu-explanation', null, true )}
        </div>
        <div class="panel-group" title="` + getMessage.FTE01039 + `">
            <div class="panel-group-title">` + getMessage.FTE01028 + `</div>
            ${fn.html.textarea(['panel-note', 'panel-textarea', 'popup'], '', 'create-menu-note', null, true )}
        </div>`;
    } else {
        panelType.menuType = '1';
        panelType.hostType = '1';
        panelType.verticalMenu = 'false';
        html += `
        <div class="panel-group">
            <div class="panel-group-title">` + getMessage.FTE01009 + `</div>
            <table class="panel-table">
                <tbody>
                    <tr>
                        <th class="panel-th">` + getMessage.FTE01010 + `</th>
                        <td class="panel-td" colspan="3"><span id="create-menu-id" class="panel-span" data-value=""><span class="editorAutoInput">${getMessage.FTE01011}</span></span></td>
                    </tr>
                </tbody>
            </table>
            <hr class="panel-hr">
            <table class="panel-table">
                <tbody>
                    <tr title="` + getMessage.FTE01029 + `">
                        <th class="panel-th panel-th-only">${getMessage.FTE01012 + fn.html.required()}</th>
                    </tr>
                    <tr title="` + getMessage.FTE01029 + `">
                        <td class="panel-td" colspan="3"><input id="create-menu-name" class="panel-text" type="text" autocomplete="off"></td>
                    </tr>
                    <tr title="` + getMessage.FTE01030 + `">
                        <th class="panel-th panel-th-only">${getMessage.FTE01013 + fn.html.required()}</th>
                    </tr>
                    <tr title="` + getMessage.FTE01030 + `">
                        <td class="panel-td" colspan="3"><input id="create-menu-name-rest" class="panel-text" type="text" autocomplete="off"></td>
                    </tr>
                    <tr title="` + getMessage.FTE01031 + `">
                        <th class="panel-th panel-th-only">` + getMessage.FTE01014 + `</th>
                    </tr>
                    <tr title="` + getMessage.FTE01031 + `">
                        <td class="panel-td" colspan="3">
                            <select id="create-menu-type" class="panel-select">
                            </select>
                        </td>
                    </tr>
                </tbody>
            </table>
            <hr class="panel-hr">
            <table class="panel-table">
                <tbody>
                    <tr title="` + getMessage.FTE01032 + `">
                        <th class="panel-th">${getMessage.FTE01015 + fn.html.required()}</th>
                        <td class="panel-td"><input id="create-menu-order" class="panel-number" type="number" data-min="0" data-max="2147483647" autocomplete="off"></td>
                    </tr>
                </tbody>
            </table>
            <table class="panel-table">
                <tbody>
                    <tr class="parameter-sheet panel-check-tr" title="` + getMessage.FTE01154 + `">
                        <th class="panel-th">${getMessage.FTE01153}</th>
                        <td class="panel-td">
                            ${fn.html.checkboxText('panel-check', getMessage.FTE01034, 'create-menu-use-host-group', 'create-menu-use-host-group')}
                        </td>
                    </tr>
                    <tr class="parameter-sheet parameter-operation panel-check-tr" title="` + getMessage.FTE01033 + `">
                        <th class="panel-th">` + getMessage.FTE01016 + `</th>
                        <td class="panel-td">
                            ${fn.html.checkboxText('panel-check', getMessage.FTE01034, 'create-menu-use-vertical', 'create-menu-use-vertical')}
                        </td>
                    </tr>
                </tbody>
            </table>
            <table class="panel-table">
                <tbody>
                    <tr>
                        <th class="panel-th">` + getMessage.FTE01017 + `</th>
                        <td class="panel-td" colspan="3"><span id="create-menu-last-modified" class="panel-span" data-value=""><span class="editorAutoInput">${getMessage.FTE01011}</span></span></td>
                    </tr>
                    <tr>
                        <th class="panel-th">` + getMessage.FTE01018 + `</th>
                        <td class="panel-td" colspan="3"><span id="create-last-update-user" class="panel-span" data-value=""><span class="editorAutoInput">${getMessage.FTE01011}</span></span></td>
                    </tr>
                </tbody>
            </table>
            <table class="panel-table">
                <tbody>
                    <tr>
                        <th class="panel-th">${getMessage.FTE01159}</th>
                        <td class="panel-td" colspan="3"><span class="panel-span"><span class="menu-editor-item-counter-number"></span></span></td>
                    </tr>
                </tbody>
            </table>
        </div>
        <div id="menu-group" class="panel-group">
            <div class="panel-group-title">${getMessage.FTE01019 + fn.html.required()}</div>
            <table class="panel-table">
                <tbody>
                    <tr class="data-sheet parameter-sheet parameter-operation">
                        <th class="panel-th">${getMessage.FTE01020}</th>
                        <td class="panel-td" colspan="3"><span id="create-menu-for-input" type="text" class="panel-span" data-id="" data-value=""></span></td>
                    </tr>
                    <tr class="parameter-sheet parameter-operation">
                        <th class="panel-th">${getMessage.FTE01021}</th>
                        <td class="panel-td" colspan="3"><span id="create-menu-for-substitution" type="text" class="panel-span" data-id="" data-value=""></span></td>
                    </tr>
                    <tr class="parameter-sheet parameter-operation">
                        <th class="panel-th">${getMessage.FTE01022}</th>
                        <td class="panel-td" colspan="3"><span id="create-menu-for-reference" type="text" class="panel-span" data-id="" data-value=""></span></td>
                    </tr>
                </tbody>
            </table>
            <ul class="panel-button-group">
                <li><button id="create-menu-group-select" class="panel-button">` + getMessage.FTE01035 + `</button></li>
            </ul>
        </div>
        <div id="unique-constraint" class="panel-group">
            <div class="panel-group-title">` + getMessage.FTE01023 + `</div>
            <table class="panel-table">
                <tbody>
                    <tr class="data-sheet parameter-sheet parameter-operation">
                        <th class="panel-th">` + getMessage.FTE01024 + `</th>
                        <td class="panel-td" colspan="3"><span id="unique-constraint-list" type="text" class="panel-span"></span></td>
                    </tr>
                </tbody>
            </table>
            <ul class="panel-button-group">
                <li><button id="unique-constraint-select" class="panel-button">` + getMessage.FTE01036 + `</button></li>
            </ul>
        </div>
        <div id="permission-role" class="panel-group">
            <div class="panel-group-title">` + getMessage.FTE01025 + `</div>
            <table class="panel-table">
                <tbody>
                    <tr class="data-sheet parameter-sheet parameter-operation">
                        <th class="panel-th">` + getMessage.FTE01026 + `</th>
                        <td class="panel-td" colspan="3"><span id="permission-role-name-list" type="text" class="panel-span"></span></td>
                    </tr>
                </tbody>
            </table>
            <ul class="panel-button-group">
                <li><button id="permission-role-select" class="panel-button">` + getMessage.FTE01037 + `</button></li>
            </ul>
        </div>
        <div class="panel-group" title="` + getMessage.FTE01038 + `">
            <div class="panel-group-title">` + getMessage.FTE01027 + `</div>
            ${fn.html.textarea(['panel-note', 'panel-textarea', 'popup'], '', 'create-menu-explanation', null, true )}
        </div>
        <div class="panel-group" title="` + getMessage.FTE01039 + `">
            <div class="panel-group-title">` + getMessage.FTE01028 + `</div>
            ${fn.html.textarea(['panel-note', 'panel-textarea', 'popup'], '', 'create-menu-note', null, true )}
        </div>`;
    }

    return `
    <div id="panel-container" class="editor-panel">
        <div id="property" data-menu-type="${panelType.menuType}" data-host-type="${panelType.hostType}" data-vertical-menu="${panelType.verticalMenu}" class="editor-block">
            <div class="editor-block-inner">
                <div id="menu-info" class="editor-panel-block">
                    <div class="editor-panel-title">
                        <div class="editor-panel-title-inner">${getMessage.FTE01008}</div>
                    </div>
                    <div class="editor-panel-body">
                        <div class="editor-panel-body-inner">
                            ${html}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>`;
}
/*
##################################################
    作成対象 select
##################################################
*/
panelMenuTypeHtml() {
    const html = [];
    const list = this.menuEditorArray.sheet_type_list;
    const length = list.length;
    const sort = [0,2,1];
    for ( let i = 0; i < length; i++ ) {
        const item = list[sort[i]];
        html.push(`<option value="${item.sheet_type_id}">${item.sheet_type_name}</option>`);
    }
    return html.join('');
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//  select2
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    select2セット
##################################################
*/
setSelect2( $select, optionlist ) {
    return new Promise( ( resolve ) => {
        $.fn.select2.amd.require([
            'select2/data/array',
            'select2/utils'
        ], function( ArrayData, Utils ) {
            function CustomData ( $element, options ) {
                CustomData.__super__.constructor.call( this, $element, options );
            }
            Utils.Extend( CustomData, ArrayData );
            CustomData.prototype.query = function ( params, callback ) {
                let options;
                if ( params.term && params.term !== '') {
                    options = optionlist.optionList.filter(function( item ){
                        return String( item.text ).indexOf( params.term ) !== -1;
                    });
                } else {
                    options = optionlist.optionList;
                }
                // ページネーション
                if ( !('page' in params) ) params.page = 1;
                const pageSize = 50;
                const results = {
                    results: options.slice(( params.page - 1 ) * pageSize, params.page * pageSize ),
                    pagination: {
                        more: ( params.page * pageSize < options.length )
                    }
                };
                callback( results );
            };

            // select2セット
            const select2Option = {
                dropdownAutoWidth: false,
                ajax: {},
                dataAdapter: CustomData,
                data: optionlist.selectedList
            };
            $select.select2( select2Option );
            $select.select2('open');
            resolve();
        });
    });
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   メニュー情報作成
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    JSONデータの作成
##################################################
*/
createJsonData( mode = 'registration') {
    const json = {
        group: {}, column: {}, menu: {}
    };

    // パネル情報
    this.getPanelParameter( json.menu, mode );

    // 最終更新日時
    if ( mode !== 'file' && ( this.editorMode === 'initialize' || this.editorMode === 'edit') ) {
        json.menu.last_update_date_time = this.menuEditorArray.menu_info.menu.last_update_date_time;
    }

    // トップ階層のカラム情報
    json.menu.columns = [];
    this.$.menuTable.children().each( function() {
        json.menu.columns.push( $( this ).attr('id') );
    });

    // Item Order用カウンター
    let itemCount = 0;

    // テーブル情報解析
    const tableAnalysis = ( $parent ) => {
        $parent.children().each( ( index, element ) => {
            const $item = $( element );
            const key = $item.attr('id');
            const data = this.menuMap.get( key );
            if ( data === null ) {
                console.warn(`createJsonData error. ${key} data not found.`);
                return true;
            }

            // 親グループ名
            const parentArray = [];
            $item.parents('.menu-column-group').each( ( index, element ) => {
                const groupKey = $( element ).attr('id');
                const groupData = this.menuMap.get( groupKey );
                const gorupName = ( groupData )? groupData.group_name: '';
                if ( gorupName ) parentArray.unshift( gorupName );
            });
            const parents = ( parentArray.length )? parentArray.join('/'): null;

            // 親グループID
            const parentGroupId = $item.closest('.menu-column-group').attr('data-group-id');

            if ( $item.is('.menu-column') ) {
                // カラム情報
                const column_class_id = data.column_class_id ?? '';
                const column_class = ( column_class_id !== '') ? this.getColumnClassName( column_class_id ): '';
                json.column[key] = {
                    item_name: data.item_name ?? '',
                    item_name_rest: data.item_name_rest ?? '',
                    required: data.required ?? '0',
                    uniqued: data.uniqued ?? '0',
                    column_class: column_class,
                    column_class_id: column_class_id,
                    description: data.description ?? '',
                    remarks: data.remarks ?? '',
                    display_settings: data.display_settings ?? null,
                    column_group: parents,
                    display_order: itemCount++
                };
                // 親グループID
                json.column[key].column_group_id = ( mode === 'file' || parentGroupId === '')? null: parentGroupId;
                // アイテムID
                if ( this.editorMode === 'diversion' || mode === 'file') {
                    json.column[key].create_column_id = null;
                } else {
                    json.column[key].create_column_id = data.create_column_id;
                }
                // アイテム最終更新日時
                if ( mode !== 'file' && ( this.editorMode === 'initialize' || this.editorMode === 'edit' ) ) {
                    if ( data.last_update_date_time ) {
                        json.column[key].last_update_date_time = data.last_update_date_time;
                    }
                }
                // 項目タイプ別
                this.getItemData( data, json.column[key] );
            } else if ( $item.is('.menu-column-group') ) {
                // グループ内項目
                const columns = [];
                $item.children('.menu-column-group-body').children().each( function() {
                    const $groupChildren = $( this )
                    if ( !$groupChildren.is('.column-empty') ) columns.push( $( this ).attr('id') );
                });
                // グループ情報
                json.group[key] = {
                    group_name: data.group_name,
                    columns: columns,
                    parent_full_col_group_name: parents
                };
                // 親グループID
                json.group[key].parent_column_group_id = ( mode === 'file' || parentGroupId === '')? null: parentGroupId;
                // グループID
                if ( this.editorMode === 'diversion' || mode === 'file') {
                    json.group[key].group_id = null;
                } else {
                    json.group[key].group_id = data.group_id;
                }
                // 再帰
                tableAnalysis( $item.children('.menu-column-group-body') );
            }

        });
    };
    tableAnalysis( this.$.menuTable );

    return json;
}
// パネル情報取得
getPanelParameter( menuData, mode = 'registration') {
    // 作成対象
    const $selectMenuType = $('#create-menu-type').find('option:selected');

    // 基本データ
    menuData.menu_create_id = ( mode !== 'file')? $('#create-menu-id').attr('data-value'): null;
    menuData.menu_name = $('#create-menu-name').val();
    menuData.menu_name_rest = $('#create-menu-name-rest').val();
    menuData.display_order = $('#create-menu-order').val();
    menuData.description = $('#create-menu-explanation').val();
    menuData.remarks = $('#create-menu-note').val();
    menuData.sheet_type_id = $selectMenuType.val();
    menuData.sheet_type = $selectMenuType.text();

    // ロール
    const role = this.getRoleListValidID( $('#permission-role-name-list').attr('data-role-id') );
    if ( role === "") {
        menuData.role_list = role;
    } else {
        menuData.role_list = role.split(','); // ロール
    }

    // 一意制約
    const unique = $('#unique-constraint-list').attr('data-unique-list');
    if ( unique ) {
        const uniqueConstraint = [];
        const uniqueList = unique.split(',');
        for ( const uniqueItem of uniqueList ) {
            const columnKeys = uniqueItem.split('-');
            const setList = [];
            for ( const key of columnKeys ) {
                const data = this.menuMap.get( key );
                if ( !data ) continue;
                setList.push( data.item_name_rest );
            }
            uniqueConstraint.push( setList );
        }
        menuData.unique_constraint = uniqueConstraint;
    } else {
        menuData.unique_constraint = null;
    }

    // 作成対象別項目
    const type = $('#create-menu-type').val();
    menuData.sheet_type_id = type;
    if ( type === '1' || type === '3') {
        // パラメータシート
        if ( type === '1' ) {
            // ホストグループ利用有無
            const hostgroup = $('#create-menu-use-host-group').prop('checked');
            if ( hostgroup ) {
                menuData.hostgroup = "1";
            } else {
                menuData.hostgroup = "0";
            }
        } else {
            menuData.hostgroup = null;
        }
        // 縦メニュー利用有無
        const vertical = $('#create-menu-use-vertical').prop('checked');
        if ( vertical ) {
            menuData.vertical = "1";
        } else {
            menuData.vertical = "0";
        }
        // 入力用
        menuData.menu_group_for_input = $('#create-menu-for-input').text();
        menuData.menu_group_for_input_id = $('#create-menu-for-input').attr('data-id');
        // 代入値用
        menuData.menu_group_for_subst = $('#create-menu-for-substitution').text();
        menuData.menu_group_for_subst_id = $('#create-menu-for-substitution').attr('data-id');
        // 参照用
        menuData.menu_group_for_ref = $('#create-menu-for-reference').text();
        menuData.menu_group_for_ref_id = $('#create-menu-for-reference').attr('data-id');
    } else if ( type === '2') {
        // データシート

        // 入力用
        menuData.menu_group_for_input = $('#create-menu-for-input').text();
        menuData.menu_group_for_input_id = $('#create-menu-for-input').attr('data-id');
    }

    // undefined,''をnullに
    for ( const key in menuData ) {
        if ( menuData[key] === undefined || menuData[key] === '') {
            menuData[key] = null;
        }
    }
}
// カンマ区切りロールIDリストからID変換失敗を除いたロールIDを返す
getRoleListValidID( roleListText ) {
    if ( roleListText !== undefined && roleListText !== '' ) {
        const roleList = roleListText.split(',');
        const roleListLength = roleList.length;
        const roleIdList = [];
        for ( let i = 0; i < roleListLength; i++ ) {
            const roleName = this.listIdName('role', roleList[i]);
            if ( roleName !== null ) {
                roleIdList.push( roleList[i] );
            }
        }
        return roleIdList.join(',');
    } else {
        return '';
    }
}
// 項目タイプ別情報の取得
getItemData( data, setData ) {
    switch ( data.column_class_id ) {
        case '1':
            setData.single_string_maximum_bytes = data.single_string_maximum_bytes ?? '';
            setData.single_string_regular_expression = data.single_string_regular_expression ?? '';
            setData.single_string_default_value = data.single_string_default_value ?? '';
            break;
        case '2':
            setData.multi_string_maximum_bytes = data.multi_string_maximum_bytes ?? '';
            setData.multi_string_regular_expression = data.multi_string_regular_expression ?? '';
            setData.multi_string_default_value = data.multi_string_default_value ?? '';
            break;
        case '3':
            setData.integer_minimum_value = data.integer_minimum_value ?? '';
            setData.integer_maximum_value = data.integer_maximum_value ?? '';
            setData.integer_default_value = data.integer_default_value ?? '';
            break;
        case '4':
            setData.decimal_minimum_value = data.decimal_minimum_value ?? '';
            setData.decimal_maximum_value = data.decimal_maximum_value ?? '';
            setData.decimal_digit = data.decimal_digit ?? '';
            setData.decimal_default_value = data.decimal_default_value ?? '';
            break;
        case '5':
            setData.datetime_default_value = data.datetime_default_value ?? '';
            break;
        case '6':
            setData.date_default_value = data.date_default_value ?? '';
            break;
        case '7':
            setData.pulldown_selection_id = data.pulldown_selection_id ?? '';
            setData.pulldown_selection = data.pulldown_selection ?? '';
            setData.pulldown_selection_default_value = data.pulldown_selection_default_value ?? '';
            setData.reference_item = data.reference_item ?? '';
            break;
        case '8':
            setData.password_maximum_bytes = data.password_maximum_bytes ?? '';
            break;
        case '9':
            setData.file_upload_maximum_bytes = data.file_upload_maximum_bytes ?? '';
            break;
        case '10':
            setData.link_maximum_bytes = data.link_maximum_bytes ?? '';
            setData.link_default_value = data.link_default_value ?? '';
            break;
        case '11':
            setData.parameter_sheet_reference_id = data.parameter_sheet_reference_id ?? '';
            setData.parameter_sheet_reference = data.parameter_sheet_reference ?? '';
            break;
        default:
    }
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//  メニュー登録
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    登録
##################################################
*/
registrationMenu( type ) {
    // 必須・初期値なし・画面からの編集禁止の項目があれば警告し、無視した場合は登録する
    return this.disableEditRequiredConfirm().then( ( flag ) => {
        if ( !flag ) return Promise.reject();
        return this.registrationMenuExecute( type );
    });
}
// 必須・初期値なし・画面からの編集禁止の項目チェック
disableEditRequiredConfirm() {
    const defaultValueKeys = {
        '1': 'single_string_default_value',
        '2': 'multi_string_default_value',
        '3': 'integer_default_value',
        '4': 'decimal_default_value',
        '5': 'datetime_default_value',
        '6': 'date_default_value',
        '7': 'pulldown_selection_default_value',
        '10': 'link_default_value'
    };
    const columns = this.createJsonData().column;
    const itemNames = [];
    for ( const key in columns ) {
        const column = columns[ key ];
        const displaySettings = ( fn.typeof( column.display_settings ) === 'object')? column.display_settings: {};
        if ( column.required !== '1' || displaySettings.disable_edit !== true ) continue;

        // 初期値が無い項目タイプ（パスワード、ファイルアップロード等）は常に対象
        const defaultValueKey = defaultValueKeys[ column.column_class_id ];
        const defaultValue = ( defaultValueKey )? column[ defaultValueKey ]: null;
        if ( defaultValue === undefined || defaultValue === null || defaultValue === '') {
            const groupName = ( column.column_group )? column.column_group + '/': '';
            itemNames.push( '・' + groupName + column.item_name );
        }
    }
    if ( !itemNames.length ) return Promise.resolve( true );

    return fn.iconConfirm('circle_exclamation', getMessage.FTE10059, getMessage.FTE01172 + '\n\n' + itemNames.join('\n') + '\n\n' + getMessage.FTE01173 );
}
// 登録実行
registrationMenuExecute( type ) {
    return new Promise( ( resolve, reject ) => {
        // 登録データ
        const registrationData = this.createJsonData();
        registrationData.type = type;

        // 進行中モーダル
        let process = fn.processingModal('');

        fn.fetch('/create/define/execute/', null, 'POST', registrationData ).then( (result) => {
            let id  = result['history_id'];
            let string = getMessage.FTE01140;
            let log = string + id;
            this.log.set( 'done', log );

            fn.alert('', fn.escape( log, true ) ).then(function(){
                let url_path = location.pathname,
                    splitstr = url_path.split('/'),
                    organization_id = splitstr[1],
                    workspace_id = splitstr[3],
                    menu_name_rest = result['menu_name_rest'],
                    menu = fn.getParams().menu;
                process.close();
                process = null;
                resolve();

                window.location.href = '/' + organization_id + '/workspaces/' + workspace_id + '/ita/?menu=' + menu + '&menu_name_rest=' + menu_name_rest + '&history_id=' + id;
            });
        }).catch( ( error ) => {
            if ( fn.typeof( error ) === 'object') {
                if ( error.result === '498-00004') {
                    if ( fn.typeof( error.message ) === 'string') window.alert( error.message );
                } else {
                    let message = this.errorFormat(error.message);
                    this.log.clear();
                    this.log.set('error', message );
                    window.alert(getMessage.FTE01141);
                }
            }
            process.close();
            process = null;
            reject();
        });
    });
}
// 登録エラー
errorFormat( error ) {
    let errorMessage;
    let message;
    let keyVal;
    let val;
    let errMessage = "";

    const errorRow = function( m ){
        return `<div class="error-log-row">${fn.escape(m)}</div>`
    };

    try {
        errorMessage = JSON.parse(error);
        for ( const key in errorMessage ) {
            message = errorMessage[key];
            if ( key === '__line__'){
                val = errorRow( message );
                errMessage = errMessage + val;
            } else {
                if (key in this.nameConvertList) {
                    keyVal = errorRow( this.nameConvertList[key] + ':' + message );
                    errMessage = errMessage + keyVal;
                } else {
                    keyVal = errorRow( key + ':' + message );
                    errMessage = errMessage + keyVal;
                }
            }
        }
    } catch ( e ) {
        errMessage = errorRow( error );
    }
    return errMessage;
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//  ログタブ
//
////////////////////////////////////////////////////////////////////////////////////////////////////
menuEditorLogNumber = 1;
log = {
    set: ( type, content ) => {
        $('.editor-tab-menu-item[data-tab="menu-editor-log"]').click();
        if ( type === undefined || type === '' ) type = 'log';

        const $menuEditorLog = $('.editor-log');
        const $menuEditorLogTable = $menuEditorLog.find('tbody');
        const logClass = ( type !== 'log')? ' editor-log-content-level': '';
        let logRowHTML = ''
            + '<tr class="editor-log-row ' + type + '">'
            + '<th class="editor-log-number">' + ( this.menuEditorLogNumber++ ) +'</th><td class="editor-log-content"><div class="editor-log-content-inner' + logClass + '">';
        if ( type !== 'log') logRowHTML += '<span class="logLevel">' + fn.escape( type.toLocaleUpperCase() ) + '</span>';
        logRowHTML += content + '</div></td></tr>';

        $menuEditorLogTable.append( logRowHTML );

        // 一番下までスクロール
        const scrollTop = $menuEditorLog.get(0).scrollHeight - $menuEditorLog.get(0).clientHeight;
        $menuEditorLog.animate({ scrollTop : scrollTop }, 200 );
    },
    clear: () => {
        $('.editor-log').find('tbody').empty();
    }
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   再表示
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    エディタ欄セット
##################################################
*/
async setMenu( setMode ) {
    this.$.editor.addClass('load-wait');

    // メニューデータ
    const menuInfo = fn.arrayCopy( this.menuEditorArray.menu_info );

    // データ初期化
    this.menuMap = new Map();
    this.displaySettingOpenIds = new Set();
    this.pulldownSelectionDefaultValue = {};
    this.menuIdList = [];
    this.floor = [];
    this.columnCounter = 1;
    this.groupCounter = 1;

    // JSON読込時に読み込まない項目
    if ( setMode === 'jsonRead') {
        menuInfo.menu.menu_create_id = null;
        menuInfo.menu.last_update_date_time = null;
        menuInfo.menu.last_updated_user = null;
        menuInfo.menu.menu_create_done_status_id = null;
    }

    // 流用新規時に引き継がない項目
    if ( this.editorMode === 'diversion' ){
        menuInfo.menu.menu_create_id = null;
        menuInfo.menu.menu_name = null;
        menuInfo.menu.menu_name_rest = null;
        menuInfo.menu.display_order = null;
        menuInfo.menu.last_update_date_time = null;
        menuInfo.menu.description = null;
        menuInfo.menu.remarks = null;
    }

    // エディタ欄セット
    const fragment = document.createDocumentFragment();
    const previewFlagment = document.createDocumentFragment();
    const setMenuTable = async ( items, container, previewContainer, floor ) => {
        if ( !items ) return;
        for ( const id of items ) {
            const type = id.slice( 0, 1 );
            // IDが重複していないかチェック
            if ( this.menuIdList.includes( id) ) throw new Error( getMessage.FTE01155(id) );
            this.menuIdList.push( id );
            if ( type === 'g') {
                const groupData = menuInfo.group[ id ]
                if ( !groupData ) throw new Error( getMessage.FTE01156(id) );
                this.groupCounter++;
                const group = this.getFlagment('commonGroupContainerHtml');
                const element = group.firstElementChild;
                element.setAttribute('id', id );
                // グループID
                if ( setMode === 'jsonRead') groupData.group_id = null;
                const groupId = groupData.group_id ?? '';
                element.setAttribute('data-group-id', groupId );
                // グループ名互換
                const groupName = groupData.column_group_name
                    ?? groupData.col_group_name
                    ?? groupData.group_name
                    ?? '';
                groupData.group_name = groupName;
                
                this.menuMap.set( id, groupData );
                container.appendChild( group );

                // プレビュー
                const preview = this.getFlagment('previewGroupContainerHtml');
                const previewElement = preview.firstElementChild;
                previewElement.setAttribute('data-id', id );
                previewContainer.appendChild( preview );

                // 再帰
                if ( groupData.columns && groupData.columns.length ) {
                    await setMenuTable(
                        groupData.columns,
                        element.querySelector('.menu-column-group-body'),
                        previewElement.querySelector('.previewGroupBody'),
                        floor + 1
                    );
                }
            } else if ( type === 'c') {
                const column = this.getFlagment('commonColumnContainerHtml');
                const element = column.firstElementChild;
                element.setAttribute('id', id );
                const columnData = menuInfo.column[ id ];
                this.columnCounter++;
                // 階層
                columnData.floor = floor;
                if ( !this.floor[ floor ] ) this.floor[ floor ] = 0;
                this.floor[ floor ]++;
                // カラムID
                if ( setMode === 'jsonRead') columnData.create_column_id = null;
                const columnId = columnData.create_column_id ?? '';
                element.setAttribute('data-item-id', columnId );
                // プルダウン選択初期値リスト
                if ( columnData.column_class_id === '7') {
                    const selectionId = columnData.pulldown_selection_id ?? null;
                    if ( selectionId !== null ) {
                        await this.itemGetPulldownSelectionDefaultValueList( selectionId );
                    }
                }
                // 整数・少数の最小値・最大値・初期値・桁数が数値で返ってくるので文字列に変換する
                if ( columnData.column_class_id === '3' || columnData.column_class_id === '4') {
                    const numToStringTargetKeys = [
                        'integer_default_value',
                        'integer_maximum_value',
                        'integer_minimum_value',
                        'decimal_default_value',
                        'decimal_maximum_value',
                        'decimal_minimum_value',
                        'decimal_digit'
                    ];
                    for ( const targetKey of numToStringTargetKeys ) {
                        if ( typeof columnData[ targetKey ] === 'number') {
                            columnData[ targetKey ] = String( columnData[ targetKey ] );
                        }
                    }
                }

                this.menuMap.set( id, columnData );
                container.appendChild( column );

                // 画面表示設定が設定済みなら開いた状態にする
                if ( this.hasDisplaySetting( columnData ) ) this.displaySettingOpenIds.add( id );

                // プレビュー
                const preview = this.getFlagment('previewColumnContainerHtml');
                const previewElement = preview.firstElementChild;
                previewElement.setAttribute('data-id', id );
                previewContainer.appendChild( preview );
            }
        }
    };
    await setMenuTable( menuInfo.menu.columns, fragment, previewFlagment, 0 );

    // HTMLセット
    this.$.menuTable.empty().hide();
    this.$.menuTable.get(0).appendChild( fragment );
    this.$.previewTable.empty().hide();
    this.$.previewTable.get(0).appendChild( previewFlagment );

    // パネル情報表示
    this.setPanelParameter( menuInfo );
    this.updatePreviewType();
    this.setColumnHeaderStyle();

    this.history.clear();

    // 交差監視
    await this.setMenuObserve();

    this.$.menuTable.show();
    this.$.previewTable.show();
    this.$.editor.removeClass('load-wait');

    this.updateCounter();

    return;
}
// 交差監視
async setMenuObserve() {
    const items = this.$.menuTable.get(0).querySelectorAll('.menu-column, .menu-column-group');
    await this.observeIdle( items, this.itemIO );

    const previewItems = this.$.previewTable.get(0).querySelectorAll('.previewColumnContainer, .previewGroupContainer');
    await this.observeIdle( previewItems, this.previewIO );

    return;
}
// 監視付与処理を分割する
observeIdle( list, io, chunkSize = 100 ) {
    return new Promise( resolve => {
        let index = 0;
        function work( deadline ) {
            let count = 0;
            while (
                index < list.length &&
                count < chunkSize &&
                deadline.timeRemaining() > 0
            ) {
                io.observe( list[ index++ ] );
                count++;
            }

            if ( index < list.length ) {
                requestIdleCallback( work );
            } else {
                resolve();
            }
        }
        requestIdleCallback( work );
    });
}
/*
##################################################
    パネル情報セット
##################################################
*/
setPanelParameter( setData ) {
    const menu = setData.menu;
    // nullを空白に
    for ( const key in setData.menu ) {
        if ( menu[ key ] === null ) menu[ key ] = '';
    }
    // パネルに値をセットする
    const type = menu.sheet_type_id;
    this.$.property.attr('data-menu-type', type );

    if ( this.editorMode !== 'diversion'){
        // 項番
        if ( menu.menu_create_id ) {
            $('#create-menu-id')
                .attr('data-value', menu.menu_create_id )
                .text( menu.menu_create_id );
        }
        // 最終更新日時
        if ( menu.last_update_date_time ) {
            const date = menu.last_update_date_time;
            const last_update_date_time = fn.date( date, 'yyyy-MM-dd HH:mm:ss');
            $('#create-menu-last-modified')
                .attr('data-value', last_update_date_time )
                .text( last_update_date_time );
        }
        // 最終更新者
        if ( menu.last_updated_user ) {
            $('#create-last-update-user')
                .attr('data-value', menu.last_updated_user )
                .text( menu.last_updated_user );
        }
    }
    
    // ロール
    let roleList = [];
    if ( menu.selected_role_id !== undefined ) roleList = menu.selected_role_id;
    if ( menu.role_list !== undefined ) roleList = menu.role_list;
    if ( fn.typeof( roleList ) !== 'array') roleList = [];
    $('#permission-role-name-list')
        .attr('data-role-id', roleList )
        .text( this.getRoleListIdToName( roleList ) );

    // 一意制約(複数項目)
    let unique_constraint = [];
    if ( menu.unique_constraint !== undefined ) unique_constraint = menu.unique_constraint;
    if ( fn.typeof( unique_constraint ) !== 'array') unique_constraint = [];

    // column key : item_name_rest（["a","b"]を[{c1:"a"},{c2:"b"}]）の形式に変換
    const allUniqueList = [];
    for ( const uniqueData of unique_constraint ) {
        const uniqueList = [];
        for ( const itemNameRest of uniqueData ) {
            for ( const [ itemKey, obj ] of this.menuMap ) {
                if ( obj.item_name_rest === itemNameRest ) {
                    uniqueList.push({
                        [ itemKey ]: itemNameRest
                    });
                }
            }
        }
        allUniqueList.push( uniqueList );
    }
    this.panelSetUniqueConstraint( allUniqueList );

    // エディットモード別
    let dispOrder = '';
    if ( menu.disp_seq !== undefined ) dispOrder = menu.disp_seq;
    if ( menu.display_order !== undefined ) dispOrder = menu.display_order;

    if ( this.editorMode === 'view') {
        $('#create-menu-name').text( menu.menu_name ); // メニュー名
        $('#create-menu-name-rest').text( menu.menu_name_rest ); // メニュー名(REST)
        $('#create-menu-type').text( this.listIdName('target', menu.sheet_type_id )); // 作成対象
        $('#create-menu-order').text( dispOrder ); // 表示順序
        $('#create-menu-explanation').text( menu.description );  // 説明
        $('#create-menu-note').text( menu.remarks ); // 備考
    } else {
        $('#create-menu-name').val( menu.menu_name ); // メニュー名
        $('#create-menu-name-rest').val( menu.menu_name_rest ); // メニュー名(REST)
        $('#create-menu-type').val( menu.sheet_type_id ); // 作成対象
        $('#create-menu-order').val( dispOrder ); // 表示順序
        $('#create-menu-explanation').val( menu.description );  // 説明
        $('#create-menu-note').val( menu.remarks ); // 備考
    }

    // 作成対象項目別
    if ( type === '1' || type === '3') {
        // パラメータシート
        if ( type === '1') {
            // ホストグループ利用有無
            if ( menu.hostgroup === '1' || menu.hostgroup === 'True' || menu.hostgroup === true ) {
                if ( this.editorMode === 'view') {
                    $('#create-menu-use-host-group').text( getMessage.FTE01085 );
                } else {
                    $('#create-menu-use-host-group').prop('checked', true );
                }
            }
        }
        // 縦メニュー利用有無
        if ( menu.vertical === '1' || menu.vertical === 'True' || menu.vertical === true ) {
            if ( this.editorMode === 'view') {
                $('#create-menu-use-vertical').text( getMessage.FTE01085 );
            } else {
                $('#create-menu-use-vertical').prop('checked', true );
            }
        }
        // 入力用
        const $forInput = $('#create-menu-for-input');
        const forInputId = menu.menu_group_for_input_id;
        const forInputText = this.listIdName('group', forInputId );
        if ( forInputText ) {
            $forInput.attr('data-id', forInputId ).text( forInputText );
        } else {
            $forInput.attr('data-id', '').text('');
        }
        // 代入値自動登録用
        const $forSubstitution = $('#create-menu-for-substitution');
        const forSubstitutionId = menu.menu_group_for_subst_id;
        const forSubstitutionText = this.listIdName('group', forSubstitutionId );
        if ( forSubstitutionText ) {
            $forSubstitution.attr('data-id', forSubstitutionId ).text( forSubstitutionText );
        } else {
            $forSubstitution.attr('data-id', '').text('');
        }
        // 参照用
        const $forReference = $('#create-menu-for-reference');
        const forReferenceId = menu.menu_group_for_ref_id;
        const forReferenceText = this.listIdName('group', forReferenceId );
        if ( forReferenceText ) {
            $forReference.attr('data-id', forReferenceId ).text( forReferenceText );
        } else {
            $forReference.attr('data-id', '').text('');
        }
    } else if ( type === '2') {
        // データシート
        // 入力用
        const $forInput = $('#create-menu-for-input');
        const forInputId = menu.menu_group_for_input_id;
        const forInputText = this.listIdName('group', forInputId );
        if ( forInputText ) {
            $forInput.attr('data-id', forInputId ).text( forInputText );
        } else {
            $forInput.attr('data-id', '').text('');
        }
    }

    //「メニュー作成状態」が2(作成済み)の場合は、メニュー名(REST)入力欄を非活性にする。
    if ( this.editorMode !== 'diversion') {
        if ( menu.menu_create_done_status_id == 2 ){
            $('#create-menu-name-rest').prop('disabled', true);
        }
    }

    //「メニュー作成状態」が1（未作成）の場合に各種ボタンを操作
    if( menu.menu_create_done_status_id == 1 ){
        //「編集」ボタンを削除
        this.$.editor.find('[data-type="edit"]').closest('.operationMenuItem').remove();
        const buttonText = ( this.editorMode === 'view')? getMessage.FTE01151: getMessage.FTE01090;

        //「初期化」「作成(初期化)」ボタンを「作成」に名称変更
        const $initialize = this.$.editor.find('[data-type="initialize"], [data-type="update-initialize"]');
        $initialize.attr({
            'data-action': 'positive',
            'title': buttonText
        }).find('.iconButtonBody').text( buttonText )
            .closest('.operationMenuItem').removeClass('operationMenuSeparate');
        $initialize.find('.icon-clear').removeClass('icon-clear').addClass('icon-plus');
    }

    if ( menu.number_item ) {
        this.columnCounter = menu.number_item + 1;
    } else {
        const columnCount = this.$.menuTable.find('.menu-column').length;
        this.columnCounter = columnCount + 1;
    }
    if ( menu.number_group ) {
        this.groupCounter = menu.number_group + 1;
    } else {
        const groupCount = this.$.menuTable.find('.menu-column-group').length;
        this.groupCounter = groupCount + 1;
    }
}
// カンマ区切りロールIDリストからロールNAMEリストを返す
getRoleListIdToName( roleListText ) {
    if ( roleListText !== undefined && roleListText !== '') {
        const roleList = roleListText;
        const roleListLength = roleList.length;
        const roleNameList = new Array;

        for ( let i = 0; i < roleListLength; i++ ) {
            const roleName = roleList[i];
            if ( roleName !== null ) {
                const hideRoleName = "********";
                if ( roleName !== hideRoleName ) {
                    roleNameList.push( roleName );
                } else {
                    roleNameList.push( roleName + '(' + roleList[i] + ')');
                }
            } else {
                roleNameList.push( getMessage.FTE01133 + '(' + roleList[i] + ')');
            }
        }
        return roleNameList.join(', ');
    } else {
        return '';
    }
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//  取り消し・やり直し
//
////////////////////////////////////////////////////////////////////////////////////////////////////
initUndoRedo() {
    this.maxHistory = 50;
    this.$.undoButton = $('#button-undo');
    this.$.redoButton = $('#button-redo');
}
history = {
    add: () => {
        this.workCounter++;
        const $editor = this.$.menuTable.clone();
        $editor.find('.menu-column, .menu-column-group-header').empty();
        const $preview = this.$.previewTable.clone();
        $preview.find('.previewColumnContainer, .previewGroupHeader .ci').empty();

        this.workHistory[ this.workCounter ] = {
            editor: $editor.html(),
            preview: $preview.html(),
            map: this.cloneState( this.menuMap )
        }

        // 履歴追加後の履歴を削除する
        if ( this.workHistory[ this.workCounter + 1 ] !== undefined ) {
            this.workHistory.length = this.workCounter + 1;
        }

        // 最大履歴数を超えた場合最初の履歴を削除する
        if ( this.workHistory.length > this.maxHistroy ) {
            this.workHistory.shift();
            this.workCounter--;
        }
        
        this.historyButtonCheck();
    },
    undo: () => {
        this.workCounter--;
        this.setHistory();
    },
    redo: () => {
        this.workCounter++;
        this.setHistory();
    },
    clear: () => {
        this.workCounter = -1;
        this.workHistory = [];
        this.history.add();
        this.historyButtonCheck();
    },
}
// 履歴セット
setHistory() {
    const history = this.workHistory[ this.workCounter ];
    this.menuMap = this.cloneState( history.map );
    this.$.menuTable.html( history.editor );
    this.$.previewTable.html( history.preview );
    this.setMenuObserve();
    this.historyButtonCheck();
    this.updateCounter();
}
// 状態コピー
cloneState( menuMap ) {
    const cloned = new Map();
    for ( const [ key, value ] of menuMap ) {
        cloned.set( key, structuredClone( value ));
    }
    return cloned;
}
// 履歴ボタンチェック
historyButtonCheck() {
    if ( this.workHistory[ this.workCounter - 1 ] !== undefined ) {
        this.$.undoButton.prop('disabled', false );
    } else {
        this.$.undoButton.prop('disabled', true );
    }
    if ( this.workHistory[ this.workCounter + 1 ] !== undefined ) {
        this.$.redoButton.prop('disabled', false );
    } else {
        this.$.redoButton.prop('disabled', true );
    }
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

}