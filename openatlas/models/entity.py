# Copyright 2017 by Alexander Watzinger and others. Please see README.md for licensing information
import ast
from collections import OrderedDict
import openatlas
from openatlas.models.date import DateMapper
from openatlas.models.link import LinkMapper
from .classObject import ClassMapper


class Entity(object):
    def __init__(self, row):
        self.id = row.id
        self.nodes = []
        if hasattr(row, 'types') and row.types:
            nodes_list = ast.literal_eval('[' + row.types + ']')
            # converting nodes_list to set, to list to avoid duplicates (from the sql statement)
            for node_id in list(set(nodes_list)):
                self.nodes.append(openatlas.nodes[node_id])
        self.name = row.name
        self.root = None
        self.description = row.description if row.description else ''
        self.system_type = row.system_type
        self.created = row.created
        self.modified = row.modified
        self.first = int(row.first) if hasattr(row, 'first') and row.first else None
        self.last = int(row.last) if hasattr(row, 'last') and row.last else None
        self.class_ = openatlas.classes[row.class_id]
        self.dates = {}

    def get_linked_entity(self, code, inverse=False):
        return LinkMapper.get_linked_entity(self, code, inverse)

    def get_linked_entities(self, code, inverse=False):
        return LinkMapper.get_linked_entities(self, code, inverse)

    def link(self, code, range_, description=False):
        return LinkMapper.insert(self, code, range_, description)

    def get_links(self, code, inverse=False):
        return LinkMapper.get_links(self, code, inverse)

    def delete_links(self, codes):
        LinkMapper.delete_by_codes(self, codes)

    def update(self):
        EntityMapper.update(self)

    def save_dates(self, form):
        DateMapper.save_dates(self, form)

    def save_nodes(self, form):
        openatlas.NodeMapper.save_entity_nodes(self, form)

    def set_dates(self):
        self.dates = DateMapper.get_dates(self)

    def print_base_type(self):
        if self.class_.code in openatlas.app.config['CLASS_CODES']['actor']:
            return ''  # actors have no base type
        root_name = openatlas.app.config['CODE_CLASS'][self.class_.code].title()
        if self.class_.code in openatlas.app.config['CLASS_CODES']['place']:
            root_name = 'Site'
        elif self.class_.code in openatlas.app.config['CLASS_CODES']['reference']:
            root_name = self.system_type.title()
        root_id = openatlas.NodeMapper.get_hierarchy_by_name(root_name).id
        for node in self.nodes:
            if node.root and node.root[-1] == root_id:
                return node.name
        return ''


