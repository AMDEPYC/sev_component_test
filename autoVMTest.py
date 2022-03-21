import os
import subprocess
from time import sleep
import localVMTest
import OVMFFunctions
import encryptionTest

def launchVM(version,currDirectory):
    '''
    Launch the automatic VM using QEMU.
    '''
    #Known qemu commands that can be used to launch VMs
    qemuCommandList = {'ubuntu':'qemu-system-x86_64', 'debian': 'qemu-system-x86_64', 'fedora': '/usr/libexec/qemu-kvm', 'rhel': '/usr/libexec/qemu-kvm', 
    'opensuse-tumbleweed': 'qemu-system-x86_64', 'opensuse-leap' : 'qemu-system-x86_64', 'centos':'/usr/libexec/qemu-kvm', 'oracle':'/usr/libexec/qemu-kvm'}
    
    #If not in known list, use qemu-kvm
    if version not in qemuCommandList:
        qemuCommand = "qemu-kvm"
    else:
        qemuCommand = qemuCommandList[version]
    
    #One QEMU command that can be used if the current system uses the .fd version of OVMF
    if os.path.exists(os.path.abspath(currDirectory + '/autoVM/OVMF_READ.fd')):
        command = qemuCommand + " --enable-kvm \
        -cpu EPYC \
        -machine q35 \
        -no-reboot \
        -daemonize \
        -vga std -vnc :0 \
        -drive if=pflash,format=raw,unit=0,file=" + os.path.abspath(currDirectory + '/autoVM/OVMF_READ.fd') + ",readonly=on \
        -drive if=pflash,format=raw,unit=1,file=" + os.path.abspath(currDirectory + '/autoVM/OVMF_WRITE.fd') + " \
        -drive file=" + os.path.abspath(currDirectory + '/autoVM/SEVminimal.qcow2') + ",if=none,id=disk0,format=qcow2 \
        -device virtio-scsi-pci,id=scsi0,disable-legacy=on,iommu_platform=on \
        -device scsi-hd,drive=disk0 \
        -machine memory-encryption=sev0,vmport=off \
        -object sev-guest,id=sev0,policy=0x3,cbitpos=47,reduced-phys-bits=1"
   
    #QEMU command that can be used if the current system uses the .bin version of OVMF
    else:
        command = qemuCommand + " --enable-kvm \
        -cpu EPYC \
        -machine q35 \
        -no-reboot \
        -daemonize \
        -vga std -vnc :0 \
        -drive if=pflash,format=raw,unit=0,file=" + os.path.abspath(currDirectory + '/autoVM/OVMF_READ.bin') + ",readonly=on \
        -drive if=pflash,format=raw,unit=1,file=" + os.path.abspath(currDirectory + '/autoVM/OVMF_WRITE.bin') + " \
        -drive file=" + os.path.abspath(currDirectory + '/autoVM/SEVminimal.qcow2') + ",if=none,id=disk0,format=qcow2 \
        -device virtio-scsi-pci,id=scsi0,disable-legacy=on,iommu_platform=on \
        -device scsi-hd,drive=disk0 \
        -machine memory-encryption=sev0,vmport=off \
        -object sev-guest,id=sev0,policy=0x3,cbitpos=47,reduced-phys-bits=1"
    
    subprocess.run(command, shell=True, stdout = subprocess.PIPE, stderr=subprocess.PIPE)
    
    return command

def killMachine(PID):
    '''
    Kill the process using PID
    '''
    os.system("kill -9 " + str(PID))

