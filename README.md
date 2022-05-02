
# Table of Contents

- [Introduction](#SEV-component-test)
- [Setting up host OS](#Setting-up-host-os)
    - [Ubuntu](#Ubuntu)
    - [RHEL](#RHEL)
    - [OpenSUSE-Tumbleweed](#OpenSUSE-Tumbleweed)
- [Usage](#Usage)
    - [Stop at failure](#Stop-at-failure)
    - [Feature testing](#Feature-testing)
    - [nonVerbose](#nonverbose)
- [Virtual machine tests](#Virtual-machine-tests)
    - [Test local](#Test-local)
    - [Print local](#Print-local)
    - [Auto VM Test](#automatic-virtual-machine-test)
- [Testing](#Testing)

# SEV component test
This script is used to query a host system's capabilities to run SEV or SEV-ES encrypted virtual machines. It also checks for SME compatibility. It will run checks of several different components, and it will allow us to know if the host system is set-up correctly in order to support SEV features. If there are any more questions regarding SME, SEV or SEV-ES please visit [AMD'S SEV developer website](https://developer.amd.com/sev/).

# Setting up host OS
All OS distributions need to install 2 packages in order to run this tool. Installation for each package differs depending on the distro.
Packages needed:
- CPUID
- python3 module packaging

In order to install all the required python packages, there is a requirements.txt file provided. To install the desired packages simply run:
```
$ pip/pip3 -r install requirements.txt
```
on the root directory of the project.
## Ubuntu
To install CPUID run command:
```
$ sudo apt install cpuid
```
## RHEL 8
RHEL stopped supporting CPUID in their package manager, but it can still be installed.
First install PERL using:
```
$ yum install perl
```
Then to install CPUID run command to install from original source:
```
$ rpm -i http://www.etallen.com/cpuid/cpuid-20220224-1.x86_64.rpm
```
## OpenSUSE-Tumbleweed
To install CPUID run command:
```
$ zypper install cpuid
```
# Usage
Once the host is set-up, in order to run the tool simply use:
```
$ python ./sev_component_test/sev_component_test.py
```
This will initialize the check on the system and the results of the component test will appear on the terminal screen.

** PYTHON 3.6 OR NEWER IS REQUIRED TO RUN THE PROGRAM**

There are flags that can be raised in order to use different features that the tool offers. These can be raised individually or a combination of them at the same time.

Test example on Ubuntu:
```
Running SEV Component Test tool. For more running options, run 'python3 SEVComponentTest.py -h'.
For more information please go to https://developer.amd.com/sev/

Querying for system capabilities:
- CPUID function 0x8000001f bit 1 for SEV [ cpuid -r -1 -l 0x8000001f ] Found: EAX bit 1 is 1 Expected: EAX bit 1 to be '1' OK
- Virtualization capabilities [ lscpu | grep Virtualization ] Found: Virtualization: AMD-V Expected: Virtualization: AMD-V OK
SYSTEM SUPPORT PASS

Comparing Host OS componenets to known SEV minimum versions:
- Current OS distribution [ cat /etc/os-release ] Found: ubuntu 20.04 Expected: (comparing against known minimum version list) OK
- Kernel [ uname -r ] Found: 5.13.0-28-generic Expected: 4.16 minimum OK
- OS support for SEV [ dmesg | grep -w 'SEV supported' ] Found: SEV supported Expected: SEV supported OK
- Available SEV ASIDS [ dmesg | grep -w 'SEV supported' ] Found: 493 ASIDs Expected: xxx ASIDs OK
- Libvirt version [ virsh -V ] Found: 6.0.0 Expected: 4.5 minimum OK
- LibVirt SEV enablement [ virsh domcapabilities | grep sev ] Found: <sev supported='yes'> Expected: <sev supported='yes'> OK
- QEMU version [ qemu-system-x86_64 --version ] Found: 4.2.1 (Debian 1:4.2-3ubuntu6.21) Expected: 2.12 minimum OK
- OMVF path install [ dpkg --list ] Found: /usr/share/OVMF/OVMF_VARS.fd 2019-11-22  Expected: 2018-07-06  OK
SEV COMPONENT TEST PASS

Comparing Host OS componenets to known SEV-ES minimum versions:
- Kernel [ uname -r ] Found: 5.13.0-28-generic Expected: 5.11 minimum OK
- OS support for SEV-ES [ dmesg | grep SEV-ES ] Found: SEV-ES supported Expected: SEV-ES supported OK
- Available SEV-ES ASIDS [ dmesg | grep SEV-ES ] Found: 16 ASIDs Expected: xxx ASIDs OK
- Libvirt version [ virsh -V ] Found: 6.0.0 Expected: 4.5 minimum OK
- QEMU version [ qemu-system-x86_64 --version ] Found: 4.2.1 (Debian 1:4.2-3ubuntu6.21) Expected: 6.0 minimum FAIL
- OMVF path install [ dpkg --list ] Found: /usr/share/OVMF/OVMF_VARS.fd 2019-11-22  Expected: 2020-11-01  FAIL
SEV-ES COMPONENT TEST FAIL
```

## Stop at failure
This flag causes the component test to stop running at the very first failure it reaches. This facilitates the visualization of individual failures, and allows the user to approach the checks individually if several of them are failing. 
To use this flag, use the command:
```
$ python ./sev_component_test/sev_component_test.py --stopfailure
```
or
```
$ python ./sev_component_test/sev_component_test.py -s
```

## NonVerbose
This flag will run all the desired tests, but no text will be printed. It is intented for people that are using the tool as part of a script.
```
$ python ./sev_component_test/sev_component_test.py --nonverbose
```
or
```
$ python ./sev_component_test/sev_component_test.py -nv
```

## Feature testing
This flag allows the user to pick what features to test for. By raising it the user can specify if they want to test for only one specific feature (SEV, SEV-ES or SME), all of them, or any combination of the 3. That way if the user is curious about only one feature, they can just test for that one, instead of having to test for all of them. **Note**: If testing for SEV-ES, SEV test will always run, since being able to run SEV is a prerequisite for SEV-ES. By default the program will only test for SEV and SEV-ES.
To use this flag, use the command:
```
$ python ./sev_component_test/sev_component_test.py --test [features to be tested]
```
or
```
$ python ./sev_component_test/sev_component_test.py -t [features to be tested]
```
Features (sev, sev-es or sme) written in lower-case and separated by a space.

Example feature testing for SME and SEV only:
```
$ python ./sev_component_test/sev_component_test.py -t sme sev
```
# Virtual machine tests
Along with the component test, there are three virtual machine utilities that can be used to make sure SEV is working correctly. They can be used by raising the appropriate flag. **Note**: The testlocal/printlocal utilities only work on VMs that were launched using QEMU. For more information on how to run SEV VMs, please visit [AMD'S SEV developer website](https://developer.amd.com/sev/).

## Test local
This utility will perform an encryption test on the memory of virtual machines that are currently running in the system. The user can provide the **full** command used to launch the VM in order to test that specific VM or it can leave the entry blank in order to launch an interactive menu where the user can pick what VMs to test for encryption.
To test for a specific VM provided by the user:
```
$ python ./sev_component_test/sev_component_test.py --testlocal "qemu-system-x86_64 -enable-kvm -cpu EPYC -machine q35 -smp 4,maxcpus=64 -m 2048M,slots=5,maxmem=30G -drive if=pflash,format=raw,unit=0,file=/usr/local/share/qemu/OVMF_CODE.fd,readonly -drive if=pflash,format=raw,unit=1,file=OVMF_VARS.fd -netdev user,id=vmnic -device e1000,netdev=vmnic,romfile= -drive file=ubuntu-18.04-server-cloudimg-amd64.img,if=none,id=disk0 -drive file=seed.iso,if=none,id=cd0 -object sev-guest,id=sev0,cbitpos=47,reduced-phys-bits=1 -machine memory-encryption=sev0 -nographic"
```
or the user can leave the command blank to launch the UI:
```
$ python ./sev_component_test/sev_component_test.py -tl

Running local virtual machine encryption test:
Input PID of the VM you would like to test memory for. After all the desired machines have been added, input q or quit to run tests.


Virtual Machine: 35031
qemu-system-x86_64 -enable-kvm -cpu EPYC -machine q35 -smp 4,maxcpus=64 -m 2048M,slots=5,maxmem=30G -drive if=pflash,format=raw,unit=0,file=/usr/share/OVMF/OVMF_CODE.fd,readonly -drive if=pflash,format=raw,unit=1,file=OVMF_VARS.fd -netdev user,id=vmnic -device e1000,netdev=vmnic,romfile= -drive file=focal-server-cloudimg-amd64-disk-kvm.img,if=none,id=disk0 -drive file=seed.iso,if=none,id=cd0 -device virtio-scsi-pci,id=scsi0,disable-legacy=on,iommu_platform=true -device scsi-hd,drive=disk0 -device scsi-cd,drive=cd0 -nographic

What VM would you like to test? (Enter PID): 35031
Virtual Machine 35031 has been added.
What VM would you like to test? (Enter PID): q
Provided Virtual Machine found!

PID: 35031
qemu-system-x86_64 -enable-kvm -cpu EPYC -machine q35 -smp 4,maxcpus=64 -m 2048M,slots=5,maxmem=30G -drive if=pflash,format=raw,unit=0,file=/usr/share/OVMF/OVMF_CODE.fd,readonly -drive if=pflash,format=raw,unit=1,file=OVMF_VARS.fd -netdev user,id=vmnic -device e1000,netdev=vmnic,romfile= -drive file=focal-server-cloudimg-amd64-disk-kvm.img,if=none,id=disk0 -drive file=seed.iso,if=none,id=cd0 -device virtio-scsi-pci,id=scsi0,disable-legacy=on,iommu_platform=true -device scsi-hd,drive=disk0 -device scsi-cd,drive=cd0 -nographic

Testing virtual machine 35031 for encryption
Entropy value 1
Virtual Machine 35031 is probably not encrypted.
At least one VM failed the encryption test.
```
The user can add as many VMs as it wants in the user menu, but it can only test one if they provide the desired VM command. The UI won't work if the nonVerbose flag is also raised.

## Print Local
This utility is very similar to the test local one, the only difference is that instead of performing the encryption test on the memory, it will print 1 page of the memory for the given VMs. This allows the user to inspect the memory of the VMs in case that the encryption tests are returning unexpected results. 
To run this utility, use the command:
```
$ python ./sev_component_test/sev_component_test.py --printlocal
```
or to print the memory of a specific VM the command can be provided too.
```
$ python ./sev_component_test/sev_component_test.py -pl "qemu-system-x86_64 -enable-kvm -cpu EPYC -machine q35 -smp 4,maxcpus=64 -m 2048M,slots=5,maxmem=30G -drive if=pflash,format=raw,unit=0,file=/usr/local/share/qemu/OVMF_CODE.fd,readonly -drive if=pflash,format=raw,unit=1,file=OVMF_VARS.fd -netdev user,id=vmnic -device e1000,netdev=vmnic,romfile= -drive file=ubuntu-18.04-server-cloudimg-amd64.img,if=none,id=disk0 -drive file=seed.iso,if=none,id=cd0 -object sev-guest,id=sev0,cbitpos=47,reduced-phys-bits=1 -machine memory-encryption=sev0 -nographic"
```
This feature can't be used if the nonVerbose flag is also raised.

## Automatic Virtual Machine test
This utility tests the system's ability to launch SEV VMs. Using a qcow2 image created using [linux-kit](https://github.com/linuxkit/linuxkit), the tool will attempt to launch an SEV VM. If the VM launches, it will then test the VMs memory for encryption. If the VM is succesfully launched and the memory appears to be encrypted, then the auto VM test will pass.
To launch this test use the command:
```
$ python ./sev_component_test/sev_component_test.py --autotest
```
or
```
$ python ./sev_component_test/sev_component_test.py -at
```
Example of result:
```
Running automatic test for VM encryption:
Preparing machine for launch...
Launching Virtual Machine for testing:
Machine Launched!
Corresponding PID: 37167
Looking for machine memory....
Entropy value 8
Virtual Machine is probably encrypted.
Cleaning up machine...
```

# Testing
Unittests are provided to show how certain functions and formulas are supposed to behave. They can all be found in the tests folder. Pytesting can also be performed on this tests by installing pytest from the requirements.txt file. To run testing, simply run the command:
```
$ pytest ./tests
```