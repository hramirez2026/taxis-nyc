import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import comun

st.title("¿Cuántos taxis enviar?")
st.caption("El pronóstico no es la decisión. La cantidad correcta depende de qué cuesta más: "
           "un taxi esperando sin pasajero o un pasajero que no encuentra taxi.")

info = comun.conectar_api()
zona_id, fecha = comun.selector(info)
datos = comun.llamar("/pronostico", zona_id=zona_id, fecha=fecha)
df = comun.a_dataframe(datos)
CUANTILES = info["cuantiles"]
QS = [int(c[1:]) / 100 for c in CUANTILES]
tiene_real = df["real"].notna().all()


def taxis_a_enviar(matriz, q):
    """Interpola entre los cuantiles de la API para la fila de cada hora y redondea hacia arriba."""
    return np.ceil([np.interp(q, QS, fila) for fila in matriz])


def costo(enviados, real, c_ocioso, c_perdido):
    enviados, real = np.asarray(enviados, dtype=float), np.asarray(real, dtype=float)
    return float((np.maximum(enviados - real, 0) * c_ocioso + np.maximum(real - enviados, 0) * c_perdido).sum())


@st.fragment
def planificador():
    a, b = st.columns(2)
    c_o = a.slider("Costo de un taxi sin pasajero durante una hora (USD)", 1, 100, 10,
                   help="Combustible y hora de conductor desperdiciados.")
    c_p = b.slider("Costo de un pasajero que no encontró taxi (USD)", 1, 200, 40,
                   help="Viaje perdido y cliente que se va a la competencia.")
    q = c_p / (c_p + c_o)

    st.markdown(f"Perder un pasajero cuesta **{c_p / c_o:.1f} veces** lo que cuesta un taxi ocioso. "
                f"La regla óptima es cubrir el **cuantil {q:.0%}** de la demanda.")
    st.latex(r"\text{cuantil óptimo} = \frac{C_{perdido}}{C_{perdido} + C_{ocioso}} = \frac{"
             + f"{c_p}" + "}{" + f"{c_p}+{c_o}" + "} = " + f"{q:.2f}")
    if not QS[0] <= q <= QS[-1]:
        st.warning(f"El modelo entrega cuantiles entre {QS[0]:.0%} y {QS[-1]:.0%}; se usa el más cercano.")

    plan = taxis_a_enviar(df[CUANTILES].to_numpy(), q)

    fig = go.Figure()
    fig.add_bar(x=df["hora"], y=plan, name=f"Taxis recomendados (p{q * 100:.0f})", marker_color="#2d6e68")
    fig.add_trace(go.Scatter(x=df["hora"], y=df["p50"], mode="lines", name="Pronóstico central (p50)",
                             line=dict(color="#d98a3d", width=3)))
    if tiene_real:
        fig.add_trace(go.Scatter(x=df["hora"], y=df["real"], mode="markers", name="Demanda real",
                                 marker=dict(color="#b03a3a", size=7)))
    fig.update_layout(xaxis_title="Hora", yaxis_title="Taxis / viajes", legend=dict(orientation="h", y=-0.2),
                      margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

    if tiene_real:
        st.markdown("**Si este día se hubiera decidido así, el costo habría sido:**")
        real = df["real"].to_numpy()
        c_rec = costo(plan, real, c_o, c_p)
        c_p50 = costo(np.round(df["p50"]), real, c_o, c_p)
        c_sem = costo(df["semana"], real, c_o, c_p)
        m1, m2, m3 = st.columns(3)
        m1.metric(f"Recomendación (p{q * 100:.0f})", f"${c_rec:,.0f}", border=True)
        for col, etiqueta, valor in ((m2, "Enviar el pronóstico central (p50)", c_p50),
                                     (m3, "Enviar lo de hace una semana", c_sem)):
            col.metric(etiqueta, f"${valor:,.0f}", border=True, delta_color="inverse",
                       delta=f"{valor / c_rec - 1:+.0%} vs. la recomendación" if c_rec else None)
    else:
        st.info("Mañana no tiene demanda real, así que no se puede calcular el costo; el plan sí está disponible.",
                icon=":material/schedule:")

    csv = pd.DataFrame({"hora": df["hora"], "taxis_recomendados": plan.astype(int), "pronostico_p50": df["p50"].round(0),
                        "hace_una_semana": df["semana"]}).to_csv(index=False).encode("utf-8")
    st.download_button("Descargar plan de taxis por hora", csv, file_name=f"plan_taxis_zona{zona_id}_{fecha}.csv",
                       mime="text/csv", icon=":material/download:")


planificador()

with st.expander("¿Por qué no enviar simplemente el pronóstico central?", icon=":material/lightbulb:"):
    st.markdown(
        "El pronóstico central (p50) se pasa la mitad de las veces y se queda corto la otra mitad. "
        "Si quedarse corto **cuesta más** que pasarse, conviene enviar *más* que el centro; si cuesta menos, *menos*. "
        "Este razonamiento se conoce como el *problema del vendedor de periódicos*. "
        "Para simplificar, se supone que un taxi atiende un viaje por hora."
    )
