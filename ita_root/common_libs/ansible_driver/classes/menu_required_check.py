from flask import g

from common_libs.ansible_driver.classes.AnscConstClass import AnscConst



class AuthTypeParameterRequiredCheck:
    chkType_Loadtable_DeviceList = '1'
    chkType_Loadtable_TowerHostList = '2'
    chkType_WorkflowExec_DevaiceList = '3'
    chkType_WorkflowExec_TowerHostList = '4'
    
    def __init__(self):
        self.err_msg_code_ary = {}
        # ERROR_TYPE1: (xxxx)認証方式がパスワード認証の場合、パスワードは必須項目です。
        # ERROR_TYPE2: (xxxx)認証方式が鍵認証の場合、公開鍵ファイルは必須項目です。";
        # ERROR_TYPE3: (xxxx)認証方式が鍵認証(パスフレーズあり)の場合、公開鍵ファイルは必須項目です。
        # ERROR_TYPE4: (xxxx)認証方式が鍵認証(パスフレーズあり)の場合、パスフレーズは必須項目です。
        # ERROR_TYPE5: (xxxx)認証方式が選択されていません。
        # ERROR_TYPE6: (xxxx)認証方式がパスワード認証の場合、ログインパスワードの管理は必須項目です。
        # ERROR_TYPE7: (xxxx)認証方式が不正です。
        # ERROR_TYPE8: (xxxx)ログインユーザーIDが未入力です。
        # ERROR_TYPE9: 機器一覧の認証方式が不正です。pioneerでパスワード認証(winrm)は対応していません。(host:{})";
        # ERROR_TYPE10: 機器一覧のPioneer利用情報のプロトコルが選択されていません。(host:{})
        # ERROR_TYPE11: 機器一覧のPioneer利用情報のプロトコルが不正です。(host:{})
        # AuthType 1:機器一覧ロードテーブル
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_Loadtable_DeviceList] = {}
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_Loadtable_DeviceList]['ERROR_TYPE1'] = "MSG-10232"
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_Loadtable_DeviceList]['ERROR_TYPE2'] = "MSG-10233"
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_Loadtable_DeviceList]['ERROR_TYPE3'] = "MSG-10234"
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_Loadtable_DeviceList]['ERROR_TYPE4'] = "MSG-10235"
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_Loadtable_DeviceList]['ERROR_TYPE5'] = "MSG-10236"
        # 未使用
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_Loadtable_DeviceList]['ERROR_TYPE6'] = "MSG-10237"
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_Loadtable_DeviceList]['ERROR_TYPE7'] = "MSG-10238"
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_Loadtable_DeviceList]['ERROR_TYPE8'] = "MSG-10239"
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_Loadtable_DeviceList]['ERROR_TYPE9'] = "MSG-10240"
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_Loadtable_DeviceList]['ERROR_TYPE10'] = "MSG-10241"
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_Loadtable_DeviceList]['ERROR_TYPE11'] = "MSG-10242"

        # AuthType 2:Towerホスト一覧ロードテーブル
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_Loadtable_TowerHostList] = {}
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_Loadtable_TowerHostList]['ERROR_TYPE1'] = "MSG-10232"
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_Loadtable_TowerHostList]['ERROR_TYPE2'] = "MSG-10233"
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_Loadtable_TowerHostList]['ERROR_TYPE3'] = "MSG-10234"
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_Loadtable_TowerHostList]['ERROR_TYPE4'] = "MSG-10235"
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_Loadtable_TowerHostList]['ERROR_TYPE5'] = "MSG-10236"
        # 未使用
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_Loadtable_TowerHostList]['ERROR_TYPE6'] = "MSG-10237"
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_Loadtable_TowerHostList]['ERROR_TYPE7'] = "MSG-10238"
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_Loadtable_TowerHostList]['ERROR_TYPE8'] = "MSG-10239"
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_Loadtable_TowerHostList]['ERROR_TYPE9'] = "MSG-10240"
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_Loadtable_TowerHostList]['ERROR_TYPE10'] = "MSG-10241"
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_Loadtable_TowerHostList]['ERROR_TYPE11'] = "MSG-10242"

        # AuthType 3:作業実行 機器一覧チェック
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_WorkflowExec_DevaiceList] = {}
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_WorkflowExec_DevaiceList]['ERROR_TYPE1'] = "MSG-10210"
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_WorkflowExec_DevaiceList]['ERROR_TYPE2'] = "MSG-10211"
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_WorkflowExec_DevaiceList]['ERROR_TYPE3'] = "MSG-10212"
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_WorkflowExec_DevaiceList]['ERROR_TYPE4'] = "MSG-10213"
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_WorkflowExec_DevaiceList]['ERROR_TYPE5'] = "MSG-10214"
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_WorkflowExec_DevaiceList]['ERROR_TYPE6'] = "MSG-10215"
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_WorkflowExec_DevaiceList]['ERROR_TYPE7'] = "MSG-10216"
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_WorkflowExec_DevaiceList]['ERROR_TYPE8'] = "MSG-10217"
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_WorkflowExec_DevaiceList]['ERROR_TYPE9'] = "MSG-10218"
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_WorkflowExec_DevaiceList]['ERROR_TYPE10'] = "MSG-10219"
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_WorkflowExec_DevaiceList]['ERROR_TYPE11'] = "MSG-10220"

        # AuthType 4:作業実行 Towerホスト一覧チェック
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_WorkflowExec_TowerHostList] = {}
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_WorkflowExec_TowerHostList]['ERROR_TYPE1'] = "MSG-10221"
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_WorkflowExec_TowerHostList]['ERROR_TYPE2'] = "MSG-10222"
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_WorkflowExec_TowerHostList]['ERROR_TYPE3'] = "MSG-10223"
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_WorkflowExec_TowerHostList]['ERROR_TYPE4'] = "MSG-10224"
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_WorkflowExec_TowerHostList]['ERROR_TYPE5'] = "MSG-10225"
        # 未使用
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_WorkflowExec_TowerHostList]['ERROR_TYPE6'] = "MSG-10226"
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_WorkflowExec_TowerHostList]['ERROR_TYPE7'] = "MSG-10227"
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_WorkflowExec_TowerHostList]['ERROR_TYPE8'] = "MSG-10228"
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_WorkflowExec_TowerHostList]['ERROR_TYPE9'] = "MSG-10229"
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_WorkflowExec_TowerHostList]['ERROR_TYPE10'] = "MSG-10230"
        self.err_msg_code_ary[AuthTypeParameterRequiredCheck.chkType_WorkflowExec_TowerHostList]['ERROR_TYPE11'] = "MSG-10231"
    
    def DeviceListAuthTypeRequiredParameterCheck(self, chk_type, err_msg_parameter_ary, str_auth_mode, str_login_user, str_passwd, str_ssh_key_file, str_passphrase, driver_id):  # str_protocol_idを後で引数に追加
        """
        処理内容
        機器一覧とTowerホスト一覧で選択されている認証方式の必須入力チェック
        ARGS:
        $AuthType:            呼び元区分
                                    2:Towerホスト一覧ロードテーブル
                                    4:作業実行 Towerホスト一覧チェック
                                    1:機器一覧ロードテーブル　
                                    3:作業実行 機器一覧チェック
            err_msg_parameter_ary   エラーメッセージのパラメータ配列
                                    機器一覧
                                    array(機器一覧['HOSTNAME'])
                                    Towerホスト一覧
                                    array(Towerホスト一覧['ANSTWR_HOSTNAME'])
            str_auth_mode:           認証方式
                                    1:鍵認証
                                    2:パスワード認証
                                    3:鍵認証(鍵交換済み)
                                    4:鍵認証(パスフレーズあり)
                                    5:認証方式:パスワード認証(winrm)
            str_login_user:         ログインユーザー
            str_passwd:             パスワード
            str_ssh_key_file:       公開鍵ファイル
            str_passphrase:         パスフレーズ
            driver_id:              ドライバ識別子
                                    DF_LEGACY_DRIVER_ID
                                    DF_LEGACY_ROLE_DRIVER_ID
                                    DF_PIONEER_DRIVER_ID
            str_protocol_id:        Pioneerプロトコル
                                        "": 未選択
                                        1:  telnet
                                        2:  ssh
        
        RETRUN:
            retBool :True/ False
            msg :エラーメッセージ
        """
        retBool = ""
        result = ""
        msg = ""
        # 認証方式:鍵認証(パスフレーズなし), 認証方式:パスワード認証, 認証方式:鍵認証(鍵交換済み), 認証方式:鍵認証(パスフレーズあり), 認証方式:パスワード認証(winrm)
        if str_auth_mode == AnscConst.DF_LOGIN_AUTH_TYPE_KEY or str_auth_mode == AnscConst.DF_LOGIN_AUTH_TYPE_PW or str_auth_mode == AnscConst.DF_LOGIN_AUTH_TYPE_KEY_EXCH or str_auth_mode == AnscConst.DF_LOGIN_AUTH_TYPE_KEY_PP_USE or str_auth_mode == AnscConst.DF_LOGIN_AUTH_TYPE_PW_WINRM:
            # ログインユーザーIDの入力チェック
            if not str_login_user:
                error_cde = self.err_msg_code_ary[chk_type]['ERROR_TYPE8']
                if len(result) != 0:
                    result += "\n"
                result = g.appmsg.get_api_message(error_cde, [err_msg_parameter_ary])

        # 認証方式毎の必須入力チェック
        if str_auth_mode == AnscConst.DF_LOGIN_AUTH_TYPE_KEY:  # 認証方式:鍵認証(パスフレーズなし)
            if not str_ssh_key_file:
                error_cde = self.err_msg_code_ary[chk_type]['ERROR_TYPE2']
                if len(result) != 0:
                    result += "\n"
                result = g.appmsg.get_api_message(error_cde, [err_msg_parameter_ary])
        elif str_auth_mode == AnscConst.DF_LOGIN_AUTH_TYPE_PW:  # 認証方式:パスワード認証
            if not str_passwd:
                error_cde = self.err_msg_code_ary[chk_type]['ERROR_TYPE1']
                if len(result) != 0:
                    result += "\n"
                result = g.appmsg.get_api_message(error_cde, [err_msg_parameter_ary])
        elif str_auth_mode == AnscConst.DF_LOGIN_AUTH_TYPE_KEY_EXCH or str_auth_mode == AnscConst.DF_LOGIN_AUTH_TYPE_PW_WINRM:  # 認証方式:鍵認証(鍵交換済み),認証方式:パスワード認証(winrm)
            pass
        elif str_auth_mode == AnscConst.DF_LOGIN_AUTH_TYPE_KEY_PP_USE:  # 認証方式:鍵認証(パスフレーズあり)
            if not str_ssh_key_file:
                error_cde = self.err_msg_code_ary[chk_type]['ERROR_TYPE3']
                result = g.appmsg.get_api_message(error_cde, [err_msg_parameter_ary])
            if not str_passphrase:
                error_cde = self.err_msg_code_ary[chk_type]['ERROR_TYPE4']
                if len(result) != 0:
                    result += "\n"
                result += g.appmsg.get_api_message(error_cde, [err_msg_parameter_ary])
        elif not str_auth_mode:  # 認証方式: 未選択
            pass
        else:  # 認証方式が不正
            error_cde = self.err_msg_code_ary[chk_type]['ERROR_TYPE7']
            if len(result) != 0:
                result += "\n"
            result += g.appmsg.get_api_message(error_cde, [err_msg_parameter_ary])
        
        # 作業実行からの場合に実行ドライバとPioneerプロトコルと認証方式の組み合わせ確認
        if chk_type == AuthTypeParameterRequiredCheck.chkType_WorkflowExec_DevaiceList:
            if driver_id == AnscConst.DF_LEGACY_DRIVER_ID or driver_id == AnscConst.DF_LEGACY_ROLE_DRIVER_ID:  # Legacy, Role
                # 認証方式選択チェック
                if not str_auth_mode:
                    error_cde = self.err_msg_code_ary[chk_type]['ERROR_TYPE5']
                    if len(result) != 0:
                        result += "\n"
                    result += g.appmsg.get_api_message(error_cde, [err_msg_parameter_ary])
            """
            str_protocol_idがないためコメントアウト
            elif driver_id == AnscConst.DF_PIONEER_DRIVER_ID:  # pioneer
                if str_protocol_id == '2':  # ssh
                    if str_auth_mode == AnscConst.DF_LOGIN_AUTH_TYPE_PW_WINRM:  # 認証方式:パスワード認証(winrm)
                        error_cde = self.err_msg_code_ary[chk_type]['ERROR_TYPE9']
                        if len(result) != 0:
                            result += "\n"
                        result += g.appmsg.get_api_message(error_cde, [err_msg_parameter_ary])
                    elif str_auth_mode == '':
                        error_cde = self.err_msg_code_ary[chk_type]['ERROR_TYPE5']
                        if len(result) != 0:
                            result += "\n"
                        result += g.appmsg.get_api_message(error_cde, [err_msg_parameter_ary])
                elif str_protocol_id == '1':  # telnet
                    # 認証方式:鍵認証(パスフレーズなし), 認証方式:パスワード認証, 認証方式:鍵認証(鍵交換済み), 認証方式:鍵認証(パスフレーズあり), 認証方式:パスワード認証(winrm)
                    if str_auth_mode == AnscConst.DF_LOGIN_AUTH_TYPE_KEY or str_auth_mode == AnscConst.DF_LOGIN_AUTH_TYPE_PW or str_auth_mode == AnscConst.DF_LOGIN_AUTH_TYPE_KEY_EXCH or str_auth_mode == AnscConst.DF_LOGIN_AUTH_TYPE_KEY_PP_USE or str_auth_mode == AnscConst.DF_LOGIN_AUTH_TYPE_PW_WINRM or str_auth_mode == '':
                        pass
                elif str_protocol_id == '' or str_protocol_id is None:
                    # pioneer利用情報のプロトコル未選択
                    error_cde = self.err_msg_code_ary[chk_type]['ERROR_TYPE10']
                    if len(result) != 0:
                        result += "\n"
                    result += g.appmsg.get_api_message(error_cde, [err_msg_parameter_ary])
                else:
                    # 認証方式が不正
                    error_cde = self.err_msg_code_ary[chk_type]['ERROR_TYPE11']
                    if len(result) != 0:
                        result += "\n"
                    result += g.appmsg.get_api_message(error_cde, [err_msg_parameter_ary])
            """
        if len(result) == 0:
            retBool = True
            msg = ""
        else:
            retBool = False
            msg = result
        return retBool, msg

    def TowerHostListAuthTypeRequiredParameterCheck(self, chk_type, err_msg_parameter_ary, str_auth_mode, str_passwd, str_ssh_key_file, str_passphrase):
        """
        処理内容
            Towerホスト一覧で選択されている認証方式の必須入力チェック
        ARGS:
            chk_type:            呼び元区分
                                    2:Towerホスト一覧ロードテーブル
                                    4:作業実行 Towerホスト一覧チェック
                                    1:機器一覧ロードテーブル　
                                    3:作業実行 機器一覧チェック 
            str_auth_mode:          認証方式
                                    1:鍵認証 
                                    2:パスワード認証(パスフレーズなし)
                                    3:鍵認証(鍵交換済み) 
                                    4:鍵認証(パスフレーズあり)
            str_passwd:            パスワード
            str_ssh_key_file:        公開鍵ファイル
            str_passphrase:        パスフレーズ
        RETRUN:
            retBool :True/ False
            msg :エラーメッセージ
        """
        retBool = ""
        result = ""
        msg = ""
        if str_auth_mode == AnscConst.DF_LOGIN_AUTH_TYPE_KEY:  # 鍵認証(パスフレーズなし)
            if not str_ssh_key_file:
                error_cde = self.err_msg_code_ary[chk_type]['ERROR_TYPE2']
                if len(result) != 0:
                    result += "\n"
                result = g.appmsg.get_api_message(error_cde, [err_msg_parameter_ary])
        if str_auth_mode == AnscConst.DF_LOGIN_AUTH_TYPE_PW:        # 認証方式:パスワード認証
            if not str_passwd:
                error_cde = self.err_msg_code_ary[chk_type]['ERROR_TYPE1']
                if len(result) != 0:
                    result += "\n"
                result = g.appmsg.get_api_message(error_cde, [err_msg_parameter_ary])
                
        if str_auth_mode == AnscConst.DF_LOGIN_AUTH_TYPE_KEY_EXCH:   # 認証方式:鍵認証(鍵交換済み)
            pass
        if str_auth_mode == AnscConst.DF_LOGIN_AUTH_TYPE_KEY_PP_USE:  # 認証方式:鍵認証(パスフレーズあり)
            if not str_ssh_key_file:
                error_cde = self.err_msg_code_ary[chk_type]['ERROR_TYPE3']
                if len(result) != 0:
                    result += "\n"
                result = g.appmsg.get_api_message(error_cde, [err_msg_parameter_ary])
                
            if not str_passphrase:
                error_cde = self.err_msg_code_ary[chk_type]['ERROR_TYPE4']
                if len(result) != 0:
                    result += "\n"
                result += g.appmsg.get_api_message(error_cde, [err_msg_parameter_ary])
                
        if len(result) == 0:
            retBool = True
            msg = ""
        else:
            retBool = False
            msg = result
        return retBool, msg
