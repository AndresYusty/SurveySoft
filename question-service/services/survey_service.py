import uuid
from models.survey import Survey, SurveyItem, SurveySection, SurveySubSection, SurveyResults, SurveyResponse, EvaluationForm
from database import SessionLocal
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from flask import current_app
from sqlalchemy.sql import func

def get_all_surveys():
    """
    Obtiene únicamente la encuesta de ISO 25000.
    La aplicación está ahora especializada exclusivamente en este estándar.
    """
    session = SessionLocal()
    try:
        predefined_surveys = session.query(Survey).filter(
            Survey.name == 'ISO 25000 Evaluation'
        ).all()
        return predefined_surveys
    finally:
        session.close()


def initialize_iso25000_sections():
    """
    Inicializa las 4 secciones principales de ISO 25000 con sus subsecciones correspondientes:
    - División de Gestión de Calidad (2500n)
    - División de Modelo de Calidad (2501n) 
    - División de Medición de Calidad (2502n)
    - División de Requisitos de Calidad (2503n)
    - División de Evaluación de Calidad (2504n)
    """
    session = SessionLocal()
    try:
        # Buscar o crear la encuesta ISO 25000
        iso_survey = session.query(Survey).filter(Survey.name == 'ISO 25000 Evaluation').first()
        
        if not iso_survey:
            iso_survey = Survey(
                name='ISO 25000 Evaluation',
                description='Evaluación basada en el estándar ISO 25000 para medir la calidad del software'
            )
            session.add(iso_survey)
            session.commit()
        
        # Verificar si ya existen las secciones
        existing_sections = session.query(SurveySection).filter(
            SurveySection.survey_id == iso_survey.id
        ).count()
        
        # Solo crear si no hay secciones
        if existing_sections == 0:
            # Definir las secciones principales y sus subsecciones
            iso25000_structure = [
                {
                    'title': 'ISO/IEC 2500n – División de Gestión de Calidad',
                    'description': 'Las normas que forman este apartado definen todos los modelos, términos y definiciones comunes referenciados por todas las otras normas de la familia 25000.',
                    'subsections': [
                        {
                            'title': 'Guide to SQuaRE',
                            'description': 'Contiene el modelo de la arquitectura de SQuaRE, la terminología de la familia, un resumen de las partes, los usuarios previstos y las partes asociadas, así como los modelos de referencia.',
                            'iso_code': 'ISO/IEC 25000'
                        },
                        {
                            'title': 'Planning and Management',
                            'description': 'Establece los requisitos y orientaciones para gestionar la evaluación y especificación de los requisitos del producto software.',
                            'iso_code': 'ISO/IEC 25001'
                        }
                    ]
                },
                {
                    'title': 'ISO/IEC 2501n – División de Modelo de Calidad',
                    'description': 'Las normas de este apartado presentan modelos de calidad detallados incluyendo características para calidad interna, externa y en uso del producto software.',
                    'subsections': [
                        {
                            'title': 'System and software quality models',
                            'description': 'Describe el modelo de calidad para el producto software y para la calidad en uso. Esta Norma presenta las características y subcaracterísticas de calidad frente a las cuales evaluar el producto software.',
                            'iso_code': 'ISO/IEC 25010'
                        },
                        {
                            'title': 'Data Quality model',
                            'description': 'Define un modelo general para la calidad de los datos, aplicable a aquellos datos que se encuentran almacenados de manera estructurada y forman parte de un Sistema de Información.',
                            'iso_code': 'ISO/IEC 25012'
                        }
                    ]
                },
                {
                    'title': 'ISO/IEC 2502n – División de Medición de Calidad',
                    'description': 'Estas normas incluyen un modelo de referencia de la medición de la calidad del producto, definiciones de medidas de calidad (interna, externa y en uso) y guías prácticas para su aplicación.',
                    'subsections': [
                        {
                            'title': 'Measurement reference model and guide',
                            'description': 'Presenta una explicación introductoria y un modelo de referencia común a los elementos de medición de la calidad. También proporciona una guía para que los usuarios seleccionen o desarrollen y apliquen medidas propuestas por normas ISO.',
                            'iso_code': 'ISO/IEC 25020'
                        },
                        {
                            'title': 'Quality measure elements',
                            'description': 'Define y especifica un conjunto recomendado de métricas base y derivadas que puedan ser usadas a lo largo de todo el ciclo de vida del desarrollo software.',
                            'iso_code': 'ISO/IEC 25021'
                        },
                        {
                            'title': 'Measurement of quality in use',
                            'description': 'Define específicamente las métricas para realizar la medición de la calidad en uso del producto.',
                            'iso_code': 'ISO/IEC 25022'
                        },
                        {
                            'title': 'Measurement of system and software product quality',
                            'description': 'Define específicamente las métricas para realizar la medición de la calidad de productos y sistemas software.',
                            'iso_code': 'ISO/IEC 25023'
                        },
                        {
                            'title': 'Measurement of data quality',
                            'description': 'Define específicamente las métricas para realizar la medición de la calidad de datos.',
                            'iso_code': 'ISO/IEC 25024'
                        }
                    ]
                },
                {
                    'title': 'ISO/IEC 2503n – División de Requisitos de Calidad',
                    'description': 'Las normas que forman este apartado ayudan a especificar requisitos de calidad que pueden ser utilizados en el proceso de elicitación de requisitos de calidad del producto software a desarrollar o como entrada del proceso de evaluación.',
                    'subsections': [
                        {
                            'title': 'Quality requirements',
                            'description': 'Provee de un conjunto de recomendaciones para realizar la especificación de los requisitos de calidad del producto software.',
                            'iso_code': 'ISO/IEC 25030'
                        }
                    ]
                },
                {
                    'title': 'ISO/IEC 2504n – División de Evaluación de Calidad',
                    'description': 'Este apartado incluye normas que proporcionan requisitos, recomendaciones y guías para llevar a cabo el proceso de evaluación del producto software.',
                    'subsections': [
                        {
                            'title': 'Evaluation reference model and guide',
                            'description': 'Propone un modelo de referencia general para la evaluación, que considera las entradas al proceso de evaluación, las restricciones y los recursos necesarios para obtener las correspondientes salidas.',
                            'iso_code': 'ISO/IEC 25040'
                        },
                        {
                            'title': 'Evaluation guide for developers, acquirers and independent evaluators',
                            'description': 'Describe los requisitos y recomendaciones para la implementación práctica de la evaluación del producto software desde el punto de vista de los desarrolladores, de los adquirentes y de los evaluadores independientes.',
                            'iso_code': 'ISO/IEC 25041'
                        },
                        {
                            'title': 'Evaluation modules',
                            'description': 'Define lo que la Norma considera un módulo de evaluación y la documentación, estructura y contenido que se debe utilizar a la hora de definir uno de estos módulos.',
                            'iso_code': 'ISO/IEC 25042'
                        },
                        {
                            'title': 'Evaluation module for recoverability',
                            'description': 'Define un módulo para la evaluación de la subcaracterística Recuperabilidad (Recoverability).',
                            'iso_code': 'ISO/IEC 25045'
                        }
                    ]
                }
            ]
            
            # Crear secciones principales y sus subsecciones
            for section_data in iso25000_structure:
                # Crear sección principal
                new_section = SurveySection(
                    survey_id=iso_survey.id,
                    section_title=section_data['title'],
                    description=section_data['description']
                )
                session.add(new_section)
                session.commit()  # Commit para obtener el ID
                
                # Crear subsecciones
                for subsection_data in section_data['subsections']:
                    new_subsection = SurveySubSection(
                        section_id=new_section.id,
                        subsection_title=subsection_data['title'],
                        description=subsection_data['description'],
                        iso_code=subsection_data['iso_code']
                    )
                    session.add(new_subsection)
            
            session.commit()
            print("Estructura jerárquica ISO 25000 inicializada correctamente.")
        
        return iso_survey.id
        
    except Exception as e:
        session.rollback()
        print(f"Error al inicializar la estructura ISO 25000: {e}")
        raise e
    finally:
        session.close()


