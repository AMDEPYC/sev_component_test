import os
from re import sub
import subprocess
import argparse
from packaging import version
import OVMFFunctions
import localVMTest
import autoVMTest
import sys

class colors:
    '''
    Print OK, FAILURE and WARNING in appropriate colors
    '''
    reset='\033[0m'
    red='\033[31m'
    green='\033[32m'
    yellow='\033[93m'

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--stopfailure", help="Stop the program when a test fails", action="store_true")
parser.add_argument("-t", "--test", nargs='+', help="Specify what features to test for.", default=['sev','sev-es','sev-snp'])
parser.add_argument("-tl", "--testlocal", nargs='?', help="Leave empty to run manual test, or provide command of desired VM to test for encryption.",default="not raised")
parser.add_argument("-pl", "--printlocal", nargs ='?', help="Leave empty to run manual memory printer, or provide command of desired VM to print memory.", default="not raised")
parser.add_argument("-at", "--autotest", help="Run automatic VM encryption test", action="store_true")
parser.add_argument("-nv", "--nonverbose", help="Run test with no print statements", action="store_true")
args = parser.parse_args()

def hexToBinary(hex):
    '''
    Converts hex number to binary
    '''
    return bin(int(hex, 16))[2:]

def printResult(component,command,found,expectation,result):
    '''
    Format in which test results will be printed. It starts with the componenet being tested, followed by the command used to find said componenent status,
    then what the test found in the system, then what was expected to be found, and lastly whether the test passed or not.
    '''
    #Test passes
    if result == True:
        print("- " + component + " [ " + command + " ] Found: " + found + " Expected: " + expectation + colors.green + " OK" + colors.reset)
    #Test fails
    elif result == False:
        print("- " + component + " [ " + command + " ] Found: " + found + " Expected: " + expectation + colors.red + " FAIL" + colors.reset)
    #Test can't be run due to certain set-ups in the system
    elif result == None:
        print("- " + component + " [ " + command + " ] Found: " + found + " Expected: " + expectation + colors.yellow + " WARNING" + colors.reset)

def checkEAX(readOut, feature):
    '''
    Take in the cpuid read from the findCPUIDSupport function and then parse the input to get 
    either the bit 1 or bit 0 from the eax register, depending on the future that is being checked (SME or SEV).
    '''
    #Getting the eax register value
    hexnum = readOut[1][9]
    #Converting it to binary and then flipping it in order to read it. 
    binaryValue = hexToBinary(hexnum)
    binaryValue = binaryValue[::-1]

    #Return bit 0 if testing for SME
    if feature == "SME":
        return binaryValue[0]
    #Return bit 1 if testing for SEV
    elif feature == "SEV":
        return binaryValue[1]

def findCPUIDSupportSME(nonVerbose):
    '''
    Check the CPUID function 0x8000001f and look at the eax register in order to tell
    whether or not the current CPU supports SME. If the function 0x8000001f can't be found, then  
    print and return a failure. If not, call the function checkEAX to retrieve the eax register value
    and then print out whether or not SME is available on the system.
    '''
    #Turns true if test passes
    passCheck = False
    #Name of component being tested
    component = "CPUID function 0x8000001f bit 0 for SME"
    #Expected test result
    expectation = "EAX bit 0 to be '1'"
    #Will change to what the test finds
    foundResult = None

    #Command being used
    command = "cpuid -r -1 -l 0x8000001f"
    #Use CPUID to retrieve the eax value of the 0x8000001f function
    read = subprocess.run("cpuid -r -1 -l 0x8000001f | sed 's/.*eax=//'", shell=True, stdout = subprocess.PIPE, stderr=subprocess.PIPE)
    readerr = read.stderr.decode("utf-8").strip()
    readOut = read.stdout.decode("utf-8").split('\n')

    #Sometimes the flag -l causes an error, so if that is the case, we run the command again without it.
    if readerr == "cpuid: unrecognized option letter: l":
        #command being used
        command = "cpuid -r -1 0x8000001f"
        read = subprocess.run("cpuid -r -1 0x8000001f | sed 's/.*eax=//'", shell=True, stdout = subprocess.PIPE, stderr=subprocess.PIPE)
        readerr = read.stderr.decode("utf-8").strip()
        readOut = read.stdout.decode("utf-8").split('\n')
    
    #Function 0x8000001f does not exist or an error was found, return failure
    if readerr == "cpuid: unrecognized argument: 0x8000001f":
        foundResult = readerr
    #Check and see if eax register value exists
    elif readOut[1]:
        #Check for SME bit 0 value.
        bit0 = checkEAX(readOut, 'SME')
        #bit 0 is 1, test passes
        if bit0 == '1':
            passCheck = True
            foundResult = "EAX bit 0 is " + "'" + str(bit0) + "'"
        #bit 0 is 0, test fails
        else:
            foundResult = "EAX bit 0 is " + "'" + str(bit0) + "'"
    #The function 0x8000001f was not found, but no error was returned by the system.
    else:
        foundResult = "EMPTY"
    
    #Return test results
    if nonVerbose:
        return passCheck
    else:
        printResult(component,command,foundResult,expectation,passCheck)
        return passCheck
        
        
