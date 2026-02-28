from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
import os

APP_NAME = os.getenv("APP_NAME", "mini-rag")

# define metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total_HTTP Requests', ['method', 'endpoint', 'status', 'app'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP Request latency', ['method', 'endpoint', 'app'])

class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        start_time = time.time()

        # process the request
        response = await call_next(request)

        # record metrics after the request is processed
        duration = time.time() - start_time
        endpoint = request.url.path

        REQUEST_LATENCY.labels(method=request.method, endpoint=endpoint, app=APP_NAME).observe(duration)
        REQUEST_COUNT.labels(method=request.method, endpoint=endpoint, status=response.status_code, app=APP_NAME).inc()

        return response

def setup_metrics(app: FastAPI):
    app.add_middleware(PrometheusMiddleware)

    @app.get("/iwan_1177", include_in_schema=False)
    def metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

