////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Exastro IT Automation / create_menu.js
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

function getParam(name, url) {
    if (!url) url = window.location.href;
    name = name.replace(/[\[\]]/g, "\\$&");
    var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
        results = regex.exec(url);
    if (!results) return null;
    if (!results[2]) return '';
    return decodeURIComponent(results[2].replace(/\+/g, " "));
}

let menuCreateUserInfo;
let nameConvertList;

class CreateMenu {
/*
##################################################
    Constructor
##################################################
*/
constructor( target, userInfo ) {
    const cm = this;

    cm.target = target;
    menuCreateUserInfo = userInfo;
}
/*
##################################################
    Setup
##################################################
*/
setup() {
    const cm = this;

    let loadMenuID = '';
    let itaEditorMode = 'new';
    let createManagementMenuID = '';

    if ( getParam('menu_name_rest') != null ){
        if ( getParam('mode') != null ){
            itaEditorMode = getParam('mode');
        } else {
            itaEditorMode = 'view';
        }
        loadMenuID = getParam('menu_name_rest');
    }
    if ( getParam('history_id') != null ){
        createManagementMenuID = getParam('history_id');
    }

    const html = `
    <div id="menu-editor" class="editor load-wait" data-editor-mode="` + itaEditorMode + `" data-load-menu-id="` + loadMenuID + `">
        <div class="editor-inner">
            <div id="menu-editor-main" class="editor-main">
                <div id="menu-editor-menu" class="editor-menu">
                    ${cm.editorOperationMenuHtml( itaEditorMode, createManagementMenuID )}
                </div>
                <div id="menu-editor-header" class="editor-header">
                    ${cm.editorMenuHtml( itaEditorMode )}
                </div>
                ${cm.editorMainHtml()}
            </div>
            <div class="eritor-panel">
                ${cm.panelContainerHtml( itaEditorMode )}
            </div>
        </div>
    </div>`;

    // 縦メニュー説明
    /*
    <div id="vertical-menu-description" class="modal-body-html">
        <div class="modal-description">
            <p class="modal-description-paragraph">縦メニューとは、同じパラメータを繰り返して定義する場合に視認性をよくするためのメニューです。<br>
            通常のメニューでは、項目数が多い場合は横長なメニューとなりますが、縦メニューでは同一項目を縦に表示して項目全体を見やすくしています。</p>
            <p class="modal-description-paragraph"><img class="modal-description-image" src="/_/ita/imgs/vertical-menu-help-jp.png" alt="通常メニューと縦メニュー"></p>
            <p class="modal-description-note">※縦メニューの場合、入力用・代入値自動登録用メニューは以下のようになります。</p>
            <table class="modal-description-note-table">
                <tr><th class="modal-description-note-cell">入力用</th><td class="modal-description-note-cell">縦メニュー</td></tr>
                <tr><th  class="modal-description-note-cell">代入値自動登録用</th><td class="modal-description-note-cell">縦メニューから通常メニュー（横表示）に自動的に変換したメニュー</td></tr>
            </table>
        </div>
    </div>
    */

    cm.$ = {};

    // HTMLセット
    $( cm.target ).html( html );

    if ( loadMenuID === ''){
        // 必要なデータの読み込み
        fn.fetch('/create/define/').then(function( result ){
            cm.init( result );
        });
    } else {
        // 必要なデータの読み込み
        fn.fetch('/create/define/' + loadMenuID).then(function( result ){
          cm.init( result );
      });
    }
}
/*
##################################################
    editorMenuHtml
##################################################
*/
editorMenuHtml( editorMode ) {
    if ( editorMode !== 'view' ){
        const jsonButton = [`<li class="editor-menu-item menu-editor-menu-li"><button class="editor-menu-button menu-editor-menu-button" data-type="jsonSave">${getMessage.FTE02021}</button></li>`];
        if ( editorMode === 'new' || editorMode === 'diversion') {
            jsonButton.unshift(`<li class="editor-menu-item menu-editor-menu-li"><button class="editor-menu-button menu-editor-menu-button" data-type="jsonRead">${getMessage.FTE02022}</button></li>`)
        }
        return `
        <div class="menu-editor-menu">
            <ul class="editor-menu-list menu-editor-menu-ul">
                ${jsonButton.join('')}
                <li class="editor-menu-separate editor-menu-item menu-editor-menu-li"><button class="editor-menu-button menu-editor-menu-button" data-type="newColumn">` + getMessage.FTE01001 + `</button></li>
                <li class="editor-menu-item menu-editor-menu-li"><button class="editor-menu-button menu-editor-menu-button" data-type="newColumnGroup">` + getMessage.FTE01002 + `</button></li>
                <li class="editor-menu-separate editor-menu-item menu-editor-menu-li"><button id="button-undo" class="editor-menu-button menu-editor-menu-button" data-type="undo">` + getMessage.FTE01003 + `</button></li>
                <li class="editor-menu-item menu-editor-menu-li"><button id="button-redo" class="editor-menu-button menu-editor-menu-button" data-type="redo">` + getMessage.FTE01004 + `</button></li>
            </ul>
        </div>`;
    }
    return '';
}
/*
##################################################
    editorMainHtml
##################################################
*/
editorMainHtml( itaEditorMode ) {
    return `
            <div id="menu-editor-body" class="editor-body editor-row-resize">
                <div id="menu-editor-edit" class="editor-block menu-editor-block">
                    <div class="editor-block-inner menu-editor-block-inner">
                        <div class="menu-table-wrapper">
                            <div class="menu-table">
                            </div>
                        </div>
                    </div>
                    <div id="column-resize"></div>
                </div>
                <div id="menu-editor-row-resize" class="editor-row-resize-bar"></div>
                <div id="menu-editor-info" class="editor-block menu-editor-block">
                    <div class="editor-block-inner">
                        <div class="editor-tab">
                            <div class="editor-tab-menu">
                                <ul class="editor-tab-menu-list">
                                    <li class="editor-tab-menu-item" data-tab="menu-editor-preview">` + getMessage.FTE01005 + `</li>
                                    <li class="editor-tab-menu-item" data-tab="menu-editor-log">` + getMessage.FTE01006 + `</li>
                                </ul>
                            </div>
                            <div class="editor-tab-contents">
                                <div id="menu-editor-preview" class="editor-tab-body">
                                    <div class="tableWrap">
                                        <table class="table">
                                            <thead class="thead"></tbody>
                                            <tbody class="tbody"></tbody>
                                        </table>
                                    </div>
                                </div>
                                <div id="menu-editor-log" class="editor-tab-body">
                                    <div class="editor-log">
                                        <table class="editor-log-table">
                                            <tbody></tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>`;
}
/*
##################################################
    panelContainerHtml
##################################################
*/
panelContainerHtml( editorMode ) {
    const panelType = {
        menuType: '',
        hostType: '',
        verticalMenu: ''
    };
    let html = '';

    if ( editorMode === 'view' ){
        html += `
        <div class="panel-group">
            <div class="panel-group-title">${getMessage.FTE01009}</div>
            <table class="panel-table">
                <tbody>
                    <tr>
                        <th class="panel-th">` + getMessage.FTE01010 + `</th>
                        <td class="panel-td"><span id="create-menu-id" class="panel-span"><span class="editorAutoInput">${getMessage.FTE01011}</span></span></td>
                    </tr>
                </tbody>
            </table>
            <hr class="panel-hr">
            <table class="panel-table">
                <tbody>
                    <tr>
                        <th class="panel-th panel-th-only">` + getMessage.FTE01012 + `</th>
                    </tr>
                    <tr>
                        <td class="panel-td"><span id="create-menu-name" class="panel-span"></span></td>
                    </tr>
                    <tr>
                        <th class="panel-th panel-th-only">` + getMessage.FTE01013 + `</th>
                    </tr>
                    <tr>
                        <td class="panel-td"><span id="create-menu-name-rest" class="panel-span"></span></td>
                    </tr>
                    <tr>
                        <th class="panel-th panel-th-only">` + getMessage.FTE01014 + `</th>
                    </tr>
                    <tr>
                        <td class="panel-td"><span id="create-menu-type" class="panel-span"></span></td>
                    </tr>
                </tbody>
            </table>
            <hr class="panel-hr">
            <table class="panel-table">
                <tbody>
                    <tr>
                        <th class="panel-th">` + getMessage.FTE01015 + `</th>
                        <td class="panel-td"><span id="create-menu-order" class="panel-span"></span></td>
                    </tr>
                    <tr class="parameter-sheet">
                        <th class="panel-th"">` + getMessage.FTE01153 + `</th>
                        <td class="panel-td"><span id="create-menu-use-host-group" class="panel-span"></span></td>
                    </tr>
                    <tr class="parameter-sheet parameter-operation">
                        <th class="panel-th"">` + getMessage.FTE01016 + `</th>
                        <td class="panel-td"><span id="create-menu-use-vertical" class="panel-span"></span></td>
                    </tr>
                    <tr>
                        <th class="panel-th">` + getMessage.FTE01017 + `</th>
                        <td class="panel-td"><span id="create-menu-last-modified" class="panel-span"><span class="editorAutoInput">${getMessage.FTE01011}</span></span></td>
                    </tr>
                    <tr>
                        <th class="panel-th">` + getMessage.FTE01018 + `</th>
                        <td class="panel-td"><span id="create-last-update-user" class="panel-span"><span class="editorAutoInput">${getMessage.FTE01011}</span></span></td>
                    </tr>
                </tbody>
            </table>
        </div>
        <div id="menu-group" class="panel-group">
            <div class="panel-group-title">${getMessage.FTE01019}</div>
            <table class="panel-table">
                <tbody>
                    <tr class="data-sheet parameter-sheet parameter-operation">
                        <th class="panel-th">` + getMessage.FTE01020 + `</th>
                        <td class="panel-td"><span id="create-menu-for-input" type="text" class="panel-span"></span></td>
                    </tr>
                    <tr class="parameter-sheet parameter-operation">
                        <th class="panel-th">` + getMessage.FTE01021 + `</th>
                        <td class="panel-td"><span id="create-menu-for-substitution" type="text" class="panel-span"></span></td>
                    </tr>
                    <tr class="parameter-sheet parameter-operation">
                        <th class="panel-th">` + getMessage.FTE01022 + `</th>
                        <td class="panel-td"><span id="create-menu-for-reference" type="text" class="panel-span"></span></td>
                    </tr>
                </tbody>
            </table>
        </div>
        <div id="unique-constraint" class="panel-group">
            <div class="panel-group-title">${getMessage.FTE01023}</div>
            <table class="panel-table">
                <tbody>
                    <tr class="data-sheet parameter-sheet parameter-operation">
                        <th class="panel-th">` + getMessage.FTE01024 + `</th>
                        <td class="panel-td"><span id="unique-constraint-list" type="text" class="panel-span"></span></td>
                    </tr>
                </tbody>
            </table>
        </div>
        <div id="permission-role" class="panel-group">
            <div class="panel-group-title">${getMessage.FTE01025}</div>
            <table class="panel-table">
                <tbody>
                    <tr class="data-sheet parameter-sheet parameter-operation">
                        <th class="panel-th">` + getMessage.FTE01026 + `</th>
                        <td class="panel-td"><span id="permission-role-name-list" type="text" class="panel-span"></span></td>
                    </tr>
                </tbody>
            </table>
        </div>
        <div id="permission-role" class="panel-group">
            <div class="panel-group-title">${getMessage.FTE01027}</div>
            <span id="create-menu-explanation" type="text" class="panel-span"></span>
        </div>
        <div id="permission-role" class="panel-group">
            <div class="panel-group-title">${getMessage.FTE01028}</div>
            <span id="create-menu-note" type="text" class="panel-span"></span>
        </div>`;
    } else if (editorMode === 'edit'){
        panelType.menuType = '1';
        panelType.hostType = '1';
        panelType.verticalMenu = 'false';
        html += `
        <div class="panel-group">
            <div class="panel-group-title">` + getMessage.FTE01009 + `</div>
            <table class="panel-table">
                <tbody>
                    <tr>
                        <th class="panel-th">` + getMessage.FTE01010 + `</th>
                        <td class="panel-td"><span id="create-menu-id" class="panel-span" data-value=""><span class="editorAutoInput">${getMessage.FTE01011}</span></span></td>
                    </tr>
                </tbody>
            </table>
            <hr class="panel-hr">
            <table class="panel-table">
                <tbody>
                    <tr title="` + getMessage.FTE01029 + `">
                        <th class="panel-th panel-th-only">${getMessage.FTE01012 + fn.html.required()}</th>
                    </tr>
                    <tr title="` + getMessage.FTE01029 + `">
                        <td class="panel-td"><input id="create-menu-name" class="panel-text" type="text"></td>
                    </tr>
                    <tr title="` + getMessage.FTE01030 + `">
                        <th class="panel-th panel-th-only">${getMessage.FTE01013 + fn.html.required()}</th>
                    </tr>
                    <tr title="` + getMessage.FTE01030 + `">
                        <td class="panel-td"><input id="create-menu-name-rest" class="panel-text" type="text"></td>
                    </tr>
                    <tr title="` + getMessage.FTE01031 + `">
                        <th class="panel-th panel-th-only">` + getMessage.FTE01014 + `</th>
                    </tr>
                    <tr title="` + getMessage.FTE01031 + `">
                        <td class="panel-td">
                            <select id="create-menu-type" class="panel-select" disabled></select>
                        </td>
                    </tr>
                </tbody>
            </table>
            <hr class="panel-hr">
            <table class="panel-table">
                <tbody>
                    <tr title="` + getMessage.FTE01032 + `">
                        <th class="panel-th">${getMessage.FTE01015 + fn.html.required()}</th>
                        <td class="panel-td"><input id="create-menu-order" class="panel-number" type="number" data-min="0" data-max="2147483647"></td>
                    </tr>
                </tbody>
            </table>
            <table class="panel-table">
                <tbody>
                    <tr class="parameter-sheet parameter-operation panel-check-tr" title="` + getMessage.FTE01154 + `">
                        <th class="panel-th">${getMessage.FTE01153}</th>
                        <td class="panel-td">
                            ${fn.html.checkboxText('panel-check', getMessage.FTE01034, 'create-menu-use-host-group', 'create-menu-use-host-group', {disabled: 'disabled'})}
                        </td>
                    </tr>
                    <tr class="parameter-sheet parameter-operation panel-check-tr" title="` + getMessage.FTE01033 + `">
                        <th class="panel-th">` + getMessage.FTE01016 + `</th>
                        <td class="panel-td">
                            ${fn.html.checkboxText('panel-check', getMessage.FTE01034, 'create-menu-use-vertical', 'create-menu-use-vertical', {disabled: 'disabled'})}
                        </td>
                    </tr>
                </tbody>
            </table>
            <table class="panel-table">
                <tbody>
                    <tr>
                        <th class="panel-th">` + getMessage.FTE01017 + `</th>
                        <td class="panel-td" colspan="3"><span id="create-menu-last-modified" class="panel-span" data-value=""><span class="editorAutoInput">${getMessage.FTE01011}</span></span></td>
                    </tr>
                    <tr>
                        <th class="panel-th">` + getMessage.FTE01018 + `</th>
                        <td class="panel-td" colspan="3"><span id="create-last-update-user" class="panel-span" data-value=""><span class="editorAutoInput">${getMessage.FTE01011}</span></span></td>
                    </tr>
                </tbody>
            </table>
        </div>
        <div id="menu-group" class="panel-group">
            <div class="panel-group-title">${getMessage.FTE01019  + fn.html.required()}</div>
            <table class="panel-table">
                <tbody>
                    <tr class="data-sheet parameter-sheet parameter-operation">
                        <th class="panel-th">${getMessage.FTE01020}</th>
                        <td class="panel-td" colspan="3"><span id="create-menu-for-input" type="text" class="panel-span" data-id="" data-value=""></span></td>
                    </tr>
                    <tr class="parameter-sheet parameter-operation">
                        <th class="panel-th">${getMessage.FTE01021}</th>
                        <td class="panel-td" colspan="3"><span id="create-menu-for-substitution" type="text" class="panel-span" data-id="" data-value=""></span></td>
                    </tr>
                    <tr class="parameter-sheet parameter-operation">
                        <th class="panel-th">${getMessage.FTE01022}</th>
                        <td class="panel-td" colspan="3"><span id="create-menu-for-reference" type="text" class="panel-span" data-id="" data-value=""></span></td>
                    </tr>
                </tbody>
            </table>
            <ul class="panel-button-group">
                <li><button id="create-menu-group-select" class="panel-button">` + getMessage.FTE01035 + `</button></li>
            </ul>
        </div>
        <div id="unique-constraint" class="panel-group">
            <div class="panel-group-title">` + getMessage.FTE01023 + `</div>
            <table class="panel-table">
                <tbody>
                    <tr class="data-sheet parameter-sheet parameter-operation">
                        <th class="panel-th">` + getMessage.FTE01024 + `</th>
                        <td class="panel-td" colspan="3"><span id="unique-constraint-list" type="text" class="panel-span"></span></td>
                    </tr>
                </tbody>
            </table>
            <ul class="panel-button-group">
                <li><button id="unique-constraint-select" class="panel-button">` + getMessage.FTE01036 + `</button></li>
            </ul>
        </div>
        <div id="permission-role" class="panel-group">
            <div class="panel-group-title">` + getMessage.FTE01025 + `</div>
            <table class="panel-table">
                <tbody>
                    <tr class="data-sheet parameter-sheet parameter-operation">
                        <th class="panel-th">` + getMessage.FTE01026 + `</th>
                        <td class="panel-td" colspan="3"><span id="permission-role-name-list" type="text" class="panel-span"></span></td>
                    </tr>
                </tbody>
            </table>
            <ul class="panel-button-group">
                <li><button id="permission-role-select" class="panel-button">` + getMessage.FTE01037 + `</button></li>
            </ul>
        </div>
        <div class="panel-group" title="` + getMessage.FTE01038 + `">
            <div class="panel-group-title">` + getMessage.FTE01027 + `</div>
            ${fn.html.textarea(['panel-note', 'panel-textarea', 'popup'], '', 'create-menu-explanation', null, true )}
        </div>
        <div class="panel-group" title="` + getMessage.FTE01039 + `">
            <div class="panel-group-title">` + getMessage.FTE01028 + `</div>
            ${fn.html.textarea(['panel-note', 'panel-textarea', 'popup'], '', 'create-menu-note', null, true )}
        </div>`;
    } else {
        panelType.menuType = '1';
        panelType.hostType = '1';
        panelType.verticalMenu = 'false';
        html += `
        <div class="panel-group">
            <div class="panel-group-title">` + getMessage.FTE01009 + `</div>
            <table class="panel-table">
                <tbody>
                    <tr>
                        <th class="panel-th">` + getMessage.FTE01010 + `</th>
                        <td class="panel-td" colspan="3"><span id="create-menu-id" class="panel-span" data-value=""><span class="editorAutoInput">${getMessage.FTE01011}</span></span></td>
                    </tr>
                </tbody>
            </table>
            <hr class="panel-hr">
            <table class="panel-table">
                <tbody>
                    <tr title="` + getMessage.FTE01029 + `">
                        <th class="panel-th panel-th-only">${getMessage.FTE01012 + fn.html.required()}</th>
                    </tr>
                    <tr title="` + getMessage.FTE01029 + `">
                        <td class="panel-td" colspan="3"><input id="create-menu-name" class="panel-text" type="text"></td>
                    </tr>
                    <tr title="` + getMessage.FTE01030 + `">
                        <th class="panel-th panel-th-only">${getMessage.FTE01013 + fn.html.required()}</th>
                    </tr>
                    <tr title="` + getMessage.FTE01030 + `">
                        <td class="panel-td" colspan="3"><input id="create-menu-name-rest" class="panel-text" type="text"></td>
                    </tr>
                    <tr title="` + getMessage.FTE01031 + `">
                        <th class="panel-th panel-th-only">` + getMessage.FTE01014 + `</th>
                    </tr>
                    <tr title="` + getMessage.FTE01031 + `">
                        <td class="panel-td" colspan="3">
                            <select id="create-menu-type" class="panel-select"></select>
                        </td>
                    </tr>
                </tbody>
            </table>
            <hr class="panel-hr">
            <table class="panel-table">
                <tbody>
                    <tr title="` + getMessage.FTE01032 + `">
                        <th class="panel-th">${getMessage.FTE01015 + fn.html.required()}</th>
                        <td class="panel-td"><input id="create-menu-order" class="panel-number" type="number" data-min="0" data-max="2147483647"></td>
                    </tr>
                </tbody>
            </table>
            <table class="panel-table">
                <tbody>
                    <tr class="parameter-sheet panel-check-tr" title="` + getMessage.FTE01154 + `">
                        <th class="panel-th">${getMessage.FTE01153}</th>
                        <td class="panel-td">
                            ${fn.html.checkboxText('panel-check', getMessage.FTE01034, 'create-menu-use-host-group', 'create-menu-use-host-group')}
                        </td>
                    </tr>
                    <tr class="parameter-sheet parameter-operation panel-check-tr" title="` + getMessage.FTE01033 + `">
                        <th class="panel-th">` + getMessage.FTE01016 + `</th>
                        <td class="panel-td">
                            ${fn.html.checkboxText('panel-check', getMessage.FTE01034, 'create-menu-use-vertical', 'create-menu-use-vertical')}
                        </td>
                    </tr>
                </tbody>
            </table>
            <table class="panel-table">
                <tbody>
                    <tr>
                        <th class="panel-th">` + getMessage.FTE01017 + `</th>
                        <td class="panel-td" colspan="3"><span id="create-menu-last-modified" class="panel-span" data-value=""><span class="editorAutoInput">${getMessage.FTE01011}</span></span></td>
                    </tr>
                    <tr>
                        <th class="panel-th">` + getMessage.FTE01018 + `</th>
                        <td class="panel-td" colspan="3"><span id="create-last-update-user" class="panel-span" data-value=""><span class="editorAutoInput">${getMessage.FTE01011}</span></span></td>
                    </tr>
                </tbody>
            </table>
        </div>
        <div id="menu-group" class="panel-group">
            <div class="panel-group-title">${getMessage.FTE01019 + fn.html.required()}</div>
            <table class="panel-table">
                <tbody>
                    <tr class="data-sheet parameter-sheet parameter-operation">
                        <th class="panel-th">${getMessage.FTE01020}</th>
                        <td class="panel-td" colspan="3"><span id="create-menu-for-input" type="text" class="panel-span" data-id="" data-value=""></span></td>
                    </tr>
                    <tr class="parameter-sheet parameter-operation">
                        <th class="panel-th">${getMessage.FTE01021}</th>
                        <td class="panel-td" colspan="3"><span id="create-menu-for-substitution" type="text" class="panel-span" data-id="" data-value=""></span></td>
                    </tr>
                    <tr class="parameter-sheet parameter-operation">
                        <th class="panel-th">${getMessage.FTE01022}</th>
                        <td class="panel-td" colspan="3"><span id="create-menu-for-reference" type="text" class="panel-span" data-id="" data-value=""></span></td>
                    </tr>
                </tbody>
            </table>
            <ul class="panel-button-group">
                <li><button id="create-menu-group-select" class="panel-button">` + getMessage.FTE01035 + `</button></li>
            </ul>
        </div>
        <div id="unique-constraint" class="panel-group">
            <div class="panel-group-title">` + getMessage.FTE01023 + `</div>
            <table class="panel-table">
                <tbody>
                    <tr class="data-sheet parameter-sheet parameter-operation">
                        <th class="panel-th">` + getMessage.FTE01024 + `</th>
                        <td class="panel-td" colspan="3"><span id="unique-constraint-list" type="text" class="panel-span"></span></td>
                    </tr>
                </tbody>
            </table>
            <ul class="panel-button-group">
                <li><button id="unique-constraint-select" class="panel-button">` + getMessage.FTE01036 + `</button></li>
            </ul>
        </div>
        <div id="permission-role" class="panel-group">
            <div class="panel-group-title">` + getMessage.FTE01025 + `</div>
            <table class="panel-table">
                <tbody>
                    <tr class="data-sheet parameter-sheet parameter-operation">
                        <th class="panel-th">` + getMessage.FTE01026 + `</th>
                        <td class="panel-td" colspan="3"><span id="permission-role-name-list" type="text" class="panel-span"></span></td>
                    </tr>
                </tbody>
            </table>
            <ul class="panel-button-group">
                <li><button id="permission-role-select" class="panel-button">` + getMessage.FTE01037 + `</button></li>
            </ul>
        </div>
        <div class="panel-group" title="` + getMessage.FTE01038 + `">
            <div class="panel-group-title">` + getMessage.FTE01027 + `</div>
            ${fn.html.textarea(['panel-note', 'panel-textarea', 'popup'], '', 'create-menu-explanation', null, true )}
        </div>
        <div class="panel-group" title="` + getMessage.FTE01039 + `">
            <div class="panel-group-title">` + getMessage.FTE01028 + `</div>
            ${fn.html.textarea(['panel-note', 'panel-textarea', 'popup'], '', 'create-menu-note', null, true )}
        </div>`;
    }

    return `
    <div id="panel-container" class="editor-panel">
        <div id="property" data-menu-type="${panelType.menuType}" data-host-type="${panelType.hostType}" data-vertical-menu="${panelType.verticalMenu}" class="editor-block">
            <div class="editor-block-inner">
                <div id="menu-info" class="editor-panel-block">
                    <div class="editor-panel-title">
                        <div class="editor-panel-title-inner">${getMessage.FTE01008}</div>
                    </div>
                    <div class="editor-panel-body">
                        <div class="editor-panel-body-inner">
                            ${html}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>`;
}
/*
##################################################
    editorOperationMenuHtml
##################################################
*/
editorOperationMenuHtml( editorMode, createManagementMenuID ) {
    const menuList = {
        Sub: [
            { className: 'fullscreen-on', button: { className: 'menu-editor-menu-button', icon: 'expansion', text: getMessage.FTE01148, type: 'fullscreen', action: 'default', minWidth: '120px'}},
            { className: 'fullscreen-off', button: { className: 'menu-editor-menu-button', icon: 'shrink', text: getMessage.FTE01149, type: 'fullscreen', action: 'default', minWidth: '120px'}}
        ]
    };
    if ( editorMode === 'new' || editorMode === 'diversion'){
        menuList.Main = [
            { button: { className: 'menu-editor-menu-button', icon: 'plus', text: getMessage.FTE01041, type: 'registration', action: 'positive', minWidth: '160px'}},
        ];
    } else if ( editorMode === 'view' ){
        if ( createManagementMenuID !== '' ) {
            menuList.Main = [
                { button: { className: 'menu-editor-menu-button', icon: 'edit', text: getMessage.FTE01042, type: 'edit', action: 'positive', minWidth: '160px'}},
                { button: { className: 'menu-editor-menu-button', icon: 'clear', text: getMessage.FTE01043, type: 'initialize', action: 'negative', minWidth: '120px'}, separate: true },
                { button: { className: 'menu-editor-menu-button', icon: 'copy', text: getMessage.FTE01044, type: 'diversion', action: 'negative', minWidth: '120px'}},
                { button: { className: 'menu-editor-menu-button', icon: 'check', text: getMessage.FTE01045, type: 'management', action: 'default', minWidth: '160px'}, separate: true },
            ];
        } else {
            menuList.Main = [
                { button: { className: 'menu-editor-menu-button', icon: 'edit', text: getMessage.FTE01042, type: 'edit', action: 'positive', minWidth: '160px'}},
                { button: { className: 'menu-editor-menu-button', icon: 'clear', text: getMessage.FTE01043, type: 'initialize', action: 'negative', minWidth: '120px'}, separate: true },
                { button: { className: 'menu-editor-menu-button', icon: 'copy', text: getMessage.FTE01044, type: 'diversion', action: 'negative', minWidth: '120px'}},
            ];
        }
    } else if ( editorMode === 'initialize' ){
        menuList.Main = [
            { button: { className: 'menu-editor-menu-button', icon: 'plus', text: getMessage.FTE01046, type: 'update-initialize', action: 'positive', minWidth: '160px'}},
            { button: { className: 'menu-editor-menu-button', icon: 'update01', text: getMessage.FTE01047, type: 'reload-initialize', action: 'negative', minWidth: '120px'}, separate: true },
            { button: { className: 'menu-editor-menu-button', icon: 'cross', text: getMessage.FTE01048, type: 'cancel', action: 'negative', minWidth: '120px'}},
        ];
    } else if ( editorMode === 'edit' ){
        menuList.Main = [
            { button: { className: 'menu-editor-menu-button', icon: 'plus', text: getMessage.FTE01049, type: 'update', action: 'positive', minWidth: '160px'}},
            { button: { className: 'menu-editor-menu-button', icon: 'update01', text: getMessage.FTE01047, type: 'reload', action: 'negative', minWidth: '120px'}, separate: true },
            { button: { className: 'menu-editor-menu-button', icon: 'cross', text: getMessage.FTE01048, type: 'cancel', action: 'negative', minWidth: '120px'}},
        ];
    }
    return fn.html.operationMenu( menuList );
}
/*
##################################################
    Init
##################################################
*/
init( info ) {
    const cm = this;

    //cm.info = info;
    menuEditorArray = info;
    nameConvertList = menuEditorArray.name_convert_list;
    menuEditorMode = $('#menu-editor').attr('data-editor-mode');

    menuEditor( menuEditorMode, menuEditorArray );
}

}

