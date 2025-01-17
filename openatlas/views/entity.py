from typing import Any, Optional, Union

from flask import flash, g, render_template, request, url_for
from flask_babel import format_number, lazy_gettext as _
from flask_login import current_user
from werkzeug.exceptions import abort
from werkzeug.utils import redirect
from werkzeug.wrappers import Response

from openatlas import app
from openatlas.forms.form import build_table_form
from openatlas.models.entity import Entity
from openatlas.models.gis import Gis
from openatlas.models.link import Link
from openatlas.models.overlay import Overlay
from openatlas.models.place import get_structure
from openatlas.models.reference_system import ReferenceSystem
from openatlas.models.type import Type
from openatlas.models.user import User
from openatlas.util.tab import Tab
from openatlas.util.table import Table
from openatlas.util.util import (
    button, display_delete_link, format_date, get_base_table_data,
    get_entity_data, get_file_path, is_authorized, link, required_group,
    uc_first)
from openatlas.views.entity_index import file_preview
from openatlas.views.link import AddReferenceForm


@app.route('/entity/<int:id_>')
@required_group('readonly')
def view(id_: int) -> Union[str, Response]:
    if id_ in g.types:  # Types have their own view
        entity = g.types[id_]
        if not entity.root:
            return redirect(
                f"{url_for('type_index')}"
                f"#menu-tab-{entity.category}_collapse-{id_}")
    elif id_ in g.reference_systems:
        entity = g.reference_systems[id_]
    else:
        entity = Entity.get_by_id(id_, types=True, aliases=True)
        if not entity.class_.view:
            flash(_("This entity can't be viewed directly."), 'error')
            abort(400)

    event_links = None  # Needed for actor and info data
    tabs = {'info': Tab('info')}
    if isinstance(entity, Type):
        tabs |= add_tabs_for_type(entity)
    elif isinstance(entity, ReferenceSystem):
        tabs |= add_tabs_for_reference_system(entity)
    elif entity.class_.view == 'actor':
        event_links = entity.get_links(
            ['P11', 'P14', 'P22', 'P23', 'P25'],
            True)
        tabs |= add_tabs_for_actor(entity, event_links)
    elif entity.class_.view == 'artifact':
        tabs['source'] = Tab('source', entity=entity)
    elif entity.class_.view == 'event':
        tabs |= add_tabs_for_event(entity)
    elif entity.class_.view == 'file':
        tabs |= add_tabs_for_file(entity)
    elif entity.class_.view == 'place':
        tabs |= add_tabs_for_place(entity)
    elif entity.class_.view == 'reference':
        tabs |= add_tabs_for_reference(entity)
    elif entity.class_.view == 'source':
        tabs |= add_tabs_for_source(entity)

    overlays = None  # Needed for place
    if entity.class_.view in [
            'actor', 'artifact', 'event', 'place', 'source', 'type']:
        if not isinstance(entity, Type):
            tabs['reference'] = Tab('reference', entity=entity)
        if entity.class_.view == 'artifact':
            tabs['event'] = Tab('event', entity=entity)
            for link_ in entity.get_links(['P25', 'P108'], True):
                data = get_base_table_data(link_.domain)
                tabs['event'].table.rows.append(data)
        tabs['file'] = Tab('file', entity=entity)
        entity.image_id = entity.get_profile_image_id()
        if entity.class_.view == 'place' \
                and is_authorized('editor') \
                and current_user.settings['module_map_overlay']:
            tabs['file'].table.header.append(uc_first(_('overlay')))
        for link_ in entity.get_links('P67', inverse=True):
            domain = link_.domain
            data = get_base_table_data(domain)
            if domain.class_.view == 'file':  # pragma: no cover
                extension = data[3]
                data.append(
                    get_profile_image_table_link(
                        domain,
                        entity,
                        extension,
                        entity.image_id))
                if not entity.image_id \
                        and extension in app.config['DISPLAY_FILE_EXTENSIONS']:
                    entity.image_id = domain.id
                if entity.class_.view == 'place' \
                        and is_authorized('editor') \
                        and current_user.settings['module_map_overlay']:
                    overlays = Overlay.get_by_object(entity)
                    if extension in app.config['DISPLAY_FILE_EXTENSIONS']:
                        if domain.id in overlays:
                            data.append(edit_link(
                                url_for(
                                    'overlay_update',
                                    id_=overlays[domain.id].id)))
                        else:
                            data.append(link(_('link'), url_for(
                                'overlay_insert',
                                image_id=domain.id,
                                place_id=entity.id,
                                link_id=link_.id)))
                    else:  # pragma: no cover
                        data.append('')
            if domain.class_.view not in ['source', 'file']:
                data.append(link_.description)
                data.append(edit_link(
                    url_for('link_update', id_=link_.id, origin_id=entity.id)))
                if domain.class_.view == 'reference_system':
                    entity.reference_systems.append(link_)
                    continue
            data.append(
                remove_link(domain.name, link_, entity, domain.class_.view))
            tabs[domain.class_.view].table.rows.append(data)

    if 'file' in tabs \
            and current_user.settings['table_show_icons'] \
            and g.settings['image_processing']:
        tabs['file'].table.header.insert(1, uc_first(_('icon')))
        for row in tabs['file'].table.rows:
            row.insert(
                1,
                file_preview(
                    int(row[0].replace('<a href="/entity/', '').split('"')[0])))

    place_structure = None
    gis_data = None
    if entity.class_.view in ['artifact', 'place']:
        place_structure = get_structure(entity)
        if place_structure:
            for item in place_structure['subunits']:
                tabs[item.class_.name].table.rows.append(
                    get_base_table_data(item))
        gis_data = Gis.get_all([entity], place_structure)
        if gis_data['gisPointSelected'] == '[]' \
                and gis_data['gisPolygonSelected'] == '[]' \
                and gis_data['gisLineSelected'] == '[]' \
                and (not place_structure or not place_structure['super_id']):
            gis_data = {}
    entity.info_data = get_entity_data(entity, event_links=event_links)
    if not gis_data:  # Has to be after get_entity_data()
        gis_data = Gis.get_all(entity.linked_places) \
            if entity.linked_places else None
    tabs['note'] = add_note_tab(entity)
    tabs['info'].content = render_template(
        'entity/view.html',
        buttons=add_buttons(entity),
        entity=entity,
        gis_data=gis_data,
        structure=place_structure,
        overlays=overlays,
        title=entity.name)
    return render_template(
        'tabs.html',
        tabs=tabs,
        gis_data=gis_data,
        crumbs=add_crumbs(entity, place_structure),
        entity=entity)


