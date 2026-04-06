"""
Data Provider Connector Framework - UPDATED
Connects to external databases (MySQL, MongoDB, Oracle, PostgreSQL, GraphQL APIs)
and fetches credit history using the new external_db_connectors module
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sdk.python.external_db_connectors import ConnectorFactory


class DataProviderRegistry:
    """
    Registry for managing multiple data provider connectors
    
    UPDATED: Now loads real provider configs from data_provider_configs table
    and creates appropriate connectors (MySQL, MongoDB, Oracle, PostgreSQL, GraphQL)
    """
    
    def __init__(self):
        self._providers: Dict[str, Any] = {}
        self.load_providers()
    
    def load_providers(self):
        """
        Load provider configurations from database and instantiate connectors
        """
        try:
            provider_configs = ConnectorFactory.get_provider_configs()
            
            for config in provider_configs:
                try:
                    connector = ConnectorFactory.create_connector(config)
                    self._providers[config["provider_id"]] = connector
                    print(f"✅ Loaded data provider: {config['provider_name']} ({config['connector_type']})")
                except Exception as e:
                    print(f"⚠️  Failed to load provider {config.get('provider_name')}: {e}")
            
            if not self._providers:
                print("ℹ️  No active data providers configured. Use /data-connect UI to add providers.")
        except Exception as e:
            print(f"❌ Error loading data providers: {e}")
    
    def reload_providers(self):
        """Reload provider configurations from database"""
        self._providers.clear()
        self.load_providers()
    
    def get_provider(self, provider_id: str) -> Optional[Any]:
        """Get provider connector by ID"""
        return self._providers.get(provider_id)
    
    def list_providers(self) -> List[str]:
        """List all registered provider IDs"""
        return list(self._providers.keys())
    
    async def test_provider_connection(self, provider_id: str) -> bool:
        """Test connection to a specific provider - raises ConnectorError on failure"""
        from sdk.python.external_db_connectors import ConnectorError
        
        provider = self.get_provider(provider_id)
        if not provider:
            raise ConnectorError(f"Provider {provider_id} not found in registry")
        
        # Let ConnectorError bubble up - do not swallow it
        return await provider.test_connection()
