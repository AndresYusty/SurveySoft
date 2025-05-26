# SurveySoft - ISO 25000 Evaluation Tool

## Descripción

Esta aplicación ha sido especializada para enfocarse **exclusivamente** en la evaluación de calidad de software según el estándar **ISO 25000**. 

## Características Principales

- ✅ **Enfoque exclusivo en ISO 25000**: La aplicación solo trabaja con evaluaciones basadas en este estándar internacional
- ✅ **Selección automática**: El sistema selecciona automáticamente la encuesta ISO 25000 sin requerir intervención del usuario
- ✅ **Interfaz especializada**: UI optimizada para el flujo de trabajo específico de ISO 25000
- ✅ **Reportes especializados**: Generación de PDFs con resultados específicos para ISO 25000

## Cambios Realizados

### 1. Servicios Modificados
- **`survey_service.py`**: Modificado para filtrar únicamente encuestas ISO 25000
- **`question_controller.py`**: Actualizado para selección automática de ISO 25000

### 2. Templates Actualizados
- **`home.html`**: Rediseñado para mostrar la especialización en ISO 25000
- **`select_survey.html`**: Convertido en página informativa sobre ISO 25000

### 3. Mantenimiento de la Base de Datos
- ✅ **Sin cambios en la configuración**: Las conexiones y configuraciones de BD permanecen intactas
- ✅ **Sin eliminación de datos**: Los datos existentes se mantienen, solo se filtra a nivel de aplicación
- ✅ **Compatibilidad preservada**: La estructura de la BD permanece compatible

## Flujo de Trabajo

1. **Formulario inicial**: El usuario completa los datos del software a evaluar
2. **Selección automática**: El sistema selecciona automáticamente ISO 25000
3. **Evaluación**: Se presenta la encuesta específica de ISO 25000
4. **Resultados**: Se generan reportes especializados en ISO 25000

## Estructura del Proyecto

```
question-service/
├── controllers/
│   ├── question_controller.py    # Controlador principal (modificado)
│   ├── auth_controller.py
│   ├── history_controller.py
│   └── risk_controller.py
├── services/
│   └── survey_service.py         # Servicio principal (modificado)
├── templates/
│   └── survey/
│       ├── home.html            # Página principal (rediseñada)
│       └── select_survey.html   # Página informativa (actualizada)
├── models/
│   └── survey.py
├── database.py                  # Sin cambios - mantiene configuración original
└── main.py
```

## Instalación y Ejecución

1. Navegar al directorio del microservicio:
   ```bash
   cd question-service
   ```

2. Ejecutar la aplicación:
   ```bash
   python main.py
   ```

3. La aplicación estará disponible en: `http://localhost:5002`

## Notas Importantes

- **Preservación de datos**: Todos los datos existentes en la base de datos se mantienen intactos
- **Filtrado a nivel de aplicación**: Los cambios son solo en la lógica de negocio, no en la estructura de datos
- **Reversibilidad**: Los cambios pueden revertirse fácilmente modificando los filtros en el código

## Beneficios de la Especialización

1. **Simplicidad**: Interface más limpia y enfocada
2. **Eficiencia**: Flujo de trabajo optimizado para ISO 25000
3. **Especialización**: Herramienta dedicada exclusivamente a este estándar
4. **Mantenibilidad**: Código más simple y fácil de mantener 