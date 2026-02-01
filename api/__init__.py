# -*- coding: utf-8 -*-
"""
Módulo de API.
"""

from api.endpoints import Endpoints, VehicleType
from api.fipe_client import FipeClient, FipeClientError, FipeRateLimitError, FipeRequestError

__all__ = [
    "Endpoints",
    "VehicleType",
    "FipeClient",
    "FipeClientError",
    "FipeRateLimitError",
    "FipeRequestError"
]
