#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import pickle
import hashlib
import uuid
import hmac
import base64


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

    def clear(self):
        return self.session_manager.clear(self)

    def save(self):
        self.session_manager.set(self.request_handler, self)


class SessionManager(object):

    def __init__(self, secret, datastore_client, session_timeout):
        self.secret = secret
        self.client = datastore_client
        self.session_timeout = session_timeout

    def _fetch_from_store(self, session_id):
        try:
            existed = True
            is_expired = False

            raw_data = self.client.get_session_data(session_id)
            if raw_data is None:
                existed = False
                return existed, is_expired, {}

            expire_date, session_data = raw_data
            # session has been expired
            if expire_date < datetime.datetime.now():
                is_expired = True
                return existed, is_expired, {}

            if session_data is not None:
                # refresh session exprire_date
                self.client.setex(
                    session_id,
                    self.session_timeout,
                    session_data)
                session_data_dict = self.unserialize(session_data)
            return existed, is_expired, session_data_dict

        except IndexError:
            # FIXME: should keep this try catch?
            # happens when session_data is brokern in data store
            return existed, is_expired, {}

    def serialize(self, session):
        pickle_data = pickle.dumps(
            dict(
                session.items()),
            pickle.HIGHEST_PROTOCOL)
        return base64.encodestring(pickle_data)

    def unserialize(self, session_data):
        pickle_data = base64.decodestring(session_data)
        return pickle.loads(pickle_data)

    def get(self, request_handler=None):
        session_id = request_handler.get_cookie("session_id")
        hmac_key = request_handler.get_cookie("hmac_key")

        if session_id is not None:
            check_hmac_key = self._calculate_hmac(session_id)
            if check_hmac_key == hmac_key:
                session = SessionBase(session_id, hmac_key)
                # Retrive and repickle session data from DataStore
                existed, is_expired, session_data = \
                    self._fetch_from_store(session_id)
                if existed and not is_expired:
                    for k, v in session_data.iteritems():
                        session[k] = v
                else:
                    session_id = None
            else:
                session_id = None
        # session_id is None or hmac_key validation failed, return a fresh
        # session
        if session_id is None:
            session_id = self._generate_session_id()
            hmac_key = self._calculate_hmac(session_id)
            session = SessionBase(session_id, hmac_key)

        return session

    def clear(self, session):
        return self.client.delete_session(session.session_id)

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

    def __init__(self, db, table_name="yagra_sessions"):
        self.db = db
        self.table_name = table_name

    def get_session_data(self, session_id):
        sql_stmt = """SELECT expire_date, session_data
                    FROM {0} where session_id=%s"""
        sql_stmt = sql_stmt.format(self.table_name)
        params = (session_id, )

        return self.db.query_one(sql_stmt, params)

    def delete_session(self, session_id):
        sql_stmt = """DELETE FROM {0} where session_id = %s"""
        sql_stmt = sql_stmt.format(self.table_name)
        params = (session_id, )
        return self.db.update(sql_stmt, params)

    def setex(self, session_id, timeout, raw_data):
        sql_stmt = """INSERT INTO {0} (session_id, expire_date, session_data)
                    VALUES(%s, %s, %s) ON DUPLICATE KEY UPDATE
                    expire_date=%s, session_data=%s
                    """
        sql_stmt = sql_stmt.format(self.table_name)
        expired = datetime.datetime.now() + \
            datetime.timedelta(seconds=timeout)
        expired = expired.strftime("%Y-%m-%d %H:%M:%S")
        params = (session_id, expired, raw_data, expired, raw_data)

        return self.db.update(sql_stmt, params)
