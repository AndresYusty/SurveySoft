from flask import Blueprint, request, render_template, redirect, url_for, session, flash 
from services.survey_service import (
    get_all_surveys,
    get_survey_by_id,
    create_survey,
    update_survey,
    delete_survey,
    update_survey_items,
    save_survey_results,
    get_results_by_survey,
    calculate_overall_result,
    save_evaluation_form
)
from database import SessionLocal
from models.survey import Survey, SurveyResults, EvaluationForm
from uuid import uuid4  # Para generar UUID

question_bp = Blueprint('question', __name__)

# Ruta para listar encuestas
@question_bp.route('/surveys', methods=['GET'])
def surveys():
    if 'role' not in session or session['role'] != 'admin':
        flash("No tienes permiso para acceder a esta página.")
        return redirect('http://localhost:5001/auth/login')

    surveys = get_all_surveys()
    return render_template('survey/home.html', surveys=surveys)

# Ruta para el formulario de evaluación
@question_bp.route('/formulario', methods=['GET', 'POST'])
def formulario():
    if request.method == 'POST':
        data = {
            'date': request.form['date'],
            'city': request.form['city'],
            'company': request.form['company'],
            'phone': request.form['phone'],
            'software_name': request.form['software_name'],
            'general_objectives': request.form['general_objectives'],
            'specific_objectives': request.form['specific_objectives']
        }

        try:
            form_id = save_evaluation_form(data)  # Guardar el formulario y obtener su ID
            session['form_id'] = form_id  # Almacenar el ID del formulario en la sesión
            flash("Formulario guardado exitosamente.")
            return redirect(url_for('question.select_survey'))  # Redirigir a seleccionar encuesta
        except Exception as e:
            flash(f"Error al guardar el formulario: {e}", "error")

    return render_template('question/formulario.html')

# Ruta para seleccionar encuestas
@question_bp.route('/surveys/select', methods=['GET', 'POST'])
def select_survey():
    if 'user_id' not in session:
        flash("Debes iniciar sesión para seleccionar una encuesta.")
        return redirect('http://localhost:5001/auth/login')

    surveys = get_all_surveys()
    if request.method == 'POST':
        survey_id = request.form.get('survey_id')
        if survey_id:
            return redirect(url_for('question.complete_survey_view', survey_id=survey_id))
        else:
            flash("Por favor selecciona una encuesta.", "error")

    return render_template('survey/select_survey.html', surveys=surveys)

# Ruta para completar una encuesta
@question_bp.route('/surveys/<int:survey_id>/complete', methods=['GET', 'POST'])
def complete_survey_view(survey_id):
    user_id = session.get('user_id', -1)  # Asignar ID temporal para usuarios no autenticados
    form_id = session.get('form_id')

    if request.method == 'GET':
        survey = get_survey_by_id(survey_id)
        return render_template('survey/complete_survey.html', survey=survey)

    elif request.method == 'POST':
        total_score = 0
        item_scores = []

        # Procesar respuestas enviadas
        for key, value in request.form.items():
            if key.startswith('item_'):
                item_id = int(key.split('_')[1])
                score = int(value)
                total_score += score
                item_scores.append({
                    "item_id": item_id,
                    "score": score,
                    "percentage": (score / 3) * 100
                })

                # Guardar resultados individuales
                save_survey_results(
                    user_id=user_id,
                    survey_id=survey_id,
                    item_id=item_id,
                    total_score=score,
                    percentage=(score / 3) * 100,
                    overall_result="N/A",
                    form_id=form_id,
                    response_id=str(uuid4())  # Generar un UUID único
                )

        # Calcular y guardar resultado general
        overall_percentage = (total_score / (len(item_scores) * 3)) * 100
        overall_result = calculate_overall_result(overall_percentage)

        try:
            save_survey_results(
                user_id=user_id,
                survey_id=survey_id,
                item_id=None,
                total_score=total_score,
                percentage=overall_percentage,
                overall_result=overall_result,
                form_id=form_id,
                response_id=str(uuid4())
            )
        except Exception as e:
            flash("Error al guardar el resultado global.", "error")
            print(f"Error al guardar resultado global: {e}")

        flash("Encuesta completada exitosamente.")
        return redirect(url_for('question.survey_results_view', survey_id=survey_id))

# Ruta para visualizar resultados
@question_bp.route('/surveys/<int:survey_id>/results', methods=['GET'])
def survey_results_view(survey_id):
    user_id = session.get('user_id', -1)
    form_id = session.get('form_id')  # Obtener el formulario relacionado

    session_db = SessionLocal()
    try:
        # Verificar formulario
        form = session_db.query(EvaluationForm).filter_by(id=form_id).first()
        if not form:
            flash("No se encontraron los datos del formulario.", "error")
            return redirect(url_for('question.surveys'))

        # Obtener resultados
        results = get_results_by_survey(survey_id, user_id)
        processed_results = []
        total_score = 0
        total_max = 0

        for result in results:
            processed_results.append({
                "response_id": result.response_id,
                "section_title": result.item.section.section_title if result.item else "N/A",
                "item_name": result.item.item_name if result.item else "N/A",
                "description": result.item.description if result.item else "N/A",
                "value": result.total_score,
                "max_value": 3,
                "percentage": (result.total_score / 3) * 100 if result.item else 0
            })
            total_score += result.total_score
            total_max += 3 if result.item else 0

        overall_percentage = (total_score / total_max) * 100 if total_max > 0 else 0
        overall_result = calculate_overall_result(overall_percentage)

        return render_template(
            'survey/results.html',
            results=processed_results,
            total_score=total_score,
            total_max=total_max,
            overall_percentage=overall_percentage,
            overall_result=overall_result,
            form=form
        )
    except Exception as e:
        flash("Error al obtener los resultados.", "error")
        print(f"Error al obtener resultados: {e}")
        return redirect(url_for('question.surveys'))
    finally:
        session_db.close()
