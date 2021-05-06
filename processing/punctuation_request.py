import requests

def checkPunctuationService(diarization_host: str, diarization_port: int, inferface: str = "/healthcheck") -> bool:
    """ Check if the diarization service is up and running """
    url = "http://{}:{}{}".format(diarization_host, diarization_port, inferface)
    try:
        response = requests.get(url)
    except Exception as e:
        return False
    return response.status_code == 200


def punctuation_request(punctuation_host: str, punctuation_port: int, text, interface:str = "/"):
    """ Call the punctuation service """
    url = "http://{}:{}{}".format(punctuation_host, punctuation_port, inferface)
    if isinstance(text, dict):
        if isinstance(text['text'], list):
            text_punc = []
            for utterance in text['text']:
                data = utterance.split(':')
                result = requests.post(self.url, data=data[1].strip().encode('utf-8'), headers={'content-type': 'application/octet-stream'})
                if result.status_code != 200:
                    raise ValueError(result.text)
                
                text_punc.append(data[0]+": "+result.text.encode('latin-1').decode('utf-8'))
            text['text'] = text_punc
        else:
            result = requests.post(self.url, data=text['text'].strip().encode('utf-8'), headers={'content-type': 'application/octet-stream'})
            text['text'] = result.text.encode('latin-1').decode('utf-8')
        return text
    else:
        result = requests.post(self.url, data=text.encode('utf-8'), headers={'content-type': 'application/octet-stream'})
        if result.status_code != 200:
            raise ValueError(result.text.encode('latin-1').decode('utf-8'))

        return result.text