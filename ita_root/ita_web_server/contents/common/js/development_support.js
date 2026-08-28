////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Exastro IT Automation / DevelopmentSupport.js
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

class DevelopmentSupport {
/*
##################################################
    Constructor
##################################################
*/
constructor() {
}
/*
##################################################
    Setup
##################################################
*/
setup( modal, aceEditor ) {
    return new Promise( async ( resolve, reject ) => {
        // 初期化
        this.modal = modal;
        this.editor = aceEditor;
        this.module = {};
        this.modelList = {};
        this.llm = {};

        // ユーザID読み込み
        const userData = fn.storage.get('restUser', 'session');
        this.id = userData.user_id ?? null; 
        if ( this.id === null ) {
            alert(getMessage.FTE14001);
            return resolve();
        }

        // 設定読み込み
        this.setting = await this.db.get( this.id );
        if ( this.setting === null ) {
            this.setting = {
                assistant: '',
            };
        } else {
            if ( this.setting.assistant ) await this.getModule( this.setting.assistant );
        }

        // markdown-it
        this.md = markdownit({
            highlight: function (str, lang) {
                if (lang && hljs.getLanguage(lang)) {
                    try {
                        return '<pre><code class="hljs">' +
                            hljs.highlight(str, { language: lang, ignoreIllegals: true }).value +
                        '</code></pre>';
                    } catch (__) {}
                }
                return ''; // use external default escaping
            }
        });

        // 画面セット
        this.modal.$.dialog.addClass('developmentSupport');
        this.$ = {};
        this.setButton();
        this.openButtonCheck();

        resolve();
    });
}
/*
##################################################
    編集データ取得
##################################################
*/
getEditorData() {
    return {
        name: this.modal.$.dbody.find('.editorFileName').val(),
        body: this.editor.getValue()
    };
}
/*
##################################################
    モーダルにボタン追加
##################################################
*/
setButton() {
    // ボタン追加
    const className = 'dialogButton itaButton popup';
    const settingButton = fn.html.button( fn.html.icon('gear'), className, { kind: 'llmSetting', action: 'default', title: getMessage.FTE14002});
    const openButton = fn.html.button( fn.html.icon('stick'), className, { kind: 'llmOpen', action: 'default', title: getMessage.FTE14003, disabled: 'disabled'});
    const button = `
    <li class="dialogFooterMenuItem" style="margin-left: auto;">${settingButton}</li>
    <li class="dialogFooterMenuItem">${openButton}</li>`;
    this.modal.$.footer.find('.dialogFooterMenuList').append( button );
    this.$.openButton = this.modal.$.footer.find('.itaButton[data-kind="llmOpen"]');
    this.$.settingButton = this.modal.$.footer.find('.itaButton[data-kind="llmSetting"]');

    // ボタンイベント
    this.modal.btnFn.llmSetting = () => {
        this.openSupportSettingModal();
    };
    this.modal.btnFn.llmOpen = async () => {
        this.$.openButton.prop('disabled', true );
        this.$.settingButton.prop('disabled', true );
        await this.openSupport();
    };
    this.modal.btnFn.llmClose = async () => {
        this.$.openButton.prop('disabled', false );
        this.$.settingButton.prop('disabled', false );
        this.modal.$.dialog.removeClass('developmentSupportOpen').find('.dialog').css('width', '960px');
        this.modal.$.dialog.find('.subDialogMain').remove();
    };
    this.modal.btnFn.historyDownload = async () => {
        const history = this.llm[ this.setting.assistant ].getChatHistory() ?? [];
        const fileName = this.modal.$.dbody.find('.editorFileName').val() ?? 'ai_assistant';
        const historyName = fileName.replace(/\.[^/.]+$/, '') + '_history.json';
        fn.download('json', history, historyName );
    };
}
// 開くボタンチェック
openButtonCheck() {
    const assistant = this.setting.assistant;
    const setting =  this.setting[ assistant ];
    if ( setting ) {
        // 認証情報チェック（アシスタントごとに異なるフィールド）
        let authCheck = false;

        if ( this.llm[ assistant ] && this.llm[ assistant ].setting ) {
            const settingFields = this.llm[ assistant ].setting;

            // 各必須フィールドがすべて入力されているかチェック
            authCheck = true;
            for ( const key in settingFields ) {
                const field = settingFields[ key ];
                // required が false の場合はスキップ
                if ( field.required === false ) continue;
                // modelSelect, modelDefault はここではチェックしない
                if ( field.type === 'modelSelect' || field.type === 'modelDefault' ) continue;

                // 必須フィールドが空の場合は false
                if ( !setting[ key ] || setting[ key ] === '' ) {
                    authCheck = false;
                    break;
                }
            }
        } else {
            // 後方互換性: apiKey フィールドのチェック（Gemini等）
            authCheck = ( fn.typeof( setting.apiKey ) === 'string' && setting.apiKey !== '');
        }

        // モデル選択が配列かつ1つ以上
        const modelSelectCheck = ( fn.typeof( setting.modelSelect ) === 'array' && setting.modelSelect.length );
        // モデル初期値がオブジェクトかつIDが文字列かつ空白以外
        const modelDefaultCheck = ( fn.typeof( setting.modelDefault ) === 'object' && fn.typeof( setting.modelDefault.id ) === 'string' && setting.modelDefault.id !== '');
        const flag = ( authCheck && modelSelectCheck && modelDefaultCheck );
        this.$.openButton.prop('disabled', !flag );
    } else {
        this.$.openButton.prop('disabled', true );
    }
}
/*
##################################################
    モジュール読込
##################################################
*/
async getModule( assistant ) {
    if ( assistant && this.aiAssistantList[ assistant ] && ( this.module[ assistant ] === undefined || this.llm[ assistant ] === undefined )) {
        try {
            this.v = fn.getUiVersion();
            this.module[ assistant ]  = await import(`/_/ita/js/development_support_module/${assistant}.js?v=${this.v}`);
            this.llm[ assistant ] = new this.module[ assistant ].DevelopmentSupportModule();
        } catch ( error ) {
            console.error( error );
            reject( error );
        }
    }
    return;
}
/*
##################################################
    開発支援設定を開く
##################################################
*/
// アシスタントリスト（JSファイル名:表示名）
aiAssistantList = {
    'bedrock': 'Amazon Bedrock(Claude Code)',
    'gemini': 'Google Gemini',
}
// 設定モーダルコンフィグ
openSupportSettingModalConfig = {
    position: 'center',
    width: '640px',
    header: {
        title: getMessage.FTE14002,
    },
    footer: {
        button: {
            save: { text: getMessage.FTE14004, action: 'positive', className: 'dialogPositive'},
            close: { text: getMessage.FTE14005, action: 'normal'},
            delete: { text: getMessage.FTE14006, action: 'danger', className: 'dialogPositive'}
        }
    }
}
// 設定モーダルを開く
async openSupportSettingModal() {
    let settingModal = new Dialog( this.openSupportSettingModalConfig );
    const modalClose = () => {
        settingModal.close();
        settingModal = null;
        this.openButtonCheck();
    };
    settingModal.btnFn = {
        save: async () => {
            const assistant = settingModal.$.dialog.find('.aiSelect').val();
            this.setting.assistant = assistant;
            this.setting[ assistant ] = {};
            $setting.find('.input').each(( index, element ) => {
                const $item = $( element );
                const name = $item.attr('name');
                if ( name === 'modelSelect') {
                    const $option = $item.find('option:selected');
                    const list = [];
                    $option.each( ( i, e ) => {
                        const $o = $( e );
                        const t = $o.text();
                        const v = $o.val();
                        list.push({
                            id: v,
                            text: t
                        });
                    });
                    this.setting[ assistant ][ name ] = list;
                } else if ( name === 'modelDefault') {
                    const $option = $item.find('option:selected');
                    this.setting[ assistant ][ name ] = {
                        id: $option.val(),
                        text: $option.text()
                    };
                } else {
                    this.setting[ assistant ][ name ] = $item.val();
                }
            });
            await this.db.set( this.id, this.setting );
            this.setting = await this.db.get( this.id );
            modalClose();
        },
        delete: async () => {
            if ( confirm(getMessage.FTE14007) ) {
                await this.db.delete();
                this.setting = {
                    assistant: ''
                };
                modalClose();
            }
        },
        close: () => {
            modalClose();
        },
    };
    const list = [];
    for ( const key in this.aiAssistantList ) {
        const option = document.createElement('option');
        option.textContent = this.aiAssistantList[ key ] ?? '';
        option.value = key;
        if ( key === this.setting.assistant ) option.setAttribute('selected', '');
        list.push( option.outerHTML );
    }

    const html = `
    <div class="dialogBody">
        <div class="commonSection">
            <div class="commonTitle">${getMessage.FTE14008}</div>
            <div class="commonBody">
                <div class="commonInputGroup">
                    <table class="commonInputTable">
                        <tbody class="commonInputTbody">
                            <tr class="commonInputTr">
                                <th class="commonInputTh"><div class="commonInputTitle">${getMessage.FTE14009}</div></th>
                                <td class="commonInputTd">
                                    <select class="input select aiSelect" name="aiSelect">
                                        <option value=""></option>
                                        ${list.join('')}
                                    </select>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        <div class="commonSection aiSetting" style="display:none;">
            ${this.aiAssistantSettingHtml( this.setting.assistant ?? '')}
        </div>
    </div>`;

    // HTMLセット
    settingModal.open( html );
    const $setting = settingModal.$.dialog.find('.aiSetting');
    if ( this.setting.assistant ) $setting.show();
    $setting.find('.textareaAdjustmentWrap').css('height', '32px');
    $setting.find('.modelSelect').select2();
    settingModal.$.footer.find('.dialogFooterMenuItem:last-child').css('margin-left', 'auto');
    settingModal.buttonPositiveDisabled( false );

    // AIアシスタント選択
    settingModal.$.dialog.on('change', '.aiSelect', async ( e ) => {
        const assistant = $( e.currentTarget ).val();
        if ( assistant ) {
            await this.getModule( assistant );
            $setting.show().html( this.aiAssistantSettingHtml( assistant ) );
            $setting.find('.textareaAdjustmentWrap').css('height', '32px');
            $setting.find('.modelSelect').select2();
        } else {
            $setting.hide().empty();
        }
    });

    // モデルリスト読込
    settingModal.$.dialog.on('click', '.modelSelectButton', async ( e ) => {
        let process = fn.processingModal(getMessage.FTE14010);
        const assistant = settingModal.$.dialog.find('.aiSelect').val();

        // 各アシスタントの設定フィールドを取得
        const settingFields = this.llm[ assistant ]?.setting ?? {};
        const apiParam = {};

        for ( const key in settingFields ) {
            const value = settingModal.$.dialog.find(`[name="${key}"]`).val();
            if ( value ) {
                apiParam[ key ] = value;
            }
        }

        // 後方互換性: apiKeyフィールドが存在する場合（Gemini等）
        const apiKey = settingModal.$.dialog.find('[name="apiKey"]').val();
        if ( apiKey ) {
            apiParam.apiKey = apiKey;
        }

        // Bedrock等の複数パラメータ、またはGeminiのapiKeyを渡す
        const param = Object.keys(apiParam).length > 0 ? apiParam : apiKey;

        await this.getModelList( param, assistant );
        settingModal.$.dialog.find('[data-key="modelSelect"] .inputListBody').html( this.createModelListSelectHtml( assistant ) );
        $setting.find('.modelSelect').select2();
        process.close();
        process = null;
    });

    // モデル初期値切り替え
    settingModal.$.dialog.on('change', '.modelSelect', async ( e ) => {
        const assistant = settingModal.$.dialog.find('.aiSelect').val();
        const $option = $( e.currentTarget ).find('option:selected');
        const list = [];
        $option.each( ( i, e ) => {
            const $o = $( e );
            const t = $o.text();
            const v = $o.val();
            list.push({
                id: v,
                text: t
            });
        });
        settingModal.$.dialog.find('[data-key="modelDefault"]').html( this.createModelListDefaultSelectHtml( assistant, list ) );
    });
}
/*
##################################################
    AIアシスタント設定HTML
##################################################
*/
aiAssistantSettingHtml( assistant ) {
    if ( this.llm[ assistant ] === undefined ) return '';
    const html = [];
    const settingList = this.llm[ assistant ].setting ?? null;
    if ( settingList === null ) return '';
    for ( const key in settingList ) {
        const item = settingList[ key ];
        const title = item.title ?? '';
        const value = ( this.setting[ assistant ] )? this.setting[ assistant ][ key ] ?? '': '';
        switch ( item.type ) {
            case 'password':
                html.push( this.createSettingRowHtml( key, title, fn.html.inputPassword('', value, key, {}, { textarea: 'sizing'} )));
                break;
            case 'text':
                html.push( this.createSettingRowHtml( key, title, fn.html.inputText('', value, key, {}, { textarea: 'sizing'} )));
                break;
            case 'modelSelect':
                html.push( this.createSettingRowHtml( key, title, this.createModelListHtml( assistant ) ) );
                break;
            case 'modelDefault':
                html.push( this.createSettingRowHtml( key, title, this.createModelListDefaultSelectHtml( assistant ) ) );
                break;
        }
    }
    return `
    <div class="commonTitle">${this.aiAssistantList[assistant]} ${getMessage.FTE14011}</div>
    <div class="commonBody">
        <div class="commonInputGroup">
            <table class="commonInputTable">
                <tbody class="commonInputTbody">
                    ${html.join('')}
                </tbody>
            </table>
        </div>
    </div>`;
}
// 設定列HTML
createSettingRowHtml( key, title, body ) {
    return `
    <tr class="commonInputTr">
        <th class="commonInputTh"><div class="commonInputTitle">${fn.escape(title)}</div></th>
        <td class="commonInputTd" data-key="${key}">${body}</td>
    </tr>`;
}
// モデルリスト選択
createModelListHtml( assistant ) {
    const selectHtml = this.createModelListSelectHtml( assistant );
    return `
    <div class="inputListWrap">
        <div class="inputListBody">
            ${selectHtml}
        </div>
        <div class="inputListButton">
            ${fn.html.button( fn.html.icon('update01'), 'itaButton button popup modelSelectButton', { action: 'default', title: getMessage.FTE14010})}
        </div>
    </div>`;
}
// モデルリストselect HTML
createModelListSelectHtml( assistant ) {
    const selectedList = ( this.setting[ assistant ] && this.setting[ assistant ].modelSelect )? this.setting[ assistant ].modelSelect: [];
    const list = ( this.modelList[ assistant ])? this.modelList[ assistant ]: selectedList;
    const selected = selectedList.map( i => i.id );

    return `
    <select class="input modelSelect" name="modelSelect" multiple>
        ${this.createOptionHtml( list, selected )}
    </select>`;
}
// モデルリスト初期値select HTML
createModelListDefaultSelectHtml( assistant, setList ) {
    const selectedList = ( this.setting[ assistant ] && this.setting[ assistant ].modelDefault )? [ this.setting[ assistant ].modelDefault ]: [];
    const list = ( setList )
        ? setList
            : ( this.setting[ assistant ] && this.setting[ assistant ].modelSelect && this.setting[ assistant ].modelSelect.length )
                ? this.setting[ assistant ].modelSelect
                : selectedList;
    const selected = selectedList.map( i => i.id );
    
    return `
    <select class="input modelDefault" name="modelDefault">
        ${this.createOptionHtml( list, selected )}
    </select>`;
}
// option html
createOptionHtml( list, selected ) {
    const html = [];
    for ( const item of list ) {
        const option = document.createElement('option');
        option.textContent = item.text;
        option.value = item.id;
        if ( selected.includes( item.id ) ) option.setAttribute('selected', '');
        html.push( option.outerHTML );
    }
    return html.join('')
}
// モデルリスト読込
async getModelList( apiKey, assistant ) {
    try {
        this.modelList[ assistant ] = await this.llm[ assistant ].getModelList( apiKey );
    } catch( error ) {
        console.error( error );
        if ( error.message ) {
            alert( error.message );
        } else {
            alert(getMessage.FTE14012)
        }
        this.modelList[ assistant ] = [];
    }
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   開発支援
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    開発支援エリアを開く
##################################################
*/
async openSupport() {
    let process = fn.processingModal(getMessage.FTE14013);

    // Setup
    this.operation = false;
    this.message = [];
    const assistant = this.setting.assistant;
    try {
        await this.llm[ assistant ].setup( this.setting[ assistant ] );
    } catch( error ) {
        console.error( error );
        if ( error.message) {
            alert( error.message );
        } else {
            alert(getMessage.FTE14014);
        }
    }

    this.setSupportArea();
    this.$.input = this.modal.$.dialog.find('.developmentSupportInput');
    this.$.send = this.modal.$.dialog.find('.developmentSupportInputSubmit');
    this.$.file = this.modal.$.dialog.find('.developmentSupportInputFile');
    this.$.fileBlock = this.modal.$.dialog.find('.developmentSupportFileBlock');
    this.$.chat = this.modal.$.dialog.find('.developmentSupportChatBlock');
    this.setEvents();
    
    this.modal.$.dialog.addClass('developmentSupportOpen').find('.dialog').css('width', '1920px');

    process.close();
    process = null;
}
/*
##################################################
    開発支援エリアHTML
##################################################
*/
setSupportArea() {
    const assistant = this.setting.assistant;
    const title = this.aiAssistantList[ assistant ];
    const className = 'dialogButton itaButton popup';
    const closeButton = fn.html.iconButton('cross', getMessage.FTE14005, className, { kind: 'llmClose', action: 'normal', title: getMessage.FTE14015});
    const historyDownloadButton = fn.html.button( fn.html.icon('download'), className, { kind: 'historyDownload', action: 'restore', title: getMessage.FTE14016});
    const html = `
    <div class="subDialogMain dialogMain dialogAnimation">
        <div class="dialogHeader subDialogHeader">
            <div class="dialogHeaderTitle">
                <span class="dialogHeaderTitleInner">${fn.escape(title)}</span>
            </div>
        </div>
        <div class="dialogBody subDialogBody">${this.mainHtml()}</div>
        <div class="dialogFooter subDialogFooter">
            <ul class="dialogFooterMenuList">
                <li class="dialogFooterMenuItem">${closeButton}</li>
                <li class="dialogFooterMenuItem" style="flex:1 1 auto;margin-left:auto;">${this.modelListHtml()}</li>
                <li class="dialogFooterMenuItem">${historyDownloadButton}</li>
            </ul>
        </div>
    </div>`;
    this.modal.$.dialog.addClass('subDialogMode').find('.dialog').append( html );
    this.modal.$.dialog.find('.subDialogBody .textareaAdjustmentWrap').css('height', '32px');
    this.modal.$.dialog.find('.subDialogFooter .modelSelect').on('change', ( e ) => {
        const value = $( e.currentTarget ).val();
        this.llm[ this.setting.assistant ].setModel( value );
    });
}
// モデルリストHTML
modelListHtml() {
    const assistant = this.setting.assistant;
    const def = this.setting[ assistant ].modelDefault ?? {};
    const list = [];
    for ( const item of this.setting[ assistant ].modelSelect ) {
        const option = document.createElement('option');
        option.textContent = item.text;
        option.value = item.id;
        if ( item.id === def.id ) option.setAttribute('selected', '');
        list.push( option.outerHTML );
    }
    return `<select class="input inputSelect modelSelect" name="models">${list.join('')}</select>`;
}
/*
##################################################
    作業開始
##################################################
*/
operationStart() {
    if ( this.operation ) return;
    this.operation = true;
}
/*
##################################################
    作業終了
##################################################
*/
operationEnd() {
    if ( !this.operation ) return;
    this.operation = false;
}
/*
##################################################
    Main HTML
##################################################
*/
mainHtml() {
    return `
    <div class="developmentSupportContainer">
        <div class="developmentSupportChatBlock">
            ${this.initialMessageHtml()}
        </div>
        <div class="developmentSupportFileBlock">
        </div>
        <div class="developmentSupportInputBlock">
            <div class="developmentSupportInputTextBlock">
                ${fn.html.textarea('developmentSupportInput', '', 'developmentSupportInput', {'placeholder': getMessage.FTE14017}, true )}
            </div>
            <div class="developmentSupportInputFileBlock">
                ${fn.html.button( fn.html.icon('plus'), 'developmentSupportInputFile itaButton button popup', { action: 'positive', title: getMessage.FTE14018})}
            </div>
            <div class="developmentSupportInputSubmitBlock">
                ${fn.html.button( fn.html.icon('send'), 'developmentSupportInputSubmit itaButton button', { action: 'positive'})}
            </div>
        </div>
    </div>`;
}
/*
##################################################
    初期メッセージ
##################################################
*/
initialMessageHtml() {
    return ``
    + `<div class="developmentSupportInitialMessage">`
        + `${getMessage.FTE14019}`
    + `</div>`;
}
/*
##################################################
    チャット HTML
##################################################
*/
updateChat( message, file ) {
    if ( this.message.length === 0 && message.role === 'user') {
        this.$.chat.html(`<ul class="developmentSupportList"></ul>`);
        this.$.chatList = this.$.chat.find('.developmentSupportList');
    }

    try {
        const $message = $(``
        + `<li class="developmentSupportItem" data-role="${message.role}">`
            + `${( message.role === 'support')? `<div class="developmentSupportItemIcon"></div>`: ``}`
            + `<div class="developmentSupportItemInner">`
            + `</div>`
        + `</li>`);
        if ( message.role === 'user') {
            if ( file ) {
                const fileName = `<div class="developmentSupportItemFile">${fn.html.icon('note')}${fn.escape( file.name ?? '')}</div>`;
                const messageText = fn.escape( message.text ?? '');
                $message.find('.developmentSupportItemInner').html( fileName + messageText );
            } else {
                $message.find('.developmentSupportItemInner').text( message.text );
            }
        } else if ( message.role === 'support') {
            $message.find('.developmentSupportItemInner').html( this.loadingHtml() );
        }
        this.$.chatList.append( $message );
        setTimeout( () => {
            this.scrollChatArea( $message );
        }, 300 );
        return $message;
    } catch ( error ) {
        console.error( error );
    }
}
/*
##################################################
    チャットスクロール
##################################################
*/
scrollChatArea( $obj ) {
    const scrollTop = this.$.chat.scrollTop() + $obj.position().top - 16;
    this.$.chat.animate({ scrollTop: scrollTop }, 100 );
}
/*
##################################################
    ローディングHTML
##################################################
*/
loadingHtml() {
    return ``
    + `<div class="developmentSupportItemNowLoading">`
        + `<div class="developmentSupportItemNowLoading-dot developmentSupportItemNowLoading-dot-1"></div>`
        + `<div class="developmentSupportItemNowLoading-dot developmentSupportItemNowLoading-dot-2"></div>`
        + `<div class="developmentSupportItemNowLoading-dot developmentSupportItemNowLoading-dot-3"></div>`
        + `<div class="developmentSupportItemNowLoading-dot developmentSupportItemNowLoading-dot-4"></div>`
        + `<div class="developmentSupportItemNowLoading-dot developmentSupportItemNowLoading-dot-5"></div>`
    + `</div>`;
}
/*
##################################################
    イベント
##################################################
*/
setEvents() {
    this.setSendMessageEvent();
    this.setCodeCopyEvent();
};
/*
##################################################
    メッセージ送信イベント
##################################################
*/
setSendMessageEvent() {
    // エンター
    this.$.input.on('keydown', async ( e ) => {
        if ( this.operation ) return;
        if ( e.key === 'Enter' && !e.shiftKey ) {
            this.sendButtonDisabled( true );
            e.preventDefault();
            await this.sendMessage();
            this.sendButtonDisabled( false );
        }
    });

    // 送信ボタン
    this.$.send.on('click', async ( e ) => {
        if ( this.operation ) return;
        this.sendButtonDisabled( true );
        await this.sendMessage();
        this.sendButtonDisabled( false );
    });

    // コード添付
    this.$.file.on('click', async ( e ) => {
        if ( this.operation ) return;
        this.sendButtonDisabled( true );
        if ( this.file ) {
            this.clearFile();
        } else {
            this.setFile();
        }
        this.sendButtonDisabled( false );
    });

    // ファイル削除
    this.$.fileBlock.on('click', '.fileRemoveButton', () => {
        this.clearFile();
    });
}
// 送信ボタン管理
sendButtonDisabled( flag ) {
    this.$.send.prop('disabled', flag );
    this.$.file.prop('disabled', flag );
}
/*
##################################################
    コードコピー
##################################################
*/
setCodeCopyEvent() {
    // navigator.clipboardが使える場合のみ（https or localhost）
    if ( navigator && navigator.clipboard ) {
        this.$.chat.addClass('codeClipboardCopyOk');
        const message = new Message();
        this.$.chat.on('click', 'code', async ( e ) => {
            const $code = $( e.currentTarget );
            if ( $code.is('.copyStart') ) return;

            const text = e.currentTarget.textContent || '';
            if ( !text ) {
                console.warn('copy text is empty', e.currentTarget );
                return;
            }

            const previewLength = 50;
            const preview = Array.from(text).length > previewLength
                ? Array.from(text).slice(0, previewLength).join('') + '...'
                : text;

            $code.addClass('copyStart');
            try {
                await navigator.clipboard.writeText( text );
                message.add('success', getMessage.FTE14020, preview, null, 1000 );
            } catch ( err ) {
                console.error( err );
                message.add('danger', getMessage.FTE14021, preview, null, 1000 );
            } finally {
                await this.sleep( 1000 );
                $code.removeClass('copyStart');
            }
        });
    }
}
/*
##################################################
    スリープ
##################################################
*/
sleep( time ) {
    return new Promise( ( resolve ) => setTimeout( resolve, time ) );
}
/*
##################################################
    ファイル準備
##################################################
*/
setFile() {
    this.file = this.getEditorData();
    this.$.fileBlock.show().html(`
    <ul class="developmentSupportFileList">
        <li class="developmentSupportFileItem">
            ${fn.html.icon('note')}
            ${fn.escape(this.file.name ?? '')}
            ${fn.html.button( fn.html.icon('cross'), 'fileRemoveButton')}
        </li>
    </ul>`);
}
// クリア
clearFile() {
    this.file = null;
    this.$.fileBlock.hide().empty();
}
/*
##################################################
    メッセージ送信
##################################################
*/
sendMessage( e ) {
    return new Promise( async ( resolve ) => {
        this.operationStart();

        // ユーザメッセージ
        const message = this.$.input.val();
        if ( message === '') {
            this.operationEnd();
            return resolve();
        }
        this.$.input.val('').trigger('input');
        const userMessage = {
            role: 'user',
            text: message
        };
        const $userMessage = this.updateChat( userMessage, this.file );
        this.$.fileBlock.hide();

        await this.sleep( 1000 );

        // サポートメッセージ
        const supportMessage = {
            role: 'support'
        };
        const $supportMessage = this.updateChat( supportMessage );
        try {
            const result = await this.llm[ this.setting.assistant ].send( message, this.file );
            this.clearFile();
            supportMessage.text = result;

            await this.sleep( 100 );

            const $message = $supportMessage.find('.developmentSupportItemInner');
            $message.html( this.md.render( supportMessage.text ) );
            // classのついていないpre > codeに.codeBlockを付与
            $message.find('pre > code').each( ( i, el ) => {
                const $code = $( el );
                if ( !$code.is('.hljs') )  {
                    $code.addClass('codeBlock');
                }
            });
            this.scrollChatArea( $supportMessage );

            this.message.push( userMessage );
            this.message.push( supportMessage );
        } catch ( error ) {
            if ( error && error.message && error.message.indexOf('Failed to fetch') === -1 ) {
                alert( error.message );
            }

            // エラーが起きた場合はメッセージを削除し、入力欄にテキストを戻す
            $userMessage.remove();
            $supportMessage.remove();
            this.clearFile();
            this.$.input.val( message ).trigger('input');
        }
        this.operationEnd();

        resolve();
    });
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   ユーザデータ
//
////////////////////////////////////////////////////////////////////////////////////////////////////
db = {
    name: 'development_support',
    storeName: 'setting',
    keyName: 'id',
    encoder: new TextEncoder(),
    decoder: new TextDecoder(),
    cachedKey: null,
    set: async ( id, data ) => {
        try {
            await this.db.open();
            await this.db.save( id, data );
        } catch( error ) {
            console.error( error );
        } finally {
            this.db.close();
        }
    },
    get: async ( id ) => {
        let data;
        try {
            await this.db.open();
            data = await this.db.read( id );
        } catch( error ) {
            console.error( error );
        } finally {
            this.db.close();
        }
        return data;
    },
    open: () => {
        return new Promise( ( resolve ) => {    
            const request = indexedDB.open( this.db.name, 1 );
            request.onupgradeneeded = ( event ) => {
                this.IndexedDB = event.target.result;
                const keyName = this.db.keyName;
                const objectStore = this.IndexedDB.createObjectStore( this.db.storeName, {
                    keyPath: keyName,
                });
            };
            request.onsuccess = ( event ) => {
                this.IndexedDB = event.target.result;
                resolve();
            };
            request.onerror = () => {
                console.error('IndexedDB open error.')
                resolve();
            };
        });
    },
    save: ( id, data ) => {
        return new Promise( async ( resolve ) => {
            const transaction = this.IndexedDB.transaction([ this.db.storeName ], 'readwrite');
            const objectStore = transaction.objectStore( this.db.storeName );
            if ( this.db.hasCrypto() ) {
                const { iv, cipher } = await this.db.encryptJsonWithFixedKey(data);
                objectStore.put({
                    id,
                    type: 'crypto',
                    iv: Array.from( iv ),
                    cipher: Array.from( cipher ),
                });
            } else {
                const record = this.db.toBase64( data );
                objectStore.put({
                    id,
                    type: 'base64',
                    value: record
                });
            }
    
            transaction.oncomplete = () => {
                resolve();
            };
        });
    },
    read: ( id ) => {
        return new Promise( ( resolve ) => {
            const transaction = this.IndexedDB.transaction([ this.db.storeName ], 'readonly');
            const objectStore = transaction.objectStore( this.db.storeName );
            const request = objectStore.get( id );
    
            request.onsuccess = async () => {
                const record = request.result;
                if ( !record ) return resolve( null );
                
                if ( record.type === 'crypto') {
                    try {
                        // Array → Uint8Array に戻す
                        const iv = record.iv instanceof Uint8Array ? record.iv : new Uint8Array( record.iv );
                        const cipher = record.cipher instanceof Uint8Array ? record.cipher : new Uint8Array( record.cipher );
                        const plainData = await this.db.decryptJsonWithFixedKey( iv, cipher );
                        resolve( plainData );
                    } catch (e) {
                        console.error('decrypt error:', e);
                        resolve( null );
                    }
                } else if ( record.type === 'base64') {
                    try {
                        resolve( this.db.fromBase64( record.value ) );
                    } catch (e) {
                        console.error('pase error:', e);
                        resolve( null );
                    }
                } else {
                    alert('Read error.');
                    console.error('read error:', e);
                    resolve( null );
                }
            };
    
            request.onerror = () => {
                resolve( null );
            };
        });
    },
    delete: () => {
        return new Promise( ( resolve ) => {
            const request = indexedDB.deleteDatabase( this.db.name );
    
            request.onsuccess = () => {
                resolve();
            };
    
            request.onerror = () => {
                console.warn("IndexedDB delete error.");
                resolve();
            };

            request.onblocked = () => {
                console.warn("IndexedDB delete blocked.");
                resolve();
            };
        });
    },
    close: () => {
        this.IndexedDB.close();
    },
    // crypto
    hasCrypto: () => {
        return (
          typeof window.crypto !== 'undefined' &&
          typeof window.crypto.subtle !== 'undefined'
        );
    },
    setFixedAesKey: async () => {
        if ( this.cachedKey ) return;
        let raw = this.db.encoder.encode( this.id );
        if ( raw.length < 32 ) {
            const padded = new Uint8Array(32);
            padded.set(raw);
            raw = padded;
        } else if ( raw.length > 32 ) {
            raw = raw.slice( 0, 32 );
        }
        this.cachedKey = await crypto.subtle.importKey(
            'raw',
            raw,
            { name: 'AES-GCM' },
            false,
            ['encrypt', 'decrypt']
        );    
        return;
    },
    encryptJsonWithFixedKey: async ( dataObj ) => {
        await this.db.setFixedAesKey();
        const json = JSON.stringify( dataObj );
        const plaintext = this.db.encoder.encode( json );    
        const iv = crypto.getRandomValues( new Uint8Array(12) );
        const cipherBuffer = await crypto.subtle.encrypt(
            { name: 'AES-GCM', iv },
            this.cachedKey,
            plaintext
        );    
        return {
            iv,
            cipher: new Uint8Array( cipherBuffer ),
        };
    },
    decryptJsonWithFixedKey: async ( iv, cipher ) => {
        await this.db.setFixedAesKey();
        const plainBuffer = await crypto.subtle.decrypt(
            { name: 'AES-GCM', iv },
            this.cachedKey,
            cipher
        );    
        const plaintext = this.db.decoder.decode( plainBuffer );
        return JSON.parse( plaintext );
    },
    // base64
    toBase64: ( dataObj ) => {
        const json = JSON.stringify( dataObj );
        const bytes = new TextEncoder().encode(json);
        let binary = '';
        bytes.forEach(b => binary += String.fromCharCode(b));
        return btoa(binary);
    },
    fromBase64: ( base64 ) => {
        const binary = atob(base64);
        const bytes = Uint8Array.from(binary, c => c.charCodeAt(0));
        const decode = new TextDecoder().decode(bytes);
        const json = JSON.parse( decode );
        return json;
    }
}

}