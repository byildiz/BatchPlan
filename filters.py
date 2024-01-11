def in_list(ls, el):
    return any([el.is_a(e) for e in ls])


def default_filter():
    ls = ("IfcSite", "IfcSpace", "IfcOpeningElement")

    def fn(el):
        return el.is_a("IfcProduct") and (el.Representation is not None) and (not in_list(ls, el))

    return fn
