from flask import Blueprint, request,render_template, redirect, url_for, session, flash, current_app, send_file
from services.survey_service import (
    get_all_surveys,
    get_survey_by_id,
    save_evaluation_form,
    clone_survey,
    get_results_by_survey,
    calculate_overall_result,
    get_form_data,
    get_sections_by_survey_id,
    get_section_by_id,
    create_section,
    update_section,
    delete_section,
    get_subsections_by_section_id,
    get_subsection_by_id,
    create_subsection,
    update_subsection,
    delete_subsection
)
from database import SessionLocal
from models.survey import SurveyResults, SurveyResponse, Survey, SurveyItem, SurveySection, SurveySubSection, EvaluationForm
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer , Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from io import BytesIO
from uuid import uuid4
from sqlalchemy.sql import func
from sqlalchemy.orm import joinedload
import time  
# Importar el nuevo generador de PDFs mejorado
from utils.pdf_generator import generate_improved_pdf



question_bp = Blueprint('question', __name__)

# Ruta para listar encuestas
@question_bp.route('/surveys', methods=['GET'])
def surveys():
    # Eliminar verificación de autenticación para evitar mensajes no deseados
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
            
            # Si no hay user_id en la sesión, crear uno temporal para el proceso de evaluación
            if 'user_id' not in session:
                # Usar el form_id como user_id temporal para este proceso
                session['user_id'] = form_id
                current_app.logger.debug(f"Creando user_id temporal: {form_id}")
            
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

    # Obtener directamente la encuesta ISO 25000
    surveys = get_all_surveys()
    
    if not surveys:
        flash("No se encontró la encuesta ISO 25000.", "error")
        return redirect(url_for('question.formulario'))
    
    # Seleccionar automáticamente la encuesta ISO 25000
    iso_survey = surveys[0]  # Debería ser la única encuesta disponible
    form_id = session.get('form_id')  # ID del formulario actual
    user_id = session.get('user_id')  # ID del usuario actual

    try:
        current_app.logger.debug(f"Seleccionando automáticamente la encuesta ISO 25000: {iso_survey.id}")
        cloned_survey_id = clone_survey(iso_survey.id, form_id, user_id)
        session['survey_id'] = cloned_survey_id  # Guarda la encuesta en la sesión
        flash("Encuesta ISO 25000 seleccionada automáticamente.")
        return redirect(url_for('question.complete_survey_view', survey_id=cloned_survey_id))
    except Exception as e:
        current_app.logger.error(f"Error al procesar la encuesta ISO 25000: {e}")
        flash(f"Error al procesar la encuesta ISO 25000: {e}", "error")
        return redirect(url_for('question.formulario'))

