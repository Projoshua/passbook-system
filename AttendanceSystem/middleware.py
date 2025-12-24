from .storage_backends import set_current_request

class StorageRequestMiddleware:
    """Middleware to make request available to storage backends"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        set_current_request(request)
        response = self.get_response(request)
        return response