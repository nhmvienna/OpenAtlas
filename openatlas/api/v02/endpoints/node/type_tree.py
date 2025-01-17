from typing import Any, Union

from flasgger import swag_from
from flask import Response
from flask_restful import Resource, marshal

from openatlas.api.v02.resources.parser import default
from openatlas.api.v02.resources.resolve_endpoints import download
from openatlas.api.v02.templates.type_tree import TypeTreeTemplate
from openatlas.models.type import Type


class GetTypeTree(Resource):
    @staticmethod
    @swag_from("../swagger/type_tree.yml", endpoint="api_02.type_tree")
    def get() -> Union[tuple[Resource, int], Response]:
        parser = default.parse_args()
        type_tree = {'typeTree': GetTypeTree.get_type_tree()}
        template = TypeTreeTemplate.type_tree_template()
        if parser['download']:
            return download(type_tree, template, 'type_tree')
        return marshal(type_tree, template), 200

    @staticmethod
    def get_type_tree() -> list[dict[int, dict[str, Any]]]:
        return [
            {id_: GetTypeTree.serialize_to_json(node)}
            for id_, node in Type.get_all().items()]

    @staticmethod
    def serialize_to_json(node: Type) -> dict[str, Any]:
        return {
            'id': node.id,
            'name': node.name,
            'description': node.description,
            'origin_id': node.origin_id,
            'first': node.first,
            'last': node.last,
            'root': node.root,
            'subs': node.subs,
            'count': node.count,
            'count_subs': node.count_subs,
            'category': node.category}
