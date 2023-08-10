'''Module to automatically launch and test a VM for encryption.'''
import os
import string
import subprocess
import re
from time import sleep
import signal
import encryption_test
import ovmf_functions
import local_vm_test
import component_tests
from message_printing import print_warning_message

def grab_cbit_from_cpuid() -> str:
    '''
    Using the CPUID 0x8000001f function and ebx register we can find the system's
    required cbit to encrypt information. Grab it in order to launch encrypted VMs.
    '''
    # read ebx
    ebx = component_tests.get_cpuid(0x8000001f, 'ebx')
    if ebx:
        bin_value = bin(ebx)[::-1][0:6]
        return int(bin_value,2)
    else:
        print_warning_message(
            "Grabbing C-Bit for VM launch", "Could not read cpuid for ebx")
        return None

def launch_vm(system_os:string, current_directory:string,vm_type:str):
    '''
    Function to automatically launch the SEVminimal.qcow2 image.
    Can be launched as an encrypted SEV vm or a unencrypted vm.
    Option for SEV-ES is coded,
    but machine won't launch since the qcow2 image does not support it yet.
    '''
    # Known qemu commands that can be used to launch VMs
    qemu_command_list = {
        'ubuntu': 'qemu-system-x86_64', 'debian': 'qemu-system-x86_64',
        'fedora': '/usr/libexec/qemu-kvm', 'rhel': '/usr/libexec/qemu-kvm',
        'opensuse-tumbleweed': 'qemu-system-x86_64', 'opensuse-leap': 'qemu-system-x86_64',
        'centos': '/usr/libexec/qemu-kvm', 'oracle': '/usr/libexec/qemu-kvm'
    }

    # If not in known list, use qemu-kvm
    # Command being used
    qemu_command = qemu_command_list.get(system_os, "qemu-kvm")

    # Grab cbit for SEV use
    system_cbit = grab_cbit_from_cpuid()

    # Encryption command depending on encyption desired
    encryption_dictionary = {
        'sev' : "-machine memory-encryption=sev0,vmport=off \
        -object sev-guest,id=sev0,policy=0x3,cbitpos=" + str(system_cbit) + ",reduced-phys-bits=1",
        'sev-es': "-machine memory-encryption=sev0,vmport=off \
        -object sev-guest,id=sev0,policy=0x0007,cbitpos=" + str(system_cbit) + ",reduced-phys-bits=1",
        'unencrypted': " "
    }

    # Grab encrypted command
    encryption_command = encryption_dictionary.get(vm_type, "")

    # What type of OVMF file to expect for bios
    if os.path.exists(os.path.abspath(current_directory + '/autoVM/OVMF_READ.fd')):
        ovmf_read_path = os.path.abspath(current_directory + '/autoVM/OVMF_READ.fd')
        ovmf_write_path = os.path.abspath(current_directory + '/autoVM/OVMF_WRITE.fd')
    elif  os.path.exists(os.path.abspath(current_directory + '/autoVM/OVMF_READ.bin')):
        ovmf_read_path = os.path.abspath(current_directory + '/autoVM/OVMF_READ.bin')
        ovmf_write_path = os.path.abspath(current_directory + '/autoVM/OVMF_WRITE.bin')
    
    # Full command to be used to launch VM with qemu
    command = qemu_command + " --enable-kvm \
        -cpu EPYC \
	    -m 1024M \
        -machine q35 \
        -no-reboot \
        -daemonize \
        -vga std -vnc :0 \
        -drive if=pflash,format=raw,unit=0,file=" + ovmf_read_path + ",readonly=on \
        -drive if=pflash,format=raw,unit=1,file=" + ovmf_write_path + " \
        -drive file=" + os.path.abspath(current_directory + '/autoVM/SEVminimal.qcow2') + ",if=none,id=disk0,format=qcow2 \
        -device virtio-scsi-pci,id=scsi0,disable-legacy=on,iommu_platform=on \
        -device scsi-hd,drive=disk0 " + encryption_command

    # Launch the VM
    try:
        subprocess.run(command.strip(), shell=True, check=True, capture_output=True)
    # Error when launching VM
    except (subprocess.CalledProcessError) as err:
        if err.stderr.decode("utf-8").strip():
            print("Launching auto virtual machine was not possible. Error: " +
                  err.stderr.decode("utf-8").strip())
        else:
            print("Launching auto virtual machine was not possible.")
    # Return command used for launch
    return command.strip()

