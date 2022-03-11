
import subprocess
from re import sub
import subprocess
import datetime

def getOVMFVersion(string):
    '''
    Get the OVMF version of the default distro package. (A bit messy since different distros name the packages different things)
    It is good to remember that the "version" for OVMF is a date so it will look like 2022.11 or 20110523.
    '''
    #Variables to keep track of where we are on the string and when to break
    versionFinder = False
    inVersion = False
    version = ''
    hyphenCounter = 0
    breakAtHyphen = False
    #Parse string
    for x in string:
        #At the end of ovmf or 64
        if x == 'f' or x == '4':
            versionFinder = True
        #Going into version number
        elif x != ' ' and versionFinder:
            inVersion = True
            
            #if version leads with a digit, break at the first hyphen
            if x.isdigit():
                if version == '':
                    breakAtHyphen = True

            #break aty hyphen
            if x == '-' and breakAtHyphen:
                return version
            #version leads with hyphen, break at second hyphen
            elif x == '-' and hyphenCounter == 0:
                hyphenCounter += 1
                continue
            #version was not found yet
            elif x == 'x' and hyphenCounter > 0:
                hyphenCounter = 0
                versionFinder = False

            #Continue 
            if x != '~' and hyphenCounter == 0 and not breakAtHyphen:
                continue
            #Continue
            elif x == '~' and hyphenCounter ==0:
                hyphenCounter += 1
                continue
            #Add value to version
            version += x
        
        #Break in this scenario
        elif x == ' ' and inVersion:
            return version
    
    #Break when string ends
    return version

def getOVMFPckgDate(version):
    '''
    From default OVMF package version, get corresponding commit date
    '''
    #Get the version in date format
    versionYear,versionMonth,versionDay = '','',''

    #Remove periods
    if "." in version:
        version = version.replace(".","")
    
    #Parse through the string, getting year first, then month, then day. if no day is given, assume 01.
    for x in version:
        if len(versionYear) < 4:
            versionYear += x
        elif len(versionMonth) < 2:
            versionMonth += x
        elif len(versionDay) < 2 and x.isdigit():
            versionDay += x
        elif len(versionDay) < 2 and not x.isdigit():
            versionDay = '01'
            break
        else:
            break
    
    if versionDay == '':
        versionDay = '01'

    #Put into date time format
    versionDate = datetime.date(int(versionYear), int(versionMonth), int(versionDay))
    
    #Return version
    return versionDate

