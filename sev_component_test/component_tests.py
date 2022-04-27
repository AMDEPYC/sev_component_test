'''
Component tests to check basic requirements to run SEV and SEV-ES.
'''
import string
import subprocess
import re
import os
from packaging import version
# from . import ovmf_shared_functions
import ovmf_shared_functions

def hex_to_binary(hex_num: str) -> bin:
    '''
    Converts hex number to binary.
    '''
    return bin(int(hex_num, 16))[2:]


def check_eax(read_out: list, feature: string) -> int:
    '''
    Get CPUID read and then parse the input to get either the bit 1 or bit 0 from the eax register,
    depending on the future that is being checked (SME or SEV).
    '''
    # Getting the eax register value
    hex_num = read_out[1][9]
    # Converting it to binary and then flipping it in order to read it.
    binary_value = hex_to_binary(hex_num)
    binary_value = binary_value[::-1]

    # Return bit 0 if testing for SME
    if feature == "SME":
        return int(binary_value[0])
    # Return bit 1 if testing for SEV
    if feature == "SEV":
        return int(binary_value[1])
    return None


def find_cpuid_support(distro: string, feature: string):
    '''
    Check the CPUID function 0x8000001f and look at the eax register in order to tell
    whether or not the current CPU supports SEV/SME.
    '''
    # Turns true if test passes
    test_result = False
    # Get the appropriate test bit
    if feature == "SEV":
        test_bit = '1'
    else:
        test_bit = '0'
    # Name of component being tested
    component = "CPUID function 0x8000001f bit " + test_bit + " for " + feature
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
        if check_eax(eax_read, feature):
            test_result = True
            found_result = "EAX bit " + test_bit + " is 1"

        # Return test results
        return component, command, found_result, expectation, test_result

    # Error caught
    except (subprocess.CalledProcessError) as err:
        if err.stderr.decode("utf-8").strip():
            ovmf_shared_functions.print_warning_message(
                component, err.stderr.decode("utf-8").strip())
        return component, command, found_result, expectation, test_result


def check_virtualization():
    '''
    Check to see if virtualization is availabele on the system,
    and make sure that it is AMD virtualization that is available.
    '''
    # Test pass or Fail
    test_result = False
    # Component being tested
    component = "Virtualization capabilities"
    # Expected result
    expectation = "Virtualization: AMD-V"
    # Test findings
    found_result = "EMPTY"

    # Complete command used to find virtualization
    command = "lscpu | grep Virtualization"
    try:
        # Get lscpu
        lscpu_read = subprocess.run(
            "lscpu", shell=True, check=True, capture_output=True)
        # Get virtualization feature
        virtualization_feature = subprocess.run("grep Virtualization", shell=True,
                                                input=lscpu_read.stdout, check=True,
                                                capture_output=True)
        # Format virtualization string
        virt_string = re.sub(
            ' +', ' ', virtualization_feature.stdout.decode('utf-8').strip())

        # Virtualization string found, grab value
        if virt_string:
            found_result = virt_string

        # Vitualization available is AMD
        if 'AMD-V' in found_result:
            test_result = True

        # Return test results
        return component, command, found_result, expectation, test_result

    except (subprocess.CalledProcessError) as err:
        # Error with subprocess, print error, return failure
        if err.stderr.decode("utf-8").strip():
            ovmf_shared_functions.print_warning_message(
                component, err.stderr.decode("utf-8").strip())
        return component, command, found_result, expectation, test_result


def get_sme_string(dmesg_string:string) -> string:
    '''
    Format the SME support string from kernel message.
    Remove ccp and return only SME support found string.
    '''
    # CCP
    ccp = ''
    # Formatted string will be returned here
    sme_support = ''
    out_of_ccp = False
    for char in dmesg_string:

        if not char.isalpha() and not out_of_ccp:
            ccp += char
        # Out of the ccp, collect SME Support string
        elif char.isalpha() and not out_of_ccp:
            out_of_ccp = True
            sme_support += char
        # Continue to collect SME messge
        elif out_of_ccp:
            sme_support += char

    # Formatted string returned
    return sme_support


def get_asid_num(asid_string:string) -> string:
    '''
    Format string to get ASIDs.
    '''
    num = ''
    # Collect digits from string
    for char in asid_string:
        if char.isnumeric():
            num += char
        else:
            break

    return num


