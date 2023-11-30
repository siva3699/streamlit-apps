# streamlit_app.py

from typing import TYPE_CHECKING
import streamlit as st
import altair as alt
import pandas as pd
import pyodbc
import os 
from datetime import datetime
import json


@st.cache_resource
def init_connection(show_spinner=False, ttl=1800):
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};SERVER="
        + os.getenv('server')
        + ";DATABASE="
        + os.getenv('database')
        + ";UID="
        + os.getenv('username')
        + ";PWD="
        + os.getenv('password')
    )





# Create the SQL connection to pets_db as specified in your secrets file.
conn = init_connection()


# Perform query.
# Uses st.cache_data to only rerun when the query changes or after 10 min.
def run_query(query):
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()

def run_query_without_data(query):
    with conn.cursor() as cur:
        cur.execute(query)
        cur.commit()


@st.cache_data(show_spinner=False, ttl=600)
def get_food_items():
    data = run_query("SELECT DISTINCT ITEM_NAME FROM [dbo].[BLOOD_GLUCOSE_DIET_FOOD]") 
    data = [ tuple(rec) for rec in data ]
    if len(data) > 0:
        return [ rec[0] for rec in data ]
    
try:
    run_query_without_data("""
    CREATE TABLE dbo.BLOOD_GLUCOSE_MONITOR_LOG 
    (MEASURE_DATE VARCHAR(100) NOT NULL, 
    MEASURE_TYPE VARCHAR(100) NOT NULL,
    MG_DL DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (MEASURE_DATE, MEASURE_TYPE)
    );""")
except Exception as e:
    pass

with st.sidebar:
    st.markdown("<h1 style='color: aqua;'>Blood Glucose Monitoring App</h1>", unsafe_allow_html=True)
    #st.title(':gray[Blood Glucose Monitoring App]')
    with st.form(key='my_form'):
        measure_date = st.date_input("Log Date ?", value="today", format="MM/DD/YYYY", key="measure_date_key")
        # Format the datetime object to 'YYYY-MM-DD'
        formatted_measure_date = measure_date.strftime('%Y-%m-%d')
        measure_type = st.selectbox('Measure Type ?',('Fasting', 'Breakfast', 'Lunch', 'Dinner'))
        mg_dl = st.number_input('MG/DL ?', min_value=70, max_value=250, step=10)
        measure_time  = st.time_input("Log Time ?", value="now", key="measure_time_key", step=300)
        measure_time_formatted = measure_time.strftime('%H:%M:%S')
        measure_date_time = f"{formatted_measure_date} {measure_time_formatted}"
        diet_items = get_food_items()
        diet_options = st.multiselect("Diet ?", options=diet_items, key="diet_key")
        diet_options_string = json.dumps(diet_options)
        submit_button = st.form_submit_button(label='Submit')

        if submit_button:
            run_query_without_data(f"DELETE FROM dbo.BLOOD_GLUCOSE_MONITOR_LOG WHERE MEASURE_DATE = '{measure_date_time}' AND MEASURE_TYPE = '{measure_type}'")
            run_query_without_data(f"""INSERT INTO dbo.BLOOD_GLUCOSE_MONITOR_LOG  
                            (MEASURE_DATE, MEASURE_TYPE, MG_DL) 
                            VALUES 
                            ( '{measure_date_time}', '{measure_type}', {mg_dl} )""" )
            if len(diet_options) > 0:
                for food in diet_options:
                    run_query_without_data(f"""INSERT INTO [dbo].[BLOOD_GLUCOSE_DIET_FOOD_LOG]
                            (MEASURE_DTTM, MEASURE_TYPE, ITEM_NAME) 
                            VALUES 
                            ( '{measure_date_time}', '{measure_type}', '{food}')""" )
            st.success('Measurement Recorded!!', icon="✅")



with st.sidebar:
    st.markdown("<h2 style='color: aqua;'>Remove a Measurement</h2>", unsafe_allow_html=True)
    with st.form(key='my_form1'):
        measure_date1 = st.date_input("Log Date ?", value="today", format="MM/DD/YYYY", key="measure_date_key1")
        # Format the datetime object to 'YYYY-MM-DD'
        formatted_measure_date1 = measure_date1.strftime('%Y-%m-%d')
        measure_type1 = st.selectbox('Measure Type ?',('Fasting', 'Breakfast', 'Lunch', 'Dinner'))
        measure_time1  = st.time_input("Log Time ?", value="now", key="measure_time_key1", step=300)
        measure_time_formatted1 = measure_time1.strftime('%H:%M:%S')
        measure_date_time1 = f"{formatted_measure_date1} {measure_time_formatted1}"
        submit_button1 = st.form_submit_button(label='Remove')

        if submit_button1:
            run_query_without_data(f"DELETE FROM dbo.BLOOD_GLUCOSE_MONITOR_LOG WHERE MEASURE_DATE = '{measure_date_time1}' AND MEASURE_TYPE = '{measure_type1}'")
            st.success('Measurement Removed!!', icon="✅")



with st.sidebar:
    st.markdown("<h2 style='color: aqua;'>Add New Diet To The Collection</h2>", unsafe_allow_html=True)
    with st.form(key='my_form2'):
        item_name      =  st.text_input('Diet Item', max_chars=200)
        submit_button2 = st.form_submit_button(label='Add')

        if submit_button2:
            run_query_without_data(f"DELETE FROM [dbo].[BLOOD_GLUCOSE_DIET_FOOD] WHERE LOWER(ITEM_NAME) = '{item_name.lower().strip()}'")
            run_query_without_data(f"""INSERT INTO dbo.[BLOOD_GLUCOSE_DIET_FOOD] 
                            (ITEM_NAME) 
                            VALUES 
                            ( '{item_name.capitalize()}' )""" )
            st.success('Diet Added!!', icon="✅")
            get_food_items.clear()
            st.rerun()


result = run_query("SELECT MEASURE_DATE, MEASURE_TYPE, CONVERT(VARCHAR(10), MG_DL) AS MG_DL FROM dbo.BLOOD_GLUCOSE_MONITOR_LOG") 

# Remove the parentheses and split by comma
results = [ tuple(rec) for rec in result ]

df = pd.DataFrame(results, columns=["MEASURE_DATE","MEASURE_TYPE","MG_DL"])
df['MEASURE_DATE'] = pd.to_datetime(df['MEASURE_DATE'], format="%Y-%m-%d %H:%M:%S")

edited_df = st.data_editor(df, num_rows="dynamic", hide_index=True)

line_chart = alt.Chart(df).mark_line().encode(
    x='MEASURE_DATE:T',
    y='MG_DL:Q',
    color='MEASURE_TYPE:N'
).properties(title=["Blood Glucose Levels Over Time",""]).configure_title(
    fontSize=20,
    color='gold'  
)

st.write("")
st.write("")
st.altair_chart(line_chart, use_container_width=True)




bar_chart = alt.Chart(df).mark_bar().encode(
    x='MEASURE_TYPE:N',
    y='mean(MG_DL):Q'
).properties(title=["Average Blood Glucose Level by Measurement Type", ""]).configure_title(
    fontSize=20,
    color='blueviolet' 
)


st.write("")
st.write("")
st.altair_chart(bar_chart, use_container_width=True)



histogram = alt.Chart(df).mark_bar().encode(
    alt.X("MG_DL:Q", bin=True),
    y='count()'
).properties(title=["Distribution of Blood Glucose Measurements",""]).configure_title(
    fontSize=20,
    color='darkorange' 
)

st.write("")
st.write("")
st.altair_chart(histogram, use_container_width=True)
