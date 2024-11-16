import requests
import json
from datetime import datetime, timedelta

import pandas as pd

from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.request import Request

import plotly.express as px


class Change_Task:
    def __init__(self, sprint_name, entity_id, change):
        self.sprint_name = sprint_name
        self.entity_id = entity_id
        self.change = change

    def __repr__(self):
        return f"Change_Task({self.sprint_name}, {self.entity_id}, {self.change})"

class Task:
    def __init__(self, entity_id, estimation, spent, list_change):
        self.entity_id = entity_id
        self.estimation = estimation
        self.spent = spent
        self.list_change = list_change

    def __repr__(self):
        return f"Task({self.entity_id}, {self.estimation}, {self.spent}, {self.list_change})"
    

list_task = [
    Task(4449728, 0.0, 0.0, [
        Change_Task("Спринт 2024.3.1.NPP Shared Sprint", 4449728, "created -> inProgress"),
        Change_Task("Спринт 2024.3.1.NPP Shared Sprint", 4449728, "inProgress -> done"),
        Change_Task("Спринт 2024.3.1.NPP Shared Sprint", 4449728, "done -> closed"),
    ]),
    Task(4450628, 24.0, 24.0, [
        Change_Task("Спринт 2024.3.1.NPP Shared Sprint", 4450628, "created -> inProgress"),
        Change_Task("Спринт 2024.3.1.NPP Shared Sprint", 4450628, "inProgress -> closed"),
    ]),
    Task(4451563, 24.0, 24.0, [
        Change_Task("Спринт 2024.3.1.NPP Shared Sprint", 4451563, "created -> inProgress"),
        Change_Task("Спринт 2024.3.1.NPP Shared Sprint", 4451563, "inProgress -> closed"),
    ]),
]


# Симуляция временных меток для всех задач
start_time = datetime(2024, 11, 10, 10, 0, 0)  # Начальная дата
time_delta = timedelta(hours=12)  # Интервал между изменениями


class CreateBoard(APIView):
    def post(self, request: Request):

        data = request.data

        if 'files' in data:

            for i in data['files']:
                print(str(i))

            # df = pd.read_csv(data['file'], sep=';', header=1)
            # print(df.head(5))

        else:
            print(data)

        # Преобразование данных
        data = []
        for task in list_task:
            current_time = start_time
            for i, change in enumerate(task.list_change):
                from_state, to_state = change.change.split(" -> ")
                data.append({
                    "Task ID": task.entity_id,
                    "State": from_state,
                    "Start": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "End": (current_time + time_delta).strftime("%Y-%m-%d %H:%M:%S") if i < len(task.list_change) - 1 else None,
                    "Sprint": change.sprint_name
                })
                current_time += time_delta

            # Добавляем последнее состояние
            data[-1]["End"] = (start_time + len(task.list_change) * time_delta).strftime("%Y-%m-%d %H:%M:%S")

        # Преобразование в DataFrame
        df = pd.DataFrame(data)
        figure=px.timeline(
                    df,
                    x_start="Start",
                    x_end="End",
                    y="Task ID",
                    color="State",
                    title="История задач по спринту",
                    labels={"Task ID": "ID задачи", "State": "Состояние"},
                    hover_data=["Sprint"]
                ).update_xaxes(title="Время").update_yaxes(title="Задачи")
        div = figure.to_json()
        
        content = {
            'success': True,
            'message': f'Order executed successfully',
            'plot': div,
        }
        return Response(content, status=status.HTTP_200_OK)
            
