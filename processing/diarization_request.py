import os
import io
import requests
import json

def checkDiarizationService(diarization_host: str, diarization_port: int, inferface: str = "/healthcheck") -> bool:
    """ Check if the diarization service is up and running """
    url = "http://{}:{}{}".format(diarization_host, diarization_port, inferface)
    try:
        response = requests.get(url)
    except Exception as e:
        return False
    return response.status_code == 200


def diarization_request(diarization_host: str, diarization_port: int, file_buffer, response_holder, interface:str = "/"):
    """ Call the diarization service """
    url = "http://{}:{}{}".format(diarization_host, diarization_port, interface)
    file_buffer_io = io.BytesIO(file_buffer)
    try:
        result = requests.post(url, files={'file' : file_buffer_io})
    except Exception as e:
        raise Exception("Failed to reach the diarization server: {}".format(str(e)))
    if result.status_code != 200:
        raise Exception(result.text)
    
    # Response processing
    content = json.loads(result.text)
    speakers = content["segments"]

    last_spk = {
        'seg_begin': speakers[len(speakers) - 1]["seg_end"] + 10,
        'seg_end': -1,
        'spk_id': -1,
        'seg_id': -1,
    }
    speakers.append(last_spk)
    response_holder[0] = speakers
    