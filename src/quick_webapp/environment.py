import os

class Environment:
    """
    Wrapper for .env files to load environment variables from a file.
    """

    def __init__(self, path: str | None = ".env"):
        """
        Load environment variables from the specified .env file.
        """

        self.__env = {}
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    self.__env[key] = value

    def contains(self, key: str) -> bool:
        """
        Return True if the environment contains the specified key.
        """

        return key in self.__env
    
    def get(self, key: str, alter: str | None = None) -> str | None:
        """
        Return the value for the specified key, or the default if not found.
        """

        return self.__env[key] if key in self.__env else alter
    
    def push_to_env(self) -> None:
        """
        Set all loaded environment variables into the system environment.
        """
        
        for key, value in self.__env.items():
            os.environ[key] = value
