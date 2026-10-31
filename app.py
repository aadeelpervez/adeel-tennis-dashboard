
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Tennis Analytics",
    page_icon="🎾",
    layout="wide"
)

st.title("🎾 Tennis Analytics Dashboard")
st.caption("Explore your tennis dataset with interactive visualizations.")

file_path = Path(__file__).parent / "tennis.csv"

@st.cache_data
def load_data(path):
    return pd.read_csv(path)

try:
    df = load_data(str(file_path))
    df.columns = df.columns.astype(str).str.strip()

    st.sidebar.header("Dashboard Filters")
    search = st.sidebar.text_input("Search all columns")

    filtered = df.copy()

    text_cols = filtered.select_dtypes(
        include=["object", "category", "string", "bool"]
    ).columns.tolist()

    if text_cols:
        filter_col = st.sidebar.selectbox(
            "Filter by category",
            ["All"] + text_cols
        )

        if filter_col != "All":
            options = sorted(
                filtered[filter_col].dropna().astype(str).unique().tolist()
            )
            selected = st.sidebar.multiselect(
                f"Select {filter_col}",
                options,
                default=options
            )
            filtered = filtered[
                filtered[filter_col].fillna("").astype(str).isin(selected)
            ]

    if search:
        mask = filtered.astype(str).apply(
            lambda col: col.str.contains(
                search, case=False, na=False, regex=False
            )
        ).any(axis=1)
        filtered = filtered[mask]

    # KPI cards
    a, b, c, d = st.columns(4)
    a.metric("Total Records", f"{len(filtered):,}")
    b.metric("Total Columns", len(filtered.columns))
    c.metric("Missing Values", f"{filtered.isna().sum().sum():,}")
    d.metric("Duplicate Rows", f"{filtered.duplicated().sum():,}")

    st.divider()

    if filtered.empty:
        st.warning("No records match your filters.")
        st.stop()

    numeric_cols = filtered.select_dtypes(include="number").columns.tolist()
    category_cols = filtered.select_dtypes(
        include=["object", "category", "string", "bool"]
    ).columns.tolist()

    overview, categories, numeric, data_tab = st.tabs([
        "📊 Overview", "📂 Categories", "📈 Numeric Analysis", "📋 Data"
    ])

    with overview:
        left, right = st.columns(2)

        with left:
            missing = filtered.isna().sum()
            missing = missing[missing > 0].sort_values(ascending=False)

            st.subheader("Missing Values")
            if not missing.empty:
                missing_df = missing.rename_axis("Column").reset_index(
                    name="Missing"
                )
                fig = px.bar(
                    missing_df, x="Column", y="Missing",
                    text_auto=True, title="Data Quality"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.success("No missing values in the filtered data.")

        with right:
            st.subheader("Column Data Types")
            type_counts = filtered.dtypes.astype(str).value_counts()
            type_df = type_counts.rename_axis("Data Type").reset_index(
                name="Count"
            )
            fig = px.pie(
                type_df, names="Data Type", values="Count",
                hole=0.5, title="Dataset Structure"
            )
            st.plotly_chart(fig, use_container_width=True)

    with categories:
        if category_cols:
            cat = st.selectbox(
                "Choose category", category_cols, key="cat_chart"
            )
            counts = (
                filtered[cat].fillna("Missing").astype(str)
                .value_counts().head(15)
                .rename_axis(cat).reset_index(name="Count")
            )

            left, right = st.columns(2)

            with left:
                fig = px.bar(
                    counts.sort_values("Count"),
                    x="Count", y=cat, orientation="h",
                    text="Count", title=f"Top Categories: {cat}"
                )
                st.plotly_chart(fig, use_container_width=True)

            with right:
                fig = px.pie(
                    counts, names=cat, values="Count",
                    hole=0.45, title=f"Category Share: {cat}"
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No category columns found.")

    with numeric:
        if numeric_cols:
            num = st.selectbox(
                "Choose numeric column", numeric_cols, key="num_chart"
            )
            values = pd.to_numeric(filtered[num], errors="coerce").dropna()

            if not values.empty:
                x, y, z = st.columns(3)
                x.metric("Average", f"{values.mean():,.2f}")
                y.metric("Median", f"{values.median():,.2f}")
                z.metric(
                    "Minimum – Maximum",
                    f"{values.min():,.2f} – {values.max():,.2f}"
                )

                left, right = st.columns(2)

                with left:
                    fig = px.histogram(
                        filtered, x=num, nbins=25, marginal="box",
                        title=f"Distribution: {num}"
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with right:
                    fig = px.box(
                        filtered, y=num, points="outliers",
                        title=f"Outlier Analysis: {num}"
                    )
                    st.plotly_chart(fig, use_container_width=True)

            if len(numeric_cols) >= 2:
                st.subheader("Correlation Heatmap")
                corr = filtered[numeric_cols].corr()
                fig = px.imshow(
                    corr, text_auto=".2f", aspect="auto",
                    color_continuous_scale="RdBu_r",
                    zmin=-1, zmax=1, title="Numeric Correlations"
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No numeric columns found.")

    with data_tab:
        st.subheader("Tennis Dataset")
        st.dataframe(filtered, use_container_width=True, hide_index=True)

        st.download_button(
            "Download Filtered CSV",
            data=filtered.to_csv(index=False).encode("utf-8"),
            file_name="tennis_filtered.csv",
            mime="text/csv"
        )

except FileNotFoundError:
    st.error("tennis.csv nahi mili. CSV ko app.py ke same folder mein rakhein.")
except Exception as e:
    st.error(f"Dashboard error: {e}")
