// JavaScript Document

class WidgetCommon {
/*
##################################################
   Constructor
##################################################
*/
constructor( id, data, position, maxSize, infoData ) {
    this.id = id;
    this.data = data;
    this.widgetPosition = position;
    this.maxSize = maxSize;
    this.infoData = infoData;
    
    this.$ = {};
}
/*
##################################################
   Widget HTML
##################################################
*/
widgetHtml( titleNote = '' ) {
    const wg = this;
    
    const id = wg.id,
          data = wg.data;
    
    const attrs = {
        widget_id: 'data-widget-id',
        display: 'data-widget-display',
        header: 'data-widget-header',
        background: 'data-widget-background',
        rowspan: 'data-rowspan',
        colspan: 'data-colspan'
    }
    
    // Widget固有設定（attrがあるもの）
    if ( data.unique_setting.length ) {
        for ( const setting of data.unique_setting ) {
            if ( setting.attr ) {
                attrs[ setting.name ] = setting.attr;
            }
        }
    }
    const attr = [];
    for ( const k in attrs ) {
        const val = data[ k ];
        if ( val !== undefined ) attr.push(`${attrs[ k ]}="${val}"`);
    }

    // 編集ボタン
    const editButton = [`<li class="widget-edit-menu-item"><button class="widget-edit-button widget-edit" title="${getMessage.FTE08057}" data-type="edit">${fn.html.icon('edit')}</button></li>`];
    if ( data.widget_id !== 0 ) editButton.push(`<li class="widget-edit-menu-item"><button class="widget-edit-button widget-delete" title="${getMessage.FTE08058}" data-type="delete">${fn.html.icon('cross')}</button></li>`);
    
    const html = ``
    + `<div id="${id}" style="grid-area:${id}" class="widget-grid" ${attr.join(' ')}>`
        + `<div class="widget">`
            + `<div class="widget-header">`
                + `<div class="widget-move-knob"></div>`
                + `<div class="widget-name">`
                    + `<span class="widget-name-inner">${fn.cv( data.title, '', true ) + fn.cv( titleNote, '', true )}</span>`
                    + `<div class="widget-edit-menu">`
                        + `<ul class="widget-edit-menu-list">`
                            + editButton.join('')
                        + `</ul>`
                    + `</div>`
                + `</div>`
            + `</div>`
            + `<div class="widget-body">`
            + `</div>`
        + `</div>`
    + `</div>`;
    
    return html;
}
/*
##################################################
   Widget setting modal body HTML
##################################################
*/
modalOpen( currentPosition ) {
    const wg = this;
    
    return new Promise(function( resolve ){
        const config = {
            mode: 'modeless',
            position: 'top',
            width: '640px',
            header: {
                title: fn.cv( wg.data.title, '', true ),
            },
            footer: {
                button: {
                    ok: { text: getMessage.FTE00087, action: 'default'},
                    cancel: { text: getMessage.FTE00088, action: 'normal'},
                }
            }
        };

        const functions =  {
            ok: function(){
                $modal.find('.commonBody').not('.otherBlock').find('.input, .radioText:checked').each(function(){
                    const $input = $( this ),
                          type = $input.attr('type'),
                          val = $input.val(),
                          name = $input.attr('name');
                    
                    if ( type === 'number') {
                        const num = Number( val );
                        if ( isNaN( num ) ) {
                            wg.data[ name ] = null;
                        } else {
                            wg.data[ name ] = num;
                        }
                    } else {
                        wg.data[ name ] = val;
                    }
                });
                // リスト
                $modal.find('.otherBlock[data-block-type="list"]').each(function(){
                    const $list = $( this ),
                          name = $list.attr('data-block-name');
                    wg.data[ name ] = wg.getListData( $list );
                });
                closeModal( true );
            },
            cancel: function(){
                closeModal( false );
            }
        }

        const closeModal = function( flag ){
            wg.modal.close();
            wg.modal = null;
            resolve( flag );
        }
        
        const maxSize = wg.checkWidgetSize( currentPosition, wg.data.rowspan, wg.data.colspan );
        
        // Widget 基本設定
        const commonSetting = [
            {
                name: 'title',
                title: getMessage.FTE08059,
                type: 'text'
            },
            {
                name: 'colspan',
                title: getMessage.FTE08060,
                type: 'number',
                min: 1,
                max: maxSize[1]
            },
            {
                name: 'rowspan',
                title: getMessage.FTE08061,
                type: 'number',
                min: 1,
                max: maxSize[0]
            },
            {
                name: 'display',
                title: getMessage.FTE08062,
                type: 'radio',
                list: [
                    { value: 'show', text: getMessage.FTE08007 },
                    { value: 'hide', text: getMessage.FTE08008 }
                ]
            },
            {
                name: 'header',
                title: getMessage.FTE08063,
                type: 'radio',
                list: [
                    { value: 'show', text: getMessage.FTE08007 },
                    { value: 'hide', text: getMessage.FTE08008 }
                ]
            },
            {
                name: 'background',
                title: getMessage.FTE08064,
                type: 'radio',
                list: [
                    { value: 'show', text: getMessage.FTE08007 },
                    { value: 'hide', text: getMessage.FTE08008 }
                ]
            }
        ];

        const bodyHtml = ``
        + `<div class="commonSection">`
            + wg.settingModalBlock( getMessage.FTE08065, commonSetting )
            + `${( Object.keys( wg.data.unique_setting ).length )? wg.settingModalBlock( getMessage.FTE08066, wg.data.unique_setting ): ''}`
        + `</div>`;

        wg.modal = new Dialog( config, functions );
        wg.modal.open( bodyHtml );
        
        const $modal = wg.modal.$.dbody;
        
        // フェーダーイベント
        $modal.find('.inputFaderWrap').each(function(){
            fn.faderEvent( $( this ) );
        });
        
        // リストイベント
        wg.setListEvent( $modal );
        
        // サイズを更新するごとにサイズの最大値を更新する
        const $row = $modal.find('.inputFader[name="rowspan"]'),
              $col = $modal.find('.inputFader[name="colspan"]');
              
        $row.add( $col ).on('change', function(){
            const rowVal = Number( $row.val() ),
                  colVal = Number( $col.val() ),
                  max = wg.checkWidgetSize( currentPosition, rowVal, colVal ),
                  type = $( this ).attr('name');
            
            if ( type === 'rowspan') {
                $col.attr('data-max', max[1] ).trigger('maxChange');
            } else {
                $row.attr('data-max', max[0] ).trigger('maxChange');
            }
        });
    });
}
/*
##################################################
   サイズ変更可能な行列を求める
##################################################
*/
checkWidgetSize( p, setRow, setCol ) {
    const wg = this,
          wp = wg.widgetPosition,
          maxCol = wg.maxSize.col,
          maxRow = wg.maxSize.row,
          c = [];
    
    positionLabel:
    for ( let i = 0; i < maxRow; i++ ) {
        const rn = p[0] + i;
        if ( wp[rn] === undefined ) break;
        for ( let j = 0; j < maxCol - p[1]; j++ ) {
            const cn = p[1] + j;
            if ( wp[rn][cn] !== undefined && ( wp[rn][cn].match(/^b/) || wp[rn][cn] === wg.id )) {
                c[i] = j + 1;
            } else {
                if ( j === 0 ) {
                    break positionLabel;
                } else {
                    break;
                }
            }
        }
    }
    
    const cLength = c.length;
    let row = 0,
        col = wg.maxSize.col;
    
    // 列サイズ
    for ( let i = 0; i < setRow; i++ ) {
        if ( col > c[i] ) col = c[i];
    }
    
    // 行サイズ
    for ( let i = 0; i < cLength; i++ ) {
        if ( setCol <= c[i] ) {
            row++;
        } else {
            break;
        }
    }

    return [ row, col ];
}
/*
##################################################
   設定Block
##################################################
*/
settingModalBlock( title, commonSetting ) {
    const wg = this;
    
    const rows = [],
          other = [];
    for ( const setting in commonSetting ) {
        switch( commonSetting[ setting ].type ) {
            case 'list': other.push( wg.settingModalList( commonSetting[ setting ] ) ); break;
            default: rows.push( wg.settingModalRow( commonSetting[ setting ] ));
        }
    }
    
    const html = [];
    if ( rows.length ) {
        html.push(``
        + `<div class="commonTitle">${title}</div>`
        + `<div class="commonBody">`
            + `<div class="commonInputGroup">`
                + `<table class="commonInputTable">`
                    + `<tbody class="commonInputTbody">`
                        + rows.join('')
                    + `<tbody>`
                + `</table>`
            + `</div>`
        + `</div>`);
    }
    if ( other.length ) {
        html.push( other.join('') );
    }
    
    return html.join('');
}
/*
##################################################
   設定行
##################################################
*/
settingModalRow( settingData ) {
    return ``
    + `<tr class="commonInputTr">`
        + `<th class="commonInputTh"><div class="commonInputTitle">${fn.cv( settingData.title, '', true )}</div></th>`
        + `<td class="commonInputTd">${this.settingModalInput( settingData )}</td>`
    + `</tr>`;
}
/*
##################################################
   設定入力欄
##################################################
*/
settingModalInput( settingData ) {
    const key = settingData.name,
          value = fn.cv( this.data[ key ], '', true );
    switch ( settingData.type ) {
        case 'text':  return fn.html.inputText('db-modal-text', value, key );
        case 'number': {
            const option = {};
            if ( settingData.before ) option.before = settingData.before;
            if ( settingData.after ) option.after = settingData.after;
            return fn.html.inputFader('db-modal-number', value, key, { min: settingData.min, max: settingData.max }, option );
        }
        case 'radio': return this.settingModalInputRadio( value, key, settingData.list );
    }
}
/*
##################################################
   設定ラジオ
##################################################
*/
settingModalInputRadio( value, key, list ) {
    const itemArray = [];    
    for ( const item of list ) {
        const itemValue = item.value,
              text = fn.cv( item.text, '', true ),
              checked = ( value === itemValue )? { checked: 'checked'}: {},
              listHtml = `<li class="commonRadioItem">${fn.html.radioText('db-modal-radio', itemValue, key, `db-modal-radio-${key}_${itemValue}`, checked, text )}</li>`;
        itemArray.push( listHtml );
    }
    
    return `<ul class="commonRadioList">${itemArray.join('')}</ul>`;
}
/*
##################################################
   設定リスト
##################################################
*/
settingModalList( settingData ) {
    const wg = this;
    
    const key = settingData.name;
    
    // 編集メニュー
    const menuList = {
        Main: [
            { button: { type: 'add', icon: 'plus', text: getMessage.FTE08014, action: 'normal'}},
            { button: { type: 'download', icon: 'download', text: getMessage.FTE08015, action: 'normal'}, separate: true },
            { button: { type: 'read', icon: 'upload', text: getMessage.FTE08016, action: 'normal'}},
        ]
    };
    
    let html = ``
    + `<div class="commonTitle">${fn.cv( settingData.title, '', true )}</div>`
    + `<div class="commonBody otherBlock" data-block-name="${key}" data-block-type="${settingData.type}">`
    + `<div class="commonInputGroup">`
    + fn.html.operationMenu( menuList )
    + `<table class="db-modal-list-table">`
        + `<thead class="db-modal-list-thead">`
            + `<tr>`
                + `<th class="db-modal-list-th db-modal-list-action"></th>`;
    
    for ( const type in settingData.list ) {
        html += `<th class="db-modal-list-th"><div class="db-modal-list-header">${settingData.list[ type ]}</div></th>`;
    }
    
    html += ``
                + `<th class="db-modal-list-th db-modal-list-action"></th>`
            + `<tr>`
        + `</thead>`
        + `<tbody class="db-modal-list-tbody">`
    
    let value = this.data[ key ];
    if ( !value || !value.length ) {
        value = [{name: '', url: ''}];
    }
    
    const disabled = ( value.length === 1 )? true: false;
    wg.listIndex = 0;
    for ( const item of value ) {
        html += wg.createListRowHtml( key, item, disabled );
    }
    
    html += ``
            + `<tr>`
        + `</tbody>`
    + `</table>`
    + `</div>`
    + `</div>`;
    
    return html;
}
/*
##################################################
   リストHTML
##################################################
*/
createListRowHtml( key, item, disabledFlag = false ) {
    const wg = this;
    
    const disabled = ( disabledFlag )? ' disabled': '',
          row = [`<tr class="db-modal-list-tr"><td class="db-modal-list-td"><div class="db-modal-list-move${disabled}"></div></td>`];
    
    for ( const type in item ) {
        const idName = `${key}_${type}_${wg.listIndex}`;
              row.push(`<td class="db-modal-list-td"><div class="db-modal-list-input">${fn.html.inputText('db-modal-text', fn.cv( item[ type ], '', true ), idName, { key: type } )}</div></td>`);
    }    
    wg.listIndex++;
    row.push(`<td class="db-modal-list-td"><div class="db-modal-list-delete${disabled}">${fn.html.icon('cross')}</div></td></tr>`);
    return row.join('');
}
/*
##################################################
   項目が１つの場合は移動と削除を無効化する
##################################################
*/
checkListDisabled() {
    const wg = this;
    
    const $tr = wg.modal.$.dbody.find('.db-modal-list-tr');

    if ( $tr.length === 1 ) {
        $tr.find('.db-modal-list-move, .db-modal-list-delete').addClass('disabled');
    } else {
        $tr.find('.db-modal-list-move, .db-modal-list-delete').removeClass('disabled');
    }
    
}
/*
##################################################
   リストイベント
##################################################
*/
setListEvent() {
    const wg = this;

    wg.modal.$.dbody.find('.otherBlock[data-block-type="list"]').each(function(){
        const $listBlock = $( this ),
              key = $listBlock.attr('data-block-name');
        
        // メニュー
        $listBlock.find('.operationMenuButton').on('click', function(){
            const $button = $( this ),
                  type = $button.attr('data-type');
            switch( type ) {
                case 'add': {
                    const empty = {},
                          setting = wg.data.unique_setting.find(function( item ){ return item.name === key; });
                    for ( const item in setting.list ) {
                        empty[ item ] = '';
                    }
                    $listBlock.find('.db-modal-list-tbody').append( wg.createListRowHtml( key, empty ) );
                    wg.checkListDisabled();
                } break;
                case 'download': {
                    let downloadData;
                    try {
                        downloadData = JSON.stringify( wg.getListData( $listBlock ) );
                    } catch( error ) {
                        alert( error );
                    }
                    fn.download('text', downloadData, `dashboard_${key}`);
                } break;
                case 'read':
                    fn.fileSelect('json').then(function( result ){
                        const rowHtml = [];
                        for ( const item in result.json ) {
                            rowHtml.push( wg.createListRowHtml( key, result.json[ item ] ) );
                        }
                        $listBlock.find('.db-modal-list-tbody').html( rowHtml.join('') );
                    }).catch(function( error ){
                        alert( error );
                    });
                break;
            }
        });
        
        // 削除
        $listBlock.on('mousedown', '.db-modal-list-delete', function(){
            $( this ).closest('.db-modal-list-tr').remove();
            wg.checkListDisabled();
        });
        
        // 移動
        $listBlock.on('mousedown', '.db-modal-list-move', function( mde ){
            const $move = $( this ),
                  $window = $( window );
                  
            if ( !$move.is('.disabled') ) {
                const $line = $move.closest('.db-modal-list-tr'),
                      $list = $line.closest('.db-modal-list-tbody'),
                      height = $line.outerHeight(),
                      defaultY = $line.position().top,
                      maxY = $list.outerHeight() - height,
                      $dummy = $('<tr class="db-modal-list-dummy"></tr>'),
                      $body = $move.closest('.dialogBody'),
                      defaultScroll = $body.scrollTop();
                
                // 幅を固定
                $line.find('.db-modal-list-td').each(function(){
                    const $td = $( this );
                    $td.css('width', $td.outerWidth() );
                });
                
                $list.addClass('active');
                $line.addClass('move').css('top', defaultY ).after( $dummy )
                $dummy.css('height', height );
                
                fn.deselection();

                let positionY = defaultY;
                const listPosition = function(){
                    let setPostion = positionY - ( defaultScroll - $body.scrollTop() );
                    if ( setPostion < 0 ) setPostion = 0;
                    if ( setPostion > maxY ) setPostion = maxY;
                    $line.css('top', setPostion );
                };

                $body.on('scroll.freeMove', function(){
                    listPosition();
                });
                
                $window.on({
                    'mousemove.freeMove': function( mme ){
                        positionY = defaultY + mme.pageY - mde.pageY;
                        listPosition();
                        if ( $( mme.target ).closest('.db-modal-list-tr').length ) {
                            const $target = $( mme.target ).closest('.db-modal-list-tr'),
                                  targetNo = $target.index(),
                                  dummyNo = $dummy.index();
                            if ( targetNo < dummyNo ) {
                                $target.before( $dummy );
                            } else {
                                $target.after( $dummy );
                            }
                        }
                    },
                    'mouseup.freeUp': function(){
                        $body.off('scroll.freeMove');
                        $window.off('mousemove.freeMove mouseup.freeUp');
                        $list.removeClass('active');
                        $line.removeClass('move');
                        $line.find('.db-modal-list-td').removeAttr('style');
                        $dummy.replaceWith( $line );
                    }
                });
            }
        });
        
        
    });
    
}
/*
##################################################
   リストデータ取得
##################################################
*/
getListData( $list ) {
    const data = [];
    $list.find('.db-modal-list-tr').each(function(){
        const $tr = $( this ),
              row = {};
        $tr.find('.input').each(function(){
            const $item = $( this ),
                  val = $item.val(),
                  name = $item.attr('data-key');
            row[ name ] = val;
        });
        // 未入力がある場合は無視
        let count = 0;
        for ( const key in row ) {
            if ( row[ key ] === '') count++;
        }
        if ( count === 0 ) data.push( row );
    });
    return data;
}
/*
##################################################
   リンクHTML
##################################################
*/
linkHtml( className, href, text, type = 'same', option = {}) {
    if ( option.encode === true ) {
        href = encodeURI( fn.cv( href, '' ) );
    }
    
    const attr = [`class="${className} db-link" href="${href}" data-type="${type}"`];
    if ( type === 'blank') {
        attr.push(`target="_blank" rel="noopener noreferrer"`);
    }

    return `<a ${attr.join(' ')}>${text}</a>`;
}

}