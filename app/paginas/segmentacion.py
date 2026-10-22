import json

import plotly.express as px
import streamlit as st

import comun

COLORES_BADGE = ["green", "orange", "red", "blue", "violet", "gray", "yellow"]
COLORES_PLOT = ["#2d6e68", "#d98a3d", "#b03a3a", "#4a78b5", "#7b5ea7", "#8a8a8a", "#c9b037"]

seg = comun.cargar_csv("zonas_segmentadas.csv")
grupos = comun.cargar_csv("grupos.csv")
metricas = json.loads((comun.DATA / "metricas.json").read_text(encoding="utf-8"))
nombres = grupos["grupo"].tolist()
color_badge = dict(zip(nombres, COLORES_BADGE))
color_plot = dict(zip(nombres, COLORES_PLOT))
horas_cols = [f"h{h:02d}" for h in range(24)]

st.title("Segmentación de zonas")
st.caption("K-Means agrupa las zonas por cómo se usan los taxis: a qué hora, qué tan lejos, cuánto se paga. "
           "PCA las resume en dos ejes para poder dibujarlas.")

elegidos = st.pills("Grupos", nombres, selection_mode="multi", default=nombres)
if not elegidos:
    st.info("Elige al menos un grupo para ver las zonas.")
    st.stop()
fil = seg[seg["grupo"].isin(elegidos)]

columnas = st.columns(len(elegidos))
for col, nombre in zip(columnas, elegidos):
    fila = grupos[grupos["grupo"] == nombre].iloc[0]
    with col, st.container(border=True):
        st.badge(nombre, color=color_badge[nombre])
        st.metric("Zonas", int(fila["n_zonas"]))
        st.caption(f"{fila['viajes_dia']:,.0f} viajes al día · {fila['dist_mediana']:.1f} millas · "
                   f"{fila['pct_noche']:.0%} de noche")
        with st.popover("¿Qué lo distingue?"):
            st.write(fila["descripcion"])

izq, der = st.columns([3, 2])
with izq:
    fig = px.scatter(fil, x="pc1", y="pc2", color="grupo", size="viajes_dia", size_max=26, custom_data=["zona_id"],
                     hover_name="nombre", hover_data={"distrito": True, "viajes_dia": ":,.0f", "pc1": False, "pc2": False},
                     color_discrete_map=color_plot, labels={"pc1": "Componente 1", "pc2": "Componente 2", "grupo": "Grupo"})
    fig.update_layout(legend=dict(orientation="h", y=-0.2), margin=dict(l=10, r=10, t=10, b=10))
    evento = st.plotly_chart(fig, on_select="rerun", selection_mode=("points", "box", "lasso"), use_container_width=True,
                             key="grafico_pca")
    st.caption("Selecciona zonas en el gráfico (clic, caja o lazo) para compararlas.")

ids = [p["customdata"][0] for p in evento.selection.points] if evento and evento.selection.points else []
detalle = fil[fil["zona_id"].isin(ids)] if ids else fil.nlargest(15, "viajes_dia")

with der:
    perfiles = (detalle if ids else fil.nlargest(5, "viajes_dia")).head(8)
    fig2 = px.line(perfiles.melt(id_vars="nombre", value_vars=horas_cols, var_name="h", value_name="prop")
                   .assign(h=lambda d: d["h"].str[1:].astype(int)),
                   x="h", y="prop", color="nombre", labels={"h": "Hora del día", "prop": "Proporción de viajes", "nombre": ""})
    fig2.update_layout(title="Perfil horario " + ("de las zonas elegidas" if ids else "de las zonas con más viajes"),
                       legend=dict(orientation="h", y=-0.3), margin=dict(l=10, r=10, t=50, b=10))
    st.plotly_chart(fig2, use_container_width=True)
    st.caption("Prueba: selecciona zonas de vida nocturna y compáralas con Midtown. ¿A qué hora llega cada pico?")

st.subheader("Detalle por zona")
tabla = detalle.assign(perfil=detalle[horas_cols].values.tolist())
st.dataframe(
    tabla[["nombre", "distrito", "grupo", "viajes_dia", "dist_mediana", "pct_noche", "propina_mediana", "perfil"]],
    hide_index=True, use_container_width=True,
    column_config={
        "nombre": "Zona", "distrito": "Distrito", "grupo": "Grupo",
        "viajes_dia": st.column_config.NumberColumn("Viajes al día", format="%.0f"),
        "dist_mediana": st.column_config.NumberColumn("Distancia mediana", format="%.1f mi"),
        "pct_noche": st.column_config.ProgressColumn("Viajes de noche", min_value=0, max_value=1, format="percent"),
        "propina_mediana": st.column_config.NumberColumn("Propina mediana", format="$%.2f"),
        "perfil": st.column_config.LineChartColumn("Perfil de 0 a 23 h"),
    },
)

with st.expander(f"¿Por qué {metricas['segmentacion']['k']} grupos?", icon=":material/science:"):
    sil = comun.cargar_csv("silueta.csv")
    k = metricas["segmentacion"]["k"]
    fig3 = px.bar(sil, x="k", y="silueta", labels={"k": "Número de grupos (k)", "silueta": "Coeficiente de silueta"})
    fig3.update_traces(marker_color=["#b03a3a" if v == k else "#2d6e68" for v in sil["k"]])
    st.plotly_chart(fig3, use_container_width=True)
    pca = metricas["segmentacion"]
    st.markdown(f"Se eligió **k = {k}**, el de mayor coeficiente de silueta ({pca['silueta']:.2f}). "
                f"El PCA conserva **{pca['pca_pc1'] + pca['pca_pc2']:.0%}** de la variación en dos componentes "
                f"({pca['pca_pc1']:.0%} + {pca['pca_pc2']:.0%}). "
                "Los grupos se nombran por su perfil, no por el número que les dio K-Means.")
