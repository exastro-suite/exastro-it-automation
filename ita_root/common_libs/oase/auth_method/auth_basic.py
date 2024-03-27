from common_libs.oase.api_client_common import APIClientCommon


class BasicAuthAPIClient(APIClientCommon):
    def __init__(self, auth_settings=None):
        super().__init__(auth_settings)

    def call_api(self, parameter):
        if self.headers is None:
            self.headers = {}
        self.headers["Authorization"] = f"Basic {self.username}:{self.password}"
        return super().call_api(parameter)
