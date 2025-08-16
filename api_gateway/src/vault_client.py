
import hvac
import os
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class VaultClient:
    def __init__(self, vault_url: str = None, vault_token: str = None):
        self.vault_url = vault_url or os.getenv("VAULT_URL", "http://localhost:8200")
        self.vault_token = vault_token or os.getenv("VAULT_TOKEN", "root")
        self.client = hvac.Client(url=self.vault_url, token=self.vault_token)
        
    def get_secret(self, path: str, key: str = None) -> Optional[Any]:
        """Get secret from Vault"""
        try:
            response = self.client.secrets.kv.v2.read_secret_version(path=path)
            data = response['data']['data']
            
            if key:
                return data.get(key)
            return data
        except Exception as e:
            logger.error(f"Failed to get secret from Vault: {e}")
            return None
    
    def set_secret(self, path: str, secret_dict: Dict[str, Any]) -> bool:
        """Set secret in Vault"""
        try:
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path, 
                secret=secret_dict
            )
            return True
        except Exception as e:
            logger.error(f"Failed to set secret in Vault: {e}")
            return False

    def is_authenticated(self) -> bool:
        """Check if client is authenticated"""
        return self.client.is_authenticated()

def get_vault_secrets() -> Dict[str, str]:
    """Get all required secrets from Vault"""
    vault_client = VaultClient()
    
    if not vault_client.is_authenticated():
        logger.warning("Vault client not authenticated, falling back to environment variables")
        return {
            "FIREBASE_PROJECT_ID": os.getenv("FIREBASE_PROJECT_ID"),
            "FIREBASE_PRIVATE_KEY": os.getenv("FIREBASE_PRIVATE_KEY"),
            "FIREBASE_CLIENT_EMAIL": os.getenv("FIREBASE_CLIENT_EMAIL"),
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        }
    
    secrets = {}
    
    # Get Firebase secrets
    firebase_secrets = vault_client.get_secret("secret/firebase")
    if firebase_secrets:
        secrets.update({
            "FIREBASE_PROJECT_ID": firebase_secrets.get("project_id"),
            "FIREBASE_PRIVATE_KEY": firebase_secrets.get("private_key"),
            "FIREBASE_CLIENT_EMAIL": firebase_secrets.get("client_email"),
        })
    
    # Get AI secrets
    ai_secrets = vault_client.get_secret("secret/ai")
    if ai_secrets:
        secrets.update({
            "OPENAI_API_KEY": ai_secrets.get("openai_key"),
        })
    
    return secrets
