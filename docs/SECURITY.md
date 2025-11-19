# Documentation Viewer Security Measures

This document outlines the security measures implemented in the documentation viewer system to protect against common web vulnerabilities.

## Overview

The documentation viewer implements multiple layers of security to ensure safe rendering and navigation of markdown documentation files. All security measures align with **Requirement 1.3** from the requirements document.

## Security Measures Implemented

### 1. Path Traversal Prevention

**Threat**: Attackers could attempt to access files outside the documentation directory using path traversal techniques (e.g., `../../etc/passwd`).

**Mitigations**:

#### In `views.py` - `validate_doc_path()` function:
- Removes null bytes from paths
- Rejects absolute paths (both Unix `/` and Windows `C:` style)
- Blocks paths containing `..` (parent directory references)
- Validates characters (only alphanumeric, hyphens, underscores, slashes, dots)
- Prevents access to hidden files/folders (starting with `.`)
- Logs all rejected path attempts with user information

#### In `markdown_processor.py` - `render()` method:
- Validates file exists before processing
- Uses `Path.resolve().relative_to()` to ensure file is within `base_path`
- Rejects any file outside the documentation directory
- Logs path traversal attempts

#### In `navigation.py` - `_scan_directory()` method:
- Validates each directory is within `base_path` before scanning
- Skips symlinks to prevent following links outside documentation
- Validates each file/folder before adding to TOC
- Recursive validation at every level

#### In `utils.py` - `search_documentation()` function:
- Skips symlinks during search
- Validates each file is within `base_path` before reading
- Prevents search from accessing files outside documentation

### 2. Input Sanitization

**Threat**: Malicious input in search queries or file paths could lead to injection attacks or unexpected behavior.

**Mitigations**:

#### Search Query Sanitization (`utils.py` - `sanitize_search_query()`):
- Strips leading/trailing whitespace
- Limits query length to 200 characters (configurable)
- Removes null bytes and control characters
- Preserves only printable characters and basic whitespace
- Applied before any search processing

#### Path Validation (`views.py` - `validate_doc_path()`):
- Comprehensive validation as described in Path Traversal Prevention
- Sanitizes path before any file system operations
- Returns sanitized path for safe use

### 3. XSS (Cross-Site Scripting) Prevention

**Threat**: Malicious markdown content could inject JavaScript or HTML that executes in users' browsers.

**Mitigations**:

#### HTML Sanitization (`markdown_processor.py` - `_sanitize_html()`):
- Uses `bleach` library for robust HTML sanitization
- Whitelist approach: Only allows safe HTML tags and attributes
- Allowed tags: Standard markdown output (headings, paragraphs, lists, tables, code, etc.)
- Allowed attributes: Only safe attributes (href, src, class, id, etc.)
- Allowed protocols: Only http, https, mailto, ftp
- Strips disallowed tags rather than escaping (cleaner output)
- Linkifies plain URLs safely (skips code blocks)
- Fallback to full HTML escaping if sanitization fails

#### Search Result Highlighting (`utils.py` - `highlight_search_term()`):
- Escapes all HTML in text before highlighting
- Uses Django's `escape()` function
- Only then adds safe `<mark>` tags for highlighting
- Prevents injection through search terms

#### Template Auto-Escaping:
- Django templates auto-escape all variables by default
- Only uses `|safe` filter on sanitized HTML from markdown processor
- Search highlights are marked safe only after HTML escaping

### 4. CSRF (Cross-Site Request Forgery) Protection

**Implementation**:

#### Search Form:
- Uses GET method (standard for search, no state changes)
- GET requests are not subject to CSRF in Django
- No sensitive operations performed via search
- Read-only operation (no data modification)

**Note**: If POST methods are added in the future for any documentation operations, Django's CSRF middleware will automatically protect them when `{% csrf_token %}` is included in forms.

### 5. Authentication and Authorization

**Mitigations**:

#### Access Control:
- All documentation views require authentication (`LoginRequiredMixin`)
- Only authenticated users can access documentation
- Aligns with Requirement 1.3 (accessible to authenticated users)
- Django's session management handles authentication securely

