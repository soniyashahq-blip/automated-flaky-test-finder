import random


def test_random_value():
    value = random.randint(1, 10)
    assert 1 <= value <= 10