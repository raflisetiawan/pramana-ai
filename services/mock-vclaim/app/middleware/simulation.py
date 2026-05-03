"""
Pramana AI — Mock Simulation Middleware.

Applies artificial delays and simulated errors based on mock state.
"""
import asyncio
import json
import random

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.helpers import error_response
from app.mock_state import state


class SimulationMiddleware(BaseHTTPMiddleware):
    """Applies configured mock behaviors (delay, error, timeout)."""

    async def dispatch(self, request: Request, call_next):
        # Skip control endpoints, docs, and health
        path = request.url.path
        if path.startswith("/vclaim/v2/_mock") or path in {"/docs", "/redoc", "/openapi.json", "/health"}:
            return await call_next(request)

        # 1. Apply timeout simulation
        if state.simulate_timeout:
            await asyncio.sleep(30)  # Sleep long enough to trigger client timeout
            return JSONResponse(status_code=504, content={"message": "Gateway Timeout Simulation"})

        # 2. Apply response delay
        if state.response_delay_ms > 0:
            await asyncio.sleep(state.response_delay_ms / 1000.0)

        # 3. Apply force error on specific NOKA
        # (Very basic extraction, we might need to parse body or path)
        body = b""
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
            # Need to put body back so downstream can read it
            async def receive():
                return {"type": "http.request", "body": body}
            request._receive = receive

        forced_error = False
        if state.force_error_on_noka:
            # Check path
            for noka in state.force_error_on_noka:
                if noka in path:
                    forced_error = True
                    break
            
            # Check body
            if not forced_error and body:
                try:
                    json_body = json.loads(body)
                    if json_body.get("noKartu") in state.force_error_on_noka:
                        forced_error = True
                except json.JSONDecodeError:
                    pass
                    
        if forced_error:
            return JSONResponse(
                status_code=500,
                content=error_response("500", "Simulated Internal Server Error for NOKA")
            )

        # 4. Apply random error rate
        if state.error_rate > 0:
            if random.random() < state.error_rate:
                return JSONResponse(
                    status_code=500,
                    content=error_response("500", "Simulated Random Internal Server Error")
                )

        # Continue normally
        response = await call_next(request)
        return response
