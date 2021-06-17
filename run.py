#!/usr/bin/env python3

import os
from time import time
import threading

import argparse
import logging

from flask import Flask, request, abort, Response, json
from gevent.pywsgi import WSGIServer

from processing import prepare, loadModel, decode, formatAudio, prepare_response
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
        logger.debug(request.headers.get('accept').lower())
        if request.headers.get('accept').lower() == 'application/json':
            join_metadata = True
        elif request.headers.get('accept').lower() == 'text/plain':
            join_metadata = False
        else:
            raise ValueError('Not accepted header')
        logger.debug("Metadata: {}".format(join_metadata))

        # get input file
        if 'file' in request.files.keys():
            file_buffer = request.files['file'].read()
            audio_data, sampling_rate = formatAudio(file_buffer)
            start_t = time()
            
            # Transcription
            transcription, confidence = decode(audio_data, model, sampling_rate, join_metadata, False)
            logger.debug("Transcription complete (t={}s)".format(time() - start_t))
            
            #Postprocessing
            logger.debug("Postprocessing ...")
            trans = prepare_response(transcription, confidence, join_metadata)
            response = trans
            logger.debug("... Complete")
            
        else:
            raise ValueError('No audio file was uploaded')

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
        '--debug',
        action='store_true',
        help='Display debug logs')
    args = parser.parse_args()
    
    logger.setLevel(logging.DEBUG if args.debug else logging.INFO)
    
    try:    
        # Setup SwaggerUI
        if args.swagger_path is not None:
            setupSwaggerUI(app, args)
    except Exception as e:
        logger.warning("Could not setup swagger: {}".format(str(e)))

    # Instantiate services
    logger.debug("Setting folders and configuration files")
    try:
        prepare(args.am_path, args.lm_path, args.config_path)
    except Exception as e:
        logger.error("Could not prepare service: {}".format(str(e)))
        exit(-1)
    
    # Load ASR models (acoustic model and decoding graph)
    logger.info('Loading acoustic model and decoding graph ...')
    start = time()
    try:
        model = loadModel(args.am_path, args.lm_path, os.path.join(args.config_path, "online.conf"))
    except Exception as e:
        raise Exception("Failed to load transcription model: {}".format(str(e)))
        exit(-1)
    logger.info('Acoustic model and decoding graph loaded. (t={}s)'.format(time() - start))
    try:        
        # Run server
        http_server = WSGIServer(('', args.service_port), app)
        logger.info("Service up and running")
        http_server.serve_forever()

    except KeyboardInterrupt:
        http_server.stop()
        logger.info("Service is shut down (user input)")
        exit(1)

    except Exception as e:
        logger.error(str(e))
        logger.critical("Service is shut down (Error)")
        exit(e)