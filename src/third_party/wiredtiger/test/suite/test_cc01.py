#!/usr/bin/env python
#
# Public Domain 2014-present MongoDB, Inc.
# Public Domain 2008-2014 WiredTiger, Inc.
#
# This is free and unencumbered software released into the public domain.
#
# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, either in source code form or as a compiled
# binary, for any purpose, commercial or non-commercial, and by any
# means.
#
# In jurisdictions that recognize copyright laws, the author or authors
# of this software dedicate any and all copyright interest in the
# software to the public domain. We make this dedication for the benefit
# of the public at large and to the detriment of our heirs and
# successors. We intend this dedication to be an overt act of
# relinquishment in perpetuity of all present and future rights to this
# software under copyright law.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# [TEST_TAGS]
# checkpoint:checkpoint_cleanup
# [END_TAGS]

import time, wiredtiger, wttest
from wtdataset import SimpleDataSet
from wiredtiger import stat

# test_cc01.py
# Shared base class used by cc tests.
class test_cc_base(wttest.WiredTigerTestCase):

    def get_stat(self, stat, uri = ""):
        stat_cursor = self.session.open_cursor(f'statistics:{uri}')
        val = stat_cursor[stat][2]
        stat_cursor.close()
        return val

    def large_updates(self, uri, value, ds, nrows, commit_ts):
        # Update a large number of records.
        session = self.session
        cursor = session.open_cursor(uri)
        for i in range(0, nrows):
            session.begin_transaction()
            cursor[ds.key(i)] = value
            session.commit_transaction('commit_timestamp=' + self.timestamp_str(commit_ts))
        cursor.close()

    def large_modifies(self, uri, value, ds, location, nbytes, nrows, commit_ts):
        # Load a slight modification.
        session = self.session
        cursor = session.open_cursor(uri)
        session.begin_transaction()
        for i in range(0, nrows):
            cursor.set_key(i)
            mods = [wiredtiger.Modify(value, location, nbytes)]
            self.assertEqual(cursor.modify(mods), 0)
        session.commit_transaction('commit_timestamp=' + self.timestamp_str(commit_ts))
        cursor.close()

    def check(self, check_value, uri, nrows, read_ts):
        session = self.session
        session.begin_transaction('read_timestamp=' + self.timestamp_str(read_ts))
        cursor = session.open_cursor(uri)
        count = 0
        for k, v in cursor:
            self.assertEqual(v, check_value)
            count += 1
        session.rollback_transaction()
        self.assertEqual(count, nrows)

    # Trigger checkpoint cleanup. The function waits for checkpoint cleanup to make progress before
    # exiting.
    def wait_for_cc_to_run(self, ckpt_name = ""):
        c = self.session.open_cursor('statistics:')
        cc_success = prev_cc_success = c[stat.conn.checkpoint_cleanup_success][2]
        c.close()
        ckpt_config = "debug=(checkpoint_cleanup=true)"
        if ckpt_name:
            ckpt_config += f",name={ckpt_name}"
        self.session.checkpoint(ckpt_config)
        while cc_success - prev_cc_success == 0:
            time.sleep(0.1)
            c = self.session.open_cursor('statistics:')
            cc_success = c[stat.conn.checkpoint_cleanup_success][2]
            c.close()

    # Trigger checkpoint clean up and check it has visited and removed pages.
    def check_cc_stats(self, ckpt_name = ""):
        self.wait_for_cc_to_run(ckpt_name=ckpt_name)
        c = self.session.open_cursor('statistics:')
        self.assertGreaterEqual(c[stat.conn.checkpoint_cleanup_pages_visited][2], 0)
        self.assertGreaterEqual(c[stat.conn.checkpoint_cleanup_pages_removed][2], 0)
        c.close()

