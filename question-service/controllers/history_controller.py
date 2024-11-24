from flask import Blueprint, jsonify, request, render_template, flash, redirect, url_for
from services.survey_service import get_user_survey_history, get_survey_details

history_bp = Blueprint('history', __name__)

from flask import Blueprint, render_template



@history_bp.route('/users/<int:user_id>/history', methods=['GET'])
def view_history(user_id):
    """
    Muestra el historial de encuestas realizadas por un usuario.
    """
    try:
        history = get_user_survey_history(user_id)
        if not history:
            history = []  # Si no hay historial, devolver lista vacía
        return render_template('survey/history.html', history=history, username="Usuario")  # Cambia username según el contexto
    except Exception as e:
        return render_template('survey/history.html', history=[], username="Usuario", error=str(e))


@history_bp.route('/users/<int:user_id>/history', methods=['GET'])
def get_user_survey_history_endpoint(user_id):
    """
    Endpoint para obtener el historial de encuestas de un usuario.
    """
    try:
        history = get_user_survey_history(user_id)
        if not history:
            return jsonify({"error": "No survey history found for the user."}), 404
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
        if not details:
            flash("No se encontraron detalles para esta encuesta.")
            return redirect(url_for('history.view_history', user_id=user_id))
        return render_template('survey/details.html', details=details, username="Usuario")
    except Exception as e:
        flash(f"Error al cargar los detalles: {e}")
        return redirect(url_for('history.view_history', user_id=user_id))
