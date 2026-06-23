import random
import string

def generate_public_id(prefix):
    """Generate a public ID like STU-XXXX."""
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{prefix}-{suffix}"