def getDefaultOVMFPath(version):
    '''
    Get the path were the default version of OVMF (OVMF_VARS.fd or OVMF_VARS.bin) is stored for a given distro.
    Also get its version and version date.
    '''
    #Command list for given distro
    commandList = {'ubuntu':'dpkg --list', 'debian': 'dpkg --list', 'fedora': 'rpm -q edk2-ovmf', 'rhel': 'rpm -q edk2-ovmf', 
    'opensuse-tumbleweed': 'rpm -q ovmf', 'opensuse-leap': 'rpm -q qemu-ovmf-x86_64','centos':'rpm -q edk2-ovmf'}

    #Where the package will be stored
    defaultPath = None
    #date corresponding to the OVMF version
    versionDate = None

    #If distro not in the list use a default rpm -q edk2-ovmf command
    if version not in commandList:
        command = "rpm -q edk2-ovmf"
    else:
        command = commandList[version]

    #Find default package form distro
    ovmf = subprocess.run(" " + command + " | grep ovmf", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ovmfInstall = ovmf.stdout.decode("utf-8").strip()
    #Default package not found or not installed
    if not ovmfInstall or ovmfInstall == 'package ovmf is not installed':
        return command,None,None,None
    else:
        #Call to get default package version
        OVMFVersion = getOVMFVersion(ovmfInstall)
        #Call to get deafualt package commit date
        versionDate = getOVMFPckgDate(OVMFVersion)
        #If opensuse, expect the default OVMF file to be here
        if version == "opensuse-tumbleweed" or version == "opensuse-leap":
            defaultPath = '/usr/share/qemu/ovmf-x86_64-vars.bin'
        #Expect the default file to be here
        else:
            defaultPath = '/usr/share/OVMF/OVMF_VARS.fd'
    
    #Return results
    return command,defaultPath,OVMFVersion,versionDate

def compareOVMFVersion(versionDate,date):
    '''
    Compare version date with given minimum date for OVMF
    '''
    #Format min date into a daytime variable
    minYear,minMonth,minDay = date.split('-')
    minDate = datetime.date(int(minYear),int(minMonth),int(minDay))

    #Compare with given version date and return result
    if versionDate >= minDate:
        return True
    else:
        return False

def getBuiltPaths():
    '''
    Find manually built OVMF paths.
    '''
    #Paths found
    paths = []
    #Command to find all paths containing FV from root (if built from repository, it will contain this directory)
    pathsRaw = subprocess.run("find / type -d -name FV", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pathsDirty = pathsRaw.stdout.decode("utf-8").split('\n')
    pathsDirty.remove('')
    #Go through each found path
    for path in pathsDirty:
        #From found path, get path to OVMF_VARS.fd
        ovmfRaw = subprocess.run("find " + path + " -name OVMF_VARS.fd", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        ovmfPath = ovmfRaw.stdout.decode("utf-8").strip()
        #Ignore possible paths that do not contain OVMF
        if ovmfPath == '':
            continue
        #Put found paths into path list
        else:
            paths.append(ovmfPath)
    #Return paths
    return paths

def getCommitDate(path):
    '''
    Get the commit date for an externally built OVMF
    '''
    #Split the path string into a listh of files
    directory = path.split('/')
    directory.remove('')
    gitPath = '/'
    #Go through the directory
    for x in directory:
        #can use git command at path right before build, so we manually rebuild the path to that point.
        if x == 'Build':
            break
        else:
            gitPath += x
            gitPath += '/'
    
    #Command to get git summary, from which we can get the commit date
    gitDateRaw = subprocess.run("git --git-dir "+ gitPath +".git show --summary | grep Date", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    gitDate = gitDateRaw.stdout.decode("utf-8").strip()
    gitDate = sub(' +', ' ', gitDate)
    dateArray = gitDate.split(' ')
    
    #Get commit date as a date object with time
    datetime_object = datetime.datetime.strptime(dateArray[2], "%b")
    month_number = datetime_object.month

    #Get git commit date as day-month-year format for date
    versionDate = datetime.date(int(dateArray[5]), month_number, int(dateArray[3]))

    #return the git commit date as the version date
    return versionDate

def formatOVMFPath(rawPath):
    '''
    Format the path for display and testing
    '''
    editedPath = None
    directory = rawPath.split('/')
    if 'OVMF_VARS.fd' in directory:
        directory.remove('OVMF_VARS.fd')
    elif 'ovmf-x86_64-vars.bin' in directory:
        directory.remove('ovmf-x86_64-vars.bin')
    editedPath = '/'.join(directory)
    return editedPath

def getPathToOVMF(version):
    '''
    Find 1 working path to an OVMF file. Will return the 1st found path found that can support SEV. 
    '''
    #Will contain path to first working OVMF file found
    editedPath = None
    #Look for default path and version date of default path
    command, defaultPath, defaultVersion, defaultpckgInstallDate = getDefaultOVMFPath(version)
    
    #Default path found
    if defaultPath:
        #Default path meets minimum, return as working path
        if compareOVMFVersion(defaultpckgInstallDate,'2018-07-06'):
            editedPath = formatOVMFPath(defaultPath)
            return editedPath
    #Default path not found, look for build path
    builtPathList = getBuiltPaths()
    #Go through found built paths and look for one OVMF file that can run SEV
    for builtPath in builtPathList:    
        #Call to get commit date from given path
        ovmfCommitDate = getCommitDate(builtPath)
        #Call to compare path commit date with given minimum date for either SEV or SEV-ES
        if compareOVMFVersion(ovmfCommitDate, '2018-07-06'):
            editedPath = formatOVMFPath(builtPath)
            break
    
    return editedPath