def get_sev_string_and_asids(dmesg_string:string):
    '''
    Get SEV or SEV-ES support string from kernel message.
    Remove ccp, return support string and ASIDs if available.
    '''
    # ccp
    ccp = ''
    # Will contain the kernel support string
    sev_support = ''
    # Will conatin found ASIDs
    available_asids = ''
    out_of_ccp = False
    in_asid_count = False
    support_found = False
    for char in dmesg_string:
        # At ccp
        if not char.isalpha() and not out_of_ccp:
            ccp += char
        # Out of CCP, collect support string
        elif char.isalpha() and not out_of_ccp:
            out_of_ccp = True
            sev_support += char
        # Support string completed
        elif (
            sev_support in ('SVM: SEV supported',
                            'SEV supported', 'SEV-ES supported')
            and not support_found
        ):
            support_found = True
        # Continue to collect support string
        elif not support_found:
            sev_support += char
        # At available Available ASIDs in string
        elif char.isnumeric() and not in_asid_count:
            in_asid_count = True
            available_asids += char
        # Continue to collect ASID num
        elif in_asid_count:
            available_asids += char

    # ASIDs found
    if available_asids != '':
        asid_num = get_asid_num(available_asids)
    # No ASIDS found
    else:
        asid_num = False

    # Return appropriate strings
    return sev_support, available_asids, asid_num


def get_version_num(line:string) -> string:
    '''
    Get version number for given feature (Kernel, libvirt, qemu,ASIDs).
    Get versions in MAJOR.MINOR.PATHC format. Will populate patch with 0 if not available.
    '''
    # How many periods have we encountered
    period_counter = 0
    # Will return version number
    version_num = ''
    for char in line:
        # Add to version
        if char.isnumeric():
            version_num += char
        # Valid period encounter
        elif char == '.' and period_counter < 2:
            version_num += char
            period_counter += 1
        elif not char.isnumeric() and period_counter == 1:
            period_counter += 1
            version_num += '.0'
            break
        # Unvalid period encounter, return version number.
        elif not char.isnumeric() and period_counter == 2:
            break
    # Populate patch number if empty
    if period_counter == 1:
        version_num += '.0'
    # Return version number
    return version_num


def get_kernel_version():
    '''
    Get the system's kernel version number.
    '''
    try:
        # Grab kernel from uname -r
        kernel = subprocess.run("uname -r", shell=True,
                                check=True, capture_output=True)
        kernel_string = kernel.stdout.decode('utf-8').strip()
        # Return version and string
        return get_version_num(kernel_string), kernel_string
    # Error with subprocess
    except (subprocess.CalledProcessError) as err:
        if err.stderr.decode("utf-8").strip():
            ovmf_shared_functions.print_warning_message(
                "Kernel version", err.stderr.decode("utf-8").strip())
        else:
            ovmf_shared_functions.print_warning_message(
                "Kernel version", 'kernel version not found')
        return False, False


def find_asid_count(feature:string):
    '''
    Get the system's available ASID count, if the kernel permits it.
    '''
    # Test pass or Fail
    test_result = False
    # Component being tested
    component = "Available " + feature + " ASIDS"
    # Results found in testing
    found_result = "EMPTY"
    # Expected result
    expectation = "xxx ASIDs"
    # Test findings
    found_result = "EMPTY"
    # Grab correct expectation and command according to the feature
    if feature == "SEV":
        grep_command = "grep -w 'SEV supported'"
    elif feature == "SEV-ES":
        grep_command = "grep SEV-ES"
    else:
        ovmf_shared_functions.print_warning_message(component, "invalid feature")
        return component, 'NONE', found_result, 'NONE', test_result

    # Complete command
    command = "dmesg | " + grep_command

    kernel_version, _ = get_kernel_version()
    if not kernel_version:
        ovmf_shared_functions.print_warning_message(component, "Could not get kernel version.")
    if version.parse(kernel_version) < version.parse('5.11') and feature == "SEV":
        ovmf_shared_functions.print_warning_message(
            component,
            "Update kernel to 5.11 version to find available ASIDS for SEV"
            " or check in BIOS settings"
        )
        # Making it true, because this does not mean test should fail.
        test_result = True
    else:
        try:
            # Read using dmesg
            dmesg_read = subprocess.run(
                "dmesg", shell=True, check=True, capture_output=True)
            # Grep specific component
            test_string_raw = subprocess.run(grep_command, shell=True,
                                             input=dmesg_read.stdout, check=True, capture_output=True)
            test_string = test_string_raw.stdout.decode('utf-8').strip()
            _, found_result, asid_num = get_sev_string_and_asids(test_string)
            if found_result and int(asid_num) > 0:
                test_result = True

            # Return result
            return component, command, found_result, expectation, test_result

        except (subprocess.CalledProcessError) as err:
            if err.stderr.decode("utf-8").strip():
                ovmf_shared_functions.print_warning_message(
                    component, err.stderr.decode("utf-8").strip())
            return component, command, found_result, expectation, test_result
    return component, command, found_result, expectation, test_result


