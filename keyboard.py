import re
import typing
import xml.etree.ElementTree as ET
from unicodedata import name
from typing import *
from jinja2 import Template

keylayout_file = 'keylayout_file'
keylayout_xml = keylayout_file + '.xml'
keylayout_html = keylayout_file + '.html'
TOFU = '\ufffd'


def mapindex_by_modifier(map_to_modifier: Dict[int, str], modifier: str) -> int:
    '''Get the index (in the XML list) of the keyboard map, given the modifiers that produce that map.'''
    return [k for k, v in map_to_modifier.items() if v == modifier][0]

def map_by_index(tree: ET.Element) -> Dict[int, Dict[int, str]]:
    '''Get the  keyboard map given the index n its XML list, given the modifiers that produce that map.'''
    def to_chr(v: str) -> str:
        return chr(int(v, 16)) if len(v) == 6 else v

    keyMapSets = tree.findall('./keyMapSet')
    assert len(keyMapSets) == 1, 'For now, only supports a single KeyMapSet in the file, found %d' % len(keyMapSets)
    theOnlykeyMapSet = keyMapSets[0]
    key_maps = {int(keyMap.attrib['index']): {
        int(oneKey.attrib['code']): to_chr(oneKey.attrib['output'])
        for oneKey in keyMap} for keyMap in theOnlykeyMapSet}
    return key_maps


def modifier_by_mapindex(tree: ET.Element) -> Dict[int, str]:
    '''Get the modifiers that produce a keyboard map, given its index in the XML.'''
    def shorten_modifier_descriptions(s: str) -> str:
        '''Abbreviate the names of the modifiers, using Mac modifier icons. Separate with semicolons.'''
        conversions = {'Shift': '⇧', 'Option': '⌥', 'Command': '⇧', 'Control': '⌃',
                       ' ': '; '}
        for in_, out in conversions.items():
            s = re.sub(in_, out, s, flags=re.IGNORECASE)

        return s
    keyMapSelects = tree.find("./modifierMap").findall('./keyMapSelect')
    return {
        int(keyMapSelect.attrib['mapIndex']):
            shorten_modifier_descriptions(keyMapSelect.find('./modifier').attrib['keys'])
        for keyMapSelect in keyMapSelects}


def tweaked_xml() -> str:
    '''Read the XML and fix entity markers.'''
    def remove_entity_markers(xml_s):
        '''
        Reformat entities like &#78e7 as 0x78e7. This is necessary because
        the XML parser can choke on inability to resolve entities, which
        we do not want to do anyway.
        '''
        return re.sub(r'&#(x[\dA-F]{4});', r'0\g<1>', xml_s)

    with open(keylayout_xml, 'r') as f:
        return remove_entity_markers(f.read())


def build_table(ascii_keyboard, unmodified_nonasciii_keyboard, map_by_index_,
                modifier_by_mapindex_: Dict[int, str])-> List[Dict[str, str]]:

    def sort_by_asciifirst_and_moddescription_length(modifier_by_mapindex_, ascii_keyboard_):
        modifier_by_map_index_items = list(modifier_by_mapindex_.items())
        '''
        We are using length of modifiers to sort the keyboards, since a single
        modifier is more "common" than multiple modifiers, and NO modifiers
        is most common of all. However, we put the ASCII keyboard first.
        '''
        modifier_by_map_index_items.sort(key=lambda item: (item[1].count(';'), item[1]))
        ascii_keyboard_dict = {0: ascii_keyboard_}  # Put it first
        modifier_by_mapindex_ = dict(modifier_by_map_index_items)
        modifier_by_mapindex_ = {**ascii_keyboard_dict, **modifier_by_mapindex_}
        return modifier_by_mapindex_

    def unicode_name(s: str) -> str:
        '''Get the official unicode name for a character.'''
        if not s:
            return ""
        names = []
        for ch in s:
            try:
                names.append(name(ch))
            except ValueError:  # codepoints like 4,12,16,127
                # Code points including  1...31 and 127 have no name.

                names.append(TOFU)  # tofu

        return ' & '.join(names)

    modifier_by_mapindex_ = sort_by_asciifirst_and_moddescription_length(modifier_by_mapindex_, ascii_keyboard)
    rows = []
    for idx, modifier in modifier_by_mapindex_.items():
        modified_keyboard = map_by_index_[idx]
        for key_idx in modified_keyboard:
            modified_key = modified_keyboard[key_idx]
            if unicode_name(modified_key) not in [TOFU, '']:
                if not modifier.strip():
                    modifier = '<NONE>'
                rows.append({
                    'modifier': modifier,
                    'ascii': ascii_keyboard[key_idx],
                    'unmodified_non_ascii_key': unmodified_nonasciii_keyboard[key_idx],
                    'modified_key': modified_key,
                    'unicode_name': unicode_name(modified_key)})
    return rows


def render(title, rows:List[Dict[str,str]]):
    template = """
        <!DOCTYPE html>
        
        <html>
          <head>
            <title>{{ title|escape }}</title>
             <meta charset="UTF-8">
             <style>
                th {
                  background: #ACA
                }
                tr:nth-child(even) {background: #CAC}
                tr:nth-child(odd) {background: #EEE}
                table {
                  border: 1px solid black;
                }
             </style>
          </head>
          <body>
            <table>
             <tr><th>{%- for k in item_list[0]%}{{k.replace('_',' ').title()|escape}}{%- if not loop.last %}</th><th>{%- endif %}{%- endfor %}</th></tr>
             
              {%- for item in item_list %}
              <tr><td>{%- for v in item.values() %}{{v|escape}}{%- if not loop.last %}</td><td>{%- endif %}{%- endfor %}</td></tr> 
              {%- endfor %}
            </table>
          </body>
        </html>"""

    rendered = Template(template).render(title=title, item_list=rows)

    with open(keylayout_html, 'w') as f:
        f.write(rendered)


def main():
    tree = ET.fromstring(tweaked_xml())
    map_by_index_ = map_by_index(tree)
    modifier_by_mapindex_ = modifier_by_mapindex(tree)
    unmodified_nonasciii_keyboard = map_by_index_[mapindex_by_modifier(modifier_by_mapindex_, '')]
    ascii_keyboard = map_by_index_[0]
    item_list = build_table(ascii_keyboard, unmodified_nonasciii_keyboard, map_by_index_, modifier_by_mapindex_)
    title = tree.attrib['name']
    render(title, item_list)


if __name__ == '__main__':
    main()

pass
