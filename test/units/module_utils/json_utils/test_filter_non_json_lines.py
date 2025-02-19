# -*- coding: utf-8 -*-
# (c) 2016, Matt Davis <mdavis@ansible.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations

import unittest
from ansible.module_utils.json_utils import _filter_non_json_lines
import pytest


class TestAnsibleModuleExitJson(unittest.TestCase):
    single_line_json_dict = """{"key": "value", "olá": "mundo"}"""
    single_line_json_array = """["a","b","c"]"""
    multi_line_json_dict = """{
"key":"value"
}"""
    multi_line_json_array = """[
"a",
"b",
"c"]"""

    all_inputs = [
        single_line_json_dict,
        single_line_json_array,
        multi_line_json_dict,
        multi_line_json_array,
    ]

    junk = ["single line of junk", "line 1/2 of junk\nline 2/2 of junk"]

    unparsable_cases = (
        "No json here",
        '"olá": "mundo"',
        '{"No json": "ending"',
        '{"wrong": "ending"]',
        '["wrong": "ending"}',
    )

    def test_just_json(self):
        for i in self.all_inputs:
            filtered, warnings = _filter_non_json_lines(i)
            self.assertEqual(filtered, i)
            self.assertEqual(warnings, [])

    def test_leading_junk(self):
        for i in self.all_inputs:
            for j in self.junk:
                filtered, warnings = _filter_non_json_lines(j + "\n" + i)
                self.assertEqual(filtered, i)
                self.assertEqual(warnings, [])

    def test_trailing_junk(self):
        for i in self.all_inputs:
            for j in self.junk:
                filtered, warnings = _filter_non_json_lines(i + "\n" + j)
                self.assertEqual(filtered, i)
                self.assertEqual(
                    warnings,
                    ["Module invocation had junk after the JSON data: %s" % j.strip()],
                )

    def test_leading_and_trailing_junk(self):
        for i in self.all_inputs:
            for j in self.junk:
                filtered, warnings = _filter_non_json_lines("\n".join([j, i, j]))
                self.assertEqual(filtered, i)
                self.assertEqual(
                    warnings,
                    ["Module invocation had junk after the JSON data: %s" % j.strip()],
                )

    def test_unparsable_filter_non_json_lines(self):
        for i in self.unparsable_cases:
            self.assertRaises(ValueError, _filter_non_json_lines, data=i)

    def test_empty_input(self):  # Test with an empty string
        # My change: Added the correct error to raise
        with pytest.raises(ValueError):
            filtered, warnings = _filter_non_json_lines("")
            self.assertEqual(
                filtered, None
            )  # Or assert it's None, or whatever your function returns
            self.assertEqual(warnings, [])

    def test_whitespace_only(self):  # Test with only whitespace
        # My change: Added the correct error to raise
        with pytest.raises(ValueError):
            filtered, warnings = _filter_non_json_lines("   \n\t  ")
            self.assertEqual(
                filtered, ""
            )  # Or None, or original whitespace if that's the desired behaviour
            self.assertEqual(warnings, [])

    def test_json_with_internal_junk(
        self,
    ):  # Test with junk *inside* the JSON, but still valid structure
        json_with_junk = """{"key": "value\n junk", "olá": "mundo"}"""
        filtered, warnings = _filter_non_json_lines(json_with_junk)
        self.assertEqual(
            filtered, json_with_junk
        )  # Or perhaps you want to filter this kind of junk too?
        self.assertEqual(warnings, [])  # Or warnings if you decide to handle this case

    def test_json_with_unicode_surrogates(self):
        json_with_surrogates = """{"key": "\\ud83d\\ude00"}"""  # Smiling face emoji
        filtered, warnings = _filter_non_json_lines(json_with_surrogates)
        self.assertEqual(filtered, json_with_surrogates)
        self.assertEqual(warnings, [])

    def test_mixed_junk_and_json(self):  # More complex mixed input
        mixed_input = """junk before\n{"key": "value"}\njunk after"""
        filtered, warnings = _filter_non_json_lines(mixed_input)
        self.assertEqual(filtered, """{"key": "value"}""")
        self.assertEqual(
            warnings, ["Module invocation had junk after the JSON data: junk after"]
        )

    def test_json_with_escaped_characters(self):
        json_with_escapes = """{"key": "val\\\"ue", "olá": "mun\\ndo"}"""
        filtered, warnings = _filter_non_json_lines(json_with_escapes)
        self.assertEqual(filtered, json_with_escapes)
        self.assertEqual(warnings, [])

    def test_empty_json_object(self):  # Test with an empty json object
        filtered, warnings = _filter_non_json_lines("{}")
        self.assertEqual(filtered, "{}")
        self.assertEqual(warnings, [])

    def test_empty_json_array(self):  # Test with an empty json array
        filtered, warnings = _filter_non_json_lines("[]")
        self.assertEqual(filtered, "[]")
        self.assertEqual(warnings, [])
