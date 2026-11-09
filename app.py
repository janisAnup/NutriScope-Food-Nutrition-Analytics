# NutriScope – Food Product & Nutrition Analytics
# Run with: python -m streamlit run app.py

import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------------------------------------
# 1. Page configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="NutriScope | Nutrition Analytics",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🥗 NutriScope")
st.subheader("Food Product & Nutrition Analytics")
st.caption(
    "Explore product records and compare their nutritional characteristics "
    "using the Open Food Facts dataset."
)

DATA_PATH = "nutriscope_cleaned.csv"


# ---------------------------------------------------------
# 2. Load dataset
# ---------------------------------------------------------
@st.cache_data
def load_data(file_path):
    data = pd.read_csv(file_path)

    # Convert columns to suitable data types.
    data["created_datetime"] = pd.to_datetime(
        data["created_datetime"], errors="coerce", utc=True
    )
    numeric_columns = [
        "energy_kcal_100g",
        "fat_100g",
        "saturated-fat_100g",
        "carbohydrates_100g",
        "sugars_100g",
        "proteins_100g",
        "fiber_100g",
        "sodium_100g",
        "additives_n",
    ]

    for column in numeric_columns:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    # Extract the first listed category for a manageable category filter.
    # This is the first category label in the source field, not a verified
    # official "main category".
    data["primary_listed_category"] = (
        data["categories_en"]
        .fillna("Unknown")
        .astype(str)
        .str.split(",")
        .str[0]
        .str.strip()
        .replace("", "Unknown")
    )

    data["record_month"] = (
        data["created_datetime"].dt.tz_convert(None).dt.to_period("M").dt.to_timestamp()
    )

    return data


try:
    df = load_data(DATA_PATH)
except FileNotFoundError:
    st.error(
        f"Could not find **{DATA_PATH}**. Place the cleaned CSV file in the same "
        "folder as app.py, then run the app again."
    )
    st.stop()
except Exception as error:
    st.error(f"An error occurred while loading the dataset: {error}")
    st.stop()


# ---------------------------------------------------------
# 3. Sidebar filters
# ---------------------------------------------------------
st.sidebar.header("🔎 Filter Products")
st.sidebar.caption("Choose filters below. All dashboard sections update automatically.")

countries = sorted(
    value for value in df["countries_en"].dropna().astype(str).unique()
    if value.strip() and value != "Unknown"
)
country_options = ["All countries"] + countries
selected_country = st.sidebar.selectbox("Country", country_options)

pnns_groups = sorted(
    value for value in df["pnns_groups_1"].dropna().astype(str).unique()
)
selected_groups = st.sidebar.multiselect(
    "Food group",
    options=pnns_groups,
    default=[],
    help="Leave this empty to include all food groups.",
)

# Display the 30 most frequent listed categories to keep the filter manageable.
category_values = (
    df.loc[df["primary_listed_category"] != "Unknown", "primary_listed_category"]
    .value_counts()
    .head(30)
    .index
    .tolist()
)
selected_categories = st.sidebar.multiselect(
    "Primary listed category (top 30)",
    options=category_values,
    default=[],
    help="Choose from the 30 most frequent first-listed category labels. Leave empty for all categories.",
)

min_energy = float(df["energy_kcal_100g"].min())
max_energy = float(df["energy_kcal_100g"].max())
energy_range = st.sidebar.slider(
    "Energy (kcal per 100g)",
    min_value=0.0,
    max_value=float(max_energy),
    value=(max(0.0, min_energy), float(max_energy)),
    step=1.0,
)

protein_max = float(df["proteins_100g"].max())
protein_range = st.sidebar.slider(
    "Protein (g per 100g)",
    min_value=0.0,
    max_value=max(1.0, protein_max),
    value=(0.0, max(1.0, protein_max)),
    step=0.5,
)

# Apply all selected filters to a copy of the original data.
filtered_df = df.copy()

if selected_country != "All countries":
    filtered_df = filtered_df[
        filtered_df["countries_en"].astype(str) == selected_country
    ]

