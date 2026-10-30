# Security Policy

## Reporting Security Issues

We take the security and privacy of Typing Buddy very seriously.

If you believe you have discovered a vulnerability, security flaw, or privacy leak in this project, **please do not report it in a public GitHub issue**.

Instead, please report security issues through **GitHub Private Vulnerability Reporting** on the repository page:
1. Navigate to the repository's **Security** tab (`https://github.com/harshverse-svg/typing-buddy/security`).
2. Under "Reporting a vulnerability", click **Report a vulnerability**.
3. Provide a clear description, reproduction steps, and the affected version.

You will receive an initial response within 48 hours.

---

## Security Model & Design Principles

Typing Buddy adheres to the following principles:

1. **Zero Network Connectivity:** The application runtime does not open sockets, make HTTP requests, or send external telemetry.
2. **Volatile Memory Only:** Typed input is never persisted to disk or logs. The rolling sentence tracker is capped at 300 characters in RAM and flushed on cursor motion, window change, or click.
3. **No Elevation Required:** Typing Buddy runs with standard user privileges. It never requires Administrator rights (`runas`).
4. **Transparent Source Code:** Distributed as readable Python source rather than opaque packaged executables, allowing straightforward auditing.

---

## Known Boundaries & Recommendations

- **Password Field Detection:** Typing Buddy queries the Windows UI Automation (UIA) API for password elements. Because some web browsers and custom Electron applications do not report this attribute reliably, users should:
  - Add sensitive applications or browsers to `"blocked_apps"` in `%APPDATA%\typing-buddy\settings.json`.
  - Use the manual pause key (default `Pause` key) whenever typing credentials or sensitive tokens.
- **Administrator Windows:** Windows integrity levels prevent standard-user applications from intercepting keystrokes inside elevated (`Run as Administrator`) windows. This is expected Windows security behavior.
