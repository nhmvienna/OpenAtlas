from typing import Any, Optional, Union

from openatlas.models.entity import Entity
from openatlas.models.gis import Gis
from openatlas.models.link import Link


class Geojson:

    @staticmethod
    def get_geojson(entities: list[Entity]) -> list[dict[str, Any]]:
        out = []
        for entity in entities:
            if geoms := [
                    Geojson.get_entity(entity, geom)
                    for geom in Geojson.get_geom(entity)]:
                out.extend(geoms)
            else:
                out.append(Geojson.get_entity(entity))
        return out

    @staticmethod
    def get_entity(
            entity: Entity,
            geom: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        features = {
            'type': 'Feature',
            'geometry': geom,
            'properties': {
                '@id': entity.id,
                'systemClass': entity.class_.name,
                'name': entity.name,
                'description': entity.description,
                'begin_earliest': entity.begin_from,
                'begin_latest': entity.begin_to,
                'begin_comment': entity.begin_comment,
                'end_earliest': entity.end_from,
                'end_latest': entity.end_to,
                'end_comment': entity.end_comment,
                'types': Geojson.get_node(entity)
            }}
        return features

    @staticmethod
    def get_node(entity: Entity) -> Optional[list[str]]:
        nodes = []
        for node in entity.types:
            out = [node.name]
            nodes.append(': '.join(out))
        return nodes if nodes else None

    @staticmethod
    def return_output(output: list[dict[str, Any]]) -> dict[str, Any]:
        return {'type': 'FeatureCollection', 'features': output}

    @staticmethod
    def get_geom(entity: Entity) -> Union[list[dict[str, Any]], list[Any]]:
        if entity.class_.view == 'place' or entity.class_.name == 'artifact':
            return Gis.get_by_id(
                Link.get_linked_entity_safe(entity.id, 'P53').id)
        if entity.class_.name == 'object_location':
            return Gis.get_by_id(entity.id)
        return []
