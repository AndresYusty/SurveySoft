from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, 
    PageBreak, KeepTogether, Image, Frame, PageTemplate
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from io import BytesIO
from datetime import datetime


def create_custom_styles():
    """Crea estilos personalizados para el PDF"""
    styles = getSampleStyleSheet()
    
    # Estilo para el título principal
    styles.add(ParagraphStyle(
        name='CustomTitle',
        parent=styles['Title'],
        fontSize=22,
        spaceAfter=25,
        spaceBefore=10,
        textColor=colors.HexColor('#2C3E50'),
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    ))
    
    # Estilo para subtítulos de sección
    styles.add(ParagraphStyle(
        name='SectionTitle',
        parent=styles['Heading1'],
        fontSize=14,
        spaceAfter=15,
        spaceBefore=25,
        textColor=colors.HexColor('#34495E'),
        fontName='Helvetica-Bold',
        borderWidth=1,
        borderColor=colors.HexColor('#3498DB'),
        borderPadding=8,
        backColor=colors.HexColor('#F8F9FA')
    ))
    
    # Estilo para subsecciones
    styles.add(ParagraphStyle(
        name='SubsectionTitle',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=10,
        spaceBefore=15,
        textColor=colors.HexColor('#2980B9'),
        fontName='Helvetica-Bold'
    ))
    
    # Estilo para información general
    styles.add(ParagraphStyle(
        name='InfoStyle',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        spaceBefore=2,
        textColor=colors.HexColor('#2C3E50'),
        fontName='Helvetica'
    ))
    
    # Estilo para resultados destacados
    styles.add(ParagraphStyle(
        name='ResultHighlight',
        parent=styles['Normal'],
        fontSize=13,
        spaceAfter=12,
        spaceBefore=12,
        textColor=colors.white,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        borderWidth=2,
        borderColor=colors.HexColor('#27AE60'),
        borderPadding=12,
        backColor=colors.HexColor('#27AE60')
    ))
    
    # Estilo para sugerencias
    styles.add(ParagraphStyle(
        name='SuggestionStyle',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=8,
        spaceBefore=3,
        textColor=colors.HexColor('#2C3E50'),
        fontName='Helvetica',
        leftIndent=15,
        bulletIndent=8
    ))
    
    return styles


def get_result_color(percentage):
    """Retorna el color basado en el porcentaje de resultado"""
    if percentage >= 90:
        return colors.HexColor('#27AE60')  # Verde - Excelente
    elif percentage >= 70:
        return colors.HexColor('#3498DB')  # Azul - Sobresaliente
    elif percentage >= 50:
        return colors.HexColor('#F39C12')  # Naranja - Aceptable
    elif percentage >= 30:
        return colors.HexColor('#E67E22')  # Naranja oscuro - Insuficiente
    else:
        return colors.HexColor('#E74C3C')  # Rojo - Deficiente


