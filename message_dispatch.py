#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
#   Author  :   cold
#   E-mail  :   wh_linux@126.com
#   Date    :   13/03/01 11:44:05
#   Desc    :   消息调度
#
from util import get_logger

class MessageDispatch(object):
    """ 消息调度器 """
    def __init__(self, qxbot, bridges, xmpp_msg_queue, qq_msg_queue):
        self.logger = get_logger()
        self.xmpp_msg_queue = xmpp_msg_queue
        self.qq_msg_queue = qq_msg_queue
        self.qxbot = qxbot
        self.uin_qid_map = {}
        self.qid_uin_map = {}
        self.bridges = bridges

    def get_map(self):
        uins = [key for key, value in self.qxbot.webqq.group_map.items()]
        for uin in uins:
            qid = self.get_qid_with_uin(uin)
            self.uin_qid_map[uin] = qid
            self.qid_uin_map[qid] = uin

    def get_xmpp_account(self, uin):
        """ 根据uin获取桥接的XMPP帐号 """
        qid = self.get_qid_with_uin(uin)
        for q, xmpp in self.bridges:
            if q == qid:
                return xmpp

    def get_uin_account(self, xmpp):
        """ 根据xmpp帐号获取桥接的qq号的uin """
        for qid, x in self.bridges:
            if x == xmpp:
                return self.qid_uin_map.get(qid)

    def get_qid_with_uin(self, uin):
        qid = self.uin_qid_map.get(uin)
        if not qid:
            qid = self.qxbot.webqq.get_qid_with_uin(uin)
            self.uin_qid_map[uin] = qid
        return qid

    def handle_qq_group_msg(self, message):
        """ 处理组消息 """
        gcode = message.get("value", {}).get("group_code")
        uin = message.get("value", {}).get("send_uin")
        content = message.get("value", {}).get("content", [])[-1]
        gname = self.qxbot.get_group_name(gcode)
        uname = self.qxbot.get_group_member_nick(gcode, uin)
        body = u"[{0}][{1}] {2}".format(gname, uname, content)
        msg = {"to":self.get_xmpp_account(gcode), "body":body}
        self.xmpp_msg_queue.put(msg)

    def dispatch_qq(self, qq_source):
        if qq_source.get("retcode") == 0:
            messages = qq_source.get("result")
            for m in messages:
                if m.get("poll_type") == "group_message":
                    self.handle_qq_group_msg(m)

    def dispatch_xmpp(self, stanza):
        body = stanza.body
        frm = stanza.from_jid.bare().as_string()
        msg = {"to":self.get_uin_account(frm), "body" : body}
        self.qq_msg_queue.put(msg)