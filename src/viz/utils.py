import os
import requests
import urllib
from logging import log
from branca.element import Template, MacroElement

script_dir_path = os.path.dirname(os.path.realpath(__file__))

class BindColormap(MacroElement):
    def __init__(self, layer, colormap):
        super(BindColormap, self).__init__()
        self.layer = layer
        self.colormap = colormap
        self._template = Template(u"""
        {% macro script(this, kwargs) %}
            {{this.colormap.get_name()}}.svg[0][0].style.display = 'block';
            {{this._parent.get_name()}}.on('overlayadd', function (eventLayer) {
                if (eventLayer.layer == {{this.layer.get_name()}}) {
                    {{this.colormap.get_name()}}.svg[0][0].style.display = 'block';
                }});
            {{this._parent.get_name()}}.on('overlayremove', function (eventLayer) {
                if (eventLayer.layer == {{this.layer.get_name()}}) {
                    {{this.colormap.get_name()}}.svg[0][0].style.display = 'none';
                }});
        {% endmacro %}
        """)

def download_file(download_url='', location='', filename=''):
    if not download_url:
        raise AttributeError('Error. No url provided')
    if not filename:
        filename = download_url[download_url.rfind('/')+1:]
    if location:
        location = os.path.join(location, filename)
    else:
        location = filename
        
    try:
        urllib.request.urlretrieve(download_url, location)
    except Exception as e:
        raise Exception(e)
    
def create_legend(caption=None, legend_labels=None) -> str:
    if legend_labels is None:
        raise AttributeError('Error. No legend_labels provided.')
    
    file = open(os.path.join(script_dir_path, '..', 'data', 'legend_template.txt'), 'r')
    lines = file.readlines()
    file.close()
    
    if caption is not None:
        legend_title = "<div class='legend-title'>" + caption + "</div>\n"
        lines[lines.index("<div class='legend-title'>Legend (draggable!)</div>\n")] = legend_title
    
    if any(isinstance(value, dict) for value in legend_labels.values()):
        css_index = lines.index("<style type='text/css'>\n") + 1
        css_decorator = '''
            .legend-labels {{
            columns: {};
            -webkit-columns: {};
            -moz-columns: {};
        }}
        '''.format(len(legend_labels), len(legend_labels), len(legend_labels))
        lines.insert(css_index, css_decorator)
        # legend_labels_str = [""] * len(legend_labels[0])
        label_index = lines.index("  <ul class='legend-labels'>\n") + 1
        for _, (category, legend) in enumerate(legend_labels.items()):
            print(category, legend)
            lines.insert(label_index, "    <li><b>" + category + "</b></li>\n")
            label_index += 1
            for j, (k, v) in enumerate(legend.items()):
                legend_label = "    <li><span style='background:" + k + ";opacity:0.7;'></span>" + v +"</li>\n"
                lines.insert(label_index, legend_label)
                label_index += 1
                # print(k, v)
                # if i == 0:
                #     legend_labels_str[j] = "    <li><span style='background:" + k + ";opacity:0.7;'></span>" + v +"     "
                # elif i == len(legend_labels)-4:
                #     legend_labels_str[j] +=  "<span style='background:" + k + ";opacity:0.7;'></span>" + v +"</li>\n"
                # else:
                #     legend_labels_str[j] +=  "<span style='background:" + k + ";opacity:0.7;'></span>" + v +"     "
                
                # if i == 1:
                #     lines.insert(label_index, legend_labels_str[j])
                # print(lines[label_index])     
                # label_index += 1
    else:
        label_index = lines.index("  <ul class='legend-labels'>\n") + 1
        for _, (k, v) in enumerate(legend_labels.items()):
            legend_label = "    <li><span style='background:" + k + ";opacity:0.7;'></span>" + v +"</li>\n"
            lines.insert(label_index, legend_label)
            label_index += 1
    
    separator = ''
    return separator.join(lines)         