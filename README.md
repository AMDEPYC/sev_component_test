
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
    - [enablement](#enablement)
- [Virtual machine tests](#Virtual-machine-tests)
    - [Test local](#Test-local)
    - [Print local](#Print-local)
    - [Auto VM Test](#automatic-virtual-machine-test)
- [Testing](#Testing)

# SEV component test
This script is used to query a host system's capabilities to use AMD'S encryption techonologies: SEV, SEV-ES and SEV-SNP. It can also checks for SME compatibility and TSME enablement. It will run checks of several different components, and it will allow the user to know if the host system is set-up correctly in order to use SEV features. If there are any more questions regarding SME, SEV SEV-ES, or SEV-SNP please visit [AMD'S SEV developer website](https://www.amd.com/en/developer/sev.htm).

# Setting up host OS
All OS distributions need to install some pip packages in order to run this tool. Installation for each package differs depending on the distro.

In order to install all the required python packages, there is a requirements.txt file provided. To install the desired packages simply run:
```
$ pip/pip3 install -r requirements.txt
```
on the root directory of the project.

# Usage
Once the host is set-up, in order to run the tool simply use:
```
$ sudo python ./sev_component_test/sev_component_test.py
```
This will initialize the check on the system and the results of the component test will appear on the terminal screen.
Since the program is checking MSRs and CPUID functions, it will need to be run with root privileges.

**PYTHON 3.8 OR NEWER IS REQUIRED TO RUN THE PROGRAM**

There are flags that can be raised in order to use different features that the tool offers. These can be raised individually or a combination of them at the same time.

Test example on Ubuntu 22.04:
```
Running SEV Component Test tool. For more running options, run 'python sev_component_test.py -h'.
For more information please go to https://www.amd.com/en/developer/sev.htm/

Querying for system capabilities:
- CPUID function 0x8000001f bit 1 for SEV [ cpuid 0x8000001f ] Found: EAX bit 1 is True Expected: EAX bit 1 to be '1' OK
- Virtualization capabilities [ lscpu | grep Virtualization ] Found: Virtualization: AMD-V Expected: Virtualization: AMD-V OK
- SME enabled [ MSR 0xC0010010 ] Found: MSR 0xC0010010 bit 23 is 1 Expected: MSR 0xC0010010 it 23 is 1 OK
SYSTEM SUPPORT PASS

Comparing Host OS componenets to known SEV minimum versions:
- CPU model generation support [ cpuid 0x80000001 ] Found: SEV supported by milan Expected: naples or newer model OK
- CPUID function 0x8000001f bit 1 for SEV [ cpuid 0x8000001f ] Found: EAX bit 1 is True Expected: EAX bit 1 to be '1' OK
- Available SEV ASIDS [ cpuid 0x8000001f ] Found: 410 ASIDs Expected: xxx ASIDs OK
- Current OS distribution [ cat /etc/os-release ] Found: ubuntu 22.04 Expected: (comparing against known minimum version list) OK
- Kernel [ uname -r ] Found: 5.19.0-rc6-snp-host-c4daeffce Expected: 4.16 minimum OK
- SEV INIT STATE [ SEV apis ] Found: 1 Expected: 1 OK
- Libvirt version [ virsh -V ] Found: 8.0.0 Expected: 4.5 minimum OK
- QEMU version [ qemu-system-x86_64 --version ] Found: 6.2.0 (Debian 1:6.2+dfsg-2ubuntu6.12) Expected: 2.12 minimum OK
- OMVF path install [ dpkg --list ] Found: /usr/share/OVMF/OVMF_VARS.fd 2022-02-01  Expected: 2018-07-06  OK
- OMVF path install [ git --git-dir /root/snp/setup/latest/AMDSEV/ovmf/.git show ] Found: /root/snp/setup/latest/AMDSEV/ovmf/Build/OvmfX64/DEBUG_GCC5/FV/OVMF_VARS.fd 2022-03-28  Expected: 2018-07-06  OK
SEV COMPONENT TEST PASS

Comparing Host OS componenets to known SEV-ES minimum versions:
- CPU model generation support [ cpuid 0x80000001 ] Found: SEV-ES supported by milan Expected: rome or newer model OK
- CPUID function 0x8000001f bit 3 for SEV-ES [ cpuid 0x8000001f ] Found: EAX bit 3 is True Expected: EAX bit 3 to be '1' OK
- Kernel [ uname -r ] Found: 5.19.0-rc6-snp-host-c4daeffce Expected: 5.11 minimum OK
- Available SEV-ES ASIDS [ cpuid 0x8000001f ] Found: 99 ASIDs Expected: xxx ASIDs OK
- SEV-ES INIT STATE [ SEV apis ] Found: 1 Expected: 1 OK
- Libvirt version [ virsh -V ] Found: 8.0.0 Expected: 4.5 minimum OK
- QEMU version [ qemu-system-x86_64 --version ] Found: 6.2.0 (Debian 1:6.2+dfsg-2ubuntu6.12) Expected: 6.0 minimum OK
- OMVF path install [ dpkg --list ] Found: /usr/share/OVMF/OVMF_VARS.fd 2022-02-01  Expected: 2020-11-01  OK
- OMVF path install [ git --git-dir /root/snp/setup/latest/AMDSEV/ovmf/.git show ] Found: /root/snp/setup/latest/AMDSEV/ovmf/Build/OvmfX64/DEBUG_GCC5/FV/OVMF_VARS.fd 2022-03-28  Expected: 2020-11-01  OK
SEV-ES COMPONENT TEST PASS

Comparing Host OS componenets to known SEV-SNP minimum versions:
- CPU model generation support [ cpuid 0x80000001 ] Found: SEV-SNP supported by milan Expected: milan or newer model OK
- CPUID function 0x8000001f bit 4 for SEV-SNP [ cpuid 0x8000001f ] Found: EAX bit 4 is True Expected: EAX bit 4 to be '1' OK
- SNP enabled in MSR [ MSR 0xC0010010 ] Found: MSR 0xC0010010 bit 23 is 1 Expected: MSR 0xC0010010 bit 24 is 1 OK
- System SEV firmware version [ SEV_PLATFORM_STATUS ] Found: 1.53 Expected: SEV-SNP API VERSION 1.51 OK
- Checking IOMMU enablement [ find /sys/kernel/iommu_groups/ ] Found: /sys/kernel/iommu_groups/ exists Expected: /sys/kernel/iommu_groups/ exists OK
- SNP INIT [ SNP_PLATFORM_STATUS ] Found: 1 Expected: 1 OK
- RMP INIT [ SNP_PLATFORM_STATUS ] Found: 1 Expected: 1 OK
- RMP table addresses [ MSR 0xC0010132 - 0xC0010133 ] Found: RMP table physical address range 0x39e00000 - 0x566fffff Expected: RMP table physical address range xxx - xxx OK
- Comparing TCB versions [ SNP_PLATFORM_STATUS ] Found: Current TCB: 12180548142176927747 Reported TCB: 12180548142176927747 Expected: Current TCB matches reported TCB OK
SEV-SNP COMPONENT TEST PASS
```
** Program will only check for components in the system PATH for qemu and libvirt. Components built from source code will need to be added to the PATH in order to be tested. **

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
This flag allows the user to pick what features to test for. By raising it the user can specify if they want to test for only one specific feature (SEV, SEV-ES, SEV-SNP or SME), all of them, or any combination of the 4. That way if the user is curious about only one feature, they can just test for that one, instead of having to test for all of them. **Note**: If testing for SEV-ES, the SEV test will always run, since being able to run SEV is a prerequisite for SEV-ES. The same goes for SEV-SNP with SEV and SEV-ES, since they're prerequisites for SEV-SNP. By default the program will only test for SEV, SEV-ES and SEV-SNP.
To use this flag, use the command:
```
$ python ./sev_component_test/sev_component_test.py --test [features to be tested]
```
or
```
$ python ./sev_component_test/sev_component_test.py -t [features to be tested]
```
Features (sev, sev-es, sev-snp or sme) written in lower-case and separated by a space.

Example feature testing for SME and SEV only:
```
$ python ./sev_component_test/sev_component_test.py -t sme sev
```

## Enablement
This flag allows the user to only check for SEV enablement on the system. The test checks by default for package support for QEMU and libvirt, but somtimes a user will be interested on just knowing if SEV is enabled correctly in the system, and then run their own tests with different packages. The enablment flag will make it so that the test only checks for SEV (and other tested features) to be enabled correctly in the system.
To use this flag, use the command:
```
$ python ./sev_component_test/sev_component_test.py --enablement
```
or
```
$ python ./sev_component_test/sev_component_test.py -e
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
This utility tests the system's ability to launch SEV VMs. Using a qcow2 image created using [linux-kit](https://github.com/linuxkit/linuxkit), the tool will attempt to automatically launch a VM. The user can specify if they want to launch an SEV VM or an unencrypted VM for testing. This is meant to work as a sanity check to make sure the system is working as expected after all of the SEV component tests have passed. If the user decides to launch the VM with SEV, then the memory will be checked for encryption, if the memory seems to be encrypted then the test will pass. If the user decides to launch the VM without encryption, then the test will make sure that the memory is unencrypted, thus making sure the SEV test is not a false positive. The qcow2 image is not intented to be used as a full VM since it has very limited funcitonality. The test will not run unless the SEV part of the component test passes.

### Set-up
Due to the large size of the qcow2 image, the image is being stored in the repository through git large file storage. In order to be able to use this feature, one has to pull down the repo using git lfs. To do this, one first has to install the git-lfs extension.

Ubuntu:
```
$ sudo apt install git-lfs
```
RHEL:
```
$ sudo dnf install git-lfs.x86_64
```
OPEN-SUSE:
```
$ sudo zypper install git-lfs
```

Once git-lfs is installed, you can pull again in the same repository using:
```
$ git lfs pull
```
This will pull down the qcow2 image from the lfs repository and will be available for testing.
### Run Test
To launch this test use the command:
```
$ python ./sev_component_test/sev_component_test.py --autotest [sev | unencrypted]
```
or
```
$ python ./sev_component_test/sev_component_test.py -at
```

If the entry is left blank, then the tool will perform the sev test as a default.

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