# Test that checkpoint cleans the obsolete history store pages.
class test_cc01(test_cc_base):
    # Force a small cache.
    conn_config = ('cache_size=50MB,eviction_updates_trigger=95,eviction_updates_target=80,'
                   'statistics=(all)')

    def test_cc(self):
        nrows = 10000

        # Create a table without logging.
        uri = "table:cc01"
        ds = SimpleDataSet(self, uri, 0, key_format="i", value_format="S")
        ds.populate()

        # Pin oldest and stable to timestamp 1.
        self.conn.set_timestamp('oldest_timestamp=' + self.timestamp_str(1) +
            ',stable_timestamp=' + self.timestamp_str(1))

        bigvalue = "aaaaa" * 100
        bigvalue2 = "ddddd" * 100
        self.large_updates(uri, bigvalue, ds, nrows, 10)

        # Check that all updates are seen.
        self.check(bigvalue, uri, nrows, 10)

        self.large_updates(uri, bigvalue2, ds, nrows, 100)

        # Check that the new updates are only seen after the update timestamp.
        self.check(bigvalue2, uri, nrows, 100)

        # Check that old updates are seen.
        self.check(bigvalue, uri, nrows, 10)

        # Pin oldest and stable to timestamp 100.
        self.conn.set_timestamp('oldest_timestamp=' + self.timestamp_str(100) +
            ',stable_timestamp=' + self.timestamp_str(100))

        # Trigger checkpoint cleanup and wait until it is done. This should clean the history store.
        self.check_cc_stats()

        # Check that the new updates are only seen after the update timestamp.
        self.check(bigvalue2, uri, nrows, 100)

        # Load a slight modification with a later timestamp.
        self.large_modifies(uri, 'A', ds, 10, 1, nrows, 110)
        self.large_modifies(uri, 'B', ds, 20, 1, nrows, 120)
        self.large_modifies(uri, 'C', ds, 30, 1, nrows, 130)

        # Second set of update operations with increased timestamp.
        self.large_updates(uri, bigvalue, ds, nrows, 200)

        # Check that the new updates are only seen after the update timestamp.
        self.check(bigvalue, uri, nrows, 200)

        # Check that the modifies are seen.
        bigvalue_modA = bigvalue2[0:10] + 'A' + bigvalue2[11:]
        bigvalue_modB = bigvalue_modA[0:20] + 'B' + bigvalue_modA[21:]
        bigvalue_modC = bigvalue_modB[0:30] + 'C' + bigvalue_modB[31:]
        self.check(bigvalue_modA, uri, nrows, 110)
        self.check(bigvalue_modB, uri, nrows, 120)
        self.check(bigvalue_modC, uri, nrows, 130)

        # Check that old updates are seen.
        self.check(bigvalue2, uri, nrows, 100)

        # Pin oldest and stable to timestamp 200.
        self.conn.set_timestamp('oldest_timestamp=' + self.timestamp_str(200) +
            ',stable_timestamp=' + self.timestamp_str(200))

        # Trigger checkpoint cleanup and wait until it is done. This should clean the history store.
        self.check_cc_stats()

        # Check that the new updates are only seen after the update timestamp.
        self.check(bigvalue, uri, nrows, 200)

        # Load a slight modification with a later timestamp.
        self.large_modifies(uri, 'A', ds, 10, 1, nrows, 210)
        self.large_modifies(uri, 'B', ds, 20, 1, nrows, 220)
        self.large_modifies(uri, 'C', ds, 30, 1, nrows, 230)

        # Third set of update operations with increased timestamp.
        self.large_updates(uri, bigvalue2, ds, nrows, 300)

        # Check that the new updates are only seen after the update timestamp.
        self.check(bigvalue2, uri, nrows, 300)

        # Check that the modifies are seen.
        bigvalue_modA = bigvalue[0:10] + 'A' + bigvalue[11:]
        bigvalue_modB = bigvalue_modA[0:20] + 'B' + bigvalue_modA[21:]
        bigvalue_modC = bigvalue_modB[0:30] + 'C' + bigvalue_modB[31:]
        self.check(bigvalue_modA, uri, nrows, 210)
        self.check(bigvalue_modB, uri, nrows, 220)
        self.check(bigvalue_modC, uri, nrows, 230)

        # Check that old updates are seen.
        self.check(bigvalue, uri, nrows, 200)

        # Pin oldest and stable to timestamp 300.
        self.conn.set_timestamp('oldest_timestamp=' + self.timestamp_str(300) +
            ',stable_timestamp=' + self.timestamp_str(300))

        # Trigger checkpoint cleanup and wait until it is done. This should clean the history store.
        self.check_cc_stats()

        # Check that the new updates are only seen after the update timestamp.
        self.check(bigvalue2, uri, nrows, 300)
