from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.Names import NAMES
class BLOG_TASK:
    @classmethod
    async def GetBlogData(self, blog_instance):
        try:
            if blog_instance is None:
                return None
            

            blog_data = {
                NAMES.ID: blog_instance.id,
                NAMES.TITLE: blog_instance.title,
                NAMES.SLUG: blog_instance.slug,
                NAMES.COVER_IMAGE_URL: blog_instance.cover_image_url,
                NAMES.AUTHOR_NAME: blog_instance.author,
                NAMES.AUTHOR_IMAGE: blog_instance.authorImageUrl,
                NAMES.PUBLISH_DATE: blog_instance.timestamp.strftime(NAMES.DMY_FORMAT),
                NAMES.READ_TIME: await MY_METHODS.getReadTime(blog_instance.description.html),
            }
            return blog_data

        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in GetBlogData: {e}')
            return None
        
    @classmethod
    async def GetBlogDetailData(self, blog_instance):
        try:
            if blog_instance is None:
                return None

            blog_data = {
                NAMES.ID: blog_instance.id,
                NAMES.TITLE: blog_instance.title,
                NAMES.COVER_IMAGE_URL: blog_instance.cover_image_url,
                NAMES.CONTENT: blog_instance.description.html,
                NAMES.AUTHOR: blog_instance.author,
                NAMES.AUTHOR_IMAGE: blog_instance.authorImageUrl,
                NAMES.PUBLISH_DATE: blog_instance.timestamp.strftime(NAMES.DMY_FORMAT),
                NAMES.READ_TIME: await MY_METHODS.getReadTime(blog_instance.description.html),
            }
            return blog_data

        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in GetBlogDetailData: {e}')
            return None