# Ruta para completar la encuesta
@question_bp.route('/surveys/<int:survey_id>/complete', methods=['GET', 'POST'])
@question_bp.route('/surveys/<int:survey_id>/complete/<int:section_index>', methods=['GET', 'POST'])
def complete_survey_view(survey_id, section_index=0):
    session_db = SessionLocal()
    try:
        if request.method == 'GET':
            survey = get_survey_by_id(survey_id)
            if not survey:
                flash("Encuesta no encontrada.", "error")
                return redirect(url_for('question.select_survey'))
            
            # Verificar que el índice de sección sea válido
            if section_index >= len(survey.sections):
                flash("Sección no encontrada.", "error")
                return redirect(url_for('question.complete_survey_view', survey_id=survey_id, section_index=0))
            
            current_section = survey.sections[section_index]
            total_sections = len(survey.sections)
            
            # Obtener respuestas existentes para esta sección
            existing_responses = {}
            section_items = []
            for subsection in current_section.subsections:
                section_items.extend(subsection.items)
            
            if section_items:
                responses = session_db.query(SurveyResponse).filter(
                    SurveyResponse.survey_id == survey_id,
                    SurveyResponse.user_id == session.get('user_id'),
                    SurveyResponse.item_id.in_([item.id for item in section_items])
                ).all()
                
                for response in responses:
                    existing_responses[response.item_id] = response.value
            
            return render_template('survey/complete_survey_paginated.html', 
                                 survey=survey,
                                 current_section=current_section,
                                 section_index=section_index,
                                 total_sections=total_sections,
                                 existing_responses=existing_responses)

        elif request.method == 'POST':
            user_id = session.get('user_id')
            form_id = session.get('form_id')

            if not user_id or not form_id:
                flash("Faltan datos del usuario o formulario.", "error")
                return redirect(url_for('question.select_survey'))

            # Procesar respuestas de la sección actual
            for key, value in request.form.items():
                if key.startswith('item_'):
                    try:
                        item_id = int(key.split('_')[1])
                        score = int(value)
                        
                        # Verificar si ya existe una respuesta para este item
                        existing_response = session_db.query(SurveyResponse).filter(
                            SurveyResponse.survey_id == survey_id,
                            SurveyResponse.user_id == user_id,
                            SurveyResponse.item_id == item_id
                        ).first()
                        
                        if existing_response:
                            existing_response.value = score
                        else:
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

            # Determinar la siguiente acción basada en el botón presionado
            action = request.form.get('action', 'next')
            
            if action == 'previous':
                # Ir a la sección anterior
                if section_index > 0:
                    return redirect(url_for('question.complete_survey_view', 
                                          survey_id=survey_id, 
                                          section_index=section_index - 1))
                else:
                    return redirect(url_for('question.complete_survey_view', 
                                          survey_id=survey_id, 
                                          section_index=0))
            
            elif action == 'next':
                # Ir a la siguiente sección
                survey = get_survey_by_id(survey_id)
                if section_index < len(survey.sections) - 1:
                    flash("Sección guardada exitosamente.", "success")
                    return redirect(url_for('question.complete_survey_view', 
                                          survey_id=survey_id, 
                                          section_index=section_index + 1))
                else:
                    # Es la última sección, finalizar encuesta
                    return redirect(url_for('question.finalize_survey', survey_id=survey_id))
            
            elif action == 'finish':
                # Finalizar encuesta directamente
                return redirect(url_for('question.finalize_survey', survey_id=survey_id))

    except Exception as e:
        session_db.rollback()
        current_app.logger.error(f"Error al procesar la encuesta con ID {survey_id}: {e}")
        flash("Hubo un error al procesar la encuesta.", "error")
        return redirect(url_for('question.select_survey'))
    finally:
        session_db.close()

# Nueva ruta para finalizar la encuesta
@question_bp.route('/surveys/<int:survey_id>/finalize', methods=['GET'])
def finalize_survey(survey_id):
    session_db = SessionLocal()
    try:
        user_id = session.get('user_id')
        form_id = session.get('form_id')

        if not user_id or not form_id:
            flash("Faltan datos del usuario o formulario.", "error")
            return redirect(url_for('question.select_survey'))

        # Calcular resultados finales
        responses = session_db.query(SurveyResponse).filter(
            SurveyResponse.survey_id == survey_id,
            SurveyResponse.user_id == user_id
        ).all()

        total_score = sum(response.value for response in responses if response.value is not None)
        max_score = len(responses) * 3
        percentage = (total_score / max_score) * 100 if max_score > 0 else 0
        overall_result = calculate_overall_result(percentage)

        # Verificar si ya existe un resultado para esta encuesta
        existing_result = session_db.query(SurveyResults).filter(
            SurveyResults.survey_id == survey_id,
            SurveyResults.user_id == user_id,
            SurveyResults.form_id == form_id
        ).first()

        if existing_result:
            # Actualizar resultado existente
            existing_result.total_score = total_score
            existing_result.percentage = percentage
            existing_result.overall_result = overall_result
        else:
            # Crear nuevo resultado
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

        # Obtener datos del formulario para mostrar en la página de resultados
        form_data = get_form_data(form_id)
        
        # Redirigir a página de resultados en lugar de descargar PDF directamente
        return render_template('survey/survey_completed.html', 
                             survey_id=survey_id,
                             total_score=total_score,
                             max_score=max_score,
                             percentage=round(percentage, 2),
                             overall_result=overall_result,
                             form_data=form_data,
                             total_responses=len(responses))

    except Exception as e:
        session_db.rollback()
        current_app.logger.error(f"Error al finalizar la encuesta con ID {survey_id}: {e}")
        flash("Hubo un error al finalizar la encuesta.", "error")
        return redirect(url_for('question.select_survey'))
    finally:
        session_db.close()

