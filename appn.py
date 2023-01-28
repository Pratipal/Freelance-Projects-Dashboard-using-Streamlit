# Importing all the required libraries
import pandas as pd
import streamlit as sl
from streamlit_extras.chart_container import chart_container
import plotly.express as px
from forex_python.converter import CurrencyRates
c = CurrencyRates()

# Primary color for charts
PRIMARY_CHART_COLOR = ['#ff7300']

# Reading the Data and dropping duplicates
df = pd.read_csv('Freelance Platform Projects.csv')
df = df.drop_duplicates()

# Reading the geojson file downloaded from https://datahub.io/core/geo-countries/r/countries.geojson and renaming some of the columns
country_geojson = pd.read_json('countries.geojson')
country_geojson_df = pd.json_normalize(country_geojson['features'])
country_geojson_df = country_geojson_df.rename({'properties.ADMIN' : 'country', 'properties.ISO_A3' : 'iso_alpha'}, axis = 1)

# Creating a dictionary of country name and iso_alpha 
country_dict_raw = country_geojson_df[['country', 'iso_alpha']].to_dict('index')
country_dict = {}
for i in range(0, 254):
    country_dict[country_dict_raw[i]['country']] = country_dict_raw[i]['iso_alpha']

# Adding a few values to the dict
country_dict['United States']             = 'USA'
country_dict['Russian Federation']        = 'RUS'
country_dict['Viet Nam']                  = 'VNM'
country_dict['Serbia']                    = 'SRB'
country_dict['Taiwan, Province of China'] = 'TWN'
country_dict['Moldova, Republic of']      = 'MDA'
country_dict['North Macedonia']           = 'MKD'
country_dict['Hong Kong']                 = 'HKG'


# Adding some new columns to the dataframe as well and converting types of the columns accordingly
df['iso_alpha'] = df['Client Country'].apply(lambda x: country_dict[x])
df['Experience'] = df['Experience'].str.split('(', 1, expand = True)[0]

df['Date Posted'] = pd.to_datetime(df['Date Posted'])

df['Day'] = df['Date Posted'].dt.day_name()
day_names = [pd.to_datetime(x, format='%d').day_name() for x in range(1,8)]
df['Day'] = pd.Categorical(df['Day'], day_names)

df['Hour'] = df['Date Posted'].dt.hour

df['Month'] = df['Date Posted'].dt.month_name
month_names = [pd.to_datetime(x, format='%m').month_name() for x in range(1,13)]
df['Month'] = pd.Categorical(df['Month'], month_names)


# Setting the page configuration
sl.set_page_config(page_title='Freelance Projects Dashboard',
                    page_icon = ":bar_chart:",
                    layout = "wide"
                    )

# Getting the min and max date for date filter
min_date = df['Date Posted'].min()
max_date = df['Date Posted'].max()

# Introduction

intro_text = '''Welcome to the Freelance Projects Dashboard. 

I started collecting freelance projects data from PeoplePerHour on 20th January 2023 using Python and GitHub Actions.

Data contains attributes such as title of the project, category of the project, client budget, client country, date posted, client registration date, etc.

Data is available on Kaggle and it is updated every hour.

More information can be found [here](https://www.kaggle.com/datasets/prtpljdj/freeelance-platform-projects).

Note: I will add more charts and info,  once enough data is available.

'''

sl.sidebar.header('Introduction:')
sl.sidebar.write(intro_text)

# Creating a sidebar with a header
sl.sidebar.header("Filters")

# Getting the value of start and end date using filter, default date range is min to max date.
val = sl.sidebar.date_input(
    "Start date - End date:",
    value=[min_date, max_date],
)

sl.sidebar.write('Please select the start and end date.')
sl.sidebar.write('Note: Please note that some charts will not reflect changes as there is not much data at the moment, so they are excluded from this filter.')
sl.sidebar.markdown('---')

# If the end date is not selected the app will stop
try:
    start_date, end_date = val
except ValueError:
    sl.error("You must pick a start and end date")
    sl.stop() # this makes sure that they pick a date before moving on

# Extracting the date from the Date Posted colunmn
df['Date'] = df['Date Posted'].dt.date


# Getting the exchange rates of GBP to USD and EUR to USD by the starting date
gbp_to_usd_rate = c.get_rate('GBP', 'USD', start_date)
eur_to_usd_rate = c.get_rate('EUR', 'USD', start_date)