def findCPUIDSupportSEV(nonVerbose):
    '''
    Check the CPUID function 0x8000001f and look at the eax register in order to tell
    whether or not the current CPU supports SEV. If the function 0x8000001f can't be found, then  
    print and return a failure. If not, call a separate function to retrieve the eax register value
    and then print out whther or not SEV is available on the system.
    '''
    #Will turn true if test passes
    passCheck = False
    #Component being tested
    component = "CPUID function 0x8000001f bit 1 for SEV"
    #Expected Result
    expectation = "EAX bit 1 to be '1'"
    #What was found in the test as result
    foundResult = None

    #Command being used
    command = "cpuid -r -1 -l 0x8000001f"
    #Use CPUID to retrieve the eax value of the 0x8000001f function
    read = subprocess.run("cpuid -r -1 -l 0x8000001f | sed 's/.*eax=//'", shell=True, stdout = subprocess.PIPE, stderr=subprocess.PIPE)
    readerr = read.stderr.decode("utf-8").strip()
    readOut = read.stdout.decode("utf-8").split('\n')

    #Sometimes the flag -l causes an error, so if that is the case, we run the command again without it.
    if readerr == "cpuid: unrecognized option letter: l":
        #New command being used
        command = "cpuid -r -1 0x8000001f"
        read = subprocess.run("cpuid -r -1 0x8000001f | sed 's/.*eax=//'", shell=True, stdout = subprocess.PIPE, stderr=subprocess.PIPE)
        readerr = read.stderr.decode("utf-8").strip()
        readOut = read.stdout.decode("utf-8").split('\n') 
    
    #Function 0x8000001f does not exist or an error was found, return failure
    if readerr == "cpuid: unrecognized argument: 0x8000001f":
        foundResult = readerr
    #Check and see if eax register value exists
    elif readOut[1]:
        #Check for eax bit 1 value to find SEV support
        bit1 = checkEAX(readOut, 'SEV')
        #Bit 1 is 1, test passes
        if bit1 == "1":
            passCheck = True
            foundResult = "EAX bit 1 is " + "'" + str(bit1) + "'"
        #Bit 1 is 0, test fails
        else:
            foundResult = "EAX bit 1 is " + "'" + str(bit1) + "'"
    #The function 0x8000001f was not found, but no error was returned by the system.
    else:
        foundResult = "EMPTY"
    
    #Return test results
    if nonVerbose:
        return passCheck
    else:
        printResult(component,command,foundResult,expectation,passCheck)
        return passCheck

def checkVirtualization(nonVerbose):
    '''
    Check to see if virtualization is availabele on the system, and also make sure that it is AMD virtualization
    that is available. 
    '''
    #Test pass or Fail
    passCheck = False
    #Component being tested
    component = "Virtualization capabilities"
    #Expected result
    expectation = "Virtualization: AMD-V"
    #Found result in test
    foundResult = None

    #Use lscpu to find virtualization
    command = "lscpu | grep Virtualization"
    virtualizationFeature = subprocess.run("lscpu | grep Virtualization", shell=True, stdout = subprocess.PIPE)
    virtString = sub(' +', ' ',virtualizationFeature.stdout.decode('utf-8').strip())
    
    #Both virtualization and AMD-V are found, test passes
    if virtString and 'AMD-V' in virtString:
        passCheck = True
        foundResult = virtString
    #Virtualization found, but not AMD-V, test fails
    elif virtString:
        foundResult = virtString
    #Virtualization not found, test fails
    else:
        foundResult = "EMPYT"

    #Return test results
    if nonVerbose:
        return passCheck
    else:
        printResult(component,command,foundResult,expectation,passCheck)
        return passCheck

def getSMEString(string):
    '''
    Format the SME support string from kernel message. Receive original string from find OSSupportSME function. 
    Remove ccp and return only SME support found string.
    '''
    #CCP 
    ccp = ''
    #Formatted string will be returned here
    SMESupport = ''
    outofccp = False
    for x in string:

        if not x.isalpha() and not outofccp:
            ccp += x
        #Out of the ccp, collect SME Support string
        elif x.isalpha() and not outofccp:
            outofccp = True
            SMESupport += x
        #Continue to collect SME messge
        elif outofccp:
            SMESupport += x
    
    #Formatted string returned
    return SMESupport

def findOSSupportSME(nonVerbose):
    '''
    Check if SME is enabled on the OS by checking the kernel message. This check will only run if SME testing is enabled
    with the --test flag. 
    '''
    #Becomes true if test passes
    passCheck = False
    component = "OS support for SME"
    expectation = "AMD Memory Encrtyption Features active: SME"
    foundResult = None

    #Check for SME support on dmesg
    command = "dmesg | grep SME"
    SMETest = subprocess.run("dmesg | grep SME", shell=True, stdout = subprocess.PIPE)
    SMEstring = SMETest.stdout.decode('utf-8').strip()

    #SME support found on kernel message check, test passes.
    if SMEstring: 
        #Call to get formatted SME support
        SMEstring = getSMEString(SMEstring)
        passCheck = True
        foundResult = SMEstring
    #SME support not found, test fails
    else:
        foundResult = "EMPTY"

    #Return test results
    if nonVerbose:
        return passCheck
    else:
        printResult(component,command,foundResult,expectation,passCheck)
        return passCheck

def getAsidNum(AsidString):
    '''
    Format string from getSEVStringAndASIDS. Add numbers to a string until a non-number is found to get ASID number
    '''
    num = ''
    for x in AsidString:
        if x.isnumeric():
            num += x
        else:
            return num


def getSEVStringAndASIDS(string):
    '''
    Get SEV or SEV-ES support string from kernel message from findOSSupport function.
    Remove ccp, return ASIDs if any available and support found string. 
    '''
    #ccp
    ccp = ''
    #Will contain the kernel support string
    SEVSupport = ''
    #Will conatin found ASIDs
    availableASIDS = ''
    outofccp = False
    inasidcount = False
    supportFound = False
    for x in string:
        #At ccp
        if not x.isalpha() and not outofccp:
            ccp += x
        #Out of CCP, collect support string
        elif x.isalpha() and not outofccp:
            outofccp = True
            SEVSupport += x
        #Support string completed
        elif (SEVSupport == 'SVM: SEV supported' or SEVSupport == 'SEV supported' or SEVSupport == 'SEV-ES supported') and not supportFound:
            supportFound = True
        #Continue to collect support string
        elif not supportFound:
            SEVSupport += x
        #At available Available ASIDs in string
        elif x.isnumeric() and not inasidcount:
            inasidcount = True
            availableASIDS += x
        #Continue to collect ASID num
        elif inasidcount:
            availableASIDS += x
    
    #ASIDs found
    if availableASIDS != '':
        asidNum = getAsidNum(availableASIDS)
    #No ASIDS found
    else:
        asidNum = False

    #Return appropriate strings
    return SEVSupport, availableASIDS, asidNum
    
