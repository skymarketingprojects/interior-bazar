from django.shortcuts import render
from django.http import HttpResponse
def render_index(request, page_name):
    return render(request, 'index.html', {'page_name': page_name})

# Individual views
def seller_buyer(request):
    return render_index(request, 'seller_buyer')

def blog(request):
    return render_index(request, 'blog')

def blog_detail(request, slug):
    return render_index(request, f'blog_detail:{slug}')

def plan(request):
    return render_index(request, 'plan')

def faqs(request):
    return render_index(request, 'faqs')

def disclaimer(request):
    return render_index(request, 'disclaimer')

def return_and_refund_policy(request):
    return render_index(request, 'return_and_refund_policy')

def terms_and_conditions(request):
    return render_index(request, 'terms_and_conditions')

def privacy_policy(request):
    return render_index(request, 'privacy_policy')

def sign_up(request):
    return render_index(request, 'sign_up')

def sign_in(request):
    return render_index(request, 'sign_in')

def contact_us(request):
    return render_index(request, 'contact_us')


def robots_txt(request):
    lines = [
        "User-Agent: *",
        "Allow: /",
        "Sitemap: https://interiorbazzar.com/sitemap.xml"
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

