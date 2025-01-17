from typing import Type, Union

from flask_restful import fields
from flask_restful.fields import Integer, String


# Deprecated
class CountTemplate:

    @staticmethod
    def overview_template() -> dict[str, Type[Union[String, Integer]]]:
        return {'systemClass': fields.String, 'count': fields.Integer}
