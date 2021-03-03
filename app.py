
import math
import numpy as np
import pandas as pd
import os

from bokeh.embed import components
from bokeh.layouts import column, gridplot, layout, row
from bokeh.models import ColumnDataSource, HoverTool, PrintfTickFormatter
from bokeh.models.tickers import SingleIntervalTicker
from bokeh.plotting import figure
from bokeh.transform import factor_cmap
from bokeh.models import GMapOptions
from bokeh.plotting import gmap

from flask import Flask, render_template, request

df = pd.read_csv('data/tv.csv')

##Constants

palette = ['#ba32a0', '#f85479', '#f8c260', '#00c2ba']

chart_font = 'Helvetica'
chart_title_font_size = '16pt'
chart_title_alignment = 'center'
axis_label_size = '14pt'
axis_ticks_size = '12pt'
default_padding = 30
chart_inner_left_padding = 0.015
chart_font_style_title = 'bold italic'

##HELPER FUNCTIONS

def palette_generator(length, palette):
    int_div = length // len(palette)
    remainder = length % len(palette)
    return (palette * int_div) + palette[:remainder]


def plot_styler(p):
    p.title.text_font_size = chart_title_font_size
    p.title.text_font  = chart_font
    p.title.align = chart_title_alignment
    p.title.text_font_style = chart_font_style_title
    p.y_range.start = 0
    p.x_range.range_padding = chart_inner_left_padding
    p.xaxis.axis_label_text_font = chart_font
    p.xaxis.major_label_text_font = chart_font
    p.xaxis.axis_label_standoff = default_padding
    p.xaxis.axis_label_text_font_size = axis_label_size
    p.xaxis.major_label_text_font_size = axis_ticks_size
    p.yaxis.axis_label_text_font = chart_font
    p.yaxis.major_label_text_font = chart_font
    p.yaxis.axis_label_text_font_size = axis_label_size
    p.yaxis.major_label_text_font_size = axis_ticks_size
    p.yaxis.axis_label_standoff = default_padding
    p.toolbar.logo = None
    p.toolbar_location = None


def redraw(selected_class):

    selected_class = int(selected_class)
    if selected_class == 0: # all classes
        dataset = df
    elif selected_class == 1:
        dataset = df[df['Year'] == 2012]
    elif selected_class == 2:
        dataset = df[df['Year'] == 2013]
    elif selected_class == 3:
        dataset = df[df['Year'] == 2014]
    elif selected_class == 4:
        dataset = df[df['Year'] == 2015]
    elif selected_class == 5:
        dataset = df[df['Year'] == 2016]
    elif selected_class == 6:
        dataset = df[df['Year'] == 2017]         

    class_texts = ["All Years","2012", "2013","2014","2015","2016","2017"]
    class_text = class_texts[selected_class]
    gender_chart = gender_bar_chart(dataset, "Gender wise analysis for Year " + class_text)
    state_chart = state_bar_chart(dataset, "State(Province) wise analysis for Year " + class_text)
    map_chart = map_chart_loc(dataset, "MAP for locations in YEAR" + class_text)

    return (
        gender_chart,
        state_chart,
        map_chart
    )

##FLASK FRAMEWORK

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def chart():

    selected_class = request.form.get('dropdown-select')
    if selected_class is None:
        selected_class = 0
    gender_chart, state_chart, map_chart = redraw(selected_class)

    script_gender_chart, div_gender_chart = components(gender_chart)
    script_state_chart, div_state_chart = components(state_chart)
    script_hist_age, div_hist_age = components(map_chart)

    return render_template(
        'index.html',
        div_gender_chart=div_gender_chart,
        script_gender_chart=script_gender_chart,
        div_state_chart=div_state_chart,
        script_state_chart=script_state_chart,
        div_hist_age=div_hist_age,
        script_hist_age=script_hist_age,
        selected_class=selected_class
    )

##GENDER CHART GENERATION FUNCTIONS

def gender_bar_chart(dataset, title, cpalette=None):

    if cpalette is None:
        cpalette = palette[1:3]

    gen_data = dataset
    gender_wise = list(gen_data['Gender'].value_counts().index)
    gender_values = list(gen_data['Gender'].value_counts().values)
    gender_wise_text = ['Male', 'Female']
        
    source = ColumnDataSource(data={
        'gender': gender_wise,
        'gender_txt': gender_wise_text,
        'values': gender_values
    })

    hover_tool = HoverTool(
        tooltips=[('Gender?', '@gender_txt'),
                  ('Count', '@values')]
    )
    
    p = figure(tools=[hover_tool], plot_height=400, title=title)
    p.vbar(x='gender', top='values', source=source, width=0.9,
           fill_color=factor_cmap('gender_txt',
                                  palette=palette_generator(len(source.data['gender_txt']), cpalette),
                                  factors=source.data['gender_txt']))
    
    plot_styler(p)
    p.xaxis.ticker = source.data['gender']
    p.xaxis.major_label_overrides = { 0: 'Male', 1: 'Female' }
    p.sizing_mode = 'scale_width'
    
    return p


def state_bar_chart(dataset, title, cpalette=None):
    if cpalette is None:
        cpalette = palette
    ttl_data = dataset
    title_possibilities = list(ttl_data['State'].value_counts().index)
    title_values = list(ttl_data['State'].value_counts().values)
    int_possibilities = np.arange(len(title_possibilities))
    
    source = ColumnDataSource(data={
        'titles': title_possibilities,
        'titles_int': int_possibilities,
        'values': title_values
    })

    hover_tool = HoverTool(
        tooltips=[('State', '@titles'), ('Count', '@values')]
    )
    
    chart_labels = {}
    for val1, val2 in zip(source.data['titles_int'], source.data['titles']):
        chart_labels.update({ int(val1): str(val2) })
        
    p = figure(tools=[hover_tool], plot_height=300, title=title)
    p.vbar(x='titles_int', top='values', source=source, width=0.9,
           fill_color=factor_cmap('titles', palette=palette_generator(len(source.data['titles']), cpalette),
                                  factors=source.data['titles']))
    
    plot_styler(p)
    p.xaxis.ticker = source.data['titles_int']
    p.xaxis.major_label_overrides = chart_labels
    p.xaxis.major_label_orientation = math.pi / 4
    p.sizing_mode = 'scale_width'
    
    return p


def map_chart_loc(dataset, title, color=palette[1]):

    #dataset = df[df['State'] == "VA"]
    map_options = GMapOptions(lat=39.16288833, lng=-77.22908833, map_type="roadmap", zoom=12)

    p = gmap("AIzaSyAK0D5nFLLwrpgTmU-nzGPlQU26vy_v7NI", map_options, title="Vialations Clusturing by Location")

    data = dict(lat=dataset['Latit0de'].values,
                lon=dataset['Longit0de'].values)

    p.circle(x="lon", y="lat", size=4, fill_color="blue", fill_alpha=0.8, source=data)
    p.plot_width=1200

    return p

if __name__ == '__main__':
    app.run(debug=True)