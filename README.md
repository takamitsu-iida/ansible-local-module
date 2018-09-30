# Ansibleローカルモジュール

ネットワーク機器の設定をAnsibleで変更するためのローカルモジュールの例です。

## ローカルモジュールとは

Ansibleのコアモジュールはいずれも以下の動作をモジュールの中で完結してしまいます。

- リモートデバイスから情報を収集
- 差分コンフィグを生成
- リモートデバイスに適用

これらのうち差分コンフィグを生成する機能だけを使いたくても、できない作りになっています。

そこで事前に採取しておいたリモートデバイスの設定情報と希望するコンフィグ状態を入力すると、打ち込むべきコマンドを生成するモジュールを作成しました。
リモートデバイスへの接続を行わないので、ここではローカルモジュールと呼んでいます。

事前に投入するコマンドをレビューしたい場合に便利でしょう。

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

## ios_interface_local

[説明　README_interface.md](README_interface.md)

インタフェース内のパラメータを設定するローカルモジュールです。

現在は以下のパラメータを設定できます。
不足するパラメータは必要に応じてモジュールを改造すればいいでしょう。

- description
- negotiation
- speed
- duplex
- mtu
- shutdown

<br>

## ios_interface_address_local

[説明　README_interface_address.md](README_interface_address.md)

インタフェースにIPアドレスを設定するローカルモジュールです。
セカンダリアドレスにも対応しています。

<br>

## ios_hsrp_local

[説明　README_hsrp.md](README_hsrp.md)

HSRPの設定コマンドを生成するローカルモジュールです。

<br>

## ios_static_route_local

[説明　README_static_route.md](README_static_route.md)

スティックルートの設定を生成するローカルモジュールです。
スタティックルートが大量にある場合に便利です。

<br>

## ios_ip_acl_local

[説明　README_ip_acl.md](README_ip_acl.md)

ip access-listの中身を管理します。
順番の入れ替えや追加、削除といった操作はどうしても間違えがちなので、このモジュールで差分コンフィグを生成した方が安全でしょう。

<br>

# Cisco Catalyst系ローカルモジュール

IOS Catalystを対象にしたローカルモジュールです。

<br>

## ios_vlan_local

[説明　README_vlan.md](README_vlan.md)

VANの定義は','や'-'を使った変則的なコマンド入力になりますのでどうしても間違えやすいです。
このモジュールで差分コンフィグを生成した方が安全でしょう。

<br>

## ios_interface_trunk_local

[説明　README_interface_trunk.md](README_interface_trunk.md)

インタフェースにVLANを通す、通さない、といった設定変更は間違えやすいものの一つです。
このモジュールで差分コンフィグを生成した方が安全でしょう。

<br>

## ios_linkagg_local

[説明　README_linkagg.md](README_linkagg.md)

リンクアグリゲーションの設定は複数の物理インタフェースに設定することになりますので、手作業で変更すると間違えやすいです。
このモジュールで差分コンフィグを生成した方が安全でしょう。

<br>

# IOSデバイスへのコンフィグの流し込み

ローカルモジュールで生成した差分コンフィグをリモートデバイスに流し込むには、独自に作成した`ios_cfg`モジュールを使います。

ios_configモジュールは親子関係を指定する必要があるため少々使いづらく、しばしば期待通りになりません。
できるだけ`ios_cfg`モジュールを使って流し込みましょう。

## 使い方

```yaml
- name: apply config to the remote device
  ios_cfg:
    lines: "{{ commands }}"
  when:
    - commands
  register: r
```

<br>

# reveal.jsの練習

[decks](decks/index.html)
