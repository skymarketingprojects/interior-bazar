from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from app_ib.models import Blog,Business
from interior_products.models import Product,Service,Catelogue 
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
            # 'seller_buyer',
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
            'cookie-policy',
            'marketplace',
            'marketBusiness',
            'marketCatalogue',
            'marketService',
            'marketProduct',
            'legal',
            'payment',

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

class BusinessProfileSitemap(Sitemap):
    def items(self):
        return Business.objects.all()

    def location(self, obj:Business):
        return f'/b/{slugify(obj.businessName, obj.id)}/profile'

    def lastmod(self, obj):
        return obj.updatedAt

    def changefreq(self, obj):
        return 'weekly'
    

class BusinessCatalogueSitemap(Sitemap):
    def items(self):
        return Business.objects.all()

    def location(self, obj:Business):
        return f'/b/{slugify(obj.businessName, obj.id)}/catalogue'

    def lastmod(self, obj):
        return obj.updatedAt

    def changefreq(self, obj):
        return 'weekly'
    

class BusinessProductSitemap(Sitemap):
    def items(self):
        return Business.objects.all()

    def location(self, obj:Business):
        return f'/b/{slugify(obj.businessName, obj.id)}/product'

    def lastmod(self, obj:Business):
        return obj.updatedAt

    def changefreq(self, obj):
        return 'weekly'
    

class BusinessServiceSitemap(Sitemap):
    def items(self):
        return Business.objects.all()

    def location(self, obj:Business):
        return f'/b/{slugify(obj.businessName, obj.id)}/service'

    def lastmod(self, obj):
        return obj.updatedAt

    def changefreq(self, obj):
        return 'weekly'
    

class ContactSitemap(Sitemap):
    def items(self):
        return Business.objects.all()

    def location(self, obj:Business):
        return f'/b/{slugify(obj.businessName, obj.id)}/contact'

    def lastmod(self, obj):
        return obj.updatedAt

    def changefreq(self, obj):
        return 'weekly'

class ProductSitemap(Sitemap):
    def items(self):
        return Product.objects.all()

    def location(self, obj:Product):
        return f'/marketplace/product/{slugify(obj.title, obj.id)}/'

    def lastmod(self, obj:Product):
        return obj.updatedAt

    def changefreq(self, obj):
        return 'weekly'
    

class ServiceSitemap(Sitemap):
    def items(self):
        return Service.objects.all()

    def location(self, obj:Service):
        return f'/marketplace/service/{slugify(obj.title, obj.id)}/'

    def lastmod(self, obj:Service):
        return obj.updatedAt

    def changefreq(self, obj):
        return 'weekly'

class CatalogueSitemap(Sitemap):
    def items(self):
        return Catelogue.objects.all()

    def location(self, obj:Catelogue):
        return f'/marketplace/catalogue/{slugify(obj.title, obj.id)}/'

    def lastmod(self, obj:Catelogue):
        return obj.updatedAt

    def changefreq(self, obj):
        return 'weekly'