#!/usr/bin/env python3

import os
from time import time
import threading

import argparse
import logging

from flask import Flask, request, abort, Response, json
from gevent.pywsgi import WSGIServer

from processing import prepare, loadModel, decode, formatAudio, process_response
from processing import checkDiarizationService, diarization_request
from processing import checkPunctuationService, punctuation_request
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
        logging.debug("Metadata: {}".format(join_metadata))

        # get input file
        if 'file' in request.files.keys():
            file_buffer = request.files['file'].read()
            audio_data, sampling_rate = formatAudio(file_buffer)
            start_t = time()
            
            # Diarization request is done on a separate thread.
            diarization_result = [None] # Create a object to be shared between the main thread and the diarization thread
            if join_metadata:
                if diarization_service_set:
                    if checkDiarizationService(args.diarization_host, args.diarization_port):
                        spk_thread = threading.Thread(target=diarization_request,
                                                    args=[args.diarization_host, args.diarization_port, file_buffer, diarization_result, "/"],
                                                    daemon=True)
                        spk_thread.start()
                    else:
                        raise Exception("Could not reach diarization service healthcheck.")
                else:
                    raise Exception("Diarization service is not set on this worker.")
            # Transcription
            result, confidence = decode(audio_data, model, sampling_rate, join_metadata, False)
            logger.debug("Transcription complete (t={}s)".format(time() - start_t))
            
            if join_metadata:
                logger.debug("Waiting for diarization")            
                spk_thread.join()
                if diarization_result[0] is None:
                    raise Exception("Diarization process returned None.")

            #Postprocessing
            logger.debug("Postprocessing ...")
            trans = process_response(result, diarization_result[0], confidence, join_metadata)
            response = trans
            logger.debug("... Complete")
            logger.debug("Punctuation ...")
            if punctuation_service_set:
                #if checkPunctuationService(args.punctuation_host, args.punctuation_port, interface=args.punctuation_route):
                pass
        else:
            raise ValueError('No audio file was uploaded')
        # TODO libérer la ressource
        return response, 200
    except ValueError as error:
        return str(error), 400
    except Exception as e:
        logger.error(e)
        return 'Server Error: {}'.format(str(e)), 500

# Rejected request handlers
@app.errorhandler(405)
def method_not_allowed(error):
    return 'The method is not allowed for the requested URL', 405


@app.errorhandler(404)
def page_not_found(error):
    return 'The requested URL was not found', 404


@app.errorhandler(500)
def server_error(error):
    logger.error(error)
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
        '--diarization_host',
        type=str,
        help='Speaker Diarization service host',
        default=os.environ.get('SPEAKER_DIARIZATION_HOST', None)
    )
    parser.add_argument(
        '--diarization_port',
        type=int,
        help='Speaker Diarization service port',
        default=os.environ.get('SPEAKER_DIARIZATION_PORT', None)
    )
    parser.add_argument(
        '--punctuation_host',
        type=str,
        help='Punctuation service host',
        default=os.environ.get('PUNCTUATION_HOST', None)
    )
    parser.add_argument(
        '--punctuation_port',
        type=int,
        help='Punctuation service port',
        default=os.environ.get('PUNCTUATION_PORT', None)
    )
    parser.add_argument(
        '--punctuation_route',
        type=str,
        help='Punctuation service route',
        default=os.environ.get('PUNCTUATION_ROUTE', '/')
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Display debug logs')
    args = parser.parse_args()
    
    logger.setLevel(logging.DEBUG if args.debug else logging.INFO)
    
    diarization_service_set = args.diarization_host is not None and args.diarization_port is not None
    punctuation_service_set = args.diarization_host is not None and args.diarization_port is not None
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
        start = time()
        try:
            model = loadModel(args.am_path, args.lm_path, os.path.join(args.config_path, "online.conf"))
        except Exception as e:
            raise Exception("Failed to load transcription model: {}".format(str(e)))
        logger.info('Acoustic model and decoding graph loaded. (t={}s)'.format(time() - start))

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