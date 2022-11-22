////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Exastro IT Automation / ui.js
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

class CommonUi {

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
constructor() {
    const ui = this;
    
    // jQuery cache
    ui.$ = {};
    ui.$.window = $( window ),
    ui.$.body = $('body'),
    ui.$.container = $('#container');
    ui.$.header = $('#header');
    ui.$.menu = $('#menu');
    ui.$.content = $('#content');
    
    // Common parameter
    ui.params = fn.getCommonParams();
    ui.params.menuNameRest = fn.getParams().menu;
    
    // Set common events
    fn.setCommonEvents();
    
    // 結果を入れる
    ui.rest = {};
}
/*
##################################################
   画面初期設定
##################################################
*/
init() {
    const ui = this;
    
    // UIモード
    if ( window.parent === window ) {
        ui.$.container.addClass('windowMode');
        
        // サイドメニュー開閉チェック
        const sideMenu = fn.storage.get('sideMenuClose');
        if ( sideMenu === true ) {
            ui.$.container.addClass('menuClose');
        }
        
        // サイドメニューイベントのセット
        ui.setSideMenuEvents();
        
        // Session storageにデータがある場合は先に表示する
        ui.storageLang = fn.storage.get('lang', 'session');
        ui.storageMenuGroups = fn.storage.get('restMenuGroups', 'session');
        ui.storagePanel = fn.storage.get('restPanel', 'session');
        ui.storageUser = fn.storage.get('restUser', 'session');
        
        if ( ui.storageLang && ui.storageMenuGroups && ui.storagePanel && ui.storageUser ) {
            ui.lang = ui.storageLang;
            fn.loadAssets({type:'script', url:`/_/ita/js/messageid_${ui.lang}.js`, id: 'lang'}).then(function(){
                ui.rest.menuGroups = ui.storageMenuGroups;
                ui.rest.panel = ui.storagePanel;
                ui.rest.user = ui.storageUser;
                
                ui.setSideMenu();
                ui.headerMenu();
            });
        }
        
    } else {
        ui.$.container.addClass('iframeMode');
        
        const iframeMode = fn.getParams().iframeMode;
        if ( iframeMode ) {
            ui.$.container.attr('data-iframeMode', iframeMode );
        }
    }    
}
/*
##################################################
   UI set
##################################################
*/
setUi() {
    const ui = this;
    
    const set = function() {
        // iframeで読み込まれていないか？
        if ( window.parent === window ) {
            ui.mode = 'window';
            ui.getSideMenuData();
        } else {
            ui.mode = 'iframe';
        }
        ui.setMenu();
    }

    // 言語ファイル
    const $lang = $('#lang'),
          tmpLang = CommonAuth.getLanguage();
    if ( ui.lang !== tmpLang ) {
        fn.storage.set('lang', tmpLang, 'session');
        ui.lang = tmpLang;
        
        if ( $lang.length ) $('#lang').remove();
        fn.loadAssets({type:'script', url:`/_/ita/js/messageid_${ui.lang}.js`, id: 'lang'}).then(function(){
            set();
        });
    } else {
        set();
    }
}

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   サイドメニュー、トピックパス
//
////////////////////////////////////////////////////////////////////////////////////////////////////

/*
##################################################
   サイドメニュー各種イベントをセット
##################################################
*/
setSideMenuEvents() {
    const ui = this;
    
    ui.$.menu.on('click', '.menuTabLink', function( e ){
        e.preventDefault();
        
        const $link = $( this );
        ui.menuTab = $link.attr('href');
        ui.$.menu.find('.tabOpen').removeClass('tabOpen').removeAttr('tabindex');
        ui.$.menu.find(`.menuTabLink[href="${ui.menuTab}"]`).addClass('tabOpen').attr('tabindex', -1 );
        $( ui.menuTab ).addClass('tabOpen');
        fn.storage.set('menuTab', ui.menuTab );
        
    });
    
    // Menu toggle
    ui.$.menu.on('click', '.menuToggleButton', function(){
        if ( !ui.$.container.is('.menuClose') ) {
            fn.storage.set('sideMenuClose', true );
            ui.$.container.addClass('menuClose');
        } else {
            fn.storage.remove('sideMenuClose');
            ui.$.container.removeClass('menuClose');
            ui.$.menu.find('.cloneMenu').remove();
        }
    });
    
    // Menu accordion
    ui.$.container.on('click', '.menuSecondaryToggleButton', function( e ){
        e.preventDefault();
        
        const $button = $( this ),
              menuId = $button.attr('data-id'),
              $menu = $button.next('.menuSecondaryList');
        
        if ( $button.is('.open') ) {
            $button.removeClass('open');
            $menu.stop(0,0).slideUp( ui.menuSecondaryToggleSpeed );
            if ( ui.menuSecondary.indexOf( menuId ) !== -1 ) {
                ui.menuSecondary.splice( ui.menuSecondary.indexOf( menuId ), 1 );
            }
        } else {
            $button.addClass('open');
            $menu.stop(0,0).slideDown( ui.menuSecondaryToggleSpeed );
            if ( ui.menuSecondary.indexOf( menuId ) === -1 ) {
                ui.menuSecondary.push( menuId );
            }
        }
        fn.storage.set('subMenuOpen', ui.menuSecondary );
    });
    
    // メニューグループクリック時、メニュー一覧表示
    ui.$.menu.on('click', '.menuGroupLink', function( e ){
        e.preventDefault();
        
        const $link = $( this ),
              num = $link.attr('data-num'),
              id = $link.attr('data-id'),
              list = ui.menuGroupList[ num ],
              width = ui.$.menu.outerWidth();
        
        if ( list.id === id && !$link.is('.subGroupMenuOpen') ) {
            if ( $link.is('.cloneLink') ) {
                $link.closest('.menuItem').trigger('pointerleave');
            }
            
            ui.$.menu.find(`.menuGroupLink[data-id="${id}"]`).addClass('subGroupMenuOpen');
        
            const $html = $(`<div class="menuGroupSub" style="left:${width}px">`
            + `<div class="menuHeader"></div>`
            + `<div class="menuBody">`
                +`<div class="menuBlock">`
                    + ui.sideMenuBody( list.menu_group_name, null, ui.menuSub( list.menus ), ui.rest.panel[ id ] )
                + `</div>`
            + `</div></div>`);
            
            ui.$.container.append( $html );
            ui.$.window.on('mousedown.groupSub', function( e ){
                if ( !$( e.target ).closest('.menuGroupSub, .subGroupMenuOpen').length ) {
                    ui.$.menu.find('.subGroupMenuOpen').removeClass('subGroupMenuOpen');
                    $html.animate({ left: '-100%'}, 300, function(){
                        $( this ).remove();
                    });
                    ui.$.window.off('mousedown.groupSub');
                }
            });
        }
    });
    
    // メニューが閉じている場合、サイドメニュータブを表示
    ui.$.menu.on('pointerenter', '.menuHeader', function( e ){
        if ( ui.$.container.is('.menuClose') ) {
            const $menu = $( this ),
                  $cloneHeader = $menu.find('.menuHeaderInner').clone();
            
            $cloneHeader.addClass('cloneMenu');
            
            $menu.prepend( $cloneHeader );
            
            ui.$.menu.find('.menuHeader').on('pointerleave', function( e ){
                ui.$.menu.find('.menuHeader').off('pointerleave');
                $cloneHeader.remove();
            });
        }
    });
    
    ui.$.menu.on('pointerenter', '.menuItem', function( e ){
        if ( ui.$.container.is('.menuClose') ) {
            const $item = $( this ),
                  $link = $item.find('.menuLink');
            
            if ( $link.is('.subGroupMenuOpen') || $link.is('.current') ) return;
            
            const $cloneLink = $link.clone();
            
            $cloneLink.addClass('cloneLink');
            
            $item.prepend( $cloneLink );
            
            $item.on('pointerleave', function( e ){
                $item.off('pointerleave click');
                $cloneLink.remove();
            });
        }
    });
}
/*
##################################################
   サイドメニューデータの取得
##################################################
*/
getSideMenuData() {
    const ui = this;
    
    // REST API URLs
    const restApiUrls = [
        '/user/menus/',
        '/user/menus/panels/'
    ];

    fn.fetch( restApiUrls ).then(function( result ){
        if ( result ) {
            // 変更があればSession storageにセット            
            if ( JSON.stringify( result[0].menu_groups ) !== JSON.stringify( ui.storageMenuGroups ) || JSON.stringify( result[1] ) !== JSON.stringify( ui.storagePanel ) ) {
                ui.rest.menuGroups = result[0].menu_groups;
                ui.rest.panel = result[1];
                fn.storage.set('restMenuGroups', ui.rest.menuGroups, 'session');
                fn.storage.set('restPanel', ui.rest.panel, 'session');
                
                // 変更したデータサイドメニューを再セット
                ui.setSideMenu();
            }

        }
    }).catch(function( error ){
        window.console.error( error );
        if ( error.message !== 'Failed to fetch') {
            fn.gotoErrPage( error.message );
        }
    });
}
/*
##################################################
   サイドメニューをセット
##################################################
*/
setSideMenu() {
    const ui = this;
    
    // Secondary(Child) menu
    ui.menuSecondaryToggleSpeed = 300;
    ui.menuSecondary = fn.storage.get('subMenuOpen');
    if ( !ui.menuSecondary ) ui.menuSecondary = [];
    
    // メニュー構造作成
    ui.createMenuGroupList();
    
    const menus = [
        { name: 'menuGroup', icon: 'menuGroup', title: getMessage.FTE10002 },
        { name: 'menuMain', icon: 'menuList', title: ui.currentGroup.title },
        /*{ name: 'menuFavorite', icon: 'star'},
        { name: 'menuHistory', icon: 'history'}*/
    ];
    
    // Menu tab
    ui.menuTab = fn.storage.get('menuTab');
    if ( !ui.menuTab || ui.menuTab === '#menuGroup') ui.menuTab = '#menuMain';
    
    const tab = [],
          body = [];
    
    for ( const menu of menus ) {
        tab.push(`<li class="menuTabItem"><a class="menuTabLink popup darkPopup" title="${menu.title}" href="#${menu.name}"><span class="icon icon-${menu.icon}"></span></a></li>`);
        body.push(`<div class="menuBlock" id="${menu.name}">${ui[ menu.name ]()}</div>`);
    }
    
    ui.$.menu.html(`
    <div class="menuHeader">
        <div class="menuHeaderInner">
            <div class="menuTab">
                <ul class="menuTabList">
                    ${tab.join('')}
                </ul>
            </div>
            <div class="menuToggle">
                <button class="menuToggleButton"><span class="icon icon-arrow01_left"></span></button>
            </div>
        </div>
        <div class="menuCloseMark">${fn.html.icon('ellipsis')}</div>
    </div>
    <div class="menuBody">
        ${body.join('')}
    </div>`);
    
    // 最初に開いているタブをセット
    ui.$.menu.find(`.menuTabLink[href="${ui.menuTab}"]`).addClass('tabOpen').attr('tabindex', -1 );
    ui.$.menu.find( ui.menuTab ).addClass('tabOpen');
    
    // トピックパスをセット
    ui.topicPath();
    
    // メインメニューの場合メニューグループ一覧を表示する
    if ( !ui.params.menuNameRest ) {
        ui.mainMenu();
    }
}
/*
##################################################
   サイドメニューデ階層データの作成
##################################################
*/
createMenuGroupList() {
    const ui = this;
    
    // メニューグループリストの作成    
    ui.menuGroupList = [];
    ui.currentMenuGroupList = null;
    const childs = [];
    
    // 配列のディープコピー
    const tempMenuGroups = $.extend( true, [], ui.rest.menuGroups );
    
    // 親と子を分ける
    for ( const menuGroup of tempMenuGroups ) {
        if ( menuGroup.parent_id === null ) {
            ui.menuGroupList.push( menuGroup );
        } else {
            childs.push( menuGroup );
        }
    }
    
    // 親に子を追加（開いているメニュー・各メインメニュー・カレントチェック）
    for ( const parent of ui.menuGroupList ) {
        for ( const child of childs ) {
            if ( parent.id === child.parent_id ) {
                child.main_menu_rest = null;
                if ( child.menus && child.menus.length ) {
                    ui.dispSeqSort( child.menus );
                    if ( child.menus[0].menu_name_rest ) {
                         child.main_menu_rest = child.menus[0].menu_name_rest;
                    }
                    if ( ui.menuSecondary.indexOf( child.id ) !== -1 ) {
                        child.secondary_open_flag = true;
                    }
                    for ( const menu of child.menus ) {
                        if ( ui.params.menuNameRest === menu.menu_name_rest ) {
                            child.secondary_open_flag = true;
                            ui.currentMenuGroupList = parent;
                        }
                    }
                }
                parent.menus.push( child );
            }
        }
        ui.dispSeqSort( parent.menus );
  
        parent.main_menu_rest = null;
        let subRest = null;
        for ( const menu of parent.menus ) {
            if ( menu.menu_name_rest && parent.main_menu_rest === null ) {
                parent.main_menu_rest = menu.menu_name_rest;
            } else if ( menu.menus && menu.menus.length && menu.menus[0].menu_name_rest ) {
                subRest = menu.menus[0].menu_name_rest;
            }
            if ( ui.currentMenuGroupList === null && ui.params.menuNameRest === menu.menu_name_rest ) {
                ui.currentMenuGroupList = parent;
            }
        }
        if ( !parent.main_menu_rest && subRest ) parent.main_menu_rest = subRest;
    }
    ui.dispSeqSort( ui.menuGroupList );
    
    if ( ui.currentMenuGroupList ) {
        const menuGroupName = fn.cv( ui.currentMenuGroupList.menu_group_name, '', true ),
              menuGroupPanel = fn.cv( ui.rest.panel[ ui.currentMenuGroupList.id ], ''),
              menuGroupLink = fn.cv( ui.currentMenuGroupList.main_menu_rest, '');
        ui.currentGroup = {
            title: menuGroupName,
            panel: menuGroupPanel,
            link: menuGroupLink
        };
    } else {
        ui.currentGroup = {
            title: getMessage.FTE10001
        };
    }
}
/*
##################################################
  パネルイメージを返す
##################################################
*/
getPanelImage( title, icon, panel ) {
    if ( icon ) {
        return `<span class="icon icon-${icon}"></span>`;
    } else {
        return ( fn.cv( panel, false ) )?
        `<img class="menuTitleIconImage" src="data:;base64,${panel}" alt="${title}">`:
        `<img class="menuTitleIconImage" src="/_/ita/imgs/icon_default.png" alt="${title}">`;
    }
}
/*
##################################################
   サイドメニュー各HTML
##################################################
*/
sideMenuBody( title, icon, list, panel ) {
    const ui = this;
    
    const iconImage = ui.getPanelImage( title, icon, panel );
    
    return `
    <div class="menuTitle">
        <div class="menuTitleIcon">
            ${iconImage}
        </div>
        <div class="menuTitleText">
            ${title}
        </div>
    </div>
    <nav class="menuNavi">
        <ul class="menuList">
            ${list}
        </ul>
    </nav>
    ${ui.serachBlock()}`;
}
/*
##################################################
   表示しているメニューリストの作成
##################################################
*/
menuMain() {
    const ui = this;    
    
    if ( ui.params.menuNameRest && ui.currentMenuGroupList ) {
        const item = function( m, secondary ){
            const menuName = fn.cv( m.menu_name, '', true ),
                  menuRest = fn.cv( m.menu_name_rest, ''),
                  attr = [`href="${ui.params.path}?menu=${menuRest}"`],
                  className = ['menuLink'];
            if ( secondary ) className.push('menuSecondaryLink');
            if ( menuRest === ui.params.menuNameRest ) {
                className.push('current');
                attr.push('tabindex="-1"');
                ui.currentPage = {
                    title: menuName,
                    name: menuRest
                };
                if ( secondary ) {
                    ui.currentSecondaryGroup = secondary;
                }
            }
            return `<li class="menuItem"><a class="${className.join(' ')}" ${attr.join(' ')}>${menuName}</a></li>`;
        };

        const list = function( menus, secondary ) {
            const htmlArray = [];
            for ( const menu of menus ) {
                if ( menu.menus ) {
                    // Secondary
                    const secondaryGroupName = fn.cv( menu.menu_group_name, '', true ),
                          secondaryGroupLink = fn.cv( menu.main_menu_rest, ''),
                          secondaryClassName = ['menuSecondaryToggleButton'],
                          listStyle = [],
                          menuID = fn.cv( menu.id, '');
                    if ( menu.secondary_open_flag ) {
                        secondaryClassName.push('open');
                        listStyle.push('display:block');
                    }
                    const secondaryHTML = ``
                    + `<li class="menuItem">`
                        + `<div class="menuSecondary">`
                            +`<button class="${secondaryClassName.join(' ')}" data-id="${menuID}">`
                                + `${secondaryGroupName}<span class="menuSecondaryToggleIcon"></span>`
                            + `</button>`
                            + `<ul class="menuList menuSecondaryList" style="${listStyle.join(';')}">`
                                + list( menu.menus, { title: secondaryGroupName, link: secondaryGroupLink })
                            + `</ul>`
                        + `</div>`
                    + `</li>`;
                    htmlArray.push( secondaryHTML );
                } else {
                    htmlArray.push( item( menu, secondary ) );
                }
            }
            return htmlArray.join('');
        };

        return ui.sideMenuBody( ui.currentGroup.title, null, list( ui.currentMenuGroupList.menus ), ui.currentGroup.panel );
    } else {
        // メインメニュー用リスト
        const dashboard = `<li class="menuItem"><a class="menuLink current" href="${ui.params.path}">DashBoard</a></li>`;
        ui.currentPage = {
            title: getMessage.FTE10001
        };
        return ui.sideMenuBody( ui.currentPage.title, null, dashboard );
    }
}
/*
##################################################
   Sub main list
##################################################
*/
menuSub( subMenuList ) {
    const ui = this;    

    const item = function( m, secondary ){
        const menuName = fn.cv( m.menu_name, '', true ),
              menuRest = fn.cv( m.menu_name_rest, ''),
              attr = [`href="${ui.params.path}?menu=${menuRest}"`],
              className = ['menuLink'];
        if ( secondary ) className.push('menuSecondaryLink');
        return `<li class="menuItem"><a class="${className.join(' ')}" ${attr.join(' ')}>${menuName}</a></li>`;
    };

    const list = function( menus, secondary ) {
        const htmlArray = [];
        for ( const menu of menus ) {
            if ( menu.menus ) {
                // Secondary
                const secondaryGroupName = fn.cv( menu.menu_group_name, '', true ),
                      secondaryGroupLink = fn.cv( menu.main_menu_rest, ''),
                      secondaryClassName = ['menuSecondaryToggleButton'],
                      listStyle = [],
                      menuID = fn.cv( menu.id, '');
                if ( menu.secondary_open_flag ) {
                    secondaryClassName.push('open');
                    listStyle.push('display:block');
                }
                const secondaryHTML = ``
                + `<li class="menuItem">`
                    + `<div class="menuSecondary">`
                        +`<button class="${secondaryClassName.join(' ')}" data-id="${menuID}">`
                            + `${secondaryGroupName}<span class="menuSecondaryToggleIcon"></span>`
                        + `</button>`
                        + `<ul class="menuList menuSecondaryList" style="${listStyle.join(';')}">`
                            + list( menu.menus, { title: secondaryGroupName, link: secondaryGroupLink })
                        + `</ul>`
                    + `</div>`
                + `</li>`;
                htmlArray.push( secondaryHTML );
            } else {
                htmlArray.push( item( menu, secondary ) );
            }
        }
        return htmlArray.join('');
    };

    return list( subMenuList );
}
/*
##################################################
   Menu group
##################################################
*/
menuGroup() {
    const ui = this;
    
    const list = [],
          length = ui.menuGroupList.length;
    
    for ( let i = 0; i < length; i++ ) {
        const menuGroup = ui.menuGroupList[i];
        if ( menuGroup.parent_id === null ) {
            const title = fn.cv( menuGroup.menu_group_name, '', true ),
                  id =  fn.cv( menuGroup.id, ''),
                  panel = ui.getPanelImage( title, null, ui.rest.panel[ id ] );
            list.push(`<li class="menuItem"><a class="menuGroupLink menuLink" data-id="${id}" data-num="${i}" href="${ui.params.path}?menu=${menuGroup.main_menu_rest}"><span class="menuGroupPanel">${panel}</span><span class="menuGroupTitle">${title}</span></a></li>`);
        }
    }
    
    return ui.sideMenuBody( getMessage.FTE10002, 'menuGroup', list.join(''));
}
/*
##################################################
   Favorite menu
##################################################
*/
menuFavorite(){
    return this.sideMenuBody( getMessage.FTE10003, 'star', '');
}
/*
##################################################
   History menu
##################################################
*/
menuHistory(){
    return this.sideMenuBody( getMessage.FTE10004, 'history', '');
}
/*
##################################################
   Search menu
##################################################
*/
serachBlock() {
    return `
    <!--<div class="menuSearch">
        <input class="menuSearchText" data-search="menuMain" placeholder="${getMessage.FTE10007}">
    </div>-->`;
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
   Topic path
##################################################
*/
topicPath() {
    const ui = this;
    const topics = [],
          title = [ ui.currentPage.title ];
    if ( ui.currentGroup.link ) {
        topics.push({ href: ui.params.path, title: getMessage.FTE10001 });
        topics.push({ href: `${ui.params.path}?menu=${ui.currentGroup.link}`, title: ui.currentGroup.title });
        title.push( ui.currentGroup.title );
    }
    if ( ui.currentSecondaryGroup ) {
        topics.push({ href: `${ui.params.path}?menu=${ui.currentSecondaryGroup.link}`, title: ui.currentSecondaryGroup.title });
        title.push( ui.currentSecondaryGroup.title );
    }
    
    const list = [];
    if ( topics.length ) {
        for ( const topic of topics ) {
            list.push(`<li class="topichPathItem"><a class="topichPathLink" href="${topic.href}">${topic.title}</a></li>`);
        }
        list.push(`<li class="topichPathItem"><span class="topichPathCurrent">${ui.currentPage.title}</span></li>`);
    } else {
        list.push(`<li class="topichPathItem"><span class="topichPathCurrent">${getMessage.FTE10001}</span></li>`);
    }
    
    const html = `
    <ol class="topichPathList">
        ${list.join('')}
    </ol>`;
    
    ui.$.header.find('.topicPath').html( html );
    
    title.push('Exastro IT Automation');
    document.title = title.join(' / ');
}

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   メニュー（コンテンツ）
//
////////////////////////////////////////////////////////////////////////////////////////////////////

/*
##################################################
   メニューをセット
##################################################
*/
setMenu() {
    const mn = this;
      
    const urls = ['/user/'];
    
    if ( mn.params.menuNameRest ) urls.push(`/menu/${mn.params.menuNameRest}/info/`);

    fn.fetch( urls ).then(function( result ){
        // ユーザ情報に変更があれば更新
        if ( JSON.stringify( result[0] ) !== JSON.stringify( mn.storageUser ) ) { 
            mn.rest.user = result[0];
            mn.headerMenu();
            
            fn.storage.set('restUser', mn.rest.user, 'session');
        }
        
        if ( mn.params.menuNameRest ) {
            mn.info = result[1];
            mn.title = fn.cv( mn.info.menu_info.menu_name, '', true );
            mn.sheetType();
        }
    }).catch(function( error ){
        window.console.error( error );
        if ( error.message !== 'Failed to fetch') {
            fn.gotoErrPage( error.message );
        }
    });
}
/*
##################################################
   シートタイプごとにページを表示する
##################################################
*/
sheetType() {
    const mn = this;
    if ( mn.info ) {

        // 権限フラグ
        mn.flag = fn.editFlag( mn.info.menu_info );
        
        // シートタイプ
        mn.type = mn.info.menu_info.sheet_type;

        // sheet_typeによって分ける
        switch ( mn.type ) {
            case undefined:
            break;
            // 0 - 4 : 標準メニュー
            case '0': case '1': case '2': case '3': case '4':
                mn.$.content.addClass('tabContent');
                mn.defaultMenu('standard');
            break;
            // 5 - 6 : 参照用メニュー
            case '5': case '6':
                mn.$.content.addClass('tabContent');
                mn.defaultMenu('reference');
            break;
            // 11 : 作業実行
            case '11':
                mn.$.content.addClass('defaultContent');
                mn.executeMenu();
            break;
            // 12 : 作業状態確認
            case '12':
                mn.$.content.addClass('tabContent');
                mn.operationStatusMenu();
            break;
            // 13 : メニュー定義・作成
            case '13':
                mn.createMenu();
            break;
            // 14 : Conductorクラス編集
            case '14':
                mn.condcutor('edit');
            break;
            // 16 : Conductor作業確認
            case '16':
                mn.condcutor('confirmation');
            break;
            // 17 : 比較実行
            // 19 : メニュー作成実行
            default:
            // メインメニュー
            //mn.mainMenu();
        }
    } else {
        //mn.mainMenu();
    }
}

/*
##################################################
   Header menu
##################################################
*/
headerMenu() {
    const mn = this;
    
    const html = `
    <ul class="headerMenuList">
        <li class="userInfomation headerMenuItem">${mn.userInfo()}</li>
    </ul>`;
    
    mn.$.header.find('.headerMenu').html( html );
    
    mn.$.header.find('.headerMenuButton').on('click', function(){
        const $button = $( this ),
              $userInfo = $button.next('.userInfoContainer');
        
        if ( $userInfo.is('.open') ) {
            $userInfo.removeClass('open');
        } else {
            $userInfo.addClass('open');
            mn.$.window.on('pointerdown.userInfo', function( e ){
                if ( !$( e.target ).closest('.userInfomation, .modalOverlay').length ) {
                    $userInfo.removeClass('open');
                    mn.$.window.off('pointerdown.userInfo');
                }
            });
        }
    });
    
    // ワークスペース切替
    mn.$.header.find('.userInfoWorkspaceButton').on('click', function(){
        const workspaceId =  $( this ).attr('data-workspace');
        window.location.href = fn.getWorkspaceChangeUrl( workspaceId );        
    });
    
    // ログアウト
    mn.$.header.find('.userInfoMenuButton').on('click', function(){
        const $button = $( this ),
              type = $button.attr('data-type');
        switch ( type ) {
            case 'version':
                $button.prop('disabled', true );
                fn.fetch('/version/').then(function( result ){
                    mn.checkVersion( result ).then(function(){
                        
                        $button.prop('disabled', false );
                    });
                });
            break;
            case 'logout':
                const url = document.location.href;
                CommonAuth.logout(url);
            break;
        }
    });
}
/*
##################################################
   User infomation
##################################################
*/
userInfo() {
    const mn = this,
          $user = mn.$.header.find('.userIndo'),
          name = fn.cv( mn.rest.user.user_name, '', true ),
          id = fn.cv( mn.rest.user.user_id, '', true ),
          roles = fn.cv( mn.rest.user.roles, []),
          workspaces = fn.cv( mn.rest.user.workspaces, []);
    
    const workspaceList = [];
    
    for ( const work in workspaces ) {
        workspaceList.push(`<li class="userinfoWorkspaceItem">`
            + `<button class="userInfoWorkspaceButton" data-workspace="${work}">${workspaces[work]}</button>`
        + `</li>`);
    }
    
    const roleList = [];
    for ( const role of roles ) {
        roleList.push(`<li class="userinfoRoleItem">`
            + role
        + `</li>`);
    }
    
    return `
    <button class="headerMenuButton">
        <span class="icon icon-user"></span>
        <span class="userName"><span class="userNameText">${name}</span></span>
    </button>
    <div class="userInfoContainer">
        <div class="userInfoBlock userInfo">
            <div class="userInfoBody">
                <div class="userInfoName">${name}</div>
                <div class="userInfoId">${id}</div>
            </div>
        </div>
        <div class="userInfoBlock userInfoWorkspace">
            <div class="userInfoTitle">${fn.html.icon('workspace')} ${getMessage.FTE10005}</div>
            <div class="userInfoBody">
                <ul class="userInfoWorkspaceList">
                    ${workspaceList.join('')}
                </ul>
            </div>
        </div>
        <div class="userInfoBlock userInfoRole">
            <div class="userInfoTitle">${fn.html.icon('role')} ${getMessage.FTE10006}</div>
            <div class="userInfoBody">
                <ul class="userInfoRoleList">
                    ${roleList.join('')}
                </ul>
            </div>
        </div>
        <div class="userInfoBlock userInfoMenu">
            <div class="userInfoBody">
                <ul class="userInfoMenuList">
                    <li class="userInfoMenuItem">
                        ${fn.html.button( fn.html.icon('note') + getMessage.FTE10033, ['userInfoMenuButton', 'itaButton'], { type: 'version', action: 'default'})}
                    </li>
                    <li class="userInfoMenuItem">
                        ${fn.html.button( fn.html.icon('logout') + getMessage.FTE10034, ['userInfoMenuButton', 'itaButton'], { type: 'logout', action: 'positive'})}
                    </li>
                </div>
            </div>
        </div>
    </div>`;
}
/*
##################################################
   バージョン確認
##################################################
*/
checkVersion( version ) {
    const driverList = [];
    for ( const item of version.installed_driver ) {
        driverList.push(`<li class="driverItem">${fn.html.icon('plus')} ${item}</li>`);
    }
    
    const versionHtml = `<div class="versionContainer">
        <div class="versionLogo"><img class="versionLogoImg" src="/_/ita/imgs/logo.svg" alt="Exastro IT Automation"></div>
        <div class="versionNumber"><span class="versionNumberWrap">Version: ${version.version}</span></div>
        <div class="installedDriver">
            <div class="driverTitle">${getMessage.FTE10035}</div>
            <ul class="driverList">
                ${driverList.join('')}
            </ul>
        </div>
    </div>`;
    
    return new Promise( function( resolve ){
        fn.alert('Exastro IT Automation', versionHtml ).then(function(){
            resolve();
        });
    });
}

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Content general
//
////////////////////////////////////////////////////////////////////////////////////////////////////

/*
##################################################
   Ready
##################################################
*/
onReady() {
    this.$.container.addClass('ready');
}
/*
##################################################
   Common container
##################################################
*/
commonContainer( title, info, body, menuFlag = true ) {
    return `
    <div class="contentInner">
        <div class="contentHeader">
            <h1 class="contentTitle"><span class="contentTitleInner">${title}</span></h1>
            <p class="contentMenuInfo">
                <span class="contentMenuInfoInner">${info}</span>${( menuFlag )? `
                <button class="contentMenuInfoButton button popup" title="${getMessage.FTE00079}">
                    <span class="inner">${fn.html.icon('ellipsis_v')}<span></button>`: ``}
            </p>
        </div>
        <div class="contentBody">
            ${body}
        </div>
    </div>`;
}
/*
##################################################
   Content tab
##################################################
*/
contentTab( list ) {
    const mn = this;
    
    const tab = [],
          section = [];
    
    for ( const item of list ) {
        const listClass = ['contentMenuItem'];
        if ( item.className ) listClass.push( item.className );
        if ( item.view === false ) listClass.push('contentMenuItemToggle hidden');
        tab.push(`<li class="${listClass.join(' ')}"><a class="contentMenuLink" href="#${item.name}">`
        + `<span class="contentMenuLinkTab"><span class="contentMenuLinkInner">${item.title}</span></span></a></li>`);
        
        const sectionBody = ( item.type !== 'blank' )? mn[item.name](): '';
        section.push( mn.contentSection( sectionBody, item.name ) );
    }
    
    return `
    <div class="contentMenu">
        <ul class="contentMenuList">
            ${tab.join('')}
        </ul>
    </div>
    ${section.join('')}`;
}
/*
##################################################
   Content section
##################################################
*/
contentSection( body, id ) {
    return `<section class="section"${( id )?` id="${id}"`: ``}><div class="sectionBody">${(body)?body:``}</div></section>`;
}
/*
##################################################
   Content tab event
##################################################
*/
contentTabEvent( openTab = '#dataList') {
    const mn = this;
    
    mn.$.content.find(`.contentMenuLink[href="${openTab}"]`).addClass('tabOpen').attr('tabindex', -1 );
    mn.$.content.find( openTab ).addClass('tabOpen');
    
    mn.$.content.find('.contentMenuLink').on('click', function( e ){
        e.preventDefault();
        
        const $link = $( this ),
              tab = $link.attr('href');
        mn.$.content.find('.tabOpen').removeClass('tabOpen').removeAttr('tabindex');
        $link.addClass('tabOpen').attr('tabindex', -1 );
        $( tab ).addClass('tabOpen');
    });
}
// 指定のタブを開く
contentTabOpen( openTab ) {
    const mn = this;
    
    const $link = mn.$.content.find(`.contentMenuLink[href="${openTab}"]`);
    
    mn.$.content.find('.tabOpen').removeClass('tabOpen').removeAttr('tabindex');
    $link.addClass('tabOpen').attr('tabindex', -1 );
    
    mn.$.content.find(`.contentMenuLink[href="${openTab}"]`).addClass('tabOpen').attr('tabindex', -1 );
    mn.$.content.find( openTab ).addClass('tabOpen');
}

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   メインメニュー
//
////////////////////////////////////////////////////////////////////////////////////////////////////

mainMenu() {
    const mn = this;

    const list = [],
          length = mn.menuGroupList.length;
    
    for ( let i = 0; i < length; i++ ) {
        const menuGroup = mn.menuGroupList[i];
        if ( menuGroup.parent_id === null ) {
            const title = fn.cv( menuGroup.menu_group_name, '', true ),
                  id =  fn.cv( menuGroup.id, ''),
                  panel = mn.getPanelImage( title, null, mn.rest.panel[ id ] );
            
            list.push(`<li class="dashboardMenuGroupItem"><a class="dashboardMenuGroupLink" href="${mn.params.path}?menu=${menuGroup.main_menu_rest}"><span class="dashboardMenuGroupPanel">${panel}</span><span class="dashboardMenuGroupTitle">${title}</span></a></li>`);
        }
    }
    
    const html = `<ul class="dashboardMenuGroupList">${list.join('')}</ul>`;
    
    mn.$.content.html( mn.commonContainer( 'DashBoard', getMessage.FTE00077, html, false ) );  

    mn.onReady();
}

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   標準メニュー
//
////////////////////////////////////////////////////////////////////////////////////////////////////

defaultMenu( sheetType ) {
    const mn = this;
    
    const contentTab = [{ name: 'dataList', title: getMessage.FTE10008, type: 'blank' }];
    // 履歴タブ
    if ( mn.flag.history ) {
        contentTab.push({ name: 'changeHistory', title: getMessage.FTE10009, type: 'blank' });
    }
    contentTab.push({ name: 'dataDownload', title: getMessage.FTE10010 });

    const menuInfo = fn.cv( mn.info.menu_info.menu_info, '', true );
    
    mn.$.content.html( mn.commonContainer( mn.title, menuInfo, mn.contentTab( contentTab ) ) );
    mn.contentTabEvent('#dataList');
    
    // 一覧
    const $dataList = mn.$.content.find('#dataList'),
          initSetFilter = fn.getParams().filter,
          option = { sheetType: sheetType };
    if ( initSetFilter !== undefined ) option.initSetFilter = initSetFilter;
    mn.mainTable = new DataTable('MT', 'view', mn.info, mn.params, option );
    $dataList.find('.sectionBody').html( mn.mainTable.setup() );
    
    // 履歴ボディ
    if ( mn.flag.history ) {
        const $history = mn.$.content.find('#changeHistory');
        mn.historyTable = new DataTable('HT', 'history', mn.info, mn.params );
        $history.find('.sectionBody').html( mn.historyTable.setup() );
        
        // 一覧 個別履歴ボタン
        mn.mainTable.$.container.on('click', '.tBodyRowMenuUi', function(){
            const $button = $( this ),
                  uuid = $button.attr('data-id');

            mn.contentTabOpen('#changeHistory');
            $history.find('.tableHistoryId').val( uuid ).trigger('input');

            mn.historyTable.$.header.find('.itaButton').prop('disabled', false );
            mn.historyTable.workStart('filter');
            mn.historyTable.workerPost('history', uuid );
        });
    }
    
    // 全件ダウンロード・ファイル一括登録
    const $download = mn.$.content.find('#dataDownload');
    $download.find('.operationButton').on('click', function(){
        const $button = $( this ),
              type = $button.attr('data-type');
        
        const downloadFile = function( type, url, fileName ){
            $button.prop('disabled', true );
            
            fn.fetch( url ).then(function( result ){
                fn.download( type, result, fileName );                
            }).catch(function( error ){
                fn.gotoErrPage( error.message );
            }).then(function(){
                fn.disabledTimer( $button, false, 1000 );
            });
        };
        
        switch ( type ) {
            case 'allDwonloadExcel': {
                $button.prop('disabled', true );
                
                fn.fetch(`/menu/${mn.params.menuNameRest}/filter/count/`).then(function( result ){
                    const limit = mn.info.menu_info.xls_print_limit;
                    if ( limit && mn.info.menu_info.xls_print_limit < result ) {
                        alert( getMessage.FTE00085( result, limit) );
                    } else {
                        downloadFile('excel', `/menu/${mn.params.menuNameRest}/excel/`, mn.title + '_all');
                    }
                }).catch(function( error ){
                    fn.gotoErrPage( error.message );
                }).then(function(){
                    fn.disabledTimer( $button, false, 1000 );
                });
            } break;
            case 'allDwonloadJson':
                downloadFile('json', `/menu/${mn.params.menuNameRest}/filter/`, mn.title + '_all');
            break;
            case 'newDwonloadExcel':
                downloadFile('excel', `/menu/${mn.params.menuNameRest}/excel/format/`, mn.title + '_format');
            break;
            case 'excelUpload':
                mn.fileRegister( $button, 'excel');
            break;
            case 'jsonUpload':
                mn.fileRegister( $button, 'json');
            break;
            case 'allHistoryDwonloadExcel':
                downloadFile('excel', `/menu/${mn.params.menuNameRest}/excel/journal/`, mn.title + '_journal');
            break;
        }
    });
    
    mn.setCommonEvents();
    mn.onReady();
}
/*
##################################################
   タブ：全件ダウンロード・ファイル一括登録
##################################################
*/
dataDownload() {
    const mn = this;
    
    const list = [
        { title: getMessage.FTE10011, description: getMessage.FTE10012, type: 'allDwonloadExcel'},
        { title: getMessage.FTE10013, description: getMessage.FTE10014, type: 'allDwonloadJson'}
    ];
    
    if ( mn.flag.insert ) {
        list.push({ title: getMessage.FTE10015, description: getMessage.FTE10016, type: 'newDwonloadExcel'});
    } 
    
    list.push({ title: getMessage.FTE10023, description: getMessage.FTE10024, type: 'allHistoryDwonloadExcel'});
    
    if ( mn.flag.edit ) {
        list.push({ title: getMessage.FTE10017, description: getMessage.FTE10018, type: 'excelUpload', action: 'positive'});
        list.push({ title: getMessage.FTE10019, description: getMessage.FTE10020, type: 'jsonUpload', action: 'positive'});
    } else if ( mn.flag.update ) {
        list.push({ title: getMessage.FTE10017, description: getMessage.FTE10031, type: 'excelUpload', action: 'positive'});
        list.push({ title: getMessage.FTE10019, description: getMessage.FTE10032, type: 'jsonUpload', action: 'positive'});
    }
    
    const html = [];
    for ( const item of list ) {
        const attr = { type: item.type };
        if ( item.action ) attr.action = item.action;
        html.push(`<div class="operationBlock">`
            + `<div class="operationTitle">${fn.html.button( item.title, ['operationButton', 'itaButton'], attr )}</div>`
            + `<div class="operationDescription">${item.description}</div>`
        + `</div>`);
    }
    
    return html.join('');
}
/*
##################################################
   ファイル一括登録
##################################################
*/
fileRegister( $button, type ) {
    const mn = this;
    
    const fileType = ( type === 'excel')? 'base64': 'json',
          fileMime = ( type === 'excel')? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'application/json',
          restUrl = ( type === 'excel')? `excel/maintenance/`: `maintenance/all/`;
    
    // ボタンを無効
    $button.prop('disabled', true );
    
    // ファイル選択
    fn.fileSelect( fileType, null, fileMime ).then(function( selectFile ){
        const postData = ( type === 'excel')? { excel: selectFile.base64 }: selectFile.json;
        
        // 登録するか確認する
        const buttons = {
            ok: { text: getMessage.FTE10025, action: 'positive'},
            cancel: { text: getMessage.FTE10026, action: 'normal'}
        };
        
        const table = { tbody: []};
        table.tbody.push([ getMessage.FTE10027, selectFile.name ]);
        table.tbody.push([ getMessage.FTE10028, selectFile.size.toLocaleString() + ' byte']);
        
        if ( fileType === 'json') {
            try {
                table.tbody.push([ getMessage.FTE10029, selectFile.json.length.toLocaleString() ]);
            } catch( e ) {
                throw new Error( getMessage.FTE10021 );
            }
        }
        
        fn.alert( getMessage.FTE00083, fn.html.table( table, 'fileSelectTable', 1 ), 'confirm', buttons ).then( function( flag ){
            if ( flag ) {
            
                const processing = fn.processingModal( getMessage.FTE00084 );
                
                // POST（登録）
                fn.fetch(`/menu/${mn.params.menuNameRest}/${restUrl}`, null, 'POST', postData ).then(function( result ){
                    // 登録成功
                    fn.resultModal( result ).then(function(){
                        mn.contentTabOpen('#dataList');
                        mn.mainTable.changeViewMode();
                    });
                }).catch(function( error ){
                    // 登録失敗
                    fn.errorModal( error, mn.title, mn.info );
                }).then(function(){
                    // ボタンを戻す
                    fn.disabledTimer( $button, false, 1000 );
                    processing.close();
                });
            } else {
                // キャンセル
                fn.disabledTimer( $button, false, 0 );
            }
        });
    }).catch(function( error ){
        if ( error !== 'cancel') {
            alert( error );
        }
        fn.disabledTimer( $button, false, 0 );
    });
}

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   作業実行メニュー
//
////////////////////////////////////////////////////////////////////////////////////////////////////

executeMenu() {
    const mn = this;
    
    const menuInfo = fn.cv( mn.info.menu_info.menu_info, '');
    
    const initSetFilter = fn.getParams().filter,
          option = {};
    if ( initSetFilter !== undefined ) option.initSetFilter = initSetFilter;  
    
    mn.$.content.html( mn.commonContainer( mn.title, menuInfo, mn.contentSection() ) );  
    mn.setCommonEvents();
    
    fn.fetch(`/menu/${mn.params.menuNameRest}/driver/execute/info/`).then(function( result ){
        // 実行時に渡す名前のKey
        mn.params.selectNameKey = 'movement_name';
        // Main REST URL
        mn.params.restFilter = `/menu/${mn.params.menuNameRest}/driver/execute/filter/movement_list_ansible_role/`;
        mn.params.restFilterPulldown = `/menu/${mn.params.menuNameRest}/driver/execute/filter/movement_list_ansible_role/search/candidates/`;
        
        // Operation
        mn.params.operation = {
            selectNameKey: 'operation_name',
            infoData: result.operation_list,
            filter: `/menu/${mn.params.menuNameRest}/driver/execute/filter/operation_list/`,
            filterPulldown: `/menu/${mn.params.menuNameRest}/driver/execute/filter/operation_list/search/candidates/`
        };

        mn.mainTable = new DataTable('MT', 'execute', result.movement_list_ansible_role, mn.params, option );
        mn.$.content.find('.sectionBody').html( mn.mainTable.setup() ).show();
        
        mn.onReady();
    }).catch(function( error ){
        fn.gotoErrPage( error.message );
    });  
}

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   作業状態確認メニュー
//
////////////////////////////////////////////////////////////////////////////////////////////////////

operationStatusMenu() {
    const mn = this;
    
    const contentTab = [
        { name: 'operationStatus', title: getMessage.FTE00080, type: 'blank' },
        { name: 'executeLog', title: getMessage.FTE00081, type: 'blank', view: false, className: 'executeLogTab'},
        { name: 'errorLog', title: getMessage.FTE00082, type: 'blank', view: false, className: 'errorLogTab' }
    ];
    
    const menuInfo = fn.cv( mn.info.menu_info.menu_info, '');
    
    mn.$.content.html( mn.commonContainer( mn.title, menuInfo, mn.contentTab( contentTab ) ) );
    mn.setCommonEvents();
    mn.contentTabEvent('#operationStatus');
    
    const assets = [
        { type: 'js', url: '/_/ita/js/operation_status.js'},
        { type: 'css', url: '/_/ita/css/conductor.css'},
        { type: 'css', url: '/_/ita/css/operation_status.css'},
    ];
    
    fn.loadAssets( assets ).then(function(){
        const id = fn.getParams().execution_no;
        fn.createCheckOperation( mn.params.menuNameRest, id );
        
        mn.onReady();
    });
}

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Create menu
//
////////////////////////////////////////////////////////////////////////////////////////////////////

createMenu( mode ) {
    const mn = this;
    
    const assets = [
        { type: 'js', url: '/_/ita/js/create_menu.js'},
        { type: 'css', url: '/_/ita/css/editor_common.css'},
        { type: 'css', url: '/_/ita/css/create_menu.css'}
    ];
    
    fn.loadAssets( assets ).then(function(){
        const createMenu = new CreateMenu('#content', mn.rest.user );
        createMenu.setup();
        
        mn.onReady();
    });
}

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Conductor
//
////////////////////////////////////////////////////////////////////////////////////////////////////

condcutor( mode ) {
    const mn = this;
    
    const assets = [
        { type: 'js', url: '/_/ita/js/conductor.js'},
        { type: 'css', url: '/_/ita/css/editor_common.css'},
        { type: 'css', url: '/_/ita/css/conductor.css'}
    ];
    
    const getId = function(){
        if ( mode === 'confirmation') {
            return fn.getParams().conductor_instance_id;
        } else {
            return fn.getParams().conductor_class_id;
        }
    }
    const id = getId();
    if ( mode === 'edit' && id ) mode = 'view';
    
    fn.loadAssets( assets ).then(function(){
        const conductor = fn.createConductor( mn.params.menuNameRest, '#content', mode, id );
        conductor.setup();
        
        mn.onReady();
    });
}

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   common events
//
////////////////////////////////////////////////////////////////////////////////////////////////////

setCommonEvents() {
    const mn = this;
    
    const menuInfo = mn.info.menu_info;
    
    const buttons = {
        cancel: { text: '閉じる', action: 'normal'},
        //ok: { text: 'メニュー情報詳細確認', action: 'positive'}
    }
    
    mn.$.content.find('.contentHeader').find('.contentMenuInfoButton').on('click', function(){
        const menuInfoHTml = ``
        + `<div class="menuInfoContainer">`
            + `<div class="menuInfoTitle">${menuInfo.menu_name}</div>`
            + `<div class="menuInfoDescription">${fn.escape( menuInfo.menu_info, true )}</div>`;
        + `</div>`;
        fn.alert( getMessage.FTE00078, menuInfoHTml, 'confirm', buttons ).then(function( result ){
            /*
            if ( result ) {
                const filter = encodeURIComponent( JSON.stringify( {'menu_id':{NORMAL:menuInfo.menu_id}} ) );
                window.location.href = `?menu=menu_list&filter=${filter}`;
            }
            */
        });
    });
}

}