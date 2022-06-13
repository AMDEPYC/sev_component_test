'''Testing for local_vm_test functions'''
from sev_component_test import local_vm_test


def test_create_vm_dictionary():
    '''
    Testing for create_vm_dictionary
    '''
    raw_vm_list = [
        '1234 qemu-system-x86_64 -kvm ',
        '5634 /usr/libexec/qemu-kvm -enable-kvm -cpu EPYC -machine q35 -smp 4,maxcpus=64 -m 2048M,slots=5,maxmem=30G',
        '3434 qemu-system-x86_64 -enable-kvm -cpu EPYC -machine q35 -smp 4,maxcpus=64 -m 2048M,slots=5,maxmem=30G']
    expected_dictionary = {
        '1234': 'qemu-system-x86_64 -kvm',
        '5634': '/usr/libexec/qemu-kvm -enable-kvm -cpu EPYC -machine q35 -smp 4,maxcpus=64 -m 2048M,slots=5,maxmem=30G',
        '3434': 'qemu-system-x86_64 -enable-kvm -cpu EPYC -machine q35 -smp 4,maxcpus=64 -m 2048M,slots=5,maxmem=30G'
    }

    assert local_vm_test.create_vm_dictionary(raw_vm_list) == expected_dictionary

def test_find_virtual_machine():
    '''
    Testing find_virtual_machine
    '''
    example_dictionary = {
        '1234': 'qemu-system-x86_64 -kvm',
        '5634': '/usr/libexec/qemu-kvm -enable-kvm -cpu EPYC -machine q35 -smp 4,maxcpus=64 -m 2048M,slots=5,maxmem=30G',
        '3434': 'qemu-system-x86_64 -enable-kvm -cpu EPYC -machine q35 -smp 4,maxcpus=64 -m 2048M,slots=5,maxmem=30G'
    }

    test_command = '/usr/libexec/qemu-kvm -enable-kvm -cpu EPYC -machine q35 -smp 4,maxcpus=64 -m 2048M,slots=5,maxmem=30G'
    expected_pid = '5634'

    assert local_vm_test.find_virtual_machine(test_command,example_dictionary) == expected_pid
