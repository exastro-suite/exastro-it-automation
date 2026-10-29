////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Exastro IT Automation / ai_assistant_tool_ask_user_choice.js
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

// 画面専用ツール「ask_user_choice」（ユーザーへの選択肢表示）。
//
// ・MCPサーバーではなく画面側（このクラス）で実行するツール。ツール定義（LLMへ渡す内容）と
//   その動作を1ファイルにまとめている。
// ・LLMへ渡す使い方のルールは description に持たせる（システムプロンプトはプラットフォーム側が
//   保持しており、画面側からは追記できないため）。
// ・このツールは即座に結果を返さない。選択肢を表示して制御をユーザーへ戻し、ユーザーが選んだ
//   ラベル（または自由記述）を次の送信時に tool_result として返す（AiAssistantChat.sendMessage）。
class AiAssistantToolAskUserChoice {
/*
##################################################
   ツール定義
##################################################
*/
static get toolName() {
    return 'ask_user_choice';
}
// LLMへ渡すツール定義（MCPのtools/listと同じ形式。inputSchemaはLLM層でinput_schemaへ変換される）
static get definition() {
    return {
        name: AiAssistantToolAskUserChoice.toolName,
        description: 'ユーザーに同意確認（はい/いいえ等）や複数案からの選択を求めるためのツール。'
            + '選択肢は options に指定する。ユーザーが選んだラベルが結果として返る。'
            + 'テキストで質問を重ねず、質問文は question に入れること。'
            + '各選択肢にはボタンの見た目を決める action（positive / negative / other）を指定できる。'
            + '\n【使い方のルール】'
            + '\n・ユーザーに「はい/いいえ」などの同意確認を求めるときや、複数の案から選んでもらうときは必ずこのツールを使う。'
            + '\n・重要: すべての選択肢は必ず options という1つの配列にまとめ、このツールは1回だけ呼び出すこと。'
            + '選択肢ごとに呼び出しを分けたり、label / action を options の外側に置いてはいけない。'
            + '\n・質問文は question に入れ、テキスト応答で同じ質問を重ねて書かないこと。'
            + '\n・自由記述での回答が必要な場合や、単に情報を伝えるだけの場合はこのツールを使わないこと。'
            + '\n・ユーザーへの確認は複数項目を一度に行わず、1つずつ確認すること。',
        inputSchema: {
            type: 'object',
            properties: {
                question: {
                    type: 'string',
                    description: 'ユーザーに提示する質問文。'
                },
                options: {
                    type: 'array',
                    description: 'ユーザーが選べる選択肢の一覧（2件以上）。',
                    items: {
                        type: 'object',
                        properties: {
                            label: {
                                type: 'string',
                                description: 'ボタンに表示する選択肢のラベル。'
                            },
                            action: {
                                type: 'string',
                                enum: [ 'positive', 'negative', 'other' ],
                                description: '選択肢の意味合い。'
                                    + '肯定的な操作（はい / 承認 / 実行 など）は positive、'
                                    + '否定的な操作（いいえ / 拒否 / キャンセル など）は negative、'
                                    + 'それ以外は other を指定する。省略時は other 扱い。'
                            }
                        },
                        required: [ 'label' ]
                    },
                    minItems: 2
                }
            },
            required: [ 'question', 'options' ]
        }
    };
}
/*
##################################################
   Constructor
##################################################
*/
// chat … AiAssistantChat（画面の描画・状態管理はチャット側に委ねる）
constructor( chat ) {
    this.chat = chat;
}
/*
##################################################
   実行（選択肢の表示）
##################################################
*/
// 質問文をアシスタントメッセージとして表示し、選択肢のボタンを追加する。
// tool_result はこの場では返さない（ユーザーの回答を次の送信で tool_result として返す）ため、
// 戻り値は null。
execute( toolUse ) {
    const input = toolUse.arguments ?? toolUse.input ?? {};
    const question = typeof input.question === 'string' ? input.question : '';
    // options は文字列配列（旧形式）／オブジェクト配列（新形式）を許容する。
    // さらに、モデルのフォーマット崩れで options 自体が文字列化されている場合も救済する。
    const options = this.extractOptions( input );

    // 質問文をアシスタントメッセージとして表示
    if ( question ) {
        this.chat.updateChat({ role: 'assistant', text: question });
    }

    // 次のユーザ入力を、この tool_use に対する tool_result として返せるように保持する。
    // options が抽出できなかった場合でも、ボタンは出さないが tool_use は未応答のままに
    // できないため（次回送信で API エラーになる）、pendingChoiceToolId は必ず設定して
    // 次のユーザ入力（自由記述）を tool_result として返せるようにする。
    if ( toolUse.id ) {
        this.chat.pendingChoiceToolId = toolUse.id;
        this.chat.pendingExtraChoiceToolIds = Array.isArray( toolUse._extraIds ) ? toolUse._extraIds : [];
        this.chat.pendingChoiceContext = this.buildContext( input );
    }

    // 選択肢を追加する
    if ( options.length ) {
        this.chat.updateChat({ role: 'userChoice', options: options, toolId: toolUse.id ?? ''}, false );
    }
    return null;
}
/*
##################################################
   履歴からの復元
##################################################
*/
// 未回答のまま残っている選択肢のボタンを再表示する（履歴からの再開・選択肢までの巻き戻し時）。
// 質問文は resume で復元済みのため、ここではボタンだけを末尾に表示する。
// 回答待ちの保留状態（pendingChoiceToolId 等）は呼び出し側（restorePendingChoice）が設定する。
resumePending( toolUse ) {
    const input = toolUse?.arguments ?? toolUse?.input ?? {};
    const options = this.extractOptions( input );
    if ( options.length ) {
        this.chat.updateChat({ role: 'userChoice', options: options, toolId: toolUse.id ?? ''}, false );
    }
}
// 選択肢ツールの質問文は tool_use の input に入っており、textブロックとしては履歴に残らない。
// ライブ表示（execute）と同様に、質問文をアシスタントメッセージとして復元する。
// （選択肢ボタン自体は、回答済みならユーザ発言として復元されるため描画しない。
//   未回答の場合は AiAssistantChat.restorePendingChoice が回答待ちとして復元し、resumePending でボタンを再表示する）
resume( toolUse, block ) {
    const input = toolUse.arguments ?? toolUse.input ?? {};
    if ( typeof input.question === 'string' && input.question ) {
        this.chat.updateChat({ role: 'assistant', text: input.question, timestamp: block?._timestamp }, false );
    }
}
/*
##################################################
   選択肢の正規化
##################################################
*/
// 選択肢の1件を { label, action } 形式に正規化する。
// 旧形式（文字列）／新形式（オブジェクト）の両方に対応する。
normalizeOption( opt ) {
    const allowedActions = [ 'positive', 'negative', 'other'];
    if ( opt !== null && typeof opt === 'object') {
        const label = typeof opt.label === 'string' ? opt.label : String( opt.label ?? '');
        const action = allowedActions.includes( opt.action ) ? opt.action : 'other';
        return { label, action };
    }
    return { label: String( opt ?? ''), action: 'other'};
}
// tool_use の input から、表示する選択肢（{ label, action } の配列。空ラベルは除く）を取り出す。
extractOptions( input ) {
    return this.coerceOptions( input?.options )
        .map(( opt ) => this.normalizeOption( opt ) )
        .filter(( opt ) => opt.label !== '');
}
// tool_use の input から、回答時に LLM へ添える選択肢の内容（{ question, labels }）を作る。
buildContext( input ) {
    const question = typeof input?.question === 'string' ? input.question : '';
    const labels = this.extractOptions( input ).map(( opt ) => opt.label );
    return { question, labels };
}
// options を配列に正規化する。
// 長文脈になるとモデルがツール入力のフォーマットを崩し、options を配列ではなく
// 文字列（例: '\n<parameter name="options">[{"label":...}]' のようにツールの内部タグごと
// JSON文字列に漏らす）で返すことがある。その場合でも中の JSON 配列を救済して配列に戻す。
coerceOptions( rawOptions ) {
    // 既に配列ならそのまま
    if ( Array.isArray( rawOptions ) ) return rawOptions;
    if ( typeof rawOptions !== 'string') return [];

    // 文字列内の最初の '[' から最後の ']' までを JSON 配列とみなして取り出す
    // （先頭の改行や <parameter ...> タグなどのゴミを無視する）。
    const start = rawOptions.indexOf('[');
    const end = rawOptions.lastIndexOf(']');
    if ( start === -1 || end === -1 || end <= start ) return [];
    const jsonText = rawOptions.slice( start, end + 1 );
    try {
        const parsed = JSON.parse( jsonText );
        return Array.isArray( parsed ) ? parsed : [];
    } catch ( error ) {
        console.warn('ask_user_choice: options のパースに失敗しました', error, rawOptions );
        return [];
    }
}
/*
##################################################
   フォーマット崩れの判定・救済
##################################################
*/
// 応答（tool_use ブロック群）がフォーマット崩れかどうかを判定する。
// 崩れていれば true を返し、呼び出し側でモデルに正しい形式での再出力を促す。
// 崩れの例：
//   ・options が配列でない（文字列化している 等）
//   ・options 配列の要素が {label,...} 形式のオブジェクトでない
//   ・label / action が options の外（tool_use 直下）に漏れている
//   ・1応答に複数の ask_user_choice tool_use が分裂して出ている
//   ・有効な選択肢（非空 label）が2件未満しか取り出せない
isMalformed( choiceBlocks ) {
    const list = Array.isArray( choiceBlocks ) ? choiceBlocks : [ choiceBlocks ];
    // 選択肢の tool_use が複数に分裂している時点で崩れ。
    if ( list.length !== 1 ) return true;

    const block = list[ 0 ];
    const input = ( block && ( block.arguments ?? block.input ) ) ?? {};

    // label / action が options の外に漏れている（分裂の断片）のは崩れ。
    if ( 'label' in input || 'action' in input ) return true;

    // options は配列であることが必須（文字列化などは崩れ）。
    if ( !Array.isArray( input.options ) ) return true;

    // 各要素は { label: string(非空) } を持つオブジェクトであること。
    const validLabels = input.options.filter(( opt ) =>
        opt !== null && typeof opt === 'object' && typeof opt.label === 'string' && opt.label !== ''
    );
    if ( validLabels.length !== input.options.length ) return true;

    // 選択肢UIとして成立するには2件以上必要。
    if ( validLabels.length < 2 ) return true;

    return false;
}
// 1応答に含まれる複数の ask_user_choice tool_use を、1つの選択肢 tool_use に統合する。
// 長文脈でモデルがフォーマットを崩すと、
//   ・options が配列ではなく壊れた文字列になる
//   ・1つの選択肢（label / action）が独立した tool_use に分裂する
// といったことが起きる。ここで質問文と全 options を1つに束ね、代表以外の
// tool_use_id は _extraIds として持たせる（未応答にならないよう後で tool_result を返す）。
mergeBlocks( blocks ) {
    const list = Array.isArray( blocks ) ? blocks : [ blocks ];
    let question = '';
    const options = [];
    const ids = [];
    for ( const block of list ) {
        if ( !block ) continue;
        if ( block.id ) ids.push( block.id );
        const input = block.arguments ?? block.input ?? {};
        // 質問文は最初に見つかった非空のものを採用する。
        if ( !question && typeof input.question === 'string' && input.question ) {
            question = input.question;
        }
        // 正規の options（配列 or 文字列化されたもの）を取り込む。
        for ( const opt of this.coerceOptions( input.options ) ) {
            options.push( opt );
        }
        // フォーマット崩れで選択肢が tool_use 直下（label / action）に漏れた場合も救済する。
        if ( typeof input.label === 'string' && input.label ) {
            options.push({ label: input.label, action: input.action });
        }
    }
    return {
        id: ids[ 0 ] ?? '',
        _extraIds: ids.slice( 1 ),
        arguments: { question, options }
    };
}

}
