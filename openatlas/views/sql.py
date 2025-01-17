from flask import flash, g, render_template, url_for
from flask_babel import lazy_gettext as _
from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField
from wtforms.validators import InputRequired

from openatlas import app, logger
from openatlas.database.connect import Transaction
from openatlas.util.util import get_backup_file_data, required_group


class SqlForm(FlaskForm):
    statement = TextAreaField(
        '',
        [InputRequired()],
        render_kw={'placeholder': 'SELECT code FROM model.cidoc_class;'})
    save = SubmitField(_('execute'))


@app.route('/sql')
@required_group('admin')
def sql_index() -> str:
    return render_template(
        'sql/index.html',
        title=_('SQL'),
        crumbs=[[_('admin'), f"{url_for('admin_index')}#tab-data"], _('SQL')])


@app.route('/sql/execute', methods=['POST', 'GET'])
@required_group('admin')
def sql_execute() -> str:
    file_data = get_backup_file_data()
    response = ''
    form = SqlForm()
    if form.validate_on_submit() and not file_data['backup_too_old']:
        Transaction.begin()
        try:
            g.cursor.execute(form.statement.data)
            response = f'<p>Rows affected: {g.cursor.rowcount}</p>'
            try:
                response += f'<p>{g.cursor.fetchall()}</p>'
            except Exception:  # pragma: no cover
                pass  # Assuming no SELECT statement so returning rowcount
            Transaction.commit()
            flash(_('SQL executed'), 'info')
            logger.log('info', 'database', 'SQL executed', form.statement.data)
        except Exception as e:
            Transaction.rollback()
            logger.log('error', 'database', 'transaction failed', e)
            response = str(e)
            flash(_('error transaction'), 'error')
    return render_template(
        'sql/execute.html',
        form=form,
        response=response,
        file_data=file_data,
        title=_('SQL'),
        crumbs=[
            [_('admin'), f"{url_for('admin_index')}#tab-data"],
            [_('SQL'), url_for('sql_index')],
            _('execute')])
