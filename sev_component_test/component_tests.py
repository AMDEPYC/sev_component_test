'''
Component tests to check basic requirements to run SEV and SEV-ES.
'''
import string
import subprocess
import re
import os
import struct
from packaging import version
from cpuid import cpuid
import ovmf_functions
import ioctl
from message_printing import print_warning_message

def get_cpuid(function, register) -> int:
    '''
    Get register value for a cpuid funtion
    '''

    registers = ['eax', 'ebx', 'ecx', 'edx']

    try:
        register_values = cpuid(function)
    except ValueError:
        return None

    reg_dict = dict(zip(registers, register_values))

    return reg_dict[register]

def readmsr(msr, cpu = 0):
    '''
    Read contents of dev cpu msr to get the desired msr value.
    '''
    msr_file = os.open(f'/dev/cpu/{cpu}/msr', os.O_RDONLY)
    os.lseek(msr_file, msr, os.SEEK_SET)
    val = struct.unpack('Q', os.read(msr_file, 8))[0]
    os.close(msr_file)
    return val

def find_cpuid_support(feature: str):
    '''
    Check the CPUID function 0x8000001f and look at the eax register in order to tell
    whether or not the current CPU supports SEV/SME.
    '''
    # Turns true if test passes
    test_result = False
    # Get the appropriate test bit
    if feature == "SEV":
        test_bit = '1'
    elif feature == 'SEV-ES':
        test_bit = '3'
    elif feature == 'SEV-SNP':
        test_bit = '4'
    elif feature == 'SME':
        test_bit = '0'
    # Name of component being tested
    component = "CPUID function 0x8000001f bit " + test_bit + " for " + feature
    # Expected test result
    expectation = "EAX bit " + test_bit + " to be '1'"
    # Will change to what the test finds
    found_result = "EAX bit " + test_bit + " is '0'"

    # Command being used
    command = "cpuid 0x8000001f"

    eax = get_cpuid(0x8000001f, 'eax')

    if eax:
        bin_value = bin(eax)[2:][::-1]
        test_result = bin_value[int(test_bit)]
        found_result = "EAX bit " + test_bit + " is " + str(test_result)
    else:
        print_warning_message(component, "Could not read cpuid for eax")
        found_result = "Could not read cpuid"
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
            print_warning_message(
                component, err.stderr.decode("utf-8").strip())
        return component, command, found_result, expectation, test_result

