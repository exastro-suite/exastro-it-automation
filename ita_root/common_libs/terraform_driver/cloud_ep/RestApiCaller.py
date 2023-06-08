#   Copyright 2023 NEC Corporation
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
import time
import inspect
from flask import g
from common_libs.common.util import ky_decrypt


class RestApiCaller():
    """
    【概要】
        Terraform Cloud/Enterprise用 REST API call クラス
    """
    API_BASE_PATH = "/api/v2"

    def __init__(self, protocol, hostName, portNo=None, encryptedAuthToken=None, proxySetting=None):
        if portNo:
            self.baseURI = '%s://%s:%s%s' % (protocol, hostName, portNo, self.API_BASE_PATH)
            self.targetHost = '%s://%s:%s' % (protocol, hostName, portNo)
        else:
            self.baseURI = '%s://%s%s' % (protocol, hostName, self.API_BASE_PATH)
            self.targetHost = '%s://%s' % (protocol, hostName)
        if encryptedAuthToken:
            self.decryptedAuthToken = ky_decrypt(encryptedAuthToken)
        else:
            self.decryptedAuthToken = encryptedAuthToken
        self.proxySetting = proxySetting
        self.accessToken = None
        self.RestResultList = []

    def authorize(self):
        self.accessToken = self.decryptedAuthToken
        response_array = {}
        response_array['success'] = True
        response_array['responseContents'] = self.accessToken

        return response_array

    def rest_call(self, method, api_uri, content=None, header=None, module_upload_flag=False, direct_url="", get_log=False):  # noqa: C901
        # 変数定義
        httpContext = {}
        httpContext['http'] = {}
        headers = {}
        ssl_context = None
        self.RestResultList = []
        response_array = {}
        proxy_address = ""

        # コンテンツ付与
        if module_upload_flag is True:
            headers['Content-type'] = 'application/octet-stream'
        else:
            headers['Content-type'] = 'application/vnd.api+json'
            if content is not None:
                httpContext['http']['content'] = json.dumps(content).encode('utf-8')

        # Header精査
        if self.accessToken:
            headers['Authorization'] = 'Bearer %s' % (self.accessToken)

        if self.hasHeaderField(headers, "Accept") is False:
            if module_upload_flag is True:
                headers['Accept'] = 'application/octet-stream'
            else:
                headers['Accept'] = 'application/vnd.api+json'

        # HTTPコンテキスト作成
        httpContext['http']['method'] = method
        httpContext['http']['ignore_errors'] = True

        # Proxy設定
        if 'address' in self.proxySetting and self.proxySetting['address']:
            proxy_address = self.proxySetting['address']
            if 'port' in self.proxySetting and self.proxySetting['port']:
                proxy_address = '%s:%s' % (proxy_address, self.proxySetting['port'])

            httpContext['http']['proxy'] = proxy_address
            httpContext['http']['request_fulluri'] = True

        # [暫定対応] SSL認証エラー無視
        ssl_context = ssl._create_unverified_context()
        httpContext['ssl'] = {}
        httpContext['ssl']['verify_peer'] = False
        httpContext['ssl']['verify_peer_name'] = False

        # URL定義
        if direct_url:
            url = direct_url
        else:
            url = '%s%s' % (self.baseURI, api_uri)

        print_HttpContext = 'http context\n%s' % (httpContext)
        print_url = "URL: %s\n" % (url)

        # RESTAPI失敗時は３回までリトライ
        for t in range(3):
            ################################
            # RestCall
            ################################
            http_response_header = None
            data = None
            if module_upload_flag is True:
                data = content
            else:
                if 'content' in httpContext['http']:
                    data = httpContext['http']['content']

            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            if proxy_address:
                req.set_proxy(proxy_address, 'http')
                req.set_proxy(proxy_address, 'https')
            try:
                with urllib.request.urlopen(req, context=ssl_context, timeout=10) as resp:
                    status_code = resp.getcode()
                    http_response_header = resp.getheaders()
                    responseContents = resp.read().decode('utf-8')
                    print_HttpStatusCode = "http ststus code: %s" % (str(status_code))
                    print_HttpResponsHeader = "http response header\n%s" % (str(http_response_header))
                    print_ResponseContents = "http response contents\n%s" % (str(responseContents))

            except urllib.error.HTTPError as e:
                # 返却用のArrayを編集
                response_array['statusCode'] = e.code
                e_read = json.loads(e.read())
                if e_read:
                    errors = e_read.get('errors')
                    if isinstance(errors, list):
                        error_detail = errors[0]
                    elif isinstance(errors, dict):
                        error_detail = errors[0].get('detail')
                    else:
                        error_detail = errors
                    if error_detail:
                        response_array['responseContents'] = {"errorMessage": error_detail}
                    else:
                        response_array['responseContents'] = {"errorMessage": "HTTP access error "}
                else:
                    response_array['responseContents'] = {"errorMessage": "HTTP access error "}

                # ログ出力
                self.appinfologer(print_url)
                self.appinfologer(print_HttpContext)

            except urllib.error.URLError as e:
                # 返却用のArrayを編集
                response_array['statusCode'] = -2
                response_array['responseContents'] = {"errorMessage": "HTTP access error "}

                # ログ出力
                self.appinfologer(print_url)
                self.appinfologer(print_HttpContext)

            else:
                response_array = {}
                if not isinstance(http_response_header, list):
                    # 返却用のArrayを編集
                    response_array['statusCode'] = -2
                    response_array['responseContents'] = {"errorMessage": "HTTP access error "}

                    # ログ出力
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
                            response_array['responseContents'] = {"errorMessage": responseContents}

                            # ログ出力
                            self.apperrorloger(self.backtrace())
                            self.apperrorloger(print_url)
                            self.apperrorloger(print_HttpContext)
                            self.apperrorloger(print_HttpStatusCode)
                            self.apperrorloger(print_HttpResponsHeader)
                            self.apperrorloger(print_ResponseContents)

                        else:
                            # 正常時
                            response_array['responseHeaders'] = http_response_header
                            response_array['responseContents'] = responseContents
                            for arrHeader in response_array['responseHeaders']:
                                if re.search('^\s*Content-Type$', arrHeader[0]):
                                    if re.search('\s*application\/vnd.api+json', arrHeader[1]):
                                        try:
                                            response_array['responseContents'] = json.loads(responseContents)

                                        except json.JSONDecodeError as e:  # noqa: F841
                                            response_array['responseContents'] = None

                    else:
                        print_HttpResponsHeader = "http response header\n%s" % (http_response_header)

                        # 返却用のArrayを編集
                        response_array['statusCode'] = -2
                        response_array['responseContents'] = {"errorMessage": "HTTP Socket Timeout"}

                        # ログ出力
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

    def get_log_data(self, method, url, direct_flag):  # noqa: C901
        # 変数定義
        httpContext = {}
        httpContext['http'] = {}
        headers = {}
        ssl_context = None
        self.RestResultList = []
        proxy_address = ""

        # コンテンツ付与
        headers['Content-type'] = 'application/vnd.api+json'

        # Header精査
        if self.accessToken:
            headers['Authorization'] = 'Bearer %s' % (self.accessToken)

        # HTTPコンテキスト作成
        httpContext['http']['method'] = method
        httpContext['http']['ignore_errors'] = True

        # Proxy設定
        if 'address' in self.proxySetting and self.proxySetting['address']:
            proxy_address = self.proxySetting['address']
            if 'port' in self.proxySetting and self.proxySetting['port']:
                proxy_address = '%s:%s' % (proxy_address, self.proxySetting['port'])

            httpContext['http']['proxy'] = proxy_address
            httpContext['http']['request_fulluri'] = True

        # URL定義
        if not direct_flag:
            url = '%s%s' % (self.targetHost, url)

        # [暫定対応] SSL認証エラー無視
        ssl_context = ssl._create_unverified_context()
        httpContext['ssl'] = {}
        httpContext['ssl']['verify_peer'] = False
        httpContext['ssl']['verify_peer_name'] = False

        print_HttpContext = 'http context\n%s' % (httpContext)
        print_url = "URL: %s\n" % (url)

        ################################
        # RestCall
        ################################
        responseContents = ''
        req = urllib.request.Request(url, headers=headers, method=method)
        if proxy_address:
            req.set_proxy(proxy_address, 'http')
            req.set_proxy(proxy_address, 'https')
        try:
            with urllib.request.urlopen(req, context=ssl_context, timeout=10) as resp:
                # status_code = resp.getcode()
                # http_response_header = resp.getheaders()
                responseContents = resp.read().decode('utf-8')

        except Exception as e:
            self.apperrorloger(self.backtrace())
            self.apperrorloger(e)
            self.apperrorloger(print_url)
            self.apperrorloger(print_HttpContext)

        return responseContents

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
            g.applogger.error(msg)
        self.RestResultList.append(msg)

    def appinfologer(self, msg, stdout=True):
        if stdout is True:
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
