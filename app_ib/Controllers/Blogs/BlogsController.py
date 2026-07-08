from asgiref.sync import sync_to_async
from adrf.decorators import api_view
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.Names import NAMES
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.LocalResponse import LocalResponse
from .Tasks.BlogTasks import BLOG_TASK
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from django.core.paginator import Paginator
import asyncio
from django.core.cache import cache
from app_ib.models import Blog

class BLOG_CONTROLLER:
    @classmethod
    async def GetBlogsPagination(self, page, per_page=2):
        cache_key = f"blogs_pagination_{page}_{per_page}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return LocalResponse(
                code=RESPONSE_CODES.success,
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.blog_fetch_success,
                data=cached_data)

        try:
            all_blogs = await sync_to_async(list)(
                Blog.objects.filter(status='published').order_by(f'-{NAMES.TIMESTAMP}')
            )

            # Step 2: Paginate the evaluated list
            paginator = Paginator(all_blogs, per_page)
            page_obj = paginator.get_page(page)

            # Step 3: Gather blog data concurrently
            tasks = [BLOG_TASK.GetBlogData(blog) for blog in page_obj]
            blog_details = await asyncio.gather(*tasks)

            # Step 4: Build and return plain dict response
            blog_data = {
                NAMES.BLOGS: blog_details,
                NAMES.CURRENT_PAGE: page_obj.number,
                NAMES.HAS_NEXT: page_obj.has_next(),
                NAMES.HAS_PREVIOUS: page_obj.has_previous(),
                NAMES.TOTAL_PAGES: paginator.num_pages,
                NAMES.TOTAL_COUNT: len(all_blogs),
                NAMES.PAGE_SIZE: per_page
            }
            
            # Cache the result for 1 hour
            cache.set(cache_key, blog_data, 3600)
            
            return LocalResponse(
                code=RESPONSE_CODES.success,
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.blog_fetch_success,
                data=blog_data)

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.blog_fetch_error,
                code=RESPONSE_CODES.error,
                data={
                    NAMES.ERROR: str(e)
                })  

    @classmethod
    async def GetAllBlogs(self):
        cache_key = "all_blogs_list"
        cached_data = cache.get(cache_key)
        if cached_data:
            return LocalResponse(
                code=RESPONSE_CODES.success,
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.blog_fetch_success,
                data=cached_data)

        try:
            all_blogs = await sync_to_async(list)(
                Blog.objects.filter(status='published').order_by(f'-{NAMES.TIMESTAMP}')
            )

            # Step 3: Gather blog data concurrently
            tasks = [BLOG_TASK.GetBlogData(blog) for blog in all_blogs]
            blog_details = await asyncio.gather(*tasks)
            
            # Cache for 1 hour
            cache.set(cache_key, blog_details, 3600)

            return LocalResponse(
                code=RESPONSE_CODES.success,
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.blog_fetch_success,
                data=blog_details)

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.blog_fetch_error,
                code=RESPONSE_CODES.error,
                data={
                    NAMES.ERROR: str(e)
                })


    @classmethod
    async def GetBlogById(self, id):
        try:

            # Public detail is published-only — a draft must 404 for anon visitors.
            blog_instance = await Blog.objects.filter(id=id, status='published').afirst()
            if blog_instance is None:
                return LocalResponse(
                    code=RESPONSE_CODES.error,
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.blog_fetch_error,
                    data={})

            blog_data = await BLOG_TASK.GetBlogDetailData(blog_instance)
            return LocalResponse(
                code=RESPONSE_CODES.success,
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.blog_fetch_success,
                data={NAMES.BLOG:blog_data})

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.blog_fetch_error,
                code=RESPONSE_CODES.error,
                data={
                    NAMES.ERROR: str(e)
                })