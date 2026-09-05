import uuid


def generate_request_id() -> str:
    return str(uuid.uuid4())


def generate_trace_id() -> str:
    return uuid.uuid4().hex
