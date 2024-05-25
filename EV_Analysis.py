import pandas as pd
import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
from statsmodels.tsa.arima.model import ARIMA




file_path = 'C:/Users/amodi20/IEA Global EV Data 2024.csv'

df = pd.read_csv(file_path)

regions = df['region'].unique()
categories = df['category'].unique()
parameter = df['parameter'].unique()
mode = df['mode'].unique()
powertrain = df['powertrain'].unique()
year = df['year'].unique()
units = df['unit'].unique()
value = df['value'].unique()

# Dropping the rows where the year is 2025, 2030 or 2035

df = df[~df['year'].isin([2025, 2030, 2035])]
# print(df['year'].unique())


# Making a filtered Dataframe considering just the sales of the EVs
sales_df = df[(df['parameter'] == 'EV sales') & (df['region']!='World') & (df['region']!='Rest of the world')]
region_sales = sales_df.groupby('region')['value'].sum().reset_index()

# Making a filtered dataframe conidering only the vehicles that are either BEV or PHEV
bev_phev_df = sales_df[(sales_df['powertrain'] == 'BEV') | (sales_df['powertrain'] == 'PHEV')]
print(bev_phev_df['powertrain'].unique())

powertrain_counts = bev_phev_df['powertrain'].value_counts().reset_index()
powertrain_counts.columns = ['powertrain', 'count']

# Making a dataframe for the percentage share of the EVs
percent_df = df[df['unit'] == 'percent']




app = dash.Dash(__name__)

app.layout = html.Div([

    # Heading
    html.H1(
        "EV Sales Analysis",
        style={
            'color': '#ecf0f1',  # Light color for the heading
            'textAlign': 'center'
        }
    ),

    # 1st row
    html.Div([
        dcc.Graph(id='EV-distribution-donut-chart', className='six columns', style={'width': '45%', 'display': 'inline-block', 'margin': '5px'}),
        dcc.Graph(id='Percentage-share-pie-chart', className='six columns', style={'width': '45%', 'display': 'inline-block', 'margin': '5px'}),
        dcc.Graph(id='sales-distribution-bar-chart', className='six columns', style={'width': '45%', 'display': 'inline-block', 'margin': '5px'})
    ], style={'display': 'flex', 'justifyContent': 'center', 'margin': '10px', 'backgroundColor': '2c3e50'}),

    # 2nd row
    html.Div([
        dcc.Graph(id='year-on-year-sales')
    ], style={'margin': '10px'}),

    # 3rd row
    html.Div([
        dcc.Graph(id='bev-phev-line-chart')
    ], style={'margin': '10px'}),

    # 4th row
    html.Div([
        dcc.Graph(id='world-graph-forecasting')
    ], style={'margin': '10px'})
], style={'backgroundColor': '#2c3e50', 'color': '#ecf0f1', 'marginBottom': '10px'})

@app.callback(
    Output('sales-distribution-bar-chart', 'figure'), 
    Input('sales-distribution-bar-chart', 'id')
)

# Sales Distribution Bar Chart
def sales_bar_chart(input):
    top10regions = region_sales.sort_values(by='value', ascending=False).head(10)
    fig = px.bar(top10regions, x='region', y='value', title='Total Sales Distribution by Region')
    fig.update_layout(xaxis_title='Country', yaxis_title='Total EV Vehicles')
    return fig


@app.callback(
    Output('EV-distribution-donut-chart', 'figure'),
    Input('EV-distribution-donut-chart', 'id')
)

# BEV vs PHEV distribution donut chart
def EV_donut_chart(input):
    fig = px.pie(powertrain_counts, names='powertrain', values='count', hole=0.4, title='BEV vs PHEV Distribution')
    return fig


@app.callback(
    Output('Percentage-share-pie-chart', 'figure'),
    Input('Percentage-share-pie-chart', 'id')
)

# Vehicle wise percentage share of EVs
def percentage_pie_chart(input):
    fig = px.pie(percent_df, names='mode', values='value', title='Vehicle Wise Percentage Share of EVs')
    return fig

@app.callback(
    Output('year-on-year-sales', 'figure'),
    Input('year-on-year-sales', 'id')
)

