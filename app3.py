# app3.py
# Streamlit LP Optimizer (Soil fixed 75%, Additives ≤ 25%) + AI Suggestions + 3 languages (ID/EN/繁中)
# IMPORTANT CHANGE REQUEST:
# - Mode 1: "Minimize Cost"  -> objective = minimize cost, UCS uses minimum target (>=)
# - Mode 2: "UCS Maximum (Cap)" -> objective STILL = minimize cost, but UCS becomes MAX constraint (<= UCS_max)
#
# Run:
#   pip install streamlit pulp pandas numpy
#   streamlit run app3.py

import streamlit as st
import pandas as pd
from pulp import LpProblem, LpVariable, LpMinimize, lpSum, LpStatus, value

# =========================
# PAGE
# =========================
st.set_page_config(page_title="LP Optimizer – Soil Mix Design", layout="wide")
st.title("LP Optimizer – Soil Mix Design (Soil + Additives)")

# =========================
# SIDEBAR IDENTITY (above language selector)
# =========================
st.sidebar.markdown(
    """
    <div style="text-align:center;">
        <h4 style="margin-bottom:0;">Haidar Fadhila</h4>
        <p style="margin:0; font-size:13px;">M11316025</p>
        <p style="margin:0; font-size:12px; color:gray;">
            Management Science<br>
            Term Project
        </p>
        <hr style="margin-top:10px; margin-bottom:10px;">
    </div>
    """,
    unsafe_allow_html=True
)

# =========================
# LANGUAGE
# =========================
LANG = st.sidebar.selectbox("Language / Bahasa / 語言", ["Bahasa Indonesia", "English", "繁體中文"], index=0)

