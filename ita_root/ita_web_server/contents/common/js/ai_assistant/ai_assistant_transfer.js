////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Exastro IT Automation / ai_assistant_transfer.js
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

// AIアシスタントの会話履歴・学習事項のインポート／エクスポート。
// 会話履歴タブ・学習事項タブの一覧（DataTablePF）のインポート・エクスポートボタンから呼ばれる。
//
// ・エクスポートは一覧で選択した行が対象（選択が無い場合はボタンが押せない）。
//   件数を確認してからJSONファイルへ書き出す。
// ・会話履歴（ターンの配列）は会話1件ずつしか取得できない（GET /conversations/{id}/messages）ため、
//   1件ずつ順番に取得する。まとめて並列に投げるとサーバー側の負荷が高くなるため、
//   直列＋取得の間に短い待ちを入れ、進捗（何件中何件）を表示して途中で中止できるようにしている。
// ・インポートはファイルを選択し、含まれている件数を確認してから1件ずつ登録する。
//   登録は新しいレコードの作成のため、登録日時・更新日時はインポートした日時になる
//   （元の日時を引き継ぐ手段はプラットフォームAPIに無い）。
// ・会話のインポートでは、エクスポートしたファイルのほかに、会話履歴の確認（rowMenuのcheck）で
//   ダウンロードした「履歴部分だけ」のファイル（ターンの配列）も読み込める。
//   その場合はタイトルが分からないため、インポートした日時を添えたタイトルを付ける。
class AiAssistantTransfer {
/*
##################################################
   ファイルの形式
##################################################
*/
// エクスポートするファイルの種類（インポート時にどのファイルかを判別する目印）
static get conversationFileType() {
    return 'ita_ai_assistant_conversations';
}
static get lessonFileType() {
    return 'ita_ai_assistant_lessons';
}
// ファイル形式のバージョン（形式を変えた場合に上げる。インポートでは判定に使わない）
static get fileVersion() {
    return 1;
}
// インポートするファイルの最大バイト数（これを超えるファイルは選択した時点で受け付けない）
static get importFileSizeLimit() {
    return 50 * 1024 * 1024;
}
// 1件ずつの取得・登録を続けるときの待ち時間（ミリ秒）。
// 会話履歴の取得（エクスポート）と会話の登録（インポート）は件数分の通信になるため、
// 続けて投げ続けないよう間隔をあける（サーバー側の負荷を抑えるため）。
static get requestInterval() {
    return 100;
}
// エクスポートするファイル名（拡張子はfn.downloadが付ける）
static exportFileName( prefix ) {
    return `${prefix}_${fn.date( new Date(), 'yyyyMMdd_HHmmss')}`;
}
/*
##################################################
   会話のエクスポート
##################################################
*/
// 一覧で選択した会話を、保存されている会話履歴とあわせてJSONファイルへ書き出す。
// 会話履歴は1件ずつしか取得できないため、順番に取得して進捗を表示する。
// 取得できなかった会話はファイルへ含めず、件数をまとめて知らせる。
// 戻り値は常にfalse（一覧の内容は変わらないため取得しなおさない）。
static async exportConversations( conversations ) {
    const title = getMessage.FTE14075;

    const items = (( Array.isArray( conversations ) )? conversations: [])
        .filter(( item ) => item?.conversation_id );
    if ( !items.length ) {
        await fn.alert( title, getMessage.FTE14080 );
        return false;
    }

    const check = await fn.iconConfirm('export', title, getMessage.FTE14076( items.length ) );
    if ( !check ) return false;

    const progress = AiAssistantTransfer.openProgressModal( title, items.length );

    const records = [],
          errors = [];
    let canceled = false;
    for ( let i = 0; i < items.length; i++ ) {
        // 中止は取得中の1件が終わってから（進行中の通信は待つ）
        if ( progress.canceled ) {
            canceled = true;
            break;
        }
        const conversation = items[ i ];
        try {
            const history = await AiAssistantLlm.fetchHistory( conversation.conversation_id );
            records.push( AiAssistantTransfer.conversationRecord( conversation, history ) );
        } catch ( error ) {
            console.error( error );
            // どの会話か分かるようにタイトルを添える（タイトルが無い場合は会話ID）
            const label = ( conversation.title )? conversation.title: conversation.conversation_id;
            errors.push(`${label}：${fn.cv( error?.message, '')}`);
        }
        progress.update( i + 1 );
        if ( i + 1 < items.length ) await AiAssistantTransfer.wait();
    }
    await progress.close();

    // 中止した場合は、途中までの内容ではファイルを作らない
    if ( canceled ) {
        await fn.alert( title, getMessage.FTE14079 );
        return false;
    }
    if ( !records.length ) {
        await fn.alert( title, ( errors.length )
            ? getMessage.FTE14078( errors.length ) + '<br>' + fn.escape( errors.join('\n'), true )
            : getMessage.FTE14080 );
        return false;
    }

    fn.download('json', {
        file_type: AiAssistantTransfer.conversationFileType,
        version: AiAssistantTransfer.fileVersion,
        exported_at: fn.date( new Date(), 'yyyy/MM/dd HH:mm:ss'),
        conversations: records
    }, AiAssistantTransfer.exportFileName('ai_assistant_conversations') );

    if ( errors.length ) {
        await fn.alert( title, getMessage.FTE14078( errors.length ) + '<br>'
            + fn.escape( errors.join('\n'), true ) );
    }
    return false;
}
// ファイルへ書き出す会話1件の内容。
// インポートで使うのは title と history のみで、残りは元の会話が分かるようにするための情報
// （インポートでは登録日時・件数などを指定できないため、そのまま復元されるわけではない）。
static conversationRecord( conversation, history ) {
    return {
        title: fn.cv( conversation.title, ''),
        conversation_id: fn.cv( conversation.conversation_id, ''),
        message_count: conversation.message_count ?? null,
        current_token_count: conversation.current_token_count ?? null,
        created_at: fn.cv( conversation.created_at, ''),
        updated_at: fn.cv( conversation.updated_at, ''),
        history: ( Array.isArray( history ) )? history: []
    };
}
/*
##################################################
   会話のインポート
##################################################
*/
// ファイルに含まれている会話を、新しい会話として1件ずつ登録する。
//   ・登録日時・更新日時はインポートした日時になる（プラットフォーム側が付ける）
//   ・発言数は登録した履歴のターン数から決まる
//   ・トークン数は問い合わせのたびに積算される値のため0のまま（一覧では不明としてハイフンを表示する）
//   ・AIサービスとモデルは、ファイルの内容ではなくAI利用設定のものを使う
//     （ファイルの作成元とAIサービスのIDが一致しないため）
// param = { aiServiceId, modelId, tools, promptProfile }
//   promptProfile … 登録する会話のプロンプトプロファイル（インポート元の一覧のもの）
// 戻り値がfalseのときは一覧を取得しなおさない（1件も登録しなかった場合）。
static async importConversations( param = {}) {
    const title = getMessage.FTE14083;

    // 会話の作成にはAIサービスとモデルが必要
    if ( !param.aiServiceId || !param.modelId ) {
        await fn.alert( title, getMessage.FTE14088 );
        return false;
    }

    const selected = await AiAssistantTransfer.selectJsonFile( title );
    if ( !selected ) return false;

    // 履歴部分だけのファイルはタイトルが分からないため、インポートした日時を添えて付ける
    const records = AiAssistantTransfer.parseConversations( selected.json,
        fn.date( new Date(), 'yyyy/MM/dd HH:mm:ss') );
    if ( !records.length ) {
        await fn.alert( title, getMessage.FTE14085 );
        return false;
    }

    const check = await fn.iconConfirm('import', title, getMessage.FTE14084( records.length ) );
    if ( !check ) return false;

    const progress = AiAssistantTransfer.openProgressModal( title, records.length );

    const errors = [];
    let imported = 0,
        canceled = false;
    for ( let i = 0; i < records.length; i++ ) {
        // 中止は登録中の1件が終わってから（登録済みの会話はそのまま残る）
        if ( progress.canceled ) {
            canceled = true;
            break;
        }
        const record = records[ i ];
        try {
            await AiAssistantLlm.importConversation({
                title: record.title,
                aiServiceId: param.aiServiceId,
                modelId: param.modelId,
                tools: param.tools,
                promptProfile: param.promptProfile,
                history: record.history
            });
            imported++;
        } catch ( error ) {
            console.error( error );
            errors.push(`${record.title}：${fn.cv( error?.message, '')}`);
        }
        progress.update( i + 1 );
        if ( i + 1 < records.length ) await AiAssistantTransfer.wait();
    }
    await progress.close();

    if ( canceled ) {
        await fn.alert( title, getMessage.FTE14089 );
    } else if ( errors.length ) {
        await fn.alert( title, getMessage.FTE14086( errors.length ) + '<br>'
            + fn.escape( errors.join('\n'), true ) );
    }
    // 1件でも登録できた場合は、一覧へ反映されるように取得しなおす
    return ( imported )? undefined: false;
}
// インポートするファイルの内容から、登録する会話（[{ title, history }, …]）を取り出す。
// 次の形式を受け付ける（履歴が空のものは登録しても意味が無いため除く）。
//   ・エクスポートしたファイル … { conversations: [{ title, history }, …] }
//   ・会話1件 … { title, history }
//   ・会話履歴の確認からダウンロードしたファイル … [{ role, content }, …]（ターンの配列）
// date … インポートした日時（履歴部分だけのファイルに付けるタイトルへ入れる）
static parseConversations( json, date ) {
    const historyTitle = getMessage.FTE14087( date );
    const records = [];

    // 会話1件（タイトルが無い場合は履歴だけのファイルと同じ扱い）
    const addConversation = ( item ) => {
        if ( !item || !Array.isArray( item.history ) ) return;
        const history = item.history.filter( AiAssistantTransfer.isTurn );
        if ( !history.length ) return;
        const title = String( item.title ?? '').trim();
        records.push({ title: ( title )? title: historyTitle, history: history });
    };
    // ターンの配列（履歴部分だけのファイル）
    const addHistory = ( turns ) => {
        const history = turns.filter( AiAssistantTransfer.isTurn );
        if ( !history.length ) return;
        records.push({ title: historyTitle, history: history });
    };

    if ( Array.isArray( json ) ) {
        // 配列は、ターンの配列（履歴）と会話の配列のどちらもありうるため中身で見分ける
        if ( json.some( AiAssistantTransfer.isTurn ) ) {
            addHistory( json );
        } else {
            for ( const item of json ) addConversation( item );
        }
    } else if ( Array.isArray( json?.conversations ) ) {
        for ( const item of json.conversations ) addConversation( item );
    } else if ( json && typeof json === 'object') {
        addConversation( json );
    }
    return records;
}
// 会話履歴のターン（{ role, content }）かどうか。
// 会話履歴のファイルかを見分ける判定と、登録する履歴から余計な要素を除くために使う。
static isTurn( turn ) {
    if ( !turn || typeof turn !== 'object') return false;
    if ( typeof turn.role !== 'string' || turn.role === '') return false;
    return ( Array.isArray( turn.content ) || typeof turn.content === 'string');
}
/*
##################################################
   学習事項のエクスポート
##################################################
*/
// 一覧で選択した学習事項をJSONファイルへ書き出す。
// 一覧の内容がそのまま書き出す内容になるため、APIの呼び出しは行わない。
// 戻り値は常にfalse（一覧の内容は変わらないため取得しなおさない）。
static async exportLessons( lessons ) {
    const title = getMessage.FTE14081;

    const items = (( Array.isArray( lessons ) )? lessons: []).filter(( item ) => item?.lesson_id );
    if ( !items.length ) {
        await fn.alert( title, getMessage.FTE14080 );
        return false;
    }

    const check = await fn.iconConfirm('export', title, getMessage.FTE14082( items.length ) );
    if ( !check ) return false;

    fn.download('json', {
        file_type: AiAssistantTransfer.lessonFileType,
        version: AiAssistantTransfer.fileVersion,
        exported_at: fn.date( new Date(), 'yyyy/MM/dd HH:mm:ss'),
        lessons: items.map( AiAssistantTransfer.lessonRecord )
    }, AiAssistantTransfer.exportFileName('ai_assistant_lessons') );

    return false;
}
// ファイルへ書き出す学習事項1件の内容。
// インポートで使うのは内容・分類・重要度・状態で、残りは元の学習事項が分かるようにするための情報。
static lessonRecord( lesson ) {
    return {
        lesson: fn.cv( lesson.lesson, ''),
        category: fn.cv( lesson.category, ''),
        priority: lesson.priority ?? null,
        enabled: lesson.enabled === true,
        prompt_profile: fn.cv( lesson.prompt_profile, ''),
        lesson_id: fn.cv( lesson.lesson_id, ''),
        created_at: fn.cv( lesson.created_at, ''),
        updated_at: fn.cv( lesson.updated_at, '')
    };
}
/*
##################################################
   学習事項のインポート
##################################################
*/
// ファイルに含まれている学習事項を、新しい学習事項として1件ずつ登録する。
//   ・登録日時・更新日時はインポートした日時になる（プラットフォーム側が付ける）
//   ・学習元の会話（conversation_id）は引き継がない（インポート先には無い会話のため）
//   ・プロンプトプロファイルはファイルの内容ではなく、インポート先の一覧のものを使う
// param = { promptProfile }
//   promptProfile … 登録する学習事項のプロンプトプロファイル（インポート元の一覧のもの）
// 戻り値がfalseのときは一覧を取得しなおさない（1件も登録しなかった場合）。
static async importLessons( param = {}) {
    const title = getMessage.FTE14090;

    const selected = await AiAssistantTransfer.selectJsonFile( title );
    if ( !selected ) return false;

    const records = AiAssistantTransfer.parseLessons( selected.json );
    if ( !records.length ) {
        await fn.alert( title, getMessage.FTE14092 );
        return false;
    }

    const check = await fn.iconConfirm('import', title, getMessage.FTE14091( records.length ) );
    if ( !check ) return false;

    const progress = AiAssistantTransfer.openProgressModal( title, records.length );

    const errors = [];
    let imported = 0,
        canceled = false;
    for ( let i = 0; i < records.length; i++ ) {
        // 中止は登録中の1件が終わってから（登録済みの学習事項はそのまま残る）
        if ( progress.canceled ) {
            canceled = true;
            break;
        }
        const record = records[ i ];
        try {
            await AiAssistantLlm.createLesson({ ...record, promptProfile: param.promptProfile });
            imported++;
        } catch ( error ) {
            console.error( error );
            errors.push(`${AiAssistantTransfer.lessonLabel( record )}：${fn.cv( error?.message, '')}`);
        }
        progress.update( i + 1 );
        if ( i + 1 < records.length ) await AiAssistantTransfer.wait();
    }
    await progress.close();

    if ( canceled ) {
        await fn.alert( title, getMessage.FTE14089 );
    } else if ( errors.length ) {
        await fn.alert( title, getMessage.FTE14093( errors.length ) + '<br>'
            + fn.escape( errors.join('\n'), true ) );
    }
    // 1件でも登録できた場合は、一覧へ反映されるように取得しなおす
    return ( imported )? undefined: false;
}
// インポートするファイルの内容から、登録する学習事項（AiAssistantLlm.createLessonへ渡す形）を取り出す。
// 次の形式を受け付ける（内容が空のものは登録できないため除く）。
//   ・エクスポートしたファイル … { lessons: [{ lesson, category, priority, enabled }, …] }
//   ・学習事項の配列 … [{ lesson, category, priority, enabled }, …]
static parseLessons( json ) {
    const list = ( Array.isArray( json ) )? json
        : ( Array.isArray( json?.lessons ) )? json.lessons: [];

    const records = [];
    for ( const item of list ) {
        if ( !item || typeof item !== 'object') continue;
        const lesson = String( item.lesson ?? '').trim();
        if ( !lesson ) continue;
        records.push({
            // 内容・分類は、プラットフォーム側の上限を超えている場合は登録できないため切り詰める
            lesson: lesson.slice( 0, AiAssistantLlm.lessonLength ),
            category: String( item.category ?? '').slice( 0, AiAssistantLlm.lessonCategoryLength ),
            priority: AiAssistantLlm.lessonPriority( item.priority ),
            // 状態（有効・無効）が分からない場合は有効にする（登録ダイアログの既定と同じ）
            enabled: ( typeof item.enabled === 'boolean')? item.enabled: true
        });
    }
    return records;
}
// エラーメッセージで、どの学習事項か分かるようにする目印（内容の先頭のみ）
static lessonLabel( lesson ) {
    const text = fn.cv( lesson?.lesson, '').split('\n')[0];
    return ( text.length > 40 )? text.slice( 0, 40 ) + '…': text;
}
/*
##################################################
   ファイルの選択
##################################################
*/
// インポートするJSONファイルを選択する。
// 戻り値: { json, name, size }。選択をキャンセルした場合はnull
//   （読み込めなかった場合は理由を知らせてnullを返す）
static async selectJsonFile( title ) {
    try {
        return await fn.fileSelect('json', AiAssistantTransfer.importFileSizeLimit,
            'application/json,.json');
    } catch ( error ) {
        // キャンセルは何もしない。それ以外（JSONの形式・ファイルサイズ）は理由を知らせる
        if ( error === 'cancel') return null;
        console.error( error );
        const message = ( typeof error === 'string')? error: fn.cv( error?.message, '');
        await fn.alert( title, fn.escape( message, true ) );
        return null;
    }
}
/*
##################################################
   進捗モーダル
##################################################
*/
// 1件ずつ処理する間の進捗（何件中何件）を表示するモーダル。
// 件数が多い場合は時間がかかるため、キャンセルボタンで中止できるようにしている
// （中止は処理中の1件が終わってから。押した時点で通信を打ち切ることはしない）。
// 戻り値: { update( num ), close(), canceled }
static openProgressModal( title, total ) {
    const config = {
        mode: 'modeless',
        position: 'center',
        width: '400px',
        header: {
            title: title,
            close: false,
            move: false
        },
        footer: {
            button: {
                cancel: { text: getMessage.FTE00088, action: 'normal', width: '120px'}
            }
        }
    };

    const dialog = new Dialog( config );
    const state = { canceled: false };
    dialog.btnFn = {
        cancel: function(){
            state.canceled = true;
            // 中止は次の1件から効くため、二度押しできないようにする
            dialog.buttonDisabled();
        }
    };

    const html = ``
    + `<div class="progressConteinar">`
        + `<div class="progressWrap">`
            + `<div class="progressBar"></div>`
            + `<div class="progressPercentage"><span class="progressPercentageNumber">0</span><span class="progressPercentageUnit">%</span></div>`
        + `</div>`
        + `<div class="progressText"></div>`
    + `</div>`;
    dialog.open( html );

    const update = function( num ){
        const rate = ( total > 0 )? Math.floor( num / total * 100 ): 100;
        dialog.$.dbody.find('.progressBar').css('width', `${rate}%`);
        dialog.$.dbody.find('.progressPercentageNumber').text( rate );
        dialog.$.dbody.find('.progressText').text( getMessage.FTE14077( num, total ) );
    };
    update( 0 );

    return {
        update: update,
        close: () => dialog.close(),
        get canceled() {
            return state.canceled;
        }
    };
}
// 続けて通信を投げないようにする待ち
static wait( ms = AiAssistantTransfer.requestInterval ) {
    return new Promise(( resolve ) => setTimeout( resolve, ms ) );
}

}
