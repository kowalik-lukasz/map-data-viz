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
    
def create_legend(caption=None, legend_labels: dict = None) -> str:
    if legend_labels is None:
        raise AttributeError('Error. No legend_labels provided.')
    
    file = open(os.path.join(script_dir_path, '..', 'data', 'legend_template.txt'), 'r')
    lines = file.readlines()
    file.close()
    
    if caption is not None:
        legend_title = "<div class='legend-title'>" + caption + "</div>\n"
        lines[lines.index("<div class='legend-title'>Legend (draggable!)</div>\n")] = legend_title
    
    label_index = lines.index("  <ul class='legend-labels'>\n") + 1
    for _, (k, v) in enumerate(legend_labels.items()):
        print(k, v)
        legend_label = "    <li><span style='background:" + k + ";opacity:0.7;'></span>" + v +"</li>\n"
        lines.insert(label_index, legend_label)
        label_index += 1
    
    separator = ''
    return separator.join(lines)         