if selected_groups:
    filtered_df = filtered_df[
        filtered_df["pnns_groups_1"].isin(selected_groups)
    ]

if selected_categories:
    filtered_df = filtered_df[
        filtered_df["primary_listed_category"].isin(selected_categories)
    ]

# Apply numeric filters. When a slider is left at its full range, retain
# missing values rather than silently removing those records.
energy_mask = filtered_df["energy_kcal_100g"].between(
    energy_range[0], energy_range[1], inclusive="both"
)
if energy_range[0] == 0.0 and energy_range[1] == max_energy:
    energy_mask = energy_mask | filtered_df["energy_kcal_100g"].isna()

protein_mask = filtered_df["proteins_100g"].between(
    protein_range[0], protein_range[1], inclusive="both"
)
if protein_range[0] == 0.0 and protein_range[1] == protein_max:
    protein_mask = protein_mask | filtered_df["proteins_100g"].isna()

filtered_df = filtered_df[energy_mask & protein_mask]

st.sidebar.divider()
st.sidebar.metric("Products after filtering", f"{len(filtered_df):,}")
if st.sidebar.button("Reset all filters"):
    st.rerun()


# ---------------------------------------------------------
# 4. Dataset information and tabs
# ---------------------------------------------------------
with st.expander("About this dataset"):
    st.write(
        "The dataset contains food product records from Open Food Facts. "
        "The analysis focuses on energy, fat, saturated fat, carbohydrates, "
        "sugars, protein, fibre, sodium and recorded additives."
    )
    st.write(
        "**Important:** Nutritional values are expressed per 100 g. "
        "Energy is displayed in kcal per 100 g after converting the source "
        "energy value from kJ. The record date represents when a product "
        "record was created in the database; it is not a sales or manufacturing date."
    )
    st.write(
        "**Dataset preparation:** The downloaded source contained 356,027 records. "
        "After cleaning and validation, 291,870 records were considered valid. "
        "A working sample of 50,000 records was then selected for this dashboard."
    )
    st.write(
        "**Processing:** Energy was converted from kJ per 100 g to kcal per 100 g "
        "using the factor 1 kcal = 4.184 kJ. Missing numerical values are retained "
        "as missing (not replaced with zero) and are excluded only from calculations "
        "that require that particular attribute."
    )
    st.write(
        "**Date field:** The timeline uses the date the product record was created "
        "in Open Food Facts. It does not represent the product's manufacturing date "
        "or sales date."
    )

overview_tab, exploration_tab, visual_tab, insights_tab = st.tabs(
    ["📊 Dashboard Overview", "🔍 Data Exploration", "📈 Visual Analytics", "💡 Insights"]
)


