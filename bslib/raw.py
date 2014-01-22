#
# bslib - raw api access 
#

"""
This module provides raw access to Open Build Service API.

The raw means ugly, low level and to be used with a care. All it does is to
define functions and arguments needed for accessing various BS API calls. It is
worth to mention that no function does do any argument checking except quoting
(see api wrapper for details).

The advantage of having such low-level acces is the flexibility for testing and
to allow to easy adapt on future OBS API changes.
"""

from functools import wraps

from .utils import is_url, inspect_signature, apply_urltemplate

def raw(ctx, method, apiurl, url, datafp=None):
    """Do the raw http method call. Having both apiurl and url seems to be
    awkard, but actually it saves us from calling urlsplit on url. Plus all
    callers does have apiurl."""
    
    #TODO: we need a real debugging
    print("DEBUG: {} {}".format(method, url))
    opener = ctx.opener(apiurl)
    if method == "GET":
        resp = opener.open(url)
        if resp.getcode() != 200:
            raise NotImplementedError("non 200 responses are not yet implemented")
    elif method == "POST":
        resp = opener.open(url, data=datafp.read() if datafp is not None else None)
        if resp.getcode() != 200:
            raise NotImplementedError("non 200 responses are not yet implemented")
    elif method in ("PUT", "DELETE"):
        raise NotImplementedError("HTTP method '{}' is not yet implemented".format(method))
    else:
        raise ValueError("HTTP method '{}' is not known".format(method))

    return resp

def api(template):
    """This is quite magic decorator (but which one does not?), thus is worth
    to explain a bit more.
    
    It need a template or url as an argument
        'GET {apiurl}/some/{parametrized}/path?followed={by}&query={string}'

    where format arguments are read from underlying function signature. Which
    would look like

    def some_cool_name(context, apiurl, parametrized, by="by", string="arguments"): pass

    for POST requests, template does look like
        'POST(comment) {apiurl}/some/{path}'
        def some_other_name(context, apiurl, path, comment): pass

    where comment is a parameter containing file-like object, which will be
    passed to POST request. For POST requests without any data, simple POST or POST()
    would be acceptable.

    Function must have at least two arguments - context and apiurl, the rest is
    optional. It does ignore empty (or None) parts of query string.

    returns: filelike object with a response
    """
    def inner(func):
        @wraps(func)
        def wrapper(*args, **kwargs):

            if len(args) < 2:
                raise ValueError("arguments context and apiurl are mandatory")
            
            method, utemplate = template.split(' ', 1)
            post_variable_name = None
            if method[:4] == "POST":
                try:
                    method, post_variable_name = method.split("(")
                    post_variable_name = post_variable_name[:-1]
                except ValueError:
                    post_variable_name = None
            elif method not in ("GET", "PUT", "DELETE"):
                raise ValueError("invalid HTTP method {}".format(method))

            dct = {p: df for p, hd, df in inspect_signature(func) if hd == True}
            dct.update(zip(func.__code__.co_varnames[2:func.__code__.co_argcount], args[2:]))
            dct.update(kwargs)
            
            dct["ctx"] = args[1]
            dct["apiurl"] = args[1]

            url = apply_urltemplate(utemplate.replace("{apiurl}", dct["apiurl"]), dct)
            if not is_url(url):
                raise ValueError("invalid url {}".format(url))
            return raw(dct['ctx'], method, dct['apiurl'], url, datafp=dct.get(post_variable_name))
        return wrapper
    return inner

@api("GET {apiurl}/request/{reqid}")
def GET_request_id(ctx, apiurl, reqid):
    """show info for given request id, returns xml"""
    pass

@api("POST {apiurl}/request/{reqid}?cmd=diff")
def POST_request_id_cmddiff(ctx, apiurl, reqid):
    """show the diff of given request id, returns plain text"""
    pass

@api("POST(comment) {apiurl}/request/{reqid}?cmd={cmd}&newstate={newstate}&by_group={by_group}")
def POST_request(ctx, apiurl, reqid, comment, cmd="", newstate="", by_group=""):
    """change the state of reqid to newstate
    
    TBD: document allowed arguments for newstate and cmd
    cmd=changereviewstate&newstate=(accepted|declined) --> accept/decline the review
    """
    pass

@api("GET {apiurl}/build/{project}/_result?package={package}")
def GET_build_project_result(ctx, apiurl, project, package="package"):
    """show the build results of given project/package, returns plain text(?)"""
    pass

