"""
Bot de trading conservador - Binance
Estrategia: RSI (compra < 35, vende > 65)
"""

import time
import os
from binance.client import Client
from binance.exceptions import BinanceAPIException

def cargar_env():
    try:
        with open(".env") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()
        print("Variables cargadas desde .env")
    except FileNotFoundError:
        print("No se encontro .env, usando variables del sistema")

cargar_env()

API_KEY    = os.getenv("BINANCE_API_KEY", "").strip()
API_SECRET = os.getenv("BINANCE_SECRET_KEY", "").strip()

PAR        = "BTCUSDT"
INTERVALO  = 60
RSI_COMPRA = 35
RSI_VENTA  = 65
PORCENTAJE = 0.40


def conectar():
    if not API_KEY or not API_SECRET:
        print("ERROR: Faltan las claves API")
        print(f"API_KEY presente: {'SI' if API_KEY else 'NO'}")
        print(f"API_SECRET presente: {'SI' if API_SECRET else 'NO'}")
        raise ValueError("Faltan claves API de Binance")
    print(f"API_KEY (primeros 6): {API_KEY[:6]}...")
    print(f"API_SECRET (primeros 6): {API_SECRET[:6]}...")
    client = Client(API_KEY, API_SECRET)
    client.ping()
    print("Conectado a Binance correctamente")
    return client


def obtener_precios(client, par, limite=14):
    velas = client.get_klines(symbol=par, interval=Client.KLINE_INTERVAL_1MINUTE, limit=limite + 1)
    return [float(v[4]) for v in velas]


def calcular_rsi(precios):
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
    info = client.get_asset_balance(asset=moneda)
    return float(info["free"]) if info else 0.0


def obtener_precio_actual(client, par):
    ticker = client.get_symbol_ticker(symbol=par)
    return float(ticker["price"])


def ejecutar_compra(client, par, usdt_disponible):
    precio = obtener_precio_actual(client, par)
    monto_usdt = round(usdt_disponible * PORCENTAJE, 2)
    if monto_usdt < 10:
        print(f"Fondos insuficientes (minimo $10 USDT, tienes ${monto_usdt:.2f})")
        return False
    cantidad = round(monto_usdt / precio, 6)
    try:
        client.order_market_buy(symbol=par, quantity=cantidad)
        print(f"COMPRA ejecutada | {cantidad} BTC a ${precio:,.2f} | Total: ${monto_usdt:.2f}")
        return True
    except BinanceAPIException as e:
        print(f"Error en compra: {e.message}")
        return False


def ejecutar_venta(client, par, btc_disponible):
    precio = obtener_precio_actual(client, par)
    cantidad = round(btc_disponible * 0.50, 6)
    valor_usdt = cantidad * precio
    if valor_usdt < 10:
        print(f"Monto muy pequeno (${valor_usdt:.2f}), saltando venta.")
        return False
    try:
        client.order_market_sell(symbol=par, quantity=cantidad)
        print(f"VENTA ejecutada | {cantidad} BTC a ${precio:,.2f} | Recuperado: ${valor_usdt:.2f}")
        return True
    except BinanceAPIException as e:
        print(f"Error en venta: {e.message}")
        return False


def ejecutar_bot():
    print("Bot de trading conservador iniciado")
    print(f"Par: {PAR} | RSI compra <{RSI_COMPRA} | RSI venta >{RSI_VENTA}")

    client = conectar()
    ultima_accion = None

    while True:
        try:
            precios = obtener_precios(client, PAR)
            rsi     = calcular_rsi(precios)
            precio  = precios[-1]
            usdt    = obtener_balance(client, "USDT")
            btc     = obtener_balance(client, "BTC")

            print(f"Precio: ${precio:,.2f} | RSI: {rsi} | USDT: ${usdt:.2f} | BTC: {btc:.6f}")

            if rsi < RSI_COMPRA and usdt >= 10 and ultima_accion != "compra":
                print(f"RSI={rsi} sobrevendido, comprando...")
                if ejecutar_compra(client, PAR, usdt):
                    ultima_accion = "compra"

            elif rsi > RSI_VENTA and btc > 0 and ultima_accion != "venta":
                print(f"RSI={rsi} sobrecomprado, vendiendo...")
                if ejecutar_venta(client, PAR, btc):
                    ultima_accion = "venta"

            else:
                print(f"Esperando senal... (ultima accion: {ultima_accion or 'ninguna'})")

        except BinanceAPIException as e:
            print(f"Error de Binance: {e.message}")
        except Exception as e:
            print(f"Error inesperado: {e}")

        time.sleep(INTERVALO)


if __name__ == "__main__":
    ejecutar_bot()
