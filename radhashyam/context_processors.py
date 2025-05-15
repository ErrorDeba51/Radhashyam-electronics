# radhashyam/context_processors.py
from django.utils import timezone


def timestamp_context(request):
    return {'TIMESTAMP': int(timezone.now().timestamp())}
