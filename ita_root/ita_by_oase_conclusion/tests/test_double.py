import copy
import operator
import uuid

from bson import ObjectId
from common_libs.oase.const import oaseConst
from tests.common import V_OASE_LABEL_KEY_GROUP, deep_merged


class DummyDB:
    """データベース接続(DBConnectWs)のダミークラス"""

    def __init__(self, workspace_id):
        self.workspace_id = workspace_id
        self.ended = False
        self.disconnected = False
        self.args_end = None

        # テーブル別のカスタムデータ（テストでオーバーライド可能）
        self.table_data: dict[str, list[dict]] = {
            oaseConst.V_OASE_LABEL_KEY_GROUP: [
                {
                    "LABEL_KEY_ID": label_key_id,
                    "LABEL_KEY_NAME": label_key_name,
                    "DISUSE_FLAG": 0,
                }
                for label_key_name, label_key_id in V_OASE_LABEL_KEY_GROUP.items()
            ],
            oaseConst.T_OASE_DEDUPLICATION_SETTINGS: [],
            oaseConst.T_OASE_ACTION_LOG: [],
        }

    def db_transaction_end(self, flag):
        """トランザクション終了"""
        self.ended = True
        self.args_end = flag

    def db_disconnect(self):
        """データベース切断"""
        self.disconnected = True

    def table_select(
        self, table: str, where="", params: list | None = None
    ) -> list[dict]:
        """テーブル選択"""
        params = params or []
        match table:
            case oaseConst.T_OASE_ACTION:
                return [
                    row
                    for row in self.table_data[table]
                    if row.get("DISUSE_FLAG", 0) == 0
                    and ("ACTION_IN" not in where or row["ACTION_ID"] == params[1])
                ]
            case _:
                return self.table_data[table]

    def table_update(
        self,
        table_name,
        data,
        primary_key_name,
        is_register_history=False,
        last_timestamp=True,
    ):
        """テーブル更新"""
        for idx, row in enumerate(self.table_data.get(table_name, [])):
            if row.get(primary_key_name) == data.get(primary_key_name):
                self.table_data[table_name][idx].update(data)
        return True

    def sql_execute(self, sql, params=None):
        """SQL実行"""
        params = params or []
        return [
            {
                "JOIN_CONDUCTOR_INSTANCE_ID": "mock_instance_id",
                "CONDUCTOR_STATUS_ID": "mock_status_id",
                "TAB_B_DISUSE_FLAG": 0,
                "JOIN_RULE_ID": rule.get("RULE_ID"),
                "RULE_NAME": rule.get("RULE_NAME"),
                "RULE_PRIORITY": rule.get("RULE_PRIORITY"),
                "FILTER_A": rule.get("FILTER_A"),
                "FILTER_OPERATOR": rule.get("FILTER_OPERATOR"),
                "FILTER_B": rule.get("FILTER_B"),
                "BEFORE_NOTIFICATION": rule.get("BEFORE_NOTIFICATION"),
                "BEFORE_APPROVAL_PENDING": rule.get("BEFORE_APPROVAL_PENDING"),
                "BEFORE_NOTIFICATION_DESTINATION": rule.get(
                    "BEFORE_NOTIFICATION_DESTINATION"
                ),
                "ACTION_ID": rule.get("ACTION_ID"),
                "ACTION_LABEL_INHERITANCE_FLAG": rule.get(
                    "ACTION_LABEL_INHERITANCE_FLAG"
                ),
                "EVENT_LABEL_INHERITANCE_FLAG": rule.get(
                    "EVENT_LABEL_INHERITANCE_FLAG"
                ),
                "CONCLUSION_LABEL_SETTINGS": rule.get("CONCLUSION_LABEL_SETTINGS"),
                "RULE_LABEL_NAME": rule.get("RULE_LABEL_NAME"),
                "EVENT_ID_LIST": rule.get("EVENT_ID_LIST"),
                "TTL": rule.get("TTL"),
                "AFTER_APPROVAL_PENDING": rule.get("AFTER_APPROVAL_PENDING"),
                "AFTER_NOTIFICATION": rule.get("AFTER_NOTIFICATION"),
                "AFTER_NOTIFICATION_DESTINATION": rule.get(
                    "AFTER_NOTIFICATION_DESTINATION"
                ),
                "RULE_AVAILABLE_FLAG": rule.get("AVAILABLE_FLAG"),
                "TAB_C_DISUSE_FLAG": rule.get("DISUSE_FLAG"),
                **row,
            }
            for row in self.table_data.get(oaseConst.T_OASE_ACTION_LOG, [])
            for rule in self.table_data.get(oaseConst.T_OASE_RULE, [])
            if rule["RULE_ID"] == row["RULE_ID"]
        ]

    def db_commit(self):
        """コミット"""
        pass


