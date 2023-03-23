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
    
    wg.dispSeqSort( wg.infoData );
    for ( const menuGroup of wg.infoData ) {
        // ポジション情報がない場合はw0に変更する
        if ( menuGroup.position === '' ) menuGroup.position = 'w0';
        
        if ( menuGroup.position === wg.id ) {
            if ( menuGroup.parent_id === null ) {
                if ( menuGroup.menus.length ) wg.dispSeqSort( menuGroup.menus );

                if ( menuGroup.menus[0].menu_name_rest ) {
                    const menuNameRest = menuGroup.menus[0].menu_name_rest,
                          menuGroupId = menuGroup.id,
                          icon = ( menuGroup.icon )? `data:;base64,${menuGroup.icon}`: `/_/ita/imgs/icon_default.png`;
                    
                    const link = ``
                    + `<div class="db-menu-group-link-inner">`
                        + `<div class="db-menu-group-item-image"><img src="${icon}"></div>`
                        + `<div class="db-menu-group-item-name">${fn.cv( menuGroup.menu_group_name, '', true )}</div>`
                    + `</div>`;
                    
                    const html = ``
                    + `<li class="db-menu-group-item" style="width:calc(100%/${wg.data.menu_number})" data-menu-id="${menuGroupId}">`
                        + wg.linkHtml('db-menu-group-link', `?menu=${menuNameRest}`, link, wg.data.page_move, { html: true });
                    + `</li>`;
                    list.push( html );
                }
            }
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

}