def find_os_support(feature:string):
    '''
    Find OS support for feature in the kernel message.
    Find available ASIDs if support found for SEV and SEV-ES.
    '''
    # Test pass or Fail
    test_result = False
    # Component being tested
    component = "OS support for " + feature
    # Test findings
    found_result = "EMPTY"

    # Grab correct expectation and command according to the feature
    if feature == "SME":
        expectation = "AMD Memory Encrtyption Features active: SME"
        grep_command = "grep SME"
    elif feature == "SEV":
        expectation = "SEV supported"
        grep_command = "grep -w 'SEV supported'"
    elif feature == "SEV-ES":
        expectation = "SEV-ES supported"
        grep_command = "grep SEV-ES"
    else:
        ovmf_shared_functions.print_warning_message(component, "invalid feature")
        return component, 'NONE', found_result, 'NONE', test_result

    # Complete command
    command = "dmesg | " + grep_command
    # Test findings
    found_result = "EMPTY"

    try:
        # Read using dmesg
        dmesg_read = subprocess.run(
            "dmesg", shell=True, check=True, capture_output=True)
        # Grep specific component
        test_string_raw = subprocess.run(grep_command, shell=True,
                                         input=dmesg_read.stdout, check=True, capture_output=True)
        test_string = test_string_raw.stdout.decode('utf-8').strip()

        if test_string and feature == 'SME':
            # Call to get formatted SME support
            found_result = get_sme_string(test_string)
            test_result = True
        elif test_string and feature in ('SEV', 'SEV-ES'):
            # Call to get formatted SEV support string
            found_result, _, _ = get_sev_string_and_asids(test_string)
            test_result = True

        return component, command, found_result, expectation, test_result

    except (subprocess.CalledProcessError) as err:
        if err.stderr.decode("utf-8").strip():
            ovmf_shared_functions.print_warning_message(
                component, err.stderr.decode("utf-8").strip())
        return component, command, found_result, expectation, test_result


def get_linux_distro():
    '''
    Get the distribution and version of the linux system.
    '''
    try:
        # cat to get os-release
        cat_read = subprocess.run("cat /etc/os-release", shell=True,
                                  check=True, capture_output=True)
        # grep to get the desired fields
        grep_read_version = subprocess.run("grep -w 'VERSION_ID='", shell=True,
                                           input=cat_read.stdout, check=True, capture_output=True)
        grep_read_name = subprocess.run("grep ID=", shell=True,
                                        input=cat_read.stdout, check=True, capture_output=True)
        # sed to cut down the result
        distro_version_read = subprocess.run("sed 's/.*VERSION_ID=//'", shell=True,
                                             input=grep_read_version.stdout, check=True, capture_output=True)
        distro_name_read = subprocess.run("sed 's/.*ID=//'", shell=True,
                                          input=grep_read_name.stdout, check=True, capture_output=True)

        # Format in to grap the distro version number
        linux_version = distro_version_read.stdout.decode(
            'UTF-8').strip().replace("\"", "")
        # Format to get the distro name
        linux_os = distro_name_read.stdout.decode(
            'UTF-8').split('\n')[0].replace("\"", "")

        return linux_os, linux_version
    except (subprocess.CalledProcessError) as err:
        if err.stderr.decode("utf-8").strip():
            ovmf_shared_functions.print_warning_message("Getting linux distribution error: ",
                                  err.stderr.decode("utf-8").strip())
        else:
            ovmf_shared_functions.print_warning_message("Getting linux distribution error: ",
                                  "Distro can't be found")
        return False, False


def check_linux_distribution():
    '''
    Get the system's distribution and version,
    and compare it to a known distribution list that support SEV.
    '''
    # Turns true if test passes
    test_result = False
    # Name of component being tested
    component = "Current OS distribution"
    # Expected test result
    expectation = "(comparing against known minimum version list)"
    # Will change to what the test finds
    found_result = "EMPTY"
    # Command being used
    command = "cat /etc/os-release"

    # List of known minimum distro versions that support SEV
    min_distro_versions = {
        'ubuntu': '18.04', 'sles': '15', 'fedora': '28', 'rhel': '8', 'opensuse-tumbleweed': '0'
    }

    # Get system distribution and version
    distro_name, distro_version = get_linux_distro()

    found_result = distro_name + ' ' + distro_version
    # If distribution in list, then compare system version against minimum version
    if distro_name:
        found_result = distro_name + ' ' + distro_version
        if distro_name in min_distro_versions:
            min_version = min_distro_versions[distro_name]
            # Version meets minimum, test passes
            if version.parse(distro_version) >= version.parse(min_version):
                test_result = True
        else:
            ovmf_shared_functions.print_warning_message(
                component, "os distribution not in known minimum list")
            # SEV could still work with OS, this test just doesn't apply
            test_result = True

    return component, command, found_result, expectation, test_result


