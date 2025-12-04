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
from datetime import datetime, timedelta
from pathlib import Path
import time
import functools


# ==================== ERROR HANDLING ====================

def retry_with_backoff(max_retries=3, initial_delay=1, backoff_factor=2, exceptions=(Exception,)):
    """
    Decorator to retry a function with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch and retry
    
    Example:
        @retry_with_backoff(max_retries=3, initial_delay=2)
        def unreliable_api_call():
            response = requests.get("https://api.example.com")
            return response.json()
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        logging.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                            f"Retrying in {delay}s..."
                        )
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logging.error(
                            f"{func.__name__} failed after {max_retries + 1} attempts: {e}"
                        )
            
            raise last_exception
        
        return wrapper
    return decorator


def timeout_handler(timeout_seconds):
    """
    Decorator to add timeout to functions (Unix/Linux only).
    For Windows, use subprocess with timeout parameter instead.
    
    Args:
        timeout_seconds: Maximum seconds before timeout
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import signal
            
            def timeout_error(signum, frame):
                raise TimeoutError(f"{func.__name__} timed out after {timeout_seconds}s")
            
            # Set the signal handler
            signal.signal(signal.SIGALRM, timeout_error)
            signal.alarm(timeout_seconds)
            
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)  # Disable the alarm
            
            return result
        
        return wrapper
    return decorator


class NetworkError(Exception):
    """Custom exception for network-related errors."""
    pass


class RateLimitError(Exception):
    """Custom exception for rate limit errors."""
    pass


def handle_github_response(response):
    """
    Handle GitHub API response and raise appropriate exceptions.
    
    Args:
        response: requests.Response object
    
    Raises:
        RateLimitError: If rate limit exceeded
        NetworkError: For other network errors
    """
    if response.status_code == 403:
        if 'rate limit' in response.text.lower():
            raise RateLimitError("GitHub API rate limit exceeded")
        raise NetworkError(f"GitHub API forbidden: {response.text}")
    elif response.status_code == 401:
        raise NetworkError("GitHub API authentication failed - check your token")
    elif response.status_code >= 500:
        raise NetworkError(f"GitHub API server error: {response.status_code}")
    elif response.status_code >= 400:
        raise NetworkError(f"GitHub API client error: {response.status_code} - {response.text}")
    
    return response


# ==================== LOGGING SETUP ====================

def setup_logging(log_file: Path, log_level: str = 'INFO'):
    """
    Set up comprehensive logging with separate debug and error logs.
    
    Args:
        log_file: Path to main log file
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger('scanner')
    logger.setLevel(logging.DEBUG)  # Capture all levels
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Formatter for detailed logs
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - [%(levelname)s] - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Formatter for console (simpler)
    console_formatter = logging.Formatter(
        '%(asctime)s - [%(levelname)s] - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # 1. Console Handler (INFO and above)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level))
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 2. Main Log File (all levels based on config)
    main_file_handler = logging.FileHandler(log_file, encoding='utf-8', mode='a')
    main_file_handler.setLevel(getattr(logging, log_level))
    main_file_handler.setFormatter(detailed_formatter)
    logger.addHandler(main_file_handler)
    
    # 3. Debug Log File (DEBUG and above) - separate file
    debug_log = log_file.parent / 'debug.log'
    debug_handler = logging.FileHandler(debug_log, encoding='utf-8', mode='a')
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(detailed_formatter)
    logger.addHandler(debug_handler)
    
    # 4. Error Log File (ERROR and above only) - separate file
    error_log = log_file.parent / 'error.log'
    error_handler = logging.FileHandler(error_log, encoding='utf-8', mode='a')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    logger.addHandler(error_handler)
    
    # Log startup
    logger.info("=" * 60)
    logger.info("Logging initialized")
    logger.info(f"Main log: {log_file}")
    logger.info(f"Debug log: {debug_log}")
    logger.info(f"Error log: {error_log}")
    logger.info(f"Log level: {log_level}")
    logger.info("=" * 60)
    
    return logger


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