def get_version_num(line:str) -> str:
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
            print_warning_message(
                "Kernel version", err.stderr.decode("utf-8").strip())
        else:
            print_warning_message(
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
    # Checking cpuid function 0x8000001f register edx
    command = "cpuid 0x8000001f"

    if feature == 'SEV':
        ecx = get_cpuid(0x8000001f, 'ecx')
        edx = get_cpuid(0x8000001f, 'edx')
        if edx and ecx:
            asids = ecx - (edx - 1)
            if asids > 0:
                test_result = True
            found_result = str(asids) + " ASIDs"
        elif edx is None or ecx is None:
            found_result = "failed to read cpuid."
            print_warning_message(component, "Could not read cpuid to find SEV ASIDs")
    elif feature == 'SEV-ES':
        edx = get_cpuid(0x8000001f, 'edx')
        if edx:
            asids = edx - 1
            if asids > 0:
                test_result = True
            found_result = str(asids) + " ASIDs"
        elif edx is None:
            found_result = "failed to read cpuid."
            print_warning_message(component, "Could not read cpuid to find SEV-ES ASIDs")
    else:
        print_warning_message(component, "invalid feature")
        return component, 'NONE', found_result, 'NONE', test_result

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
        grep_read_version = subprocess.run("grep -w 'VERSION_ID'", shell=True,
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
        id_read = distro_name_read.stdout.decode(
            'UTF-8').split('\n')
        for read in id_read:
            read = read.replace("\"", "")
            if not True in [char.isdigit() for char in read]:
                linux_os = read
                break

        return linux_os, linux_version
    except (subprocess.CalledProcessError) as err:
        if err.stderr.decode("utf-8").strip():
            print_warning_message("Getting linux distribution error: ",
                                  err.stderr.decode("utf-8").strip())
        else:
            print_warning_message("Getting linux distribution error: ",
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

    # If distribution in list, then compare system version against minimum version
    if distro_name and distro_version:
        found_result = distro_name + ' ' + distro_version
        if distro_name in min_distro_versions:
            min_version = min_distro_versions[distro_name]
            # Version meets minimum, test passes
            if version.parse(distro_version) >= version.parse(min_version):
                test_result = True
        else:
            print_warning_message(
                component, "os distribution not in known minimum list")
            # SEV could still work with OS, this test just doesn't apply
            test_result = True

    return component, command, found_result, expectation, test_result

def check_kernel(feature:str):
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
        print_warning_message(component, "Invalid feature")
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

def check_if_sev_init():
    '''
    Use SEV_PLATFORM_STATUS ioctl to see if sev is initialized in the current system.
    '''
    # Turns true if test passes
    test_result = False
    # Name of component being tested
    component = "SEV INIT STATE"
    # Will change to what the test finds
    found_result = "EMPTY"
    # Command being used
    command = "SEV apis"
    #Expected result
    expectation = "1"

    sev_plat_status = ioctl.run_sev_platform_status()

    sev_init_status = sev_plat_status.state

    found_result = str(sev_init_status)

    if sev_init_status:
        test_result = True

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
            print_warning_message(component,
                                  err.stderr.decode("utf-8").strip())
        else:
            print_warning_message(component,
                                  "Grabbing libvirt version failed.")
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
        'fedora': 'qemu-system-x86_64 --version', 'rhel': '/usr/libexec/qemu-kvm --version',
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
        print_warning_message(component, "Invalid feature provided")
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
            print_warning_message("Getting QEMU version error: ",
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
        is_default_pkg_install, default_pkg_date = ovmf_functions.get_default_ovmf_path(
            system_os)

    # Get all of the manually built paths
    built_ovmf_paths = ovmf_functions.get_built_ovmf_paths()

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
            built_ovmf_date, built_command = ovmf_functions.get_commit_date(
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

def check_sme_enablement():
    '''
    Find in SEV/SME encryption is enabled in bios by checking the MSR.
    Looking at MSR address 0x0xC0010010 bit 23 for enablment.
    '''
    # Turns true if test passes
    test_result = False
    # Name of component being tested
    component = "SME enabled"
    # Expected test result
    expectation = "MSR 0xC0010010 it 23 is 1"
    # Will change to what the test finds
    found_result = ""
    # Command being used
    command = "MSR 0xC0010010"
    try:
        msr_value = readmsr(0xC0010010)
        bin_value = bin(msr_value)[2:][::-1]
        meme_val = bin_value[23]
        if meme_val:
            test_result = True
        found_result = "MSR 0xC0010010 bit 23 is " + str(meme_val)
        return component, command, found_result, expectation, test_result
    except OSError as err:
        # Could not read the msr, print a warning and return a failure
        print_warning_message(component, f"Failed to read the desired MSR: {err}")
        # Return results
        found_result = 'Failed to read MSR'
        return component, command, found_result, expectation, test_result

def check_if_sev_es_init():
    '''
    Use SEV_PLATFORM_STATUS ioctl to see if sev-es is initialized in the current system.
    '''
    # Turns true if test passes
    test_result = False
    # Name of component being tested
    component = "SEV-ES INIT STATE"
    # Will change to what the test finds
    found_result = "EMPTY"
    # Command being used
    command = "SEV apis"
    #Expected result
    expectation = "1"

    sev_plat_status = ioctl.run_sev_platform_status()

    sev_es_init_status = sev_plat_status.config_es

    found_result = str(sev_es_init_status)

    if sev_es_init_status:
        test_result = True

    return component, command, found_result, expectation, test_result
