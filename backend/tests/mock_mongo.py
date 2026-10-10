import copy
from datetime import datetime
from typing import Any, Dict, List, Optional
from bson import ObjectId


class MockCursor:
    """Mock async cursor supporting sort, skip, limit, and to_list."""

    def __init__(self, docs: List[Dict[str, Any]]) -> None:
        self._docs = docs
        self._sort_key = None
        self._sort_dir = 1
        self._skip = 0
        self._limit = None

    def sort(self, key_or_list: Any, direction: int = 1) -> "MockCursor":
        if isinstance(key_or_list, list):
            self._sort_key = key_or_list[0][0]
            self._sort_dir = key_or_list[0][1]
        else:
            self._sort_key = key_or_list
            self._sort_dir = direction
        return self

    def skip(self, n: int) -> "MockCursor":
        self._skip = n
        return self

    def limit(self, n: int) -> "MockCursor":
        self._limit = n
        return self

    async def to_list(self, length: Optional[int] = None) -> List[Dict[str, Any]]:
        result = list(self._docs)
        if self._sort_key:
            reverse = self._sort_dir == -1
            result.sort(
                key=lambda d: d.get(self._sort_key, datetime.min if reverse else datetime.max),
                reverse=reverse,
            )

        if self._skip:
            result = result[self._skip :]

        limit = length if length is not None else self._limit
        if limit is not None:
            result = result[:limit]

        return [copy.deepcopy(doc) for doc in result]


class MockInsertResult:
    def __init__(self, inserted_id: ObjectId):
        self.inserted_id = inserted_id


class MockDeleteResult:
    def __init__(self, deleted_count: int):
        self.deleted_count = deleted_count


class MockCollection:
    """In-memory MongoDB collection for testing."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.docs: Dict[str, Dict[str, Any]] = {}

    def _matches(self, doc: Dict[str, Any], query: Dict[str, Any]) -> bool:
        for k, v in query.items():
            if k == "_id":
                if str(doc.get("_id")) != str(v):
                    return False
            elif doc.get(k) != v:
                return False
        return True

    async def insert_one(self, document: Dict[str, Any]) -> MockInsertResult:
        doc = copy.deepcopy(document)
        if "_id" not in doc:
            doc["_id"] = ObjectId()
        oid_str = str(doc["_id"])
        self.docs[oid_str] = doc
        return MockInsertResult(doc["_id"])

    async def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for doc in self.docs.values():
            if self._matches(doc, query):
                return copy.deepcopy(doc)
        return None

    def find(self, query: Dict[str, Any]) -> MockCursor:
        matched = [doc for doc in self.docs.values() if self._matches(doc, query)]
        return MockCursor(matched)

    async def count_documents(self, query: Dict[str, Any]) -> int:
        return sum(1 for doc in self.docs.values() if self._matches(doc, query))

    async def update_one(self, query: Dict[str, Any], update: Dict[str, Any]) -> None:
        target = None
        for doc in self.docs.values():
            if self._matches(doc, query):
                target = doc
                break

        if target:
            if "$set" in update:
                for k, v in update["$set"].items():
                    target[k] = copy.deepcopy(v)
            if "$inc" in update:
                for k, v in update["$inc"].items():
                    target[k] = target.get(k, 0) + v

    async def find_one_and_update(
        self,
        query: Dict[str, Any],
        update: Dict[str, Any],
        return_document: bool = True,
    ) -> Optional[Dict[str, Any]]:
        await self.update_one(query, update)
        return await self.find_one(query)

    async def delete_one(self, query: Dict[str, Any]) -> MockDeleteResult:
        for oid, doc in list(self.docs.items()):
            if self._matches(doc, query):
                del self.docs[oid]
                return MockDeleteResult(1)
        return MockDeleteResult(0)

    async def delete_many(self, query: Dict[str, Any]) -> MockDeleteResult:
        count = 0
        for oid, doc in list(self.docs.items()):
            if self._matches(doc, query):
                del self.docs[oid]
                count += 1
        return MockDeleteResult(count)

    async def create_index(self, *args, **kwargs) -> str:
        return "mock_index"


class MockMongoDBManager:
    """Mock MongoDB Manager for automated unit/integration tests."""

    def __init__(self) -> None:
        self.collections: Dict[str, MockCollection] = {
            "users": MockCollection("users"),
            "conversations": MockCollection("conversations"),
            "messages": MockCollection("messages"),
        }
        self.db = self

    def __getitem__(self, name: str) -> MockCollection:
        if name not in self.collections:
            self.collections[name] = MockCollection(name)
        return self.collections[name]

    @property
    def users(self) -> MockCollection:
        return self["users"]

    @property
    def conversations(self) -> MockCollection:
        return self["conversations"]

    @property
    def messages(self) -> MockCollection:
        return self["messages"]

    async def ping(self) -> bool:
        return True

    async def connect(self, uri: str, db_name: str) -> None:
        pass

    async def close(self) -> None:
        pass

    def clear(self) -> None:
        for col in self.collections.values():
            col.docs.clear()
