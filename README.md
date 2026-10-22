# Taxis NYC: una app para quien toma decisiones

Pronóstico de demanda con incertidumbre, segmentación de zonas y recomendación de cuántos taxis enviar
(AIMLF1 · Módulo 2).

- **Integrantes:** _(completar)_
- **App (Streamlit Cloud):** _(completar)_
- **API (Render):** _(completar)_ — documentación en `/docs`
- **Repositorio:** _(completar)_

## Estructura

```
preparacion.ipynb   datos, modelos y métricas (genera todo lo de api/ y app/data/)
api/                FastAPI: main.py, modelo_pronostico.ubj, demanda.parquet, zonas.csv, meta.json
app/                Streamlit: streamlit_app.py, paginas/, data/, comun.py
```

## Cómo correrlo

1. Ejecutar `preparacion.ipynb` de arriba abajo (descarga ~50 MB de la NYC TLC). Genera el modelo, `demanda.parquet`
   y los CSV/JSON de `app/data/`.
2. API: `cd api && pip install -r requirements.txt && uvicorn main:app --reload` → http://localhost:8000/docs
3. App: `cd app && pip install -r requirements.txt && streamlit run streamlit_app.py`
   (por defecto usa `http://localhost:8000`; en Streamlit Cloud definir el secret `API_URL = "https://su-api.onrender.com"`, sin «/» final).

## Publicación

- **Render:** Root Directory `api`, Build `pip install -r requirements.txt`, Start `uvicorn main:app --host 0.0.0.0 --port $PORT`.
- **Streamlit Cloud:** Main file `app/streamlit_app.py` y secret `API_URL`.

## Decisiones de diseño

- Sin lags menores a 24 h (evita fuga de datos: el pronóstico se hace el día anterior).
- Un único modelo XGBoost (`reg:quantileerror`) con 9 cuantiles; se ordenan por fila para evitar cuantiles cruzados.
- Los nombres de los grupos de zonas se asignan por su perfil, no por el número de K-Means.
- Página extra de **Monitoreo** (+10): error diario de la semana de prueba con límite configurable.
