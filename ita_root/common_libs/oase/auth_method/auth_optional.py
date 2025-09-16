from common_libs.oase.api_client_common import APIClientCommon


class OptionalAuthAPIClient(APIClientCommon):
    def __init__(self, setting, last_fetched_event):
        super().__init__(setting, last_fetched_event)

    def call_api(self, setting, last_fetched_event):
        return super().call_api(setting, last_fetched_event)