def get_profile_image_table_link(
        file: Entity,
        entity: Entity,
        extension: str,
        profile_image_id: Optional[int] = None) -> str:
    if file.id == profile_image_id:
        return link(
            _('unset'),
            url_for('file_remove_profile_image', entity_id=entity.id))
    if extension in app.config['DISPLAY_FILE_EXTENSIONS'] or (
            g.settings['image_processing']
            and extension in app.config['ALLOWED_IMAGE_EXT']):
        return link(
            _('set'),
            url_for('set_profile_image', id_=file.id, origin_id=entity.id))
    return ''  # pragma: no cover


def add_crumbs(
        entity: Union[Entity, Type],
        structure: Optional[dict[str, Any]]) -> list[str]:
    label = _(entity.class_.view.replace('_', ' '))
    crumbs = [
        [label, url_for('index', view=entity.class_.view)],
        entity.name]
    if structure:
        crumbs = [[g.classes['place'].label, url_for('index', view='place')]]
        if entity.class_.name == 'artifact':
            crumbs = [[
                g.classes['artifact'].label,
                url_for('index', view='artifact')]]
        crumbs += [
            structure['place'],
            structure['feature'],
            structure['stratigraphic_unit'],
            entity.name]
    elif isinstance(entity, Type):
        crumbs = [[_('types'), url_for('type_index')]]
        if entity.root:
            crumbs += [g.types[type_id] for type_id in entity.root]
        crumbs.append(entity.name)
    elif entity.class_.view == 'source_translation':
        crumbs = [
            [_('source'), url_for('index', view='source')],
            entity.get_linked_entity('P73', True),
            entity.name]
    return crumbs