T = {
    "Bahasa Indonesia": {
        "caption": "Linear Programming (PuLP) + AI Suggestions (rule-based, offline).",
        "mode_header": "Mode Optimasi",
        "mode_pick": "Pilih mode",
        "mode_cost": "Minimasi Biaya (UCS minimum)",
        "mode_ucscap": "UCS Maksimum (Cap) + Minimasi Biaya",
        "fixed_header": "Komposisi",
        "soil_fixed": "Tanah (%) (fixed)",
        "add_cap": "Batas Maks Aditif (%)",
        "tech_header": "Batasan Teknis",
        "target_ucs": "Target UCS (minimum) (mode biaya)",
        "ucs_max": "Batas UCS (maksimum) (mode cap)",
        "pi_max": "Batas PI (maksimum)",
        "w_max": "Batas Water Content (maksimum)",
        "base_header": "Nilai Dasar Tanah (Base)",
        "base_ucs": "Base UCS",
        "base_pi": "Base PI",
        "base_w": "Base Water Content",
        "data_title": "Tabel Data Aditif (Editable)",
        "data_note": "Isi semua kolom numerik dengan angka murni (tanpa satuan di sel).",
        "run_title": "Jalankan Optimasi",
        "btn": "Optimize",
        "ai_ok": "🤖 AI Suggestions (Auto-Interpretation)",
        "ai_bad": "🤖 AI Suggestions (Why infeasible?)",
        "ai_info": "Saran dihasilkan dari aturan (rule-based) berdasarkan margin constraint.",
        "summary": "Ringkasan hasil",
        "total_cost": "Total Cost (Aditif)",
        "opt_comp": "Komposisi optimal aditif (%)",
        "add_used": "Total aditif terpakai",
        "soil_total": "Total tanah (approx.)",
        "math_title": "Model Matematis (untuk slide)",
        "footer": "Haidar Fadhila Rahma- M11316025- Management Sciece | National Yunlin University of Science and Technology",
        "err_cols": "Kolom wajib hilang. Wajib ada: {cols}",
        "err_nan": "Ada nilai non-angka (NaN) pada kolom numerik. Perbaiki tabel.",
        "err_lbub": "Ada baris dengan LB > UB. Perbaiki bounds.",
        "err_dup": "Nama material duplikat. Pastikan unik.",
        "ai_margin_min": "**Margin:** UCS = **{u:.2f}** (hasil-target), PI = **{p:.2f}** (max-hasil), W = **{w:.2f}** (max-hasil).",
        "ai_margin_cap": "**Margin:** UCS = **{u:.2f}** (UCSmax-hasil), PI = **{p:.2f}** (max-hasil), W = **{w:.2f}** (max-hasil).",
        "ai_tightest": "✅ Constraint paling ketat: {c}",
        "ai_tight_ucs": "UCS",
        "ai_tight_pi": "PI",
        "ai_tight_w": "Water Content",
        "ai_dom": "📌 Aditif dominan: {a1}={v1:.2f}%, {a2}={v2:.2f}%.",
        "ai_note_cap": "Catatan: Karena aditif dibatasi (≤ cap), solusi optimal bisa memakai aditif < cap untuk menekan biaya.",
        "ai_suggest_ucs_min": "Saran: Jika infeasible, turunkan target UCS atau naikkan UB aditif yang kontribusi UCS tinggi.",
        "ai_suggest_ucs_cap": "Saran: Jika melanggar cap UCS, turunkan koefisien UCS (atau kurangi aditif yang menaikkan UCS) / naikkan UCSmax.",
        "ai_suggest_pi": "Saran: Perketat/longgarkan PI dengan mengatur aditif yang menurunkan PI (koefisien PI lebih negatif).",
        "ai_suggest_w": "Saran: Perketat/longgarkan W dengan mengatur aditif yang menurunkan W (koefisien W lebih negatif).",
        "ai_infeas_bounds": "❌ Infeasible karena bounds: ΣLB sudah terlalu besar atau constraint terlalu ketat.",
        "ai_infeas_tech": "⚠️ Infeasible kemungkinan karena batasan teknis terlalu ketat (UCS/PI/W).",
    },
    "English": {
        "caption": "Linear Programming (PuLP) + AI Suggestions (rule-based, offline).",
        "mode_header": "Optimization Mode",
        "mode_pick": "Choose mode",
        "mode_cost": "Minimize Cost (UCS minimum)",
        "mode_ucscap": "UCS Maximum (Cap) + Minimize Cost",
        "fixed_header": "Composition",
        "soil_fixed": "Soil (%) (fixed)",
        "add_cap": "Max Additives (%)",
        "tech_header": "Technical Constraints",
        "target_ucs": "Target UCS (minimum) (cost mode)",
        "ucs_max": "UCS limit (maximum) (cap mode)",
        "pi_max": "PI limit (maximum)",
        "w_max": "Water content limit (maximum)",
        "base_header": "Soil Base Properties",
        "base_ucs": "Base UCS",
        "base_pi": "Base PI",
        "base_w": "Base Water Content",
        "data_title": "Additives Data Table (Editable)",
        "data_note": "All numeric cells must be pure numbers (no units inside cells).",
        "run_title": "Run Optimization",
        "btn": "Optimize",
        "ai_ok": "🤖 AI Suggestions (Auto-Interpretation)",
        "ai_bad": "🤖 AI Suggestions (Why infeasible?)",
        "ai_info": "Suggestions are generated by rule-based logic using constraint margins.",
        "summary": "Results summary",
        "total_cost": "Total Cost (Additives)",
        "opt_comp": "Optimal additives composition (%)",
        "add_used": "Total additives used",
        "soil_total": "Total soil (approx.)",
        "math_title": "Mathematical Model (for slides)",
        "footer": "Haidar Fadhila Rahman- M11316025- Management Sciece | National Yunlin University of Science and Technology",
        "err_cols": "Required columns missing. Must include: {cols}",
        "err_nan": "There are non-numeric (NaN) values in numeric columns. Fix the table.",
        "err_lbub": "Some rows have LB > UB. Fix bounds.",
        "err_dup": "Duplicate material names. Make them unique.",
        "ai_margin_min": "**Margins:** UCS = **{u:.2f}** (result-target), PI = **{p:.2f}** (max-result), W = **{w:.2f}** (max-result).",
        "ai_margin_cap": "**Margins:** UCS = **{u:.2f}** (UCSmax-result), PI = **{p:.2f}** (max-result), W = **{w:.2f}** (max-result).",
        "ai_tightest": "✅ Tightest constraint: {c}",
        "ai_tight_ucs": "UCS",
        "ai_tight_pi": "PI",
        "ai_tight_w": "Water Content",
        "ai_dom": "📌 Dominant additives: {a1}={v1:.2f}%, {a2}={v2:.2f}%.",
        "ai_note_cap": "Note: since additives are constrained (≤ cap), the optimal solution may use < cap to reduce cost.",
        "ai_suggest_ucs_min": "Suggestion: If infeasible, reduce UCS target or increase UB for high-UCS additives.",
        "ai_suggest_ucs_cap": "Suggestion: If UCS cap is violated, reduce strength-raising additives or increase UCSmax.",
        "ai_suggest_pi": "Suggestion: Adjust PI by increasing additives that reduce PI (more negative PI coefficients) or relax PI limit.",
        "ai_suggest_w": "Suggestion: Adjust W by increasing additives that reduce W (more negative W coefficients) or relax W limit.",
        "ai_infeas_bounds": "❌ Infeasible due to bounds: ΣLB too high or constraints too tight.",
        "ai_infeas_tech": "⚠️ Infeasible likely due to tight technical constraints (UCS/PI/W).",
    },
    "繁體中文": {
        "caption": "線性規劃（PuLP）＋ AI 建議（規則式、離線）",
        "mode_header": "最佳化模式",
        "mode_pick": "選擇模式",
        "mode_cost": "最小化成本（UCS 下限）",
        "mode_ucscap": "UCS 上限（Cap）＋最小化成本",
        "fixed_header": "配比",
        "soil_fixed": "土壤 (%)（固定）",
        "add_cap": "添加劑上限 (%)",
        "tech_header": "技術限制",
        "target_ucs": "UCS 目標（下限）（成本模式）",
        "ucs_max": "UCS 上限（cap 模式）",
        "pi_max": "PI 上限",
        "w_max": "含水量上限",
        "base_header": "土壤基準值",
        "base_ucs": "Base UCS",
        "base_pi": "Base PI",
        "base_w": "Base 含水量",
        "data_title": "添加劑資料表（可編輯）",
        "data_note": "數值欄位請填純數字（不要在儲存格內寫單位）。",
        "run_title": "執行最佳化",
        "btn": "Optimize",
        "ai_ok": "🤖 AI 建議（自動解讀）",
        "ai_bad": "🤖 AI 建議（為何不可行？）",
        "ai_info": "建議由規則式邏輯根據約束裕度自動產生。",
        "summary": "結果摘要",
        "total_cost": "總成本（添加劑）",
        "opt_comp": "最佳添加劑配比 (%)",
        "add_used": "實際使用添加劑總量",
        "soil_total": "土壤總量（約）",
        "math_title": "數學模型（投影片用）",
        "footer": "Haidar Fadhila Rahman- M11316025- Management Sciece | National Yunlin University of Science and Technology",
        "err_cols": "缺少必要欄位：{cols}",
        "err_nan": "數值欄位出現 NaN（非數字），請修正。",
        "err_lbub": "有些列 LB > UB，請修正。",
        "err_dup": "材料名稱重複，請確保唯一。",
        "ai_margin_min": "**裕度：** UCS = **{u:.2f}**（結果-目標），PI = **{p:.2f}**（上限-結果），含水量 = **{w:.2f}**（上限-結果）。",
        "ai_margin_cap": "**裕度：** UCS = **{u:.2f}**（UCSmax-結果），PI = **{p:.2f}**（上限-結果），含水量 = **{w:.2f}**（上限-結果）。",
        "ai_tightest": "✅ 最緊約束：{c}",
        "ai_tight_ucs": "UCS",
        "ai_tight_pi": "PI",
        "ai_tight_w": "含水量",
        "ai_dom": "📌 主要添加劑：{a1}={v1:.2f}%，{a2}={v2:.2f}%。",
        "ai_note_cap": "注意：因添加劑限制為「≤ 上限」，最佳解可能使用少於上限以降低成本。",
        "ai_suggest_ucs_min": "建議：若不可行，降低 UCS 目標或提高高 UCS 添加劑的 UB。",
        "ai_suggest_ucs_cap": "建議：若超過 UCS 上限，減少提高強度的添加劑或提高 UCSmax。",
        "ai_suggest_pi": "建議：透過增加能降低 PI（PI 係數更負）的添加劑或放寬 PI 上限來調整。",
        "ai_suggest_w": "建議：透過增加能降低含水量（W 係數更負）的添加劑或放寬含水量上限來調整。",
        "ai_infeas_bounds": "❌ 因 bounds 不可行：ΣLB 太高或限制過嚴。",
        "ai_infeas_tech": "⚠️ 可能因技術限制過嚴（UCS/PI/W）而不可行。",
    },
}

