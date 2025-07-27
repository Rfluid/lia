def remove_none_values(obj: dict) -> dict:
    """Recursively removes None values from a dictionary."""
    return {
        k: remove_none_values(v) if isinstance(v, dict) else v
        for k, v in obj.items()
        if v is not None
    }
