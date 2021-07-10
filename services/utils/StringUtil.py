from typing import Dict


class StringUtil:

    @classmethod
    def dict_to_str(cls, in_dict: Dict):
        my_str = []
        for key, val in in_dict.items():
            my_str.append('%s: %s ' % (str(key), str(val)))

        return "".join(my_str)
