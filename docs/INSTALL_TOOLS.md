# 🔧 Installing External Tools

The scanner requires two external tools for secret detection. These are **NOT included** in the repository and must be downloaded separately.

## Required Tools

### 1. **Gitleaks** (Required)
Scans git repositories for leaked secrets.

**Download:**
- Windows: https://github.com/gitleaks/gitleaks/releases/latest
- Download `gitleaks_x.x.x_windows_x64.tar.gz`
- Extract `gitleaks.exe` to project root

**Or via PowerShell:**
```powershell
# Download latest release
Invoke-WebRequest -Uri "https://github.com/gitleaks/gitleaks/releases/download/v8.18.0/gitleaks_8.18.0_windows_x64.zip" -OutFile "gitleaks.zip"
Expand-Archive gitleaks.zip -DestinationPath .
Move-Item gitleaks.exe .
Remove-Item gitleaks.zip
```

### 2. **TruffleHog** (Optional)
Additional secret scanner for comprehensive detection.

**Install via pip:**
```bash
pip install trufflehog
```

**Or download binary:**
- https://github.com/trufflesecurity/trufflehog/releases/latest

---

## Configuration

Update `.env` with tool paths:

```env
# Tool paths
GITLEAKS_PATH=gitleaks.exe
TRUFFLEHOG_PATH=trufflehog  # or path to binary
```

---

## Verify Installation

```bash
# Test gitleaks
gitleaks.exe version

# Test trufflehog
trufflehog --version
```

---

## Why Tools Are Not Included

1. **Large file size** - Gitleaks.exe is ~22MB
2. **Platform-specific** - Different binaries for Windows/Mac/Linux  
3. **License compliance** - Separate licenses
4. **Security** - Avoid false-positive secret detection in binaries
5. **Updates** - Users can download latest versions

---

## Troubleshooting

**"gitleaks.exe not found":**
- Download from link above
- Place in project root
- Update `GITLEAKS_PATH` in `.env`

**"Permission denied":**
```bash
chmod +x gitleaks  # Linux/Mac only
```

**Alternative locations:**
If tools are in PATH, update `.env`:
```env
GITLEAKS_PATH=gitleaks     # Uses system PATH
TRUFFLEHOG_PATH=trufflehog
```
