import mitmproxy.http
from mitmproxy import ctx

class Intercept:
    def request(self, flow: mitmproxy.http.HTTPFlow) -> None:
        ctx.log.info(f"Intercepted request: {flow.request.method} {flow.request.pretty_url}")
        # You can modify requests here

    def response(self, flow: mitmproxy.http.HTTPFlow) -> None:
        ctx.log.info(f"Intercepted response: {flow.response.status_code} {flow.request.pretty_url}")
        # You can modify responses here

addons = [Intercept()]
