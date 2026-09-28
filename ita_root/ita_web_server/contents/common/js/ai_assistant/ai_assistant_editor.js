////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Exastro IT Automation / ai_assistant_editor.js
//
//   -----------------------------------------------------------------------------------------------
//
//   Copyright 2026 NEC Corporation
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

// ファイル編集画面（common.jsのfn.fileEditor）から開くAIアシスタント。
// 左側にエディター、右側にAIアシスタントが並ぶ形（ダイアログの中にもう1つダイアログを並べる
// サブダイアログ）で、編集中のファイルの作成・修正をAIに手伝ってもらうためのもの。
//
// ・右側に組み立てるのはAIアシスタントメニューと同じ3つのタブ
//   （AIアシスタント・会話履歴・学習事項）で、中身はAiAssistantをそのまま使う。
//   置き場所（タブの中身の要素・タブの開閉）だけをこのクラスから渡している。
// ・ここから始めた会話はプロンプトプロファイルがLLMEditorになる（メニューから始めた会話は
//   AgenticAI）。ITAの操作を主とするメニュー側とは目的が違うため、プラットフォーム側で
//   読み込むシステムプロンプトを分けている。会話履歴タブの一覧もプロファイルで絞り込まれる。
// ・AIアシスタント一式（ai_assistant.jsなど）はファイル数が多いため、右側を開くときに
//   まとめて読み込む（開かない場合は読み込まない）。
//
// 使い方（fn.fileEditorの編集モードから呼ばれる）
//   const editor = new AiAssistantEditor();
//   await editor.setup( modal, aceEditor );
class AiAssistantEditor {
/*
##################################################
   定数
##################################################
*/
// ここから始めた会話のプロンプトプロファイル（プラットフォーム側で読み込むプロンプトの種別）
static get promptProfile() {
    return AiAssistantLlm.editorPromptProfile;
}
// 会話履歴・学習事項の一覧のTableに付けるIDの接頭辞。
// AIアシスタントメニューの一覧とIDがぶつからないようにするためのもの
// （Tableは自分のIDでスタイルを書き出すため、同じIDが2つあると表示が崩れる）。
static get tableIdPrefix() {
    return 'Editor';
}
// 右側を開いたときのダイアログの幅（エディターとAIアシスタントを左右に並べるため広げる）
static get openDialogWidth() {
    return '1920px';
}
// 右側を開くときに読み込むAIアシスタント一式（AIアシスタントメニューと同じもの）
static get assets() {
    return [
        { type: 'js', url: '/_/ita/js/ai_assistant.js'},
        { type: 'js', url: '/_/ita/js/ai_assistant/ai_assistant_setting.js'},
        { type: 'js', url: '/_/ita/js/ai_assistant/ai_assistant_llm.js'},
        // 会話履歴・学習事項のインポート／エクスポート
        { type: 'js', url: '/_/ita/js/ai_assistant/ai_assistant_transfer.js'},
        // 画面専用ツール（ツールごとに定義と動作を1ファイルにまとめている）
        { type: 'js', url: '/_/ita/js/ai_assistant/tools/ai_assistant_tool_ask_user_choice.js'},
        { type: 'js', url: '/_/ita/js/ai_assistant/tools/ai_assistant_tool_display_html.js'},
        // チャット部分
        { type: 'js', url: '/_/ita/js/ai_assistant/ai_assistant_chat.js'},
        // プラットフォームAPIの一覧表示用Table（会話履歴・学習事項の一覧に使う）
        { type: 'js', url: '/_/ita/js/table_pf.js'},
        { type: 'css', url: '/_/ita/css/conductor.css'},
        { type: 'css', url: '/_/ita/css/ai_assistant.css'},
        // コードブロック反映・差分確認
        { type: 'js', url: '/_/ita/lib/diffjs/diff.min.js' },
        { type: 'js', url: '/_/ita/lib/diff2html/diff2html.min.js' },
        { type: 'css', url: '/_/ita/lib/diff2html/diff2html.css' },
        { type: 'css', url: '/_/ita/css/compare.css'},
    ];
}
/*
##################################################
   AIアシスタント一式の読み込み
##################################################
*/
// 一度読み込めば以降は不要なため、読み込みのPromiseを保持して使いまわす。
// 読み込み済みかどうかはクラスの有無で判定する（AIアシスタントメニューのように
// すでに読み込まれている画面から開かれた場合は、読み込みなおすと同じクラスを
// 二重に宣言してしまうため）。
static loadAssets() {
    if ( typeof AiAssistant === 'function') return Promise.resolve();

    if ( !AiAssistantEditor._loadAssets ) {
        AiAssistantEditor._loadAssets = fn.loadAssets( AiAssistantEditor.assets ).catch(function( error ){
            // 失敗した場合は、開きなおしたときにもう一度読み込めるようにする
            AiAssistantEditor._loadAssets = null;
            throw error;
        });
    }
    return AiAssistantEditor._loadAssets;
}
/*
##################################################
   Constructor
##################################################
*/
constructor() {
    // AIアシスタント（右側を開いたときに作る）
    this.aa = null;
    // 要素の保持
    this.$ = {};
}
/*
##################################################
   Setup
##################################################
*/
// ファイル編集画面のダイアログへ「AIアシスタントを開く」ボタンを追加する。
// 右側の画面そのものは、そのボタンが押されたときに組み立てる。
//   modal     … ファイル編集画面のDialog
//   aceEditor … 左側のエディター（編集中の内容を添付するために使う）
async setup( modal, aceEditor ) {
    const ae = this;

    ae.modal = modal;
    ae.editor = aceEditor;

    // ユーザ情報（チャットの動作に必要。取れない場合はAIアシスタントを出さない）
    const userData = fn.storage.get('restUser', 'session');
    if ( !userData || !userData.user_id ) {
        window.console.warn('AI assistant is not available. (user information cannot be found.)');
        return;
    }
    ae.user = userData;

    // 右側を閉じたときに戻す幅（ファイル編集画面のダイアログの元の幅）
    ae.dialogWidth = fn.cv( modal.config?.width, '960px');

    ae.modal.$.dialog.addClass('aiAssistantEditor');
    ae.setButton();
    ae.setDialogCloseEvent();

    return;
}
/*
##################################################
   ファイル編集画面へのボタンの追加
##################################################
*/
setButton() {
    const ae = this;

    const openButton = fn.html.button( fn.html.icon('stick'), 'dialogButton itaButton popup',
        { kind: 'aiAssistantOpen', action: 'default', title: getMessage.FTE14380 });
    ae.modal.$.footer.find('.dialogFooterMenuList')
        .append(`<li class="dialogFooterMenuItem" style="margin-left:auto;">${openButton}</li>`);
    ae.$.openButton = ae.modal.$.footer.find('.itaButton[data-kind="aiAssistantOpen"]');

    // 右側の開閉と、編集中のファイルの添付（サブダイアログ側のボタン）
    ae.modal.btnFn.aiAssistantOpen = () => ae.open();
    ae.modal.btnFn.aiAssistantClose = () => ae.close();
    ae.modal.btnFn.aiAssistantAttach = () => ae.attachEditingFile();
}
// ファイル編集画面が閉じられたときに後片付けする。
// 閉じ方が複数あるため（閉じるボタン・更新ボタン）、Dialogのclose自体を包んで1か所で行う。
setDialogCloseEvent() {
    const ae = this,
          modal = ae.modal,
          close = modal.close.bind( modal );

    modal.close = function(){
        ae.destroy();
        return close();
    };
}
/*
##################################################
   右側のAIアシスタントを開く
##################################################
*/
async open() {
    const ae = this;

    ae.$.openButton.prop('disabled', true );
    const process = fn.processingModal( getMessage.FTE14382 );

    // 失敗を知らせるのは読み込み中の表示を消してから（重なって表示されないようにする）
    let failed = null;
    try {
        await AiAssistantEditor.loadAssets();

        // 3つのタブの枠を作る（この時点でタブの切り替えができる状態にしておき、
        // このあとのAiAssistantからタブが開かれたときの処理を登録してもらう）
        ae.setPanel();

        // AIアシスタントメニューと同じ3つのタブの中身を、作った枠の中へ組み立てる
        ae.aa = new AiAssistant( null, { user: ae.user }, {
            promptProfile: AiAssistantEditor.promptProfile,
            tableIdPrefix: AiAssistantEditor.tableIdPrefix,
            elements: ae.tabElements(),
            onTabOpen: ( name, callback ) => ae.onTabOpen( name, callback ),
            openTab: ( name ) => ae.openTab( name )
        });
        await ae.aa.setup();

        // ai_assistant_chatのsetCodeBlockToEditorメソッドをオーバーライドして、
        // エディターへの反映処理をこのクラスで処理する
        if ( ae.aa.chat ) {
            ae.aa.chat.setCodeBlockToEditor = ( button ) => {
                try{
                    ae.setCodeBlockToEditor( button )
                } catch(error){
                    console.error('setCodeBlockToEditor execution error:',error);
                }
            };
        }
    } catch ( error ) {
        failed = error;
    }
    await process.close();

    if ( failed ) {
        window.console.error( failed );
        // 中途半端に開いたままにしないよう、閉じた状態へ戻してから理由を知らせる
        ae.close();
        // 読み込みの失敗（スクリプトのonerror）は理由が分からないため、分かる場合だけ添える
        const detail = fn.cv( failed?.message, '');
        await fn.alert( getMessage.FTE14022, getMessage.FTE14383
            + (( detail )? `<br>${fn.escape( detail, true )}`: '') );
    }
}
/*
##################################################
   右側のAIアシスタントの枠
##################################################
*/
// エディターの右側に並べるサブダイアログ（3つのタブとフッターのボタン）を作る。
setPanel() {
    const ae = this;

    const className = 'dialogButton itaButton popup';
    const closeButton = fn.html.iconButton('cross', getMessage.FTE00170, className,
        { kind: 'aiAssistantClose', action: 'normal', title: getMessage.FTE14381});
    const attachButton = fn.html.button( fn.html.icon('note'), className,
        { kind: 'aiAssistantAttach', action: 'positive', title: getMessage.FTE14384});

    // タブはAIアシスタントメニューと同じ並び（data-tabはAiAssistant側の名前と合わせる）
    const tabs = [
        { name: 'container', title: getMessage.FTE14022 },
        { name: 'conversations', title: getMessage.FTE14023 },
        { name: 'lessons', title: getMessage.FTE14024 }
    ];

    const html = `
    <div class="subDialogMain dialogMain dialogAnimation">
        <div class="dialogHeader subDialogHeader">
            <div class="dialogHeaderTitle">
                <span class="dialogHeaderTitleInner">${getMessage.FTE14022}</span>
            </div>
        </div>
        <div class="dialogBody subDialogBody">
            <div class="commonTab aiAssistantEditorTab">
                <div class="commonTabMenu">
                    <ul class="commonTabList">
                        ${tabs.map(( tab ) => `<li class="commonTabItem" data-tab="${tab.name}">${tab.title}</li>`).join('')}
                    </ul>
                </div>
                <div class="commonTabBody">
                    ${tabs.map(( tab ) => `<div class="commonTabSection" data-tab="${tab.name}"></div>`).join('')}
                </div>
            </div>
        </div>
        <div class="dialogFooter subDialogFooter">
            <ul class="dialogFooterMenuList">
                <li class="dialogFooterMenuItem">${closeButton}</li>
                <li class="dialogFooterMenuItem" style="margin-left:auto;">${attachButton}</li>
            </ul>
        </div>
    </div>`;

    // 左右に並べる（サブダイアログの分だけダイアログを広げる）
    ae.modal.$.dialog.addClass('subDialogMode')
        .find('.dialog').css('width', AiAssistantEditor.openDialogWidth ).append( html );

    ae.$.tab = ae.modal.$.dialog.find('.aiAssistantEditorTab');

    // タブの切り替え（最初のタブが開いた状態になる）。
    // AiAssistant側のタブが開かれたときの処理より先に登録して、
    // 一覧を組み立てるときにはタブが表示されている状態にする。
    fn.commonTab( ae.$.tab );
}
// 3つのタブの中身を入れる要素（AiAssistantのoption.elementsへ渡すもの）
tabElements() {
    const ae = this,
          select = ( name ) => ae.$.tab.find(`.commonTabSection[data-tab="${name}"]`).get(0);
    return {
        chat: select('container'),
        conversations: select('conversations'),
        lessons: select('lessons')
    };
}
// タブが開かれたときの処理を登録する（一覧はタブを最初に開いたときに取得するため）
onTabOpen( name, callback ) {
    this.$.tab?.find(`.commonTabItem[data-tab="${name}"]`).on('click', callback );
}
// タブを開く（会話を再開したあとにチャットを表示するために使う）
openTab( name ) {
    this.$.tab?.find(`.commonTabItem[data-tab="${name}"]`).trigger('click');
}
/*
##################################################
   編集中のファイルの添付
##################################################
*/
// 編集中の内容を、チャットの添付ファイルとして追加する。
// 「このファイルをこう直したい」と頼めるようにするためのもので、テキストファイル
// （fn.textToFileが作るtext/plain）はそのままの中身がAIへ渡される。
attachEditingFile() {
    const ae = this,
          chat = ae.aa?.chat;
    // 応答処理・ツール実行中は、送るファイルが途中で変わらないように受け付けない
    if ( !chat || chat.isRunning ) return;

    // ファイル名は編集中のもの（入力欄が空の場合はダイアログのタイトル＝元のファイル名）
    const inputName = fn.cv( ae.modal.$.dbody.find('.editorFileName').val(), '').trim(),
          fileName = ( inputName )? inputName: fn.cv( ae.modal.config?.header?.title, 'file.txt');

    chat.setFile( [ fn.textToFile( ae.editor.getValue(), fileName ) ], { useLlm: true });

    // 添付したファイルはチャットの入力欄の上に並ぶため、チャットのタブへ切り替える
    ae.openTab('container');
}
/*
##################################################
##################################################
*/
// 右側のAIアシスタントが提案したコードブロックを編集中の内容に反映する。
setCodeBlockToEditor( button ){
    const ae = this;

    // チャットインスタンスからコードブロックのテキストを取得
    if ( !ae.aa?.chat ) return;

    //ソースコード取得(改行コードをLFに統一)
    const beforeValue = ae.editor.getValue().replace(/\r\n/g, '\n').replace(/\r/g, '\n');
    const afterValue = ae.aa.chat.getCodeBlockText( button ).replace(/\r\n/g, '\n').replace(/\r/g, '\n');

    //ファイル名取得
    const beforeFileName = fn.cv( ae.modal.config?.header?.title, 'file.txt')
    const inputName = fn.cv( ae.modal.$.dbody.find('.editorFileName').val(), '').trim();
    const afterFileName = ( inputName )? inputName: fn.cv( ae.modal.config?.header?.title, 'file.txt');

    // 差分を生成
    const unifiedDiff = Diff.createTwoFilesPatch(
        beforeFileName,
        afterFileName,
        beforeValue,
        afterValue
    );

    const diffHtml = Diff2Html.html(unifiedDiff, {
        drawFileList: false,
        matching: 'lines',
        outputFormat: 'side-by-side',
    });

    // ダイアログの設定
    const config = {
        mode: 'modeless',
        position: 'center',
        header: {
            title: getMessage.FTE14391
        },
        width: '1600px',
        footer: {
            button: {
                ok: { text: getMessage.FTE14392, action: 'positive' },
                cancel: { text: getMessage.FTE14393, action: 'normal' }
            }
        }
    };

    // ダイアログのアクション
    const func = {
        ok: () => {
            ae.editor.setValue( afterValue );
            modal.close();
            modal = null;
        },
        cancel: () => {
            modal.close();
            modal = null;
        }
    };

    // ダイアログを開く
    let modal = new Dialog( config, func );
    modal.open( diffHtml );
}


/*
##################################################
   右側のAIアシスタントを閉じる
##################################################
*/
// 閉じたあともファイル編集画面は続くため、「開く」ボタンで開きなおせるようにする。
close() {
    this.destroy();
    this.$.openButton?.prop('disabled', false );
}
// 右側のAIアシスタントを片付けて、ファイル編集画面だけの状態へ戻す。
// チャットは応答処理の中止・イベントの解除まで行う（AiAssistant.destroy）。
destroy() {
    const ae = this;

    ae.aa?.destroy();
    ae.aa = null;
    ae.$.tab = null;

    const $dialog = ae.modal?.$?.dialog;
    if ( !$dialog ) return;
    $dialog.removeClass('subDialogMode')
        .find('.dialog').css('width', ae.dialogWidth );
    $dialog.find('.subDialogMain').remove();
}

}
