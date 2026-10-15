
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# ==========================================
# RetailPulse - Retail Business Analytics
# ==========================================

st.set_page_config(
    page_title="RetailPulse Analytics",
    page_icon="📊",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parent.parent


# ==========================================
# Data Loading
# ==========================================

def find_csv(filename):
    possible_paths = [
        BASE_DIR / "data" / "processed" / filename,
        BASE_DIR / "data" / filename,
        Path("E:/data/processed") / filename,
    ]

    for path in possible_paths:
        if path.exists():
            try:
                return pd.read_csv(path)
            except Exception as error:
                st.error(f"Could not read {filename}: {error}")
                return None

    # Support compressed sales CSV
    if filename == "retail_cleaned.csv":
        compressed_paths = [
            BASE_DIR / "data" / "processed" / "retail_cleaned.csv.gz",
            Path("E:/data/processed/retail_cleaned.csv.gz"),
        ]

        for path in compressed_paths:
            if path.exists():
                try:
                    return pd.read_csv(path, compression="gzip")
                except Exception as error:
                    st.error(f"Could not read compressed data: {error}")
                    return None

    return None



sales_df = find_csv("retail_cleaned.csv")
customer_df = find_csv("customer_segments.csv")
forecast_df = find_csv("demand_forecast.csv")


# ==========================================
# Page Header
# ==========================================

st.title("📊 RetailPulse – Retail Business Analytics")
st.caption(
    "Sales Performance | Customer Segmentation | Demand Forecasting"
)

# ==========================================
# Sidebar Navigation
# ==========================================

st.sidebar.title("RetailPulse")

page = st.sidebar.radio(
    "Select Dashboard",
    [
        "Overview",
        "Sales Analysis",
        "Customer Segmentation",
        "Demand Forecast",
        "Data Explorer",
    ],
)

if sales_df is None:
    st.error(
        "retail_cleaned.csv not found. "
        "Please check RetailPulse/data/processed/."
    )
    st.stop()


# ==========================================
# Prepare Sales Data
# ==========================================

sales_df.columns = sales_df.columns.str.strip()

if "InvoiceDate" not in sales_df.columns:
    st.error("InvoiceDate column is missing from retail_cleaned.csv.")
    st.stop()

sales_df["InvoiceDate"] = pd.to_datetime(
    sales_df["InvoiceDate"],
    errors="coerce"
)

if "Revenue" not in sales_df.columns:
    if {"Quantity", "Price"}.issubset(sales_df.columns):
        sales_df["Revenue"] = (
            pd.to_numeric(sales_df["Quantity"], errors="coerce")
            * pd.to_numeric(sales_df["Price"], errors="coerce")
        )
    else:
        st.error("Revenue or Quantity and Price columns are required.")
        st.stop()

sales_df["Revenue"] = pd.to_numeric(
    sales_df["Revenue"], errors="coerce"
)

if "Quantity" in sales_df.columns:
    sales_df["Quantity"] = pd.to_numeric(
        sales_df["Quantity"], errors="coerce"
    )

sales_df = sales_df.dropna(
    subset=["InvoiceDate", "Revenue"]
)

if sales_df.empty:
    st.error("No valid sales records are available.")
    st.stop()


# ==========================================
# Date Filter
# ==========================================

st.sidebar.subheader("Filters")

min_date = sales_df["InvoiceDate"].min().date()
max_date = sales_df["InvoiceDate"].max().date()

date_range = st.sidebar.date_input(
    "Select date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    key="sales_date_range",
)

filtered = sales_df.copy()

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range

    if start_date <= end_date:
        filtered = filtered[
            (filtered["InvoiceDate"].dt.date >= start_date)
            & (filtered["InvoiceDate"].dt.date <= end_date)
        ]
    else:
        st.sidebar.warning("Start date must be before end date.")


# -----------------------------
# Overview
# -----------------------------
if page == "Overview":
    st.header("Business Overview")

    # Calculate business metrics
    total_revenue = filtered["Revenue"].sum()

    total_orders = (
        filtered["Invoice"].nunique()
        if "Invoice" in filtered.columns
        else len(filtered)
    )

    total_customers = (
        filtered["Customer ID"].nunique()
        if "Customer ID" in filtered.columns
        else 0
    )

    total_units = (
        filtered["Quantity"].sum()
        if "Quantity" in filtered.columns
        else 0
    )

    # Display KPI cards only once
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric("Total Revenue", f"£{total_revenue:,.2f}")

    with c2:
        st.metric("Orders / Records", f"{total_orders:,}")

    with c3:
        st.metric("Unique Customers", f"{total_customers:,}")

    with c4:
        st.metric("Units Sold", f"{total_units:,.0f}")

    # Business Insights
    st.subheader("Business Insights")

    if not filtered.empty:
        monthly_sales = (
            filtered.set_index("InvoiceDate")["Revenue"]
            .resample("MS")
            .sum()
        )

        if not monthly_sales.empty:
            best_month = monthly_sales.idxmax()
            worst_month = monthly_sales.idxmin()

            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "Highest Revenue Month",
                    best_month.strftime("%B %Y"),
                    f"£{monthly_sales.max():,.2f}"
                )

            with col2:
                st.metric(
                    "Lowest Revenue Month",
                    worst_month.strftime("%B %Y"),
                    f"£{monthly_sales.min():,.2f}"
                )

            st.info(
                "Use the date filter in the sidebar to compare "
                "sales performance across different periods."
            )

            # Monthly Revenue Chart
            st.subheader("Monthly Revenue Trend")

            monthly_df = monthly_sales.rename(
                "Revenue"
            ).reset_index()

            fig = px.line(
                monthly_df,
                x="InvoiceDate",
                y="Revenue",
                markers=True,
                title="Monthly Revenue",
                labels={
                    "InvoiceDate": "Month",
                    "Revenue": "Revenue (£)"
                }
            )

            fig.update_layout(
                xaxis_title="Month",
                yaxis_title="Revenue (£)",
                hovermode="x unified"
            )

            st.plotly_chart(
                fig,
                width="stretch",
                key="overview_monthly_revenue_chart"
            )

        else:
            st.info("No monthly sales data available.")

    else:
        st.warning("No sales records found for the selected date range.")

        # Four KPI cards - only once
        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Total Revenue", f"£{total_revenue:,.2f}")
        c2.metric("Orders / Records", f"{total_orders:,}")
        c3.metric("Unique Customers", f"{total_customers:,}")
        c4.metric("Units Sold", f"{total_units:,.0f}")

        # Calculate monthly revenue once
        monthly_sales = (
            filtered.set_index("InvoiceDate")["Revenue"]
            .resample("MS")
            .sum()
            .rename("Revenue")
            .reset_index()
        )

        # Business Insights
        st.subheader("Business Insights")

        if not monthly_sales.empty:
            best_month = monthly_sales.loc[
                monthly_sales["Revenue"].idxmax()
            ]

            worst_month = monthly_sales.loc[
                monthly_sales["Revenue"].idxmin()
            ]

            col1, col2 = st.columns(2)

            col1.metric(
                "Highest Revenue Month",
                best_month["InvoiceDate"].strftime("%B %Y"),
                f"£{best_month['Revenue']:,.2f}",
            )

            col2.metric(
                "Lowest Revenue Month",
                worst_month["InvoiceDate"].strftime("%B %Y"),
                f"£{worst_month['Revenue']:,.2f}",
            )

        st.info(
            "Use the date filter in the sidebar to compare "
            "sales performance across different periods."
        )

        # Monthly chart - only once
        st.subheader("Monthly Revenue Trend")

        fig = px.line(
            monthly_sales,
            x="InvoiceDate",
            y="Revenue",
            markers=True,
            title="Monthly Revenue",
            labels={
                "InvoiceDate": "Month",
                "Revenue": "Revenue (£)",
            },
        )

        st.plotly_chart(
            fig,
            width="stretch",
            key="overview_monthly_revenue",
        )

        # Top countries
        if "Country" in filtered.columns:
            st.subheader("Top 10 Countries by Revenue")

            country_sales = (
                filtered.groupby("Country", as_index=False)["Revenue"]
                .sum()
                .nlargest(10, "Revenue")
            )

            fig_country = px.bar(
                country_sales,
                x="Country",
                y="Revenue",
                title="Revenue by Country",
                labels={"Revenue": "Revenue (£)"},
            )

            st.plotly_chart(
                fig_country,
                width="stretch",
                key="overview_country_revenue",
            )


