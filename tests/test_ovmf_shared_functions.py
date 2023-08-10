'''Testing for the omvf_shared_functions'''
import datetime
from sev_component_test import ovmf_functions


def test_get_ovmf_version():
    '''
    Testing for get_ovmf_version
    '''
    test_string_1 = "ii  ovmf 2020.11-4ubuntu0.1 all UEFI firmware for 64-bit x86 virtual machines"
    pass_string_1 = "2020.11"
    test_string_2 = "edk2-ovmf-20210527gite1999b264f1f-3.el8.noarch"
    pass_string_2 = "20210527"
    test_string_3 = "omvf-x86_64~20200627blahblah"
    pass_string_3 = "20200627"
    test_string_4 = "ovmf-202202-3.1.x86_64"
    pass_string_4 = "202202"

    assert ovmf_functions.get_ovmf_version(test_string_1) == pass_string_1,\
        "the wrong ovmf version was retrieved from the string"
    assert ovmf_functions.get_ovmf_version(test_string_2) == pass_string_2,\
        "the wrong ovmf version was retrieved from the string"
    assert ovmf_functions.get_ovmf_version(test_string_3) == pass_string_3,\
        "the wrong ovmf version was retrieved from the string"
    assert ovmf_functions.get_ovmf_version(test_string_4) == pass_string_4,\
        "the wrong ovmf version was retrieved from the string"

def test_convert_ovmf_version_to_date():
    '''
    Testing for convert_ovmf_version_to_date
    '''
    test_date_1 = "20200627"
    pass_date_1 = datetime.date(2020,6,27)
    test_date_2 = "2020.11"
    pass_date_2 = datetime.date(2020,11,1)
    test_date_3 = "202105"
    pass_date_3 = datetime.date(2021,5,1)
    test_date_4 = "2020.11.14"
    pass_date_4 = datetime.date(2020,11,14)

    assert ovmf_functions.convert_ovmf_version_to_date(test_date_1) == pass_date_1,\
        "String was not converted to the correct date."
    assert ovmf_functions.convert_ovmf_version_to_date(test_date_2) == pass_date_2,\
        "String was not converted to the correct date."
    assert ovmf_functions.convert_ovmf_version_to_date(test_date_3) == pass_date_3,\
        "String was not converted to the correct date."
    assert ovmf_functions.convert_ovmf_version_to_date(test_date_4) == pass_date_4,\
        "String was not converted to the correct date."
