from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag(takes_context=True)
def media_url(context, file_field):
    """Generate media URL using current request host"""
    if not file_field:
        return ''
    
    request = context.get('request')
    url = file_field.url
    
    if request and url:
        # Get current host
        host = request.get_host()
        host_without_port = host.split(':')[0]
        
        # Replace MinIO internal references with current host
        url = url.replace('minio:9000', f'{host_without_port}:9000')
        url = url.replace('localhost:9000', f'{host_without_port}:9000')
        url = url.replace('192.168.1.13:9000', f'{host_without_port}:9000')
        url = url.replace('102.34.17.131:9000', f'{host_without_port}:9000')
    
    return url