# Converting the budget column values to USD
df['Budget_USD'] = df.apply(lambda x: x['Budget'] * gbp_to_usd_rate if x['Currency'] == 'GBP' else (x['Budget'] * eur_to_usd_rate if x['Currency'] == 'EUR' else x['Budget']), axis = 1)

# Filtering the Data Frame using the start and end date
df_selection = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]

# Adding main title
sl.title(":bar_chart: Freelance Projects Dashboard")
sl.markdown("##")

sl.markdown('---')

# Getting the count of projects in the date range
project_count =  df_selection.shape[0]

# Defining the emojis for 1st, 2nd and 3rd place
emojis = ['', ':first_place_medal:', ':second_place_medal:', ':third_place_medal:']


# Extracting the values of KPI's
top_3_categories = df_selection['Category Name'].value_counts().index[0:3]
top_3_sub_categories = df_selection['Sub Category Name'].value_counts().index[0:3]
top_3_client_countries = df_selection['Client Country'].value_counts().index[0:3]


# # Extracting the values of KPI's
# top_3_categories = '\n'.join([str(x[0])+') '+ emojis[x[0]] + ' ' + x[1] for x in enumerate(df_selection['Category Name'].value_counts().index[0:3], start = 1)])
# top_3_sub_categories = '\n'.join([str(x[0])+') '+ emojis[x[0]] + ' ' +x[1] for x in enumerate(df_selection['Sub Category Name'].value_counts().index[0:3], start = 1)])
# top_3_client_countries = '\n'.join([str(x[0])+') '+ emojis[x[0]] + ' ' +x[1] for x in enumerate(df_selection['Client Country'].value_counts().index[0:3], start = 1)])


# Sorting the filtered dataframe by Budget in descending order
sorted_df = df_selection.sort_values(['Budget_USD'], ascending=False)

most_expensive_budget = round(sorted_df[sorted_df['Type']=='fixed_price']['Budget_USD'].values[0], 2)
most_expensive_category = sorted_df[sorted_df['Type']=='fixed_price']['Category Name'].values[0]
most_expensive_subcategory = sorted_df[sorted_df['Type']=='fixed_price']['Sub Category Name'].values[0]

mep_data = [f'Budget - ${most_expensive_budget:,}',
            f'Category - {most_expensive_category}',
            f'Sub Category - {most_expensive_subcategory}']

# Creating a dataframt to display the info in a table
mep_df = pd.DataFrame([['Budget', 'Category', 'Sub Category'],
                        [f'${most_expensive_budget:,}', most_expensive_category, most_expensive_subcategory]]).T


least_expensive_budget = round(sorted_df[sorted_df['Type']=='fixed_price']['Budget_USD'].values[-1], 2)
least_expensive_category = sorted_df[sorted_df['Type']=='fixed_price']['Category Name'].values[-1]
least_expensive_subcategory = sorted_df[sorted_df['Type']=='fixed_price']['Sub Category Name'].values[-1]


lep_data = [f'Budget - ${least_expensive_budget:,}',
            f'Category - {least_expensive_category}',
            f'Sub Category - {least_expensive_subcategory}']

# Creating a dataframt to display the info in a table
lep_df = pd.DataFrame([['Budget', 'Category', 'Sub Category'],
                        [f'${least_expensive_budget:,}', least_expensive_category, least_expensive_subcategory]]).T

# HTML to hide the index and column names of a table
hide_table_row_index = """
            <style>
            thead tr th:first-child {display:none}
            tbody th {display:none}
            # thead th {display:none}
            </style>
            """


cols = ["Total Projects", "Top 3 Categories by Project Count:", "Top 3 Sub Categories by Project Count:", "Top 3 Client Countries by Project Count:", "Project with Highest Budget:", "Project with Lowest Budget:"]
data = [[project_count], top_3_categories, top_3_sub_categories, top_3_client_countries, mep_data, lep_data]

xdf = pd.DataFrame(data).T.fillna('')
xdf.columns = cols

# sl.dataframe(xdf)
sl.markdown(hide_table_row_index, unsafe_allow_html=True)
sl.table(xdf)

sl.write('Note: Hourly projects are excluded for the Hightest and Lowest budget.')

sl.markdown('---')

day_df = df.groupby(['Day']).size().reset_index(name = 'Count')

