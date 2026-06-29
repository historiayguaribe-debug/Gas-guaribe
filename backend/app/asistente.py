import os
from groq import Groq
from .database import SessionLocal
from .models import (
    Pedido, Cliente, Planta, Cilindro, DetallePedido, CostoOperativo
)
from sqlalchemy import func, and_
import json
from datetime import datetime, timedelta

# Inicializar el cliente de Groq con la llave API
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def get_estadisticas_completas():
    """
    Recopila TODOS los datos relevantes del negocio para que la IA pueda
    generar reportes y responder preguntas complejas sobre:
    - Pedidos (totales, por día, semana, mes, por estado)
    - Finanzas (ingresos, costos logísticos, administrativos, utilidades)
    - Cilindros (totales, disponibles, por tamaño, ventas por tamaño)
    - Exoneraciones (cantidad de cilindros, valor monetario)
    - Plantas (pedidos por planta, ingresos por planta)
    - Clientes (totales, exonerados)
    - Repartidores (activos)
    - Costos operativos (logísticos, administrativos)
    """
    db = SessionLocal()
    try:
        hoy = datetime.now().date()
        inicio_mes = hoy.replace(day=1)
        semana_pasada = hoy - timedelta(days=7)

        # --- 1. PEDIDOS ---
        total_pedidos = db.query(Pedido).count()
        pedidos_hoy = db.query(Pedido).filter(func.date(Pedido.fecha_creacion) == hoy).count()
        pedidos_mes = db.query(Pedido).filter(func.date(Pedido.fecha_creacion) >= inicio_mes).count()
        pedidos_semana = db.query(Pedido).filter(func.date(Pedido.fecha_creacion) >= semana_pasada).count()
        
        # Por estado
        pendientes = db.query(Pedido).filter(Pedido.estado == "pendiente").count()
        en_ruta = db.query(Pedido).filter(Pedido.estado == "en_ruta").count()
        entregados = db.query(Pedido).filter(Pedido.estado == "entregado").count()
        cancelados = db.query(Pedido).filter(Pedido.estado == "cancelado").count()

        # --- 2. INGRESOS Y COSTOS ---
        pedidos_entregados = db.query(Pedido).filter(Pedido.estado == "entregado").all()
        ingreso_total = sum(float(p.monto_total) for p in pedidos_entregados)
        costo_logistico_total = sum(float(p.costo_logistico) for p in pedidos_entregados)
        costo_admin_total = sum(float(p.costo_administrativo) for p in pedidos_entregados)
        utilidad_bruta = ingreso_total - costo_logistico_total
        utilidad_neta = utilidad_bruta - costo_admin_total

        # --- 3. CILINDROS ---
        total_cilindros = db.query(Cilindro).count()
        disponibles = db.query(Cilindro).filter(Cilindro.estado == "disponible").count()
        en_ruta_cil = db.query(Cilindro).filter(Cilindro.estado == "en_ruta").count()
        vacios = db.query(Cilindro).filter(Cilindro.estado == "vacio").count()
        
        # Por tamaño
        cilindros_por_tamano = {}
        for tam in ["P", "M", "G"]:
            count = db.query(Cilindro).filter(Cilindro.tamanio == tam).count()
            cilindros_por_tamano[tam] = count

        # --- 4. DETALLE DE PEDIDOS (qué se vendió) ---
        detalles = db.query(DetallePedido).all()
        ventas_por_tamano = {"P": 0, "M": 0, "G": 0}
        exonerados_total = 0
        valor_exoneraciones = 0
        for d in detalles:
            if d.cilindro:
                tam = d.cilindro.tamanio.value if hasattr(d.cilindro.tamanio, 'value') else str(d.cilindro.tamanio)
                ventas_por_tamano[tam] = ventas_por_tamano.get(tam, 0) + d.cantidad
                if d.exonerado:
                    exonerados_total += d.cantidad
                    valor_exoneraciones += float(d.precio_unitario) * d.cantidad

        # --- 5. PLANTAS ---
        plantas = db.query(Planta).all()
        datos_plantas = []
        for p in plantas:
            pedidos_planta = db.query(Pedido).filter(Pedido.planta_asignada_id == p.id).count()
            ingresos_planta = sum(
                float(ped.monto_total) for ped in db.query(Pedido).filter(
                    Pedido.planta_asignada_id == p.id, Pedido.estado == "entregado"
                ).all()
            )
            datos_plantas.append({
                "nombre": p.nombre,
                "pedidos": pedidos_planta,
                "ingresos": round(ingresos_planta, 2)
            })

        # --- 6. REPARTIDORES ---
        repartidores_activos = db.query(Pedido.repartidor_id).distinct().count()

        # --- 7. CLIENTES ---
        total_clientes = db.query(Cliente).count()
        clientes_exonerados = db.query(Cliente).filter(Cliente.exonerado == True).count()

        # --- 8. EXONERACIONES (resumen) ---
        exoneraciones_mes = db.query(DetallePedido).filter(
            DetallePedido.exonerado == True,
            DetallePedido.pedido.has(Pedido.fecha_creacion >= inicio_mes)
        ).count()

        # --- 9. COSTOS OPERATIVOS ---
        costos_logisticos = db.query(CostoOperativo).filter(CostoOperativo.tipo == "Logístico").all()
        costos_admin = db.query(CostoOperativo).filter(CostoOperativo.tipo == "Administrativo").all()
        total_logistico = sum(float(c.monto) for c in costos_logisticos)
        total_admin = sum(float(c.monto) for c in costos_admin)

        return {
            "fecha_actual": str(hoy),
            "pedidos": {
                "total": total_pedidos,
                "hoy": pedidos_hoy,
                "esta_semana": pedidos_semana,
                "este_mes": pedidos_mes,
                "pendientes": pendientes,
                "en_ruta": en_ruta,
                "entregados": entregados,
                "cancelados": cancelados,
            },
            "finanzas": {
                "ingreso_total": round(ingreso_total, 2),
                "costo_logistico": round(costo_logistico_total, 2),
                "costo_administrativo": round(costo_admin_total, 2),
                "utilidad_bruta": round(utilidad_bruta, 2),
                "utilidad_neta": round(utilidad_neta, 2),
            },
            "cilindros": {
                "total": total_cilindros,
                "disponibles": disponibles,
                "en_ruta": en_ruta_cil,
                "vacios": vacios,
                "por_tamano": cilindros_por_tamano,
                "ventas_por_tamano": ventas_por_tamano,
            },
            "exoneraciones": {
                "total_cilindros": exonerados_total,
                "valor_monetario": round(valor_exoneraciones, 2),
                "este_mes": exoneraciones_mes,
            },
            "plantas": datos_plantas,
            "clientes": {
                "total": total_clientes,
                "exonerados": clientes_exonerados,
            },
            "repartidores": {
                "activos": repartidores_activos,
            },
            "costos": {
                "logistico": round(total_logistico, 2),
                "administrativo": round(total_admin, 2),
                "detalle": [
                    {"descripcion": c.descripcion, "monto": float(c.monto), "fecha": str(c.fecha)}
                    for c in costos_logisticos + costos_admin
                ]
            }
        }
    finally:
        db.close()

