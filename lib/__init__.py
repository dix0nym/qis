import re

def get_token(html):
    """return regexed token from website source"""
    pattern = r";asi=(.+?)\""
    matches = re.findall(pattern, html)
    return matches[0] if matches else None

def clean(str):
    pattern = r"\s+"
    return re.sub(pattern, " ", str)
