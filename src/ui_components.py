from __future__ import annotations
from typing import List
import streamlit as st

def pill_choice(title: str, options: List[str], key: str, columns: int = 3) -> str:
    st.markdown(f"{title}")
    if key not in st.session_state:
        st.session_state[key] = options[0]
    rows = [options[i:i+columns] for i in range(0, len(options), columns)]
    for r, row in enumerate(rows):
        cols = st.columns(columns, gap="small")
        for i in range(columns):
            if i >= len(row):
                cols[i].write("")
                continue
            opt = row[i]
            active = (st.session_state[key] == opt)
            label = f"● {opt}" if active else opt
            if cols[i].button(label, key=f"{key}_{r}_{i}", use_container_width=True):
                st.session_state[key] = opt
    return st.session_state[key]

def drip_css(left_pct: float) -> str:
    left_pct = max(0.0, min(95.0, float(left_pct)))
    return f"<div class='drip'><div class='drop' style='left:{left_pct}%;'></div></div>"