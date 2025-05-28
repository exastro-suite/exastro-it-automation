from flask import g
import datetime
import ssl
import socket
import socks
import re

from imapclient import imapclient, IMAPClient
from imapclient.response_types import Address
import email
from email.header import decode_header
import quopri
import base64
import chardet
import binascii
import traceback

from common_libs.common.util import arrange_stacktrace_format
from common_libs.common.exception import AppException
from common_libs.oase.api_client_common import APIClientCommon


class IMAPAuthClient(APIClientCommon):
    def __init__(self, auth_settings=None):
        super().__init__(auth_settings)

    def imap_login(self):
        result = False
        try:
            self.ssl = False
            self.ssl_context = None

            # SSL/TLSの場合
            if self.request_method == "3":
                self.ssl = True
                self.ssl_context = ssl.create_default_context()

            # IMAPサーバに接続
            self.client = IMAPClient(
                host=self.url,
                port=self.port,
                ssl=self.ssl,
                ssl_context=self.ssl_context
            )

            # StartTLSの場合
            if self.request_method == "4":
                self.ssl_context = ssl.create_default_context()
                self.client.starttls(self.ssl_context)

            # LOGIN
            self.client.login(
                username=self.username,
                password=self.password
            )

            result = True
            return result

        except imapclient.exceptions.LoginError:
            g.applogger.info(g.appmsg.get_log_message("AGT-10033", [self.event_collection_settings_name]))
            return result
        except Exception as e:
            raise AppException("AGT-10028", [e])

    def call_api(self, parameter=None):

        if self.proxy_host:
            socks.setdefaultproxy(socks.SOCKS5, self.proxy_host, self.proxy_port)
            socket.socket = socks.socksocket

        response = []

        # IMAPサーバにログイン
        logged_in = self.imap_login()

        if logged_in is False:
            return False, response

        # メールボックスの選択
        if self.mailbox_name is None:
            self.mailbox_name = "INBOX"

        try:
            mailbox = self.client.select_folder(self.mailbox_name)  # noqa F841

            # 最後の取得時間以降に受信したメールのIDを取得
            datetime_obj = datetime.datetime.fromtimestamp(self.last_fetched_timestamp)
            target_datetime = datetime_obj.strftime("%d-%b-%Y")
            message_ids = self.client.search(["SINCE", target_datetime])

            # 取得したIDのメールの内容を取得
            mail_dict = self.client.fetch(message_ids, ['ENVELOPE', 'RFC822.HEADER', 'RFC822.TEXT'])
            if mail_dict == {}:
                return False, response

            # メールの内容を辞書型にまとめる
            for mid, d in mail_dict.items():
                e = d[b'ENVELOPE']
                h = d[b'RFC822.HEADER']
                b = d[b'RFC822.TEXT']
                # print(d)
                # print(dir(d))
                # print(e)
                # print(dir(e))
                # print(h)
                # print(dir(h))
                try:
                    res = {}
                    # RFC5322 Message-IDは含むべき、Dateは必須
                    # Dateがない場合は、古いデータにしてしまい、取り扱わない
                    e_timestamp = e.date.timestamp() if type(e.date) is datetime.datetime else int(self.last_fetched_timestamp) - 1
                    res['date'] = int(e_timestamp)
                    res['lastchange'] = e_timestamp
                    # message_idがない場合は無理やりつける
                    res['message_id'] = e.message_id.decode() if e.message_id is not None else '{}_{}'.format(self.event_collection_settings_name, e_timestamp)

                    # メール重複取得防止
                    # 受信時間が最終取得時間より後かつ、message_idがすでに取得したメールのmessage_idと一致しないかチェック
                    if res["date"] < self.last_fetched_timestamp or res["message_id"] in self.saved_ids:
                        # g.applogger.debug('event[messege_id={}] is skipped'.format(res['message_id']))
                        continue
                    # ヘッダー情報から、文字コードなどを抜き出しておく
                    eobj_header = email.message_from_bytes(h)
                    header_content_type = eobj_header.get_content_type()  # ヘッダーにあるContent-Type
                    header_content_charset = eobj_header.get_content_charset()  # ヘッダーにあるContent-Typeの中にあるcharset
                    header_transfer_encoding = eobj_header.get('Content-Transfer-Encoding')  # ヘッダーにあるContent-Transfer-Encoding
                    # g.applogger.debug(f'{header_content_type=}')
                    # g.applogger.debug(f'{header_content_charset=}')
                    # g.applogger.debug(f'{header_transfer_encoding=}')

                    # 件名
                    subject = ''
                    subject_content_charset = ''
                    encoding_blocks = decode_header(e.subject.decode())
                    for encoding_block in encoding_blocks:
                        byte_msg, _charset =encoding_block

                        charset = _charset if _charset is not None else header_content_charset
                        if subject_content_charset is None:
                            subject_content_charset = charset  # subjectのcharsetは文字コード情報が足りない場合に使う候補
                        subject += str(self._decode_msg(byte_msg, None, charset))
                    res['subject'] = subject
                    # g.applogger.debug("{}={}".format('subject', res['subject']))

                    # 本文（body）
                    res['body'] = {
                        'raw' : '',
                        'plain' : '',
                        'html' : ''
                    }
                    eobj_body = email.message_from_bytes(b)
                    # rawデータをとりあえずつっこんでおく
                    charset = eobj_body.get_charsets()[0] or header_content_charset
                    body_transfer_encoding = eobj_body.get('Content-Transfer-Encoding') or header_transfer_encoding
                    res['body']['raw'] = self._decode_msg(b, body_transfer_encoding, charset)

                    # マルチパートかどうか
                    if eobj_header.get_content_maintype() == "multipart":
                        is_multipart = True
                    else:
                        is_multipart = False

                    if is_multipart is False:
                    # シングルパートのとき
                        # bodyにエンコード情報がなければ、ヘッダーからスライドさせる（重要）
                        content_type = eobj_body.get_content_type() or header_content_type or 'text/plain'  # Content-Type
                        charset = eobj_body.get_content_charset() or header_content_charset or subject_content_charset  # Content-Typeの中にあるcharset
                        body = self._decode_msg(b, body_transfer_encoding, charset)

                        if content_type == 'text/plain':
                            res['body']['plain'] = body
                        elif content_type == 'text/html':
                            res['body']['html'] = re.sub(r'\s', '', body)
                        # g.applogger.debug(charset)
                        # g.applogger.debug(body_transfer_encoding)
                    else:
                    # マルチパートのとき
                        boundry = eobj_header.get_boundary()
                        # g.applogger.debug(boundry)
                        boundry = r'--{}'.format(boundry) if boundry is not None else r'--.*?'
                        pattern = re.compile(boundry, re.DOTALL)
                        body_parts = re.split(pattern, b.decode())[1:-1]  # boundryによって分割したブロックの最初と最後はスキップさせる
                        for body_part in body_parts:
                            # boundryによって分割したブロックの最初と最後はスキップさせる（以下二つのifは保険）
                            body_part = str.strip(body_part)
                            if body_part == '':
                                continue
                            body_part = str.strip(re.sub(r'^--', '', body_part))
                            if body_part == '':
                                continue

                            eobj_body_part = email.message_from_string(body_part)

                            payload = eobj_body_part.get_payload()  # パートの本文部分
                            content_type = eobj_body_part.get_content_type()  # パートのContent-Type
                            charset_part = eobj_body_part.get_content_charset() or header_content_charset or subject_content_charset  # パートのContent-Typeの中にあるcharset
                            body_transfer_encoding_part = eobj_body_part.get('Content-Transfer-Encoding') or body_transfer_encoding  # パートのContent-Transfer-Encoding
                            body = str(self._decode_msg(payload, body_transfer_encoding_part, charset_part))

                            # g.applogger.debug(content_type)
                            # g.applogger.debug(charset_part)
                            # g.applogger.debug(body_transfer_encoding_part)
                            # g.applogger.debug(body)
                            if content_type == 'text/plain':
                                res['body']['plain'] = body
                            elif content_type == 'text/html':
                                res['body']['html'] = re.sub(r'\s', '', body)

                    # 宛先ヘッダー（ENVELOPE）に含まれる各項目をデコードしていく
                    res['from'] = ""
                    res['sender'] = ""
                    res['to'] = ""
                    res['cc'] = ""
                    res['bcc'] = ""
                    res['reply_to'] = ""
                    res['in_reply_to'] = ""

                    item_map = {
                        'from_': {'prop': 'from', 'val': e.from_},  # 差出人アドレス。複数可能
                        'sender': {'prop': 'sender', 'val': e.sender},  # 実際の差出人（送信者）のアドレス。複数不可
                        'to': {'prop': 'to', 'val': e.to},
                        'cc': {'prop': 'cc', 'val': e.cc},
                        'bcc': {'prop': 'bcc', 'val': e.bcc},
                        'reply_to': {'prop': 'reply_to', 'val': e.reply_to},  # メールの返信先。指定されていない場合には、通常Fromが返信先として使用される
                        'in_reply_to': {'prop': 'in_reply_to', 'val': e.in_reply_to}  # 返信時に、どのメールへの返信かを示す。通常はMessage-IDが指定される
                    }
                    for _item_name in ['from_', 'sender', 'to', 'cc', 'bcc', 'reply_to', 'in_reply_to']:
                        item_name = item_map[_item_name]['prop']  # 最終的にeventにつけるプロパティ名を取得
                        _tupple_address = item_map[_item_name]['val']
                        item_value_list = []

                        if _tupple_address is None or len(_tupple_address) == 0:
                            continue

                        # g.applogger.debug(_tupple_address)
                        if type(_tupple_address) is tuple:
                            for address in _tupple_address:
                                if isinstance(address, Address):
                                    # Addressクラスのインスタンス
                                    if address.name is not None:
                                        # 名前いり
                                        byte_msg, _charset = decode_header(address.name.decode())[0]
                                        charset = _charset if _charset is not None else header_content_charset
                                        item_value = '"%s"<%s@%s>' % (self._decode_msg(byte_msg, None, charset), address.mailbox.decode(), address.host.decode())
                                    else:
                                        item_value = '%s@%s' % (address.mailbox.decode(), address.host.decode())
                                else:
                                    try:
                                        item_value = address.decode()
                                    except:
                                        g.applogger.info(g.appmsg.get_log_message("AGT-10034", [address]))
                                        item_value = address
                                item_value_list.append(str(item_value))
                        else:
                            try:
                                item_value = _tupple_address.decode()
                            except:
                                g.applogger.info(g.appmsg.get_log_message("AGT-10035", [_tupple_address]))
                                item_value = _tupple_address
                            item_value_list.append(str(item_value))

                        res[item_name] = ','.join(item_value_list)
                        # g.applogger.debug("{}={}".format(item_name, res[item_name]))

                    # Return-Path Mail Fromコマンド（SMTP）の内容を付加することになる。エンベロープの差出人アドレス。メールが届かなかった場合に、そのメールが送り返されるメールアドレス
                    # Delivered-To 送信者が本来送信した宛先から別のアドレスに転送された宛先。 受信したメールサーバで別のメールアドレスに転送している場合などに付加される。
                    res['return_path'] = self._parser(h.decode(), 'Return-Path: ')
                    res['deliver_to'] = self._parser(h.decode(), 'Delivered-To: ')

                    # g.applogger.debug('subject={}'.format(res['subject']))
                    # g.applogger.debug('body={}'.format(res['body']))
                    # g.applogger.debug(res)
                except Exception as e:
                    t = traceback.format_exc()
                    err_log = arrange_stacktrace_format(t)
                    g.applogger.info(err_log)

                # レスポンスに追加
                response.append(res)
        except Exception as e:
            socks.setdefaultproxy()
            raise AppException("AGT-10028", [e])

        socks.setdefaultproxy()

        return True, response

    def _parser(self, header_text, key):

        val = ''

        text_list = header_text.split('\r\n')
        for t in text_list:
            if t.startswith(key):
                val = t[len(key):]
                break

        return val

    def _decode_msg(self, row_b, _cte, _charset):
        b = ''
        if row_b is None or row_b == '':
            return b
        if str.strip(str(row_b)) == '':
            return b
        if type(row_b) not in [bytes, str]:
            g.applogger.info(g.appmsg.get_log_message("AGT-10036", [type(row_b), row_b]))
            return row_b

        try:
            cte = _cte.lower() if _cte is not None else '7bit'
            if cte == "base64":
                b = base64.b64decode(row_b)
            elif cte == "quoted-printable":
                b = quopri.decodestring(row_b, header=False)
            elif cte in ('x-uuencode', 'uuencode', 'uue', 'x-uue'):
                b = self._decode_uu(row_b)
            elif cte in {'7bit', '8bit', 'binary'}:
                b = row_b
        except Exception as e:
            g.applogger.info(g.appmsg.get_log_message("AGT-10037", [e, cte, _charset, row_b]))
            b = row_b

        if type(b) not in [bytes]:
            # g.applogger.debug('unnecessary decode (not bytes but {}) {} {} {}'.format(type(b), cte, _charset, b))
            return b

        try:
            # https://docs.python.org/ja/3/library/codecs.html#standard-encodings
            # Codec名で記載
            charset = _charset.lower().replace("_", "-") if _charset is not None else "ascii"
            if charset == "utf-8":
                return b.decode("utf_8", "ignore")
            elif charset == "iso-2022-jp": # JISコード
                return b.decode("iso2022_jp", "ignore")
            elif charset == "shift-jis":
                return b.decode("shift_jis", "ignore")
            elif charset == "iso-8859-1":
                return b.decode("latin_1", "ignore")
            elif charset == "euc-jp":
                return b.decode("euc_jp", "ignore")
            else:
                return b.decode("ascii", "ignore")
        except Exception as e:
            g.applogger.info(g.appmsg.get_log_message("AGT-10038", [e, cte, charset, row_b]))

            # 検知してみる
            try:
                detect = chardet.detect(b)
                if detect['encoding'] is None:
                    return b

                charset = detect['encoding'].lower()
                return b.decode(charset, "ignore")
            except Exception as e_e:
                g.applogger.info(g.appmsg.get_log_message("AGT-10039", [e_e, charset]))

            return b


    def _decode_uu(encoded):
        """Decode uuencoded data."""
        decoded_lines = []
        encoded_lines_iter = iter(encoded.splitlines())
        for line in encoded_lines_iter:
            if line.startswith(b"begin "):
                mode, _, path = line.removeprefix(b"begin ").partition(b" ")
                try:
                    int(mode, base=8)
                except ValueError:
                    continue
                else:
                    break
            else:
                g.applogger.info(g.appmsg.get_log_message("AGT-10040"))
                return encoded

        for line in encoded_lines_iter:
            if not line:
                g.applogger.info(g.appmsg.get_log_message("AGT-10041"))
                return encoded
            elif line.strip(b' \t\r\n\f') == b'end':
                break

            try:
                decoded_line = binascii.a2b_uu(line)
            except binascii.Error:
                # Workaround for broken uuencoders by /Fredrik Lundh
                nbytes = (((line[0]-32) & 63) * 4 + 5) // 3
                decoded_line = binascii.a2b_uu(line[:nbytes])
            decoded_lines.append(decoded_line)

        return b''.join(decoded_lines)
