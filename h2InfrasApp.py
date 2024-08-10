#Libraries
#----dataFrame visualisation platform
import streamlit as st
#----raw Package
import numpy as np
import pandas as pd
#----data viz
import plotly.graph_objs as go
import plotly_express as px
import matplotlib.pyplot as plt
import seaborn as sns
#----dates
from datetime import date, timedelta
import calendar

#-------Version 3
#......+by Freeman Adane, August 10, 2024
#------------------------------------
#Page Descriptions
st.set_page_config(
    page_title = 'Hydrogen Production App',
    page_icon = '🚰',
    layout = 'wide'
)
#---------------------------------#
#-----Variables to be updated....
#----........assign a variable to data file for easy update, just change the year
datafilename="IEA Hydrogen Production Projects Database 2023-Readable.xlsx"
curr_date=date(2023,10,31) #Last download from IEA website
@st.cache(ttl=3600,allow_output_mutation=True)
def load_data():
    data=pd.read_excel(datafilename,
                   sheet_name="Projects",engine="openpyxl")
    #....some clean up
    data["Announced Size"]=data["Announced Size"].astype(str) #text&no.
    data=data.dropna(how='all', axis='columns') #drop extra NA columns
    data=data[data['Number'].notna()] #drop extra NA rows
    data["IEA zero-carbon estimated normalized capacity[nm³ H₂/hour]"]=(
    data["IEA zero-carbon estimated normalized capacity[nm³ H₂/hour]"].astype(float))
    data=data.rename(columns=
                     {'IEA zero-carbon estimated normalized capacity[nm³ H₂/hour]':
                      'Zero-carbon norm. capacity[nm³ H₂/hour]'})
    #.........for consistency all: FID, etc-> "Under Construction", Unknown, etc->Other 
    data.replace(to_replace=["FID/Construction", "FID"],value="Under Construction")
    data.replace(to_replace=["Other/Unknown", "Unknown"],value="Other")
    st.write(data)
    #----read country list and create dictionary for it and country code
    #.....for UX: keys-> Country name and values->ISO Code
    country_list=pd.read_excel(datafilename,
                   sheet_name="Countries",engine="openpyxl")
    country_code=dict(zip(country_list['Country'],country_list['ISO-3 Code']))
    return data,country_code
#---+function format numbers
def format_dec(t_var,ct):
    #---formating to 1 or decimal place
    if ct in ['No','N']:
        t_var="{:.1f}".format(t_var)
        tf=float(t_var)
    else:
        t_var="{:.1f}".format(t_var)
        tf=int(float(t_var))
    return tf
#---+Trending plotting function
def varable_plot(data_plot,var_plot,yax_tit,chart_tit):
  data_plot = data_plot.rename(columns={'Date online':'Date'})
  fig=px.line(data_plot,x='Date',y=var_plot,width=400, height=300)
  fig.update_layout(title='<b>'+chart_tit+'</b>',yaxis_title=yax_tit,paper_bgcolor='white',)
  fig.update_layout(template="seaborn")
  fig.layout.yaxis.tickformat='.1f'
  return st.plotly_chart(fig)
#---+Loading default data-World no, filteration...
data,country_code=load_data()
#.......Creating country list from dictionary, add empty country
country_list=pd.DataFrame(country_code.keys(),columns=['Country'])
no_select = pd.DataFrame([['-']], columns=['Country'])
country_list=pd.concat([no_select,country_list])

#---+Sidebar - Specify Country
with st.sidebar.header('Country Data'):
    country_name = st.sidebar.selectbox('Choose a country:',country_list['Country'].tolist())
    st.sidebar.write('**Tip**: click ✖️ when done')
#--------------------------------------------------------------------------------
#Dashboard.....
st.markdown("## Hydrogen Production Dashboard")
st.markdown("As of "+" **"+str(calendar.day_name[curr_date.weekday()])+"**, "+
            str(curr_date.strftime("**%B %d, %Y**")))  #** ** is for bold
if country_name == '-':
    st.markdown("<h1 style='text-align: center; color: black;'>Global</h1>",
                unsafe_allow_html=True)
else:
    st.markdown("<h1 style='text-align: center; color: blue;'>"+country_name+"</h1>",
                unsafe_allow_html=True)
    if country_code[country_name] not in list(data['Country']):
        st.error("👈  Sorry, choose different a **Country**")  
    else:
        data=data.groupby(['Country']).get_group(country_code[country_name])    
st.markdown("<hr/>",unsafe_allow_html=True) #for aesthetic

#---Dashboard column creation
db1, db2, db3 = st.columns(3)
with db1:
    total_count=data['Project Name'].count()
    st.metric("Number of Investments",str(total_count))
    #....get counts by grouping, get respective %, and reset to Status header
    gp_status=pd.DataFrame(data.groupby(['Status']).count())/total_count
    gp_status=gp_status.reset_index()
    #....first check for info and get Operational value
    if gp_status.query('Status == "Operational"').empty:
        st.metric("Number in Operation",str("N/A"))
    else:
        ops_no=float(gp_status['Project Name'].iloc[gp_status.query(
        'Status == "Operational"').index])*total_count
        st.metric("Number in Operation",str(format_dec(ops_no,'Yes')))
    #....pie for Status...
    fig = px.pie(gp_status,values='Project Name', names='Status',hole=.3,
                 width=450,height=400)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update(layout_title_text='<b>Investment Status</b>',
               layout_showlegend=False)
    st.markdown("<hr/>",unsafe_allow_html=True) #for aesthetic
    st.plotly_chart(fig)    
with db2:
    st.metric("Number of Technologies",str(len(data['Technology'].unique())))
    #....first check for info and get construction value
    if gp_status.query('Status == "Under construction"').empty:
        st.metric("Number Under Construction",str("N/A"))
    else:
        ops_no=float(gp_status['Project Name'].iloc[gp_status.query(
        'Status == "Under construction"').index])*total_count
        st.metric("Number Under Construction",str(format_dec(ops_no,'Yes')))
    st.markdown("<hr/>",unsafe_allow_html=True) #for aesthetic
    #.....Trending of Number in Operation ....
    if gp_status.query('Status == "Operational"').empty is False:
        varable_plot(data.groupby(['Status']).get_group('Operational').groupby(
        ['Date online']).count().reset_index(),'Project Name',
                 'No. of Investments','Annual Projects in Operation')
with db3:
    st.metric("Total Capacity [ktH2/yr]",str(format_dec(data['kt H2/y'].sum(),'No')))
    st.metric("Largest Capacity [ktH2/yr]",str(format_dec(data['kt H2/y'].max(),'No')))
    st.markdown("<hr/>",unsafe_allow_html=True) #for aesthetic
    #....get counts by grouping, reset to Status header, and decending sorted
    gp_tech=pd.DataFrame(data.groupby(['Technology']).count())
    gp_tech=gp_tech.reset_index().sort_values(by=['Project Name'],ascending=False)
    #....Top 5, assign is meant to remove index, plotly table can be used for pretty.
    #....Note, most common is "Other Electrolysis" which is vague, so ignoring....?
    top5Tech=pd.DataFrame(gp_tech['Technology'].iloc[0:5]).assign(empt='').set_index('empt')
    st.table(top5Tech.rename(columns={'Technology':'5 Most Common Tech'}))

#foot note on data source, "str" is to format the year to match other text
st.write("Data Source: IEA (",str(curr_date.year),"), Hydrogen Projects Database.")
