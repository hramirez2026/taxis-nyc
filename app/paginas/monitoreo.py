import json

import plotly.graph_objects as go
import streamlit as st

import comun

m = json.loads((comun.DATA / "metricas.json").read_text(encoding="utf-8"))
dias = comun.cargar_csv("metricas_diarias.csv")

st.title("Monitoreo del modelo")
st.caption("Error día a día de la semana de prueba. Si un día supera el límite, el modelo debería revisarse.")

limite = st.slider("Límite de error (viajes por hora)", 1.0, float(max(2 * m["mae_modelo"], dias["mae_modelo"].max() * 1.2)),
                   float(m["umbral_error"]), 0.5,
                   help=f"Sugerido: 125 % del error promedio de la semana ({m['mae_modelo']:.1f}).")

fig = go.Figure()
fig.add_bar(x=dias["fecha"], y=dias["mae_modelo"], name="Modelo",
            marker_color=["#b03a3a" if v > limite else "#2d6e68" for v in dias["mae_modelo"]])
fig.add_trace(go.Scatter(x=dias["fecha"], y=dias["mae_semana"], mode="lines+markers", name="Igual que hace una semana",
                         line=dict(color="#7a7a7a", dash="dot")))
fig.add_hline(y=limite, line_dash="dash", line_color="#d98a3d", annotation_text="límite")
fig.update_layout(yaxis_title="Error promedio (viajes/hora)", legend=dict(orientation="h", y=-0.2),
                  margin=dict(l=10, r=10, t=10, b=10))
st.plotly_chart(fig, use_container_width=True)

fuera = dias[dias["mae_modelo"] > limite]
if fuera.empty:
    st.success("Todos los días están dentro del límite.", icon=":material/check_circle:")
else:
    st.error("Días por encima del límite: " + ", ".join(f"{f} ({v:.1f})" for f, v in zip(fuera["fecha"], fuera["mae_modelo"])),
             icon=":material/notification_important:")

st.dataframe(dias, hide_index=True, use_container_width=True, column_config={
    "fecha": "Fecha",
    "mae_modelo": st.column_config.NumberColumn("Error del modelo", format="%.1f"),
    "mae_semana": st.column_config.NumberColumn("Error «hace una semana»", format="%.1f"),
    "cobertura": st.column_config.ProgressColumn("Cobertura 10–90 %", min_value=0, max_value=1, format="percent"),
    "viajes_real": st.column_config.NumberColumn("Viajes reales", format="%d"),
})
