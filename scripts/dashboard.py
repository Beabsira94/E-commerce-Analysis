import streamlit as st
import pandas as pd
import plotly.express as px

# Load datasets
final_df = pd.read_csv('../data/final_dataset.csv')
monthly_df = pd.read_csv('../data/monthly_aggregation.csv')
weekly_df = pd.read_csv('../data/weekly_aggregation.csv')
daily_df = pd.read_csv('../data/daily_aggregation.csv')

# Convert 'InvoiceDate' to datetime format based on the specific format for each dataset
final_df['InvoiceDate'] = pd.to_datetime(final_df['InvoiceDate'], errors='coerce', format='%m/%d/%Y')  # Example: '1/6/2011'
monthly_df['InvoiceDate'] = pd.to_datetime(monthly_df['InvoiceDate'], errors='coerce', format='%Y-%m')  # Example: '2010-12'
weekly_df['InvoiceDate'] = pd.to_datetime(weekly_df['InvoiceDate'].str.split('/').str[0], errors='coerce', format='%Y-%m-%d')  # Extract start date from '2010-11-29/2010-12-05'
daily_df['InvoiceDate'] = pd.to_datetime(daily_df['InvoiceDate'], errors='coerce', format='%Y-%m-%d')  # Example: '2010-12-01'

# Drop rows with NaT in 'InvoiceDate' column
final_df = final_df.dropna(subset=['InvoiceDate'])
monthly_df = monthly_df.dropna(subset=['InvoiceDate'])
weekly_df = weekly_df.dropna(subset=['InvoiceDate'])
daily_df = daily_df.dropna(subset=['InvoiceDate'])

# Create KPIs for the dashboard
total_sales = final_df['Price'].sum()
total_transactions = final_df['InvoiceNo'].nunique()
average_order_value = total_sales / total_transactions
customer_segments = final_df['CustomerID'].nunique()

# Streamlit Layout
st.title("E-commerce Dashboard")
st.sidebar.header("Filters")

# Filters (for date range and CustomerID)
# Get min and max dates from the final_df without NaT values
min_date = final_df['InvoiceDate'].min()
max_date = final_df['InvoiceDate'].max()

# Ensure that min_date and max_date are not NaT
if pd.isna(min_date) or pd.isna(max_date):
    st.error("The dataset contains no valid dates.")
else:
    # Use date input widget with valid date range
    date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date])
    filtered_data = final_df[(final_df['InvoiceDate'] >= pd.to_datetime(date_range[0])) & 
                             (final_df['InvoiceDate'] <= pd.to_datetime(date_range[1]))]

    # Display KPIs
    st.subheader("Key Performance Indicators (KPIs)")
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Sales", f"€{total_sales:,.2f}")
    col2.metric("Number of Transactions", f"{total_transactions:,}")
    col3.metric("Avg. Order Value", f"€{average_order_value:,.2f}")
    col4.metric("Customer Segments", f"{customer_segments:,}")

    # Line Chart for Sales Trend
    st.subheader("Sales Trend Over Time")
    sales_trend = filtered_data.groupby('InvoiceDate')['Price'].sum().reset_index()
    fig = px.line(sales_trend, x='InvoiceDate', y='Price', title="Sales Over Time")
    st.plotly_chart(fig)

    # Bar Chart for Monthly Aggregation
    st.subheader("Monthly Sales")
    monthly_sales = monthly_df.groupby('InvoiceDate')['TotalRevenue'].sum().reset_index()
    fig_monthly = px.bar(monthly_sales, x='InvoiceDate', y='TotalRevenue', title="Monthly Sales")
    st.plotly_chart(fig_monthly)

    # Bar Chart for Weekly Aggregation
    st.subheader("Weekly Sales")

    # Ensure 'InvoiceDate' is not datetime before attempting to split
    if weekly_df['InvoiceDate'].dtype == 'O':  # Check if 'InvoiceDate' is object/string
        weekly_df['StartDate'] = pd.to_datetime(weekly_df['InvoiceDate'].str.split('/').str[0], errors='coerce')
    else:
        # If already datetime, extract the date as 'StartDate'
        weekly_df['StartDate'] = weekly_df['InvoiceDate']

    # Drop rows with NaT in 'StartDate'
    weekly_df = weekly_df.dropna(subset=['StartDate'])

    # Aggregate TotalRevenue by StartDate
    weekly_sales = weekly_df.groupby('StartDate')['TotalRevenue'].sum().reset_index()

    # Plot weekly sales as a bar chart
    fig_weekly = px.bar(weekly_sales, x='StartDate', y='TotalRevenue', title="Weekly Sales")
    st.plotly_chart(fig_weekly)

    # Bar Chart for Daily Aggregation
    st.subheader("Daily Sales")

    # Use the 'TotalRevenue' column for daily sales aggregation
    daily_sales = daily_df.groupby('InvoiceDate')['TotalRevenue'].sum().reset_index()

    # Plot daily sales as a bar chart
    fig_daily = px.bar(daily_sales, x='InvoiceDate', y='TotalRevenue', title="Daily Sales")
    st.plotly_chart(fig_daily)


    # Pie Chart for Customer Segmentation
    st.subheader("Customer Segmentation")

    # Group by 'Country' and count unique 'CustomerID'
    customer_segments = final_df.groupby('Country')['CustomerID'].nunique().reset_index()

    # Sort by 'CustomerID' in descending order and extract the top 8 countries
    top_12_countries = customer_segments.nlargest(12, 'CustomerID')

    # Identify the remaining countries and aggregate them under "Others"
    other_countries_total = customer_segments.loc[~customer_segments['Country'].isin(top_12_countries['Country']), 'CustomerID'].sum()
    compressed_data = pd.concat([top_12_countries, pd.DataFrame({'Country': ['Others'], 'CustomerID': [other_countries_total]})])

    # Plot the pie chart with compressed data
    fig_pie = px.pie(compressed_data, names='Country', values='CustomerID', title="Customer Segments by Country (Top 12 + Others)")
    st.plotly_chart(fig_pie)


    # Final Section - Display Filters and Interactivity
    st.subheader("Filter by Customer and Country")
    customer_filter = st.selectbox("Select Customer", final_df['CustomerID'].unique())
    country_filter = st.selectbox("Select Country", final_df['Country'].unique())

    filtered_data_customer = final_df[(final_df['CustomerID'] == customer_filter) & 
                                      (final_df['Country'] == country_filter)]

    st.write(filtered_data_customer)
