import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import io
import base64
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

from addons.enhancement import belogurovs_algorithm
from addons.preprocess import preprocess

# Create Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

def concatenate_files(contents_list, filenames):
    #try:
        if contents_list is not None:
            dfs = []
            for contents, filename in zip(contents_list, filenames):
                content_type, content_string = contents.split(',')
                decoded = base64.b64decode(content_string)
                df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), sep=';', header=1)
                dfs.append(df)
            if dfs:
                concatenated_df = pd.concat(dfs, ignore_index=True)
                concatenated_df = preprocess(concatenated_df)
                return concatenated_df
        return pd.DataFrame()
    # except:
    #     return pd.DataFrame()

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
    dcc.Loading(
        id="loading-1",
        type="default",
        children=html.Div(id="loading-output-1")
    ),
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
    html.Br(),
    dcc.Dropdown(
        id="team_selector",
        options=[],
        value=None,
        multi=True
    ),
    html.Br(),
    html.Label("Выберите дату, на которую отобразить состояние задач:"),
    dcc.Slider(
    id="date_slider",
    min=0,  # Значения будут обновлены в колбэке
    max=1,
    step=14400,  # 4 часа в секундах
    marks={},
    value=0
    ),
    html.Br(),
    dcc.Graph(id="kpi_chart", figure={}),
    dcc.Graph(id="sprint_metrics_chart", figure={}),
    dcc.Graph(id="priority_chart", figure={}),
    dcc.Graph(id="status_chart", figure={})
    
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

