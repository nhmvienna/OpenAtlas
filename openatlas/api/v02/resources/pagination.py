import itertools
from typing import Any

from openatlas.api.v02.resources.error import EntityDoesNotExistError, \
    LastEntityError, NoEntityAvailable, TypeIDError
from openatlas.api.v02.resources.formats.geojson import Geojson
from openatlas.api.v02.resources.formats.linked_places import LinkedPlaces
from openatlas.api.v02.resources.util import get_all_links, \
    get_all_links_inverse, get_entity_by_id
from openatlas.models.entity import Entity
from openatlas.models.link import Link


class Pagination:

    @staticmethod
    def get_start_entity(total: list[int], parser: dict[str, Any]) -> list[Any]:
        if parser['first'] and int(parser['first']) in total:
            return list(itertools.islice(
                total,
                total.index(int(parser['first'])),
                None))
        if parser['last'] and int(parser['last']) in total:
            out = list(itertools.islice(
                total,
                total.index(int(parser['last'])) + 1,
                None))
            if not out:
                raise LastEntityError  # pragma: no cover
            return out
        raise EntityDoesNotExistError  # pragma: no cover

    @staticmethod
    def get_by_page(
            index: list[dict[str, Any]],
            parser: dict[str, Any]) -> dict[str, Any]:
        page = parser['page'] \
            if parser['page'] < index[-1]['page'] else index[-1]['page']
        return [entry['startId'] for entry in index if entry['page'] == page][0]

    @staticmethod
    def pagination(
            entities: list[Entity],
            parser: dict[str, Any]) -> dict[str, Any]:
        if not entities:
            raise NoEntityAvailable  # pragma: no cover
        if parser['type_id']:
            entities = Pagination.get_entities_by_type(entities, parser)
            if not entities:
                raise TypeIDError  # pragma: no cover
        total = [e.id for e in entities]
        count = len(total)
        e_list = list(itertools.islice(total, 0, None, int(parser['limit'])))
        index = [{'page': num + 1, 'startId': i} for num, i in
                 enumerate(e_list)]
        parser['first'] = Pagination.get_by_page(index, parser) \
            if parser['page'] else parser['first']
        total = Pagination.get_start_entity(total, parser) \
            if parser['last'] or parser['first'] else total
        j = [i for i, x in enumerate(entities) if x.id == total[0]]
        new_entities = [e for idx, e in enumerate(entities[j[0]:])]
        return {
            "results": Pagination.get_results(new_entities, parser),
            "pagination": {
                'entitiesPerPage': int(parser['limit']),
                'entities': count,
                'index': index,
                'totalPages': len(index)}}

    @staticmethod
    def get_results(
            new_entities: list[Entity],
            parser: dict[str, Any]) -> list[dict[str, Any]]:
        if parser['format'] == 'geojson':
            return [Pagination.get_geojson(new_entities, parser)]
        return Pagination.linked_places_result(
            new_entities[:int(parser['limit'])],
            parser,
            Pagination.link_builder(new_entities, parser),
            Pagination.link_builder(new_entities, parser, True))

    @staticmethod
    def get_entities_by_type(
            entities: list[Entity],
            parser: dict[str, Any]) -> list[Entity]:
        new_entities = []
        for entity in entities:
            if any(ids in [key.id for key in entity.types]
                   for ids in parser['type_id']):
                new_entities.append(entity)
        return new_entities

    @staticmethod
    def link_builder(
            new_entities: list[Entity],
            parser: dict[str, Any],
            inverse: bool = False) -> list[Link]:
        if any(i in ['relations', 'types', 'depictions', 'links', 'geometry']
               for i in parser['show']):
            entities = [e.id for e in new_entities[:int(parser['limit'])]]
            return get_all_links_inverse(entities) \
                if inverse else get_all_links(entities)
        return []

    @staticmethod
    def linked_places_result(
            entities: list[Entity],
            parser: dict[str, str],
            links: list[Link],
            links_inverse: list[Link]) -> list[dict[str, Any]]:
        return [
            LinkedPlaces.get_entity(
                get_entity_by_id(entity.id) if 'names' in parser['show']
                else entity,
                [link_ for link_ in links if link_.domain.id == entity.id],
                [link_ for link_ in links_inverse if
                 link_.range.id == entity.id],
                parser)
            for entity in entities]

    @staticmethod
    def get_geojson(
            entity_limit: list[Entity],
            parser: dict[str, str]) -> dict[str, Any]:
        return Geojson.return_output(
            Geojson.get_geojson(entity_limit[:int(parser['limit'])]))
