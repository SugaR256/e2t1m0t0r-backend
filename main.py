import os

from flask import Flask
from flask_restful import Resource, Api, reqparse
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
import subprocess
import re
from waitress import serve

UPLOAD_FOLDER = '/app/temp/'
ALLOWED_EXTENSIONS = {'stl'}

app = Flask(__name__)
api = Api(app)
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


class Estimate(Resource):
    @staticmethod
    def post():
        parser = reqparse.RequestParser()
        parser.add_argument('file', type=FileStorage, location='files')
        args = parser.parse_args()
        stl_file = args['file']
        if stl_file.filename == '':
            return {'error': 'No file'}, 400
        if stl_file and allowed_file(stl_file.filename):
            filename = secure_filename(stl_file.filename)
            file_path = os.path.join(os.environ['HOME'], app.config['UPLOAD_FOLDER'], filename)
            stl_file.save(file_path)
            result = estimate(file_path)
            return {'duration': result}, 200

        return {'error': 'This shouldn\'t happen'}, 500


if __name__ == '__main__':
    api.add_resource(Estimate, '/estimate')

    if os.getenv('PRODUCTION') == '1':
        serve(app, host="0.0.0.0", port=5000)
    else:
        app.run()
