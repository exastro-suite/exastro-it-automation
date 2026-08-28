////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Exastro IT Automation / bedrock.js
//
//   -----------------------------------------------------------------------------------------------
//
//   AWS Bedrock API (Claude)
//
////////////////////////////////////////////////////////////////////////////////////////////////////

export class DevelopmentSupportModule {
/*
##################################################
    Constructor
##################################################
*/
constructor() {
    this.chatHistory = [];
}
/*
##################################################
    Setup
##################################################
*/
setup( apiParam ) {
    if ( apiParam ) this.param = apiParam;
    return new Promise(async ( resolve, reject ) => {
        try {
            // AWS SDK v3を読み込み
            // ローカルのnode_modulesを優先、フォールバックとしてCDNを使用
            let bedrockModule;
            try {
                bedrockModule = await import('/_/ita/lib/aws-bedrock/aws-bedrock-runtime.bundle.js');
            } catch (error) {
                throw error;
            }
            this.BedrockRuntimeClient = bedrockModule.BedrockRuntimeClient;
            this.InvokeModelCommand = bedrockModule.InvokeModelCommand;

            // クライアント設定の準備
            const clientConfig = {
                region: this.param?.region || 'ap-northeast-1'
            };

            // 認証情報の構築
            const accessKeyId = this.param?.accessKeyId;
            const secretAccessKey = this.param?.secretAccessKey;
            const sessionToken = this.param?.sessionToken;

            // 認証情報が指定されている場合のみ設定
            if ( accessKeyId && secretAccessKey ) {
                const credentials = {
                    accessKeyId: accessKeyId.trim(),
                    secretAccessKey: secretAccessKey.trim()
                };

                // Session Tokenがある場合は追加（SSOや一時認証情報用）
                if ( sessionToken ) {
                    credentials.sessionToken = sessionToken.trim();
                }

                clientConfig.credentials = credentials;
            } else {
                // 認証情報が指定されていない場合はエラー
                const error = new Error('Access Key ID and Secret Access Key are required. Please check your input fields.');
                console.error('Setup failed:', {
                    accessKeyId: accessKeyId ? 'provided' : 'missing',
                    secretAccessKey: secretAccessKey ? 'provided' : 'missing'
                });
                throw error;
            }

            // クライアントの初期化
            this.client = new this.BedrockRuntimeClient(clientConfig);

            // デフォルトモデルの設定
            if ( apiParam?.modelDefault && apiParam.modelDefault.id ) {
                this.setModel( apiParam.modelDefault.id );
            } else {
                this.setModel( 'jp.anthropic.claude-sonnet-4-5-20250929-v1:0' );
            }

            resolve();
        } catch ( error ) {
            console.error('Bedrock setup error:', error);
            reject( error );
        }
    });
}
/*
##################################################
    Send prompt
##################################################
*/
send( prompt, file ) {
    return new Promise(async ( resolve, reject ) => {
        try {
            // ファイルがある場合はプロンプトに追加
            if ( file ) {
                const filePrompt = `[FILE NAME:${file.name}\nFILE CONTENTS:${file.body}]\n`;
                prompt = filePrompt + prompt;
            }

            // Claude APIのメッセージ形式に変換
            const messages = [
                ...this.chatHistory,
                {
                    role: 'user',
                    content: prompt
                }
            ];

            // リクエストボディの作成
            const requestBody = {
                anthropic_version: 'bedrock-2023-05-31',
                max_tokens: 4096,
                messages: messages,
                temperature: 0.7
            };

            // システムプロンプトがある場合は追加
            if ( this.systemInstruction ) {
                requestBody.system = this.systemInstruction;
            }

            // Bedrock APIへのリクエスト
            const command = new this.InvokeModelCommand({
                modelId: this.modelId,
                contentType: 'application/json',
                accept: 'application/json',
                body: JSON.stringify(requestBody)
            });

            const response = await this.client.send(command);

            // レスポンスのパース
            const responseBody = JSON.parse(new TextDecoder().decode(response.body));
            const assistantMessage = responseBody.content[0].text;

            // 会話履歴に追加
            this.chatHistory.push({
                role: 'user',
                content: prompt
            });
            this.chatHistory.push({
                role: 'assistant',
                content: assistantMessage
            });

            resolve( assistantMessage );
        } catch ( error ) {
            // エラーメッセージを改善
            if ( error.message && error.message.includes("isn't supported") ) {
                error.message = `Model ${this.modelId} is not available. Please check:\n1. Model Access is enabled in Bedrock console\n2. Correct region is selected\n3. Model ID format (e.g., jp.anthropic.* for Japan region)`;
            } else if ( error.message && error.message.includes("not authorized") ) {
                error.message = `Permission denied. Please contact your AWS administrator to grant bedrock:InvokeModel permission.`;
            }
            reject( error );
        }
    });
}
/*
##################################################
    Model list
##################################################
*/
getModelList( paramObj ) {
    return new Promise(async ( resolve, reject ) => {
        try {
            // development_support.jsからは、設定画面の全フィールドがオブジェクトで渡される想定
            let accessKeyId, secretAccessKey, sessionToken, region;

            if ( typeof paramObj === 'object' && paramObj !== null ) {
                // オブジェクトとして渡された場合
                accessKeyId = paramObj.accessKeyId;
                secretAccessKey = paramObj.secretAccessKey;
                sessionToken = paramObj.sessionToken;
                region = paramObj.region;
            } else if ( typeof paramObj === 'string' ) {
                // 文字列の場合、geminiのapiKeyと同じ扱い（後方互換性）
                // この場合はエラーを出す
                throw new Error('AWS Bedrock requires accessKeyId and secretAccessKey. Please configure them in the settings.');
            } else {
                // 引数なしの場合、setup()で保存された認証情報を使用
                accessKeyId = this.param?.accessKeyId;
                secretAccessKey = this.param?.secretAccessKey;
                sessionToken = this.param?.sessionToken;
                region = this.param?.region;
            }

            // 認証情報の検証
            if ( !accessKeyId || !secretAccessKey ) {
                const error = new Error('Access Key ID and Secret Access Key are required. Please enter them in the settings dialog.');
                console.error('getModelList failed:', {
                    accessKeyId: accessKeyId ? 'provided' : 'missing',
                    secretAccessKey: secretAccessKey ? 'provided' : 'missing',
                    paramType: typeof paramObj,
                    paramExists: !!this.param
                });
                throw error;
            }

            // AWS SDK v3を読み込み
            let bedrockModule;
            try {
                // ローカルのバンドルファイルから読み込み
                bedrockModule = await import('/_/ita/lib/aws-bedrock/aws-bedrock.bundle.js');
            } catch (error) {
                throw error;
            }
            const BedrockClient = bedrockModule.BedrockClient;
            const ListInferenceProfilesCommand = bedrockModule.ListInferenceProfilesCommand;

            const credentialsObj = {
                accessKeyId: accessKeyId.trim(),
                secretAccessKey: secretAccessKey.trim()
            };

            // Session Tokenがある場合は追加
            if ( sessionToken ) {
                credentialsObj.sessionToken = sessionToken.trim();
            }

            const client = new BedrockClient({
                region: region || 'ap-northeast-1',
                credentials: credentialsObj
            });

            // ListInferenceProfilesCommandを使用（Pythonのlist_inference_profiles()と同じ）
            const command = new ListInferenceProfilesCommand({});

            const response = await client.send(command);

            // モデルリストを整える
            const list = [];
            const currentRegion = region || 'ap-northeast-1';

            if ( response.inferenceProfileSummaries ) {
                for ( const item of response.inferenceProfileSummaries ) {
                    // Anthropicのモデルのみフィルタリング
                    const models = item.models || [];
                    const isAnthropic = models.some(m => m.modelArn?.includes('anthropic'));

                    if ( !isAnthropic ) continue;

                    // inferenceProfileIdをモデルIDとして使用
                    const modelId = item.inferenceProfileId;
                    const modelName = item.inferenceProfileName || modelId;
                    const status = item.status || 'UNKNOWN';
                    const profileType = item.type || 'UNKNOWN';

                    list.push({
                        id: modelId,
                        text: modelName,
                        description: `Type: ${profileType} | Status: ${status}`,
                        raw: item
                    });
                }
                resolve( list );
            } else {
                reject({ message: 'No inference profiles found' });
            }
        } catch ( error ) {
            console.error('getModelList error:', error);
            reject( error );
        }
    });
}
/*
##################################################
    Chat history
##################################################
*/
getChatHistory() {
    return this.chatHistory;
}
/*
##################################################
    Model set
##################################################
*/
setModel( modelId = 'jp.anthropic.claude-sonnet-4-5-20250929-v1:0') {
    // デフォルトモデルID
    this.modelId = modelId;

    const systemInstruction = getMessage.FTE14104;
    // const systemInstruction = [
    //     'あなたは親切なインフラエンジニアです。',
    //     'Ansible Playbookの記述方法を教えるのがあなたの仕事です。',
    //     'Ansible Playbookを答えるときはtasksのセクションの配下だけをtasksを含めずに切り出して答えます。',
    //     'Ansible Playbookのtasksのセクションを切り出したものを"Exastro IT Automation用 Playbook"と呼称します。',
    //     'Ansible moduleのインストールが必要な時は、別途Ansible moduleのインストール方法も教えてください。',
    //     'また、pythonのライブラリーのインストールが必要な時は、別途pythonのライブラリーのインストール方法も教えてください。',
    //     'Ansible Playbook内で指定する値は、冒頭でset_factで大文字の変数名の変数に代入してから使用してください。'
    // ]
    this.systemInstruction = systemInstruction.join("\n");

    // モデル変更時は履歴は保持するがクリアも可能
    // 必要に応じて this.chatHistory = [] でクリア
}
/*
##################################################
    Setting
##################################################
*/
setting = {
    accessKeyId: {
        title: 'AWS Access Key ID',
        type: 'password',
        required: true
    },
    secretAccessKey: {
        title: 'AWS Secret Access Key',
        type: 'password',
        required: true
    },
    sessionToken: {
        title: 'AWS Session Token (optional for SSO)',
        type: 'password',
        required: false
    },
    region: {
        title: 'AWS Region',
        type: 'text',
        required: false
    },
    modelSelect: {
        title: getMessage.FTE14102,
        type: 'modelSelect'
    },
    modelDefault: {
        title: getMessage.FTE14103,
        type: 'modelDefault'
    }
}

}
