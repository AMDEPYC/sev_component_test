'''
Functions required to print and test the memory of VMs being run in the host system.
'''
import string
import subprocess
from re import sub
import memory_reader
import encryption_test

def create_vm_dictionary(available_vms) -> dict:
    '''
    From the found running qemu commands in the host system,
    Create a dictionary were the key is the VM PID and the
    value is the command used to launch the VM.
    '''
    vm_dict = {}
    for virt in available_vms:
        virt = virt.strip()
        current_pid = ''
        for char in virt:
            # The first part of the line will be the VM's PID
            if char.isnumeric():
                current_pid += str(char)
            elif char == ' ':
                break
        # The rest of the line will be the VM command
        vm_command = virt[len(current_pid) + 1:]
        # Add the VM to the dictionary
        vm_dict[current_pid] = vm_command

    return vm_dict


def get_virtual_machines(system_os:string):
    '''
    Will find all of the running VMs in the system (if launched with QEMU)
    and return a dictionary where the key is the VM PID
    and the value is the command used to launch the VM.
    '''
    # Commands for different distros
    qemu_command_list = {
        'ubuntu': '[q]emu-system-x86_64', 'debian': '[q]emu-system-x86_64',
        'fedora': '[q]emu-kvm', 'rhel': '[q]emu-kvm',
        'opensuse-tumbleweed': '[q]emu-system-x86_64', 'opensuse-leap': '[q]emu-system-x86_64',
        'centos': '[q]emu-kvm', 'oracle': '[q]emu-kvm'}

    # Default command if distro not in list
    qemu_command = qemu_command_list.get(system_os, "[q]emu")

    try:
        ps_read = subprocess.run('ps axo pid,command',
                                 shell=True, check=True, capture_output=True)
        grep_qemu = subprocess.run(
            'egrep ' + qemu_command, input=ps_read.stdout, shell=True, check=True, capture_output=True)
        # Loop to get available VMs and their PIDs, put them into the dictionary.
        found_vms = grep_qemu.stdout.decode('utf-8').split('\n')
        found_vms.remove('')
        return create_vm_dictionary(found_vms)
    except (subprocess.CalledProcessError) as err:
        if err.stderr.decode("utf-8").strip():
            print("Could not find qemu VMs using ps axo. Error: " +
                  err.stderr.decode("utf-8").strip())
        else:
            print("Could not find qemu VMs using ps axo.")
        return None


def find_virtual_machine(vm_command:string, available_vms:dict) -> string:
    '''
    From a given command used to launch a VM,
    find its PID from a the dictionary of currently running VM's.
    '''
    # Format command if necessary
    vm_command = sub(' +', ' ', vm_command)
    # Loop through dictionary
    for pid, virtual_machine in available_vms.items():
        # Command found in dictionary, return PID
        if vm_command == virtual_machine.strip():
            return pid
    # VM not found
    return False


def setup_memory_for_testing(vm_command:string, pid:string):
    '''
    With the command used to launch the VM and the PID corresponding to the VM, grab a page of its memory and then
    format it for testing.
    '''
    # Will contain memory
    memory = None

    # Find the size of the memory (Eg QEMU -m 2048 M)
    mem_size = memory_reader.get_memory_size(vm_command)
    # With the memory size found, find the top and bottom adresses corresponding to the VMs memory pages in the host system
    top_address, bot_address = memory_reader.find_ram_specific_memory(
        pid, mem_size)
    # Grab one page of memory for testing
    memory = memory_reader.read_one_memory_page_for_testing(
        pid, top_address, bot_address)
    return memory.stdout


