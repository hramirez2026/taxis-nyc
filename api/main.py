import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from fastapi import FastAPI, HTTPException

AQUI = Path(__file__).parent

meta = json.loads((AQUI / "meta.json").read_text())
VARIABLES = meta["variables"]
CUANTILES = meta["cuantiles"]
FECHA_FUTURA = meta["fecha_futura"]

modelo = xgb.XGBRegressor()
modelo.load_model(AQUI / "modelo_pronostico.ubj")

demanda = pd.read_parquet(AQUI / "demanda.parquet")
# Mismas categorías que en el entrenamiento: todas las zonas pronosticables, ordenadas
demanda["zona"] = pd.Categorical(demanda["PULocationID"], categories=sorted(demanda["PULocationID"].unique()))
zonas = pd.read_csv(AQUI / "zonas.csv").set_index("zona_id")

app = FastAPI(title="Taxis NYC · pronóstico de demanda")


def _entero(valor):
    return None if pd.isna(valor) else int(valor)


@app.get("/")
def raiz():
    return {"estado": "en línea", "servicio": "Taxis NYC"}


@app.get("/info")
def info():
    fechas = sorted(demanda["hora"].dt.date.astype(str).unique())
    lista = [
        {"id": int(i), "nombre": fila["nombre"], "distrito": fila["distrito"]}
        for i, fila in zonas.sort_values("nombre").iterrows()
    ]
    return {"zonas": lista, "fechas": fechas, "fecha_futura": FECHA_FUTURA, "cuantiles": CUANTILES}


@app.get("/pronostico")
def pronostico(zona_id: int, fecha: date):
    filas = demanda[(demanda["PULocationID"] == zona_id) & (demanda["hora"].dt.date == fecha)].sort_values("hora")
    if filas.empty:
        raise HTTPException(status_code=404, detail="No hay datos para esa zona o fecha")

    cuantiles = np.sort(np.maximum(modelo.predict(filas[VARIABLES]), 0), axis=1)
    zona = zonas.loc[zona_id]
    horas = []
    for (_, fila), q in zip(filas.iterrows(), cuantiles):
        horas.append({
            "hora": int(fila["hora_dia"]),
            "real": _entero(fila["viajes"]),
            "hace_una_semana": _entero(fila["lag_168"]),
            "cuantiles": {nombre: round(float(valor), 1) for nombre, valor in zip(CUANTILES, q)},
        })
    return {
        "zona": {"id": zona_id, "nombre": zona["nombre"], "distrito": zona["distrito"]},
        "fecha": fecha.isoformat(),
        "horas": horas,
    }
