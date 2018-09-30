# Ansibleローカルモジュール

ネットワーク機器の設定をAnsibleで変更するためのローカルモジュールの例です。

## ローカルモジュールとは

Ansibleのコアモジュールはいずれも以下の動作をモジュールの中で完結してしまいます。

- リモートデバイスから情報を収集
- 差分コンフィグを生成
- リモートデバイスに適用

差分コンフィグを生成する機能だけを使いたくてもできない作りになっています。

事前に採取しておいたリモートデバイスの設定情報と希望するコンフィグ状態を入力すると、打ち込むべきコマンドを生成するモジュールを作りました。
リモートデバイスへの接続を行わないので、ここではローカルモジュールと呼んでいます。

事前に投入するコマンドをレビューしたい場合に便利です。

<br>

## ディレクトリ構成

独自モジュールは`library`以下に配置します。

モジュールといっても実態としてはアクションプラグインで実装していますので`plugins/action`に同名のファイルを配置しています。

```bash
.
├── library
│   ├── ios_cfg.py
│   ├── ios_hsrp_local.py
│   ├── ios_interface_address_local.py
│   ├── ios_interface_local.py
│   ├── ios_interface_trunk_local.py
│   ├── ios_ip_acl_local.py
│   ├── ios_linkagg_local.py
│   ├── ios_static_route_local.py
│   └── ios_vlan_local.py
├── playbooks
│   ├── hsrp.yml
│   ├── interface.yml
│   ├── interface_address.yml
│   ├── interface_trunk.yml
│   ├── ip_access_list.yml
│   ├── linkagg.yml
│   ├── static_route.yml
│   └── vlan.yml
├── plugins
│   └── action
│       ├── ios_hsrp_local.py
│       ├── ios_interface_address_local.py
│       ├── ios_interface_local.py
│       ├── ios_interface_trunk_local.py
│       ├── ios_ip_acl_local.py
│       ├── ios_linkagg_local.py
│       ├── ios_static_route_local.py
│       └── ios_vlan_local.py
```

## ansible.cfg

独自モジュールの置き場とプラグインの置き場にだけ注意が必要です。

```ini
[defaults]

inventory = ./inventories/development

library = ./library
action_plugins = ./plugins/action

stdout_callback = debug
```

<br>

# Cisco IOS系ローカルモジュール

Cisco IOSルータを対象にしたローカルモジュールです。

<br>

## ios_hsrp_local

[説明](README_hsrp.md)

<br>

## ios_interface_address_local

[説明](README_interface_address.md)

<br>

## ios_interface_local

[説明](README_interface.md)

<br>

## ios_static_route_local

[説明](README_static_route.md)

<br>

## ios_ip_acl_local

[説明](README_ip_acl.md)

<br>

# Cisco Catalyst系ローカルモジュール

IOS Catalystを対象にしたローカルモジュールです。

<br>

## ios_vlan_local

[説明](README_vlan.md)

## ios_interface_trunk_local

[説明](README_interface_trunk.md)

<br>

## ios_linkagg_local

[説明](README_linkagg.md)

<br>

# コンフィグの流し込み

ローカルモジュールで生成した差分コンフィグをリモートデバイスに流し込むには、独自に作成した`ios_cfg`モジュールを使います。

ios_configモジュールは親子関係を指定する必要があるため少々使いづらく、しばしば期待通りになりません。
