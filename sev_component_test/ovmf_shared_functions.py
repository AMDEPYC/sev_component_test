'''Functions used for OVMF testing. Used by component test and by auto vm test'''
import subprocess
import re
import datetime

def print_warning_message(component, warning):
    '''
    Warning message when a test runs into an error and the test can't be performed.
    '''
    yellow = '\033[93m'
    reset_color = '\033[0m'
    # Test can't be run due to certain set-ups in the system
    print("- " + component + " test could not be performed. Error found: "
          + warning + yellow + " WARNING" + reset_color)


def get_ovmf_version(console_string):
    '''
    Get the OVMF version of the default distro package.
    It is good to remember that the "version" for OVMF is a date,
    so it will look like 2022.11 or 20110523.
    '''
    # Variables to keep track of where we are on the string and when to break
    version_finder = False
    in_version = False
    ovmf_version = ''
    hyphen_counter = 0
    break_at_hyphen = False
    # Loop through the string received to get the version
    for char in console_string:
        # At the end of ovmf or 64
        if char in ('f', '4'):
            version_finder = True
        # Going into version number
        elif char != ' ' and version_finder:
            in_version = True
            # Break at the first hyphen raised
            if char == '-' and break_at_hyphen:
                break

            # Version leads with hyphen, break at second hyphen
            if char == '-' and hyphen_counter == 0:
                hyphen_counter += 1
                continue

            # Ignore this character
            if char != '~' and hyphen_counter == 0 and not break_at_hyphen and not char.isdigit():
                continue

            # Count this character as a hyphen
            if char == '~' and hyphen_counter == 0:
                hyphen_counter += 1
                continue

            # Arrived at the end of the the version
            if not char.isdigit() and ovmf_version and char not in ('x', '.'):
                break

            # If version leads with a digit, break at the first hyphen
            if char.isdigit() and not ovmf_version:
                break_at_hyphen = True
                ovmf_version += char
            # Version was not found yet
            elif char == 'x' and hyphen_counter > 0:
                hyphen_counter = 0
                version_finder = False
            # You are in the version, grab the character
            else:
                # You are in the version, grab the character
                ovmf_version += char

        # Full version collected, unecessary additional data
        elif char == ' ' and in_version:
            break
    if len(ovmf_version) > 8 and ovmf_version[0] == '0':
        ovmf_version = ovmf_version[1:]
    # return result
    return ovmf_version


def convert_ovmf_version_to_date(ovmf_version):
    '''
    From default OVMF package version, get corresponding commit date
    '''
    # Get the version in date format
    version_year, version_month, version_day = '', '', ''
    # Remove periods
    ovmf_version = ovmf_version.replace(".", "")

    if len(ovmf_version) < 8:
        version_year, version_month, version_day = ovmf_version[0:4], ovmf_version[4:], '01'
    else:
        version_year, version_month, version_day = ovmf_version[
            0:4], ovmf_version[4:6], ovmf_version[6:]

    try:
        # Put into date time format
        version_date = datetime.date(
            int(version_year), int(version_month), int(version_day))

        # Return version
        return version_date
    except TypeError:
        print_warning_message('OVMF Version retrieval',
                              'Could not get ovmf version in a datetime format')
        return False


def get_default_ovmf_path(system_os):
    '''
    Get the path were the default version of OVMF
    (OVMF_VARS.fd or OVMF_VARS.bin) is stored for a given distro.
    Also get its version and version date.
    '''

    # Command list for given distro
    command_list = {
        'ubuntu': 'dpkg --list', 'debian': 'dpkg --list',
        'fedora': 'rpm -q edk2-ovmf', 'rhel': 'rpm -q edk2-ovmf',
        'opensuse-tumbleweed': 'rpm -q ovmf', 'opensuse-leap': 'rpm -q qemu-ovmf-x86_64',
        'centos': 'rpm -q edk2-ovmf'}

    # Where the package path is expected to be stored
    if system_os in ("opensuse-tumbleweed", "opensuse-leap"):
        default_path = '/usr/share/qemu/ovmf-x86_64-vars.bin'
    else:
        default_path = '/usr/share/OVMF/OVMF_VARS.fd'
    # Date corresponding to the default OVMF version
    version_date = None

    # If distro not in the list use a default rpm -q edk2-ovmf command
    command = command_list.get(system_os, "rpm -q edk2-ovmf")

    try:
        # Find default package form distro
        ovmf_version_read = subprocess.run(
            command, shell=True, check=True, capture_output=True)
        grep_ovmf_read = subprocess.run("grep ovmf", shell=True,
                                        input=ovmf_version_read.stdout, check=True, capture_output=True)
        # Call to get default package version
        ovmf_version = get_ovmf_version(
            grep_ovmf_read.stdout.decode("utf-8").strip())
        # Call to get deafualt package commit date
        version_date = convert_ovmf_version_to_date(ovmf_version)
        # Return results
        return command, default_path, ovmf_version, version_date

    # Error with the subprocess command
    except (subprocess.CalledProcessError) as err:
        if not err.stdout.decode("utf-8").strip():
            print_warning_message(
                'Finding default ovmf package', 'OVMF not installed')
        else:
            print_warning_message('Finding default ovmf package',
                                  err.stderr.decode("utf-8").strip())
        return False, False, False, False


