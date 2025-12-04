"""
GitHub repository search and discovery module.
Searches for repositories with potential API key leaks using GitHub Search API.
"""
import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict
from src.utils.utils import calculate_priority_score, wait_for_rate_limit, safe_get

logger = logging.getLogger('scanner.search')


class RepoSearcher:
    """Search GitHub for repositories with potential secrets."""
    
    def __init__(self, github_token: str, max_stars: int = 50, min_recency_days: int = 180):
        """
        Initialize repository searcher.
        
        Args:
            github_token: GitHub personal access token
            max_stars: Maximum stars for target repos
            min_recency_days: Minimum recency in days
        """
        self.github_token = github_token
        self.max_stars = max_stars
        self.min_recency_days = min_recency_days
        self.headers = {'Authorization': f'token {github_token}'}
        self.base_url = 'https://api.github.com/search/repositories'
    
    def build_search_queries(self) -> List[str]:
        """
        Build list of search queries for finding potential leaks.
        
        Returns:
            List of GitHub search query strings
        """
        # Calculate date threshold
        cutoff_date = (datetime.now() - timedelta(days=self.min_recency_days)).strftime('%Y-%m-%d')
        
        # Base filters applied to all queries
        base_filters = f"stars:<{self.max_stars} pushed:>{cutoff_date} fork:false"
        
        # Search patterns for common leak locations
        queries = [
            # Configuration files with API keys
            f'.env in:path {base_filters}',
            f'config.json in:path {base_filters}',
            f'settings.py in:path {base_filters}',
            f'application.yml in:path {base_filters}',
            f'secrets.json in:path {base_filters}',
            
            # Common API key patterns
            f'"api_key" extension:env {base_filters}',
            f'"apiKey" extension:json {base_filters}',
            f'"API_TOKEN" {base_filters}',
            f'"SECRET_KEY" {base_filters}',
            
            # Specific service patterns
            f'"sk-" in:file {base_filters}',  # OpenAI
            f'"ghp_" in:file {base_filters}',  # GitHub
            f'"xoxb-" in:file {base_filters}',  # Slack
            f'"AKIA" in:file {base_filters}',  # AWS Access Key
            
            # Database connection strings
            f'"mongodb://" in:file {base_filters}',
            f'"postgres://" in:file {base_filters}',
            f'"mysql://" in:file {base_filters}',
        ]
        
        return queries
    
    def search_repositories(self, query: str, max_results: int = 30) -> List[Dict]:
        """
        Search GitHub repositories using a query.
        
        Args:
            query: GitHub search query
            max_results: Maximum number of results to return
        
        Returns:
            List of repository dictionaries
        """
        logger.info(f"Searching: {query}")
        
        # Check rate limit before making request
        wait_for_rate_limit(self.github_token, min_remaining=50)
        
        all_repos = []
        page = 1
        per_page = 30  # GitHub max per page
        
        while len(all_repos) < max_results:
            try:
                params = {
                    'q': query,
                    'sort': 'updated',
                    'order': 'desc',
                    'per_page': per_page,
                    'page': page
                }
                
                response = requests.get(self.base_url, headers=self.headers, params=params)
                
                if response.status_code != 200:
                    logger.error(f"Search failed: {response.status_code} - {response.text}")
                    break
                
                data = response.json()
                items = data.get('items', [])
                
                if not items:
                    break
                
                all_repos.extend(items)
                
                # Check if there are more pages
                if len(items) < per_page:
                    break
                
                page += 1
                
            except Exception as e:
                logger.error(f"Error during search: {e}")
                break
        
        logger.info(f"Found {len(all_repos)} repositories for query")
        return all_repos[:max_results]
    
    def discover_repos(self, max_repos: int = 100) -> List[Dict]:
        """
        Discover repositories with potential leaks using multiple queries.
        
        Args:
            max_repos: Maximum total repositories to return
        
        Returns:
            List of unique repositories with priority scores
        """
        logger.info("Starting repository discovery...")
        
        queries = self.build_search_queries()
        all_repos = {}  # Use dict to deduplicate by URL
        
        # Search using each query
        for query in queries:
            results = self.search_repositories(query, max_results=20)
            
            for repo in results:
                repo_url = safe_get(repo, 'clone_url', default='')
                
                # Skip if already found
                if repo_url in all_repos:
                    continue
                
                # Extract repo info
                repo_info = {
                    'url': repo_url,
                    'full_name': safe_get(repo, 'full_name', default=''),
                    'owner': safe_get(repo, 'owner', 'login', default=''),
                    'name': safe_get(repo, 'name', default=''),
                    'description': safe_get(repo, 'description', default=''),
                    'stars': safe_get(repo, 'stargazers_count', default=0),
                    'pushed_at': safe_get(repo, 'pushed_at', default=''),
                    'size': safe_get(repo, 'size', default=0),
                    'language': safe_get(repo, 'language', default='Unknown'),
                    'search_query': query
                }
                
                # Skip repos that are too large (>10MB)
                if repo_info['size'] > 10000:  # Size in KB
                    logger.debug(f"Skipping large repo: {repo_info['full_name']} ({repo_info['size']} KB)")
                    continue
                
                # Calculate priority score
                repo_info['priority_score'] = calculate_priority_score(
                    stars=repo_info['stars'],
                    pushed_at=repo_info['pushed_at'],
                    file_matches=1  # At least one suspicious file found via search
                )
                
                all_repos[repo_url] = repo_info
                
                logger.debug(
                    f"Found: {repo_info['full_name']} "
                    f"(⭐{repo_info['stars']}, priority={repo_info['priority_score']})"
                )
        
        # Convert to list and sort by priority
        repo_list = list(all_repos.values())
        repo_list.sort(key=lambda x: x['priority_score'], reverse=True)
        
        logger.info(f"Discovered {len(repo_list)} unique repositories")
        
        # Return top repos by priority
        return repo_list[:max_repos]
    
    def filter_scanned_repos(self, repos: List[Dict], db_manager) -> List[Dict]:
        """
        Filter out already-scanned repositories.
        
        Args:
            repos: List of repository dictionaries
            db_manager: DatabaseManager instance
        
        Returns:
            Filtered list of repositories
        """
        unscanned = []
        
        for repo in repos:
            if not db_manager.was_repo_scanned(repo['url']):
                unscanned.append(repo)
            else:
                logger.debug(f"Skipping already scanned: {repo['full_name']}")
        
        logger.info(f"Filtered to {len(unscanned)} unscanned repositories")
        return unscanned


