from common_libs.oase.api_client_common import APIClientCommon
import datetime


class SharedKeyLiteAuthAPIClient(APIClientCommon):
    def __init__(self, auth_settings=None):
        super().__init__(auth_settings)

    def call_api(self, parameter):
        self.current_datetime = datetime.datetime.now()
        self.fomatted_datetime = self.current_datetime.strftime("%a, %d %b %Y %H:%M:%S GMT")
        if self.headers is None:
            self.headers = {}
        self.headers["Authorization"] = f"SharedKeyLite {self.access_key_id}:{self.secret_access_key}"
        self.headers["Date"] = self.fomatted_datetime
        return super().call_api(parameter)
