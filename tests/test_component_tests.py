'''Testing for component_tests functions'''
from sev_component_test import component_tests

def test_hex_to_binary():
    '''
    Test for hex_to_binary
    '''
    hex_num = "223d9"
    bin_num = "100010001111011001"
    assert component_tests.hex_to_binary(hex_num) == bin_num,\
        "Hex number not converted to binary correctly"

def test_check_eax():
    '''
    Test for check_eax
    '''
    pass_sev_case = [[], ['0', '0', '0', '0', '0', '0', '0', '0', '0', 'F']]
    fail_sev_case = [[], ['0', '0', '0', '0', '0', '0', '0', '0', '0', 'D']]
    pass_sme_case = [[], ['0', '0', '0', '0', '0', '0', '0', '0', '0', 'D']]
    fail_sme_case = [[], ['0', '0', '0', '0', '0', '0', '0', '0', '0', 'C']]

    assert component_tests.check_eax(pass_sev_case, "SEV"),\
        "check_eax did not find the correct decimal value"
    assert not component_tests.check_eax(fail_sev_case, "SEV"),\
        "check_eax did not find the correct decimal value"
    assert component_tests.check_eax(pass_sme_case, "SME"),\
        "check_eax did not find the correct decimal value"
    assert not component_tests.check_eax(fail_sme_case, "SME"),\
        "check_eax did not find the correct decimal value"
    assert component_tests.check_eax(pass_sev_case,"SNP") is None,\
        "check_eax did not return none for a non-supported feature"

def test_get_sme_string():
    '''
    Testing for get_sme_string
    '''
    test_string = "[    1.921098] AMD Memory Encryption Features active: SME"
    expected_string = "AMD Memory Encryption Features active: SME"
    assert component_tests.get_sme_string(test_string) == expected_string,\
        "get_sme did not format the string correctly"

def test_get_asid_num():
    '''
    Testing get_asid_num
    '''
    test_string = "5401294214421 ASIDs"
    expected_string = "5401294214421"
    assert component_tests.get_asid_num(test_string) == expected_string,\
        "get_asid_num did not format the string correctly"

def test_get_sev_string_and_asids():
    '''
    Testing for get_sev_string_and_asids
    '''
    # Test 1
    test_string_1 = "[   12.612470] SEV supported: 493 ASIDs"
    expected_support_1 = "SEV supported"
    expected_available_asids_1 = "493 ASIDs"
    expected_asids_1 = "493"
    test_result_1 = component_tests.get_sev_string_and_asids(test_string_1)
    # Test 2
    test_string_2 = "[   12.612470] SEV supported"
    expected_support_2 = "SEV supported"
    expected_available_asids_2 = ''
    expected_asids_2 = False
    test_result_2 = component_tests.get_sev_string_and_asids(test_string_2)
    # Test 3
    test_string_3 = "[   12.612471] SEV-ES supported: 16 ASIDs"
    expected_support_3 = "SEV-ES supported"
    expected_available_asids_3 = "16 ASIDs"
    expected_asids_3 = "16"
    test_result_3 = component_tests.get_sev_string_and_asids(test_string_3)
    
    assert test_result_1 == (expected_support_1, expected_available_asids_1,expected_asids_1),\
        "dmesg string not formatted correctly"
    assert test_result_2 == (expected_support_2, expected_available_asids_2,expected_asids_2),\
        "dmesg string not formatted correctly"
    assert test_result_3 == (expected_support_3, expected_available_asids_3,expected_asids_3),\
        "dmesg string not formatted correctly"

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
