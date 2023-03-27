// JavaScript Document

export class WidgetLinkList extends WidgetCommon {
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
    
    const html = [];
    if ( fn.typeof( wg.data.link_list ) === 'array' && wg.data.link_list.length) {
        for ( const item of wg.data.link_list ) {
            const url = encodeURI( item.url ),
                text = fn.cv( item.name, '', true );
            html.push(``
            + `<li class="db-linklist-item" style="width:calc(100%/${fn.cv( wg.data.menu_number, 1 )});">`
                + wg.linkHtml('db-linklist-link', url, text, wg.data.page_move )
            + `</li>`);
        }
    }
    
    return `<div class="db-linklist-list-warp"><ul class="db-linklist-list">${html.join('')}</ul></div>`;
}

}