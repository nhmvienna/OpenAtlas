import ast

from flask import g, request
from flask_babel import lazy_gettext as _
from flask_wtf import FlaskForm

from openatlas.forms.util import form_to_datetime64
from openatlas.util.util import uc_first


def validate(self: FlaskForm) -> bool:
    valid = FlaskForm.validate(self)

    # Dates
    if hasattr(self, 'begin_year_from'):

        # Check date format, put in list "dates" for further validation
        dates = {}
        for prefix in ['begin_', 'end_']:
            if getattr(self, f'{prefix}year_to').data \
                    and not getattr(self, f'{prefix}year_from').data:
                getattr(self, prefix + 'year_from').errors.append(
                    _("Required for time span"))
                valid = False
            for postfix in ['_from', '_to']:
                if getattr(self, f'{prefix}year{postfix}').data:
                    date = form_to_datetime64(
                        getattr(self, f'{prefix}year{postfix}').data,
                        getattr(self, f'{prefix}month{postfix}').data,
                        getattr(self, f'{prefix}day{postfix}').data)
                    if not date:
                        getattr(self, f'{prefix}day{postfix}').errors.append(
                            _('not a valid date'))
                        valid = False
                    else:
                        dates[prefix + postfix.replace('_', '')] = date

        # Check for valid date combination e.g. begin not after end
        if valid:
            for prefix in ['begin', 'end']:
                if f'{prefix}_from' in dates \
                        and f'{prefix}_to' in dates \
                        and dates[f'{prefix}_from'] > dates[f'{prefix}_to']:
                    field = getattr(self, f'{prefix}_day_from')
                    field.errors.append(_('First date cannot be after second.'))
                    valid = False
        if 'begin_from' in dates and 'end_from' in dates:
            field = getattr(self, 'begin_day_from')
            if len(dates) == 4:  # All dates are used
                if dates['begin_from'] > dates['end_from'] \
                        or dates['begin_to'] > dates['end_to']:
                    field.errors.append(
                        _('Begin dates cannot start after end dates.'))
                    valid = False
            else:
                first = dates['begin_to'] \
                    if 'begin_to' in dates else dates['begin_from']
                second = dates['end_from'] \
                    if 'end_from' in dates else dates['end_to']
                if first > second:
                    field.errors.append(
                        _('Begin dates cannot start after end dates.'))
                    valid = False

    # File
    if request.files:
        for file_ in request.files.getlist('file'):
            if not file_:  # pragma: no cover
                self.file.errors.append(_('no file to upload'))
                valid = False
            elif not (
                    '.' in file_.filename
                    and file_.filename.rsplit('.', 1)[1].lower() in
                    g.settings['file_upload_allowed_extension']):
                self.file.errors.append(_('file type not allowed'))
                valid = False

    # Super event
    if hasattr(self, 'event') \
            and hasattr(self, 'event_id') \
            and self.event.data \
            and str(self.event.data) == str(self.event_id.data):
        self.event.errors.append(_('self as super not allowed'))
        valid = False

    # Preceding event
    if hasattr(self, 'event_preceding') \
            and self.event_preceding.data \
            and str(self.event_preceding.data) == str(self.event_id.data):
        self.event_preceding.errors.append(_('self as preceding not allowed'))
        valid = False

    # External reference systems
    for field_id, field in self.__dict__.items():
        if field_id.startswith('reference_system_id_') and field.data:
            if not getattr(self, field_id.replace('id_', 'precision_')).data:
                valid = False
                field.errors.append(uc_first(_('precision required')))
            if field.label.text == 'Wikidata':
                if field.data[0].upper() != 'Q' or not field.data[1:].isdigit():
                    field.errors.append(uc_first(_('wrong id format') + '.'))
                    valid = False
                else:
                    field.data = uc_first(field.data)
            if field.label.text == 'GeoNames' and not field.data.isnumeric():
                field.errors.append(uc_first(_('wrong id format') + '.'))
                valid = False

    # Membership
    if hasattr(self, 'member_origin_id'):
        member = getattr(self, 'actor') \
            if hasattr(self, 'actor') else getattr(self, 'group')
        if self.member_origin_id.data in ast.literal_eval(member.data):
            member.errors.append(_("Can't link to itself."))
            valid = False

    # Actor actor relation
    if hasattr(self, 'relation_origin_id') and \
            self.relation_origin_id.data in ast.literal_eval(self.actor.data):
        self.actor.errors.append(_("Can't link to itself."))
        valid = False
    return valid