def get_built_ovmf_paths():
    '''
    Find manually built OVMF paths.
    '''
    # Paths found
    paths = []
    try:
        # Command to find all paths containing FV from root
        subprocess_paths = subprocess.run("find / -type d -name FV",
                                          shell=True, check=True, capture_output=True)
        all_fv_paths = subprocess_paths.stdout.decode("utf-8").split('\n')
        all_fv_paths.remove('')
        for path in all_fv_paths:
            # From found path, get path to OVMF_VARS.fd
            ovmf_path = subprocess.run("find " + path + " -name OVMF_VARS.fd",
                                       shell=True, check=True, capture_output=True)
            ovmf_path = ovmf_path.stdout.decode("utf-8").strip()
            # Put found paths into path list
            if ovmf_path:
                paths.append(ovmf_path)
        # Return paths
        return paths
    # Error with the subprocess command
    except (subprocess.CalledProcessError) as err:
        print_warning_message('Finding built ovmf paths',
                              err.stderr.decode("utf-8").strip())
        return False


def get_commit_date(path):
    '''
    Get the commit date for an externally built OVMF
    '''
    # Split the path string into a listh of files
    directory = path.split('/')
    directory.remove('')
    git_path = '/'
    if 'Build' in directory:
        git_path = '/'.join(directory[0:directory.index('Build')]) + '/'
    else:
        print_warning_message('Getting commit date for build path',
                              'Could not find Build in path')
        return False

    try:
        # Command to get git summary from which we can get the commit date
        git_command = "git --git-dir /" + git_path + ".git show"
        git_summary = subprocess.run(
            git_command, shell=True, check=True, capture_output=True)
        git_date_raw = subprocess.run("grep Date", input=git_summary.stdout,
                                      shell=True, check=True, capture_output=True)
        git_date = git_date_raw.stdout.decode("utf-8").strip()
        git_date = re.sub(' +', ' ', git_date)
        date_array = git_date.split(' ')
        # Get commit date as a date object with time
        datetime_object = datetime.datetime.strptime(date_array[2], "%b")
        month_number = datetime_object.month
        # Get git commit date as day-month-year format for date
        version_date = datetime.date(
            int(date_array[5]), month_number, int(date_array[3]))

        # return the git commit date as the version date
        return version_date, git_command
    # Error with the subprocess command
    except (subprocess.CalledProcessError) as err:
        print_warning_message('Finding built path commit date',
                              err.stderr.decode("utf-8").strip())
        return False, False
    except TypeError:
        print_warning_message('Finding built path commit date',
                              'Could not convert path into a datetime object')
        return False, False


def format_ovmf_path(raw_path):
    '''
    Format the path for display and testing
    '''
    edited_path = None
    directory_array = raw_path.split('/')
    if 'OVMF_VARS.fd' in directory_array:
        directory_array.remove('OVMF_VARS.fd')
    elif 'ovmf-x86_64-vars.bin' in directory_array:
        directory_array.remove('ovmf-x86_64-vars.bin')
    edited_path = '/'.join(directory_array)
    return edited_path


def get_path_to_ovmf(system_os):
    '''
    Find 1 working path to an OVMF file. Will return the 1st found path found that can support SEV.
    '''
    # Minimum date required to run SEV
    min_date = datetime.date(2018, 7, 6)
    # Look for default path and version date of default path
    _, default_path, _, default_install_date = get_default_ovmf_path(system_os)
    # If default_path exists and the path exists, default version of ovmf works
    if default_path and default_install_date >= min_date:
        return format_ovmf_path(default_path)
    # Default path not found, look for build path
    built_paths = get_built_ovmf_paths()
    for path in built_paths:
        # Call to get commit date from given path
        ovmf_commit_date = get_commit_date(path)
        # Call to compare path commit date with given minimum date for either SEV or SEV-ES
        if ovmf_commit_date >= min_date:
            return format_ovmf_path(path)

    return False