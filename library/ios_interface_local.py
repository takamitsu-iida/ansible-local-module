#!/usr/bin/python
# -*- coding: utf-8 -*-
# pylint: disable=C0111,E0611

# (c) 2018, Takamitsu IIDA (@takamitsu-iida)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ios_interface_local

short_description: IOS interface config generator

version_added: 2.6

description:
  - generate config from intent config and configured config

author:
  - Takamitsu IIDA (@takamitsu-iida)

notes:
  - Tested against CSR1000v 16.03.06

options:
  running_config:
    description:
      - show running-config output on the remote device
    required: True

  running_config_path:
    description:
      - file path to the running-config

  speed:
    description:
      - speed

  description:
    description:
      - description

  duplex:
    description:
      - duplex

  mtu:
    description:
      - mtu

  interfaces:
    description:
      - list of parameters
'''

EXAMPLES = '''
- name: playbook for module test
  hosts: localhost
  connection: local
  gather_facts: false

  vars:
    running_config: |
      !
      interface Loopback0
       ip address 192.168.254.1 255.255.255.255
      !
      interface GigabitEthernet1
       ip address dhcp
       negotiation auto
       no mop enabled
       no mop sysid
      !
      interface GigabitEthernet2
       ip address 172.20.0.21 255.255.0.0
       negotiation auto
       cdp enable
       no mop enabled
       no mop sysid
      !
      interface GigabitEthernet3
       ip address 33.33.33.33 255.255.255.0
       negotiation auto
       cdp enable
       no mop enabled
       no mop sysid
      !
      interface GigabitEthernet4
       ip address 44.44.44.44 255.255.255.0
       negotiation auto
       cdp enable
       no mop enabled
       no mop sysid
      !

    interfaces:
      - name: GigabitEthernet3
        enabled: true
        description: configured by ansible
        mtu: 1512

      - name: GigabitEthernet4
        enabled: true
        description:
        mtu:

      - name: Loopback0
        state: present
        description: configured by ansible

  tasks:

    #
    # TEST 1
    #

    - include_vars: vars/r1.yml

    - name: create config to be pushed
      ios_interface_local:
        running_config: "{{ running_config }}"
        interfaces: "{{ interfaces }}"
      register: r

    - name: TEST 1
      debug:
        var: r

    #
    # TEST 2
    #

    - name: create config to be pushed
      ios_interface_local:
        running_config: "{{ running_config }}"
        name: GigabitEthernet3
        description: configured by ansible
        mtu: 1492
      register: r

    - name: TEST 2
      debug:
        var: r

    #
    # TEST 3
    #

    - name: create config to be pushed
      ios_interface_local:
        running_config: "{{ running_config }}"
        description: configured by ansible
        aggregate:
          - name: GigabitEthernet3
          - name: GigabitEthernet4
      register: r

    - name: TEST 3
      debug:
        var: r

result

TASK [TEST 1]
ok: [localhost] => {
    "r": {
        "changed": false,
        "commands": [
            "interface GigabitEthernet3",
            "description configured by ansible",
            "mtu 1512",
            "interface Loopback0",
            "description configured by ansible"
        ],
        "failed": false
    }
}

TASK [TEST 2]
ok: [localhost] => {
    "r": {
        "changed": false,
        "commands": [
            "interface GigabitEthernet3",
            "description configured by ansible",
            "mtu 1492"
        ],
        "failed": false
    }
}

TASK [TEST 3]
ok: [localhost] => {
    "r": {
        "changed": false,
        "commands": [
            "interface GigabitEthernet3",
            "description configured by ansible",
            "interface GigabitEthernet4",
            "description configured by ansible"
        ],
        "failed": false
    }
}
'''

RETURN = '''
commands:
  description: The list of configuration mode commands to send to the remotedevice
  returned: always
  type: list
'''

from copy import deepcopy

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import remove_default_spec


def main():
  """main entry point for module execution
  """

  element_spec = dict(
    name=dict(),
    state=dict(choices=['present', 'absent']),
    description=dict(type='str'),
    negotiation=dict(type='str'),
    speed=dict(type='str'),
    duplex=dict(choices=['full', 'half', 'auto']),
    mtu=dict(type='int'),
    shutdown=dict(type='bool')
  )

  # list of interfaces
  aggregate_spec = deepcopy(element_spec)
  aggregate_spec['name'] = dict(required=True)

  # remove default in aggregate spec, to handle common arguments
  remove_default_spec(aggregate_spec)

  argument_spec = dict(
    aggregate=dict(type='list', elements='dict', options=aggregate_spec),
    interfaces=dict(type='list'),
    running_config=dict(type='str'),
    running_config_path=dict(type='path'),
    debug=dict(type='bool')
  )

  argument_spec.update(element_spec)

  required_one_of = [
    ('interfaces', 'name', 'aggregate'),
    ('running_config', 'running_config_path')
  ]

  mutually_exclusive = [
    ('name', 'aggregate'),
    ('running_config', 'running_config_path')
  ]

  module = AnsibleModule(
    argument_spec=argument_spec,
    required_one_of=required_one_of,
    mutually_exclusive=mutually_exclusive,
    supports_check_mode=True)

  result = {'changed': False}

  module.exit_json(**result)


if __name__ == '__main__':
  main()
