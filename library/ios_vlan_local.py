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
module: ios_vlan_local

short_description: vlan config command generator for Cisco Catalyst

version_added: 2.6

description:
  - generate config command from intent config and configured config

notes:
  - Tested against Catalyst 3560G

options:

  running_config:
    description:
      - show running-config vlan output on the remote device
    required: True

  running_config_path:
    description:
      - file path to the running-config

  vlan_id:
    description:
      - ID of the VLAN. (1-4094)

  vlan_name:
    description:
      - Name of the VLAN.

  vlan_range:
    description:
      - Range of the vlan. (1-4094)

  vlans:
    description:
      - list of vlan parameters
    type: list

  state:
    description:
      - State of the VLAN configuration.
    default: present
    choices: ['present', 'absent']
'''

EXAMPLES = '''
- name: playbook for module test
  hosts: localhost
  connection: local
  gather_facts: false

  vars:
    running_config: |
      !
      vlan 2
       name inside
      !
      vlan 3
       name outside
      !
      vlan 4-9
      !

    vlans:
      - vlan_id: 2
        vlan_name: inside
        state: present
      - vlan_id: 3
        vlan_name: outside
        state: present
      - vlan_range: 4-9
        state: present
      - vlan_range: 10-4094
        state: absent

  tasks:
    - name: create config to be pushed
      ios_vlan_local:
        running_config: "{{ running_config }}"
        vlans: "{{ vlans }}"
      register: r

    - debug:
        var: r

'''

RETURN = '''
commands:
  description: The list of configuration mode commands to send to the remotedevice
  returned: always
  type: list
'''

from ansible.module_utils.basic import AnsibleModule


def main():
  """main entry point for module execution
  """

  argument_spec = dict(
    state=dict(default='present', choices=['present', 'absent']),
    vlan_id=dict(type='int'),
    vlan_range=dict(type='str'),
    vlan_name=dict(type='str'),
    vlans=dict(type='list'),
    running_config=dict(type='str'),
    running_config_path=dict(type='path'),
    debug=dict(type='bool')
  )

  required_one_of = [
    ('vlan_id', 'vlan_range', 'vlans'),
    ('running_config', 'running_config_path')
  ]

  mutually_exclusive = [
    ('vlan_id', 'vlan_range'),
    ('vlan_range', 'vlan_name'),
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
