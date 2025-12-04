# 🔍 Automated Repository Secret Scanner

Automated tool for discovering and scanning GitHub repositories for leaked API keys, tokens, and secrets using **Gitleaks** and **TruffleHog**.

## ✨ Features

- 🔎 **Dual Scanning Modes:**
  - **Search Mode**: Automatically discovers repos with potential leaks across GitHub
  - **User Mode**: Scan specific users or organizations
  
- 🎯 **Smart Prioritization**: Focuses on less popular repos (<50 stars) where leaks are more common

- 💾 **Persistent Tracking**: SQLite database tracks scanned repos and findings to avoid duplicates

- ⏰ **Automated Scheduling**: Run scans automatically at configured intervals

- 📊 **Comprehensive Reporting**: Export findings to JSON and CSV formats

## 🚀 Quick Start

### Prerequisites
### Configuration

Edit `.env` file with your settings:

```env
# Required: Your GitHub token
GITHUB_TOKEN=ghp_your_token_here

# Choose mode: 'search' or 'user'
SCAN_MODE=search

# For search mode: configure filters
MAX_STARS_THRESHOLD=50
MIN_RECENCY_DAYS=180

# For user mode: specify users
GITHUB_USERS=username1,username2
```

### Usage

**Search Mode** (Find repos with potential leaks):
```bash
python scan_repos.py
```

**User Mode** (Scan specific users):
```bash
# Set SCAN_MODE=user in .env
python scan_repos.py
```

**Scheduled Scanning**:
```bash
python scheduler.py
```

## 📋 How It Works

### Search Mode Flow
1. Uses GitHub Search API to find repositories with suspicious files (`.env`, `config.json`, etc.)
2. Filters for less popular repos (low star count) pushed recently
3. Calculates priority score based on:
   - Recency (40%)
   - Unpopularity (40%)
   - File pattern matches (20%)
4. Scans top-priority repos with Gitleaks & TruffleHog
5. Stores findings in database and generates reports

### User Mode Flow
1. Fetches all repositories from specified users/orgs
2. Checks database to skip recently scanned repos
3. Clones and scans each repository
4. Deduplicates findings and tracks history

## 📂 Output

Results are saved in `scan_results/`:
- `findings.json` - Detailed JSON report
- `findings.csv` - CSV format for spreadsheets
- `scans.db` - SQLite database with scan history

## ⚙️ Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `SCAN_MODE` | Mode: `search` or `user` | `search` |
| `MAX_STARS_THRESHOLD` | Max stars for target repos | `50` |
| `MIN_RECENCY_DAYS` | Only scan repos updated in last N days | `180` |
| `SCAN_INTERVAL_HOURS` | Hours between automated scans | `24` |
| `MAX_CONCURRENT_REPOS` | Parallel repo scans | `3` |

See `.env.example` for all options.

## 🔒 Security Best Practices

> [!WARNING]
> **Never commit your `.env` file or GitHub token to version control!**

- Use a token with **minimal permissions** (public_repo only)
- Rotate tokens regularly
- Review findings before sharing
- Be mindful of API rate limits (5,000 requests/hour for authenticated users)

## 📊 Database Schema

The tool tracks:
- **Scanned Users**: Username, last scan date, scan count
- **Repositories**: URL, owner, stars, priority score, last scan
- **Findings**: File path, secret type, hash, first/last seen, status
- **Scan Runs**: Statistics for each scan execution

## 🛠️ Development

### Project Structure
```
scan_repos/
├── scan_repos.py      # Main scanning script
├── search_repos.py    # GitHub repository discovery
├── config.py          # Configuration management
├── database.py        # Database models and operations
├── scheduler.py       # Automated scheduling
├── utils.py           # Helper functions
├── requirements.txt   # Python dependencies
├── .env.example       # Environment template
└── README.md          # This file
```

### Key Modules
- **config.py**: Loads and validates `.env` settings
- **database.py**: SQLAlchemy models for persistence
- **search_repos.py**: GitHub search and prioritization
- **utils.py**: Logging, hashing, rate limit handling

## 🐛 Troubleshooting

**"Authentication failed"**
- Check your `GITHUB_TOKEN` in `.env`
- Ensure token has correct permissions

**"Rate limit exceeded"**
- Wait for rate limit reset (check headers)
- Use authenticated requests (token required)

**"Gitleaks not found"**
- Download from [releases page](https://github.com/gitleaks/gitleaks/releases)
- Update `GITLEAKS_PATH` in `.env`

## 📝 License

This tool is for educational and security research purposes. Always respect repository owners' privacy and GitHub's Terms of Service.

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## ⚠️ Disclaimer

This tool is designed to help identify publicly exposed secrets. Use responsibly and ethically. Do not use for malicious purposes.

---

**Happy hunting! 🕵️‍♂️**
