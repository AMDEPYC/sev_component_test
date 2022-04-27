'''Testing for memory_reader functions'''
from sev_component_test import memory_reader

def test_hex_to_decimal():
    '''
    Testing for hex_to_decimal
    '''
    hex_number = "77c7f"
    decimal_number = 490623

    assert memory_reader.hex_to_decimal(hex_number) == decimal_number,\
        "hex number not converted to the correct decimal integer"

def test_convert_gb_to_bytes():
    '''
    Testing convert gb_to_bytes
    '''
    test_num = 2
    expected_num = 2147483648
    assert memory_reader.convert_gb_to_bytes(test_num) == expected_num,\
        "GB not converted to the right amount of bytes"

def test_convert_mb_to_bytes():
    '''
    Testing for convert_mb_to_bytes
    '''
    test_num = 1024
    expected_num = 1073741824
    assert memory_reader.convert_mb_to_bytes(test_num) == expected_num,\
        "MB not converted to the right number of bytes"

def test_get_memory_size():
    '''
    Testing get_memory_size
    '''
    test_string_1 = "qemu-system-x86_64 -enable-kvm -cpu EPYC -machine q35 -smp 4,maxcpus=64 -m 2048M,slots=5,maxmem=30G"
    result_string_1 = "2147483648"
    test_string_2 = "qemu-system-x86_64 -enable-kvm -cpu EPYC -machine q35 -smp 4,maxcpus=64 -m 1024,slots=5"
    result_string_2 = "1073741824"
    test_string_3 = "qemu-system-x86_64 -enable-kvm -cpu EPYC -machine q35 -smp 4,maxcpus=64 -m 3G -device"
    result_string_3 = "3221225472"
    test_string_4 = "qemu-system-x86_64 -enable-kvm -cpu EPYC -machine q35 -smp 4,maxcpus=64 -device"
    result_string_4 = "134217728"

    assert memory_reader.get_memory_size(test_string_1) == result_string_1,\
        "The correct amount of bytes was not retrieved from the test string"
    assert memory_reader.get_memory_size(test_string_2) == result_string_2,\
        "The correct amount of bytes was not retrieved from the test string"
    assert memory_reader.get_memory_size(test_string_3) == result_string_3,\
        "The correct amount of bytes was not retrieved from the test string"
    assert memory_reader.get_memory_size(test_string_4) == result_string_4,\
        "The correct amount of bytes was not retrieved from the test string"