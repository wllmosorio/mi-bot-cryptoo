"""
Bot de trading conservador - Binance
Estrategia: RSI (compra < 35, vende > 65)
Capital inicial sugerido: $10 USD mínimo
"""
"""
Bot de trading conservador - Binance
Estrategia: RSI (compra < 35, vende > 65)
Capital inicial sugerido: $10 USD mínimo
"""

import time
import os
from binance.client import Client
from binance.exceptions import BinanceAPIException

# ── Configuración ──────────────────────────────────────────
API_KEY    = os.getenv("BINANCE_API_KEY", "").strip()
API_SECRET = os.getenv("BINANCE_SECRET_KEY", "").strip()

PAR        = "BTCUSDT"       # Par a operar (cambia a ETHUSDT si prefieres)
INTERVALO  = 60              # Segundos entre cada revisión del mercado
RSI_COMPRA = 35              # Compra cuando RSI baja de este valor
RSI_VENTA  = 65              # Vende cuando RSI sube de este valor
PORCENTAJE = 0.40            # Usa el 40% del capital disponible por operación
# ──────────────────────────────────────────────────────────


def conectar():
    client = Client(API_KEY, API_SECRET)
    print("✅ Conectado a Binance correctamente")
    return client


def obtener_precios(client, par, limite=14):
    """Obtiene los últimos N precios de cierre."""
    velas = client.get_klines(symbol=par, interval=Client.KLINE_INTERVAL_1MINUTE, limit=limite + 1)
    return [float(v[4]) for v in velas]


def calcular_rsi(precios):
    """Calcula el RSI de 14 periodos."""
    if len(precios) < 2:
        return 50
    cambios = [precios[i] - precios[i - 1] for i in range(1, len(precios))]
    ganancias = [c for c in cambios if c > 0]
    perdidas  = [-c for c in cambios if c < 0]
    avg_ganancia = sum(ganancias) / len(precios) if ganancias else 0
    avg_perdida  = sum(perdidas)  / len(precios) if perdidas  else 0
    if avg_perdida == 0:
        return 100
    rs = avg_ganancia / avg_perdida
    return round(100 - (100 / (1 + rs)), 2)


def obtener_balance(client, moneda="USDT"):
    """Obtiene el balance disponible de una moneda."""
    info = client.get_asset_balance(asset=moneda)
    return float(info["free"]) if info else 0.0


def obtener_precio_actual(client, par):
    """Obtiene el precio actual del par."""
    ticker = client.get_symbol_ticker(symbol=par)
    return float(ticker["price"])


def ejecutar_compra(client, par, usdt_disponible):
    """Ejecuta una orden de compra de mercado."""
    precio = obtener_precio_actual(client, par)
    monto_usdt = round(usdt_disponible * PORCENTAJE, 2)
    if monto_usdt < 10:
        print(f"⚠️  Fondos insuficientes para operar (mínimo $10 USDT, tienes ${monto_usdt:.2f})")
        return False
    cantidad = round(monto_usdt / precio, 6)
    try:
        orden = client.order_market_buy(symbol=par, quantity=cantidad)
        print(f"🟢 COMPRA ejecutada | {cantidad} BTC a ~${precio:,.2f} USDT | Total: ${monto_usdt:.2f}")
        return True
    except BinanceAPIException as e:
        print(f"❌ Error en compra: {e.message}")
        return False


def ejecutar_venta(client, par, btc_disponible):
    """Ejecuta una orden de venta de mercado."""
    precio = obtener_precio_actual(client, par)
    cantidad = round(btc_disponible * 0.50, 6)   # Vende el 50% del BTC que tienes
    valor_usdt = cantidad * precio
    if valor_usdt < 10:
        print(f"⚠️  Monto a vender muy pequeño (${valor_usdt:.2f}), saltando venta.")
        return False
    try:
        orden = client.order_market_sell(symbol=par, quantity=cantidad)
        print(f"🔴 VENTA ejecutada | {cantidad} BTC a ~${precio:,.2f} USDT | Recuperado: ${valor_usdt:.2f}")
        return True
    except BinanceAPIException as e:
        print(f"❌ Error en venta: {e.message}")
        return False


def ejecutar_bot():
    print("🤖 Bot de trading conservador iniciado")
    print(f"   Par: {PAR} | RSI compra <{RSI_COMPRA} | RSI venta >{RSI_VENTA}")
    print("─" * 50)

    client = conectar()
    ultima_accion = None

    while True:
        try:
            precios = obtener_precios(client, PAR)
            rsi     = calcular_rsi(precios)
            precio  = precios[-1]
            usdt    = obtener_balance(client, "USDT")
            btc     = obtener_balance(client, "BTC")

            print(f"📊 Precio: ${precio:,.2f} | RSI: {rsi} | USDT libre: ${usdt:.2f} | BTC: {btc:.6f}")

            if rsi < RSI_COMPRA and usdt >= 10 and ultima_accion != "compra":
                print(f"📉 RSI={rsi} → mercado sobrevendido → comprando...")
                if ejecutar_compra(client, PAR, usdt):
                    ultima_accion = "compra"

            elif rsi > RSI_VENTA and btc > 0 and ultima_accion != "venta":
                print(f"📈 RSI={rsi} → mercado sobrecomprado → vendiendo...")
                if ejecutar_venta(client, PAR, btc):
                    ultima_accion = "venta"

            else:
                print(f"⏸️  Esperando señal clara... (última acción: {ultima_accion or 'ninguna'})")

        except BinanceAPIException as e:
            print(f"❌ Error de Binance: {e.message}")
        except Exception as e:
            print(f"❌ Error inesperado: {e}")

        time.sleep(INTERVALO)


