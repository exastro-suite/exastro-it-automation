#   Copyright 2022 NEC Corporation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


import json
import urllib
import ssl
import re
import inspect
import time
from flask import g

from common_libs.common.util import ky_decrypt
from common_libs.ansible_driver.functions.util import getAnsibleConst
from common_libs.common.dbconnect.dbconnect_ws import DBConnectWs


def setAACRestAPITimoutVaule(objdbca):
    g.AACRestAPITimout = None
    # ansibleインターフェース情報取得
    sql = "SELECT * FROM T_ANSC_IF_INFO WHERE DISUSE_FLAG='0'"
    inforows = objdbca.sql_execute(sql, [])
    # 件数判定はしない
    inforow = inforows[0]
    # RestAPIタイムアウト値確認
    if not inforow['ANSTWR_REST_TIMEOUT']:
        # 空の場合、デフォルト値を設定
        g.AACRestAPITimout = 60
    else:
        g.AACRestAPITimout = inforow['ANSTWR_REST_TIMEOUT']

def getAACRestAPITimoutVaule():
    return g.AACRestAPITimout

class RestApiCaller():

    """
    【概要】
        AnsibleTower REST API call クラス
    """

    API_BASE_PATH = "/api/v2/"
    API_TOKEN_PATH = "authtoken/"

    def __init__(self, protocol, hostName, portNo, encryptedAuthToken, proxySetting, driver_id=None):

        self.baseURI = '%s://%s:%s%s' % (protocol, hostName, portNo, self.API_BASE_PATH)
        self.directURI = '%s://%s:%s' % (protocol, hostName, portNo)
        self.decryptedAuthToken = ky_decrypt(encryptedAuthToken)
        self.proxySetting = proxySetting
        self.accessToken = None
        self.RestResultList = []

        self.AnsConstObj = None
        if driver_id:
            self.AnsConstObj = getAnsibleConst(driver_id)

    def getOrchestratorSubId_dir(self):
        return self.AnsConstObj.vg_OrchestratorSubId_dir

    def authorize(self):

        self.accessToken = self.decryptedAuthToken

        response_array = {}
        response_array['success'] = True
        response_array['responseContents'] = self.accessToken

        return response_array

    def restCall(self, method, apiUri, content=None, header=None, Rest_stdout_flg=False, DirectUrl=False):

        httpContext = {}
        headers = {}
        ssl_context = None

        response_array = {}

        if Rest_stdout_flg == False:
            # コンテンツ付与
            if content:
                httpContext['http'] = {}
                httpContext['http']['content'] = json.dumps(content).encode('utf-8')
                headers['Content-type'] = 'application/json'

            # Header精査
            if self.accessToken:
                headers['Authorization'] = 'Bearer %s' % (self.accessToken)

            if self.hasHeaderField(headers, "Accept") is False:
                headers['Accept'] = 'application/json'

        else:
            if content:
                httpContext['http'] = {}
                httpContext['http']['content'] = json.dumps(content).encode('utf-8')

            headers['Authorization'] = 'Bearer %s' % (self.accessToken)

        # HTTPコンテキスト作成
        if 'http' not in httpContext:
            httpContext['http'] = {}

        httpContext['http']['method'] = method
        httpContext['http']['ignore_errors'] = True

        ################################
        # Proxy設定
        ################################
        if 'address' in self.proxySetting and self.proxySetting['address']:
            address = self.proxySetting['address']
            if 'port' in self.proxySetting and self.proxySetting['port']:
                address = '%s:%s' % (address, self.proxySetting['port'])

            httpContext['http']['proxy'] = address
            httpContext['http']['request_fulluri'] = True

        # 暫定対応 SSL認証エラー無視
        ssl_context = ssl._create_unverified_context()
        httpContext['ssl'] = {}
        httpContext['ssl']['verify_peer'] = False
        httpContext['ssl']['verify_peer_name'] = False

        if DirectUrl == False:
            url = '%s%s' % (self.baseURI, apiUri)

        else:
            url = '%s%s' % (self.directURI, apiUri)

        print_HttpContext = 'http context\n%s' % (httpContext)
        print_url = "URL: %s\n" % (url)
        # RESTAPI失敗時は３回までリトライ
        for t in range(3):
            self.RestResultList = []
            ################################
            # RestCall
            ################################
            http_response_header = None
            data = None
            if 'content' in httpContext['http']:
                data = httpContext['http']['content']

            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            if 'address' in self.proxySetting and self.proxySetting['address']:
                req.set_proxy(self.proxySetting['address'], 'http')
                req.set_proxy(self.proxySetting['address'], 'https')

            try:
                RestTimeout = getAACRestAPITimoutVaule()
                startlog = "[Trace] ansible automation controller rest api request start. (url:{} method:{})".format(url, method)
                endlog = "[Trace] ansible automation controller rest api request done."
                g.applogger.info(startlog)     # 外部アプリへの処理開始・終了ログ
                with urllib.request.urlopen(req, context=ssl_context, timeout=RestTimeout) as resp:
                    g.applogger.info(endlog)
                    status_code = resp.getcode()
                    http_response_header = resp.getheaders()
                    responseContents = resp.read().decode('utf-8')

                    print_HttpStatusCode = "http ststus code: %s" % (str(status_code))
                    print_HttpResponsHeader = "http response header\n%s" % (str(http_response_header))
                    print_ResponseContents = "http response contents\n%s" % (str(responseContents))
            except urllib.error.HTTPError as e:
                # 返却用のArrayを編集
                response_array['statusCode'] = -2
                response_array['responseContents'] = {"errorMessage":"HTTP access error "}

                print_Except = \
                    "Except HTTPError\n" \
                    "http status code: %s\n" \
                    "http response contents: %s\n" \
                    "http response headers: %s\n" \
                    "http response body: %s" \
                    % (e.code, e.reason, e.headers, e.read().decode())
                self.apperrorloger(self.backtrace())
                self.apperrorloger(print_url)
                self.apperrorloger(print_HttpContext)
                self.apperrorloger(print_Except)

            except urllib.error.URLError as e:
                # 返却用のArrayを編集
                response_array['statusCode'] = -2
                response_array['responseContents'] = {"errorMessage":"HTTP access error "}

                print_Except = "Except URLError\nhttp response contents: %s" % (e.reason)
                self.apperrorloger(self.backtrace())
                self.apperrorloger(print_url)
                self.apperrorloger(print_HttpContext)
                self.apperrorloger(print_Except)

            else:
                response_array = {}
                if not isinstance(http_response_header, list):
                    # 返却用のArrayを編集
                    response_array['statusCode'] = -2
                    response_array['responseContents'] = {"errorMessage":"HTTP access error "}

                    self.apperrorloger(self.backtrace())
                    self.apperrorloger(print_url)
                    self.apperrorloger(print_HttpContext)
                    self.apperrorloger(print_HttpStatusCode)
                    self.apperrorloger(print_HttpResponsHeader)
                    self.apperrorloger(print_ResponseContents)

                else:
                    # 通信結果を判定
                    if len(http_response_header) > 0:
                        print_HttpResponsHeader = "http response header\n"
                        for t in http_response_header:
                            print_HttpResponsHeader += '%s: %s\n' % (t[0], t[1])

                        # 返却用のArrayを編集
                        response_array['statusCode'] = status_code
                        if status_code < 200 or status_code >= 400:
                            response_array['responseHeaders'] = http_response_header
                            response_array['responseContents'] = {"errorMessage":responseContents}

                            self.apperrorloger(self.backtrace())
                            self.apperrorloger(print_url)
                            self.apperrorloger(print_HttpContext)
                            self.apperrorloger(print_HttpStatusCode)
                            self.apperrorloger(print_HttpResponsHeader)
                            self.apperrorloger(print_ResponseContents)

                        else:
                            response_array['responseHeaders'] = http_response_header
                            response_array['responseContents'] = responseContents
                            for arrHeader in response_array['responseHeaders']:
                                if re.search('^\s*Content-Type$', arrHeader[0]):
                                    if re.search('\s*application\/json', arrHeader[1]):
                                        try:
                                            response_array['responseContents'] = json.loads(responseContents)

                                        except json.JSONDecodeError as e:
                                            response_array['responseContents'] = None

                            # 正常時
                            self.apperrorloger(self.backtrace(), False)
                            self.apperrorloger(print_url, False)
                            self.apperrorloger(print_HttpContext, False)
                            self.apperrorloger(print_HttpStatusCode, False)
                            self.apperrorloger(print_HttpResponsHeader, False)
                            self.apperrorloger(print_ResponseContents, False)
                    else:
                        print_HttpResponsHeader = "http response header\n%s" % (http_response_header)

                        # 返却用のArrayを編集
                        response_array['statusCode'] = -2
                        response_array['responseContents'] = {"errorMessage":"HTTP Socket Timeout"}

                        self.apperrorloger(self.backtrace())
                        self.apperrorloger(print_url)
                        self.apperrorloger(print_HttpContext)
                        self.apperrorloger(print_HttpStatusCode)
                        self.apperrorloger(print_HttpResponsHeader)
                        self.apperrorloger(print_ResponseContents)

            # ステータスコードがが200～399ではない場合はリトライ
            if response_array['statusCode'] < 200 or response_array['statusCode'] >= 400:
                time.sleep(1)
                continue
            else:
                break

        return response_array

    def hasHeaderField(self, header, field):

        if isinstance(header, dict) is False:
            return False

        if field in header:
            return True

        return False

    def getAccessToken(self):
        return self.accessToken

    def apperrorloger(self, msg, stdout=True):
        if stdout is True:
            # applogger.error => applogger.info
            g.applogger.info(msg)
        self.RestResultList.append(msg)

    def getRestResultList(self):
        return self.RestResultList

    def backtrace(self):
        print_backtrace = "-------------------------backtrace----------------------\n"
        trace = inspect.currentframe()
        while trace:
            print_backtrace += '%s: line:%s\n' % (trace.f_code.co_filename, trace.f_lineno)
            trace = trace.f_back
        return print_backtrace
