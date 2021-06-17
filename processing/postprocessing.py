import re
import json

def clean_text(text):
    ''' Remove extra symbols '''
    text = re.sub(r"<unk>", "", text)  # remove <unk> symbol
    text = re.sub(r"#nonterm:[^ ]* ", "", text)  # remove entity's mark
    text = re.sub(r"' ", "'", text)  # remove space after quote '
    text = re.sub(r" +", " ", text)  # remove multiple spaces
    text = text.strip()
    return text

def prepare_response(transcription: dict, confidence: float, join_metadata: bool):
    """ Prepare response from transcription. """
    res_meta = {"text": "", "confidence-score": "", "words" : []}

    if transcription is not None:
        transcription_content = json.loads(transcription)
        res_meta['confidence-score'] = confidence
        if not join_metadata:
            # Raw format return text only
            return clean_text(transcription_content["text"])
        res_meta["text"] = transcription_content["text"]
        if 'words' in transcription_content:
            res_meta["words"] = transcription_content["words"]
            
    return res_meta

# return a json object including word-data, speaker-data
def process_output(data, spkrs):
    try:
        speakers = []
        text = []
        i = 0
        text_ = ""
        words = []

        for word in data['words']:
            if len(spkrs) == i+1:
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
                    str(spkrs[i]["spk_id"])+' : ' + clean_text(text_))
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
                    ' : ' + clean_text(text_))
        speakers.append(speaker)

        return {'speakers': speakers, 'text': text, 'confidence-score': data['conf']}
    except Exception as e:
        log.error(e)
        return {'text': data['text'], 'words': data['words'], 'confidence-score': data['conf'], 'spks': []}