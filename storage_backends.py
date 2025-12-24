from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings
import threading

# Thread-local storage for request context
_thread_locals = threading.local()

def set_current_request(request):
    """Store the current request in thread-local storage"""
    _thread_locals.request = request

def get_current_request():
    """Retrieve the current request from thread-local storage"""
    return getattr(_thread_locals, 'request', None)


class DynamicDomainS3Storage(S3Boto3Storage):
    """S3 storage that uses the current request's host for URL generation"""
    
    def url(self, name, parameters=None, expire=None, http_method=None):
        # Get the base URL from parent
        url = super().url(name, parameters, expire, http_method)
        
        # Get current request
        request = get_current_request()
        
        if request:
            # Use the host from the current request
            host = request.get_host()
            
            # Extract just the domain/IP without port from MinIO URL
            if '://' in url:
                protocol, rest = url.split('://', 1)
                if '/' in rest:
                    old_domain, path = rest.split('/', 1)
                    # Replace with current host + MinIO port
                    host_without_port = host.split(':')[0]
                    new_url = f"{protocol}://{host_without_port}:9000/{path}"
                    return new_url
        
        return url