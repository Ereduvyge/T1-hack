import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import io
import base64
import plotly.express as px

# Create Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

def concatenate_files(contents_list, filenames):
    if contents_list is not None:
        dfs = []
        for contents, filename in zip(contents_list, filenames):
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), sep=';', header=1)
            dfs.append(df)
        if dfs:
            concatenated_df = pd.concat(dfs, ignore_index=True)
            return concatenated_df
    return pd.DataFrame()

# Main layout
app.layout = dbc.Container([
    html.H1("Дашборд", style={'margin': '10px'}),
    html.Hr(),
    # Store for sharing data between callbacks
    dcc.Store(id='data-store', data=None),
    dbc.Row([
        dbc.Col([
            html.H4("Загрузите файлы заданий"),
            dcc.Upload(
                id='upload-tasks',
                children=html.Div([
                    'Перетащите или ',
                    html.A('Выберите файлы')
                ]),
                multiple=True,
                style={
                    'width': '100%', 'height': '60px', 'lineHeight': '60px',
                    'borderWidth': '1px', 'borderStyle': 'dashed',
                    'borderRadius': '5px', 'textAlign': 'center',
                    'margin': '10px'
                }
            ),
            html.Div(id='output-tasks-upload', style={'margin-top': '10px'})
        ], width=4),
        dbc.Col([
            html.H4("Загрузите файлы с историей"),
            dcc.Upload(
                id='upload-history',
                children=html.Div([
                    'Перетащите или ',
                    html.A('Выберите файлы')
                ]),
                multiple=True,
                style={
                    'width': '100%', 'height': '60px', 'lineHeight': '60px',
                    'borderWidth': '1px', 'borderStyle': 'dashed',
                    'borderRadius': '5px', 'textAlign': 'center',
                    'margin': '10px'
                }
            ),
            html.Div(id='output-history-upload', style={'margin-top': '10px'})
        ], width=4),
        dbc.Col([
            html.H4("Загрузите файлы спринтов"),
            dcc.Upload(
                id='upload-sprints',
                children=html.Div([
                    'Перетащите или ',
                    html.A('Выберите файлы')
                ]),
                multiple=True,
                style={
                    'width': '100%', 'height': '60px', 'lineHeight': '60px',
                    'borderWidth': '1px', 'borderStyle': 'dashed',
                    'borderRadius': '5px', 'textAlign': 'center',
                    'margin': '10px'
                }
            ),
            html.Div(id='output-sprints-upload', style={'margin-top': '10px'})
        ], width=4),
    ]),
    dbc.Button("Получить данные", id='process-button', color='primary', style={'margin': '20px'}),
    html.Div(id='output-data-upload'),
    html.Hr(),
    # Placeholders for dropdown and graphs
    html.Div([
        html.H1("Sprint Dashboard"),
        html.Br(),
        dcc.Dropdown(
            id="sprint_selector",
            options=[],
            value=None,
            multi=False
        ),
        dcc.Graph(id="status_chart", figure={}),
        dcc.Graph(id="time_chart", figure={}),
        dcc.Graph(id="priority_chart", figure={}),
    ], style={'display': 'none'}, id='dashboard-content'),
])

# Callback to update file upload statuses
@app.callback(
    Output('output-tasks-upload', 'children'),
    Output('output-history-upload', 'children'),
    Output('output-sprints-upload', 'children'),
    Input('upload-tasks', 'filename'),
    Input('upload-history', 'filename'),
    Input('upload-sprints', 'filename')
)
def update_file_upload_status(tasks_filenames, history_filenames, sprints_filenames):
    tasks_files = ', '.join(tasks_filenames) if tasks_filenames else 'Файлы еще не загружены'
    history_files = ', '.join(history_filenames) if history_filenames else 'Файлы еще не загружены'
    sprints_files = ', '.join(sprints_filenames) if sprints_filenames else 'Файлы еще не загружены'
    
    return f"Файлы заданий: {tasks_files}", f"Файлы с историей: {history_files}", f"Файлы спринтов: {sprints_files}"

# Callback to process uploaded files and update the dashboard
@app.callback(
    Output('output-data-upload', 'children'),
    Output('data-store', 'data'),
    Output('sprint_selector', 'options'),
    Output('sprint_selector', 'value'),
    Output('dashboard-content', 'style'),
    Input('process-button', 'n_clicks'),
    State('upload-tasks', 'contents'),
    State('upload-history', 'contents'),
    State('upload-sprints', 'contents'),
    State('upload-tasks', 'filename'),
    State('upload-history', 'filename'),
    State('upload-sprints', 'filename'),
)
def upload_output(n_clicks, tasks_contents, history_contents, sprints_contents,
                  tasks_filenames, history_filenames, sprints_filenames):
    if n_clicks is None:
        return 'После загрузки нажмите получить данные', None, [], None, {'display': 'none'}
    
    if not tasks_contents or not history_contents or not sprints_contents:
        return 'Не все файлы загружены', None, [], None, {'display': 'none'}

    tasks_df = concatenate_files(tasks_contents, tasks_filenames)
    history_df = concatenate_files(history_contents, history_filenames)
    sprints_df = concatenate_files(sprints_contents, sprints_filenames)

    if tasks_df.empty or history_df.empty or sprints_df.empty:
        return 'Все файлы должны быть в .csv формате', None, [], None, {'display': 'none'}

    # Merge dataframes
    data = pd.read_csv('test_df.csv')

    # Parse dates
    data['create_date'] = pd.to_datetime(data['create_date'])
    data['update_date'] = pd.to_datetime(data['update_date'])
    data['due_date'] = pd.to_datetime(data['due_date'])

    # Convert data to JSON for storage
    data_json = data.to_json(date_format='iso', orient='split')

    # Update sprint selector options
    unique_sprints = data['sprint_id'].unique()
    options = [{"label": f"Sprint {sprint}", "value": sprint} for sprint in unique_sprints]
    value = unique_sprints[0] if len(unique_sprints) > 0 else None

    # Show the dashboard content
    return '', data_json, options, value, {'display': 'block'}

# Callback to update the charts based on the selected sprint
@app.callback(
    [Output("status_chart", "figure"),
     Output("time_chart", "figure"),
     Output("priority_chart", "figure")],
    [Input("sprint_selector", "value")],
    [State('data-store', 'data')]
)
def update_charts(selected_sprint, data_json):
    if data_json is None or selected_sprint is None:
        return {}, {}, {}
    data = pd.read_json(data_json, orient='split')

    # Filter data based on the selected sprint
    filtered_data = data[data['sprint_id'] == selected_sprint]

    # Check if filtered data is empty
    if filtered_data.empty:
        return {}, {}, {}

    # Status distribution chart
    status_fig = px.pie(
        filtered_data,
        names="status",
        title="Распределение по статусам задач"
    )

    # Estimation vs Spent Time chart
    time_fig = px.bar(
        filtered_data,
        x="ticket_number",
        y=["estimation", "spent"],
        barmode="group",
        title="Оценка vs Затраченное время"
    )

    # Tasks by Priority and Status chart
    priority_fig = px.bar(
        filtered_data,
        x="priority",
        color="status",
        title="Задачи по приоритету и статусу",
        barmode="stack"
    )

    return status_fig, time_fig, priority_fig

if __name__ == '__main__':
    app.run_server(debug=True)
