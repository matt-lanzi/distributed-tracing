import re

def parse_bcis(line):
    def is_valid_bcis_log(text):
        return "BCIS:" in text and "ID:" in text

    if not is_valid_bcis_log(line):
        return None

    match = re.search(
        r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}) BCIS: (\S+) - (\S+) \(ID: ([^)]+)\)(?: - (.+))?',
        line
    )

    if match:
        timestamp, checkpoint, status, correlation_id, failure_reason = match.groups()
        return {
            "system_id": "bcis",
            "checkpoint_id": checkpoint,
            "timestamp": timestamp,
            "status": status.upper(),
            "correlation_id": correlation_id,
            "failure_reason": failure_reason
        }

    return None