@question_bp.route('/surveys/<int:survey_id>/results/pdf', methods=['GET'])
def download_survey_results_pdf(survey_id):
    """
    Genera un PDF mejorado con los resultados de la encuesta, con mejor organización,
    sin superposición de textos y con sugerencias basadas en los resultados.
    """
    session_db = SessionLocal()
    try:
        user_id = session.get('user_id')  # Obtener el usuario desde la sesión de Flask
        if not user_id:
            flash("No se pudo identificar al usuario.", "error")
            return redirect(url_for('question.formulario'))

        current_app.logger.info(f"Generando PDF mejorado para survey_id={survey_id}, user_id={user_id}")

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

        current_app.logger.info(f"Respuestas encontradas: {len(responses)}")

        # Si no hay respuestas, crear un PDF con mensaje informativo
        if not responses:
            current_app.logger.warning("No se encontraron respuestas, creando PDF informativo")
            
            # Obtener datos del formulario
            form_data = get_form_data(session.get('form_id'))
            survey = session_db.query(Survey).filter(Survey.id == survey_id).one_or_none()
            
            # Crear PDF informativo usando el nuevo generador
            buffer = generate_improved_pdf(
                survey_id=survey_id,
                responses=[],  # Lista vacía para indicar que no hay respuestas
                survey=survey,
                form_data=form_data,
                total_score=0,
                max_score=0,
                overall_percentage=0,
                overall_result="Incompleto"
            )
            
            return send_file(buffer, as_attachment=True, download_name=f"evaluacion_iso25000_{survey_id}_incompleta.pdf", mimetype='application/pdf')

        # Obtener datos adicionales de la encuesta y formulario
        survey = session_db.query(Survey).filter(Survey.id == survey_id).one_or_none()
        form_data = get_form_data(session.get('form_id'))

        # Calcular puntajes totales y porcentaje general
        total_score = sum(response.value for response in responses if response.value is not None)
        max_score = len(responses) * 3  # Suponiendo que el valor máximo por pregunta es 3
        overall_percentage = (total_score / max_score) * 100 if max_score > 0 else 0.0
        overall_result = calculate_overall_result(overall_percentage)

        current_app.logger.info(f"Calculando PDF: total_score={total_score}, max_score={max_score}, percentage={overall_percentage}")

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

        # Crear respuesta para el cliente
        current_app.logger.info("PDF mejorado generado exitosamente")
        return send_file(buffer, as_attachment=True, download_name=f"evaluacion_iso25000_{survey_id}.pdf", mimetype='application/pdf')

    except Exception as e:
        current_app.logger.error(f"Error al generar el PDF de resultados: {e}")
        import traceback
        traceback.print_exc()
        flash("Hubo un error al generar el archivo PDF.", "error")
        return redirect(url_for('question.formulario'))
    finally:
        session_db.close()

