////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Exastro IT Automation / ai_assistant_tool_download_attachment_file.js
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

// 画面専用ツール「download_attachment_file」（添付ファイルのダウンロード）。
//
// ・MCPサーバーではなく画面側（このクラス）で実行するツール。ツール定義（LLMへ渡す内容）と
//   その動作を1ファイルにまとめている。
// ・file_id を受け取り、チャット欄にファイル名とダウンロードボタンを持つ吹き出しを表示する。
//   自動ではダウンロードせず、ユーザーがボタンを押したときに
//   MCPサーバーの GET mcp/attachment_file/{file_id}/download からファイル本体を取得して保存させる。
// ・ツール実行時はメタ情報（GET mcp/attachment_file/{file_id}）だけを取得し、
//   ファイルの有無の確認と、ファイル名・サイズの表示に使う。
// ・履歴復元時も同じ吹き出し（ボタン）を再表示する。
// ・ファイルの内容はLLMには返らない（成功可否とファイル名等のメタ情報のみ返す）。
class AiAssistantToolDownloadAttachmentFile {
/*
##################################################
   ツール定義
##################################################
*/
static get toolName() {
    return 'download_attachment_file';
}
// 添付ファイルのメタ情報取得URL
static metaUrl( fileId ) {
    const { organizationId, workspaceId } = fn.getCommonParams();
    return `/api/${organizationId}/workspaces/${workspaceId}/mcp/attachment_file/${encodeURIComponent( fileId )}`;
}
// 添付ファイルのダウンロードURL
static downloadUrl( fileId ) {
    const { organizationId, workspaceId } = fn.getCommonParams();
    return `/api/${organizationId}/workspaces/${workspaceId}/mcp/attachment_file/${encodeURIComponent( fileId )}/download`;
}
// LLMへ渡すツール定義（MCPのtools/listと同じ形式。inputSchemaはLLM層でinput_schemaへ変換される）
static get definition() {
    return {
        name: AiAssistantToolDownloadAttachmentFile.toolName,
        description: 'file_id で指定した添付ファイルを、ユーザーがダウンロードできるようにするための画面専用ツール。'
            + 'create-attachment-text-file・create-attachment-zip-file などで作成したファイルや、ユーザーが添付したファイルをユーザーに渡したいときに使う。'
            + '呼び出すとチャット欄にダウンロードボタンが表示され、ユーザーがそのボタンを押すとダウンロードされる（自動ではダウンロードされない）。'
            + '呼び出した後は、テキスト応答で「ダウンロードボタンを押してファイルを保存してください」とユーザーに案内すること。'
            + '重要: ファイルの中身をテキスト応答（Markdown）に貼り付けてユーザーにコピーさせるのではなく、このツールでダウンロードさせること。'
            + '複数のファイルを渡す場合は、可能であれば create-attachment-zip-file で1つにまとめてから、このツールを1回だけ呼ぶこと。'
            + '注意: ファイルの内容はLLMには返らない（成功可否とファイル名・サイズのみ返る）。',
        inputSchema: {
            type: 'object',
            properties: {
                file_id: {
                    type: 'string',
                    description: 'ダウンロードさせる添付ファイルの file_id。'
                },
                filename: {
                    type: 'string',
                    description: '保存時のファイル名（任意）。省略時は登録されているファイル名を使う。'
                }
            },
            required: [ 'file_id' ]
        }
    };
}
/*
##################################################
   Constructor
##################################################
*/
// chat … AiAssistantChat（吹き出しの生成・スクロール・トークン取得はチャット側に委ねる）
constructor( chat ) {
    this.chat = chat;
}
/*
##################################################
   実行（ダウンロード）
##################################################
*/
// LLMから渡された file_id のメタ情報を取得し、ダウンロードボタンの吹き出しを表示する。
// 自動ではダウンロードしない（ユーザーがボタンを押したときに取得する）。
// LLMには成功可否とメタ情報だけを tool_result で返す（失敗時は is_error で伝える）。
async execute( toolUse ) {
    const input = toolUse.arguments ?? toolUse.input ?? {};
    const fileId = typeof input.file_id === 'string' ? input.file_id.trim() : '';
    const requestName = typeof input.filename === 'string' ? input.filename.trim() : '';

    // 待機中（思考中）インジケータが残っていれば消してから表示する。
    this.chat.elements.chatList
        ?.querySelectorAll('.aiAssistantChatItemLoading')
        .forEach(( item ) => item.remove() );

    try {
        if ( !fileId ) throw new Error('file_id is required');
        const meta = await this.fetchMeta( fileId );
        const filename = requestName || meta.filename || fileId;
        const size = Number( meta.size ) || 0;

        const el = this.appendElement( fileId, filename, size );
        if ( el ) setTimeout(() => { this.chat.scrollChatArea( el ); }, 100 );

        return {
            type: 'tool_result',
            tool_use_id: toolUse.id ?? '',
            content: getMessage.FTE14409( filename, size )
        };
    } catch ( error ) {
        console.error( error );
        return {
            type: 'tool_result',
            tool_use_id: toolUse.id ?? '',
            is_error: true,
            content: getMessage.FTE14410( fileId, error?.message ?? String( error ) )
        };
    }
}
/*
##################################################
   履歴からの復元
##################################################
*/
// 履歴復元時は吹き出し（ダウンロードボタン）を再表示する。
// 履歴に残るのはツールの入力（file_id / filename）だけでサイズは無いため、
// 吹き出しを先に出してからメタ情報を非同期に取得し、サイズ（とファイル名）を後から埋める。
// 取得できない（期限切れ等）場合は空欄のままにする（ボタン押下時に期限切れを伝える）。
resume( toolUse ) {
    const input = toolUse.arguments ?? toolUse.input ?? {};
    const fileId = typeof input.file_id === 'string' ? input.file_id.trim() : '';
    if ( !fileId ) return;
    const filename = typeof input.filename === 'string' ? input.filename.trim() : '';

    const el = this.appendElement( fileId, filename, null );
    if ( !el ) return;
    this.fetchMeta( fileId ).then(( meta ) => {
        const sizeEl = el.querySelector('.aiAssistantChatDownloadFileSize');
        if ( sizeEl && meta?.size !== undefined ) {
            sizeEl.textContent = this.chat.formatFileSize( meta.size );
        }
        // filename 未指定時は file_id を表示しているため、登録されているファイル名に差し替える
        const nameEl = el.querySelector('.aiAssistantChatDownloadFileName');
        if ( nameEl && !filename && meta?.filename ) {
            nameEl.textContent = meta.filename;
        }
    }).catch(() => {
        // 期限切れ等で取得できない場合は何もしない
    });
}
/*
##################################################
   ファイル取得
##################################################
*/
// メタ情報API・ダウンロードAPIへGETする（エラー時は例外を投げる）。
// fn.getFile はITAのREST API（/ita配下）向けのURLに変換するため使わず、直接 fetch する。
async request( url ) {
    const response = await fetch( url, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${this.chat.getToken()}`
        }
    });

    // 対象が無い（404）のは、保存期限切れでバックヤードに削除された場合。
    // 履歴の吹き出しから押されることが多いため、期限切れとして伝える。
    if ( response.status === 404 ) {
        const error = new Error( getMessage.FTE14413 );
        error.expired = true;
        throw error;
    }
    // エラー時は本文にerror/messageが入る（サーバー内部エラーではJSONで返らない場合もある）
    if ( !response.ok ) {
        const json = await response.json().catch( () => null );
        throw new Error( json?.message ?? getMessage.FTE14411( response.status ) );
    }
    return response;
}
// メタ情報API（file_id/filename/mime_type/size）を取得する。
async fetchMeta( fileId ) {
    const response = await this.request( AiAssistantToolDownloadAttachmentFile.metaUrl( fileId ) );
    return await response.json();
}
// ダウンロードAPIからファイル本体（Blob）とファイル名を取得する。
async fetchFile( fileId ) {
    const response = await this.request( AiAssistantToolDownloadAttachmentFile.downloadUrl( fileId ) );
    const blob = await response.blob();
    const filename = this.parseFilename( response.headers.get('Content-Disposition') ) || fileId;
    return { blob, filename };
}
// Content-Disposition からファイル名を取り出す。
// 非ASCIIのファイル名は filename*=UTF-8''... で返るため、そちらを優先する。
parseFilename( disposition ) {
    if ( !disposition ) return '';
    const extended = /filename\*\s*=\s*(?:UTF-8|utf-8)''([^;\n]+)/.exec( disposition );
    if ( extended?.[1] ) {
        try {
            return decodeURIComponent( extended[1].trim() );
        } catch ( error ) {
            // デコードできない場合は filename= の値を使う
        }
    }
    const plain = /filename\s*=\s*(?:"([^"]*)"|([^;\n]*))/.exec( disposition );
    return ( plain?.[1] ?? plain?.[2] ?? '').trim();
}
/*
##################################################
   ダウンロードボタン
##################################################
*/
// 吹き出しのダウンロードボタンから、同じファイルを再取得してダウンロードする。
async downloadFromButton( button ) {
    const fileId = button?.dataset?.fileId;
    if ( !fileId ) return;
    button.disabled = true;
    try {
        const file = await this.fetchFile( fileId );
        await fn.download('file', file.blob, button.dataset.filename || file.filename );
    } catch ( error ) {
        console.error( error );
        alert( error?.expired ? getMessage.FTE14413 : getMessage.FTE00179 );
    }
    button.disabled = false;
}
/*
##################################################
   吹き出し
##################################################
*/
// 吹き出しを生成してチャット欄へ追加する（ライブ表示・履歴復元で共用）。
appendElement( fileId, filename, size ) {
    const chatList = this.chat.elements.chatList;
    if ( !chatList ) return null;

    const el = this.createElement( fileId, filename, size );
    // 直前がアシスタントなら連続クラスを付与（他の吹き出しと同じ体裁）
    const prevItem = chatList.lastElementChild;
    if ( prevItem?.classList.contains('aiAssistantChatAssistantMessage') ) {
        el.classList.add('aiAssistantChatAssistantMessageChain');
    }
    chatList.append( el );
    return el;
}
// 吹き出し（アシスタントメッセージ枠 + ファイル名・サイズ・ダウンロードボタン）を生成する。
// filename が空（履歴復元で未指定）のときは file_id を表示し、保存名はサーバー側の名前に任せる。
createElement( fileId, filename, size ) {
    const el = this.chat.createAssistantMessageElement('', false );
    const inner = el.querySelector('.aiAssistantChatAssistantMessageInner');
    inner.classList.add('aiAssistantChatDownloadFileInner');

    // サイズ欄は履歴復元時に後から埋めるため、サイズ不明でも空の要素を置いておく。
    const sizeHtml = `<span class="aiAssistantChatDownloadFileSize">`
        + ( typeof size === 'number' ? this.chat.formatFileSize( size ) : '')
        + `</span>`;
    // fn.html.button は属性値をエスケープせず、キー名もそのまま data- に付けるため、
    // 値はここでエスケープし、dataset.fileId で読めるようキーはハイフン区切りにする。
    // 案内文 ＋ 保存期間の注意書き（保存日数は画面側では分からないため期間は明示しない）
    inner.innerHTML = `<div class="aiAssistantChatDownloadFileGuide">${getMessage.FTE14414}</div>`
        + `<div class="aiAssistantChatDownloadFileNote">${getMessage.FTE14415}</div>`
        + `<div class="aiAssistantChatDownloadFile">`
        + `<span class="aiAssistantChatDownloadFileName">${fn.escape( filename || fileId )}</span>`
        + sizeHtml
        + fn.html.button(
            fn.html.icon('download') + getMessage.FTE14412,
            'itaButton aiAssistantChatDownloadFileButton',
            {
                type: 'downloadAttachmentFile',
                action: 'default',
                'file-id': fn.escape( fileId ),
                filename: fn.escape( filename ?? ''),
                title: getMessage.FTE14412
            }
        )
        + `</div>`;
    return el;
}

}
