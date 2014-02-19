#encoding: utf-8

# high level api for bslib
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

from collections import namedtuple

from xml.etree import cElementTree as ET
from .raw import GET_request_id, POST_request_id_cmddiff, GET_build_project_result, GET_build_project_package_buildlog, GET_request_collection, GET_comments_request
from .xml import Request, ResultList, Collection, Comments

def get_request(ctx, reqid, diff=False, comments=False):

    resp = GET_request_id(ctx, reqid)
    if diff:
        resp_d = POST_request_id_cmddiff(ctx, reqid)
    if comments:
        resp_c = GET_comments_request(ctx, reqid)

    request = Request.fromxml(
        ET.fromstring(resp.read()))
    if diff:
        request.diff = resp_d.readlines()

    if comments:
        request.comments = Comments.fromxml(
            ET.fromstring(resp_c.read()))

    return request

def get_package_result(ctx, project, package):

    resp = GET_build_project_result(ctx, project, package)
    return ResultList.fromxml(ET.fromstring(resp.read()))

def get_package_buildlog(ctx, project, package, repository, arch):
    
    resp = GET_build_project_package_buildlog(
        ctx, project, package, repository, arch)
    return resp.read()

def get_package_rpmlint(ctx, project, package, repository, arch):
    
    resp = GET_build_project_package_file(
        ctx, project, package, repository, arch, "rpmlint.log")
    return resp.read()

def get_package_statistics(ctx, project, package, repository, arch):
    
    resp = GET_build_project_package_file(
        ctx, project, package, repository, arch, "statistics")
    return resp.read()

MyWorkTuple = namedtuple("MyWorkTuple", "reviews, outgoing, declined")
def get_my_work(ctx, maintenance=False):
    
    if maintenance:
        raise NotImplementedError("maintenance incidents are not yet supported")

    user = ctx.config.user
    #GET https://api.opensuse.org/search/package?match=%28%5Bkind%3D%27patchinfo%27+and+issue%2F%5B%40state%3D%27OPEN%27+and+owner%2F%40login%3D%27mvyskocil%27%5D%5

    # get open reviews
    resp = GET_request_collection(ctx, states="review", user=user, roles="reviewer", reviewstates="new")
    reviews = Collection.fromxml(ET.fromstring(resp.read()))

    # get new (outgoing?) things
    resp = GET_request_collection(ctx, states="new", user=user, roles="maintainer")
    outgoing = Collection.fromxml(ET.fromstring(resp.read()))

    # get declined things
    resp = GET_request_collection(ctx, states="declined", user=user, roles="creator")
    declined = Collection.fromxml(ET.fromstring(resp.read()))

    return MyWorkTuple(reviews, outgoing, declined)