def add_buttons(entity: Entity) -> list[str]:
    if not is_authorized(entity.class_.write_access):
        return []  # pragma: no cover
    buttons = []
    if isinstance(entity, Type):
        if entity.root and entity.category != 'system':
            buttons.append(button(_('edit'), url_for('update', id_=entity.id)))
            if not entity.count and not entity.subs:
                buttons.append(display_delete_link(entity))
    elif isinstance(entity, ReferenceSystem):
        buttons.append(button(_('edit'), url_for('update', id_=entity.id)))
        if not entity.classes and not entity.system:
            buttons.append(display_delete_link(entity))
    elif entity.class_.name == 'source_translation':
        buttons.append(button(_('edit'), url_for('update', id_=entity.id)))
        buttons.append(display_delete_link(entity))
    else:
        buttons.append(button(_('edit'), url_for('update', id_=entity.id)))
        if entity.class_.view != 'place' \
                or not entity.get_linked_entities('P46'):
            buttons.append(display_delete_link(entity))
    return buttons


@app.route('/entity/add/file/<int:id_>', methods=['GET', 'POST'])
@required_group('contributor')
def entity_add_file(id_: int) -> Union[str, Response]:
    entity = Entity.get_by_id(id_)
    if request.method == 'POST':
        if request.form['checkbox_values']:
            entity.link_string(
                'P67',
                request.form['checkbox_values'], inverse=True)
        return redirect(f"{url_for('view', id_=id_)}#tab-file")
    form = build_table_form(
        'file',
        entity.get_linked_entities('P67', inverse=True))
    return render_template(
        'form.html',
        entity=entity,
        form=form,
        title=entity.name,
        crumbs=[
            [_(entity.class_.view), url_for('index', view=entity.class_.view)],
            entity,
            f"{_('link')} {_('file')}"])


@app.route('/entity/add/source/<int:id_>', methods=['POST', 'GET'])
@required_group('contributor')
def entity_add_source(id_: int) -> Union[str, Response]:
    entity = Entity.get_by_id(id_)
    if request.method == 'POST':
        if request.form['checkbox_values']:
            entity.link_string(
                'P67',
                request.form['checkbox_values'],
                inverse=True)
        return redirect(f"{url_for('view', id_=id_)}#tab-source")
    form = build_table_form(
        'source',
        entity.get_linked_entities('P67', inverse=True))
    return render_template(
        'form.html',
        form=form,
        title=entity.name,
        crumbs=[
            [_(entity.class_.view), url_for('index', view=entity.class_.view)],
            entity,
            f"{_('link')} {_('source')}"])


@app.route('/entity/add/reference/<int:id_>', methods=['POST', 'GET'])
@required_group('contributor')
def entity_add_reference(id_: int) -> Union[str, Response]:
    entity = Entity.get_by_id(id_)
    form = AddReferenceForm()
    if form.validate_on_submit():
        entity.link_string(
            'P67',
            form.reference.data,
            description=form.page.data,
            inverse=True)
        return redirect(f"{url_for('view', id_=id_)}#tab-reference")
    form.page.label.text = uc_first(_('page / link text'))
    return render_template(
        'display_form.html',
        entity=entity,
        form=form,
        crumbs=[
            [_(entity.class_.view), url_for('index', view=entity.class_.view)],
            entity,
            f"{_('link')} {_('reference')}"])


def edit_link(url: str) -> Optional[str]:
    return link(_('edit'), url) if is_authorized('contributor') else None


def remove_link(
        name: str,
        link_: Link,
        origin: Entity,
        tab: str) -> Optional[str]:
    if not is_authorized('contributor'):
        return None  # pragma: no cover
    url = url_for('link_delete', id_=link_.id, origin_id=origin.id)
    return link(
        _('remove'),
        f'{url}#tab-{tab}',
        js="return confirm('{x}')".format(
            x=_('Remove %(name)s?', name=name.replace("'", ''))))


