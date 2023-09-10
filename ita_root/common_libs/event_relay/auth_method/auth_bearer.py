from common_libs.event_relay.api_client_common import APIClientCommon


class BearerAuthAPIClient(APIClientCommon):
    def __init__(self, auth_settings=None, last_fetched_timestamp=None):
        super().__init__(auth_settings, last_fetched_timestamp)

    def call_api(self, parameter):

        self.headers["Authorization"] = f"Bearer {self.auth_token}"
        return super().call_api(parameter)
