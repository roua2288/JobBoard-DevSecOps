"""Read structured application logs on stdin; emit a security alert for denied access/brute force."""
import json
import sys
for line in sys.stdin:
    start=line.find('{')
    if start<0:continue
    try:record=json.loads(line[start:])
    except ValueError:continue
    if record.get('event') in ('brute_force_detected','access_denied','upload_rejected'):
        print(json.dumps({'alert':'jobboard_suspicious_activity','severity':'high' if record['event']=='brute_force_detected' else 'medium',**record}),flush=True)