def check_kernel(feature:string):
    '''
    Find current kernel version in system,
    then compare it against known minimums to see if system can run either SEV or SEV-ES.
    *Modifications might have to be done for certain distros.
    '''
    # Turns true if test passes
    test_result = False
    # Name of component being tested
    component = "Kernel"
    # Will change to what the test finds
    found_result = "EMPTY"
    # Command being used
    command = "uname -r"
    # Expected test result according to the feature presented
    if feature == "SEV":
        expectation = "4.16 minimum"
        minimum_version = "4.16"
    elif feature == "SEV-ES":
        expectation = "5.11 minimum"
        minimum_version = "5.11"
    else:
        expectation = 'NONE'
        ovmf_shared_functions.print_warning_message(component, "Invalid feature")
        return component, command, found_result, expectation, test_result

    # Get kernel version
    kernel_version, kernel_string = get_kernel_version()

    # Kernel find did not return false
    if kernel_string:
        # Found result is the full kernel string
        found_result = kernel_string
        # Compare to the minimum version
        if version.parse(kernel_version) >= version.parse(minimum_version):
            test_result = True

    return component, command, found_result, expectation, test_result


def find_sev_libvirt_enablement():
    '''
    Find if SEV is enabled using LibVirt domcapabilities.
    A good way to confirm that SEV is enabled on the host OS.
    This test will only run if LibVirt is found to be installed and it is also compatible with SEV.
    '''
    # Turns true if test passes
    test_result = False
    # Name of component being tested
    component = "LibVirt SEV enablement"
    # Expected test result
    expectation = "<sev supported='yes'>"
    # Will change to what the test finds
    found_result = "EMPTY"
    # Command being used
    command = "virsh domcapabilities | grep sev"
    try:
        libvirt_domcapabilities = subprocess.run(
            "virsh domcapabilities", shell=True, check=True, capture_output=True)
        grep_read = subprocess.run("grep sev", shell=True,
                                   input=libvirt_domcapabilities.stdout, check=True, capture_output=True)
        if grep_read:
            found_result = grep_read.stdout.decode(
                "utf-8").split('\n')[0].strip()
            if found_result == "<sev supported='yes'>":
                test_result = True
       # Return results
        return component, command, found_result, expectation, test_result
    except (subprocess.CalledProcessError) as err:
        if err.stderr.decode("utf-8").strip():
            ovmf_shared_functions.print_warning_message(component,
                                  err.stderr.decode("utf-8").strip())
        return component, command, found_result, expectation, test_result


def find_libvirt_support():
    '''
    Find if libvirt is installed in the system,
    then get the version installed and compare it to the known minimum needed
    to run either SEV or SEV-ES.
    '''
    # Turns true if test passes
    test_result = False
    # Name of component being tested
    component = "Libvirt version"
    # Expected test result
    expectation = "4.5 minimum"
    # Will change to what the test finds
    found_result = "EMPTY"
    # Command being used
    command = "virsh -V"
    try:
        # Get the libvirt version, will return error if not installed
        libvirt_version_read = subprocess.run(
            "virsh -V", shell=True, check=True, capture_output=True)
        sed_read = subprocess.run("sed 's/.*libvirt //'", shell=True,
                                  input=libvirt_version_read.stdout, check=True, capture_output=True)

        # Call to get the formatted version number
        if sed_read.stdout:
            found_result = sed_read.stdout.decode("utf-8").split('\n')[0]
            lib_virt_version = get_version_num(found_result)
            if version.parse(lib_virt_version) >= version.parse('4.5'):
                test_result = True

        # Return test result
        return component, command, found_result, expectation, test_result

    except (subprocess.CalledProcessError) as err:
        if err.stderr.decode("utf-8").strip():
            ovmf_shared_functions.print_warning_message(component,
                                  err.stderr.decode("utf-8").strip())
        return component, command, found_result, expectation, test_result


