import datetime
from flask import render_template, request, make_response, Flask, redirect, url_for
from data import db_session as db_sess
from data.case_table import Case
from data.comment_table import Comment


app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False


@app.route('/')
def home():
    sess = db_sess.create_session()
    
    view = request.args.get('view', 'all')
    date_str = request.args.get('date', datetime.date.today().isoformat())
    
    try:
        target_date = datetime.date.fromisoformat(date_str)
    except (ValueError, TypeError):
        target_date = datetime.date.today()

    cases = []
    error_message = None
    try:
        query = sess.query(Case)
        
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
            
        cases = query.order_by(Case.deadline.asc()).all()
        
    except Exception as e:
        error_message = "Внимание: некоторые записи в архиве повреждены и были пропущены."
        cases = []

    res = make_response(
        render_template(
            'home.html', 
            cases=cases, 
            current_view=view, 
            current_date=target_date.isoformat(),
            error_message=error_message
        )
    )
    return res


@app.route('/create_case', methods=['POST'])
def create_case():
    sess = db_sess.create_session()
    try:
        # Извлекаем данные из POST-запроса формы
        guild = request.form.get('guild')
        title = request.form.get('title')
        description = request.form.get('description')
        promised_str = request.form.get('promised_at')
        deadline_str = request.form.get('deadline')

        # Конвертируем строки дат в объекты datetime.date (или datetime.datetime)
        promised_at = datetime.date.fromisoformat(promised_str) if promised_str else datetime.date.today()
        deadline = datetime.date.fromisoformat(deadline_str) if deadline_str else None

        # Создаем экземпляр модели Case
        new_case = Case(
            guild=guild,
            title=title,
            description=description,
            promised_at=datetime.datetime.combine(promised_at, datetime.time.min),
            deadline=datetime.datetime.combine(deadline, datetime.time.max) if deadline else None,
            status='active'
        )

        # Сохраняем в базу данных
        sess.add(new_case)
        sess.commit()
    except Exception as e:
        sess.rollback()
        # В случае ошибки можно было бы залогировать, но сессия закроется автоматически
        print(f"Ошибка при создании дела: {e}")
    finally:
        sess.close()

    # Перенаправляем обратно на главную страницу
    return redirect(url_for('home'))


@app.route('/case/<int:case_id>', methods=['GET'])
def view_case(case_id):
    sess = db_sess.create_session()
    try:
        case = sess.query(Case).filter(Case.id == case_id).first()
        if not case:
            return redirect(url_for('home'))
        
        # Получаем комментарии, отсортированные от старых к новым
        comments = sess.query(Comment).filter(Comment.case_id == case_id).order_by(Comment.timestamp.asc()).all()
        
        return render_template('case.html', case=case, comments=comments)
    except Exception as e:
        print(f"Ошибка при получении карточки дела: {e}")
        return redirect(url_for('home'))
    finally:
        sess.close()


@app.route('/case/<int:case_id>/add_comment', methods=['POST'])
def add_comment(case_id):
    sess = db_sess.create_session()
    try:
        text = request.form.get('text')
        if text and text.strip():
            new_comment = Comment(
                case_id=case_id,
                text=text.strip(),
                timestamp=datetime.datetime.now()  # Точная отметка времени
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
    sess = db_sess.create_session()
    try:
        case = sess.query(Case).filter(Case.id == case_id).first()
        if case:
            case.status = 'closed' if case.status == 'active' else 'active'
            sess.commit()
    except Exception as e:
        sess.rollback()
        print(f"Ошибка при изменении статуса: {e}")
    finally:
        sess.close()

    return redirect(url_for('view_case', case_id=case_id))

if __name__ == '__main__':
    db_sess.global_init('store.db')
    app.run()