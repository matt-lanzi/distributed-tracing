import re

def parse_cmf(line):
    def is_main_log(text):
        return "CMF:" in text and "CMF_ERROR:" not in text

    def is_error_log(text):
        return "CMF_ERROR:" in text and "ID:" in text


    if is_main_log(line):
        match = re.search(
            r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}) CMF: (\S+) - (\S+) \(ID: ([^)]+)\)',
            line
        )
        if match:
            timestamp, checkpoint, status, correlation_id = match.groups()
            return {
                "system_id": "cmf",
                "checkpoint_id": checkpoint,
                "timestamp": timestamp,
                "status": status.upper(),
                "correlation_id": correlation_id,
                "failure_reason": None
            }

    if is_error_log(line):
        match = re.search(
            r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}) CMF CMF_ERROR: \(ID: ([^)]+)\) - (.+)',
            line
        )
        if match:
            timestamp, correlation_id, failure_reason = match.groups()
            return {
                "system_id": "cmf",
                "correlation_id": correlation_id,
                "failure_reason": failure_reason,
                "timestamp": timestamp 
            }

    return None
