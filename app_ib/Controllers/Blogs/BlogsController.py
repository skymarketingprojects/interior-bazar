from asgiref.sync import sync_to_async
from adrf.decorators import api_view
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.LocalResponse import LocalResponse
from .Tasks.BlogTasks import BLOG_TASK
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from django.core.paginator import Paginator
import asyncio
from app_ib.models import Blog

class BLOG_CONTROLLER:
    @classmethod
    async def GetBlogsPagination(self, page,per_page=2):
        try:

            all_blogs = await sync_to_async(list)(
                Blog.objects.all().order_by("-timestamp")
            )

            # Step 2: Paginate the evaluated list
            paginator = Paginator(all_blogs, per_page)
            page_obj = paginator.get_page(page)

            # Step 3: Gather blog data concurrently
            tasks = [BLOG_TASK.GetBlogData(blog) for blog in page_obj]
            blog_details = await asyncio.gather(*tasks)

            # Step 4: Build and return plain dict response
            blog_data = {
                "blogs": blog_details,
                    "current_page": page_obj.number,
                    "hasNext": page_obj.has_next(),
                    "hasPrevious": page_obj.has_previous(),
                    "totalPages": paginator.num_pages,
                    "totalCount": len(all_blogs),
                    "pageSize": per_page
            }
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
                    'error': str(e)
                })  

    @classmethod
    async def GetAllBlogs(self):
        try:

            all_blogs = await sync_to_async(list)(
                Blog.objects.all().order_by("-timestamp")
            )

            # Step 3: Gather blog data concurrently
            tasks = [BLOG_TASK.GetBlogData(blog) for blog in all_blogs]
            blog_details = await asyncio.gather(*tasks)

            
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
                    'error': str(e)
                })

    @classmethod
    async def GetBlogById(self, id):
        try:

            blog_instance = await sync_to_async(Blog.objects.get)(id=id)
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
                data={"blog":blog_data})

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.blog_fetch_error,
                code=RESPONSE_CODES.error,
                data={
                    'error': str(e)
                })