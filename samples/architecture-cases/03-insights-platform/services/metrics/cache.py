import json
from redis import Redis
class MetricsCache:
    def __init__(self):
        self.client = Redis.from_url('redis://redis:6379/0')
    def store(self, key: str, value: dict):
        self.client.setex(key, 300, json.dumps(value))
