import os

KNOWN_CONFIG_VALUES = [
    "SOURCE_READ_INTERVAL_MINUTES",
    "SOURCE_INGESTION_RUN_INTERVAL_SECONDS",
    "PYTEST_RUNTIME_TYPE",
    "JWT_ALGORITHM",
    "JWT_SECRET",
    "DB_HOST",
    "DB_PORT",
    "EXTRACT_HOST",
    "EXTRACT_PORT",
    "OLLAMA_HOST",
    "OLLAMA_PORT",
    "OLLAMA_USER",
    "OLLAMA_PASSWORD",
    "OLLAMA_EMBEDDING_MODEL",
    "RSS_BRIDGE_HOST",
    "RSS_BRIDGE_PORT",
    "BUILD_VERSION",
]

DEFAULT_CONFIG = {
    "SOURCE_READ_INTERVAL_MINUTES": 30,
    "SOURCE_INGESTION_RUN_INTERVAL_SECONDS": 15,
    "PYTEST_RUNTIME_TYPE": "local",
    "JWT_ALGORITHM": "HS256",
    "OLLAMA_PORT": 11434,
    "RSS_BRIDGE_PORT": 80,
    "BUILD_VERSION": "0.0.0-beta",
}


class ConfigError(Exception):
    """Custom exception for configuration errors."""

    pass


class Config:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.config = {}

    def get(self, key, default=None):
        if key not in KNOWN_CONFIG_VALUES:
            raise ConfigError(
                f"Tried to get unknown configuration key: '{key}'. Are you sure this is correct?"
            )

        if key not in self.config:
            env_value = os.getenv(key)
            if env_value is not None:
                self.config[key] = env_value
            elif key in DEFAULT_CONFIG:
                self.config[key] = DEFAULT_CONFIG[key]
            elif default is not None:
                return default
            else:
                raise ConfigError(
                    f"Tried to get unset known configuration key: '{key}' with no default value"
                )

        return self.config[key]

    def set(self, key, value):
        self.config[key] = value


config = Config()
