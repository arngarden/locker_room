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
            
        
