<!-- markdownlint-disable MD012 -->

# Ansibleローカルモジュール

<br>

Takamitsu IIDA (@takamitsu-iida)

---

## Ansibleのネットワークモジュール

設定変更するモジュールは次の動作を行う

1. リモートデバイスに接続
1. 設定情報を採取
1. 差分設定を生成
1. リモートデバイスに設定を投入

<br>

これはこれで便利だけど・・・

---

## 動く装置がないと利用できない

- 事前に打ち込むコマンドをレビューしたい
- 事前に検証機器が必要

<br>

以前採取したコンフィグを持っていても活用できない

---

## こうあってほしい

差分コンフィグ生成の冪等性は魅力だけど、リモートデバイスとの接続は別モジュールに任せたい

- 予め採取しておいたコンフィグと比較して差分コンフィグを生成したい
- 流し込む手段と切り離したい

<br>

モジュールの動作だって完璧とは限らないので、事前に流し込むコマンドをレビューしないと怖い

---

## ローカルモジュール

コアモジュールの改造は難しそう

なので、差分設定を生成するだけのモジュールを作成

ローカルホストだけで完結するのでローカルモジュールと呼ぶ

---

## モジュールへの入力（１）

装置の設定情報を入力

- **running_config** 既存の設定を文字列で指定
- **running_config_path** ファイルを直接読ませるならこっち

```yaml
tasks:
  - name: create config to be pushed
    ios_interface_local:
      running_config: "{{ running_config }}"
      interfaces: "{{ interfaces }}"
    register: r
```

---

## モジュールへの入力（２）

希望する設定の状態をYAMLで入力

- リストなので同時に複数を指定可能

```yaml
interfaces:

  - name: GigabitEthernet3
    description: configured by ansible
    negotiation:
    speed:
    mtu: 1500
    shutdown: false
    state: present
```

---

## モジュールからの出力

- **commands** 流し込むコマンドをリストで返却

```bash
"commands": [
    "interface GigabitEthernet3",
    "no description",
    "description configured by ansible",
    "mtu 1512",
    "interface GigabitEthernet4",
    "no negotiation auto",
    "speed 1000",
    "interface Loopback0",
    "description configured by ansible",
    "shutdown"
]
```
