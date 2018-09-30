# -*- coding: utf-8 -*-
# pylint: disable=E0611,C0111
# E0611:No name 'urllib' in module '_MovedItems'
# C0111:Missing class docstring
# C0412:Imports from package ansible are not grouped

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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import re

from ansible.plugins.action.normal import ActionModule as _ActionModule
from ansible.module_utils._text import to_text
from ansible.module_utils.six.moves.urllib.parse import urlsplit
from ansible.module_utils.network.common.config import NetworkConfig
from ansible.module_utils.network.common.utils import is_netmask, is_masklen, to_netmask, to_masklen

try:
  # pylint: disable=W0611
  # W0611:Unused display imported from __main__
  from __main__ import display
except ImportError:
  # pylint: disable=C0412
  # C0412:Imports from package ansible are not grouped
  from ansible.utils.display import Display
  display = Display()


class ActionModule(_ActionModule):

  supported_params = ('ipv4', 'ipv4_secondary', 'ipv6', 'purge')


  def validate_ipv4(self, want):
    key = 'ipv4'
    value = want.get(key)
    if value:
      return self._validate_ipv4_prefix(value)


  def validate_ipv4_secondary(self, want):
    key = 'ipv4_secondary'
    value = want.get(key)
    if value:
      if isinstance(value, str):
        value = list(value)
        want[key] = value

      for prefix in value:
        msg = self._validate_ipv4_prefix(prefix)
        if msg:
          return msg


  def _validate_ipv4_prefix(self, prefix):
    items = prefix.split('/')
    if len(items) != 2:
      return 'address format is <ipv4 address>/<mask>, invalid format {}'.format(prefix)
    if not is_masklen(items[1]):
      return 'invalid value for mask: {}, mask should be in range 0-32'.format(prefix)


  def validate_ipv6(self, want):
    key = 'ipv6'
    value = want.get(key)
    if value:
      address = value.split('/')
      if len(address) != 2:
        return 'address format is <ipv6 address>/<mask>, invalid format {}'.format(value)
      else:
        if not 0 <= int(address[1]) <= 128:
          return 'invalid value for mask: {}, mask should be in range 0-128'.format(address[1])


  def validate(self, want_list):
    for want in want_list:
      # presentのときのみ検証する
      state = want.get('state')
      if state != 'present':
        continue

      # 存在するキーについてのみvaludate_key()を実行する
      for key in want.keys():
        func_name = 'validate_{}'.format(key)
        validator = getattr(self, func_name, None)
        if callable(validator):
          # pylint: disable=E1102
          msg = validator(want)
          if msg:
            return msg


  @staticmethod
  def search_obj_in_list(name, lst):
    for o in lst:
      if o['name'] == name:
        return o
    return None


  @staticmethod
  def parse_config_argument(configobj, name, arg=None):

    parent = 'interface {}'.format(name)

    cfg = configobj[parent]
    cfg = '\n'.join(cfg.children)

    values = []
    matches = re.finditer(r'{} (.+)$'.format(arg), cfg, re.M)
    for match in matches:
      match_str = match.group(1).strip()
      values.append(match_str)

    return values


  def map_config_to_obj(self, config):
    results = []

    match = re.findall(r'^interface\s+(\S+)', config, re.M)
    if not match:
      return results

    configobj = NetworkConfig(indent=1, contents=config)

    for intf_name in set(match):
      obj = {
        'state': 'present',
        'name': intf_name
      }

      # ip addressで始まっている設定コマンドをリスト化する
      # これにはsecondaryも含まれる
      #  ip address 3.3.3.3 255.255.255.0
      #  ip address 33.33.33.33 255.255.255.0 secondary
      cmds = self.parse_config_argument(configobj, intf_name, 'ip address')

      ipv4 = None
      secondary_list = []
      for cmd in cmds:
        tokens = cmd.strip().split(' ')
        if len(tokens) >= 2 and is_netmask(tokens[1]):
          prefix = '{0}/{1}'.format(tokens[0], to_text(to_masklen(tokens[1])))
          is_secondary = bool(len(tokens) == 3 and tokens[2] == 'secondary')
          if is_secondary:
            secondary_list.append(prefix)
          else:
            ipv4 = prefix

      obj['ipv4'] = ipv4
      obj['ipv4_secondary'] = secondary_list

      ipv6_list = self.parse_config_argument(configobj, intf_name, 'ipv6 address')
      obj['ipv6'] = ipv6_list

      results.append(obj)

    return results


  def args_to_obj(self, args):
    obj = {}
    for p in self.supported_params:
      # そのパラメータが入力したYAMLにある場合だけwantに取り込む
      if p in args:
        obj[p] = args.get(p)

    # stateは設定されていない場合'present'の扱いにする
    obj['state'] = args.get('state', 'present')

    return obj


  def map_params_to_obj(self):
    results = []

    # パラメータの一覧を渡された場合
    interfaces = self._task.args.get('interfaces')
    if interfaces and isinstance(interfaces, list):
      for item in interfaces:
        intf_name = item.get('name')
        if intf_name:
          obj = self.args_to_obj(item)
          obj['name'] = intf_name
          results.append(obj)
      return results

    # aggregateが渡された場合
    aggregate = self._task.args.get('aggregate')
    if aggregate and isinstance(aggregate, list):
      for item in aggregate:
        # _task.argsを使ってオブジェクトを作成してからaggregateの内容を追記する
        obj = self.args_to_obj(self._task.args)
        obj.update(item)
        results.append(obj)
      return results

    # パラメータだけが指定された場合
    obj = self.args_to_obj(self._task.args)
    obj['name'] = self._task.args.get('name')
    results.append(obj)

    return results

  #
  # メモ
  # absent_XXX(want, have)
  #  haveは必ず存在する
  #  wantにXXXキーは存在する
  #

  def absent_ipv4(self, want, have):
    commands = []

    key = 'ipv4'
    want_ipv4 = want.get(key)
    have_ipv4 = have.get(key)

    if not want_ipv4 and not have_ipv4:
      pass
    elif not want_ipv4 and have_ipv4:
      # キーは存在するので、
      # ipv4:
      # という、空文字列で指定されたということ。
      # この場合は、ipv4アドレスを消したい、という意味だと捉えて設定されているアドレスを消す
      tokens = have_ipv4.split('/')
      ipv4 = '{0} {1}'.format(tokens[0], to_netmask(tokens[1]))
      commands.append('no ip address {}'.format(ipv4))
    elif want_ipv4 and not have_ipv4:
      pass
    elif want_ipv4 and have_ipv4:
      if want_ipv4 == have_ipv4:
        # 同じものが設定されているそれを消す
        tokens = have_ipv4.split('/')
        if len(tokens) == 2:
          ipv4 = '{0} {1}'.format(tokens[0], to_netmask(tokens[1]))
          commands.append('no ip address {}'.format(ipv4))
      else:
        # 指定されたものとは違うものが設定されている。それを消すかどうかだけど・・・ここでは消さない
        pass

    return commands

  #
  # メモ
  # present_XXX(want, have)
  #  haveは存在する
  #  wantにXXXキーは存在する
  #

  def present_ipv4(self, want, have):
    commands = []

    key = 'ipv4'
    want_ipv4 = want.get(key)
    have_ipv4 = have.get(key)

    if not want_ipv4 and not have_ipv4:
      pass
    elif not want_ipv4 and have_ipv4:
      # キーは存在するので、
      # ipv4:
      # という、空文字列で指定されたということ。
      # この場合は、ipv4アドレスを空っぽの状態にしたい、という意味だと捉えて設定されているアドレスを消す
      tokens = have_ipv4.split('/')
      ipv4 = '{0} {1}'.format(tokens[0], to_netmask(tokens[1]))
      commands.append('no ip address {}'.format(ipv4))
    elif want_ipv4 and not have_ipv4:
      # 新規にアドレスを設定
      tokens = want_ipv4.split('/')
      ipv4 = '{0} {1}'.format(tokens[0], to_netmask(tokens[1]))
      commands.append('ip address {}'.format(ipv4))
    elif want_ipv4 and have_ipv4:
      if want_ipv4 == have_ipv4:
        # 同じものが設定されているなら何もしない
        pass
      else:
        # 安全のため既存の設定をnoで削除してから新規でアドレスを設定する
        tokens = have_ipv4.split('/')
        if len(tokens) == 2:
          ipv4 = '{0} {1}'.format(tokens[0], to_netmask(tokens[1]))
          commands.append('no ip address {}'.format(ipv4))
        tokens = want_ipv4.split('/')
        if len(tokens) == 2:
          ipv4 = '{0} {1}'.format(tokens[0], to_netmask(tokens[1]))
          commands.append('ip address {}'.format(ipv4))

    return commands


  def absent_ipv4_secondary(self, want, have):
    commands = []

    key = 'ipv4_secondary'
    want_secondary = want.get(key)
    have_secondary = have.get(key)

    if not want_secondary and not have_secondary:
      pass
    elif not want_secondary and have_secondary:
      # キーは存在するので、
      # ipv4_secondary:
      # という、空文字列で指定されたということ。
      # この場合は、セカンダリアドレスを全て消したい、という意味だと捉えて設定されているアドレスを消す
      for prefix in have_secondary:
        tokens = prefix.split('/')
        if len(tokens) == 2:
          ipv4 = '{0} {1}'.format(tokens[0], to_netmask(tokens[1]))
          commands.append('no ip address {} secondary'.format(ipv4))
    elif want_secondary and not have_secondary:
      pass
    elif want_secondary and have_secondary:
      superfluous = set(have_secondary).difference(set(want_secondary))
      for prefix in superfluous:
        tokens = prefix.split('/')
        if len(tokens) == 2:
          ipv4 = '{0} {1}'.format(tokens[0], to_netmask(tokens[1]))
          commands.append('no ip address {} secondary'.format(ipv4))

    return commands


  def present_ipv4_secondary(self, want, have):
    commands = []

    key = 'ipv4_secondary'
    want_secondary = want.get(key)
    have_secondary = have.get(key)

    if not want_secondary and not have_secondary:
      pass
    elif not want_secondary and have_secondary:
      # キーは存在するので、
      # ipv4_secondary:
      # という、空文字列で指定されたということ。
      # この場合は、セカンダリアドレスを存在しない状態にしたい、という意味だと捉えて設定されているアドレスを消す
      for prefix in have_secondary:
        tokens = prefix.split('/')
        if len(tokens) == 2:
          ipv4 = '{0} {1}'.format(tokens[0], to_netmask(tokens[1]))
          commands.append('no ip address {} secondary'.format(ipv4))
    elif want_secondary and not have_secondary:
      # 新規にセカンダリアドレスを設定
      for prefix in want_secondary:
        tokens = prefix.split('/')
        ipv4 = '{0} {1}'.format(tokens[0], to_netmask(tokens[1]))
        commands.append('ip address {} secondary'.format(ipv4))
    elif want_secondary and have_secondary:
      # 不足する分を追加で設定する
      missing = set(want_secondary).difference(set(have_secondary))
      for prefix in missing:
        tokens = prefix.split('/')
        if len(tokens) == 2:
          ipv4 = '{0} {1}'.format(tokens[0], to_netmask(tokens[1]))
          commands.append('ip address {} secondary'.format(ipv4))

      if want.get('purge') is True:
        # 余分なものはpurgeする
        superfluous = set(have_secondary).difference(set(want_secondary))
        for prefix in superfluous:
          tokens = prefix.split('/')
          if len(tokens) == 2:
            ipv4 = '{0} {1}'.format(tokens[0], to_netmask(tokens[1]))
            commands.append('no ip address {} secondary'.format(ipv4))

    return commands


  def absent_ipv6(self, want, have):
    commands = []

    key = 'ipv6'
    want_ipv6 = want.get(key)
    have_ipv6 = have.get(key)

    if not want_ipv6 and not have_ipv6:
      pass
    elif not want_ipv6 and have_ipv6:
      # キーは存在するので、
      # ipv6:
      # という、空文字列で指定されたということ。
      # この場合は、IPv6アドレスを全て消したい、という意味だと捉えて設定されているアドレスを消す
      for ipv6 in have_ipv6:
        commands.append('no ipv6 address {}'.format(ipv6))
    elif want_ipv6 and not have_ipv6:
      pass
    elif want_ipv6 and have_ipv6:
      superfluous = set(have_ipv6).difference(set(want_ipv6))
      for ipv6 in superfluous:
        commands.append('no ipv6 address {}'.format(ipv6))

    return commands


  def present_ipv6(self, want, have):
    commands = []

    key = 'ipv6'
    want_ipv6 = want.get(key)
    have_ipv6 = have.get(key)

    if not want_ipv6 and not have_ipv6:
      pass
    elif not want_ipv6 and have_ipv6:
      # キーは存在するので、
      # ipv6:
      # という、空文字列で指定されたということ。
      # この場合は、IPv6アドレスを全て消したい、という意味だと捉えて設定されているアドレスを消す
      for ipv6 in have_ipv6:
        commands.append('no ipv6 address {}'.format(ipv6))
    elif want_ipv6 and not have_ipv6:
      pass
    elif want_ipv6 and have_ipv6:
      missing = set(want_ipv6).difference(set(have_ipv6))
      for ipv6 in missing:
        commands.append('ipv6 address {}'.format(ipv6))
      if want.get('purge') is True:
        superfluous = set(have_ipv6).difference(set(want_ipv6))
        for ipv6 in superfluous:
          commands.append('no ipv6 address {}'.format(ipv6))

    return commands


  def to_commands_absent(self, want, have):

    commands = []

    for p in self.supported_params:
      # wantにキーがある場合、すなわちYAMLでパラメータが書かれているときだけ
      if p in want:
        func_name = 'absent_{}'.format(p)
        func = getattr(self, func_name, None)
        if callable(func):
          # pylint: disable=E1102
          cmds = func(want, have)
          if cmds:
            commands.extend(cmds)

    return commands


  def to_commands_present(self, want, have):

    commands = []

    for p in self.supported_params:
      # wantにキーがある場合、すなわちYAMLでパラメータが書かれているときだけ
      if p in want:
        func_name = 'present_{}'.format(p)
        func = getattr(self, func_name, None)
        if callable(func):
          # pylint: disable=E1102
          cmds = func(want, have)
          if cmds:
            commands.extend(cmds)

    return commands


  def to_commands(self, want, have):

    commands = []

    intf_name = want.get('name')
    state = want.get('state')

    # 'interface GigabitEthernet1'
    interface = 'interface {}'.format(intf_name)
    commands.append(interface)

    if state == 'absent':
      cmds = self.to_commands_absent(want, have)
      if cmds:
        commands.extend(cmds)

    if state == 'present':
      cmds = self.to_commands_present(want, have)
      if cmds:
        commands.extend(cmds)

    if commands[-1] == interface:
      commands.pop(-1)

    return commands


  def to_commands_list(self, want_list, have_list):
    commands = []

    for want in want_list:
      name = want.get('name')
      have = self.search_obj_in_list(name, have_list)

      # 対象となるインタフェースが存在するときだけ実行
      if have:
        cmds = self.to_commands(want, have)
        if cmds:
          commands.extend(cmds)

    return commands


  def _handle_template(self, key_path):
    # pylint: disable=W0212
    if not self._task.args.get(key_path):
      return

    src = self._task.args.get(key_path)

    working_path = self._loader.get_basedir()
    if self._task._role is not None:
      working_path = self._task._role._role_path

    if os.path.isabs(src) or urlsplit('src').scheme:
      source = src
    else:
      source = self._loader.path_dwim_relative(working_path, 'templates', src)
      if not source:
        source = self._loader.path_dwim_relative(working_path, src)

    if not os.path.exists(source):
      raise ValueError('path specified in src not found')

    try:
      with open(source, 'r') as f:
        template_data = to_text(f.read())
    except IOError:
      return dict(failed=True, msg='unable to load file, {}'.format(src))

    # Create a template search path in the following order:
    # [working_path, self_role_path, dependent_role_paths, dirname(source)]
    searchpath = [working_path]
    if self._task._role is not None:
      searchpath.append(self._task._role._role_path)
      if hasattr(self._task, "_block:"):
        dep_chain = self._task._block.get_dep_chain()
        if dep_chain is not None:
          for role in dep_chain:
            searchpath.append(role._role_path)
    searchpath.append(os.path.dirname(source))
    self._templar.environment.loader.searchpath = searchpath
    self._task.args[key_path] = self._templar.template(template_data)


  def run(self, tmp=None, task_vars=None):
    del tmp  # tmp no longer has any effect

    # ファイルへのパスを指定されていたらファイルの中身に展開する
    try:
      self._handle_template('running_config_path')
    except ValueError as e:
      return dict(failed=True, msg=to_text(e))

    # モジュールを実行する
    # ただし、このモジュールは何もしない
    result = super(ActionModule, self).run(task_vars=task_vars)

    #
    # モジュール実行後の後工程処理
    #

    if self._task.args.get('running_config_path'):
      config = self._task.args.get('running_config_path')
    else:
      config = self._task.args.get('running_config')

    have_list = self.map_config_to_obj(config)
    if self._task.args.get('debug'):
      result['have'] = have_list

    want_list = self.map_params_to_obj()
    if self._task.args.get('debug'):
      result['want'] = want_list

    msg = self.validate(want_list)
    if msg:
      result['failed'] = True
      result['msg'] = msg
      return result

    commands = self.to_commands_list(want_list, have_list)
    result['commands'] = commands

    return result