def generate_specific_suggestions(overall_percentage, section_percentages):
    """Genera sugerencias específicas y detalladas basadas en los resultados obtenidos"""
    suggestions = []
    
    # Análisis del resultado general
    if overall_percentage >= 90:
        suggestions.extend([
            "Su software demuestra excelencia en calidad. Mantenga estos estándares altos.",
            "Documente las mejores prácticas implementadas para futuros proyectos.",
            "Considere ser un modelo de referencia para otros equipos de desarrollo.",
            "Implemente un sistema de monitoreo continuo para mantener la calidad."
        ])
    elif overall_percentage >= 70:
        suggestions.extend([
            "Su software tiene buena calidad, pero puede mejorar en áreas específicas.",
            "Identifique y priorice las secciones con menor puntuación.",
            "Establezca un plan de mejora continua con objetivos medibles.",
            "Capacite al equipo en las áreas que necesitan fortalecimiento."
        ])
    elif overall_percentage >= 50:
        suggestions.extend([
            "Su software requiere mejoras importantes para alcanzar estándares óptimos.",
            "Enfóquese en las áreas críticas identificadas en la evaluación.",
            "Implemente procesos de revisión de código más rigurosos.",
            "Considere refactorización en módulos con baja puntuación."
        ])
    elif overall_percentage >= 30:
        suggestions.extend([
            "Se requiere una revisión integral del software y procesos de desarrollo.",
            "Priorice la corrección de deficiencias críticas de seguridad y funcionalidad.",
            "Implemente testing automatizado y revisiones de calidad obligatorias.",
            "Considere consultoría especializada en arquitectura de software."
        ])
    else:
        suggestions.extend([
            "Es necesaria una reestructuración completa del software.",
            "Revise la arquitectura fundamental y patrones de diseño utilizados.",
            "Implemente un programa integral de mejora de calidad.",
            "Considere rediseño de componentes críticos con baja puntuación."
        ])
    
    # Análisis específico por secciones
    if section_percentages:
        critical_areas = [name for name, perc in section_percentages.items() if perc < 40]
        improvement_areas = [name for name, perc in section_percentages.items() if 40 <= perc < 70]
        strong_areas = [name for name, perc in section_percentages.items() if perc >= 70]
        
        if critical_areas:
            suggestions.append(f"ÁREAS CRÍTICAS que requieren atención inmediata: {', '.join(critical_areas[:3])}")
            
        if improvement_areas:
            suggestions.append(f"Áreas con oportunidades de mejora: {', '.join(improvement_areas[:3])}")
            
        if strong_areas:
            suggestions.append(f"Fortalezas identificadas: {', '.join(strong_areas[:3])}")
    
    # Recomendaciones técnicas específicas
    technical_suggestions = [
        "Implemente pruebas unitarias con cobertura mínima del 80%",
        "Establezca revisiones de código obligatorias antes de cada merge",
        "Use herramientas de análisis estático de código (SonarQube, ESLint)",
        "Documente APIs y interfaces de manera detallada",
        "Implemente logging y monitoreo de errores en producción",
        "Establezca métricas de rendimiento y alertas automáticas"
    ]
    
    # Agregar sugerencias técnicas basadas en el nivel de calidad
    if overall_percentage < 70:
        suggestions.extend(technical_suggestions[:4])
    else:
        suggestions.extend(technical_suggestions[4:])
    
    return suggestions[:12]  # Limitar a 12 sugerencias máximo


