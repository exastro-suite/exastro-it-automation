// JavaScript Document

export class WidgetMenuGroup extends WidgetCommon {
/*
##################################################
   Widget
##################################################
*/
widget() {
    const wg = this;
    
    wg.$.widget = $( wg.widgetHtml() );
    wg.$.widget.find('.widget-body').html( wg.body() );
    
    return wg.$.widget;
}
/*
##################################################
   Body
##################################################
*/
body() {
    const wg = this;
    
    const list = [];
    
    const menuGroups = wg.createMenuGroupList( wg.infoData );
    for ( const menuGroup of menuGroups ) {
        // ポジション情報がない場合はw0に変更する
        if ( menuGroup.position === '' ) menuGroup.position = 'w0';
        
        if ( menuGroup.position === wg.id && menuGroup.parent_id === null && menuGroup.menus.length && menuGroup.main_menu_rest ) {
              const menuNameRest = menuGroup.main_menu_rest,
                    menuGroupId = menuGroup.id,
                    icon = ( menuGroup.icon )? `data:;base64,${menuGroup.icon}`: `/_/ita/imgs/icon_default.png`;

              const link = ``
              + `<div class="db-menu-group-link-inner">`
                  + `<div class="db-menu-group-item-image"><img src="${icon}"></div>`
                  + `<div class="db-menu-group-item-name">${fn.cv( menuGroup.menu_group_name, '', true )}</div>`
              + `</div>`;

              const html = ``
              + `<li class="db-menu-group-item" style="width:calc(100%/${wg.data.menu_number})" data-menu-id="${menuGroupId}">`
                  + wg.linkHtml('db-menu-group-link', `?menu=${menuNameRest}`, link, wg.data.page_move );
              + `</li>`;
              list.push( html );
          }
    }
    return `<div class="db-menu-group"><ul class="db-menu-group-list">${list.join('')}</ul></div>`;    
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
   メニューデ階層データの作成
##################################################
*/
createMenuGroupList( infoData ) {
    const wg = this;

    // メニューグループリストの作成
    const menuGroupList = [],
          childs = [];

    // 配列のディープコピー
    const tempMenuGroups = $.extend( true, [], infoData );

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
                    wg.dispSeqSort( child.menus );
                    if ( child.menus[0].menu_name_rest ) {
                         child.main_menu_rest = child.menus[0].menu_name_rest;
                    }
                }
                parent.menus.push( child );
            }
        }
        wg.dispSeqSort( parent.menus );

        parent.main_menu_rest = null;
        let subRest = null;
        for ( const menu of parent.menus ) {
            if ( menu.menu_name_rest && parent.main_menu_rest === null ) {
                parent.main_menu_rest = menu.menu_name_rest;
            } else if ( menu.menus && menu.menus.length && menu.menus[0].menu_name_rest && subRest === null  ) {
                subRest = menu.menus[0].menu_name_rest;
            }
        }
        if ( !parent.main_menu_rest && subRest ) parent.main_menu_rest = subRest;
    }
    wg.dispSeqSort( menuGroupList );

    return menuGroupList;
}

}