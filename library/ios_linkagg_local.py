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
module: ios_linkagg_local

short_description: IOS link aggregation config generator

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
    required: True

  group:
    description:
      - channel group number for the port-channel.
    type: int

  mode:
    description:
      - mode for the link aggregation group.
    choices: ['active', 'on', 'passive', 'auto', 'desirable']

  members:
    description:
      - list of interfaces that will be managed in the link aggregation group.
    type: list

  state:
    description:
      - state of the link aggregation group.
    default: present
    choices: ['present', 'absent']
'''

EXAMPLES = '''
---

- name: playbook for module test
  hosts: localhost
  connection: local
  gather_facts: false

  vars:
    running_config: |
      vlan 10,20,30
      no spannning-tree vlan 10,20,30

      interface GigabitEthernet0/27
       channel-group 1 mode on

      interface GigabitEthernet0/28
       channel-group 1 mode on

      interface Port-channel1
       switchport trunk encapsulation dot1q
       switchport trunk allowed vlan 10,20,30
       switchport mode trunk


  tasks:

    #
    # TEST 1
    #

    - name: create config to be pushed
      ios_linkagg_local:
        running_config: "{{ running_config }}"
        port_channels: "{{ port_channels }}"
        state: present
        debug: true
      register: r

      vars:
        port_channels:
          - group: 1
            mode: active
            members:
              - GigabitEthernet0/27
              - GigabitEthernet0/28

    - name: TEST 1
      debug:
        var: r

'''

RETURN = '''
commands:
  description: The list of configuration mode commands to send to the remotedevice
  returned: always
  type: list
  sample:
'''

# 本家はモードの変更を考慮していないので、モード変更に対応

from copy import deepcopy

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import remove_default_spec


def main():
  """main entry point for module execution
  """

  element_spec = dict(
    state=dict(default='present', choices=['present', 'absent']),
    group=dict(type='int'),
    mode=dict(choices=['active', 'on', 'passive', 'auto', 'desirable']),
    members=dict(type='list')
  )

  # list of interfaces
  aggregate_spec = deepcopy(element_spec)
  aggregate_spec['group'] = dict(required=True)

  # remove default in aggregate spec, to handle common arguments
  remove_default_spec(aggregate_spec)

  required_together = [
    ('members', 'mode')
  ]

  argument_spec = dict(
    aggregate=dict(type='list', elements='dict', options=aggregate_spec, required_together=required_together),
    purge=dict(default=False, type='bool'),
    port_channels=dict(type='list'),
    running_config=dict(type='str'),
    running_config_path=dict(type='path'),
    debug=dict(default=False, types='bool')
  )

  argument_spec.update(element_spec)

  required_one_of = [
    ('group', 'aggregate', 'port_channels')
  ]

  mutually_exclusive = [
    ('group', 'aggregate')
  ]

  module = AnsibleModule(
    argument_spec=argument_spec,
    required_one_of=required_one_of,
    mutually_exclusive=mutually_exclusive,
    supports_check_mode=True
  )

  result = {'changed': False}

  module.exit_json(**result)


if __name__ == '__main__':
  main()