def add_tabs_for_type(entity: Type) -> dict[str, Tab]:
    tabs = {
        'subs': Tab('subs', entity=entity),
        'entities': Tab('entities', entity=entity)}
    for sub_id in entity.subs:
        sub = g.types[sub_id]
        tabs['subs'].table.rows.append([
            link(sub),
            sub.count,
            sub.description])
    if entity.category == 'value':
        tabs['entities'].table.header = \
            [_('name'), _('value'), _('class'), _('info')]
    for item in entity.get_linked_entities(
            ['P2', 'P89'],
            inverse=True,
            types=True):
        if item.class_.name in ['location', 'reference_system']:
            continue  # pragma: no cover
        if item.class_.name == 'object_location':
            item = item.get_linked_entity_safe('P53', inverse=True)
        data = [link(item)]
        if entity.category == 'value':
            data.append(format_number(item.types[entity]))
        data.append(item.class_.label)
        data.append(item.description)
        tabs['entities'].table.rows.append(data)
    if not tabs['entities'].table.rows:
        # If no entities available get links with this type_id
        tabs['entities'].table.header = [_('domain'), _('range')]
        for row in Link.get_links_by_type(entity):
            tabs['entities'].table.rows.append([
                link(Entity.get_by_id(row['domain_id'])),
                link(Entity.get_by_id(row['range_id']))])
    return tabs


def add_tabs_for_reference_system(entity: ReferenceSystem) -> dict[str, Tab]:
    tabs = {}
    for name in entity.classes:
        tabs[name] = Tab(
            name,
            entity=entity,
            table=Table([_('entity'), 'id', _('precision')]))
    for link_ in entity.get_links('P67'):
        name = link_.description
        if entity.resolver_url:
            name = \
                f'<a href="{entity.resolver_url}{name}"' \
                f' target="_blank" rel="noopener noreferrer">{name}</a>'
        tabs[link_.range.class_.name].table.rows.append([
            link(link_.range),
            name,
            link_.type.name])
    for name in entity.classes:
        tabs[name].buttons = []
        if not tabs[name].table.rows and is_authorized('manager'):
            tabs[name].buttons = [button(
                _('remove'),
                url_for(
                    'reference_system_remove_class',
                    system_id=entity.id,
                    class_name=name))]
    return tabs