def find_qemu_support(system_os:string, feature:string):
    '''
    Find if QEMU is installed in the system, then get the version installed and compare it to the
    known minimum needed to run SEV.
    '''
    # Turns true if test passes
    test_result = False
    # Name of component being tested
    component = "QEMU version"
    # Will change to what the test finds
    found_result = "EMPTY"

    # List of knonw working commands to get the QEMU version in the system depending on the distro
    qemu_command_list = {
        'ubuntu': 'qemu-system-x86_64 --version', 'debian': 'qemu-system-x86_64 --version',
        'fedora': '/usr/libexec/qemu-kvm --version', 'rhel': '/usr/libexec/qemu-kvm --version',
        'opensuse-tumbleweed': 'qemu-system-x86_64 --version',
        'opensuse-leap': 'qemu-system-x86_64 --version',
        'centos': '/usr/libexec/qemu-kvm --version', 'oracle': '/usr/libexec/qemu-kvm --version'
    }
    # Command being used
    command = qemu_command_list.get(system_os, "kvm --version")

    # Expected test result
    if feature == 'SEV':
        expectation = "2.12 minimum"
        min_version = "2.12"
    elif feature == 'SEV-ES':
        expectation = "6.0 minimum"
        min_version = "6.0"
    else:
        expectation = 'NONE'
        ovmf_shared_functions.print_warning_message(component, "Invalid feature provided")
        return component, command, found_result, expectation, test_result

    try:
        # Get QEMU version
        qemu_version_read = subprocess.run(
            command, shell=True, check=True, capture_output=True)
        sed_read = subprocess.run("sed 's/.*version //'", shell=True,
                                  input=qemu_version_read.stdout, check=True, capture_output=True)
        # Grab call result
        if sed_read:
            found_result = sed_read.stdout.decode("utf-8").split('\n')[0]
            qemu_version = get_version_num(found_result)
            # If minimum version is met, test passes
            if version.parse(qemu_version) >= version.parse(min_version):
                test_result = True
        # Return results
        return component, command, found_result, expectation, test_result
    except (subprocess.CalledProcessError) as err:
        if err.stderr.decode("utf-8").strip():
            ovmf_shared_functions.print_warning_message("Getting linux distribution error: ",
                                  err.stderr.decode("utf-8").strip())
        return component, command, found_result, expectation, test_result


def test_all_ovmf_paths(system_os:string, min_commit_date):
    '''
    Function to get and print all of the found OVMF paths, whether default or manually built.
    If at least one meets the minimum, test passes.
    Will return a list of paths for printing.
    '''
    # At least one path meets the minimum
    one_path_true = False
    # Current tested path (starts with default package)
    curr_path_true = False
    # Testing for paths:
    component = 'OMVF path install'

    # Get the default path
    ovmf_default_command, default_ovmf_path,\
        is_default_pkg_install, default_pkg_date = ovmf_shared_functions.get_default_ovmf_path(
            system_os)

    # Get all of the manually built paths
    built_ovmf_paths = ovmf_shared_functions.get_built_ovmf_paths()

    # Paths found
    paths_found = []

    # No paths found
    if not is_default_pkg_install and not built_ovmf_paths:
        return False, paths_found

    # Path to default package in most distros
    if is_default_pkg_install and os.path.exists(default_ovmf_path):
        # Default package meets the minimum
        if default_pkg_date >= min_commit_date:
            one_path_true = True
            curr_path_true = True
        # Add default path results to the list.
        path_components = {
            'component': component,
            'command': ovmf_default_command,
            'found_result': default_ovmf_path + ' ' + default_pkg_date.strftime("%Y-%m-%d "),
            'expectation': min_commit_date.strftime("%Y-%m-%d "),
            'test_result': curr_path_true
        }
        paths_found.append(path_components)

    if built_ovmf_paths:
        for path in built_ovmf_paths:
            curr_path_true = False
            # Call to get commit date from given path
            built_ovmf_date, built_command = ovmf_shared_functions.get_commit_date(
                path)
            # Call to compare path commit date with given minimum date for either SEV or SEV-ES
            # Current path meets minimum
            if built_ovmf_date >= min_commit_date:
                one_path_true = True
                curr_path_true = True
            # Add current path results to the list
            path_components = {
                'component': component,
                'command': built_command,
                'found_result': path + ' ' + built_ovmf_date.strftime("%Y-%m-%d "),
                'expectation': min_commit_date.strftime("%Y-%m-%d "),
                'test_result': curr_path_true
            }
            paths_found.append(path_components)

    return one_path_true, paths_found
