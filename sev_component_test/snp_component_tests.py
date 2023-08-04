'''
Component tests to test availability of SNP in a system.
'''
import subprocess
import ioctl
from packaging import version
from component_tests import readmsr
from message_printing import print_warning_message

def check_fw_version_for_snp():
    '''
    Use SEV_PLATFORM_STATUS to find the current fw version in the system.
    If FW version is not newest test fails, SNP would not be usable.
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

    sev_plat_status = ioctl.run_sev_platform_status()

    found_result = str(sev_plat_status.api_major) + "." + str(sev_plat_status.api_minor)

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
        msr_value = readmsr(0xC0010010)
        bin_value = bin(msr_value)[2:][::-1]
        snp_val = bin_value[24]
        if int(snp_val) == 1:
            test_result = True
        found_result = "MSR 0xC0010010 bit 23 is " + str(snp_val)
        return component, command, found_result, expectation, test_result
    except OSError as err:
        # Could not read the msr, print a warning and return a failure
        print_warning_message(component, f"Failed to read the desired MSR: {err}")
        # Return results
        found_result = 'Failed to read MSR'
        return component, command, found_result, expectation, test_result

def check_iommu_enablement():
    '''
    Check dmesg for IOMMU disabled message. IOMMU has to be enabled to use SNP.
    If message doesn't appear then test passes.
    Test will only appear in results if test fails, since the test could pass if dmesg is emptied
    or if an old fw is installed.
    '''
    # Turns true if test passes
    test_result = False
    # Name of component being tested
    component = "IOMMU enablement"
    # Expected test result
    expectation = "No notice (IOMMU enabled)"
    # Will change to what the test finds
    found_result = None
    # Command being used
    command = "grep -w 'Too late to enable SNP for IOMMU'"
    try:
        # Read using dmesg
        dmesg_read = subprocess.run(
            "dmesg", shell=True, check=True, capture_output=True)
        # Grep for error message
        test_string_raw = subprocess.run(command, shell=True,
                                         input=dmesg_read.stdout, check=True, capture_output=True)
        # Grab the test string
        test_string = test_string_raw.stdout.decode('utf-8').strip()
        # If the test string appears, assume IOMMU is disabled
        if test_string:
            # Grab error message and return test result
            # Should read SNP: Too late to enable SNP for IOMMU
            division_string = test_string.split(":")
            found_result = ':'.join(division_string[-2:]).strip()
        return component, command, found_result, expectation, test_result
    except (subprocess.CalledProcessError) as err:
        # Error in subprocess, print warning message
        if err.stderr.decode("utf-8").strip():
            print_warning_message(
                component, err.stderr.decode("utf-8").strip())
        # BIOS message not found, IOMMU probably enabled in BIOS. This means the test passes,
        # Or the dmesg message is unavailable on current fw.
        elif err.returncode == 1 and not err.stderr.decode("utf-8").strip():
            found_result = ''
            test_result = True
        # Return results
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
        rmp_base = readmsr(0xC0010132)
        rmp_end = readmsr(0xC0010133)
        if rmp_base and rmp_end:
            test_result = True
        found_result =  "RMP table physical address range " + str(hex(rmp_base)) + " - " + str(hex(rmp_end))
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

    snp_plat_status = ioctl.run_snp_platform_status()

    current_tcb = str(snp_plat_status.tcb_version)
    reported_tcb = str(snp_plat_status.reported_tcb)
    
    if reported_tcb == current_tcb:
        test_result = True

    found_result = "Current TCB: " + current_tcb + " Reported TCB: " + reported_tcb

    return component, command, found_result, expectation, test_result