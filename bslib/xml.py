#encoding: utf-8
from __future__ import print_function
from __future__ import unicode_literals

from collections import namedtuple
from functools import partial

def check_tag_name(root, tag_name):
    if root.tag != tag_name:
        raise ValueError("Invalid element, got '{}', expected '{}'".format(root.tag, tag_name))

def get_attr(root, name, mandatory=True, etag_name=None):
    attr = root.get(name)
    if mandatory and attr is None:
        tn = etag_name if etag_name is not None else root.tag
        raise ValueError("The '{}' attribute is missing in element '{}'".format(name, tn))
    return attr

def get_subtag(root, tag_name, klass, mandatory=True, etag_name=None):
    subtag = root.find(tag_name)
    if mandatory and subtag is None:
        tn = etag_name if etag_name is not None else root.tag
        raise ValueError("target sub element expected in '{}'".format(tn))
    if subtag is None:
        return subtag
    return klass.fromxml(subtag)

def get_text_from_subtag(root, tag_name):
    foo = root.find(tag_name)
    if foo is None or foo.text is None:
        return None
    return foo.text.strip()

def abstract_fromxml(tag_name, mandatory_attrs, attrs, has_comment, cls, root):
    """This is a helper function, which parses sagegiven tag name, check mandatory
    and other attributes and return given cls. API might be considered as awkward,
    but this is abstract function and instances made by functools.partial does
    have only cls and root parameters.

    Usage:
        foo_fromxml = functools.partial(abstract_fromxml, "foo", ("ham", ), ("spam", "spam2"), False)
        ...
        root = xml.find("foo")
        a_foo = foo_fromxml(FooElement, root)
    
    :param tag_name: the tag name of given root element, ValueError error is
                     raised if does not match
    :param mandatory_attrs: list of mandatory attributes, ie if they're not there
                            ValueError is raised
    :param attrs: list of other attributes, defaults to empty list
    :param has_comment: a quirk for elements does have <comment></comment>
                         subelement, defaults to False
    :param cls: class, which __init__ function will be called and which instance
                will be returned
    :param root: root element to be processed

    :return: instance of a ``cls``
    """
    
    check_tag_name(root, tag_name)

    kwargs = dict()
    for name in mandatory_attrs:
        kwargs[name] = get_attr(root, name, mandatory=True)
    
    for name in attrs:
        kwargs[name] = get_attr(root, name, mandatory=False)
    
    if has_comment:
        kwargs["comment"] = get_text_from_subtag(root, "comment")

    return cls(**kwargs)

def make_klass(klass_name, tag_name, fromxml_method, mandatory_attrs, attrs=(), has_comment=False):
    """Constructs a klass (named tuple) with given name
    for specific tag, it does bind an instance of
    ``abstract_fromxml`` to it, so all klasses does
    have fromxml classmethod.
    
    Example:
        #looks a bit like Javascript :)
        FooElement = make_klass("FooElement", "foo", abstract_fromxml, ("ham", ), ("spam", "spam2"), False)
        ...
        root = xml.find("foo")
        a_foo = FooElement.fromxml(root)
        assert a_foo.ham == "ham-attr-value"
    """
    
    attrlist = list(mandatory_attrs)
    if has_comment:
        attrlist.append("comment")
    attrlist.extend(attrs)

    nt = namedtuple(klass_name, ", ".join(attrlist))
    fromxml = partial(fromxml_method, tag_name, mandatory_attrs, attrs, has_comment, nt)
    nt.fromxml = fromxml
    return nt

### REQUEST TAG BEGIN ###

RequestState = make_klass("RequestState",
    tag_name = "state",
    fromxml_method = abstract_fromxml,
    mandatory_attrs = ("name", ),
    attrs = ("who", "when", "superseed"),
    has_comment = True,
    )

RequestReview = make_klass("RequestReview", 
    tag_name = "review",
    fromxml_method = abstract_fromxml,
    mandatory_attrs = ("state", ),
    attrs = ("who", "when", "by_user", "by_group", "by_project", "by_package"),
    has_comment = True,
    )

RequestHistory = make_klass("RequestHistory", 
    tag_name = "history",
    fromxml_method = abstract_fromxml,
    mandatory_attrs = ("name", ),
    attrs = ("who", "when"), 
    has_comment = True,
    )

Source = make_klass("Source",
    tag_name = "source",
    fromxml_method = abstract_fromxml,
    mandatory_attrs = ("project", ),
    attrs = ("package", "rev", ),
    )