def findOSSupportSEV(nonVerbose):
    '''
    Check if SEV is enabled on the os by checking the kernel message. If the feature can't be found in the dmesg,
    then the function will return and print the failure.
    '''
    #Test Components
    passCheck = False
    component = "OS support for SEV"
    expectation = "SEV supported"
    foundResult = None
    
    #Look at the kernel message for SEV SUPPORT enablement
    command = "dmesg | grep -w 'SEV supported'"
    SEVTest = subprocess.run("dmesg | grep -w 'SEV supported'", shell=True, stdout = subprocess.PIPE, stderr=subprocess.PIPE)
    
    #SEV support found, test passes
    if SEVTest.stdout.decode('utf-8').strip(): 
        SEVString = SEVTest.stdout.decode('utf-8').strip()
        #Call to get formatted SEV support string
        SEVSupport,availableASIDS,asidNum = getSEVStringAndASIDS(SEVString)
        passCheck = True
        foundResult = SEVSupport
    #Support for SEV not found,test fails
    else:
        foundResult = "Empty"
    
    #Return test results
    if nonVerbose:
        return passCheck
    else:
        printResult(component,command,foundResult,expectation,passCheck)
        return passCheck

def getNum(line):
    '''
    Get version number for given feature (Kernel, libvirt, qemu,ASIDs). Get versions in ...x.xx... format.
    '''
    #How many periods have we encountered
    periodCounter = 0
    #Will return version number
    checker = ''
    for x in line:
        #Add to version
        if x.isnumeric():
            checker += x
        #First period encounter
        elif x == '.' and periodCounter < 2:
            checker += x
            periodCounter += 1
        #2nd period encounter, return version number.
        elif not x.isnumeric() and periodCounter == 2:
            return checker
    #Return version number
    return checker

def findASIDCountSEV(nonVerbose):
    '''
    If kernel is updated for SEV-ES support (5.11), then find the available ASIDS for SEV.
    '''
    #Test components
    passCheck = False
    component = "Available SEV ASIDs"
    expectation = "xxx ASIDs"

    #Look at the kernel message for available ASIDs
    command = "dmesg | grep -w 'SEV supported'"
    SEVTest = subprocess.run("dmesg | grep -w 'SEV supported'", shell=True, stdout = subprocess.PIPE, stderr=subprocess.PIPE) 
    SEVString = SEVTest.stdout.decode('utf-8').strip()
    
    #Get formatted ASIDs from function
    SEVSupport,availableASIDS,asidNum = getSEVStringAndASIDS(SEVString)
    
    #If no ASIDS found, check kernel version
    if not availableASIDS:
        #Getting kernel
        kernel = subprocess.run(['uname', '-r'], stdout=subprocess.PIPE)
        kernelString = kernel.stdout.decode('utf-8').strip()
        kernelNum = getNum(kernelString)
        
        #Kernel version does not support ASID count, return a warning
        if version.parse(kernelNum) < version.parse('5.11'):
            foundResult = "EMPTY"
            passCheck = None
            expectation = "xxx ASIDs (Update kernel to 5.11 version to find available ASIDS or check in BIOS settings)"
        
        #No ASIDS found and kernel is updated, test fails
        else:
            foundResult = "EMPTY"
    
    #Kernel updated and ASIDs found,test passes
    elif int(asidNum) > 0:
        passCheck = True
        foundResult = availableASIDS
    
    #Kernel updated and ASIDs is equal to or less than (Hopefully never less than) 0, test fails
    elif int(asidNum) <= 0:
        foundResult = availableASIDS
    
    #Return test results
    if nonVerbose:
        return passCheck
    else:
        printResult(component,command,foundResult,expectation,passCheck)
        return passCheck

def findOSSupportSEVES(nonVerbose):
    '''
    Check if SEV-ES is enabled on the OS by checking the kernel message. If the feature can't be found in the dmesg, 
    then the function will return failure. Will also find the available ASIDS for SEV-ES. 
    '''
    #Test components
    passCheck = False
    component = "OS support for SEV-ES"
    expectation = "SEV-ES supported"
    foundResult = None
    
    #Look at the kernel message for SEV-ES SUPPORT enablement
    command = "dmesg | grep SEV-ES"
    SEVESTest = subprocess.run("dmesg | grep SEV-ES", shell=True, stdout = subprocess.PIPE)
    #SEV-ES found in dmesg, test passes
    if SEVESTest.stdout.decode('utf-8').strip():
        SEVESString =  SEVESTest.stdout.decode('utf-8').strip()
        #Call to get formatted SEV-ES support string
        SEVESSupport,availableASIDS,asidNum = getSEVStringAndASIDS(SEVESString)
        passCheck = True
        foundResult = SEVESSupport
    #SEV-ES not found in dmesg, test fails
    else:
        foundResult = "EMPTY"

    #Return test results
    if nonVerbose:
        return passCheck
    else:
        printResult(component,command,foundResult,expectation,passCheck)
        return passCheck

