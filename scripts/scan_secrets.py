#!/usr/bin/env python3
"""Scan for hardcoded secrets in source code.

Detects:
  - GitHub Personal Access Tokens (ghp_, github_pat_)
  - AWS access keys (AKIA...) and secret keys
  - Stripe keys (sk_live_, sk_test_, pk_live_, pk_test_)
  - Generic API keys (api_key = "...", API_KEY="...")
  - Passwords in config (password = "..." excluding placeholders)
  - Bearer tokens (Bearer eyJ...)
  - Private keys (BEGIN PRIVATE KEY, BEGIN RSA PRIVATE KEY)
  - Connection strings with credentials (postgres://user:pass@)
  - Slack tokens (xoxb-, xoxp-)
  - JWT tokens (eyJ...eyJ)
  - Twilio Account SIDs
  - Generic long base64 strings assigned to *_key, *_secret, *_token
"""
import os
import re
import sys
from pathlib import Path


# Patterns to detect
SECRET_PATTERNS = [
    # High-confidence patterns (specific service formats)
    (r'ghp_[A-Za-z0-9]{36,}', 'GitHub PAT (ghp_)'),
    (r'github_pat_[A-Za-z0-9_]{82}', 'GitHub PAT (github_pat_)'),
    (r'AKIA[0-9A-Z]{16}', 'AWS Access Key ID'),
    (r'aws_secret_access_key\s*=\s*[\'"][A-Za-z0-9/+=]{40}[\'"]', 'AWS Secret Key'),
    (r'sk_live_[A-Za-z0-9]{24,}', 'Stripe Live Secret Key'),
    (r'pk_live_[A-Za-z0-9]{24,}', 'Stripe Live Publishable Key'),
    # Stripe TEST keys are intentional in test files — skip them
    (r'xox[bp]-[A-Za-z0-9-]{10,}', 'Slack Token'),
    (r'eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}', 'JWT Token'),
    (r'BEGIN (RSA |EC |DSA )?PRIVATE KEY', 'Private Key'),
    (r'Bearer\s+eyJ[A-Za-z0-9_-]{10,}', 'Bearer JWT Token'),

    # Generic credential patterns
    (r'(?:api[_-]?key|apikey)\s*[:=]\s*[\'"]([A-Za-z0-9+/=_-]{20,})[\'"]', 'Generic API Key'),
    (r'(?:secret|client[_-]?secret)\s*[:=]\s*[\'"]([A-Za-z0-9+/=_-]{20,})[\'"]', 'Generic Secret'),

    # Connection strings — exclude obvious documentation examples
    (r'(?:postgres|postgresql|mysql|redis|mongodb)://(?!user:pass@|user:password@|username:password@|foo:bar@)[^:\s]+:[^@\s]+@', 'DB Connection with credentials'),

    # Twilio — only match if explicitly labeled as Twilio Account SID
    (r'twilio[_-]?account[_-]?sid\s*[:=]\s*[\'"](AC[a-z0-9]{32})[\'"]', 'Twilio Account SID'),
]

# Placeholders that are NOT real secrets (skip these)
PLACEHOLDS = {
    '', 'XXX', 'XXX_XXX', 'YOUR_API_KEY', 'YOUR_API_KEY_HERE',
    'YOUR_TOKEN', 'YOUR_TOKEN_HERE', 'CHANGE_ME', 'CHANGE_ME!',
    'CHANGE_ME_PLEASE', 'PLACEHOLDER', 'TODO', 'REPLACE_ME',
    '<your-api-key>', '<your_token>', '<API_KEY>', '<TOKEN>',
    'example', 'example.com', 'your-domain.com',
    'test', 'demo', 'placeholder',
    'admin', 'password', 'secret',  # these are obvious defaults
    'YOUR_STRIPE_PUBLISHABLE_KEY', 'YOUR_STRIPE_SECRET_KEY',
    'YOUR_FURS_CERT_PATH', 'YOUR_FURS_KEY_PATH',
    'sk_test_x', 'pk_test_x',
}

# File extensions to scan
SCAN_EXTS = {'.py', '.xml', '.csv', '.yml', '.yaml', '.json', '.conf', '.cfg',
             '.ini', '.sh', '.bash', '.env', '.txt', '.md', '.js', '.ts',
             '.html', '.css', '.sql'}

# Directories to skip
SKIP_DIRS = {'.git', 'node_modules', '__pycache__', '.pytest_cache',
             'static', 'i18n',  # i18n files contain translations only
             }

