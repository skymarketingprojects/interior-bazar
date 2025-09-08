from app_ib.Utils.MyMethods import MY_METHODS
class BLOG_TASK:
    @classmethod
    async def GetBlogData(self, blog_instance):
        try:
            if blog_instance is None:
                return None
            

            blog_data = {
                "id": blog_instance.id,
                "title": blog_instance.title,
                "slug": blog_instance.slug,
                "cover_image_url": blog_instance.cover_image_url,
                "author": blog_instance.author,
                "timestamp": blog_instance.timestamp,
            }
            return blog_data

        except Exception as e:
            print(f'Error in GetBlogData: {e}')
            return None
        
    @classmethod
    async def GetBlogDetailData(self, blog_instance):
        try:
            if blog_instance is None:
                return None

            blog_data = {
                "id": blog_instance.id,
                "title": blog_instance.title,
                "cover_image_url": blog_instance.cover_image_url,
                "content": blog_instance.description.html,
                "author": blog_instance.author,
                "timestamp": blog_instance.timestamp,
            }
            return blog_data

        except Exception as e:
            print(f'Error in GetBlogDetailData: {e}')
            return None