import plotly.graph_objects as go
import streamlit as st

import comun


@st.dialog("¿Cómo leer este pronóstico?")
def ayuda():
    st.markdown(
        "- La **línea** es el pronóstico central (mediana): la mitad de las veces la demanda real queda arriba y la mitad abajo.\n"
        "- La **banda** va del cuantil 10 % al 90 %: en 8 de cada 10 horas, la demanda real cae dentro.\n"
        "- Los **puntos** son los viajes que de verdad ocurrieron (no existen para mañana).\n"
        "- Una banda ancha no es un error del modelo: es una hora **difícil de predecir**, y conviene saberlo."
    )


izq, der = st.columns([5, 1], vertical_alignment="bottom")
izq.title("Pronóstico de demanda")
if der.button("Cómo leerlo", icon=":material/help:"):
    ayuda()
st.caption("Viajes por hora que se esperan en una zona, con su rango de incertidumbre. El modelo vive en la API.")

info = comun.conectar_api()
zona_id, fecha = comun.selector(info)
futura = fecha == info["fecha_futura"]

datos = comun.llamar("/pronostico", zona_id=zona_id, fecha=fecha)
df = comun.a_dataframe(datos)
tiene_real = df["real"].notna().all()

total, semana = df["p50"].sum(), df["semana"].sum()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Viajes esperados en el día", f"{total:,.0f}", border=True, chart_data=df["p50"].tolist(), chart_type="area",
          delta=f"{total / semana - 1:+.0%} vs. hace una semana" if semana else None, delta_color="off")
pico = int(df["p50"].idxmax())
c2.metric("Hora pico", f"{pico:02d}:00", border=True, help=f"{df['p50'].max():,.0f} viajes esperados en esa hora")
c3.metric("Rango del día (80 %)", f"{df['p10'].sum():,.0f} – {df['p90'].sum():,.0f}", border=True,
          help="Suma de los cuantiles 10 % y 90 % de cada hora; es una aproximación del rango del día.")
if tiene_real:
    c4.metric("Error promedio por hora", f"{(df['p50'] - df['real']).abs().mean():.1f} viajes", border=True,
              help=f"{df['real'].sum():,.0f} viajes reales ese día")
else:
    c4.metric("Viajes reales", "Pendiente", border=True, help="Es un pronóstico a futuro: todavía no hay datos.")

fig = go.Figure()
fig.add_trace(go.Scatter(x=df["hora"], y=df["p90"], mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip"))
fig.add_trace(go.Scatter(x=df["hora"], y=df["p10"], mode="lines", line=dict(width=0), fill="tonexty",
                         fillcolor="rgba(45,110,104,0.2)", name="Rango 10 %–90 %", hoverinfo="skip"))
fig.add_trace(go.Scatter(x=df["hora"], y=df["semana"], mode="lines", line=dict(dash="dot", color="#7a7a7a"),
                         name="Hace una semana"))
fig.add_trace(go.Scatter(x=df["hora"], y=df["p50"], mode="lines", line=dict(color="#2d6e68", width=3),
                         name="Pronóstico (mediana)"))
if tiene_real:
    fig.add_trace(go.Scatter(x=df["hora"], y=df["real"], mode="markers", marker=dict(color="#b03a3a", size=7), name="Real"))
fig.update_layout(title=f"{datos['zona']['nombre']} · {comun.etiqueta_fecha(fecha, info['fecha_futura'])}"
                        + (" (pronóstico a futuro)" if futura else ""),
                  xaxis_title="Hora del día", yaxis_title="Viajes", hovermode="x unified",
                  legend=dict(orientation="h", y=-0.2), margin=dict(l=10, r=10, t=50, b=10))
st.plotly_chart(fig, use_container_width=True)

if futura:
    st.info("Este es el pronóstico de **mañana**: todavía no hay viajes reales con los que compararlo.",
            icon=":material/schedule:")

with st.expander("Ver la tabla por hora", icon=":material/table:"):
    tabla = df.rename(columns={"hora": "Hora", "real": "Real", "semana": "Hace una semana"})
    st.dataframe(
        tabla[["Hora", "p10", "p50", "p90", "Hace una semana", "Real"]], hide_index=True, use_container_width=True,
        column_config={"p50": st.column_config.ProgressColumn("p50", min_value=0, max_value=float(df["p90"].max()), format="%.0f"),
                       "p10": st.column_config.NumberColumn("p10", format="%.0f"),
                       "p90": st.column_config.NumberColumn("p90", format="%.0f")},
    )
