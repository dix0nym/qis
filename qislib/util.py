import re


def clean(str):
    return re.sub(r"\s+", " ", str)


def get_token(html):
    """return regexed token from website source"""
    pattern = r";asi=(.+?)\""
    matches = re.findall(pattern, html)
    return matches[0] if matches else None


def remove_token(str):
    pattern = r';asi=(.+?)\"'
    return re.sub(pattern, ";asi={}", str)


def to_float(data):
    if not data:
        return None
    else:
        return float(data.replace(",", "."))

def get_filename(str):
    filtered_name = "".join( x for x in str if x.isalnum() or x in "._- ")
    return filtered_name.replace(' ', '_')