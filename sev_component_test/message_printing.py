'''
Functions to print test results.
'''
def print_test_result(component, command, found, expectation, result):
    '''
    Format in which test results will be printed.
    '''
    # Colors for print statments
    colors = {
        'reset': '\033[0m',
        'red': '\033[31m',
        'green': '\033[32m',
        'yellow': '\033[93m'
    }
    if result:
        # Test passes
        print("- " + component + " [ " + command + " ] Found: "
              + found + " Expected: " + expectation + colors["green"]
              + " OK" + colors["reset"])
    else:
        # Test fails
        print("- " + component + " [ " + command + " ] Found: "
              + found + " Expected: " + expectation + colors["red"]
              + " FAIL" + colors["reset"])


def print_overall_result(test, result):
    '''
    Print the current system test result in this format. The current system test and its result.
    '''
    colors = {
        'reset': '\033[0m',
        'red': '\033[31m',
        'green': '\033[32m',
        'yellow': '\033[93m'
    }
    if result:
        print(test + colors['green'] + " PASS" + colors['reset'])
    else:
        print(test + colors['red'] + " FAIL" + colors['reset'])

def print_warning_message(component, warning):
    '''
    Warning message when a test runs into an error and the test can't be performed.
    '''
    yellow = '\033[93m'
    reset_color = '\033[0m'
    # Test can't be run due to certain set-ups in the system
    print("- " + component + " test could not be performed. Error found: "
          + warning + yellow + " WARNING" + reset_color)