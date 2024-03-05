import yaml
from common_libs.common.storage_access import storage_read

"""
  yamlファイルのパースモジュール
"""


class YamlParse:
    """
      yamlファイルのパースクラス
    """
    def __init__(self):
        self.lv_lasterrmsg = ""

    def SetLastError(self, err):
        """
          パースエラー情報退避
          Arguments:
            err: パースエラー情報
          Returns:
            None
        """
        self.lv_lasterrmsg = err

    def GetLastError(self):
        """
          パースエラー情報所得
          Arguments:
            None
          Returns:
            パースエラー情報
        """
        return self.lv_lasterrmsg

    def Parse(self, yamlfile):
        """
          yamlファイルパース処理
          Arguments:
            yamlfile: yamlファイル
          Returns:
            パース結果
            パースエラー: False
            Yaml未定義  : None
        """
        self.SetLastError("")

        # バージョン確認
        yaml_var = str(yaml.__version__).split('.')[0]

        # 対話ファイルを読み込む
        try:
            # #2079 /storage配下は/tmpを経由してアクセスする
            r_obj = storage_read()
            r_obj.open(yamlfile)
            yaml_value = r_obj.read()
            r_obj.close()

            if yaml_var >= str(5):
                retParse = yaml.load(yaml_value, Loader=yaml.FullLoader)
            else:
                retParse = yaml.load(yaml_value)
            # パーサーが辞書以外のリターンをした場合はyamlフォーマットエラーにする。
            if isinstance(retParse, dict) or isinstance(retParse, list):
                pass
            elif not retParse:
                return retParse
            else:
                self.SetLastError("not yaml format.")
                return False
        # パーサーの例外をキャッチするようにする
        except Exception as e:
            # YAML文法ミスがある場合、例外が発生する。
            self.SetLastError(str(e))
            return False

        # yaml定義がない場合にNoneが帰る
        return retParse
