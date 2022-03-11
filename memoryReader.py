import subprocess

def hexToDecimal(hexNum):
    '''
    Convert a hexnumber (given in string) into a decimal integer
    '''
    i = int(hexNum, 16)
    return i

def convertGBToBytes(memorySize):
    '''
    Convert a given memory size in GB into bytes
    '''
    bytes = memorySize * 1073741824
    return bytes

def convertMBToBytes(memorySize):
    '''
    Convert a given memory size in MB into bytes
    '''
    bytes = memorySize * 1048576
    return bytes

def getMemorySize(line):
    '''
    From a QEMU command find what memory size was passed through to find the appropriate memory in the host sytem.
    Default memory if no memory argument was passed is 128 MB.
    '''
    atMemory = False
    memorySizeStr = ''
    #Go through the command
    for i,x in enumerate(line):
        #Found the memory flag
        if line[i:i+3] == '-m ':
            atMemory = True
        #Get the memory size number
        elif atMemory == True and x.isnumeric():
            memorySizeStr += x
        #Get the memory size tag (GB or MB), if no tag assume MB
        elif atMemory == True and ((x.isalpha() and x !='m') or line[i:i+1] == ' -'):
            memorySizeInt = int(memorySizeStr)
            #Convert to bytes and return
            if x == 'G':
                memorySizeInt = convertGBToBytes(memorySizeInt)
                return str(memorySizeInt)
            elif x == 'M':
                memorySizeInt = convertMBToBytes(memorySizeInt)
                return str(memorySizeInt)
            else:
                memorySizeInt = convertMBToBytes(memorySizeInt)
                return str(memorySizeInt)
    
    #No -m flag was passed, return default
    return convertMBToBytes(128)

def findRamSpecificMemory(PID,machineMemory):
    '''
    Using a VM's PID and memory size, find its memory contents in the host system. 
    '''
    #Command to map the PID memory
    vmMemory = subprocess.Popen(['sudo', 'cat', '/proc/' + PID + '/maps'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    topAddress = ''
    botAddress = ''
    #Loop to find the top and bottom addresses of the VMs memory
    for line in iter(vmMemory.stdout.readline, b''):
        currNum = ''
        for char in line.decode("utf-8"):
            if char == ' ':
                botAddress = currNum
                break
            elif char == '-':
                topAddress = currNum
                currNum =''
            else:
                currNum += char
        num1 = hexToDecimal(topAddress)
        num2 = hexToDecimal(botAddress)
        memorysize = num2 - num1
        #If addresses found match the size of VM memory, return those addresses
        if memorysize == int(machineMemory):
            return topAddress, botAddress
        else:
            topAddress, botAddress = '', ''
    #Return empty string if VM memory address not found
    return topAddress, botAddress

def readEntireMemory(PID,topAddress, botAddress):
    '''
    Using the PID and addresses found from findRamSpecificMemory function, get the all of the VM's memory.
    '''
    #No VM memory found
    if not topAddress or not botAddress:
        return None
    #Get memory using sudo dd
    else:  
        num1 = hexToDecimal(topAddress)
        num2 = hexToDecimal(botAddress)
        skipNum = num1 // 4096
        countNum = (num2 - num1) // 4096
        #Return VM memory content
        memoryPage = subprocess.Popen('sudo dd if=/proc/' + PID + '/mem bs=4096 skip=' + str(skipNum) + ' count=' + str(countNum), shell=True,stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return memoryPage

def readOneMemoryPageforPrintforTest(PID,topAddress, botAddress):
    '''
    Using the PID and addresses found from findRamSpecificMemory function, get one page of the memory conent,
    '''
    #No VM memory found
    if not topAddress or not botAddress:
        return None
    #Get memory using sudo dd, get one page by setting count to 1
    else:  
        num1 = hexToDecimal(topAddress)
        skipNum = num1 // 4096
        #Return VM memory content
        memoryPage = subprocess.Popen('sudo dd if=/proc/' + PID + '/mem bs=4096 skip=' + str(skipNum) + ' count=1', shell=True,stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return memoryPage

def readOneMemoryPageforPrint(PID,topAddress, botAddress):
    '''
    Using the PID and addresses found from findRamSpecificMemory function, get one page of the memory formatted for printing
    '''
    #No VM memory found
    if not topAddress or not botAddress:
        return None
    #Get memory using sudo dd, format it for printing by using hexdump
    else:  
        num1 = hexToDecimal(topAddress)
        skipNum = num1 // 4096
        memoryPage = subprocess.run('sudo dd if=/proc/' + PID + '/mem bs=4096 skip=' + str(skipNum) + ' count=1' + " | hexdump -C", shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        page = memoryPage.stdout.decode("utf-8").split('\n')
        return page