def add_tabs_for_actor(
        entity: Entity,
        event_links: list[Link]) -> dict[str, Tab]:
    tabs = {}
    for name in [
            'source', 'event', 'relation', 'member_of', 'member', 'artifact']:
        tabs[name] = Tab(name, entity=entity)
    for link_ in event_links:
        event = link_.domain
        link_.object_ = None  # Needed for first/last appearance
        for place in event.get_linked_entities(['P7', 'P26', 'P27']):
            object_ = place.get_linked_entity_safe('P53', True)
            entity.linked_places.append(object_)
            link_.object_ = object_
        first = link_.first
        if not link_.first and event.first:
            first = f'<span class="inactive">{event.first}</span>'
        last = link_.last
        if not link_.last and event.last:
            last = f'<span class="inactive">{event.last}</span>'
        data = [
            link(event),
            event.class_.label,
            _('moved')
            if link_.property.code == 'P25' else link(link_.type),
            first,
            last,
            link_.description]
        if link_.property.code == 'P25':
            data.append('')
        else:
            data.append(edit_link(
                url_for('link_update', id_=link_.id, origin_id=entity.id)))
        data.append(remove_link(link_.domain.name, link_, entity, 'event'))
        tabs['event'].table.rows.append(data)
    for link_ in entity.get_links('OA7') + entity.get_links('OA7', True):
        type_ = ''
        if entity.id == link_.domain.id:
            related = link_.range
            if link_.type:
                type_ = link(
                    link_.type.get_name_directed(),
                    url_for('view', id_=link_.type.id))
        else:
            related = link_.domain
            if link_.type:
                type_ = link(
                    link_.type.get_name_directed(True),
                    url_for('view', id_=link_.type.id))
        tabs['relation'].table.rows.append([
            type_,
            link(related),
            link_.first,
            link_.last,
            link_.description,
            edit_link(
                url_for('link_update', id_=link_.id, origin_id=entity.id)),
            remove_link(related.name, link_, entity, 'relation')])
    for link_ in entity.get_links('P107', True):
        data = [
            link(link_.domain),
            link(link_.type),
            link_.first,
            link_.last,
            link_.description,
            edit_link(
                url_for('member_update', id_=link_.id, origin_id=entity.id)),
            remove_link(link_.domain.name, link_, entity, 'member-of')]
        tabs['member_of'].table.rows.append(data)
    if entity.class_.name != 'group':
        del tabs['member']
    else:
        for link_ in entity.get_links('P107'):
            tabs['member'].table.rows.append([
                link(link_.range),
                link(link_.type),
                link_.first,
                link_.last,
                link_.description,
                edit_link(
                    url_for('member_update', id_=link_.id, origin_id=entity.id)
                ),
                remove_link(link_.range.name, link_, entity, 'member')])
    for link_ in entity.get_links('P52', True):
        data = [
            link(link_.domain),
            link_.domain.class_.label,
            link(link_.domain.standard_type),
            link_.domain.first,
            link_.domain.last,
            link_.domain.description]
        tabs['artifact'].table.rows.append(data)
    return tabs


def add_tabs_for_event(entity: Entity) -> dict[str, Tab]:
    tabs = {}
    for name in ['subs', 'source', 'actor']:
        tabs[name] = Tab(name, entity=entity)
    for sub_event in entity.get_linked_entities('P9', inverse=True, types=True):
        tabs['subs'].table.rows.append(get_base_table_data(sub_event))
    tabs['actor'].table.header.insert(5, _('activity'))
    for link_ in entity.get_links(['P11', 'P14', 'P22', 'P23']):
        first = link_.first
        if not link_.first and entity.first:
            first = f'<span class="inactive">{entity.first}</span>'
        last = link_.last
        if not link_.last and entity.last:
            last = f'<span class="inactive">{entity.last}</span>'
        tabs['actor'].table.rows.append([
            link(link_.range),
            link_.range.class_.label,
            link_.type.name if link_.type else '',
            first,
            last,
            g.properties[link_.property.code].name_inverse,
            link_.description,
            edit_link(
                url_for('link_update', id_=link_.id, origin_id=entity.id)),
            remove_link(link_.range.name, link_, entity, 'actor')])
    entity.linked_places = [
        location.get_linked_entity_safe('P53', True) for location
        in entity.get_linked_entities(['P7', 'P26', 'P27'])]
    return tabs


def add_tabs_for_file(entity: Entity) -> dict[str, Tab]:
    tabs = {}
    for name in [
            'source', 'event', 'actor', 'place', 'feature',
            'stratigraphic_unit', 'artifact', 'human_remains', 'reference',
            'type']:
        tabs[name] = Tab(name, entity=entity)
    entity.image_id = entity.id if get_file_path(entity.id) else None
    for link_ in entity.get_links('P67'):
        range_ = link_.range
        data = get_base_table_data(range_)
        data.append(remove_link(range_.name, link_, entity, range_.class_.name))
        tabs[range_.class_.view].table.rows.append(data)
    for link_ in entity.get_links('P67', True):
        data = get_base_table_data(link_.domain)
        data.append(link_.description)
        data.append(edit_link(
            url_for('link_update', id_=link_.id, origin_id=entity.id)))
        data.append(remove_link(link_.domain.name, link_, entity, 'reference'))
        tabs['reference'].table.rows.append(data)
    return tabs