@question_bp.route('/surveys/<int:survey_id>/administer', methods=['GET'])
def administer_survey(survey_id):
    """
    Vista para administrar una encuesta (listar preguntas, crear, actualizar, eliminar).
    Actualizada para trabajar con la nueva estructura jerárquica: División > Subsección > Preguntas.
    """
    session_db = SessionLocal()
    try:
        current_app.logger.info(f"Iniciando administración de la encuesta con ID: {survey_id}")
        
        # Obtener la encuesta con sus secciones y subsecciones
        survey = session_db.query(Survey).filter(Survey.id == survey_id).one_or_none()
        if not survey:
            flash("Encuesta no encontrada.", "error")
            current_app.logger.error(f"Encuesta con ID {survey_id} no encontrada.")
            return redirect(url_for('question.surveys'))
        
        # Obtener todas las preguntas con su jerarquía completa: División > Subsección > Pregunta
        questions = (
            session_db.query(SurveyItem, SurveySubSection, SurveySection)
            .join(SurveySubSection, SurveyItem.subsection_id == SurveySubSection.id)
            .join(SurveySection, SurveySubSection.section_id == SurveySection.id)
            .filter(SurveySection.survey_id == survey_id)
            .order_by(SurveySection.id, SurveySubSection.id, SurveyItem.id)
            .all()
        )

        current_app.logger.info(f"Encuesta encontrada: {survey.name}")
        current_app.logger.debug(f"Preguntas encontradas: {len(questions)} preguntas para la encuesta {survey_id}")

        # Estructurar los datos para la plantilla
        structured_questions = []
        for question, subsection, section in questions:
            structured_questions.append({
                'id': question.id,
                'item_name': question.item_name,
                'description': question.description,
                'code': question.code,
                'value': question.value,
                'subsection_title': subsection.subsection_title,
                'subsection_iso_code': subsection.iso_code,
                'section_title': section.section_title,
                'subsection_id': subsection.id,
                'section_id': section.id
            })

        return render_template(
            'survey/administer_survey.html',
            survey=survey,
            questions=structured_questions
        )
    except Exception as e:
        current_app.logger.error(f"Error al administrar la encuesta con ID {survey_id}: {e}")
        flash("Hubo un error al cargar la encuesta.", "error")
        return redirect(url_for('question.surveys'))
    finally:
        session_db.close()



@question_bp.route('/surveys/<int:survey_id>/questions/new', methods=['GET', 'POST'])
def create_question(survey_id):
    """
    Crear una nueva pregunta para una encuesta con un código generado automáticamente.
    Ahora las preguntas se asocian a subsecciones, no a secciones.
    """
    session_db = SessionLocal()
    try:
        current_app.logger.info(f"Iniciando creación de una nueva pregunta para la encuesta con ID: {survey_id}")
        
        if request.method == 'POST':
            item_name = request.form['item_name']
            description = request.form['description']
            subsection_id = request.form['subsection_id']

            current_app.logger.debug(f"Datos recibidos del formulario: item_name={item_name}, description={description}, subsection_id={subsection_id}")
            
            # Generar automáticamente un código único para la pregunta
            timestamp = int(time.time())
            code = f"Q{survey_id}_{timestamp}"  # Ejemplo: Q4_1690672953
            current_app.logger.info(f"Código generado automáticamente para la pregunta: {code}")

            # Crear y guardar la pregunta
            question = SurveyItem(
                item_name=item_name,
                description=description,
                subsection_id=subsection_id,
                code=code,
                value=0  # Valor inicial por defecto
            )
            session_db.add(question)
            session_db.commit()

            current_app.logger.info(f"Pregunta creada exitosamente con ID: {question.id} y código: {code}")
            flash("Pregunta creada exitosamente.", "success")
            
            # Si la pregunta fue creada desde una subsección específica, redirigir allí
            subsection_id_param = request.args.get('subsection_id')
            if subsection_id_param:
                # Obtener la subsección para conocer la sección padre
                subsection = session_db.query(SurveySubSection).filter(
                    SurveySubSection.id == subsection_id_param
                ).one_or_none()
                
                if subsection:
                    return redirect(url_for('question.view_subsection_questions', 
                                          survey_id=survey_id, 
                                          section_id=subsection.section_id, 
                                          subsection_id=subsection_id_param))
            
            # Si no hay subsección específica, redirigir a administrar encuesta
            return redirect(url_for('question.administer_survey', survey_id=survey_id))

        # Obtener todas las subsecciones de la encuesta para el formulario
        subsections = (
            session_db.query(SurveySubSection)
            .join(SurveySection)
            .filter(SurveySection.survey_id == survey_id)
            .all()
        )
        
        current_app.logger.debug(f"Subsecciones obtenidas para la encuesta con ID {survey_id}: {len(subsections)} subsecciones")
        
        # Verificar si se debe pre-seleccionar una subsección
        preselected_subsection_id = request.args.get('subsection_id')
        
        return render_template(
            'survey/new_question.html', 
            subsections=subsections, 
            survey_id=survey_id,
            preselected_subsection_id=preselected_subsection_id
        )
    except Exception as e:
        current_app.logger.error(f"Error al crear una pregunta para la encuesta con ID {survey_id}: {e}")
        flash("Hubo un error al crear la pregunta.", "error")
        return redirect(url_for('question.administer_survey', survey_id=survey_id))
    finally:
        current_app.logger.debug("Cerrando la sesión de la base de datos.")
        session_db.close()




