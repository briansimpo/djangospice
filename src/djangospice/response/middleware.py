from djangospice.response.response import Response
from djangospice.response.shortcuts import render_response


class ResponseMiddleware:

    def __call__(self, request):
        response = self.get_response(request)

        if isinstance(response, Response):
            return render_response(response, request)
        return response