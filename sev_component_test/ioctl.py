'''
IOCTL function library to use platform status command.
'''
import fcntl
import ctypes
import struct
from enum import IntEnum
from message_printing import print_warning_message


# Defining constants for IOCTL functions
# Constant for linux portability
_IOC_NRBITS = 8
_IOC_TYPEBITS = 8
# Architecture specific
_IOC_SIZEBITS = 14
_IOC_DIRBITS = 2
_IOC_NRMASK = (1 << _IOC_NRBITS) - 1
_IOC_TYPEMASK = (1 << _IOC_TYPEBITS) - 1
_IOC_SIZEMASK = (1 << _IOC_SIZEBITS) - 1
_IOC_DIRMASK = (1 << _IOC_DIRBITS) - 1
_IOC_NRSHIFT = 0
_IOC_TYPESHIFT = _IOC_NRSHIFT + _IOC_NRBITS
_IOC_SIZESHIFT = _IOC_TYPESHIFT + _IOC_TYPEBITS
_IOC_DIRSHIFT = _IOC_SIZESHIFT + _IOC_SIZEBITS
_IOC_NONE = 0
_IOC_WRITE = 1
_IOC_READ = 2



def ioc(dir, type, nr, size):
    '''
    Python implementation of the _IOC macro from linux.
    It takes a set of parameters, and calculates a ioctl request number based on those parameters.
    '''
    if isinstance(size, str):
        size = struct.calcsize(size)
    return dir  << _IOC_DIRSHIFT  | \
           type << _IOC_TYPESHIFT | \
           nr   << _IOC_NRSHIFT   | \
           size << _IOC_SIZESHIFT

def iowr(type, nr, size):
    '''
    Python implementation of the ``_IOWR(...)`` macro from Linux.
    The ``_IOWR(...)`` macro calculates a ioctl request number for ioctl request that use
    the data for both reading (input) and writing (output).
    '''
    return ioc(_IOC_READ | _IOC_WRITE, type, nr, size)


class SEVCommand(IntEnum):
    '''
    SEV IOCTL commands
    '''
    SEV_FACTORY_RESET = 0
    SEV_PLATFORM_STATUS = 1
    SEV_PEK_GEN = 2
    SEV_PEK_CSR = 3
    SEV_PDH_GEN = 4
    SEV_PDH_CERT_EXPORT = 5
    SEV_PEK_CERT_IMPORT = 6
    SEV_GET_ID = 7    # This command is deprecated, use SEV_GET_ID2
    SEV_GET_ID2 = 8
    SNP_PLATFORM_STATUS = 9
    SNP_SET_EXT_CONFIG = 10
    SNP_GET_EXT_CONFIG = 11
    SEV_MAX = 12

class SEVIssueCommand(ctypes.Structure):
    '''
    Structure to issue SEV commands.
    '''
    _pack_ = 1
    _fields_ = [('cmd', ctypes.c_uint),
                ('data', ctypes.c_ulong),
                ('error', ctypes.c_uint)]

class SevPlatformStatus(ctypes.Structure):
    '''
    Structure for sev platform status
    '''
    _pack_ = 1
    _fields_ = [('api_major', ctypes.c_uint8),
                ('api_minor', ctypes.c_uint8),
                ('state', ctypes.c_uint8),
                ('owner', ctypes.c_uint8, 1),
                ('reserved', ctypes.c_uint8, 7),
                ('config_es', ctypes.c_uint32, 1),
                ('reserved2', ctypes.c_uint32, 23),
                ('build', ctypes.c_uint32, 8),
                ('guest_count', ctypes.c_uint32)]

class SevSnpPlatformSatus(ctypes.Structure):
    '''
    Structure for snp platform status
    '''
    _pack_ = 1
    _fields_ = [('api_major', ctypes.c_uint8),
                ('api_minor', ctypes.c_uint8),
                ('state', ctypes.c_uint8),
                ('is_rmp_init', ctypes.c_uint8, 1),
                ('reserved', ctypes.c_uint8, 7),
                ('build_id', ctypes.c_uint32),
                ('mask_chip_id', ctypes.c_uint8, 1),
                ('reserved2', ctypes.c_uint32, 31),
                ('guest_count', ctypes.c_uint32),
                ('tcb_version', ctypes.c_uint64),
                ('reported_tcb', ctypes.c_uint64)]

SEV_IOC_TYPE: ctypes.c_char = 'S'

SEV_ISSUE_CMD = iowr(ord('S'), 0x0, struct.calcsize('=IQI'))

def run_sev_platform_status():
    '''
    IOCTL call to the SEV_PLATFORM_STATUS api.
    Will return a SEV_platform_status structure with the current system's information.
    '''
    dev_sev: str = "/dev/sev"
    try:
        with open(dev_sev, 'wb') as fd:
            sev_data: SevPlatformStatus = SevPlatformStatus()
            sev_args: SEVIssueCommand = SEVIssueCommand(
                SEVCommand.SEV_PLATFORM_STATUS, ctypes.addressof(sev_data))
            sev_ioctl_return = fcntl.ioctl(fd, SEV_ISSUE_CMD, sev_args)
            if sev_ioctl_return == 0:
                return sev_data
    except OSError as err:
        print_warning_message("SEV_PLATFORM_STATUS", str(err))

def run_snp_platform_status():
    '''
    IOCTL call to the SNP_PLATFORM_STATUS abi.
    Will return a SNP_platform_status structure with the current system's information.
    '''
    dev_sev: str = "/dev/sev"
    try:
        with open(dev_sev, 'wb') as fd:
            snp_data: SevSnpPlatformSatus = SevSnpPlatformSatus()
            snp_args: SEVIssueCommand = SEVIssueCommand(
                SEVCommand.SNP_PLATFORM_STATUS, ctypes.addressof(snp_data))
            snp_ioctl_return = fcntl.ioctl(fd, SEV_ISSUE_CMD, snp_args)
            if snp_ioctl_return == 0:
                return snp_data
    except OSError as err:
        print_warning_message("SNP_PLATFORM_STATUS", str(err))