def set_up_machine(system_os:string, current_directory:string, non_verbose:bool):
    '''
    Set up vm folder to be able to launch auto VM
    '''
    # Get the path to the first compatible SEV OVMF build
    ovmf_path = ovmf_functions.get_path_to_ovmf(system_os)
    # Check if OVMF_VARS.fd path exists
    if os.path.exists(ovmf_path + '/OVMF_VARS.fd'):
        # Copy file to autoVM folder
        os.system('cp ' + ovmf_path + '/OVMF_VARS.fd ' +
                  os.path.abspath(current_directory + '/autoVM') + '/OVMF_WRITE.fd')
        # Check if OVMF_CODE.fd exists, some distros have this and others have OVMF_CODE.secboot.fd only as their default.
        if os.path.exists(ovmf_path + '/OVMF_CODE.fd'):
            os.system('cp ' + ovmf_path + '/OVMF_CODE.fd ' +
                      os.path.abspath(current_directory + '/autoVM') + '/OVMF_READ.fd')
        # Check if OVMF_CODE.secboot.fd exists
        elif os.path.exists(ovmf_path + '/OVMF_CODE.secboot.fd'):
            os.system('cp ' + ovmf_path + '/OVMF_CODE.secboot.fd ' +
                      os.path.abspath(current_directory + '/autoVM') + '/OVMF_READ.fd')
    # Check if OVMF_VARS.bin path exists
    elif os.path.exists(ovmf_path + '/ovmf-x86_64-vars.bin'):
        os.system('cp ' + ovmf_path + '/ovmf-x86_64-vars.bin ' +
                  os.path.abspath(current_directory + '/autoVM') + '/OVMF_WRITE.bin')
        os.system('cp ' + ovmf_path + '/ovmf-x86_64-code.bin ' +
                  os.path.abspath(current_directory + '/autoVM') + '/OVMF_READ.bin')

    # If no working OVMF file found, return error, VM can't be launched.
    else:
        if not non_verbose:
            print("Machine cannot be set up. No working OVMF was found. Please look at README for more information.")
        return False
    # Folder setup succesfully
    return True


def clean_up_machine(current_directory:string):
    '''
    Remove created files once VM test is completed.
    '''
    # Remove .fd version of OVMF
    if os.path.exists(os.path.abspath(current_directory + '/autoVM/OVMF_WRITE.fd')):
        os.remove(os.path.abspath(current_directory + '/autoVM/OVMF_WRITE.fd'))
        os.remove(os.path.abspath(current_directory + '/autoVM/OVMF_READ.fd'))
    # Remove .bin version of OVMF
    else:
        os.remove(os.path.abspath(current_directory +
                  '/autoVM/OVMF_WRITE.bin'))
        os.remove(os.path.abspath(current_directory + '/autoVM/OVMF_READ.bin'))


def automatic_vm_test(system_os:string, non_verbose:bool, vm_type:string):
    '''
    Run the automatic VM test. Can specify if SEV or unencrypted test is desired.
    '''
    # Will tell if overall test passed
    test_pass = False
    # Setup directory since files will be moved around
    file_directory = os.path.dirname(os.path.realpath(__file__))
    current_directory = os.path.dirname(file_directory)

    # Print explanation
    if not non_verbose:
        print("Preparing machine for launch...")

    # Setup machine, if set up fails, return failure
    if not set_up_machine(system_os, current_directory, non_verbose):
        if not non_verbose:
            print("Machine could not be setup for launch.")
        return False

    if not non_verbose:
        print("Launching Virtual Machine for testing:")

    # Launch the VM using QEMU
    vm_command = launch_vm(system_os, current_directory,vm_type)
    vm_command = re.sub('\\s+', ' ', vm_command)
    # Wait for machine to finish booting (for best results)
    sleep(15)

    # Get current VMs being run in the system
    available_vms = local_vm_test.get_virtual_machines(system_os)

    # Find our VM on the curent VM list, get its PID
    pid = local_vm_test.find_virtual_machine(vm_command, available_vms)

    # If the PID is found, the machine was succesfully launched, continue with the test
    if pid:
        if not non_verbose:
            print("Machine Launched!")
            print("Corresponding PID: " + str(pid))
            print("Looking for machine memory....")
        # Get the machine's memory contents
        vm_memory = local_vm_test.setup_memory_for_testing(vm_command, pid)
        # Test for encryption using entropy algorithm
        entropy_value = encryption_test.entropy_encryption_test(vm_memory)
        # Entropy value is equal to or above a 7, the machine is probably encrypted
        if entropy_value >= 7:
            if not non_verbose:
                print("Entropy value " + str(entropy_value))
                print("Virtual Machine is probably encrypted.")
            # SEV or SEV-ES test was required, and machinne is encrypted, so test passes.
            if vm_type in ('sev','sev-es'):
                test_pass = True
        # Entropy value is less than a 7, the machine is probably unencrypted
        else:
            if not non_verbose:
                print("Entropy value " + str(entropy_value))
                print("Virtual Machine is probably not encrypted.")
            # Unencrypted machine was requested, and memory is unencrypted, test passes.
            if vm_type == 'unencrypted':
                test_pass = True
        # Kill the machine after test ends
        os.kill(int(pid), signal.SIGTERM)
    # PID not found, machine was probably not launched, test fails
    else:
        if not non_verbose:
            print("Machine not Found. Machine probably did not launch correctly.")
        return False

    if not non_verbose:
        print("Cleaning up machine...")

    # Remove created files for test
    clean_up_machine(current_directory)

    # Return results
    return test_pass
