import subprocess
import memoryReader 
import encryptionTest
from re import sub

def getVirtualMachines(version):
    '''
    Will find all of the running VMs in the system (if launched with QEMU) and return a dictionary where the key is
    the VM PID and the value is the command used to launch the VM.
    '''

    #Will contain the available VMs
    availableVms = {}

    #Commands for different distros
    qemuCommandList = {'ubuntu':'[q]emu-system-x86_64', 'debian': '[q]emu-system-x86_64', 'fedora': '[q]emu-kvm', 'rhel': '[q]emu-kvm', 
    'opensuse-tumbleweed': '[q]emu-system-x86_64', 'opensuse-leap': '[q]emu-system-x86_64', 'centos':'[q]emu-kvm', 'oracle':'[q]emu-kvm'}

    #Default command if distro not in list
    if version not in qemuCommandList:
        qemuCommand = "[q]emu"
    else:
        qemuCommand = qemuCommandList[version]

    #Use ps command to find running VMs
    vms = subprocess.Popen('ps axo pid,command | egrep ' +  qemuCommand,shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    
    #Loop to get available VMs and their PIDs, put them into the dictionary.
    for line in iter(vms.stdout.readline, b''):
        currVM = line.decode("utf-8")
        currVM = currVM.lstrip()
        currPID = ''
        for x in currVM:
            #The first part of the line will be the VM's PID
            if x.isnumeric():
                currPID += str(x)
            elif x == ' ':
                break
        #The rest of the line will be the VM command
        VMCommand = currVM[len(currPID) + 1:]
        #Add the VM to the dictionary
        availableVms[currPID] = VMCommand
    
    #Return dictionary
    return availableVms

def findVirtualmachine(VMcommand, availableVMs):
    '''
    From a given command used to launch a VM, find its PID from a the dictionary of currently running VM's. 
    '''
    #Format command if necessary
    VMcommand = sub(' +', ' ', VMcommand)
    #Loop through dictionary
    for PID,VM in availableVMs.items():
        #Command found in dictionary, return PID
        if VMcommand == VM.strip():
            return PID
    #VM not found
    return False

def setupMemoryforTesting(command,PID):
    '''
    With the command used to launch the VM and the PID corresponding to the VM, grab a page of its memory and then
    format it for testing. 
    '''
    #Will contain memory
    memory = None
    #Put the memory contents into a list
    structuredMemory = []

    #Find the size of the memory (Eg QEMU -m 2048 M)
    memsize = memoryReader.getMemorySize(command)
    #With the memory size found, find the top and bottom adresses corresponding to the VMs memory pages in the host system
    topaddr, botaddr = memoryReader.findRamSpecificMemory(PID,memsize)
    #Grab one page of memory for testing
    memory = memoryReader.readOneMemoryPageforPrintforTest(PID,topaddr,botaddr)
    
    #Add each line of the memory page into a list
    for line in iter(memory.stdout.readline, b''):
        structuredMemory.append(line)

    #Remove unecessary lines that come from the subprocess command (Eg 'dd: /proc/"+ PID + "/mem: cannot skip to specified offset\n')
    del structuredMemory[0]
    del structuredMemory[-2:]
    
    #Return the memory ready for testing
    return structuredMemory

def setupMemoryforPrinting(command,PID):
    '''
    With the command used to launch the VM and the PID corresponding to the VM, grab a page of its memory and return it 
    for printing. Unlike setupMemoryforTesting, no formatting is necessary since the memory is just being printed, not analyzed.
    '''
    #Will contain memory
    memory = None

    #Find the size of the memory (Eg QEMU -m 2048 M)
    memsize = memoryReader.getMemorySize(command)
    #With the memory size found, find the top and bottom adresses corresponding to the VMs memory pages in the host system
    topaddr, botaddr = memoryReader.findRamSpecificMemory(PID,memsize)
    #Grab one page of memory for printing
    memory = memoryReader.readOneMemoryPageforPrint(PID,topaddr,botaddr)

    #Return the memory for printing
    return memory


def testVirtualMachine(testedVM,availableVMs,nonVerbose):
    '''
    For a given Virtual machine, perform the entropy encryption test in one page of its memory and return results.
    '''
    #Will turn False if test fails or VM was not found
    testPass = True
    #Find VM in system and get its PID
    VMPID = findVirtualmachine(testedVM,availableVMs)

    #PID was not found, so assusming VM was either not launched or there was a user input error, return failure
    if not VMPID:
        if not nonVerbose:
            print("Virtual Machine " + testedVM.strip() + " not found running in system.")
        testPass = False
    #PID found, perform test
    else:
        if not nonVerbose:
            print("Provided Virtual Machine found!")
            print('')
            print("PID: " + str(VMPID))
            print(testedVM)
            print('')
            print("Testing virtual machine " + VMPID + " for encryption")
        #Get 1 formatted page of memory for testing
        VMMemory = setupMemoryforTesting(testedVM, VMPID)
        #Perform test on the memory
        entropyValue = encryptionTest.entropyEncryptionTest(VMMemory)
        #Entropy value is 7 or higher, encryption test passes
        if entropyValue >= 7:
            if not nonVerbose:
                print("Entropy value " + str(entropyValue))
                print("Virtual Machine " + VMPID + " is probably encrypted.")
        #Entropy value lower than 7, test fails.
        else:
            if not nonVerbose:
                print("Entropy value " + str(entropyValue))
                print("Virtual Machine " + VMPID + " is probably not encrypted.")
            testPass = False
    #Return test results
    return testPass

def runLocalVMTest(version,testedVM,nonVerbose):
    '''
    Run the encryption test on already running VMs (no auto launch).
    If a command for a specific VM is provided, perform the test on that VM.
    If no VM command is provided, then launch the user UI, where the user can choose on what VMs to perform the test
    from a list of already running VMs
    '''
    #Dictionary (PID:VM COMMAND) of running VM's in the system
    availableVMs = getVirtualMachines(version)
    #Will pass if the provided VM or all the provided VMs (if UI is launched) pass the encryption test
    testPass = False
    
    #No already running VMs found, return failure
    if not availableVMs:
        if not nonVerbose:
            print("No running VMs found")
        return False
    
    #Can't run UI with nonVerbose raised, return failure
    if not testedVM and nonVerbose:
        print("Need to provide VMs to be tested in order to run with nonVerbose.")
        return False
    
    #A VM command was provided, perform encryption test on desired VM
    if testedVM:
        #Perform Test on provided VM
        testPass = testVirtualMachine(testedVM,availableVMs,nonVerbose)
        #Test passes
        if testPass and not nonVerbose:
            print("Provided VM passed the encryption test.")
        #Test fails
        elif not testPass and not nonVerbose:
            print("VM failed the encryption test.")

        #Return result
        return testPass
    #No VM command was provided, launch manual test with user UI.
    else:
        #Dictionary of VMs that will be tested (provided by user)
        vmsList = {}
        #Print all the available VMs
        print("Input PID of the VM you would like to test memory for. After all the desired machines have been added, input q or quit to run tests.\n")
        for VM in availableVMs:
            print('\nVirtual Machine: ' + VM)
            print(availableVMs[VM])
        #Will continue until user inputs q or quit
        while(1):
            currInput = input('What VM would you like to test? (Enter PID): ')
            #Close menu
            if currInput == 'quit' or currInput == 'q':
                break
            #Machine requested is available and not added yet
            elif currInput.isnumeric() and currInput in availableVMs.keys() and currInput not in vmsList.keys():
                vmsList[currInput] = availableVMs[currInput].strip()
                print('Virtual Machine ' + currInput + ' has been added.')
            #Input provided is not a valid PID
            elif not currInput.isnumeric or currInput not in availableVMs.values():
                print('Not a valid number or PID.')
            #Input provided already added
            elif currInput in vmsList.keys():
                print('VM already added to testing list.')
        
        #Will turn false if one of the provided VM's tests fail
        allPass = True
        #The user added not VM's for testing
        if not vmsList:
            if not nonVerbose:
                print("No virtual Machines added. Ending test.")
            return True
        #Perform the encryption test on each of the provided VMs
        else:
            for VM in vmsList.values():
                #One of the VM tests failed
                if not testVirtualMachine(VM,availableVMs,nonVerbose):
                    allPass = False
        
        #All the provided VMs passed
        if allPass:
            print("All the provided VMs passed the encryption test.")
        #Not of all he provided VMs passed the encryption test
        else:
            print("At least one VM failed the encryption test.")
        
        #Return test results
        return allPass

def printMemory(testedVM,availableVMs):
    '''
    From a provided VM, print one page of its memory.
    '''
    #Find VM, get its PID
    VMPID = findVirtualmachine(testedVM,availableVMs)
    #PID was not found, so assusming VM was either not launched or there was a user input error
    if not VMPID:
        print("Virtual Machine " + testedVM.strip() + " not found running in system.")
        return False
    #PID found, print memory
    else:
        print("Provided Virtual Machine found!")
        print('')
        print("PID: " + str(VMPID))
        print(testedVM)
        print('')
        print("Printing one page of memory for VM: " + VMPID)
        #Get the memory contents
        VMMemory = setupMemoryforPrinting(testedVM, VMPID)
        #For each line in the memory page, print its contents
        for line in VMMemory:
            print(line)

        #Print worked, no issues found
        return True

def runPrintMemory(version,testedVM,nonVerbose):
    '''
    Print one page of memory of running VMs (no auto launch).
    If a command for a specific VM is provided, print the page for that VM.
    If no VM command is provided, then launch the user UI, where the user can choose on what VMs to print the memory for
    '''
    #All of the currently running VM in the system
    availableVMs = getVirtualMachines(version)
    
    #Can't run print with nonVerbose raised
    if nonVerbose:
        print("Can't run memory printer with nonVerbose flag.")
        return False
    
    #No running VMs found
    if not availableVMs:
        print("No running VMs found")
        return False
    
    #A VM was provided, print its memory
    if testedVM:
        printMemory(testedVM,availableVMs)
    #No VM provided, launch the UI
    else:
        #Dictionary of VMs requested by user
        vmsList = {}
        #Print available VMs
        print("Input PID of the VM you would like to print memory for. After all the desired machines have been added, input q or quit to run tests.\n")
        for VM in availableVMs:
            print('\nVirtual Machine: ' + VM)
            print(availableVMs[VM])
        #Launch UI ask for user input
        while(1):
            currInput = input('What VM would you like to print memory for? (Enter PID): ')
            #Quit menu if this is input
            if currInput == 'quit' or currInput == 'q':
                break
            #Add input to print list
            elif currInput.isnumeric() and currInput in availableVMs.keys() and currInput not in vmsList.keys():
                vmsList[currInput] = availableVMs[currInput].strip()
                print('Virtual Machine ' + currInput + ' has been added.')
            #Input is not valid
            elif not currInput.isnumeric or currInput not in availableVMs.values():
                print('Not a valid number or PID.')
            #Input already added
            elif currInput in vmsList.keys():
                print('VM already added to printing list.')
        
        #No inputs were added
        if not vmsList:
            print("No virtual Machines added. Ending test.")
        #Print memory for each of the VMs provided
        else:
            for VM in vmsList.values():
                printMemory(VM,availableVMs)
