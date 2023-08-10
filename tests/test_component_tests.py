'''Testing for component_tests functions'''
from sev_component_test import component_tests

def test_get_sme_string():
    '''
    Testing for get_sme_string
    '''
    test_string = "[    1.921098] AMD Memory Encryption Features active: SME"
    expected_string = "AMD Memory Encryption Features active: SME"
    assert component_tests.get_sme_string(test_string) == expected_string,\
        "get_sme did not format the string correctly"

def test_get_version_num():
    '''
    Testing for get_version_num
    '''
    version_test_1 = "5.12.134.123 foo"
    version_test_2 = "5.12.134"
    version_test_3 = "1.23"
    version_test_4 = "1.32 foo"
    version_test_5 = '5.11-foo'

    assert component_tests.get_version_num(version_test_1) == "5.12.134",\
        "get_version_test did not format the version correctly"
    assert component_tests.get_version_num(version_test_2) == "5.12.134",\
        "get_version_test did not format the version correctly"
    assert component_tests.get_version_num(version_test_3) == "1.23.0",\
        "get_version_test did not format the version correctly"
    assert component_tests.get_version_num(version_test_4) == "1.32.0",\
        "get_version_test did not format the version correctly"
    assert component_tests.get_version_num(version_test_5) == "5.11.0",\
        "get_version_test did not format the version correctly"