def get_survey_by_id(survey_id):
    session = SessionLocal()
    try:
        return session.query(Survey).options(
            joinedload(Survey.sections).joinedload(SurveySection.subsections).joinedload(SurveySubSection.items)
        ).filter(Survey.id == survey_id).one_or_none()
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
        current_app.logger.error(f"Error al guardar el formulario: {e}")
        raise e
    finally:
        session.close()


def clone_survey(original_survey_id, form_id, user_id):
    session = SessionLocal()
    try:
        # Obtener la encuesta original con toda su estructura
        original_survey = session.query(Survey).options(
            joinedload(Survey.sections).joinedload(SurveySection.subsections).joinedload(SurveySubSection.items)
        ).filter(Survey.id == original_survey_id).one_or_none()
        
        if not original_survey:
            raise ValueError("Encuesta original no encontrada.")

        cloned_survey = Survey(
            name=f"{original_survey.name} - {uuid.uuid4()}",
            description=original_survey.description,
        )
        session.add(cloned_survey)
        session.commit()

        # Clonar secciones, subsecciones e items
        for section in original_survey.sections:
            cloned_section = SurveySection(
                survey_id=cloned_survey.id,
                section_title=section.section_title,
                description=section.description,
            )
            session.add(cloned_section)
            session.commit()

            # Clonar subsecciones
            for subsection in section.subsections:
                cloned_subsection = SurveySubSection(
                    section_id=cloned_section.id,
                    subsection_title=subsection.subsection_title,
                    description=subsection.description,
                    iso_code=subsection.iso_code
                )
                session.add(cloned_subsection)
                session.commit()

                # Clonar items de la subsección
                for item in subsection.items:
                    cloned_item = SurveyItem(
                        subsection_id=cloned_subsection.id,
                        code=f"ITEM-{uuid.uuid4()}",
                        item_name=item.item_name,
                        description=item.description,
                        value=0,
                    )
                    session.add(cloned_item)

        session.commit()

        # Crear respuestas iniciales para todos los items clonados
        all_cloned_items = session.query(SurveyItem).join(SurveySubSection).join(SurveySection).filter(
            SurveySection.survey_id == cloned_survey.id
        ).all()

        for item in all_cloned_items:
            response = SurveyResponse(
                survey_id=cloned_survey.id,
                user_id=user_id,
                item_id=item.id,
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


def get_results_by_survey(survey_id, user_id):
    """
    Obtiene los resultados de la encuesta ISO 25000, incluyendo secciones y preguntas.
    """
    session = SessionLocal()
    try:
        current_app.logger.debug(f"Buscando resultados de la encuesta ISO 25000 (ID: {survey_id}) para el usuario {user_id}")
        
        # Consultar la encuesta para obtener sus detalles
        survey = session.query(Survey).filter(Survey.id == survey_id).one_or_none()
        if not survey:
            raise ValueError(f"No se encontró la encuesta ISO 25000 con ID {survey_id}")

        # Consultar respuestas de la encuesta
        responses = session.query(SurveyResponse).options(
            joinedload(SurveyResponse.item).joinedload(SurveyItem.section)
        ).filter(
            SurveyResponse.survey_id == survey_id,
            SurveyResponse.user_id == user_id
        ).all()

        if not responses:
            raise ValueError(f"No se encontraron respuestas para la encuesta ISO 25000 con ID {survey_id} del usuario {user_id}")

        # Estructurar los resultados y convertir Decimal a float
        results = [
            {
                "section_title": response.item.section.section_title,
                "item_name": response.item.item_name,
                "description": response.item.description,
                "value": float(response.value) if response.value is not None else 0.0,
                "max_value": 3.0,  # Supongamos que el valor máximo por respuesta es 3
                "percentage": (float(response.value) / 3.0) * 100 if response.value is not None else 0.0
            }
            for response in responses
        ]

        # Calcular totales
        total_score = sum(result["value"] for result in results)
        max_score = len(results) * 3
        overall_percentage = (total_score / max_score) * 100 if max_score > 0 else 0.0
        overall_result = calculate_overall_result(overall_percentage)

        current_app.logger.debug(f"Resultados procesados: {results}")

        return {
            "results": results,
            "total_score": float(total_score),
            "max_score": float(max_score),
            "overall_percentage": round(overall_percentage, 2),
            "overall_result": overall_result,
            "norm": "ISO 25000 Evaluation"  # Especificar explícitamente la norma ISO 25000
        }
    except Exception as e:
        current_app.logger.error(f"Error al obtener resultados de la encuesta ISO 25000 {survey_id}: {e}")
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


def get_form_data(form_id):
    """
    Obtiene los datos de un formulario basado en su ID.
    """
    session = SessionLocal()
    try:
        form = session.query(EvaluationForm).filter(EvaluationForm.id == form_id).one_or_none()
        if not form:
            raise ValueError(f"No se encontró el formulario con ID {form_id}")
        
        return {
            "date": form.date,
            "city": form.city,
            "company": form.company,
            "phone": form.phone,
            "software_name": form.software_name,
            "general_objectives": form.general_objectives,
            "specific_objectives": form.specific_objectives,
        }
    except Exception as e:
        current_app.logger.error(f"Error al obtener los datos del formulario: {e}")
        raise e
    finally:
        session.close()


def get_filtered_responses(survey_id, user_id):
    """
    Obtiene solo las respuestas más recientes por pregunta (item_id) para un usuario en una encuesta específica.
    """
    session = SessionLocal()
    try:
        latest_responses = session.query(
            SurveyResponse.item_id,
            func.max(SurveyResponse.id).label("latest_id")
        ).filter(
            SurveyResponse.survey_id == survey_id,
            SurveyResponse.user_id == user_id
        ).group_by(SurveyResponse.item_id).subquery()

        responses = session.query(SurveyResponse).join(
            latest_responses, SurveyResponse.id == latest_responses.c.latest_id
        ).options(
            joinedload(SurveyResponse.item).joinedload(SurveyItem.section)
        ).all()

        return responses
    except Exception as e:
        current_app.logger.error(f"Error al filtrar respuestas: {e}")
        raise e
    finally:
        session.close()


def get_user_survey_history(user_id):
    """
    Obtiene el historial de encuestas realizadas por un usuario con información detallada.
    """
    session = SessionLocal()
    try:
        # Consulta mejorada que incluye información del formulario
        results = (
            session.query(SurveyResults)
            .join(Survey, SurveyResults.survey_id == Survey.id)
            .join(EvaluationForm, SurveyResults.form_id == EvaluationForm.id)
            .filter(SurveyResults.user_id == user_id)
            .order_by(SurveyResults.id.desc())  # Más recientes primero
            .all()
        )
        
        history = []
        for result in results:
            history_item = {
                "survey_id": result.survey_id,
                "survey_name": result.survey.name,
                "total_score": result.total_score,
                "percentage": round(result.percentage, 2),
                "overall_result": result.overall_result,
                "completed_at": result.form.created_at.strftime('%d/%m/%Y %H:%M') if result.form.created_at else 'N/A',
                "response_id": result.response_id,
                "form_id": result.form_id,
                # Información del formulario
                "software_name": result.form.software_name,
                "company": result.form.company,
                "city": result.form.city,
                "date": result.form.date,
                # Información adicional
                "max_score": 119 * 3,  # Asumiendo 119 preguntas con valor máximo 3
                "questions_answered": result.total_score // 3 if result.total_score > 0 else 0
            }
            history.append(history_item)
        
        return history
    except Exception as e:
        current_app.logger.error(f"Error al obtener el historial de encuestas del usuario {user_id}: {e}")
        raise e
    finally:
        session.close()


def get_survey_details(survey_id):
    """
    Obtiene los detalles de una encuesta específica (secciones y preguntas).
    """
    session = SessionLocal()
    try:
        survey = session.query(Survey).filter(Survey.id == survey_id).one_or_none()
        if not survey:
            raise ValueError(f"No se encontró la encuesta con ID {survey_id}.")

        # Obtener secciones y preguntas relacionadas
        sections = session.query(SurveySection).filter(SurveySection.survey_id == survey_id).all()
        questions = session.query(SurveyItem).join(SurveySection).filter(SurveySection.survey_id == survey_id).all()

        # Estructurar los detalles de la encuesta
        survey_details = {
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
                            "code": question.code,
                            "value": question.value
                        }
                        for question in questions if question.section_id == section.id
                    ]
                }
                for section in sections
            ]
        }

        return survey_details
    except Exception as e:
        current_app.logger.error(f"Error al obtener detalles de la encuesta {survey_id}: {e}")
        raise e
    finally:
        session.close()