Target = make_klass("Target",
    tag_name = "target",
    fromxml_method = abstract_fromxml,
    mandatory_attrs = ("project", ),
    attrs = ("package", )
    )
Acceptinfo = make_klass("Acceptinfo",
    tag_name = "acceptinfo",
    fromxml_method = abstract_fromxml,
    mandatory_attrs = (),
    attrs = ("rev", "srcmd5", "xsrcmd5", "osrcmd5", "oxsrcmd5"),
    )

Person = make_klass("Person",
    tag_name = "person",
    fromxml_method = abstract_fromxml,
    mandatory_attrs = ("name", ),
    attrs = ("role", ),
    )
Group = make_klass("Group",
    tag_name = "group",
    fromxml_method = abstract_fromxml,
    mandatory_attrs = ("name", "role"),
    )

class ActionSubmit:

    action_type = "submit"

    def __init__(self, source, target, acceptinfo, options):
        self.source = source
        self.target = target
        self.acceptinfo = acceptinfo
        self.options = options

    @classmethod
    def fromxml(cls, root):
        
        check_tag_name(root, "action")
        
        tn = "action type=\"{}\"".format(cls.action_type)
 
        if get_attr(root, "type") != cls.action_type:
            raise ValueError("only '{}' supported".format(tn))

        source = get_subtag(root, "source", Source, etag_name=tn)
        target = get_subtag(root, "target", Target, etag_name=tn)
        acceptinfo = get_subtag(root, "acceptinfo", Acceptinfo, mandatory=False)

        options = dict()
        foo = root.find("options")
        if foo is not None:
            #TODO
            for attr in ("sourceupdate", "updatelink"):
                bar = get_text_from_subtag(foo, attr)
                if bar is None:
                    continue
                options[attr] = bar

        return cls(
            source = source,
            target = target,
            acceptinfo = acceptinfo,
            options = options
            )

class ActionAddRole:

    action_type = "add_role"

    def __init__(self, target, person, group):
        self.target = target
        self.person = person
        self.group = group

    @classmethod
    def fromxml(cls, root):
        
        check_tag_name(root, "action")
        
        tn = "action type=\"{}\"".format(cls.action_type)
        
        # this raises ValueError if not exists
        if get_attr(root, "type") != cls.action_type:
            raise ValueError("only '{}' supported".format(tn))

        target = get_subtag(root, "target", Target, etag_name=tn)
        person = get_subtag(root, "person", Person, mandatory=False)
        group  = get_subtag(root, "group", Group, mandatory=False)

        return cls(
            target = target,
            person = person,
            group = group,
            )

class ActionSetBugowner(ActionAddRole):
    action_type = "set_bugowner"

class ActionDelete:

    action_type = "delete"

    def __init__(self, target):
        self.target = target

    @classmethod
    def fromxml(cls, root):
        
        check_tag_name(root, "action")
        
        tn = "action type=\"{}\"".format(cls.action_type)

        target = get_subtag(root, "target", Target, etag_name=tn)

        return cls(
            target = target,
            )

class ActionChangeDevel:

    action_type = "change_devel"

    def __init__(self, source, target):
        self.source = source
        self.target = target

    @classmethod
    def fromxml(cls, root):
        
        check_tag_name(root, "action")
        
        tn = "action type=\"{}\"".format(cls.action_type)
        
        if get_attr(root, "type") != cls.action_type:
            raise ValueError("only '{}' supported".format(tn))

        source = get_subtag(root, "source", Source, etag_name=tn)
        target = get_subtag(root, "target", Target, etag_name=tn)

        return cls(
            source = source,
            target = target,
            )

class ActionMaintenanceIncident(ActionChangeDevel):
    action_type = "maintenance_incident"
class ActionMaintenanceRelease(ActionChangeDevel):
    action_type = "maintenance_release"

class ActionGroup:
    action_type = "group"

    def __init__(self, grouped_id):
        self.grouped_id = grouped_id

    @classmethod
    def fromxml(cls, root):
        
        check_tag_name(root, "action")
        
        tn = "action type=\"{}\"".format(cls.action_type)
        
        if get_attr(root, "type") != cls.action_type:
            raise ValueError("only '{}' supported".format(tn))
        
        grouped_id = get_attr(root, "grouped_id")

        return cls(
            grouped_id = grouped_id)

