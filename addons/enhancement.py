import pandas as pd
import numpy as np

history_to_tasks_mapping = {
    'Время решения 3ЛП ФАКТ': None,
    'Время решения (ФАКТ)': 'estimation',
    'Исполнитель': 'assignee',
    'Срок исполнения': 'due_date',
    'Спринт': None,
    'Статус': 'status',
    'Резолюция': 'resolution',
    'Метки': None,
    'Дата решения': None,
    'Задача': 'name',
    'nan': None,
    'Название': 'name',
    'Приоритет': 'priority',
    'Стрим-владелец': 'owner',
    'Стрим-заказчик': 'workgroup',
    'Проект-заказчик': 'workgroup',
    'Родительская задача': 'parent_ticket_id',
    'Связанные Задачи': None,
    'Дочерние Задачи': None,
    'Владелец': 'owner',
    'Оценка': 'estimation',
    'Релиз': None,
    'Копирование': None,
    'Компоненты': None,
    'Story Points': None,
    'Учет рабочего времени': None,
    'Код системы': None,
    'Системы': None,
    'Причины Арх. Таск-трекер': None,
    'Тип работ': 'type',
    'Системы обнаружения': None,
    'Обнаружено автотестом': None,
    'Время решения 4ЛП ПЛАН': None,
    'Время решения 4ЛП ФАКТ': None,
    'Время Исправления (ПЛАН)': None,
    'Время Исправления (ФАКТ)': None,
    'Причина отсутствия НТ': None,
    'Вложения': None,
    'Среда обнаружения': None,
    'Согласие на передачу прав': None,
    'Затронуты релизы': None,
    'Время решения (ПЛАН)': None,
    'Подстатус': 'state',
    'Код системы обнаружения': None,
    'Осталось': None,
    'Комментарий при решении': None,
    'Причины дефектов ПРОМ': None,
    'Время восстановления сервиса ПЛАН': None,
    'Время привлечения 3ЛП': None,
    'Время решения 3ЛП ПЛАН': None,
    'Время привлечения 4ЛП': None,
    'Фаза обнаружения дефекта': None,
    'Пространство': None,
    'Дефект смежной ИС': None,
    'Дата начала (Гант)': None,
    'Дата окончания (Гант)': None,
    'Подрядчик-исполнитель': None,
    'Работа подрядчика/вендора': None,
    'Координатор': None,
    'Критерии приемки': None,
    'Причины Тех. долга': None,
    'Время решения 4ЛП по договору': None,
    'Тип дефекта': 'type',
    'Последствия Тех. долга': None,
    'Ожидаемый результат': None,
    'Класс причины': None,
    'Другое': None,
    'Фаза внесения дефекта': None,
    'Сервис': 'area'
}


# Функция для расчета snapshot_datetime
def calculate_snapshot(dt):
    hour = dt.hour
    # Определяем ближайший конец интервала
    snapshot_hour = (hour // 4 + 1) * 4
    if snapshot_hour == 24:  # Если округление до следующего дня
        return dt.replace(hour=0, minute=0, second=0, microsecond=0) + pd.Timedelta(days=1)
    else:
        return dt.replace(hour=snapshot_hour, minute=0, second=0, microsecond=0)
    

# Функция для получения нового значения после '->' в history_change
def extract_new_value(change):
    if pd.isna(change) or '->' not in change:
        return None
    return change.split('->')[-1].strip()


def belogurovs_algorithm(df_tasks: pd.DataFrame, df_history: pd.DataFrame, data_sprints: pd.DataFrame) -> pd.DataFrame | str | None:
    try:

        df_tasks['create_date'] = pd.to_datetime(df_tasks['create_date'])
        
        df_history.dropna(how='all', inplace=True)
        df_history['history_date'] = pd.to_datetime(df_history['history_date'])

        # Для Каждой строки в df_history прикручиваю snapshot_datetime, и сразу удаляю все, кроме последнего изменения конкретного столбца в определенный промежуток времени

        df_history['snapshot_datetime'] = df_history['history_date'].apply(calculate_snapshot)
        df = df_history.sort_values(by=['entity_id', 'snapshot_datetime', 'history_property_name', 'history_date'])
        df = df.drop_duplicates(subset=['entity_id', 'snapshot_datetime', 'history_property_name'], keep='last')

        # Далее мы соберем df, который будет состоять из столбцов nan в полях, где нет изменений,  а в остальных как раз ставится значение, которое изменили
        # Шаг 1. Создаем пустой DataFrame на основе второго DataFrame
        columns = [
            "entity_id", 
            "area", 
            "type", 
            "status", 
            "state", 
            "priority", 
            "ticket_number", 
            "name", 
            "create_date", 
            "created_by", 
            "update_date", 
            "updated_by", 
            "parent_ticket_id", 
            "assignee", 
            "owner", 
            "due_date", 
            "rank", 
            "estimation", 
            "spent", 
            "workgroup", 
            "resolution", 
            "snapshot_datetime"
        ]
        new_df = pd.DataFrame(columns=columns)

        # Шаг 2. Заполняем entity_id и snapshot_datetime
        new_df['entity_id'] = df['entity_id']
        new_df['snapshot_datetime'] = df['snapshot_datetime']

        # Шаг 3. Заполняем соответствующие столбцы значениями из history_change
        for index, row in df.iterrows():
            history_property  = row['history_property_name']
            new_value = extract_new_value(row['history_change'])

            # Проверяем, есть ли соответствующая колонка для history_property_name в словаре
            if history_property in history_to_tasks_mapping:
                column_name = history_to_tasks_mapping[history_property]
                if column_name in new_df.columns and new_value is not None:
                    new_df.loc[index, column_name] = new_value

        # Шаг 4. Заполняем все остальные значения как None
        new_df = new_df.fillna(np.nan)

        df_final = df_tasks
        df_final['snapshot_datetime'] = df_final['create_date'].apply(calculate_snapshot)

        # Объединяем df_tasks и new_df
        combined_df = pd.concat([df_final, new_df], ignore_index=True)

        # Сортируем по snapshot_datetime
        combined_df = combined_df.sort_values(by=['entity_id', 'snapshot_datetime']).reset_index(drop=True)
        # Группируем данные по entity_id и snapshot_datetime и заполняем первое ненулевое значение для каждой колонки
        combined_df = combined_df.groupby(['entity_id', 'snapshot_datetime'], as_index=False).first()

        combined_df = combined_df.sort_values(by=['entity_id', 'snapshot_datetime']).reset_index(drop=True)

        # Сначала сортируем данные по entity_id и snapshot_datetime, чтобы значения были упорядочены
        combined_df = combined_df.sort_values(by=['entity_id', 'snapshot_datetime']).reset_index(drop=True)

        # Применяем заполнение пропусков по каждому entity_id, используя forward fill (ffill)
        combined_df = combined_df.groupby('entity_id', as_index=False).apply(lambda group: group.ffill()).reset_index(drop=True)

        return combined_df
    except Exception as e:
        return f"{e}"

