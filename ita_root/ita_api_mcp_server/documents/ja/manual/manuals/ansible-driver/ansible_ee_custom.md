# Ansible実行環境のカスタマイズ方法

ITAで使用するAnsible実行環境をカスタマイズする方法を説明します。Ansible-Coreではビルド時にカスタマイズ工程を挟む（docker-compose版のみ）、またはカスタマイズ済みイメージを使用する方法があります。Ansible Execution AgentやAnsible Automation Platformではansible-builderを用いた実行環境カスタマイズが可能です。

## Ansible-Coreでのカスタマイズ

### ビルドにカスタマイズ工程を追加する例（docker-compose版のみ）

`~/exastro-docker-compose/.env` の `ANSIBLE_AGENT_IMAGE` / `ANSIBLE_AGENT_IMAGE_TAG` / `ANSIBLE_AGENT_BASE_IMAGE` / `ANSIBLE_AGENT_BASE_IMAGE_TAG` を確認します（コメントアウト時の既定値: `ANSIBLE_AGENT_IMAGE=my-exastro-ansible-agent`、タグはITAバージョン、ベースイメージは`exastro/exastro-it-automation-by-ansible-agent`）。既存イメージがある場合は`docker rmi`で削除しておきます。

ビルドには`~/exastro-docker-compose/ita_by_ansible_execute/templates/docker-compose.yml`と`work/Dockerfile`を使用するため、カスタマイズ内容はこの2ファイルに記載します（ITA 2.6.0以降、デフォルトベースイメージのPython/pipはPython3.11/pip3.11）。

**コレクション追加の例**: Dockerfileに以下を追加します（ライブラリはコレクション公式ドキュメント記載のものを指定）。

```dockerfile
RUN ansible-galaxy collection install [インストールしたいコレクション名] \
&& pip3.11 install [コレクションに必要なライブラリ]
```

透過型プロキシでSSL/TLSインスペクションを行っている場合は証明書エラーを避けるため`ansible-galaxy collection install --ignore-certs ...`のように`--ignore-certs`を付与します（カスタムCA証明書のインストールでの証明書検証も可能）。

**自作モジュールの例**: モジュールファイルを`~/exastro-docker-compose/ita_by_ansible_execute/templates/work/my_module.py`に配置し読み取り権限を付与（`chmod a+r`）、Dockerfileに以下を追加します。

```dockerfile
RUN mkdir -p /home/app_user/.ansible/plugins/modules
COPY my_module.py /home/app_user/.ansible/plugins/modules/
```

編集後、Ansible-Coreでの作業実行時にビルドが行われます（`returned a non-zero code: 1`エラーが出た場合はビルド失敗）。

### カスタマイズ済みイメージを使用する例

イメージ存在サーバで対象イメージを確認し（Kubernetesではタグ名`latest`/`none`だとローカルイメージが使われないため、それ以外のタグに変更推奨）、`docker save <image>:<tag> | gzip -c > /tmp/custom-docker-image.tar.gz`で出力します。

**docker-compose版**: 対象サーバへtar.gzを転送し`docker load < /tmp/custom-docker-image.tar.gz`で投入、`docker images`で確認後、`.env`の`ANSIBLE_AGENT_IMAGE`/`ANSIBLE_AGENT_IMAGE_TAG`を編集し、`sh setup.sh install`で反映します。

**Kubernetes版**: 全ノードへtar.gzを転送し`ctr images -n k8s.io import /tmp/custom-docker-image.tar.gz`で投入、`values.yaml`の`exastro-it-automation.ita-by-ansible-execute.extraEnv.ANSIBLE_AGENT_IMAGE`/`ANSIBLE_AGENT_IMAGE_TAG`を編集し、`helm upgrade`と`kubectl rollout restart deploy/ita-by-ansible-execute`で反映します。

## Ansible Execution Agentでのカスタマイズ

ITA側で実行環境定義テンプレート（`Ansible共通 --> 実行環境定義テンプレート管理`）と、テンプレートに代入する値（無償版は直接テンプレート内のJinja変数、有償版はパラメータシート「実行環境パラメータ定義」経由）、および両者を紐付ける実行環境（`Ansible共通 --> 実行環境管理`）を登録し、対象Movementの「Ansible Execution Agent利用情報」に実行環境名を設定する、という共通の流れで設定します。

### コレクション利用（無償版ベースイメージ）例

ベースイメージ`registry.access.redhat.com/ubi9/ubi-init:latest`にコレクション`azure.azcollection`を追加する例です。

実行環境定義テンプレート（テンプレート名`azure_ee_template`）は以下のようなJinja2テンプレートです。

```yaml+jinja
version: 3
build_arg_defaults:
  ANSIBLE_GALAXY_CLI_COLLECTION_OPTS: '--ignore-certs'
images:
  base_image:
    name: {{ image }}
dependencies:
  ansible_core:
    package_pip: {{ ansible_core }}
  ansible_runner:
    package_pip: {{ ansible_runner }}
  system: {{ bindep_file }}
  python: {{ python_requirements_file }}
{% if galaxy_requirements_file == "" %}
{% else %}
  galaxy: {{ galaxy_requirements_file }}
{% endif %}
  python_interpreter:
    package_system: "python3.11"
    python_path: "/usr/bin/python3.11"
additional_build_steps:
  append_base:
    - RUN /usr/bin/python3.11 -m pip install --upgrade pip
options:
  package_manager_path: {{ package_manager_path }}
  user: root
```

