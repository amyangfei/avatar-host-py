#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import pickle
import hashlib
import uuid
import hmac
import base64

from db import DB


class SessionBase(dict):
    def __init__(self, session_id, hmac_key):
        self.session_id = session_id
        self.hmac_key = hmac_key


class Session(SessionBase):
    def __init__(self, session_manager, request_handler):
        self.session_manager = session_manager
        self.request_handler = request_handler

        current_session = session_manager.get(request_handler)
        for k, v in current_session.iteritems():
            self[k] = v
        self.session_id = current_session.session_id
        self.hmac_key = current_session.hmac_key

    def save(self):
        self.session_manager.set(self.request_handler, self)


class SessionManager(object):
    def __init__(self, secret, datastore_client, session_timeout):
        self.secret = secret
        self.client = datastore_client
        self.session_timeout = session_timeout

    def _fetch_from_store(self, session_id):
        try:
            is_expired = False
            expire_date, raw_data = self.client.get_session_data(session_id)
            # session has been expired
            if expire_date < datetime.datetime.now():
                is_expired = True
                return is_expired, {}
            if raw_data != None:
                # refresh session exprire_date
                self.client.setex(session_id, self.session_timeout, raw_data)
                session_data_dict = self.unserialize(raw_data)
            return is_expired, session_data_dict
        except IndexError:
            return is_expired, {}

    def serialize(self, session):
        pickle_data = pickle.dumps(dict(session.items()), pickle.HIGHEST_PROTOCOL)
        return base64.encodestring(pickle_data)

    def unserialize(self, session_data):
        pickle_data = base64.decodestring(session_data)
        return pickle.loads(pickle_data)

    def get(self, request_handler=None):
        session_id = request_handler.get_cookie("session_id")
        hmac_key = request_handler.get_cookie("hmac_key")

        if session_id != None:
            check_hmac_key = self._calculate_hmac(session_id)
            if check_hmac_key == hmac_key:
                session = SessionBase(session_id, hmac_key)
                # Retrive and repickle session data from DataStore
                is_expired, session_data = self._fetch_from_store(session_id)
                if not is_expired:
                    for k, v in session_data.iteritems():
                        session[k] = v
                else:
                    session_id = None
            else:
                session_id = None
        # session_id is None or hmac_key validation failed, return a fresh session
        if session_id == None:
            session_id = self._generate_session_id()
            hmac_key = self._calculate_hmac(session_id)
            session = SessionBase(session_id, hmac_key)

        return session

    def set(self, request_handler, session):
        request_handler.set_cookie("session_id", session.session_id)
        request_handler.set_cookie("hmac_key", session.hmac_key)
        session_data = self.serialize(session)
        return self.client.setex(
                session.session_id, self.session_timeout, session_data)

    def _generate_session_id(self):
        return hashlib.sha256(self.secret + str(uuid.uuid4())).hexdigest()

    def _calculate_hmac(self, session_id):
        return hmac.new(session_id, self.secret, hashlib.sha256).hexdigest()


class MySQLStore(object):
    def __init__(self, table_name="yagra.yagra_sessions"):
        self.db = DB()
        self.table_name = table_name

    def get_session_data(self, session_id):
        base_string = """SELECT expire_date, session_data
                    FROM {} where session_id='{}'"""
        sql_string = base_string.format(self.table_name, session_id)

        return self.db.query_one(sql_string)

    def setex(self, session_id, timeout, raw_data):
        base_string = """INSERT INTO {0} (session_id, expire_date, session_data)
                    VALUES('{1}', '{2}', '{3}') ON DUPLICATE KEY UPDATE
                    expire_date='{2}', session_data='{3}'
                    """
        exprired = datetime.datetime.now() + datetime.timedelta(seconds=timeout)
        exprired = exprired.strftime("%Y-%m-%d %H:%M:%S")
        sql_string = base_string.format(
                self.table_name, session_id, exprired, raw_data)

        return self.db.update(sql_string)
