from typing import Type

from flask_restful import Resource

from openatlas.api.v03.resources.error import ResourceGoneError


class ResourceGone(Resource):
    @staticmethod
    def get(*args: str, **kwargs: str) -> tuple[Type[ResourceGoneError], int]:
        raise ResourceGoneError
