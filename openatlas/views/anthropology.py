from typing import Union

from flask import render_template, url_for
from flask_babel import lazy_gettext as _
from flask_wtf import FlaskForm
from werkzeug.wrappers import Response
from wtforms import SubmitField

from openatlas import app
from openatlas.forms.field import TreeField
from openatlas.models.entity import Entity
from openatlas.models.node import Node
from openatlas.util.util import required_group


@app.route('/anthropology/index/<int:id_>')
@required_group('readonly')
def anthropology_index(id_: int) -> Union[str, Response]:
    entity = Entity.get_by_id(id_)
    return render_template(
        'anthropology/index.html',
        entity=entity,
        crumbs=[entity, _('anthropological analyzes')])


@app.route('/anthropology/sex/<int:id_>')
@required_group('readonly')
def anthropology_sex(id_: int) -> Union[str, Response]:
    entity = Entity.get_by_id(id_)
    return render_template(
        'anthropology/sex.html',
        entity=entity,
        crumbs=[
            entity,
            [_('anthropological analyzes'), url_for('anthropology_index', id_=entity.id)],
            _('sex estimation')])


@app.route('/anthropology/sex/update/<int:id_>', methods=['POST', 'GET'])
@required_group('contributor')
def anthropology_sex_update(id_: int) -> Union[str, Response]:

    class Form(FlaskForm):  # type: ignore
        pass

    node = Node.get_hierarchy('Sex estimation')
    setattr(Form, str(node.id), TreeField('Glabella'))
    setattr(Form, 'save', SubmitField(_('save me')))
    form = Form()

    entity = Entity.get_by_id(id_)
    return render_template(
        'anthropology/sex_update.html',
        entity=entity,
        form=form,
        crumbs=[
            entity,
            [_('anthropological analyzes'), url_for('anthropology_index', id_=entity.id)],
            [_('sex estimation'), url_for('anthropology_sex', id_=entity.id)],
            _('edit')])
