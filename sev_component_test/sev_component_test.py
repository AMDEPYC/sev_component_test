'''
Core module, access all functionalities by calling this program.
Run the system check tests, then run any extra tests raised by the flags.
Will run system check for SEV and SEV-ES by default.
    Any changes to desired system tests have to be done with the --test flag
Use --stopfailure flag to stop system check at first failure.
Use --testlocal flag to test encryption of VMs being run already.
    Can provide VM command to specify one desired VM, or not provide anything to launch UI.
Use --printlocal flag to print the memory of VMs being run.
    Can provide VM command to specify one desired VM, or not provide anything to launch UI.
Use --autotest flag to launch automatic VM encryption test on the tiny VM provided.
    Can ask to perform an unencrypted test or sev test (sev default).
Use --nonVerbose flag to run program without any prints
Use --enablement flag to only test for SEV enablment on the system (ignore package support)
Will return 1 if any of the desired tests fails, will return 0 if all the desired tests pass.
'''
import argparse
import datetime
import sys
import component_tests
import snp_component_tests
import local_vm_test
import auto_vm_test

from message_printing import print_overall_result, print_test_result

parser = argparse.ArgumentParser(
    description="Raise flags for different test functionalities.")
parser.add_argument("-s", "--stopfailure", help="Stop test at failure.",
                    action="store_true")
parser.add_argument("-t", "--test", nargs='+', help="Specify features to test for.",
                    default=['sev', 'sev-es', 'sev-snp'])
parser.add_argument("-tl", "--testlocal", nargs='?', help="Run test local functionality.",
                    default="not raised")
parser.add_argument("-pl", "--printlocal", nargs='?', help="Run print local functionality.",
                    default="not raised")
parser.add_argument("-at", "--autotest", nargs='?',
                    help="Run automatic encryption test functionality.",
                    default="not raised")
parser.add_argument("-nv", "--nonverbose", help="Run test with no print statements.",
                    action="store_true")
parser.add_argument("-e", "--enablement",
                    help="Run test to only check for enablement (ignore package support)",
                    action="store_true")


def check_system_support_test(non_verbose, stop_failure):
    '''
    Run the existing system support checks that query the system capabilites and informs if the
    system can or cannot run SEV features.
    '''

    # Dont't print if nonVerbose raised
    if not non_verbose:
        print("\nQuerying for system capabilities:")

    # Will turn false if any check fails
    pass_check = True
    # Tests to be run
    running_tests = {
        component_tests.find_cpuid_support: ['SEV'],
        component_tests.check_virtualization: (),
        component_tests.check_sme_enablement: ()
    }

    for test, components in running_tests.items():
        current_component, current_command, current_found_result,\
            current_expectation, current_test_result = test(*components)
        if not non_verbose:
            print_test_result(current_component, current_command,
                              current_found_result, current_expectation, current_test_result)
        if not current_test_result and not stop_failure:
            pass_check = False
        # Test failed, stop failure not enabled.
        elif not current_test_result and stop_failure:
            pass_check = False
            break
    return pass_check


def run_sme_test(non_verbose, stop_failure):
    '''
    Run the existing OS checks that query the system capabilites,
    and informs if the current system setup can run SME.
    '''

    if not non_verbose:
        print("\nComparing Host OS componenets to known SME requirements:")

    # Will turn false if any check fails
    pass_check = True

    running_tests = {
        component_tests.find_cpuid_support: ['SME'],
        component_tests.find_tsme_enablement: []
    }

    for test, components in running_tests.items():
        current_component, current_command, current_found_result,\
            current_expectation, current_test_result = test(*components)
        if not non_verbose:
            print_test_result(current_component, current_command,
                              current_found_result, current_expectation, current_test_result)
        if not current_test_result and not stop_failure:
            pass_check = False
        # Test failed, stop failure not enabled.
        elif not current_test_result and stop_failure:
            pass_check = False
            break
    return pass_check


def run_sev_test(non_verbose, system_os, stop_failure, enablement):
    '''
    Run the existing OS checks that query the system capabilites,
    and informs if the current system setup can run SEV.
    '''

    if not non_verbose:
        print("\nComparing Host OS componenets to known SEV minimum versions:")

    # Will turn false if any check fails
    pass_check = True
    # Tests to be run
    running_tests = {
        component_tests.validate_cpu_model: ["SEV"],
        component_tests.find_cpuid_support: ["SEV"],
        component_tests.find_asid_count: ["SEV"],
        component_tests.check_linux_distribution: [],
        component_tests.check_kernel: ['SEV'],
        component_tests.check_if_sev_init: [],
    }

    # Package tests, ignore if enablment flag is on
    if not enablement:
        running_tests[component_tests.find_libvirt_support] = []
        running_tests[component_tests.find_qemu_support] = [system_os, 'SEV']
        running_tests[component_tests.test_all_ovmf_paths] = [system_os, datetime.date(2018, 7, 6)]

    #Run all tests
    for test, components in running_tests.items():
        if test == component_tests.test_all_ovmf_paths:
            current_test_result, ovmf_paths = test(*components)
            if not non_verbose:
                for path in ovmf_paths:
                    print_test_result(*path.values())
        else:
            current_component, current_command, current_found_result,\
                current_expectation, current_test_result = test(*components)
            if not non_verbose:
                print_test_result(current_component, current_command,
                                  current_found_result, current_expectation, current_test_result)

        # Stop running checks immediately if the test fails and the stopfailure flag is enabled.
        if not current_test_result and not stop_failure:
            pass_check = False
        # Test failed, stop failure enabled.
        elif not current_test_result and stop_failure:
            pass_check = False
            break

    return pass_check


