Locker Room
===========

Locker Room is a shared lock manager that uses MongoDB to store the locks.
This makes it possible for resources on a network to share the same locks.

Usage
-----------

    import locker_room
    locker = locker_room.LockerRoom(host='server1')
    
    with locker.lock_and_release('my_lock', owner='gustav', timeout=2, expire=60):
        # do important stuff

It is also possible to use the locker as a function decorator:
 
    @locker.lock_and_release('my_lock'):
    def important_function():
        # do important stuff

Or you can call the lock and release-methods explicitly:

    locker.lock('my_lock', timeout=2)
    # do stuff
    locker.release('my_lock')
    
To find out the status of a lock, use the status-method:
    
    locker.status('my_lock')
    >> {u'owner': u'gustav', u'timestamp': datetime.datetime(2014, 4, 17, 14, 6, 8, 291000), 
        u'_id': u'my_lock',  u'locked': True}

The optional expire-parameter can be used to set a limit (in seconds) for how long a lock can be held before
the lock holder is assumed to be dead and the lock can then be stolen by the next requester.
By calling the touch-method a long-lived process can delay the expiration.

Setup and requirements
----------------------

Locker Room needs access to MongoDB.

For function decorator to work you need contextlib2, if you are using Python 2.7.
