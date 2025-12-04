# 🚀 Git Repository Setup Guide

## Suggested Repository Name

**`github-leak-scanner`** or **`repo-secret-hunter`**

Alternatively:
- `api-leak-detector`
- `secret-scanner-auto`
- `gitleaks-automation`


## Step-by-Step Git Setup

### 1. Rename the Folder

```powershell
# Navigate to parent directory
cd a:\projects

# Rename folder
Rename-Item -Path "scan_repos" -NewName "github-leak-scanner"

# Navigate into renamed folder
cd github-leak-scanner
```

### 2. Initialize Git Repository

```powershell
# Initialize git
git init

# Add all files (gitignore will protect .env)
git add .

# Create initial commit
git commit -m "Initial commit: Automated GitHub secret scanner

- Dual-mode support (search/user)
- SQLite database for persistence
- Intelligent repo discovery with priority scoring
- Gitleaks + TruffleHog integration
- Automated scheduling
- Comprehensive logging and reporting"
```

### 3. Create GitHub Repository

**Option A: Via GitHub Web Interface**
1. Go to https://github.com/new
2. Repository name: `github-leak-scanner`
3. Description: "Automated tool to discover and scan GitHub repositories for leaked API keys and secrets"
4. Choose: Public or Private
5. **DO NOT** initialize with README (we already have one)
6. Click "Create repository"

**Option B: Via GitHub CLI (if installed)**
```powershell
gh repo create github-leak-scanner --public --source=. --remote=origin
```

### 4. Push to GitHub

```powershell
# Add remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/github-leak-scanner.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### 5. Verify

```powershell
# Check remote
git remote -v

# Verify gitignore is working
git status  # Should not show .env or .db files
```

---

## ⚠️ Important Pre-Push Checklist

- [ ] Removed all hardcoded tokens/secrets ✅ (already done)
- [ ] `.env` file is in `.gitignore` ✅ (already done)
- [ ] README.md is complete ✅ (already done)
- [ ] No sensitive data in commit history ✅ (fresh repo)
- [ ] `.env.example` has placeholder values only ✅ (already done)

---

## Optional: Add Additional Files

### LICENSE
```powershell
# Create MIT License
@"
MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy...
"@ | Out-File -FilePath LICENSE -Encoding UTF8
```

### CONTRIBUTING.md
Guidelines for contributors (optional)

---

## Quick Commands Summary

```powershell
# Full setup in one go:
cd a:\projects
Rename-Item "scan_repos" "github-leak-scanner"
cd github-leak-scanner

git init
git add .
git commit -m "Initial commit: Automated GitHub secret scanner"

# Then create repo on GitHub and run:
git remote add origin https://github.com/YOUR_USERNAME/github-leak-scanner.git
git branch -M main
git push -u origin main
```

---

## What Will Be Pushed

✅ **Included:**
- All `.py` source files
- `README.md` documentation
- `.env.example` template
- `requirements.txt`
- `.gitignore`
- `gitleaks.exe` (if you want, otherwise add to gitignore)

❌ **Excluded (by .gitignore):**
- `.env` (your secrets)
- `*.db` (database files)
- `scan_results/` (scan output)
- `repos/` (cloned repositories)
- `logs/` (log files)
- `__pycache__/` (Python cache)

---

## Post-Push Steps

1. **Add Repository Topics** (on GitHub):
   - `security`
   - `gitleaks`
   - `api-keys`
   - `secret-scanning`
   - `github-api`
   - `trufflehog`

2. **Add Description**:
   "🔍 Automated tool for discovering GitHub repositories with leaked API keys and secrets using Gitleaks and TruffleHog"

3. **Enable Issues/Discussions** (optional)

4. **Add GitHub Workflow** (optional):
   Create `.github/workflows/test.yml` for automated testing

---

## If You Can't Push (Automated)

Run these commands manually in PowerShell:

```powershell
cd a:\projects

# Rename
Rename-Item "scan_repos" "github-leak-scanner"

cd github-leak-scanner

# Git init
git init
git add .
git commit -m "Initial commit: Automated GitHub secret scanner"

# Then tell me your GitHub username and I'll provide the exact remote URL
```
