////////////////////////////////////////////////////////////////////////////////////////////////////
//
//   Exastro IT Automation / gemini.js
//
//   -----------------------------------------------------------------------------------------------
//
//   Gemini API
//
////////////////////////////////////////////////////////////////////////////////////////////////////

export class DevelopmentSupportModule {
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
setup( apiParam ) {
    if ( apiParam ) this.param = apiParam;
    return new Promise(async ( resolve, reject ) => {
        try {
            const module = await import('https://esm.run/@google/generative-ai');
            this.genAI = new module.GoogleGenerativeAI( this.param.apiKey );
            this.chat = null;
            if ( apiParam.modelDefault && apiParam.modelDefault.id ) {
                this.setModel( apiParam.modelDefault.id );
            }
            resolve();
        } catch ( error ) {
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
            if ( file ) {
                const filePrompt = `[FILE NAME:${file.name}\nFILE CONTENTS:${file.body}]\n`;
                prompt = filePrompt + prompt;
            }
            const result = await this.chat.sendMessage( prompt );
            resolve( result.response.text() );
        } catch ( error ) {
            reject( error );
        }
    });
}
/*
##################################################
    Model list
##################################################
*/
getModelList( apiKey ) {
    return new Promise(async ( resolve, reject ) => {
        // GeminiのAIリスト取得APIにHTTPリクエスト送信
        fetch('https://generativelanguage.googleapis.com/v1beta/models', {
            headers: {
                'x-goog-api-key': apiKey
            }
        })
            // レスポンスをJSONに変換
            .then(response => response.json())
            // JSONデータを data として受け、models プロパティの存在判定
            .then( data => {
                if ( data.models ) {
                    // モデルリストを整える
                    const list = [];
                    for ( const item of data.models ) {
                        list.push({
                            id: item.name,
                            text: item.displayName,
                            description: item.description,
                            raw: item
                        });
                    }
                    resolve( list );
                } else if ( data.error ) {
                    reject( data.error );
                } else {
                    reject({ message: getMessage.FTE14012});
                }
            })
            // 例外処理
            .catch(error => {
                reject( error );
            });
    }); 
}
/*
##################################################
    Chat hitsory
##################################################
*/
getChatHistory() {
    return ( this.chat )? this.chat._history : undefined;
}
/*
##################################################
    Model set
##################################################
*/
setModel( modelName = '') {
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
    this.model = this.genAI.getGenerativeModel({
        model: modelName,
        systemInstruction: systemInstruction.join("\n")
    });
    
    // 履歴があれば引き継ぐ
    const history = this.getChatHistory() ?? [];
    this.chat = this.model.startChat({
        history: history
    });
}
/*
##################################################
    Setting
##################################################
*/
setting = {
    apiKey: {
        title: getMessage.FTE14101,
        type: 'password'
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