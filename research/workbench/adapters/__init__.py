"""Adapters for extracting and normalizing upstream acupuncture and anatomical data."""
from .base import BaseAdapter, NormalizedMeridian, NormalizedPoint
from .jicio_adapter import JICioAdapter
from .meridian_studio_adapter import MeridianStudioAdapter
from .tcm_acupoints_adapter import TCMAcupointsAdapter
from .watercmy_adapter import WaterCMYAdapter

__all__ = [
    "BaseAdapter",
    "NormalizedPoint",
    "NormalizedMeridian",
    "JICioAdapter",
    "MeridianStudioAdapter",
    "WaterCMYAdapter",
    "TCMAcupointsAdapter",
]
