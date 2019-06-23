#!/usr/bin/env python3

import os
import sys

# Functions and references for testing

def print_exception(ex):
    print('An unknown exception occured, detailed as follows:')
    print('{e.__class__}: {e}'.format(e=ex))

def path_find_or_workaround(dir):
    path = os.environ['PATH'].split(':')
    if dir not in path:
        path.append(dir)
        os.environ['PATH'] = ':'.join(path)
        print('Workaround: Appending {} to $PATH'.format(dir))

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
    if ret != 0:
        executables = []
    else:
        executables = stdout.split('\n')
        executables.pop()
    if len(executables) == 0:
        results[bin] = False
        print('{} invalid.'.format(bin))
    elif len(executables) == 1:
        results[bin] = True
        print('{} valid at {}'.format(bin, executables[0]))
        print('--------------')
    else:
        results[bin] = True
        warning = '{} is found multiple times at {}.'.format(bin, executables)
        warnings.append(warning)
        print(warning)
        print('--------------')

def try_run(bin, *args):
    ret, stdout, _ = fork_and_exec(bin, *args)
    if ret == 0:
        print(stdout)
    else:
        results[bin] = False
        print('{} does not function as expected.'.format(bin))
        print('')

fork_and_exec = None
results = dict()
warnings = []

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
    print('Subprocess module failed upon import. Details below:')
    print(err)
    results['subprocess'] = False
except AttributeError as err:
    missing_attr = str(err).split()[5]
    print('Subprocess module has an attribute {} missing.'.format(missing_attr))
    results['subprocess'] = False
except Exception as ex:
    print_exception(ex)
    results['subprocess'] = False
# Apply workarounds
if results['subprocess']:
    # Run
    try:
        subprocess.run('/bin/true')
        fork_and_exec = exec_with_run
    except AttributeError:
        fork_and_exec = exec_with_popen
        print("Workaround: Using 'Popen' as 'fork_and_exec' because 'run' is missing.")
# Test actual functionalities
if results['subprocess']:
    # Exec, returning zero
    print('Test: Exec returning zero.')
    try:
        ret, _, _ = fork_and_exec('/bin/true')
        assert ret == 0
    except Exception as ex:
        print_exception(ex)
        results['subprocess'] = False
    # Exec, returning non-zero
    print('Test: Exec returning non-zero.')
    try:
        ret, _, _ = fork_and_exec('/bin/false')
        assert ret == 1
    except Exception as exception:
        print_exception(exception)
        results['subprocess'] = False
    # Exec, writing to stdout
    print('Test: Exec writing to stdout.')
    try:
        _, stdout, _ = fork_and_exec('/bin/echo', '-n', 'HELLO')
        assert stdout =='HELLO'
    except Exception as exception:
        print_exception(exception)
        results['subprocess'] = False
    # Exec, writing to stderr
    print('Test: Exec writing to stderr.')
    try:
        _, _, stderr = fork_and_exec('/bin/sh', '-c', 'printf HELLO>&2')
        assert stderr =='HELLO'
    except Exception as exception:
        print_exception(exception)
        results['subprocess'] = False
# Conclusion
if results['subprocess']:
    print('Subprocess module valid.')
else:
    print('Subprocess module missing or unusable.')
    print('Built-in workarounds did not help.')
    print('Further tests MAY have been skipped.')
print('')

# $PATH
path_find_or_workaround('/usr/local/sbin')
path_find_or_workaround('/usr/local/bin')
path_find_or_workaround('/usr/sbin')
path_find_or_workaround('/usr/bin')
path_find_or_workaround('/sbin')
path_find_or_workaround('/bin')
results['path'] = True
print('$PATH valid.')
print('')

# System executables

# which
which_a('which')
if results['which']:
    try_run('which', '--version')

# curl
which_a('curl')
if results['curl']:
    try_run('curl', '--version')

# sync
which_a('sync')
if results['sync']:
    try_run('sync', '--version')

# modprobe
which_a('modprobe')
if results['modprobe']:
    try_run('modprobe', '--version')

# sysctl
which_a('sysctl')
if results['sysctl']:
    try_run('sysctl', '--version')

# mkdir
which_a('mkdir')
if results['mkdir']:
    try_run('mkdir', '--version')

# mount
which_a('mount')
if results['mount']:
    try_run('mount', '--version')

# cp
which_a('cp')
if results['cp']:
    try_run('cp', '--version')

# chroot
which_a('chroot')
if results['chroot']:
    try_run('chroot', '--version')

# systemctl
which_a('systemctl')
if results['systemctl']:
    try_run('systemctl', '--version')

# service
which_a('service')
if results['service']:
    try_run('service', '--version')

# telinit
which_a('telinit')
if results['telinit']:
    print('telinit does not support dry run (which is expected), skipping.')
    print('')
