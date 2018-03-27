"""
Module to do diff on running and candidate
"""
SAME = 'same'
MOVED = 'moved'
ADDED = 'added'
REMOVED = 'removed'
CHANGED = 'changed'


def get_element_path(element):
    """
    Take an element as input and gives back
    the path
    e.g. <vr><vrId>1</vrId><vrId>2</vrId></vr>
    for <vrId>1</vrId> element '/vr/vrId[1]'
    will be returned
    Args:
       element: lxml.Element

    Returns: String e.g. '/vr/vrId[1]'
   """
    return element.getroottree().getpath(element)
