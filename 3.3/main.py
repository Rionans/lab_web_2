from flask import Flask
from flask_restx import Api, Resource, fields, reqparse
from werkzeug.exceptions import NotFound, BadRequest

app = Flask(__name__)
api = Api(app, doc='/', title='API Выставки', description='Сервис для управления информацией о выставках')

# ---------- 1. Описание модели данных (бизнес-сущность "Выставка") ----------
# Поля: id (число, генерируется), название (строка), место (строка),
# год (число), количество экспонатов (число), площадь (число), рейтинг (float)
exhibition_model = api.model('Exhibition', {
    'id': fields.Integer(description='Уникальный идентификатор', readonly=True),
    'name': fields.String(required=True, description='Название выставки', example='Импрессионизм и свет'),
    'venue': fields.String(required=True, description='Место проведения', example='ГМИИ им. Пушкина'),
    'year': fields.Integer(required=True, description='Год проведения', min=1800, max=2030, example=2024),
    'exhibits_count': fields.Integer(required=True, description='Количество экспонатов', min=0, example=150),
    'area_sqm': fields.Float(required=True, description='Площадь в кв. метрах', min=0, example=1200.5),
    'rating': fields.Float(description='Рейтинг посещаемости (0..10)', min=0, max=10, example=8.7)
})

# Модель для обновления (все поля необязательны, кроме id в URL)
exhibition_update_model = api.model('ExhibitionUpdate', {
    'name': fields.String(description='Название выставки'),
    'venue': fields.String(description='Место проведения'),
    'year': fields.Integer(description='Год проведения', min=1800, max=2030),
    'exhibits_count': fields.Integer(description='Количество экспонатов', min=0),
    'area_sqm': fields.Float(description='Площадь в кв. метрах', min=0),
    'rating': fields.Float(description='Рейтинг', min=0, max=10)
})

# ---------- 2. "База данных" в памяти (список выставок) ----------
exhibitions_db = [
    {'id': 1, 'name': 'Шедевры Эрмитажа', 'venue': 'Эрмитаж', 'year': 2023,
     'exhibits_count': 200, 'area_sqm': 800.0, 'rating': 9.2},
    {'id': 2, 'name': 'Современное искусство', 'venue': 'Гараж', 'year': 2024,
     'exhibits_count': 85, 'area_sqm': 450.5, 'rating': 7.8},
    {'id': 3, 'name': 'Древний Египет', 'venue': 'Кунсткамера', 'year': 2023,
     'exhibits_count': 120, 'area_sqm': 600.0, 'rating': 8.9}
]
next_id = 4  # для генерации новых id

def find_exhibition_by_id(eid):
    """Вспомогательная функция: найти выставку по id или вернуть None"""
    for ex in exhibitions_db:
        if ex['id'] == eid:
            return ex
    return None

# ---------- 3. Пространство имён (namespace) для выставок ----------
exhibitions_ns = api.namespace('exhibitions', description='Операции с выставками')

# ---------- 4. Парсер для параметров сортировки (GET /exhibitions) ----------
sort_parser = reqparse.RequestParser()
sort_parser.add_argument('sort', type=str, required=False,
                         help='Поле для сортировки: name, venue, year, exhibits_count, area_sqm, rating',
                         choices=('name', 'venue', 'year', 'exhibits_count', 'area_sqm', 'rating'))
sort_parser.add_argument('order', type=str, required=False, default='asc',
                         choices=('asc', 'desc'), help='Порядок сортировки: asc (по возрастанию) или desc')

# ---------- 5. GET /exhibitions - список всех выставок с возможностью сортировки ----------
@exhibitions_ns.route('/')
class ExhibitionList(Resource):
    @exhibitions_ns.doc(parser=sort_parser)
    @exhibitions_ns.marshal_list_with(exhibition_model)
    def get(self):
        """Получить список всех выставок. Поддерживается сортировка по любому полю."""
        args = sort_parser.parse_args()
        sort_by = args.get('sort')
        order = args.get('order', 'asc')
        data = exhibitions_db.copy()
        if sort_by:
            reverse = (order == 'desc')
            # Сортировка с учётом типов (числа сортируются как числа, строки как строки)
            data.sort(key=lambda x: x[sort_by], reverse=reverse)
        return data

    @exhibitions_ns.expect(exhibition_model, validate=True)
    @exhibitions_ns.marshal_with(exhibition_model, code=201)
    @exhibitions_ns.response(400, 'Некорректные данные')
    def post(self):
        """Добавить новую выставку. ID генерируется автоматически."""
        global next_id
        new_ex = api.payload
        new_ex['id'] = next_id
        next_id += 1
        exhibitions_db.append(new_ex)
        return new_ex, 201

# ---------- 6. GET /exhibitions/stats - статистика по числовым полям ----------
@exhibitions_ns.route('/stats')
class Stats(Resource):
    @exhibitions_ns.doc(description='Среднее, минимум и максимум по числовым полям (год, количество, площадь, рейтинг)')
    def get(self):
        """Возвращает агрегированную статистику: min, max, avg для каждого числового поля"""
        if not exhibitions_db:
            return {'message': 'Нет данных для статистики'}, 200
        numeric_fields = ['year', 'exhibits_count', 'area_sqm', 'rating']
        stats = {}
        for field in numeric_fields:
            values = [ex[field] for ex in exhibitions_db]
            stats[field] = {
                'min': min(values),
                'max': max(values),
                'avg': round(sum(values) / len(values), 2)
            }
        return stats

# ---------- 7. Операции с отдельной выставкой (по id) ----------
@exhibitions_ns.route('/<int:id>')
@exhibitions_ns.response(404, 'Выставка с таким id не найдена')
@exhibitions_ns.param('id', 'Уникальный идентификатор выставки')
class ExhibitionResource(Resource):
    @exhibitions_ns.marshal_with(exhibition_model)
    def get(self, id):
        """Получить данные о конкретной выставке по id"""
        ex = find_exhibition_by_id(id)
        if not ex:
            raise NotFound('Выставка не найдена')
        return ex

    @exhibitions_ns.expect(exhibition_update_model, validate=True)
    @exhibitions_ns.marshal_with(exhibition_model)
    def put(self, id):
        """Полностью обновить выставку (все поля, кроме id). Если поля не указаны – остаются старые значения."""
        ex = find_exhibition_by_id(id)
        if not ex:
            raise NotFound('Выставка не найдена')
        payload = api.payload
        # Обновляем только те поля, которые были переданы
        for field in ['name', 'venue', 'year', 'exhibits_count', 'area_sqm', 'rating']:
            if field in payload and payload[field] is not None:
                ex[field] = payload[field]
        return ex

    @exhibitions_ns.response(204, 'Выставка удалена')
    def delete(self, id):
        """Удалить выставку по id"""
        global exhibitions_db
        ex = find_exhibition_by_id(id)
        if not ex:
            raise NotFound('Выставка не найдена')
        exhibitions_db = [e for e in exhibitions_db if e['id'] != id]
        return '', 204

# ---------- 8. Регистрация пространства имён и запуск ----------
api.add_namespace(exhibitions_ns)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
