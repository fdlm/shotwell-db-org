import datetime as dt
import sys
import os
import sqlite3 as db
import shutil
from argparse import ArgumentParser

# TODO:
#       allow to choose between copy and move
#       make directory names for events with name and without name configurable

DB_FILE = os.path.join(os.getenv('HOME'), '.shotwell/data/photo.db')
DATE_FORMAT = '%Y-%m-%d'


def create_argparser():
    parser = ArgumentParser(description='Reorganises shotwell\' photo directories')
    parser.add_argument('destination_dir', help='Where to put the new photo directories')
    parser.add_argument('--database', '-d', default=DB_FILE, dest='database_file',
                        help='Path to shotwell\'s database file')
    parser.add_argument('--date-format', default=DATE_FORMAT, dest='date_format',
                        help='Date format, look up strftime for details.')

    return parser


def main():
    parser = create_argparser()
    args = parser.parse_args()

    db_file = args.database_file
    date_format = args.date_format
    dest_dir = args.destination_dir

    if not (os.path.exists(db_file) and os.path.isfile(db_file)):
        print("Database file does not exist.")
        return 1

    conn = db.connect(db_file)
    conn.row_factory = db.Row

    event_select = 'SELECT id, name FROM EventTable'
    photo_select = 'SELECT id, filename FROM PhotoTable WHERE event_id=?'
    event_time = 'SELECT min(timestamp) AS min_ts, max(timestamp) AS max_ts '\
                 'FROM PhotoTable WHERE event_id=?'

    photo_update = 'UPDATE PhotoTable SET filename=? WHERE id=?'

    for event in conn.cursor().execute(event_select):
        ts_cur = conn.cursor().execute(event_time, (event['id'],))
        min_ts, max_ts = ts_cur.fetchone()
        min_date = dt.date.fromtimestamp(min_ts)
        max_date = dt.date.fromtimestamp(max_ts)

        if event['name']:
            # we have an event name
            event_name = min_date.strftime(date_format) + ' - ' + event['name']
        else:
            # no event name
            event_name = min_date.strftime(date_format)
            if min_date != max_date:
                event_name += ' - ' + max_date.strftime(date_format)

        new_folder_name = os.path.join(dest_dir, event_name)
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
