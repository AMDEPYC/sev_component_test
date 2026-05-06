'''Functions used for OVMF testing. Used by component test and by auto vm test'''
import subprocess
import re
import datetime
import os
from message_printing import print_warning_message

def get_ovmf_version(console_string):
    '''
    Get the OVMF version of the default distro package.
    It is good to remember that the "version" for OVMF is a date,
    so it will look like 2022.11 or 20110523.
    '''
    # Split by non-digit characters to find numeric segments
    parts = [p for p in re.split(r'\D+', console_string) if p]
    
    # Find the first segment that looks like a year (at least 4 digits)
    for i, p in enumerate(parts):
        if len(p) >= 4:
            # This is our starting point. Collect it and any immediately 
            # following small segments (like month/day in 2022.11.05)
            version_segments = [p]
            for j in range(i + 1, min(i + 3, len(parts))):
                if len(parts[j]) <= 2:
                    version_segments.append(parts[j])
                else:
                    break
            return '.'.join(version_segments)
            
    return ''


def convert_ovmf_version_to_date(ovmf_version):
    '''
    From default OVMF package version, get corresponding commit date
    '''
    if not ovmf_version:
        return False

    # Split by non-digit characters to find date segments
    parts = [p for p in re.split(r'\D+', ovmf_version) if p]
    
    # Find the first part that looks like a date (starts with 4-digit year)
    # This skips things like the '2' in 'edk2'
    date_str = next((p for p in parts if len(p) >= 4), None)
    if not date_str:
        return False

    # Handle the main date string (could be YYYY, YYYYMM, or YYYYMMDD)
    year = date_str[0:4]
    month = date_str[4:6] if len(date_str) >= 6 else '01'
    day = date_str[6:8] if len(date_str) >= 8 else '01'
    
    # If it was just YYYY or YYYYMM, and there are more parts, use them for month/day
    remaining_parts = parts[parts.index(date_str)+1:]
    if len(date_str) == 4 and remaining_parts:
        month = remaining_parts[0]
        if len(remaining_parts) > 1:
            day = remaining_parts[1]

    try:
        # Put into date time format
        version_date = datetime.date(
            int(year), int(month), int(day))

        # Return version
        return version_date
    except (TypeError, ValueError):
        print_warning_message('OVMF Version retrieval',
                              f'Could not get ovmf version from "{ovmf_version}" in a datetime format')
        return False


def get_default_ovmf_path(system_os):
    '''
    Get the path were the default version of OVMF
    (OVMF_VARS.fd or OVMF_VARS.bin) is stored for a given distro.
    Also get its version and version date.
    '''

    # Command list for given distro
    version_command_list = {
        'ubuntu': "dpkg-query -f='${Version}' -W ovmf", 'debian': "dpkg-query -f='${Version}' -W ovmf",
        'fedora': "rpm -q --qf '%{VERSION}' edk2-ovmf", 'rhel': "rpm -q --qf '%{VERSION}' edk2-ovmf",
        'opensuse-tumbleweed': "rpm -q --qf '%{VERSION}' ovmf", 'opensuse-leap': "rpm -q --qf '%{VERSION}' qemu-ovmf-x86_64",
        'centos': "rpm -q --qf '%{VERSION}' edk2-ovmf"}

    # If distro not in the list, try common commands
    if system_os in version_command_list:
        ovmf_commands = [version_command_list[system_os]]
    else:
        ovmf_commands = list(dict.fromkeys(version_command_list.values()))

    # Where the package path is expected to be stored
    default_path = None
    if system_os in ("opensuse-tumbleweed", "opensuse-leap"):
        default_path = '/usr/share/qemu/ovmf-x86_64-vars.bin'
    else:
        # Common filenames for OVMF, including variations mentioned by user
        possible_filenames = [
            "ovmf_vars.fd", "ovmf_vars_4m.fd", "ovmf_code.fd", "ovmf_code_4m.fd", "ovmf.fd",
        ]
        # Common directories
        possible_dirs = ["/usr/share/OVMF/", "/usr/share/ovmf/"]

        for directory in possible_dirs:
            if os.path.exists(directory):
                try:
                    files = os.listdir(directory)
                    lower_files = {f.lower(): f for f in files}
                    for target in possible_filenames:
                        if target.lower() in lower_files:
                            default_path = os.path.join(directory, lower_files[target.lower()])
                            break
                except OSError:
                    continue
            if default_path:
                break

    # Try to find a command that works
    command = None
    ovmf_version_read = None
    for cmd in ovmf_commands:
        try:
            res = subprocess.run(
                cmd, shell=True, check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
        else:
            command = cmd
            ovmf_version_read = res
            break

    if not command or not ovmf_version_read:
        print_warning_message(
            'Finding default ovmf package', 'OVMF not installed')
        return command, False, False, False

    # Call to get default package version
    ovmf_version = get_ovmf_version(ovmf_version_read.stdout.decode("utf-8").strip())
    # Call to get deafualt package commit date
    version_date = convert_ovmf_version_to_date(ovmf_version)
    # Return results
    return command, default_path, ovmf_version, version_date


def get_built_ovmf_paths():
    '''
    Find manually built OVMF paths.
    '''
    # Paths found
    paths = []
    try:
        # Command to find all paths containing FV from root
        subprocess_paths = subprocess.run("find / -xdev -type d -name FV",
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
        return False, False

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
    if default_path and default_install_date and default_install_date >= min_date:
        return format_ovmf_path(default_path)
    # Default path not found, look for build path
    built_paths = get_built_ovmf_paths()
    for path in built_paths:
        # Call to get commit date from given path
        ovmf_commit_date, _ = get_commit_date(path)
        # Call to compare path commit date with given minimum date for either SEV or SEV-ES
        if ovmf_commit_date and ovmf_commit_date >= min_date:
            return format_ovmf_path(path)

    return False
