from common_libs.oase.api_client_common import APIClientCommon


class OptionalAuthAPIClient(APIClientCommon):
    def __init__(self, auth_settings=None):
        super().__init__(auth_settings)

    def call_api(self, parameter):
        return super().call_api(parameter)