# ---------------------------------------------------------
# 5. Dashboard overview
# ---------------------------------------------------------
with overview_tab:
    st.header("Nutrition at a glance")

    if filtered_df.empty:
        st.warning("No products match the selected filters. Change or reset the filters.")
    else:
        total_products = len(filtered_df)
        average_energy = filtered_df["energy_kcal_100g"].mean()
        average_protein = filtered_df["proteins_100g"].mean()
        average_sugar = filtered_df["sugars_100g"].mean()
        average_fat = filtered_df["fat_100g"].mean()
        total_additives = filtered_df["additives_n"].sum()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total products", f"{total_products:,}")
        col2.metric("Avg. energy", f"{average_energy:.1f} kcal")
        col3.metric("Avg. protein", f"{average_protein:.2f} g")
        col4.metric("Avg. sugar", f"{average_sugar:.2f} g")

        col5, col6, col7 = st.columns(3)
        col5.metric("Avg. fat", f"{average_fat:.2f} g")
        col6.metric("Avg. additives", f"{filtered_df['additives_n'].mean():.2f}")
        col7.metric("Total recorded additives", f"{total_additives:,.0f}")

        with st.expander("Data quality in the current selection"):
            quality_columns = [
                "fat_100g", "saturated-fat_100g", "carbohydrates_100g",
                "sugars_100g", "proteins_100g", "fiber_100g",
                "sodium_100g", "additives_n"
            ]
            missing_summary = (
                filtered_df[quality_columns].isna().sum()
                .rename("Missing records")
                .reset_index()
                .rename(columns={"index": "Nutritional attribute"})
            )
            missing_summary["Missing percentage"] = (
                missing_summary["Missing records"] / len(filtered_df) * 100
            ).round(2)
            st.dataframe(missing_summary, use_container_width=True, hide_index=True)
            st.caption(
                "Missing values are not treated as zero. Each average is calculated "
                "using the available observations for that nutritional attribute."
            )

        st.divider()
        left, right = st.columns(2)

        with left:
            st.subheader("Products by food group")
            known_group_data = filtered_df[
                filtered_df["pnns_groups_1"].astype(str).str.strip().str.lower()
                != "unknown"
            ]
            group_counts = (
                known_group_data.groupby("pnns_groups_1")
                .size()
                .reset_index(name="Product count")
                .sort_values("Product count", ascending=False)
                .head(10)
            )
            unknown_count = (
                filtered_df["pnns_groups_1"].astype(str).str.strip().str.lower()
                == "unknown"
            ).sum()
            unknown_percentage = (
                unknown_count / len(filtered_df) * 100 if len(filtered_df) else 0
            )

            if not group_counts.empty:
                fig = px.bar(
                    group_counts,
                    x="pnns_groups_1",
                    y="Product count",
                    title="Top 10 classified food groups",
                    labels={
                        "pnns_groups_1": "Food group",
                        "Product count": "Number of products",
                    },
                )
                fig.update_layout(xaxis_tickangle=-30)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No classified food groups are available in this selection.")

            st.caption(
                f"Unclassified records: {unknown_count:,} "
                f"({unknown_percentage:.1f}% of the current selection). "
                "Unknown groups are excluded from this comparison."
            )

        with right:
            st.subheader("Average nutritional values")
            nutrient_means = pd.DataFrame(
                {
                    "Nutrient": ["Fat", "Carbohydrates", "Sugars", "Protein", "Fibre"],
                    "Average (g/100g)": [
                        filtered_df["fat_100g"].mean(),
                        filtered_df["carbohydrates_100g"].mean(),
                        filtered_df["sugars_100g"].mean(),
                        filtered_df["proteins_100g"].mean(),
                        filtered_df["fiber_100g"].mean(),
                    ],
                }
            )
            fig = px.bar(
                nutrient_means,
                x="Nutrient",
                y="Average (g/100g)",
                title="Average nutrient content per 100 g",
                labels={"Average (g/100g)": "Average grams per 100 g"},
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption(
                "Interpretation: The bars compare the average grams of each "
                "nutrient per 100 g, using records where that nutrient is available."
            )


# ---------------------------------------------------------
# 6. Data exploration
# ---------------------------------------------------------
with exploration_tab:
    st.header("Explore the filtered records")
    st.write(f"Showing **{len(filtered_df):,}** product records after applying filters.")

    if filtered_df.empty:
        st.warning("No records to display. Adjust the filters in the sidebar.")
    else:
        search_text = st.text_input(
            "Search by product name or brand",
            placeholder="Enter a product name or brand...",
        )

        display_df = filtered_df.copy()
        if search_text.strip():
            search_mask = (
                display_df["product_name"].astype(str).str.contains(
                    search_text, case=False, na=False
                )
                | display_df["brands"].astype(str).str.contains(
                    search_text, case=False, na=False
                )
            )
            display_df = display_df[search_mask]

        display_columns = [
            "code",
            "product_name",
            "brands",
            "countries_en",
            "pnns_groups_1",
            "energy_kcal_100g",
            "fat_100g",
            "sugars_100g",
            "proteins_100g",
            "fiber_100g",
            "sodium_100g",
            "additives_n",
        ]
        friendly_names = {
            "code": "Product code",
            "product_name": "Product name",
            "brands": "Brand",
            "countries_en": "Country",
            "pnns_groups_1": "Food group",
            "energy_kcal_100g": "Energy (kcal/100g)",
            "fat_100g": "Fat (g/100g)",
            "sugars_100g": "Sugar (g/100g)",
            "proteins_100g": "Protein (g/100g)",
            "fiber_100g": "Fibre (g/100g)",
            "sodium_100g": "Sodium (g/100g)",
            "additives_n": "Additives (count)",
        }
        table_df = display_df[display_columns].head(1000).copy()
        table_df = table_df.rename(columns=friendly_names)

        numeric_display_columns = [
            "Energy (kcal/100g)",
            "Fat (g/100g)",
            "Sugar (g/100g)",
            "Protein (g/100g)",
            "Fibre (g/100g)",
            "Sodium (g/100g)",
        ]
        table_df[numeric_display_columns] = table_df[numeric_display_columns].round(2)

        st.dataframe(
            table_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Product code": st.column_config.TextColumn("Product code"),
                "Product name": st.column_config.TextColumn("Product name", width="large"),
                "Brand": st.column_config.TextColumn("Brand", width="medium"),
            },
        )
        st.caption(
            "The table displays up to 1,000 matching rows. Nutritional values are "
            "rounded to two decimal places for readability; the downloaded CSV "
            "retains the underlying values."
        )

        with st.expander("Descriptive statistics"):
            st.dataframe(
                filtered_df[
                    [
                        "energy_kcal_100g",
                        "fat_100g",
                        "saturated-fat_100g",
                        "carbohydrates_100g",
                        "sugars_100g",
                        "proteins_100g",
                        "fiber_100g",
                        "sodium_100g",
                        "additives_n",
                    ]
                ].describe().round(2),
                use_container_width=True,
            )

        with st.expander("Category-wise product counts (groupby)"):
            category_counts = (
                filtered_df.groupby("pnns_groups_1")
                .size()
                .reset_index(name="Product count")
                .sort_values("Product count", ascending=False)
            )
            st.dataframe(category_counts, use_container_width=True, hide_index=True)


