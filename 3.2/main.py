from flask import Flask, Blueprint
from flask_restx import Api, Resource, fields, reqparse
from random import random

app = Flask(__name__)
api = Api(app=app)

# Основной блок API будет доступен по адресу /main/
name_space = api.namespace('main', description='Main APIs')

@name_space.route("/")
class MainClass(Resource):
    def get(self):
        return {"status": "Got new data"}

    def post(self):
        return {"status": "Posted new data"}

# Импортируем и подключаем другие части API
from part.part import api as partns1
api.add_namespace(partns1)

from part.parttmpl import api as partns2
from part.parttmpl import templ as templ
api.add_namespace(partns2)

# Регистрируем Blueprint для шаблонной части
app.register_blueprint(templ, url_prefix='/templ')

# Модель данных для сериализации
list_ = api.model('list', {
    'len': fields.String(required=True, description='Size of array'),
    'array': fields.List(fields.String, required=True, description='Some array'),
})

# "База данных" в оперативной памяти
allarray = ['1']

# Создаём новое пространство имён для работы со списками
name_space1 = api.namespace('list', description='list APIs')

@name_space1.route("/")
class ListClass(Resource):
    @name_space1.doc("")
    @name_space1.marshal_with(list_)
    def get(self):
        """Получение всего хранимого массива"""
        return {'len': str(len(allarray)), 'array': allarray}

    @name_space1.doc("")
    @name_space1.expect(list_)
    @name_space1.marshal_with(list_)
    def post(self):
        """Создание массива/обновление данных"""
        global allarray
        # Получаем данные из тела запроса
        allarray = api.payload['array']
        return {'len': str(len(allarray)), 'array': allarray}

# Модель для двух значений
minmax = api.model('minmax', {
    'min': fields.String, 
    'max': fields.String
})

@name_space1.route("/minmax")
class MinMaxClass(Resource):
    @name_space1.doc("")
    @name_space1.marshal_with(minmax)
    def get(self):
        """Получение максимума и минимума массива"""
        global allarray
        # Для строк подойдёт простое сравнение
        return {'min': min(allarray), 'max': max(allarray)}

# Парсер для GET-параметров
reqp = reqparse.RequestParser()
reqp.add_argument('len', type=int, required=False)
reqp.add_argument('minval', type=float, required=False)
reqp.add_argument('maxval', type=float, required=False)

@name_space1.route("/makerand")
class MakeArrayClass(Resource):
    @name_space1.doc("")
    @name_space1.expect(reqp)
    @name_space1.marshal_with(list_)
    def get(self):
        """Возвращение массива случайных значений от min до max"""
        args = reqp.parse_args()
        # Генерируем массив случайных чисел
        array = [random()*(args['maxval']-args['minval'])+args['minval'] for i in range(args['len'])]
        # Для совместимости с моделью, числа можно преобразовать в строки
        str_array = [str(x) for x in array]
        return {'len': str(args['len']), 'array': str_array}

# Регистрируем это пространство имён в основном API
api.add_namespace(name_space1)

# Запускаем приложение в режиме отладки на всех интерфейсах
app.run(host='0.0.0.0', debug=True)
