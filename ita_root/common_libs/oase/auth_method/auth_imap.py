from flask import g
from common_libs.oase.api_client_common import APIClientCommon
from imapclient import imapclient, IMAPClient
import ssl
import socket
import socks
from common_libs.common.exception import AppException
import datetime


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
            g.applogger.info("Failed to login to mailserver. Check login settings.")
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
            return response

        # メールボックスの選択
        if self.mailbox_name is None:
            self.mailbox_name = "INBOX"

        try:
            mailbox = self.client.select_folder(self.mailbox_name)  # noqa F841

            # 最後の取得時間以降に受信したメールのIDを取得
            datetime_obj = datetime.datetime.utcfromtimestamp(self.last_fetched_timestamp)
            target_datetime = datetime_obj.strftime("%d-%b-%Y")
            message_ids = self.client.search(["SINCE", target_datetime])

            # 取得したIDのメールの内容を取得
            mail_dict = self.client.fetch(message_ids, ['ENVELOPE', 'RFC822.HEADER', 'RFC822.TEXT'])
            if mail_dict == {}:
                return response

            # メールの内容を辞書型にまとめる
            for mid, d in mail_dict.items():
                e = d[b'ENVELOPE']
                h = d[b'RFC822.HEADER']
                b = d[b'RFC822.TEXT']

                ef = e.from_[0] if isinstance(e.from_, tuple) and len(e.from_) > 0 else None
                et = e.to[0] if isinstance(e.to, tuple) and len(e.to) > 0 else None

                info = {}
                info['message_id'] = e.message_id.decode()
                info['envelope_from'] = '%s@%s' % (ef.mailbox.decode(), ef.host.decode()) if ef else ''
                info['envelope_to'] = '%s@%s' % (et.mailbox.decode(), et.host.decode()) if et else ''
                info['header_from'] = self._parser(h.decode(), 'Return-Path: ')
                info['header_to'] = self._parser(h.decode(), 'Delivered-To: ')
                info['mailaddr_from'] = self._parser(h.decode(), 'From: ')
                info['mailaddr_to'] = self._parser(h.decode(), 'To: ')
                info['date'] = int(e.date.timestamp())
                # info['date'] = e.date.strftime('%Y-%m-%d %H:%M:%S')
                info['lastchange'] = e.date.timestamp()
                info['subject'] = e.subject.decode() if e.subject else ''
                info['body'] = b.decode()

                if info["date"] >= self.last_fetched_timestamp and info["message_id"] not in self.message_ids:
                    response.append(info)

        except Exception as e:
            socks.setdefaultproxy()
            raise AppException("AGT-10028", [e])

        socks.setdefaultproxy()

        return response

    def _parser(self, header_text, key):

        val = ''

        text_list = header_text.split('\r\n')
        for t in text_list:
            if t.startswith(key):
                val = t[len(key):]
                break

        return val
