'''Testing Entropy Test'''
from sev_component_test import encryption_test

def test_entropy_encryption_test():
    '''
    Test entropy_encryption_test
    '''
    low_entropy_string = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    high_entropy_string = "M3mmbjOlIZr11OZoULqUWyFA1EpOdZAEcmaC64E/Ft9MRfDEYE7qDJm+9ezGQY15=="

    assert encryption_test.entropy_encryption_test(low_entropy_string.encode("utf-8")) <= 3
    assert encryption_test.entropy_encryption_test(high_entropy_string.encode("utf-8")) >= 6
