import json

from flask import jsonify, request
from flask_restful import Api, Resource, fields, marshal, marshal_with, reqparse
from openatlas.api.apifunction import ApiFunction
from openatlas import app
from openatlas.api.parameter import Validation
from openatlas.api.path import Path

api = Api(app)  # Establish connection between API and APP
app.config['BUNDLE_ERRORS'] = True  # Every parser shows bundled errors

# Parser
default_parser = reqparse.RequestParser()
default_parser.add_argument('download', type=bool, help='{error_msg}', default=False)
default_parser.add_argument('count', type=bool, help='{error_msg}', default=False)

language_parser = reqparse.RequestParser()
language_parser.add_argument('lang', type=str,
                             help='{error_msg}',
                             choices=app.config['LANGUAGES'].keys())

parser = default_parser.copy()  # inherit the default parser
parser.add_argument('sort', choices=('desc', 'asc'), type=str, default='asc', case_sensitive=False,
                    help='{error_msg}. Only "desc" or "asc" will work.')
parser.add_argument('column', type=str, default=['name'], action='append', case_sensitive=False,
                    help='{error_msg}', choices=(
        'id', 'class_code', 'name', 'description', 'created', 'modified', 'system_type',
        'begin_from', 'begin_to', 'end_from', 'end_to'))
# Todo: Dismiss negative value
parser.add_argument('limit', type=int, default=20, help="Invalid number for limit")
# Todo: Either first or last
parser.add_argument('first', type=int, help="Not a valid ID")
parser.add_argument('last', type=int, help="Not a valid ID")
parser.add_argument('show', type=str, help='{error_msg}.', action='append', case_sensitive=False,
                    default=['when', 'types', 'relations', 'names', 'links', 'geometry',
                             'depictions', 'geonames'],
                    choices=('when', 'types', 'relations', 'names', 'links', 'geometry',
                             'depictions', 'geonames', 'none'))
parser.add_argument('filter', type=str, help='{error_msg}', action='append', default='and|id|gt|1')

# Template

entity_json = {'@context': fields.String,
               'type': fields.String,
               'features': fields.List(fields.String)}


class GetEntity(Resource):
    @marshal_with(entity_json)
    def get(self, id_):
        args = parser.parse_args()
        validation = Validation.validate_url_query(request.args)
        entity = ApiFunction.get_entity(id_, validation)
        entity = {"@context": "teteet",
               "type": "fields.String",
               "features": ["fields.List(fields.String)", "testing"]}
        return entity


class GetClass(Resource):
    def get(self, class_code):
        args = parser.parse_args()
        print(args)
        validation = Validation.validate_url_query(request.args)
        class_ = Path.pagination(
            Path.get_entities_by_class(class_code=class_code, validation=validation),
            validation=validation)
        return class_


class GetContent(Resource):
    def get(self):
        args = language_parser.parse_args()
        print(args)
        validation = Validation.validate_url_query(request.args)
        content = Path.get_content(validation=validation)
        return content


api.add_resource(GetEntity, '/api/0.1/restful/entity/<int:id_>', endpoint='entity')
api.add_resource(GetClass, '/api/0.1/restful/class/<string:class_code>', endpoint="class")
api.add_resource(GetContent, '/api/0.1/restful/content/', endpoint="content")
