import re
import typing
import xml.etree.ElementTree as ET
from unicodedata import name

from jinja2 import Template



def mapindex_by_modifier(map_to_modifier: typing.Dict[int, str], modifier: str)->int:
    return [k for k, v in map_to_modifier.items() if v == modifier][0]


def map_by_index(tree: ET.Element) -> typing.Dict[int, typing.Dict[int, str]]:
    def to_chr(v: str) -> str:
        return chr(int(v, 16)) if len(v) == 6 else v

    keyMapSets = tree.findall("./keyMapSet")
    assert len(keyMapSets) == 1, 'For now, only supports a single KeyMapSet in the file, found %d' % len(keyMapSets)
    keyMapSet = keyMapSets[0]
    key_maps = {}
    for keyMap in keyMapSet:
        key_maps[int(keyMap.attrib['index'])] = {
            int(c.attrib['code']): to_chr(c.attrib['output'].lower())
            for c in keyMap}
    return key_maps



def modifier_by_mapindex(tree: ET.Element) -> typing.Dict[int, str]:
    def shorten_modifier_descriptions(s: str) -> str:
        conversions = {'Shift': '⇧', 'Option': '⌥', 'Command': '⇧', 'Control': '⌃',
                       ' ': '; '}
        for input, output in conversions.items():
            s = re.sub(input, output, s, flags=re.IGNORECASE)

        return s

    keyMapSelects = tree.find("./modifierMap").findall('./keyMapSelect')
    return {
        int(keyMapSelect.attrib['mapIndex']): shorten_modifier_descriptions(keyMapSelect.find('./modifier').attrib['keys'])
        for keyMapSelect in keyMapSelects}


def xml_with_hexnumbers_instead_of_entities() -> str:
    """
    Reformat entities like &#78e7 as 0x78e7. This is necessary because
    the XML parser can choke on inability to resolve entities, which
    we do not want to do anyway.
    """
    keylayout_xml = 'keylayout.xml'
    with open(keylayout_xml, 'r') as f:
        xml_s = f.read()
        return re.sub(r'&#(x[\dA-F]{4});', r'0\g<1>', xml_s)



def build_table(ascii_keyboard, unmodified_nonasciii_keyboard, map_by_index,
                modifier_by_map_index_: typing.Dict[int, str]):
    def sort_by_asciifirst_and_moddescription_length(modifier_by_map_index_, ascii_keyboard):
        modifier_by_map_index_items = list(modifier_by_map_index_.items())
        # We are using length of modifiers to sort the keyboards, since a single
        # modifier is more "common" than multiple modifiers, and NO modifiers
        # is most common of all. However, we put the ASCII keyboard first.

        modifier_by_map_index_items.sort(key=lambda item: (item[1].count(';'), item[1]))
        ascii_keyboard_dict = {0: ascii_keyboard}#Put it first
        modifier_by_map_index_ = dict(modifier_by_map_index_items)
        modifier_by_map_index_ = {**ascii_keyboard_dict, **modifier_by_map_index_}
        return modifier_by_map_index_

    def unicode_name(s: str) -> str:
        if not s:
            return '<EMPTY>'
        names = []
        for ch in s:
            try:
                names.append(name(ch))
            except ValueError as ve:  # codepoints like 4,12,16,127
                # Code points including  1...31 and 127
                names.append('\ufffd')  # tofu
        return ';'.join(names)

    modifier_by_map_index_ = sort_by_asciifirst_and_moddescription_length(modifier_by_map_index_, ascii_keyboard)
    rows = []
    for idx, modifier in modifier_by_map_index_.items():
        modified_keyboard = map_by_index[idx]
        for key_idx in modified_keyboard:
            modified_key = modified_keyboard[key_idx]
            if  unicode_name(modified_key) not in ['\ufffd', '<EMPTY>']:
                if not modifier.strip():
                    modifier="<NONE>"
                rows.append({
                  #  'keyboard_index': idx,
                  #  'key_index': key_idx,
                    'modifier': modifier,
                    'ascii': (ascii_keyboard[key_idx]),
                    'unmodified_non_ascii_key': (unmodified_nonasciii_keyboard[key_idx]),
                    'modified_key': modified_key,
                    'unicode_name': unicode_name(modified_key)})
    return rows





def render(title,item_list):
    template = """
        <!DOCTYPE html>
        
        <html>
          <head>
            <title>{{ title|escape }}</title>
             <meta charset="UTF-8">
          </head>
          <body>
            <table>
             <th>{%- for k in item_list[0]%}{{k.replace('_',' ').title()|escape}}{%- if not loop.last %}</td><td>{%- endif %}{%- endfor %}</td>
             </th>
              {%- for item in item_list %}
              <tr>
                 <td>{%- for v in item.values() %}{{v|escape}}{%- if not loop.last %}</td><td>{%- endif %}{%- endfor %}</td>
              </tr> 
          {%- endfor %}
            <table/>
          </body>
        </html>"""
    tmpl = Template(template)
    rendered = tmpl.render(title=title,item_list=item_list)
    print(rendered)
    with open('keyboards.html','w') as f:
        f.write(rendered)

def main():
    tree = ET.fromstring(xml_with_hexnumbers_instead_of_entities())
    map_by_index_ = map_by_index(tree)
    modifier_by_mapindex_ = modifier_by_mapindex(tree)
    unmodified_nonasciii_keyboard = map_by_index_[mapindex_by_modifier(modifier_by_mapindex_, '')]
    ascii_keyboard = map_by_index_[0]
    item_list = build_table(ascii_keyboard, unmodified_nonasciii_keyboard, map_by_index_, modifier_by_mapindex_)
    title=tree.attrib['name']
    render(title,item_list)



if __name__ == '__main__':
    main()

pass
