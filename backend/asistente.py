import os
from groq import Groq
from .database import SessionLocal
from .models import Pedido, Cliente, Planta, Cilindro
from sqlalchemy import func
import json
from datetime import datetime, timedelta

# Inicializar el cliente de Groq con tu llave API
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def get_estadisticas():
    """Obtiene datos clave de la base de datos para dárselos a la IA."""
    db = SessionLocal()
    # Pedidos de hoy
    hoy = datetime.now().date()
    pedidos_hoy = db.query(Pedido).filter(func.date(Pedido.fecha_creacion) == hoy).count()
    
    # Totales generales
    total_pedidos = db.query(Pedido).count()
    total_clientes = db.query(Cliente).count()
    total_plantas = db.query(Planta).count()
    
    db.close()
    
    # Devolver la información en un formato que la IA pueda entender fácilmente
    return {
        "pedidos_hoy": pedidos_hoy,
        "total_pedidos": total_pedidos,
        "total_clientes": total_clientes,
        "total_plantas": total_plantas,
    }

def generar_respuesta(pregunta_usuario: str):
    """
    Función principal que recibe una pregunta y devuelve la respuesta del asistente.
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
            {json.dumps(datos_sistema)}
            
            Responde siempre en español, de forma clara, amigable y útil.
            Si el usuario pide un reporte, ofrécete a generarlo.
            """
        },
        {
            "role": "user",
            "content": pregunta_usuario
        }
    ]

    try:
        # 3. Preguntar a Groq
        chat_completion = client.chat.completions.create(
            messages=mensajes,
            model="llama-3.3-70b-versatile", # El modelo gratuito y rápido de Groq
        )
        # 4. Devolver la respuesta de Groq
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Lo siento, tuve un problema al procesar tu solicitud: {e}"