# ==========================================
# Sales Analysis
# ==========================================

elif page == "Sales Analysis":

    st.header("Sales Analysis")

    if filtered.empty:
        st.warning("No sales records found for this date range.")

    else:
        total_revenue = filtered["Revenue"].sum()
        average_revenue = filtered["Revenue"].mean()

        c1, c2 = st.columns(2)
        c1.metric("Total Revenue", f"£{total_revenue:,.2f}")
        c2.metric("Average Record Revenue", f"£{average_revenue:,.2f}")

        monthly_sales = (
            filtered.set_index("InvoiceDate")["Revenue"]
            .resample("MS")
            .sum()
            .rename("Revenue")
            .reset_index()
        )

        st.subheader("Monthly Sales Trend")

        fig = px.line(
            monthly_sales,
            x="InvoiceDate",
            y="Revenue",
            markers=True,
            title="Monthly Revenue Trend",
        )

        st.plotly_chart(
            fig,
            width="stretch",
            key="sales_analysis_monthly",
        )

        if "StockCode" in filtered.columns:
            st.subheader("Top 10 Products by Revenue")

            product_sales = (
                filtered.groupby("StockCode", as_index=False)["Revenue"]
                .sum()
                .nlargest(10, "Revenue")
            )

            if "Description" in filtered.columns:
                descriptions = (
                    filtered.dropna(subset=["StockCode"])
                    .drop_duplicates("StockCode")
                    [["StockCode", "Description"]]
                )

                product_sales = product_sales.merge(
                    descriptions,
                    on="StockCode",
                    how="left",
                )

                product_sales["Product"] = (
                    product_sales["Description"]
                    .fillna(product_sales["StockCode"].astype(str))
                )
            else:
                product_sales["Product"] = (
                    product_sales["StockCode"].astype(str)
                )

            fig_product = px.bar(
                product_sales,
                x="Product",
                y="Revenue",
                title="Top Products by Revenue",
            )

            st.plotly_chart(
                fig_product,
                width="stretch",
                key="sales_top_products",
            )


