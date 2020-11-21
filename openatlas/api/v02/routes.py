from flasgger import Swagger
from flask_restful import Api

from openatlas import app
from openatlas.api.v02.common.class_ import GetByClass
from openatlas.api.v02.common.code import GetByCode
from openatlas.api.v02.common.content import GetContent
from openatlas.api.v02.common.entity import GetEntity
from openatlas.api.v02.common.latest import GetLatest
from openatlas.api.v02.common.node_entities import GetNodeEntities
from openatlas.api.v02.common.node_entities_all import GetNodeEntitiesAll
from openatlas.api.v02.common.query import GetQuery
from openatlas.api.v02.common.subunit import GetSubunit
from openatlas.api.v02.common.subunit_hierarchy import GetSubunitHierarchy

template = {
    "openapi": "3.0.2",
    "info": {
        "title": "Openatlas API",
        "version": "0.2",
        "description": "A documentation of the OpenAtlas API",
        "license": {
            "name": "Apache 2.0",
            "url": "http://www.apache.org/licenses/LICENSE-2.0.html"
        },
        "contact": {
            "name": "Bernhard Koschicek",
            "email": "bernhard.koschicek@oeaw.ac.at"
        }
    },
    "servers": [],
    "tags": [
        {
            "name": "Entities",
            "description": "Requesting entities through different means."
        },
        {
            "name": "Nodes",
            "description": "Requesting nodes and subunits"
        },
        {
            "name": "Content",
            "description": "Requesting content of the OpenAtlas instance."
        }
    ],
    "components": {
        "parameters": {
            "limitParam": {
                "name": "limit",
                "in": "query",
                "description": "Number of geojson representation to be returned",
                "schema": {
                    "type": "number"
                }
            },
            "columnParam": {
                "name": "column",
                "in": "query",
                "description": "The result will sorted by the given column",
                "schema": {
                    "type": "string",
                    "enum": [
                        "id",
                        "class_code",
                        "name",
                        "description",
                        "created",
                        "modified",
                        "system_type",
                        "begin_from",
                        "begin_to",
                        "end_from",
                        "end_to"
                    ]
                }
            },
            "sortParam": {
                "name": "sort",
                "in": "query",
                "description": "Result will be sorted asc/desc (by default by the name column)",
                "schema": {
                    "type": "string",
                    "enum": ["asc", "desc"]
                }
            },
            "filterParam": {
                "name": "filter",
                "in": "query",
                "description": "Specify request with custom SQL filter method",
                "schema": {
                    "type": "string"
                }
            },
            "firstParam": {
                "name": "first",
                "in": "query",
                "description": "List of results start with given ID",
                "schema": {
                    "type": "number"
                }
            },
            "lastParam": {
                "name": "last",
                "in": "query",
                "description": "List of results start with entity after given ID",
                "schema": {
                    "type": "number"
                }
            },
            "countParam": {
                "name": "count",
                "in": "query",
                "description": "Returns a number which represents the total count of the result",
                "schema": {
                    "type": "boolean"
                }
            },
            "downloadParam": {
                "name": "download",
                "in": "query",
                "description": "Triggers the file download of the given request",
                "schema": {
                    "type": "boolean"
                }
            },
            "showParam": {
                "name": "show",
                "in": "query",
                "description": "Select which key should be shown e.g. when, types, relations, names, links, geometry, depictions, not",
                "schema": {
                    "type": "string",
                    "enum": [
                        "when",
                        "types",
                        "relations",
                        "names",
                        "links",
                        "geometry",
                        "depictions",
                        "not"
                    ]
                }
            },
            "langParam": {
                "name": "language",
                "in": "query",
                "description": "Select output language",
                "schema": {
                    "type": "string",
                    "enum": ["en", "de"]
                }
            },
        }
    }
}

app.config['SWAGGER'] = {
    'openapi': '3.0.2',
    'uiversion': 3
}
api = Api(app)  # Establish connection between API and APP
swagger = Swagger(app, template=template)

api.add_resource(GetEntity, '/api/0.2/entity/<int:id_>', endpoint='entity')
api.add_resource(GetByClass, '/api/0.2/class/<string:class_code>', endpoint="class")
api.add_resource(GetByCode, '/api/0.2/code/<string:item>', endpoint="code")
api.add_resource(GetContent, '/api/0.2/content/', endpoint="content")
api.add_resource(GetLatest, '/api/0.2/latest/<int:latest>', endpoint="latest")
api.add_resource(GetNodeEntities, '/api/0.2/node_entities/<int:id_>', endpoint="node_entities")
api.add_resource(GetNodeEntitiesAll, '/api/0.2/node_entities_all/<int:id_>',
                 endpoint="node_entities_all")
api.add_resource(GetSubunit, '/api/0.2/subunit/<int:id_>', endpoint="subunit")
api.add_resource(GetSubunitHierarchy, '/api/0.2/subunit_hierarchy/<int:id_>',
                 endpoint="subunit_hierarchy")
api.add_resource(GetQuery, '/api/0.2/query/', endpoint="query")
