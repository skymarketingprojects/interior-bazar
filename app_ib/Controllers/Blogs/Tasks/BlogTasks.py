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
                "coverImageUrl": blog_instance.cover_image_url,
                "authorName": blog_instance.author,
                "authorImage": blog_instance.authorImageUrl,
                "publishDate": blog_instance.timestamp.strftime("%d-%m-%Y"),
                "readTime": await MY_METHODS.getReadTime(blog_instance.description.html),
            }
            return blog_data

        except Exception as e:
            #await MY_METHODS.printStatus(f'Error in GetBlogData: {e}')
            return None
        
    @classmethod
    async def GetBlogDetailData(self, blog_instance):
        try:
            if blog_instance is None:
                return None

            blog_data = {
                "id": blog_instance.id,
                "title": blog_instance.title,
                "coverImageUrl": blog_instance.cover_image_url,
                "content": blog_instance.description.html,
                "author": blog_instance.author,
                "timestamp": blog_instance.timestamp,
            }
            return blog_data

        except Exception as e:
            #await MY_METHODS.printStatus(f'Error in GetBlogDetailData: {e}')
            return None