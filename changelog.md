# 📦 SOSS - Changelog

## [1.0.0] - 2025-03-19

### Added
- AES-256 encryption via `cryptography.fernet`
- PBKDF2HMAC with SHA256 and 100,000 iterations
- Master password + wallet-specific password system
- Multi-wallet storage with JSON-based encrypted blobs
- Offline-first operation (no internet usage at all)
- Auto-clearing seed display (auto-wipe screen after 30s)
- Fully portable, runs from flash drives with no traces on host

### Notes
- **Initial stable release**
- Compatible with Python 3.10+
- Supports manual source execution and standalone binary packaging

---

*Stay tuned for more features + UX improvements in future releases!*
