from pymongo import MongoClient
from pymongo.database import Database


class MongoDB:
    def __init__(
        self,
        uri: str,
        database_name: str,
    ) -> None:
        self._client = MongoClient(uri)
        self._database = self._client[database_name]

    @property
    def database(self) -> Database:
        return self._database

    def ping(self) -> None:
        self._client.admin.command("ping")

    def close(self) -> None:
        self._client.close()