# ---------------------------------------------------------
# 7. Mandatory visualisations
# ---------------------------------------------------------
with visual_tab:
    st.header("Visual analysis")
    if filtered_df.empty:
        st.warning("No data is available for visualisation with the current filters.")
    else:
        # Bar chart
        st.subheader("1. Bar chart – Average energy by classified food group")
        energy_by_group = (
            filtered_df[filtered_df["pnns_groups_1"] != "Unknown"]
            .groupby("pnns_groups_1")["energy_kcal_100g"]
            .mean()
            .reset_index(name="Average energy (kcal/100g)")
            .sort_values("Average energy (kcal/100g)", ascending=False)
        )
        if not energy_by_group.empty:
            bar_fig = px.bar(
                energy_by_group,
                x="pnns_groups_1",
                y="Average energy (kcal/100g)",
                title="Average energy content across classified food groups",
                labels={
                    "pnns_groups_1": "Food group",
                    "Average energy (kcal/100g)": "Average kcal per 100 g",
                },
            )
            bar_fig.update_layout(xaxis_tickangle=-35)
            st.plotly_chart(bar_fig, use_container_width=True)
            st.caption(
                "Interpretation: Taller bars represent food groups with higher "
                "average energy per 100 g in the currently filtered records."
            )
        else:
            st.info("There are no classified food groups in the current selection.")

        st.divider()

        # Line chart
        st.subheader("2. Line chart – Product records created over time")
        monthly_records = (
            filtered_df.dropna(subset=["record_month"])
            .groupby("record_month")
            .size()
            .reset_index(name="Number of product records")
            .sort_values("record_month")
        )
        if not monthly_records.empty:
            line_fig = px.line(
                monthly_records,
                x="record_month",
                y="Number of product records",
                markers=True,
                title="Number of product records created each month",
                labels={
                    "record_month": "Record creation month",
                    "Number of product records": "Number of records",
                },
            )
            line_fig.update_layout(
                xaxis=dict(
                    title="Record creation month",
                    tickformat="%b %Y",
                    tickangle=-35,
                    ticklabelmode="period",
                ),
                yaxis_title="Number of product records",
                hovermode="x unified",
            )
            st.plotly_chart(line_fig, use_container_width=True)
            st.caption(
                "Interpretation: This chart shows the number of database records "
                "created each month. It does not represent food sales or changes "
                "in actual food consumption."
            )
        else:
            st.info("No valid record dates are available for the current selection.")

        st.divider()

        # Scatter plot
        st.subheader("3. Scatter plot – Energy versus sugar")
        scatter_data = filtered_df.dropna(
            subset=["energy_kcal_100g", "sugars_100g"]
        )
        if len(scatter_data) > 5000:
            scatter_data = scatter_data.sample(5000, random_state=42)

        if not scatter_data.empty:
            scatter_fig = px.scatter(
                scatter_data,
                x="sugars_100g",
                y="energy_kcal_100g",
                color="pnns_groups_1",
                hover_data=["product_name", "brands"],
                title="Relationship between sugar and energy content",
                labels={
                    "sugars_100g": "Sugar (g per 100 g)",
                    "energy_kcal_100g": "Energy (kcal per 100 g)",
                    "pnns_groups_1": "Food group",
                },
                opacity=0.65,
            )
            st.plotly_chart(scatter_fig, use_container_width=True)
            st.caption(
                "Interpretation: Each point represents a product. The chart helps "
                "inspect whether products with more sugar also tend to have higher "
                "energy. It does not by itself prove causation."
            )
        else:
            st.info("There are not enough valid energy and sugar values to plot.")


