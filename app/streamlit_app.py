import streamlit as st

st.set_page_config(page_title="Taxis NYC", page_icon=":material/local_taxi:", layout="wide")

paginas = {
    "Planificar": [
        st.Page("paginas/pronostico.py", title="Pronóstico", icon=":material/insights:", default=True),
        st.Page("paginas/decision.py", title="Decisión", icon=":material/tune:"),
    ],
    "Entender": [
        st.Page("paginas/segmentacion.py", title="Segmentación de zonas", icon=":material/hub:"),
        st.Page("paginas/ficha.py", title="Ficha del modelo", icon=":material/description:"),
    ],
    "Vigilar": [
        st.Page("paginas/monitoreo.py", title="Monitoreo", icon=":material/monitor_heart:"),
    ],
}
pagina = st.navigation(paginas)

with st.sidebar:
    st.divider()
    st.markdown("**Taxis NYC**")
    st.caption("Demanda de taxis amarillos, enero de 2024 (NYC TLC).")

pagina.run()
