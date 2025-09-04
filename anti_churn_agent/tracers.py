"""
Simple tracers module for generating trace IDs
"""

import time
import uuid

def make_trace_id(prefix: str = "trace") -> str:
    """Generate a unique trace ID with timestamp"""
    timestamp = int(time.time())
    unique_id = str(uuid.uuid4())[:8]
    return f"trace_{prefix}_{timestamp}_{unique_id}"
