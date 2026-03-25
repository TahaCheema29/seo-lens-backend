
from typing import Any, Dict


def create_response(status: str, message: str, data: Any = None) -> Dict:
    return {"status": status, "message": message, "data": data}
