"""Verify aspect hints preserve the window manager's other sizing constraints."""

from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'package'))
from Xlib import Xutil
from Xlib.protocol.rq import DictWrapper
from window_aspect import set_x11_aspect_ratio


class WindowAspectTests(unittest.TestCase):
    def test_existing_size_hints_are_preserved(self):
        display = Mock()
        window = display.create_resource_object.return_value
        window.get_wm_normal_hints.return_value = DictWrapper({
            'flags': Xutil.PMinSize, 'min_width': 200, 'min_height': 100,
        })
        with patch('window_aspect.Display', return_value=display):
            set_x11_aspect_ratio(123, 1012, 346)
        hints = window.set_wm_normal_hints.call_args.args[0]
        self.assertEqual(hints['flags'], Xutil.PMinSize | Xutil.PAspect | Xutil.PBaseSize)
        self.assertEqual((hints['min_width'], hints['min_height']), (200, 100))
        self.assertEqual(hints['min_aspect'], (1012, 346))
        self.assertEqual(hints['max_aspect'], (1012, 346))
        self.assertEqual((hints['base_width'], hints['base_height']), (0, 0))
        display.sync.assert_called_once()
        display.close.assert_called_once()

    def test_connection_is_closed_on_error(self):
        display = Mock()
        display.create_resource_object.side_effect = RuntimeError('Window unavailable')
        with patch('window_aspect.Display', return_value=display), self.assertRaises(RuntimeError):
            set_x11_aspect_ratio(123, 1012, 346)
        display.close.assert_called_once()
