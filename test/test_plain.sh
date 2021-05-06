curl -X POST "http://localhost:8888/transcribe" -H "accept: text/plain" -H "Content-Type: multipart/form-data" -F "file=@bonjour.wav;type=audio/wav"
