from typing import Any, Dict, List, Tuple, Union

from flasgger import swag_from
from flask import Response
from flask_restful import Resource

from openatlas.api.v02.resources.error import InvalidLimitError
from openatlas.api.v02.resources.parser import entity_
from openatlas.api.v02.resources.resolve_endpoints import resolve_entities
from openatlas.models.entity import Entity


class GetLatest(Resource):
    @swag_from("../swagger/latest.yml", endpoint="api_02.latest")
    def get(self, latest: int) \
            -> Union[Tuple[Resource, int], Response, Dict[str, Any]]:
        return resolve_entities(
            GetLatest.get_latest(latest),
            entity_.parse_args(),
            latest)

    @staticmethod
    def get_latest(limit_: int) -> List[Entity]:
        if not 0 < limit_ < 101:
            raise InvalidLimitError  # pragma: no cover
        return Entity.get_latest(limit_)
