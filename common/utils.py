def safe_dict_get(data, key, default=None):
    try:
        return data.get(key)
    except Exception:
        return default


def _get_safe(data, *keys):
    for key in keys:
        try:
            data = data[key]
        except (IndexError, TypeError, KeyError):
            return None
    return data
