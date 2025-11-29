"""Streamlit UI for the personal expense manager."""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.categorization.categorizer import Categorizer
from src.data_access.import_agent import parse_statement
from src.data_access.storage import ExpenseStorage, SQLiteExpenseStorage
from src.analysis.recommendations import generate_recommendations
from src.ml.category_predictor import load_category_model, predict_category
from src.ml.anomaly_detector import load_anomaly_model, is_anomalous
from src.utils.categories import CATEGORY_BY_KEY, CATEGORY_LABELS, get_category_groups, normalize_category, suggest_category

st.set_page_config(page_title="Ausgaben-Manager (Streamlit)", layout="wide")


def get_storage(backend: str):
    key = f"storage_{backend}"
    if key not in st.session_state:
        if backend == "sqlite":
            st.session_state[key] = SQLiteExpenseStorage()
        else:
            st.session_state[key] = ExpenseStorage()
    return st.session_state[key]


def get_categorizer() -> Categorizer:
    if "categorizer" not in st.session_state:
        st.session_state["categorizer"] = Categorizer()
    return st.session_state["categorizer"]


@st.cache_resource(show_spinner=False)
def get_category_model():
    return load_category_model()


@st.cache_resource(show_spinner=False)
def get_anomaly_artifact():
    return load_anomaly_model()


def guess_category(description: str, amount: float, categorizer: Categorizer) -> str:
    """Prefer ML model (TF-IDF) then legacy categorizer, then heuristics."""
    # ML model
    ml_model = get_category_model()
    if ml_model:
        ml_pred = predict_category(ml_model, {"description": description, "amount": amount})
        normalized_ml = normalize_category(ml_pred, amount, description)
        if normalized_ml:
            category_type = "income" if amount >= 0 else "expense"
            meta = CATEGORY_BY_KEY.get(normalized_ml)
            if meta and meta.type == category_type:
                return normalized_ml

    # Legacy categorizer (naive Bayes)
    prediction: str | None = None
    if description.strip():
        try:
            predicted = categorizer.predict(description)
            prediction = str(predicted)
        except RuntimeError:
            prediction = None
    normalized = normalize_category(prediction, amount, description)
    if normalized:
        category_type = "income" if amount >= 0 else "expense"
        meta = CATEGORY_BY_KEY.get(normalized)
        if meta and meta.type == category_type:
            return normalized
    return suggest_category(description, amount)


