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
import locker_room
from locker_room import LockerException


class TestLock(unittest.TestCase):
    def setUp(self):
        self.locker = locker_room.LockerRoom(db='locks_test')

    def tearDown(self):
        self.locker.lock_collection.drop()

    def test_lock(self):
        self.locker.lock('test_lock', owner='unittest', timeout=1)
        status = self.locker.status('test_lock')
        self.assertTrue(status['locked'])
        self.assertEqual(status['owner'], 'unittest')        
        self.locker.release('test_lock')
        status = self.locker.status('test_lock')
        self.assertFalse(status['locked'])
        self.assertTrue(status['owner'] is None)

        self.locker.lock('test_lock2', owner='unittest')
        with self.assertRaises(LockerException):
            self.locker.lock('test_lock2', owner='unittest', timeout=1)
        
        self.locker.release('test_lock2')
        with self.assertRaises(LockerException):
            self.locker.release('test_lock2')
        with self.assertRaises(LockerException):
            self.locker.release('test_lock3')
            
        with self.locker.lock_and_release('test_lock'):
            status = self.locker.status('test_lock')
            self.assertTrue(status['locked'])
        status = self.locker.status('test_lock')
        self.assertFalse(status['locked'])
            
        
