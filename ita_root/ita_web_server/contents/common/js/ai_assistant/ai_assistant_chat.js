////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Exastro IT Automation / ai_assistant_chat.js
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
class AiAssistantChat {
/*
##################################################
   REST API URL
##################################################
*/
static get apiUrl() {
    const { organizationId, workspaceId } = fn.getCommonParams();
    return {
        // MCPサーバー（JSON-RPC）
        mcp: () => `/api/${organizationId}/workspaces/${workspaceId}/mcp`,
        // 添付ファイルの登録（multipart/form-dataでアップロードし、file_idを採番する）
        attachmentFile: () => `/api/${organizationId}/workspaces/${workspaceId}/mcp/attachment_file`
    };
}
/*
##################################################
   Constructor
##################################################
*/
constructor( params, option ) {
    this.params = params;
    this.option = option;
}

/*
##################################################
    Mount
##################################################
*/
async mount( parentElement ) {
    // Main HTML build
    this.el = this.build();
    parentElement.appendChild(this.el);

    // 初期化
    await this.init();

    return;
}
/*
##################################################
    Destroy
##################################################
*/
destroy() {
    this.ac?.abort();
    // 画像プレビュー用の objectURL を解放してからDOMを破棄する。
    this.revokeAttachmentPreviews();
    this.el?.remove();
    this.ac = null;
    this.el = null;
}
/*
##################################################
    初期化
##################################################
*/
// 初期化の失敗は性質で2つに分けて扱う。
//   ・画面が成立しないもの（ユーザID・markdownit・DOM構築）… catchせず呼び出し元へ投げる。
//     ui.js側でエラーページへ遷移させるため、ここで握りつぶさない。
//   ・一部の機能が使えなくなるだけのもの（MCP・AI利用設定の取得）… 理由を保持して続行し、
//     新規チャット画面に通知として表示する（設定を直せば使える状態のため）。
async init() {
    // 画面が成立しない処理（失敗時はthrowする）
    this.initVariable();
    this.initMarkdownit();
    // 設定ダイアログを閉じたら、設定と認証状態を読み直して画面へ反映する。
    // 会話は作成時のAIサービスに紐づいているため、会話中はAIサービスを変更させない
    // （認証切れで設定を開けるようにしているのは、認証情報を更新してもらうためだけ）。
    this.setting = new AiAssistantSetting( this.params, {
        onClose: () => this.reloadSetting(),
        isServiceChangeLocked: () => this.newChat !== true
    });

    // 先に画面の枠を作る（このあとの取得が失敗しても、フッターと通知は表示できる）
    this.refElements();
    this.setFooterElement();
    this.bindEvents();

    // 縮退運転できる処理。片方の失敗でもう片方の結果を捨てない（＆未処理の例外に
    // ならない）ようにallSettledで待ち、失敗した理由はそれぞれ別に保持する。
    const [ mcp ] = await Promise.allSettled([
        this.initMcp(),
        this.loadSetting()
    ]);
    if ( mcp.status === 'rejected') {
        console.error( mcp.reason );
        this.mcpError = getMessage.FTE14230( fn.escape( this.formatErrorMessage( mcp.reason ) ) );
    }

    // 画面専用ツールを登録する（MCPサーバー側のツール一覧が取れなくても使えるため、
    // 取得の成否にかかわらず登録して、選択肢の提示などはできる状態にしておく）
    this.initUiTools();

    this.updateFooter();

    // 前回「作業中」のまま離脱された会話があれば復元し、確認のうえ継続する（自動再開）。
    // 復元できない・対象が無い場合は通常どおり新規チャットを開始する。
    // 自動再開そのものの失敗で画面を出せなくしないよう、ここで握りつぶして新規チャットへ倒す。
    let resumed = false;
    try {
        resumed = await this._tryAutoResume();
    } catch ( error ) {
        console.warn('自動再開に失敗しました。新規チャットを開始します。', error );
        resumed = false;
    }

    // チャットスタート
    // （awaitして、画面を組み立てられなかった場合のエラーを呼び出し元まで伝える。
    //   会話を開始できなかった場合はnewChatStartの中で本文に表示する）
    if ( !resumed ) {
        await this.newChatStart();
    }
}
// 要素参照
refElements() {
    this.elements = {
        header: this.el.querySelector('.aiAssistantHeader'),
        body: this.el.querySelector('.aiAssistantBody'),
        bodyInner: this.el.querySelector('.aiAssistantBodyInner'),
        footer: this.el.querySelector('.aiAssistantFooterInner'),

        // ボタン
        settingButton: this.el.querySelector('.aiAssistantSettingButton'),
        newChatButton: this.el.querySelector('.aiAssistantNewChatButton'),
        closeChatButton: this.el.querySelector('.aiAssistantCloseChatButton')
    };
}
// 変数設定
initVariable() {
    // LLM（新規チャットの開始時に作成する。AIサービス未設定・認証エラー時はnull）
    this.llm = null;
    // 新規チャット画面か（会話が始まるとfalseになる。会話中は設定を開けない・AIサービスを
    // 変更できないという判定に使うため、画面ができる前は新規チャット扱いにしておく）
    this.newChat = true;
    // チャットで使用中のモデル（フッターで切り替える。既定はAI利用設定の既定のモデル）
    this.modelId = '';
    // AIサービスの認証確認の結果
    //   checked … 確認を実行したか（AIサービス未設定の場合は確認しない）
    //   valid   … 認証が通ったか
    //   message … 認証が通らなかった理由（画面に表示する）
    //   error   … 確認そのものに失敗したか（通信エラーなど。認証情報が無効と判断できた
    //             わけではないため、会話中の認証切れの判定には使わない）
    this.auth = { checked: false, valid: false, message: '', error: false };
    // 初期化のうち、失敗しても画面は表示できる処理のエラー内容（新規チャット画面に表示する）
    //   mcpError     … MCPツール一覧の取得に失敗（ITAの操作ができない）
    //   settingError … AI利用設定の読み込みに失敗（チャットを開始できない）
    this.mcpError = '';
    this.settingError = '';
    // MCP（ツール一覧はinitMcpで取得する。取得に失敗した場合は空のまま）
    this.mcp = { tools: [], idCounter: 0 };
    // 作業中フラグ
    this.isRunning = false;
    // チャットID
    this.chatIdCounter = 0;
    // 履歴保存用クエリ
    this.historyQueues = new Map();
    // 添付したファイル
    this.files = [];
    // 添付画像のライブプレビュー用に生成した objectURL の控え。
    // 新規チャット／履歴復元で吹き出しを破棄する際にまとめて revoke する。
    this._attachmentPreviewUrls = [];
    this.uiTools = [];
    this.pendingChoiceToolId = null;
    // モデルのフォーマット崩れで、1応答に選択肢（ask_user_choice）の tool_use が複数
    // 出る（1つの選択肢が1 tool_use に分裂する等）ことがある。これらを1つの選択肢UIに
    // 統合したうえで、代表以外の余分な tool_use_id も未応答にならないよう保持しておく。
    this.pendingExtraChoiceToolIds = [];
    // 選択肢（ask_user_choice）と通常ツールが同じ応答に混在した場合、
    // 先に実行した通常ツールの tool_result を保持しておき、ユーザーが選択肢に
    // 回答したときに選択肢の tool_result とまとめて返すためのバッファ。
    this.pendingToolResults = [];
    // このターンで更新された ITA メニュー（menu_name_rest → 表示情報）。
    // maintenance-all / create-menu が成功するたびにここへ集約し、応答が完了した
    // タイミングで「更新されたページ」への（別タブで開く）リンクとしてまとめて表示する。
    this._turnUpdatedMenus = new Map();
    // メニューの主キー列 REST 名（pk_column_name_rest）のキャッシュ（絞り込みフィルター用）。
    this._menuPkRestCache = new Map();
    // 作成する会話のプロンプトプロファイル（呼び出し元が指定する。省略時はAIアシスタントメニューのもの）。
    // ファイル編集画面から開いたチャットは、編集を助けるプロファイル（LLMEditor）で会話を作る。
    this.promptProfile = this.option?.promptProfile ?? AiAssistantLlm.promptProfile;
    // イベント停止用
    this.ac = new AbortController();
    // ユーザID
    this.id = this.params?.user?.user_id ?? null; 
    if ( this.id === null ) {
        throw new Error( getMessage.FTE14231 );
    }
}
// Markdown-it
initMarkdownit() {
    if ( typeof markdownit === 'function') {
        this.md = markdownit({
            breaks: true, // 単一の改行(\n)を<br>に変換する
            linkify: true, // http(s):// で始まる文字列を自動的にリンク化する
            highlight: function (str, lang) {
                // 読み込んでいるhighlight.jsが持つ言語（css・javascript・python・yaml）で
                // 代わりに色付けできるものは、そちらへ寄せる（jsonをjavascriptで色付けするなど）。
                // 持っていない言語（bash・iniなど）は色を付けず、そのまま表示する。
                const alias = {
                    json: 'javascript', json5: 'javascript', jsonc: 'javascript',
                    ansible: 'yaml', playbook: 'yaml'
                };
                const language = ( lang && alias[ lang.toLowerCase() ] )? alias[ lang.toLowerCase() ]: lang;
                if (language && hljs.getLanguage(language)) {
                    try {
                        return '<pre><code class="hljs">' +
                            hljs.highlight(str, { language: language, ignoreIllegals: true }).value +
                        '</code></pre>';
                    } catch (__) {}
                }
                return ''; // use external default escaping
            }
        });

        // リンクは別タブで開く（target="_blank" + rel を付与する）
        const defaultLinkOpen = this.md.renderer.rules.link_open
            || function ( tokens, idx, options, env, self ) {
                return self.renderToken( tokens, idx, options );
            };
        this.md.renderer.rules.link_open = function ( tokens, idx, options, env, self ) {
            const token = tokens[ idx ];
            token.attrSet( 'target', '_blank' );
            token.attrSet( 'rel', 'noopener noreferrer' );
            return defaultLinkOpen( tokens, idx, options, env, self );
        };
    } else {
        throw new Error( getMessage.FTE14232 );
    }
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   MCP
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    初期化
##################################################
*/
// MCPの状態（this.mcp）はinitVariableで用意しておく。ツール一覧の取得に失敗しても
// 画面専用ツールの登録などで参照するため、ここでは作り直さない。
async initMcp() {
    // initialize（サーバーはステートレスなのでセッションIDは返らないが、
    // MCPの作法として最初に呼んでおく）
    await this.mcpRequest('initialize');

    // 利用可能なツール一覧を取得する（権限で絞られた結果が返る）
    const result = await this.mcpRequest('tools/list');
    this.mcp.tools = result.tools ?? [];

    return;
}
/*
##################################################
    画面専用ツールの登録
##################################################
*/
// 画面専用ツール（MCPサーバーではなく画面側で実行するツール）のクラス一覧。
// ツールごとに「ツール定義（LLMへ渡す内容）」と「動作」を1ファイルにまとめている。
// ここに追加すれば、LLMへのツール登録・実行・履歴復元の振り分けまで自動で行われる。
static get uiToolClasses() {
    return [
        AiAssistantToolAskUserChoice,
        AiAssistantToolDisplayHtml
    ];
}
initUiTools() {
    this.uiToolMap = new Map();
    for ( const ToolClass of AiAssistantChat.uiToolClasses ) {
        this.uiToolMap.set( ToolClass.toolName, new ToolClass( this ) );
        // LLMへ渡すツール一覧に加える（MCPのツールと同じ形式で登録する）
        this.mcp.tools.push( ToolClass.definition );
    }
    // 画面専用ツールの名前一覧（応答ループでMCPツールと振り分けるために使う）
    this.uiTools = Array.from( this.uiToolMap.keys() );
}
// 画面専用ツールのインスタンスを取得する（未登録・MCPツールの場合はnull）
uiTool( name ) {
    return this.uiToolMap?.get( name ) ?? null;
}
/*
##################################################
    画面専用ツールへの委譲
##################################################
*/
// 画面専用ツールの処理は各ツールのファイル（ai_assistant/tools/）が持つ。
// チャット側からは以下のメソッドを窓口として呼び出す。
// 画面専用ツールのうち、ユーザーの選択・回答を待つ種類（ask_user_choice）かどうかを判定する。
// display_html のような即時表示ツールと処理を分けるために使う。
isUiChoiceTool( name ) {
    return name === AiAssistantToolAskUserChoice.toolName;
}
// 選択肢を表示してユーザーの回答を待つ（tool_result は次の送信で返す）
askUserChoice( toolUse ) {
    return this.uiTool( AiAssistantToolAskUserChoice.toolName )?.execute( toolUse ) ?? null;
}
// 選択肢の1件を { label, action } 形式に正規化する
normalizeChoiceOption( opt ) {
    return this.uiTool( AiAssistantToolAskUserChoice.toolName )?.normalizeOption( opt )
        ?? { label: String( opt ?? ''), action: 'other'};
}
// 選択肢の応答（tool_use ブロック群）がフォーマット崩れかどうかを判定する
isChoiceResponseMalformed( choiceBlocks ) {
    return this.uiTool( AiAssistantToolAskUserChoice.toolName )?.isMalformed( choiceBlocks ) ?? false;
}
// 分裂した複数の選択肢 tool_use を1つの選択肢 tool_use に統合する
mergeChoiceBlocks( blocks ) {
    return this.uiTool( AiAssistantToolAskUserChoice.toolName )?.mergeBlocks( blocks )
        ?? { id: '', _extraIds: [], arguments: { question: '', options: []}};
}
// display_html の表示内容をPDFとしてダウンロードする（吹き出しのPDFボタンから呼ばれる）
printDisplayHtmlAsPdf( button ) {
    this.uiTool( AiAssistantToolDisplayHtml.toolName )?.printAsPdf( button );
}
/*
##################################################
    MCPサーバーへJSON-RPCリクエストを送信する
##################################################
*/
async mcpRequest( method, params = {} ) {
    const token = this.getToken();
    const response = await fetch( AiAssistantChat.apiUrl.mcp(), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
            jsonrpc: '2.0',
            method: method,
            params: params,
            id: ++this.mcp.idCounter
        })
    });

    // JSON-RPCのエラーはHTTP 400/404/500でも本文にerrorが入る
    const json = await response.json().catch( () => null );
    if ( json?.error ) {
        throw new Error(`MCP error (${json.error.code}): ${json.error.message}`);
    }
    if ( !response.ok ) {
        throw new Error(`MCP request failed: ${response.status}`);
    }
    return json.result;
}
/*
##################################################
    MCPツールを呼び出す
##################################################
*/
async mcpToolCall( name, args = {} ) {
    const result = await this.mcpRequest('tools/call', { name: name, arguments: args });

    // ツール実行失敗はHTTP 200 + isError:true で返るため、ここで判定する
    if ( result.isError ) {
        const text = result.content?.map( c => c.text ).join('\n') ?? 'tool call failed';
        throw new Error( text );
    }
    return result;
}
/*
##################################################
    LLMが要求したツールを実行する
##################################################
*/
// LLMの tool_use ブロックを受け取ってMCPサーバーのツールを実行し、tool_result を返す。
// ・応答（JSON-RPCのエンベロープ）はそのまま tool_result の content に載せてLLMへ渡す
// ・ドライバー実行系のツールは、完了まで進捗を監視してから結果を返す
// runningEl … 「ツール実行中」の吹き出し（進捗表示に使う）
// signal    … 停止用のAbortSignal（MCPへのリクエストと進捗監視をまとめて中断する）
async executeTool( toolUse, runningEl = null, signal = null ) {
    toolUse.name = toolUse.name ?? toolUse.params?.name;
    try {
        const toolResponse = await AiAssistantChat.fetchWithRetry( AiAssistantChat.apiUrl.mcp(), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.getToken()}`
            },
            body: JSON.stringify({
                jsonrpc: '2.0',
                id: ++this.mcp.idCounter,
                method: 'tools/call',
                params: {
                    name: toolUse.name,
                    arguments: toolUse.arguments ?? toolUse.input ?? {}
                }
            }),
            signal
        });
        const toolResult = await toolResponse.json();

        // ドライバー実行系ツールなら進捗を購読して実行状況を表示し、
        // 確定した最終ステータスを取得する（完了まで待機）
        const progressOutcome = await this.watchDriverProgress( toolUse, toolResult, runningEl );

        // 最終ステータスが取れた場合は tool_result に反映する。
        // execute-driver の即時レスポンス（「実行を開始しました」）だけだと
        // LLMが開始で会話を締めてしまう / 逆に自分でステータス確認を繰り返して
        // execute-driver を再実行してしまうため、進捗監視の確定結果と
        // 「次に取るべき行動」を明示的に指示する。
        let resultForLlm = toolResult;
        if ( progressOutcome ) {
            if ( progressOutcome.type === 'done') {
                resultForLlm = {
                    ...toolResult,
                    driver_execution: {
                        monitored_by_server: true,
                        completed: true,
                        final_status: progressOutcome.status ?? '',
                        status_detail: progressOutcome.result ?? null,
                        // LLMへの明示指示（再実行・再確認ループを防ぐ）
                        instruction: getMessage.FTE14233( progressOutcome.status ?? '')
                    }
                };
            } else {
                resultForLlm = {
                    ...toolResult,
                    driver_execution: {
                        monitored_by_server: true,
                        completed: false,
                        reason: progressOutcome.type,
                        message: progressOutcome.message ?? '',
                        // 未完了でも自動リトライ（再実行）はさせない
                        instruction: getMessage.FTE14234( progressOutcome.type )
                    }
                };
            }
        }

        // maintenance-all / create-menu で ITA のページ（メニュー）が更新された場合、
        // 応答完了時にリンクを出せるよう、更新先メニューをこのターン分として控えておく。
        this.collectUpdatedMenu( toolUse, toolResult );

        return {
            type: 'tool_result',
            tool_use_id: toolUse.id ?? '',
            content: JSON.stringify( resultForLlm )
        };
    } catch ( error ) {
        // ユーザ都合の停止（AbortError）は tool_result を返さず再スローし、
        // 呼び出し側でターンごと巻き戻す（未応答 tool_use を残さない）。
        if ( error?.name === 'AbortError' || signal?.aborted ) {
            throw error;
        }
        // エラーでも内容をLLMに渡すため処理を止めない。
        // tool_use に対応する user ターンは必ず tool_use_id 付きの tool_result で
        // 始まる必要があるため、type / tool_use_id を欠かさず、is_error で失敗を伝える。
        return {
            type: 'tool_result',
            tool_use_id: toolUse.id ?? '',
            is_error: true,
            content: fn.jsonStringify( error )
        };
    }
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   更新された ITA ページのリンク
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    更新されたページの収集
##################################################
*/
// ITA のページ（メニュー）を更新するツールの一覧。
// 値は toolUse.arguments から menu_name_rest / 表示名を取り出す関数。
static get UPDATE_MENU_TOOLS() {
    return {
        // レコードの登録/更新/廃止/復活/削除。arguments.menu が menu_name_rest。
        'maintenance-all': ( args ) => ({
            menuNameRest: args?.menu ?? '',
            label: args?.menu ?? ''
        }),
        // メニュー（パラメータシート）作成。menu_definition.menu に定義が入る。
        'create-menu': ( args ) => ({
            menuNameRest: args?.menu_definition?.menu?.menu_name_rest ?? '',
            label: args?.menu_definition?.menu?.menu_name ?? args?.menu_definition?.menu?.menu_name_rest ?? ''
        })
    };
}
// 更新先メニューを（menu_name_rest をキーに）このターン分として控える共通処理。
// 同一メニューへの複数操作は1リンクに集約する（表示名・IDリストは後勝ちで更新）。
// idList: maintenance-all で登録・更新されたレコードの uuid 群（絞り込み用、無ければ空）。
_addUpdatedMenu( name, args, idList = [] ) {
    const extractor = AiAssistantChat.UPDATE_MENU_TOOLS[ name ];
    if ( !extractor ) return;
    const { menuNameRest, label } = extractor( args ?? {} );
    if ( !menuNameRest ) return;
    if ( !( this._turnUpdatedMenus instanceof Map ) ) this._turnUpdatedMenus = new Map();
    this._turnUpdatedMenus.set( menuNameRest, {
        menuNameRest,
        label: label || menuNameRest,
        idList: Array.isArray( idList ) ? idList : []
    });
}
// tool_result（JSON-RPC の structuredContent 等）から登録・更新レコードの uuid 群を取り出す。
// ITA の maintenance/all 応答は `IdList` に uuid の配列を返す（menu_maintenance_all.py 準拠）。
// エンベロープの深さがゆらぐため、IdList を再帰探索する。
_extractIdList( node, depth = 0 ) {
    if ( depth > 6 || !node || typeof node !== 'object') return [];
    if ( Array.isArray( node.IdList ) ) {
        return node.IdList.filter(( id ) => typeof id === 'string' && id );
    }
    for ( const val of Object.values( node ) ) {
        if ( val && typeof val === 'object') {
            const found = this._extractIdList( val, depth + 1 );
            if ( found.length ) return found;
        }
    }
    return [];
}
// ツール実行結果（ライブ）が ITA ページの更新なら、更新先メニューを控える。
// エラー応答（isError）や menu_name_rest 不明のものは対象外。
collectUpdatedMenu( toolUse, toolResult ) {
    const name = toolUse?.name ?? '';
    if ( !AiAssistantChat.UPDATE_MENU_TOOLS[ name ] ) return;

    // ツール自体がエラーを返した場合は更新扱いにしない。
    const structured = toolResult?.result?.structuredContent ?? {};
    if ( structured.isError === true || toolResult?.result?.isError === true ) return;

    this._addUpdatedMenu( name, toolUse.arguments ?? toolUse.input, this._extractIdList( structured ) );
}
// 履歴（保存済み tool_use / tool_result）から更新先メニューを控える（再開時用）。
// tool_result.content は executeTool で JSON文字列化されているためパースして判定する。
collectUpdatedMenuFromHistory( toolUse, toolResult ) {
    const name = toolUse?.name ?? '';
    if ( !AiAssistantChat.UPDATE_MENU_TOOLS[ name ] ) return;

    // エラーで終わった実行はリンク対象外。
    if ( toolResult?.is_error === true ) return;
    let parsed = toolResult?.content ?? null;
    if ( typeof parsed === 'string') {
        try { parsed = JSON.parse( parsed ); } catch ( error ) { parsed = null; }
    }
    const structured = parsed?.result?.structuredContent ?? {};
    if ( structured.isError === true || parsed?.result?.isError === true ) return;

    this._addUpdatedMenu( name, toolUse.arguments ?? toolUse.input, this._extractIdList( structured ) );
}
/*
##################################################
    更新されたページのリンク表示
##################################################
*/
// メニューの主キー列 REST 名（pk_column_name_rest）を取得する。
// 絞り込みフィルターのキー（uuid 相当。メニューにより名称が異なる）に使う。
// 一度取得したらキャッシュし、取得失敗時は null。
async getMenuPkRest( menuNameRest ) {
    if ( !( this._menuPkRestCache instanceof Map ) ) this._menuPkRestCache = new Map();
    if ( this._menuPkRestCache.has( menuNameRest ) ) return this._menuPkRestCache.get( menuNameRest );
    let pkRest = null;
    try {
        const info = await fn.fetch(`/menu/${menuNameRest}/info/`);
        pkRest = info?.menu_info?.pk_column_name_rest ?? null;
    } catch ( error ) {
        console.warn('getMenuPkRest: メニュー情報の取得に失敗しました', menuNameRest, error );
    }
    this._menuPkRestCache.set( menuNameRest, pkRest );
    return pkRest;
}
// ITA メニューページのURLを組み立てる（別タブ表示用）。
// ITA本体（トップ画面）は ?menu=<menu_name_rest> でメニューを切り替えるため、
// 現在のトップ画面のパスに menu パラメータを付与した絶対URLを返す。
// filter を渡すと ITA のフィルター形式（{ 列: { LIST: [...] } }）を &filter= に付与する。
buildMenuUrl( menuNameRest, filter = null ) {
    const base = `${top.location.origin}${top.location.pathname}`;
    let url = `${base}?menu=${encodeURIComponent( menuNameRest )}`;
    if ( filter ) {
        // fn.filterEncode = encodeURIComponent( JSON.stringify( filter ) )
        url += `&filter=${fn.filterEncode( filter )}`;
    }
    return url;
}
// このターンで更新された ITA ページへのリンクをまとめて1つの吹き出しで表示する。
// 表示後は控えをクリアし、同じリンクを次のセグメントで重複表示しないようにする。
renderUpdatedMenuLinks( scroll = true ) {
    const menus = ( this._turnUpdatedMenus instanceof Map ) ? this._turnUpdatedMenus : null;
    if ( !menus || !menus.size || !this.elements.chatList ) return;
    this._turnUpdatedMenus = new Map();

    const el = document.createElement('li');
    el.classList.add('aiAssistantChatItem', 'aiAssistantChatAssistantMessage', 'aiAssistantChatUpdatedMenus');
    // 直前がアシスタントなら連続クラスを付与
    const prevItem = this.elements.chatList.lastElementChild;
    if ( prevItem?.classList.contains('aiAssistantChatAssistantMessage') ) {
        el.classList.add('aiAssistantChatAssistantMessageChain');
    }

    const inner = document.createElement('div');
    inner.classList.add('aiAssistantChatItemInner', 'aiAssistantChatAssistantMessageInner');

    const list = document.createElement('ul');
    list.classList.add('aiAssistantUpdatedMenusList');
    for ( const { menuNameRest, label, idList } of menus.values() ) {
        const item = document.createElement('li');
        item.classList.add('aiAssistantUpdatedMenusItem');

        const a = document.createElement('a');
        a.classList.add('aiAssistantUpdatedMenusLink');
        // まずはフィルター無しの基本URLを設定しておく（主キー取得失敗時のフォールバック）。
        a.href = this.buildMenuUrl( menuNameRest );
        a.target = '_blank';
        a.rel = 'noopener noreferrer';
        a.innerText = label || menuNameRest;
        item.append( a );
        list.append( item );

        // 登録・更新レコードがあれば、主キー列名を取得して該当レコードのみ絞り込む
        // フィルターを URL に埋め込む（非同期。取得できたら href を差し替える）。
        if ( Array.isArray( idList ) && idList.length ) {
            this.getMenuPkRest( menuNameRest ).then(( pkRest ) => {
                if ( !pkRest ) return;
                // discard: { NORMAL: '' } を付けないと ITA 既定で廃止レコードが除外され、
                // 廃止したレコードに絞り込んでもヒットしないため明示的に「廃止含む」を指定する。
                const filter = { [ pkRest ]: { LIST: idList }, discard: { NORMAL: ''}};
                a.href = this.buildMenuUrl( menuNameRest, filter );
                a.classList.add('aiAssistantUpdatedMenusLinkFiltered');
                a.title = getMessage.FTE14235( idList.length );
            });
        }
    }
    inner.append( list );
    el.append( inner );

    // 回答待ちの選択肢が表示中なら、その直前に挿入する。
    // （選択肢は updateChat 側で常に末尾へ寄せる作りのため、リンクを末尾に足すと
    //   選択肢より後ろに来てしまう。選択肢を一番最後に保つため前に差し込む）
    const choiceItem = this.elements.chatList.querySelector('.aiAssistantChatUserChoice');
    if ( choiceItem ) {
        this.elements.chatList.insertBefore( el, choiceItem );
    } else {
        this.elements.chatList.append( el );
    }
    if ( scroll ) setTimeout( () => this.scrollChatArea( el ), 100 );
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   状態チェック
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    AIアシスタントが設定済みかチェックする
##################################################
*/
// assistantCheck = true : LLMのみチェックする
checkAiAssistantSetting( assistantCheck = false) {
    return AiAssistantSetting.isConfigured( this.setting.preference, assistantCheck );
}
/*
##################################################
    AIサービスの認証が通るかチェックする
##################################################
*/
// 設定されていても、認証情報の期限切れや失効でチャットを開始できないことがある。
// 設定を読み込んだ直後に確認して、通らなかった場合は再設定を促すため結果を保持する。
//
// 会話中でも、確認するのは設定で選択中のAIサービスの認証情報でよい（会話は作成時の
// AIサービスに固定されるが、会話中はAIサービスを変更できないようにしているため、
// 選択中のAIサービスと会話のAIサービスは一致する）。
async checkAiAssistantAuth() {
    this.auth = { checked: false, valid: false, message: '', error: false };

    // AIサービスが未設定の場合は確認する認証情報がない
    if ( !this.checkAiAssistantSetting( true ) ) return this.auth;

    try {
        const result = await this.setting.verifyCredential( this.setting.preference.ai_service_id );
        this.auth = {
            checked: true,
            valid: result?.valid === true,
            message: ( result?.valid === true )? '': result?.message ?? '',
            error: false
        };
    } catch ( error ) {
        // 確認そのものに失敗した場合も、チャットは開始できないため認証エラーとして扱う
        // （認証情報が無効と判断できたわけではないためerrorを立てておく）
        console.error( error );
        this.auth = {
            checked: true,
            valid: false,
            message: this.formatErrorMessage( error ),
            error: true
        };
    }
    return this.auth;
}
/*
##################################################
    AI利用設定の読み込み
##################################################
*/
// AI利用設定を読み込み、その認証情報で実際に認証できるかを確認する。
// 取得に失敗しても画面自体は表示できるため、理由を保持して続行する（未設定と同じ扱いに
// なり、チャットは開始できない状態で「読み込めなかったこと」を本文へ表示する）。
// 一時的な失敗であれば、設定ダイアログを閉じたタイミングの再読み込みで回復する。
async loadSetting() {
    this.settingError = '';
    try {
        await this.setting.loadPreference();
    } catch ( error ) {
        console.error( error );
        this.settingError = getMessage.FTE14236( fn.escape( this.formatErrorMessage( error ) ) );
    }
    await this.checkAiAssistantAuth();
    return;
}
/*
##################################################
    チャットを開始できるかチェックする
##################################################
*/
// 設定が完了していて、かつその認証情報で認証が通っている状態
isChatReady() {
    return this.checkAiAssistantSetting() && this.auth.valid;
}
// 設定はされているが認証が通らなかった状態
isAuthError() {
    return this.checkAiAssistantSetting( true ) && this.auth.checked && !this.auth.valid;
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   認証切れ
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    認証切れの案内文
##################################################
*/
// アラートとシステムメッセージで共用するため、プレーンテキスト（改行区切り）で作る。
// 認証の確認そのものに失敗した場合（auth.error）も、有効期限切れと区別できないため
// 同じ文言を使い、確認できた理由（auth.message）を添えて判断できるようにする。
authExpiredMessage() {
    // AIサービス名は、設定が読み込めなかった場合や未設定になった場合は空になる
    const serviceName = this.setting.currentServiceName;
    const service = ( serviceName )? getMessage.FTE14237( serviceName ): getMessage.FTE14238;
    const detail = ( this.auth.message )? `\n（${this.auth.message}）`: '';
    return getMessage.FTE14239( service ) + detail;
}
/*
##################################################
    認証切れを画面へ反映する
##################################################
*/
// 会話中     … 設定ボタンを開けるようにして、システムメッセージで更新を促す
// 新規チャット … 画面を作り直して通知（認証エラー）を表示する
// alertFlag … 気付かないまま操作を続けないよう、アラートも表示するか
//   （送信エラーの内容を既にアラートで表示している場合はfalseにする）
async applyAuthExpired( alertFlag = true ) {
    const message = this.authExpiredMessage();

    if ( this.newChat === true ) {
        await this.newChatStart();
    } else {
        this.updateSettingButtonState();
        this.updateChat({ role: 'systemNotice', text: message });
    }

    if ( alertFlag ) alert( message );
    return;
}
/*
##################################################
    エラー後の認証チェック（会話中）
##################################################
*/
// AIサービスの認証情報には有効期限があり、会話の途中で切れることがある。その場合は
// 認証情報を更新しないと会話を続けられないため、応答がエラーで終わったときに認証を
// 確認し、切れていた場合は会話中でも設定を開けるようにして更新を促す。
// 戻り値：認証が切れていた場合true
async checkAuthAfterError() {
    // AIサービスが未設定の場合は確認する認証情報がない（別の原因のエラー）
    if ( !this.checkAiAssistantSetting( true ) ) return false;

    const before = this.auth;
    await this.checkAiAssistantAuth();

    // 認証は通っている（別の原因のエラー）
    if ( this.auth.valid ) return false;

    // 確認そのものに失敗した場合は、認証切れとは判断できない（通信エラーなど）。
    // 誤って認証エラーの状態にしないよう、確認前の状態へ戻して何も案内しない。
    // （エラーの内容は送信エラーとして表示済み）
    if ( this.auth.error === true ) {
        this.auth = before;
        return false;
    }

    await this.applyAuthExpired( false );
    return true;
}
/*
##################################################
    会話を再開する前の認証チェック
##################################################
*/
// 認証情報の有効期限は、会話から離れている間にも切れる。切れたまま復元しても続きを
// 送信した時点で失敗するため、再開の前に確認して、切れていた場合はアラートで更新を促す。
// 戻り値：再開できる場合true
async checkAuthBeforeResume() {
    // 未設定の場合は認証以前に再開できない（再開処理側でエラーになる）
    if ( !this.checkAiAssistantSetting( true ) ) return true;

    await this.checkAiAssistantAuth();
    if ( !this.isAuthError() ) return true;

    await this.applyAuthExpired();
    return false;
}
/*
##################################################
    設定ダイアログを閉じたあとの再読み込み
##################################################
*/
// 認証情報やモデルを再設定した結果を反映する
// （初期化時にAI利用設定を読み込めていない場合は、ここで読み込み直す）
async reloadSetting() {
    // 会話中に設定を開けるのは認証が切れているときだけなので、認証情報を更新できたか
    // 判定するために、開く前の状態を控えておく
    const wasAuthError = this.isAuthError();

    if ( this.settingError ) {
        await this.loadSetting();
    } else {
        await this.checkAiAssistantAuth();
    }

    // 新規チャット画面のみ作り直す（チャット中は表示を維持し、フッターだけ更新する）
    if ( this.newChat ) {
        await this.newChatStart();
    } else {
        this.updateFooter();
        // 認証が切れている間だけ設定を開けるようにしているため、状態を作り直す
        this.updateSettingButtonState();
        // 認証切れから会話へ戻れるようになったか（戻れない場合は更新を促し続ける）
        if ( wasAuthError ) {
            this.updateChat({
                role: 'systemNotice',
                text: ( this.auth.valid )
                    ? getMessage.FTE14240
                    : this.authExpiredMessage()
            });
        }
    }
    return;
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   基本UI
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    Main HTML
##################################################
*/
build() {
    const el = document.createElement('div');
    el.className = 'aiAssistantContainer';
    el.innerHTML = `
    <div class="aiAssistantContainerInner">
        <div class="aiAssistantHeader">${this.createHeaderMenuHtml()}</div>
        <div class="aiAssistantBody">
            <div class="aiAssistantBodyInner">
            </div>
        </div>
        <div class="aiAssistantFooter">
            <div class="aiAssistantFooterInner">
            </div>
        </div>
    </div>`;
    return el;
}
/*
##################################################
    Header HTML
##################################################
*/
createHeaderMenuHtml() {
    const menuList = {
        Main: [
            { button: { className: 'aiAssistantNewChatButton', icon: 'edit', text: getMessage.FTE14241, type: 'newChat', action: 'positive', minWidth: '160px', disabled: false }},
            { button: { className: 'aiAssistantCloseChatButton', icon: 'check', text: getMessage.FTE14242, type: 'closeChat', action: 'positive', minWidth: '160px', disabled: true }}
        ],
        Sub: [
            { button: { className: 'aiAssistantSettingButton', icon: 'gear', text: getMessage.FTE14243, type: 'aiAssistantSetting', action: 'default', minWidth: '160px'}}
        ]
    };
    return fn.html.operationMenu( menuList );
}
/*
##################################################
    AIサービス設定ボタンの活性状態
##################################################
*/
// 会話中はAI利用設定を変更できないようにしている（使用するAIサービスが入れ替わると
// 進行中の会話と噛み合わなくなるため）。ただし認証が切れている場合は、認証情報を
// 更新しないと会話を続けられないため、会話中でも設定を開けるようにする。
updateSettingButtonState() {
    const button = this.elements?.settingButton;
    if ( !button ) return;
    button.disabled = ( this.newChat !== true && !this.isAuthError() );
}
/*
##################################################
    Footer HTML
##################################################
*/
// Footer HTML
setFooterElement() {
    this.elements.footer.append( this.createFooterAiNameElement() );
    this.elements.footer.append( this.createFooterModelListElement() );
}
// 共通HTML
createFooterCommonElement() {
    const el = document.createElement('div');
    el.classList.add('aiAssistantFooterBlock')
    el.innerHTML = `
    <dl class="aiAssistantFooterList">
        <dt class="aiAssistantFooterTitle"></dt>
        <dd class="aiAssistantFooterItem"></dd>
    </dl>`;
    return el;
}
// 共通テキスト
setFooterCommonText( element, text ) {
    element.innerHTML = `<span class="aiAssistantFooterText">${text}</span>`;
}
// AI名HTML
createFooterAiNameElement() {
    const el = this.createFooterCommonElement();
    this.setFooterCommonText( el.querySelector('.aiAssistantFooterTitle'), 'AI');
    this.elements.aiName = el.querySelector('.aiAssistantFooterItem');
    return el;
}
// モデルリストHTML
createFooterModelListElement() {
    const el = this.createFooterCommonElement();
    this.setFooterCommonText( el.querySelector('.aiAssistantFooterTitle'), getMessage.FTE14244 );
    this.elements.modelList = el.querySelector('.aiAssistantFooterItem');
    return el;
}
// AI名更新
updateFooterAiName() {
    const aiName = ( this.checkAiAssistantSetting( true ) )
        ? fn.escape( this.setting.currentServiceName ): `<span class="notSelected">${getMessage.FTE14245}</span>`;
    this.setFooterCommonText( this.elements.aiName, aiName );
}
// Footer 更新
updateFooter() {
    this.updateFooterAiName();
    this.updateFooterModelList();
}
// モデルリスト更新
// AI利用設定のピックアップモデルを、チャット中に切り替えられる選択肢として表示する
updateFooterModelList() {
    const selectedList = ( this.checkAiAssistantSetting() )? this.setting.currentPickupModels: [];
    if ( !selectedList.length ) {
        this.modelId = '';
        this.setFooterCommonText( this.elements.modelList, `<span class="notSelected">${getMessage.FTE14245}</span>`);
        return;
    }

    // 使用中のモデルが選択肢から外れた場合（設定変更・AIサービス切り替え）は、既定のモデルへ戻す
    const selectModelId = this.getUseModelId( selectedList );
    this.modelId = selectModelId;

    const modelSelectWrap = document.createElement('div');
    modelSelectWrap.classList.add('modelSelectWrap');

    const modelSelectedName = document.createElement('div');
    modelSelectedName.classList.add('modelSelectedName');
    modelSelectedName.innerText = selectedList.find(( item ) => item.id === selectModelId )?.name ?? '';

    const modelList = document.createElement('ul');
    const name = `modelSelectRadio`;
    modelList.classList.add('modelSelectList');
    // モデルIDには記号が含まれるため、id属性には連番を使う
    selectedList.forEach(( item, index ) => {
        const modelid = item.id ?? '';
        const modelItem = document.createElement('li');
        modelItem.classList.add('modelSelectItem');

        const modelItemLabel = document.createElement('label');
        modelItemLabel.classList.add('modelSelectLabel');
        modelItemLabel.setAttribute('for', `modelSelectRadio_${index}`)
        modelItemLabel.innerText = item.name ?? '';

        const modelItemRadio = document.createElement('input');
        modelItemRadio.classList.add('modelSelectRadio');
        modelItemRadio.setAttribute('type', 'radio');
        modelItemRadio.setAttribute('name', name );
        modelItemRadio.setAttribute('id', `modelSelectRadio_${index}`);
        modelItemRadio.setAttribute('value', modelid );
        if ( selectModelId === modelid ) {
            modelItemRadio.checked = true;
        }

        modelItem.append( modelItemRadio, modelItemLabel );
        modelList.appendChild( modelItem );
    });
    modelSelectWrap.append( modelSelectedName, modelList );

    // 幅を最長モデル名に合わせるための採寸用（非表示）要素
    const modelSelectSizer = document.createElement('div');
    modelSelectSizer.classList.add('modelSelectSizer');
    modelSelectSizer.setAttribute('aria-hidden', 'true');
    for ( const item of selectedList ) {
        const sizerItem = document.createElement('div');
        sizerItem.classList.add('modelSelectSizerItem');
        sizerItem.innerText = item.name ?? '';
        modelSelectSizer.appendChild( sizerItem );
    }
    modelSelectWrap.append( modelSelectSizer );

    this.elements.modelList.replaceChildren( modelSelectWrap );
}
// チャットで使用するモデル（切り替えたモデルを優先し、選択肢になければ既定のモデル）
getUseModelId( modelList = this.setting.currentPickupModels ) {
    const has = ( modelId ) => Boolean( modelId ) && modelList.some(( item ) => item.id === modelId );
    if ( has( this.modelId ) ) return this.modelId;
    if ( has( this.setting.currentModelId ) ) return this.setting.currentModelId;
    return modelList[0]?.id ?? '';
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Chat
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    新規チャット画面
##################################################
*/
async newChatStart() {
    // 新しい会話を始めるので、前の会話のLLM（会話履歴）は破棄する
    this.llm = null;
    this.setNewChat();

    try {
        await this.ensureLlm();
    } catch ( error ) {
        // 準備に失敗した場合は、その旨を表示する（送信時に再度用意を試みる）
        console.error( error );
        this.elements.chatBody?.append(
            this.createNoticeMessageElement(
                getMessage.FTE14246( fn.escape( this.formatErrorMessage( error ) ) )
            )
        );
    }
}
// LLM層を用意する。用意済みならそれを返す。
//   AIサービスが未設定、または認証が通っていない場合はnullを返す
//   （フッターと本文に設定を促すメッセージを表示している状態）
// AIサービス側の会話（履歴の保存先）は、最初の送信・保存のときにLLM層が作成する
// （画面を開くだけで空の会話が会話履歴に残らないようにするため）。
async ensureLlm() {
    if ( this.llm ) return this.llm;
    if ( !this.isChatReady() ) return null;

    // 使用するモデルはフッターで切り替えたものを優先する（未選択ならAI利用設定の既定のモデル）
    this.modelId = this.getUseModelId();

    // システムプロンプトとツールの実行結果の解釈はAIサービス側（プラットフォームAPI）が
    // 持つため、ここではAIサービス・モデルとツール一覧のみを渡す。
    const llm = new AiAssistantLlm( this.promptProfile );
    await llm.setup({
        aiServiceId: this.setting.currentAiServiceId,
        modelId: this.modelId
    }, this.mcp.tools );

    this.llm = llm;
    return this.llm;
}
// チャット画面
setNewChat() {
    // メッセージ初期化
    this.newChat = true;
    this.chatId = this.chatIdCounter++;
    // 新しい会話を始めるので、中断再開マーカーは破棄する（前の会話を自動再開しない）。
    this._clearActiveChat();
    this.clearFile();
    // 破棄する吹き出しの画像プレビュー（objectURL）を解放する。
    this.revokeAttachmentPreviews();

    // 初期チャットエリア作成
    const el = this.createChatContainerElement();
    this.elements.body.classList.remove('aiAssistantChatNow');
    this.elements.body.classList.add('aiAssistantNewChat');
    this.elements.chatBody = el.querySelector('.aiAssistantChatBody');
    // 挨拶
    this.elements.chatBody.append( this.createGreetingMessageElement() );
    // 初期化で一部が読み込めなかった場合（設定を直せば使える状態のため理由を表示する）
    if ( this.settingError ) {
        this.elements.chatBody.append( this.createNoticeMessageElement( this.settingError ) );
    } else if ( !this.isChatReady() ) {
        // 未設定・認証エラーの場合
        this.elements.chatBody.append( this.createNoticeMessageElement() );
    }
    if ( this.mcpError ) {
        this.elements.chatBody.append( this.createNoticeMessageElement( this.mcpError ) );
    }

    // 設定ボタンは新規チャット画面（と、会話中の認証切れ）のみ
    this.updateSettingButtonState();

    // チャット閉じるボタン非活性
    this.elements.closeChatButton.disabled = true;

    this.elements.bodyInner.replaceChildren( el );
    this.updateFooter();
}
/*
##################################################
    Chat HTML
##################################################
*/
createChatContainerElement() {
    const el = document.createElement('div');
    el.classList.add('aiAssistantChatContainer');
    el.innerHTML = `
    <div class="aiAssistantChatInner">
        <div class="aiAssistantChatBody">
            <div class="aiAssistantCharacter">${fn.html.icon('ai_assistant')}</div>
        </div>
        <div class="aiAssistantChatFooter"></div>
    </div>`;
    // 準備完了している
    if ( this.isChatReady() ) {
        const footer = `
        <div class="aiAssistantChatComposer">
            <div class="aiAssistantInputSelectFiles">
                <ul class="aiAssistantInputSelectFilesList">
                </ul>
            </div>
            <div class="aiAssistantInputMessage">
                <textarea name="aiAssistantInputTextarea" class="aiAssistantInputTextarea textarea input" spellcheck="false" placeholder="${getMessage.FTE14247}"></textarea>
            </div>
            <div class="aiAssistantInputActions">
                ${fn.html.button( fn.html.icon('plus'), 'aiAssistantInputActionsFileButton itaButton button popup', { type: 'file', action: 'default  ', title: getMessage.FTE14248 })}
                ${fn.html.button( fn.html.icon('send'), 'aiAssistantInputActionsSendButton itaButton button popup', { type: 'send', action: 'positive', title: getMessage.FTE14249 })}
                ${fn.html.button( fn.html.icon('stop'), 'aiAssistantInputActionsStopButton itaButton button popup', { type: 'stop', action: 'danger', title: getMessage.FTE14250 })}
            </div>
        </div>
        ${this.createDisclaimerMessageHtml()}`;
        el.querySelector('.aiAssistantChatFooter').innerHTML = footer;
        this.elements.message = el.querySelector('.aiAssistantInputTextarea');
        this.elements.fileList = el.querySelector('.aiAssistantInputSelectFilesList');
        // 保持中のファイルを描画
        this.renderFileList();
    }
    return el;
}
// 挨拶
createGreetingMessageElement() {
    const el = document.createElement('div');
    el.classList.add('aiAssistantGreetingMessage');

    const hour = new Date().getHours();
    let message = '';
    if (hour >= 5 && hour < 11) {
        message += getMessage.FTE14251;
    } else if (hour >= 11 && hour < 17) {
        message += getMessage.FTE14252;
    } else if (hour >= 17 && hour < 22) {
        message += getMessage.FTE14253;
    } else {
        message += getMessage.FTE14254;
    }
    message += getMessage.FTE14255;

    if ( this.isChatReady() ) {
        message += getMessage.FTE14256;
    }

    el.innerHTML = message;
    return el;
}
// 未設定・認証エラー
//   html … 個別の通知内容（省略時は設定状況から判定して表示する）
createNoticeMessageElement( html ) {
    const el = document.createElement('div');
    el.classList.add('aiAssistantNoticeMessage');

    if ( html ) {
        el.innerHTML = fn.html.icon('circle_exclamation') + ' ' + html;
        return el;
    }

    // 認証が通らなかった場合は、認証情報の再設定を促す
    if ( this.isAuthError() ) {
        const serviceName = this.setting.currentServiceName;
        const detail = ( this.auth.message )
            ? `<div class="aiAssistantNoticeDetail">${fn.escape( this.auth.message )}</div>`: '';
        el.innerHTML = fn.html.icon('circle_exclamation') + ' '
            + getMessage.FTE14257( fn.escape( serviceName ) )
            + detail;
        return el;
    }

    el.innerHTML = fn.html.icon('circle_exclamation') + ' ' + getMessage.FTE14258;
    return el;
}
// 免責事項
createDisclaimerMessageHtml() {
    return `<div class="aiAssistantDisclaimerMessage">${getMessage.FTE14259}</div>`;
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   ファイル
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    ファイル選択
##################################################
*/
async fileSelect() {
    this.isRunning = true;

    try {
        // 複数ファイル選択
        const files = await new Promise(( resolve ) => {
            const input = document.createElement('input');
            input.type = 'file';
            input.multiple = true;
            input.addEventListener('change', () => {
                resolve( Array.from( input.files ?? [] ) );
            }, { once: true });
            // キャンセル時は空配列で解決
            input.addEventListener('cancel', () => {
                resolve( [] );
            }, { once: true });
            input.click();
        });

        if ( files.length ) {
            await this.setFile( files );
        }
    } catch ( error ) {
        console.error( error );
    }

    this.isRunning = false;
}
/*
##################################################
    ファイル準備
##################################################
*/
setFile( files, options = {} ) {
    // アップロードは送信時に行うため、ここではファイルを保持するだけ
    // useLlm : LLMにファイルを渡すか（デフォルトは渡さない）
    // options.useLlm : 追加時点で解析ONにするか（貼り付け画像などで使用）
    const useLlm = options.useLlm === true;
    if ( !Array.isArray( this.files ) ) this.files = [];
    this.files.push( ...files.map(( file ) => ({ file, useLlm })) );
    this.renderFileList();
}
// 貼り付けられた画像ファイルに、わかりやすく重複しないファイル名を付け直す。
// クリップボード由来の画像は名前が空だったり "image.png" 固定だったりするため、
// MIMEタイプから拡張子を決め、日時付きの名前にして一覧での区別をつける。
normalizePastedImageFile( file ) {
    // すでに拡張子付きの妥当な名前があればそのまま使う（"image.png" 等の既定名は付け替える）。
    const name = file.name ?? '';
    const hasProperName = name && name !== 'image.png' && /\.[^.]+$/.test( name );
    if ( hasProperName ) return file;

    const mimeType = file.type ?? '';
    const ext = ( mimeType.split('/')[ 1 ] || 'png').split('+')[ 0 ];
    const now = new Date();
    const pad = ( n ) => String( n ).padStart( 2, '0');
    const stamp = `${now.getFullYear()}${pad( now.getMonth() + 1 )}${pad( now.getDate() )}`
        + `_${pad( now.getHours() )}${pad( now.getMinutes() )}${pad( now.getSeconds() )}`;
    const newName = `pasted-image-${stamp}.${ext}`;

    // File 名は読み取り専用のため、同じ内容で名前だけ変えた File を作り直す。
    try {
        return new File( [ file ], newName, { type: mimeType, lastModified: file.lastModified });
    } catch ( error ) {
        // File コンストラクタが使えない環境では元のファイルをそのまま返す。
        console.warn('貼り付け画像のファイル名変更に失敗しました。', error );
        return file;
    }
}
// 指定したインデックスのファイルを削除する
removeFile( index ) {
    if ( !Array.isArray( this.files ) ) return;
    if ( index < 0 || index >= this.files.length ) return;
    this.files.splice( index, 1 );
    this.renderFileList();
}
// 指定したインデックスのテキストファイルをエディタで編集する
async editFile( index ) {
    if ( !Array.isArray( this.files ) ) return;
    if ( index < 0 || index >= this.files.length ) return;
    const item = this.files[ index ];
    const file = item.file;
    // common.js の fileEditor を利用（edit モードは編集結果を { name, file } で返す）
    const result = await fn.fileEditor( file, file.name, 'edit', {} );
    // インデックスが編集中にずれる可能性があるため対象を再取得して更新する
    const currentIndex = this.files.indexOf( item );
    if ( result && result.file && currentIndex !== -1 ) {
        this.files[ currentIndex ] = { ...item, file: result.file };
        this.renderFileList();
    }
}
// 指定したインデックスの画像ファイルをプレビュー表示する
async previewFile( index ) {
    if ( !Array.isArray( this.files ) ) return;
    if ( index < 0 || index >= this.files.length ) return;
    const file = this.files[ index ].file;
    await fn.fileEditor( file, file.name, 'preview', {} );
}
// 吹き出し内の画像サムネイルから、添付時と同じプレビュー（fn.fileEditor）を開く。
// 送信後はファイル実体を保持していないため、生成済みの objectURL から blob を
// 取り出して File を再構築し、プレビューに渡す。
async previewAttachment( url, filename ) {
    if ( !url ) return;
    try {
        const res = await fetch( url );
        const blob = await res.blob();
        const name = filename || 'image';
        const file = new File( [ blob ], name, { type: blob.type });
        await fn.fileEditor( file, name, 'preview', {} );
    } catch ( error ) {
        console.error('プレビューの表示に失敗しました。', error );
    }
}
// 指定したインデックスのファイルのLLM送信フラグを切り替える
toggleFileLlm( index ) {
    if ( !Array.isArray( this.files ) ) return;
    if ( index < 0 || index >= this.files.length ) return;
    this.files[ index ].useLlm = !this.files[ index ].useLlm;
    this.renderFileList();
}
// クリア
clearFile() {
    this.files = [];
    this.renderFileList();
}
// 吹き出しの画像プレビュー用に生成した objectURL をまとめて解放する。
// 新規チャット／履歴復元で吹き出しを破棄するタイミングで呼び、メモリを解放する。
revokeAttachmentPreviews() {
    if ( !Array.isArray( this._attachmentPreviewUrls ) ) {
        this._attachmentPreviewUrls = [];
        return;
    }
    for ( const url of this._attachmentPreviewUrls ) {
        try {
            URL.revokeObjectURL( url );
        } catch ( error ) {
            console.warn('プレビューURLの解放に失敗しました。', error );
        }
    }
    this._attachmentPreviewUrls = [];
}
// 選択中ファイルの表示リストを描画する
renderFileList() {
    const list = this.elements.fileList;
    if ( !list ) return;

    if ( !Array.isArray( this.files ) || !this.files.length ) {
        list.replaceChildren();
        return;
    }

    const items = this.files.map(( item, index ) => {
        const file = item.file;
        const li = document.createElement('li');
        li.classList.add('aiAssistantInputSelectFilesItem');
        if ( item.useLlm ) li.classList.add('aiAssistantInputSelectFilesItemUseLlm');

        // テキストファイルは編集、画像ファイルはプレビューのボタンを×ボタンの左に表示する
        const fileType = fn.fileTypeCheck( file.name );
        let openButton = '';
        if ( fileType === 'text') {
            openButton = fn.html.button( fn.html.icon('search'), 'itaButton aiAssistantInputSelectFilesOpen', { type: 'fileEdit', index: index, action: 'normal', title: getMessage.FTE14260 });
        } else if ( fileType === 'image') {
            openButton = fn.html.button( fn.html.icon('search'), 'itaButton aiAssistantInputSelectFilesOpen', { type: 'filePreview', index: index, action: 'normal', title: getMessage.FTE14261 });
        }

        li.innerHTML = `
            <span class="aiAssistantInputSelectFilesName">${fn.escape( file.name )}</span>
            <span class="aiAssistantInputSelectFilesSize">${this.formatFileSize( file.size )}</span>
            <label class="aiAssistantInputSelectFilesLlm" title="${getMessage.FTE14262}">
                <input type="checkbox" class="aiAssistantInputSelectFilesLlmCheck" data-type="fileToggle" data-index="${index}"${ item.useLlm ? ' checked': ''}>
                <span class="aiAssistantInputSelectFilesLlmSwitch" aria-hidden="true"></span>
                <span class="aiAssistantInputSelectFilesLlmText">${getMessage.FTE14263}</span>
            </label>
            ${openButton}
            ${fn.html.button( fn.html.icon('cross'), 'itaButton aiAssistantInputSelectFilesRemove', { type: 'fileRemove', index: index, action: 'danger', title: getMessage.FTE14264 })}`;
        return li;
    });
    list.replaceChildren( ...items );
}
// ファイルサイズを見やすい単位に整形する
formatFileSize( size ) {
    const byte = Number( size ) || 0;
    if ( byte < 1024 ) return `${byte} B`;
    const units = [ 'KB', 'MB', 'GB', 'TB'];
    let value = byte / 1024;
    let unitIndex = 0;
    while ( value >= 1024 && unitIndex < units.length - 1 ) {
        value /= 1024;
        unitIndex++;
    }
    return `${value.toFixed(1)} ${units[ unitIndex ]}`;
}
/*
##################################################
    ファイルの登録（MCPサーバーへのアップロード）
##################################################
*/
// 添付ファイルをITAのMCPサーバーへアップロードし、LLMへ渡すメタ情報（file_id等）を受け取る。
// ※ ファイルの実体はワークスペースDB（T_AI_ATTACHMENT_FILE）に保存され、ここで採番された
//    file_id をそのままMCPツールの引数に指定できる（添付ファイルの読み取り・zip化・ITAの
//    メニューへのファイル登録など）。
// ※ ファイルの中身をAIに解析させる場合は、これとは別に「AIで解析」がオンかつ対応形式のときだけ、
//    LLM層（AiAssistantLlm）が image / document のcontentブロックとして直接渡す。
async fileUploader( file ) {
    const formData = new FormData();
    // ファイル名は File が持つ名前をそのまま使う（名前が無い場合のみ既定名を付ける）
    formData.append('file', file, file?.name || 'attachment');

    // Content-Type は multipart の boundary を含める必要があるため、ヘッダーには指定せず
    // ブラウザに任せる。
    // また、リトライ（fetchWithRetry）は使わない。登録は冪等ではなく、サーバー側で登録が
    // 済んでいるのに応答を受け取れなかった場合、再送すると同じファイルが二重に登録される。
    const response = await fetch( AiAssistantChat.apiUrl.attachmentFile(), {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${this.getToken()}`
        },
        body: formData
    });

    // エラー時は本文にerror/messageが入る（サーバー内部エラーではJSONで返らない場合もある）
    const json = await response.json().catch( () => null );
    if ( !response.ok || !json?.file_id ) {
        throw new Error( json?.message ?? getMessage.FTE14265( response.status ) );
    }

    return {
        file_id: json.file_id,
        filename: json.filename ?? file?.name ?? '',
        size: json.size ?? file?.size ?? '',
        mime_type: json.mime_type ?? file?.type ?? ''
    };
}
// ファイルの実体をbase64（data URIなしの純粋なbase64）に変換する
fileToBase64( file ) {
    return new Promise(( resolve, reject ) => {
        const reader = new FileReader();
        reader.onload = () => {
            // "data:<mime>;base64,xxxx" の base64部分のみ取り出す
            const result = reader.result ?? '';
            const base64 = String( result ).split(',')[ 1 ] ?? '';
            resolve( base64 );
        };
        reader.onerror = () => reject( reader.error );
        reader.readAsDataURL( file );
    });
}
// ファイルの実体を生テキストに変換する
fileToText( file ) {
    return new Promise(( resolve, reject ) => {
        const reader = new FileReader();
        reader.onload = () => resolve( String( reader.result ?? '') );
        reader.onerror = () => reject( reader.error );
        reader.readAsText( file );
    });
}
// テキストファイルかどうかを判定する
isTextFile( file ) {
    const mimeType = file.type ?? '';
    if ( mimeType.startsWith('text/') ) return true;
    // text/ 以外でテキストとして扱うMIMEタイプ
    const textLikeTypes = [
        'application/json',
        'application/xml',
        'application/javascript',
        'application/x-yaml',
        'application/yaml'
    ];
    if ( textLikeTypes.includes( mimeType ) ) return true;
    // MIMEタイプが空の場合は拡張子で判定
    if ( mimeType === '') {
        const ext = ( file.name ?? '').split('.').pop().toLowerCase();
        const textExtensions = [
            'txt', 'md', 'csv', 'tsv', 'log', 'json', 'xml', 'yaml', 'yml',
            'js', 'ts', 'py', 'java', 'c', 'cpp', 'h', 'go', 'rb', 'php',
            'sh', 'sql', 'html', 'css', 'ini', 'conf', 'cfg', 'toml'
        ];
        return textExtensions.includes( ext );
    }
    return false;
}
// LLMがネイティブに中身を解析できる形式かどうかを判定する
// （AIサービス側の対応形式と一致させる：画像・PDF・テキスト）
isLlmSupportedFile( file ) {
    const mimeType = file.type ?? '';
    const supportedImageTypes = [ 'image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    if ( supportedImageTypes.includes( mimeType ) ) return true;
    if ( mimeType === 'application/pdf') return true;
    if ( this.isTextFile( file ) ) return true;
    return false;
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   チャット HTML
//
////////////////////////////////////////////////////////////////////////////////////////////////////
// エラーをユーザ向けのわかりやすいメッセージに整形する
formatErrorMessage( error ) {
    const raw = error?.message ?? String( error ?? '');
    // fetch のネットワーク／接続エラー（"Failed to fetch" 等）はわかりやすい文言に置き換える
    if ( /failed to fetch|networkerror|network error|load failed/i.test( raw ) ) {
        return getMessage.FTE14266;
    }
    return raw;
}
// ユーザメッセージ
// rewindable : このメッセージを起点に会話を巻き戻せる（＝ユーザが実際に送信した
//   発言）場合に true。true のときだけ、吹き出し右上に操作メニュー（巻き戻し等）を出す。
//   選択肢への回答（tool_result）やシステム通知には出さない。
createUserMessageElement( text, attachments, rewindable = false ) {
    const el = document.createElement('li');
    el.classList.add('aiAssistantChatItem', 'aiAssistantChatUserMessage');
    el.innerHTML = `<div class="aiAssistantChatItemInner aiAssistantChatUserMessageInner"></div>`;

    // 巻き戻し等の操作メニュー（この時点まで会話を戻す）を吹き出しに付ける。
    if ( rewindable ) {
        el.classList.add('aiAssistantChatUserMessageRewindable');
        el.append( this.createMessageMenuElement() );
    }

    const p = document.createElement('p');
    p.innerText = text;
    el.querySelector('.aiAssistantChatItemInner').append( p );

    // 添付ファイルがあれば表示
    if ( Array.isArray( attachments ) && attachments.length ) {
        const inner = el.querySelector('.aiAssistantChatItemInner');
        const list = document.createElement('ul');
        list.classList.add('aiAssistantChatUserMessageFiles');
        attachments.forEach(( file ) => {
            const li = document.createElement('li');
            li.classList.add('aiAssistantChatUserMessageFile');
            // プレビューURLがあれば（ライブ表示中の画像）サムネイルを先頭に表示する。
            // クリックで添付時と同じプレビュー（fn.fileEditor）を開く。
            const previewHtml = file.previewUrl
                ? `<span class="aiAssistantChatUserMessageFilePreview" data-type="attachmentPreview" data-preview-url="${fn.escape( file.previewUrl )}" data-filename="${fn.escape( file.filename ?? '' )}" title="${getMessage.FTE14261}">`
                    + `<img src="${fn.escape( file.previewUrl )}" alt="${fn.escape( file.filename ?? '' )}"></span>`
                : '';
            li.innerHTML = `
                ${previewHtml}
                <span class="aiAssistantChatUserMessageFileName">${fn.escape( file.filename ?? file.file_id ?? '' )}</span>
                <span class="aiAssistantChatUserMessageFileSize">${this.formatFileSize( file.size )}</span>`;
            if ( file.previewUrl ) li.classList.add('aiAssistantChatUserMessageFileHasPreview');
            list.appendChild( li );
        });
        inner.appendChild( list );
    }
    return el;
}
// ユーザメッセージの操作メニュー（吹き出し下側）を生成する。
// アイコンのみの操作ボタンを横並びで並べる（ホバー時に表示）。
// 現状は「この時点まで巻き戻す」のみ。将来的にフォーク等のボタンを追加できる作りにしておく。
createMessageMenuElement() {
    const menu = document.createElement('div');
    menu.classList.add('aiAssistantChatUserMessageMenu');
    // 操作ボタンの定義（今後ここに項目を追加する）。title はホバー時のツールチップ。
    const actions = [
        { type: 'rewindToHere', icon: 'return', title: getMessage.FTE14267 },
    ];
    menu.innerHTML = actions.map(( action ) =>
        fn.html.button( fn.html.icon( action.icon ), 'itaButton aiAssistantChatUserMessageMenuButton popup', { type: action.type, action: 'default', title: action.title })
    ).join('');
    return menu;
}
// システムメッセージ（操作通知）
// ユーザの入力ではなく、システム操作（会話終了など）を区別して表示する。
// 「〜しました」で伝わる短い通知（会話の区切り）に使う。読ませたい内容がある通知は
// システム通知ブロック（createSystemNoticeMessageElement）を使う。
createSystemMessageElement( text ) {
    const el = document.createElement('li');
    el.classList.add('aiAssistantChatItem', 'aiAssistantChatSystemMessage');
    el.innerHTML = `<div class="aiAssistantChatItemInner aiAssistantChatSystemMessageInner"></div>`;

    const p = document.createElement('p');
    p.innerText = text;
    el.querySelector('.aiAssistantChatItemInner').append( p );
    return el;
}
// システム通知ブロック
// 学習事項の登録結果や認証切れの案内など、複数行にわたり内容を読ませたい通知に使う。
// 会話の区切りを示す帯（システムメッセージ）とは別のブロックとして、
// アシスタントメッセージと同じ形の吹き出しをシステム色で表示する。
createSystemNoticeMessageElement( text ) {
    const el = document.createElement('li');
    el.classList.add('aiAssistantChatItem', 'aiAssistantChatSystemNoticeMessage');
    el.innerHTML = `<div class="aiAssistantChatSystemNoticeMessageIcon">${fn.html.icon('circle_info')}</div>`
        + `<div class="aiAssistantChatItemInner aiAssistantChatSystemNoticeMessageInner"></div>`;

    // 改行を含む案内文をそのまま渡されるため、innerTextで改行を活かして表示する。
    const p = document.createElement('p');
    p.innerText = text;
    el.querySelector('.aiAssistantChatItemInner').append( p );
    return el;
}
// 発言時刻を「年 / 月日 / 時刻」の3行スタックで表示する要素を作る。
// iso: ISO文字列（履歴の _timestamp など）。
// ・時刻が無い／不正な場合は null を返し、時刻を表示しない。
//   （タイムスタンプ未保存の古い履歴を復元したとき、現在時刻を誤表示しないため）
createTimestampElement( iso ) {
    if ( typeof iso !== 'string' || !iso ) return null;
    const d = new Date( iso );
    if ( isNaN( d.getTime() ) ) return null;
    const yyyy = d.getFullYear();
    const mm = String( d.getMonth() + 1 ).padStart( 2, '0');
    const dd = String( d.getDate() ).padStart( 2, '0');
    const hh = String( d.getHours() ).padStart( 2, '0');
    const mi = String( d.getMinutes() ).padStart( 2, '0');

    const span = document.createElement('span');
    span.classList.add('aiAssistantChatTime');
    // 機械可読な時刻も保持しておく（後からの再描画・デバッグ用）
    span.dataset.timestamp = d.toISOString();
    // 日付の比較キー。全てのタイムスタンプに持たせておき、次回の判定に使う。
    const dateKey = `${yyyy}-${mm}-${dd}`;
    span.dataset.date = dateKey;
    // 日付行は「最初の1件」と「日付が変わった直後の1件」だけ表示する。
    // 直前に描画済みのタイムスタンプ（＝chatList内で最後の .aiAssistantChatTime）と
    // 日付を比較し、同日なら日付行を省略する。DOMの現状を見るため、
    // 巻き戻しや履歴復元で並びが変わっても正しく判定できる。
    const prevTimeEls = this.elements.chatList?.querySelectorAll('.aiAssistantChatTime');
    const prevTimeEl = prevTimeEls?.length ? prevTimeEls[ prevTimeEls.length - 1 ] : null;
    const showDate = !prevTimeEl || prevTimeEl.dataset.date !== dateKey;
    span.innerHTML = ``
        + ( showDate ? `<span class="aiAssistantChatTimeDate">${mm}/${dd}</span>` : '' )
        + `<span class="aiAssistantChatTimeClock">${hh}:${mi}</span>`;
    return span;
}
// アシスタントメッセージ
createAssistantMessageElement( text, loading = false ) {
    const el = document.createElement('li');
    el.classList.add('aiAssistantChatItem', 'aiAssistantChatAssistantMessage');
    if ( loading ) el.classList.add('aiAssistantChatItemLoading');
    el.innerHTML = `<div class="aiAssistantChatAssistantMessageIcon"></div><div class="aiAssistantChatItemInner aiAssistantChatAssistantMessageInner">${ loading ? this.loadingHtml( text ): ''}</div>`;
    if ( text && loading === false ) {
        const inner = el.querySelector('.aiAssistantChatItemInner');
        inner.innerHTML = this.md.render( text );
        // tableをdiv.table-wrapperで囲む
        inner.querySelectorAll('table').forEach(( table ) => {
            const wrapper = document.createElement('div');
            wrapper.classList.add('table-wrapper');
            table.replaceWith( wrapper );
            wrapper.appendChild( table );
        });
        // コードブロック（pre）の右上に「コピー」「入力欄にセット」ボタンを付与する
        inner.querySelectorAll('pre').forEach(( pre ) => {
            const wrapper = document.createElement('div');
            wrapper.classList.add('aiAssistantChatCodeBlock');
            pre.replaceWith( wrapper );
            wrapper.appendChild( this.createCodeToolbar() );
            wrapper.appendChild( pre );
        });
        // インラインコード（pre配下でないcode）にも同じボタンを付与する（ボタンは枠の外に浮かせる）
        inner.querySelectorAll(':not(pre) > code').forEach(( code ) => {
            const wrapper = document.createElement('span');
            wrapper.classList.add('aiAssistantChatInlineCode');
            code.replaceWith( wrapper );
            wrapper.appendChild( code );
            wrapper.appendChild( this.createCodeToolbar('aiAssistantChatCodeToolbarInline') );
        });
    }
    return el;
}
// コードのツールバー（コピー／入力欄にセット）要素を生成する
createCodeToolbar( extraClass ) {
    const toolbar = document.createElement('div');
    toolbar.classList.add('aiAssistantChatCodeToolbar');
    if ( extraClass ) toolbar.classList.add( extraClass );
    // クリップボードAPIはセキュアコンテキスト（HTTPS等）でのみ利用できるため、その場合だけコピーボタンを表示する
    const copyButton = ( window.isSecureContext && navigator.clipboard )
        ? fn.html.button( fn.html.icon('copy'), 'itaButton aiAssistantChatCodeButton popup', { type: 'codeCopy', action: 'default', title: getMessage.FTE14268 })
        : '';
    toolbar.innerHTML =
        copyButton
        + fn.html.button( fn.html.icon('note'), 'itaButton aiAssistantChatCodeButton popup', { type: 'codeToInput', action: 'default', title: getMessage.FTE14269 });
    // LLMエディタかつextraClassの値がない(aiAssistantChatCodeToolbarInlineではない)場合、コード反映ボタンを表示する
    if( this.promptProfile == 'LLMEditor' && !extraClass) {
        toolbar.innerHTML += fn.html.button( fn.html.icon('circle_check'), 'itaButton aiAssistantChatCodeButton popup', {type: 'codeToEditor', action: 'default', title: getMessage.FTE14390 });
    }

    return toolbar;
}
// コード（ブロック／インライン）のテキストを取得する（ツールバーのボタンから呼び出す）
getCodeBlockText( button ) {
    const block = button.closest('.aiAssistantChatCodeBlock, .aiAssistantChatInlineCode');
    const target = block?.querySelector('pre code') ?? block?.querySelector('code') ?? block?.querySelector('pre');
    return target ? target.textContent : '';
}
// クリップボードへコピーする（コピーボタンはセキュアコンテキストでのみ表示される）
async copyToClipboard( text ) {
    try {
        await navigator.clipboard.writeText( text );
        return true;
    } catch ( error ) {
        console.error('クリップボードへのコピーに失敗しました。', error );
        return false;
    }
}
// ローディングHTML
loadingHtml( text ) {
    return `
    <div class="aiAssistantChatItemNowLoading">
        <div class="aiAssistantChatItemNowLoading-dot aiAssistantChatItemNowLoading-dot-1"></div>
        <div class="aiAssistantChatItemNowLoading-dot aiAssistantChatItemNowLoading-dot-2"></div>
        <div class="aiAssistantChatItemNowLoading-dot aiAssistantChatItemNowLoading-dot-3"></div>
        <div class="aiAssistantChatItemNowLoadingText">${fn.escape(text)}</div>
        <div class="aiAssistantChatItemNowLoading-dot aiAssistantChatItemNowLoading-dot-4"></div>
        <div class="aiAssistantChatItemNowLoading-dot aiAssistantChatItemNowLoading-dot-5"></div>
        <div class="aiAssistantChatItemNowLoading-dot aiAssistantChatItemNowLoading-dot-6"></div>
    </div>`;
}
// ユーザ選択肢
createUserChoiceElement( options ) {
    const el = document.createElement('li');
    el.classList.add('aiAssistantChatItem', 'aiAssistantChatUserChoice');
    el.innerHTML = `<div class="aiAssistantChatItemInner aiAssistantChatUserChoiceInner"></div>`;
    
    const list = document.createElement('ui');
    list.classList.add('aiAssistantChatUserChoiceList');
    // action（positive / negative / other）ごとにボタンの見た目とアイコンを切り替える。
    const choiceStyle = {
        positive: { action: 'positive', icon: 'check' },
        negative: { action: 'negative', icon: 'cross' },
        other:    { action: 'normal',   icon: 'circle' }
    };
    if ( Array.isArray(options) && options.length ) {
        for ( const option of options ) {
            // 旧形式（文字列）／新形式（{ label, action }）の両方を許容する。
            const normalized = this.normalizeChoiceOption( option );
            const style = choiceStyle[ normalized.action ] ?? choiceStyle.other;

            const item = document.createElement('li');
            item.classList.add('aiAssistantChatUserChoiceItem');

            const button = fn.html.iconButton( style.icon, fn.escape( normalized.label ), 'itaButton aiAssistantChatUserChoiceButton', { action: style.action, type: 'choice'});
            item.innerHTML = button;
            list.appendChild(item);
        }
    }

    const note = document.createElement('p');
    note.classList.add('aiAssistantChatUserChoiceNote');
    note.innerText = getMessage.FTE14270;

    el.querySelector('.aiAssistantChatUserChoiceInner').append( list, note );
    return el;
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   チャット
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    チャットエリア初期化
##################################################
*/
initChatArea() {
    this.newChat = false;
    this.elements.chatBody.innerHTML = `<ul class="aiAssistantChatList"></ul>`;
    this.elements.chatList = this.elements.chatBody.querySelector('.aiAssistantChatList');
    this.elements.body.classList.remove('aiAssistantNewChat');
    this.elements.body.classList.add('aiAssistantChatNow');
    this.elements.body.querySelector('.aiAssistantDisclaimerMessage').style.display ='none';
    // 会話中はAI利用設定を変更できない（認証切れの場合のみ開けるようにする）
    this.updateSettingButtonState();
    this.elements.closeChatButton.disabled = false;
}
/*
##################################################
    チャット更新
##################################################
*/
updateChat( message, scroll = true ) {
    // チャットエリア初期化
    if ( this.newChat === true && message.role === 'user') this.initChatArea();

    // 選択肢があれば削除
    const choiceItem = this.elements.chatList.querySelector('.aiAssistantChatUserChoice');
    if ( choiceItem ) choiceItem.remove();

    // 待機中があれば削除（何らかの理由で複数残ることがあるため、すべて消す）
    this.elements.chatList
        .querySelectorAll('.aiAssistantChatItemLoading')
        .forEach(( item ) => item.remove() );

    let el_messege;
    // markdown-it は文字列以外を渡すと例外を投げるため、必ず文字列へ変換する
    let messageText = message.text ?? '';
    if ( typeof messageText !== 'string') {
        messageText = messageText?.message ?? String( messageText );
    }

    switch ( message.role ) {
        // ユーザメッセージ
        case 'user':
            el_messege = this.createUserMessageElement( messageText, message.attachments, message.rewindable === true );
            break;
        // システムメッセージ（操作通知）
        case 'system':
            el_messege = this.createSystemMessageElement( messageText );
            break;
        // システム通知（学習事項の登録結果・認証切れの案内など、内容を読ませる通知）
        case 'systemNotice':
            el_messege = this.createSystemNoticeMessageElement( messageText );
            break;
        // アシスタント待機中（再送などで文言を差し替える場合は message.text を渡す）
        case 'assistantWait':
            el_messege = this.createAssistantMessageElement( messageText || getMessage.FTE14271, true );
            break;
        // ツール実行中
        case 'toolRunning':
            el_messege = this.createAssistantMessageElement( getMessage.FTE14272, true );
            break;
        // アシスタントメッセージ
        case 'assistant':
            el_messege = this.createAssistantMessageElement( messageText );
            break;
        // ユーザ選択肢
        case 'userChoice':
            el_messege = this.createUserChoiceElement( message.options );
            break;

        default:
            console.warn('Unknown role type:', message.role );
    }

    if ( el_messege ) {
        // 巻き戻し起点となるユーザメッセージには、対応する履歴ブロックの位置を持たせる。
        // これを使って「この時点まで巻き戻す」で LLM 履歴を正確に切り詰める。
        // （ライブ送信時は historyIndex が未確定なので、送信側で後から stamp する）
        if ( message.role === 'user' && message.rewindable === true && Number.isInteger( message.historyIndex ) ) {
            el_messege.dataset.historyIndex = String( message.historyIndex );
        }
        // ひとつ前のメッセージもアシスタントの場合は連続クラスを付与
        if ( ['assistantWait', 'toolRunning', 'assistant'].includes( message.role )) {
            const prevItem = this.elements.chatList.lastElementChild;
            if ( prevItem?.classList.contains('aiAssistantChatAssistantMessage') ) {
                el_messege.classList.add('aiAssistantChatAssistantMessageChain');
            }
        }

        // 発言時刻を吹き出しの脇に表示する（ユーザ＝左隣、アシスタント＝右隣）。
        // ライブ時は message.timestamp（送信側で履歴にも保存した値）、
        // 復元時は履歴の _timestamp を渡す。待機中／ツール実行中の吹き出しには付けない。
        if ( ['user', 'assistant'].includes( message.role ) ) {
            const timeEl = this.createTimestampElement( message.timestamp );
            if ( timeEl ) {
                if ( message.role === 'user') {
                    // 右寄せの吹き出しの左隣に出すため、先頭に挿入する
                    el_messege.insertBefore( timeEl, el_messege.firstChild );
                } else {
                    // 左寄せの吹き出しの右隣に出すため、末尾に追加する
                    el_messege.appendChild( timeEl );
                }
            }
        }

        this.elements.chatList.append( el_messege );

        // スクロール
        if ( scroll ) {
            setTimeout( () => {
                this.scrollChatArea( el_messege );
            }, 100 );
        }
    }

    return el_messege;
}
/*
##################################################
    チャットスクロール
##################################################
*/
scrollChatArea( el_message, duration = 500 ) {
    const chatArea = this.elements.bodyInner;
    const startTop = chatArea.scrollTop;
    const targetTop = startTop
        + el_message.getBoundingClientRect().top
        - chatArea.getBoundingClientRect().top
        - 16;
    const distance = targetTop - startTop;

    // 進行中のスクロールアニメーションがあればキャンセル
    if ( this._scrollAnimationId ) cancelAnimationFrame( this._scrollAnimationId );

    const startTime = performance.now();
    // easeInOutQuad
    const easing = ( t ) => t < 0.5 ? 2 * t * t : 1 - Math.pow( -2 * t + 2, 2 ) / 2;

    const step = ( now ) => {
        const elapsed = now - startTime;
        const progress = duration > 0 ? Math.min( elapsed / duration, 1 ) : 1;
        chatArea.scrollTop = startTop + distance * easing( progress );
        if ( progress < 1 ) {
            this._scrollAnimationId = requestAnimationFrame( step );
        } else {
            this._scrollAnimationId = null;
        }
    };
    this._scrollAnimationId = requestAnimationFrame( step );
}
/*
##################################################
    メッセージ送信
##################################################
*/
async sendMessage( message, options = {} ) {
    // -----
    // ユーザメッセージ
    // -----
    // 先頭・末尾のスペースや改行を取り除く
    if ( typeof message === 'string') message = message.trim();
    if ( message === '') return;

    // 画面の吹き出しに表示する文言。指定があれば、LLMへ送る本文（message）とは
    // 別の短い文言を表示する（例：チャット終了時、長い指示文はLLMに送りつつ
    // 吹き出しは短い文言にする）。未指定なら本文をそのまま表示する。
    const displayText = ( typeof options.displayText === 'string' && options.displayText.trim() !== '')
        ? options.displayText
        : message;
    // システム操作（会話終了など）の場合は、ユーザ入力とは別のシステム通知として表示する。
    // LLMの履歴上は通常どおり user ターンだが、画面表示のみ role を分ける。
    const displayRole = ( options.systemAction === true ) ? 'system' : 'user';
    this.elements.body.classList.add('exchangingMessages');
    this.isRunning = true;

    // 通常のユーザメッセージ送信時は「チャット終了」ボタンを再活性化する。
    // （チャット終了操作の直後は無効化されているが、会話を続ける場合は再び閉じられるようにする）
    // システム操作（会話終了）自体の送信では再活性化しない。
    if ( options.systemAction !== true && this.elements.closeChatButton ) {
        this.elements.closeChatButton.disabled = false;
    }

    // 直前に選択肢（ask_user_choice）を出している場合、
    // ボタン選択・自由入力のどちらの回答も、その tool_use に対する tool_result として返す。
    // （tool_use の直後の user ターンは tool_result で始める必要があるため）
    const pendingChoiceToolId = this.pendingChoiceToolId;
    this.pendingChoiceToolId = null;
    // 分裂した余分な選択肢 tool_use の id（代表以外）。これらも tool_result を
    // 返さないと次回送信で未応答 tool_use となり API エラーになるため、まとめて返す。
    const pendingExtraChoiceToolIds = Array.isArray( this.pendingExtraChoiceToolIds ) ? this.pendingExtraChoiceToolIds : [];
    this.pendingExtraChoiceToolIds = [];
    // 選択肢と同じ応答に混在していた通常ツールの tool_result（退避分）。
    // 選択肢の tool_result と同じ user ターンでまとめて返す必要がある。
    const pendingToolResults = Array.isArray( this.pendingToolResults ) ? this.pendingToolResults : [];
    this.pendingToolResults = [];

    // Textareaの値を消す
    this.elements.message.value = '';

    // 発言時刻。画面表示（userMessage.timestamp）と履歴保存（send の options.timestamp）で
    // 同じ値を使い、ライブ表示と再開時表示がずれないようにする。
    const userTimestamp = new Date().toISOString();
    const userMessage = {
        role: displayRole,
        text: displayText,
        timestamp: userTimestamp,
        // 送信前の選択ファイルから表示用のメタ情報を作る
        attachments: ( Array.isArray( this.files ) ? this.files : [] ).map(( item ) => {
            const attachment = {
                filename: item.file.name,
                size: item.file.size,
            };
            // 画像はライブ表示用のプレビューURLを付与する。送信後は clearFile() で
            // ファイル実体が失われるため、実体がここにある間に objectURL を作っておく。
            // （履歴には画像実体を保存しないので、履歴復元時はプレビュー無しで表示される）
            if ( ( item.file.type ?? '').startsWith('image/') ) {
                attachment.previewUrl = URL.createObjectURL( item.file );
                // 新規チャット／復元時に revoke できるよう控えておく。
                if ( !Array.isArray( this._attachmentPreviewUrls ) ) this._attachmentPreviewUrls = [];
                this._attachmentPreviewUrls.push( attachment.previewUrl );
            }
            return attachment;
        }),
    };
    // システム操作（会話終了など）以外のユーザ発言は巻き戻しの起点にできる。
    // 選択肢への回答（tool_result になる）も含めて対象にする。
    // このとき吹き出しに操作メニュー（この時点まで巻き戻す）を表示する。
    // 対応する履歴上の位置（historyIndex）は送信直前に確定するため、後で stamp する。
    const isRewindableUserTurn = ( options.systemAction !== true );
    userMessage.rewindable = isRewindableUserTurn;
    // 中断・エラー時に「このターン全体」を視覚的に区別できるよう、ターン開始要素を保持する
    const turnStartEl = this.updateChat( userMessage );

    // LLMに送るペイロード。
    // 通常はテキスト（message）だが、選択肢への回答時は tool_result として返す。
    let sendPayload = message;
    // tool_result は「直前の assistant メッセージに対応する tool_use が存在する」ことが
    // 必須。停止・エラーでターンが巻き戻されたり履歴が復元・リセットされたりすると、
    // pendingChoiceToolId が指す tool_use が履歴に残っていない場合があり、その状態で
    // tool_result を送ると ValidationException（unexpected tool_use_id）になる。
    // そこで、実際に履歴末尾の assistant に存在する tool_use_id だけを tool_result 化し、
    // 対応が取れないものは破棄してテキスト送信にフォールバックする（自己修復）。
    if ( pendingChoiceToolId ) {
        const lastAssistantToolUseIds = this.getLastAssistantToolUseIds();
        const validChoiceId = lastAssistantToolUseIds.has( pendingChoiceToolId )
            ? pendingChoiceToolId : null;
        // 通常ツール結果（退避分）も、対応 tool_use が履歴に無いものは除外する。
        const validPendingToolResults = pendingToolResults.filter(
            ( r ) => r && lastAssistantToolUseIds.has( r.tool_use_id )
        );
        const validExtraIds = pendingExtraChoiceToolIds.filter(
            ( id ) => lastAssistantToolUseIds.has( id )
        );

        if ( validChoiceId ) {
            // 選択肢と同じ応答で先に実行済みの通常ツール結果（退避分）を先頭に置き、
            // 続けて選択肢への回答を tool_result として返す。
            // （tool_use の直後の user ターンは、その応答に含まれる全 tool_use 分の
            //   tool_result を含む必要があるため、まとめて1メッセージで送る）
            sendPayload = [
                ...validPendingToolResults,
                {
                    type: 'tool_result',
                    tool_use_id: validChoiceId,
                    content: message,
                },
                // 分裂した余分な選択肢 tool_use にも空応答を返し、未応答を防ぐ。
                ...validExtraIds.map(( id ) => ({
                    type: 'tool_result',
                    tool_use_id: id,
                    content: getMessage.FTE14273,
                })),
            ];
        } else {
            // 対応する tool_use が履歴に見当たらない（巻き戻し・復元ズレ等）。
            // tool_result は送れないため、通常のテキストメッセージとして送る。
            console.warn('pendingChoiceToolId に対応する tool_use が履歴末尾に見つからないため、tool_result 送信を取りやめてテキスト送信にフォールバックします。', pendingChoiceToolId );
            sendPayload = message;
        }
    }

    // -----
    // ファイルアップロード（送信時に並列でアップロード）
    // -----
    let uploadedFiles = [];
    if ( Array.isArray( this.files ) && this.files.length ) {
        // ファイル処理中ダイアログ
        let process = fn.processingModal( getMessage.FTE14274 );

        // ファイルはすべてアップロードする
        const items = this.files.slice();
        try {
            const results = await Promise.all(
                items.map(( item ) => this.fileUploader( item.file ).catch(( error ) => {
                    // どのファイルで失敗したのかが分かるようにファイル名を添える
                    throw new Error(`${item.file?.name ?? ''}：${this.formatErrorMessage( error )}`);
                }) )
            );
            // アップロード結果にLLM送信フラグを付与
            // useLlm : true ならファイルの実体（base64）も渡す
            uploadedFiles = await Promise.all( items.map( async ( item, i ) => {
                const mimeType = item.file.type ?? '';
                // supported : LLMがネイティブに中身を解析できる形式か（解析オフでも判定して渡す）
                const supported = this.isLlmSupportedFile( item.file );
                const entry = { ...results[ i ], useLlm: item.useLlm, mimeType, supported };
                // 解析オン かつ 対応形式のときだけファイルの実体を渡す
                if ( item.useLlm && supported ) {
                    if ( this.isTextFile( item.file ) ) {
                        // テキストファイルは生テキストで渡す
                        entry.text = await this.fileToText( item.file );
                    } else {
                        // それ以外はbase64で渡す
                        entry.data = await this.fileToBase64( item.file );
                    }
                }
                return entry;
            }));
        } catch ( error ) {
            console.error( error );
            // 失敗しても処理中ダイアログは必ず閉じる（開いたままだと操作できなくなる）
            process.close();
            // 複数添付の一部だけ登録済みになる場合があるが、登録されたファイルはfile_idを
            // 使わなければ参照されないため、そのままにして送信のみ中止する。
            alert( getMessage.FTE14275( this.formatErrorMessage( error ) ) );
            this.isRunning = false;
            return;
        }
        // 送信したファイルはクリア
        this.clearFile();
        await this.sleep( 500 );

        // ダイアログを消す
        process.close();
    } else {
        await this.sleep( 500 );
    }

    // -----
    // アシスタントメッセージ（応答ループ）
    // -----
    // 応答ループは _runResponseLoop に切り出し、通常送信と「中断後の自動継続」で共用する。
    await this._runResponseLoop({
        sendPayload,
        uploadedFiles,
        turnStartEl,
        isRewindableUserTurn,
        // 最初のユーザターンにだけ渡す表示情報（displayText / systemAction / timestamp）
        firstSendOptions: { displayText: options.displayText, systemAction: options.systemAction, timestamp: userTimestamp },
        // 停止・エラー時に復元する、ターン開始前の保留状態
        savedPending: { pendingChoiceToolId, pendingExtraChoiceToolIds, pendingToolResults },
    });
}
/*
##################################################
    応答ループ
##################################################
*/
// ツール実行が「長い」と見なすまでの待ち時間（ミリ秒）。
// tool_use を含む応答の中断耐性保存（_runResponseLoop）を、この時間だけ遅らせて投げる。
// すぐに返るツール（参照系など）では、続く継続送信が同じ内容を保存するため保存が無駄になる。
static get toolUseSaveDelay() {
    return 1500;
}
// LLMへの送信 → 応答（テキスト／ツール呼び出し）処理 → ツール実行 → 結果を返して再送、を
// 繰り返す中核ループ。通常のメッセージ送信（sendMessage）と、ページ離脱で中断された会話の
// 自動継続（_continueInterrupted）で共用する。
// ctx:
//   sendPayload         : 最初の送信ペイロード（テキスト / tool_result 配列 / 継続時は null）
//   uploadedFiles       : 最初のユーザターンで渡す添付（継続時は空）
//   turnStartEl         : このターンのユーザ発言要素（中断ターンの視覚区別用。継続時は null）
//   isRewindableUserTurn: 巻き戻し起点にできるユーザターンか
//   firstSendOptions    : 最初の送信に渡す表示情報（displayText / systemAction / timestamp）
//   savedPending        : 停止・エラー時に復元する保留状態（pendingChoiceToolId 等）
//   continuation        : true の場合、最初の送信は「継続」（新規 user を積まず alreadyPushed で送る）
// 応答テキストに混ざった「ツール呼び出しの生タグ」を見つけるためのパターン。
// モデルのフォーマット崩れは <invoke name="..."> の形だけではなく、
//   ・先頭の "<" が落ちて antml:invoke name="..." だけが残る
//   ・<invoke> が無く <parameter name="...">...</parameter> の羅列だけになる
//   ・<function_calls> の囲みだけが漏れる
// といった形にもなるため、断片のどれかを見つけたら崩れと見なす。
static get rawToolCallMarkupPatterns() {
    return [
        // <invoke …> / </invoke> / <function_calls> といったタグ形式の断片
        /<\s*\/?\s*(?:antml:)?(?:invoke|function_calls)\b/i,
        // <parameter name="…"> / </parameter>（name 属性か閉じタグの形に限り、通常の文章と紛れないようにする）
        /<\s*\/?\s*(?:antml:)?parameter(?:\s+name\s*=|\s*\/?>)/i,
        // "<" が落ちて antml: 付きの名前だけが残った形
        /\bantml:(?:invoke|function_calls|parameter)\b/i
    ];
}
// 応答のテキストブロックがツール呼び出しの生タグを含んでいるか（＝フォーマット崩れか）を判定する。
_hasRawToolCallMarkup( text ) {
    const value = String( text ?? '');
    if ( !value ) return false;
    if ( AiAssistantChat.rawToolCallMarkupPatterns.some(( pattern ) => pattern.test( value )) ) return true;
    // タグの "<" がすべて落ちた形（invoke name="…" と parameter name="…" が並ぶ）も崩れと見なす。
    // どちらか片方だけでは通常の文章と紛れるため、両方が揃っているときだけ検知する。
    return /\binvoke\s+name\s*=\s*["']/i.test( value ) && /\bparameter\s+name\s*=\s*["']/i.test( value );
}
// 使えない応答（フォーマット崩れ・出力上限で途中で切れた等）をLLM履歴から取り除く。
// setChatHistory がサーバー側との「ずれ」をマークするため、次の送信で全置換され、
// 取り除いたターンはサーバー側の履歴からも消える。
_popLastAssistantTurn( llm ) {
    if ( !llm || typeof llm.getChatHistory !== 'function') return;
    const messages = llm.getChatHistory();
    if ( !Array.isArray( messages ) || !messages.length ) return;
    if ( messages[ messages.length - 1 ].role !== 'assistant') return;
    messages.pop();
    if ( typeof llm.setChatHistory === 'function') llm.setChatHistory( messages );
}
async _runResponseLoop( ctx ) {
    let sendPayload = ctx.sendPayload;
    const { uploadedFiles, turnStartEl, isRewindableUserTurn, firstSendOptions, savedPending } = ctx;
    const savedPendingChoiceToolId = savedPending?.pendingChoiceToolId ?? null;
    const savedPendingExtraChoiceToolIds = Array.isArray( savedPending?.pendingExtraChoiceToolIds ) ? savedPending.pendingExtraChoiceToolIds : [];
    const savedPendingToolResults = Array.isArray( savedPending?.pendingToolResults ) ? savedPending.pendingToolResults : [];

    // LLM（AIサービスの会話）を用意する。新規チャット時に作成できていなかった場合
    // （通信エラーなど）も、送信のたびに作成を試みる。
    // 用意できない場合はターンを開始せず、エラーだけを表示して戻る。
    let llm = null;
    try {
        llm = await this.ensureLlm();
        if ( !llm ) throw new Error( getMessage.FTE14276 );
    } catch ( error ) {
        console.error( error );
        const errorMessage = this.formatErrorMessage( error );
        alert( errorMessage );
        this.updateChat({ role: 'assistant', text: errorMessage });
        this.isRunning = false;
        this.elements.body.classList.remove('exchangingMessages');
        return;
    }
    // フッターで切り替えたモデル（this.modelId）を、このターンの問い合わせから使う
    llm.setModel( this.modelId );

    // 実行中フラグ・表示・離脱再開マーカーをセット（自動継続の入口でも確実に立てる）
    this.isRunning = true;
    this.elements.body.classList.add('exchangingMessages');
    this._writeActiveChat( true );

    const maxAttempts = 100; // 最大試行回数
    let maxAttemptsFlag = true;
    let errorFlag = false;
    let stoppedFlag = false;
    // 長文脈でモデルがツール呼び出しを tool_use ではなくテキスト内の生の <invoke> として
    // 出力してしまうこと（フォーマット崩れ）への再送カウンタ。無限ループ防止のため上限を設ける。
    let invalidToolFormatRetries = 0;
    const maxInvalidToolFormatRetries = 5;
    // 1回の応答の出力上限（プラットフォーム側の max_tokens）に達して応答が途中で切れたときの
    // 再送カウンタ。分割して出力し直すよう促して再送する（無限ループ防止のため上限を設ける）。
    let maxTokensRetries = 0;
    const maxMaxTokensRetries = 2;
    // 再送時の待機表示に出す文言。処理が止まったように見せないため、
    // 次のループ先頭の待機スピナーへ「再試行中」である旨を伝える。null のときは通常の「思考中」。
    let waitMessage = null;
    // 停止時に巻き戻すためのLLM履歴チェックポイント（今回のターン開始前の件数）
    const historyCheckpoint = ( llm?.getChatHistory()?.length ) ?? 0;
    // 巻き戻し起点となるユーザ発言の吹き出しに、対応する履歴ブロックの位置を stamp する。
    // send() はこのターンの user メッセージを historyCheckpoint の位置に push するため、
    // その index を持たせておけば「この時点まで巻き戻す」で履歴を正確に切り詰められる。
    if ( isRewindableUserTurn && turnStartEl ) {
        turnStartEl.dataset.historyIndex = String( historyCheckpoint );
    }
    this._sendController = new AbortController();
    const { signal } = this._sendController;
    // 最初の送信を「継続」（新規 user を積まず、既存履歴末尾へ alreadyPushed で送る）にするか。
    // 中断後の自動継続や、ツール結果を先に履歴へ確定させた後の再送で true になる。
    let alreadyPushedNext = ( ctx.continuation === true );
    for ( let i = 0; i < maxAttempts; i++ ) {
        // アシスタント待機中表示（再送中は文言を差し替えて「再試行中」であることを伝える）
        this.updateChat({ role: 'assistantWait', text: waitMessage });
        waitMessage = null;

        // この回の送信を継続送信（再push抑止）にするか
        const alreadyPushed = alreadyPushedNext;
        alreadyPushedNext = false;

        // LLMにメッセージ送信（ファイルは初回のユーザメッセージ時のみ渡す）
        if ( signal.aborted ) {
            stoppedFlag = true;
            maxAttemptsFlag = false;
            break;
        }
        // 継続送信（alreadyPushed）時は、ペイロードは既に履歴へ積まれているのでファイル・表示情報は渡さない。
        const sendFiles = ( i === 0 && !alreadyPushed ) ? uploadedFiles : null;
        // 表示用の別文言（_displayText）や表示種別（_displaySystem）、発言時刻（timestamp）は、
        // 最初のユーザターンにだけ持たせる（再送・是正ターンのペイロードには付けない）。
        // timestamp は画面表示と履歴を一致させるため常に渡す（displayText/systemAction は
        // 送信側で有効値のみ採用されるので、そのまま渡して問題ない）。
        const sendOptions = ( i === 0 && !alreadyPushed ) ? firstSendOptions : undefined;
        let response;
        try {
            response = await llm.send( sendPayload, sendFiles, signal, { ...( sendOptions || {} ), alreadyPushed } );
        } catch ( error ) {
            // ユーザ都合の停止（AbortError）はエラー扱いしない
            if ( error?.name === 'AbortError' || signal.aborted ) {
                stoppedFlag = true;
                maxAttemptsFlag = false;
                break;
            }
            const errorMessage = this.formatErrorMessage( error );
            alert( errorMessage );
            errorFlag = true;
            maxAttemptsFlag = false;
            this.updateChat({
                role: 'assistant',
                text: errorMessage
            });
            break;
        }

        // 会話ID（履歴の保存先）は最初の送信で確定するため、中断再開マーカーへ書き戻す。
        // これで、ツールを使わない応答の途中でページを閉じても、この会話IDから自動再開できる。
        this._writeActiveChat( true );

        // 1回の応答が出力上限（プラットフォーム側の max_tokens）に達して途中で切れた。
        // グラフィカルなレポート（display_html に長いHTMLを渡す）などで起こりやすい。
        // 途中で切れた応答は使えない（tool_use なら引数のJSONが不完全、テキストなら文章が途切れる）ため、
        // その assistant ターンを履歴から取り除き、分割して出力し直すよう促して再送する。
        if ( response.stop_reason === 'max_tokens') {
            const truncatedToolUse = ( response.content ?? [] ).some(( block ) => block.type === 'tool_use');
            // 不完全なターンを履歴に残すと、次の送信で「引数が壊れた tool_use」や
            // 「tool_result の無い tool_use」としてエラーになるため必ず取り除く。
            this._popLastAssistantTurn( llm );
            if ( maxTokensRetries < maxMaxTokensRetries ) {
                maxTokensRetries++;
                console.warn(`応答が出力上限に達して切れました。分割出力を促して再送します（${maxTokensRetries}/${maxMaxTokensRetries}）。`);
                waitMessage = getMessage.FTE14277( maxTokensRetries, maxMaxTokensRetries );
                sendPayload = ( truncatedToolUse )
                    ? getMessage.FTE14278
                    : getMessage.FTE14279;
                continue;
            }
            // 再送上限に達した：ユーザに状況と対処を伝えてループを終了する。
            console.error('応答の出力上限（max_tokens）が規定回を超えて解消しませんでした。');
            const overMessage = getMessage.FTE14280;
            alert( overMessage );
            this.updateChat({ role: 'assistant', text: overMessage });
            maxAttemptsFlag = false;
            errorFlag = true;
            break;
        }

        // 長文脈になるとモデルが本来 tool_use（構造化ツール呼び出し）で出すべきものを、
        // text ブロック内に生の <invoke name="..."> として書いてしまうことがある（フォーマット崩れ）。
        // このまま表示するとユーザにタグが露出し、ツールも実行されない（選択肢も出ない）。
        // 崩れ方は <invoke> の形に限らず、"<" が落ちた antml:invoke や <parameter name="..."> の
        // 羅列だけのこともあるため、_hasRawToolCallMarkup でいずれの断片も検知する。
        // 検知したら、その応答は表示・実行せずに履歴からこのターンの assistant を巻き戻し、
        // 是正指示を添えて同じ入力で再送する（＝再処理）。
        const hasRawInvokeInText = ( response.content ?? [] ).some(
            ( block ) => block.type === 'text' && this._hasRawToolCallMarkup( block.text )
        );
        if ( hasRawInvokeInText ) {
            // モデルが吐いた壊れた assistant ターンを履歴から除去（次回送信の整合性維持）。
            this._popLastAssistantTurn( llm );
            if ( invalidToolFormatRetries < maxInvalidToolFormatRetries ) {
                invalidToolFormatRetries++;
                console.warn(`ツール呼び出しがテキスト内の生タグ（<invoke> / <parameter> 等）として出力されました。tool_use での再出力を促して再送します（${invalidToolFormatRetries}/${maxInvalidToolFormatRetries}）。`);
                // 処理が止まったように見えないよう、次の待機表示で再試行中である旨を画面に出す。
                waitMessage = getMessage.FTE14281( invalidToolFormatRetries, maxInvalidToolFormatRetries );
                // 是正指示を user メッセージとして返し、tool_use 機能での呼び出し直しを促す。
                sendPayload = getMessage.FTE14282;
                continue;
            }
            // 再送上限に達した：ユーザに状況を伝えてループを終了する（壊れたタグは表示しない）。
            console.error('ツール呼び出しのテキスト出力が規定回を超えて解消しませんでした。');
            this.updateChat({
                role: 'assistant',
                text: getMessage.FTE14283
            });
            errorFlag = true;
            maxAttemptsFlag = false;
            break;
        }

        // 応答に含まれる選択肢（ask_user_choice）の tool_use を、内容を処理する前に先に検査する。
        // options が文字列化していたり、label/action が options の外に漏れていたり、
        // 1応答に複数の選択肢 tool_use が分裂して出ている等のフォーマット崩れを検知したら、
        // その応答は表示・処理せずに履歴からこのターンの assistant を巻き戻し、
        // 正しい形式での呼び出し直しを促して再送する（＝ <invoke> テキスト崩れと同じ扱い）。
        const choiceToolBlocks = ( response.content ?? [] ).filter(
            ( block ) => block.type === 'tool_use' && this.isUiChoiceTool( block.name )
        );
        if ( choiceToolBlocks.length && this.isChoiceResponseMalformed( choiceToolBlocks ) ) {
            if ( invalidToolFormatRetries < maxInvalidToolFormatRetries ) {
                // モデルが吐いた壊れた assistant ターンを履歴から除去（次回送信の整合性維持）。
                this._popLastAssistantTurn( llm );
                invalidToolFormatRetries++;
                console.warn(`ask_user_choice のパラメータ形式が崩れていました。正しい形式での再出力を促して再送します（${invalidToolFormatRetries}/${maxInvalidToolFormatRetries}）。`);
                // 処理が止まったように見えないよう、次の待機表示で再試行中である旨を画面に出す。
                waitMessage = getMessage.FTE14281( invalidToolFormatRetries, maxInvalidToolFormatRetries );
                // 是正指示を user メッセージとして返し、正しい形式での呼び出し直しを促す。
                sendPayload = getMessage.FTE14284;
                continue;
            }
            // 再送上限に達した：可能な範囲で救済（mergeChoiceBlocks）して表示し、行き止まりを避ける。
            console.warn('ask_user_choice のフォーマット崩れが規定回を超えて解消しませんでした。可能な範囲で救済して表示します。');
        }

        // 中断耐性：この応答が tool_use を含む場合、ツール実行の最中にページを閉じても「呼び出したこと」が
        // 履歴に残るようサーバへ保存する。これで再開時に同じ操作を再実行せず状況を確認できる
        // （未応答 tool_use は再開時にプレースホルダで整合を取る）。テキストのみの応答は
        // ツール結果保存／完了時保存でカバーされるため省く。
        //
        // ただし、すぐに返るツール（参照系など）ではこの保存は無駄になる。ツール結果を返す継続送信が
        // 同じ内容を含む履歴を全置換で保存するため、数百msの窓を守るために会話全体をもう1往復
        // 送っていることになる。そこで即時ではなくタイマーで投げ、実行が長引いたツール
        // （ドライバー実行など）のときだけ保存する。
        // 保存はキュー化・版管理された非同期処理のため、ここでは待たずに投げる（会話速度に影響しない）。
        const responseHasToolUse = ( response.content ?? [] ).some(( block ) => block.type === 'tool_use' );
        let toolUseSaveTimer = null;
        if ( responseHasToolUse ) {
            toolUseSaveTimer = setTimeout( () => {
                toolUseSaveTimer = null;
                this._enqueueHistorySafe();
            }, AiAssistantChat.toolUseSaveDelay );
        }

        const toolsResult = [];
        // 選択肢（ask_user_choice）の tool_use は、まとめて後段で処理する。
        // フォーマット崩れで1応答に複数の選択肢 tool_use が出ることがあるため、
        // ここで一旦集めておき、1つの選択肢UIへ統合する（下の mergeChoiceBlocks）。
        const choiceBlocks = [];
        for ( const block of response.content ?? [] ) {
            switch ( block.type ) {
                case 'text':
                    this.updateChat({
                        role: 'assistant',
                        text: block.text,
                        // 送信側（send）が履歴に付けた応答時刻と同じ値を表示に使う
                        timestamp: response._timestamp
                    });
                    break;

                case 'tool_use':
                    if ( !this.uiTools.includes( block.name ) ) {
                        const toolRunningEl = this.updateChat({ role: 'toolRunning'});
                        try {
                            // signal を渡し、停止時は MCP fetch / 進捗ポーリングごと中断する
                            const toolResult = await this.executeTool( block, toolRunningEl, signal );
                            toolsResult.push( toolResult );
                        } catch ( error ) {
                            // ユーザ都合の停止（AbortError）はエラー扱いせず、ターンを巻き戻す
                            if ( error?.name === 'AbortError' || signal.aborted ) {
                                stoppedFlag = true;
                            } else {
                                const errorMessage = this.formatErrorMessage( error );
                                alert( errorMessage );
                                errorFlag = true;
                                this.updateChat({ role: 'assistant', text: errorMessage });
                            }
                            maxAttemptsFlag = false;
                        }
                    } else if ( this.isUiChoiceTool( block.name ) ) {
                        // ユーザ選択肢は集約して後でまとめて処理する
                        choiceBlocks.push( block );
                    } else {
                        // 即時実行の画面専用ツール（display_html 等）。
                        // 画面に表示し、LLMには結果（表示した旨）だけを tool_result で返す。
                        const uiToolResult = this.uiTool( block.name )?.execute( block );
                        if ( uiToolResult ) toolsResult.push( uiToolResult );
                    }
                    break;

                case 'thinking':
                    // 何もしない
                    break;

                default:
                    console.warn('Unknown content type:', block.type );
                    break;
            }
            // 停止・エラーが発生したら残りのブロック処理を打ち切る
            if ( stoppedFlag || errorFlag ) break;
        }

        // ツール実行フェーズを抜けたので、中断耐性の遅延保存は取り消す。
        // まだ発火していなければ（＝ツールが早く返った）保存しない。この応答は続く継続送信の
        // 全置換、または完了時保存でサーバー側へ渡るため、ここで保存しなくても失われない。
        if ( toolUseSaveTimer !== null ) {
            clearTimeout( toolUseSaveTimer );
            toolUseSaveTimer = null;
        }

        // 停止・エラー時はループを抜けて後段の巻き戻し処理へ
        if ( stoppedFlag || errorFlag ) break;

        // 集約した選択肢 tool_use を1つの選択肢UIに統合して表示する。
        // （分裂した複数 tool_use を1つにまとめ、代表以外の tool_use_id は
        //   未応答にならないよう pendingExtraChoiceToolIds へ退避する）
        if ( choiceBlocks.length ) {
            this.askUserChoice( this.mergeChoiceBlocks( choiceBlocks ) );
        }

        // 応答に選択肢（ask_user_choice）が含まれていた場合は、ユーザーの回答を待つ。
        // このとき、同じ応答に通常ツールも混在していた（＝ toolsResult がある）ら、
        // その tool_result を自動継続で送ってしまうと、選択肢の tool_use が
        // tool_result 未応答のまま送信され API エラー（ValidationException）になる。
        // そこで通常ツールの結果はバッファに退避し、ユーザーが選択肢に回答したときに
        // 選択肢の tool_result とまとめて返す。
        if ( this.pendingChoiceToolId ) {
            this.pendingToolResults = toolsResult;
            // 選択待ちで一旦ユーザに制御が戻るため、ここまでに更新されたページのリンクを表示する。
            this.renderUpdatedMenuLinks();
            maxAttemptsFlag = false;
            break;
        }

        // ツール結果があればLLMに返す
        if ( toolsResult.length ) {
            // ツール結果を送信を待たずに履歴へ確定させる。
            // これにより、この後のLLM呼び出し中にページを閉じても「実行済みの操作とその結果」が失われず、
            // 再開時は整合した履歴（tool_use と tool_result が対）から続きを継続できる。
            // （tool_result は message で送れないため、続く継続送信が履歴を全置換して保存する）
            llm.appendToolResults( toolsResult );
            // 次回送信は継続送信（履歴末尾の tool_result をそのままLLMへ）。ペイロードの再pushはしない。
            sendPayload = null;
            alreadyPushedNext = true;
        } else {
            maxAttemptsFlag = false;
            break;
        }
    }

    if ( stoppedFlag || errorFlag ) {
        // ユーザ都合の停止、またはLLM／ツール実行のエラー：
        //   ・待機中／ツール実行中インジケータを消す
        //   ・LLM履歴を今回のターン開始前まで巻き戻す
        //     （ユーザメッセージ／tool_result 未応答の tool_use が残ると次回送信で API エラーになるため。
        //       500エラー時は send() 側で tool_result 入り user のみ pop され、未応答 tool_use を持つ
        //       assistant が履歴末尾に残るため、ここでターンごと巻き戻して整合性を保つ）
        //   ・履歴保存はしない
        this.elements.chatList
            ?.querySelectorAll('.aiAssistantChatItemLoading')
            .forEach(( item ) => item.remove() );

        if ( llm && typeof llm.getChatHistory === 'function' ) {
            const messages = llm.getChatHistory();
            if ( Array.isArray( messages ) && messages.length > historyCheckpoint ) {
                messages.length = historyCheckpoint;
                if ( typeof llm.setChatHistory === 'function' ) llm.setChatHistory( messages );
            }
        }

        // 選択肢への回答中に停止・エラーが起きた場合、直前の tool_use が tool_result 未応答のまま残る。
        // 次回送信で tool_result として返せるよう pendingChoiceToolId を復元する。
        // 同じ応答に混在していた通常ツールの結果（退避分）も、次回送信で選択肢の
        // tool_result とまとめて返せるよう合わせて復元する（片方だけ残すと未応答 tool_use になる）。
        if ( savedPendingChoiceToolId ) {
            this.pendingChoiceToolId = savedPendingChoiceToolId;
            this.pendingToolResults = savedPendingToolResults;
            this.pendingExtraChoiceToolIds = savedPendingExtraChoiceToolIds;
        }

        // このターンで表示された吹き出し（ユーザ発言～以降のAI/ツール）はすべて履歴から
        // 巻き戻されており「生きていない」ため、専用クラスで視覚的に区別する。
        this.markTurnAborted( turnStartEl );

        // 送信済みユーザメッセージのバブルに停止ラベルを付与
        this.markLastUserMessageStopped();

        // ターンを巻き戻したため、控えていた更新メニューのリンクは表示しない。
        // （ITA側の更新自体は取り消せないが、中断ターンの吹き出しとして出すのは紛らわしいため）
        this._turnUpdatedMenus = new Map();
    } else if ( maxAttemptsFlag ) {
        alert( getMessage.FTE14285 );
        console.log('LLMからの応答が規定回を超えました。ループを終了します。');
    } else {
        // 応答が正常に完了した。更新された ITA ページへのリンクをまとめて表示する。
        this.renderUpdatedMenuLinks();
        // 履歴登録（非同期）。保存失敗が未処理の Promise 拒否にならないよう安全ラッパーで投げる。
        //
        // サーバー側の履歴が画面側と一致している（llm.serverSynced＝messageを指定した問い合わせで、
        // ユーザーターンとAI応答がプラットフォーム側に保存された）場合は保存しない。
        // テキストだけのやりとりでは、これで履歴の全置換が1回も起きなくなる。
        // ただし completions は問い合わせのたびにスナップショットを1レコード追加するため、溜めたままだと
        // 保存済みレコードが増えて復元時の取得が重くなる。一定数を超えたら全置換して1レコードへ圧縮する。
        if ( !errorFlag && ( !llm.serverSynced || llm.needsCompaction() ) ) {
            this._enqueueHistorySafe();
        }
    }

    // 応答完了
    this.isRunning = false;
    this.elements.body.classList.remove('exchangingMessages');
    // 実行が終わったので離脱再開マーカーを「実行中でない」に更新する。
    // （正常完了・停止・エラーいずれもここを通るため、次回読込で誤って自動再開しない）
    this._writeActiveChat( false );

    // エラーで終わった場合は、原因が認証切れでないかを確認する（認証情報の有効期限は
    // 会話の途中でも切れる）。切れていた場合は会話中でも設定を開けるようにして更新を促す。
    // 実行中フラグを解除したあとに行い、確認の通信で操作が止まらないようにする。
    if ( errorFlag ) await this.checkAuthAfterError();
    return;
}
// 停止メソッド
stopMessage() {
    this._sendController?.abort();
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Movement
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    ドライバー実行進捗
##################################################
*/
// 専用の実行画面（Movementノード）を持つドライバー実行ツールの一覧
static DRIVER_TOOLS = ['execute-driver', 'dry-run-driver'];
// execute-driver / dryrun-driver の結果から execution_no を取り出し、
// 進捗を購読して実行状況をバブルに反映する。完了状態まで待ってから、
// 確定した最終結果（{type, status, result} など）を返す。対象外や取得失敗時は null。
async watchDriverProgress( toolUse, toolResult, runningEl ) {
    if ( !AiAssistantChat.DRIVER_TOOLS.includes( toolUse.name ) ) return null;

    // ローディングclassをremove
    runningEl.classList.remove('aiAssistantChatItemLoading');

    // execution_no を取り出す（result.data.execution_no を想定。ゆらぎに対応）
    const structured = toolResult?.result?.structuredContent ?? {};
    if ( structured.isError === true || toolResult?.result?.isError === true ) return null;
    const apiResult = structured.result ?? {};
    const data = apiResult.data ?? apiResult;
    const executionNo = data?.execution_no ?? '';
    if ( !executionNo ) {
        console.warn('watchDriverProgress: execution_no が取得できませんでした', toolResult );
        return null;
    }

    // 実行メニュー（execution_*）→ ステータス確認メニュー（check_operation_status_*）へ変換
    console.log('toolUse: ', toolUse );
    const execMenu = toolUse.arguments?.menu ?? toolUse.input?.menu ?? '';
    const statusMenu = execMenu.startsWith('execution_')
        ? execMenu.replace(/^execution_/, 'check_operation_status_')
        : execMenu;
    if ( !statusMenu ) {
        console.warn('watchDriverProgress: ステータス確認メニューを導出できませんでした', execMenu );
        return null;
    }
    const movementName = toolUse.arguments?.movement_name ?? toolUse.input?.movement_name ?? '';
    const operationName = toolUse.arguments?.operation_name ?? toolUse.input?.operation_name ?? '';
    const execListMenu = this.drivers?.[ statusMenu ]?.executionListMenu ?? '';

    // Movement HTML
    const movement = this.movementElement( statusMenu, execListMenu, movementName, operationName, executionNo );
    runningEl.querySelector('.aiAssistantChatAssistantMessageInner').replaceChildren( movement );

    try {
        return await this.pollDriverStatus( statusMenu, executionNo, runningEl );
    } catch ( error ) {
        console.warn('watchDriverProgress: 進捗監視でエラー', error );
        return null;
    }
}
// ドライバー実行の終了ステータス（driver-control.md 準拠）
static DRIVER_FINAL_STATES = [
    'Completed',
    'Completed (error)',
    'Unexpected error',
    'Emergency stop',
    'Unexecuted (schedule)',
    'Schedule canceled'
];
// 進捗ポーリング設定
static PROGRESS_POLL_INTERVAL = 5000; // ミリ秒
static PROGRESS_MAX_DURATION = 3600000; // ミリ秒（保険の上限）
// get-driver-status を一定間隔でポーリングして実行状況をバブルに反映する。
// クライアント側で毎回 CommonAuth.getToken() の最新トークンを使って直接叩く。
// 終了状態に達したら { type:'done', status, result } を返す。
pollDriverStatus( menu, executionNo, runningEl ) {
    return new Promise(async ( resolve ) => {
        const { signal } = this._sendController ?? {};
        const interval = AiAssistantChat.PROGRESS_POLL_INTERVAL;
        const maxDuration = AiAssistantChat.PROGRESS_MAX_DURATION;
        let lastStatus = null;
        let elapsed = 0;

        while ( elapsed <= maxDuration ) {
            if ( signal?.aborted ) {
                resolve({ type: 'error', message: getMessage.FTE14286 });
                return;
            }

            let statusResult;
            try {
                const response = await AiAssistantChat.fetchWithRetry( AiAssistantChat.apiUrl.mcp(), {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        // 毎回最新トークンを取得する（長時間監視での401対策）
                        "Authorization": `Bearer ${this.getToken()}`
                    },
                    body: JSON.stringify({
                        jsonrpc: "2.0",
                        id: 1,
                        method: "tools/call",
                        params: {
                            name: 'get-driver-status',
                            arguments: { menu, execution_no: executionNo }
                        }
                    }),
                    signal
                });
                statusResult = await response.json();
            } catch ( error ) {
                if ( error?.name === 'AbortError') {
                    resolve({ type: 'error', message: getMessage.FTE14286 });
                    return;
                }
                console.warn('pollDriverStatus: ステータス取得でエラー', error );
                resolve({ type: 'error', message: fn.jsonStringify( error ) });
                return;
            }

            // ツール自体がエラーを返した場合は監視を打ち切る
            const structured = statusResult?.result?.structuredContent ?? {};
            if ( structured.isError === true || statusResult?.result?.isError === true ) {
                const message = this._extractToolErrorText( statusResult );
                console.warn('pollDriverStatus: get-driver-status がエラー応答', message );
                resolve({ type: 'error', message });
                return;
            }

            // status を含むノードを取得し、そこから status と同階層の result_data も拾う
            const statusNode = this._findDriverStatusNode( structured );
            const status = this._statusFromNode( statusNode );
            const resultDataName = statusNode?.result_data ? `ResultData_${executionNo}.zip`: null;

            // 変化があったときだけ表示更新（初回は必ず反映）
            if ( status && status !== lastStatus ) {
                lastStatus = status;
                this.updateToolProgress( runningEl, status, false, resultDataName );
            }

            // 終了状態なら done を返して終了
            if ( AiAssistantChat.DRIVER_FINAL_STATES.includes( status )) {
                this.updateToolProgress( runningEl, status, true, resultDataName );
                resolve({ type: 'done', status, result: structured.result ?? null });
                return;
            }

            // 停止時は sleep を待たず即座に中断できるよう、signal で待機を打ち切る
            await this.sleepOrAbort( interval, signal );
            elapsed += interval;
        }

        // 上限に達した場合
        this.updateToolProgress( runningEl, getMessage.FTE14287, true );
        resolve({ type: 'timeout', message: 'Progress polling exceeded max duration' });
    });
}
// signal が abort されたら待機を即座に打ち切る sleep（進捗ポーリングの応答性向上用）
sleepOrAbort( time, signal ) {
    return new Promise(( resolve ) => {
        if ( signal?.aborted ) { resolve(); return; }
        const timer = setTimeout(() => {
            signal?.removeEventListener?.('abort', onAbort );
            resolve();
        }, time );
        const onAbort = () => {
            clearTimeout( timer );
            resolve();
        };
        signal?.addEventListener?.('abort', onAbort, { once: true });
    });
}
// get-driver-status で探索する status 系キー（優先順）
static STATUS_KEYS = ['status', 'execution_status', 'operation_status'];
// get-driver-status の structuredContent から status を含むノード（オブジェクト）を探す。
// data.execution_list.parameter.status などネストが深いため再帰探索する（構造のゆらぎに対応）。
// status と同階層の result_data 等も併せて取得したい場合はこのノードから拾う。
_findDriverStatusNode( structured ) {
    const result = structured?.result;
    if ( !result || typeof result !== 'object') return null;

    const search = ( node ) => {
        if ( Array.isArray( node )) {
            for ( const item of node ) {
                const found = search( item );
                if ( found ) return found;
            }
            return null;
        }
        if ( node && typeof node === 'object') {
            // status系キーを持つノードを優先
            for ( const key of AiAssistantChat.STATUS_KEYS ) {
                if ( typeof node[ key ] === 'string' && node[ key ]) return node;
            }
            for ( const val of Object.values( node )) {
                const found = search( val );
                if ( found ) return found;
            }
        }
        return null;
    };
    return search( result );
}
// ノードから status 系キーの値を取り出す。
_statusFromNode( node ) {
    if ( !node || typeof node !== 'object') return '';
    for ( const key of AiAssistantChat.STATUS_KEYS ) {
        if ( typeof node[ key ] === 'string' && node[ key ]) return node[ key ];
    }
    return '';
}
// get-driver-status の structuredContent から status 文字列を取り出す。
_extractDriverStatus( structured ) {
    return this._statusFromNode( this._findDriverStatusNode( structured ));
}
// tool_result のエラーテキストを取り出す（表示・ログ用）
_extractToolErrorText( statusResult ) {
    const content = statusResult?.result?.content;
    if ( Array.isArray( content )) {
        const text = content.find(( c ) => c.type === 'text')?.text;
        if ( text ) return text;
    }
    const structured = statusResult?.result?.structuredContent ?? {};
    return structured.error ?? statusResult?.error?.message ?? getMessage.FTE14288;
}
// 進捗バブルの表示を更新する
updateToolProgress( runningEl, statusText, done, resultDataName ) {
    if ( !runningEl ) return;

    const movementAreaEl = runningEl.querySelector('.movementArea');
    const nodeEl = runningEl.querySelector('.node');
    const emergencyStopButton = runningEl.querySelector('.movementEmergencyStopButton');
    const statusCheckButton = runningEl.querySelector('.movementStatusCheckButton');
    const resultDownloadButton = runningEl.querySelector('.movementResultDownloadButton');
    if ( nodeEl ) {
        statusCheckButton.disabled = false;
        switch ( statusText ) {
            // 準備中
            case 'Preparing':
                movementAreaEl.setAttribute('data-result', 'ready');
                nodeEl.classList.add('ready'); break;
            // 実行中
            case 'Executing':
                movementAreaEl.setAttribute('data-result', 'running');
                emergencyStopButton.disabled = false;
                nodeEl.classList.add('running'); break;
            // 完了
            case 'Completed':
                emergencyStopButton.disabled = true;
                movementAreaEl.setAttribute('data-result', 'done');
                nodeEl.querySelector('.node-result').setAttribute('data-result-text', 'DONE');
                nodeEl.classList.add('complete'); break;
            // エラー
            case 'Completed (error)':
            case 'Unexpected error':
                emergencyStopButton.disabled = true;
                movementAreaEl.setAttribute('data-result', 'error');
                nodeEl.querySelector('.node-result').setAttribute('data-result-text', 'ERROR');
                nodeEl.classList.add('complete'); break;
            // 緊急停止
            case 'Emergency stop':
                emergencyStopButton.disabled = true;
                movementAreaEl.setAttribute('data-result', 'stop');
                nodeEl.querySelector('.node-result').setAttribute('data-result-text', 'STOP');
                nodeEl.classList.add('complete'); break;
            default:
        }

        // 結果データ
        if ( resultDataName ) {
            resultDownloadButton.setAttribute('data-filename', resultDataName );
            resultDownloadButton.disabled = false;
        } else {
            resultDownloadButton.setAttribute('data-filename', '');
            resultDownloadButton.disabled = true;
        }
    }
}
// Movement HTML
movementElement( statusMenu, execListMenu, movementName, operationName, executionNo ) {
    const menu = {
        Main: [
            { html: {
                    // 作業状態確認
                    html: fn.html.iconButton(
                        'note',
                        getMessage.FTE14289,
                        'itaButton operationMenuButton movementStatusCheckButton',
                        {
                            type: 'movementStatusCheck',
                            action: 'default',
                            disabled: true,
                            'execution-no': executionNo,
                            'status-menu': statusMenu
                        }
                    )
                }
            },
            { html: {
                    // 結果データ
                    html: fn.html.iconButton(
                        'download',
                        getMessage.FTE14290,
                        'itaButton operationMenuButton movementResultDownloadButton',
                        {
                            type: 'movementResultDownload',
                            action: 'default',
                            disabled: true,
                            'execution-no': executionNo,
                            'exec-list-menu': execListMenu
                        }
                    )
                }
            }
        ],
        Sub: [
            { html: {
                    // 緊急停止
                    html: fn.html.iconButton(
                        'stop',
                        getMessage.FTE05004,
                        'itaButton operationMenuButton movementEmergencyStopButton',
                        {
                            type: 'movementEmergencyStop',
                            action: 'danger',
                            disabled: true,
                            'execution-no': executionNo,
                            'status-menu': statusMenu
                        }
                    )
                }
            }
        ]
    };
    const movement = document.createElement('div');
    movement.innerHTML = `
    ${fn.html.operationMenu( menu )}
    <div class="movementArea" data-result="">
        <div class="movementAreaInner">
            <div class="node ${this.drivers[statusMenu]?.movementClassName} operation">
                <div class="node-main">
                    <div class="node-terminal node-in connected">
                        <span class="connect-mark"></span>
                        <span class="hole">
                            <span class="hole-inner"></span>
                        </span>
                    </div>
                    <div class="node-body">
                        <div class="node-circle">
                            <span class="node-gem">
                                <span class="node-gem-inner">${this.drivers[statusMenu]?.movementGem}</span>
                            </span>
                            <span class="node-running"></span>
                            <span class="node-result node-jump popup darkPopup" title="${getMessage.FTE14289}"></span>
                        </div>
                        <div class="node-type">
                            <span>${this.drivers[statusMenu]?.movementType}</span>
                        </div>
                        <div class="node-name">
                            <span class="operationStatusData" data-type="movement_name">${fn.escape( movementName )}</span>
                        </div>
                    </div>
                    <div class="node-terminal node-out connected">
                        <span class="connect-mark"></span>
                        <span class="hole">
                            <span class="hole-inner"></span>
                        </span>
                    </div>
                </div>
                <div class="node-operation">
                    <dl class="node-operation-body">
                        <dt class="node-operation-name">OP</dt>
                        <dd class="node-operation-data">${fn.escape( operationName )}</dd>
                    </dl>
                    <div class="node-operation-border"></div>
                </div>
            </div>
        </div>
        <div class="movementWaiting">${this.loadingHtml( getMessage.FTE14291 )}</div>
    </div>`;
    const driverEl = movement.querySelector('.node-result');
    driverEl.setAttribute('data-execution-no', executionNo );
    driverEl.setAttribute('data-status-menu', statusMenu );

    return movement;
}
// Movement緊急停止
async movementStop( button ) {
    const driver = button.dataset.statusMenu;
    const executionNo = button.dataset.executionNo;
    if ( !driver || !executionNo ) {
        alert( getMessage.FTE14292 );
        return;
    }
    button.disabled = true;
    const url = `/menu/${driver}/driver/${executionNo}/scram/`;
    if ( window.confirm(getMessage.FTE02044) ) {
        try {
            const result = await fn.fetch( url, null, 'PATCH', {});
            alert( result );
        } catch ( error ) {
            alert( error.message ?? getMessage.FTE14293 );
            button.disabled = false;
        }
    } else {
        button.disabled = false;
    }
    return;
}
// 作業状態確認
async movementExecuteCheck( resultEl ) {
    const menu = resultEl.dataset.statusMenu;
    const executionNo = resultEl.dataset.executionNo;
    if ( menu && executionNo ) {
        resultEl.disabled = true;
        await fn.modalIframe( menu + '&execution_no=' + executionNo, getMessage.FTE02128, { width: '960px'} );
        resultEl.disabled = false;
    }
    return;
}
// 結果データダウンロード
async movementResultDownload( button ) {
    const menu = button.dataset.execListMenu;
    const executionNo = button.dataset.executionNo;
    const filename = button.dataset.filename;
    if ( menu && executionNo && filename ) {
        button.disabled = true;
        const endPoint = `/menu/${menu}/${executionNo}/result_data/file/`;
        try {
            const file = await fn.getFile( endPoint, 'GET', null, { title: getMessage.FTE00185 })
            await fn.download('file', file, filename );
        } catch ( error ) {
            if ( error !== 'break') {
                console.error( error );
                alert( getMessage.FTE00179 );
            }
        }
        button.disabled = false;
    }
    return;
}
drivers = {
    check_operation_status_ansible_role: {
        movementType: 'Ansible Legacy Role',
        movementGem: 'ALR',
        movementClassName: 'node-ansible-legacy-role',
        movementListMenu: 'movement_list_ansible_role',
        targetHostMenu: 'target_host_ansible_role',
        substValueMenu: 'subst_value_list_ansible_role',
        executionListMenu: 'execution_list_ansible_role'
    },
    check_operation_status_ansible_legacy: {
        movementType: 'Ansible Legacy',
        movementGem: 'AL',
        movementClassName: 'node-ansible-legacy',
        movementListMenu: 'movement_list_ansible_legacy',
        targetHostMenu: 'target_host_ansible_legacy',
        substValueMenu: 'subst_value_list_ansible_legacy',
        executionListMenu: 'execution_list_ansible_legacy'
    },
    check_operation_status_ansible_pioneer: {
        movementType: 'Ansible Pioneer',
        movementGem: 'AP',
        movementClassName: 'node-ansible-pioneer',
        movementListMenu: 'movement_list_ansible_pioneer',
        targetHostMenu: 'target_host_ansible_pioneer',
        substValueMenu: 'subst_value_list_ansible_pioneer',
        executionListMenu: 'execution_list_ansible_pioneer'
    },
    check_operation_status_terraform_cloud_ep: {
        movementType: 'Terraform Cloud/EP',
        movementGem: 'TERE',
        movementClassName: 'node-terraform-cloud-ep',
        movementListMenu: 'movement_list_terraform_cloud_ep',
        targetHostMenu: '',
        substValueMenu: 'subst_value_list_terraform_cloud_ep',
        executionListMenu: 'execution_list_terraform_cloud_ep'
    },
    check_operation_status_terraform_cli: {
        movementType: 'Terraform CLI',
        movementGem: 'TERC',
        movementClassName: 'node-terraform-cli',
        movementListMenu: 'movement_list_terraform_cli',
        targetHostMenu: '',
        substValueMenu: 'subst_value_list_terraform_cli',
        executionListMenu: 'execution_list_terraform_cli'
    }
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   履歴管理
//
////////////////////////////////////////////////////////////////////////////////////////////////////
/*
##################################################
    履歴保存（AIサービス側の会話へ保存）
##################################################
*/
// 会話履歴をプラットフォーム側の会話（conversations）へ保存する。
// 応答ループの途中から何度も呼ばれるため、チャットごとにキューを持ち、
// 常に最新の1件だけを実行する（古い保存要求は破棄、実行中のものは中断する）。
//
// メッセージの送信時はプラットフォーム側が履歴を自動保存するため、この保存は
// 画面表示用の情報（_displayText / _attachments 等）を含む正の履歴を残すためのもの。
async historyEnqueue() {
    const llm = this.llm;
    if ( !llm ) return;
    // 履歴が空（画面を開いただけ）なら、空の会話を残さないため保存しない。
    const history = llm.getChatHistory();
    if ( !history || !history.length ) return;

    let state = this.historyQueues.get( this.chatId );
    if ( !state ) {
        state = {
            tail: Promise.resolve(),
            version: 0,
            controller: null
        };
        this.historyQueues.set( this.chatId, state );
    }

    // 新しい保存要求が来るたびに番号を増やす。（最新のversionだけを実行する。）
    state.version += 1;
    const requestVersion = state.version;
    // 実行中の保存があれば中断して最新だけを通す（保存は履歴の全置換なので、
    // 最新の1回だけ完走すればよい）。
    if ( state.controller ) {
        state.controller.abort();
    }

    const current = state.tail
        // 前の処理が失敗しても、後続は実行可能にする
        .catch( error => {
            if ( error.name !== 'AbortError') console.error('Previous save failed:', error );
        })
        .then(async () => {
            // 自分より新しい保存要求が存在する場合、この処理は古いので実行しない。
            if ( requestVersion !== state.version ) {
                return {
                    status: 'skipped',
                    reason: 'A newer save request exists.'
                };
            }
            // AbortController
            const controller = new AbortController();
            state.controller = controller;

            try {
                await llm.saveHistory( controller.signal );

                // 中断再開マーカーを更新する。初回保存で会話IDが確定するため、
                // 実行中に閉じられても、この会話IDから履歴を取得して自動再開できる。
                // （このstateが現在表示中の会話のときだけ更新する）
                if ( this.historyQueues?.get?.( this.chatId ) === state ) {
                    this._writeActiveChat( this.isRunning );
                }

                return {
                    status: 'done',
                    id: llm.conversationId
                };
            } catch ( error ) {
                if ( error.name === 'AbortError') {
                    return {
                        status: 'aborted'
                    };
                }
                throw error;
            } finally {
                // 別の処理がcontrollerを置き換えている可能性があるため、自分のcontrollerの場合だけ解除する。
                if ( state.controller === controller ) {
                    state.controller = null;
                }
            }
        });

    state.tail = current;
    return current;
}
// 履歴（LLMメッセージ配列）からチャット表示を再構築する共通処理。
// 履歴復元（resumeChat）と会話の巻き戻し（rewindConversation）で共用する。
// 表示のみを行い、LLM履歴（setChatHistory）や chatId / 会話IDの管理は呼び出し側で行う。
// 戻り値：tool_use_id → tool_result の対応表（呼び出し側の後処理で使う）。
_renderChatHistory( history ) {
    this.clearFile();
    // 破棄する吹き出しの画像プレビュー（objectURL）を解放する。
    this.revokeAttachmentPreviews();
    this.initChatArea();

    // 更新されたページのリンクを再構築するため、控えを初期化する。
    this._turnUpdatedMenus = new Map();

    // ドライバー実行画面の復元用に、tool_use_id → tool_result を先に集める
    // （tool_result は tool_use の次の user メッセージに入っているため）
    const toolResultMap = this.collectToolResults( history );

    // 選択肢（ask_user_choice 等の uiTools）の tool_use_id を集めておく。
    // これらに対応する tool_result は、ユーザの回答テキストとして復元表示する。
    const choiceToolIds = this.collectChoiceToolIds( history );

    for ( let blockIndex = 0; blockIndex < history.length; blockIndex++ ) {
        const block = history[ blockIndex ];
        const content = block.content ?? [];
        if ( fn.typeof( content ) === 'array' && block.role ) {
            for ( const [ itemIndex, item ] of content.entries() ) {
                const type = item.type;
                if ( type === 'text' && AiAssistantLlm.isInjectedBlock( item, block, itemIndex ) !== null ) {
                    // 添付ファイルのメタ情報や過去セッションの学習事項（前提知識）は、
                    // LLMへ渡すために保存されたテキストであり、ユーザの発言ではないため
                    // 吹き出しにしない（添付ファイルは吹き出しのファイル欄に表示される）。
                    continue;
                } else if ( type === 'text') {
                    // ユーザメッセージはひとつ前の応答の区切り。ここまでに更新された
                    // ページのリンクを、ライブ時と同じ位置（応答の末尾）に復元表示する。
                    if ( block.role === 'user') this.renderUpdatedMenuLinks( false );
                    // ユーザメッセージに表示用の別文言（_displayText）が保存されていれば、
                    // 本文（LLMへ送った指示文）ではなくそちらを吹き出しに復元する。
                    const restoredText = ( block.role === 'user'
                        && typeof block._displayText === 'string' && block._displayText !== '')
                        ? block._displayText
                        : ( item.text ?? '');
                    // システム操作（会話終了など）として送信されたユーザターンは、
                    // 復元時もシステム通知として表示する。
                    const restoredRole = ( block.role === 'user' && block._displaySystem === true )
                        ? 'system'
                        : block.role;
                    const message = {
                        role: restoredRole,
                        text: restoredText,
                        // 添付ファイルのメタ情報を復元（userメッセージのみ持つ）
                        attachments: block._attachments,
                        // 発言時刻を復元（保存済みの _timestamp。無ければ時刻は表示しない）
                        timestamp: block._timestamp
                    };
                    // システム通知ではない通常のユーザ発言は巻き戻しの起点にできる。
                    // 対応する履歴ブロックの位置（blockIndex）を持たせ、巻き戻しボタンを表示する。
                    if ( restoredRole === 'user') {
                        message.rewindable = true;
                        message.historyIndex = blockIndex;
                    }
                    this.updateChat( message, false );
                } else if ( type === 'tool_use' && block.role === 'assistant') {
                    const uiTool = this.uiTool( item.name );
                    if ( uiTool ) {
                        // 画面専用ツール（HTML表示・選択肢など）は、保存された input から
                        // それぞれのツール自身が表示を復元する。
                        uiTool.resume( item, block );
                    } else {
                        // execute-driver / dryrun-driver は専用の実行画面を復元する
                        this.resumeDriverExecution( item, toolResultMap.get( item.id ));
                        // maintenance-all / create-menu なら更新先メニューを控える
                        this.collectUpdatedMenuFromHistory( item, toolResultMap.get( item.id ));
                    }
                } else if ( type === 'tool_result' && choiceToolIds.has( item.tool_use_id ) ) {
                    // 選択肢への回答は応答の区切り。ここまでの更新ページのリンクを先に表示する。
                    this.renderUpdatedMenuLinks( false );
                    // 選択肢への回答は tool_result として保存されているため、
                    // ユーザメッセージとして復元表示する（送信時と同じ見た目）。
                    // この位置まで巻き戻すと直前の選択肢が未応答（回答待ち）状態に戻るため、
                    // 巻き戻し起点にできる。対応する履歴ブロックの位置を持たせる。
                    this.updateChat({
                        role: 'user',
                        text: this.extractChoiceAnswerText( item ),
                        timestamp: block._timestamp,
                        rewindable: true,
                        historyIndex: blockIndex,
                    }, false );
                }
            }
        }
    }

    // 最後のターンで更新されたページのリンクを表示する（以降にユーザメッセージが無いため）。
    this.renderUpdatedMenuLinks( false );

    return toolResultMap;
}
// 履歴から再開
// conversationId … 復元元の会話ID（プラットフォーム側の会話）。この会話へ続きを保存する。
async resumeChat( savedHistory, conversationId ) {
    if ( fn.typeof( savedHistory ) !== 'array' ) {
        throw new Error( getMessage.FTE14294 );
    }
    if ( fn.typeof( conversationId ) !== 'string') {
        throw new Error( getMessage.FTE14295 );
    }
    // 保存時に差し込まれたテキストブロック（添付ファイルのメタ情報・学習事項の前提知識）を取り除く。
    // これらは送信のたびに toApiHistory が差し込み直すため、履歴から外してもLLMへは渡り続ける。
    // 取り除いた履歴を引き継ぐことで、画面に表示されず、再開のたびに同じテキストが
    // 積み上がることもなくなる（積み上がっていた分も次の保存で解消される）。
    const history = AiAssistantLlm.stripInjectedBlocks( savedHistory );
    // 復元した履歴を引き継ぐLLM層を用意する
    // （認証切れの場合もここでnullになる。再開の前に checkAuthBeforeResume で確認しておくと、
    //   認証情報の更新を促すメッセージを表示できる）
    const llm = await this.ensureLlm();
    if ( !llm ) {
        throw new Error( ( this.isAuthError() )
            ? this.authExpiredMessage()
            : getMessage.FTE14296 );
    }
    const toolResultMap = this._renderChatHistory( history );

    this.pendingChoiceToolId = null;
    this.restorePendingChoice( history, toolResultMap );

    // 再開ごとに新しいchatIdを採番し、独立した保存state（historyQueues）を持たせる。
    // これをしないと、再開前のチャットのstate（実行中の保存要求）を引き継いでしまう。
    this.chatId = this.chatIdCounter++;
    // 復元元の会話を引き継ぐ（新しい会話は作らず、続きをこの会話へ保存する）
    llm.attachConversation( conversationId, history );

    // 中断された会話の自己修復：
    // インクリメンタル保存や離脱時保存により、履歴末尾が「tool_result 未応答の tool_use」で
    // 終わっている（＝ツール実行途中で閉じられた）ことがある。この状態のまま次の送信を行うと
    // 「tool_use に対応する tool_result が無い」API エラーになる。どの再開経路（会話履歴タブ／
    // 自動再開）でも安全に続けられるよう、ここでプレースホルダの tool_result を補って整合させる。
    const unansweredIds = this.getUnansweredToolUseIds( history );
    if ( unansweredIds.length ) {
        const placeholders = unansweredIds.map(( id ) => this._makeInterruptedToolResult( id ) );
        if ( this.pendingChoiceToolId ) {
            // 選択肢の回答待ちに、選択肢以外の未応答ツールが混在するケース。
            // ここでは履歴へ積まず退避し、ユーザーが選択肢に回答したときに選択肢の
            // tool_result と同じ user ターンでまとめて返す（1メッセージで全 tool_use に応答）。
            this.pendingToolResults = placeholders;
        } else {
            // ツール実行途中で中断。プレースホルダの tool_result を履歴へ確定して整合させる。
            llm.appendToolResults( placeholders );
        }
    }

    // 復元した会話を中断再開マーカーに紐付ける（まだ実行中ではない）。
    // この後で実際にターンが走れば _runResponseLoop が running=true に更新する。
    this._writeActiveChat( false );

    // 読込完了後、一番下までスクロールする（レイアウト確定を待つ）
    requestAnimationFrame(() => {
        const chatArea = this.elements.bodyInner;
        chatArea.scrollTop = chatArea.scrollHeight;
    });
}
/*
##################################################
    会話の巻き戻し
##################################################
*/
// 指定した履歴ブロック（ユーザメッセージ）の位置まで会話を巻き戻す。
// その位置以降（当該ユーザ発言とそれに続く応答すべて）を会話履歴・画面から取り除き、
// 取り除いたユーザ発言のテキストは入力欄に戻して、編集・再送信できるようにする。
// 注意：ITA（Exastro）側で実際に行われた作業（メニュー作成・更新、ドライバー実行など）は
//       巻き戻せない。会話（表示とLLM履歴）のみが巻き戻る。
async rewindConversation( historyIndex ) {
    if ( this.isRunning ) return;
    if ( !Number.isInteger( historyIndex ) || historyIndex < 0 ) return;

    const llm = this.llm;
    const history = ( llm && typeof llm.getChatHistory === 'function' ) ? llm.getChatHistory() : null;
    if ( !Array.isArray( history ) || historyIndex >= history.length ) return;

    // 巻き戻しの起点となるユーザ発言のテキスト（入力欄に戻す用）。
    // 通常発言は text ブロック、選択肢への回答は tool_result なのでその内容を取り出す。
    const removedBlock = history[ historyIndex ];
    let removedText = '';
    if ( removedBlock && Array.isArray( removedBlock.content ) ) {
        // 保存時に差し込まれたテキスト（添付ファイルのメタ情報など）は発言ではないため除く
        const textItem = removedBlock.content.find(( item, index ) => item.type === 'text'
            && AiAssistantLlm.isInjectedBlock( item, removedBlock, index ) === null );
        if ( textItem && typeof textItem.text === 'string' ) {
            removedText = textItem.text;
        } else {
            const toolResultItem = removedBlock.content.find(( item ) => item.type === 'tool_result' );
            if ( toolResultItem ) removedText = this.extractChoiceAnswerText( toolResultItem );
        }
    }

    // 実行済みのITA作業が元に戻らない旨を明示して確認する。
    const ok = window.confirm( getMessage.FTE14297 );
    if ( !ok ) return;

    // LLM履歴を起点の直前まで切り詰める
    const truncated = history.slice( 0, historyIndex );
    if ( typeof llm.setChatHistory === 'function' ) llm.setChatHistory( truncated );

    // 途中で切ったため、選択肢・退避中ツール結果などの保留状態はすべて破棄する。
    this.pendingChoiceToolId = null;
    this.pendingExtraChoiceToolIds = [];
    this.pendingToolResults = [];

    // 表示を作り直す（現在の会話を継続するため、chatId と会話IDは維持する）
    const toolResultMap = this._renderChatHistory( truncated );
    // 切り詰めた末尾が未応答の選択肢で終わっていれば、その保留状態（回答待ち）を復元する。
    // これにより、次のユーザ入力がその選択肢に対する tool_result として返り、会話を継続できる。
    this.restorePendingChoice( truncated, toolResultMap );

    // 選択肢の回答時点まで巻き戻した場合、同じ応答に含まれていた「通常ツール」の tool_use も
    // 未応答のまま残る。次回送信で「tool_use に対応する tool_result が無い」API エラーに
    // ならないよう、選択肢以外の未応答 tool_use にはプレースホルダの結果を持たせておく。
    if ( this.pendingChoiceToolId ) {
        const choiceIds = new Set([ this.pendingChoiceToolId, ...( this.pendingExtraChoiceToolIds ?? []) ]);
        const placeholders = [];
        for ( const id of this.getLastAssistantToolUseIds() ) {
            if ( choiceIds.has( id ) ) continue;
            placeholders.push({
                type: 'tool_result',
                tool_use_id: id,
                content: getMessage.FTE14298
            });
        }
        this.pendingToolResults = placeholders;
    }

    // 取り除いたユーザ発言を入力欄に戻し、そのまま編集・再送信できるようにする。
    if ( this.elements.message ) {
        this.elements.message.value = removedText;
        this.elements.message.focus();
    }

    // 保存されている履歴も切り詰めた内容へ置き換える。
    // 通常の送信ではプラットフォーム側が履歴を自動保存するため保存しなおしは不要だが、
    // 巻き戻しは画面側だけを切り詰めるため、ここで保存しなおさないと巻き戻した後のやりとりが
    // 巻き戻す前の履歴の続きになってしまう。
    // 失敗しても画面の巻き戻し自体は成立しているため、次の送信時の再同期に任せて続行する。
    try {
        await llm.saveHistory();
    } catch ( error ) {
        console.warn( error );
    }

    // 一番下までスクロール
    requestAnimationFrame(() => {
        const chatArea = this.elements.bodyInner;
        if ( chatArea ) chatArea.scrollTop = chatArea.scrollHeight;
    });
}
// 履歴全体から tool_use_id → tool_result の対応表を作る
// （tool_result は tool_use を含む assistant メッセージの次の user メッセージにある）
collectToolResults( history ) {
    const map = new Map();
    for ( const block of history ) {
        const content = block.content ?? [];
        if ( fn.typeof( content ) !== 'array') continue;
        for ( const item of content ) {
            if ( item.type === 'tool_result' && item.tool_use_id ) {
                map.set( item.tool_use_id, item );
            }
        }
    }
    return map;
}
// 履歴全体から、選択肢ツール（uiTools）の tool_use の id 集合を作る。
// この id を tool_use_id に持つ tool_result は、ユーザの回答として復元表示する。
collectChoiceToolIds( history ) {
    const ids = new Set();
    for ( const block of history ) {
        if ( block.role !== 'assistant') continue;
        const content = block.content ?? [];
        if ( fn.typeof( content ) !== 'array') continue;
        for ( const item of content ) {
            if ( item.type === 'tool_use' && this.isUiChoiceTool( item.name ) && item.id ) {
                ids.add( item.id );
            }
        }
    }
    return ids;
}
// 選択肢の tool_result からユーザの回答テキストを取り出す。
// content は文字列、またはテキストブロックの配列のことがある。
extractChoiceAnswerText( toolResult ) {
    const content = toolResult?.content;
    if ( typeof content === 'string') return content;
    if ( Array.isArray( content ) ) {
        return content
            .map(( item ) => ( typeof item === 'string' ? item : ( item?.text ?? '') ) )
            .join('');
    }
    return '';
}
// LLM履歴の末尾にある assistant メッセージが持つ tool_use の id 集合を返す。
// tool_result を送る前に、対応する tool_use が本当に直前 assistant に存在するかを
// 検証するために使う（存在しない id への tool_result は API エラーになるため）。
getLastAssistantToolUseIds() {
    const ids = new Set();
    const llm = this.llm;
    const messages = ( llm && typeof llm.getChatHistory === 'function' ) ? llm.getChatHistory() : null;
    if ( !Array.isArray( messages ) ) return ids;
    // 末尾から最初に見つかる assistant メッセージを対象にする。
    for ( let i = messages.length - 1; i >= 0; i-- ) {
        const block = messages[ i ];
        if ( block.role !== 'assistant') continue;
        const content = Array.isArray( block.content ) ? block.content : [];
        for ( const item of content ) {
            if ( item && item.type === 'tool_use' && item.id ) ids.add( item.id );
        }
        break;
    }
    return ids;
}
// 履歴の末尾が「未応答の ask_user_choice（選択肢）tool_use」で終わっている場合に、
// その tool_use_id を pendingChoiceToolId に復元する。
// これにより、履歴復元後の最初の入力もボタン選択と同様に tool_result として返せる。
restorePendingChoice( history, toolResultMap ) {
    // 末尾から最初に見つかった assistant の tool_use を調べる。
    // それが選択肢ツールで、かつ対応する tool_result がまだ無ければ pending とみなす。
    for ( let i = history.length - 1; i >= 0; i-- ) {
        const block = history[ i ];
        const content = block.content ?? [];
        if ( fn.typeof( content ) !== 'array') continue;
        // user メッセージに tool_result が含まれていれば、直前の tool_use は応答済み。
        if ( block.role === 'user') {
            const hasToolResult = content.some(( item ) => item.type === 'tool_result');
            if ( hasToolResult ) return;
            continue;
        }
        if ( block.role !== 'assistant') continue;
        // この assistant ターンの選択肢ツール（uiTools）のうち、未応答のものを集める。
        // フォーマット崩れで1ターンに複数の選択肢 tool_use が出ることがあるため、
        // 先頭を代表（pendingChoiceToolId）、残りを pendingExtraChoiceToolIds に復元する。
        const unansweredChoiceIds = [];
        let hasToolUse = false;
        for ( const item of content ) {
            if ( item.type !== 'tool_use') continue;
            hasToolUse = true;
            if ( this.isUiChoiceTool( item.name ) && !toolResultMap.has( item.id ) ) {
                unansweredChoiceIds.push( item.id ?? '');
            }
        }
        if ( unansweredChoiceIds.length ) {
            this.pendingChoiceToolId = unansweredChoiceIds[ 0 ];
            this.pendingExtraChoiceToolIds = unansweredChoiceIds.slice( 1 );
        }
        // この assistant ターンに tool_use があれば、それが直近の未応答対象。ここで確定。
        if ( hasToolUse ) return;
    }
}
// 履歴復元時に execute-driver / dryrun-driver の実行画面（Movementノード）を再描画する。
// toolUse: 履歴内の tool_use ブロック（name, arguments を持つ）
// toolResult: 対応する tool_result ブロック（無い場合あり）
resumeDriverExecution( toolUse, toolResult ) {
    if ( !AiAssistantChat.DRIVER_TOOLS.includes( toolUse.name )) return;

    // 実行メニュー（execution_*）→ ステータス確認メニュー（check_operation_status_*）へ変換
    const execMenu = toolUse.arguments?.menu ?? toolUse.input?.menu ?? '';
    const statusMenu = execMenu.startsWith('execution_')
        ? execMenu.replace(/^execution_/, 'check_operation_status_')
        : execMenu;
    if ( !this.drivers[ statusMenu ]) return;

    const movementName = toolUse.arguments?.movement_name ?? toolUse.input?.movement_name ?? '';
    const operationName = toolUse.arguments?.operation_name ?? toolUse.input?.operation_name ?? '';
    const resultData = this.extractDataFromResult( toolResult );
    const executionNo = resultData?.execution_no ?? '';
    const resultDataName = `ResultData_${executionNo}.zip`;
    const execListMenu = this.drivers?.[ statusMenu ]?.executionListMenu ?? '';

    // 実行画面のバブルを生成
    const el = this.createAssistantMessageElement('', false );
    const movement = this.movementElement( statusMenu, execListMenu, movementName, operationName, executionNo );
    el.querySelector('.aiAssistantChatAssistantMessageInner').replaceChildren( movement );

    // 直前がアシスタントなら連続クラスを付与
    const prevItem = this.elements.chatList.lastElementChild;
    if ( prevItem?.classList.contains('aiAssistantChatAssistantMessage')) {
        el.classList.add('aiAssistantChatAssistantMessageChain');
    }
    this.elements.chatList.append( el );

    // tool_result から最終ステータスを取り出して反映（①で付与した driver_execution を優先）
    const finalStatus = this.extractFinalStatusFromResult( toolResult );
    if ( finalStatus ) {
        this.updateToolProgress( el, finalStatus, true, resultDataName );
    } else {
        // 最終ステータスが無い＝確定しないまま中断された。このまま放置すると「待機中」スピナーが
        // 回り続けて固まって見えるため、停止表示に切り替える。
        // ・tool_result 自体が無い（ツール呼び出し途中でページを閉じた）＝ページ離脱による中断。
        // ・tool_result はあるが最終ステータスが取れていない＝監視が確定前に終了した。
        this.markDriverExecutionInterrupted( el, { hasToolResult: !!toolResult, executionNo } );
    }
}
// 実行状況が確定しないまま中断された Movement 実行バブルを「停止」表示に切り替える。
// ・「待機中」スピナーを止め、指定メッセージに差し替える。
// ・サーバ側で実行が継続・完了している可能性があるため、状態確認は押せるようにしておく。
markDriverExecutionInterrupted( runningEl, opts = {} ) {
    if ( !runningEl ) return;
    const waitingEl = runningEl.querySelector('.movementWaiting');
    const statusCheckButton = runningEl.querySelector('.movementStatusCheckButton');
    const emergencyStopButton = runningEl.querySelector('.movementEmergencyStopButton');
    const nodeEl = runningEl.querySelector('.node');

    // 実行No.は引数優先、無ければ状態確認ボタンの data 属性から拾う。
    // 実行No.が無い＝ツール呼び出し途中でページを閉じ、実行No.が記録されていない場合は
    // この画面から作業状態を確認できないため、ボタンを非活性化し文言もその旨にする。
    const executionNo = opts.executionNo || statusCheckButton?.dataset.executionNo || '';
    const canCheckStatus = !!executionNo;

    let messageHtml;
    if ( !canCheckStatus ) {
        messageHtml = getMessage.FTE14299;
    } else if ( !opts.hasToolResult ) {
        messageHtml = getMessage.FTE14300;
    } else {
        messageHtml = getMessage.FTE14301;
    }

    if ( waitingEl ) {
        waitingEl.classList.add('movementWaitingStopped');
        waitingEl.innerHTML =
            `<div class="movementStopped">${fn.html.icon('circle_exclamation')}`
            + `<span>${messageHtml}</span></div>`;
    }
    // 実行No.があるときだけ状態確認を活性化。緊急停止は常に不可（このセッションでは監視していない）。
    if ( statusCheckButton ) statusCheckButton.disabled = !canCheckStatus;
    if ( emergencyStopButton ) emergencyStopButton.disabled = true;
    // ノードを「停止」見た目にする（実行アニメーションを止め、STOP バッジを表示）。
    if ( nodeEl ) {
        nodeEl.classList.remove('ready', 'running');
        nodeEl.classList.add('complete');
        const nodeResult = nodeEl.querySelector('.node-result');
        if ( nodeResult ) nodeResult.setAttribute('data-result-text', 'STOP');
    }
}
// 履歴の tool_result から最終ステータス文字列を取り出す。
// ①で付与した driver_execution.final_status を優先し、無ければ再帰探索でフォールバック。
extractFinalStatusFromResult( toolResult ) {
    if ( !toolResult ) return '';
    let parsed = toolResult.content;
    if ( typeof parsed === 'string') {
        try {
            parsed = JSON.parse( parsed );
        } catch ( e ) {
            return '';
        }
    }
    if ( !parsed || typeof parsed !== 'object') return '';

    // ①で付与した確定ステータス
    const fromDriver = parsed.driver_execution?.final_status;
    if ( typeof fromDriver === 'string' && fromDriver ) return fromDriver;

    // フォールバック: structuredContent 配下を再帰探索
    return this._extractDriverStatus( parsed.result?.structuredContent ?? {});
}
// 履歴の tool_result から data を取り出す。
// watchDriverProgress と同じく result.structuredContent.result.data を想定（ゆらぎに対応）。
extractDataFromResult( toolResult ) {
    if ( !toolResult ) return '';
    let parsed = toolResult.content;
    if ( typeof parsed === 'string') {
        try {
            parsed = JSON.parse( parsed );
        } catch ( e ) {
            return '';
        }
    }
    if ( !parsed || typeof parsed !== 'object') return '';

    const structured = parsed.result?.structuredContent ?? {};
    const apiResult = structured.result ?? {};
    const data = apiResult.data ?? apiResult;
    return data;
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   離脱時の中断保存 ＆ 再読込時の自動再開
//
////////////////////////////////////////////////////////////////////////////////////////////////////
// 「作業中の会話」をブラウザ（localStorage）に記録するためのキー。ユーザーごとに分ける。
// ページを閉じても残るため、開き直したときに中断された会話を特定して再開できる。
// 呼び出し元（プロンプトプロファイル）ごとにも分ける。ファイル編集画面のチャットで中断した会話を
// AIアシスタントメニューが自動再開してしまうと、会話が想定外の画面へ移ってしまうため。
// 既定のプロファイル（AIアシスタントメニュー）は、記録済みのマーカーをそのまま使えるよう
// これまでと同じキーにしておく。
_activeChatKey() {
    const profile = this.promptProfile ?? AiAssistantLlm.promptProfile;
    const suffix = ( profile === AiAssistantLlm.promptProfile )? '': `:${profile}`;
    return `aiAssistantActiveChat:${this.id ?? 'unknown'}${suffix}`;
}
// 現在の会話を「実行中かどうか」とともに localStorage へ記録する。
// conversationId（プラットフォーム側の会話ID）は最初の送信・保存で確定する。
// running=true かつ conversationId 確定済みのときだけ、次回読込での自動再開の対象になる。
_writeActiveChat( running ) {
    try {
        const conversationId = this.llm?.conversationId ?? null;
        const payload = { conversationId, running: !!running, chatId: this.chatId };
        localStorage.setItem( this._activeChatKey(), JSON.stringify( payload ) );
    } catch ( error ) {
        // localStorage が使えない環境でも致命的ではない（自動再開が効かないだけ）。
        console.warn('中断再開マーカーの保存に失敗しました。', error );
    }
}
// 中断再開マーカーを削除する（新規チャット開始時など）。
_clearActiveChat() {
    try {
        localStorage.removeItem( this._activeChatKey() );
    } catch ( error ) {
        console.warn('中断再開マーカーの削除に失敗しました。', error );
    }
}
// 停止・エラー時に _runResponseLoop へ渡す「空の保留状態」。
_emptyPending() {
    return { pendingChoiceToolId: null, pendingExtraChoiceToolIds: [], pendingToolResults: [] };
}
// 履歴保存（historyEnqueue）を待たずに投げる際の安全ラッパー。
// 応答ループ中に何度も呼ぶため、保存失敗が未処理の Promise 拒否にならないよう握りつぶす
// （本当の整合性は、次の保存 or 復元時の自己修復で担保される）。
_enqueueHistorySafe() {
    try {
        const p = this.historyEnqueue();
        if ( p && typeof p.catch === 'function' ) p.catch(( error ) => console.warn('履歴の逐次保存に失敗しました。', error ) );
    } catch ( error ) {
        console.warn('履歴の逐次保存に失敗しました。', error );
    }
}
// 中断された tool_use に返す、プレースホルダの tool_result を作る。
// 実行済みかどうかは不明なため、再実行させず状況確認を促す文面にする。
_makeInterruptedToolResult( toolUseId ) {
    return {
        type: 'tool_result',
        tool_use_id: toolUseId,
        content: getMessage.FTE14302
    };
}
// 履歴末尾の assistant ターンに含まれる、未応答（tool_result が無い）かつ選択肢以外の
// tool_use の id を返す。履歴末尾が assistant であることが前提（＝直後に tool_result が無い）。
// 中断された（ツール実行途中で閉じられた）会話を継続する際、これらへプレースホルダの
// tool_result を返して履歴整合を保つために使う。
getUnansweredToolUseIds( history ) {
    if ( !Array.isArray( history ) || !history.length ) return [];
    const last = history[ history.length - 1 ];
    if ( !last || last.role !== 'assistant' || !Array.isArray( last.content ) ) return [];
    const ids = [];
    for ( const item of last.content ) {
        if ( item && item.type === 'tool_use' && item.id && !this.isUiChoiceTool( item.name ) ) {
            ids.push( item.id );
        }
    }
    return ids;
}
// 復元した会話が「継続できる中断状態」か、末尾から判定する。
//   toolUse     : 末尾 assistant に未応答の（選択肢以外の）tool_use がある（ツール実行途中で中断）
//   userPending : 末尾が user（テキスト or tool_result）＝ LLM 応答前に中断
//   none        : 末尾 assistant がテキストのみ＝応答は完了済み（継続不要）
_detectInterruptedContinuation( history ) {
    if ( !Array.isArray( history ) || !history.length ) return { type: 'none', ids: [] };
    const last = history[ history.length - 1 ];
    if ( !last ) return { type: 'none', ids: [] };
    if ( last.role === 'assistant' ) {
        const ids = this.getUnansweredToolUseIds( history );
        return ids.length ? { type: 'toolUse', ids } : { type: 'none', ids: [] };
    }
    if ( last.role === 'user' ) {
        return { type: 'userPending', ids: [] };
    }
    return { type: 'none', ids: [] };
}
// ページ再読込時、前回「作業中」に中断された会話があれば復元し、ユーザーの確認のうえ継続する。
// 戻り値：復元して画面を占有した場合 true（呼び出し側は newChatStart をスキップする）。
async _tryAutoResume() {
    // 設定未完了なら再開できない（LLM を用意できない）。
    if ( !this.checkAiAssistantSetting() ) return false;

    // 中断再開マーカーを読む。実行中フラグが立っていて会話IDが確定しているものだけが対象。
    let marker = null;
    try {
        marker = JSON.parse( localStorage.getItem( this._activeChatKey() ) || 'null' );
    } catch ( error ) {
        marker = null;
    }
    if ( !marker || marker.running !== true || !marker.conversationId ) return false;

    // 認証が切れている場合は、復元しても続きを送信できないため再開しない。
    // 読み込み時（loadSetting）に確認した結果で判定し、更新を促すアラートを表示する。
    // マーカーは残すため、認証情報を更新して読み込み直せば再開できる。
    if ( this.isAuthError() ) {
        alert( getMessage.FTE14303( this.authExpiredMessage() ) );
        return false;
    }

    // AIサービス側（会話）に保存されている履歴を取得する（会話履歴タブの再開と同じ経路）。
    let history;
    try {
        history = await AiAssistantLlm.fetchHistory( marker.conversationId );
    } catch ( error ) {
        console.warn('自動再開: 履歴の取得に失敗しました。新規チャットを開始します。', error );
        // 取得に失敗したマーカーは残しても意味がないので消す。
        this._clearActiveChat();
        return false;
    }
    if ( fn.typeof( history ) !== 'array' || !history.length ) {
        this._clearActiveChat();
        return false;
    }

    // 新規チャット相当の初期化（チャットUI＝入力欄・送信/停止ボタンの構築、LLMセットアップ、
    // 学習事項の反映）を行ってから履歴を復元する。会話履歴タブからの手動再開と同じ順序で、
    // newChatStart で土台を作ってから resumeChat する（初期化を飛ばすと入力欄が無くなる）。
    // ※ newChatStart 内の setNewChat がマーカーを消すが、必要な値は marker に取得済みで、
    //   resumeChat 後に改めて書き戻されるため問題ない。
    try {
        await this.newChatStart();
        await this.resumeChat( history, marker.conversationId );
    } catch ( error ) {
        console.warn('自動再開: 会話の復元に失敗しました。新規チャットを開始します。', error );
        this._clearActiveChat();
        return false;
    }

    // 復元が終わったのでページ全体のローディング表示（#content の nowLoading）を解除する。
    // これをしないと、継続処理（LLMの応答待ち等）が終わるまでページがローディングのまま固まって見える。
    document.querySelector('#content')?.classList.remove('nowLoading');

    // 中断状態に応じた継続（確認ダイアログ＋LLMループ）は、ページ描画・他タブの初期化・
    // mount の完了を止めないよう、現在の実行を抜けてから走らせる。
    // （await すると mount がLLM応答の完了まで返らず、window.confirm もページ描画前に出てしまう）
    setTimeout( () => {
        this._offerResumeContinuation().catch(( error ) => console.warn('自動再開の継続に失敗しました。', error ) );
    }, 0 );
    return true;
}
// 復元済みの会話について、中断状態を判定し、ユーザーの確認を得てから継続する。
// ・選択肢の回答待ち  : 確認不要。上の選択肢に答えれば続く旨を案内するだけ。
// ・完了済み          : 継続不要。復元した旨を案内し、マーカーを実行中でないに更新する。
// ・継続可能（途中）  : 確認ダイアログを出し、「はい」で自動継続、「いいえ」で復元のみ。
async _offerResumeContinuation() {
    const llm = this.llm;
    const history = ( llm && typeof llm.getChatHistory === 'function' ) ? llm.getChatHistory() : null;

    // 選択肢の回答待ちで復元された場合は、ユーザーの回答を待つ（自動継続しない）。
    if ( this.pendingChoiceToolId ) {
        this.updateChat({ role: 'system', text: getMessage.FTE14304 });
        // 回答待ち＝実行中ではないので、マーカーを実行中でないに更新する。
        this._writeActiveChat( false );
        return;
    }

    const info = this._detectInterruptedContinuation( history );

    // 継続の必要がない（応答完了済み）場合は、復元した旨だけ伝える。
    if ( info.type === 'none' ) {
        this.updateChat({ role: 'system', text: getMessage.FTE14305 });
        this._writeActiveChat( false );
        return;
    }

    // ここへ来る時点で、tool_use 未応答は resumeChat で既にプレースホルダ補完済み
    // （＝末尾は user）。修復後に整合した履歴を保存しておく（この時点で再度閉じても壊れないように）。
    this._enqueueHistorySafe();

    // 中断された作業がある旨を表示し、継続するか確認する。
    this.updateChat({ role: 'system', text: getMessage.FTE14306 });
    const ok = window.confirm( getMessage.FTE14307 );

    if ( !ok ) {
        // 復元のみ。次回読込で再び自動再開しないよう、マーカーを実行中でないに更新する。
        this._writeActiveChat( false );
        return;
    }

    // 応答ループを継続モードで再開する（新規ユーザ発言は積まず、履歴末尾から続きを生成させる）。
    await this._runResponseLoop({
        sendPayload: null,
        uploadedFiles: [],
        turnStartEl: null,
        isRewindableUserTurn: false,
        firstSendOptions: undefined,
        savedPending: this._emptyPending(),
        continuation: true,
    });
}
// 中断・エラーで巻き戻されたターンの吹き出しに専用クラスを付与する。
// turnStartEl（このターンのユーザ発言）から chatList 末尾までを「中断ターン」として区別する。
markTurnAborted( turnStartEl ) {
    const list = this.elements.chatList;
    if ( !list || !turnStartEl ) return;
    // turnStartEl 以降（同ターンで追加された全吹き出し）にクラスを付ける
    let el = turnStartEl;
    while ( el ) {
        el.classList.add('aiAssistantChatItemAborted');
        el = el.nextElementSibling;
    }
}
// 直近の送信済みユーザメッセージに「停止」ラベルを付与する
markLastUserMessageStopped() {
    const items = this.elements.chatList?.querySelectorAll('.aiAssistantChatUserMessage');
    const lastUser = items?.length ? items[ items.length - 1 ] : null;
    if ( !lastUser || lastUser.querySelector('.aiAssistantChatUserMessageStopped') ) return;
    const label = document.createElement('p');
    label.classList.add('aiAssistantChatUserMessageStopped');
    label.innerText = getMessage.FTE14308;
    lastUser.querySelector('.aiAssistantChatItemInner')?.append( label );
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   イベント設定
//
////////////////////////////////////////////////////////////////////////////////////////////////////
// root配下でselectorに一致した要素だけをhandlerへ渡す委譲リスナー。
// whileRunning: true のときは応答処理中（isRunning）でも実行する（読み取り専用操作など）。
delegate( root, type, selector, handler, { whileRunning = false } = {} ) {
    root.addEventListener( type, ( e ) => {
        if ( !whileRunning && this.isRunning ) return;
        const target = e.target?.closest?.( selector );
        if ( !target || !root.contains( target ) ) return;
        return handler.call( this, e, target );
    }, { signal: this.ac.signal });
}
// data-type に対応するアクション定義（*EventActions）を実行する共通処理。
//   whileRunning: true … 応答処理中（isRunning）でも実行する（読み取り専用の操作など）
//   lockButton  : true … 実行中はボタンを無効化して連打を防ぐ
// 定義がないdata-typeは対象外として無視する。
async runEventAction( actions, target, e ) {
    const action = actions[ target.dataset.type ];
    if ( !action ) return;
    if ( this.isRunning && !action.whileRunning ) return;
    if ( action.lockButton ) target.disabled = true;
    try {
        await action.run( target, e );
    } finally {
        if ( action.lockButton ) target.disabled = false;
    }
}
/*
##################################################
    イベント登録
##################################################
*/
bindEvents() {
    this.bindHeaderEvents();
    this.bindBodyEvents();
    this.bindFooterEvents();
    this.bindWindowEvents();
}
/*
##################################################
    Windowイベント
##################################################
*/
// 応答処理・ツール実行中（isRunning）のページ離脱に備える。
//   ・離脱前に確認ダイアログを出して、作業中であることを知らせる。
//   ・それでも離脱された場合は、その時点の履歴を保存しようと試みる（次回読込での自動再開用）。
bindWindowEvents() {
    // 稼働中（応答処理・ツール実行中）のページ離脱時に確認ダイアログを表示する
    window.addEventListener('beforeunload', ( e ) => {
        if ( !this.isRunning ) return;
        // 標準の離脱確認ダイアログを表示する（メッセージ文言はブラウザ既定）
        e.preventDefault();
        e.returnValue = '';
    }, { signal: this.ac.signal });

    // 離脱時のベストエフォート保存。
    // 実行中に閉じられたら、その時点の履歴をAIサービス側の会話へ保存しようと試みる。
    // ・ただし離脱中の非同期通信は完了保証がない（ブラウザに打ち切られ得る）。
    //   本当の耐障害性は、応答ループ中に「応答受信直後」「ツール実行直後」へ細かく保存する
    //   インクリメンタル保存で担保しており、これはあくまで最後の数秒分の保険。
    // ・pagehide はタブ破棄／bfcache 遷移でも発火するため beforeunload より取りこぼしにくい。
    const flushOnLeave = () => {
        if ( !this.isRunning ) return;
        // 離脱中のため失敗は握りつぶす（次回はインクリメンタル保存済みの状態から再開する）。
        this._enqueueHistorySafe();
    };
    window.addEventListener('pagehide', flushOnLeave, { signal: this.ac.signal });
    window.addEventListener('beforeunload', flushOnLeave, { signal: this.ac.signal });
}
/*
##################################################
    Headerイベント
##################################################
*/
// 新しいチャット・チャット終了は応答処理中でも呼べるようにし（whileRunning）、
// 「応答中は実行できない」ことを各処理の中でユーザーへ伝える（無反応にしない）。
headerEventActions = {
    newChat: { lockButton: true, whileRunning: true, run:() => this.newChatEvent() },
    // チャット終了は応答完了までボタンの状態を自前で管理するため lockButton は使わない
    // （lockButton の後処理で、終了後に無効化したボタンが再活性化されてしまう）
    closeChat: { whileRunning: true, run:() => this.closeChatEvent() },
    aiAssistantSetting: { lockButton: true, run:() => this.aiAssistantSettingEvent() }
}
bindHeaderEvents() {
    this.delegate( this.elements.header, 'click', '.itaButton[data-type]',
        ( e, button ) => this.runEventAction( this.headerEventActions, button, e ), { whileRunning: true });
}
// 新しいチャット
// 会話中の場合は確認したうえで、ここまでの履歴を保存してから新規チャット画面へ戻す。
// 履歴はAIサービス側の会話に保存されているため、新しいチャットを始めても失われない。
async newChatEvent() {
    // 応答中に会話を差し替えると、進行中のツール実行の結果が新しいチャットへ混ざるため中止する。
    if ( this.isRunning ) {
        alert( getMessage.FTE14309 );
        return;
    }
    if ( this.newChat !== true ) {
        // 表示用の情報（発言時刻・表示文言など）を含む最新の履歴を保存しておく。
        // 失敗しても新規チャットの開始は妨げない（保存は応答完了時にも行われている）。
        try {
            await this.historyEnqueue();
        } catch ( error ) {
            console.warn('新しいチャットを開始する前の履歴保存に失敗しました。', error );
        }
    }
    await this.newChatStart();
}
// チャット終了
// 終了時に行う処理（会話の要約・作業レポート・学習事項の登録）をダイアログで選ばせ、
// 選択されたものをまとめて実行して会話を締める。
// 終了後もメッセージを送信すれば会話は続けられる（送信時に終了ボタンが再活性化される）。
async closeChatEvent() {
    // 応答中はまとめを送れない（送信が二重になる）ため、終わるまで待ってもらう。
    if ( this.isRunning ) {
        alert( getMessage.FTE14310 );
        return;
    }
    // まだ何も送信していない（新規チャット画面）場合は終了するものが無い
    if ( this.newChat === true || !this.llm?.getChatHistory()?.length ) return;

    // 終了時に行う処理を選ばせる（誤操作の防止も兼ねる）。キャンセルなら何もしない。
    // 何も選択せずに終了した場合（空配列）は、終了時の処理は行わないが
    // 「チャットを終了する」操作自体は成立させ、終了したことをシステム通知で伝える。
    const actions = await this.openCloseChatDialog();
    if ( !Array.isArray( actions ) ) return;

    // 終了操作中は再度押せないようにする（通常のメッセージ送信で再活性化される）
    if ( this.elements.closeChatButton ) this.elements.closeChatButton.disabled = true;

    // LLMに出力させる処理（要約・レポート）は1通の指示にまとめて送る。
    // 指示文はLLMへ送り、吹き出しには短い文言をシステム通知として表示する。
    const instruction = this.buildCloseChatInstruction( actions );
    let closed = true;
    if ( instruction ) {
        const historyLength = this.llm?.getChatHistory()?.length ?? 0;
        await this.sendMessage( instruction, {
            displayText: getMessage.FTE14311,
            systemAction: true
        });
        // まとめのターンが履歴に残っていれば終了できた。停止・エラーでターンが巻き戻された
        // 場合は終了できていないため、終了ボタンを戻して再度終了できるようにする。
        closed = ( this.llm?.getChatHistory()?.length ?? 0 ) > historyLength;
    }

    // 学習事項の登録は、この会話とは別の会話（prompt_profile = Lessons）で抽出するため、
    // 上の要約・レポートとは独立して実行する。失敗しても会話の終了自体は成立させる。
    if ( actions.includes('lessons') ) await this.confirmAndRecordLessons();

    // タイトルの付け直しも別の会話（prompt_profile = GenerateTitle）で生成するため独立して実行する。
    // 要約・レポートを含む最新の履歴からタイトルを付けたいので、最後に行う。
    if ( actions.includes('title') ) await this.generateAndSaveTitle();

    if ( closed ) {
        // 何も選択されていない場合は要約・レポートの吹き出しが出ないため、
        // 終了時の処理を行っていないことも併せて伝える。
        this.updateChat({ role: 'system', text: ( actions.length )
            ? getMessage.FTE14312
            : getMessage.FTE14313 });
    } else if ( this.elements.closeChatButton ) {
        this.elements.closeChatButton.disabled = false;
    }
}
/*
##################################################
    チャット終了時の処理を選ぶダイアログ
##################################################
*/
// チャット終了時に実行する処理をユーザーに選ばせるダイアログを表示する。
// 戻り値: 選択されたactionの配列（例: ['summary','reportMd','lessons','title']）。
// 　　　　何も選択されなかった場合は空配列（＝処理なしで終了）、キャンセル時はnull。
openCloseChatDialog() {
    return new Promise(( resolve ) => {
        const config = {
            position: 'center',
            width: '520px',
            header: { title: getMessage.FTE14314 },
            footer: {
                button: {
                    // 何も選択せずに押した場合は「処理なしで終了する」意味になるため、
                    // 「実行」ではなく「終了する」とする。
                    execute: { text: getMessage.FTE14315, action: 'positive', className: 'dialogPositive'},
                    cancel: { text: getMessage.FTE14316, action: 'normal'}
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
                const selected = [];
                // 要約・学習事項（複数選択できるチェックボックス）
                dialog.$.dialog.find('.aiCloseChatOption:checked').each(( i, el ) => {
                    if ( el && el.value ) selected.push( el.value );
                });
                // レポート種別（Markdown / HTML の排他選択。ラジオ）。
                // 値が空（＝作成しない）の場合は追加しない。
                const report = dialog.$.dialog.find('.aiCloseChatReport:checked').val();
                if ( report ) selected.push( report );
                finish( selected );
            },
            cancel: () => finish( null )
        };

        // 要約・学習事項は複数選択できるチェックボックス
        const checkItem = ( o, i ) => {
            const id = `aiCloseChatCheck_${i}`;
            return `
                <li class="aiCloseChatOptionItem">
                    <label class="aiCloseChatOptionLabel" for="${id}">
                        <input type="checkbox" id="${id}" class="aiCloseChatOption" value="${o.value}"${( o.checked )? ' checked': ''}>
                        <span class="aiCloseChatOptionText">${o.label}</span>
                    </label>
                </li>`;
        };
        // レポートは Markdown / HTML を排他選択（ラジオ）。「作成しない」を既定にする。
        const radioItem = ( o, i ) => {
            const id = `aiCloseChatReport_${i}`;
            return `
                <li class="aiCloseChatOptionItem">
                    <label class="aiCloseChatOptionLabel" for="${id}">
                        <input type="radio" id="${id}" name="aiCloseChatReport" class="aiCloseChatReport" value="${o.value}"${( o.checked )? ' checked': ''}>
                        <span class="aiCloseChatOptionText">${o.label}</span>
                    </label>
                </li>`;
        };

        const reportRadios = [
            { value: '', label: getMessage.FTE14317, checked: false },
            { value: 'reportMd', label: getMessage.FTE14318, checked: true },
            { value: 'reportHtml', label: getMessage.FTE14319, checked: false }
        ].map( radioItem ).join('');

        const html = `
        <div class="dialogBody">
            <div class="commonSection">
                <div class="aiCloseChatDescription">${getMessage.FTE14320}</div>
                <div class="aiCloseChatGroup commonInputGroup">
                    <ul class="aiCloseChatOptionList">
                        ${checkItem({ value: 'summary', label: getMessage.FTE14321, checked: true }, 0 )}
                    </ul>
                </div>
                <div class="aiCloseChatGroup commonInputGroup">
                    <ul class="aiCloseChatOptionList">${reportRadios}</ul>
                </div>
                <div class="aiCloseChatGroup commonInputGroup">
                    <ul class="aiCloseChatOptionList">
                        ${checkItem({ value: 'lessons', label: getMessage.FTE14322, checked: false }, 1 )}
                    </ul>
                </div>
                <div class="aiCloseChatGroup commonInputGroup">
                    <ul class="aiCloseChatOptionList">
                        ${checkItem({ value: 'title', label: getMessage.FTE14323, checked: false }, 2 )}
                    </ul>
                </div>
            </div>
        </div>`;

        dialog.open( html );
        // positiveボタン（実行）は既定で非活性のため、明示的に有効化する
        dialog.buttonPositiveDisabled( false );
    });
}
// 選択されたactionから、LLMに出力させる指示メッセージを組み立てる。
// 要約・作業レポート・グラフィカルなレポートのうち選ばれたものだけを1通にまとめる。
// いずれも選ばれていなければ空文字を返す（送信不要）。
buildCloseChatInstruction( actions ) {
    const wants = ( action ) => Array.isArray( actions ) && actions.includes( action );
    const parts = [];

    if ( wants('summary') ) {
        parts.push( ...getMessage.FTE14324, '');
    }
    if ( wants('reportMd') ) {
        parts.push( ...getMessage.FTE14325, '');
    }
    if ( wants('reportHtml') ) {
        parts.push(
            ...getMessage.FTE14326,
            getMessage.FTE14327,
            // 1回の応答には出力量の上限（プラットフォーム側の max_tokens）があり、レポート全体を
            // 1回のツール呼び出しで渡そうとすると引数が途中で切れる。最初から分割させて回避する。
            getMessage.FTE14328,
            ''
        );
    }

    if ( !parts.length ) return '';

    // 冒頭の共通指示（実績の水増し・数値の断定を防ぐ）と、選択項目を連結する。
    return getMessage.FTE14329.concat( '', parts ).join('\n')
        // 思考時間の実測値（応答ごとに保存した_thinkingMsの集計）を根拠データとして添える。
        // データが無ければ空文字なので、その場合は思考時間の節は出ない。
        + this.buildThinkingTimeReportSection();
}
/*
##################################################
    思考時間（LLMの応答往復時間）の集計
##################################################
*/
// 会話履歴に残したAI応答ごとの往復時間（_thinkingMs）を集計する。
// レポートで「実測値」として使うためのデータで、計測値が1件も無ければnullを返す。
// なお、ここでの思考時間はLLMの応答往復時間であり、ツールの実行時間は含まない。
collectThinkingTimeStats() {
    const history = this.llm?.getChatHistory();
    if ( !Array.isArray( history ) ) return null;

    const items = [];  // { order, ms, label, model }
    let order = 0;
    for ( const turn of history ) {
        if ( !turn || turn.role !== 'assistant') continue;
        // 何番目の応答かは、計測値の有無に関わらず数える（会話の流れと番号を合わせる）
        order++;
        if ( typeof turn._thinkingMs !== 'number' || !isFinite( turn._thinkingMs ) || turn._thinkingMs < 0 ) continue;
        items.push({
            order: order,
            ms: turn._thinkingMs,
            label: this.describeAssistantTurn( turn ),
            model: ( typeof turn._model === 'string' && turn._model )? turn._model: getMessage.FTE14330
        });
    }
    if ( !items.length ) return null;

    const durations = items.map(( item ) => item.ms );
    const total = durations.reduce(( a, b ) => a + b, 0 );
    // 時間がかかった応答の上位3件（同着は会話順）
    const slowest = [ ...items ].sort(( a, b ) => ( b.ms - a.ms ) || ( a.order - b.order ) ).slice( 0, 3 );

    // 会話の途中でモデルを切り替えられるため、モデル別にもまとめる
    const byModel = new Map();
    for ( const item of items ) {
        let group = byModel.get( item.model );
        if ( !group ) {
            group = { model: item.model, count: 0, total: 0, max: -Infinity, min: Infinity };
            byModel.set( item.model, group );
        }
        group.count++;
        group.total += item.ms;
        group.max = Math.max( group.max, item.ms );
        group.min = Math.min( group.min, item.ms );
    }
    const models = [ ...byModel.values() ]
        .map(( group ) => ({ ...group, avg: group.total / group.count }))
        .sort(( a, b ) => b.avg - a.avg );

    return {
        count: items.length,
        total: total,
        avg: total / items.length,
        max: Math.max( ...durations ),
        min: Math.min( ...durations ),
        slowest: slowest,
        models: models
    };
}
// AI応答のターンを、どの応答かが分かる短い文言にする（レポートの明細用）
describeAssistantTurn( turn ) {
    const content = ( Array.isArray( turn?.content ) )? turn.content: [];
    const textBlock = content.find(( block ) =>
        block && block.type === 'text' && typeof block.text === 'string' && block.text.trim() );
    if ( textBlock ) {
        const text = textBlock.text.trim().replace( /\s+/g, ' ');
        return ( text.length > 40 )? text.slice( 0, 40 ) + '…': text;
    }
    // テキストが無い応答（ツール呼び出しのみ）は、呼び出したツール名で示す
    const toolNames = content.filter(( block ) => block && block.type === 'tool_use' && block.name )
        .map(( block ) => block.name );
    if ( toolNames.length ) return getMessage.FTE14331( toolNames.join(', ') );
    return getMessage.FTE14332;
}
// 思考時間の集計を、レポートの根拠データとして指示文へ添える節にする。
// 計測値が無ければ空文字（節を付けない）。
buildThinkingTimeReportSection() {
    const stats = this.collectThinkingTimeStats();
    if ( !stats ) return '';

    const sec = ( ms ) => ( ms / 1000 ).toFixed( 1 );
    const lines = [
        getMessage.FTE14333,
        getMessage.FTE14334( stats.count ),
        getMessage.FTE14335( sec( stats.total ) ),
        getMessage.FTE14336( sec( stats.avg ) ),
        getMessage.FTE14337( sec( stats.min ), sec( stats.max ) ),
        getMessage.FTE14338
    ];
    for ( const item of stats.slowest ) {
        lines.push( getMessage.FTE14339( item.order, sec( item.ms ), item.model, item.label ) );
    }
    if ( stats.models.length >= 2 ) {
        lines.push( getMessage.FTE14340 );
        for ( const model of stats.models ) {
            lines.push( getMessage.FTE14341( model.model, model.count, sec( model.avg ), sec( model.min ), sec( model.max ) ) );
        }
    }
    lines.push( getMessage.FTE14342(
        ( stats.models.length >= 2 )? getMessage.FTE14343: ''
    ) );
    return '\n\n' + lines.join('\n');
}
/*
##################################################
    学習事項（次回セッションへの申し送り）
##################################################
*/
// 学習事項は「今回の会話から抽出 → ユーザーが確認・修正 → 登録」の3段階で登録する。
//
// ・保存先はプラットフォーム側の専用API（/lessons）。登録した学習事項のうち有効なものは、
//   次回以降の問い合わせでプラットフォーム側がシステムプロンプトへ自動的に反映するため、
//   画面側から前提知識として渡す処理（読み出し・差し込み）は行わない。
// ・重要度（priority）は 1（最低）〜 10（最高）の10段階。確認ダイアログで修正できる。
// ・抽出だけは会話を使う（prompt_profile が Lessons の会話。AiAssistantLlmの学習事項の節を参照）。
//   抽出用の会話は使い捨てのため、抽出が済んだらレコードごと削除する。

// 今回の会話から学習事項を抽出し、確認ダイアログを経て登録する。
// ・各段階の結果はシステム通知ブロックで表示する。
// ・ダイアログでキャンセル、または1件も選択されなかった場合は登録しない。
// ・失敗しても会話の終了自体は成立させたいので、例外はここで止める。
async confirmAndRecordLessons() {
    // 学習元として学習事項に残す会話ID（この会話がまだ未作成の場合はnull）
    const sourceConversationId = this.llm?.conversationId ?? null;
    const transcript = this.buildTranscript( this.llm?.getChatHistory() );
    if ( !transcript ) {
        this.updateChat({ role: 'systemNotice', text: getMessage.FTE14344 });
        return;
    }

    // 抽出は数秒かかる単発の問い合わせのため、処理中表示を出す
    let extracted = { conversationId: null, lessons: []};
    const processing = fn.processingModal( getMessage.FTE14345 );
    try {
        extracted = await AiAssistantLlm.extractLessons( transcript, {
            aiServiceId: this.setting.currentAiServiceId,
            modelId: this.modelId
        });
    } catch ( error ) {
        processing.close();
        console.warn('学習事項の抽出に失敗しました。', error );
        // 失敗しても、抽出用の会話には問い合わせ内容が残っていることがあるため消しておく
        await this.discardConversation( error?.conversationId, '学習事項の抽出');
        this.updateChat({ role: 'systemNotice',
            text: getMessage.FTE14346( this.formatErrorMessage( error ) ) });
        return;
    }
    processing.close();

    // 抽出用の会話は役目を終えた（学習事項の保存先ではないため、会話一覧に残さない）
    await this.discardConversation( extracted.conversationId, '学習事項の抽出');

    const lessons = this.normalizeLessons( extracted.lessons );
    if ( !lessons.length ) {
        this.updateChat({ role: 'systemNotice', text: getMessage.FTE14344 });
        return;
    }

    // 抽出結果をユーザーに確認させる（チェックで選択、本文・分類・重要度は編集できる）
    const selected = await this.openLessonsConfirmDialog( lessons );
    if ( selected === null || !selected.length ) {
        this.updateChat({ role: 'systemNotice', text: ( selected === null )
            ? getMessage.FTE14347
            : getMessage.FTE14348 });
        return;
    }

    const result = await this.registerLessons( selected, sourceConversationId );
    const failed = ( result.errors.length )
        ? getMessage.FTE14349( result.errors.length, result.errors.join('\n') )
        : '';
    // 上限を超えた場合は、学習事項タブでの整理を促す（登録そのものは成功している）
    const max = AiAssistantLlm.lessonsMaxCount;
    const over = ( result.totalCount !== null && result.totalCount > max )
        ? '\n' + getMessage.FTE14053( max, result.totalCount ): '';
    this.updateChat({ role: 'systemNotice', text: ( result.count > 0 )
        ? getMessage.FTE14350( result.count )
            + getMessage.FTE14065( AiAssistantLlm.lessonsPromptMaxCount ) + failed + over
        : getMessage.FTE14351 + failed });
}
// 使い捨ての会話（学習事項の抽出・タイトルの生成）を削除する。
// レコードごと削除するため、会話履歴の一覧にも残らない。
// purpose … 何に使った会話か（削除に失敗した場合のログに使う）
// （削除できなかった場合は会話一覧に残るが、抽出・生成の結果には影響しない）
async discardConversation( conversationId, purpose ) {
    if ( !conversationId ) return;
    try {
        await AiAssistantLlm.deleteConversation( conversationId );
    } catch ( error ) {
        console.warn(`${purpose}に使った会話の削除に失敗しました。`, error );
    }
}
// 会話履歴を、LLMへ渡す読みやすいテキスト（発言者＋本文）へ変換する。
// 学習事項の抽出・タイトルの生成のように、今回の会話の内容そのものを渡す処理で使う。
// maxLength … リクエストが大きくなりすぎないための上限文字数（超える分は中略する）
buildTranscript( history, maxLength = 8000 ) {
    if ( !Array.isArray( history ) ) return '';

    const lines = [];
    for ( const turn of history ) {
        // システム操作（会話終了など）の指示文は学習事項のノイズになるため除外する
        if ( turn?._displaySystem === true ) continue;
        if ( !Array.isArray( turn?.content ) ) continue;
        const roleLabel = ( turn.role === 'assistant')? getMessage.FTE14352: getMessage.FTE14353;
        for ( const [ blockIndex, block ] of turn.content.entries() ) {
            if ( block?.type !== 'text' || typeof block.text !== 'string') continue;
            // 保存時に差し込まれたテキスト（添付ファイルのメタ情報）は発言ではなく
            // ノイズになるため除外する
            // （復元した会話では、この文面もテキストブロックとして履歴に入っている）
            if ( AiAssistantLlm.isInjectedBlock( block, turn, blockIndex ) !== null ) continue;
            const text = block.text.trim();
            if ( text ) lines.push(`${roleLabel}: ${text}`);
        }
    }

    let transcript = lines.join('\n');
    // リクエストが大きくなりすぎないよう、長すぎる場合は先頭と末尾を残して中略する
    if ( transcript.length > maxLength ) {
        transcript = `${transcript.slice( 0, maxLength / 2 )}\n${getMessage.FTE14354}\n${transcript.slice( -maxLength / 2 )}`;
    }
    return transcript;
}
// 抽出結果を、確認ダイアログと登録APIで扱える形へ整える。本文が空のものは捨てる。
// 文字数の上限はプラットフォーム側のバリデーションに合わせて切り詰める
// （上限を超えるとエラーになるため、登録できずに捨てるより切り詰めて残す）。
normalizeLessons( lessons ) {
    if ( !Array.isArray( lessons ) ) return [];
    return lessons
        .filter(( item ) => item && typeof item.lesson === 'string' && item.lesson.trim() )
        .map(( item ) => ({
            lesson: String( item.lesson ).trim().slice( 0, AiAssistantLlm.lessonLength ),
            category: ( typeof item.category === 'string')
                ? item.category.trim().slice( 0, AiAssistantLlm.lessonCategoryLength ): '',
            // 抽出結果の重要度は、範囲外の数値や数値以外で返ることもあるため1〜10へ整える
            priority: AiAssistantLlm.lessonPriority( item.priority )
        }));
}
// 抽出した学習事項の確認ダイアログを表示する。
// ・各項目はチェックボックスで登録対象を選択でき、本文・分類・重要度はその場で修正できる。
// ・戻り値: 登録する学習事項の配列（1件も選ばなければ空配列）。キャンセル時はnull。
openLessonsConfirmDialog( lessons ) {
    return new Promise(( resolve ) => {
        const config = {
            position: 'center',
            width: '760px',
            header: { title: getMessage.FTE14355 },
            footer: {
                button: {
                    execute: { text: getMessage.FTE14356, action: 'positive', className: 'dialogPositive'},
                    cancel: { text: getMessage.FTE14316, action: 'normal'}
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
                // チェックされた項目だけを、画面上の編集内容（本文・分類・重要度）で拾い直す
                const selected = [];
                dialog.$.dialog.find('.aiLessonsItem').each(( i, el ) => {
                    const $item = $( el );
                    if ( !$item.find('.aiLessonsCheck').prop('checked') ) return;
                    const lesson = ( $item.find('.aiLessonsText').val() ?? '').trim();
                    if ( !lesson ) return;
                    selected.push({
                        lesson: lesson,
                        category: ( $item.find('.aiLessonsCategory').val() ?? '').trim(),
                        priority: $item.find('.aiLessonsPriority').val() ?? ''
                    });
                });
                finish( selected );
            },
            cancel: () => finish( null )
        };

        const prioritySelect = ( selected, index ) => `<select class="aiLessonsPriority input select" id="aiLessonsPriority_${index}">`
            + `${AiAssistantLlm.lessonPriorityOptions( selected )}</select>`;

        const items = lessons.map(( item, i ) => `
            <li class="aiLessonsItem">
                <div class="aiLessonsItemHead">
                    <label class="aiLessonsItemCheckLabel" for="aiLessonsCheck_${i}">
                        <input type="checkbox" id="aiLessonsCheck_${i}" class="aiLessonsCheck" checked>
                        <span class="aiLessonsItemCheckText">${getMessage.FTE14357}</span>
                    </label>
                    <div class="aiLessonsItemField">
                        <label class="aiLessonsItemFieldLabel" for="aiLessonsCategory_${i}">${getMessage.FTE14358}</label>
                        <input type="text" id="aiLessonsCategory_${i}" class="aiLessonsCategory input inputText" spellcheck="false" maxlength="${AiAssistantLlm.lessonCategoryLength}" value="${fn.escape( item.category ?? '')}">
                    </div>
                    <div class="aiLessonsItemField">
                        <label class="aiLessonsItemFieldLabel" for="aiLessonsPriority_${i}">${getMessage.FTE14359}</label>
                        ${prioritySelect( item.priority, i )}
                    </div>
                </div>
                <textarea class="aiLessonsText textarea input" spellcheck="false" rows="4" maxlength="${AiAssistantLlm.lessonLength}" aria-label="${getMessage.FTE14360}">${fn.escape( item.lesson ?? '')}</textarea>
            </li>`).join('');

        const html = `
        <div class="dialogBody">
            <div class="commonSection">
                <div class="aiLessonsDescription">${getMessage.FTE14361( AiAssistantLlm.lessonsPromptMaxCount )}</div>
                <div class="aiLessonsToolbar">
                    <label class="aiLessonsItemCheckLabel" for="aiLessonsAllCheck">
                        <input type="checkbox" id="aiLessonsAllCheck" class="aiLessonsAllCheck" checked>
                        <span class="aiLessonsItemCheckText">${getMessage.FTE14362}</span>
                    </label>
                    <div class="aiLessonsCount"><span class="aiLessonsSelectedCount">${lessons.length}</span> / ${getMessage.FTE14363( lessons.length )}</div>
                </div>
                <ul class="aiLessonsList">${items}</ul>
            </div>
        </div>`;

        dialog.open( html );

        const $dialog = dialog.$.dialog;
        // 選択件数の表示、全選択チェックの状態、登録ボタンの活性を選択状況に合わせて更新する
        const updateState = () => {
            const $checks = $dialog.find('.aiLessonsCheck');
            const checked = $checks.filter(':checked').length;
            $dialog.find('.aiLessonsSelectedCount').text( checked );
            $dialog.find('.aiLessonsAllCheck').prop('checked', checked === $checks.length );
            dialog.buttonPositiveDisabled( checked === 0 );
        };
        $dialog.on('change', '.aiLessonsAllCheck', function(){
            $dialog.find('.aiLessonsCheck').prop('checked', $( this ).prop('checked') );
            updateState();
        });
        $dialog.on('change', '.aiLessonsCheck', updateState );
        updateState();
    });
}
// 確認ダイアログで選択・修正された学習事項を、専用API（/lessons）へ1件ずつ登録する。
// sourceConversationId … 学習元の会話ID（学習事項に残す。未作成の場合はnull）
// 戻り値 { count, errors, totalCount } … count は登録できた件数、errors は登録できなかった項目の
// メッセージ、totalCount は登録後の学習事項の総件数（既存分を取得できなかった場合はnull）。
//
// 同じ内容の学習事項が積み上がらないよう、本文が一致する既存の学習事項があれば、
// 新規登録ではなく更新（PATCH）にする。既存分の取得に失敗した場合は、登録そのものは
// 妨げず新規登録として続ける（重複が残ることはあっても、登録できない方が困る）。
async registerLessons( lessons, sourceConversationId ) {
    const records = this.normalizeLessons( lessons );
    if ( !records.length ) return { count: 0, errors: [], totalCount: null };

    const processing = fn.processingModal( getMessage.FTE14364 );

    // 本文 → 既存の学習事項ID
    const registered = new Map();
    let totalCount = null;
    try {
        // 照合するのは、この会話と同じプロンプトプロファイルの学習事項だけ
        const existing = await AiAssistantLlm.fetchLessons({ promptProfile: this.promptProfile });
        totalCount = existing.totalCount;
        for ( const item of existing.lessons ) {
            if ( item?.lesson_id && typeof item.lesson === 'string') {
                registered.set( item.lesson.trim(), item.lesson_id );
            }
        }
    } catch ( error ) {
        console.warn('登録済みの学習事項の取得に失敗しました。すべて新規として登録します。', error );
    }

    let count = 0;
    const errors = [];
    for ( const record of records ) {
        try {
            const lessonId = registered.get( record.lesson );
            if ( lessonId ) {
                // 内容が同じものは、分類・重要度を今回の内容へ更新し、有効に戻す
                await AiAssistantLlm.updateLesson( lessonId, {
                    category: record.category,
                    priority: record.priority,
                    enabled: true
                });
            } else {
                await AiAssistantLlm.createLesson({ ...record, conversationId: sourceConversationId,
                    promptProfile: this.promptProfile });
                // 総件数は新規登録した分だけ増える（更新した分は増えない）
                if ( totalCount !== null ) totalCount++;
            }
            count++;
        } catch ( error ) {
            console.warn('学習事項の登録に失敗しました。', record, error );
            // どの項目が記録できなかったか分かるよう、本文の先頭だけを添える
            const head = record.lesson.split('\n')[0];
            errors.push( getMessage.FTE14365(
                ( head.length > 40 )? head.slice( 0, 40 ) + '…': head,
                this.formatErrorMessage( error )
            ) );
        }
    }

    processing.close();
    return { count: count, errors: errors, totalCount: totalCount };
}
/*
##################################################
    会話のタイトルの生成（AIに付けてもらう）
##################################################
*/
// 今回の会話の内容から、AIにタイトルを考えてもらってこの会話へ保存する。
//
// ・会話のタイトルは最初の発言から機械的に作られる（AiAssistantLlm.buildTitle）ため、
//   会話の内容を表していないことがある。チャットの終了時に、その会話が何だったのかが
//   ひと目で分かるタイトルへ付け替えるのがこの処理。
// ・タイトルは会話履歴の一覧での目印にのみ使われるため、付け替えても保存されている履歴・
//   AIの記憶は変わらない（気に入らない場合は会話履歴タブから編集できる）。
// ・生成はこの会話とは別の使い捨ての会話（prompt_profile = GenerateTitle）で行い、
//   済んだらその会話はレコードごと削除する。
// ・各段階の結果はシステム通知ブロックで表示する。
// ・失敗しても会話の終了自体は成立させたいので、例外はここで止める。
async generateAndSaveTitle() {
    // 保存先の会話（この会話。1回でも送信していれば作成済み）
    const conversationId = this.llm?.conversationId ?? null;
    if ( !conversationId ) {
        this.updateChat({ role: 'systemNotice',
            text: getMessage.FTE14366 });
        return;
    }

    // タイトルは会話の主題が分かれば付けられるため、学習事項の抽出より短い範囲を渡す
    const transcript = this.buildTranscript( this.llm?.getChatHistory(), 4000 );
    if ( !transcript ) {
        this.updateChat({ role: 'systemNotice',
            text: getMessage.FTE14367 });
        return;
    }

    // 生成は数秒かかる単発の問い合わせのため、処理中表示を出す
    let generated = { conversationId: null, title: ''};
    const processing = fn.processingModal( getMessage.FTE14368 );
    try {
        generated = await AiAssistantLlm.generateTitle( transcript, {
            aiServiceId: this.setting.currentAiServiceId,
            modelId: this.modelId
        });
    } catch ( error ) {
        processing.close();
        console.warn('会話のタイトルの生成に失敗しました。', error );
        // 失敗しても、生成用の会話には問い合わせ内容が残っていることがあるため消しておく
        await this.discardConversation( error?.conversationId, 'タイトルの生成');
        this.updateChat({ role: 'systemNotice',
            text: getMessage.FTE14369( this.formatErrorMessage( error ) ) });
        return;
    }
    processing.close();

    // 生成用の会話は役目を終えた（タイトルの保存先ではないため、会話一覧に残さない）
    await this.discardConversation( generated.conversationId, 'タイトルの生成');

    if ( !generated.title ) {
        this.updateChat({ role: 'systemNotice', text: getMessage.FTE14370 });
        return;
    }

    // 生成できたタイトルをこの会話へ保存する（会話履歴の一覧に反映される）
    try {
        await AiAssistantLlm.updateConversationTitle( conversationId, generated.title );
    } catch ( error ) {
        console.warn('会話のタイトルの保存に失敗しました。', error );
        this.updateChat({ role: 'systemNotice',
            text: getMessage.FTE14371( this.formatErrorMessage( error ) ) });
        return;
    }

    this.updateChat({ role: 'systemNotice',
        text: getMessage.FTE14372( generated.title ) });
}
// AIサービス設定
async aiAssistantSettingEvent() {
    await this.setting.open();
}
/*
##################################################
    Bodyイベント
##################################################
*/
// Body内のクリック操作（data-type単位）。
// 読み取り専用の操作（プレビュー・コピー・状態確認など）は whileRunning: true で
// 応答処理中でも実行できるようにしている。
bodyEventActions = {
    // 送信・停止
    send:   { lockButton: true, run:() => this.sendMessage( this.elements.message.value ) },
    choice: { lockButton: true, run:( button ) => this.sendMessage( button.innerText ) },
    stop:   { whileRunning: true, run:() => this.stopMessage() },

    // 添付ファイル
    file:              { lockButton: true, run:() => this.fileSelect() },
    fileRemove:        { lockButton: true, run:( button ) => this.removeFile( Number( button.dataset.index ) ) },
    fileEdit:          { lockButton: true, run:( button ) => this.editFile( Number( button.dataset.index ) ) },
    filePreview:       { lockButton: true, run:( button ) => this.previewFile( Number( button.dataset.index ) ) },
    // 吹き出し内の画像サムネイル（添付時と同じプレビューを開く）
    attachmentPreview: { whileRunning: true, run:( el ) => this.previewAttachment( el.dataset.previewUrl, el.dataset.filename ) },

    // 会話の巻き戻し
    rewindToHere: { lockButton: true, run:( button ) => this.rewindToHere( button ) },

    // Movement（作業実行）
    movementStatusCheck:    { whileRunning: true, run:( button ) => this.movementExecuteCheck( button ) },
    movementResultDownload: { whileRunning: true, run:( button ) => this.movementResultDownload( button ) },
    movementEmergencyStop:  { whileRunning: true, run:( button ) => this.movementStop( button ) },

    // コードブロック・表示専用HTML
    codeCopy:       { whileRunning: true, run:( button ) => this.copyCodeBlock( button ) },
    codeToInput:    { whileRunning: true, run:( button ) => this.setCodeBlockToInput( button ) },
    codeToEditor:   { whileRunning: true, run:( button ) => this.setCodeBlockToEditor( button ) },
    displayHtmlPdf: { whileRunning: true, run:( button ) => this.printDisplayHtmlAsPdf( button ) }
}
bindBodyEvents() {
    const body = this.elements.body;

    // クリック（bodyEventActionsで一括処理）
    this.delegate( body, 'click', '[data-type]',
        ( e, target ) => this.runEventAction( this.bodyEventActions, target, e ), { whileRunning: true });

    // 入力欄のキー操作（Enter送信・Alt+Enter改行）
    this.delegate( body, 'keydown', '.aiAssistantInputTextarea',
        ( e, textarea ) => this.inputKeydown( e, textarea ), { whileRunning: true });

    // 入力欄への貼り付け（画像はファイルとして添付する）
    this.delegate( body, 'paste', '.aiAssistantInputTextarea', ( e ) => this.pasteAttachment( e ) );

    // 添付ファイルのLLM送信トグル
    this.delegate( body, 'change', '[data-type="fileToggle"]',
        ( e, check ) => this.toggleFileLlm( Number( check.dataset.index ) ), { whileRunning: true });

    // 入力欄へのファイルドラッグ&ドロップ
    this.bindComposerDragEvents( body );

    // Movementノードのホバー表示・作業状態確認
    this.bindMovementNodeEvents( body );
}
// 入力欄のキーダウン
async inputKeydown( e, textarea ) {
    if ( e.key !== 'Enter') return;

    // Excelの癖（Alt+Enter／MacはOption+Enter）でも改行できるようにする。
    // Alt+Enterの既定動作はブラウザやOSで一定しないため、明示的に改行を挿入する。
    // Ctrl+Enterは他アプリで「送信」の意味が強いため割り当てない。
    if ( e.altKey && !e.ctrlKey && !e.metaKey ) {
        e.preventDefault();
        textarea.setRangeText('\n', textarea.selectionStart, textarea.selectionEnd, 'end');
        textarea.dispatchEvent( new Event('input', { bubbles: true }) );
        return;
    }

    // IME変換中の確定Enterで送信しないようにする。
    if ( e.isComposing || e.keyCode === 229 ) return;

    // Shift+Enterは改行（既定動作のまま）
    if ( e.shiftKey ) return;

    // Enterは送信ボタンのクリックと同じ処理を行う（連打防止のロックも共通）
    e.preventDefault();
    if ( this.isRunning ) return;
    const sendButton = this.elements.body.querySelector('.aiAssistantInputActionsSendButton');
    if ( sendButton ) await this.runEventAction( this.bodyEventActions, sendButton, e );
}
// 入力欄への貼り付け
// スクリーンショットやコピーした画像をペーストした場合、テキストではなく
// 添付ファイルとして扱う（ドラッグ&ドロップと同じ setFile 経路に流す）。
pasteAttachment( e ) {
    // クリップボード内の画像ファイルだけを取り出す。
    const imageFiles = Array.from( e.clipboardData?.items ?? [] )
        .filter(( item ) => item.kind === 'file' && ( item.type ?? '').startsWith('image/') )
        .map(( item ) => item.getAsFile() )
        .filter(( file ) => file )
        .map(( file ) => this.normalizePastedImageFile( file ) );
    if ( !imageFiles.length ) return;

    // 画像を添付として扱うため、テキストへの貼り付け（＝ゴミ文字混入）は抑止する。
    e.preventDefault();
    // 貼り付け画像は解析ONで追加する（そのままAIが読み取れるようにする）。
    this.setFile( imageFiles, { useLlm: true });
}
// 入力欄へのファイルドラッグ&ドロップ
// ドラッグの出入りは子要素をまたぐ度に発火するため、深度カウンタでちらつきを防ぐ。
bindComposerDragEvents( body ) {
    const composerSelector = '.aiAssistantChatComposer';
    // ファイル以外のドラッグ（テキスト選択など）は対象外
    const hasFiles = ( e ) => Array.from( e.dataTransfer?.types ?? [] ).includes('Files');
    const setDragover = ( composer, dragover ) => composer.classList.toggle('aiAssistantChatComposerDragover', dragover );
    let dragDepth = 0;

    this.delegate( body, 'dragenter', composerSelector, ( e, composer ) => {
        if ( !hasFiles( e ) ) return;
        e.preventDefault();
        dragDepth++;
        setDragover( composer, true );
    });
    this.delegate( body, 'dragover', composerSelector, ( e ) => {
        if ( !hasFiles( e ) ) return;
        // preventDefaultしないとdropが発火しない
        e.preventDefault();
        if ( e.dataTransfer ) e.dataTransfer.dropEffect = 'copy';
    });
    // ドラッグ解除・ドロップは、応答処理中でもドラッグ表示を必ず戻す
    this.delegate( body, 'dragleave', composerSelector, ( e, composer ) => {
        if ( !hasFiles( e ) ) return;
        dragDepth--;
        if ( dragDepth > 0 ) return;
        dragDepth = 0;
        setDragover( composer, false );
    }, { whileRunning: true });
    this.delegate( body, 'drop', composerSelector, ( e, composer ) => {
        if ( !hasFiles( e ) ) return;
        e.preventDefault();
        dragDepth = 0;
        setDragover( composer, false );
        if ( this.isRunning ) return;
        const files = Array.from( e.dataTransfer?.files ?? [] );
        if ( files.length ) this.setFile( files );
    }, { whileRunning: true });
}
// Movementノード（作業実行の進捗表示）
// クリックでの作業状態確認は bodyEventActions ではなく、data-type を持たない
// .node-result 自体が対象のためここで個別に登録する。
bindMovementNodeEvents( body ) {
    const nodeSelector = '.node-result';
    // mouseover／mouseoutは子要素をまたぐ度に発火するため、
    // .node-result内の移動（mouseenter／mouseleave相当）は無視する
    const isInnerMove = ( e, result ) => result.contains( e.relatedTarget );

    this.delegate( body, 'mouseover', nodeSelector, ( e, result ) => {
        if ( isInnerMove( e, result ) ) return;
        result.classList.add('mouseenter');
    }, { whileRunning: true });
    this.delegate( body, 'mouseout', nodeSelector, ( e, result ) => {
        if ( isInnerMove( e, result ) ) return;
        result.classList.remove('mouseenter');
    }, { whileRunning: true });
    this.delegate( body, 'click', nodeSelector, ( e, result ) => {
        this.movementExecuteCheck( result );
    }, { whileRunning: true });
}
// この吹き出し（ユーザ発言）の時点まで会話を巻き戻す
rewindToHere( button ) {
    const bubble = button.closest('.aiAssistantChatUserMessage');
    return this.rewindConversation( bubble ? Number( bubble.dataset.historyIndex ): NaN );
}
// コードブロックをクリップボードへコピーする
copyCodeBlock( button ) {
    // 連打防止：コピー直後の短い間は再実行しない
    if ( button.classList.contains('aiAssistantChatCodeButtonCopied') ) return;
    // 色は変えず、押した合図に少しだけ薄く表示する
    button.classList.add('aiAssistantChatCodeButtonCopied');
    setTimeout( () => button.classList.remove('aiAssistantChatCodeButtonCopied'), 800 );
    return this.copyToClipboard( this.getCodeBlockText( button ) );
}
// コードブロックの内容を入力欄へセットする（送信はしない）
setCodeBlockToInput( button ) {
    if ( !this.elements.message ) return;
    this.elements.message.value = this.getCodeBlockText( button );
    this.elements.message.focus();
}

// エディターへコードブロックを反映（オーバーライド用）
// ai_assistant_editor.js でオーバーライドされる。
// デフォルト実装は提供しない。
setCodeBlockToEditor( button ) {
    // オーバーライドされていない場合は何もしない
}

/*
##################################################
    Footerイベント
##################################################
*/
// モデルの選択肢は普段隠れているため、モデル名のクリックで開閉する。
// フッターは更新のたびに作り直すため、イベントはフッターへ委譲して1度だけ設定する。
bindFooterEvents() {
    const footer = this.elements.footer;

    // 応答処理中でも選択肢は開けるようにする（実際の切り替えはselectModelで止める）
    this.delegate( footer, 'click', '.modelSelectedName', () => {
        this.toggleFooterModelList();
    }, { whileRunning: true });

    this.delegate( footer, 'change', '.modelSelectRadio', ( e, radio ) => {
        this.selectModel( radio.value );
    }, { whileRunning: true });

    // 使用中のモデルを選び直した場合はchangeが発生しないため、クリックでも閉じる
    this.delegate( footer, 'click', '.modelSelectLabel', () => {
        this.closeFooterModelList();
    }, { whileRunning: true });

    // 選択肢の外側をクリックしたら閉じる
    document.addEventListener('click', ( e ) => {
        if ( e.target?.closest?.('.modelSelectWrap') ) return;
        this.closeFooterModelList();
    }, { signal: this.ac.signal });
}
// モデルの選択肢の開閉
toggleFooterModelList() {
    this.elements.modelList?.querySelector('.modelSelectList')?.classList.toggle('modelSelectOpen');
}
closeFooterModelList() {
    this.elements.modelList?.querySelector('.modelSelectList')?.classList.remove('modelSelectOpen');
}
// 使用するモデルを切り替える
selectModel( modelId ) {
    this.closeFooterModelList();

    // 応答処理中の切り替えは、送信中のやり取りと表示が食い違うため受け付けない。
    // ラジオは操作した時点で切り替わっているので、使用中のモデルへ戻す。
    if ( this.isRunning || !modelId ) {
        this.updateFooterModelList();
        return;
    }

    // 切り替えたモデルは次の送信時にLLMへ反映する（会話は作り直さない）
    this.modelId = modelId;

    const modelName = this.setting.currentPickupModels.find(( item ) => item.id === modelId )?.name ?? '';
    const selectedName = this.elements.modelList?.querySelector('.modelSelectedName');
    if ( selectedName ) selectedName.innerText = modelName;
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   ユーティリティ
//
////////////////////////////////////////////////////////////////////////////////////////////////////
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
    スリープ
##################################################
*/
sleep( time ) {
    return new Promise( ( resolve ) => setTimeout( resolve, time ) );
}
/*
##################################################
    fetch リトライ
##################################################
*/
// fetch の応答エラー／ネットワークエラー時にリトライする共通処理（LLM・ツール実行で共用）。
// - AbortError（ユーザ都合の停止）はリトライせず即座に throw する。
// - 一時的なHTTPステータス（408 / 425 / 429 / 5xx）や fetch 例外（ネットワーク断）で再試行する。
// - 指数バックオフ（baseDelay を 2倍ずつ）で待機。Retry-After ヘッダがあればそれを優先し、
//   signal 経由で待機を即座に中断できる。
// - リトライを使い切った場合は最後の Response をそのまま返す（呼び出し側の .ok 判定を維持）。
static async fetchWithRetry( url, options = {}, retryOptions = {} ) {
    const retries = retryOptions.retries ?? 2;            // 追加試行回数（初回 + retries 回）
    const baseDelay = retryOptions.baseDelay ?? 1000;     // 初回リトライ前の待機（ミリ秒）
    const retryStatuses = retryOptions.retryStatuses ?? [ 408, 425, 429, 500, 502, 503, 504 ];
    const signal = options.signal;

    // signal が abort されたら待機を即座に打ち切る、リトライ待機用の sleep
    const wait = ( delay ) => new Promise(( resolve ) => {
        if ( signal?.aborted ) { resolve(); return; }
        const timer = setTimeout(() => {
            signal?.removeEventListener?.('abort', onAbort );
            resolve();
        }, delay );
        const onAbort = () => { clearTimeout( timer ); resolve(); };
        signal?.addEventListener?.('abort', onAbort, { once: true });
    });

    let lastError = null;
    for ( let attempt = 0; attempt <= retries; attempt++ ) {
        // 中断済みなら即座に AbortError
        if ( signal?.aborted ) {
            const err = new Error('Aborted');
            err.name = 'AbortError';
            throw err;
        }
        try {
            const response = await fetch( url, options );
            // 応答エラー（リトライ対象ステータス）で、まだ試行が残っていれば待機して再試行
            if ( retryStatuses.includes( response.status ) && attempt < retries ) {
                lastError = new Error(`HTTP ${response.status}`);
                // 待機時間：指数バックオフ。Retry-After ヘッダがあれば優先。
                let delay = baseDelay * Math.pow( 2, attempt );
                const retryAfter = response.headers?.get?.('Retry-After');
                if ( retryAfter ) {
                    const sec = Number( retryAfter );
                    if ( !Number.isNaN( sec ) ) delay = sec * 1000;
                }
                console.warn(`fetchWithRetry: 応答エラー HTTP ${response.status}。${delay}ms 後にリトライします（${attempt + 1}/${retries}）。`, url );
                await wait( delay );
                continue;
            }
            return response;
        } catch ( error ) {
            // ユーザ都合の停止はリトライしない
            if ( error?.name === 'AbortError' || signal?.aborted ) throw error;
            lastError = error;
            // 試行が残っていなければ throw（ネットワークエラーをそのまま呼び出し側へ）
            if ( attempt >= retries ) throw error;
            const delay = baseDelay * Math.pow( 2, attempt );
            console.warn(`fetchWithRetry: fetch 失敗。${delay}ms 後にリトライします（${attempt + 1}/${retries}）。`, url, error );
            await wait( delay );
        }
    }
    // ループを抜けるのは通常ないが、保険として最後のエラーを投げる
    if ( lastError ) throw lastError;
}

}