# Year-on-year sales growth
def year_on_year_line_chart(input):

    regions_to_include = ['China', 'Europe', 'USA', 'EU27', 'Germany', 'France', 'United Kingdom', 'Norway', 'India']
    # filtered_df = df[df['region'].isin(regions_to_include)]
    filtered_df = sales_df[sales_df['region'].isin(regions_to_include)]
    filtered_df = filtered_df.groupby(['region', 'year']).mean().reset_index()
    pivot_df = filtered_df.pivot(index='year', columns='region', values='value').reset_index()

    fig = go.Figure()

    for region in regions_to_include:
        fig.add_trace(go.Scatter(
            x=pivot_df['year'],
            y=pivot_df[region],
            mode='lines+markers',
            name=region,
            line=dict(width=3)
        ))
    
    # Update layout
    fig.update_layout(
        title='EV Sales Over Years by Region',
        xaxis_title='Year',
        yaxis_title='Total Sales',
        template='plotly_white'
    )

    return fig


@app.callback(
    Output('bev-phev-line-chart', 'figure'),
    Input('bev-phev-line-chart', 'id')
)

def bev_v_phev_line_chart(input):

    grouped_df = bev_phev_df.groupby(['year', 'powertrain'])['value'].sum().reset_index()

    # Pivot the DataFrame to have years as the index and powertrains as columns
    pivot_df = grouped_df.pivot(index='year', columns='powertrain', values='value').reset_index()

    # Create the plot
    fig = go.Figure()

    for powertrain in pivot_df.columns[1:]:  # Skip the 'year' column
        fig.add_trace(go.Scatter(
            x=pivot_df['year'],
            y=pivot_df[powertrain],
            mode='lines+markers',
            name=powertrain,
            line=dict(width=3)
        ))

    # Update layout
    fig.update_layout(
        title='Total Sales of BEV vs PHEV Over Years',
        xaxis_title='Year',
        yaxis_title='Total Sales',
        template='plotly_white'
    )

    # Show the plot
    return fig


def world_graph_forecasting(df):
    # Filter and pivot the DataFrame
    regions_to_include = ['World']
    filtered_df = df[df['region'].isin(regions_to_include)]
    filtered_df = filtered_df.groupby(['region', 'year']).mean().reset_index()
    pivot_df = filtered_df.pivot(index='year', columns='region', values='value').reset_index()

    # Prepare the DataFrame for ARIMA
    arima_df = pivot_df.set_index('year')['World']

    # Print some debugging information
    print("ARIMA DataFrame:")
    print(arima_df.head())

    # Fit ARIMA model
    model = ARIMA(arima_df, order=(1, 1, 1))
    fitted_model = model.fit()

    # Print some debugging information
    print("ARIMA Model Summary:")
    print(fitted_model.summary())

    # Make future predictions
    forecast = fitted_model.forecast(steps=5)

    print("Forecast Data:")
    print(forecast)

    # Plot the historical data and forecast
    forecast_years = list(range(2024, 2031))

# Plot the historical data and forecast
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=pivot_df['year'],  # Use pivot_df for historical data
        y=pivot_df['World'],
        mode='lines+markers',
        name='Historical Data',
        line=dict(width=3)
    ))
    fig.add_trace(go.Scatter(
        x=forecast_years,  # Forecasted years as a list
        y=forecast.values,
        mode='lines+markers',
        name='Forecast',
        line=dict(width=3)
    ))
        
    # Update layout
    fig.update_layout(
        title='EV Sales Over Years with Forecast',
        xaxis_title='Year',
        yaxis_title='Total Sales',
        template='plotly_white',
        xaxis=dict(range=[2010, 2030]),  # Extend the range of years to include forecasted years
        yaxis=dict(range=[0, forecast.max() * 1.2])  # Adjust the range of y-axis
    )

    print("Figure Object:")
    print(fig)

    return fig

@app.callback(
    Output('world-graph-forecasting', 'figure'),
    Input('world-graph-forecasting', 'id')
)

def update_world_graph_forecasting(_):
    return world_graph_forecasting(df)





if __name__ == '__main__':
    app.run_server(debug=True)