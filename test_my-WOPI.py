myWOPI = __import__("my-WOPI")
import pytest

def test_checkType():
    td = {"goodkey":"badvalue"}
    with pytest.raises(Exception):
        my-WOPI.checkType(td,"goodkey",int)