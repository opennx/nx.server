def textify(text):
    """ 
    Creates valid unicode string from anything (TODO: eventually should create....)
    """
    try:
        text = unicode(text)
    except:
        pass
    return text