class MockMONGOConnectWs:
    """MONGOConnectWsのモッククラス"""

    def __init__(self, test_events: list[dict] | None = None):
        """
        コンストラクタ
        Args:
            test_events: テスト用イベントデータ
        """
        self.test_events = test_events or []
        self.update_calls = []
        self.insert_calls = []
        self.disconnected = False

    def disconnect(self):
        """接続切断"""
        self.disconnected = True

    def collection(self, collection_name):
        """コレクション取得"""
        return MockCollection(collection_name, self)


class MockCollection:
    """MongoDBコレクションのモッククラス"""

    def __init__(self, collection_name, mongo_instance: MockMONGOConnectWs):
        self.collection_name = collection_name
        self.mongo_instance = mongo_instance

    def find(self, query=None, projection=None):
        """find操作のモック"""
        return MockCursor(self.mongo_instance.test_events, query)

    def update_one(self, query, update_data):
        """update_one操作のモック"""
        self.mongo_instance.update_calls.append((query, update_data))
        return True

    def insert_one(self, document):
        """insert_one操作のモック"""
        self.mongo_instance.insert_calls.append(document)
        return True


class MockCursor:
    """MongoDBカーソルのモッククラス"""

    __mongo_compare_operator_map = {
        "$eq": operator.eq,
        "$ne": operator.ne,
        "$gt": operator.gt,
        "$lt": operator.lt,
        "$gte": operator.ge,
        "$lte": operator.le,
    }

    __mongo_calculation_map = {
        "$add": (operator.add, 0),
        "$multiply": (operator.mul, 1),
        "$subtract": (operator.sub, None),
        "$divide": (operator.truediv, None),
    }

    def __init__(self, test_events: list[dict] | dict, query=None):
        self.test_events = test_events
        self.query = query or {}
        if isinstance(test_events, dict):
            self._events = list(test_events.values())
        elif isinstance(test_events, list):
            self._events = test_events
        else:
            self._events = []

    def sort(self, field, direction):
        """ソート処理のモック"""
        # 簡単なソート実装（実際のテストではより詳細な実装が必要な場合もある）
        if field == "labels._exastro_fetched_time":
            self._events.sort(
                key=lambda x: int(x.get("labels", {}).get("_exastro_fetched_time", 0))
            )
        return self

    def __iter__(self):
        """イテレータ"""
        return iter(self._filter_events())

    def _filter_events(self):
        """クエリに基づいてイベントをフィルタリング"""
        filtered_events = []
        for event in self._events:
            if self._matches_query(event, self.query):
                filtered_events.append(event)
        return filtered_events

    @classmethod
    def _matches_query(cls, event, query):
        """イベントがクエリにマッチするかチェック"""
        if not query:
            return True

        for joined_key, expression in query.items():
            if joined_key.startswith("$"):
                return cls._match_query_body(event, event, query)
            remain_keys = joined_key.split(".")
            target = event
            # キーがネストされている場合に対応
            while remain_keys:
                key, *remain_keys = remain_keys
                if not isinstance(target, dict) or key not in target:
                    return False
                target = target[key]
                if not remain_keys and not cls._match_query_body(
                    event, target, expression
                ):
                    return False

        return True

    @classmethod
    def _match_query_body(cls, event, target, expression):
        """クエリ本体にマッチするかチェック"""
        match expression:
            case {"$in": [*values]}:
                return target in values
            case {"$gte": value}:
                return target >= value
            case {"$and": [*queries]}:
                return all(cls._matches_query(target, query) for query in queries)
            case {"$expr": expression}:
                return cls._match_expression(event, expression)
            case value:
                return target == value
        return False

    @classmethod
    def _match_expression(cls, event, expression_or_value):
        """式にマッチするかチェック"""

        def match_expression_nested(expression_or_value):
            return cls._match_expression(event, expression_or_value)

        match expression_or_value:
            case {"$gt": [expr1, expr2]}:
                return cls.__compare("$gt", expr1, expr2)
            case {"$gte": [expr1, expr2]}:
                return cls.__compare("$gte", expr1, expr2)
            case {"$lt": [expr1, expr2]}:
                return cls.__compare("$lt", expr1, expr2)
            case {"$lte": [expr1, expr2]}:
                return cls.__compare("$lte", expr1, expr2)
            case {"$add": [*expressions]}:
                return cls.__calculation(
                    "$add", *expressions, match_expression=match_expression_nested
                )
            case {"$multiply": [*expressions]}:
                return cls.__calculation(
                    "$multiply",
                    *expressions,
                    match_expression=match_expression_nested,
                )
            case {"$divide": [expr1, expr2]}:
                return cls.__calculation(
                    "$divide", expr1, expr2, match_expression=match_expression_nested
                )
            case {"$subtract": [expr1, expr2]}:
                return cls.__calculation(
                    "$subtract",
                    expr1,
                    expr2,
                    match_expression=match_expression_nested,
                )
            case {"$ifNull": [expr1, expr2]}:
                v1 = match_expression_nested(expr1)
                return v1 if v1 is not None else match_expression_nested(expr2)
            case str() as field_name if field_name.startswith("$"):
                return cls.__resolve_fieldpath(event, field_name)
            case value:
                return value

    @staticmethod
    def __resolve_fieldpath(event: dict, field_path: str):
        """フィールドパスから値を取得"""
        remain_keys = field_path.strip("$").split(".")
        target = event
        while remain_keys:
            key, *remain_keys = remain_keys
            if not isinstance(target, dict) or key not in target:
                return None
            target = target[key]
            if not remain_keys:
                return target
        return target

    @classmethod
    def __compare(cls, operator_name, value1, value2):
        """MongoDBのBSON比較条件に基づく比較"""
        return cls.__mongo_compare_operator_map[operator_name](
            cls.__get_comparable(value1), cls.__get_comparable(value2)
        )

    @classmethod
    def __get_comparable(cls, value):
        """MongoDBのBSON比較条件に基づく比較可能な値を取得"""
        return cls.__get_type_order(value), value

    @classmethod
    def __get_type_order(cls, value):
        """MongoDBのBSONタイプ順序に基づく型の順序を取得"""
        match value:
            case None:
                return 2
            case int() | float():
                return 3
            case str():
                return 4
            case dict():
                return 5
            case list():
                return 6
            case bool():
                return 9
            case _:
                return 100

    @classmethod
    def __calculation(cls, operator_name, *exprs, match_expression):
        """MongoDBの算術演算に基づく計算"""
        operator, result = cls.__mongo_calculation_map[operator_name]
        for expr in exprs:
            value = match_expression(expr)
            if value is None:
                return None
            result = operator(result, value) if result is not None else value
        return result


