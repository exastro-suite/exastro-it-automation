from common_libs.oase.api_client_common import APIClientCommon


class BearerAuthAPIClient(APIClientCommon):
    def __init__(self, setting, last_fetched_event):
        super().__init__(setting, last_fetched_event)

    def call_api(self, setting, last_fetched_event):
        if self.headers is None:
            self.headers = {}
        self.headers["Authorization"] = f"Bearer {self.auth_token}"
        return super().call_api(setting, last_fetched_event)
