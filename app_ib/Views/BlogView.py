import asyncio
from django.http import JsonResponse
from asgiref.sync import sync_to_async
from adrf.decorators import api_view
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated

from app_ib.Controllers.Blogs.BlogsController import BLOG_CONTROLLER

@api_view(['GET'])
async def GetBlogsPaginationView(request,page):
    try:
        blogs_resp = await asyncio.gather(BLOG_CONTROLLER.GetBlogsPagination(page=page, per_page=3))
        blogs_resp = blogs_resp[0]

        return ServerResponse(
            response=blogs_resp.response,
            code=blogs_resp.code,
            message=blogs_resp.message,
            data=blogs_resp.data)

    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.blog_fetch_error,
            code=RESPONSE_CODES.error,
            data={
                'error': str(e)
            })
@api_view(['GET'])
async def GetAllBlogsView(request):
    try:

        blogs_resp = await asyncio.gather(BLOG_CONTROLLER.GetAllBlogs())
        blogs_resp = blogs_resp[0]

        return ServerResponse(
            response=blogs_resp.response,
            code=blogs_resp.code,
            message=blogs_resp.message,
            data=blogs_resp.data)

    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.blog_fetch_error,
            code=RESPONSE_CODES.error,
            data={
                'error': str(e)
            })
@api_view(['GET'])
async def GetBlogByIdView(request,id):
    try:

        blog_resp = await asyncio.gather(BLOG_CONTROLLER.GetBlogById(id=id))
        blog_resp = blog_resp[0]

        return ServerResponse(
            response=blog_resp.response,
            code=blog_resp.code,
            message=blog_resp.message,
            data=blog_resp.data)

    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.blog_fetch_error,
            code=RESPONSE_CODES.error,
            data={
                'error': str(e)
            })