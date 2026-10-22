import json

import pandas as pd
import plotly.express as px
import streamlit as st

import comun

m = json.loads((comun.DATA / "metricas.json").read_text(encoding="utf-8"))

st.title("Ficha del modelo")
st.caption("Qué hace el modelo, qué tan bien lo hace y en qué no se debe confiar. Una ficha (model card) es un "
           "documento estándar para que cualquier persona entienda un modelo antes de usarlo.")

with st.container(border=True):
    st.subheader(":material/target: Para qué sirve")
    st.markdown(f"Pronostica cuántos viajes en taxi amarillo empezarán **cada hora** en {m['n_zonas_pronostico']} zonas de "
                "Nueva York, con un rango de incertidumbre (cuantiles del 10 % al 90 %). Está pensado para "
                "**planificar la flota** con un día de anticipación.")
    st.badge("XGBoost con 9 cuantiles", color="blue")
    st.badge(f"Datos: NYC TLC, enero 2024 ({m['n_viajes_enero']:,} viajes)", color="gray")
    st.badge(f"Horizonte: {m['horizonte_horas']} horas", color="green")

st.subheader(":material/analytics: Qué tan bien funciona")
st.caption(f"Evaluado en la última semana de enero ({m['n_horas_zona_prueba']:,} horas-zona que el modelo nunca vio). "
           f"Entrenado hasta el {m['entrenamiento_hasta']}.")
c1, c2, c3 = st.columns(3)
c1.metric("Error del modelo", f"{m['mae_modelo']:.1f} viajes/hora", border=True, delta_color="inverse",
          delta=f"{-m['mejora_vs_semana_pct']:+.0f}% vs. «igual que hace una semana»")
c2.metric("Cobertura del rango 10 %–90 %", f"{m['cobertura_80']:.0%}", border=True, delta="objetivo: 80 %", delta_color="off")
c3.metric("Zonas agrupadas", m["n_zonas_segmentadas"], border=True, delta=f"{m['n_grupos']} grupos (K-Means)", delta_color="off")

izq, der = st.columns(2)
with izq:
    reglas = pd.DataFrame({"Regla": ["Modelo (mediana)", "Igual que hace una semana", "Igual que ayer"],
                           "Error": [m["mae_modelo"], m["mae_semana"], m["mae_ayer"]]})
    fig = px.bar(reglas, x="Error", y="Regla", orientation="h", title="Error frente a reglas simples",
                 labels={"Error": "Viajes por hora"})
    fig.update_traces(marker_color="#2d6e68")
    st.plotly_chart(fig, use_container_width=True)
    gana = m["mae_modelo"] < m["mae_semana"]
    st.caption(f"El modelo {'le gana' if gana else 'NO le gana'} a «igual que hace una semana» "
               f"{'por poco' if gana and m['mejora_vs_semana_pct'] < 10 else ''}. "
               "Su valor principal está en el **rango**, que las reglas simples no dan.")
with der:
    g = pd.DataFrame(m["error_por_grupo"]).sort_values("mae")
    fig = px.bar(g, x="mae", y="grupo", orientation="h", title="Error según el tipo de zona",
                 labels={"mae": "Viajes por hora", "grupo": ""})
    fig.update_traces(marker_color="#d98a3d")
    st.plotly_chart(fig, use_container_width=True)
    peor = g.iloc[-1]
    st.caption(f"El error es mayor en «{peor['grupo']}» ({peor['mae']:.1f} viajes/hora): "
               "dependen de factores que el modelo no ve, como vuelos, retrasos o eventos.")

with st.container(border=True):
    st.subheader(":material/warning: Limitaciones")
    st.markdown(
        "- Entrenado con **un solo mes de invierno**: no conoce el verano, las vacaciones ni eventos como un maratón.\n"
        "- Solo usa la historia de la propia demanda y el calendario: **no sabe de clima, conciertos ni cierres de calles**.\n"
        f"- Las {m['n_zonas_sin_pronostico']} zonas con menos de 3,000 viajes al mes no tienen pronóstico "
        f"({m['pct_sin_pronostico_fuera_manhattan']:.0%} están fuera de Manhattan).\n"
        f"- El rango del 80 % acierta {m['cobertura_80']:.0%} en promedio, pero varía por zona: "
        f"de {m['cobertura_min_zona']:.0%} a {m['cobertura_max_zona']:.0%}."
    )

with st.container(border=True):
    st.subheader(":material/block: Usos no recomendados")
    st.markdown(
        "- Decidir **qué conductores trabajan** o evaluar su desempeño con este pronóstico.\n"
        "- **Recortar el servicio** en zonas periféricas porque «el modelo predice poca demanda»: en esos barrios se usan "
        "más los taxis verdes y las apps, que no están en estos datos. Poca demanda de taxi amarillo no significa poca "
        "necesidad de transporte.\n"
        "- Usarlo más de un día hacia adelante: está entrenado para el día siguiente."
    )

st.divider()
st.markdown("**¿Te resultó clara esta ficha?**")
estrellas = st.feedback("stars")
if estrellas is not None:
    st.toast(f"¡Gracias por tu opinión! ({estrellas + 1}/5)", icon=":material/favorite:")
