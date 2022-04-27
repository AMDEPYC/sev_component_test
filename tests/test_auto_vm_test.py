'''Testing auto_vm_test'''
import pytest
from sev_component_test.sev_component_test import run_sev_test
from sev_component_test import auto_vm_test, component_tests

system_os ,_ = component_tests.get_linux_distro()

@pytest.mark.skipif(not run_sev_test(True, system_os, False),\
    reason="Auto VM won't be able to be launche, do not test it.")
def test_auto_vm_encryption():
    '''
    Testing auto_vm_test encryption results
    '''
    encrypted_vm_test_result = auto_vm_test.automatic_vm_test(system_os, True)
    unecrypted_vm_test_result = auto_vm_test.unencrypted_automatic_vm_test(system_os, True)

    assert encrypted_vm_test_result,"Auto VM did not launch or launched and it was not encrypted"
    assert not unecrypted_vm_test_result,\
        "Auto VM launched or it launched and it gave us encryption when we weren't expecting any."
