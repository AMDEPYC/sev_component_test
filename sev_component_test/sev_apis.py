import fcntl
from ctypes import *
import struct
from enum import IntEnum
import ovmf_shared_functions

# constant for linux portability
_IOC_NRBITS = 8
_IOC_TYPEBITS = 8
# architecture specific
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
def _IOC(dir, type, nr, size):
    if isinstance(size, str):
        size = struct.calcsize(size)
    return dir  << _IOC_DIRSHIFT  | \
           type << _IOC_TYPESHIFT | \
           nr   << _IOC_NRSHIFT   | \
           size << _IOC_SIZESHIFT
def _IO(type, nr): return _IOC(_IOC_NONE, type, nr, 0)
def _IOR(type, nr, size): return _IOC(_IOC_READ, type, nr, size)
def _IOW(type, nr, size): return _IOC(_IOC_WRITE, type, nr, size)
def _IOWR(type, nr, size): return _IOC(_IOC_READ | _IOC_WRITE, type, nr, size)
class SEVCommand(IntEnum):
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

class SEV_issue_command(Structure):
    _pack_ = 1
    _fields_ = [('cmd', c_uint),
                ('data', c_ulong),
                ('error',c_uint)]

class SEV_platform_status(Structure):
    _pack_ = 1
    _fields_ = [('api_major', c_uint8),
                ('api_minor', c_uint8),
                ('state', c_uint8),
                ('owner', c_uint8, 1),
                ('reserved', c_uint8, 7),
                ('config_es',c_uint32, 1),
                ('reserved2', c_uint32, 23),
                ('build', c_uint32, 8),
                ('guest_count', c_uint32)]

class SEV_SNP_platform_status(Structure):
    _pack_ = 1
    _fields_ = [('api_major', c_uint8),
                ('api_minor', c_uint8),
                ('state', c_uint8),
                ('is_rmp_init', c_uint8, 1),
                ('reserved', c_uint8, 7),
                ('build_id', c_uint32),
                ('mask_chip_id', c_uint8, 1),
                ('reserved2', c_uint32, 31),
                ('guest_count', c_uint32),
                ('tcb_version', c_uint64),
                ('reported_tcb', c_uint64)]

SEV_IOC_TYPE: c_char = 'S'

SEV_ISSUE_CMD = _IOWR(ord('S'), 0x0, struct.calcsize('=IQI'))

def run_sev_platform_status():
    dev_sev: str = "/dev/sev"
    try:
        with open(dev_sev, 'wb') as fd:
            sev_data: SEV_platform_status = SEV_platform_status()
            sev_args: SEV_issue_command = SEV_issue_command(SEVCommand.SEV_PLATFORM_STATUS, addressof(sev_data))
            sev_ioctl_return = fcntl.ioctl(fd, SEV_ISSUE_CMD, sev_args)
            if sev_ioctl_return == 0:
                return sev_data
    except OSError as err:
        ovmf_shared_functions.print_warning_message("SEV_PLATFORM_STATUS", str(err))

def run_snp_platform_status():
    dev_sev: str = "/dev/sev"
    try:
        with open(dev_sev, 'wb') as fd:
            snp_data: SEV_SNP_platform_status = SEV_SNP_platform_status()
            snp_args: SEV_issue_command = SEV_issue_command(SEVCommand.SNP_PLATFORM_STATUS, addressof(snp_data))
            snp_ioctl_return = fcntl.ioctl(fd, SEV_ISSUE_CMD, snp_args)
            if snp_ioctl_return == 0:
                return snp_data
    except OSError as err:
        ovmf_shared_functions.print_warning_message("SNP_PLATFORM_STATUS", str(err))
