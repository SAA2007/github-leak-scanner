"""
🔍 Automated Repository Secret Scanner
Scans GitHub repositories for leaked API keys and secrets.
Supports dual mode: search (auto-discover) or user (specific users).
"""
import os
import subprocess
import json
import csv
from pathlib import Path
import logging
from tqdm import tqdm
from datetime import datetime

# Import our modules
from src.core.config import config
from src.database.database import DatabaseManager
from src.core.search_repos import search_and_prioritize
from src.utils.utils import setup_logging, generate_finding_hash, safe_get

# Setup logging
logger = setup_logging(config.log_file, config.log_level)

# Initialize database
db = DatabaseManager(config.database_path)

# Create output directory
config.output_dir.mkdir(exist_ok=True)


def get_repos_user_mode():
    """
    Fetch repositories from specified users (User Mode).
    
    Returns:
        List of repository URLs to scan
    """
    logger.info(f"[USER MODE] Fetching repos from: {', '.join(config.github_users)}")
    headers = {"Authorization": f"token {config.github_token}"}
    all_repos = []
    
    for user in config.github_users:
        # Check if user was scanned recently
        if db.was_user_scanned_recently(user, config.scan_interval_hours):
            logger.info(f"⏭️  User '{user}' was scanned recently, skipping...")
            continue
        
        logger.info(f"Fetching repos for user: {user}")
        page = 1
        
        while True:
            url = f"https://api.github.com/users/{user}/repos?per_page=100&page={page}"
            
            try:
                import requests
                response = requests.get(url, headers=headers)
                
                if response.status_code != 200:
                    logger.error(f"Failed to fetch repos for {user}: {response.status_code}")
                    break
                
                data = response.json()
                
                if not data or "message" in data:
                    break
                
                all_repos.extend(data)
                page += 1
                
            except Exception as e:
                logger.error(f"Error fetching repos for {user}: {e}")
                break
        
        # Update user scan record
        db.update_user_scan(user)
        logger.info(f"✓ Found {len(all_repos)} repos for {user}")
    
    # Convert to repo info dictionaries
    repos = []
    for repo in all_repos:
        repo_url = safe_get(repo, 'clone_url', default='')
        if repo_url and not db.was_repo_scanned(repo_url):
            repos.append({
                'url': repo_url,
                'owner': safe_get(repo, 'owner', 'login', default='unknown'),
                'name': safe_get(repo, 'name', default='unknown'),
                'full_name': safe_get(repo, 'full_name', default=''),
                'stars': safe_get(repo, 'stargazers_count', default=0),
                'pushed_at': safe_get(repo, 'pushed_at', default=''),
                'priority_score': 0.5  # Default priority for user mode
            })
    
    logger.info(f"📊 Total unscanned repos: {len(repos)}")
    return repos


def get_repos_search_mode():
    """
    Discover repositories using GitHub Search (Search Mode).
    
    Returns:
        List of prioritized repository dictionaries
    """
    logger.info("[SEARCH MODE] Discovering repositories with potential leaks...")
    
    repos = search_and_prioritize(
        github_token=config.github_token,
        max_stars=config.max_stars_threshold,
        min_recency_days=config.min_recency_days,
        db_manager=db,
        max_repos=50
    )
    
    logger.info(f"🎯 Found {len(repos)} high-priority targets")
    return repos


def clone_repo(repo_info: dict):
    """
    Clone a repository.
    
    Args:
        repo_info: Repository information dictionary
    
    Returns:
        Path to cloned repository or None if failed
    """
    name = repo_info['name']
    url = repo_info['url']
    
    logger.info(f"📥 Cloning {repo_info.get('full_name', name)}...")
    repo_dir = Path("repos") / name
    
    # Remove if exists
    if repo_dir.exists():
        try:
            import shutil
            shutil.rmtree(repo_dir)
        except Exception as e:
            logger.warning(f"Failed to remove existing repo dir: {e}")
    
    repo_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", url, str(repo_dir)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            logger.info(f"✓ Cloned successfully")
            return repo_dir
        else:
            logger.error(f"Clone failed: {result.stderr}")
            return None
            
    except subprocess.TimeoutExpired:
        logger.error(f"Clone timeout for {name}")
        return None
    except Exception as e:
        logger.error(f"Clone error: {e}")
        return None


