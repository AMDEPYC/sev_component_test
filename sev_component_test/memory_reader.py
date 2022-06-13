'''Functions that allow the program to access a VM's memory in the host system'''
import string
import subprocess


def hex_to_decimal(hex_num:string) -> int:
    '''
    Convert a hexnumber (given in string) into a decimal integer
    '''
    return int(hex_num, 16)


def convert_gb_to_bytes(memory_size:int) -> int:
    '''
    Convert a given memory size in GB into bytes
    '''
    return memory_size * 1073741824


def convert_mb_to_bytes(memory_size:int) -> int:
    '''
    Convert a given memory size in MB into bytes
    '''
    return memory_size * 1048576


def get_memory_size(line:string) -> string:
    '''
    From a QEMU command find what memory size was passed through to find the appropriate memory in the host sytem.
    Default memory if no memory argument was passed is 128 MB.
    '''
    at_memory = False
    memory_size_string = ''
    # Go through the command
    for letter_num, char in enumerate(line):
        # Found the memory flag
        if line[letter_num:letter_num+3] == '-m ':
            at_memory = True
        # Get the memory size number
        elif at_memory and char.isnumeric():
            memory_size_string += char
        # Get the memory size tag (GB or MB), if no tag assume MB
        elif at_memory and ((char.isalpha() and char != 'm') or line[letter_num:letter_num+1] == ' -'):
            memory_size_integer = int(memory_size_string)
            # Convert to bytes and return
            if char == 'G':
                memory_size_integer = convert_gb_to_bytes(memory_size_integer)
            elif char == 'M':
                memory_size_integer = convert_mb_to_bytes(memory_size_integer)
            else:
                memory_size_integer = convert_mb_to_bytes(memory_size_integer)
            break
    if not memory_size_string:
        memory_size_integer = convert_mb_to_bytes(128)
    return str(memory_size_integer)


def find_ram_specific_memory(pid:string, machine_memory:string) -> string:
    '''
    Using a VM's PID and memory size, find its memory contents in the host system. 
    '''
    try:
        # Command to map the PID memory
        vm_memory_raw = subprocess.run(
            'sudo cat /proc/' + pid + '/maps', shell=True, check=True, capture_output=True)
        top_address = ''
        bot_address = ''
        vm_memory = vm_memory_raw.stdout.decode("utf-8").split('\n')
        # Loop to find the top and bottom addresses of the VMs memory
        for line in vm_memory:
            curr_num = ''
            for char in line:
                if char == '-':
                    top_address = curr_num
                    curr_num = ''
                elif char == ' ':
                    bot_address = curr_num
                    break
                else:
                    curr_num += char
            num_1 = hex_to_decimal(top_address)
            num_2 = hex_to_decimal(bot_address)
            memory_size = num_2 - num_1
            # If addresses found match the size of VM memory, return those addresses
            if memory_size != int(machine_memory):
                top_address, bot_address = '', ''
            else:
                break
        # Return empty string if VM memory address not found
        return top_address, bot_address
    except (subprocess.CalledProcessError) as err:
        print("Could not find the VM memory in host system. Error returned: " +
              err.stderr.decode("utf-8").strip())
        return '', ''


def read_entire_memory(pid:string, top_address:string, bot_address:string):
    '''
    Using the PID and addresses found from find_ram_specific_memory function,
    get the all of the VM's memory.
    '''
    # Get memory using sudo dd
    if top_address or not bot_address:
        num_1 = hex_to_decimal(top_address)
        num_2 = hex_to_decimal(bot_address)
        skip_num = num_1 // 4096
        count_num = (num_2 - num_1) // 4096
        try:
            # Return VM memory content
            memory_page = subprocess.run('sudo dd if=/proc/' + pid + '/mem bs=4096 skip=' + str(
                skip_num) + ' count=' + str(count_num), shell=True, check=True, capture_output=True)
            return memory_page
        except (subprocess.CalledProcessError) as err:
            print("Could not read the VM memory in host system. Error returned: " +
                  err.stderr.decode("utf-8").strip())
            return None
    # No VM memory found
    else:
        return None


def read_one_memory_page_for_testing(pid:string, top_address:string, bot_address:string):
    '''
    Using the PID and addresses found from find_ram_specific_memory function,
    get one page of the memory conent,
    '''
    if top_address or not bot_address:
        num_1 = hex_to_decimal(top_address)
        skip_num = num_1 // 4096
        try:
            # Return VM memory content
            memory_page = subprocess.run('sudo dd if=/proc/' + pid + '/mem bs=4096 skip=' + str(
                skip_num) + ' count=1', shell=True, check=True, capture_output=True)
            return memory_page
        except (subprocess.CalledProcessError) as err:
            print("Could not read the VM memory in host system. Error returned: " +
                  err.stderr.decode("utf-8").strip())
            return None
    # Get memory using sudo dd
    else:
        return None


def read_one_memory_page_for_printing(pid:string, top_address:string, bot_address:string):
    '''
    Using the PID and addresses found from find_ram_specific_memory function,
    get one page of the memory formatted for printing
    '''
    if top_address or not bot_address:
        num_1 = hex_to_decimal(top_address)
        skip_num = num_1 // 4096
        try:
            # Get memory using sudo dd, format it for printing by using hexdump
            memory_page = subprocess.run('sudo dd if=/proc/' + pid + '/mem bs=4096 skip=' + str(
                skip_num) + ' count=1', shell=True, check=True, capture_output=True)
            hex_dump = subprocess.run(
                "hexdump -C", input=memory_page.stdout, shell=True, check=True, capture_output=True)
            return hex_dump
        except (subprocess.CalledProcessError) as err:
            print("Could not read the VM memory in host system. Error returned: " +
                  err.stderr.decode("utf-8").strip())
            return None
    # No VM memory found
    else:
        return None