@question_bp.route('/surveys/<int:survey_id>/questions/<int:question_id>/edit', methods=['GET', 'POST'])
def edit_question(survey_id, question_id):
    """
    Editar una pregunta existente de una encuesta.
    """
    session_db = SessionLocal()
    try:
        # Obtener la pregunta con su subsección cargada
        question = session_db.query(SurveyItem).options(
            joinedload(SurveyItem.subsection)
        ).filter(SurveyItem.id == question_id).one_or_none()
        
        if not question:
            flash("Pregunta no encontrada.", "error")
            current_app.logger.warning(f"Pregunta con ID {question_id} no encontrada en la encuesta {survey_id}")
            return redirect(url_for('question.administer_survey', survey_id=survey_id))

        if request.method == 'POST':
            question.item_name = request.form['item_name']
            question.description = request.form['description']
            session_db.commit()

            flash("Pregunta actualizada exitosamente.", "success")
            current_app.logger.info(f"Pregunta actualizada exitosamente: {question.item_name}")
            return redirect(url_for('question.administer_survey', survey_id=survey_id))

        return render_template('survey/edit_question.html', question=question, survey_id=survey_id)
    except Exception as e:
        current_app.logger.error(f"Error al editar la pregunta con ID {question_id} en la encuesta {survey_id}: {e}")
        flash("Hubo un error al actualizar la pregunta.", "error")
        return redirect(url_for('question.administer_survey', survey_id=survey_id))
    finally:
        session_db.close()


@question_bp.route('/surveys/<int:survey_id>/questions/<int:question_id>/delete', methods=['POST'])
def delete_question(survey_id, question_id):
    """
    Eliminar una pregunta específica.
    """
    session_db = SessionLocal()
    try:
        current_app.logger.info(f"Eliminando pregunta con ID: {question_id} de la encuesta {survey_id}")
        question = session_db.query(SurveyItem).filter(SurveyItem.id == question_id).one_or_none()
        if not question:
            flash("Pregunta no encontrada.", "error")
            current_app.logger.error(f"Pregunta con ID {question_id} no encontrada.")
            return redirect(url_for('question.administer_survey', survey_id=survey_id))

        session_db.delete(question)
        session_db.commit()

        current_app.logger.info(f"Pregunta con ID {question_id} eliminada exitosamente.")
        flash("Pregunta eliminada exitosamente.", "success")
        return redirect(url_for('question.administer_survey', survey_id=survey_id))
    except Exception as e:
        session_db.rollback()
        current_app.logger.error(f"Error al eliminar la pregunta con ID {question_id}: {e}")
        flash("Hubo un error al eliminar la pregunta.", "error")
        return redirect(url_for('question.administer_survey', survey_id=survey_id))
    finally:
        session_db.close()


# === GESTIÓN DE SECCIONES ===

@question_bp.route('/surveys/<int:survey_id>/sections', methods=['GET'])
def manage_sections(survey_id):
    """
    Vista para administrar las secciones de una encuesta (listar, crear, editar, eliminar).
    """
    if 'role' not in session or session['role'] != 'admin':
        flash("No tienes permiso para acceder a esta página.")
        return redirect('http://localhost:5001/auth/login')
    
    try:
        current_app.logger.info(f"Iniciando administración de secciones para la encuesta con ID: {survey_id}")
        
        # Obtener la encuesta
        survey = get_survey_by_id(survey_id)
        if not survey:
            flash("Encuesta no encontrada.", "error")
            return redirect(url_for('question.surveys'))
        
        # Obtener secciones de la encuesta
        sections = get_sections_by_survey_id(survey_id)
        
        current_app.logger.info(f"Secciones encontradas: {len(sections)} para la encuesta {survey_id}")
        
        return render_template(
            'survey/manage_sections.html',
            survey=survey,
            sections=sections
        )
    except Exception as e:
        current_app.logger.error(f"Error al administrar secciones de la encuesta {survey_id}: {e}")
        flash("Hubo un error al cargar las secciones.", "error")
        return redirect(url_for('question.surveys'))


