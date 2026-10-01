////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Exastro IT Automation / ai_assistant_setting.js
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
class AiAssistantSetting {
/*
##################################################
   REST API URL
##################################################
*/
static get apiUrl() {
    const { organizationId } = fn.getCommonParams();
    return {
        // 利用可能なAIサービス一覧: GET
        ai_service: () => `/api/${organizationId}/platform/ai-services`,
        // Credential: 取得 GET / 登録 POST / 更新 PUT / 削除 DELETE
        //   1つのAIサービスにつき1件のみ登録できるため、URLにCredential IDは含まない
        //   verify = true で認証情報の検証: POST
        credential: ( credentialType, verify = false ) => {
            const url = `/api/${organizationId}/platform/users/_current/${credentialType}/credentials`;
            return ( verify )? `${url}/verify`: url;
        },
        // AI Serviceモデル一覧: GET
        models: ( credentialType ) => `/api/${organizationId}/platform/users/_current/${credentialType}/models`,
        // 現在選択中のAIサービス: 取得 GET / 保存 PUT
        //   保存できるのはai_service_idのみ。取得時は選択中のAIサービスに保存されている
        //   モデル（model_id・model_name）もあわせて返る
        preference: () => `/api/${organizationId}/platform/users/_current/ai-preference`,
        // AIサービスごとのAI利用設定（モデル）: 取得 GET / 保存 PUT（全置換）
        servicePreference: ( credentialType ) => `/api/${organizationId}/platform/users/_current/${credentialType}/ai-preference`,
    };
}
/*
##################################################
   認証情報の入力欄（表示上の補足）
##################################################
*/
// 入力欄の定義（キー名・表示名・種別・必須）はGET /ai-servicesのsettingsから受け取る。
// settingsでは表現できない表示上の情報のみ、`${ai_service_id}.${キー名}`をキーにしてここで補う。
//   multiline    … 貼り付けやすいように複数行の入力欄にする
//   json         … 入力値がJSONとして正しいかを送信前に確認する（値は文字列のまま送信する）
//   requiredKeys … jsonに含まれていなければならないキー
//   fileSelect   … ファイルを選択して内容を入力欄へ読み込むボタンを表示する（値はaccept属性に指定する）
//   note         … 入力欄の下に表示する説明
static get fieldUiHints() {
    return {
        'bedrock-cache.apiKey': {
            multiline: true,
            json: true,
            requiredKeys: [ 'accessToken', 'refreshToken', 'idToken'],
            fileSelect: 'application/json,.json',
            note: getMessage.FTE14140
        }
    };
}
// ファイル選択で読み込めるファイルサイズの上限（認証情報のJSONは小さいため、誤選択の保険として制限する）
static get fileSelectLimitSize() {
    return 1048576;
}
// Credentialのステータス表示名
static get statusText() {
    return {
        'active': getMessage.FTE14141,
        'expired': getMessage.FTE14142,
        'disabled': getMessage.FTE14143
    };
}
/*
##################################################
   Constructor
##################################################
*/
// option = {
//   onSave: ( preference ) => {}   保存完了を呼び出し側へ通知する
//   onClose: ( preference ) => {}  設定ダイアログを閉じたことを呼び出し側へ通知する
//                                 （認証情報の再設定結果を反映させるために使う）
//   isServiceChangeLocked: () => Boolean
//                                 使用するAIサービスを変更できない状態か（会話中など）を返す。
//                                 trueの間は一覧での選択と適用ができなくなる（認証情報の
//                                 登録・更新・削除・確認とモデルの選択は行える）
// }
constructor( params, option = {} ) {
    this.params = params;
    this.option = option;
    // 現在選択中のAIサービス（ai-preference）
    this.preference = {};
    // AIサービスごとのAI利用設定（ai_service_id → モデルの設定。未保存はnull）
    this.servicePreferences = {};
    // システムとして利用可能なAIサービス
    this.serviceList = [];
    // 登録済みCredential（ai_service_id → Credential。未登録はnull）
    this.credentials = {};
    // Credentialの取得に失敗したAIサービス（ai_service_id → エラーメッセージ）
    this.credentialErrors = {};
    // 取得済みのモデル一覧（ai_service_id → モデルの配列）
    //   モデル一覧の取得はBedrockへの問い合わせが必要で時間がかかるため、
    //   一度取得したものは一覧の表示名に流用する
    this.modelLists = {};
    // 設定ダイアログ
    this.dialog = null;
    // AIサービスの登録・更新ダイアログ
    this.credentialDialog = null;
    // モデル選択ダイアログ
    this.modelDialog = null;
}
/*
##################################################
   設定完了判定（chat 側からも参照する）
##################################################
*/
static isConfigured( preference, aiServiceOnly = false ) {
    if ( !preference?.ai_service_id ) return false;
    if ( aiServiceOnly ) return true;
    return Boolean( preference.model_id );
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   API
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
    AI Serviceにリクエストを送信する
##################################################
*/
async aiServiceRequest( url, method, body ) {
    const token = this.getToken();
    const payload = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        }
    };
    if ( body ) {
        payload.body = JSON.stringify( body );
    }
    const response = await fetch( url, payload );