def findASIDCountSEVES(nonVerbose):
    '''
    If SEV-ES is enabled in kernel, find the available ASIDs
    '''
    #Test components
    passCheck = False
    component = "Available SEV-ES ASIDs"
    expectation = "xxx ASIDs"
    foundResult = None

    #Look at the kernel message for available ASIDs
    command = "dmesg | grep SEV-ES"
    SEVESTest = subprocess.run("dmesg | grep SEV-ES", shell=True, stdout = subprocess.PIPE, stderr=subprocess.PIPE) 
    SEVESString = SEVESTest.stdout.decode('utf-8').strip()
    #Get formatted ASIDs in dmesg string
    SEVESSupport,availableASIDS,asidNum = getSEVStringAndASIDS(SEVESString)
    
    #1 or more ASID available, test passes
    if int(asidNum) > 0:
        passCheck = True
        foundResult = availableASIDS
    #No ASIDs available, test fails
    elif int(asidNum) <= 0:
        foundResult = availableASIDS
    
    #Return test results
    if nonVerbose:
        return passCheck
    else:
        printResult(component,command,foundResult,expectation,passCheck)
        return passCheck
    
def getDistribution():
    '''
    Get the distribution and version of the linux system.
    '''
    #Find the VERSION_ID from os-release to get the version.
    rawVersion = subprocess.run("cat /etc/os-release | grep -w 'VERSION_ID=' | sed 's/.*VERSION_ID=//'", shell=True, stdout = subprocess.PIPE)
    #Find the ID from os-release to get the distro.
    rawLinuxOS = subprocess.run("cat /etc/os-release | grep -w 'ID=' | sed 's/.*ID=//'", shell=True, stdout = subprocess.PIPE)
    #Sometimes original command won't work, so we use a small workaround.
    if not rawLinuxOS.stdout:
        rawLinuxOS = subprocess.run("cat /etc/os-release | grep ID= | sed 's/.*ID=//'", shell=True, stdout = subprocess.PIPE)
        linuxOS = rawLinuxOS.stdout.decode('utf-8').split('\n')
        linuxOS = linuxOS[0]
    #Format distros
    else:
        linuxOS = rawLinuxOS.stdout.decode('utf-8').strip()
        linuxOS = linuxOS.replace("\"","")
    #Format versions
    version = rawVersion.stdout.decode('utf-8').strip()
    version = version.replace("\"","")
    #Retrun appropriate strings
    return linuxOS,version

def checkLinuxDistribution(nonVerbose):
    '''
    Get system distribution and version, then compare it to a known distribution list that support SEV. 
    If distribution not in list, then print warning.
    '''
    #Test Components
    passCheck = False
    component = "Current OS distribution"
    expectation = "(comparing against known minimum version list)"
    foundResult = None

    #List of known minimum distro versions that support SEV
    minDistributionVersions = {'ubuntu':'18.04', 'sles': '15', 'fedora': '28', 'rhel': '8', 'opensuse-tumbleweed': '0'}
    
    #Command to get system distribution and version
    command = "cat /etc/os-release"
    
    #Get system distribution and version
    distribution, OSVersion = getDistribution()
    
    #If distribution in list, then compare system version against minimum version
    if distribution in minDistributionVersions.keys():
        minVersion = minDistributionVersions[distribution]
        #Version meets minimum, test passes
        if version.parse(OSVersion) >= version.parse(minVersion):
            passCheck = True
            foundResult = distribution + ' ' + OSVersion 
        #Version does not meet minimum, test fails
        else:
            foundResult = distribution + ' ' + OSVersion
    #Distribution not in the known list, return a warning
    else:
        passCheck = None
        expectation = "os distribution not in known minimum list"
        foundResult = distribution + ' ' + OSVersion
    
    #Return test results
    if nonVerbose:
        return passCheck
    else:
        printResult(component,command,foundResult,expectation,passCheck)
        return passCheck
    
def checkKernelSEV(nonVerbose):
    '''
    Find current kernel version in system and then compare it against known minimums to see if system can run
    either SEV. *Modifications might have to be done for certain distros.
    '''
    #Test Components
    passCheck = False
    component = "Kernel"
    expectation = "4.16 minimum"
    foundResult = None

    #Get the kernel version
    command = "uname -r"
    kernel = subprocess.run(['uname', '-r'], stdout=subprocess.PIPE)
    kernelString = kernel.stdout.decode('utf-8').strip()
    
    #Call to get exact version number
    kernelNum = getNum(kernelString)

    #Meets minimum kernel version 4.16, test passes
    if version.parse(kernelNum) >= version.parse('4.16'):
        passCheck = True
        foundResult = kernelString
    #Does not meet minimum, test fails
    else:
        foundResult = kernelString
    
    #Return test results
    if nonVerbose:
        return passCheck
    else:
        printResult(component,command,foundResult,expectation,passCheck)
        return passCheck

def checkKernelSEVES(nonVerbose):
    '''
    Find current kernel version in system and then compare it against known minimums to see if system can run
    SEV-ES. *Modifications might have to be done for certain distros.
    '''
    #Test components
    passCheck = False
    component = "Kernel"
    expectation = "5.11 minimum"
    foundResult = None

    #Get the kernel version
    command = "uname -r"
    kernel = subprocess.run(['uname', '-r'], stdout=subprocess.PIPE)
    kernelString = kernel.stdout.decode('utf-8').strip()
    
    #Call to get exact version number
    kernelNum = getNum(kernelString)

    #Kernel meets the minimum version, test passes
    if version.parse(kernelNum) >= version.parse('5.11'):
        passCheck = True
        foundResult = kernelString
    #Does not meet minimum test fails
    else:
        foundResult = kernelString
    
    #Return test results
    if nonVerbose:
        return passCheck
    else:
        printResult(component,command,foundResult,expectation,passCheck)
        return passCheck

