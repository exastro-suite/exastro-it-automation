from common_libs.event_relay.api_client_common import APIClientCommon
from datetime import datetime


class SharedKeyLiteAuthAPIClient(APIClientCommon):
    def __init__(self, auth_settings=None):
        super().__init__(auth_settings)

    def call_api(self, parameter):
        self.current_datetime = datetime.utcnow()
        self.fomatted_datetime = self.current_datetime.strftime("%a, %d %b %Y %H:%M:%S GMT")
        self.headers["Authorization"] = f"SharedKeyLite {self.username}:{self.password}"
        self.headers["Date"] = self.fomatted_datetime
        return super().call_api(parameter)
