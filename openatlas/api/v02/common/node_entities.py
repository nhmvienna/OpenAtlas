from typing import Any, Dict, List, Tuple

from flask import g, jsonify, url_for
from flask_restful import Resource, marshal

from openatlas.api.v01.error import APIError
from openatlas.api.v02.resources.download import Download
from openatlas.api.v02.resources.parser import default_parser
from openatlas.api.v02.templates.nodes import NodeTemplate


class GetNodeEntities(Resource):
    def get(self, id_: int) -> Tuple[Any, int]:
        parser = default_parser.parse_args()
        node = GetNodeEntities.get_node(id_)
        template = NodeTemplate.node_template()
        if parser['count']:
            # Todo: very static, make it dynamic
            return jsonify(len(node))
        if parser['download']:
            return Download.download(data=node, template=template, name=id_)
        return marshal(node, template), 200

    @staticmethod
    def get_node(id_: int) -> List[Dict[str, Any]]:
        try:
            id_ = int(id_)
        except Exception:
            raise APIError('Invalid ID: ' + str(id_), status_code=404, payload="404b")
        if id_ not in g.nodes:
            raise APIError('Node ID ' + str(id_) + ' doesn\'t exist', status_code=404,
                           payload="404g")
        entities = g.nodes[id_].get_linked_entities(['P2', 'P89'], inverse=True)
        data = []
        for e in entities:
            data.append({'id': e.id, 'label': e.name,
                         'url': url_for('api_entity', id_=e.id, _external=True)})
        return data