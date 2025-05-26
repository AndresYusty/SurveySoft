from flask import Blueprint, jsonify, render_template, flash, redirect, url_for, send_file, session, current_app
from services.survey_service import get_user_survey_history, get_survey_details, get_user_survey_details
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from utils.pdf_generator import generate_improved_pdf
from database import SessionLocal
from models.survey import SurveyResults, SurveyResponse, Survey, SurveyItem, SurveySection, SurveySubSection, EvaluationForm
from services.survey_service import get_form_data, calculate_overall_result
from sqlalchemy.sql import func
from sqlalchemy.orm import joinedload

history_bp = Blueprint('history', __name__)

@history_bp.route('/users/<int:user_id>/history', methods=['GET'])
def view_history(user_id):
    """
    Muestra el historial de encuestas realizadas por un usuario.
    """
    try:
        # Obtener historial del usuario
        history = get_user_survey_history(user_id)
        username = session.get('username', 'Usuario')  # Usar nombre de usuario si está en la sesión

        if not history:
            flash("No se encontraron encuestas realizadas por el usuario.")
            history = []  # Si no hay historial, devolver lista vacía

        return render_template('survey/history.html', history=history, username=username)
    except Exception as e:
        flash(f"Error al cargar el historial: {e}")
        return render_template('survey/history.html', history=[], username="Usuario", error=str(e))


