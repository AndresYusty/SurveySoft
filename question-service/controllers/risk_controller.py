from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import SessionLocal
from models.risk_matrix import RiskMatrix 
from models.survey import EvaluationForm, SurveyResults
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from flask import current_app
from functools import wraps
from datetime import datetime

risk_bp = Blueprint('risk', __name__)

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session or session['role'] not in roles:
                flash("No tienes permiso para acceder a esta página.", "error")
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@risk_bp.route('/', methods=['GET', 'POST'])
@role_required('user', 'admin')  # Require user or admin role
def manage_risks():
    if 'user_id' not in session:
        flash("Debes iniciar sesión para acceder a esta página.", "error")
        return redirect(url_for('auth.login'))

    session_db = SessionLocal()
    try:
        if request.method == 'POST':
            # Recibir datos del formulario
            software_name = request.form['software_name']
            description = request.form['description']
            probability = request.form['probability']
            impact = request.form['impact']
            risk_level = request.form['risk_level']
            mitigation = request.form.get('mitigation', '')

            # Mapear el nivel de riesgo al formato correcto
            risk_level_mapping = {
                'Bajo': 'Bajo',
                'Medio': 'Moderado',
                'Alto': 'Crítico'
            }
            mapped_risk_level = risk_level_mapping.get(risk_level, 'Moderado')

            try:
                # Verificar si el software ya existe
                software = session_db.query(EvaluationForm).filter(
                    EvaluationForm.software_name == software_name
                ).first()

                # Si no existe, crear nuevo software
                if not software:
                    software = EvaluationForm(
                        software_name=software_name,
                        date=datetime.now().strftime('%Y-%m-%d'),
                        city='N/A',
                        company='N/A',
                        phone='N/A',
                        general_objectives='N/A',
                        specific_objectives='N/A'
                    )
                    session_db.add(software)
                    session_db.flush()  # Para obtener el ID del nuevo software

                # Crear un nuevo riesgo
                new_risk = RiskMatrix(
                    software_id=software.id,
                    user_id=session['user_id'],
                    description=description,
                    probability=probability,
                    impact=impact,
                    risk_level=mapped_risk_level,
                    mitigation=mitigation
                )
                session_db.add(new_risk)
                session_db.commit()
                flash("Riesgo agregado exitosamente.", "success")
                return redirect(url_for('risk.manage_risks'))
            except IntegrityError as e:
                session_db.rollback()
                if "foreign key constraint fails" in str(e):
                    flash("Error: El usuario no existe en el sistema. Por favor, inicie sesión nuevamente.", "error")
                else:
                    flash("Error al agregar el riesgo. Por favor, intente nuevamente.", "error")
                print(f"Error de integridad: {str(e)}")
                return redirect(url_for('risk.manage_risks'))

        # Obtener la página actual
        page = request.args.get('page', 1, type=int)
        per_page = 10  # Número de elementos por página

        # Obtener el total de riesgos
        total_risks = session_db.query(RiskMatrix).filter(
            RiskMatrix.user_id == session['user_id']
        ).count()
        print(f"Total de riesgos: {total_risks}")

        # Calcular el total de páginas
        total_pages = (total_risks + per_page - 1) // per_page
        print(f"Total de páginas: {total_pages}")

        # Obtener los riesgos paginados
        risks = session_db.query(RiskMatrix).join(
            EvaluationForm, RiskMatrix.software_id == EvaluationForm.id
        ).filter(
            RiskMatrix.user_id == session['user_id']
        ).order_by(
            RiskMatrix.risk_id.desc()
        ).offset(
            (page - 1) * per_page
        ).limit(per_page).all()
        
        print(f"Riesgos obtenidos: {len(risks)}")
        for risk in risks:
            print(f"Riesgo ID: {risk.risk_id}, Software: {risk.software.software_name}, Descripción: {risk.description}")
        
        # Obtener la lista de software evaluado por el usuario (los que aparecen en el historial)
        software_list = (
            session_db.query(EvaluationForm)
            .join(SurveyResults, SurveyResults.form_id == EvaluationForm.id)
            .filter(SurveyResults.user_id == session['user_id'])
            .distinct()
            .all()
        )
        
        return render_template(
            'risk/manage_risk.html',
            risks=risks,
            software_list=software_list,
            current_page=page,
            total_pages=total_pages
        )
    except SQLAlchemyError as e:
        session_db.rollback()
        flash("Ocurrió un error al gestionar los riesgos.", "error")
        print(f"Error SQL: {str(e)}")
        return redirect(url_for('risk.manage_risks'))
    finally:
        session_db.close()

@risk_bp.route('/delete/<int:risk_id>', methods=['POST'])
@role_required('user', 'admin')
def delete_risk(risk_id):
    session_db = SessionLocal()
    try:
        risk = session_db.query(RiskMatrix).filter_by(risk_id=risk_id, user_id=session['user_id']).first()
        if not risk:
            flash("Riesgo no encontrado o no autorizado.", "error")
            return redirect(url_for('risk.manage_risks'))
        session_db.delete(risk)
        session_db.commit()
        flash("Riesgo eliminado exitosamente.", "success")
    except Exception as e:
        session_db.rollback()
        flash("Error al eliminar el riesgo.", "error")
        print(str(e))
    finally:
        session_db.close()
    return redirect(url_for('risk.manage_risks'))

@risk_bp.route('/edit/<int:risk_id>', methods=['POST'])
@role_required('user', 'admin')
def edit_risk(risk_id):
    session_db = SessionLocal()
    try:
        risk = session_db.query(RiskMatrix).filter_by(risk_id=risk_id, user_id=session['user_id']).first()
        if not risk:
            flash("Riesgo no encontrado o no autorizado.", "error")
            return redirect(url_for('risk.manage_risks'))
        # Actualiza los campos
        risk.description = request.form['description']
        risk.probability = request.form['probability']
        risk.impact = request.form['impact']
        risk.risk_level = request.form['risk_level']
        risk.mitigation = request.form.get('mitigation', '')
        session_db.commit()
        flash("Riesgo editado exitosamente.", "success")
    except Exception as e:
        session_db.rollback()
        flash("Error al editar el riesgo.", "error")
        print(str(e))
    finally:
        session_db.close()
    return redirect(url_for('risk.manage_risks'))