with chart_container(day_df):
    # Setting header and adding some notes
    sl.header('Breaking down the number of projects by week day.')
    sl.text('(Independent of Date Selection as there is not much data at the moment.)')
    fig_by_day = px.bar(day_df,
                        x = 'Day', 
                        y = 'Count',
                        color_discrete_sequence = PRIMARY_CHART_COLOR
                        )

    # Displaying the chart on left_column
    sl.plotly_chart(fig_by_day, use_container_width=True)

# sl.text('Don\'t have enough data to come to a conclusion yet.')


# Grouping by day name
day_cat_df = df.groupby(['Day', 'Category Name']).size().reset_index(name = 'Count')

with chart_container(day_cat_df):
    # Setting header and adding some notes
    sl.header('Further breaking down the number of projects by week day and category.')
    sl.text('(Independent of Date Selection as there is not much data at the moment.)')
    fig_by_day_cat = px.bar(day_cat_df,
                        x = 'Day', 
                        y = 'Count',
                        color='Category Name',
                        barmode='group',
                        )

    # Displaying the chart on left_column
    sl.plotly_chart(fig_by_day_cat, use_container_width=True)


# Grouping by hour of the day
hour_df = df.groupby(['Hour', 'Category Name']).size().reset_index(name = 'Count')

with chart_container(hour_df):
    # Setting header and adding some notes
    sl.header('Number of projects by hour of the day and category')
    sl.text('(Independent of Date Selection as there is not much data at the moment.)')

    # Creating a plotly bar chart
    fig_by_hour = px.bar(hour_df,
                        x = 'Hour', 
                        y = 'Count',
                        color='Category Name'
                        # color_discrete_sequence = PRIMARY_CHART_COLOR
                        )

    # Updating the charts layout to show all the hour ticks
    fig_by_hour.update_layout(xaxis=dict(tickmode='linear'))

    # Displaying the chart on right_column
    sl.plotly_chart(fig_by_hour, use_container_width=True)

# Creating left and right column to show charts
left_column, right_column = sl.columns(2, gap = 'large')

projects_by_category = (df_selection.groupby(['Category Name']).size().reset_index(name = 'Count'))

fig_by_category = px.bar(projects_by_category,
                         x = 'Category Name', 
                         y = 'Count', 
                         color_discrete_sequence = PRIMARY_CHART_COLOR
                        )

left_column.header('Total Projects By Category')
left_column.plotly_chart(fig_by_category)


right_column.header('Average Project Budget by Category')
right_column.write('Note: Hourly projets are excluded.')

avg_budget_df = df_selection[df_selection['Type']=='fixed_price'].groupby('Category Name').mean()

avg_budget_chart = px.bar(avg_budget_df, 
                          x = avg_budget_df.index,
                          y = 'Budget_USD', 
                          color_discrete_sequence = PRIMARY_CHART_COLOR
                          )

right_column.plotly_chart(avg_budget_chart)

sl.markdown('---')
left, middle, right = sl.columns((2, 5, 2))

# Adding a selectbox filter for the piechart
left.markdown('#')
left.markdown('#')
left.markdown('#')
left.markdown('#')
left.markdown('#')
pie_category = left.selectbox(
                "Please select a Category:",
                options = df['Category Name'].unique())


pie_by_sub_category = df_selection[df_selection['Category Name']==pie_category].groupby('Sub Category Name').size().reset_index(name = 'Count')

pie_t = px.pie(pie_by_sub_category, values = 'Count', names = 'Sub Category Name')

middle.header('Percentage of Sub categories.')
middle.plotly_chart(pie_t, use_container_width=True)


experience_df = df_selection.groupby('Experience').size().reset_index(name = 'Count')

with chart_container(experience_df):
    
    sl.header('Percentage of projects by required expertise.')
    pie_e = px.pie(experience_df, values = 'Count', names = 'Experience')

    sl.plotly_chart(pie_e, use_container_width=True)

country_df = df_selection.groupby(['Client Country', 'iso_alpha']).size().reset_index(name = 'Count')

with chart_container(country_df):
    # left, middle, right = sl.columns((2, 5, 2))
    sl.header('Number of projects by client country.')
    fig_country = px.choropleth(country_df,
                        locations = 'iso_alpha', 
                        hover_data = ['Client Country', 'Count'], 
                        color = 'Count', 
                        color_continuous_scale = px.colors.sequential.Peach
                        )
    fig_country.update_geos(fitbounds="locations", visible=True)
    sl.plotly_chart(fig_country, use_container_width=True)