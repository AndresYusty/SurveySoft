from flask import Blueprint, request, render_template, redirect, url_for, session, flash
from services.auth_service import create_user, authenticate_user, request_password_reset, reset_password

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Validar que se proporcionen ambos campos
        if not username or not password:
            flash("Por favor, ingresa tanto el usuario como la contraseña.", "error")
            return render_template('auth/login.html')
        
        user = authenticate_user(username, password)  # Obtén el usuario autenticado
        if user:
            session['user_id'] = user.id  # Guarda el ID del usuario en la sesión
            session['username'] = user.username
            session['role'] = user.role
            flash("Inicio de sesión exitoso.", "success")
            
            # Redirige según el rol
            if user.role == 'admin':
                return redirect(url_for('auth.admin_dashboard'))
            elif user.role == 'user':
                return redirect(url_for('auth.user_dashboard'))
        else:
            flash("Usuario o contraseña incorrectos. Por favor, verifica tus credenciales e intenta nuevamente.", "error")
    return render_template('auth/login.html')

# Ruta para el dashboard de admin
@auth_bp.route('/admin/dashboard')
def admin_dashboard():
    if 'role' not in session or session['role'] != 'admin':
        flash("No tienes permiso para acceder a esta página.", "error")
        return redirect(url_for('auth.login'))
    return render_template('auth/admin_dashboard.html', username=session['username'])

@auth_bp.route('/user/dashboard')
def user_dashboard():
    if 'role' not in session or session['role'] != 'user':
        flash("No tienes permiso para acceder a esta página.", "error")
        return redirect(url_for('auth.login'))
    return render_template(
        'auth/dashboard.html',
        username=session['username'],
        user_id=session['user_id']  # Pasa el user_id a la plantilla
    )


# Ruta para el registro
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form.get('email')  # El email es opcional
        
        # Validar que se proporcionen los campos requeridos
        if not username or not password:
            flash("Por favor, completa todos los campos requeridos.", "error")
            return render_template('auth/register.html')
        
        user = create_user(username, password, email)
        if user is None:
            flash("El usuario ya existe. Por favor, elige un nombre de usuario diferente.", "error")
        else:
            flash("Registro exitoso. Ahora puedes iniciar sesión.", "success")
            return redirect(url_for('auth.login'))
    return render_template('auth/register.html')

# Ruta para cerrar sesión
@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("Sesión cerrada exitosamente.", "success")
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            flash("Por favor, ingresa tu correo electrónico.", "error")
            return render_template('auth/forgot_password.html')
        
        success, message = request_password_reset(email)
        if success:
            flash(message, "success")
            return redirect(url_for('auth.login'))
        else:
            flash(message, "error")
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password_route(token):
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not password or not confirm_password:
            flash("Por favor, completa todos los campos.", "error")
            return render_template('auth/reset_password.html', token=token)
        
        if password != confirm_password:
            flash("Las contraseñas no coinciden.", "error")
            return render_template('auth/reset_password.html', token=token)
        
        if reset_password(token, password):
            flash("Tu contraseña ha sido restablecida exitosamente.", "success")
            return redirect(url_for('auth.login'))
        else:
            flash("El enlace de restablecimiento es inválido o ha expirado.", "error")
            return redirect(url_for('auth.forgot_password'))
    
    return render_template('auth/reset_password.html', token=token)