# ---------------------------------------------------------
# 8. Insights
# ---------------------------------------------------------
with insights_tab:
    st.header("Key observations from the selected data")

    if filtered_df.empty:
        st.warning("No products match the current filters.")
    else:
        st.subheader("Highest average energy food groups")
        group_energy = (
            filtered_df[filtered_df["pnns_groups_1"] != "Unknown"]
            .groupby("pnns_groups_1")["energy_kcal_100g"]
            .mean()
            .sort_values(ascending=False)
        )

        if not group_energy.empty:
            top_group = group_energy.index[0]
            top_energy = group_energy.iloc[0]
            st.write(
                f"Among the classified groups currently displayed, **{top_group}** "
                f"has the highest average energy at **{top_energy:.1f} kcal per 100 g**."
            )
        else:
            st.write("There are no classified food groups in the current selection.")

        st.subheader("Highest average sugar food groups")
        group_sugar = (
            filtered_df[filtered_df["pnns_groups_1"] != "Unknown"]
            .groupby("pnns_groups_1")["sugars_100g"]
            .mean()
            .dropna()
            .sort_values(ascending=False)
        )

        if not group_sugar.empty:
            top_sugar_group = group_sugar.index[0]
            top_sugar = group_sugar.iloc[0]
            st.write(
                f"**{top_sugar_group}** has the highest average sugar content "
                f"among the classified groups in this selection "
                f"(**{top_sugar:.2f} g per 100 g**)."
            )

        st.subheader("Additives")
        avg_additives = filtered_df["additives_n"].mean()
        st.write(
            f"The average recorded additive count is **{avg_additives:.2f} per product** "
            "in the filtered records. The additive count alone does not determine "
            "whether a product is healthy or unhealthy."
        )

        st.subheader("Data quality note")
        unknown_share = (
            (filtered_df["pnns_groups_1"] == "Unknown").mean() * 100
            if len(filtered_df) else 0
        )
        st.write(
            f"**{unknown_share:.1f}%** of the filtered records have an "
            "`Unknown` food-group classification. Interpret group comparisons "
            "with this missing classification in mind."
        )

        st.divider()
        st.subheader("Download filtered data")
        csv_data = filtered_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download filtered records as CSV",
            data=csv_data,
            file_name="nutriscope_filtered_data.csv",
            mime="text/csv",
        )


# ---------------------------------------------------------
# 9. Footer
# ---------------------------------------------------------
st.divider()
st.caption(
    "NutriScope | Academic data analytics project | "
    "Dataset: Open Food Facts | Nutritional values are per 100 g"
)
