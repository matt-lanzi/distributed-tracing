def parse_structured(log):
    def is_full_log(log_dict):
        required = ["system", "checkpoint", "status", "timestamp"]
        return all(key in log_dict for key in required)

    def is_error_log(log_dict):
        required = ["system", "correlation_id", "failure_reason"]
        return all(key in log_dict for key in required)

    if is_full_log(log):
        return {
            "system_id": log.get("system"),
            "checkpoint_id": log.get("checkpoint"),
            "timestamp": log.get("timestamp"),
            "status": log.get("status").upper(),
            "correlation_id": log.get("correlation_id"),
            "failure_reason": log.get("failure_reason")
        }

    if is_error_log(log):
        return {
            "system_id": log.get("system"),
            "correlation_id": log.get("correlation_id"),
            "failure_reason": log.get("failure_reason")
        }

    return None
