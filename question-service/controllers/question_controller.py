from flask import Blueprint, request,render_template, redirect, url_for, session, flash, current_app, send_file
from services.survey_service import (
    get_all_surveys,
    get_survey_by_id,
    save_evaluation_form,
    clone_survey,
    get_results_by_survey,
    calculate_overall_result,
    get_form_data  
)
from database import SessionLocal
from models.survey import SurveyResults, SurveyResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
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

# Ruta para el formulario inicial
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

# Ruta para seleccionar encuesta
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

# Ruta para completar la encuesta
@question_bp.route('/surveys/<int:survey_id>/complete', methods=['GET', 'POST'])
def complete_survey_view(survey_id):
    session_db = SessionLocal()
    try:
        if request.method == 'GET':
            survey = get_survey_by_id(survey_id)
            if not survey:
                flash("Encuesta no encontrada.", "error")
                return redirect(url_for('question.select_survey'))
            return render_template('survey/complete_survey.html', survey=survey)

        elif request.method == 'POST':
            user_id = session.get('user_id')
            form_id = session.get('form_id')

            if not user_id or not form_id:
                flash("Faltan datos del usuario o formulario.", "error")
                return redirect(url_for('question.select_survey'))

            total_score = 0
            max_score = 0

            for key, value in request.form.items():
                if key.startswith('item_'):
                    try:
                        item_id = int(key.split('_')[1])
                        score = int(value)
                        total_score += score
                        max_score += 3  # Supongamos que el puntaje máximo por ítem es 3
                        response = SurveyResponse(
                            survey_id=survey_id,
                            user_id=user_id,
                            item_id=item_id,
                            value=score
                        )
                        session_db.add(response)
                    except ValueError:
                        current_app.logger.error(f"Valor inválido para el ítem {key}.")
                    except Exception as e:
                        current_app.logger.error(f"Error procesando respuesta para {key}: {e}")

            session_db.commit()

            percentage = (total_score / max_score) * 100 if max_score > 0 else 0
            overall_result = calculate_overall_result(percentage)

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

            flash("Encuesta completada exitosamente.", "success")
            return redirect(url_for('question.download_survey_results_pdf', survey_id=survey_id))

    except Exception as e:
        session_db.rollback()
        current_app.logger.error(f"Error al procesar la encuesta con ID {survey_id}: {e}")
        flash("Hubo un error al procesar la encuesta.", "error")
        return redirect(url_for('question.select_survey'))
    finally:
        session_db.close()

@question_bp.route('/surveys/<int:survey_id>/results/pdf', methods=['GET'])
def download_survey_results_pdf(survey_id):
    try:
        user_id = session.get('user_id')
        if not user_id:
            flash("No se pudo identificar al usuario.", "error")
            return redirect(url_for('question.surveys'))

        # Obtener los resultados
        survey_results = get_results_by_survey(survey_id, user_id)
        form_data = get_form_data(session.get('form_id'))

        # Crear un archivo PDF en memoria
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        c.setFont("Helvetica-Bold", 14)

        # Título y detalles del reporte
        c.drawString(100, 750, f"Resultados de la Encuesta ID: {survey_id}")
        c.drawString(100, 730, f"Software evaluado: {form_data['software_name']}")
        c.drawString(100, 710, f"Empresa: {form_data['company']}")
        c.drawString(100, 690, f"Norma de evaluación: {survey_results['norm']}")  # Norma

        c.setFont("Helvetica", 12)
        c.drawString(100, 670, f"Resultado General: {survey_results['overall_result']}")
        c.drawString(100, 650, f"Porcentaje Total: {survey_results['overall_percentage']}%")
        c.drawString(100, 630, f"Puntaje Total: {survey_results['total_score']}/{survey_results['max_score']}")

        # Detalles por pregunta
        y = 610
        for result in survey_results["results"]:
            if y < 100:
                c.showPage()
                y = 750
            c.drawString(100, y, f"Sección: {result['section_title']}")
            c.drawString(120, y - 20, f"Pregunta: {result['item_name']} - {result['value']}/{result['max_value']} ({result['percentage']:.2f}%)")
            y -= 40

        c.save()

        # Crear respuesta para el cliente
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name=f"survey_{survey_id}_results.pdf", mimetype='application/pdf')

    except Exception as e:
        current_app.logger.error(f"Error al descargar resultados como PDF: {e}")
        flash("No se pudo generar el archivo PDF.", "error")
        return redirect(url_for('question.surveys'))
