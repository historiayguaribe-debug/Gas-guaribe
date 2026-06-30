import random
import string

def generar_codigo_qr():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def calcular_utilidad(ventas, cargas, gastos):
    ingresos = sum(v.cantidad * v.precio_unitario for v in ventas)
    costo_compras = sum(c.costo_total for c in cargas)
    gastos_total = sum(g.monto for g in gastos)
    return ingresos - costo_compras - gastos_total
