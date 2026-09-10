"""Regression checks for literal chart content at the SVG/XML boundary."""
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from svgplot import plot

SVG = '{http://www.w3.org/2000/svg}'


class SvgTextTests(unittest.TestCase):
    def render(self, title='Research & evidence', xlabel='Scope', ylabel='Value', **kwargs):
        with tempfile.TemporaryDirectory(prefix='fabius-svg-test-') as tmp:
            output = Path(tmp) / 'chart.svg'
            series = kwargs.pop('series', [{'x': [0, 1], 'y': [0, 1]}])
            plot(output, title, xlabel, ylabel, series, (0, 1), (0, 1), **kwargs)
            return ET.fromstring(output.read_text())

    def test_ordinary_ampersand_is_literal_in_title(self):
        root = self.render()
        self.assertEqual(root.find(SVG + 'title').text, 'Research & evidence')
        self.assertIn('Research & evidence', [node.text for node in root.findall(SVG + 'text')])

    def test_every_text_field_preserves_special_characters_and_unicode(self):
        labels = {name: name + ' & <value> "quoted" \'single\' שלום' for name in
                  ['title', 'x', 'y', 'xtick', 'ytick', 'vline', 'point', 'note', 'legend', 'shade']}
        root = self.render(title=labels['title'], xlabel=labels['x'], ylabel=labels['y'],
                           xticks=[(0, labels['xtick'])], yticks=[(0, labels['ytick'])],
                           vlines=[{'x': 0.5, 'label': labels['vline']}],
                           points=[{'x': 0.5, 'y': 0.5, 'label': labels['point']}],
                           notes=[{'x': 0.5, 'y': 0.5, 't': labels['note']}],
                           legend=[(labels['legend'], '#222222')],
                           shade=[{'x0': 0.2, 'x1': 0.4, 'label': labels['shade']}])
        texts = [node.text for node in root.findall(SVG + 'text')]
        for label in labels.values():
            self.assertIn(label, texts)
        self.assertEqual(root.find(SVG + 'title').text, labels['title'])

    def test_markup_stays_text_and_attributes_cannot_break_out(self):
        text = '</text><script>throw new Error("injected")</script><text>'
        attribute = '#222222" onload="alert(1)'
        root = self.render(title=text, xlabel=text, ylabel=text,
                           series=[{'x': [0, 1], 'y': [0, 1], 'color': attribute, 'width': attribute, 'dash': attribute}],
                           shade=[{'x0': 0.1, 'x1': 0.2, 'color': attribute, 'opacity': attribute, 'textcolor': attribute, 'label': text}],
                           vlines=[{'x': 0.5, 'color': attribute, 'label': text}],
                           points=[{'x': 0.5, 'y': 0.5, 'color': attribute, 'anchor': attribute, 'label': text}],
                           notes=[{'x': 0.5, 'y': 0.5, 'anchor': attribute, 'color': attribute, 't': text}],
                           legend=[(text, attribute)])
        self.assertFalse(root.findall('.//' + SVG + 'script'))
        for node in root.iter():
            self.assertNotIn('onload', node.attrib)
        self.assertEqual(root.find(SVG + 'polyline').get('stroke'), attribute)
        self.assertEqual(root.find(SVG + 'title').text, text)

    def test_disallowed_xml_characters_fail_explicitly(self):
        for value in ['null\x00', 'surrogate\ud800', 'noncharacter\uffff']:
            with self.subTest(value=repr(value)):
                with self.assertRaisesRegex(ValueError, 'XML 1.0'):
                    self.render(title=value)

    def test_plain_data_geometry_is_preserved(self):
        root = self.render(title='Plain title')
        self.assertEqual(root.get('viewBox'), '0 0 660 410')
        self.assertEqual(root.find(SVG + 'polyline').get('points'), '74.0,350.0 634.0,48.0')


if __name__ == '__main__':
    unittest.main()