tr = T[LANG]
st.caption(tr["caption"])

# =========================
# DEFAULT DATA
# =========================
default_df = pd.DataFrame(
    {
        "material": ["x1", "x2", "x3", "x4", "x5", "x6"],
        "cost": [1500, 400, 600, 200, 700, 600],
        "LB": [1, 6, 1, 3, 1, 2],
        "UB": [10, 8, 10, 15, 10, 8],
        "UCS_coef": [25, 5, 15, 2, 10, 8],
        "PI_coef": [-0.5, -0.2, -0.1, -0.3, -0.2, -0.25],
        "W_coef": [-0.2, -0.1, -0.1, -0.5, -0.1, -0.15],
    }
)

NUMERIC_COLS = ["cost", "LB", "UB", "UCS_coef", "PI_coef", "W_coef"]
REQUIRED_COLS = ["material"] + NUMERIC_COLS

# =========================
# SIDEBAR INPUTS
# =========================
st.sidebar.header(tr["mode_header"])
mode = st.sidebar.radio(tr["mode_pick"], [tr["mode_cost"], tr["mode_ucscap"]])

st.sidebar.header(tr["fixed_header"])
soil_fixed = st.sidebar.number_input(tr["soil_fixed"], value=75.0, step=1.0)
additive_cap = st.sidebar.number_input(tr["add_cap"], value=25.0, step=1.0)

