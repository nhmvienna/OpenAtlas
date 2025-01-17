from typing import Any, Union

from flasgger import swag_from
from flask import Response, g
from flask_restful import Resource

from openatlas.api.v02.resources.error import InvalidCodeError
from openatlas.api.v02.resources.parser import entity_
from openatlas.api.v02.resources.resolve_endpoints import resolve_entities
from openatlas.database.api import Api as Db
from openatlas.models.entity import Entity


class GetByCode(Resource):
    @staticmethod
    @swag_from("../swagger/code.yml", endpoint="api_02.code")
    def get(code: str) -> Union[tuple[Resource, int], Response, dict[str, Any]]:
        parsed = entity_.parse_args()
        return resolve_entities(
            GetByCode.get_by_view(code, parsed),
            parsed,
            code)

    @staticmethod
    def get_by_view(code_: str, parser: dict[str, Any]) -> list[Entity]:
        if code_ not in g.view_class_mapping:
            raise InvalidCodeError  # pragma: no cover
        sys_class = Db.get_by_system_class(g.view_class_mapping[code_], parser)
        return [Entity(row) for row in sys_class]
