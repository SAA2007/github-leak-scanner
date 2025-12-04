# 📝 CHANGELOG

## Version 2.0.0 - Phase 2 Improvements (2025-12-04)

### ✨ New Features

**Error Handling & Reliability**
- Added retry decorator with exponential backoff for API calls
- Implemented custom exceptions (`NetworkError`, `RateLimitError`)
- Enhanced GitHub API response handling
- Graceful error recovery and logging

**Progress Indicators**
- Integrated `tqdm` progress bars for real-time scan feedback
- Live status updates during repository scanning
- Display of current repository being processed
- Real-time finding counts in progress bar

**Improved Logging**
- Separated logging into three files:
  - `scanner.log` - Main log (INFO and above)
  - `debug.log` - All debug messages
  - `error.log` - Errors only
- Enhanced log formatting with filename and line numbers
- Better structured logging for troubleshooting

### 🔧 Improvements

**Database**
- Fixed `ScannedUser` model to correctly track scan dates
- Improved deduplication logic
- Better session management

**Code Quality**
- Removed duplicate imports
- Fixed indentation issues
- Improved error messages
- Added comprehensive test coverage

### 🧪 Testing

- Core scanner tests: 8/8 passing (100%)
- Error handling tests: 4/4 passing (100%)
- Progress indicator tests: 3/3 passing (100%)
- Total test coverage significantly improved

### 📚 Documentation

- Created Phase 2 roadmap with future features
- Updated README with new features
- Added comprehensive error handling documentation

---

## Version 1.0.0 - Initial Release (2025-12-04)

### Core Features

**Dual-Mode Scanning**
- Search mode: Auto-discover repositories with potential leaks
- User mode: Scan specific GitHub users/organizations

**Database Persistence**
- SQLite database for tracking scans
- Deduplication of findings
- Scan history tracking

**Intelligence Features**
- Priority scoring for repositories
- Rate limit handling
- Automated scheduling support

**Security**
- Removed hardcoded credentials
- Environment-based configuration
- Comprehensive `.gitignore`

**Tools Integration**
- Gitleaks support
- TruffleHog support
- JSON/CSV report generation
