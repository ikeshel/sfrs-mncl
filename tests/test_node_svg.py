"""Equipment-label substitution must stay local to each rendered SVG."""

from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'package'))
from node_svg import svg_for_host, svg_for_power_led

NS = {'svg': 'http://www.w3.org/2000/svg'}


class NodeSvgTests(unittest.TestCase):
    def test_music_template_has_independent_host_labels(self):
        path = ROOT / 'images/intel_music.svg'
        original = path.read_bytes()
        template = ET.fromstring(original)
        for hostname in ('x86l-259', 'x86l-260', 'x86l-261'):
            with self.subTest(hostname=hostname):
                result = ET.fromstring(svg_for_host(original, hostname))
                label = result.find('.//svg:g[@id="g43"]/svg:text[@id="host_name"]', NS)
                self.assertEqual(''.join(label.itertext()).strip(), hostname)
                self.assertEqual(label.attrib, template.find('.//svg:text[@id="host_name"]', NS).attrib)
                self.assertEqual(result.attrib, template.attrib)
                # All other text, including LED labels, must remain unchanged.
                self.assertEqual(
                    [ET.tostring(t) for t in result.findall('.//svg:text', NS) if t.get('id') != 'host_name'],
                    [ET.tostring(t) for t in template.findall('.//svg:text', NS) if t.get('id') != 'host_name'],
                )
        self.assertEqual(path.read_bytes(), original)

    def test_nested_inkscape_text_and_xml_escaping(self):
        original = b'''<svg xmlns="http://www.w3.org/2000/svg">
          <text>X86-XXX</text>
          <g id="g43"><text id="text35" fill="red"><tspan font-size="13">X86-</tspan><tspan>XXX</tspan></text>
          <text>HDD</text></g></svg>'''
        result = ET.fromstring(svg_for_host(original, 'node<&>'))
        label = result.find('.//svg:text[@id="text35"]', NS)
        self.assertEqual(''.join(label.itertext()), 'node<&>')
        self.assertEqual(label.find('svg:tspan', NS).get('font-size'), '13')
        self.assertEqual(result.find('svg:text', NS).text, 'X86-XXX')
        self.assertEqual(result.find('svg:g/svg:text[2]', NS).text, 'HDD')

    def test_renamed_text_element_is_found_by_placeholder(self):
        original = b'<svg xmlns="http://www.w3.org/2000/svg"><g id="g43"><text id="new-label">X86-XXX</text></g></svg>'
        result = ET.fromstring(svg_for_host(original, 'x86l-260'))
        self.assertEqual(result.find('.//svg:text', NS).text, 'x86l-260')

    def test_unrelated_svg_is_returned_unchanged(self):
        for original in (b'<svg xmlns="http://www.w3.org/2000/svg"><text>LAN</text></svg>',
                         b'<svg xmlns="http://www.w3.org/2000/svg"><g id="g43"><text>HDD</text></g></svg>'):
            self.assertEqual(svg_for_host(original, 'x86l-260'), original)

    def test_x86_template_displays_plsci_and_scifi_hosts(self):
        path = ROOT / 'images/intel_x86.svg'
        original = path.read_bytes()
        template = ET.fromstring(original)
        for hostname in ('x86l-132', 'x86l-207', 'x86l-253'):
            with self.subTest(hostname=hostname):
                result = ET.fromstring(svg_for_host(original, hostname))
                label = result.find('.//svg:text[@id="text35"]', NS)
                self.assertEqual(''.join(label.itertext()).strip(), hostname)
                self.assertEqual(label.attrib, template.find('.//svg:text[@id="text35"]', NS).attrib)
                self.assertEqual(
                    [ET.tostring(t) for t in result.findall('.//svg:text', NS) if t.get('id') != 'text35'],
                    [ET.tostring(t) for t in template.findall('.//svg:text', NS) if t.get('id') != 'text35'],
                )
        self.assertEqual(path.read_bytes(), original)

    def test_placeholder_outside_group_is_supported(self):
        original = b'<svg xmlns="http://www.w3.org/2000/svg"><text id="new-label">X86-XXX</text></svg>'
        result = ET.fromstring(svg_for_host(original, 'x86l-132'))
        self.assertEqual(result.find('svg:text', NS).text, 'x86l-132')

    def test_host_name_id_takes_priority_over_legacy_label(self):
        original = b'''<svg xmlns="http://www.w3.org/2000/svg">
          <text id="text35">Other label</text>
          <text id="host_name"><tspan>X86-XXX</tspan></text></svg>'''
        result = ET.fromstring(svg_for_host(original, 'x86l-260'))
        self.assertEqual(''.join(result.find('svg:text[@id="host_name"]', NS).itertext()), 'x86l-260')
        self.assertEqual(result.find('svg:text[@id="text35"]', NS).text, 'Other label')

    def test_power_led_changes_only_its_fill_in_both_templates(self):
        for filename in ('intel_music.svg', 'intel_x86.svg'):
            path = ROOT / 'images' / filename
            original = path.read_bytes()
            customized = svg_for_host(original, 'test-host')
            for color in ('green', 'lightgreen', 'red', 'pink'):
                with self.subTest(filename=filename, color=color):
                    template = ET.fromstring(customized)
                    result = ET.fromstring(svg_for_power_led(customized, color))
                    led = result.find('.//*[@id="led_power"]')
                    original_led = template.find('.//*[@id="led_power"]')
                    self.assertEqual(led.get('fill'), color)
                    if original_led.get('style') is not None:
                        style = dict(part.split(':', 1) for part in led.get('style').split(';'))
                        self.assertEqual(style['fill'], color)
                    # Restoring the fill/style must make the entire SVG identical,
                    # including the hostname, other LEDs, transforms and dimensions.
                    for attribute in ('fill', 'style'):
                        led.attrib.pop(attribute, None)
                        if attribute in original_led.attrib:
                            led.set(attribute, original_led.get(attribute))
                    for element in (led, original_led):
                        attributes = sorted(element.attrib.items())
                        element.attrib.clear()
                        element.attrib.update(attributes)
                    self.assertEqual(ET.tostring(result), ET.tostring(template))
            self.assertEqual(path.read_bytes(), original)

    def test_power_led_is_optional_for_other_illustrations(self):
        original = b'<svg xmlns="http://www.w3.org/2000/svg"><circle id="other" fill="blue"/></svg>'
        self.assertEqual(svg_for_power_led(original, 'red'), original)


if __name__ == '__main__':
    unittest.main()