    const json = await response.json().catch( () => null );
    if ( json?.error ) {
        throw new Error(`AI Service error (${json.error.code}): ${json.error.message}`);
    }
    if ( !response.ok ) {
        // platform APIはエラー時も message を返すため、あればそれを利用する
        throw new Error( json?.message ?? `AI Service request failed: ${response.status}`);
    }
    // 応答は { result, message, ts, data } の形なので data のみを返す
    return json?.data ?? {};
}
/*
##################################################
    現在選択中のAIサービスを取得
##################################################
*/
// 未設定の場合も404にはならず全項目nullで返る。
// model_id・model_nameは選択中のAIサービスのAI利用設定から返るため、ここでは保存できない。
async getPreference() {
    this.preference = await this.aiServiceRequest(AiAssistantSetting.apiUrl.preference(), 'GET');
    return this.preference;
}
/*
##################################################
    現在選択中のAIサービスを保存する
##################################################
*/
async setPreference( aiServiceId ) {
    await this.aiServiceRequest(AiAssistantSetting.apiUrl.preference(), 'PUT', {
        ai_service_id: aiServiceId
    });
    await this.getPreference();
    if ( this.option.onSave ) this.option.onSave( this.preference );
    return this.preference;
}
/*
##################################################
    AIサービスのAI利用設定（モデル）を取得
##################################################
*/
// 未保存の場合も404にはならず、model_idがnull・pickup_model_idsが空配列で返る。
// モデルが未設定のAIサービスは未選択として扱いたいため、model_idがなければnullとして保持する。
async getServicePreference( aiServiceId ) {
    const preference = await this.aiServiceRequest(AiAssistantSetting.apiUrl.servicePreference( aiServiceId ), 'GET');
    this.servicePreferences[ aiServiceId ] = ( preference?.model_id )? preference: null;
    return this.servicePreferences[ aiServiceId ];
}
/*
##################################################
    登録済みAIサービスのAI利用設定をまとめて取得
##################################################
*/
// AI利用設定はAIサービスごとに保存されるため、一覧に表示する分をまとめて取得する。
// 1つのAIサービスの取得に失敗しても他の結果は表示したいので allSettled で待つ。
async getServicePreferenceList() {
    // Credentialを削除したAIサービスの設定を残さないため、取得のたびに作り直す
    this.servicePreferences = {};
    const targetList = this.serviceList.filter(( item ) => this.credentials[ item.ai_service_id ] );
    const results = await Promise.allSettled(
        targetList.map(( item ) => this.getServicePreference( item.ai_service_id ) )
    );
    results.forEach(( result, index ) => {
        if ( result.status === 'rejected') {
            console.error( result.reason );
            this.servicePreferences[ targetList[ index ].ai_service_id ] = null;
        }
    });
    return this.servicePreferences;
}
/*
##################################################
    AIサービスのAI利用設定（モデル）を保存する（全置換）
##################################################
*/
// pickupModelsはモデルIDだけでは表示名がわからないため、{ id, name }の配列で送信する。
async setServicePreference( aiServiceId, modelId, modelName, pickupModels = [] ) {
    this.servicePreferences[ aiServiceId ] = await this.aiServiceRequest(
        AiAssistantSetting.apiUrl.servicePreference( aiServiceId ), 'PUT', {
            model_id: modelId,
            model_name: modelName,
            pickup_model_ids: pickupModels
        });
    // 選択中のAIサービスのモデルを変更した場合は、呼び出し側が参照するpreferenceも読み直す
    if ( this.preference?.ai_service_id === aiServiceId ) {
        await this.getPreference();
        if ( this.option.onSave ) this.option.onSave( this.preference );
    }
    return this.servicePreferences[ aiServiceId ];
}
/*
##################################################
    利用できるAIサービスの一覧を取得
##################################################
*/
async getAiServiceList() {
    const aiService = await this.aiServiceRequest(AiAssistantSetting.apiUrl.ai_service(), 'GET');
    this.serviceList = aiService?.ai_services ?? [];
    return this.serviceList;
}
/*
##################################################
    登録済みのAIサービス（Credential）を取得
##################################################
*/
// AIサービスごとにCredentialを取得する。
// 1つのAIサービスの取得に失敗しても他の結果は表示したいので allSettled で待つ。
async getRegisteredAiServiceList() {
    const registeredList = await Promise.allSettled(
        this.serviceList.map(( item ) => this.aiServiceRequest(AiAssistantSetting.apiUrl.credential( item.ai_service_id ), 'GET') )
    );

    this.credentials = {};
    this.credentialErrors = {};
    this.serviceList.forEach(( item, index ) => {
        const result = registeredList[ index ];
        if ( result.status === 'fulfilled') {
            // 未登録でも404にはならず全項目nullで返るため、credential_idの有無で判定する
            this.credentials[ item.ai_service_id ] = ( result.value?.credential_id )? result.value: null;
        } else {
            console.error( result.reason );
            this.credentials[ item.ai_service_id ] = null;
            this.credentialErrors[ item.ai_service_id ] = result.reason?.message ?? getMessage.FTE14144;
        }
    });
    return this.credentials;
}
/*
##################################################
    Credentialを登録する
##################################################
*/
async registerCredential( aiServiceId, credentialName, credentialData, notes ) {
    const body = {
        credential_name: credentialName,
        credential_data: credentialData
    };
    if ( notes ) body.notes = notes;
    return await this.aiServiceRequest(AiAssistantSetting.apiUrl.credential( aiServiceId ), 'POST', body );
}
/*
##################################################
    Credentialを更新する（全体更新）
##################################################
*/
// credential_dataは差分更新できないため、登録時と同じ内容を組み立てて送信する。
// notesは省略した場合のみ現在の値が維持される。
async updateCredential( aiServiceId, credentialName, credentialData, notes ) {
    const body = {
        credential_name: credentialName,
        credential_data: credentialData
    };
    if ( notes ) body.notes = notes;
    return await this.aiServiceRequest(AiAssistantSetting.apiUrl.credential( aiServiceId ), 'PUT', body );
}
/*
##################################################
    Credentialを検証する
##################################################
*/
async verifyCredential( aiServiceId ) {
    return await this.aiServiceRequest(AiAssistantSetting.apiUrl.credential( aiServiceId, true ), 'POST');
}
/*
##################################################
    Credentialを削除する
##################################################
*/
async deleteCredential( aiServiceId ) {
    return await this.aiServiceRequest(AiAssistantSetting.apiUrl.credential( aiServiceId ), 'DELETE');
}
/*
##################################################
    使用できるモデルの一覧を取得
##################################################
*/
async getModelList( aiServiceId ) {
    const result = await this.aiServiceRequest(AiAssistantSetting.apiUrl.models( aiServiceId ), 'GET');
    this.modelLists[ aiServiceId ] = result?.models ?? [];
    return this.modelLists[ aiServiceId ];
}
/*
##################################################
    登録済みCredentialの合計件数
##################################################
*/
get registeredCount() {
    return Object.values( this.credentials ).filter(( credential ) => credential ).length;
}
/*
##################################################
    AIサービス情報を取得する
##################################################
*/
getService( aiServiceId ) {
    return this.serviceList.find(( item ) => item.ai_service_id === aiServiceId ) ?? null;
}
/*
##################################################
    登録済みCredentialを取得する
##################################################
*/
getCredential( aiServiceId ) {
    return this.credentials[ aiServiceId ] ?? null;
}
/*
##################################################
    まだCredentialを登録していないAIサービス
##################################################
*/
// 1つのAIサービスにつき1件しか登録できないため、追加できるのは未登録のAIサービスのみ
get unregisteredServiceList() {
    return this.serviceList.filter(( item ) => !this.credentials[ item.ai_service_id ] );
}
/*
##################################################
    選択中のモデルを取得する
##################################################
*/
// AI利用設定はAIサービスごとに保存されるため、選択中でないAIサービスもモデルの設定を持つ。
getSelectedModel( aiServiceId ) {
    const preference = this.servicePreferences[ aiServiceId ];
    if ( !preference?.model_id ) return null;
    return {
        modelId: preference.model_id,
        modelName: preference.model_name ?? '',
        pickupModels: preference.pickup_model_ids ?? []
    };
}
// 現在選択中のAIサービスか
isCurrentService( aiServiceId ) {
    return Boolean( aiServiceId ) && this.preference?.ai_service_id === aiServiceId;
}
// 使用するAIサービスを変更できない状態か
//   会話は作成時のAIサービスに紐づいていて、途中から別のAIサービスへ切り替えることはできない。
//   会話中に変更を許すと、表示しているAIサービス名と実際に応答しているAIサービスが食い違うため、
//   呼び出し側（チャット）が会話中かどうかを判断して変更を禁止する。
get serviceChangeLocked() {
    if ( !this.option.isServiceChangeLocked ) return false;
    return this.option.isServiceChangeLocked() === true;
}
/*
##################################################
    チャットで使用するAIサービス・モデル
##################################################
*/
// 現在選択中のAIサービスとそのモデルを読み込む（チャット側の表示用）
//   選択中のAIサービスのピックアップモデルはAIサービスごとのAI利用設定にあるため、
//   preferenceだけではモデルの切り替え候補がわからない。
//   モデル設定の取得に失敗しても、AIサービス名と既定のモデルは表示できるようにする。
async loadPreference() {
    await this.getPreference();

    const aiServiceId = this.preference?.ai_service_id;
    if ( aiServiceId ) {
        try {
            await this.getServicePreference( aiServiceId );
        } catch ( error ) {
            console.error( error );
            this.servicePreferences[ aiServiceId ] = null;
        }
    }
    return this.preference;
}
// 現在選択中のAIサービス
get currentAiServiceId() {
    return this.preference?.ai_service_id ?? '';
}
// 現在選択中のAIサービスの表示名
//   AIサービス一覧（serviceList）は設定ダイアログを開くまで取得しないため、
//   ai-preferenceが返す表示名を優先して使う
get currentServiceName() {
    const aiServiceId = this.preference?.ai_service_id;
    if ( !aiServiceId ) return '';
    return this.preference.ai_service_name || this.getService( aiServiceId )?.ai_service_name || aiServiceId;
}
// 現在選択中のAIサービスの既定のモデル
get currentModelId() {
    return this.preference?.model_id ?? '';
}
// チャットで切り替えられるモデル（現在選択中のAIサービスのピックアップモデル）
get currentPickupModels() {
    const aiServiceId = this.preference?.ai_service_id;
    if ( !aiServiceId ) return [];

    // ピックアップモデルが未保存・取得できない場合も、既定のモデルは使用できる
    const selected = this.getSelectedModel( aiServiceId );
    const pickupModels = ( selected?.pickupModels.length )? selected.pickupModels
        : ( this.preference.model_id )? [{ id: this.preference.model_id, name: this.preference.model_name }]
        : [];

    return pickupModels.map(( model ) => {
        return { id: model.id, name: model.name || this.getModelName( aiServiceId, model.id ) };
    });
}
// モデルの表示名（モデル一覧が未取得の場合は、AI利用設定に保存されている表示名・モデルIDで代用する）
getModelName( aiServiceId, modelId ) {
    const model = ( this.modelLists[ aiServiceId ] ?? [] ).find(( item ) => item.id === modelId );
    if ( model?.name ) return model.name;

    const preference = this.servicePreferences[ aiServiceId ];
    const pickup = ( preference?.pickup_model_ids ?? [] ).find(( item ) => item.id === modelId );
    if ( pickup?.name ) return pickup.name;
    if ( preference?.model_id === modelId && preference.model_name ) return preference.model_name;

    return modelId;
}
/*
##################################################
    認証情報の入力欄の定義を取得する
##################################################
*/
// GET /ai-servicesのsettingsから組み立てる。キー名はそのままcredential_dataのキーになる。
getCredentialFields( aiServiceId ) {
    const service = this.getService( aiServiceId );
    const settings = ( fn.typeof( service?.settings ) === 'object')? service.settings: {};

    return Object.keys( settings ).map(( key ) => {
        const setting = settings[ key ] ?? {};
        const hint = AiAssistantSetting.fieldUiHints[`${aiServiceId}.${key}`] ?? {};
        return Object.assign({
            key: key,
            title: setting.title ?? key,
            type: setting.type ?? 'text',
            required: setting.required === true
        }, hint );
    });
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   設定ダイアログ
//
////////////////////////////////////////////////////////////////////////////////////////////////////
// 設定モーダルコンフィグ
get dialogConfig() {
    return {
        position: 'center',
        width: '800px',
        header: {
            title: getMessage.FTE14145
        },
        footer: {
            button: {
                // 適用は選択が現在使用中のAIサービスから変わったときだけ押せるため、dialogPositiveにして個別に切り替える
                apply: { text: getMessage.FTE14146, action: 'positive', className: 'dialogPositive', width: '120px'},
                close: { text: getMessage.FTE10043, action: 'normal'}
            }
        }
    };
}
/*
##################################################
    ダイアログを開く
##################################################
*/
async open() {
    // 二重に開かない
    if ( this.dialog ) return;

    const close = () => { this.close(); };
    const apply = () => { this.applyUseService(); };
    const dialog = new Dialog( this.dialogConfig, { apply: apply, close: close });
    this.dialog = dialog;

    // bodyなしで開くとローディング表示になる
    dialog.open();
    this.setDialogEvents();

    try {
        await this.loadServiceList();
        dialog.setBody( this.createBodyHtml() );
        this.setApplyButtonState();
    } catch ( error ) {
        console.error( error );
        dialog.setBody( this.createLoadErrorHtml( error ) );
    }
    return;
}
/*
##################################################
    ダイアログを閉じる
##################################################
*/
async close() {
    if ( !this.dialog ) return;
    const dialog = this.dialog;
    this.dialog = null;
    await dialog.close();
    // 閉じたあとの設定内容を呼び出し側へ通知する
    if ( this.option.onClose ) await this.option.onClose( this.preference );
    return;
}
/*
##################################################
    AIサービスの登録状況を読み込む
##################################################
*/
async loadServiceList() {
    await this.getAiServiceList();
    await this.getRegisteredAiServiceList();
    // 選択中のAIサービスと、AIサービスごとのモデルを一覧に表示するため、AI利用設定も読み直す
    await this.getPreference();
    await this.getServicePreferenceList();
    return;
}
/*
##################################################
    ダイアログ本体HTML
##################################################
*/
// AIサービスブロックは追加・削除のたびに作り直すため、外側のラッパーを分けておく
createBodyHtml() {
    return `<div class="aiSettingServiceBlock">${this.createServiceBlockHtml()}</div>`;
}
// 読み込み失敗
createLoadErrorHtml( error ) {
    const message = error?.message ?? getMessage.FTE14147;
    return `
    <div class="aiSettingEmpty">
        <div class="aiSettingEmptyMessage">${fn.html.icon('circle_exclamation')} ${getMessage.FTE14147}</div>
        <div class="aiSettingEmptyNote">${fn.escape( message )}</div>
    </div>`;
}
/*
##################################################
    AIサービス一覧HTML
##################################################
*/
createServiceBlockHtml() {
    const main = ( this.registeredCount === 0 )? this.createNoServiceHtml(): this.createServiceListHtml();
    return main + this.createServiceErrorHtml();
}
// AIサービス追加ボタン（すべてのAIサービスが登録済みの場合は追加できない）
createAddServiceButtonHtml() {
    const attrs = { action: 'default'};
    if ( !this.unregisteredServiceList.length ) attrs.disabled = 'disabled';
    return fn.html.iconButton('plus', getMessage.FTE14148, 'itaButton aiSettingAddServiceButton', attrs );
}
// 未登録
createNoServiceHtml() {
    return `
    <div class="aiSettingEmpty">
        <div class="aiSettingEmptyMessage">${fn.html.icon('circle_exclamation')} ${getMessage.FTE14149}</div>
        <div class="aiSettingEmptyNote">${getMessage.FTE14150}</div>
        <div class="aiSettingEmptyMenu">${this.createAddServiceButtonHtml()}</div>
    </div>`;
}
// 登録済み
createServiceListHtml() {
    const html = [];
    for ( const service of this.serviceList ) {
        const credential = this.getCredential( service.ai_service_id );
        if ( credential ) html.push( this.createServiceItemHtml( service, credential ) );
    }
    // 会話中はAIサービスを変更できないため、選択のかわりに理由を案内する
    const note = ( this.serviceChangeLocked )
        ? getMessage.FTE14151
        : getMessage.FTE14152;
    return `
    <div class="commonSection">
        <div class="aiSettingListHeader">
            <div class="aiSettingListTitle">${getMessage.FTE14153}<span class="aiSettingListCount">${getMessage.FTE14154( this.registeredCount )}</span><br>
            ${note}</div>
            <div class="aiSettingListMenu">${this.createAddServiceButtonHtml()}</div>
        </div>
        <ul class="aiSettingList">${html.join('')}</ul>
    </div>`;
}
// Credential 1件
createServiceItemHtml( service, credential ) {
    const status = credential.status ?? '';
    const info = [];
    if ( credential.expires_at ) {
        info.push(`<div class="aiSettingItemInfo">${getMessage.FTE14155( fn.date( credential.expires_at, 'yyyy/MM/dd HH:mm') )}</div>`);
    }
    if ( credential.last_used_at ) {
        info.push(`<div class="aiSettingItemInfo">${getMessage.FTE14156( fn.date( credential.last_used_at, 'yyyy/MM/dd HH:mm') )}</div>`);
    }

    const aiServiceId = service.ai_service_id;
    const isCurrent = this.isCurrentService( aiServiceId );
    // 使用するAIサービスは1つのみ選択できる（選択中のAIサービスはai-preferenceに1件だけ保存される）
    const checkAttrs = ( isCurrent )? { checked: 'checked'}: {};
    // 会話中は選択を変えられないようにする（使用中がどれかは表示したままにする）
    if ( this.serviceChangeLocked ) checkAttrs.disabled = 'disabled';
    const currentHtml = ( isCurrent )? `<div class="aiSettingItemCurrent">${getMessage.FTE14157}</div>`: '';

    return `
    <li class="aiSettingItem" data-ai-service="${fn.escape( aiServiceId )}">
        <div class="aiSettingItemMain">
            <div class="aiSettingItemCheck">
                ${fn.html.radio('aiSettingUseRadio', fn.escape( aiServiceId ), 'use_ai_service', `aiSettingUse_${fn.escape( aiServiceId )}`, checkAttrs )}
            </div>
            <div class="aiSettingItemBody">
                <div class="aiSettingItemHeader">
                    <div class="aiSettingItemName">${fn.escape( credential.credential_name )}</div>
                    <div class="aiSettingItemStatus" data-status="${fn.escape( status )}">${AiAssistantSetting.statusText[ status ] ?? fn.escape( status )}</div>
                    ${currentHtml}
                </div>
                <div class="aiSettingItemService">${fn.escape( service.ai_service_name ?? service.ai_service_id )}</div>
                ${info.join('')}
            </div>
            <div class="aiSettingItemMenu">
                ${fn.html.iconButton('menuList', getMessage.FTE14158, 'itaButton aiSettingModelSelectButton', { action: 'default'})}
                ${fn.html.iconButton('edit', getMessage.FTE14159, 'itaButton aiSettingUpdateButton', { action: 'default'})}
                ${fn.html.iconButton('circle_check', '', 'itaButton aiSettingVerifyButton popup', { action: 'positive', title: getMessage.FTE14160 })}
                ${fn.html.iconButton('trash', '', 'itaButton aiSettingDeleteButton popup', { action: 'danger', title: getMessage.FTE14161 })}
            </div>
        </div>
        ${this.createItemModelHtml( service )}
    </li>`;
}
// 選択中のモデル（枠の下に表示する）
createItemModelHtml( service ) {
    const aiServiceId = service.ai_service_id;
    const selected = this.getSelectedModel( aiServiceId );

    if ( !selected ) {
        return `
        <div class="aiSettingItemModel">
            <div class="aiSettingModelEmpty">${fn.html.icon('circle_exclamation')} ${getMessage.FTE14162}</div>
        </div>`;
    }

    // 既定のモデルはピックアップモデルの中から選ぶため、一覧では強調して表示する
    const pickupHtml = selected.pickupModels.map(( model ) => {
        const currentClass = ( model.id === selected.modelId )? ' aiSettingModelCurrent': '';
        return `<li class="aiSettingModelItem${currentClass}">${fn.escape( this.getModelName( aiServiceId, model.id ) )}</li>`;
    });

    const pickupRow = ( pickupHtml.length )
        ? `<div class="aiSettingModelRow">
            <div class="aiSettingModelLabel">${getMessage.FTE14163}</div>
            <ul class="aiSettingModelList">${pickupHtml.join('')}</ul>
        </div>`
        : '';

    return `
    <div class="aiSettingItemModel">
        <div class="aiSettingModelRow">
            <div class="aiSettingModelLabel">${getMessage.FTE14164}</div>
            <div class="aiSettingModelDefault">${fn.escape( this.getModelName( aiServiceId, selected.modelId ) )}</div>
        </div>
        ${pickupRow}
    </div>`;
}
// Credentialの取得に失敗したAIサービス
createServiceErrorHtml() {
    const html = [];
    for ( const aiServiceId in this.credentialErrors ) {
        const service = this.getService( aiServiceId );
        const name = service?.ai_service_name ?? aiServiceId;
        html.push(`<li class="aiSettingNoticeItem">${fn.escape( name )}：${fn.escape( this.credentialErrors[ aiServiceId ] )}</li>`);
    }
    if ( !html.length ) return '';
    return `
    <div class="aiSettingNotice">
        <div class="aiSettingNoticeTitle">${fn.html.icon('attention')} ${getMessage.FTE14165}</div>
        <ul class="aiSettingNoticeList">${html.join('')}</ul>
    </div>`;
}
/*
##################################################
    ダイアログイベント
##################################################
*/
// AIサービスブロックは作り直すため、イベントはbodyへ委譲して1度だけ設定する
setDialogEvents() {
    const $body = this.dialog.$.dbody;

    $body.on('click', '.aiSettingAddServiceButton', () => {
        this.openCredentialDialog('register');
    });

    $body.on('click', '.aiSettingModelSelectButton', ( e ) => {
        const { aiService } = this.getItemData( e.currentTarget );
        this.openModelDialog( aiService );
    });

    $body.on('click', '.aiSettingVerifyButton', ( e ) => {
        const { aiService } = this.getItemData( e.currentTarget );
        this.verifyServiceItem( aiService, e.currentTarget );
    });

    $body.on('click', '.aiSettingUpdateButton', ( e ) => {
        const { aiService } = this.getItemData( e.currentTarget );
        this.openCredentialDialog('update', aiService );
    });

    $body.on('click', '.aiSettingDeleteButton', ( e ) => {
        const { aiService, credentialName } = this.getItemData( e.currentTarget );
        this.deleteServiceItem( aiService, credentialName );
    });

    // 使用するAIサービスの選択を変えたら、フッターの適用ボタンを押せるようにする
    $body.on('change', '.aiSettingUseRadio', () => {
        this.setApplyButtonState();
    });
}
// ボタンから対象のCredential情報を取得する
getItemData( button ) {
    const $item = $( button ).closest('.aiSettingItem');
    return {
        aiService: $item.attr('data-ai-service'),
        credentialName: $item.find('.aiSettingItemName').text()
    };
}
// 一覧で選択されているAIサービス
getCheckedAiServiceId() {
    if ( !this.dialog ) return '';
    return this.dialog.$.dbody.find('.aiSettingUseRadio:checked').val() ?? '';
}
// 使用中のAIサービスから選択が変わっていない場合（会話中の場合も）は適用できない
setApplyButtonState() {
    if ( !this.dialog ) return;
    const checkedId = this.getCheckedAiServiceId();
    this.dialog.buttonPositiveDisabled(
        this.serviceChangeLocked || !checkedId || this.isCurrentService( checkedId ) );
}
/*
##################################################
    AIサービス一覧の再描画
##################################################
*/
async reloadServiceBlock() {
    if ( !this.dialog ) return;
    const $block = this.dialog.$.dbody.find('.aiSettingServiceBlock');
    $block.html('<div class="aiSettingLoading nowLoading"></div>');
    try {
        await this.loadServiceList();
    } catch ( error ) {
        console.error( error );
        // 再描画中にダイアログが閉じられた場合は何もしない
        if ( this.dialog ) $block.html( this.createLoadErrorHtml( error ) );
        return;
    }
    if ( !this.dialog ) return;
    $block.html( this.createServiceBlockHtml() );
    // 一覧を作り直すとラジオの選択状態も変わるため、適用ボタンの状態も合わせる
    this.setApplyButtonState();
    return;
}
/*
##################################################
    使用するAIサービスの適用
##################################################
*/
// 一覧で選択したAIサービスを、現在選択中のAIサービスとして保存する
// 適用できた場合は設定ダイアログを閉じる
async applyUseService() {
    const title = getMessage.FTE14166;
    // ボタンは押せないようにしてあるが、状態の取り違えで適用されないように念のため確認する
    if ( this.serviceChangeLocked ) {
        await fn.alert( title, getMessage.FTE14167 );
        return;
    }
    const aiServiceId = this.getCheckedAiServiceId();
    const credential = this.getCredential( aiServiceId );
    if ( !aiServiceId || !credential ) {
        await fn.alert( title, getMessage.FTE14168 );
        return;
    }

    // モデルが未設定のAIサービスを適用してもチャットを開始できないため、先にモデルを選択してもらう
    if ( !this.getSelectedModel( aiServiceId ) ) {
        await fn.alert( title, getMessage.FTE14169 );
        return;
    }

    // 適用するとダイアログを閉じるため、実行前に確認する
    const check = await fn.iconConfirm('circle_check', title,
        getMessage.FTE14170( credential.credential_name ) );
    if ( !check ) return;

    // 適用中は操作できないようにする
    this.dialog.buttonDisabled();
    const processing = fn.processingModal( title );

    let error = null;
    try {
        await this.setPreference( aiServiceId );
    } catch ( e ) {
        console.error( e );
        error = e;
    }

    processing.close();
    if ( error ) {
        await fn.alert( title, getMessage.FTE14171( fn.escape( error.message ?? '') ) );
        // 適用できなかった場合はダイアログを開いたままにして、やり直せるようにする
        if ( this.dialog ) {
            this.dialog.buttonEnabled();
            await this.reloadServiceBlock();
        }
        return;
    }

    // 適用できたら設定ダイアログを閉じる
    await this.close();
    return;
}
/*
##################################################
    接続確認
##################################################
*/
// 接続確認はサーバー側で何も保存しないため、一覧の再描画は行わない
async verifyServiceItem( aiServiceId, button ) {
    const title = getMessage.FTE14172;
    const $button = $( button );
    $button.prop('disabled', true );
    const processing = fn.processingModal( title );

    let message = '';
    try {
        const result = await this.verifyCredential( aiServiceId );
        if ( result?.valid ) {
            const detail = ( result.account_id )? `<br>${getMessage.FTE14174( fn.escape( result.account_id ) )}`: '';
            message = `${getMessage.FTE14173}${detail}`;
        } else {
            message = getMessage.FTE14175( fn.escape( result?.message ?? '') );
        }
    } catch ( error ) {
        console.error( error );
        message = getMessage.FTE14176( fn.escape( error.message ?? '') );
    }

    processing.close();
    await fn.alert( title, message );

    $button.prop('disabled', false );
    return;
}
/*
##################################################
    削除
##################################################
*/
// Credentialを削除すると、そのAIサービスのモデルの設定もサーバー側で削除される。
// 使用中のAIサービスの場合は使用するAIサービスの設定もリセットされ、未選択の状態に戻る。
async deleteServiceItem( aiServiceId, credentialName ) {
    const title = getMessage.FTE14177;
    const isCurrent = this.isCurrentService( aiServiceId );
    const notice = ( isCurrent )
        ? '\n\n' + getMessage.FTE14178: '';

    const check = await fn.iconConfirm('circle_exclamation', title, getMessage.FTE14179( credentialName ) + notice );
    if ( !check ) return;

    try {
        await this.deleteCredential( aiServiceId );
    } catch ( error ) {
        console.error( error );
        await fn.alert( title, getMessage.FTE14180( fn.escape( error.message ?? '') ) );
    }
    await this.reloadServiceBlock();

    // 使用するAIサービスの設定がリセットされたことを呼び出し側へ通知する
    //   再描画でpreferenceを読み直しているため、選択中でなくなったことを確認できた場合のみ通知する
    if ( isCurrent && !this.isCurrentService( aiServiceId ) && this.option.onSave ) {
        this.option.onSave( this.preference );
    }
    return;
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   AIサービスの登録・更新ダイアログ
//
////////////////////////////////////////////////////////////////////////////////////////////////////
// ダイアログの表示名（mode: 'register' | 'update'）
static dialogTitle( mode ) {
    return ( mode === 'update')? getMessage.FTE14181: getMessage.FTE14182;
}
// 登録・更新モーダルコンフィグ
credentialDialogConfig( mode ) {
    return {
        position: 'center',
        width: '720px',
        header: {
            title: AiAssistantSetting.dialogTitle( mode )
        },
        footer: {
            button: {
                save: { text: ( mode === 'update')? getMessage.FTE14183: getMessage.FTE14184, action: 'positive', className: 'dialogPositive', width: '120px'},
                cancel: { text: getMessage.FTE10026, action: 'normal'}
            }
        }
    };
}
/*
##################################################
    登録・更新ダイアログを開く
##################################################
*/
// 更新の場合は対象のAIサービスIDを渡す
// 保存できた場合はtrue、キャンセルした場合はfalseで解決する
async openCredentialDialog( mode, aiServiceId = null ) {
    // 二重に開かない
    if ( this.credentialDialog ) return false;

    if ( mode === 'update') {
        if ( !this.getCredential( aiServiceId ) ) return false;
    } else if ( !this.unregisteredServiceList.length ) {
        // 1つのAIサービスにつき1件しか登録できない
        await fn.alert(AiAssistantSetting.dialogTitle( mode ), getMessage.FTE14185 );
        return false;
    }

    return new Promise(( resolve ) => {
        let dialog = null;

        const cancel = async () => {
            this.credentialDialog = null;
            await dialog.close();
            dialog = null;
            resolve( false );
        };

        const save = async () => {
            dialog.buttonDisabled();
            const saved = await this.saveFromDialog( dialog, mode, aiServiceId );
            if ( !saved ) {
                // 入力エラー・保存失敗時はダイアログを開いたままにする
                dialog.buttonEnabled();
                dialog.buttonPositiveDisabled( false );
                return;
            }
            this.credentialDialog = null;
            await dialog.close();
            dialog = null;
            await this.reloadServiceBlock();
            resolve( true );
        };

        dialog = new Dialog( this.credentialDialogConfig( mode ), { save: save, cancel: cancel });
        this.credentialDialog = dialog;
        dialog.open( this.createCredentialBodyHtml( mode, aiServiceId ) );
        dialog.buttonPositiveDisabled( false );

        // Credential名の初期値（AIサービス変更時、未編集なら初期値を差し替える）
        let defaultName = String( dialog.$.dbody.find('[name="credential_name"]').val() ?? '');

        // AIサービスを変更したら認証情報の入力欄を切り替える（更新時はAIサービスを変更できない）
        dialog.$.dbody.on('change', '.aiSettingServiceSelect', ( e ) => {
            const selected = e.currentTarget.value;
            const $name = dialog.$.dbody.find('[name="credential_name"]');
            if ( $name.val() === defaultName ) {
                defaultName = this.defaultCredentialName( selected );
                $name.val( defaultName );
            }
            dialog.$.dbody.find('.aiSettingServiceDescription').text( this.getService( selected )?.description ?? '');
            dialog.$.dbody.find('.aiSettingCredentialFields').html( this.createCredentialFieldsHtml( selected, mode ) );
        });

        // 選択したファイルの内容を入力欄へ読み込む
        dialog.$.dbody.on('click', '.aiSettingFileSelectButton', ( e ) => {
            this.readFileToInput( $( e.currentTarget ), AiAssistantSetting.dialogTitle( mode ) );
        });
    });
}
/*
##################################################
    ファイルを選択して入力欄に読み込む
##################################################
*/
async readFileToInput( $button, title ) {
    const $input = $button.closest('.inputPasswordWrap').find('.inputPassword');
    if ( !$input.length ) return;

    let file;
    try {
        file = await fn.fileSelect('file', AiAssistantSetting.fileSelectLimitSize, $button.attr('data-accept') );
    } catch ( error ) {
        // 選択をキャンセルした場合は何もしない
        if ( error === 'cancel') return;
        await fn.alert( title, getMessage.FTE14186( fn.escape( String( error?.message ?? error ) ) ) );
        return;
    }

    try {
        // 読み込んだ内容は貼り付けたときと同じ扱いにする（内容の確認は保存時に行う）
        $input.val( await this.fileToText( file ) ).trigger('change');
    } catch ( error ) {
        console.error( error );
        await fn.alert( title, getMessage.FTE14186( fn.escape( error.message ?? '') ) );
    }
}
// ファイルの実体を生テキストに変換する（fn.fileToTextは読み込み失敗時に解決しないため個別に用意する）
fileToText( file ) {
    return new Promise(( resolve, reject ) => {
        const reader = new FileReader();
        reader.onload = () => resolve( String( reader.result ?? '') );
        reader.onerror = () => reject( reader.error );
        reader.readAsText( file );
    });
}
/*
##################################################
    登録・更新ダイアログHTML
##################################################
*/
createCredentialBodyHtml( mode, aiServiceId = null ) {
    const credential = ( mode === 'update')? this.getCredential( aiServiceId ): null;
    let serviceBody = '';
    let selected = aiServiceId ?? '';

    if ( mode === 'update') {
        // 更新時はAIサービスを変更できないため、名称を表示するだけにする
        const service = this.getService( selected );
        serviceBody = `<div class="commonInputText">${fn.escape( service?.ai_service_name ?? selected )}</div>`
            + `<div class="aiSettingServiceDescription">${fn.escape( service?.description ?? '')}</div>`;
    } else {
        const selectList = this.unregisteredServiceList.map(( item ) => {
            return { id: item.ai_service_id, text: item.ai_service_name ?? item.ai_service_id };
        });
        selected = selectList[0]?.id ?? '';
        serviceBody = fn.html.select( selectList, 'aiSettingServiceSelect', selected, 'ai_service_id', {}, { idText: true })
            + `<div class="aiSettingServiceDescription">${fn.escape( this.getService( selected )?.description ?? '')}</div>`;
    }

    // 登録時は「AIサービス名_日時」を初期値にする
    const credentialName = ( mode === 'update')? credential?.credential_name ?? '': this.defaultCredentialName( selected );

    const rows = [
        this.createInputRowHtml('ai_service_id', getMessage.FTE14187, serviceBody, mode !== 'update'),
        this.createInputRowHtml('credential_name', getMessage.FTE14188,
            fn.html.inputText('', credentialName, 'credential_name', { placeholder: 'My Bedrock Credential'}), true )
    ];

    return `
    <div class="aiSettingCredentialForm" spellcheck="false">
        <div class="commonSection">
            <div class="commonTitle">${getMessage.FTE14187}</div>
            <div class="commonBody">
                <div class="commonInputGroup">
                    <table class="commonInputTable">
                        <tbody class="commonInputTbody">${rows.join('')}</tbody>
                    </table>
                </div>
            </div>
        </div>
        <div class="commonSection">
            <div class="commonTitle">${getMessage.FTE14189}</div>
            <div class="commonBody">
                <div class="commonInputGroup aiSettingCredentialFields">${this.createCredentialFieldsHtml( selected, mode )}</div>
            </div>
        </div>
    </div>`;
}
// Credential名の初期値（AIサービス名_日時）
defaultCredentialName( aiServiceId ) {
    if ( !aiServiceId ) return '';
    const name = this.getService( aiServiceId )?.ai_service_name ?? aiServiceId;
    return `${name}_${fn.date( new Date(), 'yyyyMMdd_HHmmss')}`;
}
// 認証情報の入力欄
createCredentialFieldsHtml( aiServiceId, mode = 'register') {
    const fields = this.getCredentialFields( aiServiceId );
    if ( !fields.length ) {
        return `<div class="aiSettingFieldsNote">${fn.html.icon('circle_info')} ${getMessage.FTE14190}</div>`;
    }

    // 更新時、マスク対象外（passwordタイプ以外）の項目は登録済みの値が返るため入力欄に反映する
    const credentialData = ( mode === 'update')? this.getCredential( aiServiceId )?.credential_data ?? {}: {};

    const rows = fields.map(( field ) => {
        return this.createInputRowHtml( field.key, field.title, this.createFieldInputHtml( field, credentialData ), field.required, field.note );
    });

    // 更新は全体置換だが、マスクされている項目は取得できないため引き継げない
    const modeNote = ( mode === 'update')
        ? `<div class="aiSettingFieldsNote">${fn.html.icon('circle_info')} ${getMessage.FTE14191}</div>`
        : '';

    return modeNote + `
    <table class="commonInputTable">
        <tbody class="commonInputTbody">${rows.join('')}</tbody>
    </table>`;
}
// 入力欄HTML
createFieldInputHtml( field, credentialData = {}) {
    // マスクされる項目は登録済みの値を取得できないため、常に空で表示する
    const value = ( field.type === 'password')? '': String( credentialData[ field.key ] ?? '');

    // JSONの貼り付けなどで複数行にする。マスク表示にして、目のボタンで表示を切り替える。
    if ( field.multiline ) {
        const option = { textarea: 'sizing'};

        // 貼り付けの代わりにファイルからも読み込めるようにする（ボタンはパスワード表示ボタンの下に置く）
        if ( field.fileSelect ) {
            option.subButton = fn.html.button( fn.html.icon('upload'), 'itaButton aiSettingFileSelectButton popup', {
                action: 'default',
                title: getMessage.FTE14192,
                accept: field.fileSelect
            });
        }
        return fn.html.inputPassword('aiSettingJsonInput', value, field.key, {}, option );
    }
    if ( field.type === 'password') {
        return fn.html.inputPassword('', value, field.key );
    }
    return fn.html.inputText('', value, field.key );
}
// 入力列HTML
createInputRowHtml( key, title, body, required = false, note = '') {
    const requiredHtml = ( required )? '<span class="aiSettingRequired">*</span>': '';
    const noteHtml = ( note )? `<div class="aiSettingFieldNote">${fn.escape( note )}</div>`: '';
    return `
    <tr class="commonInputTr">
        <th class="commonInputTh"><div class="commonInputTitle">${fn.escape( title )}${requiredHtml}</div></th>
        <td class="commonInputTd" data-key="${key}">${body}${noteHtml}</td>
    </tr>`;
}
/*
##################################################
    ダイアログの内容を保存する
##################################################
*/
async saveFromDialog( dialog, mode, aiServiceId = null ) {
    const $body = dialog.$.dbody;
    const title = AiAssistantSetting.dialogTitle( mode );

    // 更新時はAIサービスを変更できないため、対象のIDをそのまま使用する
    const serviceId = ( mode === 'update')? aiServiceId: $body.find('.aiSettingServiceSelect').val();
    if ( !this.getService( serviceId ) ) {
        await fn.alert( title, getMessage.FTE14193 );
        return false;
    }

    const credentialName = String( $body.find('[name="credential_name"]').val() ?? '').trim();
    if ( credentialName === '') {
        await fn.alert( title, getMessage.FTE14194 );
        return false;
    }

    const credentialData = await this.createCredentialDataFromDialog( $body, this.getCredentialFields( serviceId ), title );
    if ( !credentialData ) return false;

    const notes = String( $body.find('[name="notes"]').val() ?? '').trim();

    try {
        if ( mode === 'update') {
            await this.updateCredential( serviceId, credentialName, credentialData, notes );
        } else {
            await this.registerCredential( serviceId, credentialName, credentialData, notes );
        }
    } catch ( error ) {
        console.error( error );
        await fn.alert( title, getMessage.FTE14195( ( mode === 'update')? getMessage.FTE14183: getMessage.FTE14184, fn.escape( error.message ?? '') ) );
        return false;
    }

    // 保存できたら続けて検証する。検証に失敗しても保存自体は残す。
    const savedText = ( mode === 'update')? getMessage.FTE14196: getMessage.FTE14197;
    try {
        const verify = await this.verifyCredential( serviceId );
        if ( !verify?.valid ) {
            await fn.alert( title, getMessage.FTE14198( savedText, fn.escape( verify?.message ?? '') ) );
        }
    } catch ( error ) {
        console.error( error );
        await fn.alert( title, getMessage.FTE14198( savedText, fn.escape( error.message ?? '') ) );
    }
    return true;
}
/*
##################################################
    入力内容からcredential_dataを組み立てる
##################################################
*/
// 入力に問題がある場合はメッセージを表示してnullを返す
async createCredentialDataFromDialog( $body, fields, title ) {
    if ( !fields.length ) {
        await fn.alert( title, getMessage.FTE14199 );
        return null;
    }

    const credentialData = {};
    for ( const field of fields ) {
        const value = String( $body.find(`[name="${field.key}"]`).val() ?? '').trim();
        if ( value === '') {
            if ( field.required ) {
                await fn.alert( title, getMessage.FTE14200( fn.escape( field.title ) ) );
                return null;
            }
            continue;
        }

        // JSONを貼り付ける項目は、送信前に内容を確認する（値は文字列のまま送信する）
        if ( field.json ) {
            const check = await this.checkJsonField( field, value, title );
            if ( !check ) return null;
        }

        credentialData[ field.key ] = value;
    }

    // 入力欄をすべて省略した場合、credential_dataが必須のため保存できない
    if ( !Object.keys( credentialData ).length ) {
        await fn.alert( title, getMessage.FTE14201 );
        return null;
    }
    return credentialData;
}
/*
##################################################
    貼り付けられたJSONを確認する
##################################################
*/
// サーバー側で受け付けられない内容を、送信前に見つけて知らせる
async checkJsonField( field, value, title ) {
    let json;
    try {
        json = JSON.parse( value );
    } catch ( error ) {
        await fn.alert( title, getMessage.FTE14202( fn.escape( field.title ), fn.escape( error.message ) ) );
        return false;
    }
    if ( fn.typeof( json ) !== 'object') {
        await fn.alert( title, getMessage.FTE14203( fn.escape( field.title ) ) );
        return false;
    }

    const lackKeys = ( field.requiredKeys ?? [] ).filter(( key ) => !( key in json ) );
    if ( lackKeys.length ) {
        await fn.alert( title, getMessage.FTE14204( fn.escape( field.title ), fn.escape( lackKeys.join(', ') ) ) );
        return false;
    }
    return true;
}
////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   モデル選択ダイアログ
//
////////////////////////////////////////////////////////////////////////////////////////////////////
// モデル選択モーダルコンフィグ
get modelDialogConfig() {
    return {
        position: 'center',
        width: '960px',
        header: {
            title: getMessage.FTE14205
        },
        footer: {
            button: {
                save: { text: getMessage.FTE14206, action: 'positive', className: 'dialogPositive', width: '120px'},
                cancel: { text: getMessage.FTE10026, action: 'normal'}
            }
        }
    };
}
/*
##################################################
    モデル選択ダイアログを開く
##################################################
*/
// 設定できた場合はtrue、キャンセルした場合はfalseで解決する
async openModelDialog( aiServiceId ) {
    // 二重に開かない
    if ( this.modelDialog ) return false;
    if ( !this.getCredential( aiServiceId ) ) return false;

    return new Promise(( resolve ) => {
        let dialog = null;

        const cancel = async () => {
            this.modelDialog = null;
            await dialog.close();
            dialog = null;
            resolve( false );
        };

        const save = async () => {
            dialog.buttonDisabled();
            const saved = await this.saveModelFromDialog( dialog, aiServiceId );
            if ( !saved ) {
                // 入力エラー・保存失敗時はダイアログを開いたままにする
                dialog.buttonEnabled();
                this.setModelDialogSaveState( dialog );
                return;
            }
            this.modelDialog = null;
            await dialog.close();
            dialog = null;
            await this.reloadServiceBlock();
            resolve( true );
        };

        dialog = new Dialog( this.modelDialogConfig, { save: save, cancel: cancel, headerClose: cancel });
        this.modelDialog = dialog;

        // モデル一覧の取得はBedrockへの問い合わせが必要で時間がかかるため、bodyなしで開いてローディング表示にする
        dialog.open();
        dialog.buttonPositiveDisabled( true );
        this.loadModelDialog( dialog, aiServiceId );
    });
}
/*
##################################################
    モデル一覧を読み込む
##################################################
*/
async loadModelDialog( dialog, aiServiceId ) {
    let modelList = [];
    try {
        modelList = await this.getModelList( aiServiceId );
    } catch ( error ) {
        console.error( error );
        // 読み込み中にダイアログが閉じられた場合は何もしない
        if ( this.modelDialog !== dialog ) return;
        dialog.setBody( this.createModelLoadErrorHtml( error ) );
        return;
    }
    if ( this.modelDialog !== dialog ) return;

    dialog.setBody( this.createModelBodyHtml( aiServiceId, modelList ) );
    this.setModelDialogEvents( dialog );
    // グループの選択件数は描画後に反映する（一部だけ選択されている場合の中間状態はHTMLで表せない）
    this.updateModelGroupState( dialog.$.dbody );
    this.setModelDialogSaveState( dialog );
    return;
}
// 読み込み失敗
createModelLoadErrorHtml( error ) {
    const message = error?.message ?? getMessage.FTE14207;
    return `
    <div class="aiSettingEmpty">
        <div class="aiSettingEmptyMessage">${fn.html.icon('circle_exclamation')} ${getMessage.FTE14207}</div>
        <div class="aiSettingEmptyNote">${fn.escape( message )}</div>
    </div>`;
}
/*
##################################################
    モデル選択ダイアログHTML
##################################################
*/
createModelBodyHtml( aiServiceId, modelList ) {
    if ( !modelList.length ) {
        return `
        <div class="aiSettingEmpty">
            <div class="aiSettingEmptyMessage">${fn.html.icon('circle_exclamation')} ${getMessage.FTE14208}</div>
            <div class="aiSettingEmptyNote">${getMessage.FTE14209}</div>
        </div>`;
    }

    // このAIサービスに保存されている設定（利用できなくなったモデルは選択済みとして扱わない）
    const selected = this.getSelectedModel( aiServiceId );
    const pickupModelIds = ( selected?.pickupModels ?? [] ).map(( model ) => model.id )
        .filter(( modelId ) => modelList.some(( model ) => model.id === modelId ) );

    // モデルIDには記号が含まれるため、idにはそのまま使わず連番を使う
    let itemIndex = 0;

    const groupHtml = this.groupModelList( modelList ).map(( group, groupIndex ) => {
        const itemHtml = group.models.map(( model ) => {
            const attrs = {};
            if ( pickupModelIds.includes( model.id ) ) attrs.checked = 'checked';
            const inputHtml = fn.html.checkboxText('aiSettingPickupCheck', model.id, 'pickup_model_ids', `aiSettingPickup_${itemIndex++}`, attrs, fn.escape( model.name ) );
            // 絞り込みは表示名とモデルIDの両方を対象にするため、小文字にした検索用の文字列を持たせておく
            return `
            <li class="aiSettingModelSelectItem" data-search="${fn.escape(`${model.name} ${model.id}`.toLowerCase() )}" title="${fn.escape( model.id )}">
                ${inputHtml}
            </li>`;
        });

        // モデルが多いため既定では閉じておき、選択済みのモデルを含むグループだけ開いた状態にする
        const openClass = ( group.models.some(( model ) => pickupModelIds.includes( model.id ) ) )? ' aiSettingModelGroupOpen': '';
        return `
        <li class="aiSettingModelGroup${openClass}">
            <div class="aiSettingModelGroupHeader">
                ${fn.html.check('aiSettingPickupGroupCheck', group.key, 'pickup_model_group', `aiSettingPickupGroup_${groupIndex}`)}
                <button class="aiSettingModelGroupToggle" type="button">
                    ${fn.html.icon('arrow02_bottom', 'aiSettingModelGroupIcon')}
                    <span class="aiSettingModelGroupName">${fn.escape( group.name )}</span>
                    <span class="aiSettingModelGroupCount"></span>
                </button>
            </div>
            <ul class="aiSettingModelGroupList">${itemHtml.join('')}</ul>
        </li>`;
    });

    return `
    <div class="aiSettingModelSelect" data-ai-service="${fn.escape( aiServiceId )}">
        <div class="commonSection aiSettingModelSelectSection">
            <div class="commonTitle">${getMessage.FTE14163}</div>
            <div class="commonBody">
                <div class="aiSettingModelSelectNote">${getMessage.FTE14210}</div>
                <div class="aiSettingModelFilter">
                    ${fn.html.icon('search')}
                    <input type="text" class="aiSettingModelFilterText input inputText" spellcheck="false" name="model_filter" placeholder="${getMessage.FTE14211}" autocomplete="off">
                    <button class="aiSettingModelFilterClear" type="button">${fn.html.icon('cross')}</button>
                </div>
                <ul class="aiSettingModelSelectList">${groupHtml.join('')}</ul>
                <div class="aiSettingModelSelectEmpty aiSettingModelFilterEmpty">${fn.html.icon('circle_info')} ${getMessage.FTE14212}</div>
            </div>
        </div>
        <div class="commonSection aiSettingModelSelectSection">
            <div class="commonTitle">${getMessage.FTE14164}</div>
            <div class="commonBody">
                <div class="aiSettingModelSelectNote">${getMessage.FTE14213}</div>
                <ul class="aiSettingModelSelectList aiSettingDefaultModelList">${this.createDefaultModelListHtml( aiServiceId, pickupModelIds, selected?.modelId )}</ul>
            </div>
        </div>
    </div>`;
}
// 既定のモデル（ピックアップモデルの選択に合わせて作り直す）
createDefaultModelListHtml( aiServiceId, pickupModelIds, modelId ) {
    if ( !pickupModelIds.length ) {
        return `<li class="aiSettingModelSelectEmpty">${fn.html.icon('circle_info')} ${getMessage.FTE14214}</li>`;
    }

    // 選択中の既定のモデルがピックアップから外れた場合は、先頭のピックアップモデルを既定にする
    const checkedModelId = ( pickupModelIds.includes( modelId ) )? modelId: pickupModelIds[0];

    return pickupModelIds.map(( pickupModelId, index ) => {
        const attrs = {};
        if ( pickupModelId === checkedModelId ) attrs.checked = 'checked';
        const inputHtml = fn.html.radioText('aiSettingDefaultRadio', pickupModelId, 'model_id', `aiSettingDefault_${index}`, attrs,
            fn.escape( this.getModelName( aiServiceId, pickupModelId ) ) );
        return `
        <li class="aiSettingModelSelectItem">
            ${inputHtml}
        </li>`;
    }).join('');
}
/*
##################################################
    モデルのグループ化
##################################################
*/
// 同じ系統のモデル（リージョン違い・バージョン違い）をまとめる
groupModelList( modelList ) {
    const groups = [];
    for ( const model of modelList ) {
        const { provider, family } = this.getModelFamily( model.id );
        const key = ( family.length )? `${provider}.${family.join('-')}`: '';

        let group = groups.find(( item ) => item.key === key );
        if ( !group ) {
            group = { key: key, provider: provider, family: family, models: []};
            groups.push( group );
        }
        group.models.push( model );
    }

    // 複数のプロバイダーのモデルが並ぶ場合は、グループ名にプロバイダーも入れて区別できるようにする
    const multiProvider = new Set( groups.map(( group ) => group.provider ) ).size > 1;
    for ( const group of groups ) {
        const words = ( multiProvider )? [ group.provider, ...group.family ]: group.family;
        group.name = ( group.family.length )
            ? words.filter(( word ) => word ).map(( word ) => word.charAt(0).toUpperCase() + word.slice(1) ).join(' ')
            : getMessage.FTE14215;
    }

    // 表示名にリージョンとバージョンが含まれるため、名称順に並べるとリージョン・バージョンごとに並ぶ
    const collator = new Intl.Collator('ja', { numeric: true });
    for ( const group of groups ) {
        group.models.sort(( a, b ) => collator.compare( a.name, b.name ) );
    }
    return groups.sort(( a, b ) => {
        // 系統がわからないモデルのグループは最後にする
        if ( !a.key ) return 1;
        if ( !b.key ) return -1;
        return collator.compare( a.name, b.name );
    });
}
// モデルIDから系統を取り出す（例：global.anthropic.claude-opus-5 → anthropic ＋ claude opus）
getModelFamily( modelId ) {
    // 推論プロファイルIDは <リージョン>.<プロバイダー>.<モデル名> の形式で、リージョンが付かないモデルIDもある
    const parts = String( modelId ?? '').split('.');
    const provider = ( parts.length >= 2 )? parts[ parts.length - 2 ]: '';

    // バージョン（5・4-5・v2）や日付（20241022）は系統の違いではないため、名前から取り除く
    const family = ( parts[ parts.length - 1 ] ?? '').replace(/:.*$/, '').split(/[-_]/)
        .filter(( word ) => word && !/^\d/.test( word ) && !/^v\d+$/.test( word ) );

    return { provider: provider, family: family };
}
/*
##################################################
    モデル選択ダイアログイベント
##################################################
*/
setModelDialogEvents( dialog ) {
    const $body = dialog.$.dbody;

    $body.on('change', '.aiSettingPickupCheck', () => {
        this.updateModelSelectState( dialog );
    });

    // グループ内のモデルをまとめて選択する（絞り込み中は表示されているモデルのみ）
    $body.on('change', '.aiSettingPickupGroupCheck', ( e ) => {
        $( e.currentTarget ).closest('.aiSettingModelGroup')
            .find('.aiSettingModelSelectItem').not('.aiSettingModelSelectItemHide')
            .find('.aiSettingPickupCheck').prop('checked', e.currentTarget.checked );
        this.updateModelSelectState( dialog );
    });

    // グループの開閉
    $body.on('click', '.aiSettingModelGroupToggle', ( e ) => {
        $( e.currentTarget ).closest('.aiSettingModelGroup').toggleClass('aiSettingModelGroupOpen');
    });

    // モデルの絞り込み
    $body.on('input', '.aiSettingModelFilterText', ( e ) => {
        this.filterModelList( dialog, e.currentTarget.value );
    });
    $body.on('click', '.aiSettingModelFilterClear', () => {
        $body.find('.aiSettingModelFilterText').val('');
        this.filterModelList( dialog, '');
    });
}
// ピックアップモデルの選択に合わせて、既定のモデルの選択肢とグループ・設定ボタンの状態を作り直す
updateModelSelectState( dialog ) {
    const $body = dialog.$.dbody;
    const aiServiceId = $body.find('.aiSettingModelSelect').attr('data-ai-service');

    $body.find('.aiSettingDefaultModelList').html(
        this.createDefaultModelListHtml( aiServiceId, this.getPickupModelIdsFromDialog( dialog ), this.getDefaultModelIdFromDialog( dialog ) )
    );
    this.updateModelGroupState( $body );
    this.setModelDialogSaveState( dialog );
}
// グループの選択件数と一括選択チェックボックスの状態を合わせる（絞り込みで表示されているモデルが対象）
updateModelGroupState( $body ) {
    $body.find('.aiSettingModelGroup').each(( index, group ) => {
        const $items = $( group ).find('.aiSettingModelSelectItem').not('.aiSettingModelSelectItemHide');
        const itemLength = $items.length;
        const checkedLength = $items.find('.aiSettingPickupCheck:checked').length;

        $( group ).find('.aiSettingModelGroupCount').text(`${checkedLength} / ${itemLength}`);

        // 一部だけ選択されている場合は中間状態にする
        const groupCheck = group.querySelector('.aiSettingPickupGroupCheck');
        if ( groupCheck ) {
            groupCheck.checked = ( itemLength > 0 && checkedLength === itemLength );
            groupCheck.indeterminate = ( checkedLength > 0 && checkedLength < itemLength );
        }
    });
}
// 入力された文字でモデルを絞り込む（表示名・モデルIDの部分一致、空白区切りはAND条件）
filterModelList( dialog, keyword ) {
    const $body = dialog.$.dbody;
    const words = keyword.trim().toLowerCase().split(/\s+/).filter(( word ) => word );

    let matchLength = 0;
    $body.find('.aiSettingModelGroup').each(( index, group ) => {
        let groupMatchLength = 0;
        $( group ).find('.aiSettingModelSelectItem').each(( itemIndex, item ) => {
            const searchText = item.getAttribute('data-search') ?? '';
            const isMatch = words.every(( word ) => searchText.includes( word ) );
            item.classList.toggle('aiSettingModelSelectItemHide', !isMatch );
            if ( isMatch ) groupMatchLength++;
        });
        // 該当するモデルがないグループは隠し、絞り込み中は該当するモデルが見えるように開く
        group.classList.toggle('aiSettingModelGroupHide', groupMatchLength === 0 );
        group.classList.toggle('aiSettingModelGroupFilterOpen', words.length > 0 && groupMatchLength > 0 );
        matchLength += groupMatchLength;
    });

    $body.find('.aiSettingModelFilterEmpty').toggleClass('aiSettingModelFilterEmptyShow', matchLength === 0 );
    // 一括選択の対象が変わるため、グループの状態も合わせる
    this.updateModelGroupState( $body );
}
// ピックアップモデルが未選択の場合は設定できない
setModelDialogSaveState( dialog ) {
    dialog.buttonPositiveDisabled( this.getPickupModelIdsFromDialog( dialog ).length === 0 );
}
// 選択されているピックアップモデル
getPickupModelIdsFromDialog( dialog ) {
    return dialog.$.dbody.find('.aiSettingPickupCheck:checked').map(( index, input ) => input.value ).get();
}
// 選択されている既定のモデル
getDefaultModelIdFromDialog( dialog ) {
    return dialog.$.dbody.find('.aiSettingDefaultRadio:checked').val() ?? '';
}
/*
##################################################
    モデルの設定を保存する
##################################################
*/
async saveModelFromDialog( dialog, aiServiceId ) {
    const title = getMessage.FTE14205;
    const pickupModelIds = this.getPickupModelIdsFromDialog( dialog );
    if ( !pickupModelIds.length ) {
        await fn.alert( title, getMessage.FTE14214 );
        return false;
    }

    const modelId = this.getDefaultModelIdFromDialog( dialog );
    if ( !pickupModelIds.includes( modelId ) ) {
        await fn.alert( title, getMessage.FTE14216 );
        return false;
    }

    // モデルIDだけでは表示名がわからないため、取得済みのモデル一覧から表示名を添えて保存する
    const pickupModels = pickupModelIds.map(( pickupModelId ) => {
        return { id: pickupModelId, name: this.getModelName( aiServiceId, pickupModelId ) };
    });

    try {
        // AI利用設定はAIサービスごとに全置換で保存する
        await this.setServicePreference( aiServiceId, modelId, this.getModelName( aiServiceId, modelId ), pickupModels );
    } catch ( error ) {
        console.error( error );
        await fn.alert( title, getMessage.FTE14217( fn.escape( error.message ?? '') ) );
        return false;
    }

    // 使用するAIサービスが1つも適用されていない場合は、設定できたこのAIサービスをそのまま使用する
    if ( !this.preference?.ai_service_id ) {
        try {
            await this.setPreference( aiServiceId );
        } catch ( error ) {
            console.error( error );
            await fn.alert( title, getMessage.FTE14218( fn.escape( error.message ?? '') ) );
        }
    }
    return true;
}

}
