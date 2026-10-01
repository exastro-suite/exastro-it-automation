////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Exastro IT Automation / ai_assistant_llm.js
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

// AIアシスタントのLLM層。
// チャット画面（AiAssistantChat）とプラットフォームAPIの会話（conversations）の間を受け持つ。
//
// ・認証情報（Credential）はプラットフォーム側に保存されており、ブラウザからは取得できないため、
//   LLMの呼び出しもプラットフォームAPI（/conversations/{id}/completions）を経由して行う。
// ・システムプロンプトとツール定義はプラットフォーム側が保持する（会話作成時に渡したtoolsと
//   prompt_profileが使われる）。
// ・会話履歴（メッセージのターン配列）は画面側（this.messages）を正とする。サーバー側にも履歴の
//   スナップショット（＝会話履歴の保存先そのもの）が保存されており、completionsはその保存内容を
//   使って問い合わせる。ITA側（会話履歴メニュー）への二重保存は行わない。
// ・テキストだけのユーザー発言は completions の message で送る。プラットフォーム側がユーザーターンと
//   AI応答を履歴へ自動保存するため、送信ごとの同期（PUT /messages）は不要。
// ・添付ファイル（image / document）やツール結果（tool_result）はmessage（文字列）では送れないため、
//   PUT /messages で履歴を全置換してから、messageなし（＝サーバー側は保存しない）で問い合わせる。
// ・saveHistory() の全置換は履歴全体を送る通信なので、必要なときだけ行う（回数を抑える）。
//     ・サーバー側とずれているとき（serverSynced=false。巻き戻し・履歴復元・保存されない問い合わせの後）
//     ・時間のかかるツールの実行中（中断耐性。すぐ返るツールでは、続く継続送信の全置換に任せる）
//     ・スナップショットが積み上がったとき（needsCompaction。1件へ圧縮して復元時の取得を軽くする）
//   全置換では、画面表示用の情報（_displayText / _attachments 等）を含む正の履歴が保存される。
//   なお添付ファイルの実体（base64）は保存しない（復元は _attachments のメタ情報から行う）。
// ・サーバー側の履歴が画面側とずれているかは this.serverSynced で管理する。
// ・会話（プラットフォーム側のレコード）は最初の送信・保存のときに作成する（title は最初の発言から作る）。
//   画面を開いただけで空の会話が残らないようにするため、setup() では作成しない。
class AiAssistantLlm {
/*
##################################################
   REST API URL
##################################################
*/
static get apiUrl() {
    const { organizationId, workspaceId } = fn.getCommonParams();
    const workspace = `/api/${organizationId}/platform/workspaces/${workspaceId}`;
    const conversation = `${workspace}/conversations`;
    const lesson = `${workspace}/lessons`;
    return {
        // 会話: 作成 POST / 一覧 GET
        conversation: () => conversation,
        // 会話（レコード）: 部分更新 PATCH（タイトル・ステータス）/ 削除 DELETE（紐づくメッセージもまとめて削除される）
        conversationRecord: ( conversationId ) => `${conversation}/${conversationId}`,
        // 会話メッセージ: 取得 GET / 作成 POST / 全置換 PUT / 全削除 DELETE
        messages: ( conversationId ) => `${conversation}/${conversationId}/messages`,
        // AI応答の生成: POST
        completion: ( conversationId ) => `${conversation}/${conversationId}/completions`,
        // 学習事項: 登録 POST / 一覧 GET / 有効・無効の一括更新 PATCH
        lesson: () => lesson,
        // 学習事項（レコード）: 取得 GET / 部分更新 PATCH / 削除 DELETE
        lessonRecord: ( lessonId ) => `${lesson}/${lessonId}`
    };
}
/*
##################################################
   定数
##################################################
*/
// システムプロンプトの切り替え（プラットフォーム側で読み込むプロンプトの種別）
// AIアシスタントメニューから始めた会話で使う既定のプロファイル。
static get promptProfile() {
    return 'AgenticAI';
}
// ファイル編集画面（fn.fileEditor）から呼び出したAIアシスタントの会話で使うプロファイル。
// 編集中のファイルの作成・修正を助けることが目的のため、ITAの操作を主とするAgenticAIとは
// 別のシステムプロンプト（プラットフォーム側の llmeditor_base.md）を読み込ませる。
// 会話一覧（会話履歴タブ）もプロファイルで絞り込まれるため、メニュー側の会話とは混ざらない。
static get editorPromptProfile() {
    return 'LLMEditor';
}
// 学習事項の抽出に使う会話のプロンプトプロファイル。
// プラットフォーム側の lessons_base.md（学習事項をJSON配列で出力させるプロンプト）が読み込まれる。
static get lessonsPromptProfile() {
    return 'Lessons';
}
// 会話のタイトルの生成に使う会話のプロンプトプロファイル。
// プラットフォーム側の generatetitle_base.md（会話の主題を短いタイトル1つで出力させるプロンプト）が
// 読み込まれる。
static get titlePromptProfile() {
    return 'GenerateTitle';
}
// 学習事項の重要度（priority）の範囲と既定値。
// プラットフォーム側のバリデーション（LESSON_PRIORITY_MIN / MAX）と POST /lessons の既定値に合わせる。
static get lessonPriorityMin() {
    return 1;
}
static get lessonPriorityMax() {
    return 10;
}
static get lessonPriorityDefault() {
    return 5;
}
// 学習事項の内容・分類の最大文字数（プラットフォーム側のバリデーションに合わせる）
static get lessonLength() {
    return 4000;
}
static get lessonCategoryLength() {
    return 255;
}
// 学習事項の一覧を1回のGETで取得する件数（学習事項タブの一覧と、登録時の既存分の照合に使う）
static get lessonsFetchLimit() {
    return 200;
}
// 画面で扱う学習事項の上限件数（この件数までの登録を案内する）。
// 一覧はページングを行わず1回のGET（lessonsFetchLimit）で全件を表示するため、
// 取得できる件数に余裕を持たせた件数にしている。
static get lessonsMaxCount() {
    return 100;
}
// 1回の問い合わせでAIへ渡される学習事項の件数。有効な学習事項のうち、重要度（priority）と
// 最終更新日時の降順でこの件数までがシステムプロンプトへ差し込まれる。
// プラットフォーム側の既定値（AI_ASSISTANT_LESSONS_MAX_ITEMS）に合わせているため、
// 環境変数でその件数を変えた場合は、ここも合わせる必要がある（案内の文言にのみ使う）。
static get lessonsPromptMaxCount() {
    return 20;
}
// 会話タイトル（最初の発言からタイトルを作れなかった場合の既定値）
static get defaultTitle() {
    return getMessage.FTE14110;
}
// 会話タイトルの最大文字数（プラットフォーム側の TITLE カラムに合わせる）
static get titleLength() {
    return 256;
}
// AIに生成させた会話タイトルの最大文字数。
// プラットフォーム側のプロンプトは30文字以内を指示しているが、多少超えた応答を捨てずに
// 使えるよう余裕を持たせた上限（超えた分は切り詰める）。
static get generatedTitleLength() {
    return 60;
}
// 会話履歴（スナップショット）の取得件数。1回のGETで取得するレコード数。
//   保存（saveHistory）のたびに全置換され1件へ圧縮されるため、通常は1〜数件しか無い。
static get messagesFetchLimit() {
    return 100;
}
// 保存済みスナップショットの圧縮（全置換）を行うレコード数のしきい値。
// messageを指定した問い合わせは、プラットフォーム側が問い合わせごとに会話全体のスナップショットを
// 1レコード追加する。放置すると保存済みレコードが増えて復元時の取得（ページング）が重くなるため、
// この数を超えたら全置換して1レコードへ圧縮する。
static get snapshotCompactionThreshold() {
    return 10;
}
// 再送するHTTPステータス（一過性のエラーのみ。タイムアウトはユーザー確認のうえで再送する）
static get retryStatuses() {
    return [ 425, 429, 500, 502, 503 ];
}
// タイムアウトのHTTPステータス（待たされた末の再試行になるため、再送前にユーザーへ確認する）
static get timeoutStatuses() {
    return [ 408, 504 ];
}
/*
##################################################
   Constructor
##################################################
*/
// promptProfile … 作成する会話のプロンプトプロファイル（省略時はAIアシスタントメニューのもの）。
//   APIを叩くためだけの一時インスタンス（fetchHistoryなど）では会話を作らないため指定は不要。
constructor( promptProfile ) {
    // 会話（プラットフォーム側のレコード）を作るときに渡すプロンプトプロファイル
    this.promptProfile = promptProfile ?? AiAssistantLlm.promptProfile;
    // 会話ID（最初の送信・保存のときに作成する。履歴復元時は復元元の会話IDを引き継ぐ）
    this.conversationId = null;
    // 会話履歴（Anthropic Messages API形式のターン配列）
    //   画面の表示・巻き戻し・サーバーへの履歴保存もこの配列を使う
    this.messages = [];
    // サーバー側に保存されている履歴が this.messages と一致しているか
    //   false のとき（巻き戻し・履歴復元・保存されない問い合わせの後など）は、
    //   次の問い合わせの前に PUT /messages で保存しなおす
    this.serverSynced = true;
    // 全置換（PUT /messages）以降にプラットフォーム側が追加したスナップショットのレコード数。
    //   messageを指定した問い合わせが成功するたびに1件増える。全置換で1レコードへ圧縮すると0に戻る。
    this.snapshotCount = 0;
    // 使用するAIサービス
    this.aiServiceId = '';
    // 使用するモデル（フッターで切り替えられる）
    this.modelId = '';
    // ツール定義（Anthropic tools形式）
    this.tools = [];
    // メニュー情報
    this.menu = fn.getParams().menu ?? '';
    // サーバー側の履歴を書き換える処理（全置換・completions）を直列化するためのキュー。
    // 保存（履歴の全置換）は応答ループから待たずに投げられるため、問い合わせと同時に走ると
    // サーバー側の履歴が壊れる（＝二重保存や、保存済み判定のずれ）。
    this.writeChain = Promise.resolve();
}
/*
##################################################
   Setup（AIサービス・モデル・ツールの設定）
##################################################
*/
// param = { aiServiceId, modelId }
// tools … MCPサーバーから取得したツール一覧（Anthropic tools形式へ変換して会話に登録する）
//
// 会話（プラットフォーム側のレコード）はここでは作らない。画面を開くたびに空の会話が
// 会話履歴に残るのを避けるため、最初の送信・保存のときに ensureConversation() で作成する。
async setup( param = {}, tools ) {
    this.aiServiceId = param.aiServiceId ?? '';
    this.modelId = param.modelId ?? '';
    this.tools = AiAssistantLlm.convertTools( tools );
    // 新しい会話なので、履歴と会話IDは初期化する（サーバー側も履歴が無いので同期済み）
    this.messages = [];
    this.conversationId = null;
    this.serverSynced = true;
    this.snapshotCount = 0;

    if ( !this.aiServiceId ) throw new Error( getMessage.FTE14111 );
    if ( !this.modelId ) throw new Error( getMessage.FTE14112 );
}
/*
##################################################
   会話（プラットフォーム側のレコード）
##################################################
*/
// 会話が未作成なら作成する。タイトルは最初の発言から作って登録する
// （作成後のタイトルは会話履歴タブから編集できる）。
async ensureConversation() {
    if ( this.conversationId ) return this.conversationId;

    if ( !this.aiServiceId ) throw new Error( getMessage.FTE14111 );
    if ( !this.modelId ) throw new Error( getMessage.FTE14112 );

    const data = await this.request(AiAssistantLlm.apiUrl.conversation(), 'POST', {
        title: AiAssistantLlm.buildTitle( this.messages ),
        model_id: this.modelId,
        ai_service_id: this.aiServiceId,
        prompt_profile: this.promptProfile,
        // ツール定義は会話単位で固定される（completionsの都度は指定しない）
        tools: this.tools
    });

    this.conversationId = data.conversation_id ?? null;
    if ( !this.conversationId ) throw new Error( getMessage.FTE14113 );

    return this.conversationId;
}
// 保存済みの会話を引き継ぐ（履歴復元）。復元元の会話へ続きを保存するため、新しい会話は作らない。
attachConversation( conversationId, history ) {
    if ( !conversationId ) throw new Error( getMessage.FTE14114 );
    this.conversationId = conversationId;
    this.setChatHistory( history );
}
// 会話のタイトルを作る。会話の作成時（POST /conversations）に渡す初期のタイトルで、
// 履歴内のユーザー発言のテキストを上限文字数まで結合し、タブと改行は取り除く。
static buildTitle( messages ) {
    let title = '';
    if ( Array.isArray( messages ) ) {
        for ( const turn of messages ) {
            if ( !turn || turn.role !== 'user' || !Array.isArray( turn.content ) ) continue;
            // 画面表示用の文言（システム操作など）があればそちらを優先する
            if ( typeof turn._displayText === 'string' && turn._displayText !== '') {
                title += turn._displayText;
            } else {
                for ( const block of turn.content ) {
                    if ( !block || block.type !== 'text' || typeof block.text !== 'string') continue;
                    title += block.text;
                    if ( title.length >= AiAssistantLlm.titleLength ) break;
                }
            }
            if ( title.length >= AiAssistantLlm.titleLength ) break;
        }
    }
    title = title.replace( /[\t\r\n]/g, '').slice( 0, AiAssistantLlm.titleLength );
    return ( title !== '')? title: AiAssistantLlm.defaultTitle;
}
/*
##################################################
   保存済みの会話履歴の取得（履歴復元用）
##################################################
*/
// 会話履歴（最新のスナップショット）を取得する。会話の作成前でも呼べるよう、
// APIを叩くためだけの一時インスタンスを使う。
static async fetchHistory( conversationId ) {
    if ( !conversationId ) throw new Error( getMessage.FTE14114 );
    const llm = new AiAssistantLlm();
    const limit = AiAssistantLlm.messagesFetchLimit;
    const endPoint = AiAssistantLlm.apiUrl.messages( conversationId );

    // 履歴はスナップショット（会話全体を丸ごと持つレコード）の列で、最後のレコードが最新。
    // 取得は message_seq の昇順・ページングのため、取得件数が上限に達している間は続きを読む。
    let history = [];
    for ( let offset = 0; ; offset += limit ) {
        const data = await llm.request(`${endPoint}?limit=${limit}&offset=${offset}`, 'GET');
        const messages = ( Array.isArray( data?.messages ) )? data.messages: [];
        if ( !messages.length ) break;
        const contents = messages[ messages.length - 1 ]?.contents;
        if ( Array.isArray( contents ) ) history = contents;
        if ( messages.length < limit ) break;
    }
    return history;
}
/*
##################################################
   会話のインポート（履歴を持つ会話の作成）
##################################################
*/
// 会話履歴（ターンの配列）から、その履歴を持つ会話を新しく作る（会話履歴タブのインポート）。
// 会話を作成（POST /conversations）し、その会話の履歴として全置換（PUT /messages）する。
//   ・レコードは新しく作られるため、登録日時・更新日時はインポートした日時になる
//     （元の日時を引き継ぐ手段はプラットフォームAPIに無い）
//   ・一覧の発言数は最新のスナップショットのターン数から求められるため、保存した履歴から決まる
//   ・一覧のトークン数は問い合わせのたびに積算される値のため、インポートした会話では0のまま。
//     0トークンと数えられたわけではないので、一覧では不明（ハイフン）として表示される
//     （→ DataTablePF.conversationColumns）
// param = { title, aiServiceId, modelId, tools, history, promptProfile }
//   tools … 会話に登録するツール定義（会話単位で固定されるため、インポート後に再開して
//           続きを話せるように、その時点のツール一覧を渡す）
//   promptProfile … 作成する会話のプロンプトプロファイル（省略時はAIアシスタントメニューのもの）。
//           一覧はプロファイルで絞り込まれるため、インポートした会話が同じ一覧に並ぶよう
//           呼び出し元の一覧のプロファイルを渡す
// 戻り値: 作成した会話のID
static async importConversation( param = {}) {
    const title = String( param.title ?? '').trim();
    if ( !title ) throw new Error( getMessage.FTE14115 );

    const aiServiceId = param.aiServiceId ?? '';
    const modelId = param.modelId ?? '';
    if ( !aiServiceId ) throw new Error( getMessage.FTE14111 );
    if ( !modelId ) throw new Error( getMessage.FTE14112 );

    const llm = new AiAssistantLlm( param.promptProfile );
    llm.aiServiceId = aiServiceId;
    llm.modelId = modelId;
    llm.tools = AiAssistantLlm.convertTools( param.tools );
    // 添付ファイルの実体は保存しない（通常の保存と同じ扱いにする）
    llm.messages = AiAssistantLlm.storableHistory(
        ( Array.isArray( param.history ) )? param.history: []);

    const data = await llm.request(AiAssistantLlm.apiUrl.conversation(), 'POST', {
        title: title.slice( 0, AiAssistantLlm.titleLength ),
        model_id: modelId,
        ai_service_id: aiServiceId,
        prompt_profile: llm.promptProfile,
        tools: llm.tools
    });
    llm.conversationId = data.conversation_id ?? null;
    if ( !llm.conversationId ) throw new Error( getMessage.FTE14113 );

    // 履歴の保存に失敗した場合は、履歴の無い会話が残ってしまうため後片付けする
    // （後片付けにも失敗した場合は、作成された会話が一覧に残る）
    try {
        await llm.syncHistory( undefined, llm.messages );
    } catch ( error ) {
        try {
            await AiAssistantLlm.deleteConversation( llm.conversationId );
        } catch ( deleteError ) {
            console.error( deleteError );
        }
        throw error;
    }

    return llm.conversationId;
}
/*
##################################################
   会話のタイトルの更新
##################################################
*/
// 会話のタイトルを付け替える（PATCH /conversations/{conversation_id}）。
// タイトルは一覧での目印にのみ使われるため、変更しても保存されている履歴・AIの記憶は変わらない。
// 空のタイトルはプラットフォーム側でバリデーションエラーになるため、ここで先に弾く。
static async updateConversationTitle( conversationId, title ) {
    if ( !conversationId ) throw new Error( getMessage.FTE14114 );

    const text = String( title ?? '').trim();
    if ( !text ) throw new Error( getMessage.FTE14115 );

    const llm = new AiAssistantLlm();
    return await llm.request(AiAssistantLlm.apiUrl.conversationRecord( conversationId ), 'PATCH', {
        title: text.slice( 0, AiAssistantLlm.titleLength )
    });
}
/*
##################################################
   会話のタイトルの生成（AIに付けてもらう）
##################################################
*/
// 会話の内容からタイトルをAIに考えてもらう。
// タイトル生成用の会話（prompt_profile = GenerateTitle）を1つ作り、そのシステムプロンプトの
// もとで1回だけ問い合わせる（学習事項の抽出と同じつくり）。
// 生成したタイトルの保存（PATCH /conversations/{conversation_id}）は行わないため、
// 呼び出し側で updateConversationTitle() を使って保存する。
// 戻り値 { conversationId, title } … conversationId は、生成に使った会話のID。
//   生成用の会話は使い捨てのため、生成できたかどうかに関わらず呼び出し側で削除すること。
//   title は応答からタイトルを取り出せなかった場合は空文字。
// 生成そのものの失敗（会話の作成・問い合わせの失敗）は例外を投げる。
static async generateTitle( transcript, param = {}, signal ) {
    const aiServiceId = param.aiServiceId ?? '';
    const modelId = param.modelId ?? '';
    if ( !aiServiceId ) throw new Error( getMessage.FTE14111 );
    if ( !modelId ) throw new Error( getMessage.FTE14112 );

    const llm = new AiAssistantLlm();
    // ツールは渡さない（ツール呼び出しを抑止し、純粋なテキスト応答だけを得る）
    const data = await llm.request(AiAssistantLlm.apiUrl.conversation(), 'POST', {
        title: AiAssistantLlm.disposableTitle( getMessage.FTE14116 ),
        model_id: modelId,
        ai_service_id: aiServiceId,
        prompt_profile: AiAssistantLlm.titlePromptProfile
    });
    const conversationId = data.conversation_id ?? null;
    if ( !conversationId ) throw new Error( getMessage.FTE14117 );

    // 出力形式（タイトルの文字列だけを返す）の指示はプラットフォーム側のシステムプロンプトが
    // 持つため、ここでは会話内容を渡すだけでよい。
    let response;
    try {
        response = await llm.request(AiAssistantLlm.apiUrl.completion( conversationId ), 'POST', {
            model_id: modelId,
            message: getMessage.FTE14118( transcript )
        }, signal );
    } catch ( error ) {
        // 失敗しても、作成済みの会話には問い合わせ内容が保存されていることがある。
        // 使い捨ての会話を会話一覧に残さないよう、後片付けできる会話IDをエラーへ載せて返す。
        error.conversationId = conversationId;
        throw error;
    }

    return {
        conversationId: conversationId,
        title: AiAssistantLlm.parseTitle(
            AiAssistantLlm.blocksText( llm.responseContents( response ) ) )
    };
}
// LLMの応答テキストから会話のタイトルを取り出す。
// システムプロンプトはタイトルの文字列だけを返すよう指示しているが、前置きや「タイトル：」などの
// 接頭辞・引用符が付くことがあるため、最初の1行を取り出してそれらを取り除く。
// タイトルとして使える文字列が無ければ空文字を返す（会話終了処理を止めないため例外にしない）。
static parseTitle( text ) {
    if ( typeof text !== 'string') return '';
    // 前置きの空行を飛ばし、最初の中身のある行だけをタイトルとして扱う
    const line = text.split('\n').map(( row ) => row.trim() ).find(( row ) => row !== '') ?? '';
    return line
        .replace( /^(?:タイトル|title)\s*[:：]\s*/i, '')
        .replace( /^[「『【“”"'`]+/, '')
        .replace( /[」』】“”"'`]+$/, '')
        .trim()
        .slice( 0, AiAssistantLlm.generatedTitleLength );
}
/*
##################################################
   会話（レコード）の削除
##################################################
*/
// 会話のレコードを削除する（DELETE /conversations/{conversation_id}）。
// 会話に紐づくメッセージ（履歴のスナップショット）もまとめて削除されるため、
// 削除した会話は一覧から消え、再開・履歴の確認もできなくなる。
static async deleteConversation( conversationId ) {
    if ( !conversationId ) throw new Error( getMessage.FTE14114 );
    const llm = new AiAssistantLlm();
    return await llm.request(AiAssistantLlm.apiUrl.conversationRecord( conversationId ), 'DELETE');
}
/*
##################################################
   学習事項（専用API /lessons）
##################################################
*/
// 学習事項（次回セッションへの申し送り）は、プラットフォーム側の専用API（/lessons）へ
// ユーザー・ワークスペース・プロンプトプロファイル単位に保存される。
//
// ・学習事項はプロンプトプロファイル（AgenticAI / LLMEditor）ごとに分かれる。登録時の prompt_profile の
//   会話にだけ反映され、一覧（GET /lessons）もプロファイルで絞り込まれる（指定は必須）。
// ・有効（enabled = true）な学習事項は、プラットフォーム側が問い合わせのたびに
//   システムプロンプトへ自動的に追記する。そのため画面側からLLMへ渡す必要は無く、
//   前提知識としての読み出しも行わない（登録するだけで次回以降の会話に反映される）。
// ・重要度（priority）は 1（最低）〜 10（最高）の整数。システムプロンプトへ載せる順序と、
//   件数・文字数の上限を超えた分の取捨選択に使われる。
// ・抽出（LLMへの問い合わせ）だけは会話を使う。prompt_profile が Lessons の会話を1つ作って
//   問い合わせ、抽出が済んだらその会話はレコードごと削除する（保存先ではないため残さない）。

// 今回の会話内容から学習事項を抽出する。
// 抽出用の会話を作り、Lessons用のシステムプロンプトのもとで1回だけ問い合わせる。
// 戻り値 { conversationId, lessons } … conversationId は、抽出に使った会話のID。
//   抽出用の会話は使い捨てのため、抽出できたかどうかに関わらず呼び出し側で削除すること。
// 抽出そのものの失敗（会話の作成・問い合わせの失敗）は例外を投げる。
static async extractLessons( transcript, param = {}, signal ) {
    const aiServiceId = param.aiServiceId ?? '';
    const modelId = param.modelId ?? '';
    if ( !aiServiceId ) throw new Error( getMessage.FTE14111 );
    if ( !modelId ) throw new Error( getMessage.FTE14112 );

    const llm = new AiAssistantLlm();
    // ツールは渡さない（ツール呼び出しを抑止し、純粋なテキスト応答だけを得る）
    const data = await llm.request(AiAssistantLlm.apiUrl.conversation(), 'POST', {
        title: AiAssistantLlm.disposableTitle( getMessage.FTE14119 ),
        model_id: modelId,
        ai_service_id: aiServiceId,
        prompt_profile: AiAssistantLlm.lessonsPromptProfile
    });
    const conversationId = data.conversation_id ?? null;
    if ( !conversationId ) throw new Error( getMessage.FTE14120 );

    // 出力形式（JSON配列）の指示はプラットフォーム側のシステムプロンプトが持つため、
    // ここでは会話内容を渡すだけでよい。
    let response;
    try {
        response = await llm.request(AiAssistantLlm.apiUrl.completion( conversationId ), 'POST', {
            model_id: modelId,
            message: getMessage.FTE14121( transcript )
        }, signal );
    } catch ( error ) {
        // 失敗しても、作成済みの会話には問い合わせ内容が保存されていることがある。
        // 使い捨ての会話を会話一覧に残さないよう、後片付けできる会話IDをエラーへ載せて返す。
        error.conversationId = conversationId;
        throw error;
    }

    return {
        conversationId: conversationId,
        lessons: AiAssistantLlm.parseLessons(
            AiAssistantLlm.blocksText( llm.responseContents( response ) ) )
    };
}
// 学習事項を1件登録する（POST /lessons）。
// record = { lesson, category, priority, enabled, conversationId, promptProfile }
//   category … 分類（空の場合は分類なしとして登録する）
//   priority … 重要度（1〜10。範囲外や数値以外は lessonPriority() が読み替える）
//   enabled … 有効・無効（省略時は有効。無効にすると次回以降の会話へ反映されない）
//   conversationId … 学習元の会話ID（任意。どの会話から得た学習事項かを残す）
//   promptProfile … 反映先のプロンプトプロファイル（省略時はAIアシスタントメニューのもの）
// 戻り値: 登録された学習事項（lesson_id を含む）
static async createLesson( record ) {
    const lesson = String( record?.lesson ?? '').trim();
    if ( !lesson ) throw new Error( getMessage.FTE14122 );

    const llm = new AiAssistantLlm();
    return await llm.request(AiAssistantLlm.apiUrl.lesson(), 'POST', {
        lesson: lesson,
        category: ( record?.category )? record.category: null,
        prompt_profile: record?.promptProfile ?? AiAssistantLlm.promptProfile,
        priority: AiAssistantLlm.lessonPriority( record?.priority ),
        // 登録した学習事項は、次回以降の会話へすぐ反映させる（指定された場合はその状態で登録する）
        enabled: ( typeof record?.enabled === 'boolean')? record.enabled: true,
        conversation_id: ( record?.conversationId )? record.conversationId: null
    });
}
// 登録済みの学習事項を取得する（GET /lessons）。
// param = { promptProfile, enabled, category, limit, offset }
//   promptProfile … 取得するプロンプトプロファイル（省略時はAIアシスタントメニューのもの）
//   それ以外は任意。enabled・categoryは省略時は絞り込みなし
// 戻り値 { lessons, count, totalCount } … lessons は重要度の高い順・更新日時の新しい順。
static async fetchLessons( param = {} ) {
    const query = [];
    query.push(`prompt_profile=${encodeURIComponent( param.promptProfile ?? AiAssistantLlm.promptProfile )}`);
    if ( typeof param.enabled === 'boolean') query.push(`enabled=${param.enabled}`);
    if ( param.category ) query.push(`category=${encodeURIComponent( param.category )}`);
    query.push(`limit=${param.limit ?? AiAssistantLlm.lessonsFetchLimit}`);
    query.push(`offset=${param.offset ?? 0}`);

    const llm = new AiAssistantLlm();
    const data = await llm.request(`${AiAssistantLlm.apiUrl.lesson()}?${query.join('&')}`, 'GET');
    return {
        lessons: ( Array.isArray( data?.lessons ) )? data.lessons: [],
        count: data?.count ?? 0,
        totalCount: data?.total_count ?? 0
    };
}
// 学習事項を部分更新する（PATCH /lessons/{lesson_id}）。
// param = { lesson, category, priority, enabled }。指定した項目だけが更新される。
//   分類（category）は空文字を渡すと分類なしになる（プラットフォーム側の更新はCOALESCEのため、
//   nullを渡した場合は「未指定」として現在の分類が残る）。
static async updateLesson( lessonId, param = {} ) {
    if ( !lessonId ) throw new Error( getMessage.FTE14123 );

    const body = {};
    if ( typeof param.lesson === 'string' && param.lesson !== '') body.lesson = param.lesson;
    if ( typeof param.category === 'string') body.category = param.category;
    if ( param.priority !== undefined ) body.priority = AiAssistantLlm.lessonPriority( param.priority );
    if ( typeof param.enabled === 'boolean') body.enabled = param.enabled;

    const llm = new AiAssistantLlm();
    return await llm.request(AiAssistantLlm.apiUrl.lessonRecord( lessonId ), 'PATCH', body );
}
// 複数の学習事項の有効・無効をまとめて更新する（PATCH /lessons）。
// items = [{ lessonId, enabled }, …]（要素ごとに異なる有効・無効を指定できる）
//   存在しないID・他ユーザーのIDが含まれてもエラーにはならず、更新された件数に含まれないだけ。
// 戻り値: 更新された件数
static async updateLessonsEnabled( items ) {
    const lessons = (( Array.isArray( items ) )? items: [])
        .filter(( item ) => item?.lessonId && typeof item.enabled === 'boolean')
        .map(( item ) => ({ lesson_id: item.lessonId, enabled: item.enabled }));
    if ( !lessons.length ) throw new Error( getMessage.FTE14124 );

    const llm = new AiAssistantLlm();
    const data = await llm.request(AiAssistantLlm.apiUrl.lesson(), 'PATCH', { lessons: lessons });
    return data?.updated_count ?? 0;
}
// 学習事項を1件削除する（DELETE /lessons/{lesson_id}）。
// まとめて削除するAPIは無いため、複数を削除する場合は呼び出し側で1件ずつ繰り返す。
static async deleteLesson( lessonId ) {
    if ( !lessonId ) throw new Error( getMessage.FTE14123 );

    const llm = new AiAssistantLlm();
    return await llm.request(AiAssistantLlm.apiUrl.lessonRecord( lessonId ), 'DELETE');
}
// 重要度（priority）を、プラットフォーム側が受け付ける整数（1〜10）へ整える。
// LLMの抽出結果には数値以外（3段階の「高・中・低」やhigh/low等）が混ざることがあるため、
// それらは10段階の値へ読み替える。判別できない場合は既定値（5）。
static lessonPriority( value ) {
    const number = ( typeof value === 'number')? value: parseInt( value, 10 );
    if ( Number.isFinite( number ) ) {
        return Math.min( AiAssistantLlm.lessonPriorityMax,
            Math.max( AiAssistantLlm.lessonPriorityMin, Math.round( number ) ) );
    }
    const rank = new Map([
        [ '高', 9 ], [ 'high', 9 ],
        [ '中', 5 ], [ 'medium', 5 ],
        [ '低', 2 ], [ 'low', 2 ]
    ]);
    const text = ( typeof value === 'string')? value.trim().toLowerCase(): '';
    return rank.get( text ) ?? AiAssistantLlm.lessonPriorityDefault;
}
// 重要度の選択肢（1〜10）のHTMLを返す。最大値と最小値には、どちらの向きが重要かを添える。
static lessonPriorityOptions( selected ) {
    const value = AiAssistantLlm.lessonPriority( selected );
    const html = [];
    for ( let i = AiAssistantLlm.lessonPriorityMax; i >= AiAssistantLlm.lessonPriorityMin; i-- ) {
        let label = String( i );
        if ( i === AiAssistantLlm.lessonPriorityMax ) label = getMessage.FTE14058( i );
        if ( i === AiAssistantLlm.lessonPriorityMin ) label = getMessage.FTE14059( i );
        html.push(`<option value="${i}"${( i === value )? ' selected': ''}>${label}</option>`);
    }
    return html.join('');
}
// 使い捨ての会話（学習事項の抽出・タイトルの生成）のタイトル。
// 用途と作成日時を入れて、後片付けできず会話一覧に残った場合の目印にする。
static disposableTitle( label ) {
    const now = new Date();
    const pad = ( value ) => String( value ).padStart( 2, '0');
    return `${label} ${now.getFullYear()}/${pad( now.getMonth() + 1 )}/${pad( now.getDate() )}`
        + ` ${pad( now.getHours() )}:${pad( now.getMinutes() )}:${pad( now.getSeconds() )}`;
}
// LLMの応答テキストから学習事項のJSON配列を取り出す。
// 説明文やコードフェンス（```）が付いても壊れないよう、配列部分だけを切り出して解析する。
// 解析できない場合は空配列を返す（会話終了処理を止めないため例外にしない）。
static parseLessons( text ) {
    if ( typeof text !== 'string' || text === '') return [];
    let jsonText = text;
    const start = jsonText.indexOf('[');
    const end = jsonText.lastIndexOf(']');
    if ( start !== -1 && end > start ) jsonText = jsonText.slice( start, end + 1 );
    try {
        const parsed = JSON.parse( jsonText );
        return ( Array.isArray( parsed ) )? parsed: [];
    } catch ( error ) {
        console.warn('学習事項JSONの解析に失敗しました。空配列として扱います。', error, text );
        return [];
    }
}
// contentブロックの配列からテキストだけを取り出して連結する
static blocksText( blocks ) {
    if ( !Array.isArray( blocks ) ) return '';
    return blocks
        .filter(( block ) => block?.type === 'text' && typeof block.text === 'string')
        .map(( block ) => block.text )
        .join('')
        .trim();
}
// MCPのツール定義（inputSchema）をAnthropic tools形式（input_schema）へ変換する
static convertTools( tools ) {
    if ( !Array.isArray( tools ) ) return [];
    return tools.map(( tool ) => {
        const { inputSchema, ...rest } = tool;
        if ( inputSchema !== undefined && rest.input_schema === undefined ) {
            rest.input_schema = inputSchema;
        }
        return rest;
    });
}
/*
##################################################
   使用するモデルの切り替え
##################################################
*/
// 会話のデフォルトモデルは会話作成時に決まるが、問い合わせごとに上書きできる。
setModel( modelId = '') {
    if ( modelId ) this.modelId = modelId;
}
/*
##################################################
   会話履歴
##################################################
*/
getChatHistory() {
    return this.messages;
}
// 画面側の履歴を差し替える（巻き戻し・履歴復元・ターンの巻き戻しなど）。
// サーバー側の保存内容とはずれるため、次の問い合わせの前に保存しなおす必要があるとマークする。
setChatHistory( history ) {
    this.messages = ( Array.isArray( history ) )? history: [];
    this.serverSynced = false;
}
/*
##################################################
   ツール結果を履歴へ確定（継続送信用）
##################################################
*/
// ツール実行結果（tool_result ブロック群）を user ターンとして履歴へ積む。
// 中断耐性のため、送信（send）を待たずにツール実行直後へ確定させ、その時点で保存できるようにする。
// この後のLLM呼び出しは send( null, null, signal, { alreadyPushed: true } ) で継続する。
appendToolResults( toolResults ) {
    if ( !Array.isArray( toolResults ) || !toolResults.length ) return;
    if ( !Array.isArray( this.messages ) ) this.messages = [];
    this.messages.push({
        'role': 'user',
        'content': toolResults,
        // 発言時刻（履歴保存・復元用。LLMには渡さない）
        '_timestamp': new Date().toISOString()
    });
    // サーバー側にはまだ無いターンなので、次の問い合わせの前に保存しなおす
    this.serverSynced = false;
}
/*
##################################################
   Send prompt
##################################################
*/
// prompt  … テキスト（文字列）または contentブロックの配列（tool_result等）
// files   … 送信するファイル（アップロード済みの情報。useLlm=trueのものは実体も渡す）
// signal  … 停止用のAbortSignal
// options … { displayText, systemAction, timestamp, alreadyPushed }
async send( prompt, files, signal, options = {} ) {
    // 継続送信（alreadyPushed）の場合、送るべきメッセージ（tool_result等）は呼び出し側が
    // 既に履歴へ積んでいるため、ここでは積まない。
    const alreadyPushed = options.alreadyPushed === true;
    // ユーザーターンを履歴へ積んだか（失敗時に取り消すため）
    let pushed = false;

    let data = null;
    let contents = null;
    // タイムアウトで再送したか（messageを指定した再送は、1度目が保存まで終わっていた場合に
    // サーバー側の履歴へ同じユーザーターンが二重に積まれる可能性があるため、同期済みとみなさない）
    let retried = false;
    // この問い合わせの往復時間（ミリ秒）。応答ごとに履歴へ残し、会話終了レポートの実測値に使う。
    let thinkingMs = null;
    try {
        // 履歴の全置換（保存）と問い合わせは、サーバー側の履歴を書き換える処理なので直列化する。
        data = await this.writeQueue( async () => {
            // ユーザーターンは書き込みキューの中で積む。先に積んでしまうと、待機中の保存が
            // 「まだ送信していないユーザーターン」を含む履歴を保存してしまい、その後に
            // messageを指定して問い合わせることで同じユーザーターンが二重に積まれる。
            let messageText = null;
            if ( !alreadyPushed ) {
                const userMessage = this.buildUserMessage( prompt, files, options );
                this.messages.push( userMessage );
                pushed = true;
                // completionsのmessage（文字列）で送れるユーザー発言か。テキスト1ブロックのみのターンが
                // 対象で、添付ファイルやツール結果を含むターンは送れない（→履歴を全置換して同期する）。
                messageText = AiAssistantLlm.completionMessageText( userMessage );
            }

            // 会話が未作成なら、ここで作成する（タイトルは積んだユーザー発言から作られる）
            await this.ensureConversation();

            if ( messageText !== null ) {
                // messageを指定した問い合わせは、プラットフォーム側がユーザーターンとAI応答を
                // 履歴へ自動保存する。サーバー側の履歴がずれている（巻き戻し・履歴復元後など）ときだけ、
                // 今回のユーザーターンを除いた履歴で全置換して整合させてから問い合わせる。
                if ( !this.serverSynced ) {
                    await this.syncHistory( signal, this.messages.slice( 0, -1 ) );
                }
            } else {
                // messageで送れないターン（tool_result・添付ファイル付きなど）は、
                // 問い合わせに使われるサーバー側の履歴を全置換して渡す。
                await this.syncHistory( signal );
            }

            // 問い合わせの往復時間を測る。「AIの応答を待った時間」だけを見たいので、
            // 履歴の全置換（syncHistory）や会話の作成は計測に含めない。
            // これはプラットフォームAPI経由のAIサービス呼び出しの往復時間であり、
            // ツールの実行時間は含まない。
            const requestStart = performance.now();
            try {
                const response = await this.requestCompletion( signal, messageText );
                thinkingMs = Math.round( performance.now() - requestStart );
                return response;
            } catch ( error ) {
                // タイムアウトは同じ内容の再送で解消することがあるため、ユーザーに確認して1度だけ再送する
                if ( !AiAssistantLlm.timeoutStatuses.includes( error?.status ) ) throw error;
                const proceed = window.confirm( getMessage.FTE14125( error.status ) );
                if ( !proceed ) throw new Error( getMessage.FTE14126 );
                retried = true;
                // 再送の場合は、待たされた末に失敗した1度目ではなく再送分の往復時間を記録する
                // （ユーザーの確認待ちの時間も含めない）
                const retryStart = performance.now();
                const response = await this.requestCompletion( signal, messageText );
                thinkingMs = Math.round( performance.now() - retryStart );
                return response;
            }
        });
        contents = this.responseContents( data );
    } catch ( error ) {
        // 応答を得られなかったユーザーターンは履歴に残さない
        // （未応答のまま次の送信に混ざると、会話の整合性が崩れるため）
        if ( pushed ) this.messages.pop();
        // どこまでサーバーへ渡ったか（全置換の成否・保存の有無）が分からないため、
        // 次の問い合わせの前に保存しなおす
        this.serverSynced = false;
        throw error;
    }

    // saved=true なら、今回のユーザーターンとAI応答はサーバー側の履歴へ保存済み（＝同期されている）。
    // messageなしの問い合わせは保存されない（saved=false）ため、次の問い合わせの前に保存しなおす。
    this.serverSynced = ( data.saved === true && !retried );
    // 保存された問い合わせは、サーバー側にスナップショットのレコードが1件積まれている
    // （履歴を全置換すると1レコードへ圧縮される。→ needsCompaction / syncHistory）
    if ( data.saved === true ) this.snapshotCount++;

    // 応答時刻（履歴保存・復元表示用。LLMには渡さない）。
    // 画面表示（呼び出し側）と一致させるため、返却する応答にも同じ値を載せる。
    const timestamp = new Date().toISOString();
    this.messages.push({
        'role': 'assistant',
        'content': contents,
        '_timestamp': timestamp,
        // この問い合わせの往復時間（ミリ秒。会話終了レポートの実測値に使う）
        '_thinkingMs': thinkingMs,
        // この応答を生成したモデル（会話途中でモデルを変更できるため応答ごとに記録する）
        '_model': this.modelId
    });

    return {
        content: contents,
        stop_reason: data.stop_reason ?? null,
        usage: data.usage ?? null,
        _timestamp: timestamp,
        _thinkingMs: thinkingMs,
        _model: this.modelId
    };
}
// completionsのmessageとして送れるユーザー発言なら、そのテキストを返す（送れないならnull）。
// messageはプラットフォーム側で { type: 'text', text: message } の1ブロックのユーザーターンとして
// 履歴へ保存されるため、それと同じ形のターン（テキスト1ブロックのみ・添付なし）だけを対象にする。
// ツール結果（tool_result）や添付ファイル（image / document、_attachmentsのメタ情報）を含むターンは
// messageでは表現できないので、履歴の全置換（PUT /messages）で渡す。
// 画面表示用の情報（_displayText / _displaySystem）を持つターンも、messageで送ると保存されずに
// 失われてしまうため、同様に全置換で渡す。
static completionMessageText( userMessage ) {
    if ( !userMessage || userMessage._attachments ) return null;
    if ( userMessage._displayText !== undefined || userMessage._displaySystem !== undefined ) return null;
    const content = userMessage.content;
    if ( !Array.isArray( content ) || content.length !== 1 ) return null;
    const block = content[0];
    if ( !block || block.type !== 'text' || typeof block.text !== 'string' || block.text === '') return null;
    return block.text;
}
/*
##################################################
   送信するユーザーターンの組み立て
##################################################
*/
buildUserMessage( prompt, files, options = {} ) {
    const fileList = ( Array.isArray( files ) )? files: ( files )? [ files ]: [];
    // 添付ファイルのメタ情報（履歴に保存し、復元に使う）
    const attachments = fileList.map(( file ) => {
        return {
            file_id: file.file_id ?? '',
            filename: file.filename ?? '',
            mime_type: file.mimeType || file.mime_type || '',
            size: file.size ?? '',
            use_llm: file.useLlm === true,      // ユーザーがAI解析をオンにしたか
            supported: file.supported === true  // LLMがネイティブに解析できる形式か
        };
    });

    let content = [];
    if ( typeof prompt === 'object' && prompt !== null ) {
        // ツールの実行結果（contentブロックの配列）
        content = prompt;
    } else {
        content.push({
            'type': 'text',
            'text': prompt
        });

        // useLlm=true のファイルはファイルの実体（base64）もcontentに追加する
        // Anthropic Messages API準拠：画像（image）とPDF（document）のみネイティブ添付できる
        const supportedImageTypes = [ 'image/jpeg', 'image/png', 'image/gif', 'image/webp'];
        for ( const file of fileList ) {
            // 実体（base64のdata または 生テキストのtext）が無ければスキップ
            if ( !file.useLlm || ( !file.data && typeof file.text !== 'string') ) continue;
            const mimeType = file.mimeType || file.mime_type || '';
            if ( supportedImageTypes.includes( mimeType ) ) {
                // 画像
                content.push({
                    'type': 'image',
                    'source': {
                        'type': 'base64',
                        'media_type': mimeType,
                        'data': file.data
                    }
                });
            } else if ( mimeType === 'application/pdf') {
                // PDF
                content.push({
                    'type': 'document',
                    'source': {
                        'type': 'base64',
                        'media_type': 'application/pdf',
                        'data': file.data
                    },
                    'title': file.filename ?? file.file_id ?? 'document'
                });
            } else if ( typeof file.text === 'string') {
                // テキストファイルは生テキストのドキュメントとして渡す
                content.push({
                    'type': 'document',
                    'source': {
                        'type': 'text',
                        'media_type': 'text/plain',
                        'data': file.text
                    },
                    'title': file.filename ?? file.file_id ?? 'document'
                });
            }
            // 上記以外の形式は実体を渡せない（file_idのメタ情報のみ）
        }
    }

    const userMessage = {
        'role': 'user',
        'content': content
    };
    // 添付があればメタ情報を持たせる（履歴保存・復元用。LLMへはメタ情報テキストとして渡す）
    if ( attachments.length ) {
        userMessage._attachments = attachments;
    }
    // 画面表示用の別文言があれば持たせる（履歴保存・復元用。LLMには渡さない）
    if ( typeof options.displayText === 'string' && options.displayText !== '') {
        userMessage._displayText = options.displayText;
    }
    // システム操作（会話終了など）としての表示種別を持たせる（同上）
    if ( options.systemAction === true ) {
        userMessage._displaySystem = true;
    }
    // 発言時刻（履歴保存・復元表示用）。画面表示と一致させるため、呼び出し側の時刻を優先する。
    userMessage._timestamp = ( typeof options.timestamp === 'string' && options.timestamp )
        ? options.timestamp
        : new Date().toISOString();

    return userMessage;
}
/*
##################################################
   会話履歴の保存（全置換）
##################################################
*/
// サーバー側の履歴を書き換える処理（全置換・completions・会話の作成）を直列化する。
// 保存（saveHistory）は応答ループから待たずに呼ばれるため、直列化しないと問い合わせ（send）と
// 同時に走り、「全置換 → completions」の間に別の全置換が割り込んで履歴が壊れる
// （ユーザーターンの重複など）。それを防ぐのがこのキューで、サーバー側の履歴を書き換える処理は
// すべて writeQueue() の中から呼ぶこと（＝ send と saveHistory 以外から呼ばない）。
writeQueue( task ) {
    const result = this.writeChain.then( task, task );
    // キューは後続の処理のために繋ぐだけ（エラーは呼び出し側で扱うため、ここでは伝播させない）
    this.writeChain = result.then( () => {}, () => {} );
    return result;
}
// 画面側の履歴をサーバーへ保存する（会話履歴の保存はこれだけで完結する）。
//   ・ターンの区切り（ツール実行前・応答完了時など）… 画面表示用の情報を含む正の履歴を残す
//   ・巻き戻し（会話の切り詰め）後 … 切り詰めた内容へ置き換える
// 会話が未作成で履歴も空の場合（画面を開いただけ）は、空の会話を残さないため何もしない。
async saveHistory( signal ) {
    return this.writeQueue( async () => {
        if ( !this.conversationId ) {
            if ( !this.messages.length ) return;
            await this.ensureConversation();
        }
        await this.syncHistory( signal, AiAssistantLlm.storableHistory( this.messages ) );
    });
}
// サーバー側に積み上がったスナップショットを圧縮（全置換）すべきか。
// messageを指定した問い合わせは保存を伴う（＝画面側と同期している）ため保存しなおす必要は無いが、
// 問い合わせのたびに会話全体のスナップショットが1レコード増えていく。復元時の取得を軽く保つため、
// しきい値を超えたら保存（全置換）して1レコードへまとめる。
needsCompaction() {
    return this.snapshotCount >= AiAssistantLlm.snapshotCompactionThreshold;
}
// 保存する履歴に整える。添付ファイルの実体（image / document のbase64・生テキスト）は
// 肥大化するため保存しない（復元時は _attachments のメタ情報から表示を組み立てる）。
// 実体が無い場合は渡された配列をそのまま返す（＝保存後も「同期済み」を維持する）。
static storableHistory( messages ) {
    if ( !Array.isArray( messages ) ) return [];
    const dropTypes = [ 'image', 'document'];
    const isDropBlock = ( block ) => block && dropTypes.includes( block.type );
    const hasFileBody = messages.some(( turn ) => Array.isArray( turn?.content ) && turn.content.some( isDropBlock ) );
    if ( !hasFileBody ) return messages;

    return messages.map(( turn ) => {
        if ( !Array.isArray( turn?.content ) || !turn.content.some( isDropBlock ) ) return turn;
        return { ...turn, content: turn.content.filter(( block ) => !isDropBlock( block ) ) };
    });
}
// サーバーに保存されている履歴（最新のスナップショット）を画面側の履歴で全置換する。
// completionsはサーバーの保存内容を使って問い合わせるため、画面側とずれている場合に呼ぶ。
//   ・巻き戻し（会話の切り詰め）や履歴復元でずれたとき
//   ・messageで送れないターン（tool_result・添付ファイル付き）を渡すとき
// 直列化が必要なので、writeQueue()の中から呼ぶこと（保存はsaveHistory、問い合わせはsendが行う）。
// messages … 置き換える履歴（省略時は画面側の履歴すべて）
async syncHistory( signal, messages ) {
    const history = ( Array.isArray( messages ) )? messages: this.messages;
    await this.request(AiAssistantLlm.apiUrl.messages( this.conversationId ), 'PUT', {
        // 履歴は1レコード（1スナップショット）にまとめて保存する（空の場合はレコードなし）
        messages: ( history.length )? [{ contents: this.toApiHistory( history ) }]: []
    }, signal );
    // 画面側の履歴をそのまま置き換えたときだけ「同期済み」になる
    this.serverSynced = ( history === this.messages );
    // 全置換でスナップショットは1レコードへ圧縮された（＝積み上がりは無くなった）
    this.snapshotCount = 0;
}
// 保存・問い合わせ用の履歴に整える。
// ・独自フィールド（_始まり）はそのまま渡す（プラットフォーム側でLLMへ渡す前に除去される）
// ・添付ファイルのメタ情報（_attachments）は、LLMが解析状態を判断できるようテキストブロックにする
//
// 差し込んだテキストブロックは、そのままサーバー側の履歴へ保存される（問い合わせは保存内容を
// 使うため、保存を避けられない）。そのため復元した履歴には既に入っている可能性があり、
// 二重に差し込まないよう、同じ内容があれば差し込まない（→ isInjectedBlock）。
// どのブロックを差し込んだかは、ターン直下の目印（_injectedText）に控えて一緒に保存する。
toApiHistory( messages ) {
    const history = ( Array.isArray( messages ) )? messages: this.messages;
    return history.map(( message ) => {
        const turn = { ...message };
        if ( !Array.isArray( turn.content ) ) return turn;

        // 既に差し込まれているブロックの種別を、ブロックと組にして控える
        // （並べ替えても対応が崩れないよう、位置ではなく組で持つ）
        let entries = turn.content.map(( block, index ) => {
            return { 'block': block, 'injected': AiAssistantLlm.isInjectedBlock( block, message, index ) };
        });
        // 差し込むテキストブロック（無ければ何もしない）
        const insertEntries = [];
        const injected = ( type ) => entries.some(( entry ) => entry.injected === type );
        const metaBlock = ( !injected('attachment') )
            ? AiAssistantLlm.attachmentMetaBlock( message._attachments ): null;
        if ( metaBlock ) insertEntries.push({ 'block': metaBlock, 'injected': 'attachment'});

        if ( insertEntries.length ) {
            // tool_result（選択肢への回答など）は userターンのcontent先頭に置く必要があるため、
            // 差し込むテキストは tool_result ブロックの後ろに挿入する。
            const toolResults = entries.filter(( entry ) => entry.block && entry.block.type === 'tool_result');
            const others = entries.filter(( entry ) => !entry.block || entry.block.type !== 'tool_result');
            entries = [ ...toolResults, ...insertEntries, ...others ];
            turn.content = entries.map(( entry ) => entry.block );
        }

        // 差し込んだブロックの位置と種別を目印として持たせる（→ isInjectedBlock）。
        // 並べ替えで位置が変わるため、目印はこの時点のcontentに対して毎回作り直す。
        const marks = {};
        entries.forEach(( entry, index ) => {
            if ( entry.injected ) marks[ index ] = entry.injected;
        });
        if ( Object.keys( marks ).length ) {
            turn._injectedText = marks;
        } else {
            delete turn._injectedText;
        }
        return turn;
    });
}
// 添付ファイルのメタ情報テキストの先頭
// （目印を持たない履歴で、差し込んだブロックを判別するために使う）
static get attachmentMetaPrefix() {
    return getMessage.FTE14127;
}
// contentブロックが toApiHistory で差し込まれたものかを判定する。
//   'attachment' … 添付ファイルのメタ情報   null … それ以外
// index … turn.content の中での位置（目印での判定に必要）
//
// contentブロック内に _ 始まりの目印を持たせる方法は使えない（プラットフォーム側の _ 除去は
// ターン直下のキーだけが対象で、ブロック内のキーはそのままLLMへ渡ってしまう）ため、
// ターン直下の目印（_injectedText：contentの位置 → 種別）で判定する。
// 目印を持たない履歴（この仕組みより前に保存された会話）は、ターンの独自フィールド
// （_attachments）とテキストの先頭で判定する。こちらは表示言語に依存する（＝日本語で保存した
// 会話を英語で開くと判定できない）ため、目印がある場合は使わない。
static isInjectedBlock( block, turn, index ) {
    if ( !block || block.type !== 'text' || typeof block.text !== 'string') return null;
    const marks = turn?._injectedText;
    if ( marks && typeof marks === 'object' && Number.isInteger( index ) ) {
        const type = marks[ index ];
        return ( typeof type === 'string' && type )? type: null;
    }
    if ( Array.isArray( turn?._attachments ) && turn._attachments.length
        && block.text.startsWith( AiAssistantLlm.attachmentMetaPrefix ) ) return 'attachment';
    return null;
}
// 差し込まれたテキストブロックを取り除いた履歴を返す（保存済みの履歴を復元するときに使う）。
// ・画面に表示しない（ユーザーの発言ではないため）
// ・保存・復元を繰り返して同じテキストが積み上がったものも、この時点で1つ残らず取り除く
//   （復元後に保存されるのは取り除いた後の履歴なので、次回の保存で解消される）
// ・差し込みは toApiHistory が保存・問い合わせのたびに行うため、取り除いてもLLMへは渡り続ける
static stripInjectedBlocks( history ) {
    if ( !Array.isArray( history ) ) return history;
    return history.map(( turn ) => {
        if ( !turn || !Array.isArray( turn.content ) ) return turn;
        const content = turn.content.filter(( block, index ) => AiAssistantLlm.isInjectedBlock( block, turn, index ) === null );
        // contentが空のターンはプラットフォーム側で除外されるため、その場合は元のまま返す
        // （取り除かないので、目印もそのまま残す）
        if ( !content.length || content.length === turn.content.length ) return turn;
        const stripped = { ...turn, 'content': content };
        // 取り除いて位置がずれるため、目印は捨てる（次の保存で toApiHistory が作り直す）
        delete stripped._injectedText;
        return stripped;
    });
}
// 添付ファイルのメタ情報と、その取り扱い指示のテキストブロックを作る
static attachmentMetaBlock( attachments ) {
    if ( !Array.isArray( attachments ) || !attachments.length ) return null;

    const metaText = attachments.map(( file ) => {
        // 解析状態を判定してLLMに伝える
        //   未対応形式          … ネイティブに中身を読み取れない
        //   対応形式かつ解析オフ … ユーザーが「AIで解析」をオフにしている
        //   対応形式かつ解析オン … 中身（実体）も渡されている
        let analysisState;
        if ( !file.supported ) {
            analysisState = getMessage.FTE14128;
        } else if ( !file.use_llm ) {
            analysisState = getMessage.FTE14129;
        } else {
            analysisState = getMessage.FTE14130;
        }
        return getMessage.FTE14131( file.file_id ?? '', file.filename ?? '', file.mime_type ?? '', file.size ?? '', analysisState );
    }).join('\n');

    return {
        'type': 'text',
        'text': `${AiAssistantLlm.attachmentMetaPrefix}\n${metaText}\n\n`
            + getMessage.FTE14132
    };
}
/*
##################################################
   AI応答の生成
##################################################
*/
// messageText … ユーザー発言（テキスト）。指定するとプラットフォーム側がユーザーターンを履歴へ追加し、
//                AI応答も含めて保存する（レスポンスの saved が true になる）。
//                nullのときはmessageを指定せず、同期済みの履歴（添付ファイルやtool_resultを含む
//                contentブロック）だけで問い合わせる（プラットフォーム側でユーザーターンを追加させない）。
async requestCompletion( signal, messageText = null ) {
    const body = {
        // 会話のデフォルトモデルを上書きする（フッターで切り替えたモデルを使う）
        model_id: this.modelId,
        menu_id: this.menu
    };
    if ( messageText !== null ) body.message = messageText;
    return await this.request(AiAssistantLlm.apiUrl.completion( this.conversationId ), 'POST', body, signal );
}
/*
##################################################
   応答のcontentブロック
##################################################
*/
// 画面側（AiAssistantChat）はcontentブロックの配列（text / tool_use / thinking）を処理する。
// 現在のプラットフォームAPIはテキスト部分（content）とstop_reasonのみを返すため、
// ブロック配列が返る場合はそれを優先し、返らない場合はテキストのみのブロックに組み立てる。
//
// 【制限事項】stop_reasonが"tool_use"の応答は、どのツールをどの引数で呼び出したか
// （tool_useブロック）がAPIの応答に含まれないため実行できない。ツール実行を伴う会話には
// completionsの応答にcontentブロックをそのまま返す拡張（content_blocks）が必要。
responseContents( data ) {
    if ( Array.isArray( data.content_blocks ) ) return data.content_blocks;
    if ( Array.isArray( data.content ) ) return data.content;

    if ( data.stop_reason === 'tool_use') {
        throw new Error( getMessage.FTE14133 );
    }

    const text = ( typeof data.content === 'string')? data.content: '';
    return ( text )? [{ 'type': 'text', 'text': text }]: [];
}
/*
##################################################
   トークン取得
##################################################
*/
getToken() {
    return ( fn.getCmmonAuthFlag() )? CommonAuth.getToken():
        ( window.parent !== window && window.parent.getToken )? window.parent.getToken(): null;
}
/*
##################################################
   プラットフォームAPIへリクエストを送信する
##################################################
*/
async request( url, method, body, signal ) {
    const token = this.getToken();
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        }
    };
    if ( body ) options.body = JSON.stringify( body );
    if ( signal ) options.signal = signal;

    const response = await AiAssistantChat.fetchWithRetry( url, options, {
        retryStatuses: AiAssistantLlm.retryStatuses
    });

    const json = await response.json().catch( () => null );
    if ( !response.ok ) {
        // platform APIはエラー時も message を返すため、あればそれを利用する。
        // ステータスコードは呼び出し側での再送判断（タイムアウト確認）に使う。
        const error = new Error( json?.message ?? `AI Assistant request failed: ${response.status}`);
        error.status = response.status;
        throw error;
    }
    // 応答は { result, message, ts, data } の形なので data のみを返す
    return json?.data ?? {};
}

}