def setUpMachine(version,currDirectory,nonVerbose):
    '''
    Set up vm folder to be able to launch auto VM
    '''
    #Get the path to the first compatible SEV OVMF build
    OVMFPath = OVMFFunctions.getPathToOVMF(version)
    #Check if OVMF_VARS.fd path exists
    if os.path.exists(OVMFPath + '/OVMF_VARS.fd'):
        #Copy file to autoVM folder
        os.system('cp ' + OVMFPath + '/OVMF_VARS.fd ' + os.path.abspath(currDirectory + '/autoVM') + '/OVMF_WRITE.fd')
        #Check if OVMF_CODE.fd exists, some distros have this and others have OVMF_CODE.secboot.fd only as their default.
        if os.path.exists(OVMFPath + '/OVMF_CODE.fd'):
            os.system('cp ' + OVMFPath + '/OVMF_CODE.fd ' + os.path.abspath(currDirectory + '/autoVM') + '/OVMF_READ.fd')
        #Check if OVMF_CODE.secboot.fd exists
        elif os.path.exists(OVMFPath + '/OVMF_CODE.secboot.fd'):
            os.system('cp ' + OVMFPath + '/OVMF_CODE.secboot.fd ' + os.path.abspath(currDirectory + '/autoVM') + '/OVMF_READ.fd')
    #Check if OVMF_VARS.bin path exists
    elif os.path.exists(OVMFPath + '/ovmf-x86_64-vars.bin'):
        os.system('cp ' + OVMFPath + '/ovmf-x86_64-vars.bin ' + os.path.abspath(currDirectory + '/autoVM') + '/OVMF_WRITE.bin')
        os.system('cp ' + OVMFPath + '/ovmf-x86_64-code.bin ' + os.path.abspath(currDirectory + '/autoVM') + '/OVMF_READ.bin')
    
    #If no working OVMF file found, return error, VM can't be launched.
    else:
        if not nonVerbose:
            print("Machine cannot be set up. No working OVMF was found. Please look at README for more information.")
        return False
    #Folder setup succesfully
    return True
    

def cleanUpMachine(currDirectory):
    '''
    Remove created files once VM test is completed.
    '''
    #Remove .fd version of OVMF
    if os.path.exists(os.path.abspath(currDirectory + '/autoVM/OVMF_WRITE.fd')):
        os.system('rm ' + os.path.abspath(currDirectory + '/autoVM/OVMF_WRITE.fd'))
        os.system('rm ' + os.path.abspath(currDirectory + '/autoVM/OVMF_READ.fd'))
    #Remove .bin version of OVMF
    else:
        os.system('rm ' + os.path.abspath(currDirectory + '/autoVM/OVMF_WRITE.bin'))
        os.system('rm ' + os.path.abspath(currDirectory + '/autoVM/OVMF_READ.bin'))

        # TODO
        #Use os removes instead of system rm, probably other utilities where I use system instead of a more efficient utility.


def automaticVMTest(version,nonVerbose):
    '''
    Run the automatic VM test. 
    '''
    #Will tell if overall test passed
    testPass = False
    #Setup directory since files will be moved around
    currDirectory = os.path.dirname(os.path.realpath(__file__))
    
    #Print explanation
    if not nonVerbose:
        print("Preparing machine for launch...")
    
    #Setup machine, if set up fails, return failure
    if not setUpMachine(version,currDirectory,nonVerbose):
        if not nonVerbose:
            print("Machine could not be setup for launch.")
        return False
    
    if not nonVerbose:
        print("Launching Virtual Machine for testing:")
    
    #Launch the VM using QEMU
    VM = launchVM(version,currDirectory)
    
    #Wait for machine to finish booting (for best results)
    sleep(15)

    #Get current VMs being run in the system
    availableVMs = localVMTest.getVirtualMachines(version)
    
    #Find our VM on the curent VM list, get its PID
    PID = localVMTest.findVirtualmachine(VM,availableVMs)
    
    #If the PID is found, the machine was succesfully launched, continue with the test
    if PID:
        if not nonVerbose:
            print("Machine Launched!")
            print("Corresponding PID: " + str(PID))
            print("Looking for machine memory....")
        #Get the machine's memory contents
        VMMemory = localVMTest.setupMemoryforTesting(VM,PID)
        #Test for encryption using entropy algorithm
        entropyValue = encryptionTest.entropyEncryptionTest(VMMemory)
        #Entropy value is equal to or above a 7, the machine is probably encrypted, test passes
        if entropyValue >= 7:
            if not nonVerbose:
                print("Entropy value " + str(entropyValue))
                print("Virtual Machine is probably encrypted.")
            testPass = True
        #Entropy value is less than a 7, the machine is probably unencrypted, test fails
        else:
            if not nonVerbose:
                print("Entropy value " + str(entropyValue))
                print("Virtual Machine is probably not encrypted.")
            testPass = False
        #Kill the machine after test ends
        killMachine(PID)
    #PID not found, machine was probably not launched, test fails
    else:
        if not nonVerbose:
            print("Machine not Found. Machine probably did not launch correctly.")
        return False
    
    if not nonVerbose:
        print("Cleaning up machine...")
    
    #Remove created files for test
    cleanUpMachine(currDirectory)
    
    #Return results
    return testPass