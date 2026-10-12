# Security policy

## Supported versions

| Version | Supported |
|---|---|
| 1.x | ✅ |

## Reporting a vulnerability

**Please do not open a public issue for security problems.**

Report privately through [GitHub Security Advisories](https://github.com/tanmayai23/README-Editor-skill/security/advisories/new). Include the affected file or script, steps to reproduce, and the impact as you understand it.

You'll get an acknowledgement within 5 business days. With your permission, you'll be credited in the release notes.

## Scope

The scripts read files in the repository you point them at. Only `check_links.py` makes network requests, and only to the URLs already in your README. Nothing uploads your code. Reports about a script reading outside the target directory, executing repository code, or sending data elsewhere are in scope.