def search_and_prioritize(github_token: str, max_stars: int, min_recency_days: int,
                         db_manager, max_repos: int = 50) -> List[Dict]:
    """
    Main function to search and prioritize repositories.
    
    Args:
        github_token: GitHub personal access token
        max_stars: Maximum stars threshold
        min_recency_days: Minimum recency in days
        db_manager: DatabaseManager instance
        max_repos: Maximum repositories to return
    
    Returns:
        List of prioritized repository dictionaries
    """
    searcher = RepoSearcher(github_token, max_stars, min_recency_days)
    
    # Discover repositories
    repos = searcher.discover_repos(max_repos=max_repos * 2)  # Get extra to account for filtering
    
    # Filter out already-scanned repos
    repos = searcher.filter_scanned_repos(repos, db_manager)
    
    # Return top priority repos
    return repos[:max_repos]


if __name__ == '__main__':
    # Test search functionality
    import os
    from dotenv import load_dotenv
    from src.database.database import DatabaseManager
    
    load_dotenv()
    token = os.getenv('GITHUB_TOKEN')
    
    if token:
        db = DatabaseManager('test_scans.db')
        repos = search_and_prioritize(token, 50, 180, db, max_repos=10)
        
        print(f"\n✅ Found {len(repos)} repositories:\n")
        for i, repo in enumerate(repos, 1):
            print(f"{i}. {repo['full_name']} (⭐{repo['stars']}, priority={repo['priority_score']})")
    else:
        print("❌ GITHUB_TOKEN not set in .env file")
