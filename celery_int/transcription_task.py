import os
import requests
import json
from celery_int.celeryapp import celery

@celery.task(name="transcribe_task", bind=True)
def transcribe_task(self, file_name, output_format):
    """ transcribe_task do a synchronous call to the transcribe worker API """
    headers={"accept": "text/plain" if output_format == "raw" else "application/json"}
    try:
        file_content = open(os.path.join("/opt/audio",file_name), 'rb').read()
    except Exception as e:
        raise Exception("Could not open ressource {}".format(file_name))
    result = requests.post("http://localhost:80/transcribe", headers=headers, files={'file' : file_content})
    if result.status_code == 200:
        if output_format != "raw":
            return json.loads(result.text)
        return result.text
    else:
        raise Exception(result.text)