import datetime
from flask import Flask, render_template, request, redirect, url_for
from data import db_session
from data.case_table import Case
from data.comment_table import Comment
from data.guild_table import Guild
from sqlalchemy.orm import selectinload

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_patrician_diary_key'


@app.route('/')
def home():
    sess = db_session.create_session()
    view = request.args.get('view', 'all')
    date_str = request.args.get('date', datetime.date.today().isoformat())

    start_str = request.args.get('start_date', '')
    end_str = request.args.get('end_date', '')
    status_filter = request.args.get('status_filter', 'all')

    guild_filter = request.args.getlist('guild_id')

    display_mode = request.args.get('display_mode', 'cards')

    try:
        target_date = datetime.date.fromisoformat(date_str)
    except (ValueError, TypeError):
        target_date = datetime.date.today()

    cases = []
    guilds = []
    error_message = None

    try:
        guilds = sess.query(Guild).order_by(Guild.name.asc()).all()
        query = sess.query(Case)

        if guild_filter:
            try:
                guild_ids = [int(g) for g in guild_filter]
                query = query.filter(Case.guild_id.in_(guild_ids))
            except (ValueError, TypeError):
                pass

        if view == 'day':
            start_dt = datetime.datetime.combine(target_date, datetime.time.min)
            end_dt = datetime.datetime.combine(target_date, datetime.time.max)
            query = query.filter(Case.deadline >= start_dt, Case.deadline <= end_dt)

        elif view == 'week':
            start_week = target_date - datetime.timedelta(days=target_date.weekday())
            end_week = start_week + datetime.timedelta(days=6)
            start_dt = datetime.datetime.combine(start_week, datetime.time.min)
            end_dt = datetime.datetime.combine(end_week, datetime.time.max)
            query = query.filter(Case.deadline >= start_dt, Case.deadline <= end_dt)

        elif view == 'month':
            start_month = target_date.replace(day=1)
            if target_date.month == 12:
                end_month = target_date.replace(year=target_date.year + 1, month=1, day=1) - datetime.timedelta(days=1)
            else:
                end_month = target_date.replace(month=target_date.month + 1, day=1) - datetime.timedelta(days=1)
            start_dt = datetime.datetime.combine(start_month, datetime.time.min)
            end_dt = datetime.datetime.combine(end_month, datetime.time.max)
            query = query.filter(Case.deadline >= start_dt, Case.deadline <= end_dt)

        elif view == 'range' and start_str and end_str:
            start_dt_val = datetime.date.fromisoformat(start_str)
            end_dt_val = datetime.date.fromisoformat(end_str)
            start_dt = datetime.datetime.combine(start_dt_val, datetime.time.min)
            end_dt = datetime.datetime.combine(end_dt_val, datetime.time.max)
            query = query.filter(Case.deadline >= start_dt, Case.deadline <= end_dt)

        now = datetime.datetime.now()
        if status_filter == 'active':
            query = query.filter(Case.status == 'active')
        elif status_filter == 'closed':
            query = query.filter(Case.status == 'closed')
        elif status_filter == 'overdue':
            query = query.filter(Case.status == 'active', Case.deadline < now)
        elif status_filter == 'burning':
            three_days_later = now + datetime.timedelta(days=3)
            query = query.filter(Case.status == 'active', Case.deadline >= now, Case.deadline <= three_days_later)
        
        
        cases = (
            query
            .options(selectinload(Case.guild))
            .order_by(Case.deadline.asc())
            .all()
        )

    except Exception as e:
        error_message = f"Внимание: произошла ошибка при получении данных ({e})."
        cases = []
    finally:
        sess.close()

    return render_template(
        'home.html',
        cases=cases,
        guilds=guilds,
        current_view=view,
        current_date=target_date.isoformat(),
        start_date=start_str,
        end_date=end_str,
        status_filter=status_filter,
        guild_filter=guild_filter,   # теперь список, а не строка
        display_mode=display_mode,
        error_message=error_message
    )


@app.route('/create_case', methods=['POST'])
def create_case():
    sess = db_session.create_session()
    try:
        guild_name = (request.form.get('guild') or '').strip()
        title = (request.form.get('title') or '').strip()
        description = request.form.get('description')
        promised_str = request.form.get('promised_at')
        deadline_str = request.form.get('deadline')

        if not guild_name:
            guild_name = 'Без гильдии'
        if not title:
            title = 'Без названия'

        guild = sess.query(Guild).filter(Guild.name.ilike(guild_name)).first()
        if not guild:
            guild = Guild(name=guild_name)
            sess.add(guild)
            sess.flush()

        promised_at = datetime.date.fromisoformat(promised_str) if promised_str else datetime.date.today()
        deadline = datetime.date.fromisoformat(deadline_str) if deadline_str else None

        new_case = Case(
            guild_id=guild.id,
            title=title,
            description=description,
            promised_at=datetime.datetime.combine(promised_at, datetime.time.min),
            deadline=datetime.datetime.combine(deadline, datetime.time.max) if deadline else None,
            status='active'
        )

        sess.add(new_case)
        sess.commit()
    except Exception as e:
        sess.rollback()
        print(f"Ошибка при создании дела: {e}")
    finally:
        sess.close()

    return redirect(url_for('home'))


@app.route('/case/<int:case_id>', methods=['GET'])
def view_case(case_id):
    sess = db_session.create_session()
    try:
        case = (
            sess.query(Case)
            .options(selectinload(Case.guild))
            .filter(Case.id == case_id)
            .first()
        )
        if not case:
            return redirect(url_for('home'))
                
        comments = sess.query(Comment).filter(Comment.case_id == case_id).order_by(Comment.timestamp.asc()).all()
        return render_template('case.html', case=case, comments=comments)


    except Exception as e:
        print(f"Ошибка при загрузке дела: {e}")
        return redirect(url_for('home'))
    finally:
        sess.close()


@app.route('/case/<int:case_id>/add_comment', methods=['POST'])
def add_comment(case_id):
    sess = db_session.create_session()
    try:
        text = request.form.get('text')
        if text and text.strip():
            new_comment = Comment(
                case_id=case_id,
                text=text.strip(),
                timestamp=datetime.datetime.now()
            )
            sess.add(new_comment)
            sess.commit()
    except Exception as e:
        sess.rollback()
        print(f"Ошибка при добавлении комментария: {e}")
    finally:
        sess.close()
    
    return redirect(url_for('view_case', case_id=case_id))


@app.route('/case/<int:case_id>/toggle_status', methods=['POST'])
def toggle_case_status(case_id):
    sess = db_session.create_session()
    try:
        case = sess.query(Case).filter(Case.id == case_id).first()
        if case:
            case.status = 'closed' if case.status == 'active' else 'active'
            sess.commit()
    except Exception as e:
        sess.rollback()
        print(f"Ошибка при смене статуса: {e}")
    finally:
        sess.close()

    return redirect(url_for('view_case', case_id=case_id))


if __name__ == '__main__':
    db_session.global_init("diary.db")
    app.run(debug=True)