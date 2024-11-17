import pandas as pd
import numpy as np

status_mapping = {
    '<empty>': '<empty>',
    'analysis': 'Анализ',
    'at': 'Неопределено',
    'closed': 'Закрыто',
    'created': 'Создано',
    'design': 'Неопределено',
    'development': 'Разработка',
    'done': 'Выполнено',
    'fixing': 'Исправление',
    'hold': 'Отложен',
    'ift': 'Неопределено',
    'inProgress': 'В работе',
    'introduction': 'Неопределено',
    'localization': 'Локализация',
    'readyForDevelopment': 'Готово к разработке',
    'rejectedByThePerformer': 'Отменено',
    'review': 'Подтверждение',
    'st': 'СТ',
    'stCompleted': 'СТ Завершено',
    'testing': 'Тестирование',
    'verification': 'Подтверждение исправления',
    'waiting': 'В ожидании'
}

strip_status_mapping = {
    '<empty>': '<empty>',
    'analysis': 'В работе',
    'at': 'В работе',
    'closed': 'Закрыто',
    'created': 'Создано',
    'design': 'В работе',
    'development': 'В работе',
    'done': 'Выполнено',
    'fixing': 'В работе',
    'hold': 'Отложен',
    'ift': 'В работе',
    'inProgress': 'В работе',
    'introduction': 'В работе',
    'localization': 'В работе',
    'readyForDevelopment': 'Создано',
    'rejectedByThePerformer': 'Отменено',
    'review': 'В работе',
    'st': 'В работе',
    'stCompleted': 'В работе',
    'testing': 'В работе',
    'verification': 'В работе',
    'waiting': 'В ожидании'
}

strip_status_mapping_rus = {
    'Анализ': 'В работе',
    'Закрыто': 'Закрыто',
    'Создано': 'Создано',
    'Разработка': 'В работе',
    'Выполнено': 'Выполнено',
    'Исправление': 'В работе',
    'Отложен': 'Отложен',
    'В работе': 'В работе',
    'Локализация': 'В работе',
    'Готово к разработке': 'Создано',
    'Отклонен исполнителем': 'Отменено',
    'Подтверждение': 'В работе',
    'СТ': 'В работе',
    'СТ Завершено': 'В работе',
    'Тестирование': 'В работе',
    'Подтверждение исправления': 'В работе',
    'В ожидании': 'В ожидании'
}

strip_priority_mapping = {
    'average': 'Средний',
    'low': 'Низкий',
    'high': 'Высокий', 
    'critical': 'Критический'
}

strip_resolution_mapping = {
    '<empty>': '<empty>',
    'Готово': 'Выполнено',
    'Создано': 'Создано',
    'Дубликат': 'Отменено',
    'Отклонено': 'Отменено',
    'Отменен инициатором': 'Отменено'
}


def replace_status(history_change, strip_mapping):
    if isinstance(history_change, str) and '->' in history_change:
        for part in history_change.split('->'):
            part = part.strip()
            if part in strip_mapping.keys():
                history_change = history_change.replace(part, strip_mapping[part])
        return history_change
    return history_change


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(how='all')
    if 'history_change' in df.columns:
        strip_mapping = combined_mapping = strip_status_mapping | strip_priority_mapping | strip_resolution_mapping
        df['history_change'] = df['history_change'].apply(
            lambda x: replace_status(x, strip_mapping=strip_mapping)
        )
    if 'status' in df.columns:
        df["status"] = df["status"].apply(
            lambda status: status.replace(status, strip_status_mapping_rus[status])
        )

    if 'resolution' in df.columns:
        df["resolution"] = df["resolution"].fillna('Создано')
        df["resolution"] = df["resolution"].apply(
            lambda status: status.replace(status, strip_resolution_mapping[status])
        )

    if 'estimation' in df.columns:
        df["estimation"] = df["estimation"].fillna(0)

    def filter_date_column(column):
        return column.find('_date') != -1
    date_columns = list(filter(filter_date_column, df.columns.tolist()))
    df[date_columns] = df[date_columns].apply(pd.to_datetime)

    return df
