import uuid
from models.survey import Survey, SurveyItem, SurveySection, SurveyResults, SurveyResponse, EvaluationForm
from database import SessionLocal
from sqlalchemy.orm import joinedload


def get_all_surveys():
    """
    Obtiene todas las encuestas disponibles.
    """
    session = SessionLocal()
    try:
        surveys = session.query(Survey).all()
        return surveys
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


def update_survey(survey_id, name, description):
    """
    Actualiza una encuesta existente.
    """
    session = SessionLocal()
    try:
        survey = session.query(Survey).filter(Survey.id == survey_id).first()
        if survey:
            survey.name = name
            survey.description = description
            session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error al actualizar encuesta: {e}")
        raise e
    finally:
        session.close()


def delete_survey(survey_id):
    """
    Elimina una encuesta por su ID.
    """
    session = SessionLocal()
    try:
        survey = session.query(Survey).filter(Survey.id == survey_id).first()
        if survey:
            session.delete(survey)
            session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error al eliminar encuesta: {e}")
        raise e
    finally:
        session.close()


def update_survey_items(items, new_items, delete_items):
    """
    Actualiza, elimina o crea nuevos ítems de una encuesta.
    """
    session = SessionLocal()
    try:
        # Actualizar ítems existentes
        if items:
            for item_id, data in items.items():
                survey_item = session.query(SurveyItem).filter(SurveyItem.id == int(item_id)).first()
                if survey_item:
                    survey_item.item_name = data.get('item_name', survey_item.item_name)
                    survey_item.description = data.get('description', survey_item.description)

        # Eliminar ítems
        if delete_items:
            for item_id in delete_items:
                if item_id:
                    survey_item = session.query(SurveyItem).filter(SurveyItem.id == int(item_id)).first()
                    if survey_item:
                        session.delete(survey_item)

        # Añadir nuevos ítems
        if new_items:
            for section_id, items_data in new_items.items():
                for data in items_data:
                    if 'item_name' in data and 'description' in data:
                        new_item = SurveyItem(
                            section_id=int(section_id),
                            item_name=data['item_name'],
                            description=data['description']
                        )
                        session.add(new_item)

        # Guardar los cambios
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error al actualizar ítems: {e}")
        raise e
    finally:
        session.close()


def save_survey_results(user_id, survey_id, item_id, total_score, percentage, overall_result, form_id, response_id):
    """
    Guarda los resultados de la encuesta en la base de datos.
    """
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
    except Exception as e:
        session.rollback()
        print(f"Error al guardar resultados: {e}")
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

        sections = {}
        total_score = 0
        max_score = 0

        for response in responses:
            item = session.query(SurveyItem).filter_by(id=response.item_id).first()
            if not item:
                continue
            section_id = item.section_id
            if section_id not in sections:
                sections[section_id] = {'total': 0, 'max': 0}
            sections[section_id]['total'] += response.value
            sections[section_id]['max'] += 3
            total_score += response.value
            max_score += 3

        percentage = (total_score / max_score) * 100 if max_score > 0 else 0
        result = calculate_overall_result(percentage)

        response_id = str(uuid.uuid4())
        save_survey_results(user_id, survey_id, None, total_score, percentage, result, form_id, response_id)

        return {'sections': sections, 'overall_result': result, 'response_id': response_id}
    except Exception as e:
        print(f"Error al calcular resultados: {e}")
        raise e
    finally:
        session.close()


def get_results_by_survey(survey_id, user_id):
    """
    Obtiene los resultados de una encuesta específica para un usuario.
    """
    session = SessionLocal()
    try:
        results = (
            session.query(SurveyResults)
            .filter_by(survey_id=survey_id, user_id=user_id)
            .options(
                joinedload(SurveyResults.item).joinedload(SurveyItem.section)
            )
            .all()
        )
        if not results:
            raise ValueError("No se encontraron resultados para esta encuesta y usuario.")
        return results
    except Exception as e:
        print(f"Error al obtener resultados: {e}")
        raise e
    finally:
        session.close()


def save_evaluation_form(data):
    """
    Guarda un formulario de evaluación y retorna su ID.
    """
    session = SessionLocal()
    try:
        required_fields = ['date', 'city', 'company', 'phone', 'software_name', 'general_objectives', 'specific_objectives']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"El campo {field} es obligatorio.")

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


def get_evaluation_form_by_id(form_id):
    """
    Obtiene un formulario de evaluación por su ID.
    """
    session = SessionLocal()
    try:
        return session.query(EvaluationForm).filter_by(id=form_id).first()
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
