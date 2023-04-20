// JavaScript Document

export class WidgetPieChart extends WidgetCommon {
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
   Movement（movement）データ変換
##################################################
*/
movement( data ) {
    const movementSetting = {
        'Ansible Legacy':  ['ansible_legacy', 0, '?menu=movement_list_ansible_legacy', '#F0891D'],
        'Ansible Pioneer':  ['ansible_pioneer', 0, '?menu=movement_list_ansible_pioneer', '#009768'],
        'Ansible Legacy Role':  ['ansible_legacy_role', 0, '?menu=movement_list_ansible_role', '#684915'],
        'Terraform Cloud/EP':  ['terraform_cloud_ep', 0, '?menu=movement_list_terraform_cloud_ep', '#6C60E8'],
        'Terraform CLI':  ['terraform_cli', 0, '?menu=movement_list_terraform_cli', '#889dd8'],
    };
    const movementData = {};
    for ( const key in data ) {
        const num = Number( data[ key ].number );
        if ( !isNaN( num ) && num !== 0 ) {
            const name = data[ key ].name;
            movementData[ name ] = movementSetting[ name ];
            movementData[ name ][ 1 ] = num;
        }
    }
    return movementData;
}
/*
##################################################
   作業状況（work_info）データ変換
##################################################
*/
workStatus( data ) {
    const workStatusSetting = {};
    workStatusSetting[ getMessage.FTE08076 ] = ['runing', 0, '?menu=conductor_list', '#002B62'];
    workStatusSetting[ getMessage.FTE08077 ] = ['schedule', 0, '?menu=conductor_list', '#7A91AD'];
    workStatusSetting[ getMessage.FTE08078 ] = ['stop', 0, '?menu=conductor_list', '#FF640A'];
    workStatusSetting[ getMessage.FTE08079 ] = ['waiting', 0, '?menu=conductor_list', '#ADADAD'];

    // フィルター
    for ( const type in workStatusSetting ) {
        const filter = {
            status_id: {
               LIST: type
            }
        };
        workStatusSetting[ type ][2] += `&filter=${fn.filterEncode( filter )}`;
    }
    
    for ( const type in data ) { // conductor
        for ( const num in data[ type ] ) {
            for ( const id in data[ type ][ num ] ) {
                const result = data[ type ][ num ][ id ];
                if ( workStatusSetting[ result.status ] ) {
                    workStatusSetting[ result.status ][1]++;
                }
            }
        }
    }
    return workStatusSetting;
}
/*
##################################################
   作業結果（work_result）データ変換
##################################################
*/
workResult( data ) {
    const workResultSetting = {};
    workResultSetting[ getMessage.FTE08068 ] = ['done', 0, '?menu=conductor_list', '#91D21E'];
    workResultSetting[ getMessage.FTE08069 ] = ['fail', 0, '?menu=conductor_list', '#8227B4'];
    workResultSetting[ getMessage.FTE08070 ] = ['warning', 0, '?menu=conductor_list', '#FFB400'];
    workResultSetting[ getMessage.FTE08071 ] = ['stop', 0, '?menu=conductor_list', '#FFDC00'];
    workResultSetting[ getMessage.FTE08072 ] = ['cancel', 0, '?menu=conductor_list', '#FF69A3'];
    workResultSetting[ getMessage.FTE08073 ] = ['error', 0, '?menu=conductor_list', '#E60000'];

    // フィルター
    for ( const type in workResultSetting ) {
        const filter = {
            status_id: {
               LIST: type
            }
        };
        workResultSetting[ type ][2] += `&filter=${fn.filterEncode( filter )}`;
    }
    
    const resultData = {};
    for ( const type in data ) { // conductor
        for ( const num in data[ type ] ) {
            for ( const id in data[ type ][ num ] ) {
                const result = data[ type ][ num ][ id ];
                if ( workResultSetting[ result.status ] ) {
                    workResultSetting[ result.status ][1]++;
                }                
            }
        }
    }
    return workResultSetting;
}
/*
##################################################
   円グラフ
##################################################
*/
body() {
    const wg = this;

    // 円グラフデータ変換
    let pieChartData;
    switch ( wg.data.widget_name ) {
        case 'movement': pieChartData = wg.movement( wg.infoData ); break;
        case 'workStatus': pieChartData = wg.workStatus( wg.infoData ); break;
        case 'workResult': pieChartData = wg.workResult( wg.infoData ); break;
        default: pieChartData = wg.infoData;
    }
    
    const widgetID = wg.id,
          title = fn.cv( wg.data.pie_chart_title, '', true );
    
    const xmlns = 'http://www.w3.org/2000/svg',
          radius = 50,  // 円グラフ半径
          strokeWidth = 20,  // 円グラフ線幅
          circumference = radius * 2 * Math.PI, // 円周（半径×２×円周率）
          cxcy = radius + strokeWidth,
          viewBox = cxcy * 2,
          viewBoxAttr = '0 0 ' + viewBox + ' ' + viewBox;
    
    // 円グラフ
    const $pieChartSvg = $( document.createElementNS( xmlns, 'svg') );
    $pieChartSvg.attr('class','pie-chart-svg').get(0).setAttribute('viewBox', viewBoxAttr );
    
    // 装飾
    const $pieChartSvgDecoration = $( document.createElementNS( xmlns, 'svg') );
    $pieChartSvgDecoration.attr('class','pie-chart-decoratio-svg').get(0).setAttribute('viewBox', viewBoxAttr );
    $pieChartSvgDecoration.html(
      '<circle cx="' + cxcy + '" cy="' + cxcy + '" r="' + ( cxcy - 5 ) + '" class="pie-chart-circle-outside"></circle>'
      + '<circle cx="' + cxcy + '" cy="' + cxcy + '" r="' + ( cxcy - 15 - strokeWidth ) + '" class="pie-chart-circle-inside"></circle>'
    );
    
    // 割合表示
    const $pieChartRatioSvg = $( document.createElementNS( xmlns, 'svg') );
    $pieChartRatioSvg.attr('class','pie-chart-ratio-svg').get(0).setAttribute('viewBox', viewBoxAttr );
    
    const outSideNamber = [];
    let totalNumber = 0,
        serialWidthNumber = 0,
        serialAngleNumber = -90,
        outsideGroupCheck = 0,
        outsideGroupNumber = -1,
        checkGroupText = '';
    
    // 合計値
    for ( let key in pieChartData ) {
        totalNumber += pieChartData[key][1];
    }
    
    // Table
    let tableHTML = '';
    if ( Object.keys( pieChartData ).length ) {
        tableHTML += ''
        + '<div class="db-table-wrap">'
          + '<table class="db-table">'
            + '<tbody>';
        for ( let key in pieChartData ) {
            const number = Number( pieChartData[key][1] ),
                  numHtml = ( number !== 0 )?
                wg.linkHtml('db-cell-l db-cell-ln', pieChartData[key][2], number, wg.data.page_move ):
                `<span class="db-cell-z">0</span>`;

            tableHTML += ''
                + '<tr class="db-row" data-type="' + pieChartData[key][0] + '">'
                  + '<th class="db-cell"><div class="db-cell-i">'
                    + '<span class="db-usage" style="background-color:' + pieChartData[key][3] + '"></span>' + key
                  + '</div></th>'
                  + '<td class="db-cell"><div class="db-cell-i">'
                    + numHtml
                  + '</div></td>'
              + '</tr>';
        }
        tableHTML += ''
            + '</tbody>'
          + '</table>'
        + '</div>';
    } else {
        tableHTML += '<div class="db-nodata">No data</div>';
    }
    
    for ( let key in pieChartData ) {
        const $pieChartCircle = $( document.createElementNS( xmlns, 'circle') ),
              $pieChartText = $( document.createElementNS( xmlns, 'text') );

        // 割合・幅の計算
        const className = 'circle-' + pieChartData[key][0],
              number = pieChartData[key][1],
              ratio = number / totalNumber,
              angle = 360 * ratio;

        // 幅
        let ratioWidth = Math.round( circumference * ratio * 1000 ) / 1000;
        if ( serialWidthNumber + ratioWidth > circumference ) ratioWidth = circumference - serialWidthNumber;
        const remainingWidth =  Math.round( ( circumference - ( serialWidthNumber + ratioWidth ) ) * 1000 ) / 1000;

        // stroke-dasharrayの形に整える
        let strokeDasharray = '';
        if ( isNaN( ratioWidth ) ) {
            strokeDasharray === 'none';
        } else {
            if ( serialWidthNumber === 0 ) {
                strokeDasharray = ratioWidth + ' ' + remainingWidth + ' 0 0';
            } else {
                strokeDasharray = '0 ' + serialWidthNumber + ' ' + ratioWidth + ' '+ remainingWidth;
            }
        }

        // 属性登録
        $pieChartCircle.attr({
            'cx': cxcy,
            'cy': cxcy,
            'r': radius,
            'stroke': pieChartData[key][3],
            'class': 'pie-chart-circle ' + className,
            'style': 'stroke-dasharray:0 0 0 '+ circumference,
            'data-style': strokeDasharray,
            'data-type': pieChartData[key][0]
        });

        // 追加
        $pieChartSvg.append( $pieChartCircle );

        // 割合追加
        if ( ratio > 0 ) {
            const textAngle = serialAngleNumber + ( angle / 2 ),
                  centerPosition = wg.anglePiePosition( cxcy, cxcy, radius, textAngle );
            let ratioClass = 'pie-chart-ratio ' + className,
                x = centerPosition[0],
                y = centerPosition[1];

            const displayRatio = Math.round( ratio * 1000 ) / 10;

            // 特定値以下の場合は表示の調整をする
            if ( displayRatio < 2.5 ) {
                if ( outsideGroupCheck === 0 ) {
                    checkGroupText += '@'; // グループフラグ
                    outsideGroupNumber++;
                    outSideNamber[outsideGroupNumber] = new Array();
                }
                outsideGroupCheck = 1;
                outSideNamber[outsideGroupNumber].push( [ratioClass,textAngle,displayRatio] );
            } else {
                // 30%以下の場合グループを分けない
                if ( displayRatio > 30 ) {
                    outsideGroupCheck = 0;
                    checkGroupText += 'X';
                }
                if ( displayRatio < 10 ) {
                    ratioClass += ' rotate';
                    let rotateAngle = textAngle;
                    if ( textAngle > 90 ) rotateAngle = rotateAngle + 180;
                    $pieChartText.attr('transform', 'rotate('+rotateAngle+','+x+','+y+')' );
                     y += 1.5; //ベースライン調整
                } else {
                     y += 2.5;
                }
                $pieChartText.html( displayRatio + '<tspan class="ratio-space"> </tspan><tspan class="ratio-mark">%</tspan>').attr({
                    'x': x,
                    'y': y,
                    'text-anchor': 'middle',
                    'stroke': pieChartData[key][3],
                    'class': ratioClass
                });
                $pieChartRatioSvg.append( $pieChartText );
            }
        }

        // スタート幅
        serialWidthNumber += ratioWidth;
        serialAngleNumber += angle;
        if ( serialWidthNumber > circumference ) serialWidthNumber = circumference;
    }
    
    // 2.5%以下は外側に表示する
    let outSideGroupLength = outSideNamber.length;
    if ( outSideNamber.length > 0 ) {
        // 最初と最後が繋がる場合、最初のグループを最後に結合する
        if ( checkGroupText.length > 2 && checkGroupText.slice( 0, 1 ) === '@' && checkGroupText.slice( -1 ) === '@' ) {
            outSideNamber[ outSideGroupLength - 1] = outSideNamber[ outSideGroupLength - 1].concat( outSideNamber[0] );
            outSideNamber.shift();
            outSideGroupLength = outSideNamber.length;
        }
        for ( let i = 0; i < outSideGroupLength; i++ ) {
            const outSideNamberLength = outSideNamber[i].length;
            if ( outSideNamberLength > 0 ) {
                const maxOutWidth = 14;
                // 配列の真ん中から処理する
                let arrayNumber = Math.floor( ( outSideNamberLength - 1 ) / 2 );
                for ( let j = 0; j < outSideNamberLength; j++ ) {
                    arrayNumber = ( ( j + 1 ) % 2 !== 0 )? arrayNumber - j: arrayNumber + j; 
                    if ( outSideNamber[i][arrayNumber] !== undefined ) {
                        const $pieChartText = $( document.createElementNS( xmlns, 'text') ),
                              $pieChartLine = $( document.createElementNS( xmlns, 'line') ),
                              count = Math.floor( j / 2 ),
                              position = radius + maxOutWidth;
                        let textAnchor = 'middle',
                            ratioClass = outSideNamber[i][arrayNumber][0]  + ' outside',
                            angle = outSideNamber[i][arrayNumber][1],
                            ratio = outSideNamber[i][arrayNumber][2],
                            newAngle = angle,
                            lineStartPositionAngle,
                            rotetaNumber,
                            verticalPositionNumber = 0;

                        // 横位置調整
                        const setAngle = 16 * count + 8,
                              setLineAngle = ( Number.isInteger( ratio ) )? 4: 6;
                        if ( ( j + 1 ) % 2 !== 0 ) {
                            newAngle -= setAngle;
                            lineStartPositionAngle = newAngle + setLineAngle;
                        } else {
                            newAngle += setAngle;
                            lineStartPositionAngle = newAngle - setLineAngle;
                        }

                        if ( newAngle > 0 && newAngle < 180 ) {
                            verticalPositionNumber = 4;
                            rotetaNumber = newAngle + 270;
                        } else {
                            rotetaNumber = newAngle + 90;
                        }

                        const outsidePosition = wg.anglePiePosition( cxcy, cxcy, position, newAngle ),
                              x = outsidePosition[0],
                              y = outsidePosition[1],
                              lineStartPosition = wg.anglePiePosition( cxcy, cxcy, position, lineStartPositionAngle ),
                              x1 = lineStartPosition[0],
                              y1 = lineStartPosition[1],
                              lineEndPosition = wg.anglePiePosition( cxcy, cxcy, radius + strokeWidth / 2 - 2, angle ),
                              x2 = lineEndPosition[0],
                              y2 = lineEndPosition[1];

                        $pieChartLine.attr({
                            'x1': x1,
                            'y1': y1,
                            'x2': x2,
                            'y2': y2,
                            'class': 'pie-chart-ratio-line'
                        });
                        $pieChartText.html( ratio + '<tspan class="ratio-space"> </tspan><tspan class="ratio-mark">%</tspan>' ).attr({
                            'x': x,
                            'y': y + verticalPositionNumber,
                            'text-anchor': textAnchor,
                            'class': ratioClass,
                            'transform': 'rotate(' + rotetaNumber + ',' + x + ',' +y + ')'
                        });
                        $pieChartRatioSvg.append( $pieChartText, $pieChartLine );
                    }
                }
            }
        }
    }
    
    // テキスト
    const $pieChartTotalSvg = $( document.createElementNS( xmlns, 'svg') );
    $pieChartTotalSvg.get(0).setAttribute('viewBox', '0 0 ' + viewBox + ' ' + viewBox );
    $pieChartTotalSvg.attr('class','pie-chart-total-svg');

    const $pieChartName = $( document.createElementNS( xmlns, 'text') ).text( title ).attr({
        'class': 'pie-chart-total-name', 'x': '50%', 'y': '35%'
    });
    const $pieChartNumber = $( document.createElementNS( xmlns, 'text') ).text( totalNumber ).attr({
        'class': 'pie-chart-total-number', 'x': '50%', 'y': '50%'
    });
    const $pieChartTotal = $( document.createElementNS( xmlns, 'text') ).text('Total').attr({
        'class': 'pie-chart-total-text', 'x': '50%', 'y': '60%'
    });  
    $pieChartTotalSvg.append( $pieChartName, $pieChartNumber, $pieChartTotal );
    
    // SVG / HTML set
    const $pieChartHTML = $('<div class="pie-chart"><div class="pie-chart-inner"></div></div>' + tableHTML );
    $pieChartHTML.find('.pie-chart-inner').append( $pieChartSvgDecoration, $pieChartTotalSvg, $pieChartSvg, $pieChartRatioSvg );  
    
    return $pieChartHTML;
}
/*
##################################################
   角度から位置を求める
##################################################
*/
anglePiePosition ( x1, y1, r, a ) {
    const x2 = x1 + r * Math.cos( a * ( Math.PI / 180 ) ),
          y2 = y1 + r * Math.sin( a * ( Math.PI / 180 ) );
    return [ x2, y2 ];
}
/*
##################################################
   準備完了時
##################################################
*/
ready() {
    const wg = this;
    
    const $pieChartSvg = wg.$.widget.find('.pie-chart-svg'),
          $pieChartRatioSvg = wg.$.widget.find('.pie-chart-ratio-svg'),
          $pieChartHTML = wg.$.widget.find('.widget-body'),
          $circles = $pieChartSvg.find('.pie-chart-circle'),
          circleLength = $circles.length,
          strokeWidth = 20;

    let circleAnimationCount = 0;
    $pieChartRatioSvg.css('opacity','1');
    // 仮セットした値を本セットする
    $circles.each( function(){
        const $circle = $( this );
        if ( $circle.attr('data-style') !== '') {
            $circle.attr('style', ''
              + 'stroke-dasharray:' + $circle.attr('data-style') + ';'
              + 'stroke-width: ' + strokeWidth + 'px;');
        }
    }).on({
        // 全てのアニメーションが終わったら
        'transitionend webkitTransitionEnd': function() {
          circleAnimationCount++;
          if ( circleAnimationCount >= circleLength ) {
            $pieChartHTML.removeClass('start');
            // 円グラフホバー
            $circles.on({
              'mouseenter': function(){
                const $enter = $( this ),
                      dataType = $enter.attr('data-type');
                if ( dataType !== undefined ) {
                  $enter.closest('.widget-body').find('tr[data-type="' + dataType + '"]').addClass('emphasis');
                  $enter.css('stroke-width', strokeWidth * 1.2 );
                }
              },
              'mouseleave': function(){
                const $leave = $( this ),
                      dataType = $leave.attr('data-type');
                if ( dataType !== undefined ) {
                  $leave.css('stroke-width', strokeWidth );
                  $leave.closest('.widget-body').find('.emphasis').removeClass('emphasis');
                }
              },
              'click': function() {
                  const $pie = $( this ),
                        dataType = $pie.attr('data-type');
                  if ( dataType !== undefined ) {
                      $pie.closest('.widget-body').find('tr[data-type="' + dataType + '"]').find('.db-cell-l')[0].click();
                  }
              }
            });
            // Tableグラフホバー
            $pieChartHTML.find('.db-row').on({
              'mouseenter': function(){
                const $enter = $( this ),
                      dataType = $enter.attr('data-type');
                $enter.addClass('emphasis');
                if ( dataType !== undefined ) {
                  $enter.closest('.widget-body').find('.pie-chart-circle.circle-' + dataType ).css('stroke-width', strokeWidth * 1.2 );
                }
              },
              'mouseleave': function(){
                const $leave = $( this ),
                      dataType = $leave.attr('data-type');
                $leave.removeClass('emphasis');
                if ( dataType !== undefined ) {
                  $leave.closest('.widget-body').find('.pie-chart-circle.circle-' + dataType ).css('stroke-width', strokeWidth );
                }
              }
            });
          }        
        }
    });
}

}