class DummyAppMsg:
    def get_log_message(self, code, params):
        # ログ本文はテストで詳細検証しないので簡略
        return f"{code}:{params}"


class DummyLogger:
    def __init__(self):
        self.logs = []

    def debug(self, msg):
        self.logs.append(("debug", msg))

    def info(self, msg):
        self.logs.append(("info", msg))

    def warning(self, msg):
        self.logs.append(("warning", msg))


class DummyAction:
    """Actionクラスのダミー実装"""

    def __init__(self, ws_db=None, event_obj=None):
        """コンストラクタ"""
        self.ws_db = ws_db
        self.event_obj = event_obj


class DummyActionStatusMonitor:
    """ActionStatusMonitorクラスのダミー実装"""

    def __init__(self, ws_db=None, event_obj=None):
        """コンストラクタ"""
        self.called = []
        self.ws_db = ws_db
        self.event_obj = event_obj
        self.match_called = False
        self.exec_called = False

    def check_rule_match(self, action_obj):
        """ルールマッチチェック"""
        self.called.append("match")
        self.match_called = True
        return None

    def check_executing(self):
        """実行中チェック"""
        self.called.append("exec")
        self.exec_called = True
        return None

    def __getattr__(self, name):
        """属性アクセス対応"""
        if name == "checkRuleMatch":
            return self.check_rule_match
        if name == "checkExecuting":
            return self.check_executing
        raise AttributeError(name)


