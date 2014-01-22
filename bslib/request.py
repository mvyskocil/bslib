
from xml.etree import cElementTree as ET
from collections import namedtuple
from functools import partial

def abstract_fromxml(tag_name, mandatory_attrs, attrs, has_comment, cls, root):
    
    if root.tag != tag_name:
        raise ValueError("{} tag expected, got {}".format(tag_name, root.tag))

    kwargs = dict()
    for attr in mandatory_attrs:
        foo = root.get(attr)
        if foo is None:
            raise ValueError("{} attribute missing in tag {}".format(attr, tag_name))
        kwargs[attr] = foo

    for attr in attrs:
        kwargs[attr] = root.get(attr)
    
    if has_comment:
        foo = root.find("comment")
        if foo is None:
            kwargs["comment"] = ""
        else:
            kwargs["comment"] = foo.text.strip()

    return cls(**kwargs)

def make_klass(klass_name, tag_name, fromxml_method, mandatory_attrs, attrs=(), has_comment=False):
    
    attrlist = list(mandatory_attrs)
    if has_comment:
        attrlist.append("comment")
    attrlist.extend(attrs)

    nt = namedtuple(klass_name, ", ".join(attrlist))
    fromxml = partial(fromxml_method, tag_name, mandatory_attrs, attrs, has_comment, nt)
    nt.fromxml = fromxml
    return nt

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
        if root.tag != "action":
            raise ValueError("action tag expected, got {}".format(root.tag))

        if root.get("type") != "submit":
            raise ValueError("only action type='{}' supported".format(cls.action_type))

        foo = root.find("source")
        if foo is None:
            raise ValueError("source sub element expected in action type='submit'")
        source = Source.fromxml(foo)
        
        foo = root.find("target")
        if foo is None:
            raise ValueError("target sub element expected in action type='submit'")
        target = Target.fromxml(foo)

        foo = root.find("acceptinfo")
        if foo is None:
            acceptinfo = None
        else:
            acceptinfo = Acceptinfo.fromxml(foo)

        options = dict()
        foo = root.find("options")
        if foo is not None:
            #TODO
            for attr in ("sourceupdate", "updatelink"):
                bar = foo.find(attr)
                if bar is None:
                    continue
                options = bar.text.strip()

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
        if root.tag != "action":
            raise ValueError("action tag expected, got {}".format(root.tag))

        if root.get("type") != cls.action_type:
            raise ValueError("only action type='{}' supported".format(cls.action_type))

        foo = root.find("target")
        if foo is None:
            raise ValueError("target sub element expected in action type='{}'".format(cls.action_type))
        target = Target.fromxml(foo)

        foo = root.find("person")
        if foo is None:
            person = None
        else:
            person = Person.fromxml(foo)
        
        foo = root.find("group")
        if foo is None:
            group = None
        else:
            group = Group.fromxml(foo)

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
        if root.tag != "action":
            raise ValueError("action tag expected, got {}".format(root.tag))

        if root.get("type") != cls.action_type:
            raise ValueError("only action type='{}' supported".format(cls.action_type))

        foo = root.find("target")
        if foo is None:
            raise ValueError("target sub element expected in action type='{}'".format(cls.action_type))
        target = Target.fromxml(foo)

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
        if root.tag != "action":
            raise ValueError("action tag expected, got {}".format(root.tag))

        if root.get("type") != cls.action_type:
            raise ValueError("only action type='{}' supported".format(cls.action_type))
        
        foo = root.find("source")
        if foo is None:
            raise ValueError("source sub element expected in action type='{}'".format(cls.action_type))
        source = Source.fromxml(foo)

        foo = root.find("target")
        if foo is None:
            raise ValueError("target sub element expected in action type='{}'".format(cls.action_type))
        target = Target.fromxml(foo)

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
        if root.tag != "action":
            raise ValueError("action tag expected, got {}".format(root.tag))

        if root.get("type") != cls.action_type:
            raise ValueError("only action type='{}' supported".format(cls.action_type))
        
        grouped_id = root.get("grouped_id")
        if grouped_id is None:
            raise ValueError("grouped_id attribute is missing in action type='{}'".format(cls.action_type))

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

        if root.tag != "action":
            raise ValueError("action tag expected, got {}".format(root.tag))

        action_type = root.get("type")
        if action_type is None:
            raise ValueError("'type' attribute mandatory for action element")

        if action_type not in cls._type_map:
            raise ValueError("unknown action type='{}'".format(action_type))

        return getattr(
            cls._type_map[action_type],
            "fromxml")(root)

class Request:

    def __init__(self, reqid, title, description, state, accept_at, actions, reviews, history):
        self.reqid = reqid
        self.title = title
        self.description = description
        self.accept_at = accept_at
        self.state = state
        self.actions = actions
        self.reviews = reviews
        self.history = history

    @classmethod
    def fromxml(cls, root):
        """read it from parsed xml"""

        if root.tag != "request":
            raise ValueError("request tag expected, got {}".format(root.tag))

        reqid = root.get("id")
        if not reqid:
            raise ValueError("id attribute missing in tag request")

        def _text(root, tag_name):
            foo = root.find(tag_name)
            if foo is None: return None
            return foo.text.strip()

        title = _text(root, "title")
        description = _text(root, "description")
        accept_at = _text(root, "accept_at")

        state_el = root.find("state")
        if state_el is None:
            raise ValueError("state tag not found!")
        state = RequestState.fromxml(state_el)

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

rq = Request.fromxml(ET.parse("apidocs/api.opensuse.org/apidocs/request.xml").getroot())