@question_bp.route('/surveys/<int:survey_id>/sections/<int:section_id>/questions', methods=['GET'])
def view_section_questions(survey_id, section_id):
    """
    Vista para ver todas las preguntas de una sección específica.
    """
    if 'role' not in session or session['role'] != 'admin':
        flash("No tienes permiso para acceder a esta página.")
        return redirect('http://localhost:5001/auth/login')
    
    session_db = SessionLocal()
    try:
        current_app.logger.info(f"Mostrando preguntas de la sección {section_id}")
        
        # Obtener la sección
        section = session_db.query(SurveySection).filter(
            SurveySection.id == section_id,
            SurveySection.survey_id == survey_id
        ).one_or_none()
        
        if not section:
            flash("Sección no encontrada.", "error")
            return redirect(url_for('question.manage_sections', survey_id=survey_id))
        
        # Obtener preguntas de esta sección específica
        questions = session_db.query(SurveyItem).filter(
            SurveyItem.section_id == section_id
        ).all()
        
        # Obtener la encuesta para contexto
        survey = get_survey_by_id(survey_id)
        
        current_app.logger.info(f"Preguntas encontradas: {len(questions)} para la sección {section_id}")
        
        return render_template(
            'survey/section_questions.html',
            survey=survey,
            section=section,
            questions=questions
        )
    except Exception as e:
        current_app.logger.error(f"Error al obtener preguntas de la sección {section_id}: {e}")
        flash("Hubo un error al cargar las preguntas de la sección.", "error")
        return redirect(url_for('question.manage_sections', survey_id=survey_id))
    finally:
        session_db.close()


@question_bp.route('/surveys/<int:survey_id>/sections/new', methods=['GET', 'POST'])
def create_section_view(survey_id):
    """
    Crear una nueva sección para una encuesta.
    """
    if 'role' not in session or session['role'] != 'admin':
        flash("No tienes permiso para acceder a esta página.")
        return redirect('http://localhost:5001/auth/login')
    
    try:
        if request.method == 'POST':
            section_title = request.form['section_title']
            description = request.form['description']
            
            current_app.logger.debug(f"Creando nueva sección: {section_title}")
            
            section_id = create_section(survey_id, section_title, description)
            flash("Sección creada exitosamente.", "success")
            return redirect(url_for('question.manage_sections', survey_id=survey_id))
        
        # Obtener la encuesta para mostrar información
        survey = get_survey_by_id(survey_id)
        if not survey:
            flash("Encuesta no encontrada.", "error")
            return redirect(url_for('question.surveys'))
        
        return render_template('survey/new_section.html', survey=survey)
    except Exception as e:
        current_app.logger.error(f"Error al crear sección para la encuesta {survey_id}: {e}")
        flash("Hubo un error al crear la sección.", "error")
        return redirect(url_for('question.manage_sections', survey_id=survey_id))


@question_bp.route('/surveys/<int:survey_id>/sections/<int:section_id>/edit', methods=['GET', 'POST'])
def edit_section(survey_id, section_id):
    """
    Editar una sección existente.
    """
    if 'role' not in session or session['role'] != 'admin':
        flash("No tienes permiso para acceder a esta página.")
        return redirect('http://localhost:5001/auth/login')
    
    try:
        if request.method == 'POST':
            section_title = request.form['section_title']
            description = request.form['description']
            
            current_app.logger.debug(f"Actualizando sección {section_id}: {section_title}")
            
            update_section(section_id, section_title, description)
            flash("Sección actualizada exitosamente.", "success")
            return redirect(url_for('question.manage_sections', survey_id=survey_id))
        
        # Obtener la sección para el formulario
        section = get_section_by_id(section_id)
        if not section:
            flash("Sección no encontrada.", "error")
            return redirect(url_for('question.manage_sections', survey_id=survey_id))
        
        # Obtener la encuesta para contexto
        survey = get_survey_by_id(survey_id)
        
        return render_template('survey/edit_section.html', section=section, survey=survey)
    except Exception as e:
        current_app.logger.error(f"Error al editar la sección {section_id}: {e}")
        flash("Hubo un error al editar la sección.", "error")
        return redirect(url_for('question.manage_sections', survey_id=survey_id))


