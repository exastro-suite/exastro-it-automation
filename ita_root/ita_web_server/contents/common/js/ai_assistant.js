////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Exastro IT Automation / ai_assistant.js
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
// AIアシスタント（チャット・会話履歴・学習事項の3つのタブ）。
// 置き場所は呼び出し元が決められるようにしてある。既定はAIアシスタントメニューのタブだが、
// ファイル編集画面（AiAssistantEditor）はダイアログ内のタブへ同じものを組み立てる。
class AiAssistant {
/*
##################################################
   Constructor
##################################################
*/
// option で指定できるもの（省略時はAIアシスタントメニューとして動く）
//   promptProfile  … 会話を作るときのプロンプトプロファイル。会話履歴タブの一覧の
//                    絞り込みにも使う（プロファイルごとに別の一覧になる）
//   tableIdPrefix  … 一覧のTableのIDに付ける接頭辞。1つの画面に2つのAIアシスタントが
//                    ある場合にIDが衝突しないようにする
//   elements       … 3つのタブの中身を入れる要素 { chat, conversations, lessons }
//   onTabOpen      … タブが開かれたときの処理を登録する ( name, callback ) => void
//                    name は 'container'（チャット）/ 'conversations' / 'lessons'
//   openTab        … タブを開く ( name ) => void
constructor( info, params, option = {}) {
    this.info = info;
    this.params = params;
    this.option = option;
    // 会話を作るときのプロンプトプロファイル
    this.promptProfile = option.promptProfile ?? AiAssistantLlm.promptProfile;
    // 会話履歴タブの会話一覧（タブを開いたときに作る）
    this.conversationTable = null;
    // 会話履歴タブのボタンの処理中（同時に押されるのを防ぐ）
    this.conversationBusy = false;
    // 学習事項タブの学習事項一覧（タブを開いたときに作る）
    this.lessonTable = null;
    // 学習事項タブのボタンの処理中（同時に押されるのを防ぐ）
    this.lessonBusy = false;
}
/*
##################################################
   Setup
##################################################
*/
async setup() {
    this.el = this.getElements();
    await Promise.all([
        this.setupChat(),
        this.setupConversations(),
        this.setupLessons()
    ]);

    return;
}
// 画面を閉じるときの後片付け（AIアシスタントメニューでは画面遷移で消えるため呼ばないが、
// ファイル編集画面のように途中で閉じられる場所では呼ぶ必要がある）。
// チャットは実行中の応答の中止・イベントの解除まで行う（AiAssistantChat.destroy）。
destroy() {
    this.chat?.destroy();
    this.chat = null;
    this.conversationTable = null;
    this.lessonTable = null;
}
/*
##################################################
   画面の置き場所
##################################################
*/
// 3つのタブの中身を入れる要素（既定はAIアシスタントメニューのタブの中身）
getElements() {
    if ( fn.typeof( this.option.elements ) === 'object') return this.option.elements;

    const select = ( id ) => document.querySelector(`#${id} > .sectionBody`);
    return {
        chat: select('ai_assistant_container'),
        conversations: select('ai_assistant_conversations'),
        lessons: select('ai_assistant_lessons')
    };
}
// タブが開かれたときの処理を登録する（一覧はタブを最初に開いたときに取得するため）
onTabOpen( name, callback ) {
    if ( fn.typeof( this.option.onTabOpen ) === 'function') {
        this.option.onTabOpen( name, callback );
        return;
    }
    $(`.contentMenuLink[href="#ai_assistant_${name}"]`).on('click', callback );
}
// タブを開く（会話を再開したあとにチャットを表示するために使う）
openTab( name ) {
    if ( fn.typeof( this.option.openTab ) === 'function') {
        this.option.openTab( name );
        return;
    }
    $(`.contentMenuLink[href="#ai_assistant_${name}"]`).trigger('click');
}
// 一覧のTableのID（1つの画面に2つのAIアシスタントがあってもぶつからないようにする）
tableId( id ) {
    return `${fn.cv( this.option.tableIdPrefix, '')}${id}`;
}
// チャットタブ
async setupChat() {
    this.chat = new AiAssistantChat( this.params, { promptProfile: this.promptProfile });
    await this.chat.mount(this.el.chat);
}
// 会話履歴タブ。保存されている会話の一覧（GET /conversations）を表示し、行のボタンから
// 会話の再開（チャットへの復元）・保存されている会話履歴のJSON表示・タイトルの編集を行う。
// 一覧の取得はタブを最初に開いたときに行う（開かない場合はAPIを呼ばない）。
async setupConversations() {
    const aa = this;
    if ( !aa.el.conversations ) return;

    aa.onTabOpen('conversations', function(){
        if ( aa.conversationTable ) return;

        aa.conversationTable = DataTablePF.conversationList( aa.tableId('AAC'), {
            promptProfile: aa.promptProfile,
            // 会話に対する操作
            rowMenu: [
                { type: 'resume', icon: 'square_next', text: getMessage.FTE14033, action: 'positive'},
                { type: 'check', icon: 'detail', text: getMessage.FTE10059, action: 'default'},
                { type: 'titleEdit', icon: 'edit', text: getMessage.FTE00009, action: 'default'}
            ],
            rowMenuAction: ( type, item ) => aa.conversationMenuAction( type, item ),
            // 会話のインポート（メニューの右側にボタンが追加される）
            importAction: () => aa.importConversations(),
            // 選択した会話のエクスポート（メニューの右側にボタンが追加される）
            exportAction: ( items ) => aa.exportConversations( items ),
            // 選択した会話の削除（一番左にチェックボックスの列、メニューに削除ボタンが追加される）
            deleteAction: ( items ) => aa.deleteConversations( items )
        });
        // Tableのsetupで一覧の取得が始まる
        $( aa.el.conversations ).html( aa.conversationTable.setup() );
    });
}
conversationMenuAction( type, conversation ) {
    switch ( type ) {
        case 'resume':
            this.resumeConversation( conversation );
        break;
        case 'check':
            this.checkConversation( conversation );
        break;
        case 'titleEdit':
            this.editConversationTitle( conversation );
        break;
    }
}
/*
##################################################
   会話の再開
##################################################
*/
// 保存されている会話履歴をチャット画面へ復元し、その会話の続きを話せるようにする。
async resumeConversation( conversation ) {
    const aa = this,
          chat = aa.chat,
          conversationId = conversation?.conversation_id;
    if ( !conversationId || !chat || aa.conversationBusy ) return;

    // 応答中に会話を差し替えると、進行中のツール実行の結果が復元した会話へ混ざってしまう
    if ( chat.isRunning ) {
        alert( getMessage.FTE14035 );
        return;
    }

    // 復元が終わるまで行のボタンを押せないようにする（一覧の表示はそのまま）
    aa.conversationBusy = true;
    aa.conversationTable.rowMenuDisabled();
    try {
        // 認証情報の有効期限は、会話から離れている間にも切れる。切れたまま復元しても続きを
        // 送信した時点で失敗するため、復元を始める前に認証を確認する。
        // （切れている場合は、認証情報の更新を促すメッセージをチャット画面側で表示する。
        //   表示中のチャットは差し替えずに残すため、認証情報を更新すれば会話を続けられる）
        if ( !( await chat.checkAuthBeforeResume() ) ) return;

        // チャット中の場合は、ここまでの内容を保存してから差し替える
        if ( chat.newChat !== true ) {
            // 表示用の情報（発言時刻・表示文言など）を含む最新の履歴を保存しておく。
            // 失敗しても再開は妨げない（保存は応答完了時にも行われている）。
            try {
                await chat.historyEnqueue();
            } catch ( error ) {
                console.warn('会話を再開する前の履歴保存に失敗しました。', error );
            }
        }

        const history = await AiAssistantLlm.fetchHistory( conversationId );
        if ( fn.typeof( history ) !== 'array' || !history.length ) {
            alert( getMessage.FTE14036 );
            return;
        }
        // 新規チャット相当の初期化（入力欄の構築・LLMの用意）を行ってから履歴を復元する
        // （初期化を飛ばすと入力欄が無くなる）。自動再開と同じ順序。
        await chat.newChatStart();
        await chat.resumeChat( history, conversationId );

        // 復元したチャットを表示する（タブをクリックしたときと同じ切り替え）
        aa.openTab('container');
    } catch ( error ) {
        console.error( error );
        alert( getMessage.FTE14037 + '\n' + fn.cv( error?.message, ''));
    } finally {
        aa.conversationBusy = false;
        aa.conversationTable.rowMenuDisabled( false );
    }
}
/*
##################################################
   会話履歴の確認
##################################################
*/
// 保存されている会話履歴（LLMへ渡すターンの配列）をJSONとしてエディターで表示する。
async checkConversation( conversation ) {
    const aa = this,
          conversationId = conversation?.conversation_id;
    if ( !conversationId || aa.conversationBusy ) return;

    // 取得が終わるまで行のボタンを押せないようにする（一覧の表示はそのまま）
    aa.conversationBusy = true;
    aa.conversationTable.rowMenuDisabled();

    let history;
    try {
        history = await AiAssistantLlm.fetchHistory( conversationId );
    } catch ( error ) {
        console.error( error );
        alert( getMessage.FTE14038 + '\n' + fn.cv( error?.message, ''));
        return;
    } finally {
        aa.conversationBusy = false;
        aa.conversationTable.rowMenuDisabled( false );
    }

    // fn.fileEditorはファイルの内容を表示する（拡張子.jsonでJSONとして色分けされる）
    const fileName = `${conversationId}.json`,
          file = new File([ JSON.stringify( history, null, 4 ) ], fileName, { type: 'application/json'});
    await fn.fileEditor( file, fileName, 'preview', {});
}
/*
##################################################
   会話のタイトルの編集
##################################################
*/
// 会話のタイトルをダイアログで編集し、変更されたらAPIへ反映して一覧を取得しなおす。
// タイトルは一覧での目印にのみ使われるため、変更しても履歴・AIの記憶には影響しない
// （表示中のチャットの会話でも、そのまま会話を続けられる）。
async editConversationTitle( conversation ) {
    const aa = this,
          conversationId = conversation?.conversation_id;
    if ( !conversationId || aa.conversationBusy ) return;

    // ダイアログを閉じるまで行のボタンを押せないようにする（一覧の表示はそのまま）
    aa.conversationBusy = true;
    aa.conversationTable.rowMenuDisabled();

    let title;
    try {
        title = await aa.openConversationTitleDialog( conversation );
    } finally {
        aa.conversationBusy = false;
        aa.conversationTable.rowMenuDisabled( false );
    }
    // キャンセルした場合と、タイトルが変わっていない場合は更新しない
    if ( title === null || title === fn.cv( conversation.title, '') ) return;

    const processing = fn.processingModal( getMessage.FTE14070 );
    let error = null;
    try {
        await AiAssistantLlm.updateConversationTitle( conversationId, title );
    } catch ( e ) {
        console.error( e );
        error = e;
    }
    processing.close();

    if ( error ) {
        await fn.alert( getMessage.FTE14070, getMessage.FTE14072 + '<br>'
            + fn.escape( fn.cv( error?.message, ''), true ) );
        return;
    }
    // 変更したタイトルが一覧に反映されるように取得しなおす
    aa.conversationTable.reload();
}
// 会話のタイトルの編集ダイアログを表示する。
// 戻り値: 入力されたタイトル（前後の空白は取り除く）。キャンセル時はnull。
openConversationTitleDialog( conversation ) {
    const title = getMessage.FTE14070;

    return new Promise(( resolve ) => {
        const config = {
            position: 'center',
            width: '640px',
            header: { title: title },
            footer: {
                button: {
                    execute: { text: getMessage.FTE00087, action: 'positive', className: 'dialogPositive'},
                    cancel: { text: getMessage.FTE00088, action: 'normal'}
                }
            }
        };
        let dialog = new Dialog( config );
        let settled = false;
        const finish = ( result ) => {
            if ( settled ) return;
            settled = true;
            dialog.close();
            dialog = null;
            resolve( result );
        };
        const apply = () => {
            const text = ( dialog.$.dialog.find('.aiConversationTitleInput').val() ?? '').trim();
            // タイトルは必須（空のままでは適用できない）
            if ( !text ) return;
            finish( text );
        };
        dialog.btnFn = {
            execute: apply,
            cancel: () => finish( null )
        };

        const html = `
        <div class="dialogBody">
            <div class="commonSection">
                <div class="aiConversationTitleDescription">${getMessage.FTE14071}</div>
                <input type="text" class="aiConversationTitleInput input inputText" spellcheck="false" maxlength="${AiAssistantLlm.titleLength}" aria-label="${getMessage.FTE14028}" value="${fn.cv( conversation?.title, '', true )}">
            </div>
        </div>`;

        dialog.open( html );

        const $dialog = dialog.$.dialog,
              $input = $dialog.find('.aiConversationTitleInput');
        // タイトルが空の場合は適用できない（タイトルは必須）
        const updateState = () => {
            dialog.buttonPositiveDisabled(( $input.val() ?? '').trim() === '');
        };
        $dialog.on('input', '.aiConversationTitleInput', updateState );
        // 1行の入力欄のため、Enterでも適用できるようにする
        $dialog.on('keydown', '.aiConversationTitleInput', function( e ){
            if ( e.key !== 'Enter') return;
            e.preventDefault();
            apply();
        });
        updateState();
        $input.trigger('focus');
    });
}
/*
##################################################
   会話の削除
##################################################
*/
// 一覧で選択した会話をレコードごと削除する（履歴もまとめて消え、一覧からも消える）。
// 確認をとってから1件ずつ削除し、削除できなかったものがあればまとめて知らせる。
// 戻り値がfalseのときは一覧を取得しなおさない（確認をキャンセルした場合）。
async deleteConversations( conversations ) {
    const aa = this,
          chat = aa.chat;
    if ( aa.conversationBusy || fn.typeof( conversations ) !== 'array' || !conversations.length ) return false;

    const title = getMessage.FTE14039;

    // 応答中の会話を削除しても、応答の完了時に履歴が保存されなおしてしまう
    const currentId = chat?.llm?.conversationId;
    if ( chat?.isRunning && conversations.some(( item ) => item.conversation_id === currentId ) ) {
        await fn.alert( title, getMessage.FTE14040 );
        return false;
    }

    const check = await fn.iconConfirm('circle_exclamation', title,
        getMessage.FTE14041( conversations.length ) );
    if ( !check ) return false;

    aa.conversationBusy = true;
    const processing = fn.processingModal( title );

    const errors = [],
          deletedIds = [];
    for ( const conversation of conversations ) {
        const conversationId = conversation?.conversation_id;
        if ( !conversationId ) continue;
        try {
            await AiAssistantLlm.deleteConversation( conversationId );
            deletedIds.push( conversationId );
        } catch ( error ) {
            console.error( error );
            errors.push(`${fn.cv( conversation.title, conversationId )}：${fn.cv( error?.message, '')}`);
        }
    }

    // 表示中のチャットの会話を削除した場合は、会話のレコードが無くなっているため
    // そのまま続けると保存も問い合わせも失敗する。新しいチャットへ戻す（保存はしない）
    if ( chat && currentId && deletedIds.indexOf( currentId ) !== -1 ) {
        await chat.newChatStart();
    }

    processing.close();
    aa.conversationBusy = false;

    if ( errors.length ) {
        await fn.alert( title, getMessage.FTE14042( errors.length ) + '<br>'
            + fn.escape( errors.join('\n'), true ) );
    }
    return;
}
/*
##################################################
   会話のインポート・エクスポート
##################################################
*/
// 一覧で選択した会話を、保存されている会話履歴とあわせてJSONファイルへ書き出す（AiAssistantTransfer）。
// 一覧の内容は変わらないため、常にfalseを返して取得しなおしを省く。
async exportConversations( conversations ) {
    const aa = this;
    if ( aa.conversationBusy ) return false;

    aa.conversationBusy = true;
    try {
        return await AiAssistantTransfer.exportConversations( conversations );
    } finally {
        aa.conversationBusy = false;
    }
}
// 選択したJSONファイルに含まれている会話を、新しい会話として登録する（AiAssistantTransfer）。
// AIサービスとモデルは、ファイルの内容ではなくAI利用設定のものを使う（会話の作成に必要なため、
// 未設定の場合はインポートできない）。ツール定義は、インポートした会話を再開して続きを話せるよう
// 現在のツール一覧を渡す。
// 戻り値がfalseのときは一覧を取得しなおさない（キャンセルした場合・1件も登録しなかった場合）。
async importConversations() {
    const aa = this,
          chat = aa.chat;
    if ( aa.conversationBusy ) return false;

    const configured = ( chat )? chat.checkAiAssistantSetting(): false;

    aa.conversationBusy = true;
    try {
        return await AiAssistantTransfer.importConversations({
            aiServiceId: ( configured )? chat.setting.currentAiServiceId: '',
            modelId: ( configured )? chat.getUseModelId(): '',
            tools: ( chat )? chat.mcp.tools: [],
            // インポートした会話が、この一覧（同じプロンプトプロファイル）に並ぶようにする
            promptProfile: aa.promptProfile
        });
    } finally {
        aa.conversationBusy = false;
    }
}
// 学習事項タブ。登録されている学習事項（GET /lessons）の一覧を表示し、メニューのボタンから新規登録、
// 行のボタンから1件ごとの編集、選択した行に対する有効化・無効化・削除を行う。
// ページングは行わず全件を表示する（登録できる件数の案内はフッターの件数の右側へ表示する）。
// 一覧の取得はタブを最初に開いたときに行う（開かない場合はAPIを呼ばない）。
async setupLessons() {
    const aa = this;
    if ( !aa.el.lessons ) return;

    aa.onTabOpen('lessons', function(){
        if ( aa.lessonTable ) return;

        const max = AiAssistantLlm.lessonsMaxCount,
              promptMax = AiAssistantLlm.lessonsPromptMaxCount;

        aa.lessonTable = DataTablePF.lessonList( aa.tableId('AAL'), {
            promptProfile: aa.promptProfile,
            // 学習事項の新規登録（再読込の右側にボタンが追加される）
            headerMenu: [
                { type: 'lessonAdd', icon: 'plus', text: getMessage.FTE00008, action: 'positive'}
            ],
            headerMenuAction: ( type ) => aa.lessonHeaderMenuAction( type ),
            // 学習事項に対する操作
            rowMenu: [
                { type: 'edit', icon: 'edit', text: getMessage.FTE00009, action: 'default'}
            ],
            rowMenuAction: ( type, item ) => aa.lessonMenuAction( type, item ),
            // 選択した学習事項の有効化・無効化（一番左にチェックボックスの列が追加される）
            selectMenu: [
                { type: 'lessonDisable', icon: 'cross', text: getMessage.FTE14051, action: 'warning'},
                { type: 'lessonEnable', icon: 'circle_check', text: getMessage.FTE14050, action: 'restore'}
            ],
            selectMenuAction: ( type, items ) => aa.changeLessonsEnabled( type, items ),
            // 学習事項のインポート（メニューの右側にボタンが追加される）
            importAction: () => aa.importLessons(),
            // 選択した学習事項のエクスポート（メニューの右側にボタンが追加される）
            exportAction: ( items ) => aa.exportLessons( items ),
            // 選択した学習事項の削除（メニューに削除ボタンが追加される）
            deleteAction: ( items ) => aa.deleteLessons( items ),
            // 登録できる件数と、AIへ渡される件数の案内（フッターの件数の右側に表示する）。
            // 登録できる件数を超えている場合は、整理を促す表示にする。
            // 現在の件数は左側に表示されているため、文言には入れない
            notice: ( total ) => {
                const over = ( total > max ),
                      text = [( over )? getMessage.FTE14053( max ): getMessage.FTE14052( max ),
                          getMessage.FTE14065( promptMax )].join( getMessage.FTE14066 );
                return { icon: ( over )? 'circle_exclamation': 'circle_info',
                    text: fn.escape( text ), alert: over };
            }
        });
        // Tableのsetupで一覧の取得が始まる
        $( aa.el.lessons ).html( aa.lessonTable.setup() );
    });
}
lessonMenuAction( type, lesson ) {
    switch ( type ) {
        case 'edit':
            this.editLesson( lesson );
        break;
    }
}
// 一覧のメニューのボタン（行の選択によらないもの）。戻り値がfalseのときは一覧を取得しなおさない。
lessonHeaderMenuAction( type ) {
    switch ( type ) {
        case 'lessonAdd':
            return this.addLesson();
    }
    return false;
}
/*
##################################################
   学習事項の登録
##################################################
*/
// 学習事項を1件、ダイアログで入力した内容で新しく登録する。
// 戻り値がfalseのときは一覧を取得しなおさない（キャンセルした場合・登録に失敗した場合）。
async addLesson() {
    const aa = this;
    if ( aa.lessonBusy ) return false;

    // ダイアログを閉じるまでは、行のボタンからの編集を始められないようにする
    // （一覧のボタンの制御はTable側で行っている）
    aa.lessonBusy = true;

    let added;
    try {
        added = await aa.openLessonEditDialog( null );
    } finally {
        aa.lessonBusy = false;
    }
    if ( added === null ) return false;

    const processing = fn.processingModal( getMessage.FTE14067 );
    let error = null;
    try {
        // この一覧（同じプロンプトプロファイル）の学習事項として登録する
        await AiAssistantLlm.createLesson({ ...added, promptProfile: aa.promptProfile });
    } catch ( e ) {
        console.error( e );
        error = e;
    }
    processing.close();

    if ( error ) {
        await fn.alert( getMessage.FTE14067, getMessage.FTE14069 + '<br>'
            + fn.escape( fn.cv( error?.message, ''), true ) );
        return false;
    }
    // 登録した学習事項が一覧に反映されるように取得しなおす（件数の案内も更新される）
    return;
}
/*
##################################################
   学習事項の編集
##################################################
*/
// 1件の学習事項をダイアログで編集し、適用されたらAPIへ反映して一覧を取得しなおす。
async editLesson( lesson ) {
    const aa = this,
          lessonId = lesson?.lesson_id;
    if ( !lessonId || aa.lessonBusy ) return;

    // ダイアログを閉じるまで行のボタンと登録ボタンを押せないようにする（一覧の表示はそのまま）
    aa.lessonBusy = true;
    aa.lessonTable.rowMenuDisabled();
    aa.lessonTable.headerMenuDisabled();

    let edited;
    try {
        edited = await aa.openLessonEditDialog( lesson );
    } finally {
        aa.lessonBusy = false;
        aa.lessonTable.rowMenuDisabled( false );
        aa.lessonTable.headerMenuDisabled( false );
    }
    if ( edited === null ) return;

    const processing = fn.processingModal( getMessage.FTE14054 );
    let error = null;
    try {
        await AiAssistantLlm.updateLesson( lessonId, edited );
    } catch ( e ) {
        console.error( e );
        error = e;
    }
    processing.close();

    if ( error ) {
        await fn.alert( getMessage.FTE14054, getMessage.FTE14057 + '<br>'
            + fn.escape( fn.cv( error?.message, ''), true ) );
        return;
    }
    // 編集した内容が一覧に反映されるように取得しなおす
    aa.lessonTable.reload();
}
// 学習事項の編集・登録ダイアログを表示する。
// ・lesson … 編集する学習事項。nullの場合は新規登録として、内容を空・重要度は既定値・有効の状態で開く。
// ・内容・分類・重要度・状態（有効／無効）を入力できる。
// ・戻り値: 登録・更新する内容 { lesson, category, priority, enabled }。キャンセル時はnull。
openLessonEditDialog( lesson ) {
    // 新規登録（編集する学習事項が無い）の場合は、入力欄の初期値と文言を登録用にする
    const add = !lesson,
          record = ( add )
              ? { lesson: '', category: '', priority: AiAssistantLlm.lessonPriorityDefault, enabled: true }
              : lesson,
          title = ( add )? getMessage.FTE14067: getMessage.FTE14054,
          description = ( add )? getMessage.FTE14068( AiAssistantLlm.lessonsPromptMaxCount )
              : getMessage.FTE14055( AiAssistantLlm.lessonsPromptMaxCount );

    return new Promise(( resolve ) => {
        const config = {
            position: 'center',
            width: '760px',
            header: { title: title },
            footer: {
                button: {
                    execute: { text: ( add )? getMessage.FTE00008: getMessage.FTE00087,
                        action: 'positive', className: 'dialogPositive'},
                    cancel: { text: getMessage.FTE00088, action: 'normal'}
                }
            }
        };
        let dialog = new Dialog( config );
        let settled = false;
        const finish = ( result ) => {
            if ( settled ) return;
            settled = true;
            dialog.close();
            dialog = null;
            resolve( result );
        };
        dialog.btnFn = {
            execute: () => {
                const $dialog = dialog.$.dialog;
                const text = ( $dialog.find('.aiLessonsText').val() ?? '').trim();
                if ( !text ) return;
                finish({
                    lesson: text,
                    // 分類は空にできる（空文字を渡すと分類なしになる）
                    category: ( $dialog.find('.aiLessonsCategory').val() ?? '').trim(),
                    priority: $dialog.find('.aiLessonsPriority').val() ?? '',
                    enabled: $dialog.find('.aiLessonEditEnabled').prop('checked') === true
                });
            },
            cancel: () => finish( null )
        };

        const html = `
        <div class="dialogBody">
            <div class="commonSection">
                <div class="aiLessonsDescription">${description}</div>
                <div class="aiLessonsItem">
                    <div class="aiLessonsItemHead">
                        <div class="aiLessonsItemField">
                            <label class="aiLessonsItemFieldLabel" for="aiLessonEditCategory">${getMessage.FTE14044}</label>
                            <input type="text" id="aiLessonEditCategory" class="aiLessonsCategory input inputText" spellcheck="false" maxlength="${AiAssistantLlm.lessonCategoryLength}" value="${fn.cv( record.category, '', true )}">
                        </div>
                        <div class="aiLessonsItemField">
                            <label class="aiLessonsItemFieldLabel" for="aiLessonEditPriority">${getMessage.FTE14045}</label>
                            <select id="aiLessonEditPriority" class="aiLessonsPriority input select">${AiAssistantLlm.lessonPriorityOptions( record.priority )}</select>
                        </div>
                        <label class="aiLessonsItemCheckLabel" for="aiLessonEditEnabled">
                            <input type="checkbox" id="aiLessonEditEnabled" class="aiLessonEditEnabled"${( record.enabled )? ' checked': ''}>
                            <span class="aiLessonsItemCheckText">${getMessage.FTE14056}</span>
                        </label>
                    </div>
                    <textarea class="aiLessonsText textarea input" spellcheck="false" rows="10" maxlength="${AiAssistantLlm.lessonLength}" aria-label="${getMessage.FTE14043}">${fn.cv( record.lesson, '', true )}</textarea>
                </div>
            </div>
        </div>`;

        dialog.open( html );

        // 内容が空の場合は適用できない（内容は必須）
        const $dialog = dialog.$.dialog;
        const updateState = () => {
            const text = ( $dialog.find('.aiLessonsText').val() ?? '').trim();
            dialog.buttonPositiveDisabled( text === '');
        };
        $dialog.on('input', '.aiLessonsText', updateState );
        updateState();
    });
}
/*
##################################################
   学習事項の有効化・無効化
##################################################
*/
// 一覧で選択した学習事項の状態をまとめて変更する（1回のPATCHで更新できる）。
// 有効な学習事項だけが、次回以降のセッションでAIへの前提知識として反映される。
// 戻り値がfalseのときは一覧を取得しなおさない。
async changeLessonsEnabled( type, lessons ) {
    if ( this.lessonBusy || fn.typeof( lessons ) !== 'array' || !lessons.length ) return false;

    const enabled = ( type === 'lessonEnable'),
          title = ( enabled )? getMessage.FTE14050: getMessage.FTE14051;

    // すでにその状態のものは変更する必要がない
    const items = lessons
        .filter(( lesson ) => lesson?.lesson_id && lesson.enabled !== enabled )
        .map(( lesson ) => ({ lessonId: lesson.lesson_id, enabled: enabled }));
    if ( !items.length ) {
        await fn.alert( title, getMessage.FTE14060 );
        return false;
    }

    const processing = fn.processingModal( title );
    let error = null;
    try {
        await AiAssistantLlm.updateLessonsEnabled( items );
    } catch ( e ) {
        console.error( e );
        error = e;
    }
    processing.close();

    if ( error ) {
        await fn.alert( title, getMessage.FTE14061 + '<br>'
            + fn.escape( fn.cv( error?.message, ''), true ) );
    }
    return;
}
/*
##################################################
   学習事項の削除
##################################################
*/
// 一覧で選択した学習事項を削除する。まとめて削除するAPIは無いため、確認をとってから
// 1件ずつ削除し、削除できなかったものがあればまとめて知らせる。
// 戻り値がfalseのときは一覧を取得しなおさない（確認をキャンセルした場合）。
async deleteLessons( lessons ) {
    const aa = this;
    if ( aa.lessonBusy || fn.typeof( lessons ) !== 'array' || !lessons.length ) return false;

    const title = getMessage.FTE14062;

    const check = await fn.iconConfirm('circle_exclamation', title,
        getMessage.FTE14063( lessons.length ) );
    if ( !check ) return false;

    const processing = fn.processingModal( title );

    const errors = [];
    for ( const lesson of lessons ) {
        const lessonId = lesson?.lesson_id;
        if ( !lessonId ) continue;
        try {
            await AiAssistantLlm.deleteLesson( lessonId );
        } catch ( error ) {
            console.error( error );
            errors.push(`${aa.lessonLabel( lesson )}：${fn.cv( error?.message, '')}`);
        }
    }

    processing.close();

    if ( errors.length ) {
        await fn.alert( title, getMessage.FTE14064( errors.length ) + '<br>'
            + fn.escape( errors.join('\n'), true ) );
    }
    return;
}
/*
##################################################
   学習事項のインポート・エクスポート
##################################################
*/
// 一覧で選択した学習事項をJSONファイルへ書き出す（AiAssistantTransfer）。
// 一覧の内容は変わらないため、常にfalseを返して取得しなおしを省く。
async exportLessons( lessons ) {
    const aa = this;
    if ( aa.lessonBusy ) return false;

    aa.lessonBusy = true;
    try {
        return await AiAssistantTransfer.exportLessons( lessons );
    } finally {
        aa.lessonBusy = false;
    }
}
// 選択したJSONファイルに含まれている学習事項を、新しい学習事項として登録する（AiAssistantTransfer）。
// 戻り値がfalseのときは一覧を取得しなおさない（キャンセルした場合・1件も登録しなかった場合）。
async importLessons() {
    const aa = this;
    if ( aa.lessonBusy ) return false;

    aa.lessonBusy = true;
    try {
        // インポートした学習事項が、この一覧（同じプロンプトプロファイル）に並ぶようにする
        return await AiAssistantTransfer.importLessons({ promptProfile: aa.promptProfile });
    } finally {
        aa.lessonBusy = false;
    }
}
// エラーメッセージで、どの学習事項か分かるようにする目印（内容の先頭のみ）
lessonLabel( lesson ) {
    const text = fn.cv( lesson?.lesson, '').split('\n')[0];
    if ( !text ) return fn.cv( lesson?.lesson_id, '');
    return ( text.length > 40 )? text.slice( 0, 40 ) + '…': text;
}

}