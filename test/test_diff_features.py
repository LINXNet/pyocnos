"""
TBD
"""
# pylint: disable=invalid-name

import pytest
from pyocnos.diff import build_xml_diff

# Add a test for not supporting diffing two simple node
def test_diff_cannot_compare_simple_xml():
    with pytest.raises(ValueError):
        build_xml_diff("<data>100</data>", "<data>200</data>")

    with pytest.raises(ValueError):
        build_xml_diff("<data>100</data>", "<data><foo>200</foo></data>")


def test_diff_mismatched_root_tag():
    """
    Scenario: Exception shall be thrown when two tree does have have the same root tag.
    """

    with pytest.raises(ValueError):
        build_xml_diff("<data><foo>100</foo></data>", "<config><foo>200</foo></config>")


def test_diff_identical_xml():
    pass