def get_sections_by_survey_id(survey_id):
    """
    Obtiene todas las secciones de una encuesta específica con sus subsecciones.
    """
    session = SessionLocal()
    try:
        sections = session.query(SurveySection).options(
            joinedload(SurveySection.subsections).joinedload(SurveySubSection.items)
        ).filter(
            SurveySection.survey_id == survey_id
        ).all()
        return sections
    except Exception as e:
        current_app.logger.error(f"Error al obtener secciones de la encuesta {survey_id}: {e}")
        raise e
    finally:
        session.close()


def get_subsections_by_section_id(section_id):
    """
    Obtiene todas las subsecciones de una sección específica con sus preguntas.
    """
    session = SessionLocal()
    try:
        subsections = session.query(SurveySubSection).options(
            joinedload(SurveySubSection.items)
        ).filter(
            SurveySubSection.section_id == section_id
        ).all()
        return subsections
    except Exception as e:
        current_app.logger.error(f"Error al obtener subsecciones de la sección {section_id}: {e}")
        raise e
    finally:
        session.close()


def get_subsection_by_id(subsection_id):
    """
    Obtiene una subsección específica por su ID con sus preguntas.
    """
    session = SessionLocal()
    try:
        subsection = session.query(SurveySubSection).options(
            joinedload(SurveySubSection.items)
        ).filter(
            SurveySubSection.id == subsection_id
        ).one_or_none()
        return subsection
    except Exception as e:
        current_app.logger.error(f"Error al obtener la subsección {subsection_id}: {e}")
        raise e
    finally:
        session.close()


