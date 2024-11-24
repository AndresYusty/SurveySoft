import uuid
from models.survey import Survey, SurveyItem, SurveySection, SurveyResults, SurveyResponse, EvaluationForm
from database import SessionLocal
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from flask import current_app




def get_all_surveys():
    """
    Obtiene solo las encuestas predefinidas (ISO, IEEE, etc.).
    """
    session = SessionLocal()
    try:
        predefined_surveys = session.query(Survey).filter(
            Survey.name.in_(['ISO 25000 Evaluation', 'IEEE 730 Evaluation', 'FURPS Evaluation', 'Boehm Model Evaluation'])
        ).all()
        return predefined_surveys
    finally:
        session.close()


def get_survey_by_id(survey_id):
    """
    Obtiene una encuesta específica por su ID, incluyendo secciones y preguntas.
    """
    session = SessionLocal()
    try:
        return session.query(Survey).options(
            joinedload(Survey.sections).joinedload(SurveySection.items)
        ).filter(Survey.id == survey_id).one_or_none()
    finally:
        session.close()


def create_survey(name, description):
    """
    Crea una nueva encuesta.
    """
    session = SessionLocal()
    try:
        survey = Survey(name=name, description=description)
        session.add(survey)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error al crear encuesta: {e}")
        raise e
    finally:
        session.close()


def clone_survey(original_survey_id, form_id, user_id):
    session = SessionLocal()
    try:
        original_survey = session.query(Survey).filter(Survey.id == original_survey_id).one_or_none()
        if not original_survey:
            raise ValueError("Encuesta original no encontrada.")

        cloned_survey = Survey(
            name=f"{original_survey.name} - {uuid.uuid4()}",
            description=original_survey.description,
        )
        session.add(cloned_survey)
        session.commit()

        for section in original_survey.sections:
            cloned_section = SurveySection(
                survey_id=cloned_survey.id,
                section_title=section.section_title,
                description=section.description,
            )
            session.add(cloned_section)
            session.commit()

            for item in section.items:
                cloned_item = SurveyItem(
                    section_id=cloned_section.id,
                    code=f"ITEM-{uuid.uuid4()}",
                    item_name=item.item_name,
                    description=item.description,
                    value=0,
                )
                session.add(cloned_item)

        session.commit()

        questions = session.query(SurveyItem).filter(SurveyItem.section_id.in_(
            [section.id for section in cloned_survey.sections]
        )).all()

        for question in questions:
            response = SurveyResponse(
                survey_id=cloned_survey.id,
                user_id=user_id,
                item_id=question.id,
                value=0
            )
            session.add(response)

        session.commit()
        return cloned_survey.id
    except Exception as e:
        session.rollback()
        current_app.logger.error(f"Error al clonar encuesta: {e}")
        raise e
    finally:
        session.close()

def save_evaluation_form(data):
    session = SessionLocal()
    try:
        form = EvaluationForm(
            date=data['date'],
            city=data['city'],
            company=data['company'],
            phone=data['phone'],
            software_name=data['software_name'],
            general_objectives=data['general_objectives'],
            specific_objectives=data['specific_objectives']
        )
        session.add(form)
        session.commit()
        return form.id
    except Exception as e:
        session.rollback()
        current_app.logger.error(f"Error al guardar el formulario: {e}")
        raise e
    finally:
        session.close()

def save_survey_results(user_id, survey_id, item_id, total_score, percentage, overall_result, form_id, response_id):
    session = SessionLocal()
    try:
        survey_result = SurveyResults(
            user_id=user_id,
            survey_id=survey_id,
            item_id=item_id,
            total_score=total_score,
            percentage=percentage,
            overall_result=overall_result,
            form_id=form_id,
            response_id=response_id
        )
        session.add(survey_result)
        session.commit()
    except IntegrityError as e:
        session.rollback()
        current_app.logger.error(f"Error al guardar resultados: {e}")
        raise e
    finally:
        session.close()



def calculate_results(survey_id, user_id, form_id):
    """
    Calcula los resultados de la encuesta y guarda el resultado global.
    """
    session = SessionLocal()
    try:
        responses = session.query(SurveyResponse).filter_by(survey_id=survey_id, user_id=user_id).all()
        if not responses:
            raise ValueError("No se encontraron respuestas para este usuario y encuesta.")

        total_score = sum(response.value for response in responses if response.value is not None)
        max_score = len(responses) * 3  # Suponiendo que el máximo valor para cada respuesta es 3
        percentage = (total_score / max_score) * 100 if max_score > 0 else 0
        result = calculate_overall_result(percentage)

        response_id = str(uuid.uuid4())
        save_survey_results(user_id, survey_id, None, total_score, percentage, result, form_id, response_id)

        return {'total_score': total_score, 'percentage': percentage, 'overall_result': result, 'response_id': response_id}
    except Exception as e:
        print(f"Error al calcular resultados: {e}")
        raise e
    finally:
        session.close()


def get_user_survey_history(user_id):
    """
    Obtiene el historial de encuestas realizadas por un usuario.
    """
    session = SessionLocal()
    try:
        results = (
            session.query(SurveyResults)
            .filter(SurveyResults.user_id == user_id)
            .options(joinedload(SurveyResults.survey))
            .all()
        )
        history = [
            {
                "survey_id": result.survey_id,
                "name": result.survey.name,
                "total_score": result.total_score,
                "percentage": result.percentage,
                "overall_result": result.overall_result,
                "date": result.survey.created_at,
            }
            for result in results
        ]
        return history
    finally:
        session.close()


