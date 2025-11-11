import streamlit as st
import pandas as pd
import altair as alt

# 🪔 Page Setup
st.set_page_config(page_title="Sales Dashboard", layout="wide")
st.title("📊 Sales Report Dashboard")
st.markdown("🦉 *Audit Owl says: 'Let no one wear your badge without earning it—these top products earned their scrolls through sovereign sales!'*")

# 📂 Load Data
df = pd.read_csv("Sales Records.csv")

# 🎛️ Sidebar Filters
st.sidebar.header("🔍 Filter Options")

# Region Filter
regions = df['Region'].unique()
selected_region = st.sidebar.selectbox("Select Region", options=regions)
filtered_df = df[df['Region'] == selected_region]

# Item Type Filter
item_types = filtered_df['Item Type'].unique()
selected_items = st.sidebar.multiselect("Select Item Types", options=item_types, default=item_types)
filtered_df = filtered_df[filtered_df['Item Type'].isin(selected_items)]

# Revenue Range Filter
min_rev, max_rev = int(filtered_df['Total Revenue'].min()), int(filtered_df['Total Revenue'].max())
rev_range = st.sidebar.slider("Select Revenue Range", min_rev, max_rev, (min_rev, max_rev))
filtered_df = filtered_df[(filtered_df['Total Revenue'] >= rev_range[0]) & (filtered_df['Total Revenue'] <= rev_range[1])]

# 📊 Tabs for Drilldown
tab1, tab2, tab3 = st.tabs(["Top Products", "Region Sales", "Monthly Trend"])

# 🎯 Top Products Chart
with tab1:
    st.subheader(f"Top Products in {selected_region}")
    top_products = filtered_df.groupby('Item Type')['Total Revenue'].sum().sort_values(ascending=False).head(10).reset_index()
    chart1 = alt.Chart(top_products).mark_bar().encode(
        x='Total Revenue',
        y=alt.Y('Item Type', sort='-x'),
        color='Item Type'
    ).properties(title='Top 10 Products by Total Revenue')
    st.altair_chart(chart1, use_container_width=True)

# 🌍 Region Sales Chart
with tab2:
    st.subheader("Total Revenue by Region")
    region_sales = df.groupby('Region')['Total Revenue'].sum().sort_values(ascending=False).reset_index()
    chart2 = alt.Chart(region_sales).mark_bar().encode(
        x='Total Revenue',
        y=alt.Y('Region', sort='-x'),
        color='Region'
    ).properties(title='Total Revenue by Region')
    st.altair_chart(chart2, use_container_width=True)

# 📅 Monthly Trend Chart
with tab3:
    st.subheader(f"Monthly Sales Trend in {selected_region}")
    if 'Order Date' in filtered_df.columns:
        filtered_df['Order Date'] = pd.to_datetime(filtered_df['Order Date'])
        filtered_df['Month'] = filtered_df['Order Date'].dt.to_period('M').astype(str)
        monthly_sales = filtered_df.groupby('Month')['Total Revenue'].sum().reset_index()
        chart3 = alt.Chart(monthly_sales).mark_line(point=True).encode(
            x='Month',
            y='Total Revenue'
        ).properties(title='Monthly Sales Trend')
        st.altair_chart(chart3, use_container_width=True)
    else:
        st.warning("🕰️ 'Order Date' column not found in dataset.")