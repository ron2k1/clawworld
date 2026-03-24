import os

# Disable rate limiting in tests so rapid-fire messages aren't rejected.
os.environ.setdefault("CLAWWORLD_RATE_LIMIT", "0")