# ==========================================
# Customer Segmentation
# ==========================================

elif page == "Customer Segmentation":

    st.header("Customer Segmentation")

    if customer_df is None:
        st.warning(
            "customer_segments.csv not found in data/processed."
        )

    else:
        customer_df.columns = customer_df.columns.str.strip()

        st.subheader("Customer Segment Data")
        st.dataframe(customer_df, width="stretch")

        if "Segment" in customer_df.columns:
            st.subheader("Customers by Segment")

            segment_counts = (
                customer_df["Segment"]
                .fillna("Unknown")
                .value_counts()
                .rename_axis("Segment")
                .reset_index(name="Customers")
            )

            fig_segment = px.bar(
                segment_counts,
                x="Segment",
                y="Customers",
                color="Segment",
                title="Customer Distribution",
            )

            st.plotly_chart(
                fig_segment,
                width="stretch",
                key="customer_segment_counts",
            )

            if "Total_Spending" in customer_df.columns:
                st.subheader("Revenue by Customer Segment")

                segment_revenue = (
                    customer_df.groupby("Segment", as_index=False)
                    ["Total_Spending"]
                    .sum()
                    .sort_values("Total_Spending", ascending=False)
                )

                fig_revenue = px.bar(
                    segment_revenue,
                    x="Segment",
                    y="Total_Spending",
                    title="Total Spending by Segment",
                )

                st.plotly_chart(
                    fig_revenue,
                    width="stretch",
                    key="customer_segment_revenue",
                )


# ==========================================
# Demand Forecast
# ==========================================

elif page == "Demand Forecast":

    st.header("Customer Demand Forecast")

    if forecast_df is None:
        st.warning(
            "demand_forecast.csv not found in data/processed."
        )

    else:
        forecast_df.columns = forecast_df.columns.str.strip()

        st.subheader("Forecast Data")
        st.dataframe(forecast_df, width="stretch")

        date_col = next(
            (
                col for col in ["Month", "InvoiceDate", "Date"]
                if col in forecast_df.columns
            ),
            None,
        )

        demand_col = next(
            (
                col for col in [
                    "Forecast_Demand",
                    "Forecast",
                    "Predicted_Demand",
                ]
                if col in forecast_df.columns
            ),
            None,
        )

        if date_col and demand_col:
            forecast_df[date_col] = pd.to_datetime(
                forecast_df[date_col],
                errors="coerce",
            )

            forecast_df[demand_col] = pd.to_numeric(
                forecast_df[demand_col],
                errors="coerce",
            )

            valid_forecast = forecast_df.dropna(
                subset=[date_col, demand_col]
            )

            if not valid_forecast.empty:
                fig_forecast = px.line(
                    valid_forecast,
                    x=date_col,
                    y=demand_col,
                    markers=True,
                    title="Demand Forecast",
                )

                st.plotly_chart(
                    fig_forecast,
                    width="stretch",
                    key="demand_forecast_chart",
                )
            else:
                st.info("No valid forecast values found.")
        else:
            st.info(
                "Could not identify forecast date and demand columns. "
                "Check the column names in your CSV."
            )


# ==========================================
# Data Explorer
# ==========================================

elif page == "Data Explorer":

    st.header("Retail Data Explorer")

    display_df = filtered.copy()

    st.write(f"Records found: {len(display_df):,}")

    search = st.text_input(
        "Search in displayed data",
        placeholder="Enter a product, country, invoice or customer",
    )

    if search:
        mask = display_df.astype(str).apply(
            lambda column: column.str.contains(
                search,
                case=False,
                na=False,
                regex=False,
            )
        ).any(axis=1)

        display_df = display_df[mask]

    st.dataframe(
        display_df,
        width="stretch",
        height=450,
    )

    csv_data = display_df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "Download filtered data as CSV",
        data=csv_data,
        file_name="retailpulse_filtered_data.csv",
        mime="text/csv",
    )


# ==========================================
# Footer
# ==========================================

st.sidebar.markdown("---")
st.sidebar.caption("RetailPulse | Business Intelligence Project")
