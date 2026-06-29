import os
from groq import Groq
from .database import SessionLocal
from .models import Pedido, Cliente, Planta, Cilindro
from sqlalchemy import func
import json
from datetime import datetime, timedelta

# Inicializar el cliente de Groq con tu llave API
# La llave debe estar configurada como variable de entorno GROQ_API_KEY en Render
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def get_estadisticas():
    """Obtiene datos clave de la base de datos para dárselos a la IA."""
    db = SessionLocal()
    try:
        # Pedidos de hoy
        hoy = datetime.now().date()
        pedidos_hoy = db.query(Pedido).filter(func.date(Pedido.fecha_creacion) == hoy).count()
        
        # Totales generales
        total_pedidos = db.query(Pedido).count()
        total_clientes = db.query(Cliente).count()
        total_plantas = db.query(Planta).count()
        
        # Pedidos por estado
        pedidos_pendientes = db.query(Pedido).filter(Pedido.estado == "pendiente").count()
        pedidos_entregados = db.query(Pedido).filter(Pedido.estado == "entregado").count()
        
        # Cilindros en inventario (disponibles)
        cilindros_disponibles = db.query(Cilindro).filter(Cilindro.estado == "disponible").count()
        
        return {
            "pedidos_hoy": pedidos_hoy,
            "total_pedidos": total_pedidos,
            "total_clientes": total_clientes,
            "total_plantas": total_plantas,
            "pedidos_pendientes": pedidos_pendientes,
            "pedidos_entregados": pedidos_entregados,
            "cilindros_disponibles": cilindros_disponibles,
        }
    finally:
        db.close()

def generar_respuesta(pregunta_usuario: str):
    """
    Función principal que recibe una pregunta del administrador,
    consulta a la IA de Groq y devuelve una respuesta en lenguaje natural.
    """
    # 1. Obtener los datos actuales de la base de datos
    datos_sistema = get_estadisticas()
    
    # 2. Crear el mensaje para Groq, dándole contexto y los datos
    mensajes = [
        {
            "role": "system",
            "content": f"""
            Eres el asistente virtual de 'GASGUARIBE', un sistema de gestión de gas doméstico para el municipio Guaribe.
            Tu tarea es ayudar al administrador respondiendo preguntas sobre el negocio.
            Aquí tienes los datos actuales del sistema en formato JSON. Úsalos para responder las preguntas del usuario:
            {json.dumps(datos_sistema, indent=2, default=str)}
            
            Responde siempre en español, de forma clara, amigable y útil.
            Si el usuario pide un reporte, ofrécete a generarlo.
            Si el usuario pregunta algo que no está en los datos, indícalo y sugiere qué puede hacer.
            """
        },
        {
            "role": "user",
            "content": pregunta_usuario
        }
    ]

    try:
        # 3. Preguntar a Groq (usando el modelo gratuito y rápido)
        chat_completion = client.chat.completions.create(
            messages=mensajes,
            model="llama-3.3-70b-versatile",  # Modelo gratuito de Groq
            temperature=0.7,
            max_tokens=1024,
        )
        # 4. Devolver la respuesta de Groq
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Lo siento, tuve un problema al procesar tu solicitud: {e}"
