import requests
import json
from celery_int.celeryapp import celery

@celery.task(name="transcribe_task", bind=True)
def transcribe_task(self, file_path, output_format):
    """ transcribe_task do a synchronous call to the transcribe worker API """
    headers={"accept": "text/plain" if output_format == "raw" else "application/json"}
    result = requests.post("localhost", headers=headers, files={'file' : open(file_path, 'rb').read()})
    if result.status_code == 200:
        if output_format != "raw":
            return json.loads(result.text)
        return result.text
    else:
        raise Exception(result.text)