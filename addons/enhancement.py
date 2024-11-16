import pandas as pd
import numpy as np

history_to_tasks_mapping = {
    'Время решения 3ЛП ФАКТ': None,
    'Время решения (ФАКТ)': None,
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



def belogurovs_algorithm(df_tasks: pd.DataFrame, df_history: pd.DataFrame, data_sprints: pd.DataFrame) -> pd.DataFrame | str | None:
    try:
        # Convert date columns to datetime
        df_tasks['create_date'] = pd.to_datetime(df_tasks['create_date'])
        df_history = df_history.dropna(how='all')
        df_history['history_date'] = pd.to_datetime(df_history['history_date'])

        # Calculate snapshot_datetime using vectorized operations
        df_history['snapshot_hour'] = ((df_history['history_date'].dt.hour // 4 + 1) * 4) % 24
        df_history['snapshot_datetime'] = df_history['history_date'].dt.floor('D') + pd.to_timedelta(df_history['snapshot_hour'], unit='H')
        df_history.loc[df_history['snapshot_hour'] == 0, 'snapshot_datetime'] += pd.Timedelta(days=1)

        # Drop duplicates to keep the last change per property in each snapshot interval
        df = df_history.sort_values(by=['entity_id', 'snapshot_datetime', 'history_property_name', 'history_date'])
        df = df.drop_duplicates(subset=['entity_id', 'snapshot_datetime', 'history_property_name'], keep='last')

        # Map history_property_name to corresponding column names using the mapping dictionary
        df['column_name'] = df['history_property_name'].map(history_to_tasks_mapping)

        # Extract new values from history_change using vectorized string operations
        df['new_value'] = df['history_change'].str.extract(r'->\s*(.*)').iloc[:, 0]

        # Create a pivot table to reshape the DataFrame
        pivot_df = df.pivot_table(
            index=['entity_id', 'snapshot_datetime'],
            columns='column_name',
            values='new_value',
            aggfunc='first'
        ).reset_index()

        # Combine df_tasks with the pivot_df
        df_tasks['snapshot_datetime'] = df_tasks['create_date']
        combined_df = pd.concat([df_tasks, pivot_df], ignore_index=True)

        # Sort and group by entity_id and snapshot_datetime
        combined_df = combined_df.sort_values(by=['entity_id', 'snapshot_datetime'])

        # Forward fill missing values within each group
        combined_df = combined_df.groupby('entity_id').apply(lambda group: group.ffill()).reset_index(drop=True)

        # After forward fill, drop duplicates if necessary
        combined_df = combined_df.drop_duplicates(subset=['entity_id', 'snapshot_datetime'])

        # Step 1: Precompute the tasks_set and create a DataFrame with it
        data_sprints['tasks_set'] = data_sprints['entity_ids'].apply(lambda x: set(eval(x)))

        # Step 2: Create a DataFrame from combined_df with the columns of interest (entity_id, snapshot_datetime)
        combined_df = combined_df[['entity_id', 'snapshot_datetime']]

        # Step 3: Create a DataFrame that maps entity_ids to sprints using the tasks_set column.
        # This step is for matching each entity_id to the relevant sprint based on entity_id and snapshot_datetime.
        # We will "explode" entity_ids into multiple rows for each sprint, allowing us to merge later.

        # Exploding df_sprints based on tasks_set
        exploded_sprints = data_sprints.explode('tasks_set')[['sprint_name', 'tasks_set', 'sprint_start_date', 'sprint_end_date']]

        # Step 4: Merge combined_df with exploded_sprints on entity_id and tasks_set
        merged_df = combined_df.merge(exploded_sprints, left_on='entity_id', right_on='tasks_set', how='left')

        # Step 5: Filter rows based on snapshot_datetime within sprint_start_date and sprint_end_date
        merged_df['is_in_sprint'] = (merged_df['snapshot_datetime'] >= merged_df['sprint_start_date']) & \
                                    (merged_df['snapshot_datetime'] <= merged_df['sprint_end_date'])

        # Step 6: Filter out rows where 'is_in_sprint' is False (no valid sprint for this entity_id and snapshot_datetime)
        valid_sprints = merged_df[merged_df['is_in_sprint']]

        # Step 7: For rows that match, take the sprint_name. If no match is found, keep NaN
        combined_df['sprint_id'] = valid_sprints.groupby('entity_id')['sprint_name'].first()

        # Step 8: Fill NaN values with None if necessary
        combined_df['sprint_id'] = combined_df['sprint_id'].fillna(None)

        return combined_df

    except Exception as e:
        return f"{e}"
