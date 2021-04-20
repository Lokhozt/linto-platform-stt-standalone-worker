import re

def parse_text(self, text):
    ''' Remove extra symbols '''
    text = re.sub(r"<unk>", "", text)  # remove <unk> symbol
    text = re.sub(r"#nonterm:[^ ]* ", "", text)  # remove entity's mark
    text = re.sub(r"' ", "'", text)  # remove space after quote '
    text = re.sub(r" +", " ", text)  # remove multiple spaces
    text = text.strip()
    return text

# Postprocess response
def get_response(self, dataJson, speakers, confidence, is_metadata):
    if dataJson is not None:
        data = json.loads(dataJson)
        data['conf'] = confidence
        if not is_metadata:
            text = data['text']  # get text from response
            return self.parse_text(text)

        elif 'words' in data:
            if speakers is not None:
                # Generate final output data
                return self.process_output(data, speakers)
            else:
                return {'speakers': [], 'text': data['text'], 'confidence-score': data['conf'], 'words': data['words']}

        elif 'text' in data:
            return {'speakers': [], 'text': data['text'], 'confidence-score': data['conf'], 'words': []}
        else:
            return {'speakers': [], 'text': '', 'confidence-score': 0, 'words': []}
    else:
        return {'speakers': [], 'text': '', 'confidence-score': 0, 'words': []}

# return a json object including word-data, speaker-data
def process_output(self, data, spkrs):
    try:
        speakers = []
        text = []
        i = 0
        text_ = ""
        words = []

        for word in data['words']:
            if i+1 == len(spkrs):
                continue
            if i+1 < len(spkrs) and word["end"] < spkrs[i+1]["seg_begin"]:
                text_ += word["word"] + " "
                words.append(word)
            elif len(words) != 0:
                speaker = {}
                speaker["start"] = words[0]["start"]
                speaker["end"] = words[len(words)-1]["end"]
                speaker["speaker_id"] = str(spkrs[i]["spk_id"])
                speaker["words"] = words

                text.append(
                    str(spkrs[i]["spk_id"])+' : ' + self.parse_text(text_))
                speakers.append(speaker)

                words = [word]
                text_ = word["word"] + " "
                i += 1
            else:
                words = [word]
                text_ = word["word"] + " "
                i += 1

        speaker = {}
        speaker["start"] = words[0]["start"]
        speaker["end"] = words[len(words)-1]["end"]
        speaker["speaker_id"] = str(spkrs[i]["spk_id"])
        speaker["words"] = words

        text.append(str(spkrs[i]["spk_id"]) +
                    ' : ' + self.parse_text(text_))
        speakers.append(speaker)

        return {'speakers': speakers, 'text': text, 'confidence-score': data['conf']}
    except Exception as e:
        self.log.error(e)
        return {'text': data['text'], 'words': data['words'], 'confidence-score': data['conf'], 'spks': []}