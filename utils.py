"""
Utility functions for the repository scanner.
Provides logging, hashing, rate limiting, and other helpers.
"""
import hashlib
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
import requests


def setup_logging(log_file: Path, log_level: str = 'INFO'):
    """
    Set up logging to both console and file.
    
    Args:
        log_file: Path to log file
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    # Create logs directory if it doesn't exist
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger('scanner')


def generate_finding_hash(file_path: str, line_number: int, secret_type: str, content: str = '') -> str:
    """
    Generate a unique hash for a finding to detect duplicates.
    
    Args:
        file_path: Path to file containing the secret
        line_number: Line number where secret was found
        secret_type: Type of secret (e.g., 'AWS Key', 'GitHub Token')
        content: Optional content snippet
    
    Returns:
        SHA256 hash string
    """
    hash_input = f"{file_path}:{line_number}:{secret_type}:{content}"
    return hashlib.sha256(hash_input.encode()).hexdigest()


def check_rate_limit(github_token: str) -> dict:
    """
    Check GitHub API rate limit status.
    
    Args:
        github_token: GitHub personal access token
    
    Returns:
        Dictionary with rate limit info: {limit, remaining, reset_time}
    """
    headers = {'Authorization': f'token {github_token}'}
    
    try:
        response = requests.get('https://api.github.com/rate_limit', headers=headers)
        data = response.json()
        
        core_limits = data.get('resources', {}).get('core', {})
        
        return {
            'limit': core_limits.get('limit', 0),
            'remaining': core_limits.get('remaining', 0),
            'reset_time': datetime.fromtimestamp(core_limits.get('reset', 0))
        }
    except Exception as e:
        logging.error(f"Failed to check rate limit: {e}")
        return {'limit': 0, 'remaining': 0, 'reset_time': datetime.now()}


def wait_for_rate_limit(github_token: str, min_remaining: int = 100):
    """
    Wait if rate limit is too low.
    
    Args:
        github_token: GitHub personal access token
        min_remaining: Minimum remaining requests before waiting
    """
    limits = check_rate_limit(github_token)
    
    if limits['remaining'] < min_remaining:
        wait_seconds = (limits['reset_time'] - datetime.now()).total_seconds()
        if wait_seconds > 0:
            logging.warning(
                f"Rate limit low ({limits['remaining']}/{limits['limit']}). "
                f"Waiting {int(wait_seconds)} seconds until reset..."
            )
            time.sleep(wait_seconds + 5)  # Add 5 second buffer


def calculate_recency_score(pushed_at: str, max_days: int = 30) -> float:
    """
    Calculate recency score based on when repo was last pushed.
    
    Args:
        pushed_at: ISO format timestamp of last push
        max_days: Days for maximum score (1.0)
    
    Returns:
        Score from 0.0 to 1.0
    """
    try:
        pushed_date = datetime.fromisoformat(pushed_at.replace('Z', '+00:00'))
        days_ago = (datetime.now(pushed_date.tzinfo) - pushed_date).days
        
        if days_ago <= max_days:
            return 1.0
        elif days_ago <= max_days * 6:  # 6 months
            return max(0.0, 1.0 - (days_ago - max_days) / (max_days * 5))
        else:
            return 0.0
    except Exception as e:
        logging.error(f"Error calculating recency score: {e}")
        return 0.0


def calculate_unpopularity_score(stars: int, max_stars: int = 10) -> float:
    """
    Calculate unpopularity score (inverse of popularity).
    Lower stars = higher score.
    
    Args:
        stars: Number of stars
        max_stars: Stars for minimum score
    
    Returns:
        Score from 0.0 to 1.0
    """
    if stars <= max_stars:
        return 1.0
    elif stars <= max_stars * 5:
        return max(0.0, 1.0 - (stars - max_stars) / (max_stars * 4))
    else:
        return 0.0


def calculate_priority_score(stars: int, pushed_at: str, file_matches: int) -> float:
    """
    Calculate overall priority score for a repository.
    
    Args:
        stars: Number of stars
        pushed_at: Last push timestamp
        file_matches: Number of suspicious files found
    
    Returns:
        Priority score from 0.0 to 1.0
    """
    recency = calculate_recency_score(pushed_at)
    unpopularity = calculate_unpopularity_score(stars)
    file_score = min(1.0, file_matches * 0.2)  # Each match adds 0.2, capped at 1.0
    
    # Weighted average: 40% recency, 40% unpopularity, 20% file matches
    priority = (recency * 0.4) + (unpopularity * 0.4) + (file_score * 0.2)
    
    return round(priority, 3)


def sanitize_repo_name(repo_url: str) -> str:
    """
    Extract clean repository name from URL.
    
    Args:
        repo_url: Full repository URL
    
    Returns:
        Clean repo name (e.g., 'username/repo')
    """
    parts = repo_url.rstrip('/').split('/')
    if len(parts) >= 2:
        return f"{parts[-2]}/{parts[-1].replace('.git', '')}"
    return repo_url


def format_bytes(bytes_size: int) -> str:
    """
    Format bytes into human-readable string.
    
    Args:
        bytes_size: Size in bytes
    
    Returns:
        Formatted string (e.g., '1.5 MB')
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"


def safe_get(dictionary: dict, *keys, default=None):
    """
    Safely get nested dictionary values.
    
    Args:
        dictionary: Dictionary to query
        *keys: Sequence of keys to traverse
        default: Default value if key not found
    
    Returns:
        Value at nested key or default
    """
    result = dictionary
    for key in keys:
        if isinstance(result, dict):
            result = result.get(key, default)
        else:
            return default
    return result if result is not None else default