def run_gitleaks(repo_path: Path):
    """Run Gitleaks scanner on repository."""
    logger.info(f"🔍 Running Gitleaks on {repo_path.name}...")
    
    try:
        result = subprocess.run(
            [
                config.gitleaks_path,
                "detect",
                "--source", str(repo_path),
                "--no-banner",
                "-v",
                "--report-format=json"
            ],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        try:
            findings = json.loads(result.stdout) if result.stdout else []
            logger.info(f"✓ Gitleaks found {len(findings)} potential secrets")
            return findings
        except json.JSONDecodeError:
            logger.warning("Gitleaks output parsing failed")
            return []
            
    except subprocess.TimeoutExpired:
        logger.error(f"Gitleaks timeout on {repo_path.name}")
        return []
    except FileNotFoundError:
        logger.error(f"Gitleaks not found at {config.gitleaks_path}")
        return []
    except Exception as e:
        logger.error(f"Gitleaks error: {e}")
        return []


def run_trufflehog(repo_path: Path):
    """Run TruffleHog scanner on repository."""
    logger.info(f"🔍 Running TruffleHog on {repo_path.name}...")
    
    try:
        result = subprocess.run(
            [
                config.trufflehog_path,
                "filesystem",
                str(repo_path),
                "--json"
            ],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        findings = []
        for line in result.stdout.splitlines():
            try:
                findings.append(json.loads(line))
            except json.JSONDecodeError:
                pass
        
        logger.info(f"✓ TruffleHog found {len(findings)} potential secrets")
        return findings
        
    except subprocess.TimeoutExpired:
        logger.error(f"TruffleHog timeout on {repo_path.name}")
        return []
    except FileNotFoundError:
        logger.warning(f"TruffleHog not found, skipping...")
        return []
    except Exception as e:
        logger.error(f"TruffleHog error: {e}")
        return []


def process_findings(repo_info: dict, gitleaks_findings: list, truffle_findings: list):
    """
    Process and store findings in database.
    
    Args:
        repo_info: Repository information
        gitleaks_findings: Findings from Gitleaks
        truffle_findings: Findings from TruffleHog
    
    Returns:
        Dictionary with finding counts
    """
    repo_url = repo_info['url']
    total = 0
    new = 0
    
    # Process Gitleaks findings
    for finding in gitleaks_findings:
        file_path = safe_get(finding, 'File', default='unknown')
        secret_type = safe_get(finding, 'Description', default='unknown')
        line_num = safe_get(finding, 'StartLine', default=0)
        
        hash_val = generate_finding_hash(file_path, line_num, secret_type)
        
        _, is_new = db.add_finding(
            repo_url=repo_url,
            tool='gitleaks',
            file_path=file_path,
            secret_type=secret_type,
            finding_hash=hash_val,
            line_number=line_num,
            description=safe_get(finding, 'Match', default='')
        )
        
        total += 1
        if is_new:
            new += 1
    
    # Process TruffleHog findings
    for finding in truffle_findings:
        file_path = safe_get(finding, 'SourceMetadata', 'Data', 'Filesystem', 'file', default='unknown')
        secret_type = safe_get(finding, 'DetectorName', default='unknown')
        line_num = safe_get(finding, 'SourceMetadata', 'Data', 'Filesystem', 'line', default=0)
        
        hash_val = generate_finding_hash(file_path, line_num, secret_type)
        
        _, is_new = db.add_finding(
            repo_url=repo_url,
            tool='trufflehog',
            file_path=file_path,
            secret_type=secret_type,
            finding_hash=hash_val,
            line_number=line_num,
            description=''
        )
        
        total += 1
        if is_new:
            new += 1
    
    return {'total': total, 'new': new}


def save_reports(scan_run_id: int):
    """Export findings to JSON and CSV."""
    logger.info("📄 Generating reports...")
    
    session = db.get_session()
    try:
        from src.database.database import Finding
        findings = session.query(Finding).all()
        
        # Prepare data
        report_data = []
        for f in findings:
            report_data.append({
                'repo_url': f.repo_url,
                'tool': f.tool,
                'file': f.file_path,
                'secret_type': f.secret_type,
                'status': f.status,
                'first_seen': f.first_seen.isoformat() if f.first_seen else '',
                'last_seen': f.last_seen.isoformat() if f.last_seen else ''
            })
        
        # JSON report
        json_path = config.output_dir / "findings.json"
        with open(json_path, "w", encoding='utf-8') as f:
            json.dump(report_data, f, indent=2)
        
        # CSV report
        csv_path = config.output_dir / "findings.csv"
        with open(csv_path, "w", newline="", encoding='utf-8') as f:
            if report_data:
                writer = csv.DictWriter(f, fieldnames=report_data[0].keys())
                writer.writeheader()
                writer.writerows(report_data)
        
        logger.info(f"✓ Reports saved to {config.output_dir}/")
        
    finally:
        session.close()


def main():
    """Main scanner entry point."""
    logger.info("=" * 60)
    logger.info("🔍 Automated Secret Scanner Starting")
    logger.info(f"Mode: {config.scan_mode.upper()}")
    logger.info("=" * 60)
    
    # Create scan run record
    scan_run = db.create_scan_run(mode=config.scan_mode)
    
    try:
        # Get repositories based on mode
        if config.scan_mode == 'search':
            repos = get_repos_search_mode()
        else:  # user mode
            repos = get_repos_user_mode()
        
        if not repos:
            logger.warning("⚠️  No repositories to scan")
            db.update_scan_run(scan_run.id, end_time=datetime.now(), repos_scanned=0)
            return
        logger.info(f"📋 Scanning {len(repos)} repositories...")
        print()  # Newline before progress bar
        
        total_findings = 0
        total_new = 0
        repos_scanned = 0
        
        # Progress bar for scanning
        with tqdm(total=len(repos), desc="🔍 Scanning repos", unit="repo", ncols=100) as pbar:
            for i, repo_info in enumerate(repos, 1):
                repo_name = repo_info.get('full_name', repo_info['name'])
                pbar.set_postfix_str(f"Current: {repo_name[:30]}...")
                
                logger.debug(f"[{i}/{len(repos)}] Processing: {repo_name}")
                logger.debug(f"   ⭐ Stars: {repo_info.get('stars', 0)} | Priority: {repo_info.get('priority_score', 0):.2f}")
                
                # Clone repository
                repo_path = clone_repo(repo_info)
                if not repo_path:
                    pbar.update(1)
                    continue
                
                # Save repo to database
                db.get_or_create_repo(
                    repo_url=repo_info['url'],
                    owner=repo_info['owner'],
                    name=repo_info['name'],
                    stars=repo_info.get('stars', 0),
                    priority_score=repo_info.get('priority_score', 0),
                    discovered_via=config.scan_mode
                )
                
                # Run scanners
                gitleaks_results = run_gitleaks(repo_path)
                truffle_results = run_trufflehog(repo_path)
                
                # Process findings
                counts = process_findings(repo_info, gitleaks_results, truffle_results)
                total_findings += counts['total']
                total_new += counts['new']
                
                logger.debug(f"   📊 Findings: {counts['total']} total, {counts['new']} new")
                
                # Update repo scan record
                db.update_repo_scan(repo_info['url'])
                repos_scanned += 1
                
                # Update progress bar
                pbar.update(1)
                pbar.set_postfix_str(f"Found: {total_new} new secrets")
                
                # Cleanup cloned repo with better Windows handling
                try:
                    import shutil
                    import time
                    
                    # Try normal removal first
                    shutil.rmtree(repo_path, ignore_errors=False)
                except PermissionError:
                    # Windows file lock - try harder
                    try:
                        time.sleep(0.5)  # Brief pause
                        import subprocess
                        subprocess.run(['rmdir', '/S', '/Q', str(repo_path)], 
                                     shell=True, check=False)
                    except Exception as e:
                        logger.warning(f"Could not cleanup {repo_path.name}: {e}")
                except Exception as e:
                    logger.debug(f"Cleanup error (non-critical): {e}")
        
        # Update scan run
        db.update_scan_run(
            scan_run.id,
            end_time=datetime.now(),
            repos_scanned=repos_scanned,
            findings_count=total_findings,
            new_findings_count=total_new,
            success=True
        )
        
        # Generate reports
        save_reports(scan_run.id)
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("✅ SCAN COMPLETE")
        logger.info(f"📊 Repositories scanned: {repos_scanned}")
        logger.info(f"🔍 Total findings: {total_findings}")
        logger.info(f"🆕 New findings: {total_new}")
        logger.info(f"📁 Reports: {config.output_dir}/")
        logger.info("=" * 60)
        
        # Database stats
        stats = db.get_stats()
        logger.info(f"\n📈 Database Statistics:")
        logger.info(f"   Total users tracked: {stats['total_users']}")
        logger.info(f"   Total repos tracked: {stats['total_repos']}")
        logger.info(f"   Total findings: {stats['total_findings']}")
        logger.info(f"   New findings: {stats['new_findings']}")
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Scan interrupted by user")
        db.update_scan_run(
            scan_run.id,
            end_time=datetime.now(),
            success=False,
            error_message="Interrupted by user"
        )
    except Exception as e:
        logger.error(f"\n❌ Scan failed: {e}", exc_info=True)
        db.update_scan_run(
            scan_run.id,
            end_time=datetime.now(),
            success=False,
            error_message=str(e)
        )


if __name__ == "__main__":
    main()