#### No Authorization Bypass:
- No direct file access endpoints
- All access goes through validated view layer
- No user-controllable file paths in URLs without validation

### 6. Logging and Monitoring

**Security Logging**:

#### Comprehensive Logging:
- All path validation failures logged with user information
- Path traversal attempts logged with ERROR level
- Invalid path attempts logged with WARNING level
- Search queries logged for audit trail
- Error IDs generated for tracking security incidents

#### Log Information Includes:
- Username of requester
- Attempted path or query
- Timestamp
- Request path
- Error ID for correlation

### 7. Secure File Operations

**Mitigations**:

#### File Reading:
- Always uses context managers (`with` statements)
- Proper exception handling for file operations
- UTF-8 encoding explicitly specified
- No user-controllable file operations

#### Symlink Protection:
- Skips symlinks in directory scanning
- Skips symlinks in search operations
- Prevents following links outside documentation directory

### 8. Caching Security

**Considerations**:

#### Cache Keys:
- Include file modification time in cache keys
- Prevents serving stale content
- Cache keys are hashed (MD5) to prevent injection

#### Cache Invalidation:
- Automatic invalidation on file modification
- Manual invalidation available if needed
- No user-controllable cache operations

## Security Testing Checklist

- [x] Path traversal attempts blocked (../, ../../, etc.)
- [x] Absolute path attempts blocked (/etc/passwd, C:\Windows\, etc.)
- [x] Hidden file access blocked (.env, .git, etc.)
- [x] Null byte injection blocked
- [x] Symlink traversal blocked
- [x] XSS in markdown content prevented
- [x] XSS in search results prevented
- [x] Search query injection prevented
- [x] Authentication required for all views
- [x] Path validation logging enabled
- [x] Error handling doesn't leak sensitive info

## Dependencies

### Security-Related Libraries:

- **bleach**: HTML sanitization (XSS prevention)
  - Version: Latest stable
  - Purpose: Whitelist-based HTML cleaning
  - Configuration: Custom tag/attribute whitelist

- **Django**: Web framework with built-in security
  - CSRF protection (middleware)
  - SQL injection prevention (ORM)
  - XSS prevention (template auto-escaping)
  - Session security

- **markdown**: Markdown to HTML conversion
  - Safe extensions only
  - No user-controllable extension loading

## Security Best Practices

### For Developers:

1. **Never bypass validation**: Always use `validate_doc_path()` before file operations
2. **Never use `|safe` without sanitization**: Only mark HTML safe after bleach processing
3. **Log security events**: Use appropriate log levels for security-related events
4. **Test with malicious input**: Always test with path traversal and XSS payloads
5. **Keep dependencies updated**: Regularly update bleach and other security libraries

### For Administrators:

1. **Monitor logs**: Watch for repeated path traversal attempts
2. **Review access patterns**: Unusual search patterns may indicate reconnaissance
3. **Keep documentation directory secure**: Proper file permissions on docs/user-guide
4. **Regular security audits**: Periodically review security logs
5. **Update dependencies**: Keep Django and security libraries up to date

## Incident Response

If a security issue is discovered:

1. **Log the incident**: Capture all relevant information
2. **Assess impact**: Determine what data/files were accessed
3. **Patch immediately**: Fix the vulnerability
4. **Review logs**: Check for exploitation attempts
5. **Update documentation**: Document the issue and fix

## Future Enhancements

Potential security improvements for future versions:

- Rate limiting on search queries
- Content Security Policy (CSP) headers
- Subresource Integrity (SRI) for external resources
- Security headers (X-Frame-Options, X-Content-Type-Options, etc.)
- Automated security scanning in CI/CD
- Penetration testing

## References

- OWASP Top 10: https://owasp.org/www-project-top-ten/
- Django Security: https://docs.djangoproject.com/en/stable/topics/security/
- Bleach Documentation: https://bleach.readthedocs.io/
- Path Traversal: https://owasp.org/www-community/attacks/Path_Traversal
- XSS Prevention: https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html

## Contact

For security concerns or to report vulnerabilities, contact the development team immediately.
