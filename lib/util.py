import re

def clean(str):
    return re.sub(r"\s+", " ", str)
    
def get_token(html):
    """return regexed token from website source"""
    pattern = r";asi=(.+?)\""
    matches = re.findall(pattern, html)
    return matches[0] if matches else None