st.sidebar.header(tr["tech_header"])
target_ucs = None
ucs_max = None

if mode == tr["mode_cost"]:
    target_ucs = st.sidebar.number_input(tr["target_ucs"], value=250.0, step=1.0)
else:
    ucs_max = st.sidebar.number_input(tr["ucs_max"], value=300.0, step=1.0)

pi_max = st.sidebar.number_input(tr["pi_max"], value=15.0, step=0.1)
w_max = st.sidebar.number_input(tr["w_max"], value=25.0, step=0.1)

st.sidebar.header(tr["base_header"])
base_ucs = st.sidebar.number_input(tr["base_ucs"], value=50.0, step=1.0)
base_pi = st.sidebar.number_input(tr["base_pi"], value=10.0, step=0.1)
base_w = st.sidebar.number_input(tr["base_w"], value=30.0, step=0.1)

# =========================
# HELPERS
# =========================
def coerce_numeric(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["material"] = out["material"].astype(str)
    for c in NUMERIC_COLS:
        out[c] = pd.to_numeric(out[c], errors="coerce")
    return out


def validate_df(df: pd.DataFrame):
    for c in REQUIRED_COLS:
        if c not in df.columns:
            return False, tr["err_cols"].format(cols=", ".join(REQUIRED_COLS))
    if df[NUMERIC_COLS].isna().any().any():
        return False, tr["err_nan"]
    if (df["LB"] > df["UB"]).any():
        return False, tr["err_lbub"]
    if df["material"].duplicated().any():
        return False, tr["err_dup"]
    return True, ""


def render_solver_status_badge(status: str):
    if status == "Optimal":
        st.markdown(
            """
            <div style="
                background-color:#e6f4ea;
                color:#137333;
                padding:10px;
                border-radius:6px;
                font-weight:700;
                width:fit-content;
                margin-bottom:10px;
            ">
                ✅ Solver status: <span style="font-weight:800;">OPTIMAL</span>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div style="
                background-color:#fdecea;
                color:#b71c1c;
                padding:10px;
                border-radius:6px;
                font-weight:700;
                width:fit-content;
                margin-bottom:10px;
            ">
                ❌ Solver status: <span style="font-weight:800;">{status}</span>
            </div>
            """,
            unsafe_allow_html=True
        )


def ai_suggestions_feasible(res: dict, sol: dict) -> list[str]:
    # margins depend on mode
    if mode == tr["mode_cost"]:
        u_margin = res["UCS"] - float(target_ucs)  # result - target(min)
    else:
        u_margin = float(ucs_max) - res["UCS"]  # cap - result(max)

    p_margin = float(pi_max) - res["PI"]
    w_margin = float(w_max) - res["W"]

    # Clean -0.00 artifacts
    for name, val in [("u", u_margin), ("p", p_margin), ("w", w_margin)]:
        pass
    if abs(u_margin) < 1e-6:
        u_margin = 0.0
    if abs(p_margin) < 1e-6:
        p_margin = 0.0
    if abs(w_margin) < 1e-6:
        w_margin = 0.0

    tips = [tr["ai_note_cap"]]

    if mode == tr["mode_cost"]:
        tips.append(tr["ai_margin_min"].format(u=u_margin, p=p_margin, w=w_margin))
    else:
        tips.append(tr["ai_margin_cap"].format(u=u_margin, p=p_margin, w=w_margin))

    margins = {"UCS": u_margin, "PI": p_margin, "W": w_margin}
    tightest = min(margins, key=margins.get)

    tips.append(tr["ai_tightest"].format(c={
        "UCS": tr["ai_tight_ucs"],
        "PI": tr["ai_tight_pi"],
        "W": tr["ai_tight_w"]
    }[tightest]))

    if tightest == "UCS":
        tips.append(tr["ai_suggest_ucs_min"] if mode == tr["mode_cost"] else tr["ai_suggest_ucs_cap"])
    elif tightest == "PI":
        tips.append(tr["ai_suggest_pi"])
    else:
        tips.append(tr["ai_suggest_w"])

    sol_sorted = sorted(sol.items(), key=lambda kv: kv[1], reverse=True)
    if len(sol_sorted) >= 2:
        (a1, v1), (a2, v2) = sol_sorted[0], sol_sorted[1]
        tips.append(tr["ai_dom"].format(a1=a1, v1=v1, a2=a2, v2=v2))

    return tips


def ai_suggestions_infeasible() -> list[str]:
    return [tr["ai_infeas_bounds"], tr["ai_infeas_tech"]]

# =========================
# DATA EDITOR
# =========================
st.subheader(tr["data_title"])
st.write(tr["data_note"])
edited = st.data_editor(default_df, use_container_width=True, hide_index=True, num_rows="fixed")
df = coerce_numeric(edited)

ok, msg = validate_df(df)
if not ok:
    st.error(msg)
    st.stop()

# =========================
# SOLVER
# =========================
def solve_lp(df: pd.DataFrame):
    mats = df["material"].tolist()

    x = {
        m: LpVariable(
            name=m,
            lowBound=float(df.loc[df["material"] == m, "LB"].iloc[0]),
            upBound=float(df.loc[df["material"] == m, "UB"].iloc[0]),
            cat="Continuous",
        )
        for m in mats
    }

    # Objective ALWAYS: Minimize total additives cost
    prob = LpProblem("SoilMix_CostMin", LpMinimize)
    prob += lpSum(float(df.loc[df["material"] == m, "cost"].iloc[0]) * x[m] for m in mats)

    # Additives cap
    prob += lpSum(x[m] for m in mats) <= float(additive_cap)

    # Expressions
    ucs_expr = base_ucs + lpSum(float(df.loc[df["material"] == m, "UCS_coef"].iloc[0]) * x[m] for m in mats)
    pi_expr = base_pi + lpSum(float(df.loc[df["material"] == m, "PI_coef"].iloc[0]) * x[m] for m in mats)
    w_expr = base_w + lpSum(float(df.loc[df["material"] == m, "W_coef"].iloc[0]) * x[m] for m in mats)

    # UCS constraint depends on mode:
    if mode == tr["mode_cost"]:
        prob += ucs_expr >= float(target_ucs)   # UCS minimum target
    else:
        prob += ucs_expr <= float(ucs_max)      # UCS maximum cap

    # PI/W always maximum limits
    prob += pi_expr <= float(pi_max)
    prob += w_expr <= float(w_max)

    prob.solve()
    status = LpStatus.get(prob.status, str(prob.status))
    if status != "Optimal":
        return status, None

    sol = {m: float(value(x[m])) for m in mats}
    total_add_used = float(sum(sol.values()))
    total_soil_approx = float(100.0 - total_add_used)

    total_cost = float(sum(float(df.loc[df["material"] == m, "cost"].iloc[0]) * sol[m] for m in mats))
    ucs_val = float(value(ucs_expr))
    pi_val = float(value(pi_expr))
    w_val = float(value(w_expr))

    res = {
        "solution": sol,
        "add_used": total_add_used,
        "soil_total": total_soil_approx,
        "total_cost": total_cost,
        "UCS": ucs_val,
        "PI": pi_val,
        "W": w_val,
    }
    return status, res

# =========================
# OUTPUT UI
# =========================
left, right = st.columns([1.05, 0.95])

with left:
    st.subheader(tr["run_title"])
    if st.button(tr["btn"], type="primary"):
        status, res = solve_lp(df)

        # highlighted solver status
        render_solver_status_badge(status)

        if res is None:
            with st.expander(tr["ai_bad"], expanded=True):
                for t in ai_suggestions_infeasible():
                    st.markdown(f"- {t}")
        else:
            st.write(f"**{tr['opt_comp']}**")
            out = pd.DataFrame({"material": list(res["solution"].keys()), "x (%)": list(res["solution"].values())})
            st.dataframe(out, use_container_width=True, hide_index=True)

            st.write(f"- {tr['add_used']}: **{res['add_used']:.2f}%** (cap {additive_cap:.2f}%)")
            st.write(f"- {tr['soil_total']}: **{res['soil_total']:.2f}%**")

            st.write(f"**{tr['summary']}**")
            k1, k2, k3, k4 = st.columns(4)
            k1.metric(tr["total_cost"], f"{res['total_cost']:,.2f}")
            k2.metric("UCS", f"{res['UCS']:.3f}")
            k3.metric("PI", f"{res['PI']:.3f}")
            k4.metric("Water Content", f"{res['W']:.3f}")

            with st.expander(tr["ai_ok"], expanded=True):
                st.info(tr["ai_info"])
                for t in ai_suggestions_feasible(res, res["solution"]):
                    st.markdown(f"- {t}")

with right:
    st.subheader(tr["math_title"])
    st.markdown(
        r"""
**Decision variables (additives):** \(x_i\) = additive percentage, \(i=1..6\)

**Additives constraint (cap):**
\[
\sum_{i=1}^{6} x_i \le 25
\]

**Objective (always):** minimize additives cost  
\[
\min \sum c_i x_i
\]

**UCS constraint depends on mode:**
- Cost mode: \(UCS \ge UCS_{min}\)
- UCS-cap mode: \(UCS \le UCS_{max}\)

\[
UCS = baseUCS + \sum a_i x_i
\]
\[
PI = basePI + \sum b_i x_i \le PI_{max}
\]
\[
W = baseW + \sum d_i x_i \le W_{max}
\]
\[
LB_i \le x_i \le UB_i
\]
"""
    )

st.markdown("---")
st.caption(tr["footer"])
