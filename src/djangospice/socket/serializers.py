import json
import uuid
from datetime import date
from datetime import datetime


class SmartJSONEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return super().default(obj)


def dumps(data):
    return json.dumps(data, cls=SmartJSONEncoder,)