def set_up_memory_for_printing(vm_command:string, pid:string):
    '''
    With the command used to launch the VM and the PID corresponding to the VM,
    grab a page of its memory and return it for printing.
    Unlike setupMemoryforTesting,
    no formatting is necessary since the memory is just being printed, not analyzed.
    '''
    # Will contain memory
    memory = None

    # Find the size of the memory (Eg QEMU -m 2048 M)
    mem_size = memory_reader.get_memory_size(vm_command)
    # With the memory size found, find the top and bottom adresses corresponding to the VMs memory
    top_addr, bot_addr = memory_reader.find_ram_specific_memory(
        pid, mem_size)
    # Grab one page of memory for printing
    memory = memory_reader.read_one_memory_page_for_printing(
        pid, top_addr, bot_addr)

    # Return the memory for printing
    return memory


def test_virtual_machine(tested_vm:string, available_vms:dict, non_verbose:bool):
    '''
    For a given Virtual machine,
    perform the entropy encryption test in one page of its memory and return results.
    '''
    # Will turn False if test fails or VM was not found
    test_pass = True
    # Find VM in system and get its PID
    vm_pid = find_virtual_machine(tested_vm, available_vms)

    # PID found, perform test
    if vm_pid:
        if not non_verbose:
            print("Provided Virtual Machine found!")
            print('')
            print("PID: " + str(vm_pid))
            print(tested_vm)
            print('')
            print("Testing virtual machine " + vm_pid + " for encryption")
        # Get 1 formatted page of memory for testing
        vm_memory = setup_memory_for_testing(tested_vm, vm_pid)
        # Perform test on the memory
        entropy_value = encryption_test.entropy_encryption_test(
            vm_memory)
        # Entropy value is 7 or higher, encryption test passes
        if entropy_value >= 7:
            if not non_verbose:
                print("Entropy value " + str(entropy_value))
                print("Virtual Machine " + vm_pid + " is probably encrypted.")
        # Entropy value lower than 7, test fails.
        else:
            if not non_verbose:
                print("Entropy value " + str(entropy_value))
                print("Virtual Machine " + vm_pid +
                      " is probably not encrypted.")
            test_pass = False
    # PID was not found, assume VM was not launched
    else:
        if not non_verbose:
            print("Virtual Machine " + tested_vm.strip() +
                  " not found running in system.")
        test_pass = False
    return test_pass


def run_local_vm_test(system_os:string, tested_vm:string, non_verbose:bool):
    '''
    Run the encryption test on already running VMs (no auto launch).
    If a command for a specific VM is provided, perform the test on that VM.
    If no VM command is provided, then launch the user UI.
    '''
    # Dictionary (PID:VM COMMAND) of running VM's in the system
    available_vms = get_virtual_machines(system_os)
    # Will pass if the provided VMs pass the encryption test
    test_pass = False

    # No already running VMs found, return failure
    if not available_vms:
        if not non_verbose:
            print("No running VMs found")
        return False

    # Can't run UI with nonVerbose raised, return failure
    if not tested_vm and non_verbose:
        print("Need to provide VMs to be tested in order to run with nonVerbose.")
        return False

    # A VM command was provided, perform encryption test on desired VM
    if tested_vm:
        # Perform Test on provided VM
        test_pass = test_virtual_machine(tested_vm, available_vms, non_verbose)
        # Test passes
        if test_pass and not non_verbose:
            print("Provided VM passed the encryption test.")
        # Test fails
        elif not test_pass and not non_verbose:
            print("VM failed the encryption test.")

    # No VM command was provided, launch manual test with user UI.
    else:
        # Dictionary of VMs that will be tested (provided by user)
        vm_list = {}
        # Print all the available VMs
        print(
            "Input PID of the VM you would like to test memory for. "
            "After all the desired machines have been added, input q or quit to run tests.\n")
        for vm_pid, vm_command in available_vms.items():
            print('\nVirtual Machine: ' + vm_pid)
            print(vm_command)
        # Will continue until user inputs q or quit
        while True:
            curr_input = input('What VM would you like to test? (Enter PID): ')
            if(
                curr_input.isnumeric()
                and curr_input in available_vms.keys()
                and curr_input not in vm_list.keys()
            ):
                vm_list[curr_input] = available_vms[curr_input].strip()
                print('Virtual Machine ' + curr_input + ' has been added.')
            # Input provided is not a valid PID
            elif(
                (not curr_input.isnumeric() or curr_input not in available_vms.values())
                and curr_input.lower() not in ('quit', 'q')):
                print('Not a valid number or PID.')
            # Input provided already added
            elif curr_input in vm_list.keys():
                print('VM already added to testing list.')
            # Close menu
            elif curr_input.lower() in ('quit', 'q'):
                break

        # Will turn false if one of the provided VM's tests fail
        test_pass = True
        # The user added not VM's for testing
        if vm_list:
            for virtual_machine in vm_list.values():
                if not test_virtual_machine(virtual_machine, available_vms, non_verbose):
                    test_pass = False
        elif not vm_list and not non_verbose:
            print("No virtual Machines added. Ending test.")

        # All the provided VMs passed
        if test_pass:
            print("All the provided VMs passed the encryption test.")
        # Not of all he provided VMs passed the encryption test
        else:
            print("At least one VM failed the encryption test.")
    # Return result
    return test_pass

