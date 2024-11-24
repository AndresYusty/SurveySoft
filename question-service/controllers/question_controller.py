from flask import Blueprint, request, render_template, redirect, url_for, session, flash, current_app

from services.survey_service import (
    get_all_surveys,
    get_survey_by_id,
    save_evaluation_form,
    clone_survey,
    save_survey_results,
    get_results_by_survey,
    calculate_overall_result,
)
from database import SessionLocal
from models.survey import Survey, SurveyResults, EvaluationForm, SurveyResponse, SurveyItem
from sqlalchemy.orm import joinedload
from uuid import uuid4


question_bp = Blueprint('question', __name__)

# Ruta para listar encuestas
@question_bp.route('/surveys', methods=['GET'])
def surveys():
    if 'role' not in session or session['role'] != 'admin':
        flash("No tienes permiso para acceder a esta página.")
        return redirect('http://localhost:5001/auth/login')

    surveys = get_all_surveys()
    return render_template('survey/home.html', surveys=surveys)

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
            current_app.logger.debug(f"Datos del formulario recibidos: {data}")
            form_id = save_evaluation_form(data)  # Guarda solo el formulario
            session['form_id'] = form_id  # Guarda el ID del formulario en la sesión
            flash("Formulario guardado exitosamente.")
            return redirect(url_for('question.select_survey'))  # Redirige a seleccionar encuesta
        except Exception as e:
            current_app.logger.error(f"Error al guardar el formulario: {e}")
            flash(f"Error al guardar el formulario: {e}", "error")

    return render_template('question/formulario.html')




@question_bp.route('/surveys/select', methods=['GET', 'POST'])
def select_survey():
    current_app.logger.debug("Accediendo a la ruta para seleccionar encuesta.")
    if 'user_id' not in session:
        flash("Debes iniciar sesión para seleccionar una encuesta.")
        return redirect('http://localhost:5001/auth/login')

    surveys = get_all_surveys()  # Obtén las encuestas disponibles

    if request.method == 'POST':
        selected_survey_id = request.form.get('survey_id')  # Obtén el ID de la encuesta seleccionada
        form_id = session.get('form_id')  # ID del formulario actual
        user_id = session.get('user_id')  # ID del usuario actual

        if selected_survey_id:
            try:
                current_app.logger.debug(f"Encuesta seleccionada: {selected_survey_id}")
                # Clonar la encuesta seleccionada
                cloned_survey_id = clone_survey(selected_survey_id, form_id, user_id)
                session['survey_id'] = cloned_survey_id  # Guarda la encuesta en la sesión
                flash("Encuesta seleccionada exitosamente.")
                return redirect(url_for('question.complete_survey_view', survey_id=cloned_survey_id))
            except Exception as e:
                current_app.logger.error(f"Error al procesar la encuesta seleccionada: {e}")
                flash(f"Error al procesar la encuesta seleccionada: {e}", "error")
        else:
            flash("Por favor selecciona una encuesta.", "error")

    return render_template('survey/select_survey.html', surveys=surveys)


@question_bp.route('/surveys/<int:survey_id>/complete', methods=['GET', 'POST'])
def complete_survey_view(survey_id):
    session_db = SessionLocal()
    try:
        if request.method == 'GET':
            current_app.logger.debug(f"Accediendo a la ruta para completar la encuesta con ID: {survey_id}")
            survey = get_survey_by_id(survey_id)
            if not survey:
                flash("Encuesta no encontrada.", "error")
                return redirect(url_for('question.select_survey'))
            current_app.logger.debug(f"Encuesta obtenida: {survey}")
            return render_template('survey/complete_survey.html', survey=survey)

        elif request.method == 'POST':
            current_app.logger.debug(f"Procesando respuestas para la encuesta con ID: {survey_id}")
            user_id = session.get('user_id')
            form_id = session.get('form_id')

            if not user_id or not form_id:
                flash("Faltan datos del usuario o formulario.", "error")
                return redirect(url_for('question.select_survey'))

            total_score = 0
            max_score = 0

            # Procesar respuestas específicas de las preguntas
            for key, value in request.form.items():
                if key.startswith('item_'):
                    try:
                        item_id = int(key.split('_')[1])
                        score = int(value)
                        total_score += score
                        max_score += 3  # Supongamos que el puntaje máximo de cada pregunta es 3

                        # Guardar respuestas individuales
                        response = SurveyResponse(
                            survey_id=survey_id,
                            user_id=user_id,
                            item_id=item_id,
                            value=score
                        )
                        session_db.add(response)
                    except Exception as e:
                        current_app.logger.error(f"Error procesando respuesta para {key}: {e}")

            session_db.commit()

            # Calcular resultados generales
            percentage = (total_score / max_score) * 100 if max_score > 0 else 0
            overall_result = calculate_overall_result(percentage)

            # Guardar el resultado general (sin asignar `item_id`)
            survey_result = SurveyResults(
                user_id=user_id,
                survey_id=survey_id,
                total_score=total_score,
                percentage=percentage,
                overall_result=overall_result,
                form_id=form_id,
                response_id=str(uuid4())
            )
            session_db.add(survey_result)
            session_db.commit()

            current_app.logger.debug(f"Encuesta completada con éxito. Resultado general: {overall_result}, Puntaje: {total_score}/{max_score}")
            flash("Encuesta completada exitosamente.", "success")
            return redirect(url_for('question.survey_results_view', survey_id=survey_id))

    except Exception as e:
        session_db.rollback()
        current_app.logger.error(f"Error al procesar la encuesta con ID {survey_id}: {e}")
        flash("Hubo un error al procesar la encuesta.", "error")
        return redirect(url_for('question.select_survey'))

    finally:
        session_db.close()



@question_bp.route('/surveys/<int:survey_id>/results', methods=['GET'])
def survey_results_view(survey_id):
    user_id = session.get('user_id', -1)
    form_id = session.get('form_id')

    session_db = SessionLocal()
    try:
        # Verificar que el formulario exista
        form = session_db.query(EvaluationForm).filter_by(id=form_id).first()
        if not form:
            flash("No se encontraron datos del formulario.", "error")
            return redirect(url_for('question.surveys'))

        # Obtener resultados
        results = get_results_by_survey(survey_id, user_id)
        processed_results = []
        total_score = 0
        total_max = 0

        for result in results:
            processed_results.append({
                "section_title": result.item.section.section_title if result.item else "N/A",
                "item_name": result.item.item_name if result.item else "N/A",
                "description": result.item.description if result.item else "N/A",
                "value": result.value or 0,
                "max_value": 3,  # Suponiendo que el valor máximo es 3
                "percentage": (result.value / 3) * 100 if result.value else 0,
            })
            total_score += result.value or 0
            total_max += 3  # Suponiendo que el valor máximo es 3

        overall_percentage = (total_score / total_max) * 100 if total_max > 0 else 0
        overall_result = calculate_overall_result(overall_percentage)

        return render_template(
            'survey/results.html',
            form=form,
            results=processed_results,
            total_score=total_score,
            total_max=total_max,
            overall_percentage=round(overall_percentage, 2),
            overall_result=overall_result
        )
    except Exception as e:
        current_app.logger.error(f"Error al obtener resultados: {e}")
        flash("Hubo un error al obtener los resultados.", "error")
        return redirect(url_for('question.surveys'))
    finally:
        session_db.close()