def create_subsection(section_id, subsection_title, description, iso_code=None):
    """
    Crea una nueva subsección para una sección específica.
    """
    session = SessionLocal()
    try:
        new_subsection = SurveySubSection(
            section_id=section_id,
            subsection_title=subsection_title,
            description=description,
            iso_code=iso_code
        )
        session.add(new_subsection)
        session.commit()
        
        current_app.logger.info(f"Subsección creada exitosamente: {subsection_title}")
        return new_subsection.id
    except Exception as e:
        session.rollback()
        current_app.logger.error(f"Error al crear la subsección: {e}")
        raise e
    finally:
        session.close()


def update_subsection(subsection_id, subsection_title, description, iso_code=None):
    """
    Actualiza una subsección existente.
    """
    session = SessionLocal()
    try:
        subsection = session.query(SurveySubSection).filter(
            SurveySubSection.id == subsection_id
        ).one_or_none()
        
        if not subsection:
            raise ValueError(f"Subsección con ID {subsection_id} no encontrada.")
        
        subsection.subsection_title = subsection_title
        subsection.description = description
        subsection.iso_code = iso_code
        session.commit()
        
        current_app.logger.info(f"Subsección actualizada exitosamente: {subsection_title}")
        return subsection_id
    except Exception as e:
        session.rollback()
        current_app.logger.error(f"Error al actualizar la subsección {subsection_id}: {e}")
        raise e
    finally:
        session.close()


