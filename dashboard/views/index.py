from django.shortcuts import render

from django_plotly_dash import DjangoDash
from dash import html, dcc
import pandas as pd

import plotly.graph_objects as go


def index(request):
    # Template context date
    fig = go.Figure(data=[go.Bar(x=[1, 2, 3], y=[2, 1, 3])])
    fig.update_layout(title='A Simple Bar Chart')

    plot_div = fig.to_html(full_html=False)
    context: dict = {
        'title': 'BMI Calculator',
        'bar_plot': plot_div}
    return render(request, 'dashboard/index.html', context=context)  # Assumes you have this template


