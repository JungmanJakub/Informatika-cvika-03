# app.py
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import pandas as pd

st.set_page_config(page_title="Body na kružnici", layout="wide")
st.title("Body na kružnici — interaktivní aplikace")

st.markdown("Zadej souřadnice středu, poloměr, počet bodů a barvu — graf se přepočítá hned po změně hodnot.")

# --- SIDEBAR: vstupy (změny se projeví ihned)
st.sidebar.header("Parametry kružnice")
x0 = st.sidebar.number_input("Střed X", value=0.0, step=0.1, format="%.3f")
y0 = st.sidebar.number_input("Střed Y", value=0.0, step=0.1, format="%.3f")

radius = st.sidebar.slider("Poloměr (r)", min_value=0.0, max_value=100.0, value=1.0, step=0.1, format="%.2f")
num_points = st.sidebar.number_input("Počet bodů", min_value=1, value=8, step=1)

point_size = st.sidebar.slider("Velikost bodů (px)", min_value=5, max_value=200, value=60, step=1)
color = st.sidebar.color_picker("Barva bodů", value="#1f77b4")

unit = st.sidebar.text_input("Jednotka os", value="m")

st.sidebar.markdown("---")
st.sidebar.text_input("Tvé jméno (pro PDF)", key="author_name", value="")
st.sidebar.text_input("Kontakt (email/Teams)", key="author_contact", value="")

# --- výpočet souřadnic
angles = np.linspace(0, 2 * np.pi, int(num_points), endpoint=False)
xs = x0 + float(radius) * np.cos(angles)
ys = y0 + float(radius) * np.sin(angles)

# --- vykreslení (matplotlib)
fig, ax = plt.subplots(figsize=(6,6), dpi=120)
# kružnice jako ohraničení
circle = Circle((x0, y0), radius, fill=False, linestyle="--", linewidth=1)
ax.add_patch(circle)
# body
ax.scatter(xs, ys, s=point_size, c=[color], edgecolors="black", zorder=3)
# očíslování bodů
for i, (xx, yy) in enumerate(zip(xs, ys), start=1):
    ax.annotate(str(i), (xx, yy), textcoords="offset points", xytext=(4,4), fontsize=9, zorder=4)

# nastavení os, mřížky, jednotky
pad = max(0.1, float(radius) * 0.3)
ax.set_xlim(x0 - radius - pad, x0 + radius + pad)
ax.set_ylim(y0 - radius - pad, y0 + radius + pad)
ax.set_aspect('equal', adjustable='box')
ax.set_xlabel(f"X ({unit})")
ax.set_ylabel(f"Y ({unit})")
ax.grid(True, linestyle=':', linewidth=0.5)

st.subheader("Graf")
st.pyplot(fig)

# --- tabulka souřadnic
df = pd.DataFrame({
    "index": np.arange(1, len(xs)+1),
    "x": np.round(xs, 6),
    "y": np.round(ys, 6)
})
df = df.set_index("index")
st.subheader("Souřadnice bodů")
st.dataframe(df)

# --- možnost stáhnout CSV se souřadnicemi
csv_bytes = df.reset_index().to_csv(index=False).encode('utf-8')
st.download_button("Stáhnout souřadnice (CSV)", data=csv_bytes, file_name="souradnice.csv", mime="text/csv")

# --- PDF export (graf + parametry + seznam bodů)
def create_pdf_bytes(author, contact, params_text, fig, df_table, unit):
    # uložit fig do PNG bufferu
    img_buf = BytesIO()
    fig.savefig(img_buf, format='png', bbox_inches='tight', dpi=150)
    img_buf.seek(0)

    pdf_buf = BytesIO()
    c = canvas.Canvas(pdf_buf, pagesize=A4)
    width, height = A4

    # nadpis + metadata
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, height - 50, "Výstup úlohy: Body na kružnici")
    c.setFont("Helvetica", 10)
    c.drawString(40, height - 70, f"Autor: {author}    Kontakt: {contact}")
    c.drawString(40, height - 90, params_text)

    # vložit obrázek grafu
    img = ImageReader(img_buf)
    img_w = width - 80
    iw, ih = img.getSize()
    aspect = ih / float(iw)
    img_h = img_w * aspect
    max_img_h = height - 200
    if img_h > max_img_h:
        img_h = max_img_h
        img_w = img_h / aspect
    c.drawImage(img, 40, height - 120 - img_h, width=img_w, height=img_h)

    # seznam souřadnic pod obrázkem (text)
    text_y = height - 140 - img_h
    c.setFont("Helvetica", 9)
    if text_y < 120:
        c.showPage()
        text_y = height - 40
        c.setFont("Helvetica", 9)
    c.drawString(40, text_y, "Seznam bodů (č. | x | y):")
    text_y -= 14
    for i, row in enumerate(df_table.itertuples(index=False), start=1):
        xval = row.x
        yval = row.y
        line = f"{i:>2} | {xval:>12} {unit} | {yval:>12} {unit}"
        c.drawString(44, text_y, line)
        text_y -= 12
        if text_y < 40:
            c.showPage()
            text_y = height - 40
            c.setFont("Helvetica", 9)

    c.showPage()
    c.save()
    pdf_buf.seek(0)
    return pdf_buf.getvalue()

author = st.sidebar.session_state.get("author_name", "")
contact = st.sidebar.session_state.get("author_contact", "")
params = f"Střed=({x0},{y0}) {unit} | r={radius} {unit} | počet bodů={int(num_points)} | barva={color}"

if st.button("Generovat PDF (graf + souřadnice)"):
    pdf_bytes = create_pdf_bytes(author or "Nezadáno", contact or "Nezadáno", params, fig, df.reset_index()[["x","y"]], unit)
    st.download_button("Stáhnout PDF", data=pdf_bytes, file_name="vysledek_kruznice.pdf", mime="application/pdf")
