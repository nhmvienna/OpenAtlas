from __future__ import annotations  # Needed for Python 4.0 type annotations

from typing import Optional, TYPE_CHECKING

from flask import g, url_for
from flask_babel import lazy_gettext as _
from flask_login import current_user

from openatlas.util.table import Table
from openatlas.util.util import button, is_authorized, uc_first

if TYPE_CHECKING:  # pragma: no cover
    from openatlas.models.entity import Entity

# Needed for translations of tab titles
_('member of')
_('texts')
_('invalid dates')
_('invalid link dates')
_('invalid involvement dates')
_('unlinked')
_('missing files')
_('orphaned files')
_('circular dependencies')


class Tab:

    def __init__(
            self,
            name: str,
            content: Optional[str] = None,
            table: Optional[Table] = None,
            buttons: Optional[list[str]] = None,
            entity: Optional[Entity] = None) -> None:

        self.name = name
        self.content = content
        self.title = uc_first(_(name.replace('_', ' ')))
        self.entity = entity
        self.table = table if table else Table()
        self.set_table_headers(name, entity)
        self.buttons: list[str] = []
        if is_authorized('contributor'):
            self.set_buttons(name, buttons, entity)

    def set_table_headers(
            self,
            name: str,
            entity: Optional[Entity] = None) -> None:
        view = entity.class_.view if entity else None
        if entity:
            if not self.table.header:
                self.table.header = g.table_headers[name]
        if name == 'reference' or entity and entity.class_.view == 'reference':
            self.table.header = self.table.header + ['page']
        if name == 'actor':
            if view == 'place':
                self.table.header = [
                    'actor',
                    'property',
                    'class',
                    'first',
                    'last',
                    'description']
            elif view == 'event':
                self.table.header = [
                    'actor',
                    'class',
                    'involvement',
                    'first',
                    'last',
                    'description']
        elif name == 'event':
            if view == 'actor':
                self.table.header = [
                    'event',
                    'class',
                    'involvement',
                    'first',
                    'last', 'description']
        elif name == 'file':
            if view != 'reference':
                self.table.header += [_('main image')]
        elif name == 'subs':
            self.table.header = [_('name'), _('count'), _('info')]
            if view == 'event':
                self.table.header = g.table_headers['event']

    def set_buttons(
            self,
            name: str,
            buttons: Optional[list[str]],
            entity: Optional[Entity] = None) -> None:

        view = entity.class_.view if entity else None
        id_ = entity.id if entity else None
        class_ = entity.class_ if entity else None

        self.buttons = buttons if buttons else []
        if name == 'actor':
            if view == 'file':
                self.buttons.append(
                    button('link', url_for('file_add', id_=id_, view=name)))
            elif view == 'reference':
                self.buttons.append(
                    button(
                        'link',
                        url_for('reference_add', id_=id_, view=name)))
            elif view == 'source':
                self.buttons.append(
                    button('link', url_for('link_insert', id_=id_, view=name)))
            elif view == 'event':
                self.buttons.append(button(
                    'link',
                    url_for('involvement_insert', origin_id=id_)))
            for item in g.view_class_mapping['actor']:
                self.buttons.append(button(
                    g.classes[item].label,
                    url_for('insert', class_=item, origin_id=id_)))
        elif name == 'artifact':
            if class_ and class_.name != 'stratigraphic_unit':
                self.buttons.append(
                    button(
                        'link',
                        url_for('link_insert', id_=id_, view='artifact')))
            self.buttons.append(
                button(
                    g.classes[name].label,
                    url_for('insert', class_=name, origin_id=id_)))
        elif name == 'entities':
            if id_:
                self.buttons.append(
                    button(
                        _('move entities'),
                        url_for('type_move_entities', id_=id_)))
        elif name == 'event':
            if view == 'file':
                self.buttons.append(
                    button('link', url_for('file_add', id_=id_, view='event')))
            elif view == 'actor':
                self.buttons.append(
                    button(
                        'link',
                        url_for('involvement_insert', origin_id=id_)))
            elif view == 'source':
                self.buttons.append(
                    button(
                        'link',
                        url_for('link_insert', id_=id_, view='event')))
            elif view == 'reference':
                self.buttons.append(
                    button(
                        'link',
                        url_for('reference_add', id_=id_, view='event')))
            if view == 'artifact':
                for item in ['move', 'production']:
                    self.buttons.append(
                        button(
                            g.classes[item].label,
                            url_for('insert', class_=item, origin_id=id_)))
            else:
                for item in g.view_class_mapping['event']:
                    self.buttons.append(
                        button(
                            g.classes[item].label,
                            url_for('insert', class_=item, origin_id=id_)))
        elif name == 'feature':
            if current_user.settings['module_sub_units'] \
                    and class_ \
                    and class_.name == 'place':
                self.buttons.append(
                    button(
                        g.classes[name].label,
                        url_for('insert', class_=name, origin_id=id_)))
        elif name == 'file':
            if view == 'reference':
                self.buttons.append(
                    button(
                        'link',
                        url_for('reference_add', id_=id_, view=name)))
            else:
                self.buttons.append(
                    button('link', url_for('entity_add_file', id_=id_)))
            self.buttons.append(
                button(
                    g.classes[name].label,
                    url_for('insert', class_=name, origin_id=id_)))
        elif name == 'human_remains':
            if current_user.settings['module_sub_units'] \
                    and class_ \
                    and class_.name == 'stratigraphic_unit':
                self.buttons.append(
                    button(
                        g.classes[name].label,
                        url_for('insert', origin_id=id_, class_=name)))
        elif name == 'member':
            self.buttons.append(
                button('link', url_for('member_insert', origin_id=id_)))
        elif name == 'member_of':
            self.buttons.append(button(
                'link',
                url_for('member_insert', origin_id=id_, code='membership')))
        elif name == 'note' and is_authorized('contributor'):
            self.buttons.append(
                button(_('note'), url_for('note_insert', entity_id=id_)))
        elif name == 'place':
            if class_ and class_.name == 'file':
                self.buttons.append(
                    button('link', url_for('file_add', id_=id_, view=name)))
            elif view == 'reference':
                self.buttons.append(
                    button(
                        'link',
                        url_for('reference_add', id_=id_, view=name)))
            elif view == 'source':
                self.buttons.append(
                    button('link', url_for('link_insert', id_=id_, view=name)))
            self.buttons.append(button(
                g.classes[name].label,
                url_for('insert', class_=name, origin_id=id_)))
        elif name == 'reference':
            self.buttons.append(
                button('link', url_for('entity_add_reference', id_=id_)))
            for item in g.view_class_mapping['reference']:
                self.buttons.append(button(
                    g.classes[item].label,
                    url_for('insert', class_=item, origin_id=id_)))
        elif name == 'relation':
            self.buttons.append(
                button('link', url_for('relation_insert', origin_id=id_)))
            for item in g.view_class_mapping['actor']:
                self.buttons.append(
                    button(
                        g.classes[item].label,
                        url_for('insert', class_=item, origin_id=id_)))
        elif name == 'source':
            if class_ and class_.name == 'file':
                self.buttons.append(
                    button(_('link'), url_for('file_add', id_=id_, view=name)))
            elif view == 'reference':
                self.buttons.append(
                    button(
                        'link',
                        url_for('reference_add', id_=id_, view=name)))
            else:
                self.buttons.append(
                    button('link', url_for('entity_add_source', id_=id_)))
            self.buttons.append(
                button(
                    g.classes['source'].label,
                    url_for('insert', class_=name, origin_id=id_)))
        elif name == 'stratigraphic_unit':
            if current_user.settings['module_sub_units'] \
                    and class_ \
                    and class_.name == 'feature':
                self.buttons.append(
                    button(
                        g.classes['stratigraphic_unit'].label,
                        url_for('insert', class_=name, origin_id=id_)))
        elif name == 'text':
            self.buttons.append(button(
                _('text'),
                url_for('insert', class_='source_translation', origin_id=id_)))