def create_summary_table(total_score, max_score, percentage, overall_result, total_responses):
    """Crea una tabla resumen con los resultados principales - sin decimales innecesarios"""
    # Redondear valores para mejor legibilidad
    percentage_rounded = round(percentage)
    
    data = [
        ['Métrica', 'Valor', 'Descripción'],
        ['Puntaje Total', f'{int(total_score)} / {max_score}', 'Puntos obtenidos vs máximo posible'],
        ['Porcentaje de Calidad', f'{percentage_rounded}%', 'Nivel de cumplimiento general'],
        ['Clasificación', overall_result, 'Resultado según estándares ISO 25000'],
        ['Criterios Evaluados', str(total_responses), 'Total de aspectos analizados']
    ]
    
    table = Table(data, colWidths=[4.5*cm, 3*cm, 7.5*cm])
    
    # Estilo de la tabla mejorado
    table_style = TableStyle([
        # Encabezado
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        
        # Contenido
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (0, 1), (1, -1), 'CENTER'),
        ('ALIGN', (2, 1), (2, -1), 'LEFT'),
        
        # Bordes y colores alternos
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#BDC3C7')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F8F9FA'), colors.white]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ])
    
    table.setStyle(table_style)
    return table


def create_detailed_results_table(responses):
    """Crea una tabla detallada con todos los resultados por sección - mejorada para evitar superposición"""
    # Organizar respuestas por sección y subsección
    sections_data = {}
    
    for response in responses:
        try:
            section_title = response.item.subsection.section.section_title
            subsection_title = response.item.subsection.subsection_title
            
            if section_title not in sections_data:
                sections_data[section_title] = {}
            
            if subsection_title not in sections_data[section_title]:
                sections_data[section_title][subsection_title] = []
            
            sections_data[section_title][subsection_title].append({
                'item_name': response.item.item_name,
                'value': response.value,
                'max_value': 3,
                'percentage': round((response.value / 3) * 100) if response.value else 0
            })
        except Exception as e:
            continue
    
    elements = []
    
    for section_title, subsections in sections_data.items():
        # Título de sección con espaciado mejorado
        elements.append(Spacer(1, 15))
        elements.append(Paragraph(f"<b>{section_title}</b>", 
                                ParagraphStyle('SectionHeader', 
                                             fontSize=13, 
                                             spaceAfter=12,
                                             spaceBefore=8,
                                             textColor=colors.HexColor('#2C3E50'),
                                             fontName='Helvetica-Bold')))
        
        for subsection_title, items in subsections.items():
            # Título de subsección con espaciado
            elements.append(Spacer(1, 8))
            elements.append(Paragraph(f"<i>{subsection_title}</i>", 
                                    ParagraphStyle('SubsectionHeader', 
                                                 fontSize=11, 
                                                 spaceAfter=8,
                                                 spaceBefore=5,
                                                 textColor=colors.HexColor('#34495E'),
                                                 fontName='Helvetica-Bold')))
            
            # Tabla de items con mejor espaciado
            data = [['Criterio de Evaluación', 'Puntos', '%']]
            
            for item in items:
                # Truncar texto de manera más inteligente
                item_name = item['item_name']
                if len(item_name) > 55:
                    # Buscar un espacio cerca del límite para cortar mejor
                    cut_point = item_name.rfind(' ', 0, 52)
                    if cut_point > 40:
                        item_name = item_name[:cut_point] + "..."
                    else:
                        item_name = item_name[:52] + "..."
                
                data.append([
                    item_name,
                    f"{int(item['value'])}/{item['max_value']}",
                    f"{item['percentage']}%"
                ])
            
            table = Table(data, colWidths=[11*cm, 2*cm, 2*cm])
            
            table_style = TableStyle([
                # Encabezado
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                
                # Contenido
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                
                # Bordes y espaciado mejorado
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BDC3C7')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F8F9FA'), colors.white]),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ])
            
            table.setStyle(table_style)
            elements.append(table)
            elements.append(Spacer(1, 12))
        
        elements.append(Spacer(1, 20))
    
    return elements


