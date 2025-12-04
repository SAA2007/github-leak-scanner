"""
Database models and operations for repository scanner.
Uses SQLAlchemy for persistence and tracking.
"""
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pathlib import Path
import logging

logger = logging.getLogger('scanner.database')
Base = declarative_base()


class ScannedUser(Base):
    """Track scanned GitHub users/organizations."""
    __tablename__ = 'scanned_users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    last_scan_date = Column(DateTime, default=datetime.now)
    scan_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<ScannedUser(username='{self.username}', last_scan={self.last_scan_date})>"


class Repository(Base):
    """Track scanned repositories."""
    __tablename__ = 'repositories'
    
    id = Column(Integer, primary_key=True)
    repo_url = Column(String(500), unique=True, nullable=False, index=True)
    owner = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    last_scan_date = Column(DateTime, default=datetime.now)
    last_commit_hash = Column(String(40))
    stars = Column(Integer, default=0)
    priority_score = Column(Float, default=0.0)
    discovered_via = Column(String(50))  # 'search' or 'user'
    created_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<Repository(owner='{self.owner}', name='{self.name}', stars={self.stars})>"


class Finding(Base):
    """Track discovered secrets/API keys."""
    __tablename__ = 'findings'
    
    id = Column(Integer, primary_key=True)
    repo_id = Column(Integer, nullable=False, index=True)
    repo_url = Column(String(500), nullable=False)
    tool = Column(String(50), nullable=False)  # 'gitleaks' or 'trufflehog'
    file_path = Column(String(500), nullable=False)
    secret_type = Column(String(100), nullable=False)
    finding_hash = Column(String(64), unique=True, nullable=False, index=True)
    first_seen = Column(DateTime, default=datetime.now)
    last_seen = Column(DateTime, default=datetime.now)
    status = Column(String(20), default='new')  # 'new', 'recurring', 'resolved'
    line_number = Column(Integer)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<Finding(type='{self.secret_type}', file='{self.file_path}', status='{self.status}')>"


class ScanRun(Base):
    """Track scan execution history."""
    __tablename__ = 'scan_runs'
    
    id = Column(Integer, primary_key=True)
    start_time = Column(DateTime, default=datetime.now)
    end_time = Column(DateTime)
    repos_scanned = Column(Integer, default=0)
    findings_count = Column(Integer, default=0)
    new_findings_count = Column(Integer, default=0)
    search_query = Column(Text)  # For search mode
    mode = Column(String(20))  # 'search' or 'user'
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    
    def __repr__(self):
        return f"<ScanRun(id={self.id}, mode='{self.mode}', repos={self.repos_scanned}, findings={self.findings_count})>"


class SearchQuery(Base):
    """Track search queries used in search mode."""
    __tablename__ = 'search_queries'
    
    id = Column(Integer, primary_key=True)
    query_text = Column(Text, nullable=False)
    last_run = Column(DateTime)
    results_count = Column(Integer, default=0)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<SearchQuery(query='{self.query_text[:50]}...', results={self.results_count})>"


