// JavaScript Document

export class WidgetReserveList extends WidgetCommon {
/*
##################################################
   Widget
##################################################
*/
widget() {
    const wg = this;
    
    wg.$.widget = $( wg.widgetHtml( getMessage.FTE08081( wg.data.period ) ) );
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
    
    wg.stopCountDown();
    
    let tableHTML = '';
    
    const dataSet = {
        conductor: {
            name: 'conductor_name',
            menu: 'conductor_confirmation',
            rest: 'conductor_instance_id'
        }
    };
    
    const today = new Date();
    for ( const type in wg.infoData ) {
        tableHTML += `<div class="db-reserve"><div class="db-reserve-inner">`;
        
        const tableArray = [];
        for ( const reserve of wg.infoData[ type ] ) {
            for ( const id in reserve ) {
                const date = new Date( reserve[id].time_book ),
                      diff = ( date - today ) / 86400000;
                if ( wg.data.period >= diff ) {
                    const link = `?menu=${dataSet[ type ].menu}&${dataSet[ type ].rest}=${id}`;
                    tableArray.push({
                        id: id,
                        name: reserve[id][ dataSet[ type ].name ],
                        operation_name: reserve[id].operation_name,
                        status: reserve[id].status,
                        time_book: reserve[id].time_book,
                        link: link
                    });
                }
            }
        }
        
        if ( tableArray.length > 0 ) {
            tableArray.sort(function( a, b ){
                if ( a.time_book > b.time_book ) {
                    return 1;          
                } else if ( a.time_book < b.time_book ) {
                    return -1;
                } else {
                    return 0;
                }
            });

            // header
            tableHTML += ``
            + `<table class="db-reserve-table db-table">`
                + `<thead class="db-reserve-thead">`
                    + `<tr class="db-reserve-tr db-tr">`
                        + `<th class="db-reserve-th db-cell db-cell-text tHeadTh"><div class="db-cell-i">${getMessage.FTE08059}</div></th>`
                        + `<th class="db-reserve-th db-cell db-cell-text tHeadTh"><div class="db-cell-i">${getMessage.FTE08033}</div></th>`
                        + `<th class="db-reserve-th db-cell tHeadTh db-cell-min"><div class="db-cell-i">${getMessage.FTE08034}</div></th>`
                        + `<th class="db-reserve-th db-cell tHeadTh db-cell-min"><div class="db-cell-i">${getMessage.FTE08035}</div></th>`
                        + `<th class="db-reserve-th db-cell tHeadTh db-cell-min"><div class="db-cell-i">${getMessage.FTE08036}</div></th>`
                    + `</tr>`
                + `</thead>`
                + `<tbody>`;
            
            for ( const item of tableArray ) {
                const date = fn.date( item.time_book, 'yyyy/MM/dd HH:mm').replace(' ', '<br>');
                tableHTML += ``
                + `<tr class="db-reserve-tr db-tr">`
                    + `<td class="db-reserve-td db-cell"><div class="db-cell-i">`
                        + wg.linkHtml('db-reserve-link db-cell-l', item.link, fn.cv( item.name, '', true ), wg.data.page_move )
                    + `</div></td>`
                    + `<td class="db-reserve-td db-cell"><div class="db-cell-i">${fn.cv( item.operation_name, '', true )}</div></td>`
                    + `<td class="db-reserve-td db-cell db-cell-min"><div class="db-cell-i">`
                        + `<div class="db-reserve-status"><span class="db-reserve-status-icon"></span>${fn.cv( item.status, '', true )}</div>`
                    + `</div></td>`
                    + `<td class="db-reserve-td db-cell db-cell-min"><div class="db-cell-i">${date}</div></td>`
                    + `<td class="db-reserve-td db-cell db-cell-min"><div class="db-cell-i">`
                        + `<div class="db-reserve-count-down" data-date="${item.time_book}"></div>`
                    + `</div></td>`
                + `</tr>`;
            }
            tableHTML += `</tbody></table>`;
        } else {
            tableHTML += `<div class="db-reserve-message">${getMessage.FTE08087( wg.data.period )}</div>`;
        }
        
        tableHTML += `</div></div>`;
    }
    
    return tableHTML;
}
/*
##################################################
   Ready
##################################################
*/
ready() {
    const wg = this;
  
    wg.countDown();
}
/*
##################################################
   カウントダウン
##################################################
*/
countDown() {
    const wg = this;
    
    const countDown = function() {
        const today = new Date();
        wg.$.widget.find('.db-reserve-count-down').each(function(){
            const $date = $( this ),
                  date = new Date( $date.attr('data-date') ),
                  diff = date - today;

            const day = ( diff >= 0 )? Math.floor( diff / (24 * 60 * 60 * 1000) ): 0,
                  hour = ( diff >= 0 )? Math.floor(( diff % (24 * 60 * 60 * 1000)) / (60 * 60 * 1000)): 0,
                  min = ( diff >= 0 )? Math.floor(( diff % (24 * 60 * 60 * 1000)) / (60 * 1000)) % 60: 0;

            const html = ``
            + `<span class="db-reserve-cd">${fn.zeroPadding( day, 3, true )}</span>${getMessage.FTE08037}`
            + `<span class="db-reserve-cd">${fn.zeroPadding( hour, 2, true )}</span>${getMessage.FTE08038}`
            + `<span class="db-reserve-cd">${fn.zeroPadding( min, 2, true )}</span>${getMessage.FTE08039}`;

            if ( diff <= 0 ) {
                $date.addClass('running').removeClass('shortly');
            } else if ( day == 0 ) {
                $date.addClass('shortly');
            }

            $date.html( html );
        });
    };
    
    wg.widgetTimerId = setInterval( countDown, 60000 );
    countDown();
}
/*
##################################################
   カウントダウン停止
##################################################
*/
stopCountDown() {
    const wg = this;
    
    if ( wg.widgetTimerId !== false ) {
        clearInterval( wg.widgetTimerId );
        wg.widgetTimerId = false;
    }
}

}