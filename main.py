import os
import random

from flask import Flask
from flask_restful import Resource, Api, reqparse
from flask_cors import CORS
from werkzeug.datastructures import FileStorage
import subprocess
import re
import uuid
from waitress import serve

UPLOAD_FOLDER = '/app/temp/'
ALLOWED_EXTENSIONS = {'stl'}

app = Flask(__name__)
api = Api(app)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 128 * 1000 * 1000
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def estimate(file_path):
    try:
        completed = subprocess.run(['./CuraEngine', 'slice',
                                    '-j', 'definitions/creality_ender3.def.json',
                                    '-j', 'definitions/fdmextruder.def.json',
                                    '-s', 'layer_height=0.2',
                                    '-s', 'material_shrinkage_percentage=0',
                                    '-s', 'roofing_layer_count=2',
                                    '-s', 'roofing_monotonic=0',
                                    '-s', 'adhesion_extruder_nr=0',
                                    '-e0',
                                    '-l', file_path,
                                    '-o', '/dev/null'],
                                   shell=False,
                                   text=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT
                                   )
        result = re.findall(r";TIME:\d+", completed.stdout)[0][6:]
        return int(result)
    except Exception as e:
        print(str(e))
    finally:
        if os.path.isfile(file_path):
            os.remove(file_path)
    return -1


class EstimateMultiple(Resource):
    @staticmethod
    def post():
        request_number = random.randint(1000, 9999)
        print('Request for multiple files ' + str(request_number) + ' started...')
        parser1 = reqparse.RequestParser()
        parser1.add_argument('files_number', required=True, type=int, location='form')
        args1 = parser1.parse_args()

        files_number = args1['files_number']

        parser2 = reqparse.RequestParser()
        for i in range(0, files_number):
            parser2.add_argument('file_' + str(i), required=True, type=FileStorage, location='files')
        args2 = parser2.parse_args()
        results = {}
        for i in range(0, files_number):
            name = 'file_' + str(i)
            stl_file = args2[name]
            if stl_file is None or stl_file.filename == '':
                return {'error': 'No file or file with no name'}, 400
            elif not allowed_file(stl_file.filename):
                return {'error': 'Illegal filename or extension'}, 400
            else:
                filename = str(uuid.uuid4().hex) + '.stl'
                file_path = os.path.join(os.environ['HOME'], app.config['UPLOAD_FOLDER'], filename)
                stl_file.save(file_path)
                result = estimate(file_path)
                results[stl_file.filename] = result
        return results, 200


class Estimate(Resource):
    @staticmethod
    def post():
        request_number = random.randint(1000, 9999)
        print('Request ' + str(request_number) + ' started...')
        parser = reqparse.RequestParser()
        parser.add_argument('file', required=True, type=FileStorage, location='files')
        args = parser.parse_args()
        stl_file = args['file']
        if stl_file is None or stl_file.filename == '':
            return {'error': 'No file or file with no name'}, 400
        elif not allowed_file(stl_file.filename):
            return {'error': 'Illegal filename or extension'}, 400
        else:
            filename = str(uuid.uuid4().hex) + '.stl'
            file_path = os.path.join(os.environ['HOME'], app.config['UPLOAD_FOLDER'], filename)
            stl_file.save(file_path)
            result = estimate(file_path)
            print('Request ' + str(request_number) + ' completed successfuly!')
            return {'duration': result}, 200


class Status(Resource):
    @staticmethod
    def get():
        print('Hello!')
        return {'status': True}, 200


if __name__ == '__main__':
    api.add_resource(Estimate, '/estimate')
    api.add_resource(EstimateMultiple, '/estimate_multiple')
    api.add_resource(Status, '/status')

    if os.getenv('PRODUCTION') == '1':
        serve(app, host='0.0.0.0', port=5000)
    else:
        app.run()