実行環境管理には、実行環境名（例: `azure_ee_ubi9`）、実行環境構築方法「ITA」、タグ名（例: `azure_ee_image_ubi9`）、実行環境定義名（初期データの「~[Exastro standard] default (galaxy collection is azure only)」を使用）、テンプレート名（`azure_ee_template`）を登録します。対象MovementのAnsible Execution Agent利用情報の「実行環境」に実行環境名（`azure_ee_ubi9`）を設定します（ansible-builderパラメータは通常不要、デバッグ時に`-v 3`等を指定）。

### コレクション利用（有償版ベースイメージ）例

ベースイメージ`registry.redhat.io/ansible-automation-platform-24/ee-minimal-rhel9:latest`を使う場合。Agent側で事前に`podman login registry.redhat.io`を実施しておきます。

パラメータシート「実行環境パラメータ定義」（`入力用 --> 実行環境パラメータ定義`）に、execution_environment_name（例: `azure_ee`）、image（上記ベースイメージ）、ansible_core（例: `ansible_core==2.16.0`）、ansible_runner、bindep_file（`systemd-devel`/`gcc`/`python3.11-devel`）、python_requirements_file（`pywinrm`/`setuptools`/`pexpect`/`boto3`/`paramiko`/`boto`/`certifi`）、galaxy_requirements_file（`collections:\n - azure.azcollection`）、package_manager_path（`/usr/bin/microdnf`）を登録します。テンプレート・実行環境管理・Movementの設定は無償版と同様（実行環境定義名は「実行環境パラメータ定義/azure_ee」を指定）。

### 自作モジュールを使用する例（Agent）

`/tmp/ansible_module/my_module.py`をAgentに配置し読み取り権限を付与します。実行環境定義テンプレート（例: `my_module_ubi9_template`）には`additional_build_files`でモジュールファイルをコピーし、`additional_build_steps.append_base`で`COPY _build/configs/my_module.py /usr/share/ansible/plugins/modules/`を追加します。実行環境定義名には初期データ「~[Exastro standard] default (no galaxy collection)」を使用し、実行環境管理・Movement設定は同様です。

## Ansible Automation Platformでのカスタマイズ

Ansible Automation Platform (Cloud)を実行エンジンに選択した場合も同じ手順が使えます（Cloudの場合はITA作業用ディレクトリへのファイル配置が不要になるのみで、実行環境の指定方法自体は変わりません）。

共通の流れ: ControlNodeに`ansible-builder`をインストール（`dnf install --enablerepo=ansible-automation-platform-2.4-for-rhel-8-x86_64-rpms ansible-builder`）→ 定義ファイル（`execution-environment.yml`、`galaxy-requirements.yml`、`python-requirements.txt`、`bindep.txt`）を同一ディレクトリに準備 → `ansible-builder build -t <タグ名>`でイメージ作成 → `podman images`で確認 → `podman save`でtarに出力しControlNode/ExecutionNodeのawxユーザへ`podman load`でコピー → AAPの管理画面で実行環境として登録 → ITA側のMovement「Ansible Automation Controller利用情報」の実行環境にAAPで登録した名前を設定。

**コレクション利用（無償版）例**: `execution-environment.yml`のbase_imageに`registry.access.redhat.com/ubi9/ubi-init:latest`、galaxy-requirements.ymlに`azure.azcollection`、python-requirements.txtに`pywinrm`/`setuptools`/`pexpect`/`boto3`/`paramiko`/`boto`/`certifi`、bindep.txtに`openssh-clients`/`sshpass`/`expect`を記載します。

**コレクション利用（有償版）例**: base_imageに`registry.redhat.io/ansible-automation-platform-24/ee-minimal-rhel9:latest`を使用し、事前に`podman login registry.redhat.io`が必要です。bindep.txtは`systemd-devel`/`gcc`/`python3.11-devel`、package_manager_pathは`/usr/bin/microdnf`となります（他のファイル内容は無償版と同様）。

**自作モジュール利用例**: モジュールをControlNodeの`/tmp/ansible_module/my_module.py`に配置し読み取り権限を付与、`execution-environment.yml`に`additional_build_files`（`src: /tmp/ansible_module/my_module.py`, `dest: configs`）と`additional_build_steps.append_base`の`COPY _build/configs/my_module.py /usr/share/ansible/plugins/modules/`を追加します。

いずれの場合も、ビルド完了後は`Complete! The build context can be found at: ...`が表示され、`podman images`でイメージを確認できます。イメージはControlNodeのawxユーザ用に`podman save`→`chown awx:awx`→`podman load`、ExecutionNodeには転送後`podman load`でコピーしてから、AAPの実行環境管理画面に登録します。
