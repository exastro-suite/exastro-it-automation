from common_libs.event_relay.api_client_common import APIClientCommon
from datetime import datetime


class SharedKeyLiteAuthAPIClient(APIClientCommon):
    def __init__(self, auth_settings=None, last_fetched_timestamp=None):
        super().__init__(auth_settings, last_fetched_timestamp)

    def call_api(self, parameter):
        self.current_datetime = datetime.utcnow()
        self.fomatted_datetime = self.current_datetime.strftime("%a, %d %b %Y %H:%M:%S GMT")
        self.headers["Authorization"] = f"SharedKeyLite {self.access_key_id}:{self.secret_access_key}"
        self.headers["Date"] = self.fomatted_datetime
        return super().call_api(parameter)
