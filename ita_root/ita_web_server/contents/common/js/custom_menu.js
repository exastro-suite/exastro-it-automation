function getToken() {
    return CommonAuth.getToken();
}

function getRealm() {
    return CommonAuth.getRealm();
}

function getWorkspace() {
    return window.location.pathname.split('/')[3];
}

function customMenu( info ) {
    return new Promise(function( resolve, reject ) {
        const mainHtml = ( info )? info.custom_menu['main.html']: null;

        if ( mainHtml ) {
            // base64 > text変換
            fn.base64Decode( mainHtml ).then(function( text ){
                try {
                    // 各種素材をBASE64で埋め込む
                    for ( const fileName in info.custom_menu ) {
                        if ( fileName === 'main.html') continue;

                        const
                        base64 = info.custom_menu[ fileName ],
                        fileType = fn.customMenufileTypeCheck( fileName ),
                        attr = ( fileType === 'style')? 'href': 'src',
                        reg = new RegExp(`(?<=${attr}=")${fileName}(.*?)(?=")`),
                        mine = ( fileType === 'style')? 'text/css': ( fileType === 'script')? 'text/javascript': `image/${fn.imageMimeTypeCheck( fileName )}`

                        text = text.replace( reg, `data:${mine};base64,${base64}`);
                    }

                    // iframeを作成
                    const $iframe = $('<iframe>', {
                        class: 'customMenuIframe',
                        srcdoc: text,
                        src: 'about:blank'
                    });
                    resolve( $iframe );
                } catch ( error ) {
                    window.console.error( error );
                    reject();
                }
            }).catch(function( error ){
                window.console.error( error );
                reject();
            });
        } else {
            reject();
        }
    });
}