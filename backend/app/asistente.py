import os
import json
from datetime import datetime
from groq import Groq
from sqlalchemy import func
from .database import SessionLocal
from .models import Pedido, Cliente, Planta, Cilindro

# Inicializar el cliente de Groq con la llave desde variables de entorno
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("La variable de entorno GROQ_API_KEY no está configurada")

client = Groq(api_key=GROQ_API_KEY)

def get_estadisticas():
    """
    Obtiene datos actuales de la base de datos para dárselos a la IA.
    """
    db = SessionLocal()
    try:
        hoy = datetime.now().date()
        pedidos_hoy = db.query(Pedido).filter(func.date(Pedido.fecha_creacion) == hoy).count()
        total_pedidos = db.query(Pedido).count()
        total_clientes = db.query(Cliente).count()
        total_plantas = db.query(Planta).count()
        pedidos_pendientes = db.query(Pedido).filter(Pedido.estado == "pendiente").count()
        pedidos_entregados = db.query(Pedido).filter(Pedido.estado == "entregado").count()
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

def generar_respuesta(pregunta_usuario: str) -> str:
    """
    Toma una pregunta del usuario, consulta a Groq con los datos del sistema,
    y devuelve la respuesta en lenguaje natural.
    """
    # 1. Obtener los datos actuales
    datos = get_estadisticas()

    # 2. Construir el mensaje para el sistema (el prompt)
    mensaje_sistema = f"""
    Eres el asistente virtual de 'GASGUARIBE', un sistema de gestión de gas doméstico para el municipio Guaribe.
    Ayudas al administrador respondiendo preguntas sobre el negocio.
    Aquí tienes los datos actuales del sistema en formato JSON. Úsalos para responder las preguntas del usuario:
    {json.dumps(datos, indent=2, default=str)}

    Responde siempre en español, de forma clara, amigable y útil.
    Si el usuario pide un reporte, ofrécete a generarlo.
    Si la pregunta no está relacionada con los datos, indícalo y sugiere qué puede hacer.
    """

    mensajes = [
        {"role": "system", "content": mensaje_sistema},
        {"role": "user", "content": pregunta_usuario}
    ]

    try:
        respuesta = client.chat.completions.create(
            messages=mensajes,
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=1024,
        )
        return respuesta.choices[0].message.content
    except Exception as e:
        # Captura errores de red, autenticación, etc.
        return f"Lo siento, ocurrió un error al consultar la IA: {str(e)}"
