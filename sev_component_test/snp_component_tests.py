'''
Component tests to test availability of SNP in a system.
'''
import subprocess
import ioctl
from packaging import version
from message_printing import print_warning_message
from component_tests import check_eax

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

def get_rmp_address(dmesg_string):
    '''
    Function to find the reserved rmp table addresses from the string presented in the kernel message.
    '''
    # CCP
    ccp = ''
    # RMP table notice
    rmp_message = ''
    # Addresses found
    rmp_address = ''

    out_of_ccp = False
    in_rmp_address = False

    for char in dmesg_string:
        if not char.isalpha() and not out_of_ccp:
            ccp += char
        # Out of the ccp, collect RMP string
        elif char.isalpha() and not out_of_ccp:
            out_of_ccp = True
            rmp_message += char
        # Continue to collect RMP messge
        elif out_of_ccp and not in_rmp_address and char != "[" and not char.isnumeric():
            rmp_message += char
        # Collected the message, now collet the adress if there is any.
        elif out_of_ccp and (char == "[" or char.isnumeric()) and not in_rmp_address:
            in_rmp_address = True
            rmp_address += char
        elif in_rmp_address:
            rmp_address += char

    # Formatted string returned
    return rmp_message, rmp_address

def check_reserved_rmp():
    '''
    Find if the reserved rmp tables in the system by checking the kernel message.
    '''
    # Turns true if test passes
    test_result = False
    # Name of component being tested
    component = "Reserved RMP table adress"
    # Expected test result
    expectation = "SEV-SNP: RMP table physical address"
    # Will change to what the test finds
    found_result = "EMPTY"
    # Command being used
    command = "dmesg | grep RMP"

    try:
        # Get dmesg
        dmesg_read = subprocess.run(
            "dmesg", shell=True, check=True, capture_output=True)
        # grep from rmp
        grep_read = subprocess.run("grep RMP", shell=True,
                                  input=dmesg_read.stdout, check=True, capture_output=True)
        # Grab message and adress
        rmp_message, rmp_address = get_rmp_address(grep_read.stdout.decode('utf-8'))

        # Success message
        if rmp_message.strip() == "SEV-SNP: RMP table physical address":
            found_result = rmp_message.strip() + " " + rmp_address.strip()
            test_result = True
        # Message not correct test fails.
        else:
            found_result = rmp_message
        return component, command, found_result, expectation, test_result
    except (subprocess.CalledProcessError) as err:
        if err.stderr.decode("utf-8").strip():
            print_warning_message("Getting RMP adresses from kernel messge: ",
                                  err.stderr.decode("utf-8").strip())
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
 
def find_snp_cpuid_support(distro: str):
    '''
    Check the CPUID function 0x8000001f and look at the eax register in order to tell
    whether or not the current CPU supports SNP.
    '''
    # Turns true if test passes
    test_result = False
    # Get the appropriate test bit
    test_bit = "4"
    # Name of component being tested
    component = "CPUID function 0x8000001f bit " + test_bit + " for SNP."
    # Expected test result
    expectation = "EAX bit " + test_bit + " to be '1'"
    # Will change to what the test finds
    found_result = "EAX bit " + test_bit + " is '0'"

    # Command being used
    if distro == 'rhel':
        command = "cpuid -r -1 0x8000001f"
    else:
        command = "cpuid -r -1 -l 0x8000001f"

    try:
        # Read CPUID
        cpuid_read = subprocess.run(
            command, shell=True,
            check=True, capture_output=True)
        # Format the return string
        eax_read_raw = subprocess.run(
            "sed 's/.*eax=//'", input=cpuid_read.stdout,
            shell=True, check=True, capture_output=True)
        eax_read = eax_read_raw.stdout.decode("utf-8").split('\n')
            
        # Check the eax register
        if check_eax(eax_read, "SNP"):
            test_result = True
            found_result = "EAX bit " + test_bit + " is 1"

        # Return test results
        return component, command, found_result, expectation, test_result

    # Error caught
    except (subprocess.CalledProcessError) as err:
        if err.stderr.decode("utf-8").strip():
            print_warning_message(
                component, err.stderr.decode("utf-8").strip())
        else: print_warning_message(component, "Could not read cpuid for eax")
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