@question_bp.route('/surveys/<int:survey_id>/sections/<int:section_id>/delete', methods=['POST'])
def delete_section_view(survey_id, section_id):
    """
    Eliminar una sección y todas sus preguntas asociadas.
    """
    if 'role' not in session or session['role'] != 'admin':
        flash("No tienes permiso para acceder a esta página.")
        return redirect('http://localhost:5001/auth/login')
    
    try:
        current_app.logger.info(f"Eliminando sección con ID: {section_id}")
        
        delete_section(section_id)
        flash("Sección eliminada exitosamente.", "success")
        return redirect(url_for('question.manage_sections', survey_id=survey_id))
    except Exception as e:
        current_app.logger.error(f"Error al eliminar la sección {section_id}: {e}")
        flash("Hubo un error al eliminar la sección.", "error")
        return redirect(url_for('question.manage_sections', survey_id=survey_id))

# === GESTIÓN DE SUBSECCIONES ===

@question_bp.route('/surveys/<int:survey_id>/sections/<int:section_id>/subsections', methods=['GET'])
def manage_subsections(survey_id, section_id):
    """
    Vista para administrar las subsecciones de una sección (listar, crear, editar, eliminar).
    """
    if 'role' not in session or session['role'] != 'admin':
        flash("No tienes permiso para acceder a esta página.")
        return redirect('http://localhost:5001/auth/login')
    
    try:
        current_app.logger.info(f"Iniciando administración de subsecciones para la sección con ID: {section_id}")
        
        # Obtener la encuesta y sección
        survey = get_survey_by_id(survey_id)
        section = get_section_by_id(section_id)
        
        if not survey or not section:
            flash("Encuesta o sección no encontrada.", "error")
            return redirect(url_for('question.manage_sections', survey_id=survey_id))
        
        # Obtener subsecciones de la sección
        subsections = get_subsections_by_section_id(section_id)
        
        current_app.logger.info(f"Subsecciones encontradas: {len(subsections)} para la sección {section_id}")
        
        return render_template(
            'survey/manage_subsections.html',
            survey=survey,
            section=section,
            subsections=subsections
        )
    except Exception as e:
        current_app.logger.error(f"Error al administrar subsecciones de la sección {section_id}: {e}")
        flash("Hubo un error al cargar las subsecciones.", "error")
        return redirect(url_for('question.manage_sections', survey_id=survey_id))


@question_bp.route('/surveys/<int:survey_id>/sections/<int:section_id>/subsections/<int:subsection_id>/questions', methods=['GET'])
def view_subsection_questions(survey_id, section_id, subsection_id):
    """
    Vista para ver todas las preguntas de una subsección específica.
    """
    if 'role' not in session or session['role'] != 'admin':
        flash("No tienes permiso para acceder a esta página.")
        return redirect('http://localhost:5001/auth/login')
    
    try:
        current_app.logger.info(f"Mostrando preguntas de la subsección {subsection_id}")
        
        # Obtener la subsección con sus preguntas
        subsection = get_subsection_by_id(subsection_id)
        
        if not subsection:
            flash("Subsección no encontrada.", "error")
            return redirect(url_for('question.manage_subsections', survey_id=survey_id, section_id=section_id))
        
        # Obtener contexto adicional
        survey = get_survey_by_id(survey_id)
        section = get_section_by_id(section_id)
        
        current_app.logger.info(f"Preguntas encontradas: {len(subsection.items) if subsection.items else 0} para la subsección {subsection_id}")
        
        return render_template(
            'survey/subsection_questions.html',
            survey=survey,
            section=section,
            subsection=subsection,
            questions=subsection.items or []
        )
    except Exception as e:
        current_app.logger.error(f"Error al obtener preguntas de la subsección {subsection_id}: {e}")
        flash("Hubo un error al cargar las preguntas de la subsección.", "error")
        return redirect(url_for('question.manage_subsections', survey_id=survey_id, section_id=section_id))