class DummyConductorExecuteBkyLibs:
    """ConductorExecuteBkyLibsクラスのダミー実装"""

    def __init__(self, ws_db=None):
        """コンストラクタ"""
        self.objdbca = ws_db

    def set_objmenus(self):
        return None

    def conductor_execute_no_transaction(self, parameter):
        return True, {
            "conductor_instance_id": "mock_instance_id",
        }


class DummyNotificationPM:
    def __init__(self, calls):
        self.calls = calls

    def start_workspace_processing(self, org, ws):
        self.calls["notification_start_ws"] += 1

    def finish_workspace_processing(self):
        self.calls["notification_finish_ws"] += 1

    def start_process(self):
        return None

    def stop_process(self):
        return None

    def send_notification(self, event_list, info):
        self.calls["notifications"].append((list(event_list), dict(info)))


class DummyWriterPM:
    def __init__(self, calls, ws_db: DummyDB | None = None, mongo: MockMONGOConnectWs | None = None):
        self.calls = calls
        self.ws_db = ws_db
        self.mongo = mongo

    def start_workspace_processing(self, org, ws):
        self.calls["writer_start_ws"] += 1

    def finish_workspace_processing(self):
        self.calls["writer_finish_ws"] += 1

    def insert_labeled_event_collection(self, event):
        if "_id" not in event:
            event["_id"] = ObjectId()
        self.calls["insert_events"].append(copy.deepcopy(event))
        self.mongo.test_events.append(event)
        return event["_id"]  # 戻り値はイベントID

    def update_labeled_event_collection(self, filter, update):
        update_events = self.calls["update_events"]
        key = frozenset(filter.items())
        events = update_events.get(key, {})
        update_events[key] = deep_merged(events, update)
        
        matched_events = (
            event
            for event in self.mongo.test_events
            if all(
                event.get(k) == v
                for k, v in filter.items()
            )
        )
        
        update_values_map = update.get("$set", {})
        
        for event in matched_events:
            for joined_key, expression in update_values_map.items():
                remain_keys = joined_key.split(".")
                target = event
                # キーがネストされている場合に対応
                while remain_keys:
                    key, *remain_keys = remain_keys
                    if not remain_keys:
                        target[key] = expression
                    else:
                        target = target.setdefault(key, {})

    def insert_oase_action_log(self, data):
        data["ACTION_LOG_ID"] = str(uuid.uuid4())
        if self.ws_db:
            self.ws_db.table_data["T_OASE_ACTION_LOG"].append(data)
        self.calls["insert_action_log"].append(data)
        return [data]  # 戻り値はリストでラップ

    def update_oase_action_log(self, data):
        self.calls["update_action_log"].append(data)

    def flush_buffer(self):
        return None

    @classmethod
    def start_process(cls):
        return None

    @classmethod
    def stop_process(cls):
        return None