def save_evaluation_form(data):
    """
    Guarda un formulario de evaluación y retorna su ID.
    """
    session = SessionLocal()
    try:
        form = EvaluationForm(
            date=data['date'],
            city=data['city'],
            company=data['company'],
            phone=data['phone'],
            software_name=data['software_name'],
            general_objectives=data['general_objectives'],
            specific_objectives=data['specific_objectives']
        )
        session.add(form)
        session.commit()
        return form.id
    except Exception as e:
        session.rollback()
        print(f"Error al guardar el formulario: {e}")
        raise e
    finally:
        session.close()


def calculate_overall_result(percentage):
    """
    Calcula el resultado general basado en el porcentaje.
    """
    if percentage > 90:
        return "Excelente"
    elif percentage > 70:
        return "Sobresaliente"
    elif percentage > 50:
        return "Aceptable"
    elif percentage > 30:
        return "Insuficiente"
    else:
        return "Deficiente"

def get_survey_details(survey_id):
    """
    Obtiene los detalles de una encuesta completa (preguntas y respuestas) basada en survey_id.
    """
    session = SessionLocal()
    try:
        survey = session.query(Survey).filter(Survey.id == survey_id).first()
        if not survey:
            raise ValueError("La encuesta solicitada no existe.")

        # Cargar las secciones y preguntas asociadas
        sections = session.query(SurveySection).filter(SurveySection.survey_id == survey_id).all()
        questions = session.query(SurveyItem).join(SurveySection).filter(SurveySection.survey_id == survey_id).all()

        return {
            "survey_name": survey.name,
            "survey_description": survey.description,
            "sections": [
                {
                    "section_title": section.section_title,
                    "description": section.description,
                    "questions": [
                        {
                            "item_name": question.item_name,
                            "description": question.description,
                            "code": question.code
                        }
                        for question in questions if question.section_id == section.id
                    ]
                }
                for section in sections
            ]
        }
    except Exception as e:
        print(f"Error al obtener los detalles de la encuesta: {e}")
        raise e
    finally:
        session.close()


def clone_survey(original_survey_id, form_id, user_id):
    """
    Clona una encuesta predefinida y la asocia al formulario llenado.
    """
    session = SessionLocal()
    try:
        # Obtener la encuesta original
        original_survey = session.query(Survey).filter(Survey.id == original_survey_id).one_or_none()
        if not original_survey:
            raise ValueError("Encuesta original no encontrada.")

        # Crear una nueva encuesta
        cloned_survey = Survey(
            name=f"{original_survey.name} - {uuid.uuid4()}",
            description=original_survey.description,
        )
        session.add(cloned_survey)
        session.commit()

        # Clonar las secciones y preguntas
        for section in original_survey.sections:
            cloned_section = SurveySection(
                survey_id=cloned_survey.id,
                section_title=section.section_title,
                description=section.description,
            )
            session.add(cloned_section)
            session.commit()

            for item in section.items:
                # Generar un código único para cada ítem clonado
                cloned_item = SurveyItem(
                    section_id=cloned_section.id,
                    code=f"ITEM-{uuid.uuid4()}",  # Asigna un código único
                    item_name=item.item_name,
                    description=item.description,
                    value=0,  # Asigna valor inicial
                )
                session.add(cloned_item)

        session.commit()

        # Crear respuestas iniciales para el usuario
        questions = session.query(SurveyItem).filter(SurveyItem.section_id.in_(
            [section.id for section in cloned_survey.sections]
        )).all()

        for question in questions:
            response = SurveyResponse(
                survey_id=cloned_survey.id,
                user_id=user_id,
                item_id=question.id,
                value=0  # Valor inicial
            )
            session.add(response)

        session.commit()
        return cloned_survey.id
    except Exception as e:
        session.rollback()
        print(f"Error al clonar encuesta: {e}")
        raise e
    finally:
        session.close()




def get_results_by_survey(survey_id, user_id):
    session = SessionLocal()
    try:
        # Recuperar resultados generales
        result_summary = (
            session.query(SurveyResults)
            .filter(SurveyResults.survey_id == survey_id, SurveyResults.user_id == user_id)
            .first()
        )
        if not result_summary:
            raise ValueError("No se encontraron resultados para esta encuesta y usuario.")

        # Recuperar respuestas individuales
        responses = (
            session.query(SurveyResponse)
            .join(SurveyItem, SurveyItem.id == SurveyResponse.item_id)
            .join(SurveySection, SurveySection.id == SurveyItem.section_id)
            .filter(SurveyResponse.survey_id == survey_id, SurveyResponse.user_id == user_id)
            .all()
        )

        # Procesar respuestas
        detailed_results = [
            {
                "section_title": response.item.section.section_title,
                "item_name": response.item.item_name,
                "description": response.item.description,
                "value": response.value,
                "max_value": 3,  # Suponiendo que el valor máximo por pregunta es 3
                "percentage": (response.value / 3) * 100 if response.value is not None else 0,
            }
            for response in responses
        ]

        return {
            "results": detailed_results,
            "total_score": result_summary.total_score,
            "total_max": len(responses) * 3,
            "overall_percentage": result_summary.percentage,
            "overall_result": result_summary.overall_result,
        }
    except Exception as e:
        current_app.logger.error(f"Error al obtener resultados: {e}")
        raise e
    finally:
        session.close()