def run_sev_es_test(non_verbose, system_os, stop_failure, enablement):
    '''
    Run the existing OS checks that query the system capabilites,
    and informs if the current system setup can run SEV-ES.
    '''
    # if not nonVerbose:
    print("\nComparing Host OS componenets to known SEV-ES minimum versions:")

    # Will turn false if any check fails
    pass_check = True

    running_tests = {
        component_tests.validate_cpu_model: ["SEV-ES"],
        component_tests.find_cpuid_support: ['SEV-ES'],
        component_tests.check_kernel: ['SEV-ES'],
        component_tests.find_asid_count: ['SEV-ES'],
        component_tests.check_if_sev_es_init: [],
    }

    if not enablement:
        running_tests[component_tests.find_libvirt_support] = []
        running_tests[component_tests.find_qemu_support] = [system_os, 'SEV-ES']
        running_tests[component_tests.test_all_ovmf_paths] = [system_os, datetime.date(2020, 11, 1)]

    for test, components in running_tests.items():
        if test == component_tests.test_all_ovmf_paths:
            current_test_result, ovmf_paths = test(*components)
            if not non_verbose:
                for path in ovmf_paths:
                    print_test_result(*path.values())
        else:
            current_component, current_command, current_found_result,\
                current_expectation, current_test_result = test(*components)
            if not non_verbose:
                print_test_result(current_component, current_command,
                                  current_found_result, current_expectation, current_test_result)

        # Stop running checks immediately if the test fails and the stopfailure flag is enabled.
        if not current_test_result and not stop_failure:
            pass_check = False
        # Test failed, stop failure enabled.
        elif not current_test_result and stop_failure:
            pass_check = False
            break

    return pass_check

def run_sev_snp_test(non_verbose, stop_failure):
    '''
    Run the existing OS checks that query the system capabilites,
    and informs if the current system setup can run SEV-SNP.
    '''
    # if not nonVerbose:
    print("\nComparing Host OS componenets to known SEV-SNP minimum versions:")

    running_tests = {
        component_tests.validate_cpu_model: ["SEV-SNP"],
        component_tests.find_cpuid_support: ['SEV-SNP'],
        snp_component_tests.check_if_snp_enabled: [],
        snp_component_tests.check_fw_version_for_snp: [],
        snp_component_tests.find_iommu_enablement: []
    }

    snp_tests = {
        snp_component_tests.check_snp_init : [],
        snp_component_tests.check_rmp_init : [],
        snp_component_tests.get_rmp_address: [],
        snp_component_tests.compare_tcb_versions : []
    }
  
    # Will turn false if any check fails
    pass_check = True

    for test, components in running_tests.items():
        current_component, current_command, current_found_result,\
            current_expectation, current_test_result = test(*components)
        if not non_verbose:
            print_test_result(current_component, current_command,
                                current_found_result, current_expectation, current_test_result)

        # Stop running checks immediately if the test fails and the stopfailure flag is enabled.
        if not current_test_result and not stop_failure:
            pass_check = False
        # Test failed, stop failure enabled.
        elif not current_test_result and stop_failure:
            pass_check = False
            break
    
    if pass_check:
        for test, components in snp_tests.items():
            current_component, current_command, current_found_result,\
            current_expectation, current_test_result = test(*components)
            if not non_verbose:
                print_test_result(current_component, current_command,
                                    current_found_result, current_expectation, current_test_result)

            # Stop running checks immediately if the test fails and the stopfailure flag is enabled.
            if not current_test_result and not stop_failure:
                pass_check = False
            # Test failed, stop failure enabled.
            elif not current_test_result and stop_failure:
                pass_check = False
                break

    return pass_check