// モード判定用
let menuEditorMode = '';

// 読み込み対象ID
let menuEditorTargetID = '';

// 各種リスト用配列
let menuEditorArray = {};

// 一意制約更新カウント
let uniquechangecount = 0;

// 一意制約削除カウント
let uniquedeletecount = 0;

// テキストの無害化
const textEntities = function( text, flag ) {
    if ( flag === undefined ) flag = 0;
    const entities = [
        ['&', 'amp'],
        ['\"', 'quot'],
        ['\'', 'apos'],
        ['<', 'lt'],
        ['>', 'gt'],
    ];
    for ( var i = 0; i < entities.length; i++ ) {
        text = text.replace( new RegExp( entities[i][0], 'g'), '&' + entities[i][1] + ';' );
    }
    if ( flag !== 1 ) {
        text = text.replace(/^\s+|\s+$/g, '');
        text = text.replace(/\r?\n/g, '<br>');
    }
    return text;
};

// ログ表示
let menuEditorLogNumber = 1;
const menuEditorLog = {
    // log type : debug, log, notice, warning, error
    'set': function( type, content ) {
        $('.editor-tab-menu-item[data-tab="menu-editor-log"]').click();
        if ( type === undefined || type === '' ) type = 'log';

        const $menuEditorLog = $('.editor-log'),
              $menuEditorLogTable = $menuEditorLog.find('tbody');

        const logClass = ( type !== 'log')? ' editor-log-content-level': '';

        let logRowHTML = ''
          + '<tr class="editor-log-row ' + type + '">'
            + '<th class="editor-log-number">' + ( menuEditorLogNumber++ ) +'</th><td class="editor-log-content"><div class="editor-log-content-inner' + logClass + '">';
        if ( type !== 'log') logRowHTML += '<span class="logLevel">' + textEntities( type.toLocaleUpperCase() ) + '</span>'

        logRowHTML += content + '</div></td></tr>';

        $menuEditorLogTable.append( logRowHTML );

        // 一番下までスクロール
        const scrollTop = $menuEditorLog.get(0).scrollHeight - $menuEditorLog.get(0).clientHeight;
        $menuEditorLog.animate({ scrollTop : scrollTop }, 200 );
    },
    'clear': function() {
        menuEditorLogNumber = 1;
        $('.editor-log').find('tbody').empty();
    }
};

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   モーダル
//
////////////////////////////////////////////////////////////////////////////////////////////////////

// モーダルを開く
function itaModalOpen( headerTitle, bodyFunc, modalType, target = "" ) {
    if ( typeof bodyFunc !== 'function' ) return false;

    // 初期値
    if ( headerTitle === undefined ) headerTitle = 'Undefined title';
    if ( modalType === undefined ) modalType = 'default';

    const $window = $( window ),
          $body = $('body');

    let footerHTML;

    if ( modalType === 'help' ) {
      footerHTML = ''
      + '<div class="editor-modal-footer">'
        + '<ul class="editor-modal-footer-menu">'
          + '<li class="editor-modal-footer-menu-item"><button class="editor-modal-footer-menu-button negative" data-button-type="close">' + getMessage.FTE01050 + '</li>'
        + '</ul>'
      + '</div>'
    } else {
      footerHTML = ''
      + '<div class="editor-modal-footer">'
        + '<ul class="editor-modal-footer-menu">'
          + '<li class="editor-modal-footer-menu-item"><button class="editor-modal-footer-menu-button positive" data-button-type="ok">' + getMessage.FTE01051 + '</li>'
          + '<li class="editor-modal-footer-menu-item"><button class="editor-modal-footer-menu-button negative" data-button-type="cancel">' + getMessage.FTE01052 + '</li>'
        + '</ul>'
      + '</div>'
    }

    let modalHTML = ''
      + '<div id="editor-modal" class="' + modalType + '">'
        + '<div class="editor-modal-container">'
          + '<div class="editor-modal-header">'
            + '<span class="editor-modal-title">' + headerTitle + '</span>'
            + '<button class="editor-modal-header-close"></button>'
          + '</div>'
          + '<div class="editor-modal-body">'
            + '<div class="editor-modal-loading"></div>'
          + '</div>'
          + footerHTML
        + '</div>'
      + '</div>';

    const $editorModal = $( modalHTML ),
          $firstFocus = $editorModal.find('.editor-modal-header-close'),
          $lastFocus = $editorModal.find('.editor-modal-footer-menu-button[data-button-type="cancel"]');

    $body.append( $editorModal );
    $firstFocus.focus();

    $window.on('keydown.modal', function( e ) {

        switch ( e.keyCode ) {
            case 9: // Tabでの移動をモーダル内に制限する
            {
                const $focusElement = $( document.activeElement );
                if ( $focusElement.is( $firstFocus ) && e.shiftKey ) {
                    e.preventDefault();
                    $lastFocus.focus();
                } else if ( $focusElement.is( $lastFocus ) && !e.shiftKey ) {
                    e.preventDefault();
                    $firstFocus.focus();
                }
            }
            break;
            case 27: // Escでモーダルを閉じる
                itaModalClose();
                break;
        }
    });

    $firstFocus.on('click', function() {
        itaModalClose();
    });
    if ( modalType === 'help' ) {
        $editorModal.find('.editor-modal-footer-menu-button[data-button-type="close"]').on('click', itaModalClose );
    }

    if(target != ""){
        bodyFunc(target);
    }else{
        bodyFunc();
    }
}

// モーダルを閉じる
function itaModalClose() {

    const $window = $( window ),
        $editorModal = $('#editor-modal');

    if ( $editorModal.length ) {
        $window.off('keyup.modal');
        $editorModal.remove();
    }
}

// モーダルエラー表示
function itaModalError( message ) {
    const $modalBody = $('.editor-modal-body');
    $modalBody.html('<div class="editor-modal-error"><p>' + message + '</p></div>');
}

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   タブ切替初期設定
//
////////////////////////////////////////////////////////////////////////////////////////////////////

function itaTabMenu() {

    $('.editor-tab').each( function() {

        const $tab = $( this ),
            $tabItem = $tab.find('.editor-tab-menu-item'),
            $tabBody = $tab.find('.editor-tab-body');

        $tabItem.eq(0).addClass('selected');
        $tabBody.eq(0).addClass('selected');

        $tabItem.on('click', function() {
        const $clickTab = $( this ),
            $openTab = $('#' + $clickTab.attr('data-tab') );

        $tab.find('.selected').removeClass('selected');
        $clickTab.add( $openTab ).addClass('selected');
        });
    });
}

