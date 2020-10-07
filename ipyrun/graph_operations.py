# -*- coding: utf-8 -*-
"""
@author: r.woods
"""

import matplotlib.pyplot as plt
from matplotlib import rcParams
import matplotlib.image as mpimg
import plotly.graph_objects as go

def full_width_graph(data, settings, filename, img, plotly, legend=True):
        
        defaults = {
            "yaxis_title": '',
            "xaxis_title": '', 
            "yaxis_tickformat":'', 
            "xaxis_type":'-',
            "width": 1200,
            "height": 500,
            "template": "simple_white",
            "titlefont": {"size": 24},
            "font": {"size": 18},
            "showlegend": legend,
            "font_family": "Calibri"
        }
        
        for key in defaults:
            if key not in settings:
                settings[key] = defaults[key]

        fig_settings = dict({
            "data": data,
            "layout": settings
        })        
        
        fig = go.Figure(fig_settings)
        
        if(img):
            fig.write_image(filename + '.jpg')
            
        if(plotly):
            fig.write_json(filename + '.plotly')