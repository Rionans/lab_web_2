from flask import Flask, jsonify, Blueprint
from flasgger import Swagger
from sitepart.sitepart import sitepart

app = Flask(__name__)
swagger = Swagger(app)

# Основной Blueprint
main = Blueprint("/", __name__, template_folder='templates', static_folder='static')

@main.route('/info/<about>/')
def info(about):
    """Example endpoint returning about info
    This is using docstrings for specifications.
    ---
    parameters:
      - name: about
        in: path
        type: string
        enum: ['all', 'version', 'author', 'year']
        required: true
        default: all
    definitions:
      About:
        type: string
    responses:
      200:
        description: A string
        schema:
          $ref: '#/definitions/About'
        examples:
          version: '1.0'
    """
    all_info = {
        'all': 'main_author 1.0 2020',
        'version': '1.0',
        'author': 'main_author',
        'year': '2020'
    }
    result = {about: all_info[about]}
    return jsonify(result)

app.register_blueprint(main, url_prefix='/')
app.register_blueprint(sitepart, url_prefix='/sitepart')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
