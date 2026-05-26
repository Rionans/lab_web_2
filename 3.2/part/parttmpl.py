from flask import Blueprint
from flask_restx import Api

templ = Blueprint('templ', __name__, template_folder='templates', static_folder='static')
api = Api(templ)

@templ.route("/")
def index():
    return "template"