class DatabaseManager:
    """Manage database operations."""
    
    def __init__(self, db_path: str = 'scans.db'):
        """Initialize database connection."""
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        logger.info(f"Database initialized: {db_path}")
    
    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()
    
    # ===== User Operations =====
    
    def get_or_create_user(self, username: str) -> ScannedUser:
        """Get existing user or create new one."""
        session = self.get_session()
        try:
            user = session.query(ScannedUser).filter_by(username=username).first()
            if not user:
                user = ScannedUser(username=username, scan_count=0)
                session.add(user)
                session.commit()
                logger.info(f"Created new user record: {username}")
            return user
        finally:
            session.close()
    
    def update_user_scan(self, username: str):
        """Update user's last scan date and increment count."""
        session = self.get_session()
        try:
            user = self.get_or_create_user(username)
            session.query(ScannedUser).filter_by(username=username).update({
                'last_scan_date': datetime.now(),
                'scan_count': ScannedUser.scan_count + 1
            })
            session.commit()
            logger.debug(f"Updated scan for user: {username}")
        finally:
            session.close()
    
    def was_user_scanned_recently(self, username: str, hours: int = 24) -> bool:
        """Check if user was scanned within last N hours."""
        session = self.get_session()
        try:
            user = session.query(ScannedUser).filter_by(username=username).first()
            if not user or not user.last_scan_date:
                return False
            
            time_diff = datetime.now() - user.last_scan_date
            return time_diff.total_seconds() < (hours * 3600)
        finally:
            session.close()
    
    # ===== Repository Operations =====
    
    def get_or_create_repo(self, repo_url: str, owner: str, name: str, **kwargs) -> Repository:
        """Get existing repo or create new one."""
        session = self.get_session()
        try:
            repo = session.query(Repository).filter_by(repo_url=repo_url).first()
            if not repo:
                repo = Repository(
                    repo_url=repo_url,
                    owner=owner,
                    name=name,
                    **kwargs
                )
                session.add(repo)
                session.commit()
                logger.info(f"Created new repo record: {owner}/{name}")
            return repo
        finally:
            session.close()
    
    def update_repo_scan(self, repo_url: str, commit_hash: str = None):
        """Update repository's last scan date."""
        session = self.get_session()
        try:
            update_data = {'last_scan_date': datetime.now()}
            if commit_hash:
                update_data['last_commit_hash'] = commit_hash
            
            session.query(Repository).filter_by(repo_url=repo_url).update(update_data)
            session.commit()
            logger.debug(f"Updated scan for repo: {repo_url}")
        finally:
            session.close()
    
    def was_repo_scanned(self, repo_url: str) -> bool:
        """Check if repository has been scanned before."""
        session = self.get_session()
        try:
            repo = session.query(Repository).filter_by(repo_url=repo_url).first()
            return repo is not None
        finally:
            session.close()
    
    # ===== Finding Operations =====
    
    def add_finding(self, repo_url: str, tool: str, file_path: str, secret_type: str,
                   finding_hash: str, **kwargs) -> tuple:
        """
        Add or update a finding.
        
        Returns:
            Tuple of (Finding object, is_new: bool)
        """
        session = self.get_session()
        try:
            # Check if finding already exists
            existing = session.query(Finding).filter_by(finding_hash=finding_hash).first()
            
            if existing:
                # Update last_seen time and status
                existing.last_seen = datetime.now()
                if existing.status == 'new':
                    existing.status = 'recurring'
                session.commit()
                logger.debug(f"Updated existing finding: {finding_hash[:8]}...")
                return existing, False
            else:
                # Create new finding
                # Get repo_id
                repo = session.query(Repository).filter_by(repo_url=repo_url).first()
                repo_id = repo.id if repo else 0
                
                finding = Finding(
                    repo_id=repo_id,
                    repo_url=repo_url,
                    tool=tool,
                    file_path=file_path,
                    secret_type=secret_type,
                    finding_hash=finding_hash,
                    status='new',
                    **kwargs
                )
                session.add(finding)
                session.commit()
                logger.info(f"New finding: {secret_type} in {file_path}")
                return finding, True
        finally:
            session.close()
    
    def get_new_findings_count(self, since: datetime = None) -> int:
        """Count new findings since a specific time."""
        session = self.get_session()
        try:
            query = session.query(Finding).filter_by(status='new')
            if since:
                query = query.filter(Finding.first_seen >= since)
            return query.count()
        finally:
            session.close()
    
    # ===== Scan Run Operations =====
    
    def create_scan_run(self, mode: str, search_query: str = None) -> ScanRun:
        """Create a new scan run record."""
        session = self.get_session()
        try:
            run = ScanRun(mode=mode, search_query=search_query, start_time=datetime.now())
            session.add(run)
            session.commit()
            logger.info(f"Started scan run #{run.id} in {mode} mode")
            return run
        finally:
            session.close()
    
    def update_scan_run(self, run_id: int, **kwargs):
        """Update scan run with results."""
        session = self.get_session()
        try:
            session.query(ScanRun).filter_by(id=run_id).update(kwargs)
            session.commit()
            logger.debug(f"Updated scan run #{run_id}")
        finally:
            session.close()
    
    # ===== Statistics =====
    
    def get_stats(self) -> dict:
        """Get database statistics."""
        session = self.get_session()
        try:
            return {
                'total_users': session.query(ScannedUser).count(),
                'total_repos': session.query(Repository).count(),
                'total_findings': session.query(Finding).count(),
                'new_findings': session.query(Finding).filter_by(status='new').count(),
                'total_scans': session.query(ScanRun).count()
            }
        finally:
            session.close()


def init_db(db_path: str = 'scans.db'):
    """Initialize database with all tables."""
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)
    logger.info(f"Database tables created: {db_path}")
    return DatabaseManager(db_path)


if __name__ == '__main__':
    # Test database creation
    db = init_db('scans.db')
    print("✅ Database initialized successfully!")
    print(f"📊 Stats: {db.get_stats()}")
