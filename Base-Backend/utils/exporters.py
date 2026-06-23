import csv
import json
from io import StringIO

def export_csv(data, headers=None):
    """Generate CSV string from list of dicts."""
    if not data:
        return ''
    if headers is None:
        headers = list(data[0].keys())
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    writer.writerows(data)
    return output.getvalue()

def export_json(data):
    return json.dumps(data, default=str, indent=2)