def generate_improved_pdf(survey_id, responses, survey, form_data, total_score, max_score, overall_percentage, overall_result):
    """Genera un PDF mejorado con mejor organización y sin superposición de textos"""
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2.5*cm,
        bottomMargin=2.5*cm
    )
    
    # Obtener estilos personalizados
    styles = create_custom_styles()
    
    # Lista de elementos del PDF
    elements = []
    
    # ==================== PORTADA ====================
    elements.append(Paragraph("REPORTE DE EVALUACIÓN", styles['CustomTitle']))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph("ISO/IEC 25000 - Calidad de Software", styles['CustomTitle']))
    elements.append(Spacer(1, 25))
    
    # Información del proyecto
    elements.append(Paragraph("INFORMACIÓN DEL PROYECTO", styles['SectionTitle']))
    elements.append(Spacer(1, 12))
    
    project_info = [
        f"<b>Software Evaluado:</b> {form_data.get('software_name', 'N/A')}",
        f"<b>Empresa:</b> {form_data.get('company', 'N/A')}",
        f"<b>Ciudad:</b> {form_data.get('city', 'N/A')}",
        f"<b>Fecha de Evaluación:</b> {form_data.get('date', 'N/A')}",
        f"<b>Norma de Evaluación:</b> {survey.name if survey else 'N/A'}",
        f"<b>ID de Encuesta:</b> {survey_id}",
        f"<b>Fecha de Reporte:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    ]
    
    for info in project_info:
        elements.append(Paragraph(info, styles['InfoStyle']))
        elements.append(Spacer(1, 3))
    
    elements.append(Spacer(1, 25))
    
    # Verificar si hay respuestas
    if not responses or len(responses) == 0:
        # ==================== REPORTE INCOMPLETO ====================
        elements.append(Paragraph("ESTADO DE LA EVALUACIÓN", styles['SectionTitle']))
        elements.append(Spacer(1, 15))
        
        # Mensaje de estado incompleto
        incomplete_style = ParagraphStyle(
            'IncompleteHighlight',
            parent=styles['ResultHighlight'],
            backColor=colors.HexColor('#E67E22'),
            borderColor=colors.HexColor('#E67E22')
        )
        
        elements.append(Paragraph("EVALUACIÓN INCOMPLETA - SIN RESPUESTAS", incomplete_style))
        elements.append(Spacer(1, 20))
        
        # Información sobre el estado
        elements.append(Paragraph("INFORMACIÓN DEL ESTADO", styles['SubsectionTitle']))
        elements.append(Spacer(1, 8))
        
        incomplete_info = [
            "La encuesta ha sido iniciada pero no se han registrado respuestas completas.",
            "Para generar un reporte de evaluación completo, es necesario completar al menos una sección de la encuesta.",
            "Una vez completadas las respuestas, podrá generar un reporte detallado con resultados y recomendaciones."
        ]
        
        for info in incomplete_info:
            elements.append(Paragraph(f"• {info}", styles['InfoStyle']))
            elements.append(Spacer(1, 5))
        
        elements.append(Spacer(1, 20))
        
        # Instrucciones para completar
        elements.append(Paragraph("PRÓXIMOS PASOS", styles['SubsectionTitle']))
        elements.append(Spacer(1, 8))
        
        next_steps = [
            "Acceda nuevamente al sistema de evaluación.",
            "Complete las secciones de la encuesta según los criterios ISO 25000.",
            "Guarde sus respuestas al finalizar cada sección.",
            "Genere el reporte final una vez completada la evaluación."
        ]
        
        for i, step in enumerate(next_steps, 1):
            elements.append(Paragraph(f"{i}. {step}", styles['SuggestionStyle']))
            elements.append(Spacer(1, 4))
        
    else:
        # ==================== RESUMEN EJECUTIVO ====================
        elements.append(Paragraph("RESUMEN EJECUTIVO", styles['SectionTitle']))
        elements.append(Spacer(1, 15))
        
        # Resultado destacado - sin decimales innecesarios
        result_color = get_result_color(overall_percentage)
        result_style = ParagraphStyle(
            'ResultHighlight',
            parent=styles['ResultHighlight'],
            backColor=result_color,
            borderColor=result_color
        )
        
        percentage_display = round(overall_percentage)
        elements.append(Paragraph(f"RESULTADO GENERAL: {overall_result} ({percentage_display}%)", result_style))
        elements.append(Spacer(1, 20))
        
        # Tabla resumen
        summary_table = create_summary_table(total_score, max_score, overall_percentage, overall_result, len(responses))
        elements.append(summary_table)
        elements.append(Spacer(1, 20))
        
        # Interpretación del resultado
        elements.append(Paragraph("INTERPRETACIÓN DEL RESULTADO", styles['SubsectionTitle']))
        elements.append(Spacer(1, 8))
        
        interpretation = ""
        if overall_percentage >= 90:
            interpretation = "El software evaluado demuestra un <b>nivel excepcional</b> de calidad, cumpliendo con los más altos estándares ISO 25000. Esto indica una implementación sobresaliente de las mejores prácticas de desarrollo de software."
        elif overall_percentage >= 70:
            interpretation = "El software presenta un <b>buen nivel de calidad</b> según los estándares ISO 25000, con oportunidades específicas de mejora en algunas áreas para alcanzar la excelencia."
        elif overall_percentage >= 50:
            interpretation = "El software cumple con un <b>nivel aceptable</b> de calidad, pero requiere mejoras en varias áreas para optimizar su rendimiento y cumplimiento de estándares."
        elif overall_percentage >= 30:
            interpretation = "El software presenta <b>deficiencias significativas</b> que requieren atención inmediata para cumplir con los estándares mínimos de calidad ISO 25000."
        else:
            interpretation = "El software requiere una <b>revisión integral</b> y mejoras sustanciales en múltiples áreas para alcanzar los estándares básicos de calidad."
        
        elements.append(Paragraph(interpretation, styles['InfoStyle']))
        elements.append(PageBreak())
        
        # ==================== RESULTADOS DETALLADOS ====================
        elements.append(Paragraph("RESULTADOS DETALLADOS POR SECCIÓN", styles['SectionTitle']))
        elements.append(Spacer(1, 15))
        
        # Agregar tabla detallada
        detailed_elements = create_detailed_results_table(responses)
        elements.extend(detailed_elements)
        
        elements.append(PageBreak())
        
        # ==================== SUGERENCIAS Y RECOMENDACIONES ====================
        elements.append(Paragraph("SUGERENCIAS Y RECOMENDACIONES", styles['SectionTitle']))
        elements.append(Spacer(1, 15))
        
        # Calcular datos de secciones para sugerencias más específicas
        sections_data = {}
        for response in responses:
            try:
                section_title = response.item.subsection.section.section_title
                if section_title not in sections_data:
                    sections_data[section_title] = []
                sections_data[section_title].append(response.value if response.value else 0)
            except:
                continue
        
        # Calcular porcentajes por sección (sin decimales)
        section_percentages = {}
        for section, values in sections_data.items():
            if values:
                avg_score = sum(values) / len(values)
                section_percentages[section] = round((avg_score / 3) * 100)
        
        # Generar sugerencias específicas
        suggestions = generate_specific_suggestions(overall_percentage, section_percentages)
        
        elements.append(Paragraph("Basándose en los resultados de la evaluación, se recomiendan las siguientes acciones:", styles['InfoStyle']))
        elements.append(Spacer(1, 12))
        
        for i, suggestion in enumerate(suggestions, 1):
            elements.append(Paragraph(f"{i}. {suggestion}", styles['SuggestionStyle']))
            elements.append(Spacer(1, 4))
        
        elements.append(Spacer(1, 20))
        
        # ==================== PLAN DE ACCIÓN SUGERIDO ====================
        elements.append(Paragraph("PLAN DE ACCIÓN SUGERIDO", styles['SubsectionTitle']))
        elements.append(Spacer(1, 10))
        
        action_plan = []
        if overall_percentage >= 70:
            action_plan = [
                "<b>Corto Plazo (1-2 meses):</b> Optimizar las áreas identificadas con menor puntuación.",
                "<b>Mediano Plazo (3-4 meses):</b> Implementar mejores prácticas en desarrollo y testing.",
                "<b>Largo Plazo (6 meses):</b> Establecer sistema de mejora continua y documentación.",
                "<b>Seguimiento:</b> Evaluaciones trimestrales para mantener los estándares de calidad."
            ]
        else:
            action_plan = [
                "<b>Inmediato (2-4 semanas):</b> Abordar deficiencias críticas de seguridad y funcionalidad.",
                "<b>Corto Plazo (2-3 meses):</b> Refactorizar componentes con baja puntuación.",
                "<b>Mediano Plazo (4-6 meses):</b> Implementar procesos de calidad y testing automatizado.",
                "<b>Largo Plazo (6-12 meses):</b> Reestructurar arquitectura y establecer mejora continua."
            ]
        
        for action in action_plan:
            elements.append(Paragraph(f"• {action}", styles['SuggestionStyle']))
            elements.append(Spacer(1, 5))
    
    elements.append(Spacer(1, 25))
    
    # ==================== PIE DE PÁGINA ====================
    elements.append(Paragraph("INFORMACIÓN ADICIONAL", styles['SubsectionTitle']))
    elements.append(Spacer(1, 8))
    
    footer_info = [
        "Este reporte ha sido generado automáticamente basándose en los estándares ISO/IEC 25000 para la evaluación de calidad de software.",
        "Para obtener más información sobre las métricas utilizadas o para solicitar una consultoría especializada, contacte a nuestro equipo de expertos.",
        f"Reporte generado el {datetime.now().strftime('%d de %B de %Y a las %H:%M')}."
    ]
    
    for info in footer_info:
        elements.append(Paragraph(info, ParagraphStyle('Footer', fontSize=9, textColor=colors.HexColor('#7F8C8D'), spaceAfter=4)))
    
    # Construir el PDF
    doc.build(elements)
    buffer.seek(0)
    
    return buffer 