"""
Configuration management for repository scanner.
Loads settings from .env file and provides validated configuration.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration container for scanner settings."""
    
    def __init__(self):
        # GitHub API
        self.github_token = os.getenv('GITHUB_TOKEN', '')
        self.github_users = self._parse_list(os.getenv('GITHUB_USERS', ''))
        
        # Scan Mode
        self.scan_mode = os.getenv('SCAN_MODE', 'search').lower()
        if self.scan_mode not in ['search', 'user']:
            raise ValueError(f"Invalid SCAN_MODE: {self.scan_mode}. Must be 'search' or 'user'")
        
        # Tool Paths
        self.gitleaks_path = os.getenv('GITLEAKS_PATH', 'gitleaks.exe')
        self.trufflehog_path = os.getenv('TRUFFLEHOG_PATH', 'trufflehog')
        
        # Search Mode Configuration
        self.max_stars_threshold = int(os.getenv('MAX_STARS_THRESHOLD', '50'))
        self.min_recency_days = int(os.getenv('MIN_RECENCY_DAYS', '180'))
        
        # Scanning Configuration
        self.scan_interval_hours = int(os.getenv('SCAN_INTERVAL_HOURS', '24'))
        self.max_concurrent_repos = int(os.getenv('MAX_CONCURRENT_REPOS', '3'))
        self.output_dir = Path(os.getenv('OUTPUT_DIR', 'scan_results'))
        
        # Features
        self.enable_notifications = os.getenv('ENABLE_NOTIFICATIONS', 'false').lower() == 'true'
        self.enable_scheduler = os.getenv('ENABLE_SCHEDULER', 'false').lower() == 'true'
        
        # Database
        self.database_path = os.getenv('DATABASE_PATH', 'scans.db')
        
        # Logging
        self.log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        self.log_file = Path(os.getenv('LOG_FILE', 'logs/scanner.log'))
        
        # Validate critical settings
        self._validate()
    
    def _parse_list(self, value: str) -> list:
        """Parse comma-separated string into list."""
        if not value:
            return []
        return [item.strip() for item in value.split(',') if item.strip()]
    
    def _validate(self):
        """Validate critical configuration settings."""
        if not self.github_token:
            raise ValueError(
                "GITHUB_TOKEN is required! Please set it in your .env file.\n"
                "Get a token from: https://github.com/settings/tokens"
            )
        
        if self.scan_mode == 'user' and not self.github_users:
            raise ValueError(
                "GITHUB_USERS must be set when SCAN_MODE is 'user'.\n"
                "Example: GITHUB_USERS=user1,user2,org1"
            )
        
        # Validate file paths
        if not Path(self.gitleaks_path).exists():
            print(f"⚠️  Warning: Gitleaks not found at {self.gitleaks_path}")
            print("   Download from: https://github.com/gitleaks/gitleaks/releases")
    
    def __repr__(self):
        """String representation (masks sensitive data)."""
        token_preview = f"{self.github_token[:7]}..." if self.github_token else "NOT SET"
        return (
            f"Config(\n"
            f"  mode={self.scan_mode},\n"
            f"  token={token_preview},\n"
            f"  users={self.github_users if self.scan_mode == 'user' else 'N/A'},\n"
            f"  max_stars={self.max_stars_threshold},\n"
            f"  recency_days={self.min_recency_days}\n"
            f")"
        )


# Global config instance
try:
    config = Config()
except Exception as e:
    print(f"❌ Configuration Error: {e}")
    raise