class RequestAction:

    _type_map = {getattr(klass, "action_type") : klass for klass in 
            (ActionSubmit,
            ActionAddRole,
            ActionSetBugowner,
            ActionMaintenanceRelease,
            ActionMaintenanceIncident,
            ActionDelete,
            ActionChangeDevel,
            ActionGroup)}

    @classmethod
    def fromxml(cls, root):

        check_tag_name(root, "action")

        action_type = get_attr(root, "type")
        
        return getattr(
            cls._type_map[action_type],
            "fromxml")(root)

class Request:

    def __init__(self, reqid, title, description, state, accept_at, actions, reviews, history, diff=None):
        self.reqid = reqid
        self.title = title
        self.description = description
        self.accept_at = accept_at
        self.state = state
        self.actions = actions
        self.reviews = reviews
        self.history = history
        self.diff = diff

    @classmethod
    def fromxml(cls, root):
        """read it from parsed xml"""

        check_tag_name(root, "request")

        reqid = get_attr(root, "id")
        _throw = True
        try:
            reqid = int(reqid)
            _throw = False
        except ValueError:
            pass
        if _throw:
            raise ValueError("numeric reqid attribute expected in element 'request'")# from None

        title = get_text_from_subtag(root, "title")
        description = get_text_from_subtag(root, "description")
        accept_at = get_text_from_subtag(root, "accept_at")

        state = get_subtag(root, "state", RequestState)

        def _list(meth, tag_name):
            return [meth(element) \
                for element in root.findall(tag_name)]

        actions = _list(RequestAction.fromxml, "action")
        reviews = _list(RequestReview.fromxml, "review")
        history = _list(RequestHistory.fromxml, "history")

        return cls(
            reqid = reqid,
            title = title,
            description = description,
            accept_at = accept_at,
            state = state,
            actions = actions,
            reviews = reviews,
            history = history)

### REQUEST TAG END ###

### COLLECTIONS TAG BEGIN ###
class Collection:

    def __init__(self, elements):
        self.elements = elements

    @classmethod
    def fromxml(cls, root):

        check_tag_name(root, "collection")

        matches = get_attr(root, "matches")
        _throw = True
        try:
            matches = int(matches)
            _throw = False
        except ValueError:
            pass
        if _throw:
            raise ValueError("numeric matches attribute expected in element 'collection'")# from None

        xml_elements = [el for el in root]
        if matches != len(xml_elements):
            raise ValueError("'matches' value ({}) is not equal real number of elements ({})".format(matches, len(xml_elements)))

        types = {el.tag for el in xml_elements}
        if len(types) != 1:
            raise ValueError("various types in collection is not supported, {}".format(types))

        typ = types.pop()
        if typ != "request":
            raise NotImplementedError("support for {} is not yet implemented".format(typ))

        return cls(
            elements=[Request.fromxml(el) for el in xml_elements])

    def __len__(self):
        return self.elements.__len__()

    def __iter__(self):
        return self.elements.__iter__()

    def __next__(self):
        return self.elements.__next__()

    def __getitem__(self, idx):
        return self.elements.__getitem__(idx)

### COLLECTIONS TAG END ###

### RESULT AND RESULTLIST TAG BEGIN ###

StatusElement = make_klass("StatusElement",
    tag_name = "status",
    fromxml_method = abstract_fromxml,
    mandatory_attrs = ("package", "code"),
    )

class Result:
    
    def __init__(self, project, repository, arch, code, state, statuslist):
        self.project = project
        self.repository = repository
        self.arch = arch
        self.code = code
        self.state = state
        self.statuslist = statuslist

    @classmethod
    def fromxml(cls, root):
        check_tag_name(root, "result")

        kwargs = {attr: get_attr(root, attr) for attr in ("project", "repository", "arch", "code", "state")}

        kwargs["statuslist"] = [StatusElement.fromxml(el) for el in root]
        return cls(**kwargs)

class ResultList:

    def __init__(self, state, resultlist):
        self.resultlist = resultlist

    @classmethod
    def fromxml(cls, root):
        check_tag_name(root, "resultlist")
        
        state = get_attr(root, "state")
        resultlist = [Result.fromxml(el) for el in root]

        return cls(state = state, resultlist = resultlist)

    def __len__(self):
        return self.resultlist.__len__()

    def __iter__(self):
        return self.resultlist.__iter__()

    def __next__(self):
        return self.resultlist.__next__()

    def __getitem__(self, idx):
        return self.resultlist.__getitem__(idx)


### RESULT AND RESULTLIST TAG END ###