def add_tabs_for_place(entity: Entity) -> dict[str, Tab]:
    tabs = {'source': Tab('source', entity=entity)}
    if entity.class_.name == 'place':
        tabs['event'] = Tab('event', entity=entity)
    tabs['reference'] = Tab('reference', entity=entity)
    if entity.class_.name == 'place':
        tabs['actor'] = Tab('actor', entity=entity)
        tabs['feature'] = Tab('feature', entity=entity)
    elif entity.class_.name == 'feature':
        tabs['stratigraphic_unit'] = Tab(
            'stratigraphic_unit',
            entity=entity)
    elif entity.class_.name == 'stratigraphic_unit':
        tabs['artifact'] = Tab('artifact', entity=entity)
        tabs['human_remains'] = Tab('human_remains', entity=entity)
    entity.location = entity.get_linked_entity_safe('P53', types=True)
    events = []  # Collect events to display actors
    event_ids = []  # Keep track of event ids to prevent event doubles
    for event in entity.location.get_linked_entities(
            ['P7', 'P26', 'P27'],
            inverse=True):
        events.append(event)
        tabs['event'].table.rows.append(get_base_table_data(event))
        event_ids.append(event.id)
    for event in entity.get_linked_entities('P24', inverse=True):
        if event.id not in event_ids:  # Don't add again if already in table
            tabs['event'].table.rows.append(get_base_table_data(event))
            events.append(event)
    if entity.class_.name == 'place':
        for link_ in entity.location.get_links(
                ['P74', 'OA8', 'OA9'],
                inverse=True):
            actor = Entity.get_by_id(link_.domain.id)
            tabs['actor'].table.rows.append([
                link(actor),
                g.properties[link_.property.code].name,
                actor.class_.name,
                actor.first,
                actor.last,
                actor.description])
        actor_ids = []
        for event in events:
            for actor in event.get_linked_entities(
                    ['P11', 'P14', 'P22', 'P23']):
                if actor.id in actor_ids:
                    continue  # pragma: no cover
                actor_ids.append(actor.id)
                tabs['actor'].table.rows.append([
                    link(actor),
                    f"{_('participated at an event')}",
                    event.class_.name, '', '', ''])
    return tabs


def add_tabs_for_reference(entity: Entity) -> dict[str, Tab]:
    tabs = {}
    for name in [
            'source', 'event', 'actor', 'place', 'feature',
            'stratigraphic_unit', 'human_remains', 'artifact', 'file']:
        tabs[name] = Tab(name, entity=entity)
    for link_ in entity.get_links('P67'):
        range_ = link_.range
        data = get_base_table_data(range_)
        data.append(link_.description)
        data.append(edit_link(
            url_for('link_update', id_=link_.id, origin_id=entity.id)))
        data.append(remove_link(range_.name, link_, entity, range_.class_.name))
        tabs[range_.class_.view].table.rows.append(data)
    return tabs


def add_tabs_for_source(entity: Entity) -> dict[str, Tab]:
    tabs = {}
    for name in [
            'actor', 'artifact', 'feature', 'event', 'human_remains', 'place',
            'stratigraphic_unit', 'text']:
        tabs[name] = Tab(name, entity=entity)
    for text in entity.get_linked_entities('P73', types=True):
        tabs['text'].table.rows.append([
            link(text),
            next(iter(text.types)).name if text.types else '',
            text.description])
    for link_ in entity.get_links('P67'):
        range_ = link_.range
        data = get_base_table_data(range_)
        data.append(remove_link(range_.name, link_, entity, range_.class_.name))
        tabs[range_.class_.view].table.rows.append(data)
    return tabs


def add_note_tab(entity: Entity) -> Tab:
    tab = Tab('note', entity=entity)
    for note in current_user.get_notes_by_entity_id(entity.id):
        data = [
            format_date(note['created']),
            uc_first(_('public')) if note['public'] else uc_first(_('private')),
            link(User.get_by_id(note['user_id'])),
            note['text'],
            f'<a href="{url_for("note_view", id_=note["id"])}">'
            f'{uc_first(_("view"))}</a>']
        tab.table.rows.append(data)
    return tab
