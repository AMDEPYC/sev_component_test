'''Testing auto_vm_test'''
import pytest
from sev_component_test.sev_component_test import run_sev_test
from sev_component_test import auto_vm_test, component_tests

system_os ,_ = component_tests.get_linux_distro()

# Test for auto-VM, currently only testing sev and unencrypted vm, 
# sev-es support yet to be added to the qcow2 image.
@pytest.mark.skipif(not run_sev_test(True, system_os, False),\
    reason="Auto VM won't be able to be launched, do not test it.")
def test_auto_vm_encryption():
    '''
    Testing auto_vm_test encryption results
    '''
    encrypted_vm_test_result = auto_vm_test.automatic_vm_test(system_os, True,'sev')
    unecrypted_vm_test_result = auto_vm_test.automatic_vm_test(system_os, True,'unencrypted')

    assert encrypted_vm_test_result,"Auto VM did not launch or launched and it was not encrypted."
    assert unecrypted_vm_test_result,\
        "Auto VM did not launch or it launched and was unexpectedly encrypted."