def delete_subsection(subsection_id):
    """
    Elimina una subsección y todas sus preguntas asociadas.
    """
    session = SessionLocal()
    try:
        subsection = session.query(SurveySubSection).filter(
            SurveySubSection.id == subsection_id
        ).one_or_none()
        
        if not subsection:
            raise ValueError(f"Subsección con ID {subsection_id} no encontrada.")
        
        subsection_title = subsection.subsection_title
        session.delete(subsection)
        session.commit()
        
        current_app.logger.info(f"Subsección eliminada exitosamente: {subsection_title}")
        return True
    except Exception as e:
        session.rollback()
        current_app.logger.error(f"Error al eliminar la subsección {subsection_id}: {e}")
        raise e
    finally:
        session.close()


def get_section_by_id(section_id):
    """
    Obtiene una sección específica por su ID.
    """
    session = SessionLocal()
    try:
        section = session.query(SurveySection).filter(
            SurveySection.id == section_id
        ).one_or_none()
        return section
    except Exception as e:
        current_app.logger.error(f"Error al obtener la sección {section_id}: {e}")
        raise e
    finally:
        session.close()


def create_section(survey_id, section_title, description):
    """
    Crea una nueva sección para una encuesta específica.
    """
    session = SessionLocal()
    try:
        new_section = SurveySection(
            survey_id=survey_id,
            section_title=section_title,
            description=description
        )
        session.add(new_section)
        session.commit()
        
        current_app.logger.info(f"Sección creada exitosamente: {section_title}")
        return new_section.id
    except Exception as e:
        session.rollback()
        current_app.logger.error(f"Error al crear la sección: {e}")
        raise e
    finally:
        session.close()


def update_section(section_id, section_title, description):
    """
    Actualiza una sección existente.
    """
    session = SessionLocal()
    try:
        section = session.query(SurveySection).filter(
            SurveySection.id == section_id
        ).one_or_none()
        
        if not section:
            raise ValueError(f"Sección con ID {section_id} no encontrada.")
        
        section.section_title = section_title
        section.description = description
        session.commit()
        
        current_app.logger.info(f"Sección actualizada exitosamente: {section_title}")
        return section_id
    except Exception as e:
        session.rollback()
        current_app.logger.error(f"Error al actualizar la sección {section_id}: {e}")
        raise e
    finally:
        session.close()


