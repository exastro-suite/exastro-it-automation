////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Exastro IT Automation / parameter_collection.js
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

class ParameterCollection {

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   初期設定
//
////////////////////////////////////////////////////////////////////////////////////////////////////

/*
##################################################
   Constructor
##################################################
*/
constructor( menu, user ) {
   this.menu = menu;
   this.user = user;
}
/*
##################################################
   Setup
##################################################
*/
setup() {
   const pc = this;

   // jQueryオブジェクトキャッシュ
   pc.$ = {
      body: $('body'),
      content: $('#content').find('.sectionBody')
   };

   // 選択初期値・表示設定
   pc.select = {
      tableDirection: 'horizontal'
   };

   // ローディング表示
   pc.$.content.addClass('nowLoading');

   // URLs
   const urls = [
      `/menu/parameter_collection/`,
      `/menu/parameter_collection/filter_data/`
   ];
   fn.fetch( urls ).then(function( result ){
      pc.info = result[0];
      pc.preset = result[1];
      pc.$.content.removeClass('nowLoading');

      // オペレーションの登録があるか
      if ( fn.typeof( pc.info.operation ) === 'array' && pc.info.operation.length > 0 ) {
         pc.$.content.html( pc.mainHtml() );
         pc.$.param = pc.$.content.find('.parameterMain');

         pc.presetInit();
         pc.setMenuButtonEvents();
         pc.setSelectEvents();
         pc.operationTimelineEvents();

         pc.updateHostList();
         pc.updateParameterList();
      } else {
         const message = ``
         + `<div class="commonMessage">`
            + `<div class="commonMessageInner">${fn.html.icon('circle_info')}${getMessage.FTE11048}</div>`
         + `</div>`;
         pc.$.content.html( message );
         $('#menu').find('.menuPageContent').html('');
      }
   });

}

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   HTML
//
////////////////////////////////////////////////////////////////////////////////////////////////////

/*
##################################################
   Main HTML
##################################################
*/
mainHtml() {
   const pc = this;

   const menu = {
      Main: [
         { radio:
            { 
               name: 'modeSelect',
               className: 'modeSelect',
               title: getMessage.FTE11001,
               list: { host: getMessage.FTE11002, operation: getMessage.FTE11003 },
               checked: 'host'}
         }
      ],
      Sub: [
         { button: { icon: 'gear', text: getMessage.FTE11004, type: 'setting', action: 'default'} },
         { button: { icon: 'check', text: getMessage.FTE11005, type: 'preset', action: 'default'} },
         { button: { icon: 'clock', text: getMessage.FTE11006, type: 'operationToggle', action: 'default',
         toggle: { init: 'on', on:getMessage.FTE00002, off:getMessage.FTE00003}}},
      ]
   };

   return ``
   + `<div class="parameterContainer">`
      + `<div class="parameterHeader">`
         + fn.html.operationMenu( menu )
      + `</div>`
      + pc.operationTimeLineHtml()
      + '<div class="parameterBody">'
         + `<div class="parameterSide">`
            + `<div class="parameterInfo">`
               + `<div class="commonSubTitle">${getMessage.FTE11007}</div>`
               + pc.selectButton('parameter')
               + `<div class="commonBody commonWrap targetParameter"></div>`
               + `<div class="commonSubTitle">${getMessage.FTE11008}</div>`
               + pc.selectButton('host')
               + `<div class="commonBody commonWrap targetHost"></div>`
            + `</div>`
            + `<div class="parameterSet">`
               + fn.html.iconButton('check', getMessage.FTE11009, 'itaButton parameterSetButton', { action: 'positive', disabled: 'disabled'})
            + `</div>`
         + `</div>`
         + `<div class="parameterMain">`
            + pc.initMesssageHtml()
         + `</div>`
      + `</div>`
   + `</div>`;
}
/*
##################################################
   選択ボタンHTML
##################################################
*/
selectButton( type ) {
   const pc = this;

   return ``
   + `<div class="commonButtonBody">`
      + `<ul class="commonButtonList">`
         + `<li class="commonButtonItem">${fn.html.iconButton('menuList', getMessage.FTE11010, 'itaButton commonButton selectButton', {type: type, action: 'default'}, {width: '100%'})}</li>`
         + `<li class="commonButtonItem">${fn.html.iconButton('clear', getMessage.FTE11011, 'itaButton commonButton clearButton', {type: type, action: 'negative'}, {width: '100%'})}</li>`
      + `</ul>`
   + `</div>`
}
/*
##################################################
   選択無HTML
##################################################
*/
noSelectHtml() {
   return `<div class="targetNoSelect">${getMessage.FTE11012}</div>`;
}
/*
##################################################
   初期メッセージHTML
##################################################
*/
initMesssageHtml() {
   return `<div class="parameterMessage">`
      + `<div class="commonMessage">`
         + `<div class="commonMessageInner">`
         + `<span class="icon icon-circle_info"></span>`
         + getMessage.FTE11013
   + `</div></div></div>`
}
/*
##################################################
   対象リストHTML
##################################################
*/
targetListHtml( type, select, inputFlag = false ) {
   const pc = this;

   if ( ( select && select.length ) || ( type === 'Host' && pc.select.mode === 'host') ) {
      const itemClassName = ( inputFlag )? 'commonInputItem': 'commonItem',
            listClassName = ( inputFlag )? 'commonInputList': 'commonList',
            key = ( type === 'Parameter')? 'parameter_sheet': 'host',
            idKey = ( type === 'Parameter')? 'menu_id': 'managed_system_item_number',
            nameKey = ( type === 'Parameter')? 'menu_name': 'host_name';
      
      if ( !select ) select = [];
      const selectLength = select.length;

      const list = [];
      for ( let i = 0; i < selectLength; i++ ) {
         const id = select[i];
         const item = pc.info[ key ].find(function(i){
            return i[idKey] === id;
         });

         if ( item ) {
            const name = fn.cv( item[nameKey], '', true );
            if ( inputFlag ) {
               // 最初の項目を選択
               const checked = {};
               if ( i === 0 ) {
                  checked.checked = 'checked';
                  if ( type === 'Host') pc.select.mainHost = id;
               }
               list.push(`<li class="${itemClassName} target${type}Item" data-id="${id}">`
                  + fn.html.radioText(`targetSelect${type}`, id, `targetSelect${type}`, `targetSelect${type}_${id}`, checked, name, 'narrowRadioTextWrap')
               + `</li>`);
            } else {
               list.push(`<li class="${itemClassName} target${type}Item">${name}</li>`);
            }
         }
      }
      // ホスト無
      if ( type === 'Host'  && pc.select.mode === 'host') {
         const checked = {};
         if ( selectLength === 0 ) {
            pc.select.mainHost = '-1';
            checked.checked = 'checked';
         }
         list.push(`<li class="${itemClassName} target${type}Item targetNoHost" data-id="-1">`
            + fn.html.radioText(`targetSelect${type}`, -1, `targetSelect${type}`, `targetSelect${type}_-1`, checked, getMessage.FTE11014, 'narrowRadioTextWrap')
         + `</li>`);
      }
      pc.$.content.find(`.target${type}`).html(`<ul class="${listClassName}">${list.join('')}</ul>`);
   } else {
      pc.$.content.find(`.target${type}`).html( pc.noSelectHtml() );
   }
}

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   イベント
//
////////////////////////////////////////////////////////////////////////////////////////////////////

/*
##################################################
   メニューボタン
##################################################
*/
setMenuButtonEvents() {
   const pc = this;

   // 表示設定など
   pc.$.content.find('.operationMenuButton').on('click', function( e ){
      if ( pc.tableLoading ) {
         e.preventDefault();
         return false;
      }

      const $button = $( this ),
            type = $button.attr('data-type');
      switch( type ) {
         case 'setting':
            pc.settingOpen();
            break;
         case 'operationToggle':
            pc.$.content.toggleClass('operationTimelineHide');
            break;
         case 'preset':
            pc.presetSaveOpen();
            break;
      }
   });

   // ホスト・パラメータ選択モーダル
   pc.$.content.find('.selectButton').on('click', function( e ){
      if ( pc.tableLoading ) {
         e.preventDefault();
         return false;
      }

      const $button = $( this ),
            type = $button.attr('data-type');

      switch( type ) {
         case 'host':
            $button.prop('disabled', true );
            pc.hostSelectOpen().then(function(select){
               $button.prop('disabled', false );
               if ( select ) {
                  pc.select.host = select;
                  pc.targetListHtml('Host', select, pc.select.mode === 'host');
                  pc.setParameterTables();
               }
               pc.parameterSetButtonCheck();
            });
            break;
         case 'parameter':
            $button.prop('disabled', true );
            pc.parameterSelectOpen().then(function(select){
               $button.prop('disabled', false );
               if ( select ) {
                  pc.select.parameter = select;
                  pc.targetListHtml('Parameter', select );
                  pc.setParameterTables();
               }
               pc.parameterSetButtonCheck();
            });
            break;
      }

   });

   // ホスト・パラメータクリアボタン
   pc.$.content.find('.clearButton').on('click', function( e ){
      if ( pc.tableLoading ) {
         e.preventDefault();
         return false;
      }

      const $button = $( this ),
            type = $button.attr('data-type');

      switch( type ) {
         case 'host':
            pc.select.host = [];
            pc.select.mainHost = '';
            pc.targetListHtml('Host', pc.select.host, pc.select.mode === 'host');
            break;
         case 'parameter':
            pc.select.parameter = [];
            pc.targetListHtml('Parameter', pc.select.parameter );
            break;
      }

      setTimeout( function(){pc.parameterSetButtonCheck()},1);
   });

   // パラメータメニュー
   pc.$.param.on('click', '.parameterMenuButton', function(){
      const
      $button = $( this ),
      type = $button.attr('data-type');

      switch( type ) {
         case 'print': {
            const
            darkmodeFlag = ( pc.$.body.is('.darkmode') )? true: false,
            $thema = $('#thema'),
            themaHref = $thema.attr('href');

            // テーマ：ダークモードの場合一旦解除する
            if ( darkmodeFlag ) {
               pc.$.body.removeClass('darkmode');
               $thema.attr('href', '');
            }
            pc.$.body.addClass('parameterPrint');

            window.print();

            if ( darkmodeFlag ) {
               pc.$.body.addClass('darkmode');
               $thema.attr('href', themaHref );
            }
            pc.$.body.removeClass('parameterPrint');

            } break;
         case 'excel':
            $button.prop('disabled', true );
            pc.outputExcel().then(function(){
               $button.prop('disabled', false );
            }).catch(function(){
               alert( getMessage.FTE11050 );
            });
            break;
      }
   });
}
/*
##################################################
   選択イベント
##################################################
*/
setSelectEvents() {
   const pc = this;

   // 初期値
   pc.select.mode = 'host';

   // モード変更
   pc.$.content.find('.modeSelect').on('change', function( e ){
      pc.select.mode = $( this ).val();

      // 選択状態をリセット
      pc.select.operation = [];
      pc.select.mainHost = '';
      pc.select.mainOperation = '';

      pc.updateHostList();

      // オペレーションリストを更新する
      pc.operationListCheckChange();
      pc.operationGroupCheckStatusUpdate();
      pc.parameterSetButtonCheck();
   });

   // 読み込み中は無効化
   pc.$.content.find('.modeSelect').on('click', function( e ){
      if ( pc.tableLoading ) {
         e.preventDefault();
         return false;
      }
   });

   // メインホスト選択
   pc.$.content.find('.targetHost').on('click', '.targetSelectHost', function( e ){
      if ( pc.tableLoading ) {
         e.preventDefault();
         return false;
      }

      pc.select.mainHost = $( this ).val();
      pc.setParameterTables();
      pc.parameterSetButtonCheck();
   });

   // オペレーション選択
   pc.$.content.find('.operationTimelineOperationList').on('click', '.operationTimelineCheckbox', function( e ){
      if ( pc.tableLoading ) {
         e.preventDefault();
         return false;
      }

      pc.select.operation = [];
      pc.$.content.find('.operationTimelineCheckbox:checked').each(function(){
         const id = fn.cv( $( this ).val(), '');
         pc.select.operation.push( id )
      });
      if ( pc.select.mode === 'operation' && pc.select.operation.length ) {
         pc.select.mainOperation = pc.select.operation[0];
         pc.setParameterTables();
      }

      pc.operationGroupCheckStatusUpdate();
      pc.parameterSetButtonCheck();
   });

   // パラメータ表示
   pc.$.content.find('.parameterSetButton').on('click', function( e ){
      if ( pc.tableLoading ) return false;

      const $button = $( this );
      $button.prop('disabled', true );
      pc.setParameterTables().then(function(){
         $button.prop('disabled', false );
      });
   });
}
/*
##################################################
   選択ホストリスト更新
##################################################
*/
updateHostList() {
   const pc = this;
   pc.targetListHtml('Host', pc.select.host, pc.select.mode === 'host');
}
/*
##################################################
   選択パラメータリスト更新
##################################################
*/
updateParameterList() {
   const pc = this;
   pc.targetListHtml('Parameter', pc.select.parameter );
}
/*
##################################################
   パラメータ表示設定オープン
##################################################
*/
settingOpen() {
   const pc = this;

   if ( pc.tableLoading ) return false;

   return new Promise(function( resolve ){

      // 縦横切替
      const directionChange = function() {
         if ( pc.table && pc.table.length ) {
            pc.tableLoading = true;
            for ( const table of pc.table ) {
               table.option.parameterDirection = pc.select.tableDirection;
               table.resetTable();
            }
         }
      };

      // ラジオボタン初期値チェック
      const radioChecked = function( type, value ) {
         if ( pc.select[ type ] === value ) {
            return { checked: 'checked'};
         } else {
            return {};
         }
      };

      // モーダルHTML
      const html = ``
      + `<div class="commonSection">`
         + `<div class="commonTitle">${getMessage.FTE00090}</div>`
         + `<div class="commonBody">`
            + `<p class="commonParagraph">`
               + getMessage.FTE00101
            + `</p>`
            + `<ul class="commonRadioList">`
               + `<li class="commonRadioItem">${fn.html.radioText('ts_direction', 'horizontal', 'tableDirection', 'tableDirectionHorizontal', radioChecked('tableDirection', 'horizontal'), getMessage.FTE00092 )}</li>`
               + `<li class="commonRadioItem">${fn.html.radioText('ts_direction', 'vertical', 'tableDirection', 'tableDirectionVertical', radioChecked('tableDirection', 'vertical'), getMessage.FTE00091 )}</li>`
            + `</ul>`
         + `</div>`;
      + `</div>`;

      const funcs = {
         ok: function(){
            // 項目表示方向
            pc.select.tableDirection = $body.find('.ts_direction:checked').val();
            directionChange();

            modal.close();
            modal = null;

            pc.tableSetCheck().then(function(){
               pc.tableItemWidthAlign();
               resolve();
            });
         },
         cancel: function(){
            modal.close();
            modal = null;
            resolve();
         }
      };

      const config = {
         mode: 'modeless',
         position: 'center',
         header: {
             title: getMessage.FTE11046
         },
         footer: {
             button: {
                 ok: { text: getMessage.FTE10038, action: 'positive', className: 'dialogPositive',  style: `width:200px`},
                 cancel: { text: getMessage.FTE10043, action: 'normal'}
             }
         }
      };
      let modal = new Dialog( config, funcs );
      modal.open( html );

      const $body = modal.$.dbody;

      // 変更があったら反映ボタンを活性化
      $body.find('input').on('change', function(){
         modal.buttonPositiveDisabled( false );
      });
   });
}

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   オペレーションタイムライン
//
////////////////////////////////////////////////////////////////////////////////////////////////////

/*
##################################################
   オペレーションタイムラインHTML
##################################################
*/
operationTimeLineHtml() {
   const pc = this;

   if ( !pc.info.operation ) {
      return ``
      + `<div class="operationTimeline">`
         + `<div class="commonMessage">`
         + `</div>`
      + `</div>`;
   }

   const list = pc.info.operation.sort(function( a, b ){
      a = ( a.last_run_date )? a.last_run_date: a.scheduled_date_for_execution;
      b = ( b.last_run_date )? b.last_run_date: b.scheduled_date_for_execution;
      return a.localeCompare( b );
   });

   const
   length = list.length,
   start = new Date( ( list[0].last_run_date )? list[0].last_run_date: list[0].scheduled_date_for_execution ),
   end = new Date( ( list[ length - 1 ].last_run_date )? list[ length - 1 ].last_run_date: list[ length - 1 ].scheduled_date_for_execution );

   // 範囲を広げる
   start.setDate( start.getDate() - 1 );
   end.setDate( end.getDate() + 7 );

   const
   startDate = new Date( fn.date( start, 'yyyy/MM/dd 00:00:00.000') ),
   endDate =  new Date( fn.date( end, 'yyyy/MM/dd 23:59:59.999') ),
   period = endDate - startDate,
   periodDate = period / 86400000;

   // 日時リスト
   const
   monthData = [],
   dateData = [],
   blockData = [];

   let month, date, monthColspan = 0;
   for ( let i = 0; i < periodDate; i++ ) {
      const getYear = start.getFullYear(),
            getMonth = start.getMonth() + 1,
            getDate = start.getDate();

      // 月
      if ( month !== getMonth ) {
         if ( monthData[ monthData.length - 1] ) {
            monthData[ monthData.length - 1].colspan = monthColspan;
            monthColspan = 0;
         }
         monthData.push({ date: getYear + "/" + getMonth });
      }
      monthColspan++;

      // 日
      dateData.push( { date: getDate } );
      blockData.push({});

      start.setDate( getDate + 1 );
      month = getMonth;
      date = getDate;
   }
   if ( monthData[ monthData.length - 1] && !monthData[ monthData.length - 1].colspan ) {
      monthData[ monthData.length - 1].colspan = monthColspan;
   }

   // HTML
   const tr = function( list, className ){
      const td = [];
      for ( const item of list ) {
         const colspan = ( item.colspan )? ` colspan="${item.colspan}"`: ``,
               text = ( item.date )? `<div class="operationTimeLineDateInner">${item.date}</div>`: ``;
         td.push(`<td class="operationTimeLineDateTd"${colspan}>${text}</td>`);
      }
      return `<tr class="operationTimeLineDateTr ${className}">${td.join('')}</tr>`;
   };
   const dateHtml = `<table class="operationTimeLineDateTable">`
   + tr( monthData, `operationTimeLineDateMonth`)
   + tr( dateData, `operationTimeLineDateDate`)
   + tr( blockData, `operationTimeLineDateBlock`)
   + `</table>`;

   // オペレーションリスト
   const operationHtml = [];
   for ( let i = 0; i < length; i++ ) {
      const ope = list[i];
      if ( !ope.skip ) ope.skip = false;
      if ( ope.skip === false ) {
         const 
         date = ( ope.last_run_date )? ope.last_run_date: ope.scheduled_date_for_execution,
         name = fn.cv( ope.operation_name, '', true ),
         id = fn.cv( ope.operation_id, '', true ),
         time = new Date( date ).getTime() - startDate,
         ratio = time / period * 100,
         idName = `operationTimeline_${id}`,
         blockList = [];

         // 次のオペレーションがn時間以内だったら重ねる
         const n = 1 * 3600000;
         let j = 1;
         const checkTime = function(){
            const nextOpe = list[ i + j ];
            if ( nextOpe ) {
               const nextDate = ( nextOpe.last_run_date )? nextOpe.last_run_date: nextOpe.scheduled_date_for_execution;

               // 比較
               const
               a = new Date( date ).getTime(),
               b = new Date( nextDate ).getTime();
               if ( b - a <= n ) {
                  
                  blockList.push(nextOpe);
                  nextOpe.skip = true;
                  j++;
                  checkTime();
               }

            }
         };
         checkTime();

         if ( !blockList.length ) {
         operationHtml.push(``
            + `<li class="operationTimelineOperationItem" style="left:${ratio}%">`
               + `<div class="operationTimelineOperation">`
                  + `<input type="checkbox" class="operationTimelineCheckbox" id="${idName}" name="operationTimelineCheckbox" value="${id}">`
                  + `<label for="${idName}" class="operationTimelineLabel">`
                     + `<div class="operationTimelineOperationName">${name}</div>`
                  + `</label>`
               + `</div>`
            + `</li>`);
         } else {
            blockList.unshift(ope);
            const blockHtml = [], blockLength = blockList.length;
            for ( const block of blockList ) {
               const
               blockName = fn.cv( block.operation_name, '', true ),
               blockId = fn.cv( block.operation_id, '', true ),
               blockIdName = `operationTimeline_${blockId}`;
               blockHtml.push( ``
               + `<li class="operationTimelineOperationBlockItem">`
                  + `<div class="operationTimelineOperation">`
                     + `<input type="checkbox" class="operationTimelineCheckbox operationTimelineGroupCheckbox" id="${blockIdName}" name="operationTimelineCheckbox" value="${blockId}">`
                     + `<label for="${blockIdName}" class="operationTimelineLabel">`
                        + `<div class="operationTimelineOperationName">${blockName}</div>`
                     + `</label>`
                  + `</div>`
               + `</li>`)
            }
            operationHtml.push(``
            + `<li class="operationTimelineOperationItem operationTimelineOperationGroupItem" style="left:${ratio}%">`
               + `<div class="operationTimelineOperationGroup">`
                  + `<button class="operationTimelineOperationBlockButton">`
                     + `<div class="operationTimelineOperationName operationTimelineOperationGroupName">${blockLength}${getMessage.FTE11045}</div>`
                  + `</button>`
               + `</div>`
               + `<div class="operationTimelineOperationBlock">`
                  + `<ul class="operationTimelineOperationBlockList">`
                     + blockHtml.join('')
                  + `</ul>`
               + `</div>`
            + `</li>`);
         }
      }
   }

   return ``
   + `<div class="operationTimeline">`
      + '<div class="operationTimelineBody">'
         + dateHtml
         + `<ul class="operationTimelineOperationList">`
            + operationHtml.join('')
         + `</ul>`
      + `</div>`
      + `<div class="operationTimelineBar">`
         + `<div class="operationTimelineRange">`
            + `<div class="operationTimelineRangeStart"></div>`
            + `<div class="operationTimelineRangeEnd"></div>`
         + `</div>`
      + `</div>`
   + `</div>`;
}
/*
##################################################
   オペレーションタイムラインチェックタイプ変更
   type:  radio or checkbox
##################################################
*/
operationListCheckChange() {
   const pc = this;

   const checkType = ( pc.select.mode === 'host')? 'checkbox': 'radio';
   pc.$.content.find('.operationTimelineCheckbox').prop('checked', false ).attr('type', checkType );
}
/*
##################################################
   オペレーショングループチェック状態更新
##################################################
*/
operationGroupCheckStatusUpdate() {
   const pc = this;

   pc.$.content.find('.operationTimelineOperationGroupItem').each(function(){
      pc.operationGroupCheckStatus( $( this ) );
   });
}
/*
##################################################
   オペレーショングループチェック状態
##################################################
*/
operationGroupCheckStatus( $item ) {
   const check = $item.find('.operationTimelineGroupCheckbox').length,
         checked = $item.find('.operationTimelineGroupCheckbox:checked').length;
   if ( check === checked ) {
      $item.attr('data-checked', 'full');
   } else if ( checked > 0 ) {
      $item.attr('data-checked', 'some');
   } else {
      $item.attr('data-checked', 'empty');
   }
}
/*
##################################################
   オペレーションタイムラインイベント
##################################################
*/
operationTimelineEvents() {
   const pc = this;

   const $window = $( window );

   const $timeline = pc.$.content.find('.operationTimeline'),
         $body = $timeline.find('.operationTimelineBody'),
         $bar = $timeline.find('.operationTimelineBar'),
         $range = $timeline.find('.operationTimelineRange');

   const
   scaleArray = [ 1, 1.2, 1.4, 1.6, 1.8, 2, 4, 6, 8, 10, 12.5, 15, 17.5, 20, 25, 30 ],
   scaleLength = scaleArray.length;

   let scaleNum = 0;

   const setSize = function( num, offset1, offset2 ) {
      scaleNum += num;
      if ( scaleNum < 0 ) {
         scaleNum = 0;
         return;
      }
      if ( scaleNum >= scaleLength ) {
         scaleNum = scaleLength - 1;
         return;
      }

      // サイズ
      const width = $timeline.width();
      let
      newWidth = width * scaleArray[ scaleNum ],
      left = newWidth * offset1 - offset2;

      // 左右調整
      if ( left < 0 ) left = 0;
      const checkRight = newWidth - left - width;
      if ( checkRight < 0 ) left = left + checkRight;
    
      // バーサイズ
      const
      rangeWidth = width / newWidth * 100,
      rangeLeft = left / newWidth * 100;
      
      // ％
      if ( left !== 0 ) {
         left = - ( left / width * 100 );
      }
      newWidth = newWidth / width * 100;

      // css
      $body.css({
         width: newWidth + '%',
         left: left + '%'
      });
      $range.css({
         width: rangeWidth + '%',
         left: rangeLeft + '%'
      });
   };

   // 初期サイズ
   setSize( 1, 0, 0 );

   // ホイールで拡大縮小
   $timeline.on('wheel', function( e ){
      e.preventDefault();

      // 位置
      const
      timeLeft = $( this ).offset().left + 1,
      bodyLeft = $body.position().left,
      bodyWidth = $body.width(),
      offset1 = ( e.pageX - bodyLeft - timeLeft ) / bodyWidth,
      offset2 = e.pageX - timeLeft;

      // 向き
      const delta = e.originalEvent.deltaY ? - ( e.originalEvent.deltaY ) : e.originalEvent.wheelDelta ? e.originalEvent.wheelDelta : - ( e.originalEvent.detail );
      if ( delta < 0 ) {
         setSize( -1, offset1, offset2 );
      } else {
         setSize( 1, offset1, offset2 );
      }

   });

   // スクロールバー
   $range.on('pointerdown', function(downEvent){

      // 選択を解除
      getSelection().removeAllRanges();

      const type = downEvent.target.className;

      const widthCheck = function( width, max ) {
         if ( max < width ) width = max;
         if ( rageMinWidth > width ) width = rageMinWidth;
         return width;
      };

      const leftCheck = function( left, max ) {
         if ( left < 0 ) left = 0;
         if ( left > max ) left = max;
         return left;
      };

      const
      rangeWidth = $range.width(),
      barWidth = $bar.width(),
      rangeLeft = $range.position().left;

      let
      rageMinWidth = barWidth * ( 1 / scaleArray[ scaleLength - 1 ] ),
      afterWidth = rangeWidth,
      afterLeft = rangeLeft;

      const setTimePosition = function() {
         const timeWidth = 1 / ( afterWidth / barWidth ) * 100,
               timeLeft = - ( timeWidth  * ( afterLeft / barWidth ) );
         $body.css({
            width: timeWidth + '%',
            left : timeLeft + '%'
         });

         // scaleArray調整
         const num = timeWidth / 100;
         
         const index = scaleArray.findIndex(function(val){
            return val >= num;
         });
         if ( index ) scaleNum = index;
      };

      $window.on({
         'pointermove.parameterRange': function(moveEvent){
            const move = moveEvent.pageX - downEvent.pageX;
            if ( type === 'operationTimelineRangeStart') {
               afterWidth = widthCheck( rangeWidth - move, barWidth - ( barWidth - afterLeft - afterWidth ) );
               afterLeft = leftCheck( rangeLeft + move, barWidth - ( barWidth - rangeWidth - rangeLeft + rageMinWidth ) );
               $range.css({
                  left:afterLeft,
                  width: afterWidth
               });
            } else if ( type === 'operationTimelineRangeEnd') {
               afterWidth = widthCheck( rangeWidth + move, barWidth - afterLeft );
               $range.css({
                  width: afterWidth
               });
            } else {
               afterLeft = leftCheck( rangeLeft + move, barWidth - afterWidth )
               $range.css({
                  left: afterLeft
               });
            }
            setTimePosition();
         },
         'pointerup.parameterRange': function(){
            $window.off('pointermove.parameterRange pointerup.parameterRange');

            // 幅のサイズを割合に変更する
            $range.css({
               width: ( afterWidth / barWidth * 100 ) + '%',
               left: ( afterLeft / barWidth * 100 ) + '%'
            });
         }
      });

    });

    // オペレーショングループの開閉
    $timeline.find('.operationTimelineOperationBlockButton').on('click', function(){
      const $item = $( this ).closest('.operationTimelineOperationGroupItem');

      $item.addClass('operationTimelineOperationGroupItemOpen');

      $window.on('pointerdown.timelineOperationGroup', function( e ){
         if ( !$( e.target ).closest( $item  ).length ) {
            $item.removeClass('operationTimelineOperationGroupItemOpen');
            $window.off('pointerdown.timelineOperationGroup');
         }
      });
    });
}

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   選択
//
////////////////////////////////////////////////////////////////////////////////////////////////////

/*
##################################################
   パラメータ選択
##################################################
*/
parameterSelectOpen() {
   const pc = this;

   return new Promise(function( resolve ){

      const info = {
         column_group_info: {},
         column_info: {
            c1: {
               column_name: getMessage.FTE11035,
               column_name_rest: `menu_id`,
               column_type: `SingleTextColumn`,
               description: ``,
               view_item: `1`
            },
            c2: {
               column_name: getMessage.FTE11036,
               column_name_rest: `menu_group_name`,
               column_type: `SingleTextColumn`,
               description: ``,
               view_item: `1`
            },
            c3: {
               column_name: getMessage.FTE11037,
               column_name_rest: `menu_name`,
               column_type: `SingleTextColumn`,
               description: ``,
               view_item: `1`
            },
            c4: {
               column_name: getMessage.FTE11038,
               column_name_rest: `sheet_type`,
               column_type: `ParameterCollectionSheetType`,
               description: ``,
               view_item: `1`
            },
            c5: {
               column_name: getMessage.FTE11040,
               column_name_rest: `hostgroup`,
               column_type: `ParameterCollectionUse`,
               description: ``,
               view_item: `1`
            },
            c6: {
               column_name: getMessage.FTE11039,
               column_name_rest: `vertical`,
               column_type: `ParameterCollectionUse`,
               description: ``,
               view_item: `1`
            },
         },
         menu_info: {
            columns_view: [`c1`,`c2`,`c3`,`c4`,`c5`,`c6`],
            pk_column_name_rest: `menu_id`,
            sort_key: ``,
         }
      };

      const parameter = [];
      if ( pc.info.parameter_sheet ) {
         for ( const p of pc.info.parameter_sheet ) {
            parameter.push({
               parameter: p
            })
         }
      }

      const option = {
         option: {
             data: parameter
         },
         infoData: info,
         selectType: 'multi',
         select: pc.select.parameter
      }; 
 
      fn.selectModalOpen('parameterSelect', getMessage.FTE11015, 'parameterSelect', option ).then(function( result ){
         resolve( result );
      });

   });
}

/*
##################################################
   ホスト選択
##################################################
*/
hostSelectOpen() {
   const pc = this;

   return new Promise(function( resolve ){

      const info = {
         column_group_info: {},
         column_info: {
            c1: {
               column_name: getMessage.FTE11031,
               column_name_rest: `managed_system_item_number`,
               column_type: `SingleTextColumn`,
               description: ``,
               view_item: `1`
            },
            c2: {
               column_name: getMessage.FTE11032,
               column_name_rest: `host_name`,
               column_type: `SingleTextColumn`,
               description: ``,
               view_item: `1`
            },
            c3: {
               column_name: getMessage.FTE11033,
               column_name_rest: `host_dns_name`,
               column_type: `SingleTextColumn`,
               description: ``,
               view_item: `1`
            },
            c4: {
               column_name: getMessage.FTE11034,
               column_name_rest: `ip_address`,
               column_type: `SingleTextColumn`,
               description: ``,
               view_item: `1`
            }
         },
         menu_info: {
            columns_view: [`c1`,`c2`,`c3`,`c4`],
            pk_column_name_rest: `managed_system_item_number`,
            sort_key: ``,
         }
      };

      const host = [];
      if ( pc.info.host ) {
         for ( const p of pc.info.host ) {
            host.push({
               parameter: p
            })
         }
      }

      const option = {
         option: {
             data: host
         },
         infoData: info,
         selectType: 'multi',
         select: pc.select.host
      }; 
 
      fn.selectModalOpen('hostSelect', getMessage.FTE11044, 'hostSelect', option ).then(function( result ){
         resolve( result );
      });

   });
}

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   パラメータ表示
//
////////////////////////////////////////////////////////////////////////////////////////////////////

/*
##################################################
   パラメータを表示する
##################################################
*/
setParameterTables() {
   const pc = this;

   return new Promise(function( resolve ){

      if ( !pc.checkParameterStatus() ) return resolve();

      // 選択パラメータをフィルタする
      const params = pc.info.parameter_sheet.filter(function( para ){
         return pc.select.parameter.indexOf( para.menu_id ) !== -1;
      });

      if ( params.length ) {
         pc.tableLoading = true;         

         // すでにTableが作成済みの場合Workerを終了する
         if ( pc.table && pc.table.length ) {
            for ( const table of pc.table ) {
               table.worker.terminate();
            }
         }

         pc.table = [];
         pc.tableCount = 0;

         // RESTリスト作成
         const rests = [];
         for ( const param of params ) {
            const rest = ( param.hostgroup === '0')? param.menu_name_rest: param.hg_menu_name_rest;
            rests.push( rest );
         }

         // URLリスト作成
         const urls = [];
         for ( const rest of rests ) {
            urls.push(`/menu/${rest}/info/`);
         }

         // ブロック作成
         const html = [], length = rests.length;     ;
         for ( let i = 0; i < length; i++ ) {
            const rest = rests[i];
            html.push(`<div class="parameterBlock">`
               + `<div class="parameterBlockHeader">`
                  + `<div class="parameterBlockName">${fn.cv( params[i].menu_name, '', true )}</div>`
                  + `<div class="parameterBlockMenu">${fn.html.iconButton('edit', getMessage.FTE11016, 'parameterEditOpen itaButton', { action: 'default', parameter: rest })}</div>`
               + `</div>`
               + `<div class="parameterBlockBody"></div>`
            + `</div>`);
         }

         // テーブル用共通オプション
         const
         parameterOperationList = [],
         parameterHostList = [],
         filterHostList = [];

         let targetModeName, targetName;

         if ( pc.select.mode === 'host') {
            targetModeName = getMessage.FTE11008;
            if ( pc.select.mainHost !== '-1') {
               const targetHost = pc.info.host.find(function( host ){
                  return host.managed_system_item_number === pc.select.mainHost;
               });

               targetName = ( targetHost )? fn.cv( targetHost.host_name, ''): '';
               if ( targetName !== '') {
                  parameterHostList.push( targetName );
                  parameterHostList.push( '[H]' + targetName );
                  filterHostList.push( targetName );
                  filterHostList.push( '[H]' + targetName );
               }
            } else {
               targetName = getMessage.FTE11014
            }

            // 選択オペレーション
            if ( pc.select.operation && pc.select.operation.length ) {
               for ( const operaationId of pc.select.operation ) {
                  const targetOperation = pc.info.operation.find(function( ope ){
                     return ope.operation_id === operaationId;
                  });
                  const operationName = ( targetOperation )? fn.cv( targetOperation.operation_name, ''): '';
                  if ( operationName !== '') {
                     parameterOperationList.push( operationName );
                  }
               }
            }
         } else if ( pc.select.operation ) {
            targetModeName = getMessage.FTE11017;
            const targetOperation = pc.info.operation.find(function( ope ){
               return ope.operation_id === pc.select.mainOperation;
            });

            targetName = ( targetOperation )? fn.cv( targetOperation.operation_name, ''): '';
            if ( targetName !== '') {
               parameterOperationList.push( targetName );
            }

            // 選択ホスト
            if ( pc.select.host && pc.select.host.length ) {
               for ( const hostId of pc.select.host ) {
                  const targetHost = pc.info.host.find(function( host ){
                     return host.managed_system_item_number === hostId;
                  });
                  const hostName = ( targetHost )? fn.cv( targetHost.host_name, ''): '';
                  if ( hostName !== '') {
                     parameterHostList.push( hostName );
                     parameterHostList.push( '[H]' + hostName );
                     filterHostList.push( hostName );
                     filterHostList.push( '[H]' + hostName );
                  }
               }
            }
            // ホスト無しを最後に追加
            parameterHostList.push( getMessage.FTE11014 );
         }

         pc.$.param.addClass('parameterStandby').html(``
         + `<div class="mainTarget">`
            + `<div class="mainTargetType">${targetModeName}</div>`
            + `<div class="mainTargetName">${fn.cv( targetName, '', true )}</div>`
         + `</div>`
         + `<div class="parameterMenu">`
            + `<ul class="parameterMenuList">`
               + `<li class="parameterMenuItem"><button class="parameterMenuButton" data-type="print">${getMessage.FTE11018}</button></li>`
               + `<li class="parameterMenuItem"><button class="parameterMenuButton" data-type="excel">${getMessage.FTE11049}</button></li>`
            + `</ul>`
         + `</div>`
         + `<div class="parameterArea">${html.join('')}</div>`
         + `<div class="parameterLoading nowLoading"></div>`);

         // 読み込み
         fn.fetch( urls ).then(function( result ){
            
            // テーブルセット
            for ( let i = 0; i < length; i++ ) {
               const
               tableParams = fn.getCommonParams(),
               tableOption = {
                  parameterMode: pc.select.mode,
                  parameterDirection: pc.select.tableDirection,
                  parameterSheetType: params[i].sheet_type,
                  parameterHostGroup: params[i].hostgroup,
                  parameterBundle: params[i].vertical,
                  parameterOperationList: parameterOperationList,
                  parameterHostList: parameterHostList
               }

               tableParams.menuNameRest = rests[i];

               pc.table[pc.tableCount] = new DataTable('ST_' + tableParams.menuNameRest, 'parameter', result[i], tableParams, tableOption );
               pc.$.content.find('.parameterBlockBody').eq(i).html( pc.table[pc.tableCount].setup() );
               pc.tableCount++;

               // 最大項目数

               // 最大
            }

            // パラメータ編集モーダルを開く
            pc.$.content.find('.parameterEditOpen').on('click', function(){
               const menu = $( this ).attr('data-parameter');

               const modalOption = {
                  filter: {
                     host_name: {
                        LIST: []
                     },
                     operation_name_disp: {
                        LIST: []
                     }
                  }
               };

               // フィルター
               modalOption.filter.host_name.LIST = filterHostList;
               modalOption.filter.operation_name_disp.LIST = parameterOperationList;
               fn.modalIframe( menu, getMessage.FTE11016, modalOption );
            });

            // 全てのテーブルが表示完了したら
            pc.tableSetCheck().then(function(){
               pc.tableItemWidthAlign();
               pc.$.param.removeClass('parameterStandby');
               resolve();
            });
         }).catch(function( error ){
            alert( getMessage.FTE11019 );
            pc.$.param.removeClass('parameterStandby');
            pc.tableLoading = false;
            resolve();
         });
      } else {
         pc.tableLoading = false;
         resolve();
      }
   });
}
/*
##################################################
   表示ボタンチェック
##################################################
*/
parameterSetButtonCheck() {
   const pc = this;
   pc.$.content.find('.parameterSetButton').prop('disabled', !pc.checkParameterStatus() );
}
/*
##################################################
   パラメータが表示できる状態かチェック
##################################################
*/
checkParameterStatus() {
   const pc = this;

   if ( pc.select.parameter && pc.select.parameter.length ) {
      if ( pc.select.mode === 'host') {
         if ( ( pc.select.mainHost && pc.select.mainHost !== '' ) && ( pc.select.operation && pc.select.operation.length ) ) {
            return true;
         } else {
            return false;
         }
      } else {
         if ( ( pc.select.mainOperation && pc.select.mainOperation !== '' ) ) {
            return true;
         } else {
            return false;
         }
      }
   } else {
      return false;
   }
}
/*
##################################################
   テーブル表示完了チェック
##################################################
*/
tableSetCheck() {
   const pc = this;

   return new Promise(function( resolve ){
      if ( pc.table && pc.table.length ) {
         let count = 0;
         for ( const table of pc.table ) {
            $( window ).one( table.id + '__tableReady', function(){
               count++;
               if ( pc.table.length === count ) {
                  pc.tableLoading = false;
                  resolve();
               }
            });
         }
      } else {
         pc.tableLoading = false;
         resolve();
      }
   });
}
/*
##################################################
   縦表示時、幅を揃える
##################################################
*/
tableItemWidthAlign() {
   const pc = this;

   if ( pc.select.tableDirection === 'horizontal') {
      const width = {thead:[]};
      let selectLength;
      for ( const table of pc.table ) {
         width.thead.push( table.$.thead.outerWidth() );
         
         selectLength = table.$.tbody.find('.parameterTh').length;
         for ( let i = 0; i < selectLength; i++ ) {
            const target = `parameterMainTh${i}`;
            if ( !width[target] ) width[target] = [];
            width[target].push( table.$.tbody.find(`.${target}`).outerWidth() );
         }
      }

      for ( const table of pc.table ) {
         table.$.thead.width( Math.max.apply( null, width.thead ) );

         for ( let i = 0; i < selectLength; i++ ) {
            const target = `parameterMainTh${i}`;
            table.$.tbody.find(`.${target}`).width( Math.max.apply( null, width[target] ) );
         }
      }
   }
}

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   プリセット
//
////////////////////////////////////////////////////////////////////////////////////////////////////

/*
##################################################
   プリセット初期設定
##################################################
*/
presetInit() {
   const pc = this;

   const $menu = $('#menu');
   $menu.find('.menuPageContent').html( pc.presetHtml() );
   pc.$.preset = $menu.find('.parameterPreset');

   pc.setPresetEvents();
}
/*
##################################################
   プリセットイベント
##################################################
*/
setPresetEvents() {
   const pc = this;

   pc.$.preset.on('click', '.parameterPresetButton', function( e ){
      if ( pc.tableLoading || pc.presetStandby ) {
         e.preventDefault();
         return false;
      }

      const $button = $( this ),
      id = $button.attr('data-id');
      
      pc.presetLoad( id );

   });

   pc.$.preset.on('click', '.parameterPresetItemMenuButton', function( e ){
      if ( pc.tableLoading || pc.presetStandby ) {
         e.preventDefault();
         return false;
      }

      const $button = $( this ),
            type = $button.attr('data-type'),
            id =  $button.attr('data-id');

      const target = pc.preset.find(function( pr ){
         return pr.uuid === id;
      });

      switch( type ) {
         case 'update': 
            if ( target ) pc.presetSave( target.filter_name, id, target.last_update_date_time );
            break;
         case 'rename':
            if ( target ) pc.presetSaveOpen( target.filter_name, id, target.last_update_date_time );
            break;
         case 'delete':
            pc.presetDelete( id );
            break;
      }
   });
}
/*
##################################################
   プリセットリスト読み込み
##################################################
*/
presetListLoad() {
   const pc = this;

   return new Promise(function( resolve, reject ){
      fn.fetch(`/menu/parameter_collection/filter_data/`).then(function( result ){
         pc.preset = result;
         resolve();
      }).catch(function( error ){
         window.console.error( error );
         alert( error );
         reject();
      });
   });
}
/*
##################################################
   プリセット削除
##################################################
*/
presetDelete( uuid ) {
   const pc = this;

   return new Promise(function( resolve ){
      let process = fn.processingModal( getMessage.FTE11020 );
      pc.presetStandby = true;
      fn.fetch(`/menu/parameter_collection/filter_data/${uuid}`, null, `DELETE`).then(function(){
         // リストを読み込みなおす
         pc.presetListLoad().then(function(){
            pc.updatePresetList();
            process.close();
            process = null;
            pc.presetStandby = false;
            resolve();
         });
      }).catch(function( error ){
         if ( error.message ) {
            alert( error.message );
         } else {
            window.console.error( error );
         }
         process.close();
         process = null;
         pc.presetStandby = false;
         resolve();
      });
   });
}
/*
##################################################
   プリセット保存
##################################################
*/
presetSave( name = '', uuid = '', date = '') {
   const pc = this;

   return new Promise(function( resolve, reject ){
      const data = {
         uuid: uuid,
         filter_name: name,
         filter_json: fn.jsonStringify( pc.select ),
         last_update_date_time: date
      };
      let process = fn.processingModal( getMessage.FTE11021 );
      pc.presetStandby = true;
      fn.fetch(`/menu/parameter_collection/filter_data/`, null, `POST`, data ).then(function(){
         // リストを読み込みなおす
         pc.presetListLoad().then(function(){
            pc.updatePresetList();
            process.close();
            process = null;
            pc.presetStandby = false;
            resolve();
         });
      }).catch(function( error ){
         if ( error.message ) {
            alert( error.message );
         } else {
            window.console.error( error ); 
         }
         process.close();
         process = null;
         pc.presetStandby = false;
         reject();
      });
   });
}
/*
##################################################
   プリセット保存モーダル
##################################################
*/
presetSaveOpen( name = '', uuid = '', date = '') {
   const pc = this;

   if ( pc.tableLoading ) return false;

   return new Promise(function( resolve ){

      // モーダルHTML
      const html = ``
      + `<div class="commonSection">`
         + `<div class="commonBody">`
            + `<table class="commonInputTable">`
               + `<tr class="commonInputTr">`
                  + `<th class="commonInputTh">`
                     + `<div class="commonInputTitle">${getMessage.FTE00171}</div>`
                  + `</th><td class="commonInputTd">`
                     + fn.html.inputText('editorFileName', name, 'editorFileName')
                  + `</td>`
               + `</tr>`
            + `</table>`
         + `</div>`;
      + `</div>`;

      const funcs = {
         ok: function(){
            pc.presetSave( $input.val(), uuid, date ).then(function(){
               modal.close();
               modal = null;
               resolve();
            }).catch(function(){

            });
         },
         cancel: function(){
            modal.close();
            modal = null;
            resolve();
         }
      };

      const
      title = ( uuid === '')? getMessage.FTE11022: getMessage.FTE11023,
      button = ( uuid === '')? getMessage.FTE11024: getMessage.FTE11025;

      const config = {
         mode: 'modeless',
         position: 'center',
         header: {
             title: title
         },
         footer: {
             button: {
                 ok: { text: button, action: 'positive', className: 'dialogPositive',  style: `width:200px`},
                 cancel: { text: getMessage.FTE10043, action: 'normal'}
             }
         }
      };
      let modal = new Dialog( config, funcs );
      modal.open( html );

      const $body = modal.$.dbody;

      // 変更があったら反映ボタンを活性化
      const $input = $body.find('.editorFileName');
      $input.on('input', function(){
         if ( $( this ).val() !== '') {
            modal.buttonPositiveDisabled( false );
         } else {
            modal.buttonPositiveDisabled( true );
         }
      });
   });
}
/*
##################################################
   プリセット読み込み
##################################################
*/
presetLoad( id ) {
   const pc = this;

   const preset = pc.preset.find(function(pre){
      return pre.uuid === id;
   });

   if ( preset ) {
      pc.select = fn.jsonParse( preset.filter_json );

      pc.updateParameterList();
      pc.updateHostList();
      pc.operationListCheckChange();

      // モード
      pc.$.content.find('.modeSelect').val([pc.select.mode]);

      // オペレーション
      const $check = pc.$.content.find('.operationTimelineCheckbox');

      if ( pc.select.operation ) {
         const $checked = $check.filter(function(){
            return pc.select.operation.indexOf( $( this ).attr('value') ) !== -1;
         })
         $checked.prop('checked', true );
      }

      pc.operationGroupCheckStatusUpdate();
      pc.setParameterTables();
      pc.parameterSetButtonCheck();
   }
}
/*
##################################################
   プリセットリスト更新
##################################################
*/
updatePresetList() {
   const pc = this;

   pc.$.preset.find('.parameterPresetListWrap').html( pc.presetListHtml() );
}
/*
##################################################
   List HTML
##################################################
*/
presetListHtml() {
   const pc = this;

   const html = [];
   for ( const preset of pc.preset ) {
      const name = fn.cv( preset.filter_name, '', true );
      html.push(``
      + `<li class="parameterPresetItem">`
         + `<div class="prameterPresetItemName">`
            + `<button class="parameterPresetButton" data-id="${preset.uuid}">${name}</button>`
         + `</div>`
         + `<div class="prameterPresetItemMenu">`
            + `<ul class="parameterPresetItemMenuList">`
               + `<li class="parameterPresetItemMenuItem">${fn.html.iconButton('update01', '', 'parameterPresetItemMenuButton popup', { id: preset.uuid, type: 'update',title: getMessage.FTE11026 })}</li>`
               + `<li class="parameterPresetItemMenuItem">${fn.html.iconButton('edit', '', 'parameterPresetItemMenuButton popup', { id: preset.uuid, type: 'rename',title: getMessage.FTE11027 })}</li>`
               + `<li class="parameterPresetItemMenuItem">${fn.html.iconButton('cross', '', 'parameterPresetItemMenuButton popup', { id: preset.uuid, type: 'delete',title: getMessage.FTE11028 })}</li>`
            + `</ul>`
         + `</div>`
      + `</li>`);
   }

   if ( html.length ) {
      return ``
      + `<ul class="parameterPresetList">`
         + html.join('')
      + `</ul>`;
   } else {
      return `<div class="noPresetData">${getMessage.FTE11029}</div>`
   }
}
/*
##################################################
   HTML
##################################################
*/
presetHtml() {
   const pc = this;
   
   return ``
   + `<div class="parameterPreset">`
      + `<div class="parameterPresetHeader">`
         + `${fn.html.icon('menuList')} ${getMessage.FTE11030}`
      + `</div>`
      + `<div class="parameterPresetBody">`
         + `<div class="parameterPresetListWrap">`
            + pc.presetListHtml()
         + `</div>`
      + `</div>`
   + `</div>`;
}

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Excel出力
//
////////////////////////////////////////////////////////////////////////////////////////////////////

outputExcel() {
   const pc = this;

   return new Promise(function( resolve, reject ){
      try {
         // ExcelJS ワークブック作成
         const workbook = new ExcelJS.Workbook();

         // セル幅調整値（エクセルのセル幅）
         const cellWidthRatio = 0.125;

         pc.$.param.find('.parameterBlock').each(function(){
            const $block = $( this );

            // シート作成
            const sheetName = $block.find('.parameterBlockName').text().substring( 0, 31 );
            const worksheet = workbook.addWorksheet( sheetName );

            const rowsLength = $block.find('.table').find('.tr').length;

            // 行情報作成
            const rows = [], merges = [], headers = [], groups = [],
            subHeaders = [], blanks = [], width = [], values = [], sepalateValues = [];

            // classでセルを判定（タイプごとにスタイルを分ける）
            const setStylePosition = function( $cell, row, col ) {
               if ( $cell.is('.parameterTh')) subHeaders.push([ row, col ]);
               if ( $cell.is('.tHeadTh')) {
                  if ( $cell.is('.tHeadGroup') ) {
                     groups.push([ row, col ]);
                  } else if ( !$cell.is('.parameterTheadTh') ) {
                     headers.push([ row, col ]);
                  }
               }
               if ( $cell.is('.tBodyTd')) {
                  if ( $cell.is('.parameterBlankTd')) {
                     blanks.push([ row, col ]);
                  } else if ( $cell.parent('.tBodyTr').is('.parameterSeparateTr') ) {
                     sepalateValues.push([ row, col ]);
                  } else {
                     values.push([ row, col ]);
                  }
               }
            };

            // 幅をセット
            const setWidth = function( width ) {
               return { width: Math.floor( width * cellWidthRatio * 10 ) / 10 };
            };

            let maxRow = 0, maxCol = 0;

            $block.find('.tr').each(function( r ){
               let startCol = 1, startRow = 1, endCol = 1, endRow = 1;
               let colNum = 0, rowNum = 0;

               $( this ).find('.th,.td').each(function( c ){
                  const $cell = $( this ), text = $cell.text();

                  // 縦横で別処理
                  if ( pc.select.tableDirection === 'vertical') {
                     // 縦 --------------------------------------------------
                     const
                     row = r,
                     rowspan = ( $cell.attr('rowspan') )? Number( $cell.attr('rowspan') ): 1,
                     colspan = ( $cell.attr('colspan') )? Number( $cell.attr('colspan') ): 1;

                     if ( maxRow < r ) maxRow = r;
                     if ( maxCol < c ) maxCol = c;

                     for ( let i = 0; i < rowspan; i++ ) {
                        for ( let j = 0; j < colspan; j++ ) {
                           if ( !rows[ row + i ] ) rows[ row + i ] = [];
                           while ( rows[ row + i ][ colNum + j ] !== undefined ) {
                              colNum++;
                           }
                           if ( i === 0 && j === 0 ) {
                              rows[ row + i ][ colNum + j ] = text;
                              startCol = endCol = colNum + j + 1;
                              startRow = endRow = row + i + 1;
                              setStylePosition( $cell, startRow, startCol );
                              if ( colspan === 1 ) width[ colNum + j ] = setWidth( $cell.outerWidth() );
                           } else {
                              rows[ row + i ][ colNum + j ] = '';
                              endCol = colNum + j + 1;
                              endRow = row + i + 1;
                           }
                        }
                     }
                     colNum += colspan;
                  } else {
                     // 横 --------------------------------------------------
                     const
                     col = r,
                     colspan = ( $cell.attr('rowspan') )? Number( $cell.attr('rowspan') ): 1,
                     rowspan = ( $cell.attr('colspan') )? Number( $cell.attr('colspan') ): 1;

                     if ( maxRow < c ) maxRow = c;
                     if ( maxCol < r ) maxCol = r;

                     for ( let i = 0; i < rowspan; i++ ) {
                        if ( !rows[ i + rowNum ] ) rows[ i + rowNum ] = [];
                        while ( rows[ i + rowNum ][ col ] !== undefined ) {
                           rowNum++;
                        }
                        for ( let j = 0; j < colspan; j++ ) {
                           if ( i === 0 && j === 0 ) {
                              rows[ i + rowNum ][ col + j ] = text;
                              startCol = endCol = col + j + 1;
                              startRow = endRow = rowNum + i + 1;
                              setStylePosition( $cell, startRow, startCol );
                              if ( colspan === 1 ) width[ col + j ] = setWidth( $cell.outerWidth() );
                           } else {
                              rows[ i + rowNum ][ col + j ] = '';
                              endCol = col + j + 1;
                              endRow = rowNum + i + 1;
                           }
                        }
                     }
                     rowNum += rowspan;
                  }
                  if ( startRow !== endRow || startCol !== endCol ) {
                     merges.push([ startRow, startCol, endRow, endCol ]);
                  }
               });
            });

            // 行追加
            const addrowLength = rows.length;
            for ( let i = 0; i < addrowLength; i++ ) {
               worksheet.addRow( rows[i] );
            }

            // セル結合
            const mergeLength = merges.length;
            for ( let i = 0; i < mergeLength; i++ ) {
               worksheet.mergeCells( merges[i][0], merges[i][1], merges[i][2], merges[i][3] );
            }

            // スタイル
            const setStyle = function( row, col, color, bgColor, horizontal, type ) {
               const cell = worksheet.getCell( row, col );
               cell.fill = {
                  type: 'pattern',
                  pattern: 'solid',
                  fgColor: { argb: 'FF' + bgColor }
               };
               cell.font = {
                  color: { argb: 'FF' + color },
                  size: '9'
               };
               cell.alignment = {
                  vertical: 'middle', horizontal: horizontal
               };

               const border = {};
               if ( type === undefined ) {
                  border.top = {style:'thin'};
                  border.left = {style:'thin'};
                  border.bottom = {style:'thin'};
                  border.right = {style:'thin'};
               } else if ( type === 'value') {
                  border.bottom = {style:'dotted'};
                  border.right = {style:'hair'};
               } else if ( type === 'sepalateValue') {
                  border.bottom = {style:'dotted'};
                  border.right = {style:'thin'};
               }
               cell.border = border;
            };

            for ( const cell of headers ) {
               setStyle( cell[0], cell[1], 'FFFFFF', '4D6B91', ( pc.select.tableDirection === 'vertical' )? 'center': 'right');
            }

            for ( const cell of groups ) {
               setStyle( cell[0], cell[1], 'FFFFFF', '335581', 'left');
            }

            for ( const cell of subHeaders ) {
               setStyle( cell[0], cell[1], '002B62', 'E5EAEF', ( pc.select.tableDirection === 'vertical' )? 'left': 'center');
            }

            for ( const cell of blanks ) {
               setStyle( cell[0], cell[1], '000000', 'F2F2F2', 'left', 'sepalateValue');
            }

            for ( const cell of values ) {
               setStyle( cell[0], cell[1], '000000', 'FFFFFF', 'left', 'value');
            }

            for ( const cell of sepalateValues ) {
               setStyle( cell[0], cell[1], '000000', 'FFFFFF', 'left', 'sepalateValue');
            }

            // 最終行のボーダーを直線に変更
            for ( let i = 1; i <= maxCol + 1; i++ ) {
               worksheet.getCell( maxRow + 1, i ).border.bottom = { style: 'thin'};
            }

            // 幅
            worksheet.columns = width;
            
         });

         workbook.xlsx.writeBuffer().then(function( uint8Array ){
            const targetName = pc.$.param.find('.mainTargetName').text();
            let fileName = 'parameter_' + targetName;

            if ( fn.typeof( pc.select.parameter ) === 'array' && pc.select.parameter.length ) {
               const parameterNames = [];
               for ( const id of pc.select.parameter ) {
                  const data = pc.info.parameter_sheet.find(function( parameter ){
                     return parameter.menu_id === id;
                  });
                  parameterNames.push( data.menu_name );
               }
               fileName += `(${parameterNames.join('_')})`;
            }
            fileName = fileName.replace(/\s+/g, '-');
            fileName = fileName.substring( 0, 200 );
            fn.download('exceljs', uint8Array, fileName );
            
            setTimeout( function(){ resolve(); }, 1000 );
         });
      } catch ( error ) {
         reject();
      }
   });
}

}