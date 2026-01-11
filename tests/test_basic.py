"""
Our first test - testing basic math to understand pytest.
"""

def add(a, b):
    """Simple function to test"""
    return a + b


def test_add_two_numbers():
    """
    Test function names MUST start with 'test_'
    pytest automatically finds and runs these functions
    """
    result = add(2, 3)
    assert result == 5  # If this is False, test fails
    

def test_add_negative_numbers():
    """You can have multiple tests for the same function"""
    result = add(-1, -1)
    assert result == -2


def test_add_will_fail():
    """This test will FAIL on purpose to show you what failure looks like"""
    result = add(2, 2)
    assert result == 5  # This is wrong! 2+2=4, not 5
