"""Funciones compartidas por las páginas: conexión con la API, selector de zona y fecha."""
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

DATA = Path(__file__).parent / "data"
DIAS = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]


def api_url():
    try:
        url = st.secrets["API_URL"]
    except Exception:
        url = "http://localhost:8000"
    return url.rstrip("/")


@st.cache_data(ttl=3600, show_spinner=False)
def _get(url, params=None):
    respuesta = requests.get(url, params=params, timeout=90)  # Render tarda ~1 min en despertar
    respuesta.raise_for_status()
    return respuesta.json()


def _estado_api(ok):
    with st.sidebar:
        if ok:
            st.badge("API en línea", icon=":material/cloud_done:", color="green")
        else:
            st.badge("API sin respuesta", icon=":material/cloud_off:", color="red")


def conectar_api():
    """Devuelve /info; si la API no responde, lo explica y detiene la página."""
    error = None
    with st.status("Conectando con la API...", expanded=False) as estado:
        try:
            info = _get(api_url() + "/info")
            estado.update(label="API conectada", state="complete")
        except requests.RequestException as e:
            error = e
            estado.update(label="Sin conexión con la API", state="error")
    if error is not None:
        _estado_api(False)
        st.error(
            f"No se pudo conectar con la API en {api_url()}. Si está en Render, puede estar despertando: "
            "espera un minuto y recarga. Revisa también que API_URL no termine en «/».",
            icon=":material/cloud_off:",
        )
        st.caption(f"Detalle técnico: {type(error).__name__}")
        st.stop()
    _estado_api(True)
    return info


def llamar(ruta, **params):
    try:
        return _get(api_url() + ruta, params or None)
    except requests.RequestException as e:
        st.error(f"La API no pudo responder a {ruta}: {e}", icon=":material/error:")
        st.stop()


def etiqueta_fecha(fecha, futura):
    d = pd.Timestamp(fecha)
    texto = f"{DIAS[d.dayofweek]} {d.day}"
    return texto + " (mañana)" if fecha == futura else texto


def selector(info):
    """Zona y fecha; recuerdan la elección entre páginas (session_state) y en el link (query_params)."""
    zonas = {z["id"]: f'{z["nombre"]} ({z["distrito"]})' for z in info["zonas"]}
    ids = list(zonas)
    fechas, futura = info["fechas"], info["fecha_futura"]
    qp = st.query_params

    if "zona_sel" not in st.session_state:
        z = qp.get("zona", "")
        st.session_state["zona_sel"] = int(z) if z.isdigit() and int(z) in zonas else (161 if 161 in zonas else ids[0])
    if "fecha_sel" not in st.session_state:
        f = qp.get("fecha")
        st.session_state["fecha_sel"] = f if f in fechas else fechas[-2] if len(fechas) > 1 else fechas[0]

    zona = st.selectbox("Zona", ids, index=ids.index(st.session_state["zona_sel"]), format_func=zonas.get)
    fecha = st.segmented_control("Fecha", fechas, default=st.session_state["fecha_sel"],
                                 format_func=lambda f: etiqueta_fecha(f, futura))
    fecha = fecha or st.session_state["fecha_sel"]  # si desmarcan el botón, se conserva la anterior

    st.session_state["zona_sel"], st.session_state["fecha_sel"] = zona, fecha
    st.query_params["zona"], st.query_params["fecha"] = str(zona), fecha
    return zona, fecha


def a_dataframe(datos):
    filas = [{"hora": h["hora"], "real": h["real"], "semana": h["hace_una_semana"], **h["cuantiles"]}
             for h in datos["horas"]]
    return pd.DataFrame(filas).set_index("hora", drop=False)


def cargar_csv(nombre):
    return pd.read_csv(DATA / nombre)