def generar_respuesta(pregunta_usuario: str):
    """
    Función principal que recibe una pregunta del administrador,
    consulta a la IA de Groq y devuelve una respuesta en lenguaje natural.
    """
    # 1. Obtener los datos actuales de la base de datos
    datos = get_estadisticas_completas()
    
    # 2. Crear el mensaje para Groq, dándole contexto y los datos
    mensajes = [
        {
            "role": "system",
            "content": f"""
            Eres el asistente virtual de 'GASGUARIBE', una empresa de distribución de gas doméstico en el municipio Guaribe.
            Tu tarea es ayudar al administrador respondiendo preguntas sobre el negocio.
            Aquí tienes los datos actuales del sistema en formato JSON. Úsalos para responder las preguntas del usuario:
            {json.dumps(datos, indent=2, default=str)}
            
            Instrucciones importantes:
            - Responde siempre en español, de forma clara, amigable y profesional.
            - Si el usuario pide un reporte, ofrécete a generarlo.
            - Si el usuario pregunta algo que no está en los datos, indícalo y sugiere qué puede hacer.
            - Puedes hacer cálculos simples con los datos (ej: "¿cuánto es el ingreso por cilindro grande?").
            - Si el usuario pregunta por tendencias, puedes comparar con períodos anteriores si los datos están disponibles.
            - Sé conciso pero completo en tus respuestas.
            """
        },
        {
            "role": "user",
            "content": pregunta_usuario
        }
    ]

    try:
        chat_completion = client.chat.completions.create(
            messages=mensajes,
            model="llama-3.3-70b-versatile",  # Modelo gratuito de Groq
            temperature=0.5,
            max_tokens=1500,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Lo siento, tuve un problema al procesar tu solicitud: {e}"
