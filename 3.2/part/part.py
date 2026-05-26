from flask_restx import Namespace, Resource, fields

api = Namespace('part', description='some information')

# Модель данных для сериализации ответов
info = api.model('part', {
    'id': fields.String(required=True, description='The identifier'),
    'name': fields.String(required=True, description='The name'),
})

INFO = [
    {'id': '1111', 'name': 'Alex'},
]

@api.route('/')
class InfoList(Resource):
    @api.marshal_list_with(info)
    def get(self):
        '''List all / это описание появится в документации напротив GET'''
        return INFO

# Эндпоинт с динамическим параметром
@api.route('/<id>')
@api.param('id', 'The identifier')
@api.response(404, 'id not found')
class InfoId(Resource):
    @api.doc(params={'id': 'An ID'})
    @api.marshal_with(info)
    def get(self, id):
        for item in INFO:
            if item['id'] == id:
                return item
        else:
            # Если ID не найден, возвращаем 404
            api.abort(404)
