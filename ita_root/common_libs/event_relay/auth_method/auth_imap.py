from common_libs.event_relay.api_client_common import APIClientCommon
from imapclient import IMAPClient
import ssl
import json
from datetime import datetime


class IMAPAuthClient(APIClientCommon):
    def __init__(self, auth_settings=None):
        super().__init__(auth_settings)

    def imap_login(self):
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

    def call_api(self, parameter=None):

        # IMAPサーバにログイン
        self.imap_login()

        # メールボックスの選択
        if self.mailbox_name is None:
            self.mailbox_name = "INBOX"
        mailbox = self.client.select_folder(self.mailbox_name)

        # 最後の取得時間以降に受信したメールのIDを取得
        datetime_obj = datetime.utcfromtimestamp(self.last_fetched_timestamp)
        target_datetime = datetime_obj.strftime("%d-%b-%Y")
        message_ids = self.client.search(["SINCE", target_datetime])

        # 取得したIDのメールの内容を取得
        mail_dict = self.client.fetch(message_ids, ['ENVELOPE', 'RFC822.HEADER', 'RFC822.TEXT'])
        response = []

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

            response.append(info)

        response = [item for item in response if item["date"] >= self.last_fetched_timestamp]

        return response

    def _parser(self, header_text, key):

        val = ''

        text_list = header_text.split('\r\n')
        for t in text_list:
            if t.startswith(key):
                val = t[len(key):]
                break

        return val
