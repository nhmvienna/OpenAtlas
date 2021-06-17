from typing import Any, Dict, List, Tuple, Union

from flasgger import swag_from
from flask import Response, g
from flask_restful import Resource

from openatlas.api.v02.resources.error import InvalidSubunitError
from openatlas.api.v02.resources.helpers import resolve_entity
from openatlas.api.v02.resources.parser import entity_parser
from openatlas.api.v02.resources.util import get_entity_by_id


class GetTypeEntities(Resource):  # type: ignore
    @swag_from("../swagger/type_entities.yml", endpoint="api.type_entities")
    def get(self, id_: int) -> Union[Tuple[Resource, int], Response, Dict[str, Any]]:
        entities = [get_entity_by_id(entity) for entity in GetTypeEntities.get_node(id_)]
        print(entities)
        return resolve_entity(entities, entity_parser.parse_args(), id_)

    @staticmethod
    def get_node(id_: int) -> List[int]:
        if id_ not in g.nodes:
            raise InvalidSubunitError
        return [e.id for e in g.nodes[id_].get_linked_entities(['P2', 'P89'], inverse=True)]