def delete_section(section_id):
    """
    Elimina una sección y todas sus preguntas asociadas.
    """
    session = SessionLocal()
    try:
        section = session.query(SurveySection).filter(
            SurveySection.id == section_id
        ).one_or_none()
        
        if not section:
            raise ValueError(f"Sección con ID {section_id} no encontrada.")
        
        # Las preguntas se eliminan automáticamente por la relación CASCADE
        section_title = section.section_title
        session.delete(section)
        session.commit()
        
        current_app.logger.info(f"Sección eliminada exitosamente: {section_title}")
        return True
    except Exception as e:
        session.rollback()
        current_app.logger.error(f"Error al eliminar la sección {section_id}: {e}")
        raise e
    finally:
        session.close()


def get_user_survey_details(user_id, survey_id):
    """
    Obtiene los detalles específicos de una encuesta realizada por un usuario,
    incluyendo las respuestas dadas.
    """
    session = SessionLocal()
    try:
        # Obtener información básica de la encuesta y resultado
        survey_result = (
            session.query(SurveyResults)
            .join(Survey, SurveyResults.survey_id == Survey.id)
            .join(EvaluationForm, SurveyResults.form_id == EvaluationForm.id)
            .filter(
                SurveyResults.user_id == user_id,
                SurveyResults.survey_id == survey_id
            )
            .first()
        )
        
        if not survey_result:
            raise ValueError(f"No se encontró resultado de encuesta para usuario {user_id} y encuesta {survey_id}")
        
        # Obtener todas las respuestas del usuario para esta encuesta
        responses = (
            session.query(SurveyResponse)
            .join(SurveyItem, SurveyResponse.item_id == SurveyItem.id)
            .join(SurveySubSection, SurveyItem.subsection_id == SurveySubSection.id)
            .join(SurveySection, SurveySubSection.section_id == SurveySection.id)
            .filter(
                SurveyResponse.survey_id == survey_id,
                SurveyResponse.user_id == user_id
            )
            .order_by(SurveySection.id, SurveySubSection.id, SurveyItem.id)
            .all()
        )
        
        # Organizar respuestas por sección y subsección
        sections_data = {}
        for response in responses:
            section_id = response.item.subsection.section.id
            section_title = response.item.subsection.section.section_title
            subsection_id = response.item.subsection.id
            subsection_title = response.item.subsection.subsection_title
            
            if section_id not in sections_data:
                sections_data[section_id] = {
                    'section_title': section_title,
                    'subsections': {}
                }
            
            if subsection_id not in sections_data[section_id]['subsections']:
                sections_data[section_id]['subsections'][subsection_id] = {
                    'subsection_title': subsection_title,
                    'iso_code': response.item.subsection.iso_code,
                    'questions': []
                }
            
            sections_data[section_id]['subsections'][subsection_id]['questions'].append({
                'item_name': response.item.item_name,
                'description': response.item.description,
                'value': response.value,
                'max_value': 3,
                'percentage': (response.value / 3 * 100) if response.value else 0
            })
        
        # Estructurar el resultado final
        details = {
            'survey_id': survey_result.survey_id,
            'survey_name': survey_result.survey.name,
            'survey_description': survey_result.survey.description,
            'total_score': survey_result.total_score,
            'percentage': round(survey_result.percentage, 2),
            'overall_result': survey_result.overall_result,
            'completed_at': survey_result.form.created_at.strftime('%d/%m/%Y %H:%M'),
            'response_id': survey_result.response_id,
            # Información del formulario
            'form_data': {
                'software_name': survey_result.form.software_name,
                'company': survey_result.form.company,
                'city': survey_result.form.city,
                'date': survey_result.form.date,
                'phone': survey_result.form.phone,
                'general_objectives': survey_result.form.general_objectives,
                'specific_objectives': survey_result.form.specific_objectives
            },
            # Respuestas organizadas
            'sections': [
                {
                    'section_title': section_data['section_title'],
                    'subsections': [
                        {
                            'subsection_title': subsection_data['subsection_title'],
                            'iso_code': subsection_data['iso_code'],
                            'questions': subsection_data['questions']
                        }
                        for subsection_data in section_data['subsections'].values()
                    ]
                }
                for section_data in sections_data.values()
            ],
            'statistics': {
                'total_questions': len(responses),
                'max_possible_score': len(responses) * 3,
                'questions_answered': len([r for r in responses if r.value is not None and r.value > 0])
            }
        }
        
        return details
    except Exception as e:
        current_app.logger.error(f"Error al obtener detalles de encuesta {survey_id} para usuario {user_id}: {e}")
        raise e
    finally:
        session.close()
