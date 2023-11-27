# streamlit_app.py

from typing import TYPE_CHECKING
import streamlit as st
from sqlalchemy import text
import altair as alt
import pandas as pd
from sqlalchemy import create_engine
import pyodbc
import os 
from datetime import datetime


# Initialize connection.
# Uses st.cache_resource to only run once.
# @st.cache_resource
# def init_connection():
#     return pyodbc.connect(
#         "DRIVER={ODBC Driver 17 for SQL Server};SERVER="
#         + st.secrets["server"]
#         + ";DATABASE="
#         + st.secrets["database"]
#         + ";UID="
#         + st.secrets["username"]
#         + ";PWD="
#         + st.secrets["password"]
#     )

@st.cache_resource
def init_connection():
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

# Insert some data with conn.session.
with conn.session as s:
    #s.execute(text("DROP TABLE IF EXISTS BLOOD_GLUCOSE_MONITOR_LOG;"))
    s.execute(text("""
    CREATE TABLE IF NOT EXISTS dbo.BLOOD_GLUCOSE_MONITOR_LOG 
    (MEASURE_DATE VARCHAR(100) NOT NULL, 
    MEASURE_TYPE VARCHAR(100) NOT NULL,
    MG_DL DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (MEASURE_DATE, MEASURE_TYPE)
    );""")
    )
    # s.execute(text('DELETE FROM pet_owners;'))
    # pet_owners = {'jerry': 'fish', 'barbara': 'cat', 'alex': 'puppy'}
    # for k in pet_owners:
    #     s.execute(
    #         text('INSERT INTO pet_owners (person, pet) VALUES (:owner, :pet);'),
    #         params=dict(owner=k, pet=pet_owners[k])
    #     )
    s.commit()



with st.sidebar:
    st.markdown("<h1 style='color: aqua;'>Blood Glucose Monitoring App</h1>", unsafe_allow_html=True)
    #st.title(':gray[Blood Glucose Monitoring App]')
    with st.form(key='my_form'):
        measure_date = st.date_input("Log Date ?", value="today", format="MM/DD/YYYY", key="measure_date_key")
        # Format the datetime object to 'YYYY-MM-DD'
        formatted_measure_date = measure_date.strftime('%Y-%m-%d')
        measure_type = st.selectbox('Measure Type ?',('Fasting', 'Breakfast', 'Lunch', 'Dinner'))
        mg_dl = st.number_input('MG/DL ?', min_value=70, max_value=250, step=10)
        submit_button = st.form_submit_button(label='Submit')

        if submit_button:
            run_query_without_data(f"DELETE FROM dbo.BLOOD_GLUCOSE_MONITOR_LOG WHERE MEASURE_DATE = '{measure_date}' AND MEASURE_TYPE = '{measure_type}'")
            run_query_without_data(f"""INSERT INTO dbo.BLOOD_GLUCOSE_MONITOR_LOG  
                            (MEASURE_DATE, MEASURE_TYPE, MG_DL) 
                            VALUES 
                            ( '{formatted_measure_date}', '{measure_type}', {mg_dl} )""" )


result = run_query(text("SELECT * FROM dbo.BLOOD_GLUCOSE_MONITOR_LOG"))   


st.dataframe(result, hide_index=True)


df = pd.DataFrame(result.fetchall(), columns=result.keys())
df['MEASURE_DATE'] = pd.to_datetime(df['MEASURE_DATE'])



line_chart = alt.Chart(df).mark_line().encode(
    x='MEASURE_DATE:T',
    y='MG_DL:Q',
    color='MEASURE_TYPE:N'
).properties(title=["Blood Glucose Levels Over Time",""]).configure_title(
    fontSize=20,
    color='gold'  # You can change 'green' to any desired color
)

st.write("")
st.write("")
st.altair_chart(line_chart, use_container_width=True)




bar_chart = alt.Chart(df).mark_bar().encode(
    x='MEASURE_TYPE:N',
    y='mean(MG_DL):Q'
).properties(title=["Average Blood Glucose Level by Measurement Type", ""]).configure_title(
    fontSize=20,
    color='blueviolet'  # You can change 'green' to any desired color
)


st.write("")
st.write("")
st.altair_chart(bar_chart, use_container_width=True)



histogram = alt.Chart(df).mark_bar().encode(
    alt.X("MG_DL:Q", bin=True),
    y='count()'
).properties(title=["Distribution of Blood Glucose Measurements",""]).configure_title(
    fontSize=20,
    color='darkorange'  # You can change 'green' to any desired color
)

st.write("")
st.write("")
st.altair_chart(histogram, use_container_width=True)
