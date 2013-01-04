# Software License Agreement (BSD License)
#
# Copyright (c) 2012, Willow Garage, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Willow Garage, Inc. nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

"""
Checks to see if core Python scripts have:
1) Been installed
2) Have been installed via Debians on Ubuntu
3) Have not been installed via pip on Ubuntu
"""

from __future__ import print_function

import subprocess 
import importlib
import os

#A dictionary of core ROS python packages and their corresponding .deb packages
py_to_deb_packages = {'bloom': 'python-bloom',
                    'catkin': 'python-catkin',
                    'rospkg': 'python-rospkg',
                    'rosinstall': 'python-rosinstall',
                    'rosrelease': 'python-rosrelease',
                    'rosdep': 'python-rosdep',}

def get_host_os():
    """Determines the name of the host operating system"""
    import rospkg.os_detect
    os_detector = rospkg.os_detect.OsDetect()
    return (os_detector.detect_os())[0]

def is_host_os_ubuntu():
    """Indicates if the host operating system is Ubuntu"""
    return (get_host_os() == 'ubuntu')

def is_debian_package_installed(deb_pkg):
    """Uses dpkg to determine if a package has been installled"""
    return (subprocess.call('dpkg -l ' + deb_pkg, shell=True, stdout = open(os.devnull, 'w'), stderr = open(os.devnull, 'w')) == 0)

def is_a_pip_path_on_ubuntu(path):
    """Indicates if a path (either directory or file) is in the same place
    pip installs Python code"""
    return ('/usr/local' in path)

def is_python_package_installed(python_pkg):
    """Indicates if a Python package is importable in the current environment."""
    try:
        importlib.import_module(python_pkg)
        return True
    except ImportError:
        return False

def is_python_package_installed_via_pip_on_ubuntu(python_pkg):
    """Indicates if am importable package has been installed through pip on Ubuntu"""
    try:
        pkg_handle = importlib.import_module(python_pkg)
        return is_a_pip_path_on_ubuntu(pkg_handle.__file__)
    except ImportError:
        return False;
   
# Error/Warning Rules
def python_module_install_check(ctx):
    """Make sure core Python modules are installed"""
    warn_str = ''
    for py_pkg in py_to_deb_packages:
        if not is_python_package_installed(py_pkg):
            warn_str = warn_str + py_pkg + ' -- '
    if (warn_str != ''):
        return warn_str

def deb_install_check_on_ubuntu(ctx):
    """Make sure on Debian python packages are installed"""
    if (is_host_os_ubuntu()):
        warn_str = ''
        for py_pkg in py_to_deb_packages:
            deb_pkg = py_to_deb_packages[py_pkg]
            if not is_debian_package_installed(deb_pkg):
                warn_str = warn_str + py_pkg + ' (' + deb_pkg +  ') -- '
        if (warn_str != ''):
            return warn_str

def pip_install_check_on_ubuntu(ctx):
    """Make sure on Ubuntu, Python packages are install with apt and not pip"""
    if (is_host_os_ubuntu()):
        warn_str = ''
        for py_pkg in py_to_deb_packages:
            if is_python_package_installed_via_pip_on_ubuntu(py_pkg):
                warn_str = warn_str + py_pkg + ' -- '
        if (warn_str != ''):
            return warn_str

warnings = [
    (python_module_install_check, 
     "You are missing core ROS Python modules: "),
    (pip_install_check_on_ubuntu,
     "You have pip installed packages on Ubuntu, remove and install using Debian packages: "),
    (deb_install_check_on_ubuntu,
     "You are missing Debian packages for core ROS Python modules: "),
    ]

errors = []

def wtf_check(ctx):
    """Check implementation function for roswtf"""
    from roswtf.rules import warning_rule, error_rule
    for r in warnings:
        warning_rule(r, r[0](ctx), ctx)
    for r in errors:
        error_rule(r, r[0](ctx), ctx)



#Not used currently
###############################################################################
###############################################################################
###############################################################################
###############################################################################

def get_python_path_directories():
    """Gets all python path directories as a list"""
    return os.environ['PYTHONPATH'].split(os.pathsep)

def get_debian_package_version(deb_pkg):
    """Gets the Debian package version through dpkg"""
    pass

def print_table_line(python_pkg, deb_pkg, is_runnable, is_deb_installed, is_python_pkg_pip_installed):
    """prints a single line of the checks result table"""
    print('{0:15} | {1:20} | {2:15} | {3:15} | {4:15}'.format(python_pkg, \
                                            deb_pkg, \
                                            is_runnable, \
                                            is_deb_installed, \
                                            is_python_pkg_pip_installed))

def yes_or_no(bool_val):
    """Reinterprets a boolean as 'Yes' or 'No'"""
    if bool_val:
        return "Yes"
    else:
        return "No"

def check_and_print(python_pkg):
    """Runs a check for a single Python package and prints a table row with results"""
    deb_pkg = py_to_deb_packages[python_pkg]
    print_table_line(python_pkg, \
                     deb_pkg, \
                     yes_or_no(is_command_runnable(python_pkg)), \
                     yes_or_no(is_debian_package_installed(deb_pkg)), \
                     yes_or_no(is_python_package_installed_via_pip_on_ubuntu(python_pkg)))

def run_all_checks_and_print_table():
    """Prints a table of all the checks in the module"""
    print_table_line('Py Package', 'Deb Package', 'Runnable', 'Deb Installed', 'Installed Via Pip')
    print_table_line('----------', '-----------', '--------', '-------------', '-----------------')
    for key in py_to_deb_packages:
        check_and_print(key)

def is_command_runnable(cmd_name):
    """Indicates if a command is runnable on Unix/Linux"""
    try:
        rc = subprocess.call('command -v ' + cmd_name, shell=True, stdout = open(os.devnull, 'w'), stderr = open(os.devnull, 'w'))
        if(rc <= 0):
            return True
        else:
            return False
    except subprocess.CalledProcessError:        
        return False