def print_vm_memory(tested_vm,available_vms):
    '''
    From a provided VM, print one page of its memory.
    '''
    #Find VM, get its PID
    vm_pid = find_virtual_machine(tested_vm, available_vms)
    #PID found, print memory
    if vm_pid:
        print("Provided Virtual Machine found!")
        print('')
        print("PID: " + str(vm_pid))
        print(tested_vm)
        print('')
        print("Printing one page of memory for VM: " + vm_pid)
        #Get the memory contents
        vm_memory = set_up_memory_for_printing(tested_vm, vm_pid)
        #For each line in the memory page, print its contents
        print(vm_memory.stdout.decode('utf-8'))
     #PID was not found, so assusming VM was either not launched or there was a user input error
    else:
        print("Virtual Machine " + tested_vm.strip() + " not found running in system.")

def run_print_memory(system_os:string,tested_vm:string,non_verbose:bool):
    '''
    Print one page of memory of running VMs (no auto launch).
    If a command for a specific VM is provided, print the page for that VM.
    If no VM command is provided, then launch the user UI, where the user can choose on what VMs to print the memory for
    '''
    #All of the currently running VM in the system
    available_vms = get_virtual_machines(system_os)

    #Can't run print with nonVerbose raised
    if non_verbose:
        print("Can't run memory printer with nonVerbose flag.")
        return False

    #No running VMs found
    if not available_vms:
        print("No running VMs found")
        return False

    #A VM was provided, print its memory
    if tested_vm:
        print_vm_memory(tested_vm,available_vms)
    #No VM provided, launch the UI
    else:
        #Dictionary of VMs requested by user
        vm_list = {}
        #Print available VMs
        print("Input PID of the VM you would like to print memory for. After all the desired machines have been added, input q or quit to run tests.\n")
        for vm_pid, vm_command in available_vms.items():
            print('\nVirtual Machine: ' + vm_pid)
            print(vm_command)
        #Launch UI ask for user input
        while True:
            curr_input = input('What VM would you like to print memory for? (Enter PID): ')
            if(
                curr_input.isnumeric()
                and curr_input in available_vms.keys()
                and curr_input not in vm_list.keys()
            ):
                vm_list[curr_input] = available_vms[curr_input].strip()
                print('Virtual Machine ' + curr_input + ' has been added.')
            # Input provided is not a valid PID
            elif(
                (not curr_input.isnumeric() or curr_input not in available_vms.values())
                and curr_input.lower() not in ('quit', 'q')):
                print('Not a valid number or PID.')
            # Input provided already added
            elif curr_input in vm_list.keys():
                print('VM already added to printing list.')
            # Close menu
            elif curr_input.lower() in ('quit', 'q'):
                break
        # Print memory for each of the vms provided
        if vm_list:
            for virtual_machine in vm_list.values():
                print_vm_memory(virtual_machine, available_vms)
        else:
            print("No virtual Machines added. Ending test.")
