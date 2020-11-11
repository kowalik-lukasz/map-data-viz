from branca.element import Template, MacroElement
import os

script_dir_path = os.path.dirname(os.path.realpath(__file__))
# file = open(os.path.join(script_dir_path, '..', 'data', 'legend_template.txt'), 'r')
# lines = file.readlines()
# print(lines)
# separator = ''
# print(separator.join(lines))

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
                   
# macro = MacroElement()
# macro._template = Template(template)