class EntityMapper(object):
    # Todo: performance - refactor sub selects, get_by_class
    # Todo: performance - use first and last only for get_by_codes?
    sql = """
        SELECT
            e.id, e.class_id, e.name, e.description, e.created, e.modified, c.code,
                e.value_timestamp, e.value_integer, e.system_type,
            string_agg(CAST(t.id AS text), ',') AS types,
            min(date_part('year', d1.value_timestamp)) AS first,
            max(date_part('year', d2.value_timestamp)) AS last

        FROM model.entity e
        JOIN model.class c ON e.class_id = c.id

        LEFT JOIN model.link tl ON e.id = tl.domain_id
        LEFT JOIN model.entity t ON
            tl.range_id = t.id
                AND tl.property_id IN (SELECT id FROM model.property WHERE code IN ('P2', 'P89'))

        LEFT JOIN model.link dl1 ON e.id = dl1.domain_id
            AND dl1.property_id IN
                (SELECT id FROM model.property WHERE code in ('OA1', 'OA3', 'OA5'))
        LEFT JOIN model.entity d1 ON dl1.range_id = d1.id

        LEFT JOIN model.link dl2 ON e.id = dl2.domain_id
            AND dl2.property_id IN 
                (SELECT id FROM model.property WHERE code in ('OA2', 'OA4', 'OA6'))
        LEFT JOIN model.entity d2 ON dl2.range_id = d2.id"""

    @staticmethod
    def update(entity):
        from openatlas.util.util import sanitize
        sql = """
            UPDATE model.entity
            SET (name, description) = (%(name)s, %(description)s)
            WHERE id = %(id)s;"""
        cursor = openatlas.get_cursor()
        cursor.execute(sql, {
            'id': entity.id,
            'name': entity.name,
            'description': sanitize(entity.description, 'description')})

    @staticmethod
    def insert(code, name, system_type=None, description=None, date=None):
        sql = """
            INSERT INTO model.entity (
                name,
                system_type,
                class_id,
                description,
                value_timestamp)
            VALUES (
                %(name)s,
                %(system_type)s,
                (SELECT id FROM model.class WHERE code = %(code)s),
                %(description)s,
                %(value_timestamp)s
            ) RETURNING id;"""
        params = {
            'name': date if date else name.strip(),
            'code': code,
            'system_type': system_type.strip() if system_type else None,
            'description': description.strip() if description else None,
            'value_timestamp': date}
        cursor = openatlas.get_cursor()
        cursor.execute(sql, params)
        return EntityMapper.get_by_id(cursor.fetchone()[0])

    @staticmethod
    def get_by_id(entity_id):
        sql = EntityMapper.sql + ' WHERE e.id = %(id)s GROUP BY e.id, c.code ORDER BY e.name;'
        cursor = openatlas.get_cursor()
        cursor.execute(sql, {'id': entity_id})
        openatlas.debug_model['by id'] += 1
        return Entity(cursor.fetchone())

    @staticmethod
    def get_by_ids(entity_ids):
        if not entity_ids:
            return []
        sql = EntityMapper.sql + ' WHERE e.id IN %(ids)s GROUP BY e.id, c.code ORDER BY e.name;'
        cursor = openatlas.get_cursor()
        cursor.execute(sql, {'ids': tuple(entity_ids)})
        openatlas.debug_model['by id'] += 1
        entities = []
        for row in cursor.fetchall():
            entities.append(Entity(row))
        return entities

    @staticmethod
    def get_by_codes(class_name):
        class_ids = []
        for code in openatlas.app.config['CLASS_CODES'][class_name]:
            class_ids.append(ClassMapper.get_by_code(code).id)
        cursor = openatlas.get_cursor()
        if class_name == 'source':
            sql = EntityMapper.sql + """
                WHERE e.class_id IN %(class_ids)s AND e.system_type ='source content'
                GROUP BY e.id, c.code ORDER BY e.name;"""
            cursor.execute(sql, {'class_ids': tuple(class_ids)})
        else:
            sql = EntityMapper.sql + """
                WHERE e.class_id IN %(class_ids)s
                GROUP BY e.id, c.code ORDER BY e.name;"""
            cursor.execute(sql, {'class_ids': tuple(class_ids)})
        openatlas.debug_model['by codes'] += 1
        entities = []
        for row in cursor.fetchall():
            entities.append(Entity(row))
        return entities

    @staticmethod
    def delete(entity_id):
        if isinstance(entity_id, Entity):
            entity_id = entity_id.id
        sql = "DELETE FROM model.entity WHERE id = %(entity_id)s;"
        openatlas.get_cursor().execute(sql, {'entity_id': entity_id})

    @staticmethod
    def get_overview_counts():
        sub_select = 'SELECT COUNT(*) FROM model.entity e JOIN model.class c ON e.class_id = c.id'
        sql = """
            SELECT
            ({sub_select} WHERE c.code = 'E33') AS source,
            ({sub_select} WHERE c.code IN ('E6', 'E7', 'E8', 'E12')) AS event,
            ({sub_select} WHERE c.code IN ('E21', 'E74', 'E40')) AS actor,
            ({sub_select} WHERE c.code = 'E18') AS place,
            COUNT(*) AS reference FROM model.entity e JOIN model.class c ON e.class_id = c.id
                WHERE c.code IN ('E31', 'E84');""".format(sub_select=sub_select)
        cursor = openatlas.get_cursor()
        cursor.execute(sql)
        row = cursor.fetchone()
        counts = OrderedDict()  # Todo: one liner to get a dict of record?
        for idx, col in enumerate(cursor.description):
            counts[col[0]] = row[idx]
        return counts

    @staticmethod
    def get_page_ids(entity, codes):
        """
        Return ids for pager (first, previous, next, last) for entity and class codes arguments
        """
        sql_where = " c.code IN ('{codes}')".format(codes="','".join(codes)) + " AND "
        sql_where += "e.system_type='source content'" if 'E33' in codes else "e.system_type IS NULL"
        sql_prev = """
            SELECT max(e.id) AS id FROM model.entity e
            JOIN model.class c ON e.class_id = c.id WHERE e.id < %(id)s AND """ + sql_where
        sql_next = """
            SELECT min(e.id) AS id FROM model.entity e
            JOIN model.class c ON e.class_id = c.id WHERE e.id > %(id)s AND """ + sql_where
        sql = """
            SELECT min(e.id) AS first_id, max(e.id) AS last_id,
            ({sql_next}) AS next_id, ({sql_prev}) AS previous_id
            FROM model.entity e JOIN model.class c ON e.class_id = c.id WHERE """.format(
                sql_next=sql_next, sql_prev=sql_prev) + sql_where
        cursor = openatlas.get_cursor()
        cursor.execute(sql, {'id': entity.id})
        return cursor.fetchone()
