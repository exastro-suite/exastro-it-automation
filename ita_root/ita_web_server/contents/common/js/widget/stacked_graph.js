// JavaScript Document

export class WidgetStackedGraph extends WidgetCommon {
/*
##################################################
   Widget
##################################################
*/
widget() {
    const wg = this;
    
    // 表示期間
    const today = new Date(),
          targetDay = new Date().setDate( today.getDate() - wg.data.period + 1 ),
          note = getMessage.FTE08080( fn.date( targetDay, 'yyyy/MM/dd'), fn.date( today, 'yyyy/MM/dd') );
    
    wg.$.widget = $( wg.widgetHtml( note ) );
    wg.$.widget.find('.widget-body').html( wg.body() );
    
    return wg.$.widget;
}
/*
##################################################
   作業履歴（work_result）データ変換
##################################################
*/
workHistory( data ) {
    const wg = this;
    
    const workHistory = {};
    
    // 凡例
    // [ name, 表示名, リンク先, 背景カラー ]
    workHistory.usage = [
        ['sum', getMessage.FTE08067, '?menu=conductor_list', 'transparent'],
        ['done', getMessage.FTE08068, '?menu=conductor_list', '#91D21E'],
        ['fail', getMessage.FTE08069, '?menu=conductor_list','#8227B4'],
        ['warning', getMessage.FTE08070, '?menu=conductor_list','#FFB400'],
        ['stop', getMessage.FTE08071, '?menu=conductor_list','#FFDC00'],
        ['cancel', getMessage.FTE08072, '?menu=conductor_list','#FF69A3'],
        ['error', getMessage.FTE08073, '?menu=conductor_list','#E60000']
    ];
    
    // 縦軸・横軸名称
    workHistory.unit = [ getMessage.FTE08074, getMessage.FTE08075 ];
    
    // 項目名称
    workHistory.item = [];
    
    // グラフデータ
    workHistory.data = [];
    
    const period = wg.data.period,
          date = new Date(),
          today = new Date();

    // 履歴配列初期化
    for ( let i = 0; i < period; i++ ) {
      workHistory.item.push([ fn.date( date, 'yyyy/MM/dd'), date.getDate() ]);
      workHistory.data.push([ 0, 0, 0, 0, 0, 0, 0 ]);
      date.setDate( date.getDate() - 1 );
    }
    
    // 日別にカウントする
    for ( const type in data ) {
        for ( const num in data[ type ] ) {
            for ( const id in data[ type ][ num ] ) {
                const result = data[ type ][ num ][ id ],
                      status = result.status,
                      targetDay = new Date( result.end ),
                      diff = Math.round( ( today - targetDay ) / 86400000 );

                const usage = workHistory.usage.findIndex(function( item ){
                    return item[1] === status;
                });
                
                if ( diff < period ) {
                    workHistory.data[ diff ][ usage ]++;
                }
            }
        }
    }
    
    return workHistory;
}
/*
##################################################
   Stacked graph
##################################################
*/
body() {
    const wg = this;
    
    const widgetID = wg.id;
    
    // グラフデータ変換
    switch ( wg.data.widget_name ) {
        case 'workHistory': wg.stackedGraphData = wg.workHistory( wg.infoData ); break;
        default: wg.stackedGraphData = wg.infoData;
    }
    const stackedGraphData = wg.stackedGraphData;

    let sgHTML = '<div class="stacked-graph">';
    
    // 凡例と縦軸単位
    sgHTML += ``
    + `<div class="stacked-graph-header">`
        + `<div class="stacked-graph-vertica-unit">${stackedGraphData.unit[0]}</div>`
        + `<div class="stacked-graph-usage">`
            + `<ul class="stacked-graph-usage-list">`;
    
    const usageLength = stackedGraphData.usage.length;
    for ( let i = 1; i < usageLength; i++ ) {
        sgHTML += ``
        + `<li class="stacked-graph-usage-item">`
            + `<span class="db-usage" style="background-color:${stackedGraphData.usage[i][3]}"></span>`
            + stackedGraphData.usage[i][1]
        + `</li>`;
    }
    
    sgHTML += '</ul>'
        + '</div>'
    + '</div>';
    
    // 合計値と最大値
    let sgMax = 0;
    
    const sgLength = stackedGraphData.data.length
    for ( let i = 0; i < sgLength; i++ ) {
        const itemLength = stackedGraphData.data[i].length;
        for ( let j = 1; j < itemLength; j++ ) {
            stackedGraphData.data[i][0] += stackedGraphData.data[i][j];
        }
        if ( stackedGraphData.data[i][0] > sgMax ) sgMax = stackedGraphData.data[i][0];
    }
    
    // グラフ縦軸
    const digit = String( sgMax ).length, // 桁数
          digitNumber = Math.pow( 5, digit - 1 ), // 縦軸の数
          graphMaxNumber = Math.ceil( sgMax / digitNumber ) * digitNumber; // グラフ最大値
    
    sgHTML += ``
    + `<div class="stacked-graph-body">`
        + `<ol class="stacked-graph-vertical-axis">`;
    
    const verticalAxisLength = graphMaxNumber / digitNumber;
    for( let i = 0; i <= verticalAxisLength; i++ ) {
        sgHTML += `<li class="stacked-graph-vertical-axis-item">${ i * digitNumber }</li>`;
    }
    sgHTML += `</ol>`;

    // グラフ本体
    sgHTML += `<ol class="stacked-graph-horizontal-axis">`;
    for ( let i = sgLength - 1; 0 <= i; i-- ) {
        const sum = stackedGraphData.data[i][0],
              sumPer = Math.round( sum / graphMaxNumber * 100 ),
              itemLength = stackedGraphData.data[i].length;

        sgHTML += ``
        + `<li class="stacked-graph-item">`
            + `<dl class="stacked-graph-item-inner" data-id="${i}">`
                + `<dt class="stacked-graph-item-title"><span class="day-number">${stackedGraphData.item[i][1]}</span></dt>`
                + `<dd class="stacked-graph-bar">`;

        if ( sum !== 0 ) {
            sgHTML += `<ul class="stacked-graph-bar-group" data-style="${sumPer}%">`;
            for ( let j = 1; j < itemLength; j++ ) {
                const itemPer = Math.round( stackedGraphData.data[i][j] / sum * 100 );
                sgHTML += `<li class="stacked-graph-bar-item stacked-graph-bar-${stackedGraphData.usage[j][0]}" style="height:${itemPer}%;background-color:${stackedGraphData.usage[j][3]}"></li>`;
            }
            sgHTML += '</ul>';
        }
        
        sgHTML += ``
                + `</dd>`
            + `</dl>`
        + `</li>`;
    }
    
    sgHTML += '</ol></div>';
    
    // 横軸単位
    sgHTML += ``
    + `<div class="stacked-graph-footer">`
        + `<div class="stacked-graph-horizontal-unit">${stackedGraphData.unit[1]}</div>`
    + '</div>'
    + `</div></div><div class="stacked-graph-popup"></div></div>`;
    
    return sgHTML;
}
/*
##################################################
   準備完了時
##################################################
*/
ready() {
    const wg = this;
    
    wg.$.widget.find('.stacked-graph-bar-group').each( function(){
        const $bar = $( this );
        $bar.attr('style', 'height:' + $bar.attr('data-style') );
    });
    wg.setDetaileEvent();
}
/*
##################################################
   詳細表示イベント
##################################################
*/
setDetaileEvent() {
    const wg = this;
    wg.$.widget.find('.stacked-graph-item-inner').on({
        'mouseenter.detaile': function() {
            const $bar = $( this ),
                  $window = $( window ),
                  $pop = wg.$.widget.find('.stacked-graph-popup'),
                  dataID = Number( $bar.attr('data-id') ),
                  resultData = wg.stackedGraphData.data[ dataID ],
                  resultLength = resultData.length,
                  usage = wg.stackedGraphData.usage,
                  item =  wg.stackedGraphData.item,
                  total = wg.stackedGraphData.data[ dataID ][ 0 ];
            
            const resultRow = function( date, color, text, url, number, sumFlag = false ){
                // filter
                const filter = {
                    last_update_date_time: {
                        RANGE: {
                            START: `${date} 00:00:00`,
                            END: `${date} 23:59:59`
                        }
                    }
                };
                // 計は全て
                if ( sumFlag ) {
                    const itemList = [];
                    for ( const u of usage ) {
                        if ( u[0] !== 'sum') itemList.push( u[1] );
                    }
                    filter.status_id = {
                        LIST: itemList
                    }
                } else {
                    filter.status_id = {
                        LIST: text
                    }
                }
                
                const numHtml = ( number !== 0 )?
                    wg.linkHtml('db-cell-l db-cell-ln', `${url}&filter=${fn.filterEncode( filter )}`, number, wg.data.page_move ):
                    `<span class="db-cell-z">0</span>`;
            
                return ''
                + '<tr class="db-row">'
                  + '<th class="db-cell"><div class="db-cell-i">'
                    + '<span class="db-usage" style="background-color:' + color + '"></span>' + text
                  + '</div></th>'
                  + '<td class="db-cell"><div class="db-cell-i"">'
                    + numHtml
                  + '</div></td></tr>';
            };
            
            const setResult = function(){
                // Table
                const title = item[ dataID ][ 0 ];
                let tableHTML = '<div class="stacked-graph-popup-inner">'
                  + '<div class="stacked-graph-popup-close">' + fn.html.icon('cross') + '</div>'
                  + '<div class="stacked-graph-popup-date">' + title + '</div>'
                  + '<div class="db-table-wrap"><table class="db-table"><tbody>';

                for ( let i = 1; i < resultLength; i++ ) {
                  tableHTML += resultRow( title, usage[i][3], usage[i][1], usage[i][2], resultData[i] );
                }
                tableHTML += resultRow( title, usage[0][3], usage[0][1], usage[0][2], resultData[0], true );

                tableHTML += '</tbody></table></div></div>';
                $pop.html( tableHTML );
                $pop.find('.stacked-graph-popup-close').on('click', function(){
                  $pop.removeClass('fixed').html('').hide();
                });
            };
            
            const setPopPosition = function( pageX, pageY ) {
                const scrollTop = $window.scrollTop(),
                      scrollLeft = $window.scrollLeft(),
                      windowWidth = $window.width(),
                      popupWidth = $pop.outerWidth();

                let leftPosition = pageX - scrollLeft;

                // 右側チェック
                if ( leftPosition + ( popupWidth / 2 ) > windowWidth ) {
                  leftPosition = leftPosition - (( leftPosition + ( popupWidth / 2 ) ) - windowWidth );
                }
                // 左側チェック
                if ( leftPosition - ( popupWidth / 2 ) < 0 ) {
                  leftPosition = popupWidth / 2;
                }

                $pop.show().css({
                  'left': leftPosition,
                  'top': pageY - scrollTop - 16
                });
            };

            $bar.on('click.stackedGraphPopup', function( e ){
              if ( $pop.is('.fixed') ) {
                setPopPosition( e.pageX, e.pageY );
                setResult();
              }
              $pop.toggleClass('fixed');
            });

            $window.on('mousemove.stackedGraphPopup', function( e ) {
              const $target = $( e.target ).closest('.stacked-graph-item');
              if ( $target.length ) {
                let y = 0;
                if ( $target.find('.stacked-graph-bar-group').length ) {
                  y = $target.find('.stacked-graph-bar-group').offset().top;
                } else {
                  y = $target.find('.stacked-graph-item-title').offset().top;
                }
                if ( !$pop.is('.fixed') ) {
                  setPopPosition( e.pageX, y );
                  setResult();
                }
              }            
            });
        },
        'mouseleave.detaile': function() {
            wg.$.widget.find('.stacked-graph-popup').not('.fixed').html('').hide();
            $( this ).off('click.stackedGraphPopup');
            $( window ).off('mousemove.stackedGraphPopup');
        }
        
    });
}

}