@question_bp.route('/surveys/<int:survey_id>/sections/<int:section_id>/subsections/new', methods=['GET', 'POST'])
def create_subsection_view(survey_id, section_id):
    """
    Crear una nueva subsección para una sección.
    """
    if 'role' not in session or session['role'] != 'admin':
        flash("No tienes permiso para acceder a esta página.")
        return redirect('http://localhost:5001/auth/login')
    
    try:
        if request.method == 'POST':
            subsection_title = request.form['subsection_title']
            description = request.form['description']
            iso_code = request.form.get('iso_code', '')
            
            current_app.logger.debug(f"Creando nueva subsección: {subsection_title}")
            
            subsection_id = create_subsection(section_id, subsection_title, description, iso_code)
            flash("Subsección creada exitosamente.", "success")
            return redirect(url_for('question.manage_subsections', survey_id=survey_id, section_id=section_id))
        
        # Obtener contexto para mostrar información
        survey = get_survey_by_id(survey_id)
        section = get_section_by_id(section_id)
        
        if not survey or not section:
            flash("Encuesta o sección no encontrada.", "error")
            return redirect(url_for('question.manage_sections', survey_id=survey_id))
        
        return render_template('survey/new_subsection.html', survey=survey, section=section)
    except Exception as e:
        current_app.logger.error(f"Error al crear subsección para la sección {section_id}: {e}")
        flash("Hubo un error al crear la subsección.", "error")
        return redirect(url_for('question.manage_subsections', survey_id=survey_id, section_id=section_id))


@question_bp.route('/surveys/<int:survey_id>/sections/<int:section_id>/subsections/<int:subsection_id>/edit', methods=['GET', 'POST'])
def edit_subsection(survey_id, section_id, subsection_id):
    """
    Editar una subsección existente.
    """
    if 'role' not in session or session['role'] != 'admin':
        flash("No tienes permiso para acceder a esta página.")
        return redirect('http://localhost:5001/auth/login')
    
    try:
        if request.method == 'POST':
            subsection_title = request.form['subsection_title']
            description = request.form['description']
            iso_code = request.form.get('iso_code', '')
            
            current_app.logger.debug(f"Actualizando subsección {subsection_id}: {subsection_title}")
            
            update_subsection(subsection_id, subsection_title, description, iso_code)
            flash("Subsección actualizada exitosamente.", "success")
            return redirect(url_for('question.manage_subsections', survey_id=survey_id, section_id=section_id))
        
        # Obtener la subsección para el formulario
        subsection = get_subsection_by_id(subsection_id)
        if not subsection:
            flash("Subsección no encontrada.", "error")
            return redirect(url_for('question.manage_subsections', survey_id=survey_id, section_id=section_id))
        
        # Obtener contexto
        survey = get_survey_by_id(survey_id)
        section = get_section_by_id(section_id)
        
        return render_template('survey/edit_subsection.html', subsection=subsection, survey=survey, section=section)
    except Exception as e:
        current_app.logger.error(f"Error al editar la subsección {subsection_id}: {e}")
        flash("Hubo un error al editar la subsección.", "error")
        return redirect(url_for('question.manage_subsections', survey_id=survey_id, section_id=section_id))


@question_bp.route('/surveys/<int:survey_id>/sections/<int:section_id>/subsections/<int:subsection_id>/delete', methods=['POST'])
def delete_subsection_view(survey_id, section_id, subsection_id):
    """
    Eliminar una subsección y todas sus preguntas asociadas.
    """
    if 'role' not in session or session['role'] != 'admin':
        flash("No tienes permiso para acceder a esta página.")
        return redirect('http://localhost:5001/auth/login')
    
    try:
        current_app.logger.info(f"Eliminando subsección con ID: {subsection_id}")
        
        delete_subsection(subsection_id)
        flash("Subsección eliminada exitosamente.", "success")
        return redirect(url_for('question.manage_subsections', survey_id=survey_id, section_id=section_id))
    except Exception as e:
        current_app.logger.error(f"Error al eliminar la subsección {subsection_id}: {e}")
        flash("Hubo un error al eliminar la subsección.", "error")
        return redirect(url_for('question.manage_subsections', survey_id=survey_id, section_id=section_id))
