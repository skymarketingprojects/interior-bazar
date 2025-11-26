from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from app_ib.models import Blog
import re

def slugify(title: str, id: str | int) -> str:
    slug = title.lower()
    slug = slug.replace(' ', '-')
    slug = re.sub(r'[^\w-]+', '', slug)  # remove all non-word and non-hyphen characters
    return f"{slug}-{id}"

class StaticPageSitemap(Sitemap):
    def items(self):
        return [
            'home',
            'seller_buyer',
            'blog',
            'plan',
            'faqs',
            'disclaimer',
            'return_and_refund_policy',
            'terms_and_conditions',
            'privacy_policy',
            'sign_up',
            'sign_in',
            'contact_us',
        ]

    def location(self, item):
        # Use the current site's domain
        return f'{reverse(item)}'


class BlogPostSitemap(Sitemap):
    def items(self):
        return Blog.objects.all()

    def location(self, obj):
        return f'/blog/{slugify(obj.title, obj.id)}/'

    def lastmod(self, obj):
        return obj.updatedAt

    def changefreq(self, obj):
        return 'weekly'
