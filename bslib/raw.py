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

def raw(ctx, method, url, datafp=None):
    """Do the raw http method call on url."""
    
    #TODO: we need a real debugging
    print("DEBUG: {} {}".format(method, url))
    if method == "GET":
        resp = ctx.opener.open(url)
        if resp.getcode() != 200:
            raise NotImplementedError("non 200 responses are not yet implemented")
    elif method == "POST":
        resp = ctx.opener.open(url, data=datafp.read() if datafp is not None else None)
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

    def some_cool_name(context, parametrized, by="by", string="arguments"): pass

    for POST requests, template does look like
        'POST(comment) {apiurl}/some/{path}'
        def some_other_name(context, apiurl, path, comment): pass

    where comment is a parameter containing file-like object, which will be
    passed to POST request. For POST requests without any data, simple POST or POST()
    would be acceptable.

    Function must have at least context parameter, the rest is
    optional. It does ignore empty (or None) parts of query string.

    returns: filelike object with a response
    """
    def inner(func):
        @wraps(func)
        def wrapper(*args, **kwargs):

            if len(args) < 1:
                raise ValueError("context parameter is mandatory")
            
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
            dct.update(zip(func.__code__.co_varnames[1:func.__code__.co_argcount], args[1:]))
            dct.update(kwargs)
            
            dct["ctx"] = args[0]
            apiurl = dct["ctx"].apiurl

            url = apply_urltemplate(utemplate.replace("{apiurl}", apiurl), dct)
            if not is_url(url):
                raise ValueError("invalid url {}".format(url))
            return raw(dct['ctx'], method, url, datafp=dct.get(post_variable_name))
        return wrapper
    return inner

@api("GET {apiurl}/request/{reqid}")
def GET_request_id(ctx, reqid):
    """show info for given request id, returns xml"""
    pass

@api("GET {apiurl}/request/?view=collection&user={user}&project={project}&package={package}&states={states}&types={types}&roles={roles}")
def GET_request_collection(ctx, user="", project="", package="", states="", types="", roles=""):
    """
user: filter for given user, includes all target projects and packages where
the user is maintainer and also open review requests
project: limit to result to defined target project or review requests
package: limit to result to defined target package or review requests
states: filter for given request state, multiple matches can be added as comma seperated list (eg states=new,review)
types: filter for given action types (comma seperated)
roles: filter for given roles (creator, maintainer, reviewer, source or target)
    """
    pass

@api("POST {apiurl}/request/{reqid}?cmd=diff")
def POST_request_id_cmddiff(ctx, reqid):
    """show the diff of given request id, returns plain text"""
    pass

@api("POST(comment) {apiurl}/request/{reqid}?cmd={cmd}&newstate={newstate}&by_group={by_group}")
def POST_request(ctx, reqid, comment, cmd="", newstate="", by_group=""):
    """change the state of reqid to newstate
    
    TBD: document allowed arguments for newstate and cmd
    cmd=changereviewstate&newstate=(accepted|declined) --> accept/decline the review
    """
    pass

@api("GET {apiurl}/build/{project}/_result?package={package}")
def GET_build_project_result(ctx, project, package="package"):
    """returns the build results of given project/package"""
    pass

#TBD: maybe needs more logic with offsets ...
@api("GET {apiurl}/build/{project}/{package}/{repository}/{arch}/_log?start=0&nostream=1")
def GET_build_project_package_buildlog(ctx, project, package, repository, arch):
    """returns the build log of given project/package/repository/arch"""
    pass

@api("GET {apiurl}/build/{project}/{package}/{repository}/{arch}/{file}")
def GET_build_project_package_file(ctx, project, package, repository, arch, file):
    """returns the build-related file of given project/package/repository/arch"""
    pass