@app.callback(
    Output('output-data-upload', 'children'),
    Output('data-store', 'data'),
    Output('sprint_selector', 'options'),
    Output('sprint_selector', 'value'),
    Output('team_selector', 'options'),
    Output('team_selector', 'value'),
    Output('dashboard-content', 'style'),
    Output("loading-output-1", "children"),
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
        # Возвращаем значения для всех 9 Outputs
        return (
            'После загрузки нажмите получить данные', None, [], None, [], None,  {'display': 'none'}, None
        )

    if not tasks_contents or not history_contents or not sprints_contents:
        return (
            'Не все файлы загружены', None, [], None, [], None, {'display': 'none'}, None
        )

    tasks_df = concatenate_files(tasks_contents, tasks_filenames)
    history_df = concatenate_files(history_contents, history_filenames)
    sprints_df = concatenate_files(sprints_contents, sprints_filenames)

    if tasks_df.empty or history_df.empty or sprints_df.empty:
        return (
            'Все файлы должны быть в .csv формате', None, [], None, [], None, {'display': 'none'}, None
        )


    print('here')
    d1 = datetime.now()
    data = belogurovs_algorithm(tasks_df, history_df, sprints_df)
    d2 = datetime.now()
    print(d2 - d1)
    print('here2')

    if type(data) != pd.DataFrame:
        return (
            'Ошибка в преобразовании данных (проверьте формат входных данных)', None, [], None, [], None, {'display': 'none'}, None
        )
    # Преобразование дат
    data['snapshot_datetime'] = pd.to_datetime(data['snapshot_datetime'])
    # Преобразуем в количество секунд с эпохи UNIX
    data['timestamp'] = data['snapshot_datetime'].astype('int64') / 10**9
    min_date = data['timestamp'].min()
    max_date = data['timestamp'].max()

    # Конвертируем данные в JSON для хранения
    data_json = data.to_json(date_format='iso', orient='split')

    # Уникальные значения спринтов
    unique_sprints = data['sprint_id'].unique()
    options = [{"label": f"Sprint {sprint}", "value": sprint} for sprint in unique_sprints]
    
    # Уникальные значения спринтов
    unique_sprints = data['sprint_id'].dropna().unique()  # Убираем NaN значения
    options = [{"label": f"Sprint {sprint}", "value": sprint} for sprint in unique_sprints if pd.notna(sprint)]

    # Выбираем первый спринт по умолчанию, если есть
    default_sprint_value = unique_sprints[0] if len(unique_sprints) > 0 else None

    # Уникальные значения спринтов
    unique_teams = data['area'].dropna().unique()  # Убираем NaN значения
    team_options = [{"label": f"Team {team}", "value": team} for team in unique_teams if pd.notna(team)]
    
    # Выбираем первый спринт по умолчанию, если есть
    default_team_value = unique_teams


    # Возвращаем обновленные параметры
    return (
        '', data_json, options, default_sprint_value, team_options, default_team_value, {'display': 'block'}, None
    )


@app.callback(
    [Output("sprint_metrics_chart", "figure"),
     Output("status_chart", "figure"),
     Output("kpi_chart", "figure"),
     Output("priority_chart", "figure")],
    [Input("sprint_selector", "value"),
     Input("team_selector", "value"),
     Input("date_slider", "value")],
    [State('data-store', 'data')]
)
def update_charts(selected_sprint, selected_team, selected_date, data_json):
    if data_json is None or selected_sprint is None or selected_date is None:
        return {}, {}, {}, {"layout": {"title": "Данные не выбраны"}}

    # Загрузка данных
    data = pd.read_json(data_json, orient='split')

    # Преобразование timestamp в datetime
    selected_datetime = pd.to_datetime(selected_date, unit='s')
    # selected_datetime = selected_date
    # datetime debug
    print(f"Selected datetime: {selected_datetime}")
    # print(data['timestamp'].unique())


    # Фильтрация данных
    # filtered_data = data[
    #     (data['sprint_id'] == selected_sprint) &
    #     (data['timestamp'] == selected_datetime) &
    #     (data.drop_duplicates(data['entity_id'], keep='last'))
    #     (data['timestamp'].dt.microsecond == 0) &
    #     (data['area'].isin(selected_team))
    # ]
    latest_data = (
        data.sort_values(by='timestamp')
            .drop_duplicates(subset='entity_id', keep='last')
    )

    # Фильтруем данные с учетом выбранных условий
    filtered_data = latest_data[
        (latest_data['sprint_id'] == selected_sprint) &  # Выбранный спринт
        (latest_data['timestamp'] <= selected_datetime) &  # Учитываем временной срез
        (latest_data['area'].isin(selected_team))  # Команды
    ]

    if filtered_data.empty:
        return {}, {}, {}, {"layout": {"title": "Нет данных для отображения"}}

    # График метрик спринта
    # sprint_metrics_fig = px.bar(filtered_data.groupby(by='status').agg({'estimation':lambda x: x.sum()/3600}).reset_index(),
    #    x='estimation', y='status', text_auto='.1f', title='Метрики спринта по статусам')

    grouped_data = filtered_data.groupby(by='status').agg({'estimation': lambda x: x.sum() / 3600}).reset_index()

    # Добавляем цвета для каждого статуса
    color_mapping = {
        'В работе': '#4472C4',  # Синий
        'Выполнено': '#ED7D31',  # Оранжевый
        'Закрыто': '#70AD47',  # Зеленый
        'Отменено': '#E74C3C',  # Красный
        'Создан': '#00B0F0'  # Голубой
    }

    grouped_data['color'] = grouped_data['status'].map(color_mapping)

    # Добавляем единую категорию для объединения всех статусов в один столбик
    grouped_data['category'] = 'Статусы'

    # Создаем горизонтальный график
    sprint_metrics_fig = px.bar(
        grouped_data,
        x='estimation',
        y='category',                # Одна категория — "Все статусы"
        color='status',              # Используем цвет для статусов
        color_discrete_map=color_mapping,
        text='estimation',           # Показываем значения
        title='Суммарные метрики спринта по статусам'
    )

    # Настройки оформления
    sprint_metrics_fig.update_layout(
        barmode='stack',             # Столбик в одном блоке
        xaxis_title='Сумма часов',
        yaxis_title='',              # Скрыть название оси Y
        legend_title='Статусы',
        uniformtext_minsize=8,
        uniformtext_mode='hide'
    )

    # Добавляем текст для лучшей читаемости
    sprint_metrics_fig.update_traces(textposition='inside', texttemplate='%{text:.1f}')


    ###########
     
    # График распределения статусов
    status_fig = px.pie(
        filtered_data,
        names="status",
        title="Распределение по статусам задач",
        color='status',
        color_discrete_map=color_mapping
    )

    # График времени
    time_fig = px.bar(
        filtered_data,
        x="ticket_number",
        y=["state"],
        barmode="group",
        title="Состояния задач",
        color_discrete_map=color_mapping
    )

    # График задач по приоритетам
    priority_fig = px.bar(
        filtered_data,
        y="priority",
        color="status",
        title="Задачи по приоритету и статусу",
        barmode="stack",
        orientation='h',
        color_discrete_map=color_mapping
    )

    # График по KPI
    # Вычисление суммарного значения estimation
    total_estimation = grouped_data['estimation'].sum()

    # Вычисление суммарного estimation для статусов
    in_progress_estimation = grouped_data[grouped_data['status'] == 'Создано']['estimation'].sum()
    removed_estimation = grouped_data[grouped_data['status'] == 'Отменено']['estimation'].sum()

    # Вычисление долей в процентах
    in_progress_ratio = (in_progress_estimation / total_estimation) * 100 if total_estimation > 0 else 0
    removed_ratio = (removed_estimation / total_estimation) * 100 if total_estimation > 0 else 0

    # Установка цветов в зависимости от долей
    in_progress_color = 'red' if in_progress_ratio > 30 else 'orange' if in_progress_ratio > 20 else 'green'
    removed_color = 'red' if removed_ratio > 20 else 'orange' if removed_ratio > 10 else 'green'

    # Создание карточки KPI
    kpi_fig = go.Figure()

    # Индикатор для статуса "К выполнению"
    kpi_fig.add_trace(go.Indicator(
        mode="number",
        value=in_progress_ratio,
        number={"font_color":in_progress_color, "suffix":"%", "valueformat":".1f"},
        title={"text": "Доля 'Создано (к выполнению)' (%)"},
        
        domain={'x': [0, 0.33], 'y': [0, 1]},

    ))

    # Индикатор для статуса "Снято"
    kpi_fig.add_trace(go.Indicator(
        mode="number",
        value=removed_ratio,
        number={"font_color":removed_color, "suffix":"%", "valueformat":".1f"},
        title={"text": "Доля 'Отменено (снято)' (%)"},
        domain={'x': [0.33, 0.66], 'y': [0, 1]},
    ))

    # Доля изменения бэклога спринта

    selected_sprint_and_team = data[(data['sprint_id'] == selected_sprint) & (data['area'].isin(selected_team))]

    filtered_data_sprint_start = selected_sprint_and_team[selected_sprint_and_team['timestamp'] == min(selected_sprint_and_team['timestamp'])]
    filtered_data_sprint_selected = selected_sprint_and_team[selected_sprint_and_team['timestamp'] <= selected_datetime]

    start_tasks_set = set(filtered_data_sprint_start['entity_id'].unique())
    selected_tasks_set = set(filtered_data_sprint_selected[filtered_data_sprint_selected['status'] != 'Отменено']['entity_id'].unique())

    backlog_diff = round(len(selected_tasks_set - start_tasks_set) / len(start_tasks_set.union(selected_tasks_set)), 2) * 100 # Процент изменения бэклога спринта
    backlog_diff_color = 'red' if backlog_diff > 30 else 'orange' if backlog_diff > 20 else 'green'

    # Индикатор для статуса "Снято"
    kpi_fig.add_trace(go.Indicator(
        mode="number",
        value=backlog_diff,
        number={"font_color":backlog_diff_color, "suffix":'%'},
        title={"text": "Изменение бэклога со старта (%)"},
        domain={'x': [0.66, 1], 'y': [0, 1]},
    ))

    # Обновление макета
    kpi_fig.update_layout(title="KPIs по статусам задач")

    return sprint_metrics_fig, status_fig, kpi_fig, priority_fig


@app.callback(
    Output('date_slider', 'min'),
    Output('date_slider', 'max'),
    Output('date_slider', 'marks'),
    Output('date_slider', 'value'),
    Input('sprint_selector', 'value'),
    State('data-store', 'data')
)
def update_slider_dates(selected_sprint, data_json):
    if selected_sprint is None or data_json is None:
        return 0, 1, {}, 0

    # Загрузка данных
    data = pd.read_json(data_json, orient='split')

    # Фильтрация данных по выбранному спринту
    sprint_data = data[(data['sprint_id'] == selected_sprint) & (data['timestamp'].dt.microsecond == 0)]

    if sprint_data.empty:
        return 0, 1, {}, 0

    # Получаем минимальные и максимальные даты для выбранного спринта
    min_date = sprint_data['timestamp'].min()
    max_date = sprint_data['timestamp'].max()

    print('data type', min_date.timestamp())

    # Преобразуем min_date и max_date в секунды
    min_date_seconds = int(min_date.timestamp())  # Преобразуем в секунды
    max_date_seconds = int(max_date.timestamp())  # Преобразуем в секунды

    # Формируем метки слайдера для доступных дат
    marks = {
        int(row.timestamp()): row.strftime('%Y-%m-%d')  # Преобразуем в timestamp и форматируем для отображения
        for row in pd.to_datetime(sprint_data['snapshot_datetime']).sort_values().unique()
    }

    # Устанавливаем значение слайдера на минимальную дату по умолчанию
    value = max_date_seconds  # Устанавливаем значение слайдера на минимальную дату по умолчанию

    return min_date_seconds, max_date_seconds, marks, value


if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port='9090')