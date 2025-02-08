from textwrap import dedent

import libcst as cst

from django_unasyncify.config import Config
from django_unasyncify.transform import UnasyncifyMethod


def assert_transforms(code, config, expected):
    code_cst = cst.parse_module(dedent(code))
    transformer = UnasyncifyMethod(config)

    transformed = code_cst.visit(transformer)

    assert str(transformed.code) == dedent(expected)


def test_name_transform():
    before = """
    self.aconnection
    self.aconnection.aconnect()
    await self.aconnection.aconnect()
    """

    expected = """
    self.connection
    self.connection.aconnect()
    self.connection.connect()
    """

    config = Config(attribute_renames={"aconnection": "connection"})
    assert_transforms(before, config, expected)
