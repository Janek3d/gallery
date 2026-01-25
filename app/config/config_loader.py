"""
Configuration loader that reads from YAML file and environment variables.
Environment variables take precedence over YAML values.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional


class ConfigLoader:
    """Load configuration from YAML file with environment variable overrides."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize config loader.
        
        Args:
            config_path: Path to YAML config file. If None, tries common locations.
        """
        self.config_path = config_path or self._find_config_file()
        self.config: Dict[str, Any] = {}
        self._load_config()
    
    def _find_config_file(self) -> Path:
        """Find config.yaml in common locations."""
        # Try in order: /app/config.yaml (container), project root, app directory
        possible_paths = [
            Path('/app/config.yaml'),  # Docker config mount
            Path(__file__).resolve().parent.parent.parent / 'config.yaml',  # Project root
            Path(__file__).resolve().parent / 'config.yaml',  # App directory
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        # Return default path even if it doesn't exist (will use defaults)
        return possible_paths[1]
    
    def _load_config(self) -> None:
        """Load YAML configuration file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    self.config = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Warning: Could not load config from {self.config_path}: {e}")
                self.config = {}
        else:
            print(f"Warning: Config file not found at {self.config_path}, using defaults")
            self.config = {}
    
    def _get_env_var_candidates(self, key_path: str) -> List[str]:
        """
        Get possible environment variable names for a YAML key path.
        Returns list in order of preference (most preferred first).
        
        Examples:
            'django.secret_key' -> ['django.secret_key', 'DJANGO_SECRET_KEY']
            'database.name' -> ['database.name', 'DATABASE_NAME']
        """
        return [
            key_path,  # Dot-separated lowercase (matches YAML exactly)
            key_path.upper().replace('.', '_'),  # Uppercase underscore (traditional)
        ]
    
    def get(self, key_path: str, default: Any = None, env_var: Optional[str] = None) -> Any:
        """
        Get configuration value by dot-separated key path.
        
        Args:
            key_path: Dot-separated path (e.g., 'django.debug')
            default: Default value if not found
            env_var: Optional environment variable name. If None, auto-derived from key_path.
                     Checks both 'django.debug' and 'DJANGO_DEBUG' formats.
        
        Returns:
            Configuration value, with env var taking precedence
        """
        # Auto-derive env var candidates from key_path if not provided
        if env_var is None:
            env_var_candidates = self._get_env_var_candidates(key_path)
        else:
            env_var_candidates = [env_var]
        
        # Check environment variables in order of preference
        for env_var_name in env_var_candidates:
            env_value = os.getenv(env_var_name)
            if env_value is not None:
                # Try to convert to appropriate type
                if isinstance(default, bool):
                    return env_value.lower() in ('true', '1', 'yes', 'on')
                elif isinstance(default, int):
                    try:
                        return int(env_value)
                    except ValueError:
                        return env_value
                elif isinstance(default, list):
                    return [item.strip() for item in env_value.split(',')]
                return env_value
        
        # Navigate through nested dict
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_list(self, key_path: str, default: Optional[list] = None, env_var: Optional[str] = None) -> list:
        """
        Get configuration value as a list.
        
        Args:
            key_path: Dot-separated path (e.g., 'django.allowed_hosts')
            default: Default value if not found
            env_var: Optional environment variable name. If None, auto-derived from key_path.
        """
        value = self.get(key_path, default or [], env_var)
        if isinstance(value, list):
            return value
        elif isinstance(value, str):
            return [item.strip() for item in value.split(',')]
        return default or []
    
    def get_bool(self, key_path: str, default: bool = False, env_var: Optional[str] = None) -> bool:
        """
        Get configuration value as a boolean.
        
        Args:
            key_path: Dot-separated path (e.g., 'django.debug')
            default: Default value if not found
            env_var: Optional environment variable name. If None, auto-derived from key_path.
        """
        value = self.get(key_path, default, env_var)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value)
    
    def get_int(self, key_path: str, default: int = 0, env_var: Optional[str] = None) -> int:
        """
        Get configuration value as an integer.
        
        Args:
            key_path: Dot-separated path (e.g., 'celery.task_time_limit')
            default: Default value if not found
            env_var: Optional environment variable name. If None, auto-derived from key_path.
        """
        value = self.get(key_path, default, env_var)
        try:
            return int(value)
        except (ValueError, TypeError):
            return default


# Global config loader instance
_config_loader: Optional[ConfigLoader] = None


def get_config_loader() -> ConfigLoader:
    """Get or create the global config loader instance."""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader
