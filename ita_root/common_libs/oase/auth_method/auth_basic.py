from common_libs.oase.api_client_common import APIClientCommon
import base64

class BasicAuthAPIClient(APIClientCommon):
    def __init__(self, auth_settings=None):
        super().__init__(auth_settings)

    def call_api(self, parameter):
        if self.headers is None:
            self.headers = {}
        base64string = base64.b64encode('{}:{}'.format(self.username, self.password).encode('utf-8'))
        self.headers["Authorization"] = "Basic " + base64string.decode('utf-8')
        return super().call_api(parameter)
