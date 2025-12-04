"""
🚨 Containment System - Quarantine repos with active secrets

When an ACTIVE secret is found:
1. Copy entire repo to CONTAINMENT/ folder
2. Generate coordinates.txt with exact location
3. Mark in database for manual review
4. Log all containment actions

Directory structure:
CONTAINMENT/
├── repo_1_owner_name/
│   ├── COORDINATES.txt      ← Exact locations of secrets
│   ├── METADATA.json         ← Repo info, risk level
│   └── [repo files]          ← Full repo copy
└── repo_2_owner_name/
    └── ...
"""

import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import logging

logger = logging.getLogger('scanner.containment')


class ContainmentSystem:
    """Quarantine system for repos with active secrets."""
    
    def __init__(self, containment_root: Path = Path("CONTAINMENT")):
        self.containment_root = containment_root
        self.containment_root.mkdir(exist_ok=True)
        
        # Create quarantine log
        self.log_file = self.containment_root / "quarantine.log"
    
    def quarantine_repo(self, 
                       repo_path: Path,
                       repo_info: Dict,
                       findings: List[Dict]) -> Path:
        """
        Quarantine a repository with active secrets.
        
        Args:
            repo_path: Path to cloned repository
            repo_info: Repository metadata
            findings: List of active findings
        
        Returns:
            Path to quarantined repo
        """
        # Create safe directory name
        repo_name = repo_info.get('full_name', repo_info['name']).replace('/', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        quarantine_dir = self.containment_root / f"{repo_name}_{timestamp}"
        
        logger.warning(f"🚨 QUARANTINING REPO: {repo_name}")
        
        try:
            # 1. Copy repository
            shutil.copytree(repo_path, quarantine_dir, ignore=shutil.ignore_patterns('.git'))
            logger.info(f"   ✓ Copied to: {quarantine_dir}")
            
            # 2. Generate COORDINATES.txt
            coords_file = quarantine_dir / "COORDINATES.txt"
            self._generate_coordinates(coords_file, findings, repo_info)
            logger.info(f"   ✓ Generated: COORDINATES.txt")
            
            # 3. Generate METADATA.json
            metadata_file = quarantine_dir / "METADATA.json"
            self._generate_metadata(metadata_file, repo_info, findings)
            logger.info(f"   ✓ Generated: METADATA.json")
            
            # 4. Generate README.txt with instructions
            readme_file = quarantine_dir / "README_QUARANTINE.txt"
            self._generate_readme(readme_file, repo_info, findings)
            logger.info(f"   ✓ Generated: README_QUARANTINE.txt")
            
            # 5. Log quarantine action
            self._log_quarantine(repo_name, findings)
            
            logger.warning(f"   🔒 QUARANTINE COMPLETE: {quarantine_dir.name}")
            return quarantine_dir
            
        except Exception as e:
            logger.error(f"   ❌ Quarantine failed: {e}")
            # Clean up partial copy
            if quarantine_dir.exists():
                shutil.rmtree(quarantine_dir, ignore_errors=True)
            raise
    
    def _generate_coordinates(self, 
                            coords_file: Path,
                            findings: List[Dict],
                            repo_info: Dict):
        """
        Generate COORDINATES.txt with exact secret locations.
        
        Format:
        =====================================================
        🚨 SECRET COORDINATES - ACTIVE KEYS FOUND
        =====================================================
        
        Repository: owner/repo
        Scanned: 2025-12-04 20:30:00
        Total Active Secrets: 3
        
        [1] OpenAI API Key (CRITICAL RISK)
        ─────────────────────────────────────────────────────
        File:     config/settings.py
        Line:     42
        Type:     OpenAI API Key
        Status:   ACTIVE ⚠️
        Risk:     CRITICAL
        Value:    sk-proj-abc*** (truncated for safety)
        Details:  Full API access - can make requests
        
        Exact Location:
        └─ config/settings.py:42
        
        Context (3 lines before/after):
        39:  # API Configuration
        40:  API_URL = "https://api.openai.com"
        41:  
        42:  OPENAI_KEY = "sk-proj-abc123..."  ⬅️ SECRET HERE
        43:  
        44:  # Database settings
        45:  DB_HOST = "localhost"
        
        =====================================================
        """
        with open(coords_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("=" * 80 + "\n")
            f.write("🚨 SECRET COORDINATES - ACTIVE KEYS FOUND\n")
            f.write("=" * 80 + "\n\n")
            
            # Repo info
            f.write(f"Repository:    {repo_info.get('full_name', repo_info['name'])}\n")
            f.write(f"Scanned:       {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Active:  {len(findings)}\n")
            f.write(f"Stars:         {repo_info.get('stars', 0)}\n\n")
            
            # Each finding
            for idx, finding in enumerate(findings, 1):
                f.write("=" * 80 + "\n")
                f.write(f"[{idx}] {finding['secret_type']} ({finding.get('risk_level', 'HIGH')} RISK)\n")
                f.write("─" * 80 + "\n\n")
                
                f.write(f"File:      {finding['file_path']}\n")
                f.write(f"Line:      {finding.get('line_number', 'unknown')}\n")
                f.write(f"Type:      {finding['secret_type']}\n")
                f.write(f"Status:    {finding.get('validation_status', 'ACTIVE')} ⚠️\n")
                f.write(f"Risk:      {finding.get('risk_level', 'HIGH')}\n")
                
                # Truncate key for safety
                key_value = finding.get('key_value', '')
                if len(key_value) > 20:
                    truncated = key_value[:15] + '***'
                else:
                    truncated = key_value[:5] + '***'
                f.write(f"Value:     {truncated} (truncated for safety)\n")
                
                f.write(f"Details:   {finding.get('validation_details', 'No details')}\n\n")
                
                # Exact location
                f.write("Exact Location:\n")
                f.write(f"└─ {finding['file_path']}:{finding.get('line_number', '?')}\n\n")
                
                # Context (if available)
                if 'context' in finding:
                    f.write("Context:\n")
                    f.write(finding['context'] + "\n")
                
                f.write("\n")
            
            # Footer
            f.write("=" * 80 + "\n")
            f.write("⚠️  MANUAL REVIEW REQUIRED\n")
            f.write("=" * 80 + "\n\n")
            f.write("Next Steps:\n")
            f.write("1. Review each secret location above\n")
            f.write("2. Notify repository owner (if authorized)\n")
            f.write("3. Revoke active keys immediately\n")
            f.write("4. Update database with actions taken\n")
            f.write("5. Remove from quarantine after remediation\n\n")
            f.write(f"Quarantine Date: {datetime.now().isoformat()}\n")
    
    def _generate_metadata(self,
                          metadata_file: Path,
                          repo_info: Dict,
                          findings: List[Dict]):
        """Generate METADATA.json with structured data."""
        metadata = {
            "quarantine_date": datetime.now().isoformat(),
            "repository": {
                "name": repo_info.get('name'),
                "full_name": repo_info.get('full_name'),
                "owner": repo_info.get('owner'),
                "url": repo_info.get('url'),
                "stars": repo_info.get('stars', 0),
                "last_push": repo_info.get('pushed_at')
            },
            "findings_summary": {
                "total_active_secrets": len(findings),
                "critical_risk": sum(1 for f in findings if f.get('risk_level') == 'CRITICAL'),
                "high_risk": sum(1 for f in findings if f.get('risk_level') == 'HIGH'),
                "medium_risk": sum(1 for f in findings if f.get('risk_level') == 'MEDIUM')
            },
            "active_secrets": [
                {
                    "type": f['secret_type'],
                    "file": f['file_path'],
                    "line": f.get('line_number'),
                    "status": f.get('validation_status', 'ACTIVE'),
                    "risk_level": f.get('risk_level', 'HIGH'),
                    "api": f.get('api', 'Unknown'),
                    "details": f.get('validation_details', '')
                }
                for f in findings
            ],
            "actions_required": [
                "Review all secret locations",
                "Notify repository owner",
                "Revoke active keys",
                "Document remediation",
                "Remove from quarantine"
            ]
        }
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def _generate_readme(self,
                        readme_file: Path,
                        repo_info: Dict,
                        findings: List[Dict]):
        """Generate README with quarantine instructions."""
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write("🚨 QUARANTINED REPOSITORY\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Repository: {repo_info.get('full_name', repo_info['name'])}\n")
            f.write(f"Quarantine Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Active Secrets Found: {len(findings)}\n\n")
            
            f.write("WHY THIS REPO IS QUARANTINED:\n")
            f.write("-" * 80 + "\n")
            f.write("This repository has been automatically quarantined because it contains\n")
            f.write("ACTIVE API keys or secrets that were validated and confirmed to work.\n\n")
            
            f.write("RISK LEVELS:\n")
            critical = sum(1 for f in findings if f.get('risk_level') == 'CRITICAL')
            high = sum(1 for f in findings if f.get('risk_level') == 'HIGH')
            medium = sum(1 for f in findings if f.get('risk_level') == 'MEDIUM')
            
            if critical:
                f.write(f"🔴 CRITICAL: {critical} secret(s) - Immediate action required!\n")
            if high:
                f.write(f"🟠 HIGH:     {high} secret(s) - Revoke keys ASAP\n")
            if medium:
                f.write(f"🟡 MEDIUM:   {medium} secret(s) - Review and revoke\n")
            
            f.write("\n")
            f.write("FILES TO REVIEW:\n")
            f.write("-" * 80 + "\n")
            f.write("1. COORDINATES.txt - Exact secret locations\n")
            f.write("2. METADATA.json - Structured data for automation\n")
            f.write("3. Actual files in this directory\n\n")
            
            f.write("IMMEDIATE ACTIONS:\n")
            f.write("-" * 80 + "\n")
            f.write("1. Open COORDINATES.txt to find exact secret locations\n")
            f.write("2. Revoke all active API keys immediately\n")
            f.write("3. Notify repository owner (if authorized)\n")
            f.write("4. Document actions taken\n")
            f.write("5. Update database with remediation status\n\n")
            
            f.write("LEGAL & ETHICAL NOTICE:\n")
            f.write("-" * 80 + "\n")
            f.write("⚠️  This quarantine is part of authorized security research.\n")
            f.write("⚠️  Handle all information responsibly.\n")
            f.write("⚠️  Do not misuse discovered credentials.\n")
            f.write("⚠️  Follow responsible disclosure practices.\n\n")
            
            f.write(f"Scanned by: GitHub Leak Scanner v2.1\n")
            f.write(f"Scan ID: {datetime.now().strftime('%Y%m%d%H%M%S')}\n")
    
    def _log_quarantine(self, repo_name: str, findings: List[Dict]):
        """Log quarantine action to central log file."""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'=' * 80}\n")
            f.write(f"Quarantine: {repo_name}\n")
            f.write(f"Time: {datetime.now().isoformat()}\n")
            f.write(f"Active Secrets: {len(findings)}\n")
            
            for finding in findings:
                f.write(f"  - {finding['secret_type']}: {finding['file_path']}:{finding.get('line_number', '?')}\n")
            
            f.write(f"{'=' * 80}\n")
    
    def get_quarantine_stats(self) -> Dict:
        """Get statistics about quarantined repositories."""
        quarantined_repos = [d for d in self.containment_root.iterdir() if d.is_dir()]
        
        total_secrets = 0
        for repo_dir in quarantined_repos:
            metadata_file = repo_dir / "METADATA.json"
            if metadata_file.exists():
                with open(metadata_file) as f:
                    data = json.load(f)
                    total_secrets += data.get('findings_summary', {}).get('total_active_secrets', 0)
        
        return {
            'total_quarantined_repos': len(quarantined_repos),
            'total_active_secrets': total_secrets,
            'containment_directory': str(self.containment_root)
        }


# ==================== TESTING ====================
if __name__ == "__main__":
    # Test
    system = ContainmentSystem()
    
    # Mock data
    repo_info = {
        'name': 'test-repo',
        'full_name': 'testuser/test-repo',
        'owner': 'testuser',
        'url': 'https://github.com/testuser/test-repo',
        'stars': 5
    }
    
    findings = [
        {
            'secret_type': 'OpenAI API Key',
            'file_path': 'config/settings.py',
            'line_number': 42,
            'validation_status': 'ACTIVE',
            'risk_level': 'CRITICAL',
            'api': 'OpenAI',
            'validation_details': 'Full API access',
            'key_value': 'sk-proj-abc123def456'
        }
    ]
    
    stats = system.get_quarantine_stats()
    print(f"Quarantine stats: {stats}")