const menuEditor = function() {

    'use strict';

    // jQueryオブジェキャッシュ
    const $window = $( window ),
        $html = $('html'),
        $body = $('body'),
        $menuEditor = $('#menu-editor'),
        $menuEditWindow = $('#menu-editor-edit'),
        $menuTable = $menuEditor.find('.menu-table'),
        $property = $('#property');

    // タブ
    itaTabMenu();

    // 読み込み完了
    $menuEditor.removeClass('load-wait');
    $menuEditor.find('.textareaAdjustment').each( fn.textareaAdjustment );

    // --------------------------------------------------
    // フルスクリーン切り替え時のイベントを追加する
    // --------------------------------------------------
    document.onfullscreenchange = document.onmozfullscreenchange = document.onwebkitfullscreenchange = document.onmsfullscreenchange = function () {
        if( fn.fullScreenCheck() ){
            $body.addClass('editor-full-screen');
        } else {
            $body.removeClass('editor-full-screen');
        }
    }

// 項目別ダミーテキスト（value:[ja,en,type]）
const selectDummyText = {
    '0' : ['','',''],
    '1' : [getMessage.FTE01097,'','string'],
    '2' : [getMessage.FTE01098 + '<br>' + getMessage.FTE01098,'','string'],
    '3' : ['0','0','number'],
    '4' : ['0.0','0.0','number'],
    '5' : ['2020/01/01 00:00','2020/01/01 00:00','string'],
    '6' : ['2020/01/01','2020/01/01','string'],
    '7' : ['','','select'],
    '8' : [getMessage.FTE01099,'','string'],
    '9' : [getMessage.FTE01100,'','string'],
    '10' : [getMessage.FTE01101,'','string'],
    '11' : [getMessage.FTE01102,'','string']
};

const titleHeight = 32;

// 各種IDから名称を返す
const listIdName = function( type, id ) {
    let list,idKey,nameKey,name;
    if ( type === 'input') {
        list = menuEditorArray.column_class_list;
        idKey = 'column_class_id';
        nameKey = 'column_class_disp_name';
    } else if ( type === 'pulldown') {
        list = menuEditorArray.pulldown_item_list;
        idKey = 'link_id';
        nameKey = 'link_pulldown';
    } else if ( type === 'target') {
        list = menuEditorArray.sheet_type_list;
        idKey = 'sheet_type_id';
        nameKey = 'sheet_type_name';
    //} else if ( type === 'use') {
    //    list = menuEditorArray.selectParamPurpose;
    //    idKey = 'PURPOSE_ID';
    //    nameKey = 'PURPOSE_NAME';
    } else if ( type === 'group') {
        list = menuEditorArray.target_menu_group_list;
        idKey = 'menu_group_id';
        nameKey = 'full_menu_group_name';
    } else if ( type === 'role') {
        list = menuEditorArray.role_list;
        //idKey = 'ROLE_ID';
        //nameKey = 'ROLE_NAME';
    }

    const listLength = list.length;
    for ( let i = 0; i < listLength; i++ ) {
        if( type !== 'role' ){
            if ( String( list[i][idKey] ) === String( id ) ) {
                name = list[i][nameKey];
                return name;
            }
        } else {
            if ( list[i] === id ) {
                name = list[i]
                return name;
            }
        }
    }
    return null;
};

let modeDisabled = '';
if ( menuEditorMode === 'view') modeDisabled = ' disabled';

let modeKeepData = '';
if ( menuEditorMode === 'edit') modeKeepData = ' disabled';

let onHover = ' on-hover';
if ( menuEditorMode === 'edit') onHover = '';

let disbledCheckbox = '';
if ( menuEditorMode === 'edit') disbledCheckbox = ' disabled-checkbox';

// 項目ヘッダーHTML
const getColumnHeaderHTML = function( columnHeaderTitle = '', columnHeaderRest = '' ) {
    return ''
  + '<div class="menu-column-move" title="' + textEntities(getMessage.FTE01103,1) + '"></div>'
  + '<div class="menu-column-title-wrap">'
      + '<div class="menu-column-title on-hover" title="' + textEntities(getMessage.FTE01104,1) + '">'
            + '<input class="menu-column-title-input" type="text" value="' + columnHeaderTitle + '"'+modeDisabled+'>'
            + '<span class="menu-column-title-dummy">' + columnHeaderTitle + '</span>'
      + '</div>'
      + '<div class="menu-column-title on-hover" title="' + textEntities(getMessage.FTE01105,1) + '">'
            + '<input class="menu-column-title-rest-input" type="text" value="' + columnHeaderRest + '"'+modeDisabled+'>'
            + '<span class="menu-column-title-dummy">' + columnHeaderRest + '</span>'
      + '</div>'
  + '</div>'
  + '<div class="menu-column-function">'
        + '<div class="menu-column-delete on-hover" title="' + textEntities(getMessage.FTE01106,1) + '"></div>'
        + '<div class="menu-column-copy on-hover" title="' + textEntities(getMessage.FTE01107,1) + '"></div>'
  + '</div>';
};
const columnHeaderHTML = getColumnHeaderHTML();

// グループヘッダーHTML
const getColumnHeaderGroupHTML = function( columnHeaderGroupTitle = '' ) {
    return ''
  + '<div class="menu-column-move" title="' + textEntities(getMessage.FTE01103,1) + '"></div>'
  + '<div class="menu-column-title on-hover" title="' + textEntities(getMessage.FTE01104,1) + '">'
    + '<input class="menu-column-title-input" type="text" value="' + columnHeaderGroupTitle + '"'+modeDisabled+'>'
    + '<span class="menu-column-title-dummy">' + columnHeaderGroupTitle + '</span>'
  + '</div>'
  + '<div class="menu-column-function">'
    + '<div class="menu-column-delete on-hover" title="' + textEntities(getMessage.FTE01106,1) + '"></div>'
    + '<div class="menu-column-copy on-hover" title="' + textEntities(getMessage.FTE01107,1) + '"></div>'
  + '</div>';
};
const columnHeaderGroupHTML = getColumnHeaderGroupHTML();

// EmptyHTML
const columnEmptyHTML = ''
  + '<div class="column-empty"><p>Empty</p></div>';

// グループ枠HTML
const getColumnGroupHTML = function( columnHeaderGroup = {}, bodyHTML = '') {
    const sv = function( v, f = true ) { return fn.cv( columnHeaderGroup[v], '', f ); };
    return ''
  + '<div class="menu-column-group" data-group-id="' + sv('group_id') + '">'
    + '<div class="menu-column-group-header">'
      + getColumnHeaderGroupHTML( sv('group_name') )
    + '</div>'
    + '<div class="menu-column-group-body">'
        + bodyHTML
    + '</div>'
  + '</div>';
};

const columnGroupHTML = getColumnGroupHTML();

// リピートHTML
const columnRepeatHTML = ''
  + '<div class="menu-column-repeat">'
    + '<div class="menu-column-repeat-header">'
      + '<div class="menu-column-move"></div>'
      + '<div class="menu-column-repeat-number on-hover" title="' + textEntities(getMessage.FTE01108,1) + '">REPEAT : <input class="menu-column-repeat-number-input" data-min="2" data-max="99" value="2" type="number"'+modeDisabled+'></div>'
    + '</div>'
    + '<div class="menu-column-repeat-body">'
    + '</div>'
    + '<div class="menu-column-repeat-footer">'
      + '<div class="menu-column-function">'
        + '<div class="menu-column-delete"></div>'
      + '</div>'
    + '</div>'
  + '</div>';

// 入力方式 select
const selectInputMethodData = menuEditorArray.column_class_list,
    selectInputMethodDataLength = selectInputMethodData.length;

const getInputMethodHTML = function( selectValue = '' ) {
    const inputMethodArray = [];
    for ( let i = 0; i < selectInputMethodDataLength ; i++ ) {
        const classID = selectInputMethodData[i].column_class_id,
              selected = ( classID === selectValue )? ' selected="selected"': '';
        inputMethodArray.push('<option value="' + classID+ '" data-value="' + selectInputMethodData[i].column_class_name + '"' + selected + '>' + selectInputMethodData[i].column_class_disp_name + '</option>');
    }
    return inputMethodArray.join('');
};

// プルダウン選択 select
const selectPulldownListData = menuEditorArray.pulldown_item_list,
    selectPulldownListDataLength = selectPulldownListData.length;

const getPelectPulldownListHTML = function( selectValue = '' ) {
    const selectPulldownListArray = [];
    for ( let i = 0; i < selectPulldownListDataLength ; i++ ) {
        const linkID = selectPulldownListData[i].link_id,
              selected = ( linkID === selectValue )? ' selected="selected"': '';
        selectPulldownListArray.push('<option value="' + linkID + '"' + selected + '>' + selectPulldownListData[i].link_pulldown + '</option>');
    }
    return selectPulldownListArray.join('');
};

//パラメータシート参照 select
const parameterSheetReferenceListData = menuEditorArray.parameter_sheet_reference_list,
      parameterSheetReferenceListDataLength = parameterSheetReferenceListData.length;
const getParameterSheetReferenceListHTML = function( selectValue = '' ) {
    const parameterSheetReferenceListArray = [];
    for ( let i = 0; i < parameterSheetReferenceListDataLength ; i++ ) {
        const columnDefinitionId = parameterSheetReferenceListData[i].column_definition_id,
              selected = ( columnDefinitionId === selectValue )? ' selected="selected"': '';
        parameterSheetReferenceListArray.push('<option value="' + columnDefinitionId + '"' + selected + '>' + parameterSheetReferenceListData[i].select_full_name + '</option>')
    }
    return parameterSheetReferenceListArray.join('');
};

// 作成対象 select
if ( menuEditorMode !== 'view') {
    const selectParamTargetData = menuEditorArray.sheet_type_list,
        selectParamTargetDataLength = selectParamTargetData.length,
        sortOrder = [0,2,1];
    let selectParamTargetHTML = '';
    for ( let i = 0; i < selectParamTargetDataLength ; i++ ) {
        selectParamTargetHTML += '<option value="' + selectParamTargetData[sortOrder[i]].sheet_type_id + '">' + selectParamTargetData[sortOrder[i]].sheet_type_name + '</option>';
    }
    $('#create-menu-type').html( selectParamTargetHTML );
}

// 項目HTML
const getColumnHTML = function( columnData = {}, columnID = '') {

    const sv = function( v, f = true ) { return fn.cv( columnData[v], '', f ); };
    const fileMaxSize = fn.cv( menuEditorArray.org_upload_file_size_limit, 104857600 );

    return `
<div id="${columnID}" class="menu-column" data-rowpan="1" data-item-id="${sv('create_column_id')}" style="min-width: 260px;">
    <div class="menu-column-header">${getColumnHeaderHTML(sv('item_name'),sv('item_name_rest'))}</div>
    <div class="menu-column-body">
        <div class="menu-column-type" title="${textEntities(getMessage.FTE01109,1)}">
            <select class="input menu-column-type-select" id="menu-column-type-select"${modeDisabled}${modeKeepData}>
                ${getInputMethodHTML(sv('column_class_id'))}
            </select>
        </div>
        <div class="menu-column-config">
            <table class="menu-column-config-table" date-select-value="${fn.cv(columnData['column_class_id'], '1')}">
                <tbody>
                    <!-- 最大バイト数 single -->
                    <tr class="single" title="${textEntities(getMessage.FTE01110,1)}">
                        <th class="half-cell"><span class="config-title">${getMessage.FTE01055 + fn.html.required()}</span></th>
                        <td class="half-cell"><input class="input config-number max-byte" type="number" data-min="1" data-max="8192" value="${sv('single_string_maximum_bytes')}"${modeDisabled}></td>
                    </tr>
                    <!-- 正規表現 single -->
                    <tr class="single" title="${textEntities(getMessage.FTE01111,1)}">
                        <th class="full-head"><span class="config-title">${getMessage.FTE01056}</span></th>
                        <td class="full-body"><input class="input config-text regex" type="text" value="${sv('single_string_regular_expression')}"${modeDisabled}></td>
                    </tr>
                    <!-- 最大バイト数 multiple -->
                    <tr class="multiple" title="${textEntities(getMessage.FTE01110,1)}">
                        <th class="half-cell"><span class="config-title">${getMessage.FTE01055 + fn.html.required()}</span></th>
                        <td class="half-cell"><input class="input config-number multiple-max-byte" type="number" data-min="1" data-max="8192" value="${sv('multi_string_maximum_bytes')}"${modeDisabled}></td>
                    </tr>
                    <!-- 正規表現 multiple -->
                    <tr class="multiple" title="${textEntities(getMessage.FTE01111,1)}">
                        <th class="full-head"><span class="config-title">${getMessage.FTE01056}</span></th>
                        <td class="full-body"><input class="input config-text multiple-regex" type="text" value="${sv('multi_string_regular_expression')}"${modeDisabled}></td>
                    </tr>
                    <!-- 最大バイト数 link -->
                    <tr class="link" title="${textEntities(getMessage.FTE01110,1)}">
                        <th class="half-cell"><span class="config-title">${getMessage.FTE01055 + fn.html.required()}</span></th>
                        <td class="half-cell"><input class="input config-number link-max-byte" type="number" data-min="1" data-max="8192" value="${sv('link_maximum_bytes')}"${modeDisabled}></td>
                    </tr>
                    <!-- 最小値 int -->
                    <tr class="number-int" title="${textEntities(getMessage.FTE01112,1)}">
                        <th class="half-cell"><span class="config-title">${getMessage.FTE01057}</span></th>
                        <td class="half-cell"><input class="input config-number int-min-number" data-min="-2147483648" data-max="2147483647" type="number" value="${sv('integer_minimum_value')}"${modeDisabled}></td>
                    </tr>
                    <!-- 最大値 int -->
                    <tr class="number-int" title="${textEntities(getMessage.FTE01113,1)}">
                        <th class="half-cell"><span class="config-title">${getMessage.FTE01058}</span></th>
                        <td class="half-cell"><input class="input config-number int-max-number" data-min="-2147483648" data-max="2147483647" type="number" value="${sv('integer_maximum_value')}"${modeDisabled}></td>
                    </tr>
                    <!-- 最小値 froat -->
                    <tr class="number-float" title="${textEntities(getMessage.FTE01114,1)}">
                        <th class="half-cell"><span class="config-title">${getMessage.FTE01057}</span></th>
                        <td class="half-cell"><input class="input config-number float-min-number" data-min="-99999999999999" data-max="99999999999999" type="number" value="${sv('decimal_minimum_value')}"${modeDisabled}></td>
                    </tr>
                    <!-- 最大値 froat -->
                    <tr class="number-float" title="'${textEntities(getMessage.FTE01115,1)}">
                        <th class="half-cell"><span class="config-title">${getMessage.FTE01058}</span></th>
                        <td class="half-cell"><input class="input config-number float-max-number" data-min="-99999999999999" data-max="99999999999999" type="number" value="${sv('decimal_maximum_value')}"${modeDisabled}></td>
                    </tr>
                    <!-- 桁数 -->
                    <tr class="number-float" title="${textEntities(getMessage.FTE01116,1)}">
                        <th class="half-cell"><span class="config-title">${getMessage.FTE01059}</span></th>
                        <td class="half-cell"><input class="input config-number digit-number" data-min="1" data-max="14" type="number" value="${sv('decimal_digit')}"${modeDisabled}></td>
                    </tr>
                    <!-- プルダウン選択項目 -->
                    <tr class="select-option" title="${textEntities(getMessage.FTE01117,1)}">
                        <th class="full-head"><span class="config-title">${getMessage.FTE01060 + fn.html.required()}</span></th>
                        <td class="full-body">
                            <select class="input config-select pulldown-select"${modeDisabled}${modeKeepData}>${getPelectPulldownListHTML(sv('pulldown_selection_id'))}</select>
                        </td>
                    </tr>
                    <!-- 参照項目 -->
                    <tr class="select-option reference" title="${textEntities(getMessage.FTE01118,1)}">
                        <th class="full-head"><span class="config-title">${getMessage.FTE01087}</span></th>
                        <td class="full-body">
                            <div class="reference-block">
                                <span type="text" class="input config-text reference-item" type="text" data-reference-item-id ${modeDisabled}${modeKeepData}></span>
                                <button class="itaButton button reference-item-select property-button popup" data-action="normal" title="${getMessage.FTE01089}"${modeDisabled}${modeKeepData}>
                                    <div class="inner">${fn.html.icon('menuList')}</div>
                                </button>
                            </div>
                        </td>
                    </tr>
                    <!-- パラメータシート参照項目 -->
                    <tr class="param-sheet-ref" title="${textEntities(getMessage.FTE01117,1)}">
                        <th class="full-head"><span class="config-title">${getMessage.FTE01060 + fn.html.required()}</span></th>
                        <td class="full-body">
                            <select class="input config-select reference-parameter-sheet"${modeDisabled}${modeKeepData}>${getParameterSheetReferenceListHTML(sv('parameter_sheet_reference_id'))}</select>
                        </td>
                    </tr>
                    <!-- 最大バイト数 パスワード -->
                    <tr class="password" title="${textEntities(getMessage.FTE01110,1)}">
                        <th class="full-head"><span class="config-title">${getMessage.FTE01055 + fn.html.required()}</span></th>
                        <td class="full-body"><input class="input config-number password-max-byte" type="number" data-min="1" data-max="8192" value="${sv('password_maximum_bytes')}"${modeDisabled}></td>
                    </tr>
                    <!-- 最大バイト数 ファイル -->
                    <tr class="file" title="${textEntities(getMessage.FTE01119(fileMaxSize),1)}">
                        <th class="full-head"><span class="config-title">${getMessage.FTE01086 + fn.html.required()}</span></th>
                        <td class="full-body"><input class="input config-number file-max-size" data-min="1" data-max="${fileMaxSize}"  type="number" value="${sv('file_upload_maximum_bytes')}"${modeDisabled}></td>
                    </tr>
                    <!-- 初期値 -->
                    <tr class="single" title="${textEntities(getMessage.FTE01121,1)}">
                        <th class="full-head"><span class="config-title">${getMessage.FTE01094}</span></th>
                        <td class="full-body"><input class="input config-text single-default-value" type="text" value="${sv('single_string_default_value')}"${modeDisabled}></td>
                    </tr>
                    <!-- 初期値 複数行 -->
                    <tr class="multiple" title="${textEntities(getMessage.FTE01121,1)}">
                        <th class="full-head"><span class="config-title">${getMessage.FTE01094}</span></th>
                        <td class="full-body"><textarea class="input config-textarea multiple-default-value"${modeDisabled}>${sv('multi_string_default_value', false )}</textarea></td>
                    </tr>
                    <!-- 初期値 int -->
                    <tr class="number-int" title="${textEntities(getMessage.FTE01122,1)}">
                        <th class="half-cell"><span class="config-title">${getMessage.FTE01094}</span></th>
                        <td class="half-cell"><input class="input config-number int-default-value" data-min="-2147483648" data-max="2147483647" type="number" value="${sv('integer_default_value')}"${modeDisabled}></td>
                    </tr>
                    <!-- 初期値 float -->
                    <tr class="number-float" title="${textEntities(getMessage.FTE01123,1)}">
                        <th class="half-cell"><span class="config-title">${getMessage.FTE01094}</span></th>
                        <td class="half-cell"><input class="input config-number float-default-value" data-min="-99999999999999" data-max="99999999999999" type="number" value="${sv('decimal_default_value')}"${modeDisabled}></td>
                    </tr>
                    <!-- 初期値 日時 -->
                    <tr class="date-time" title="${textEntities(getMessage.FTE01124,1)}">
                        <th class="full-head"><span class="config-title">${getMessage.FTE01094}</span></th>
                        <td class="full-body">${( modeDisabled === '')?
                            fn.html.dateInput( true, 'callDateTimePicker datetime-default-value config-text', sv('datetime_default_value'), 'dateTime'):
                            `<input class="input datetime-default-value config-text" value="${sv('datetime_default_value')}"${modeDisabled}>`
                        }</td>
                    </tr>
                    <!-- 初期値 日付 -->
                    <tr class="date" title="${textEntities(getMessage.FTE01124,1)}">
                        <th class="full-head"><span class="config-title">${getMessage.FTE01094}</span></th>
                        <td class="full-body">${( modeDisabled === '')?
                            fn.html.dateInput( false, 'callDateTimePicker date-default-value config-text', sv('date_default_value'), 'date'):
                            `<input class="input date-default-value config-text" value="${sv('date_default_value')}"${modeDisabled}>`
                        }</td>
                    </tr>
                    <!-- 初期値 リンク -->
                    <tr class="link" title="${textEntities(getMessage.FTE01125,1)}">
                        <th class="full-head"><span class="config-title">${getMessage.FTE01094}</span></th>
                        <td class="full-body"><input class="input config-text link-default-value" type="text" value="${sv('link_default_value')}"${modeDisabled}></td>
                    </tr>
                    <!-- 初期値 選択 -->
                    <tr class="select-option" title="${textEntities(getMessage.FTE01126,1)}">
                        <th class="full-head">${getMessage.FTE01094}</th>
                        <td class="full-body pulldown-default-area">
                            <select class="input config-select pulldown-default-select"${modeDisabled}></select>
                        </td>
                    </tr>
                    <!-- 必須・一意 -->
                    <tr class="single multiple number-int number-float date-time date password select-option file link">
                        <td colspan="2">
                            <label class="required-label${onHover}" title="${textEntities(getMessage.FTE01127,1)}"${modeDisabled}${modeKeepData}>
                                <input class="config-checkbox required${disbledCheckbox}" type="checkbox"${modeDisabled}${modeKeepData}${( columnData.required === '1' || columnData.required === 'True' || columnData.required ===  true )? ` checked`: ``}>
                                <span></span>${getMessage.FTE01061}
                            </label>
                            <label class="unique-label${onHover}" title="${textEntities(getMessage.FTE01128,1)}"${modeDisabled}${modeKeepData}>
                                <input class="config-checkbox unique${disbledCheckbox}" type="checkbox"${modeDisabled}${modeKeepData}${( columnData.uniqued === '1' || columnData.uniqued === 'True' || columnData.uniqued ===  true )? ` checked`: ``}>
                                <span></span>${getMessage.FTE01062}
                            </label>
                        </td>
                    </tr>
                    <!-- 説明 -->
                    <tr class="all" title="${textEntities(getMessage.FTE01129,1)}">
                        <td colspan="2">
                            <div class="config-textarea-wrapper">
                                <textarea class="input config-textarea explanation${( sv('description') !== '')? ' text-in': ''}"${modeDisabled}>${sv('description', false )}</textarea>
                                <span>${getMessage.FTE01063}</span>
                            </div>
                        </td>
                    </tr>
                    <!-- 備考 -->
                    <tr class="all" title="${textEntities(getMessage.FTE01130,1)}">
                        <td colspan="2">
                            <div class="config-textarea-wrapper">
                                <textarea class="input config-textarea note${( sv('remarks') !== '')? ' text-in': ''}"${modeDisabled}>${sv('remarks', false )}</textarea>
                                <span>${getMessage.FTE01064}</span>
                            </div>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
    <div class="column-resize"></div>
</div>`;
};

const columnHTML = getColumnHTML();

// カウンター
let itemCounter = 1,
    groupCounter = 1;

// IDリスト
let menuIdList = [];

// Hover
const hoverElements = '.on-hover';
$menuTable.on({
    'mouseenter' : function() {
        if ( menuEditorMode !== 'view') $( this ).addClass('hover');
    },
    'mouseleave' : function() {
        if ( menuEditorMode !== 'view') $( this ).removeClass('hover');
    }
}, hoverElements );

const modeChange = function( mode ) {
    if ( mode !== undefined ) {
        $body.attr('data-mode', mode );
        $menuTable.addClass('hover-disabled');
    } else {
        $body.attr('data-mode', '' );
        $menuTable.removeClass('hover-disabled');
    }
}

const mode = {
    blockResize : function() { modeChange('blockResize'); },
    columnResize : function() { modeChange('columnResize'); },
    columnMove : function() { modeChange('columnMove'); },
    clear : function() { modeChange(); }
};

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   取り消し、やり直し
//
////////////////////////////////////////////////////////////////////////////////////////////////////

const $undoButton = $('#button-undo'),
    $redoButton = $('#button-redo'),
    maxHistroy = 10; // 最大履歴数

let workHistory = [''],
    workCounter = 0;

// 取り消し、やり直しボタンチェック
const historyButtonCheck = function() {
    if ( workHistory[ workCounter - 1 ] !== undefined ) {
        $undoButton.prop('disabled', false );
    } else {
        $undoButton.prop('disabled', true );
    }
    if ( workHistory[ workCounter + 1 ] !== undefined ) {
        $redoButton.prop('disabled', false );
    } else {
        $redoButton.prop('disabled', true );
    }
};

// 履歴管理
const history = {
    'add' : function() {
        workCounter++;
        const $clone = $menuTable.clone();
        $clone.find('.hover').removeClass('hover');
        workHistory[ workCounter ] = $clone.html();

        // 履歴追加後の履歴を削除する
        if ( workHistory[ workCounter + 1 ] !== undefined ) {
            workHistory.length = workCounter + 1;
        }
        // 最大履歴数を超えた場合最初の履歴を削除する
        if ( workHistory.length > maxHistroy ) {
            workHistory.shift();
            workCounter--;
        }

        historyButtonCheck();
    },
    'undo' : function() {
        workCounter--;
        $menuTable.html( workHistory[ workCounter ] );
        historyButtonCheck();
        previewTable();
        resetSelect2( $menuTable );
        //resetDatetimepicker( $menuTable );
        resetEventPulldownDefaultValue( $menuTable );
        // resetEventPulldownParameterSheetReference( $menuTable );
        updateUniqueConstraintDispData();
    },
    'redo' : function() {
        workCounter++;
        $menuTable.html( workHistory[ workCounter ] );
        historyButtonCheck();
        previewTable();
        resetSelect2( $menuTable );
        //resetDatetimepicker( $menuTable );
        resetEventPulldownDefaultValue( $menuTable );
        // resetEventPulldownParameterSheetReference( $menuTable );
        updateUniqueConstraintDispData();
    },
    'clear' : function() {
        workCounter = 0;
        workHistory = [];
        workHistory[ workCounter ] = $menuTable.html();
        historyButtonCheck();
    }
};

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   列の追加
//
////////////////////////////////////////////////////////////////////////////////////////////////////

const addColumn = function( $target, type ) {

    let html = '',
        id = '',
        title = '',
        number = 0;

    // IDがすでに使用されているかチェックする
    const idCheck = function( t, n ){
        while ( menuIdList.indexOf(`${t}${n}`) !== -1 ) {
            n++;
        }
        return n;
    };

    switch( type ) {
        case 'column':
            html = columnHTML;
            number = idCheck('c', itemCounter++ );
            id = 'c' + number;
            title = getMessage.FTE01053;
            break;
        case 'group':
            html = columnGroupHTML;
            number = idCheck('g', groupCounter++ );
            id = 'g' + number;
            title = getMessage.FTE01054;
            break;
    }

    const $addColumn = $( html ),
          $addColumnInput = $addColumn.find('.menu-column-title-input'),
          $addColumnRestInput = $addColumn.find('.menu-column-title-rest-input');

    $target.append( $addColumn );
    // プルダウンにselect2を適用する
    $target.find('.config-select').select2();

    $addColumn.attr('id', id );
    menuIdList.push( id );

    // グループの場合空HTMLを追加
    if ( type === 'group') {
        $addColumn.find('.menu-column-group-body').html( columnEmptyHTML );
    }

    // 自動付加する名前が被ってないかチェックする
    const checkName = function( cName ) {
        let nameList = [];
        $menuEditor.find('.menu-column-title-input').each( function( i ){
            nameList[ i ] = $( this ).val();
        });

        let condition = true;
        while( condition ) {
            if ( nameList.indexOf( cName ) !== -1 ) {
            number++;
            cName = title + ' ' + number;
            } else {
            condition = false;
            }
        }
        return cName;
    }
    $addColumnInput.val( checkName( title + ' ' + number ) );
    $addColumnRestInput.val( checkName( 'item_' + number ) );

    titleInputChange( $addColumnInput );
    titleInputChange( $addColumnRestInput );

    emptyCheck();
    columnHeightUpdate();

    history.add();
    previewTable();

    // 追加した項目に合わせスクロールさせる
    const $scrollArea = $menuEditWindow.children(),
          scrollElement = $scrollArea.get(0),
          scrollWidth = scrollElement.scrollWidth,
          clientWidth = scrollElement.clientWidth;

    if ( clientWidth < scrollWidth ) {
        $scrollArea.stop(0,0).animate({'scrollLeft': scrollWidth - clientWidth }, 200 );
    }

    return $addColumn;

};

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   参照項目選択
//
////////////////////////////////////////////////////////////////////////////////////////////////////

//参照項目を選択するモーダル表示イベント
$menuEditor.on('click', '.reference-item-select', function() {
    itaModalOpen(getMessage.FTE01093, modalReferenceItemList, 'reference' , $(this));
});

//選択項目変更時、参照項目を空にする
$menuEditor.on('change', '.pulldown-select', function(){
    const $input = $(this).closest('.menu-column-config-table').find('.reference-item');
    $input.attr('data-reference-item-id', '');
    $input.html('');
});

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   プルダウン選択の初期値
//
////////////////////////////////////////////////////////////////////////////////////////////////////
const setEventPulldownDefaultValue = function($item){
    $item.on('change', '.menu-column-type-select, .pulldown-select', function(){
        let typeId;

        if($(this).hasClass('menu-column-type-select')){
            typeId = $(this).val();
        }

        if($(this).hasClass('pulldown-select')){
            typeId = $item.find('.menu-column-type-select').val();
        }

        //「プルダウン選択」時のみ
        if(typeId == 7){
            getpulldownDefaultValueList($item, "");
        }

    });
}

const getpulldownDefaultValueList = function($item, defaultValue = ""){
  let loadNowSelect = '<option value="">' + getMessage.FTE01131 + '</option>';
  let faildSelect = '<option value="">' + getMessage.FTE01132 + '</option>';
  $item.find('.pulldown-default-select').html(loadNowSelect); //最初に読み込み中メッセージのセレクトボックスを挿入

  let menu = "",
      column = "";
  //「選択項目」のメニューで初期値として利用可能な値のリストを作成する。
  let selectDefaultValueList;
  let value = $item.find('.pulldown-select').val();
  for (let i = 0; i < menuEditorArray.pulldown_item_list.length; i++) {
    if ( menuEditorArray.pulldown_item_list[i].link_id == value ) {
      menu = menuEditorArray.pulldown_item_list[i].menu_name_rest;
      column = menuEditorArray.pulldown_item_list[i].column_name_rest;
    }
  }
  const restInitialUrl = '/create/define/pulldown/initial/' + menu + '/' + column + '/';
  fn.fetch( restInitialUrl ).then(function( result ) {
      //選択可能な参照項目の一覧を取得し、セレクトボックスを生成
      selectDefaultValueList = result;
      /*if ( selectDefaultValueList[0] == 'redirectOrderForHADACClient' ) {
        window.alert( selectDefaultValueList[2] );
        var redirectUrl = selectDefaultValueList[1][1] + location.search.replace('?','&');
        return redirectTo(selectDefaultValueList[1][0], redirectUrl, selectDefaultValueList[1][2]);
      }
      */
      let selectPulldownDefaultListHTML = '<option value=""></option>'; //一つ目に空を追加
      let defaultCheckFlg = false;
      for ( let key in selectDefaultValueList ) {
        if(defaultValue == key){
          selectPulldownDefaultListHTML += '<option value="' + key + '" selected>' + selectDefaultValueList[key] + '</option>';
          defaultCheckFlg = true;
        }else{
          selectPulldownDefaultListHTML += '<option value="' + key + '">' + selectDefaultValueList[key] + '</option>';
        }
      }
        //デフォルト値を持っているが一致するレコードが無い場合、ID変換失敗(ID)の選択肢を追加。
        if(defaultCheckFlg == false && defaultValue){
          selectPulldownDefaultListHTML += '<option value="' + defaultValue + '" selected>' + getMessage.FTE01133 + "{0:" + defaultValue + "}" + '</option>';
        }
        $item.find('.pulldown-default-select').html(selectPulldownDefaultListHTML);
        history.add(); //historyを更新
  }).catch(function ( e ) {
    alert( e );
    selectDefaultValueList = null;
    //エラーメッセージ入りセレックとボックスを挿入
    $item.find('.pulldown-default-select').html(faildSelect);
    history.add(); //historyを更新
  });
}

const resetEventPulldownDefaultValue = function($menuTable){
    const $item = $menuTable.find('.menu-column');
    $item.each(function(){
        setEventPulldownDefaultValue($(this));
    });
}

$menuEditWindow.on('click', '.inputDateCalendarButton', function(){
    const $button = $( this ),
          $input = $button.closest('.inputDateContainer').find('.callDateTimePicker'), // 対象のinput textを指定する
          value = $input.val(),
          id = $input[0].id;

    let flg,
        name;
    if ( id === 'dateTime' ){
        flg = true;
        name = getMessage.FTE01134;
    } else {
        flg = false;
        name = getMessage.FTE01135;
    }

    fn.datePickerDialog('date', flg, name, value ).then(function( result ){
        if ( result !== 'cancel') {
            $input.val( result.date ).change().focus().trigger('input');
        }
    });
});

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   メニュー
//
////////////////////////////////////////////////////////////////////////////////////////////////////

$menuEditor.find('.menu-editor-menu-button').on('click', function() {
    const $button = $( this ),
        buttonType = $button.attr('data-type');

    let url_path,
        splitstr,
        organization_id,
        workspace_id,
        menu;

    switch ( buttonType ) {
        case 'newColumn':
            const $newColumnTarget = addColumn( $menuTable, 'column');
            //editの場合disabledを外す。
            if(menuEditorMode === 'edit'){
                $newColumnTarget.find('.menu-column-type-select').prop('disabled', false); //カラムタイプ
                $newColumnTarget.find('.config-select'+'.pulldown-select').prop('disabled', false); //選択項目
                $newColumnTarget.find('.config-text'+'.reference-item').prop('disabled', false); //参照項目
                $newColumnTarget.find('.config-select'+'.reference-parameter-sheet').prop('disabled', false); //パラメータシート参照の選択項目
                $newColumnTarget.find('.reference-item-select').prop('disabled', false); //参照項目を選択ボタン
                $newColumnTarget.find('.config-checkbox'+'.required').prop('disabled', false); //必須
                $newColumnTarget.find('.required-label').removeAttr('disabled'); //必須
                $newColumnTarget.find('.config-checkbox'+'.unique').prop('disabled', false); //一意制
                $newColumnTarget.find('.unique-label').removeAttr('disabled'); //一意制
                $newColumnTarget.find('.config-checkbox'+'.required').removeClass('disabled-checkbox'); //必須のチェックボックスの色約
                $newColumnTarget.find('.config-checkbox'+'.unique').removeClass('disabled-checkbox'); //一意制約のチェックボックスの色
                $newColumnTarget.find('.required-label').addClass('on-hover'); //必須のカーソル動作
                $newColumnTarget.find('.unique-label').addClass('on-hover'); //一意制約のカーソル動作
            }
            //プルダウン選択の初期値を取得するイベントを設定
            setEventPulldownDefaultValue($newColumnTarget);
            break;
        case 'newColumnGroup':
            addColumn( $menuTable, 'group');
            break;
        case 'undo':
            history.undo();
            break;
        case 'redo':
            history.redo();
            break;
        case 'registration':
            $button.prop('disabled', true );
            fn.iconConfirm('plus', getMessage.FTE10059, getMessage.FTE01136 ).then(function( flag ){
                if ( flag ) {
                    registrationMenu('create_new').catch(function(){
                    $button.prop('disabled', false );
                  });
                } else {
                  $button.prop('disabled', false );
                }
            });
            break;
        case 'update-initialize':
            $button.prop('disabled', true );
            //メニュー作成状態が「未作成」の場合、windowメッセージを変更
            if(menuEditorArray['menu_info']['menu']['menu_create_done_status_id'] == 1){
                fn.iconConfirm('plus', getMessage.FTE10059, getMessage.FTE01136 ).then(function( flag ){
                    if ( flag ) {
                      registrationMenu('create_new').catch(function(){
                        $button.prop('disabled', false );
                      });
                    } else {
                      $button.prop('disabled', false );
                    }
                });
            }else{
                fn.iconConfirm('plus', getMessage.FTE10059, getMessage.FTE01137 ).then(function( flag ){
                    if ( flag ) {
                      registrationMenu('initialize').catch(function(){
                        $button.prop('disabled', false );
                      });
                    } else {
                      $button.prop('disabled', false );
                    }
                });
            }
            break;
        case 'update':
          $button.prop('disabled', true );
            fn.iconConfirm('plus', getMessage.FTE10059, getMessage.FTE01138 ).then(function( flag ){
                if ( flag ) {
                  registrationMenu('edit').catch(function(){
                    $button.prop('disabled', false );
                  });
                } else {
                  $button.prop('disabled', false );
                }
            });
            break;
        case 'management':
            //uuidでフィルターされたメニュー作成履歴画面へ移動
            url_path = location.pathname;
            splitstr = url_path.split('/');
            organization_id = splitstr[1];
            workspace_id = splitstr[3];
            const uuid = getParam('history_id');
            const filter = encodeURIComponent( JSON.stringify( {"uuid":{"NORMAL": uuid }} ) );
            const hisUrl = '/' + organization_id + '/workspaces/' + workspace_id + '/ita/?menu=menu_creation_history&filter=' + filter;
            location.replace( hisUrl );
            break;
        case 'initialize':
        case 'reload-initialize':
            // 初期化モードで開きなおす
            menuEditorTargetID = $('#menu-editor').attr('data-load-menu-id');
            url_path = location.pathname;
            splitstr = url_path.split('/');
            organization_id = splitstr[1];
            workspace_id = splitstr[3];
            menu = getParam('menu');
            window.location.href = '/' + organization_id + '/workspaces/' + workspace_id + '/ita/?menu=' + menu + '&menu_name_rest=' + menuEditorTargetID + '&mode=initialize';
            break;
        case 'edit':
        case 'reload':
            // 編集モードで開きなおす
            menuEditorTargetID = $('#menu-editor').attr('data-load-menu-id');
            url_path = location.pathname;
            splitstr = url_path.split('/');
            organization_id = splitstr[1];
            workspace_id = splitstr[3];
            menu = getParam('menu');
            window.location.href = '/' + organization_id + '/workspaces/' + workspace_id + '/ita/?menu=' + menu + '&menu_name_rest=' + menuEditorTargetID + '&mode=edit';
            break;
        case 'diversion':
            // 流用新規モードで開きなおす
            menuEditorTargetID = $('#menu-editor').attr('data-load-menu-id');
            url_path = location.pathname;
            splitstr = url_path.split('/');
            organization_id = splitstr[1];
            workspace_id = splitstr[3];
            menu = getParam('menu');
            window.location.href = '/' + organization_id + '/workspaces/' + workspace_id + '/ita/?menu=' + menu + '&menu_name_rest=' + menuEditorTargetID + '&mode=diversion';
            break;
        case 'cancel':
            // 閲覧モードで開きなおす
            menuEditorTargetID = $('#menu-editor').attr('data-load-menu-id');
            url_path = location.pathname;
            splitstr = url_path.split('/');
            organization_id = splitstr[1];
            workspace_id = splitstr[3];
            menu = getParam('menu');
            window.location.href = '/' + organization_id + '/workspaces/' + workspace_id + '/ita/?menu=' + menu + '&menu_name_rest=' + menuEditorTargetID;
            break;
        case 'fullscreen':
            fn.fullScreen();
            break;
        case 'jsonSave':
            const inputName = $('#create-menu-name').val();
            const fileName = ( inputName !== '')? inputName: 'parameter_sheet';
            fn.download('json', createJsonData('file'), fileName );
            break;
        case 'jsonRead':
            fn.fileSelect('json').then(function( result ){
                try {
                    // リセット
                    menuEditorArray.menu_info = result.json;
                    menuIdList = [];
                    uniquechangecount = 0;
                    uniquedeletecount = 0;
                    setMenu('jsonRead');
                } catch ( e ) {
                    console.error( e );
                    alert( getMessage.FTE01157 );
                    clearTable();
                }
            }).catch(function( e ){
                if ( e === 'cancel') return;
                console.error( e );
                alert( e );
                clearTable();
            });
            break;
    }
});

// 表示クリア
const clearTable = function() {
    $menuTable.empty();
    emptyCheck();
    previewTable();
    $('#unique-constraint-list').text('').attr('data-unique-list', '');
    uniquechangecount = 0;
    uniquedeletecount = 0;

    menuIdList = [];
    itemCounter = 1;
    groupCounter = 1;
}

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   タイトル入力幅調整
//
////////////////////////////////////////////////////////////////////////////////////////////////////

const titleInputChange = function( $input ) {
    const inputValue = $input.val();
    $input.next().text( inputValue );
    const inputWidth = $input.next().outerWidth() + 6;
    $input.attr('value', inputValue ).css('width', inputWidth );
};
$('.menu-column-title-input').each( function(){
    titleInputChange( $(this) );
});
$('.menu-column-title-rest-input').each( function(){
  titleInputChange( $(this) );
});
$menuEditor.on({
    'input' : function () {
        if ( $( this ).is('.menu-column-title-input') ) {
            titleInputChange( $( this ) );
        }
        if ( $( this ).is('.menu-column-title-rest-input') ) {
          titleInputChange( $( this ) );
      }
    },
    'change' : function() {
        if ( $( this ).is('.menu-column-title-input') ) {
            history.add();
            previewTable();
            updateUniqueConstraintDispData();
        }
        if ( $( this ).is('.menu-column-title-rest-input') ) {
          history.add();
          previewTable();
          updateUniqueConstraintDispData();
      }
    },
    'focus' : function() {
        // $(this).focus().select(); Edge対応版
        $( this ).click( function(){
            $( this ).select();
        });
    },
    'blur' : function() {
        getSelection().removeAllRanges();
    },
    'mousedown' : function( e ) {
        e.stopPropagation();
    }
}, '.menu-column-title-input, .menu-column-title-rest-input, .menu-column-repeat-number-input');

  // input欄外でも選択可能にする
$menuEditor.on({
    'mousedown' : function() {
        if ( menuEditorMode !== 'view') {
            const $input = $( this );
            setTimeout( function(){
                $input.find('.menu-column-title-input, .menu-column-title-rest-input, .menu-column-repeat-number-input').focus().select();
            }, 1 );
        }
    }
}, '.menu-column-title, .menu-column-repeat-number');

$menuEditor.on({
    'focus' : function() {
        $( this ).addClass('text-in');
    },
    'blur' : function() {
        if ( $( this ).val() === '' ) {
            $( this ).removeClass('text-in');
        }
    }
}, '.config-textarea');

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   設定内容をHTMLに反映させる（履歴HTML用）
//
////////////////////////////////////////////////////////////////////////////////////////////////////

$menuEditor.on('change', '.config-text', function() {
    $( this ).attr('value', $( this ).val() );
    previewTable();
    history.add();
});
$menuEditor.on('change', '.config-number, .menu-column-repeat-number-input, .property-number', function() {
    const $input = $( this ),
        min = Number( $input.attr('data-min') ),
        max = Number( $input.attr('data-max') );
    let value = $input.val();

    // 桁数が未入力の場合、最大値を入れる
    if ( $input.is('.digit-number') && value === '') {
        value = max;
    }
    if ( min !== undefined && value < min ) value = min;
    if ( max !== undefined && value > max ) value = max;

    $input.val( value ).attr('value', value );

    previewTable();
    history.add();
});
$menuEditor.on('change', '.config-textarea', function() {
    $( this ).text( $( this ).val() );
    previewTable();
    history.add();
});
$menuEditor.on('change', '.config-checkbox', function() {
    $( this ).attr('checked', $( this ).prop('checked') );
    previewTable();
    history.add();
});
$menuEditor.on('change', '.config-select', function() {
    const $select = $( this ),
        value = $select.val();
    // selectedを削除してからだと画面に反映されない？
    $select.find('option[value="' + value + '"]').attr('selected', 'selected');
    $select.find('option').not('[value="' + value + '"]').attr('selected', false);
    previewTable();
    history.add();
});

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   項目の種類によって入力項目を切り替える
//
////////////////////////////////////////////////////////////////////////////////////////////////////

$menuEditor.on('change', '.menu-column-type-select', function() {
    const $select = $( this ),
        $config = $select.closest('.menu-column-type')
            .next('.menu-column-config').find('.menu-column-config-table'),
        value = $select.val();
    $config.attr('date-select-value', value );
    $select.find('option[value="' + value + '"]').attr('selected', true);
    $select.find('option').not('[value="' + value + '"]').attr('selected', false);
    previewTable();
    history.add();
});

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   項目、グループの移動
//
////////////////////////////////////////////////////////////////////////////////////////////////////

$menuEditor.on('mousedown', '.menu-column-move', function( e ){

    // 左クリックチェック
    if (e.which !== 1 ) return false;

    // 選択を解除しておく
    getSelection().removeAllRanges();

    mode.columnMove();

    const $column = $( this ).closest('.menu-column, .menu-column-group, .menu-column-repeat'),
          $columnClone = $column.clone( false ),
          $targetArea = $('.menu-column, .menu-column-group-header, .menu-column-repeat-header, .menu-column-repeat-footer, .column-empty'),
          scrollTop = $window.scrollTop(),
          scrollLeft = $window.scrollLeft(),
          knobWidth = $( this ).outerWidth(),
          knobHeight = $( this ).outerHeight(),
          mousedownPositionX = e.pageX,
          mousedownPositionY = e.pageY,
          editorX = $menuEditor.offset().left,
          editorWidth = $menuEditWindow.outerWidth();

    // 何を移動するか
    const moveColumnType = $column.attr('class');
    $menuTable.attr('data-move-type', moveColumnType );

    // スクロール可能か調べる
    const $scrollArea = $menuEditWindow.find('.menu-editor-block-inner'),
          scrollWidth = $scrollArea.get(0).scrollWidth + 2,
          scrollAreaWidth = $scrollArea.outerWidth(),
          scrollFlag = ( scrollWidth > scrollAreaWidth ) ? true : false,
          scrollSpeed = 40;

    let scrollTimer = false;

    const scrollMove = function( direction ) {
      if ( scrollTimer === false ) {
        scrollTimer = setInterval( function() {
          const scrollLeft = $scrollArea.scrollLeft();
          let scrollWidth = ( direction === 'right' ) ? scrollSpeed : -scrollSpeed;
          $scrollArea.stop(0,0).animate({ scrollLeft : scrollLeft + scrollWidth }, 40, 'linear' );
        }, 40 );
      }
    };

    let $hoverTarget = null,
        hoverTargetWidth, hoverTargetLeft,
        moveX, moveY;

    $column.addClass('move-wait');

    // 移動用ダミーオブジェ追加
    $menuEditor.append( $columnClone );
    $columnClone.addClass('move').css({
      'left' : ( mousedownPositionX - scrollLeft - knobWidth / 2 ) + 'px',
      'top' : ( mousedownPositionY - scrollTop - knobHeight / 2 ) + 'px'
    });

    // ターゲットの左か右かチェックする
    const leftRightCheck = function( mouseX ) {
      if ( $hoverTarget !== null ) {
        if ( $hoverTarget.parent().is('.menu-column-repeat') ) {
          // リピート
          const $repeatColumn = $hoverTarget.parent('.menu-column-repeat');
          if ( $hoverTarget.is('.menu-column-repeat-header')
              && !$repeatColumn.prev().is( $column ) ) {
            $repeatColumn.addClass('left');
          } else if ( $hoverTarget.is('.menu-column-repeat-footer')
              && !$repeatColumn.next().is( $column ) ) {
            $repeatColumn.addClass('right');
          }
        } else if ( $hoverTarget.is('.column-empty') ) {
          // 空エリアの場合何もしない
          return false;
        } else {
          // その他
          const mousePositionX = mouseX - hoverTargetLeft;
          if ( hoverTargetWidth / 2 > mousePositionX ) {
            $hoverTarget.removeClass('right');
            if ( !$hoverTarget.prev().is( $column ) ) {
              $hoverTarget.addClass('left');
            }
          } else {
            $hoverTarget.removeClass('left');
            if ( !$hoverTarget.next().is( $column ) ) {
              $hoverTarget.addClass('right');
            }
          }
        }
      }
    }

    // どこの上にいるか
    $targetArea.on({
      'mouseenter.columnMove' : function( e ){
        e.stopPropagation();
        // 対象情報
        $hoverTarget = $( this );
        hoverTargetWidth = $hoverTarget.outerWidth();
        hoverTargetLeft = scrollLeft + $hoverTarget.offset().left;
        // 対象が自分以外かどうか
        if ( !$hoverTarget.is( $column ) ) {
          if ( $hoverTarget.is('.menu-column-group-header') ) {
            $hoverTarget = $hoverTarget.closest('.menu-column-group');
          }
          $hoverTarget.addClass('hover');
          $hoverTarget.parents('.menu-column-group, .menu-column-repeat-body').eq(0).addClass('hover-parent');
        } else {
          $hoverTarget = null;
        }

        leftRightCheck( e.pageX );
      },
      'mouseleave.columnMove' : function(){
        $hoverTarget = null;
        $menuTable.find('.hover, .hover-parent, .left, .right').removeClass('hover hover-parent left right');
      }
    });

    let moveTime = '';

    $window.on({
      'mousemove.columnMove' : function( e ) {
        // 仮移動
        if ( moveTime === '') {
          moveX = e.pageX - mousedownPositionX;
          moveY = e.pageY - mousedownPositionY;
          $columnClone.css('transform', 'translate(' + moveX + 'px,' + moveY + 'px)');
          leftRightCheck( e.pageX );

          // 枠の外に移動
          if ( scrollFlag === true ) {
            if ( editorX > e.pageX ) {
              scrollMove('left');
            } else if ( editorX + editorWidth < e.pageX ) {
              scrollMove('right');
            } else if ( scrollTimer ){
              clearInterval( scrollTimer );
              scrollTimer = false;
            }
          }

          moveTime = setTimeout( function() {
            moveTime = '';
          }, 16.667 );
        }
      },
      'mouseup.columnMove' : function() {
        // 対象があれば移動する
        if ( $hoverTarget !== null ) {
          // 移動した際にグループの中身が空になるか判定
          const $parentGroup = $column.parent().closest('.menu-column-group, .menu-column-repeat');
          let emptyFlag = false;
          if ( $parentGroup.length && $column.siblings().length === 0 ) {
            emptyFlag = true;
          }
          // 移動する or 空のグループに追加
          if ( $hoverTarget.is('.column-empty') ) {
            $hoverTarget.closest('.menu-column-group-body, .menu-column-repeat-body').html('').append( $column );
          } else {
            // 右か左か
            if ( $hoverTarget.parent().is('.menu-column-repeat') ) {
              $hoverTarget = $hoverTarget.closest('.menu-column-repeat');
            }
            if ( $hoverTarget.is('.left') ) {
              $column.insertBefore( $hoverTarget );
            } else if ( $hoverTarget.is('.right') ) {
              $column.insertAfter( $hoverTarget );
            }
          }
          // グループが空ならEmpty追加
          if ( emptyFlag === true ) {
            $parentGroup.find('.menu-column-group-body, .menu-column-repeat-body').html( columnEmptyHTML );
          }
          // 高さ更新
          columnHeightUpdate();
        }
        $column.removeClass('move-wait');
        $columnClone.remove();
        $menuTable.find('.hover, .hover-parent, .left, .right').removeClass('hover hover-parent left right');
        $menuTable.removeAttr('data-move-type', moveColumnType );
        $window.off('mousemove.columnMove mouseup.columnMove');
        $targetArea.off('mouseenter.columnMove mouseleave.columnMove');
        clearInterval( scrollTimer );
        mode.clear();
        // 移動した場合のみ履歴追加
        if ( $hoverTarget !== null ) {
          history.add();
        }
        previewTable();
      }
    });

});

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   項目、グループの削除
//
////////////////////////////////////////////////////////////////////////////////////////////////////

// 項目が空かチェックする
const emptyCheck = function() {
    const itemLength = $menuTable.find('.menu-column, .menu-column-group, .menu-column-repeat').length;
    if ( itemLength === 0 ) {
      $menuTable.html('<div class="no-set column-empty"><p>Empty</p></div>');
    } else {
      $menuTable.find('.no-set').remove();
    }
};
// リピートがあるかチェックする
const repeatCheck = function() {
    const $repeatButton = $('.menu-editor-menu-button[data-type="newColumnRepeat"]'),
          type = $('#create-menu-type').val();
    // パラメータシートかつ、縦メニュー利用有無チェック
    if ( ( type === '1' || type === '3' ) && $('#create-menu-use-vertical').prop('checked') ) {
      if ( $menuTable.find('.menu-column-repeat').length === 0 ) {
        $repeatButton.prop('disabled', false );
      } else {
        $repeatButton.prop('disabled', true );
      }
    } else {
      $repeatButton.prop('disabled', true );
    }
  };

  $menuEditor.on('click', '.menu-column-delete', function(){
    const $column = $( this ).closest('.menu-column, .menu-column-group, .menu-column-repeat');
    // 親列グループが空になる場合
    const $parentGroup = $column.parent().closest('.menu-column-group, .menu-column-repeat');
    if ( $parentGroup.length && $column.siblings().length === 0 ) {
      $parentGroup.find('.menu-column-group-body, .menu-column-repeat-body').html( columnEmptyHTML );
    }
    $column.remove();

    if ( $menuEditor.find('.menu-column, .menu-column-group, .menu-column-repeat').length ) {
      // 高さ更新
      columnHeightUpdate();
    }
    history.add();
    emptyCheck();
    repeatCheck();
    previewTable();
    const columnId = $column.attr('id');
    deleteUniqueConstraintDispData(columnId); //一意制約(複数項目)で削除した項目を除外する。
});

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   項目、グループの複製
//
////////////////////////////////////////////////////////////////////////////////////////////////////

// select2を再適用
const resetSelect2 = function( $target ) {
    if ( $target.find('.select2-container').length ) {
      // select2要素を削除
      $target.find('.config-select').removeClass('select2-hidden-accessible').removeAttr('tabindex aria-hidden data-select2-id');
      $target.find('option').removeAttr('data-select2-id');
      $target.find('.select2-container').remove();
      // select2を再適用
      $target.find('.config-select').select2();
    }
};

$menuEditor.on('click', '.menu-column-copy', function(){
  const $column = $( this ).closest('.menu-column, .menu-column-group');

  const $clone = $column.clone();
  $column.after( $clone );

  // 追加を待つ
  $clone.ready( function() {

    $clone.find('.hover').removeClass('hover');

    // IDをプラス・名前にコピー番号を追加
    $clone.find('.menu-column-title-input').each( function() {
      const $input = $( this ),
            title = $input.val(),
            $eachColumn = $input.closest('.menu-column, .menu-column-group');

      if ( $eachColumn.is('.menu-column') ) {
        const i = itemCounter++;
        $input.val( title );
        $eachColumn.attr({
          'id': 'c' + i,
          'data-item-id': ''
        });
      } else if ( $eachColumn.is('.menu-column-group') ) {
        const g = groupCounter++;
        $input.val( title + '(' + g + ')' );
        $eachColumn.attr({
          'id': 'g' + g,
          'data-group-id': ''
        });
      }
      $input.attr('value', $input.val() );
      titleInputChange( $input );
    });

    // 複製した項目の無効状態を解除する
    $clone.find(':disabled').prop('disabled', false );
    $clone.find('.disabled-checkbox').removeClass('disabled-checkbox');
    $clone.find('.required-label, .unique-label').removeAttr('disabled').addClass('on-hover');

    resetSelect2( $clone );

    // プルダウン選択の初期値取得eventを再適用する
    resetEventPulldownDefaultValue( $menuTable );
    // パラメータ参照の項目取得eventを再適用する
    // resetEventPulldownParameterSheetReference( $menuTable );

    history.add();
    previewTable();

    // コピーした項目に合わせスクロールさせる
    const $scrollArea = $menuEditWindow.children(),
          scrollElement = $scrollArea.get(0),
          scrollAreaWidth = $scrollArea.outerWidth(),
          scrollLeft = $scrollArea.scrollLeft(),
          scrollWidth = scrollElement.scrollWidth,
          clientWidth = scrollElement.clientWidth,
          editorLeft = scrollElement.getBoundingClientRect().left,
          cloneLeft = $clone.get(0).getBoundingClientRect().left + scrollLeft - editorLeft,
          cloneWidth = $clone.outerWidth(),
          padding = 8;

    // スクロール可能か？
    if ( clientWidth < scrollWidth && scrollLeft + scrollAreaWidth < cloneLeft + cloneWidth ) {
        const left = ( cloneLeft + cloneWidth ) - scrollAreaWidth + padding;
        $menuEditWindow.children().stop(0,0).animate({'scrollLeft': left }, 200 );
    }

  });
});

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   行数を調べる
//
////////////////////////////////////////////////////////////////////////////////////////////////////

const rowNumberCheck = function(){
    let maxLevel = 1;
    $menuTable.find('.menu-column, .column-empty').each( function(){
        const $column = $( this ),
            columnLevel = $column.parents('.menu-column-group').length + 1;
        if ( maxLevel < columnLevel ) maxLevel = columnLevel;
    });
    return maxLevel;
};

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   列の高さ更新
//
////////////////////////////////////////////////////////////////////////////////////////////////////

const columnHeightUpdate = function(){

    const maxLevel = rowNumberCheck();

    // 列の高さ調整
    $menuTable.find('.menu-column').each( function(){
        const $column = $( this ),
            columnLevel = $column.parents('.menu-column-group').length,
            rowspan = maxLevel - columnLevel;
        $column.attr('data-rowpan', rowspan );
        $column.find('.menu-column-header').css('height', titleHeight * rowspan + titleHeight );
    });
};

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   リピート数変更
//
////////////////////////////////////////////////////////////////////////////////////////////////////

$menuTable.on({
    'click' : function() {
        $( this ).addClass()
    }
}, '.menu-column-repeat-number');

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   プレビュー
//
////////////////////////////////////////////////////////////////////////////////////////////////////

// プレビュー用HTML
const sortMark = '<span class="sortMarkWrap"><span class="sortNotSelected"></span></span>',
      tHeadHeaderLeftHTML = ''
        + '<th class="tHeadTh tHeadLeftSticky tHeadRowSelect th" rowspan="{{rowspan}}"><div class="ci"><button class="rowSelectButton button"><span class="inner"></span></button></div></th>'
        + '<th class="tHeadTh tHeadLeftSticky tHeadRowMenu th" rowspan="{{rowspan}}"><div class="ci"><span class="icon icon-ellipsis_v  "></span></div></th>'
        + '<th rowspan="{{rowspan}}" class="tHeadLeftSticky tHeadTh tHeadLeftStickyLast tHeadSort th"><div class="ci">' + getMessage.FTE01010 +'</div></th>',
      tHeadParameterHeaderLeftHTML = ''
        + '<th rowspan="{{rowspan}}" class="tHeadTh tHeadSort th"><div class="ci">' + getMessage.FTE01065 + '</div></th>'
        + '<th colspan="4" class="tHeadGroup tHeadTh th"><div class="ci">' + getMessage.FTE01066 + '</div></th>'
        + '<th colspan="{{colspan}}" class="tHeadGroup tHeadTh th"><div class="ci">' + getMessage.FTE01067 + '</div></th>',
      tHeadOperationrHeaderLeftHTML = ''
        + '<th colspan="4" class="tHeadGroup tHeadTh th"><div class="ci">' + getMessage.FTE01066 + '</div></th>'
        + '<th colspan="{{colspan}}" class="tHeadGroup tHeadTh tHeadSort th"><div class="ci">' + getMessage.FTE01067 + '</div></th>',
      tHeadParameterOpeHeaderLeftHTML = ''
        + '<th rowspan="{{rowspan}}" class="tHeadTh tHeadSort th"><div class="ci">' + getMessage.FTE01068 + '</div></th>'
        + '<th rowspan="{{rowspan}}" class="tHeadTh tHeadSort th"><div class="ci">' + getMessage.FTE01069 + '</div></th>'
        + '<th rowspan="{{rowspan}}" class="tHeadTh tHeadSort th"><div class="ci">' + getMessage.FTE01070 + '</div></th>'
        + '<th rowspan="{{rowspan}}" class="tHeadTh tHeadSort th"><div class="ci">' + getMessage.FTE01071 + '</div></th>',
      tHeadHeaderRightHTML = ''
        + '<th rowspan="{{rowspan}}" class="tHeadTh tHeadSort th"><div class="ci">' + getMessage.FTE01072 + '</div></th>'
        + '<th rowspan="{{rowspan}}" class="tHeadTh tHeadSort th"><div class="ci">' + getMessage.FTE01073 + '</div></th>'
        + '<th rowspan="{{rowspan}}" class="tHeadTh tHeadSort th"><div class="ci">' + getMessage.FTE01074 + '</div></th>',

      tBodyHeaderLeftHTML = ''
        + '<th class="tBodyLeftSticky tBodyRowSelect tBodyTh th"><div class="ci"><div class="checkboxWrap"><input type="checkbox" class="tBodyRowCheck checkbox"><label class="checkboxLabel"></label></div></div></th>'
        + '<th class="tBodyLeftSticky tBodyRowMenu tBodyTh th"><div class="ci"><span class="icon icon-ellipsis_v"></span></div></th>'
        + '<th class="tBodyLeftSticky tBodyTh th"><div class="ci">XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX</div></th>',
      tBodyParameterHeaderLeftHTML = ''
        + '<td class="tBodyTd td"><div class="ci">192.168.0.1</td>'
        + '<td class="tBodyTd td"><div class="ci">' + getMessage.FTE01075 + '</div></td>'
        + '<td class="tBodyTd td"><div class="ci">2020/01/01 00:00</div></td>'
        + '<td class="tBodyTd td"><div class="ci">2020/01/01 00:00</div></td>'
        + '<td class="tBodyTd td"><div class="ci"></td>',
      tBodyOperationHeaderLeftHTML = ''
        + '<td class="tBodyTd td"><div class="ci">' + getMessage.FTE01075 + '</div></td>'
        + '<td class="tBodyTd td"><div class="ci">2020/01/01 00:00</div></td>'
        + '<td class="tBodyTd td"><div class="ci">2020/01/01 00:00</div></td>'
        + '<td class="tBodyTd td"><div class="ci"></div></td>',
      tBodyHeaderRightHTML = ''
        + '<td class="tBodyTd td"><div class="ci"></div></td>'
        + '<td class="tBodyTd td"><div class="ci">2020/01/01 00:00:00</div></td>'
        + '<td class="tBodyTd td"><div class="ci">' + getMessage.FTE01076 + '</div></td>';

// リピートを含めた子の列数を返す
const childColumnCount = function( $column, type ) {
  let counter = $column.find('.menu-column, .column-empty').length;
  const menuColumnBody = $column.find('.menu-column');
  menuColumnBody.each(function(){
    const selectTypeValue = $(this).find('.menu-column-type-select').val();
    //プルダウン選択の場合、参照項目の数だけcounterを追加
    if(selectTypeValue == '7'){
        const referenceItem = $(this).find('.reference-item');
        referenceItem.each(function(){
            //リピート内の場合はカウントしない
            if($(this).parents('.menu-column-repeat').length == 0){
                const referenceItemValue = $( this ).attr('data-reference-item-id');
                if(referenceItemValue != null && referenceItemValue != ""){ //空もしくはundefinedではない場合
                    const referenceItemAry = referenceItemValue.split(',');
                    counter = counter + referenceItemAry.length;
                }
            }

            //リピート内かつグループ内の場合はカウント
            if(type == 'group' && $column.parents('.menu-column-repeat').length != 0 && $column.find('.menu-column-group-header').length != 0){
                const referenceItemValue = $( this ).attr('data-reference-item-id');
                if(referenceItemValue != null && referenceItemValue != ""){ //空もしくはundefinedではない場合
                    const referenceItemAry = referenceItemValue.split(',');
                    counter = counter + referenceItemAry.length;
                }
            }
        });
    }
  });

  $column.find('.menu-column-repeat').each( function() {
    const columnLength = $( this ).find('.menu-column, .column-empty').length;
    if ( columnLength !== 0 ) {
        const repeatNumberInput = Number( $( this ).find('.menu-column-repeat-number-input').val());
        let referenceItemCount = 0;
        //プルダウン選択の場合、参照項目の数だけcounterを追加
        const repeatMenuColumnBody = $(this).find('.menu-column');
        repeatMenuColumnBody.each(function(){
            const repeatSelectTypeValue = $(this).find('.menu-column-type-select').val();
            if(repeatSelectTypeValue == '7'){
                const referenceItem = $(this).find('.reference-item');
                referenceItem.each(function(){
                    const referenceItemValue = $(this).attr('data-reference-item-id');
                    if(referenceItemValue != null && referenceItemValue != ""){ //空もしくはundefinedではない場合
                        const referenceItemAry = referenceItemValue.split(',');
                        referenceItemCount = referenceItemCount + Number( referenceItemAry.length );
                    }
                });
            }
        });

        counter = counter + ( (columnLength * (repeatNumberInput -1)) + ((referenceItemCount) * repeatNumberInput) );
    }
  });

  return counter;
}

// プレビューを表示する
const previewTable = function(){

  let tableArray = [],
      tbodyArray = [],
      theadHTML = '',
      tableHTML = '',
      tbodyNumber = 3,
      maxLevel = rowNumberCheck();

  // パラメータシート or データシート
  const previewType = Number( $property.attr('data-menu-type') );

  // エディタ要素をTableに変換
  const tableAnalysis = function( $cols, repeatCount ) {

    // 自分の階層を調べる
    const currentFloor = $cols.children().parents('.menu-column-group').length;
    // 配列がUndefinedなら初期化
    if ( tableArray[ currentFloor ] === undefined ) tableArray[ currentFloor ] = [];
    // 子セルを調べる
    $cols.children().each( function(){
        const $column = $( this );

        if ( $column.is('.menu-column') ) {
          // 項目ここから
            const selectTypeValue = $column.find('.menu-column-type-select').val();
            // Head
            const rowspan = $column.attr('data-rowpan');
            let itemHTML = '<th rowspan="' + rowspan + '" class="tHeadTh tHeadSort th"><div class="ci">'
                          + textEntities( $column.find('.menu-column-title-input').val() );
            if ( repeatCount > 1 ) {
              itemHTML += '[' + repeatCount + ']';
            }
            itemHTML += '</div></th>';
            tableArray[ currentFloor ].push( itemHTML );

            //プルダウン選択の参照項目
            if(selectTypeValue == '7'){
                const referenceItemValue = $column.find('.reference-item').attr('data-reference-item-id');
                const referenceItemName = $column.find('.reference-item').html();
                if(referenceItemValue != null && referenceItemValue != ""){ //空もしくはundefinedではない場合
                    const referenceItemAry = referenceItemValue.split(',');
                    const referenceItemNameAry = referenceItemName.split(',');
                    const referenceItemLength = referenceItemAry.length;
                    for ( let i = 0; i < referenceItemLength; i++ ) {
                        let referenceItemHTML = '<th rowspan="' + rowspan + '" class="tHeadTh tHeadSort th"><div class="ci">'+referenceItemNameAry[i];
                        if ( repeatCount > 1 ) {
                            referenceItemHTML += '[' + repeatCount + ']';
                        }
                        referenceItemHTML += sortMark + '</div></th>';
                        tableArray[ currentFloor ].push( referenceItemHTML );
                    }
                }
            }

            // Body
            let dummyText = selectDummyText[ selectTypeValue ][ 0 ],
                dummyType = selectDummyText[ selectTypeValue ][ 2 ];
            if ( dummyType === 'select' ) {
              dummyText = $column.find('.pulldown-select').find('option:selected').text();
            }
            tbodyArray.push('<td class="tBodyTd td ' + dummyType + '"><div class="ci">' + dummyText + '</div></td>');

            //プルダウン選択の参照項目
            if(selectTypeValue == '7'){
                const referenceItemValue = $column.find('.reference-item').attr('data-reference-item-id');
                const referenceItemName = $column.find('.reference-item').html();
                if(referenceItemValue != null && referenceItemValue != ""){ //空もしくはundefinedではない場合
                    const referenceItemAry = referenceItemValue.split(',');
                    const referenceItemNameAry = referenceItemName.split(',');
                    const referenceItemLength = referenceItemAry.length;
                    for ( let i = 0; i < referenceItemLength; i++ ) {
                        const referenceItemHTML = '<td class="tBodyTd td reference"><div class="ci">' + getMessage.FTE01088 + '</div></td>';
                        tbodyArray.push(referenceItemHTML);
                    };
                }
            }
          // Item end
        } else if ( $column.is('.menu-column-group') ) {
          // グループ
            const colspan = childColumnCount( $column, 'group' ),
                  groupTitle = textEntities( $column.find('.menu-column-title-input').eq(0).val() ),
                  regexTitle = new RegExp( '<th class="tHeadTh th" colspan=".+">' + groupTitle + '<\/th>'),
                  tableArrayLength = tableArray[ currentFloor ].length - 1;
            let groupHTML = '<th class="tHeadGroup tHeadTh th" colspan="' + colspan + '"><div class="ci">' + groupTitle + '</div></th>';
            if ( repeatCount > 1 && tableArray[ currentFloor ][ tableArrayLength ].match( regexTitle ) ) {
              tableArray[ currentFloor ][ tableArrayLength ] = '<th class="tHeadGroup tHeadTh th" colspan="' + ( colspan * repeatCount ) + '"><div class="ci">' + groupTitle + '</div></th>';
            } else {
              tableArray[ currentFloor ].push( groupHTML );
            }
            tableAnalysis( $column.children('.menu-column-group-body'), repeatCount );
          // Group end
        } else if ( $column.is('.column-empty') ) {
          // 空
            const rowspan = maxLevel - currentFloor;
            tableArray[ currentFloor ].push('<th class="tHeadBlank th empty" rowspan="' + rowspan + '"><div class="ci"></div></th>');
            tbodyArray.push('<td class="tBodyTd td"><div class="ci">Empty</div></td>');
          // Empty end
        }

    });

  };

  // 解析スタート
  tableAnalysis ( $menuTable, 0 );

  // thead HTMLを生成
  const itemLength = childColumnCount( $menuTable, 'menu' );

  if ( previewType === 1 || previewType === 3 ) {
    maxLevel++;
    tableArray.unshift('');
  }
  const tableArrayLength = tableArray.length;
  for ( let i = 0; i < tableArrayLength; i++ ) {
    theadHTML += '<tr class="tHeadTr headerTr tr">';
    if ( i === 0 ) {
      theadHTML += tHeadHeaderLeftHTML.replace(/{{rowspan}}/g, maxLevel );
      if ( previewType === 1 ) {
        theadHTML += tHeadParameterHeaderLeftHTML
          .replace(/{{rowspan}}/g, maxLevel )
          .replace(/{{colspan}}/g, itemLength );
      }
      if ( previewType === 3 ) {
        theadHTML += tHeadOperationrHeaderLeftHTML
          .replace(/{{rowspan}}/g, maxLevel )
          .replace(/{{colspan}}/g, itemLength );
      }
    }
    if ( i === 1 && previewType === 1 || i === 1 && previewType === 3 ) {
      theadHTML += tHeadParameterOpeHeaderLeftHTML.replace(/{{rowspan}}/g, maxLevel - 1 );
    }
    theadHTML += tableArray[i];
    if ( i === 0 ) {
      theadHTML += tHeadHeaderRightHTML.replace(/{{rowspan}}/g, maxLevel );
    }
  }

  for ( let i = 1; i <= tbodyNumber; i++ ) {
    tableHTML += '<tr class="tBodyTr tr">' + tBodyHeaderLeftHTML.replace('{{id}}', i );
    if ( previewType === 1 ) {
      tableHTML += tBodyParameterHeaderLeftHTML;
    }
    if ( previewType === 3 ) {
      tableHTML += tBodyOperationHeaderLeftHTML;
    }
    tableHTML += tbodyArray.join() + tBodyHeaderRightHTML + '</tr>';
  }

  // プレビュー更新
  $('#menu-editor-preview').find('.thead').html( theadHTML );
  $('#menu-editor-preview').find('.tbody').html( tableHTML );

};

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   パネル関連
//
////////////////////////////////////////////////////////////////////////////////////////////////////

// 作成対象セレクト
let beforeSelectType = '1';
$('#create-menu-type').on('change', function(){
  const $select = $( this ),
        menuType = $select.val();
  // データタイプに変更した場合、リピートをチェックする
  if ( menuType === '2') {
    const repeatFlag = repeatRemoveConfirm();
    if ( repeatFlag === true ) {
      history.clear();
    } else if ( repeatFlag === false) {
      // 選択を戻す
      $select.val( beforeSelectType );
      return false;
    }
  }
  beforeSelectType = menuType;
  $property.attr('data-menu-type', menuType );
  repeatCheck();
  previewTable();
});

// 縦メニュー利用有無チェックボックス
$('#create-menu-use-vertical').on('change', function(){
    const $checkBox = $( this );
    if ( !$checkBox.prop('checked') ) {
      const repeatFlag = repeatRemoveConfirm();
      if ( repeatFlag === true ) {
        history.clear();
      } else if ( repeatFlag === false ) {
        // チェックしなおす
        $checkBox.prop('checked', true );
        return false;
      }
    }
    repeatCheck();
});

// リピートを解除するか確認する
const repeatRemoveConfirm = function() {
    // リピートを使用しているか？
    const $repeat = $menuEditor.find('.menu-column-repeat').eq(0);
    if ( $repeat.length ) {
      if ( confirm( getMessage.FTE01078 ) ) {
        // リピートが空か？
        if ( $repeat.children('.menu-column-repeat-body').children('.column-empty').length ) {
          $repeat.remove();
        } else {
          // 中身をリピートと入れ替える
          $repeat.replaceWith( $repeat.children('.menu-column-repeat-body').html() );
          // select2を再適用する
          resetSelect2( $menuTable );
          // datetimepickerを再適用する
          //resetDatetimepicker( $menuTable );
          // プルダウン選択の初期値取得eventを再適用する
          resetEventPulldownDefaultValue( $menuTable );
          // // パラメータ参照の項目取得eventを再適用する
          // resetEventPulldownParameterSheetReference( $menuTable );
        }
        emptyCheck();
        previewTable();
        return true;
      } else {
        return false;
      }
    } else {
      return undefined;
    }
};

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   項目横幅変更
//
////////////////////////////////////////////////////////////////////////////////////////////////////

const $columnResizeLine = $('#column-resize'),
      defMinWidth = 260;
$menuEditor.on('mousedown', '.column-resize', function( e ) {

  // 左クリックチェック
  if ( e.which !== 1 ) return false;

  mode.columnResize();

  const $column = $( this ).closest('.menu-column'),
        width = $column.outerWidth(),
        positionX = $column.offset().left - $menuEditor.offset().left - 1,
        mouseDownX = e.pageX;

  let minWidth;

  $columnResizeLine.show().css({
    'left' : positionX,
    'width' : width
  });

  $window.on({
    'mousemove.columnResize' : function( e ) {
      const moveX = e.pageX - mouseDownX;
      minWidth = width + moveX;
      if ( defMinWidth > minWidth ) minWidth = defMinWidth;
      $columnResizeLine.show().css({
        'width' : minWidth
      });
    },
    'mouseup.columnResize' : function() {
      $window.off('mouseup.columnResize mousemove.columnResize');
      mode.clear();
      $columnResizeLine.hide();
      $column.css('min-width', minWidth );
      // サイズが変わったら履歴追加
      if ( width !== $column.outerWidth() ) {
        history.add();
      }
    }
  });

});

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   エディタウィンドウリサイズ
//
////////////////////////////////////////////////////////////////////////////////////////////////////

$('#menu-editor-row-resize').on('mousedown', function( e ){

    // 全ての選択を解除する
    getSelection().removeAllRanges();
    mode.blockResize();

    const $resizeBar = $( this ),
          $resizeBlock = $menuEditor.find('.menu-editor-block'),
          $section1 = $resizeBlock.eq(0),
          $section2 = $resizeBlock.eq(1),
          initialPoint = e.clientY,
          minHeight = 64;

    let movePoint = 0,
        newSection1Height = 0;

    // 高さを一旦固定値に
    $resizeBlock.each( function(){
      $( this ).css('height', $( this ).outerHeight() );
    });

    const initialSection1Height = newSection1Height = $section1.outerHeight(),
          initialHeight = initialSection1Height + $section2.outerHeight(),
          maxHeight = initialHeight - minHeight;

    $window.on({
      'mousemove.sizeChange' : function( e ){

        movePoint = e.clientY - initialPoint;

        newSection1Height = initialSection1Height + movePoint;

        if ( newSection1Height < minHeight ) {
          newSection1Height = minHeight;
          movePoint = minHeight - initialSection1Height;
        } else if ( newSection1Height > maxHeight ) {
          newSection1Height = maxHeight;
          movePoint = maxHeight - initialSection1Height;
        }

        $section1.css('height', newSection1Height );
        $section2.css('height', initialHeight - newSection1Height );
        $resizeBar.css('transform','translateY(' + movePoint + 'px)');

      },

      'mouseup.sizeChange' : function(){
        $window.off('mousemove.sizeChange mouseup.sizeChange');
        mode.clear();

        // 高さを割合に戻す
        const section1Ratio = newSection1Height / initialHeight * 100;
        $section1.css('height', section1Ratio + '%' );
        $section2.css('height', ( 100 - section1Ratio ) + '%' );
        $resizeBar.css({
          'transform' : 'translateY(0)',
          'top' : section1Ratio + '%'
        });

      }
    });
});

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//  メニューグループ選択
//
////////////////////////////////////////////////////////////////////////////////////////////////////

const menuGroupBody = function() {

    const menuGroupData = menuEditorArray.target_menu_group_list,
          menuListRowLength = menuGroupData.length,
          menuGroupType = ['for-input','for-substitution','for-reference'],
          menuGroupAbbreviation = [getMessage.FTE01080,getMessage.FTE01081,getMessage.FTE01082],
          menuGroupTypeLength = menuGroupType.length;

    let html = ''
    + '<div id="menu-group-list" class="modal-table-wrap">'
      + '<table class="modal-table">'
        + '<thead>'
          + '<tr>';

    // header Radio
    for ( let i = 0; i < menuGroupTypeLength; i++ ) {
      html += '<th class="th-radio ' + menuGroupType[i] + '" checked>' + menuGroupAbbreviation[i] + '</th>'
    }
    // header Title
    html += '<th class="id">ID</th>'
          + '<th class="name">' + getMessage.FTE01083 + '</th>';

    html += '</tr></thead><tbody><tr>';

    // Unselected Radio
    for ( let i = 0; i < menuGroupTypeLength; i++ ) {
      const radioID = 'radio-' + menuGroupType[i] + '-0';
      html += ''
      + '<th class="th-radio ' + menuGroupType[i] + '">'
        + '<span class="menu-group-radio">'
          + '<input type="radio" class="select-menu radio-number-0" id="' + radioID + '" name="' + menuGroupType[i] + '" value="unselected" data-name="unselected" checked>'
          + '<label class="select-menu-label" for="' + radioID + '"></label>'
        + '</span>'
      + '</th>'
    }

    html += '<td class="unselected" >-</td>'
          + '<td class="unselected" >Unselected</td></tr>';

    // body List
    for ( let i = 0; i < menuListRowLength; i++ ) {
      html += '<tr>';
      // body Radio
      for ( let j = 0; j < menuGroupTypeLength; j++ ) {
        const radioClass = 'select-menu radio-number-' + menuGroupData[i]['menu_group_id'],
              radioID = 'radio-' + menuGroupType[j] + '-' + menuGroupData[i]['menu_group_id'];
        html += ''
        + '<th class="th-radio ' + menuGroupType[j] + '">'
          + '<span class="menu-group-radio">'
            + '<input type="radio" class="' + radioClass +'" id="' + radioID + '" name="' + menuGroupType[j] + '" value="' + menuGroupData[i]['menu_group_id'] + '" data-name="' + menuGroupData[i]['full_menu_group_name'] + '">'
            + '<label class="select-menu-label" for="' + radioID + '"></label>'
          + '</span>'
        + '</th>'
      }
      // Menu group Data
      html += '<td class="id">' + menuGroupData[i]['menu_group_id'] + '</td>'
            + '<td class="name">' + textEntities( menuGroupData[i]['full_menu_group_name'] ) + '</td>';

      html += '</tr>';
    }

    html += '</tbody></table></div>'

    // モーダルにBodyをセット
    const $modalBody = $('.editor-modal-body');
    $modalBody.html( html ).on('change', '.select-menu', function(){
      const $input = $( this ),
            menuID = $input.attr('value'),
            neme = $input.attr('name'),
            checkClass = 'checked-row checked-' + neme;
      $('.checked-' + neme ).removeClass( checkClass )
        .find('.select-menu').prop('disabled', false );

      if ( menuID !== 'unselected' ) {
        $('.radio-number-' + menuID ).closest('tr').addClass( checkClass )
          .find('.select-menu').not(':checked').prop('disabled', true );
      }
    });

    // 選択状態をRadioボタンに反映する
    $('#menu-group').find('.panel-span:visible').each( function(){
      const $item = $( this ),
            type = $item.attr('id').replace('create-menu-',''),
            id = $item.attr('data-id');
      if ( id !== '' ) {
        $modalBody.find('input[name="' + type + '"]').filter('[value="' + id + '"]').prop('checked', true).change();
      }
    });

    // 決定・取り消しボタン
    const $modalButton = $('.editor-modal-footer-menu-button');
    $modalButton.on('click', function() {
      const $button = $( this ),
            type = $button.attr('data-button-type');
      switch( type ) {
        case 'ok':
          // チェック状態を対象メニューグループ選択に反映する
          $('.select-menu:checked').each( function() {
            const $checked = $( this ),
                  checkedType = $checked.attr('name');
            let checkedID = $checked.val(),
                checkedName = $checked.attr('data-name');
            if ( checkedID === 'unselected'){
              checkedID = checkedName = ''
            }
            $('#create-menu-' + $checked.attr('name') ).text( checkedName ).attr({
              'data-id' :  checkedID,
              'data-value' : checkedName
            });
            // 縦メニュー値があるか確認
            if ( checkedType === 'vertical' ) {
              if ( checkedID !== '') {
                $property.attr('data-vertical-menu', true );
              } else {
                $property.attr('data-vertical-menu', false );
              }
            }
          });
          itaModalClose();
          break;
        case 'cancel':
          itaModalClose();
          break;
      }
    });

};

// 対象メニューグループ モーダルを開く
const $menuGroupSlectButton = $('#create-menu-group-select');
$menuGroupSlectButton.on('click', function() {
  let type;
  // パラメータシートorデータシート
  if ( $('#create-menu-type').val() === '1' || $('#create-menu-type').val() === '3' ) {
    type = 'parameter-sheet';
  } else {
    type = 'data-sheet';
  }
  itaModalOpen( getMessage.FTE01077, menuGroupBody, type );
});

// 縦メニューヘルプ
const verticalMenuHelp = function() {
  const $modalBody = $('.editor-modal-body');
  $modalBody.html( $('#vertical-menu-description').html() );
};
$('#vertical-menu-help').on('click', function() {
  itaModalOpen( getMessage.FTE01084, verticalMenuHelp, 'help');
});

// カンマ区切りロールIDリストからロールNAMEリストを返す
const getRoleListIdToName = function( roleListText ) {
    if ( roleListText !== undefined && roleListText !== '') {
      const roleList = roleListText,
            roleListLength = roleList.length,
            roleNameList = new Array;

      for ( let i = 0; i < roleListLength; i++ ) {
        //const roleName = listIdName('role', roleList[i]);
        const roleName = roleList[i];
        if ( roleName !== null ) {
          const hideRoleName = "********";
          if ( roleName !== hideRoleName ) {
            roleNameList.push( roleName );
          } else {
            roleNameList.push( roleName + '(' + roleList[i] + ')');
          }
        } else {
          roleNameList.push( getMessage.FTE01133 + '(' + roleList[i] + ')');
        }
      }
      return roleNameList.join(', ');
    } else {
      return '';
    }
};

// カンマ区切りロールIDリストからID変換失敗を除いたロールIDを返す
const getRoleListValidID = function( roleListText ) {
    if ( roleListText !== undefined && roleListText !== '' ) {
      const roleList = roleListText.split(','),
            roleListLength = roleList.length,
            roleIdList = new Array;
      for ( let i = 0; i < roleListLength; i++ ) {
        const roleName = listIdName('role', roleList[i]);
        if ( roleName !== null ) {
          roleIdList.push( roleList[i] );
        }
      }
      return roleIdList.join(',');
    } else {
      return '';
    }
};

// ロールセレクト
const modalRoleList = function() {
    const $input = $('#permission-role-name-list');
    const initRoleList = ( $input.attr('data-role-id') === undefined )? '': $input.attr('data-role-id');
    // 決定時の処理
    const okEvent = function( newRoleList ) {
      //$input.text( getRoleListIdToName( newRoleList ) ).attr('data-role-id', newRoleList );
      $input.text( newRoleList ).attr('data-role-id', newRoleList );
      itaModalClose();
    };
    // キャンセル時の処理
    const cancelEvent = function( newRoleList ) {
      itaModalClose();
    };

    setRoleSelectModalBody( menuEditorArray.role_list, initRoleList, okEvent, cancelEvent );

};

// ロールセレクトモーダルを開く
const $roleSlectButton = $('#permission-role-select');
$roleSlectButton.on('click', function() {
    itaModalOpen(getMessage.FTE01092, modalRoleList, 'role');
});

//参照項目セレクト
const modalReferenceItemList = function($target) {
    const $input = $target.closest('.menu-column-config-table').find('.reference-item');
    const initItemList = ( $input.attr('data-reference-item-id') === undefined )? '': $input.attr('data-reference-item-id');
    const selectLinkId = $target.closest('.menu-column-config-table').find('.pulldown-select option:selected').val();

    // 決定時の処理
    const okEvent = function( newItemList, extractItemList ) {
      $input.attr('data-reference-item-id', newItemList );
      //newItemListのIDから項目名に変換
      const newItemListArray = newItemList.split(',');
      const newItemNameListArray = [];
      newItemListArray.forEach(function(data){
          newItemNameListArray.push(data);
      });

      //カンマ区切りの文字列に変換に参照項目上に表示
      var newItemNameList = newItemNameListArray.join(',');
      $input.html(newItemNameList);

      previewTable();
      itaModalClose();
    };
    // キャンセル時の処理
    const cancelEvent = function( newItemList ) {
      itaModalClose();
    };
    // 閉じる時の処理
    const closeEvent = function ( newItemList ) {
      itaModalClose();
    }

    //選択されている「プルダウン選択」で選択可能な参照項目のみを取得する
    let targetReferenceItem;
    let menu = "",
    column = "";

    for (let i = 0; i < menuEditorArray.pulldown_item_list.length; i++) {
      if (menuEditorArray.pulldown_item_list[i].link_id == selectLinkId) {
        menu = menuEditorArray.pulldown_item_list[i].menu_name_rest;
        column = menuEditorArray.pulldown_item_list[i].column_name_rest;
      }
    }
    const printReferenceItemURL = '/create/define/reference/item/' + menu + '/' + column + '/';

    //選択可能な参照項目の一覧を取得
    fn.fetch( printReferenceItemURL ).then( function(result) {
        targetReferenceItem = result;
        /*if ( targetReferenceItem[0] == 'redirectOrderForHADACClient' ) {
          window.alert( targetReferenceItem[2] );
          var redirectUrl = targetReferenceItem[1][1] + location.search.replace('?','&');
          return redirectTo(targetReferenceItem[1][0], redirectUrl, targetReferenceItem[1][2]);
        }*/
        setRerefenceItemSelectModalBody(targetReferenceItem, initItemList, okEvent, cancelEvent, closeEvent);
    }).catch( function( e ) {
      targetReferenceItem = null;
      setRerefenceItemSelectModalBody(targetReferenceItem, initItemList, okEvent, cancelEvent, closeEvent);

    });
}

//////////////////////////////////////////////////////
// 参照項目一覧取得・選択
//////////////////////////////////////////////////////
// モーダル Body HTML
function setRerefenceItemSelectModalBody( itemList, initData, okCallback, cancelCallBack, closeCallBack, valueType ) {
  if ( valueType === undefined ) valueType = 'id';
  const $modalBody = $('.editor-modal-body');
  const $modalFooterMenu = $('.editor-modal-footer-menu');

  let itemSelectHTML;

  // 入力値を取得する
  const checkList = ( initData !== null || initData !== undefined )? initData.split(','): [''];

  if ( itemList && itemList.length !== 0 ) {
      itemSelectHTML = '<div class="modal-table-wrap">'
      + '<form id="modal-reference-item-select">'
      + '<table class="modal-table modal-select-table">'
        + '<thead>'
          + '<th class="selectTh">Select</th><th class="name">' + getMessage.FTE01146 + '</th><th class="name">' + getMessage.FTE01147 + '</th>'
        + '</thead>'
        + '<tbody>';


      itemList.forEach(itemName => {
        const itemID = itemName['reference_id'],
              //checkValue = ( valueType === 'name')? itemName: itemID,
              checkValue = itemName,
              checkedFlag = ( checkList.indexOf( checkValue['column_name_rest'] ) !== -1 )? ' checked': '',
              //value = ( valueType === 'name')? itemName: itemID;
              value = itemID;
        itemSelectHTML += '<tr>'
        + '<th><input value="' + itemName['column_name_rest'] + '" class="modal-checkbox" type="checkbox"' + checkedFlag + '></th>'
        + '<td>' + itemName['column_name'] + '</td><td>' + itemName['column_name_rest'] + '</td></tr>';
      });

      itemSelectHTML += ''
          + '</tbody>'
        + '</table>'
        + '</form>'
      + '</div>';
  } else {
      // ボタンを「閉じる」に変更
      $modalFooterMenu.children().remove();
      $modalFooterMenu.append('<li class="editor-modal-footer-menu-item"><button class="editor-modal-footer-menu-button negative" data-button-type="close">' + getMessage.FTE01050 + '</li>');

      // 表示メッセージ
      const noDataMessage = ( itemList.length === 0 )? getMessage.FTE01152: getMessage.FTE01139;
      itemSelectHTML = '<p class="modal-one-message">' + noDataMessage + '</p>';
  }

  $modalBody.html( itemSelectHTML );

  // 行で選択
  $modalBody.find('.modal-select-table').on('click', 'tr', function(){
    const $tr = $( this ),
          checked = $tr.find('.modal-checkbox').prop('checked');
    if ( checked ) {
      $tr.find('.modal-checkbox').prop('checked', false );
    } else {
      $tr.find('.modal-checkbox').prop('checked', true );
    }
  });

  // 決定・取り消しボタン
  const $modalButton = $('.editor-modal-footer-menu-button');
  $modalButton.prop('disabled', false ).on('click', function() {
    const $button = $( this ),
          btnType = $button.attr('data-button-type');
    switch( btnType ) {
      case 'ok':
        // 選択しているチェックボックスを取得
        let checkboxArray = new Array;
        $modalBody.find('.modal-checkbox:checked').each( function(){
          checkboxArray.push( $( this ).val() );
        });
        const newItemList = checkboxArray.join(',');
        okCallback( newItemList, itemList );
        break;
      case 'cancel':
        cancelCallBack();
        break;
      case 'close':
        closeCallBack();
        break;
    }
  });
}


//一意制約(複数項目)
const modalUniqueConstraint = function() {
    //現在の設定値
    const $input = $('#unique-constraint-list');
    const initmodalUniqueConstraintList = ( $input.attr('data-unique-list') === undefined )? '': $input.attr('data-unique-list');

    //表示されている項目のデータを格納
    let $columnItems = $menuTable.find('.menu-column');
    let columnItemData = [];
    let i = 0;
    $columnItems.each(function(){
      let targetItem = $(this);
      let targetItemData = {};
      let columnId = "";
      columnId = targetItem.attr('id');
      //columnId = targetItem.find('.menu-column-title-rest-input').val();
      let itemName = "";
      itemName = targetItem.find('.menu-column-title-rest-input').val();
      let itemId = "";
      itemId = targetItem.attr('data-item-id');
      targetItemData = {
        'columnId': columnId,
        'itemName': itemName,
        'itemId': itemId
      };

      columnItemData[i] = targetItemData;
      i++;
    });

    // 決定時の処理
    const okEvent = function(currentUniqueConstraintArray) {
      const uniqueConstraintData = getUniqueConstraintDispData(currentUniqueConstraintArray);
      const uniqueConstraintConv = uniqueConstraintData.conv;
      const uniqueConstraintName = uniqueConstraintData.name;
      $input.attr('data-unique-list', uniqueConstraintConv); //一意制約のIDの組み合わせをセット
      $input.text(uniqueConstraintName); //一意制約の項目名の組み合わせをセット

      //現在の設定値を更新
      menuEditorArray['unique-constraints-current'] = currentUniqueConstraintArray;

      itaModalClose();
    };
    // キャンセル時の処理
    const cancelEvent = function() {
      itaModalClose();
    };
    // 閉じる時の処理
    const closeEvent = function ( ) {
      itaModalClose();
    }

    setUniqueConstraintModalBody(columnItemData, initmodalUniqueConstraintList, okEvent, cancelEvent, closeEvent);

};

// 一意制約(複数項目)選択のモーダルを開く
const $multiSetUniqueSlectButton = $('#unique-constraint-select');
$multiSetUniqueSlectButton.on('click', function() {
    itaModalOpen( getMessage.FTE01091, modalUniqueConstraint, 'unique' );
});

//一意制約の登録用のcolumnID連結文字列と、表示用の項目名を作成する
const getUniqueConstraintDispData = function(uniqueConstraintArrayData){
    let uniqueConstraintDispData = {
      "conv" : "",
      "name" : ""
    };

    let uniqueConstraintLength = uniqueConstraintArrayData.length;

    if(uniqueConstraintLength == 0){
      return uniqueConstraintDispData;
    }

    let uniqueConstraintConv = "";
    let uniqueConstraintName = "";
    let columnList;
    let columnKey;
    if ( 'menu_info' in menuEditorArray){
      columnList = menuEditorArray.menu_info.column;
    }

    for (let i = 0; i < uniqueConstraintLength; i++){
        let targetIdLength = uniqueConstraintArrayData[i].length;
        let idPatternConv = "";
        let idPatternName = "";
        if(targetIdLength != 0){
          for (let j = 0; j < targetIdLength; j++){
            for (let columnId in uniqueConstraintArrayData[i][j]){
              if( uniquechangecount === 0 && uniquedeletecount === 0 ){
                if ( 'menu_info' in menuEditorArray){
                  for (const column in columnList ){
                    if ( uniqueConstraintArrayData[i][j][columnId] === columnList[column]['item_name_rest'] ){
                      columnKey = column;
                      break;
                    }
                  }
                }
              }

              if(idPatternConv == ""){
                if ( 'menu_info' in menuEditorArray && uniquechangecount === 0 && uniquedeletecount === 0 ){
                  idPatternConv = columnKey;
                } else {
                  idPatternConv = columnId;
                }
              }else{
                if ( 'menu_info' in menuEditorArray && uniquechangecount === 0 && uniquedeletecount === 0 ){
                  idPatternConv = idPatternConv + "-" + columnKey;
                } else {
                  idPatternConv = idPatternConv + "-" + columnId;
                }
              }

              if(idPatternName == ""){
                idPatternName = uniqueConstraintArrayData[i][j][columnId];
              }else{
                idPatternName = idPatternName + "," + uniqueConstraintArrayData[i][j][columnId];
              }

            }
          }

          //columnID部分の文字列を結合
          if(uniqueConstraintConv == ""){
            uniqueConstraintConv = idPatternConv;
          }else{
            uniqueConstraintConv = uniqueConstraintConv + "," + idPatternConv;
          }

          //項目名部分の文字列を結合
          if(uniqueConstraintName == ""){
              idPatternName = "[" + idPatternName + "]";
              uniqueConstraintName = idPatternName;
          }else{
              idPatternName = idPatternName;
              idPatternName = "[" + idPatternName + "]";
              uniqueConstraintName = uniqueConstraintName + "," + idPatternName;
          }
        }
    }

    uniqueConstraintDispData.conv = uniqueConstraintConv;
    uniqueConstraintDispData.name = uniqueConstraintName;

    return uniqueConstraintDispData;

}

//項目を削除したとき、一意制約(複数項目)にその項目が含まれていた場合削除する。
const deleteUniqueConstraintDispData = function(targetColumnId){
    let currentUniqueConstraintData = new Array();
    let tmpList;
    let columnList;

    if ( 'menu_info' in menuEditorArray){
      if( uniquechangecount === 0 && uniquedeletecount === 0 ){
        columnList = menuEditorArray.menu_info.column;
        tmpList = menuEditorArray['unique-constraints-current'];
        for ( let i = 0; i < tmpList.length; i++ ) {
          let uniqueList = new Array();
          for ( let j = 0; j < tmpList[i].length; j++){
            for (const column  in columnList){
              if ( tmpList[i][j] === columnList[column]['item_name_rest'] ){
                let unique = {[column] : tmpList[i][j]};
                uniqueList.push(unique);
                break;
              }
            }
          }
          currentUniqueConstraintData.push(uniqueList);
        }
      } else {
        currentUniqueConstraintData = menuEditorArray['unique-constraints-current'];
      }
    } else {
      currentUniqueConstraintData = menuEditorArray['unique-constraints-current'];
    }

    if(currentUniqueConstraintData != null){
      let newCurrentUniqueConstraintData = currentUniqueConstraintData;
      let uniqueConstraintLength = currentUniqueConstraintData.length;
      for (let i = 0; i < uniqueConstraintLength; i++){
          let targetIdLength = currentUniqueConstraintData[i].length;
          for (let j = 0; j < targetIdLength; j++){
            for (let columnId in currentUniqueConstraintData[i][j]){
              if(targetColumnId == columnId){
                newCurrentUniqueConstraintData[i].splice(j, 1); //削除した項目の配列を除外
              }
            }
          }
      }

      //組み合わせの中身が空になった場合、その配列を除外する。
      let newUniqueConstraintLength = newCurrentUniqueConstraintData.length;
      for (let i = 0; i < newUniqueConstraintLength; i++){
        if(newCurrentUniqueConstraintData[i] != undefined){
          if(newCurrentUniqueConstraintData[i].length == 0){
            newCurrentUniqueConstraintData.splice(i, 1);
          }
        }
      }

      //更新後の値をページに反映
      uniquedeletecount = uniquedeletecount + 1;
      const uniqueConstraintData = getUniqueConstraintDispData(newCurrentUniqueConstraintData);
      const uniqueConstraintConv = uniqueConstraintData.conv;
      const uniqueConstraintName = uniqueConstraintData.name;
      const $input = $('#unique-constraint-list');
      $input.attr('data-unique-list', uniqueConstraintConv); //一意制約のIDの組み合わせをセット
      $input.text(uniqueConstraintName); //一意制約の項目名の組み合わせをセット

      //新しい配列をセット
      menuEditorArray['unique-constraints-current'] = newCurrentUniqueConstraintData;
    }

}

//項目名が変更されるアクションがあったとき、一意制約(複数項目)で表示している項目名をセットしなおす。
const updateUniqueConstraintDispData = function(){
    let currentUniqueConstraintData = new Array();
    let tmpList;
    let columnList;

    if ( 'menu_info' in menuEditorArray){
      if( uniquechangecount === 0 && uniquedeletecount === 0 ){
        columnList = menuEditorArray.menu_info.column;
        tmpList = menuEditorArray['unique-constraints-current'];
        for ( let i = 0; i < tmpList.length; i++ ) {
          let uniqueList = new Array();
          for ( let j = 0; j < tmpList[i].length; j++){
            for (const column  in columnList){
              if ( tmpList[i][j] === columnList[column]['item_name_rest'] ){
                let unique = {[column] : tmpList[i][j]};
                uniqueList.push(unique);
                break;
              }
            }
          }
          currentUniqueConstraintData.push(uniqueList);
        }
      } else {
        currentUniqueConstraintData = menuEditorArray['unique-constraints-current'];
      }
    } else {
      currentUniqueConstraintData = menuEditorArray['unique-constraints-current'];
    }

    if(currentUniqueConstraintData != null){
      let newCurrentUniqueConstraintData = currentUniqueConstraintData;
      let uniqueConstraintLength = currentUniqueConstraintData.length;
      for (let i = 0; i < uniqueConstraintLength; i++){
          let targetIdLength = currentUniqueConstraintData[i].length;
          for (let j = 0; j < targetIdLength; j++){
            for (let columnId in currentUniqueConstraintData[i][j]){
              let $itemNameArea = $menuTable.find('#'+columnId).find('.menu-column-title-rest-input');
              if($itemNameArea.length != 0){
                let itemName = $itemNameArea.val();
                newCurrentUniqueConstraintData[i][j] = {[columnId] : itemName}; //項目名を再設定
              }
            }
          }
      }

      //更新後の値をページに反映
      uniquechangecount = uniquechangecount + 1;
      const uniqueConstraintData = getUniqueConstraintDispData(newCurrentUniqueConstraintData);
      const uniqueConstraintConv = uniqueConstraintData.conv;
      const uniqueConstraintName = uniqueConstraintData.name;
      const $input = $('#unique-constraint-list');
      $input.attr('data-unique-list', uniqueConstraintConv); //一意制約のIDの組み合わせをセット
      $input.text(uniqueConstraintName); //一意制約の項目名の組み合わせをセット

      //新しい配列をセット
      menuEditorArray['unique-constraints-current'] = newCurrentUniqueConstraintData;
    }
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//  項目タイプ別情報の取得
//
////////////////////////////////////////////////////////////////////////////////////////////////////
const getItemData = function( $column, type, setData, mode = 'registration') {
    switch ( type ) {
        case '1':
            setData['single_string_maximum_bytes'] = $column.find('.max-byte').val();
            setData['single_string_regular_expression'] = $column.find('.regex').val();
            setData['single_string_default_value'] = $column.find('.single-default-value').val();
            break;
        case '2':
            setData['multi_string_maximum_bytes'] = $column.find('.multiple-max-byte').val();
            setData['multi_string_regular_expression'] = $column.find('.multiple-regex').val();
            setData['multi_string_default_value'] = $column.find('.multiple-default-value').val();
            break;
        case '3':
            setData['integer_minimum_value'] = $column.find('.int-min-number').val();
            setData['integer_maximum_value'] = $column.find('.int-max-number').val();
            setData['integer_default_value'] = $column.find('.int-default-value').val();
            break;
        case '4':
            setData['decimal_minimum_value'] = $column.find('.float-min-number').val();
            setData['decimal_maximum_value'] = $column.find('.float-max-number').val();
            setData['decimal_digit'] = $column.find('.digit-number').val();
            setData['decimal_default_value'] = $column.find('.float-default-value').val();
            break;
        case '5':
            setData['datetime_default_value'] = $column.find('.datetime-default-value').val();
            break;
        case '6':
            setData['date_default_value'] = $column.find('.date-default-value').val();
            break;
        case '7': {
            // ID
            setData['pulldown_selection_id'] = $column.find('.pulldown-select').val();
            // 名称
            const findItem = menuEditorArray.pulldown_item_list.find(function( item ){
                return item.link_id === setData['pulldown_selection_id'];
            });
            if ( findItem ) {
                setData['pulldown_selection'] = findItem.link_pulldown;
            } else {
                setData['pulldown_selection'] = null;
            }
            // 参照項目
            let reference_item = $column.find('.reference-item').attr('data-reference-item-id');
            if ( reference_item ){
                reference_item = reference_item.split(',');
            } else {
                reference_item = null;
            }
            setData['reference_item'] = reference_item;
            // 初期値
            setData['pulldown_selection_default_value'] = $column.find('.pulldown-default-select').val();
            } break;
        case '8':
            setData['password_maximum_bytes'] = $column.find('.password-max-byte').val();
            break;
        case '9':
            setData['file_upload_maximum_bytes'] = $column.find('.file-max-size').val();
            break;
        case '10':
            setData['link_maximum_bytes'] = $column.find('.link-max-byte').val();
            setData['link_default_value'] = $column.find('.link-default-value').val();
            break;
        case '11': {
            // ID
            setData['parameter_sheet_reference_id'] = $column.find('.reference-parameter-sheet').val();
            // 名称
            const findItem = menuEditorArray.parameter_sheet_reference_list.find(function( item ){
                return item.column_definition_id === setData['parameter_sheet_reference_id'];
            });
            if ( findItem ) {
                setData['parameter_sheet_reference'] = findItem.select_full_name;
            } else {
                setData['parameter_sheet_reference'] = null;
            }
            } break;
        default:
    }
};
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//  メニュー情報JSONデータ作成
//
////////////////////////////////////////////////////////////////////////////////////////////////////
const createJsonData = function( mode = 'registration'){
    const json = {
        group: {}, column: {}, menu: {}
    };

    // パネル情報
    getPanelParameter( json.menu, mode );

    // 最終更新日時
    if ( mode !== 'file' && ( menuEditorMode === 'initialize' || menuEditorMode === 'edit') ) {
        json.menu.last_update_date_time = menuEditorArray.menu_info.menu.last_update_date_time;
    }

    // トップ階層のカラム情報
    json.menu.columns = [];
    $menuTable.children().each( function() {
        json.menu.columns.push( $( this ).attr('id') );
    });

    // Item Order用カウンター
    let itemCount = 0;

    // テーブル情報
    const tableAnalysis = function( $cols ) {
        // 子セルを調べる
        $cols.children().each( function(){
            const $column = $( this );

            if ( $column.is('.menu-column') ) {
                // 項目
                const key = $column.attr('id');
                // 項目タイプ
                const columnTypeName = $column.find('.menu-column-type-select').find('option:selected').attr('data-value');
                const columnType = $column.find('.menu-column-type-select').val();
                // 必須
                const required = ( $column.find('.config-checkbox.required').prop('checked') === false )? '0': '1';
                // 一意制約
                const uniqued = ( $column.find('.config-checkbox.unique').prop('checked') === false )? '0': '1';
                // 親グループ名
                const parentArray = [];
                $column.parents('.menu-column-group').each( function() {
                    parentArray.unshift( $( this ).find('.menu-column-title-input').val() );
                });
                const parents = ( parentArray.length )? parentArray.join('/'): null;
                // アイテム情報
                json.column[key] = {
                    item_name: $column.find('.menu-column-title-input').val(),
                    item_name_rest: $column.find('.menu-column-title-rest-input').val(),
                    required: required,
                    uniqued: uniqued,
                    column_class: columnTypeName,
                    column_class_id: columnType,
                    description: $column.find('.explanation').val(),
                    remarks: $column.find('.note').val(),
                    column_group: parents,
                    display_order: itemCount++
                };
                // 親グループID
                const parentGroupId = $column.closest('.menu-column-group').attr('data-group-id');
                json.column[key].column_group_id = ( mode === 'file' || parentGroupId === '')? null: parentGroupId;
                // アイテムID
                const itemId = $column.attr('data-item-id');
                if ( itemId === '' || menuEditorMode === 'diversion' || mode === 'file') {
                    json.column[key].create_column_id = null;
                } else {
                    json.column[key].create_column_id = itemId;
                }
                // アイテム最終更新日時
                if ( mode !== 'file' && ( menuEditorMode === 'initialize' || menuEditorMode === 'edit' ) ) {
                    if ( menuEditorArray.menu_info.column[key] ) {
                        json.column[key].last_update_date_time = menuEditorArray.menu_info.column[key].last_update_date_time;
                    }
                }
                // タイプ別情報
                getItemData( $column, columnType, json.column[key], mode );
            } else if ( $column.is('.menu-column-group') ) {
                // グループ
                const key = $column.attr('id');
                // グループ内項目
                const columns = [];
                $column.children('.menu-column-group-body').children().each( function() {
                    const $groupChildren = $( this )
                    if ( !$groupChildren.is('.column-empty') ) columns.push( $( this ).attr('id') );
                });
                // 親カラムグループ名
                const parentArray = [];
                $column.parents('.menu-column-group').each( function() {
                    parentArray.unshift( $( this ).find('.menu-column-title-input').val() );
                });
                const parents = ( parentArray.length )? parentArray.join('/'): null;
                // グループ情報
                json.group[key] = {
                    group_name: $column.find('.menu-column-title-input').val(),
                    columns: columns,
                    parent_full_col_group_name: parents
                }
                // 親グループID
                const parentGroupId = $column.closest('.menu-column-group').attr('data-group-id');
                json.group[key].parent_column_group_id = ( mode === 'file' || parentGroupId === '')? null: parentGroupId;
                // グループID
                const groupID = $column.attr('data-group-id');
                if ( groupID === '' || menuEditorMode === 'diversion' || mode === 'file') {
                    json.group[key].group_id = null;
                } else {
                    json.group[key].group_id = groupID;
                }
                // 再帰
                tableAnalysis( $column.children('.menu-column-group-body') );
            }
        });
    };
    tableAnalysis( $menuTable );

    return json;
};
/*
##################################################
    パネル情報取得
##################################################
*/
const getPanelParameter = function( menuData, mode = 'registration') {

    // 作成対象
    const $selectMenuType = $('#create-menu-type').find('option:selected');

    menuData.menu_create_id = ( mode !== 'file')? $('#create-menu-id').attr('data-value'): null;
    menuData.menu_name = $('#create-menu-name').val();
    menuData.menu_name_rest = $('#create-menu-name-rest').val();
    menuData.display_order = $('#create-menu-order').val();
    menuData.description = $('#create-menu-explanation').val();
    menuData.remarks = $('#create-menu-note').val();
    menuData.sheet_type_id = $selectMenuType.val();
    menuData.sheet_type = $selectMenuType.text();

    // ロール
    const role = getRoleListValidID( $('#permission-role-name-list').attr('data-role-id') );
    if ( role === "") {
        menuData.role_list = role;
    } else {
        menuData.role_list = role.split(','); // ロール
    }

    // 一意制約
    const unique = $('#unique-constraint-list').attr('data-unique-list');
    if ( unique ) {
        const uniqueList = unique.split(',');
        const uniqueListLength = uniqueList.length;
        const uniqueConstraint = [];
        for ( let i = 0; i < uniqueListLength; i++ ) {
            const list = uniqueList[i].split('-');
            const listLength = list.length;
            for ( let j = 0; j < listLength; j++ ) {
                list[j] = $menuTable.find('#' + list[j] ).find('.menu-column-title-rest-input').val();
            }
            uniqueConstraint[i] = list;
        }
        menuData.unique_constraint = uniqueConstraint;
    } else {
        menuData.unique_constraint = null;
    }

    // 作成対象別項目
    const type = $('#create-menu-type').val();
    menuData.sheet_type_id = type;
    if ( type === '1' || type === '3') {
        // パラメータシート
        if ( type === '1' ) {
            // ホストグループ利用有無
            const hostgroup = $('#create-menu-use-host-group').prop('checked');
            if ( hostgroup ) {
                menuData.hostgroup = "1";
            } else {
                menuData.hostgroup = "0";
            }
        } else {
            menuData.hostgroup = null;
        }
        // 縦メニュー利用有無
        const vertical = $('#create-menu-use-vertical').prop('checked');
        if ( vertical ) {
            menuData.vertical = "1";
        } else {
            menuData.vertical = "0";
        }
        // 入力用
        menuData.menu_group_for_input = $('#create-menu-for-input').text();
        menuData.menu_group_for_input_id = $('#create-menu-for-input').attr('data-id');
        // 代入値用
        menuData.menu_group_for_subst = $('#create-menu-for-substitution').text();
        menuData.menu_group_for_subst_id = $('#create-menu-for-substitution').attr('data-id');
        // 参照用
        menuData.menu_group_for_ref = $('#create-menu-for-reference').text();
        menuData.menu_group_for_ref_id = $('#create-menu-for-reference').attr('data-id');
    } else if ( type === '2') {
        // データシート

        // 入力用
        menuData.menu_group_for_input = $('#create-menu-for-input').text();
        menuData.menu_group_for_input_id = $('#create-menu-for-input').attr('data-id');
    }

    // undefined,''をnullに
    for ( const key in menuData ) {
        if ( menuData[key] === undefined || menuData[key] === '') {
            menuData[key] = null;
        }
    }
};

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//  メニュー登録
//
////////////////////////////////////////////////////////////////////////////////////////////////////
const registrationMenu = function( type ){
    return new Promise(function( resolve, reject ){
        // 登録データ
        const registrationData = createJsonData();
        registrationData.type = type;

        // 進行中モーダル
        let process = fn.processingModal('');

        fn.fetch('/create/define/execute/', null, 'POST', registrationData ).then(function(result){
            let id  = result['history_id'];
            let string = getMessage.FTE01140;
            let log = string + id;
            menuEditorLog.set( 'done', log );

            fn.alert('', fn.escape( log, true ) ).then(function(){
                let url_path = location.pathname,
                splitstr = url_path.split('/'),
                organization_id = splitstr[1],
                workspace_id = splitstr[3],
                menu_name_rest = result['menu_name_rest'],
                menu = getParam('menu');
                process.close();
                process = null;
                resolve();

                window.location.href = '/' + organization_id + '/workspaces/' + workspace_id + '/ita/?menu=' + menu + '&menu_name_rest=' + menu_name_rest + '&history_id=' + id;
            });
        }).catch(function( error ){
            if ( fn.typeof( error ) === 'object') {
                if ( error.result === '498-00004') {
                    if ( fn.typeof( error.message ) === 'string') window.alert( error.message );
                } else {
                    let message = errorFormat(error.message);
                    menuEditorLog.clear();
                    menuEditorLog.set('error', message );
                    window.alert(getMessage.FTE01141);
                }
            }
            process.close();
            process = null;
            reject();
        });
    });
};
/*
##################################################
    登録エラー
##################################################
*/
const errorFormat = function( error ) {
    let errorMessage;
    let message;
    let keyVal;
    let val;
    let errMessage = "";

    const errorRow = function( m ){
        return `<div class="error-log-row">${textEntities(m)}</div>`
    };

    try {
        errorMessage = JSON.parse(error);
        for ( const key in errorMessage ) {
            message = errorMessage[key];
            if ( key === '__line__'){
                val = errorRow( message );
                errMessage = errMessage + val;
            } else {
                if (key in nameConvertList) {
                    keyVal = errorRow( nameConvertList[key] + ':' + message );
                    errMessage = errMessage + keyVal;
                } else {
                    keyVal = errorRow( key + ':' + message );
                    errMessage = errMessage + keyVal;
                }
            }
        }
    } catch ( e ) {
        errMessage = errorRow( error );
    }
    return errMessage;
};

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   再表示
//
////////////////////////////////////////////////////////////////////////////////////////////////////

const setMenu = function( setMode ) {

    // メニューデータ
    const menuInfo = menuEditorArray.menu_info;

    // JSON読込時に読み込まない項目
    if ( setMode === 'jsonRead') {
        menuInfo.menu.menu_create_id = null;
        menuInfo.menu.last_update_date_time = null;
        menuInfo.menu.last_updated_user = null;
        menuInfo.menu.menu_create_done_status_id = null;
    }

    // 流用新規時に引き継がない項目
    if ( menuEditorMode === 'diversion' ){
        menuInfo['menu']['menu_create_id'] = null;
        menuInfo['menu']['menu_name'] = null;
        menuInfo['menu']['menu_name_rest'] = null;
        menuInfo['menu']['display_order'] = null;
        menuInfo['menu']['last_update_date_time'] = null;
        menuInfo['menu']['description'] = null;
        menuInfo['menu']['remarks'] = null;
    }

    let setMenuHTML = '';
    const setMenuTable = function( columns ) {
        if ( columns ) {
            for ( const id of columns ) {
                const type = id.substr(0,1);
                // IDが重複していないかチェック
                if ( menuIdList.indexOf( id ) !== -1 ) {
                    throw new Error( getMessage.FTE01155(id) );
                }
                menuIdList.push( id );
                switch ( type ) {
                    // グループ
                    case 'g': {
                        if ( menuInfo['group'][id] ) {
                            const groupData = menuInfo['group'][id];
                            if ( setMode === 'jsonRead') groupData.group_id = null;

                            // グループ枠HTML
                            const groupId = fn.cv( groupData.group_id, '');
                            let groupName = '';
                            if ( groupData.column_group_name !== undefined ) groupName = groupData.column_group_name;
                            if ( groupData.col_group_name !== undefined ) groupName = groupData.col_group_name;
                            if ( groupData.group_name !== undefined ) groupName = groupData.group_name;
                            if ( fn.typeof( groupName ) !== 'string') groupName = '';

                            setMenuHTML += ''
                            + '<div class="menu-column-group" data-group-id="' + groupId + '" id="' + id + '">'
                                + '<div class="menu-column-group-header">'
                                + getColumnHeaderGroupHTML( groupName )
                                + '</div>'
                                + '<div class="menu-column-group-body">';

                            if ( groupData.columns && groupData.columns.length ) {
                                setMenuTable( groupData.columns );
                            } else {
                                setMenuHTML += columnEmptyHTML;
                            }

                            setMenuHTML += '</div>'
                            + '</div>';
                        } else {
                            throw new Error( getMessage.FTE01156(id) );
                        }
                    } break;
                    // 項目
                    default: {
                        if ( menuInfo['column'][id] ) {
                            const itemData = menuInfo['column'][id];
                            if ( setMode === 'jsonRead') itemData.create_column_id = null;
                            setMenuHTML += getColumnHTML( itemData, id );
                        } else {
                            throw new Error( getMessage.FTE01156(id) );
                        }
                    }
                }
            }
        }
    };
    setMenuTable( menuInfo.menu.columns );

    // HTMLセット
    $menuTable.html( setMenuHTML );

    // select2
    $menuTable.find('.config-select').select2();

    // 各種設定
    $menuTable.find('.menu-column-title-input, .menu-column-title-rest-input').each( function(){
        titleInputChange( $(this) );
    });

    // プルダウン選択
    $menuTable.find('.menu-column').each(function(){
        const $item = $( this ),
              columnID = $item.attr('id'),
              type = $item.find('.menu-column-config-table').attr('date-select-value'),
              itemData = menuInfo['column'][ columnID ];

        // プルダウン選択初期値設定
        if ( type === '7') {
            // 選択項目
            getpulldownDefaultValueList( $item, fn.cv( itemData['pulldown_selection_default_value'], '') );

            // 参照項目
            $item.find('.reference-item').attr('data-reference-item-id', itemData['reference_item'] );
            //newItemListのIDから項目名に変換
            if( itemData['reference_item'] !== null ){
                const newItemListArray = itemData['reference_item'];
                const newItemNameListArray = [];
                newItemListArray.forEach(function(data){
                      newItemNameListArray.push(data);
                });
                //重複を排除
                let setNewItemNameList = new Set(newItemNameListArray);
                let setNewItemNameListArray = Array.from(setNewItemNameList);

                //カンマ区切りの文字列に変換し参照項目上に表示
                var newItemNameList = setNewItemNameListArray.join(',');
                $item.find('.reference-item').html( newItemNameList );
            }
        }

        setEventPulldownDefaultValue( $item );
        // setEventPulldownParameterSheetReference( $item );
    });

    // パネル情報表示
    setPanelParameter( menuInfo );

    history.clear();
    emptyCheck();
    columnHeightUpdate();
    previewTable();
};

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   パネル情報セット
//
////////////////////////////////////////////////////////////////////////////////////////////////////
const setPanelParameter = function( setData ) {
  // nullを空白に
  for ( let key in setData['menu'] ) {
    if ( setData['menu'][key] === null ) {
      setData['menu'][key] = '';
    }
  }
  // パネルに値をセットする
  const type = setData['menu']['sheet_type_id'];
        $property.attr('data-menu-type', type );

  if ( menuEditorMode !== 'diversion' ){
    // 項番
    if ( setData['menu']['menu_create_id'] ) {
        $('#create-menu-id')
        .attr('data-value', setData['menu']['menu_create_id'] )
        .text( setData['menu']['menu_create_id'] );
    }
    // 最終更新日時
    if ( setData['menu']['last_update_date_time'] ) {
        let date = setData['menu']['last_update_date_time'];
        let last_update_date_time = fn.date( date, 'yyyy-MM-dd HH:mm:ss');
        $('#create-menu-last-modified')
        .attr('data-value', last_update_date_time )
        .text( last_update_date_time );
    }
    // 最終更新者
    if ( setData['menu']['last_updated_user'] ) {
        $('#create-last-update-user')
        .attr('data-value', setData['menu']['last_updated_user'] )
        .text( setData['menu']['last_updated_user'] );
    }
  }
  // ロール
  let roleList = [];
  if ( setData.menu.selected_role_id !== undefined ) roleList = setData.menu.selected_role_id;
  if ( setData.menu.role_list !== undefined ) roleList = setData.menu.role_list;
  if ( fn.typeof( roleList ) !== 'array') roleList = [];
  $('#permission-role-name-list')
    .attr('data-role-id', roleList )
    .text( getRoleListIdToName( roleList ) );

  // 一意制約(複数項目)
  let unique_constraint = [];
  if ( setData.menu.unique_constraint_current !== undefined ) unique_constraint = setData.menu.unique_constraint_current;
  if ( setData.menu.unique_constraint !== undefined ) unique_constraint = setData.menu.unique_constraint;
  if ( fn.typeof( unique_constraint ) !== 'array') unique_constraint = [];

  let unique_dict = {};
  let unique_list = [];
  let all_unique_list = [];
   for ( let i = 0; i < unique_constraint.length; i++ ) {
    unique_list = [];
    let list = unique_constraint[i];
    for ( let j = 0; j < list.length; j++ ) {
    let data = list[j];
    unique_dict = {};
    unique_dict[data] = data;
    unique_list[j] = unique_dict;
    }
    all_unique_list[i] = unique_list;
  }

  const initUniqueConstraintData = getUniqueConstraintDispData(all_unique_list);
  const initUniqueConstraintConv = initUniqueConstraintData.conv;
  const initUniqueConstraintName = initUniqueConstraintData.name;
  $('#unique-constraint-list')
    .text(initUniqueConstraintName)
    .attr('data-unique-list', initUniqueConstraintConv);
  menuEditorArray['unique-constraints-current'] = setData['menu']['unique_constraint']; //更新用に格納しなおす

  // エディットモード別
  let dispOrder = '';
  if ( setData.menu.disp_seq !== undefined ) dispOrder = setData.menu.disp_seq;
  if ( setData.menu.display_order !== undefined ) dispOrder = setData.menu.display_order;

  if ( menuEditorMode === 'view') {
    $('#create-menu-name').text( setData['menu']['menu_name'] ); // メニュー名
    $('#create-menu-name-rest').text( setData['menu']['menu_name_rest'] ); // メニュー名(REST)
    $('#create-menu-type').text( listIdName('target', setData['menu']['sheet_type_id'] )); // 作成対象
    $('#create-menu-order').text( dispOrder ); // 表示順序
    $('#create-menu-explanation').text( setData['menu']['description'] );  // 説明
    $('#create-menu-note').text( setData['menu']['remarks'] ); // 備考
  } else {
    $('#create-menu-name').val( setData['menu']['menu_name'] ); // メニュー名
    $('#create-menu-name-rest').val( setData['menu']['menu_name_rest'] ); // メニュー名(REST)
    $('#create-menu-type').val( setData['menu']['sheet_type_id'] ); // 作成対象
    $('#create-menu-order').val( dispOrder ); // 表示順序
    $('#create-menu-explanation').val( setData['menu']['description'] );  // 説明
    $('#create-menu-note').val( setData['menu']['remarks'] ); // 備考
  }

  // 作成対象項目別
  if ( type === '1' || type === '3') {
    // パラメータシート
    if ( type === '1') {
      // ホストグループ利用有無
      if ( setData.menu.hostgroup === '1' || setData.menu.hostgroup === 'True' || setData.menu.hostgroup === true ) {
        if ( menuEditorMode === 'view') {
          $('#create-menu-use-host-group').text(getMessage.FTE01085);
        } else {
          $('#create-menu-use-host-group').prop('checked', true );
        }
      }
    }
    // 縦メニュー利用有無
    if ( setData.menu.vertical === '1' || setData.menu.vertical === 'True' || setData.menu.vertical === true ) {
      if ( menuEditorMode === 'view') {
        $('#create-menu-use-vertical').text(getMessage.FTE01085);
      } else {
        $('#create-menu-use-vertical').prop('checked', true );
      }
    }
    // 入力用
    const $forInput = $('#create-menu-for-input');
    const forInputId = setData['menu']['menu_group_for_input_id'];
    const forInputText = listIdName('group', forInputId );
    if ( forInputText ) {
        $forInput.attr('data-id', forInputId ).text( forInputText );
    } else {
        $forInput.attr('data-id', '').text('');
    }
    // 代入値自動登録用
    const $forSubstitution = $('#create-menu-for-substitution');
    const forSubstitutionId = setData['menu']['menu_group_for_subst_id'];
    const forSubstitutionText = listIdName('group', forSubstitutionId );
    if ( forSubstitutionText ) {
        $forSubstitution.attr('data-id', forSubstitutionId ).text( forSubstitutionText );
    } else {
        $forSubstitution.attr('data-id', '').text('');
    }
    // 参照用
    const $forReference = $('#create-menu-for-reference');
    const forReferenceId = setData['menu']['menu_group_for_ref_id'];
    const forReferenceText = listIdName('group', forReferenceId );
    if ( forReferenceText ) {
        $forReference.attr('data-id', forReferenceId ).text( forReferenceText );
    } else {
        $forReference.attr('data-id', '').text('');
    }
  } else if ( type === '2') {
    // データシート
    // 入力用
    const $forInput = $('#create-menu-for-input');
    const forInputId = setData['menu']['menu_group_for_input_id'];
    const forInputText = listIdName('group', forInputId );
    if ( forInputText ) {
        $forInput.attr('data-id', forInputId ).text( forInputText );
    } else {
        $forInput.attr('data-id', '').text('');
    }
  }

  //「メニュー作成状態」が2(作成済み)の場合は、メニュー名(REST)入力欄を非活性にする。
  if(menuEditorMode != 'diversion'){
    if(setData['menu']['menu_create_done_status_id'] == 2){
      //$('#create-menu-name').prop('disabled', true);
      $('#create-menu-name-rest').prop('disabled', true);
    }
  }

  //「メニュー作成状態」が1（未作成）の場合に各種ボタンを操作
  if(setData['menu']['menu_create_done_status_id'] == 1){
      //「編集」ボタンを削除
      $menuEditor.find('[data-type="edit"]').closest('.operationMenuItem').remove();

      const buttonText = ( menuEditorMode === 'view')? getMessage.FTE01151: getMessage.FTE01090;

      //「初期化」「作成(初期化)」ボタンを「作成」に名称変更
      const $initialize = $menuEditor.find('[data-type="initialize"], [data-type="update-initialize"]');
      $initialize.attr({
          'data-action': 'positive',
          'title': buttonText
      }).find('.iconButtonBody').text( buttonText )
          .closest('.operationMenuItem').removeClass('operationMenuSeparate');
      $initialize.find('.icon-clear').removeClass('icon-clear').addClass('icon-plus');
  }

  if ( setData['menu']['number_item'] ) {
    itemCounter = setData['menu']['number_item'] + 1;
  } else {
    const columnCount = $menuTable.find('.menu-column').length;
    itemCounter = columnCount + 1;
  }
  if ( setData['menu']['number_group'] ) {
    groupCounter = setData['menu']['number_group'] + 1;
  } else {
    const groupCount = $menuTable.find('.menu-column-group').length;
    groupCounter = groupCount + 1;
  }
};

////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   初期表示
//
////////////////////////////////////////////////////////////////////////////////////////////////////

// メニューグループ初期値
const initialMenuGroup = function() {

    const forInputID = '502', // 入力用
          forSubstitutionID = '503', // 代入値自動登録用
          forReference = '504', // 参照用
          forInputName = listIdName( 'group', forInputID ),
          forSubstitutionName = listIdName( 'group', forSubstitutionID ),
          forReferenceName = listIdName( 'group', forReference );

    // 入力用
    if ( forInputName !== null ) {
      $('#create-menu-for-input')
        .attr('data-id', forInputID )
        .text( forInputName );
    }
    // 代入値自動登録用
    if ( forSubstitutionName !== null ) {
      $('#create-menu-for-substitution')
        .attr('data-id', forSubstitutionID )
        .text( forSubstitutionName );
    }
    // 参照用
    if ( forReferenceName !== null ) {
      $('#create-menu-for-reference')
        .attr('data-id', forReference )
        .text( forReferenceName );
    }
    // ロールの初期値を入れる
    if ( menuEditorArray.role_list !== undefined ) {
      const roleDefault = new Array,
            roleLength = menuEditorArray.role_list.length;
      const roleCheckList = menuCreateUserInfo.roles;
            for (let i = 0; i < roleCheckList.length; i++) {
              for (let j = 0; j < roleLength; j++) {
                if (roleCheckList[i] === menuEditorArray.role_list[j]) {
                  roleDefault.push(menuEditorArray.role_list[j]);
                }
              }
            }
      const newRoleList = roleDefault.join(',');
      $('#permission-role-name-list').text( newRoleList ).attr('data-role-id', newRoleList );
    }
};

if ( menuEditorMode === 'new' ) {
    initialMenuGroup();
    const currentItemCounter = itemCounter;
    addColumn( $menuTable, 'column');
    //プルダウン選択の初期値を取得するイベントを設定
    const $newColumnTarget = $menuEditor.find('#c'+currentItemCounter);
    setEventPulldownDefaultValue($newColumnTarget);
} else {
    setMenu();
}
repeatCheck();
history.clear();

}

//////////////////////////////////////////////////////
// ロール一覧取得・選択
//////////////////////////////////////////////////////

// モーダル Body HTML
function setRoleSelectModalBody( roleList, initData, okCallback, cancelCallBack, valueType ) {

  if ( valueType === undefined ) valueType = 'id';
  const $modalBody = $('.editor-modal-body');

  let roleSelectHTML = ''
  + '<div class="modal-table-wrap">'
    + '<form id="modal-role-select">'
    + '<table class="modal-table modal-select-table">'
      + '<thead>'
        + '<th class="selectTh">Select</th><th class="name">Name</th>'
      + '</thead>'
      + '<tbody>';

  // 入力値を取得する
  const checkList = ( initData !== null || initData !== undefined )? initData.split(','): [''];

  const roleLength = roleList.length;
  for ( let i = 0; i < roleLength; i++ ) {
    const roleName = roleList[i],
          hideRoleName = "********";
    // ********は表示しない
    if ( roleName !== hideRoleName ) {
      //const roleID = String(i),
            //checkValue = ( valueType === 'name')? roleName: roleID,
      const checkValue = roleName,
            checkedFlag = ( checkList.indexOf( checkValue ) !== -1 )? ' checked': '',
            //value = ( valueType === 'name')? roleName: roleID;
            value = roleName;
      roleSelectHTML += '<tr>'
      + '<th><input value="' + value + '" class="modal-checkbox" type="checkbox"' + checkedFlag + '></th>'
      + '<td>' + roleName + '</td></tr>';
    }
  }

  roleSelectHTML += ''
      + '</tbody>'
    + '</table>'
    + '</form>'
  + '</div>';

  $modalBody.html( roleSelectHTML );

  // 行で選択
  $modalBody.find('.modal-select-table').on('click', 'tr', function(){
    const $tr = $( this ),
          checked = $tr.find('.modal-checkbox').prop('checked');
    if ( checked ) {
      $tr.find('.modal-checkbox').prop('checked', false );
    } else {
      $tr.find('.modal-checkbox').prop('checked', true );
    }
  });

  // 決定・取り消しボタン
  const $modalButton = $('.editor-modal-footer-menu-button');
  $modalButton.prop('disabled', false ).on('click', function() {
    const $button = $( this ),
          btnType = $button.attr('data-button-type');
    switch( btnType ) {
      case 'ok':
        // 選択しているチェックボックスを取得
        let checkboxArray = new Array;
        $modalBody.find('.modal-checkbox:checked').each( function(){
          checkboxArray.push( $( this ).val() );
        });
        const newRoleList = checkboxArray.join(',');
        okCallback( newRoleList );
        break;
      case 'cancel':
        cancelCallBack();
        break;
    }
  });
}

//////////////////////////////////////////////////////
// 一意制約
//////////////////////////////////////////////////////
// モーダル Body HTML
function setUniqueConstraintModalBody(columnItemData, initmodalUniqueConstraintList, okCallback, cancelCallBack, closeCallBack) {
  const $modalBody = $('.editor-modal-body');
  const $modalFooterMenu = $('.editor-modal-footer-menu');
  const initUniqueConstraintArray = (initmodalUniqueConstraintList == '') ? new Array : initmodalUniqueConstraintList.split(',');
  const initUniqueConstraintLength = initUniqueConstraintArray.length;
  const columnItemDataLength = columnItemData.length;
  let uniqueConstraintSelectHTML;

  if(columnItemData.length == 0){
      //項目が0個の場合、メッセージを表示
      noColumnHTML = '<div class="column-none-message">' + getMessage.FTE01142 + '</div>';
      $modalBody.html( noColumnHTML );

      //ボタンを「閉じる」に変更
      $modalFooterMenu.children().remove();
      $modalFooterMenu.append('<li class="editor-modal-footer-menu-item"><button class="editor-modal-footer-menu-button negative" data-button-type="close">' + getMessage.FTE01050 + '</li>');
  }else{
      //項目の数だけチェックボックスを作成する「パターン」のテンプレート
      uniqueConstraintLineTemplate = '<div class="unique-constraint-pattern-tmp unique-constraint-box" data-unique-ptn="">'
                                      +'<span>';

      for (let i = 0; i < columnItemDataLength; i++){
          const columnID = columnItemData[i]['columnId'],
                itemName = columnItemData[i]['itemName'],
                itemID = columnItemData[i]['itemId'];
          uniqueConstraintLineTemplate += '<div class="unique-edit-check-wrap">'
                                          + '<input type="checkbox" id="" class="unique-constraint-checkbox unique-edit-check" data-item-id="'+ itemID +'" data-column-id="'+ columnID +'">'
                                          + '<label class="unique-constraint-label unique-edit-label" for="">' + itemName + '</label>'
                                        + '</div>';

      }

      uniqueConstraintLineTemplate += '</span>'
                                  +'<div class="line-delete-button-wrap"><button type="button" class="line-delete-button">' + getMessage.FTE01143 + '</button></div>'
                              +'</div>';

      uniqueConstraintSelectHTML = ''
                    +'<div id="modal-unique-constraint-area" class="">'
                    + uniqueConstraintLineTemplate
                      + '<ul class="add-unique-pattern">'
                        + '<li class=""><button class="add-unique-pattern-button positive" data-button-type="add">' + getMessage.FTE01144 + '</li>'
                      + '</ul>'
                      + '<form id="modal-unique-constraint-select">'
                      + '<div class="unique-none-message" hidden>' + getMessage.FTE01145 + '</div>'
                      + '<br>';

      uniqueConstraintSelectHTML += ''
                      + '</form>'
                    + '</div>';

      $modalBody.html( uniqueConstraintSelectHTML );


      //初期表示およびパターン追加処理
      const $uniqueConstraintArea = $('#modal-unique-constraint-area');
      const $addPatternButton = $uniqueConstraintArea.find('.add-unique-pattern-button');
      const $patternTemplate = $uniqueConstraintArea.find('.unique-constraint-pattern-tmp');
      const $addArea = $('#modal-unique-constraint-select');
      const $noneMsg = $uniqueConstraintArea.find('.unique-none-message');
      let patternCount = 0;

      //パターン追加関数
      function addPattern($newPattern){
          $newPattern.show(); //非表示を解除
          $newPattern.removeClass('unique-constraint-pattern-tmp').addClass('unique-constraint-pattern'); //Class入れ替え
          patternCount++;
          $newPattern.attr('data-unique-ptn', 'p'+patternCount); //連番を設定
          $newPattern.find('.unique-constraint-checkbox').each(function(){
              let itemId = $(this).attr('data-column-id');
              $(this).attr('id', 'p'+patternCount+itemId); //idを設定
              $(this).next('label').attr('for', 'p'+patternCount+itemId); //forを設定
          });
          $addArea.append($newPattern);

          //「削除」ボタンにイベント追加
          $newPattern.find('.line-delete-button').on('click', function(){
              //対象のパターンを削除
              $(this).parents('.unique-constraint-box').remove();

              //パターンが0の場合はメッセージを表示
              $pattern = $addArea.find('.unique-constraint-box');
              if($pattern.length == 0){
                  $noneMsg.show();
              }
          });
      }


      if(initUniqueConstraintLength == 0){
          //一意制約の設定値がない場合、メッセージを表示
          $noneMsg.show();
      }else{
          ///一意制約の設定値がある場合、パターンの数だけループ処理
          for (let i = 0; i < initUniqueConstraintLength; i++){
              //パターンを生成
              let $newPattern = $patternTemplate.clone(true);
              addPattern($newPattern);

              //初期チェック状態を設定
              const patternStr = initUniqueConstraintArray[i];
              const patternArray = patternStr.split('-'); //「-」で連結したIDを配列化
              const patternLength = patternArray.length;
              for(let j = 0; j < patternLength; j++){
                  //入力済みの設定値を反映
                  const patternId = patternArray[j];
                  $target = $newPattern.find('[data-column-id="'+patternId+'"]'); //対象をdata-column-idで検索
                  if($target.length != 0){
                      $target.prop('checked', true);
                  }
              }
          }
      }

      //「パターンを追加」ボタン
      $addPatternButton.on('click', function(){
          //パターンが無い場合のメッセージを非表示
          if(!$noneMsg.is('hidden')){
              $noneMsg.hide();
          }

          //新しいパターンを生成
          let $newPattern = $patternTemplate.clone(true);
          addPattern($newPattern);
      });
  }

  // 決定・取り消しボタン
  const $modalButton = $('.editor-modal-footer-menu-button');
  $modalButton.prop('disabled', false ).on('click', function() {
      const $button = $( this ),
            btnType = $button.attr('data-button-type');
      switch( btnType ) {
        case 'ok':
          //設定値を格納する配列を定義
          let currentUniqueConstraintArray = new Array;
          // 選択しているチェックボックスを取得
          $modalBody.find('.unique-constraint-box').each(function(){
              $targetPattern = $(this);
              if($targetPattern.hasClass('unique-constraint-pattern-tmp') == true){
                  return true;
              }
              let currentPatternArray = new Array;
              $targetPattern.find('.unique-constraint-checkbox:checked').each(function(){
                  let columnId = $(this).attr('data-column-id');
                  let itemName = $(this).next('label').html();
                  let idName = {[columnId] : itemName};
                  currentPatternArray.push(idName);
              });

              currentUniqueConstraintArray.push(currentPatternArray);
          });

          okCallback(currentUniqueConstraintArray);
          break;
        case 'cancel':
          cancelCallBack();
          break;
        case 'close':
          closeCallBack();
          break;
      }
  });

}
