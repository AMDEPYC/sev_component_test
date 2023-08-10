'''
Component tests to test availability of SNP in a system.
'''
import os
import ioctl
from packaging import version
from component_tests import readmsr
from message_printing import print_warning_message

def check_fw_version_for_snp():
    '''
    Use SEV_PLATFORM_STATUS to find the current fw version in the system.
    If FW version is not at least 1.51, SNP will not be usable.
    '''
    # Turns true if test passes
    test_result = False
    # Name of component being tested
    component = "System SEV firmware version"
    # Expected test result
    expectation = "SEV-SNP API VERSION 1.51"
    # Will change to what the test finds
    found_result = ""
    # Command being used
    command = "SEV_PLATFORM_STATUS"

    # Use sev platform status ioctl
    sev_plat_status = ioctl.run_sev_platform_status()

    found_result = str(sev_plat_status.api_major) + "." + str(sev_plat_status.api_minor)

    # Compare with 1.51 version
    if version.parse(found_result) >= version.parse("1.51"):
        test_result = True

    return component, command, found_result, expectation, test_result

def check_if_snp_enabled():
    '''
    Check the msr address 0xC0010010 bit 24 to see if snp is enabled in the system.
    '''
    # Turns true if test passes
    test_result = False
    # Name of component being tested
    component = "SNP enabled in MSR"
    # Expected test result
    expectation = "MSR 0xC0010010 bit 24 is 1"
    # Will change to what the test finds
    found_result = ""
    # Command being used
    command = "MSR 0xC0010010"

    try:
        # Read the MSR and bit value 24
        msr_value = readmsr(0xC0010010)
        bin_value = bin(msr_value)[2:][::-1]
        snp_val = bin_value[24]
        # If bit value equals 1 then test passes
        if int(snp_val) == 1:
            test_result = True
        # Result
        found_result = "MSR 0xC0010010 bit 23 is " + str(snp_val)
        return component, command, found_result, expectation, test_result
    except OSError as err:
        # Could not read the msr, print a warning and return a failure
        print_warning_message(component, f"Failed to read the desired MSR: {err}")
        # Return results
        found_result = 'Failed to read MSR'
        return component, command, found_result, expectation, test_result

def check_snp_init():
    '''
    Check the SNP_PLATFORM_STATUS to see if SNP is init.
    '''
    # Turns true if test passes
    test_result = False
    # Name of component being tested
    component = "SNP INIT"
    # Expected test result
    expectation = "1"
    # Will change to what the test finds
    found_result = ""
    # Command being used
    command = "SNP_PLATFORM_STATUS"

    # Use snp ioclt to find if snp is init in the system
    snp_plat_status = ioctl.run_snp_platform_status()
    found_result = str(snp_plat_status.state)

    if found_result == expectation:
        test_result = True

    return component, command, found_result, expectation, test_result

def check_rmp_init():
    '''
    Check the SNP_PLATFORM_STATUS to see if RMP is init.
    '''
    # Turns true if test passes
    test_result = False
    # Name of component being tested
    component = "RMP INIT"
    # Expected test result
    expectation = "1"
    # Will change to what the test finds
    found_result = ""
    # Command being used
    command = "SNP_PLATFORM_STATUS"

    #Use snp ioclt to find if rmp is init in the system
    snp_plat_status = ioctl.run_snp_platform_status()

    found_result = str(snp_plat_status.is_rmp_init)

    if found_result == expectation:
        test_result = True

    return component, command, found_result, expectation, test_result

def get_rmp_address():
    '''
    Check the msr addresses 0xC0010132 - 0xC0010133 to get the rmp address range.
    '''
    # Turns true if test passes
    test_result = False
    # Name of component being tested
    component = "RMP table addresses"
    # Expected test result
    expectation = "RMP table physical address range xxx - xxx"
    # Will change to what the test finds
    found_result = ""
    # Command being used
    command = "MSR 0xC0010132 - 0xC0010133"

    try:
        # Read the msr for rmp addresses
        rmp_base = readmsr(0xC0010132)
        rmp_end = readmsr(0xC0010133)
        # If both are filled pass the test
        if rmp_base and rmp_end:
            test_result = True

        # Format the found result
        found_result = ("RMP table physical address range "
                        + str(hex(rmp_base)) + " - " + str(hex(rmp_end)))
  
        return component, command, found_result, expectation, test_result
    except OSError as err:
        # Could not read the msr, print a warning and return a failure
        print_warning_message(component, f"Failed to read the desired MSR: {err}")
        # Return results
        found_result = 'Failed to read MSR'
        return component, command, found_result, expectation, test_result

def compare_tcb_versions():
    '''
    Make sure that the reported TCB and the current TCB versions match up.
    '''
    # Turns true if test passes
    test_result = False
    # Name of component being tested
    component = "Comparing TCB versions"
    # Expected test result
    expectation = "Current TCB matches reported TCB"
    # Will change to what the test finds
    found_result = ""
    # Command being used
    command = "SNP_PLATFORM_STATUS"

    # Use ioctl to get both tcb verion and reported tcb
    snp_plat_status = ioctl.run_snp_platform_status()

    current_tcb = str(snp_plat_status.tcb_version)
    reported_tcb = str(snp_plat_status.reported_tcb)

    if reported_tcb == current_tcb:
        test_result = True

    found_result = "Current TCB: " + current_tcb + " Reported TCB: " + reported_tcb

    return component, command, found_result, expectation, test_result

def find_iommu_enablement():
    '''
    Check for path /sys/kernel/iommu_groups/ to verify iommu enablement.
    '''
    # Turns true if test passes
    test_result = False
    # Name of component being tested
    component = "Checking IOMMU enablement"
    # Expected test result
    expectation = "/sys/kernel/iommu_groups/ exists"
    # Will change to what the test finds
    found_result = ""
    # Command being used
    command = "find /sys/kernel/iommu_groups/"

    # Check if path exists, if it does, IOMMU is probably enabled
    if os.path.exists("/sys/kernel/iommu_groups/"):
        found_result = "/sys/kernel/iommu_groups/ exists"
        test_result = True
    else:
        found_result = "/sys/kernel/iommu_groups/ does not exist"

    return component, command, found_result, expectation, test_result