def monthly_overview(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    summary: Dict[str, Dict[str, float]] = {}
    for tx in transactions:
        month = str(tx["date"])[:7]
        amount = float(tx["amount"])
        if month not in summary:
            summary[month] = {"month": month, "income": 0.0, "expense": 0.0, "net": 0.0}
        if amount >= 0:
            summary[month]["income"] += amount
        else:
            summary[month]["expense"] += abs(amount)
        summary[month]["net"] += amount
    return [summary[m] for m in sorted(summary.keys())]


def totals(transactions: List[Dict[str, Any]]) -> Dict[str, float]:
    income = sum(float(tx["amount"]) for tx in transactions if float(tx["amount"]) >= 0)
    expense = sum(abs(float(tx["amount"])) for tx in transactions if float(tx["amount"]) < 0)
    return {"income": income, "expense": expense, "net": income - expense}


def expense_by_category(transactions: List[Dict[str, Any]]) -> Dict[str, float]:
    totals_by_cat: Dict[str, float] = {}
    for tx in transactions:
        amount = float(tx["amount"])
        if amount >= 0:
            continue
        key = str(tx.get("category")) or "Unbekannt"
        totals_by_cat[key] = totals_by_cat.get(key, 0.0) + abs(amount)
    return totals_by_cat


def format_transactions(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    formatted: List[Dict[str, Any]] = []
    anomaly_flags = detect_anomalies(transactions)
    for idx, tx in enumerate(transactions):
        formatted.append(
            {
                "Datum": tx["date"],
                "Beschreibung": tx["description"],
                "Betrag (EUR)": float(tx["amount"]),
                "Kategorie": CATEGORY_LABELS.get(tx.get("category", ""), tx.get("category", "")),
                "Auffällig": "⚠" if anomaly_flags[idx] else "",
            }
        )
    return formatted


def detect_anomalies(transactions: List[Dict[str, Any]]) -> List[bool]:
    artifact = get_anomaly_artifact()
    if artifact is None:
        return [False] * len(transactions)
    flags: List[bool] = []
    for tx in transactions:
        flags.append(is_anomalous(artifact, tx))
    return flags


def _parse_date_safe(value: Any) -> dt.date | None:
    try:
        if isinstance(value, dt.date):
            return value
        return dt.date.fromisoformat(str(value))
    except Exception:
        return None


def _in_date_range(value: Any, start: dt.date | None, end: dt.date | None) -> bool:
    parsed = _parse_date_safe(value)
    if parsed is None:
        return False
    if start and parsed < start:
        return False
    if end and parsed > end:
        return False
    return True


def apply_table_filters(
    transactions: List[Dict[str, Any]],
    *,
    search: str = "",
    category_filter: str | None = None,
    anomalies_only: bool = False,
    start_date: dt.date | None = None,
    end_date: dt.date | None = None,
) -> List[Dict[str, Any]]:
    """Filter transactions for UI listing."""
    if not transactions:
        return []
    flags = detect_anomalies(transactions) if anomalies_only else [False] * len(transactions)
    filtered: List[Dict[str, Any]] = []
    search_lower = search.lower().strip()
    for tx, is_flagged in zip(transactions, flags):
        if anomalies_only and not is_flagged:
            continue
        if category_filter and tx.get("category") != category_filter:
            continue
        if start_date or end_date:
            if not _in_date_range(tx.get("date"), start_date, end_date):
                continue
        if search_lower:
            haystack = f"{tx.get('description','')} {tx.get('category','')} {tx.get('date','')}".lower()
            if search_lower not in haystack:
                continue
        filtered.append(tx)
    return filtered


def budget_area_dataframe(transactions: List[Dict[str, Any]], budget_config) -> pd.DataFrame:
    """Aggregate monthly expenses by budget category for area chart."""
    limits = budget_config.category_limits if budget_config else {}
    if not limits:
        return pd.DataFrame()
    agg: Dict[tuple[str, str], float] = {}
    for tx in transactions:
        amount = float(tx["amount"])
        if amount >= 0:
            continue
        category = str(tx.get("category"))
        if category not in limits:
            continue
        month = str(tx["date"])[:7]
        key = (month, category)
        agg[key] = agg.get(key, 0.0) + abs(amount)
    if not agg:
        return pd.DataFrame()
    rows = []
    for (month, category), value in agg.items():
        rows.append(
            {
                "Monat": month,
                "Kategorie": CATEGORY_LABELS.get(category, category),
                "Betrag": value,
                "Limit": limits.get(category, 0.0),
            }
        )
    return pd.DataFrame(rows).sort_values("Monat")


def budget_usage_dataframe(transactions: List[Dict[str, Any]], budget_config) -> pd.DataFrame:
    """Aggregate current month usage vs. budget for battery-style chart."""
    limits = budget_config.category_limits if budget_config else {}
    if not limits:
        return pd.DataFrame()
    if not transactions:
        return pd.DataFrame()
    latest_date = max(str(tx["date"]) for tx in transactions)
    current_month = latest_date[:7]
    spend: Dict[str, float] = {}
    for tx in transactions:
        if not str(tx["date"]).startswith(current_month):
            continue
        amount = float(tx["amount"])
        if amount >= 0:
            continue
        cat = str(tx.get("category"))
        if cat not in limits:
            continue
        spend[cat] = spend.get(cat, 0.0) + abs(amount)
    rows = []
    for cat, limit in limits.items():
        spent = spend.get(cat, 0.0)
        used_within = min(spent, limit)
        over = max(spent - limit, 0.0)
        remaining = max(limit - spent, 0.0)
        ratio = spent / limit if limit else 0.0
        rows.append(
            {
                "Kategorie": CATEGORY_LABELS.get(cat, cat),
                "spent": spent,
                "limit": limit,
                "used_within": used_within,
                "over": over,
                "remaining": remaining,
                "ratio": ratio,
            }
        )
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.sort_values("ratio", ascending=False)


def monthly_average(transactions: List[Dict[str, Any]]) -> Dict[str, float]:
    if not transactions:
        return {"income": 0.0, "expense": 0.0, "net": 0.0}
    df = pd.DataFrame(transactions)
    df["amount"] = df["amount"].astype(float)
    df["month"] = df["date"].astype(str).str[:7]
    income_by_month = df[df["amount"] >= 0].groupby("month")["amount"].sum()
    expense_by_month = df[df["amount"] < 0].groupby("month")["amount"].sum().abs()
    months_income = income_by_month.index.nunique() or 1
    months_expense = expense_by_month.index.nunique() or 1
    avg_income = income_by_month.sum() / months_income if months_income else 0.0
    avg_expense = expense_by_month.sum() / months_expense if months_expense else 0.0
    return {"income": avg_income, "expense": avg_expense, "net": avg_income - avg_expense}


def analyze_trends(transactions: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Generate positive/negative trend notes based on monthly changes."""
    if not transactions:
        return {"positive": [], "negative": []}
    df = pd.DataFrame(transactions)
    df["amount"] = df["amount"].astype(float)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    if df.empty:
        return {"positive": [], "negative": []}
    df["month"] = df["date"].dt.to_period("M").astype(str)
    month_order = sorted(df["month"].unique())
    if len(month_order) < 2:
        return {"positive": [], "negative": []}

    # Net trend
    monthly_net = df.groupby("month")["amount"].sum().reindex(month_order)
    last, prev = monthly_net.iloc[-1], monthly_net.iloc[-2]
    delta_net = last - prev

    # Expense categories trend (last vs prev month)
    exp = df[df["amount"] < 0].copy()
    exp["abs_amount"] = exp["amount"].abs()
    cat_month = exp.groupby(["month", "category"])["abs_amount"].sum().unstack(fill_value=0)
    cat_month = cat_month.reindex(index=month_order, fill_value=0)
    pos: List[str] = []
    neg: List[str] = []

    if delta_net > 0:
        pos.append(f"Netto verbessert: +{delta_net:.2f} EUR gegenüber Vormonat.")
    elif delta_net < 0:
        neg.append(f"Netto verschlechtert: {delta_net:.2f} EUR gegenüber Vormonat.")

    if cat_month.shape[0] >= 2:
        last_row = cat_month.iloc[-1]
        prev_row = cat_month.iloc[-2]
        diffs = (last_row - prev_row).sort_values()
        # stärkste Senker (positiv)
        for cat, diff in diffs.head(3).items():
            if diff < -1e-6:  # weniger ausgegeben
                label = CATEGORY_LABELS.get(cat, cat)
                pos.append(f"Weniger Ausgaben bei {label}: {-diff:.2f} EUR weniger als Vormonat.")
        # stärkste Steigerungen (negativ)
        for cat, diff in diffs.tail(3).items():
            if diff > 1e-6:
                label = CATEGORY_LABELS.get(cat, cat)
                neg.append(f"Höhere Ausgaben bei {label}: +{diff:.2f} EUR zum Vormonat.")

    return {"positive": pos, "negative": neg}


st.title("Persönlicher Ausgaben-Manager")
st.caption(
    "Erfasse Einnahmen/Ausgaben, erhalte Monatsübersichten, Diagramme, Budget-Warnungen "
    "und trainiere eine automatische Kategorisierung mit scikit-learn."
)

backend_label = st.sidebar.radio("Datenspeicher", ["CSV", "SQLite"], help="CSV als Flatfile oder SQLite-Datenbank nutzen.")
backend = backend_label.lower()
storage = get_storage(backend)
categorizer = get_categorizer()

transactions_all = storage.list_transactions()
available_months = sorted({str(tx["date"])[:7] for tx in transactions_all})
month_filter = st.sidebar.selectbox("Monatsfilter", ["Alle"] + available_months, index=0)
filtered_month = None if month_filter == "Alle" else month_filter
transactions = storage.list_transactions(filtered_month)

warn_data = storage.check_budget_limits()
totals_filtered = totals(transactions)
col_a, col_b, col_c = st.columns(3)
col_a.metric("Einnahmen", f"{totals_filtered['income']:.2f} €")
col_b.metric("Ausgaben", f"{totals_filtered['expense']:.2f} €")
col_c.metric("Saldo", f"{totals_filtered['net']:.2f} €")

avg = monthly_average(transactions_all)
col_d, col_e, col_f = st.columns(3)
col_d.metric("Durchschnitt mtl. Einnahmen", f"{avg['income']:.2f} €")
col_e.metric("Durchschnitt mtl. Ausgaben", f"{avg['expense']:.2f} €")
col_f.metric("Durchschnitt mtl. Saldo", f"{avg['net']:.2f} €")

if warn_data:
    st.warning(
        "Budgetlimits fast erreicht oder überschritten: "
        + ", ".join(
            f"{CATEGORY_LABELS.get(cat, cat)} ({ratio * 100:.0f}% des Limits)"
            for cat, ratio in warn_data.items()
        )
    )
else:
    st.success("Keine Budget-Warnungen aktiv.")

tab_input, tab_overview, tab_import, tab_ai, tab_trends = st.tabs(
    ["Transaktionen", "Übersicht & Diagramme", "Import & KI", "KI-Empfehlungen", "Trends"]
)

with tab_input:
    st.subheader("Neue Transaktion erfassen")
    with st.form("add-transaction", clear_on_submit=True):
        col1, col2 = st.columns([1, 2])
        date_value = col1.date_input("Datum", value=dt.date.today())
        description = col2.text_input("Beschreibung")
        col3, col4 = st.columns([1, 1])
        amount = col3.number_input("Betrag (negativ = Ausgabe)", value=0.0, step=1.0, format="%.2f")
        auto_category = guess_category(description, amount, categorizer)
        category_options = [cat.key for group in get_category_groups().values() for cat in group]
        default_index = category_options.index(auto_category) if auto_category in category_options else 0
        category = col4.selectbox(
            "Kategorie",
            category_options,
            index=default_index,
            format_func=lambda key: CATEGORY_LABELS.get(key, key),
            help="Auto-Vorschlag basierend auf KI/Heuristik.",
        )
        if auto_category:
            col4.caption(f"Auto: {CATEGORY_LABELS.get(auto_category, auto_category)}")
        submitted = st.form_submit_button("Speichern")
        if submitted:
            if not description.strip():
                st.error("Bitte eine Beschreibung angeben.")
            else:
                try:
                    storage.add_transaction(
                        {
                            "date": date_value.isoformat(),
                            "description": description.strip(),
                            "amount": amount,
                            "category": category,
                        }
                    )
                    st.success(f"Transaktion gespeichert ({CATEGORY_LABELS.get(category, category)}).")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

    st.subheader("Transaktionen")
    if transactions:
        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([2, 1, 1, 1])
        search_term = filter_col1.text_input("Suche (Beschreibung/Kategorie/Datum)", value="")

        cat_items = []
        for group, cats in get_category_groups().items():
            prefix = "Einnahme" if group == "income" else "Ausgabe"
            for cat in cats:
                label = f"{prefix}: {cat.label}"
                cat_items.append((label, cat.key))
        category_options = ["Alle"] + [label for label, _ in cat_items]
        category_selected_label = filter_col2.selectbox("Kategorie-Filter", options=category_options, index=0)
        category_lookup = {label: key for label, key in cat_items}
        category_key = category_lookup.get(category_selected_label) if category_selected_label != "Alle" else None

        period_options = ["Alle", "Letzte 7 Tage", "Letzte 30 Tage", "Aktueller Monat", "Letzte 3 Monate", "Letzte 12 Monate"]
        period_selected = filter_col3.selectbox("Zeitraum", options=period_options, index=0)
        end_date = dt.date.today()
        start_date = None
        if period_selected == "Letzte 7 Tage":
            start_date = end_date - dt.timedelta(days=6)
        elif period_selected == "Letzte 30 Tage":
            start_date = end_date - dt.timedelta(days=29)
        elif period_selected == "Aktueller Monat":
            start_date = end_date.replace(day=1)
        elif period_selected == "Letzte 3 Monate":
            start_date = end_date - dt.timedelta(days=89)
        elif period_selected == "Letzte 12 Monate":
            start_date = end_date - dt.timedelta(days=364)

        anomalies_only = filter_col4.checkbox("Nur Auffällige", value=False)

        filtered_tx = apply_table_filters(
            transactions,
            search=search_term,
            category_filter=category_key,
            anomalies_only=anomalies_only,
            start_date=start_date,
            end_date=end_date if period_selected != "Alle" else None,
        )
        transactions_sorted = sorted(filtered_tx, key=lambda tx: str(tx["date"]), reverse=True)
        st.dataframe(format_transactions(transactions_sorted), use_container_width=True, hide_index=True)
    else:
        st.info("Keine Transaktionen im ausgewählten Zeitraum.")

with tab_overview:
    st.subheader("Monatliche Übersicht")
    overview_rows = monthly_overview(transactions_all)
    if overview_rows:
        display_rows = [
            {
                "Monat": row["month"],
                "Einnahmen": row["income"],
                "Ausgaben": row["expense"],
                "Saldo": row["net"],
            }
            for row in overview_rows
        ]
        st.dataframe(display_rows, use_container_width=True, hide_index=True)
    else:
        st.info("Noch keine Daten für eine Monatsübersicht vorhanden.")

    st.subheader("Diagramme")
    chart_col1, chart_col2 = st.columns(2)
    if overview_rows:
        months = [row["month"] for row in overview_rows]
        net_values = [row["net"] for row in overview_rows]
        colors = ["#27ae60" if value >= 0 else "#c0392b" for value in net_values]
        fig_monthly = go.Figure(data=[go.Bar(x=months, y=net_values, marker_color=colors)])
        fig_monthly.update_layout(title="Saldo pro Monat", yaxis_title="EUR")
        chart_col1.plotly_chart(fig_monthly, use_container_width=True)
    else:
        chart_col1.info("Kein Monatschart möglich.")

    expense_totals = expense_by_category(transactions_all)
    if expense_totals:
        labels = [CATEGORY_LABELS.get(cat, cat) for cat in expense_totals.keys()]
        values = list(expense_totals.values())
        fig_pie = px.pie(values=values, names=labels, title="Ausgaben nach Kategorie", hole=0.25)
        chart_col2.plotly_chart(fig_pie, use_container_width=True)
    else:
        chart_col2.info("Keine Ausgaben für ein Kreisdiagramm vorhanden.")

    st.subheader("Budget-Füllstand (monatlich, Batterie-Ansicht)")
    df_usage = budget_usage_dataframe(transactions_all, storage.budget_config)
    if not df_usage.empty:
        fig_battery = go.Figure()
        fig_battery.add_bar(
            y=df_usage["Kategorie"],
            x=df_usage["used_within"],
            orientation="h",
            name="Genutzt",
            marker_color="#27ae60",
            hovertemplate="Genutzt: %{x:.2f} EUR<br>Kategorie: %{y}<extra></extra>",
        )
        fig_battery.add_bar(
            y=df_usage["Kategorie"],
            x=df_usage["remaining"],
            orientation="h",
            name="Verfügbar",
            marker_color="#ecf0f1",
            hovertemplate="Verfügbar: %{x:.2f} EUR<br>Kategorie: %{y}<extra></extra>",
        )
        fig_battery.add_bar(
            y=df_usage["Kategorie"],
            x=df_usage["over"],
            orientation="h",
            name="Über Budget",
            marker_color="#e74c3c",
            hovertemplate="Über: %{x:.2f} EUR<br>Kategorie: %{y}<extra></extra>",
        )
        fig_battery.update_layout(
            barmode="stack",
            title="Budget-Nutzung je Kategorie (aktueller Monat)",
            xaxis_title="EUR",
            yaxis_title="Kategorie",
            legend_title="Status",
        )
        st.plotly_chart(fig_battery, use_container_width=True)
    else:
        st.info("Keine Ausgaben im aktuellen Monat für Budget-Kategorien gefunden.")

with tab_ai:
    st.subheader("KI-Empfehlungen zur Finanzoptimierung")
    recs = generate_recommendations(transactions_all, storage.budget_config)
    if not recs:
        st.info("Noch keine Empfehlungen verfügbar. Bitte Transaktionen importieren oder hinzufügen.")
    else:
        for rec in recs:
            severity = rec.get("severity", "niedrig")
            if severity == "hoch":
                st.error(f"{rec['title']}\n\n{rec['body']}")
            elif severity == "mittel":
                st.warning(f"{rec['title']}\n\n{rec['body']}")
            else:
                st.info(f"{rec['title']}\n\n{rec['body']}")

with tab_trends:
    st.subheader("Trends (historische Entwicklung)")
    trends = analyze_trends(transactions_all)
    if not trends["positive"] and not trends["negative"]:
        st.info("Noch keine Trends verfügbar. Bitte mehr Transaktionen/Monate importieren.")
    else:
        if trends["positive"]:
            st.success("Positive Trends:")
            for item in trends["positive"]:
                st.write(f"• {item}")
        if trends["negative"]:
            st.error("Negative Trends:")
            for item in trends["negative"]:
                st.write(f"• {item}")

with tab_import:
    st.subheader("Kontoauszug importieren (CSV/PDF/Bild)")
    uploaded = st.file_uploader("Datei wählen", type=["csv", "pdf", "png", "jpg", "jpeg"])
    if uploaded is not None:
        try:
            parsed = parse_statement(uploaded.read(), uploaded.name)
        except ValueError as exc:
            parsed = []
            st.error(str(exc))
        with st.expander("Debug: Parser-Ausgabe", expanded=False):
            st.write("Anzahl importierter Transaktionen:", len(parsed))
            st.write(parsed[:5])
        if parsed:
            st.success(f"{len(parsed)} Transaktionen im Upload erkannt.")
            st.dataframe(format_transactions(parsed), use_container_width=True, hide_index=True)
            if st.button("Importieren", key="import-button"):
                imported = 0
                duplicates = 0
                for tx in parsed:
                    try:
                        storage.add_transaction(tx)
                        imported += 1
                    except ValueError:
                        duplicates += 1
                        continue
                st.success(f"{imported} importiert, {duplicates} übersprungen.")
                st.rerun()
        else:
            st.info("Keine verwertbaren Transaktionen gefunden.")

    st.subheader("Automatische Kategorisierung trainieren")
    st.caption("Verwendet Beschreibungen aller gespeicherten Transaktionen zum Trainieren eines scikit-learn-Modells.")
    if st.button("Training starten"):
        try:
            categorizer.train(storage.list_transactions())
            st.success("Kategorisierer aktualisiert. Neue Vorschläge werden direkt genutzt.")
        except Exception as exc:  # noqa: BLE001 - Benutzerfreundliche Rückmeldung
            st.error(f"Training fehlgeschlagen: {exc}")

    st.divider()
    if st.button("Alle Daten löschen", type="primary"):
        storage.clear_all()
        st.success("Alle Transaktionen gelöscht.")
        st.rerun()
