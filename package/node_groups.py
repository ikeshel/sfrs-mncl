"""Node groups shared by the manager windows and their process menus."""

import re

DETECTOR_GROUPS = ("MUSIC", "PLSCI", "SCIFI")
NODE_GROUPS = ("TIMESORTER", *DETECTOR_GROUPS)


def node_group(node):
    """Recognize existing directory/name conventions, including SCIFI3/SCIFI4."""
    for field in ("directory", "node_name"):
        value = node.get(field, "").upper()
        if re.sub(r"[\W_]", "", value) == "TIMESORTER":
            return "TIMESORTER"
        for token in re.split(r"[\W_]+", value):
            for group in DETECTOR_GROUPS:
                if re.fullmatch(rf"{group}\d*", token):
                    return group
    return None
