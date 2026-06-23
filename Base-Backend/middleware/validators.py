import re

def validate_aadhaar(aadhaar):
    """Validate Aadhaar number: 12 digits, optional checksum."""
    if not re.match(r'^[0-9]{12}$', aadhaar):
        return False
    # Optional: verify checksum (Verhoeff) - skip for MVP
    return True

def validate_public_id(pid):
    """Validate public ID format: e.g., STU-XXXX, VOL-XXXX, CLG-XXXX."""
    return re.match(r'^(STU|VOL|CLG)-[A-Z0-9]{4}$', pid) is not None

def sanitize_input(text):
    """Basic sanitization to prevent XSS (though Jinja auto-escapes)."""
    # For safety, we can strip tags, but better to rely on escaping.
    return text