def findLibVirtSupport(nonVerbose):
    '''
    Find if libvirt is installed in the system, then get the version installed and compare it to the 
    known minimum needed to run either SEV or SEV-ES.
    '''
    #Test components
    passCheck = False
    component = "Libvirt version"
    expectation = "4.5 minimum"
    foundResult = None

    #Get the libvirt version, will return error if not installed
    command = "virsh -V"
    libvirt = subprocess.run("virsh -V | sed 's/.*libvirt //'", shell=True, stdout = subprocess.PIPE, stderr=subprocess.PIPE)
    libvirtErr = libvirt.stderr.decode("utf-8").strip()
    libVirtVersion = libvirt.stdout.decode("utf-8").split('\n')[0]
    
    #Call to get the formatted version number
    libVirtNum = getNum(libVirtVersion)
    
    #If error, test fails, get error message for print
    if libvirtErr and not libVirtVersion:
        foundResult = libvirtErr
    #If found, compare version against 4.5 minimum version
    elif libVirtVersion and not libvirtErr:
        #Version meets minimum, test passes
        if version.parse(libVirtNum) >= version.parse('4.5'):
            passCheck = True
            foundResult = libVirtVersion
        #Version doen't meet the minimum, test fails
        else:
            foundResult - libVirtVersion
    #Nothing is found, test fails
    else:
        foundResult = "EMPTY"

    #Return test results
    if nonVerbose:
        return passCheck
    else:
        printResult(component,command,foundResult,expectation,passCheck)
        return passCheck

def findLibVirtSEVSupport(nonVerbose):
    '''
    Find if SEV is enabled using LibVirt domcapabilities. A good way to confirm that SEV is enabled on the host OS.
    This test will only run if LibVirt is found to be installed and it is also compatible with SEV. 
    '''
    #Test components
    passCheck = False
    component = "LibVirt SEV enablement"
    expectation = "<sev supported='yes'>"
    foundResult = None

    #Get the libvirt domcapabilities
    command = "virsh domcapabilities | grep sev"
    read = subprocess.run("virsh domcapabilities | grep sev", shell=True, stdout = subprocess.PIPE, stderr=subprocess.PIPE)
    readout = read.stdout.decode("utf-8").split('\n')
    
    #Look in returned strings for SEV support
    for line in readout:
        #SEV support found, test passes
        if line.strip() == "<sev supported='yes'>":
            foundResult = "<sev supported='yes'>"
            passCheck = True
            break
        #SEV not supported found, test fails
        elif line.strip() == "<sev supported='no'/>":
            foundResult = "<sev supported='no'/>"
            break
    
    #SEV status is not found, test fails
    if foundResult == None:
        foundResult = "EMPTY"

    #Return test results
    if nonVerbose:
        return passCheck
    else:
        printResult(component,command,foundResult,expectation,passCheck)
        return passCheck


