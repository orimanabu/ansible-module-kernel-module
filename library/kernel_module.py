#!/usr/bin/python3

# Copyright: (c) 2021, Manabu Ori <ori@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: kernel_module

short_description: Load kernel module

version_added: "2.9"

description:
    - "Load kernel module."

options:
    name:
        description:
            - Kernel module name
        required: true
    state:
        description:
            - Whether to load (`installed` or `present`) or unload (`absent` or `removed`) the kernel module.
        required: false

author:
    - Manabu Ori (@orimanabu)
'''

EXAMPLES = '''
# Load
- name: Load vxlan kernel module
  kernel_module:
    name: vxlan
    state: present

# Unload
- name: Unload vxlan kernel module
  kernel_module:
    name: vxlan
    state: absent
'''

RETURN = '''
message:
    description: The output message
    type: str
    returned: always
'''

import subprocess
from subprocess import PIPE

from ansible.module_utils.basic import AnsibleModule

def kernel_module_check(kmod):
    cmd = "/usr/sbin/lsmod | grep ^{kmod}".format(kmod=kmod)
    proc = subprocess.run(cmd, shell=True, stdout=PIPE, stderr=PIPE, text=True)
    return proc.returncode, proc.stdout, proc.stderr, cmd

def kernel_module_load(kmod, do_load):
    option = ""
    if not do_load:
        option = "-r"
    cmd = "/usr/sbin/modprobe {option} {kmod}".format(option=option, kmod=kmod)
    proc = subprocess.run(cmd, shell=True, stdout=PIPE, stderr=PIPE, text=True)
    return proc.returncode, proc.stdout, proc.stderr, cmd

def run_module():
    module_args = dict(
        name=dict(type='str', required=True),
        state=dict(type='str', default="present", choices=['absent', 'installed', 'present', 'removed']),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    rc, stdout, stderr, cmdline = kernel_module_check(module.params['name'])
    result = dict(
        changed=False if rc == 0 else True,
        cmdline=cmdline,
        cmd_stdout=stdout,
        cmd_stderr=stderr,
        message='',
    )
    if rc == 0:
        result['message'] = "module `{kmod}` is already loaded.".format(kmod=module.params['name'])
    else:
        result['message'] = "module `{kmod}` is not loaded.".format(kmod=module.params['name'])

    do_load = True
    if module.params['state'] in ('installed', 'present'):
        result['changed'] = False if rc == 0 else True
        do_load = True
    elif module.params['state'] in ('absent', 'removed'):
        result['changed'] = True if rc == 0 else False
        do_load = False
    else:
        module.fail_json(
            changed=False,
            cmd_stdout='',
            cmd_stderr='',
            message="we should never get here unless this all failed",
        )

    if module.check_mode:
        module.exit_json(**result)

    if not result['changed']:
        module.exit_json(**result)

    rc, stdout, stderr, cmdline = kernel_module_load(module.params['name'], do_load)
    if rc != 0:
        module.fail_json(
            changed=False,
            cmdline=cmdline,
            cmd_stdout=stdout,
            cmd_stderr=stderr,
            message="Kernel module {subcmd} failed.".format(subcmd="loading" if do_load else "unloading")
        )

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
