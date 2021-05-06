curl -X POST "http://192.168.0.17:8888/transcribe" -H "accept: application/json" -H "Content-Type: multipart/form-data" -F "file=@bonjour.wav;type=audio/wav"
