import asyncio
from django.http import JsonResponse
from asgiref.sync import sync_to_async
from adrf.decorators import api_view
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.Names import NAMES
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated

from app_ib.Controllers.Blogs.BlogsController import BLOG_CONTROLLER
from django.core.cache import cache

cache_get = sync_to_async(cache.get)
cache_set = sync_to_async(cache.set)
@api_view(['GET'])
async def GetBlogsPaginationView(request,page):
    try:
        # Cache for paginated blogs (TTL: 30 minutes)
        cache_key = f"cache:blog:pagination:{page}"
        cached_data = await cache_get(cache_key)

        if cached_data:
            return ServerResponse(
                response=cached_data['response'],
                code=cached_data['code'],
                message=cached_data['message'],
                data=cached_data['data']
            )

        blogs_resp = await asyncio.gather(BLOG_CONTROLLER.GetBlogsPagination(page=page, per_page=3))
        blogs_resp = blogs_resp[0]

        cache_data = {
            'response': blogs_resp.response,
            'code': blogs_resp.code,
            'message': blogs_resp.message,
            'data': blogs_resp.data
        }
        await cache_set(cache_key, cache_data, timeout=1800) # 30 mins TTL

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
                NAMES.ERROR: str(e)
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
                NAMES.ERROR: str(e)
            })
@api_view(['GET'])
async def GetBlogByIdView(request,id):
    try:

        # Global Cache for specific blog (TTL: 24 hours)
        cache_key = f"cache:blog:{id}"
        cached_data = await cache_get(cache_key)

        if cached_data:
            return ServerResponse(
                response=cached_data['response'],
                code=cached_data['code'],
                message=cached_data['message'],
                data=cached_data['data']
            )

        blog_resp = await asyncio.gather(BLOG_CONTROLLER.GetBlogById(id=id))
        blog_resp = blog_resp[0]

        cache_data = {
            'response': blog_resp.response,
            'code': blog_resp.code,
            'message': blog_resp.message,
            'data': blog_resp.data
        }
        await cache_set(cache_key, cache_data, timeout=86400) # 24 hours TTL

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
                NAMES.ERROR: str(e)
            })