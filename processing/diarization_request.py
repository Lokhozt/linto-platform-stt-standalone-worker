import os
import requests

def checkDiarizationService():
    ''' Check if the diarization service is up and running '''
    pass


class SpeakerDiarizationRequest:
    ''' Speaker Diarization Request class managed request to the Speaker Diarization Service '''
    def __init__(self):
        self.SPEAKER_DIARIZATION_ISON = False
        self.SPEAKER_DIARIZATION_HOST = None
        self.SPEAKER_DIARIZATION_PORT = None
        self.url = None
        self.log = logging.getLogger(
            "__stt-standelone-worker__.SpeakerDiarization")
        logging.basicConfig(level=logging.INFO)

    def setParam(self, SPEAKER_DIARIZATION_ISON):
        self.SPEAKER_DIARIZATION_ISON = SPEAKER_DIARIZATION_ISON
        if self.SPEAKER_DIARIZATION_ISON:
            self.SPEAKER_DIARIZATION_HOST = os.environ['SPEAKER_DIARIZATION_HOST']
            self.SPEAKER_DIARIZATION_PORT = os.environ['SPEAKER_DIARIZATION_PORT']
            self.url = "http://"+self.SPEAKER_DIARIZATION_HOST + \
                ":"+self.SPEAKER_DIARIZATION_PORT+"/"
        self.log.info(self.url) if self.url is not None else self.log.warn(
            "The Speaker Diarization service is not running!")

    def get(self, file):
        try:
            if self.SPEAKER_DIARIZATION_ISON:
                result = requests.post(self.url, files={'file': file})
                if result.status_code != 200:
                    raise ValueError(result.text)

                speakers = json.loads(result.text)
                speakers = speakers["segments"]

                last_spk = {
                    'seg_begin': speakers[len(speakers) - 1]["seg_end"] + 10,
                    'seg_end': -1,
                    'spk_id': -1,
                    'seg_id': -1,
                }
                speakers.append(last_spk)
                
                return speakers
            else:
                raise ValueError('Service is OFF')
        except Exception as e:
            self.log.error(str(e))
            return None
        except ValueError as error:
            self.log.error(str(error))
            return None