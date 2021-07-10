from typing import Dict, Any


class DictUtil:
    @classmethod
    def remove_key(cls, d: Dict, key: Any):
        r = dict(d)
        if key in r:
            del r[key]
        return r
