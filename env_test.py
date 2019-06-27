#!/usr/bin/env python3

import os
import sys

# Functions and references for testing

def workaround(msg):
    workarounds.append(msg)
    print('WORKAROUND: ' + msg)

def warn(msg):
    warnings.append(msg)
    print('WARNING: ' + msg)

def error(msg):
    sys.stderr.write(msg)

def fatal(msg, code=1):
    error('FATAL: {}'.format(msg))
    exit(code)

def print_exception(ex):
    error('An unknown exception occured, detailed as follows:')
    error('{e.__class__}: {e}'.format(e=ex))

def path_find_or_workaround(dir):
    path = os.environ['PATH'].split(':')
    if dir not in path:
        path.append(dir)
        os.environ['PATH'] = ':'.join(path)
        workaround('Append {} to $PATH.')

def exec_with_popen(*args):
    child = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = child.communicate()
    return (child.returncode, stdout, stderr)

def exec_with_run(*args):
    ret = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if ret.stdout is None:
        stdout = None
    else:
        stdout = ret.stdout.decode("utf-8")
    if ret.stderr is None:
        stderr = None
    else:
        stderr = ret.stderr.decode("utf-8")
    return (ret.returncode, stdout, stderr)

def which_a(bin):
    ret, stdout, _ = fork_and_exec('which', '-a', bin)
    executables = []
    real_executables = []
    if ret == 0:
        executables = stdout.split('\n')
        # remove the empty line
        executables.pop()
    # generate symlink traces
    def trace_symlink(path):
        trace = [path]
        while os.path.islink(path):
            target = os.readlink(path)
            target = os.path.join(os.path.dirname(path), target)
            target = os.path.normpath(target)
            trace.append(target)
            path = target
        trace = '->'.join(trace)
        # make sure we count real executables correctly
        if path not in real_executables:
            real_executables.append(path)
        return trace
    executables = list(map(trace_symlink, executables))
    if len(real_executables) == 0:
        results[bin] = False
        warn('{} not found.'.format(bin))
    elif len(real_executables) == 1:
        results[bin] = True
        print('{} found at {}.'.format(bin, executables))
        print('The real executable is {}.'.format(real_executables[0]))
        print('--------------')
    else:
        results[bin] = True
        warn('{} found multiple times at {}.'.format(bin, executables))
        print('--------------')

def try_run(bin, *args):
    ret, stdout, _ = fork_and_exec(bin, *args)
    if ret == 0:
        print(stdout)
    else:
        warn('{} does not respond to {} as expected.'.format(bin, ' '.join(args)))
        print('')
    return (ret == 0)

fork_and_exec = None
results = dict()
warnings = []
workarounds = []

# Test logic

# Banner
print('Menhera Runtime Test')
print('====================')
print('')

# Interpreter Version
print('Python version string\t: {}'.format(sys.version))
print(
    'Python version struct\t: major={v.major}, minor={v.minor}, micro={v.micro}, relese={v.releaselevel}, serial={v.serial}'
        .format(v=sys.version_info)
)
print('')

# Subprocess Module
# Test features
try:
    # Import
    import subprocess
    # Call
    child = subprocess.Popen('/bin/true')
    child.communicate()
    results['subprocess'] = True
except ImportError as err:
    error('Subprocess module failed upon import. Details below:')
    error(err)
    fatal('Cannot use python as shell. Aborting.')
except AttributeError as err:
    missing_attr = str(err).split()[5]
    error('Subprocess module has an attribute {} missing.'.format(missing_attr))
    fatal('Cannot use python as shell. Aborting.')
except Exception as ex:
    print_exception(ex)
    fatal('Cannot use python as shell. Aborting.')
# Apply workaround iff needed
try:
    subprocess.run('/bin/true')
    fork_and_exec = exec_with_run
except AttributeError:
    fork_and_exec = exec_with_popen
    workaround('Using subprocess.Popen() in fork_and_exec() because subprocess.run() is missing.')
# Test actual functionalities
try:
    print('Test: Exec returning zero.')
    ret, _, _ = fork_and_exec('/bin/true')
    assert ret == 0
    print('Test: Exec returning non-zero.')
    ret, _, _ = fork_and_exec('/bin/false')
    assert ret == 1
    print('Test: Exec writing to stdout.')
    _, stdout, _ = fork_and_exec('/bin/echo', '-n', 'HELLO')
    assert stdout =='HELLO'
    print('Test: Exec writing to stderr.')
    _, _, stderr = fork_and_exec('/bin/sh', '-c', 'printf HELLO>&2')
    assert stderr =='HELLO'
except Exception as ex:
    print_exception(ex)
    fatal('Critical test failed. Does not trust python as shell. Aborting.')
# Conclusion
print('Subprocess module valid.')
print('')

# $PATH
print('Before workarounds: $PATH={}'.format(os.environ['PATH']))
list(map(path_find_or_workaround, [
    '/usr/local/sbin',
    '/usr/local/bin',
    '/usr/sbin',
    '/usr/bin',
    '/sbin',
    '/bin'
]))
results['path'] = True
print('After workarounds: $PATH={}'.format(os.environ['PATH']))
print('$PATH sane.')
print('')

# System executables

# which
which_a('which')
if results['which']:
    # Some versions of 'which' does not support version reporting
    # It should work just fine because 'which which' is working
    # A warning is emitted
    try_run('which', '--version')

# curl
which_a('curl')
if results['curl']:
    results['curl'] = try_run('curl', '--version')

# sync
which_a('sync')
if results['sync']:
    results['sync'] = try_run('sync', '--version')

# modprobe
which_a('modprobe')
if results['modprobe']:
    results['modprobe'] = try_run('modprobe', '--version')

# sysctl
which_a('sysctl')
if results['sysctl']:
    results['sysctl'] = try_run('sysctl', '--version')

# mkdir
which_a('mkdir')
if results['mkdir']:
    results['mkdir'] = try_run('mkdir', '--version')

# mount
which_a('mount')
if results['mount']:
    results['mount'] = try_run('mount', '--version')

# cp
which_a('cp')
if results['cp']:
    results['cp'] = try_run('cp', '--version')

# chroot
which_a('chroot')
if results['chroot']:
    results['chroot'] = try_run('chroot', '--version')

# systemctl
which_a('systemctl')
if results['systemctl']:
    results['systemctl'] = try_run('systemctl', '--version')

# service
which_a('service')
if results['service']:
    results['service'] = try_run('service', '--version')
if not results['systemctl']:
    if results['service']:
        workaround('Using service instead of systemctl.')
    else:
        fatal('No supported service control system found.')

# telinit
which_a('telinit')
# telinit does not support dry run (which is expected), skipping
print('Cannot report version of telinit because it does not have such functionality.')
print('This is NOT a warning.')
print('')
if not results['systemctl']:
    if results['telinit']:
        workaround('Using telinit instead of systemctl.')
    else:
        fatal('No supported runlevel control system found.')

# Summary

print('==============')
print('')

if len(workarounds) > 0:
    print('SUMMARY OF WORKAROUNDS:')
    for i in workarounds:
        print(i)
        print('')

if len(warnings) > 0:
    print('SUMMARY OF WARNINGS:')
    for i in warnings:
        print(i)
    print('')
    print('CONCLUSION: Runtime MAY be sane. Check logs.')
else:
    print('CONCLUSION: Runtime SHOULD be sane. We still recommend checking logs.')

