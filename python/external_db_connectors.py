"""
External Database Connectors for Credit History Data Ingestion

Supports MySQL, MongoDB, Oracle, PostgreSQL, and external GraphQL APIs.
Connectors read from external databases configured via Data Connect UI.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import pymongo
import mysql.connector
import oracledb
import asyncpg
import httpx
from oauth_auth import get_db_connection


class ConnectorError(Exception):
    """Base exception for all connector failures (connection, auth, query, network)"""

    pass


class ExternalDatabaseConnector(ABC):
    """Base class for external database connectors"""

    def __init__(self, provider_config: Dict[str, Any]):
        self.provider_id = provider_config.get("provider_id")
        self.provider_name = provider_config.get("provider_name")
        self.api_url = provider_config.get("api_url")
        self.connector_type = provider_config.get("connector_type")
        self.metadata = provider_config.get("metadata", {})

        if isinstance(self.metadata, str):
            self.metadata = json.loads(self.metadata)

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if connection to external database is successful"""
        pass

    @abstractmethod
    async def fetch_credit_history(
        self,
        company_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Fetch credit history records from external database

        Returns list of records in standardized format:
        [{
            "company_id": str,
            "email": str,
            "date": datetime,
            "reference": str,
            "inflow": float,
            "outflow": float,
            "balance": float,
            "account_name": str,
            "account_number": str,
            "bank": str,
            "currency": str
        }]
        """
        pass

    def close(self):
        """Close database connection"""
        pass


class MySQLConnector(ExternalDatabaseConnector):
    """MySQL database connector"""

    def __init__(self, provider_config: Dict[str, Any]):
        super().__init__(provider_config)
        self.connection = None

    def _parse_connection_string(self) -> Dict[str, Any]:
        """Parse MySQL connection string"""
        if self.api_url.startswith("mysql://"):
            url = self.api_url.replace("mysql://", "")
            if "@" in url:
                auth, host_part = url.split("@", 1)
                user, password = auth.split(":", 1) if ":" in auth else (auth, "")
                host_port, *db_parts = host_part.split("/", 1)
                host, port = (
                    host_port.split(":", 1) if ":" in host_port else (host_port, "3306")
                )
                database = db_parts[0] if db_parts else ""

                return {
                    "host": host,
                    "port": int(port),
                    "user": user,
                    "password": password,
                    "database": database,
                }

        return {
            "host": self.metadata.get("hostname", "localhost"),
            "port": self.metadata.get("port", 3306),
            "user": self.metadata.get("username", "root"),
            "password": self.metadata.get("password", ""),
            "database": self.metadata.get("database", "credit_history"),
        }

    async def test_connection(self) -> bool:
        """Test MySQL connection - raises ConnectorError on failure"""
        try:
            config = self._parse_connection_string()
            conn = mysql.connector.connect(**config)
            conn.close()
            return True
        except Exception as e:
            raise ConnectorError(f"MySQL connection test failed: {str(e)}") from e

    async def fetch_credit_history(
        self,
        company_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Fetch credit history from MySQL database - raises ConnectorError on failure"""
        conn = None
        cursor = None

        try:
            config = self._parse_connection_string()
            conn = mysql.connector.connect(**config)
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT 
                    company_id,
                    email,
                    transaction_date as date,
                    reference,
                    inflow,
                    outflow,
                    balance,
                    account_name,
                    account_number,
                    bank,
                    currency
                FROM credit_transactions
                WHERE company_id = %s
            """

            params = [company_id]

            if start_date:
                query += " AND transaction_date >= %s"
                params.append(start_date)

            if end_date:
                query += " AND transaction_date <= %s"
                params.append(end_date)

            query += " ORDER BY transaction_date DESC LIMIT %s"
            params.append(limit)

            cursor.execute(query, params)
            results = cursor.fetchall()

            return results

        except Exception as e:
            raise ConnectorError(f"MySQL fetch failed: {str(e)}") from e

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def close(self):
        if self.connection:
            self.connection.close()


class MongoDBConnector(ExternalDatabaseConnector):
    """MongoDB database connector"""

    def __init__(self, provider_config: Dict[str, Any]):
        super().__init__(provider_config)
        self.client = None

    async def test_connection(self) -> bool:
        """Test MongoDB connection - raises ConnectorError on failure"""
        try:
            client = pymongo.MongoClient(self.api_url, serverSelectionTimeoutMS=5000)
            client.server_info()
            client.close()
            return True
        except Exception as e:
            raise ConnectorError(f"MongoDB connection test failed: {str(e)}") from e

    async def fetch_credit_history(
        self,
        company_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Fetch credit history from MongoDB - raises ConnectorError on failure"""
        client = None

        try:
            client = pymongo.MongoClient(self.api_url)
            db = client[self.metadata.get("database", "credit_history")]
            collection = db[self.metadata.get("collection", "transactions")]

            query = {"company_id": company_id}

            if start_date or end_date:
                query["date"] = {}
                if start_date:
                    query["date"]["$gte"] = start_date
                if end_date:
                    query["date"]["$lte"] = end_date

            cursor = collection.find(query).sort("date", -1).limit(limit)
            results = list(cursor)

            for record in results:
                if "_id" in record:
                    del record["_id"]

            return results

        except Exception as e:
            raise ConnectorError(f"MongoDB fetch failed: {str(e)}") from e

        finally:
            if client:
                client.close()

    def close(self):
        if self.client:
            self.client.close()


class OracleConnector(ExternalDatabaseConnector):
    """Oracle database connector"""

    def __init__(self, provider_config: Dict[str, Any]):
        super().__init__(provider_config)
        self.connection = None

    def _parse_connection_string(self) -> tuple:
        """Parse Oracle connection string"""
        if self.api_url.startswith("oracle://"):
            url = self.api_url.replace("oracle://", "")
            if "@" in url:
                auth, dsn = url.split("@", 1)
                user, password = auth.split(":", 1) if ":" in auth else (auth, "")
                return user, password, dsn

        user = self.metadata.get("username", "system")
        password = self.metadata.get("password", "")
        host = self.metadata.get("hostname", "localhost")
        port = self.metadata.get("port", 1521)
        service = self.metadata.get("service_name", "XEPDB1")
        dsn = f"{host}:{port}/{service}"

        return user, password, dsn

    async def test_connection(self) -> bool:
        """Test Oracle connection - raises ConnectorError on failure"""
        try:
            user, password, dsn = self._parse_connection_string()
            conn = oracledb.connect(user, password, dsn)
            conn.close()
            return True
        except Exception as e:
            raise ConnectorError(f"Oracle connection test failed: {str(e)}") from e

    async def fetch_credit_history(
        self,
        company_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Fetch credit history from Oracle database"""
        try:
            user, password, dsn = self._parse_connection_string()
            conn = oracledb.connect(user, password, dsn)
            cursor = conn.cursor()

            query = """
                SELECT 
                    company_id,
                    email,
                    transaction_date as date,
                    reference,
                    inflow,
                    outflow,
                    balance,
                    account_name,
                    account_number,
                    bank,
                    currency
                FROM credit_transactions
                WHERE company_id = :company_id
            """

            params = {"company_id": company_id}

            if start_date:
                query += " AND transaction_date >= :start_date"
                params["start_date"] = start_date

            if end_date:
                query += " AND transaction_date <= :end_date"
                params["end_date"] = end_date

            query += " ORDER BY transaction_date DESC FETCH FIRST :limit ROWS ONLY"
            params["limit"] = limit

            cursor.execute(query, params)

            columns = [col[0].lower() for col in cursor.description]
            results = []
            for row in cursor:
                results.append(dict(zip(columns, row)))

            return results

        except Exception as e:
            raise ConnectorError(f"Oracle fetch failed: {str(e)}") from e

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def close(self):
        if self.connection:
            self.connection.close()


class PostgreSQLConnector(ExternalDatabaseConnector):
    """PostgreSQL database connector for external databases"""

    def __init__(self, provider_config: Dict[str, Any]):
        super().__init__(provider_config)
        self.connection = None

    async def test_connection(self) -> bool:
        """Test PostgreSQL connection - raises ConnectorError on failure"""
        try:
            conn = await asyncpg.connect(self.api_url)
            await conn.close()
            return True
        except Exception as e:
            raise ConnectorError(f"PostgreSQL connection test failed: {str(e)}") from e

    async def fetch_credit_history(
        self,
        company_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Fetch credit history from external PostgreSQL database"""
        try:
            conn = await asyncpg.connect(self.api_url)

            query = """
                SELECT 
                    company_id,
                    email,
                    transaction_date as date,
                    reference,
                    inflow,
                    outflow,
                    balance,
                    account_name,
                    account_number,
                    bank,
                    currency
                FROM credit_transactions
                WHERE company_id = $1
            """

            conditions = []
            params = [company_id]
            param_count = 1

            if start_date:
                param_count += 1
                conditions.append(f"AND transaction_date >= ${param_count}")
                params.append(start_date)

            if end_date:
                param_count += 1
                conditions.append(f"AND transaction_date <= ${param_count}")
                params.append(end_date)

            query += " " + " ".join(conditions)
            param_count += 1
            query += f" ORDER BY transaction_date DESC LIMIT ${param_count}"
            params.append(limit)

            rows = await conn.fetch(query, *params)
            results = [dict(row) for row in rows]

            return results

        except Exception as e:
            raise ConnectorError(f"PostgreSQL fetch failed: {str(e)}") from e

        finally:
            if conn:
                await conn.close()

    async def close(self):
        if self.connection:
            await self.connection.close()


class GraphQLAPIConnector(ExternalDatabaseConnector):
    """External GraphQL API connector"""

    async def test_connection(self) -> bool:
        """Test GraphQL API connection - raises ConnectorError on failure"""
        try:
            async with httpx.AsyncClient() as client:
                introspection_query = """
                    query {
                        __schema {
                            queryType {
                                name
                            }
                        }
                    }
                """

                headers = self._get_headers()
                response = await client.post(
                    self.api_url,
                    json={"query": introspection_query},
                    headers=headers,
                    timeout=10.0,
                )

                if response.status_code == 200:
                    return True
                else:
                    raise ConnectorError(
                        f"GraphQL API returned status {response.status_code}"
                    )
        except ConnectorError:
            raise
        except Exception as e:
            raise ConnectorError(f"GraphQL API connection test failed: {str(e)}") from e

    def _get_headers(self) -> Dict[str, str]:
        """Get API headers including auth"""
        headers = {"Content-Type": "application/json"}

        if "api_key" in self.metadata:
            headers["Authorization"] = f"Bearer {self.metadata['api_key']}"

        return headers

    async def fetch_credit_history(
        self,
        company_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Fetch credit history from external GraphQL API"""
        try:
            async with httpx.AsyncClient() as client:
                query = """
                    query GetCreditHistory($companyId: String!, $startDate: DateTime, $endDate: DateTime, $limit: Int) {
                        creditHistory(
                            companyId: $companyId
                            startDate: $startDate
                            endDate: $endDate
                            limit: $limit
                        ) {
                            company_id
                            email
                            date
                            reference
                            inflow
                            outflow
                            balance
                            account_name
                            account_number
                            bank
                            currency
                        }
                    }
                """

                variables = {"companyId": company_id, "limit": limit}

                if start_date:
                    variables["startDate"] = start_date.isoformat()
                if end_date:
                    variables["endDate"] = end_date.isoformat()

                headers = self._get_headers()
                response = await client.post(
                    self.api_url,
                    json={"query": query, "variables": variables},
                    headers=headers,
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("data", {}).get("creditHistory", [])
                else:
                    error_msg = f"GraphQL API returned error: {response.status_code} - {response.text}"
                    raise ConnectorError(error_msg)

        except ConnectorError:
            # Already wrapped, re-raise as-is
            raise
        except Exception as e:
            # Wrap network/timeout/other errors
            raise ConnectorError(f"GraphQL API fetch failed: {str(e)}") from e


class ConnectorFactory:
    """Factory for creating database connectors"""

    CONNECTOR_MAP = {
        "mysql": MySQLConnector,
        "mongodb": MongoDBConnector,
        "oracle": OracleConnector,
        "postgresql": PostgreSQLConnector,
        "graphql": GraphQLAPIConnector,
    }

    @classmethod
    def create_connector(
        cls, provider_config: Dict[str, Any]
    ) -> ExternalDatabaseConnector:
        """Create appropriate connector based on provider type"""
        connector_type = provider_config.get("connector_type", "").lower()

        connector_class = cls.CONNECTOR_MAP.get(connector_type)
        if not connector_class:
            raise ValueError(f"Unsupported connector type: {connector_type}")

        return connector_class(provider_config)

    @classmethod
    def get_provider_configs(cls) -> List[Dict[str, Any]]:
        """Load all provider configurations from database"""
        try:
            db = get_db_connection()
            cursor = db.cursor()

            cursor.execute("""
                SELECT 
                    provider_id,
                    provider_name,
                    api_url,
                    connector_type,
                    is_active,
                    metadata
                FROM data_provider_configs
                WHERE is_active = TRUE
            """)

            columns = [
                "provider_id",
                "provider_name",
                "api_url",
                "connector_type",
                "is_active",
                "metadata",
            ]
            configs = []

            for row in cursor.fetchall():
                config = dict(zip(columns, row))
                configs.append(config)

            cursor.close()
            db.close()

            return configs
        except Exception as e:
            print(f"Error loading provider configs: {e}")
            return []