@history_bp.route('/users/<int:user_id>/history/json', methods=['GET'])
def get_user_survey_history_endpoint(user_id):
    """
    Endpoint JSON para obtener el historial de encuestas de un usuario.
    """
    try:
        history = get_user_survey_history(user_id)
        if not history:
            return jsonify({"error": "No se encontró historial para este usuario."}), 404
        return jsonify({"user_id": user_id, "history": history}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@history_bp.route('/users/<int:user_id>/details/<int:survey_id>', methods=['GET'])
def survey_details(user_id, survey_id):
    """
    Muestra los detalles de una encuesta específica realizada por el usuario.
    """
    try:
        details = get_survey_details(survey_id)
        username = session.get('username', 'Usuario')  # Usar nombre de usuario si está en la sesión

        if not details:
            flash("No se encontraron detalles para esta encuesta.")
            return redirect(url_for('history.view_history', user_id=user_id))

        return render_template('survey/details.html', details=details, username=username)
    except Exception as e:
        flash(f"Error al cargar los detalles: {e}")
        return redirect(url_for('history.view_history', user_id=user_id))


@history_bp.route('/users/<int:user_id>/history/<int:survey_id>/download', methods=['GET'])
def download_survey_results_pdf(user_id, survey_id):
    """
    Genera un archivo PDF mejorado con los resultados de una encuesta y permite descargarlo.
    """
    session_db = SessionLocal()
    try:
        current_app.logger.info(f"Generando PDF desde historial para survey_id={survey_id}, user_id={user_id}")

        # Obtener las respuestas filtradas con la estructura jerárquica correcta
        latest_responses = session_db.query(
            SurveyResponse.item_id,
            func.max(SurveyResponse.id).label("latest_id")
        ).filter(
            SurveyResponse.survey_id == survey_id,
            SurveyResponse.user_id == user_id
        ).group_by(SurveyResponse.item_id).subquery()

        responses = session_db.query(SurveyResponse).join(
            latest_responses, SurveyResponse.id == latest_responses.c.latest_id
        ).options(
            joinedload(SurveyResponse.item)
            .joinedload(SurveyItem.subsection)
            .joinedload(SurveySubSection.section)
        ).all()

        if not responses:
            flash("No se encontraron respuestas para generar el PDF.", "error")
            return redirect(url_for('history.view_history', user_id=user_id))

        # Obtener datos adicionales de la encuesta y formulario
        survey = session_db.query(Survey).filter(Survey.id == survey_id).one_or_none()
        
        # Obtener el form_id desde SurveyResults
        survey_result = session_db.query(SurveyResults).filter(
            SurveyResults.survey_id == survey_id,
            SurveyResults.user_id == user_id
        ).first()
        
        if not survey_result:
            flash("No se encontraron datos del formulario para generar el PDF.", "error")
            return redirect(url_for('history.view_history', user_id=user_id))
            
        form_data = get_form_data(survey_result.form_id)

        # Calcular puntajes totales y porcentaje general
        total_score = sum(response.value for response in responses if response.value is not None)
        max_score = len(responses) * 3  # Suponiendo que el valor máximo por pregunta es 3
        overall_percentage = (total_score / max_score) * 100 if max_score > 0 else 0.0
        overall_result = calculate_overall_result(overall_percentage)

        # Usar el nuevo generador de PDFs mejorado
        buffer = generate_improved_pdf(
            survey_id=survey_id,
            responses=responses,
            survey=survey,
            form_data=form_data,
            total_score=total_score,
            max_score=max_score,
            overall_percentage=overall_percentage,
            overall_result=overall_result
        )

        current_app.logger.info("PDF mejorado generado exitosamente desde historial")
        return send_file(buffer, as_attachment=True, download_name=f"evaluacion_iso25000_{survey_id}.pdf", mimetype='application/pdf')

    except Exception as e:
        current_app.logger.error(f"Error al generar el PDF desde historial: {e}")
        flash(f"Error al generar el PDF: {e}", "error")
        return redirect(url_for('history.view_history', user_id=user_id))
    finally:
        session_db.close()

@history_bp.route('/my-history', methods=['GET'])
def my_history():
    """
    Muestra el historial de encuestas del usuario actual (ruta simplificada).
    """
    user_id = session.get('user_id')
    if not user_id:
        flash("Debe iniciar sesión para ver su historial.", "error")
        return redirect('http://localhost:5001/auth/login')
    
    try:
        # Obtener historial del usuario actual
        history = get_user_survey_history(user_id)
        username = session.get('username', 'Usuario')

        if not history:
            flash("No se encontraron encuestas realizadas.", "info")
            history = []

        return render_template('survey/my_history.html', 
                             history=history, 
                             username=username,
                             user_id=user_id)
    except Exception as e:
        current_app.logger.error(f"Error al cargar historial del usuario {user_id}: {e}")
        flash(f"Error al cargar el historial: {e}", "error")
        return render_template('survey/my_history.html', 
                             history=[], 
                             username="Usuario",
                             user_id=user_id)

@history_bp.route('/my-history/<int:survey_id>', methods=['GET'])
def my_survey_details(survey_id):
    """
    Muestra los detalles de una encuesta específica del usuario actual.
    """
    user_id = session.get('user_id')
    if not user_id:
        flash("Debe iniciar sesión para ver los detalles.", "error")
        return redirect('http://localhost:5001/auth/login')
    
    try:
        details = get_user_survey_details(user_id, survey_id)
        username = session.get('username', 'Usuario')

        return render_template('survey/survey_details.html', 
                             details=details, 
                             username=username,
                             user_id=user_id)
    except Exception as e:
        current_app.logger.error(f"Error al cargar detalles de encuesta {survey_id} para usuario {user_id}: {e}")
        flash(f"Error al cargar los detalles: {e}", "error")
        return redirect(url_for('history.my_history'))

@history_bp.route('/my-history/<int:survey_id>/pdf', methods=['GET'])
def download_my_survey_pdf(survey_id):
    """
    Descarga el PDF de una encuesta específica del usuario actual.
    """
    user_id = session.get('user_id')
    if not user_id:
        flash("Debe iniciar sesión para descargar el PDF.", "error")
        return redirect('http://localhost:5001/auth/login')
    
    try:
        # Redirigir a la función existente de descarga de PDF
        return redirect(url_for('question.download_survey_results_pdf', survey_id=survey_id))
    except Exception as e:
        current_app.logger.error(f"Error al descargar PDF de encuesta {survey_id}: {e}")
        flash(f"Error al generar el PDF: {e}", "error")
        return redirect(url_for('history.my_history'))
