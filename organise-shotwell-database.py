import argparse
import datetime as dt
import sys
import os
import sqlite3 as db
import shutil

# TODO: make root dir configurable
#       make destination dir optionally different from root dir
#       allow to choose between copy and move
#       make DB file configurable
#       make Date format configurable
#       make directory names for events with name and without name configurable

ROOT_DIR = '/home/felipe/Projekte/Programmieren/shotwell-events/photos'
DB_FILE = '/home/felipe/datadir/data/photo.db'
DATE_FORMAT = '%Y-%m-%d'


def main():
    conn = db.connect(DB_FILE)
    conn.row_factory = db.Row

    event_select = 'SELECT id, name FROM EventTable'
    photo_select = 'SELECT id, filename FROM PhotoTable WHERE event_id=?'
    event_time = 'SELECT min(timestamp) AS min_ts, max(timestamp) AS max_ts '\
                 'FROM PhotoTable WHERE event_id=?'

    photo_update = 'UPDATE PhotoTable SET filename=? WHERE id=?'

    for event in conn.cursor().execute(event_select):
        min_ts, max_ts = conn.cursor().execute(event_time, (event['id'],)).fetchone()
        min_date = dt.date.fromtimestamp(min_ts)
        max_date = dt.date.fromtimestamp(max_ts)

        if event['name']:
            # we have an event name
            event_name = min_date.strftime(DATE_FORMAT) + ' - ' + event['name']
        else:
            # no event name
            event_name = min_date.strftime(DATE_FORMAT)
            if min_date != max_date:
                event_name += ' - ' + max_date.strftime(DATE_FORMAT)

        new_folder_name = os.path.join(ROOT_DIR, event_name)
        if not os.path.exists(new_folder_name):
            os.mkdir(new_folder_name)

        for photo in conn.cursor().execute(photo_select, (event['id'],)):
            # create new file name
            old_path = photo['filename']
            filename = os.path.basename(old_path)
            new_path = os.path.join(new_folder_name, filename)

            if old_path != new_path:
                # move to new position
                shutil.move(old_path, new_path)

                # delete directory if empty
                old_dir = os.path.dirname(old_path)
                while os.listdir(old_dir) == []:
                    os.rmdir(old_dir)
                    old_dir = os.path.dirname(old_dir)

                # update database
                upd = conn.cursor()
                upd.execute(photo_update, (new_path, photo['id']))

    conn.commit()
    return 0


if __name__ == '__main__':
    sys.exit(main())
