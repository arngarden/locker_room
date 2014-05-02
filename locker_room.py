# -*- coding: utf-8 -*-
"""
LockerRoom - Distributed lock manager using MongoDB
    Copyright (C) 2014 Gustav Arngården

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""    

import time
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from datetime import datetime, timedelta
try:
    from contextlib2 import contextmanager
except:
    print 'Warning: contextlib2 is not present, function decorator might not work properly'
    from contextlib import contextmanager


class LockerException(Exception):
    pass


class LockerRoom(object):
    """
    Distributed lock manager using MongoDB
    """

    TIMEOUT = 0.1
    
    def __init__(self, host='localhost', db='locks', collection='locks'):
        """ Init LockerRoom with optional host, database and collection names.
        """
        self.lock_collection = MongoClient(host)[db][collection]
        self.known_locks = {lock['_id'] for lock in self.lock_collection.find()}

    def lock(self, name, owner=None, timeout=None, expire=None):
        """ Try and get lock with given name.
        Optionally setting a owner (for example host name of the server that calls the lock).
        If timeout is given, wait for lock this many seconds before raising LockerException.
        If expire is given, a lock that has been held for longer than this many seconds is
        up for grabs by next process that requests it.
        """
        if not name in self.known_locks:
            # new lock, insert to collection
            try:
                self.lock_collection.insert({'_id': name, 'locked': True, 'owner': owner,
                                             'timestamp': datetime.utcnow(),
                                             'expire': expire})
                return True
            except DuplicateKeyError:
                # another instance of LockerRoom got ahead of us, try to get hold of lock
                self.lock(name, owner=owner, timeout=timeout, expire=expire)
            finally:
                self.known_locks.add(name)
        else:
            # try and get existing lock
            start_time = datetime.utcnow()
            while True:
                query = {'_id': name, 'locked': False}
                lock_expire = self.status(name)['expire']
                if lock_expire is not None:
                    # ok to steal lock if held too long
                    steal_time = datetime.utcnow() - timedelta(seconds=lock_expire)
                    query = {'$or' : [{'_id': name, 'locked': False},
                                      {'timestamp': {'$lt': steal_time}}]}
                status = self.lock_collection.find_and_modify(query,
                                                              {'locked': True, 'owner': owner,
                                                               'timestamp': datetime.utcnow(),
                                                               'expire': expire})
                if status:
                    return True
                time.sleep(self.TIMEOUT)
                if timeout:
                    if datetime.utcnow() >= start_time + timedelta(seconds=timeout):
                        status = self.status(name)
                        raise LockerException('Timeout, lock owned by %s since %s, expire time is %s'
                                              % (status['owner'], status['timestamp'], status['expire']))

    def release(self, name):
        """ Release lock with given name.
        Raises LockerException if we try and release a unlocked lock.
        """
        status = self.lock_collection.find_and_modify({'_id': name},
                                                      {'locked': False, 'owner': None,
                                                       'timestamp': None, 'expire': None})
        if not status or not status['locked']:
            raise LockerException('Trying to release a unlocked lock')

    @contextmanager
    def lock_and_release(self, name, owner=None, timeout=None, expire=None):
        """ Context manager for performing lock and release in context or function decorator.
        """
        self.lock(name, owner=owner, timeout=timeout, expire=expire)
        yield
        self.release(name)

    def status(self, name):
        """ Get status (locked, owner and timestamp) of lock with given name.
        """
        return self.lock_collection.find_one({'_id': name})

    def touch(self, name):
        """ Renew timestamp on lock to now.
        This can be used by processes that needs to hold lock for a longer period
        to prevent lock from being stolen.
        """
        self.lock_collection.update({'_id': name},
                                    {'$set': {'timestamp': datetime.utcnow()}})
