## Ansibleのネットワークモジュール

設定変更するモジュールは次の動作を行う

1. リモートデバイスに接続
1. 設定情報を採取
1. 差分設定を生成
1. リモートデバイスに設定を投入

とても便利だけど・・・

---

## 差分生成機能だけを使いたい

こうしたい

- 予め採取しておいたコンフィグと比較して差分コンフィグを生成したい
- 流し込む手段と切り離したい

---

## ローカルモジュール

コアモジュールの改造は難しそうなので、差分設定を生成するだけのモジュールを作成

ローカルホストだけで完結するのでローカルモジュールと呼ぶことにする

---

## 使い方

- running_configに既存の設定を指定
- interfacesに希望する状態を指定

```yaml
tasks:
  - name: create config to be pushed
    ios_interface_local:
      running_config: "{{ running_config }}"
      interfaces: "{{ interfaces }}"
    register: r
```

こんなコンフィグが得られる

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