def run_component_tests(non_verbose, system_os, stop_failure, feature_tests, enablement):
    '''
    Function to run all of the current tests,
    will return the result of each individual system test,
    and if all tests passed or not.
    '''
    # If all the tested features passed
    all_tests_pass = False

    # Tests to be run are added here
    tests = {}
    # Test results are added here
    results = {}
    # System support test result
    tests[check_system_support_test] = [non_verbose, stop_failure,'SYSTEM SUPPORT']
    results['SYSTEM SUPPORT'] = False

    # SME enabled
    if set(['sme']).intersection(set(feature_tests)):
        tests[run_sme_test] = [non_verbose, stop_failure,'SME COMPONENT TEST']
        results['SME COMPONENT TEST'] = False
    else:
        results['SME COMPONENT TEST'] = True

    # SEV test result
    tests[run_sev_test] = [non_verbose, system_os, stop_failure, enablement, 'SEV COMPONENT TEST']
    results['SEV COMPONENT TEST'] = False

    # SEV-ES enabled
    if set(['sev-es']).intersection(set(feature_tests)) or set(['sev-snp']).intersection(set(feature_tests)):
        tests[run_sev_es_test] = [non_verbose, system_os, stop_failure, enablement,'SEV-ES COMPONENT TEST']
        results['SEV-ES COMPONENT TEST'] = False
    else:
        results['SEV-ES COMPONENT TEST'] = True

    # SEV-SNP enabled
    if set(['sev-snp']).intersection(set(feature_tests)):
        tests[run_sev_snp_test] = [non_verbose, stop_failure,'SEV-SNP COMPONENT TEST']
        results['SEV-SNP COMPONENT TEST'] = False
    else:
        results['SEV-SNP COMPONENT TEST'] = True

    for test, test_description in tests.items():
        test_args = test_description[:-1]
        results[test_description[-1]] = test(*test_args)
        if not non_verbose:
            print_overall_result(
                test_description[-1], results[test_description[-1]])
    if False not in results.values():
        all_tests_pass = True

    return all_tests_pass, results['SEV COMPONENT TEST']


def main():
    '''
    Run the system check tests, then run any extra tests raised by the flags.
    Will run system check for SEV and SEV-ES by default.
    Any changes to desired system tests have to be done with the --test flag
    Use --stopfailure flag to stop system check at first failure.
    Use --testlocal flag to test encryption of VMs being run already.
    Can provide VM command to specify one desired VM, or not provide anything to launch UI.
    Use --printlocal flag to print the memory of VMs being run.
    Can provide VM command to specify one desired VM, or not provide anything to launch UI.
    Use --autotest flag to launch automatic VM encryption test on the tiny VM provided.
    Use --nonVerbose flag to run program without any prints
    Use --enablement flag to only test for SEV enablment on the system (ignore package support)
    Will return 1 if any of the desired tests fails, will return 0 if all the desired tests pass.
    '''
    args = parser.parse_args()
    system_os, _ = component_tests.get_linux_distro()  # Global SYSTEMOS
    # Print explanation
    if not args.nonverbose:
        print("\nRunning SEV Component Test tool. "
        "For more running options, run 'python sev_component_test.py -h'.")
        print("For more information please go to https://www.amd.com/en/developer/sev.htm/")
    
    # Overall program result
    all_requested_tests_pass = True

    component_test_pass, sev_pass = run_component_tests(args.nonverbose, system_os, args.stopfailure,args.test ,args.enablement)

    # If one of the desired system check fails, then overall test will return failure
    if not component_test_pass:
        all_requested_tests_pass = False
    
    # Test local feature has been raised
    if args.testlocal != 'not raised':
        if not args.nonverbose:
            print("\nRunning local virtual machine encryption test:")
        # If one of the provided VMs fails the encryption test, overall test fails.
        if not local_vm_test.run_local_vm_test(system_os, args.testlocal, args.nonverbose):
            all_requested_tests_pass = False

    # Print local feature has been raised
    if args.printlocal != 'not raised':
        if not args.nonverbose:
            print("\nRunning local virtual machine memory printer:")
        # Print one page of memory for the provided VMs
        local_vm_test.run_print_memory(system_os, args.printlocal, args.nonverbose)

    # auto test feature has been raised
    if args.autotest != "not raised":
        auto_test_result = False
        # Auto test will not run if the SEV test does not pass
        if not sev_pass and not args.nonverbose:
            print("SEV Component Test failed. SEV Machine cannot be launched.")
        # sev passed tests, run the vm test
        elif sev_pass:
            # Invalid argument passed for auto test
            if not args.autotest in ('sev', 'unencrypted', 'sev-es', None) and not args.nonverbose:
                print('An invalid VM type was parsed. Cannot run auto vm test.')
            # Valid argument passed
            elif args.autotest in ('sev', 'unencrypted', 'sev-es', None):
                if not args.nonverbose:
                    print("\nRunning automatic test for VM encryption:")
                # If no test is specified, run sev test
                if args.autotest is None:
                    auto_test_result =  auto_vm_test.automatic_vm_test(system_os, args.nonverbose,'sev')
                # Run specified test
                else:
                    auto_test_result =  auto_vm_test.automatic_vm_test(system_os, args.nonverbose,args.autotest)
        
        # Grab result
        all_requested_tests_pass = auto_test_result

    # Return program results
    if all_requested_tests_pass:
        return 0
    return 1


if __name__ == '__main__':
    sys.exit(main())