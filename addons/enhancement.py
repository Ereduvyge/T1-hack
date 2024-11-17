import pandas as pd
import numpy as np
import ast

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
        df_tasks['snapshot_hour'] = ((df_tasks['create_date'].dt.hour // 4 + 1) * 4) % 24
        df_tasks['snapshot_datetime'] = df_tasks['create_date'].dt.floor('D') + pd.to_timedelta(df_tasks['snapshot_hour'], unit='H')
        df_tasks.loc[df_tasks['snapshot_hour'] == 0, 'snapshot_datetime'] += pd.Timedelta(days=1)
        combined_df = pd.concat([df_tasks, pivot_df], ignore_index=True)

        # Sort and group by entity_id and snapshot_datetime
        combined_df = combined_df.sort_values(by=['entity_id', 'snapshot_datetime'])

        # Forward fill missing values within each group
        combined_df = combined_df.groupby('entity_id').apply(lambda group: group.ffill()).reset_index(drop=True)

        # After forward fill, drop duplicates if necessary
        combined_df = combined_df.drop_duplicates(subset=['entity_id', 'snapshot_datetime'])

        # Safely parse 'entity_ids' strings in df_sprints to lists using ast.literal_eval
        def parse_entity_ids(x):
            try:
                return ast.literal_eval(x)
            except (ValueError, SyntaxError):
                return []
    
        data_sprints['entity_ids_list'] = data_sprints['entity_ids'].apply(parse_entity_ids)
    
        # Explode 'entity_ids_list' to get one row per entity_id per sprint
        df_sprints_exploded = data_sprints.explode('entity_ids_list')
        df_sprints_exploded.rename(columns={'entity_ids_list': 'entity_id'}, inplace=True)
    
        # Ensure 'entity_id' types match in both DataFrames
        combined_df['entity_id'] = combined_df['entity_id'].astype(int).astype(str)
        df_sprints_exploded['entity_id'] = df_sprints_exploded['entity_id'].astype(int).astype(str)
    
        # Merge combined_df with df_sprints_exploded on 'entity_id'
        merged_df = combined_df.merge(
            df_sprints_exploded[['entity_id', 'sprint_start_date', 'sprint_end_date', 'sprint_name']],
            on='entity_id',
            how='left'
        )
    
        # Filter rows where snapshot_datetime is within sprint date range
        merged_df_filtered = merged_df[
            (merged_df['snapshot_datetime'] >= merged_df['sprint_start_date']) &
            (merged_df['snapshot_datetime'] <= merged_df['sprint_end_date'])
            ]
    
        # Sort to select the most relevant sprint
        merged_df_filtered = merged_df_filtered.sort_values(
            by=['entity_id', 'snapshot_datetime', 'sprint_start_date'],
            ascending=[True, True, False]
        )
    
        # Drop duplicates to keep one sprint per entity_id and snapshot_datetime
        merged_df_filtered = merged_df_filtered.drop_duplicates(
            subset=['entity_id', 'snapshot_datetime'],
            keep='first'
        )
    
        # Prepare sprint assignments DataFrame
        sprint_assignments = merged_df_filtered[['entity_id', 'snapshot_datetime', 'sprint_name']]
        sprint_assignments.rename(columns={'sprint_name': 'sprint_id'}, inplace=True)
    
        # Merge sprint assignments back into the combined_df
        combined_df = combined_df.merge(
            sprint_assignments,
            on=['entity_id', 'snapshot_datetime'],
            how='left'
        )
        return combined_df

    except Exception as e:
        return f"{e}"
