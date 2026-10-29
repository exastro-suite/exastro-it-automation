## Additional description
- このPlaybookは `ansible.builtin.unarchive` を `remote_src` 未指定（デフォルト `remote_src: no`）で使用します。そのため `ITA_DFLT_Target_File_Name` に指定するアーカイブは、**Ansible制御ノード（ローカル）側に存在している必要があります**。制御ノードからターゲットホストへの転送と展開を、このタスク1つで実施します。
- パラメータシートの `FileUploadColumn` 項目を `ITA_DFLT_Target_File_Name` に連携できます。アップロードしたアーカイブは制御ノード上に配置されるため、そのまま本Playbookで転送＋展開できます。
- **`Files_copy_local-to-remote.yml` 等でターゲットホスト上にアーカイブを先に配置し、そのリモートパスを `ITA_DFLT_Target_File_Name` に渡す使い方はできません。** `remote_src: no` のため制御ノード上の同一パスを展開元として探しにいき、失敗します。リモート上に既にあるアーカイブを展開したい場合は、`remote_src: yes` を指定した別Playbookを用意してください。
- ターゲットホスト側には、アーカイブ形式に応じた展開コマンドが必要です（zip の場合は `unzip`）。事前に該当パッケージをインストールしておいてください。