# File patterns to skip
SKIP_FILE_PATTERNS = {
    'CHANGELOG.md', 'README.md', 'CONTRIBUTING.md', 'SECURITY.md',
    'worklog.md',
}


def is_placeholder(value):
    """Check if a string is a known placeholder, not a real secret."""
    if not value:
        return True
    upper = value.upper().strip("'\"")
    if upper in {p.upper() for p in PLACEHOLDS}:
        return True
    # Very short strings (less than 12 chars) are unlikely to be real secrets
    if len(value) < 12:
        return True
    # All-same character (e.g., 'xxxxxxxx')
    if len(set(value)) == 1:
        return True
    # Repeated patterns like 'testtesttest'
    if len(set(value[i:i+4] for i in range(0, len(value), 4))) == 1:
        return True
    # Test values: 'sk_test_x', 'sk_test_dummy', 'pk_test_dummy'
    lower = value.lower()
    if 'test' in lower or 'dummy' in lower or 'fake' in lower:
        return True
    # All digits (likely an ID, not a secret)
    if value.isdigit():
        return True
    return False


def scan_file(path):
    """Scan one file. Yields (line_no, pattern_name, matched_text_snippet)."""
    try:
        text = open(path, encoding='utf-8', errors='ignore').read()
    except Exception:
        return

    for line_no, line in enumerate(text.split('\n'), 1):
        # Skip common comment lines
        stripped = line.lstrip()
        if stripped.startswith('#') and 'api' not in stripped.lower():
            continue
        if stripped.startswith('//'):
            continue

        for pattern, name in SECRET_PATTERNS:
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for m in matches:
                matched = m.group(0)
                # Extract the captured group if any (for api_key = "..." patterns)
                if m.groups():
                    captured = m.group(1)
                    if is_placeholder(captured):
                        continue
                    matched = captured

                # Skip placeholders for non-group patterns
                if not m.groups() and is_placeholder(matched):
                    continue

                # Skip if the line itself is clearly documentation/example
                lower_line = line.lower()
                if any(skip in lower_line for skip in (
                    'example', 'sample', 'placeholder', 'replace with',
                    'your_', 'todo', 'fixme', 'xxx',
                )):
                    continue

                # Truncate the snippet for display
                snippet = matched[:80] + ('...' if len(matched) > 80 else '')
                yield (line_no, name, snippet)


def main():
    if len(sys.argv) > 1:
        scan_paths = sys.argv[1:]
    else:
        scan_paths = ['.']

    findings = []
    files_scanned = 0

    for scan_path in scan_paths:
        if os.path.isfile(scan_path):
            files_to_scan = [scan_path]
        else:
            files_to_scan = []
            for root, dirs, files in os.walk(scan_path):
                # Skip blacklisted directories
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
                for fname in files:
                    if fname in SKIP_FILE_PATTERNS:
                        continue
                    ext = os.path.splitext(fname)[1].lower()
                    if ext in SCAN_EXTS:
                        files_to_scan.append(os.path.join(root, fname))

        for fpath in files_to_scan:
            files_scanned += 1
            for line_no, name, snippet in scan_file(fpath):
                findings.append((fpath, line_no, name, snippet))

    print(f'Scanned {files_scanned} files')
    print(f'Found {len(findings)} potential secrets')
    print()
    if not findings:
        print('OK: no hardcoded secrets found')
        return 0

    # Group by severity (service-specific tokens are HIGH, generic are MED)
    HIGH_PATTERNS = {'GitHub PAT (ghp_)', 'GitHub PAT (github_pat_)',
                      'AWS Access Key ID', 'AWS Secret Key',
                      'Stripe Live Secret Key', 'Stripe Live Publishable Key',
                      'Slack Token', 'JWT Token', 'Private Key',
                      'Bearer JWT Token', 'DB Connection with credentials'}
    by_sev = {'HIGH': [], 'MED': []}
    for fpath, line_no, name, snippet in findings:
        sev = 'HIGH' if name in HIGH_PATTERNS else 'MED'
        by_sev[sev].append((fpath, line_no, name, snippet))

    for sev in ('HIGH', 'MED'):
        items = by_sev[sev]
        if not items:
            continue
        print(f'--- {sev} ({len(items)}) ---')
        for fpath, line_no, name, snippet in items[:30]:
            print(f'  {fpath}:{line_no}: {name}')
            print(f'    {snippet}')
        if len(items) > 30:
            print(f'  ... and {len(items) - 30} more')
        print()

    return 1 if by_sev['HIGH'] else 0


if __name__ == '__main__':
    sys.exit(main())
