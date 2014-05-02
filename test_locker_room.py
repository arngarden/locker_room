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

import unittest
import time
import locker_room
from locker_room import LockerException


class TestLock(unittest.TestCase):
    def setUp(self):
        self.locker = locker_room.LockerRoom(db='locks_test')

    def tearDown(self):
        self.locker.lock_collection.drop()

    def _assert_lock(self, name, locked=True, owner=None, expire=None):
        status = self.locker.status(name)
        self.assertTrue(status['locked'] == locked)
        self.assertTrue(status['owner'] == owner)
        self.assertTrue(status['expire'] == expire)

    def test_lock(self):
        self.locker.lock('test_lock', owner='unittest', timeout=1)
        self._assert_lock('test_lock', locked=True, owner='unittest')
        self.locker.release('test_lock')
        self._assert_lock('test_lock', locked=False, owner=None)

        self.locker.lock('test_lock2', owner='unittest')
        with self.assertRaises(LockerException):
            self.locker.lock('test_lock2', owner='unittest', timeout=1)
        
        self.locker.release('test_lock2')
        with self.assertRaises(LockerException):
            self.locker.release('test_lock2')
        with self.assertRaises(LockerException):
            self.locker.release('test_lock3')
            
        with self.locker.lock_and_release('test_lock'):
            self._assert_lock('test_lock', locked=True)
        self._assert_lock('test_lock', locked=False)            

        # test expiration
        self.locker.lock('test_lock4', expire=1)
        time.sleep(2)
        self._assert_lock('test_lock4', locked=True, expire=1)
        with self.locker.lock_and_release('test_lock4', timeout=1, expire=2):
            self._assert_lock('test_lock4', locked=True, expire=2)
        self._assert_lock('test_lock4', locked=False)

        # test touching lock to prevent expiration
        self.locker.lock('test_lock4', expire=1)
        time.sleep(2)
        self._assert_lock('test_lock4', locked=True, expire=1)
        self.locker.touch('test_lock4')
        with self.assertRaises(LockerException):
            self.locker.lock('test_lock4', timeout=0.1)
        
        
if __name__ == '__main__':
    unittest.main()
