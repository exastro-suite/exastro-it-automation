// JavaScript Document

export class WidgetImage extends WidgetCommon {
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
    const wg = this,
          imageHtml = `<img class="db-image" src="${fn.cv( wg.data.image_url, '', true )}">`;
    
    if ( wg.data.link_url !== '') {
        const url = encodeURI( wg.data.link_url );
        return wg.linkHtml('db-image-link', url, imageHtml, wg.data.page_move );
    } else {
        return imageHtml;
    }
}

}