def findQemuSupportSEV(systemOS,nonVerbose):
    '''
    Find if QEMU is installed in the system, then get the version installed and compare it to the 
    known minimum needed to run SEV.
    '''
    #Test Components
    passCheck = False
    component = "QEMU version"
    expectation = "2.12 minimum"
    foundResult = None

    #List of knonw working commands to get the QEMU version in the system depending on the distro
    qemuCommandList = {'ubuntu':'qemu-system-x86_64 --version', 'debian': 'qemu-system-x86_64 --version', 'fedora': '/usr/libexec/qemu-kvm --version', 'rhel': '/usr/libexec/qemu-kvm --version', 
    'opensuse-tumbleweed': 'qemu-system-x86_64 --version', 'opensuse-leap' : 'qemu-system-x86_64 --version', 'centos':'/usr/libexec/qemu-kvm --version', 'oracle':'/usr/libexec/qemu-kvm --version'}

    #If not in the list use kvm --version as a default
    if systemOS not in qemuCommandList:
        qemmuCommand = "kvm --version"
    else:
        qemmuCommand = qemuCommandList[systemOS]
    
    #Get qemu version
    qemu = subprocess.run(qemmuCommand + " | sed 's/.*version //'", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    qemuErr = qemu.stderr.decode("utf-8").strip()
    qemuVersion = qemu.stdout.decode("utf-8").split('\n')[0]
    
    #Get formatted version number
    qemuNum = getNum(qemuVersion)

    #Command returns an error, grab error for print, test fails
    if qemuErr and not qemuVersion:
        foundResult = qemuErr
    #Command returns version
    elif qemuVersion and not qemuErr:
        #Version meets 2.12 minimum, test passes
        if version.parse(qemuNum) >= version.parse('2.12'):
            passCheck = True
            foundResult = qemuNum
        #Version does not meet minimum, test fails
        else:
            foundResult = qemuNum
    #Nothing is returned
    else:
        foundResult = "EMPTY"

    #Return test results
    if nonVerbose:
        return passCheck
    else:
        printResult(component,qemmuCommand,foundResult,expectation,passCheck)
        return passCheck
    

def findQemuSupportSEVES(systemOS,nonVerbose):
    '''
    Find if QEMU is installed in the system, then get the version installed and compare it to the 
    known minimum needed to run SEV-ES.
    '''
    #Test components
    passCheck = False
    component = "QEMU version"
    expectation = "6.0 minimum"
    foundResult = None

    #List of knonw working commands to get the QEMU version in the system depending on the distro
    qemuCommandList = {'ubuntu':'qemu-system-x86_64 --version', 'debian': 'qemu-system-x86_64 --version', 'fedora': '/usr/libexec/qemu-kvm --version', 'rhel': '/usr/libexec/qemu-kvm --version', 
    'opensuse-tumbleweed': 'qemu-system-x86_64 --version', 'opensuse-leap' : 'qemu-system-x86_64 --version', 'centos':'/usr/libexec/qemu-kvm --version', 'oracle':'/usr/libexec/qemu-kvm --version'}

    #If not in the list use kvm --version as a default
    if systemOS not in qemuCommandList:
        qemmuCommand = "kvm --version"
    else:
        qemmuCommand = qemuCommandList[systemOS]
    
    #Get qemu version
    qemu = subprocess.run(qemmuCommand + " | sed 's/.*version //'", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    qemuErr = qemu.stderr.decode("utf-8").strip()
    qemuVersion = qemu.stdout.decode("utf-8").split('\n')[0]
    
    #Get formatted version number
    qemuNum = getNum(qemuVersion)

    #Command returns an error, grab error for print, test fails
    if qemuErr and not qemuVersion:
        foundResult = qemuErr
    #Command returns version
    elif qemuVersion and not qemuErr:
        #Version meets 6.0 minimum, test passes
        if version.parse(qemuNum) >= version.parse('6.0'):
            passCheck = True
            foundResult = qemuNum
        #Version does not meet minimum, test fails
        else:
            foundResult = qemuNum
    #Nothing is returned, test fails
    else:
        foundResult = "EMPTY"

    #Return test results
    if nonVerbose:
        return passCheck
    else:
        printResult(component,qemmuCommand,foundResult,expectation,passCheck)
        return passCheck

def getOVMFPaths(nonVerbose,defaultPath,pkgInstalled,pckgInstallDate,minCommit):
    '''
    Function to get and print all of the found OVMF paths, whether default or manually built. 
    If at least one meets the minimum, test passes. 
    '''
    #At least one path meets the minimum
    onePathTrue = False
    #Get all of the manually built paths
    builtPaths = OVMFFunctions.getBuiltPaths()
    
    #Print explanation
    if (builtPaths or pkgInstalled) and not nonVerbose:
        print("All of the found OVMF paths:")
    
    #Path to default package in most distros
    if pkgInstalled and os.path.exists(defaultPath):
        #Default package meets the minimum
        if OVMFFunctions.compareOVMFVersion(pckgInstallDate, minCommit):
            if not nonVerbose:
                print("- OVMF Path Found: " + defaultPath + " Commit date Found: " + pckgInstallDate.strftime("%Y-%m-%d ") + ' Expected: commit ' + minCommit + ' ' + colors.green + "OK" + colors.reset)
            pathTrue = True
        #Default package does not meet the minimum
        else:
            if not nonVerbose:
                print("- OVMF Path Found: " + defaultPath + " Commit date Found: " + pckgInstallDate.strftime("%Y-%m-%d ") + ' Expected: commit ' + minCommit + ' ' + colors.red + "FAIL" + colors.reset)

    if builtPaths:
        for path in builtPaths:    
            #Call to get commit date from given path
            ovmfCommitDate = OVMFFunctions.getCommitDate(path)
            #Call to compare path commit date with given minimum date for either SEV or SEV-ES
            #Current path meets minimum
            if OVMFFunctions.compareOVMFVersion(ovmfCommitDate, minCommit):
                onePathTrue = True
                if not nonVerbose:
                    print("- OVMF Path Found: " + path + " Commit date Found: " + ovmfCommitDate.strftime("%Y-%m-%d ") + ' Expected: commit ' + minCommit + ' ' + colors.green + "OK" + colors.reset)
            #Current path does not meet minimum
            else:
                if not nonVerbose:
                    print("- OVMF Path Found: " + path + " Commit date Found: " + ovmfCommitDate.strftime("%Y-%m-%d ") + ' Expected: commit ' + minCommit + ' ' + colors.red + "FAIL" + colors.reset)
    
    return onePathTrue
    
def OVMFInstall(feature,version,nonVerbose):
    '''
    Finds if OVMF is installed in the system. It checks if default distro package is installed, and also attempts to find all of the 
    manual/outside builds that are in the system (through edk2). It then finds their version (git commit date) and compares
    it against known minimum to see if it supports SEV or SEV-ES.
    '''
    #Feature being tested for
    if feature == 'sev':
        minCommit = '2018-07-06'
    elif feature == 'sev-es':
        minCommit = '2020-11-01'
    
    #Test components
    passCheck = False
    component = "OVMF package installation"
    expectation = "commit " + minCommit
    foundResult = None

    #Is the default package installed
    pkgInstall = False
    #Does the default package meet the minimum commit date
    pkgTrue = False
    #Does at least one manually built OVMF version meet the minimum commit date
    pathTrue = False
    
    #Distro command to find default package, default distro path, formatted default distro version (if found), version date
    defaultCommand, defaultPath, defaultOVMFVersion, pckgInstallDate = OVMFFunctions.getDefaultOVMFPath(version)

    #Default package not found or not installed, default test fails
    if defaultPath == None:
        foundResult = "EMPTY"
    else:
        #Default package is installed
        pkgInstall = True
        #Default package meets minimum, default test passes
        if OVMFFunctions.compareOVMFVersion(pckgInstallDate,minCommit):
            pkgTrue = True
            foundResult = defaultOVMFVersion
        #Default package does not meet minimum, default test fails
        else:
            foundResult = defaultOVMFVersion
    
    #Print default package installation result
    if not nonVerbose:
        printResult(component,defaultCommand,foundResult,expectation,pkgTrue)
    
    #Function which finds all paths, manual and default 
    pathTrue = getOVMFPaths(nonVerbose,defaultPath,pkgInstall,pckgInstallDate,minCommit)
    
    #If either the default package or any externally build path meet the feature minimum, overall test passes
    if pkgTrue or pathTrue:
        passCheck = True

    #Return test result
    return passCheck

def checkSystemSupportTest(SMEEnabled,stopFailure,nonVerbose):
    '''
    Run the existing system support checks that query the system capabilites and informs if the 
    system can or cannot run SEV features. 
    '''
    #Will turn false if any check fails
    passCheck = True
    
    #Not print if nonVerbose raised (Will see this alot)
    if not nonVerbose:
        print("\nQuerying for system capabilities:")

    #Check the CPUID function 0x8000001f for SME availability, will only run test if SME enabled with --test flag.
    if SMEEnabled:
        if not findCPUIDSupportSME(nonVerbose):
            #Stop running checks immediately if the test fails and the stopfailure flag is enabled.
            if stopFailure:
                return False
            else:
                passCheck = False
    
    #Check for the CPUID function 0x8000001f for SEV availability
    if not findCPUIDSupportSEV(nonVerbose):
        if stopFailure:
            return False
        else:
            passCheck = False
    
    #Check if AMD virtualization is available
    if not checkVirtualization(nonVerbose):
        if stopFailure:
            return False
        else:
            passCheck = False
    
    return passCheck

def runSMETest(stopFailure, nonVerbose):
    '''
    Run the existing OS checks that query the system capabilites and informs if the current system setup can run SME.
    '''
    passCheck = True
    
    if not nonVerbose:
        print("\nComparing Host OS componenets to known SME minimum versions:")

    #Looks at the kernel message to see if SME is enabled.
    if not findOSSupportSME(nonVerbose):
        if stopFailure:
            return False
        else:
            passCheck = False

    return passCheck

def runSEVTest(version,stopFailure,nonVerbose):
    '''
    Run the existing OS checks that query the system capabilites and informs if the current system setup can run SEV.
    '''
    passCheck = True
    
    if not nonVerbose:
        print("\nComparing Host OS componenets to known SEV minimum versions:")
    
    #Compares system's distro and version to known minimums and see if they are compabible with SEV
    if checkLinuxDistribution(nonVerbose) == False:
        if stopFailure:
            return False
        else:
            passCheck = False

    #Find kernel version and see if it is compatible with SEV
    if not checkKernelSEV(nonVerbose):
        if stopFailure:
            return False
        else:
            passCheck = False
    
    #Looks at the kernel message to see if SEV is enabled.
    if not findOSSupportSEV(nonVerbose):
        if stopFailure:
            return False
        else:
            passCheck = False
    else:
        #If kernel message found, check for available ASIDs
        if findASIDCountSEV(nonVerbose) == False:
            if stopFailure:
                return False
            else:
                passCheck = False
    
    #Finds if libvirt is installed and find if version is compatible with SEV
    if not findLibVirtSupport(nonVerbose):
        if stopFailure:
            return False
        else:
            passCheck = False
    else:
        #If Libvirt is installed, chechk for SEV Support in the OS.
        if not findLibVirtSEVSupport(nonVerbose):
            if stopFailure:
                return False
            else:
                passCheck = False

    #Find if QEMU is installed and find if version is compatible with SEV
    if not findQemuSupportSEV(version,nonVerbose):
        if stopFailure:
            return False
        else:
            passCheck = False
    
    #Find if default distro OVMF package is installed and check SEV compability
    #Then check for manually built OVMF versions and check if those are compatible with SEV
    #Test will pass if at least one of the FOUND OVMF versions are compatible with SEV
    if not OVMFInstall('sev',version,nonVerbose):
        if stopFailure:
            return False
        else:
            passCheck = False
    
    return passCheck

def runSEVESTest(version, stopFailure, nonVerbose):
    '''
    Run the existing OS checks that query the system capabilites and informs if the current system setup can run SEV-ES
    '''
    passCheck = True

    if not nonVerbose:
        print("\nComparing Host OS componenets to known SEV-ES minimum versions:")

    #Find kernel version and see if it is compatible with SEV-ES
    if checkKernelSEVES(nonVerbose):
        if stopFailure:
            return False
        else:
            passCheck = False
    
    #Looks at the kernel message to see if SEV-ES is enabled.
    if not findOSSupportSEVES(nonVerbose):
        if stopFailure:
            return False
        else:
            passCheck = False
    else:
        #If kernel message found, check for available ASIDs
        if not findASIDCountSEVES(nonVerbose):
            if stopFailure:
                return False
            else:
                passCheck = False
    
    #Finds if libvirt is installed and find if version is compatible with SEV-ES
    if not findLibVirtSupport(nonVerbose):
        if stopFailure:
            return False
        else:
            passCheck = False
    else:
        #If Libvirt is installed, chechk for SEV Support in the OS.
        if not findLibVirtSEVSupport(nonVerbose):
            if stopFailure:
                return False
            else:
                passCheck = False

    #Find if QEMU is installed and find if version is compatible with SEV-ES
    if not findQemuSupportSEVES(version,nonVerbose):
        if stopFailure:
            return False
        else:
            passCheck = False
    
    #Find if default distro OVMF package is installed and check SEV-ES compability
    #Then check for manually built OVMF versions and check if those are compatible with SEV-ES
    #Test will pass if at least one of the FOUND OVMF versions are compatible with SEV-ES
    if not OVMFInstall('sev-es',version,nonVerbose):
        if stopFailure:
            return False
        else:
            passCheck = False
      
    return passCheck

def printTestResult(test, result):
    '''
    Print the current system test result in this format. The current system test and its result.
    '''
    if result:
        print(test + colors.green + " PASS" + colors.reset)
    else:
        print(test + colors.red + " FAIL" + colors.reset)

def runTests(systemOS, stopFailure, testedFeatures, nonVerbose):
    '''
    Function to run all of the current tests, will return the result of each individual system test, and if all tests passed or not.
    '''
    #If all the tested features passed
    TESTPASS = False
    #System support test result
    SYSTEMSUPPORTPASS = False
    #SME test result
    SMEPASS = False
    #SEV test result
    SEVPASS = False
    #SEV-ES test result
    SEVESPASS = False
    #Testing for sme enabled
    SMEEnabled = False
    #Testing for sev-es enabled:
    SEVESEnabled = False

    #Check and see if SME test is enabled by the --test parameter. Ignore test results if not enabled (DEFAULT OFF)
    if set(['sme']).intersection(set(testedFeatures)):
        SMEEnabled = True
    else:
        SMEPASS = True
    
    #Check and see if SEV-ES test is enabled by the --test parameter. Ignore test results if not enabled (DEFAULT ON)
    #Test will run if SNP is requested (NOT AVAILABLE YET)
    if set(['sev-es']).intersection(set(testedFeatures)) or set(['sev-snp']).intersection(set(testedFeatures)):
        SEVESEnabled = True
    else:
        SEVESPASS = True
    
    #System Support check test
    currentTest = "SYSTEM SUPPORT"
    #System Support test passes
    if checkSystemSupportTest(SMEEnabled,stopFailure,nonVerbose):
        SYSTEMSUPPORTPASS = True
    #System support test fails
    else:
        #stop all tests immidiately if stopfailure is up
        if stopFailure:
            #Print resulsts if nonVerbose is not raised
            if not nonVerbose:
                printTestResult(currentTest,SYSTEMSUPPORTPASS)
            return TESTPASS,SYSTEMSUPPORTPASS,SMEPASS,SEVPASS,SEVESPASS
    
    #Print result of system support test.
    if not nonVerbose:
        printTestResult(currentTest,SYSTEMSUPPORTPASS)
    
    #SME check test
    if SMEEnabled:
        currentTest = "SME COMPONENT SUPPORT"
        #SME test passes
        if runSMETest(stopFailure,nonVerbose):
            SMEPASS = True
        #SME test fails
        else:
            if stopFailure:
                if not nonVerbose:
                    printTestResult(currentTest,SMEPASS)
                return TESTPASS,SYSTEMSUPPORTPASS,SMEPASS,SEVPASS,SEVESPASS
        
        #Print result of SME test.
        if not nonVerbose:
            printTestResult(currentTest,SMEPASS)
    
    #SEV check test
    currentTest = "SEV COMPONENT SUPPORT"
    #SEV test passes
    if runSEVTest(systemOS,stopFailure,nonVerbose):
        SEVPASS = True
    #SEV test fails
    else:
        if stopFailure:
            if not nonVerbose:
                printTestResult(currentTest,SEVPASS)
            return TESTPASS,SYSTEMSUPPORTPASS,SMEPASS,SEVPASS,SEVESPASS
    
    #print SEV test result
    if not nonVerbose:
        printTestResult(currentTest,SEVPASS)
    
    #SEV-ES check test
    if SEVESEnabled:
        currentTest = "SEV-ES COMPONENT SUPPORT"
        #SEV-ES test passes
        if runSEVESTest(systemOS, stopFailure, nonVerbose):
            SEVESPASS = True
        #SEV-ES test fails
        else:
            if stopFailure:
                if not nonVerbose:
                    printTestResult(currentTest,SEVESPASS)
                return TESTPASS,SYSTEMSUPPORTPASS,SMEPASS,SEVPASS,SEVESPASS
        
        #print SEV-ES test result
        if not nonVerbose:
            printTestResult(currentTest,SEVESPASS)

    #If all the enabled tests pass, return an overall success
    if SYSTEMSUPPORTPASS and SMEPASS and SEVPASS and SEVESPASS:
        TESTPASS = True
    
    #return results
    return TESTPASS,SYSTEMSUPPORTPASS,SMEPASS,SEVPASS,SEVESPASS
    


if __name__ == '__main__':
    '''
    Run the system check tests, then run any extra tests raised by the flags.
    Will run system check for SEV and SEV-ES by default. Any changes to desired system tests have to be done with the --test flag
    Use --stopfailure flag to stop system check at first failure. 
    Use --testlocal flag to test encryption of VMs being run already. Can provide VM command to specify one desired VM, or not provide anything to launch UI.
    Use --printlocal flag to print the memory of VMs being run. Can provide VM command to specify one desired VM, or not provide anything to launch UI.
    Use --autotest flag to launch automatic VM encryption test on the tiny VM provided.
    Use --nonVerbose flag to run program without any prints
    Will return 1 if any of the desired tests fails, will return 0 if all the desired tests pass.
    '''
    #Print explanation
    if not args.nonverbose:
        print("\nRunning SEV Component Test tool. For more running options, run 'python3 SEVComponentTest.py -h'.")
        print("For more information please go to https://developer.amd.com/sev/")
    
    #Getting system OS now to avoid redundancy
    systemOS, systemVersion = getDistribution()

    #Overall program result
    allRequestedTestsPass = True
    
    #System check test resuslts
    TESTPASS,SYSTEMSUPPORTPASS,SMEPASS,SEVPASS,SEVESPASS = runTests(systemOS,args.stopfailure,args.test,args.nonverbose)
    
    #If one of the desired system check fails, then overall test will return failure
    if not TESTPASS:
        allRequestedTestsPass = False

    #Test local feature has been raised
    if args.testlocal != 'not raised':
        if not args.nonverbose:
            print("\nRunning local virtual machine encryption test:")
        #If one of the provided VMs fails the encryption test, overall test fails.
        if not localVMTest.runLocalVMTest(systemOS,args.testlocal,args.nonverbose):
            allRequestedTestsPass = False
    
    #Print local feature has been raised
    if args.printlocal != 'not raised':
        if not args.nonverbose:
            print("\nRunning local virtual machine memory printer:")
        #Print one page of memory for the provided VMs
        localVMTest.runPrintMemory(systemOS,args.printlocal,args.nonverbose)

    #auto test feature has been raised
    if args.autotest:
        #Auto test will not run if the SEV test does not pass
        if not SEVPASS:
            if not args.nonverbose:
                print("SEV Component Test failed. SEV Machine cannot be launched.")
        else:
            if not args.nonverbose:
                print("\nRunning automatic test for VM encryption:")
            #If the automatic VM Encryption test fails, overall test fails.
            if not autoVMTest.automaticVMTest(systemOS,args.nonverbose):
                allRequestedTestsPass = False
    
    #Return program results
    if allRequestedTestsPass:
        sys.exit(0)
    else:
        sys.exit(1)



