#!/usr/bin/env python3

import os
from time import gmtime, strftime
import timeit
import threading

import argparse
import logging

from flask import Flask, request, abort, Response, json
from gevent.pywsgi import WSGIServer

from processing import prepare, loadModel, decode, formatAudio
from processing import setupSwaggerUI

app = Flask("__stt-standalone-worker__")

logging.basicConfig(format='%(asctime)s %(name)s %(levelname)s: %(message)s', datefmt='%d/%m/%Y %H:%M:%S')
logger = logging.getLogger("__stt-standalone-worker__")

@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    logger.info("Received healthcheck request")
    return "1", 200

@app.route('/transcribe', methods=['POST'])
def transcribe():
    try:
        logger.info('Transcribe request received')

        # get response content type
        if request.headers.get('accept').lower() == 'application/json':
            join_metadata = True
        elif request.headers.get('accept').lower() == 'text/plain':
            join_metadata = False
        else:
            raise ValueError('Not accepted header')

        # get input file
        if 'file' in request.files.keys():
            file_buffer = request.files['file']
            audio_data = worker.formatAudio(file_buffer)
            
            # Diarization request is done on a separate thread.
            if join_metadata:
                spk_result = [None]
                spk_thread = threading.Thread(target=speakerdiarization.get, args=[file_buffer, spk_result], daemon=True) # Check file format
                start_t = timeit.timeit()
                spk_thread.start()

            # Transcription
            result, confidence = decode(join_metadata)
            logger.debug("Transcription complete (t={}s)".format(timeit.timeit() - start_t))
            logger.debug("Waiting for diarization")

            if join_metadata:            
                spk_thread.join()

            #Postprocessing
            logger.debug("Postprocessing ...")
            trans = worker.get_response(result, spk_result[0], confidence, join_metadata)
            logger.debug("... Complete")
            response = punctuation.get(trans)
            worker.clean()
        else:
            raise ValueError('No audio file was uploaded')

        return response, 200
    except ValueError as error:
        return str(error), 400
    except Exception as e:
        worker.log.error(e)
        return 'Server Error', 500

# Rejected request handlers
@app.errorhandler(405)
def method_not_allowed(error):
    return 'The method is not allowed for the requested URL', 405


@app.errorhandler(404)
def page_not_found(error):
    return 'The requested URL was not found', 404


@app.errorhandler(500)
def server_error(error):
    worker.log.error(error)
    return 'Server Error', 500

if __name__ == '__main__':
    logger.info("Startup...")

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--am_path',
        type=str,
        help='Acoustic Model Path',
        default='/opt/models/AM')
    parser.add_argument(
        '--lm_path',
        type=str,
        help='Decoding graph path',
        default='/opt/models/LM')
    parser.add_argument(
        '--config_path',
        type=str,
        help='Configuration files path',
        default='/opt/config')
    parser.add_argument(
        '--service_port',
        type=int,
        help='Service port',
        default=80)
    parser.add_argument(
        '--swagger_url',
        type=str,
        help='Swagger interface url',
        default='/api-doc')
    parser.add_argument(
        '--swagger_prefix',
        type=str,
        help='Swagger prefix',
        default=os.environ.get('SWAGGER_PREFIX', ''))
    parser.add_argument(
        '--swagger_path',
        type=str,
        help='Swagger file path',
        default=os.environ.get('SWAGGER_PATH', None))
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Display debug logs')
    args = parser.parse_args()
    
    logger.setLevel(logging.DEBUG if args.debug else logging.INFO)
    
    try:    
        # Setup SwaggerUI
        if args.swagger_path is not None:
            setupSwaggerUI(app, args)

        # Instantiate services
        logger.debug("Setting folders and configuration files")
        prepare(args.am_path, args.lm_path, args.config_path)
        # speakerdiarization = SpeakerDiarization()

        # Load ASR models (acoustic model and decoding graph)
        logger.info('Loading acoustic model and decoding graph ...')
        start = timeit.timeit()
        try:
            model = loadModel(args.am_path, args.lm_path, os.path.join(args.config_path, "online.conf"))
        except Exception as e:
            raise Exception("Failed to load transcription model: {}".format(str(e)))
        logger.info('Acoustic model and decoding graph loaded. (t={}s)'.format(timeit.timeit() - start))

        spkModel = None
        
        # Run server
        http_server = WSGIServer(('', args.service_port), app)
        logger.info("Service up and running")
        http_server.serve_forever()

    except KeyboardInterrupt:
        http_server.stop()
        logger.info("Service is shut down (user input)")

    except Exception as e:
        logger.error(str(e))
        logger.critical("Service is shut down")
        exit(e)