if __name__ == "__main__":
    ejecutar_bot()

import time
import os
from binance.client import Client
from binance.exceptions import BinanceAPIException

# ── Configuración ──────────────────────────────────────────
API_KEY    = os.environ.get("BINANCE_API_KEY")
API_SECRET = os.environ.get("BINANCE_SECRET_KEY")

PAR        = "BTCUSDT"       # Par a operar (cambia a ETHUSDT si prefieres)
INTERVALO  = 60              # Segundos entre cada revisión del mercado
RSI_COMPRA = 35              # Compra cuando RSI baja de este valor
RSI_VENTA  = 65              # Vende cuando RSI sube de este valor
PORCENTAJE = 0.40            # Usa el 40% del capital disponible por operación
# ──────────────────────────────────────────────────────────


def conectar():
    client = Client(API_KEY, API_SECRET)
    print("✅ Conectado a Binance correctamente")
    return client


def obtener_precios(client, par, limite=14):
    """Obtiene los últimos N precios de cierre."""
    velas = client.get_klines(symbol=par, interval=Client.KLINE_INTERVAL_1MINUTE, limit=limite + 1)
    return [float(v[4]) for v in velas]


def calcular_rsi(precios):
    """Calcula el RSI de 14 periodos."""
    if len(precios) < 2:
        return 50
    cambios = [precios[i] - precios[i - 1] for i in range(1, len(precios))]
    ganancias = [c for c in cambios if c > 0]
    perdidas  = [-c for c in cambios if c < 0]
    avg_ganancia = sum(ganancias) / len(precios) if ganancias else 0
    avg_perdida  = sum(perdidas)  / len(precios) if perdidas  else 0
    if avg_perdida == 0:
        return 100
    rs = avg_ganancia / avg_perdida
    return round(100 - (100 / (1 + rs)), 2)


def obtener_balance(client, moneda="USDT"):
    """Obtiene el balance disponible de una moneda."""
    info = client.get_asset_balance(asset=moneda)
    return float(info["free"]) if info else 0.0


def obtener_precio_actual(client, par):
    """Obtiene el precio actual del par."""
    ticker = client.get_symbol_ticker(symbol=par)
    return float(ticker["price"])


def ejecutar_compra(client, par, usdt_disponible):
    """Ejecuta una orden de compra de mercado."""
    precio = obtener_precio_actual(client, par)
    monto_usdt = round(usdt_disponible * PORCENTAJE, 2)
    if monto_usdt < 10:
        print(f"⚠️  Fondos insuficientes para operar (mínimo $10 USDT, tienes ${monto_usdt:.2f})")
        return False
    cantidad = round(monto_usdt / precio, 6)
    try:
        orden = client.order_market_buy(symbol=par, quantity=cantidad)
        print(f"🟢 COMPRA ejecutada | {cantidad} BTC a ~${precio:,.2f} USDT | Total: ${monto_usdt:.2f}")
        return True
    except BinanceAPIException as e:
        print(f"❌ Error en compra: {e.message}")
        return False


def ejecutar_venta(client, par, btc_disponible):
    """Ejecuta una orden de venta de mercado."""
    precio = obtener_precio_actual(client, par)
    cantidad = round(btc_disponible * 0.50, 6)   # Vende el 50% del BTC que tienes
    valor_usdt = cantidad * precio
    if valor_usdt < 10:
        print(f"⚠️  Monto a vender muy pequeño (${valor_usdt:.2f}), saltando venta.")
        return False
    try:
        orden = client.order_market_sell(symbol=par, quantity=cantidad)
        print(f"🔴 VENTA ejecutada | {cantidad} BTC a ~${precio:,.2f} USDT | Recuperado: ${valor_usdt:.2f}")
        return True
    except BinanceAPIException as e:
        print(f"❌ Error en venta: {e.message}")
        return False


def ejecutar_bot():
    print("🤖 Bot de trading conservador iniciado")
    print(f"   Par: {PAR} | RSI compra <{RSI_COMPRA} | RSI venta >{RSI_VENTA}")
    print("─" * 50)

    client = conectar()
    ultima_accion = None

    while True:
        try:
            precios = obtener_precios(client, PAR)
            rsi     = calcular_rsi(precios)
            precio  = precios[-1]
            usdt    = obtener_balance(client, "USDT")
            btc     = obtener_balance(client, "BTC")

            print(f"📊 Precio: ${precio:,.2f} | RSI: {rsi} | USDT libre: ${usdt:.2f} | BTC: {btc:.6f}")

            if rsi < RSI_COMPRA and usdt >= 10 and ultima_accion != "compra":
                print(f"📉 RSI={rsi} → mercado sobrevendido → comprando...")
                if ejecutar_compra(client, PAR, usdt):
                    ultima_accion = "compra"

            elif rsi > RSI_VENTA and btc > 0 and ultima_accion != "venta":
                print(f"📈 RSI={rsi} → mercado sobrecomprado → vendiendo...")
                if ejecutar_venta(client, PAR, btc):
                    ultima_accion = "venta"

            else:
                print(f"⏸️  Esperando señal clara... (última acción: {ultima_accion or 'ninguna'})")

        except BinanceAPIException as e:
            print(f"❌ Error de Binance: {e.message}")
        except Exception as e:
            print(f"❌ Error inesperado: {e}")

        time.sleep(INTERVALO)


if __name__ == "__main__":
    ejecutar_bot()
