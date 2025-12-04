#   Copyright 2025 NEC Corporation
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

import pytest
from unittest.mock import MagicMock, patch
from ..controllers.oase_controller import add_notification_queue
from common_libs.notification.sub_classes.oase import OASENotificationType

# Import the function to test using relative import


class TestAddNotificationQueue:

    @pytest.fixture
    def setup(self, mocker):
        """Setup common test fixtures"""
        # Mock the OASE class
        self.mock_oase_bulksend = mocker.patch('common_libs.notification.sub_classes.oase.OASE.bulksend')

        # Mock g object and its methods
        self.mock_g = mocker.patch('controllers.oase_controller.g')
        self.mock_g.appmsg.get_log_message.return_value = "Mock log message"

        # Mock stacktrace function
        self.mock_stacktrace = mocker.patch('controllers.oase_controller.stacktrace')

        # Create mock DB connection
        self.mock_wsdb = MagicMock()

        # Create sample notification lists
        self.receive_list = [{"_id": "0000", "labels": {"labelA": "01"}, "event": {"EVENT_RAWDATA": "is_here"}, "exastro_agents": {"test-ag01": "2.7.0"}, "exastro_created_at": "datetime.datetime(2025, 10, 1, 0, 0, 00, 000000)", "exastro_duplicate_check": ["a0f82210-b548-44a3-a9bb-9ac0f3c61232_test-ag01"], "exastro_duplicate_collection_settings_ids": {"a0f82210-b548-44a3-a9bb-9ac0f3c61232": 1}, "exastro_edit_count": 1}, {"_id": "0001", "labels": {"labelA": "02"}, "event": { "EVENT_RAWDATA": "is_here"}, "exastro_agents": {"test-ag01": 1}, "exastro_created_at": "datetime.datetime(2025, 10, 1, 0, 0, 00, 000000)", "exastro_duplicate_check": ["a0f82210-b548-44a3-a9bb-9ac0f3c61232_test-ag01"], "exastro_duplicate_collection_settings_ids": {"a0f82210-b548-44a3-a9bb-9ac0f3c61232": 1}, "exastro_edit_count": 1}]
        self.duplicate_list = [{"_id": "0003", "labels": {"labelB": "01"}, "event": {"EVENT_RAWDATA": "is_here"}, "exastro_agents": {"test-ag01": "2.7.0"}, "exastro_created_at": "datetime.datetime(2025, 10, 1, 0, 0, 00, 000000)", "exastro_duplicate_check": ["a0f82210-b548-44a3-a9bb-9ac0f3c61232_test-ag01"], "exastro_duplicate_collection_settings_ids": {"a0f82210-b548-44a3-a9bb-9ac0f3c61232": 1}, "exastro_edit_count": 1}, {"_id": "0004", "labels": {"labelB": "02"}, "event": { "EVENT_RAWDATA": "is_here"}, "exastro_agents": {"test-ag01": 1}, "exastro_created_at": "datetime.datetime(2025, 10, 1, 0, 0, 00, 000000)", "exastro_duplicate_check": ["a0f82210-b548-44a3-a9bb-9ac0f3c61232_test-ag01"], "exastro_duplicate_collection_settings_ids": {"a0f82210-b548-44a3-a9bb-9ac0f3c61232": 1}, "exastro_edit_count": 1}]

        # Default return values
        self.receive_return = {
            "success": 1,
            "failure": 0,
            "failure_info": [],
            "success_notification_count": 4,
            "failure_notification_count": 0
        }
        self.duplicate_return = {
            "success": 1,
            "failure": 0,
            "failure_info": [],
            "success_notification_count": 4,
            "failure_notification_count": 0
        }

    def test_both_lists_with_data(self, setup):
        """Test when both notification lists have data"""
        # Arrange
        self.mock_oase_bulksend.side_effect = [
            self.receive_return,
            self.duplicate_return
        ]

        # Act
        receive_ret, duplicate_ret = add_notification_queue(
            self.mock_wsdb, self.receive_list, self.duplicate_list
        )

        # Assert
        assert self.mock_oase_bulksend.call_count == 2
        assert receive_ret == self.receive_return
        assert duplicate_ret == self.duplicate_return

        # Verify first call arguments
        args1, _ = self.mock_oase_bulksend.call_args_list[0]
        assert args1[0] == self.mock_wsdb
        assert args1[1] == self.receive_list
        assert args1[2]["notification_type"] == OASENotificationType.RECEIVE

        # Verify second call arguments
        args2, _ = self.mock_oase_bulksend.call_args_list[1]
        assert args2[0] == self.mock_wsdb
        assert args2[1] == self.duplicate_list
        assert args2[2]["notification_type"] == OASENotificationType.DUPLICATE

        # Verify logs were called
        assert self.mock_g.applogger.info.call_count == 2

    def test_only_receive_list(self, setup):
        """Test when only receive list has data"""
        # Arrange
        self.mock_oase_bulksend.return_value = self.receive_return
        empty_duplicate_list = []

        # Act
        receive_ret, duplicate_ret = add_notification_queue(
            self.mock_wsdb, self.receive_list, empty_duplicate_list
        )

        # Assert
        assert self.mock_oase_bulksend.call_count == 1
        assert receive_ret == self.receive_return
        assert duplicate_ret == {}

        # Verify call arguments
        args, _ = self.mock_oase_bulksend.call_args
        assert args[0] == self.mock_wsdb
        assert args[1] == self.receive_list
        assert args[2]["notification_type"] == OASENotificationType.RECEIVE

        # Verify log was called once
        assert self.mock_g.applogger.info.call_count == 1

    def test_only_duplicate_list(self, setup):
        """Test when only duplicate list has data"""
        # Arrange
        self.mock_oase_bulksend.return_value = self.duplicate_return
        empty_receive_list = []

        # Act
        receive_ret, duplicate_ret = add_notification_queue(
            self.mock_wsdb, empty_receive_list, self.duplicate_list
        )

        # Assert
        assert self.mock_oase_bulksend.call_count == 1
        assert receive_ret == {}
        assert duplicate_ret == self.duplicate_return

        # Verify call arguments
        args, _ = self.mock_oase_bulksend.call_args
        assert args[0] == self.mock_wsdb
        assert args[1] == self.duplicate_list
        assert args[2]["notification_type"] == OASENotificationType.DUPLICATE

        # Verify log was called once
        assert self.mock_g.applogger.info.call_count == 1

    def test_empty_lists(self, setup):
        """Test when both lists are empty"""
        # Arrange
        empty_receive_list = []
        empty_duplicate_list = []

        # Act
        receive_ret, duplicate_ret = add_notification_queue(
            self.mock_wsdb, empty_receive_list, empty_duplicate_list
        )

        # Assert
        assert self.mock_oase_bulksend.call_count == 0
        assert receive_ret == {}
        assert duplicate_ret == {}

        # Verify no logs were called
        assert self.mock_g.applogger.info.call_count == 0

    def test_exception_handling(self, setup):
        """Test exception handling in the function"""
        # Arrange
        self.mock_oase_bulksend.side_effect = Exception("Test exception")

        # Act
        receive_ret, duplicate_ret = add_notification_queue(
            self.mock_wsdb, self.receive_list, self.duplicate_list
        )

        # Assert
        assert self.mock_oase_bulksend.call_count == 1
        assert receive_ret == {}
        assert duplicate_ret == {}

        # Verify error logs were called
        assert self.mock_g.applogger.error.call_count == 2
        assert self.mock_stacktrace.called

        # Verify the second error log has the correct arguments
        args, _ = self.mock_g.applogger.error.call_args_list[1]
        assert args[0] == "Mock log message"  # The mocked message