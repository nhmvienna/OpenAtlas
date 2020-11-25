import ast

from flask import g, request, session
from flask_babel import lazy_gettext as _
from flask_wtf import FlaskForm

from openatlas.models.date import Date
from openatlas.util.display import uc_first


def validate(self: FlaskForm) -> bool:
    valid = FlaskForm.validate(self)

    # Dates
    if hasattr(self, 'begin_year_from'):

        # Check date format, if valid put dates into a list called "dates" for further validation
        dates = {}
        for prefix in ['begin_', 'end_']:
            if getattr(self, prefix + 'year_to').data and not getattr(self,
                                                                      prefix + 'year_from').data:
                getattr(self, prefix + 'year_from').errors.append(
                    _("Required for time span"))
                valid = False
            for postfix in ['_from', '_to']:
                if getattr(self, prefix + 'year' + postfix).data:
                    date_ = Date.form_to_datetime64(
                        getattr(self, prefix + 'year' + postfix).data,
                        getattr(self, prefix + 'month' + postfix).data,
                        getattr(self, prefix + 'day' + postfix).data)
                    if not date_:
                        getattr(self, prefix + 'day' + postfix).errors.append(
                            _('not a valid date'))
                        valid = False
                    else:
                        dates[prefix + postfix.replace('_', '')] = date_

        # Check for valid date combination e.g. begin not after end
        if valid:
            for prefix in ['begin', 'end']:
                if prefix + '_from' in dates and prefix + '_to' in dates:
                    if dates[prefix + '_from'] > dates[prefix + '_to']:
                        field = getattr(self, prefix + '_day_from')
                        field.errors.append(_('First date cannot be after second.'))
                        valid = False
        if 'begin_from' in dates and 'end_from' in dates:
            field = getattr(self, 'begin_day_from')
            if len(dates) == 4:  # All dates are used
                if dates['begin_from'] > dates['end_from'] or dates['begin_to'] > dates['end_to']:
                    field.errors.append(_('Begin dates cannot start after end dates.'))
                    valid = False
            else:
                first = dates['begin_to'] if 'begin_to' in dates else dates['begin_from']
                second = dates['end_from'] if 'end_from' in dates else dates['end_to']
                if first > second:
                    field.errors.append(_('Begin dates cannot start after end dates.'))
                    valid = False

    # File
    if request.files:
        file_ = request.files['file']
        ext = session['settings']['file_upload_allowed_extension']
        if not file_:  # pragma: no cover
            self.file.errors.append(_('no file to upload'))
            valid = False
        elif not ('.' in file_.filename and file_.filename.rsplit('.', 1)[1].lower() in ext):
            self.file.errors.append(_('file type not allowed'))
            valid = False

    # Super event
    if hasattr(self, 'event') and hasattr(self, 'event_id'):
        """ Check if selected super event is allowed."""
        # Todo: also check if super is not a sub event of itself (recursively)
        if self.event.data:
            if str(self.event.data) == str(self.event_id.data):
                self.event.errors.append(_('error node self as super'))
                valid = False

    # External references
    if hasattr(self, 'wikidata_id') and self.wikidata_id.data:  # pragma: no cover
        if self.wikidata_id.data[0].upper() != 'Q' or not self.wikidata_id.data[1:].isdigit():
            self.wikidata_id.errors.append(uc_first(_('wrong Wikidata Id format') + '.'))
            valid = False
        else:
            self.wikidata_id.data = uc_first(self.wikidata_id.data)
    for name in g.external:
        if hasattr(self, name + '_id'):
            if getattr(self, name + '_id').data and not getattr(self, name + '_precision').data:
                valid = False
                getattr(self, name + '_id').errors.append(uc_first(_('precision required')))

    # Membership
    if hasattr(self, 'member_origin_id'):
        member = getattr(self, 'actor') if hasattr(self, 'actor') else getattr(self, 'group')
        if self.member_origin_id.data in ast.literal_eval(member.data):
            member.errors.append(_("Can't link to itself."))
            valid = False

    # Actor actor relation
    if hasattr(self, 'relation_origin_id'):
        if self.relation_origin_id.data in ast.literal_eval(self.actor.data):
            self.actor.errors.append(_("Can't link to itself."))
            valid = False

    return valid
