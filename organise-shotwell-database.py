import datetime as dt
import sys
import os
import sqlite3 as db
import shutil
from argparse import ArgumentParser

# TODO:
#       allow to choose between copy and move
#       make directory names for events with name and without name configurable

DB_FILE = os.path.join(os.getenv('HOME'), '.local/share/shotwell/data/photo.db')
DATE_FORMAT = '%Y-%m-%d'


def create_argparser():
    parser = ArgumentParser(description='Reorganises shotwell\' photo directories')
    parser.add_argument('destination_dir', help='Where to put the new photo directories')
    parser.add_argument('--database', '-d', default=DB_FILE, dest='database_file',
                        help='Path to shotwell\'s database file')
    parser.add_argument('--date-format', default=DATE_FORMAT, dest='date_format',
                        help='Date format, look up strftime for details.')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--copy', '-c', action='store_const', const=shutil.copy2,
                       default=shutil.move, help='Copy images instead of moving',
                       dest='file_operator')
    group.add_argument('--no-clean', '-nc', action='store_const', const=False,
                       default=True, help='Do not remove empty photo directories',
                       dest='clean')

    return parser


def main():
    parser = create_argparser()
    args = parser.parse_args()

    db_file = args.database_file
    date_format = args.date_format
    dest_dir = args.destination_dir
    process_file = args.file_operator
    clean_dirs = args.clean

    if not (os.path.exists(db_file) and os.path.isfile(db_file)):
        sys.stderr.write("Database file %s does not exist." % db_file)
        return 1

    if not (os.path.exists(dest_dir) and os.path.isdir(dest_dir)):
        sys.stderr.write("Invalid destination directory '%s'." % dest_dir)
        return 2

    conn = db.connect(db_file, isolation_level=None)
    conn.row_factory = db.Row

    event_select = 'SELECT id, name FROM EventTable'
    photo_select = 'SELECT id, filename FROM PhotoTable WHERE event_id=? UNION ALL '\
                   'SELECT id, filename FROM VideoTable WHERE event_id=?'
    event_timestamp = 'SELECT count(*) AS cnt, min(timestamp) AS min_ts, max(timestamp) AS max_ts FROM PhotoTable '\
                 'WHERE event_id=?'
    event_exposure_time = 'SELECT count(*) AS cnt, min(exposure_time) as min_et, max(exposure_time) as max_et FROM PhotoTable WHERE event_id=? AND exposure_time > 0'
    photo_update = 'UPDATE PhotoTable SET filename=? WHERE id=?'

    events = conn.cursor().execute(event_select).fetchall()
    for event in events:
        print 'Processing event', event['id'], ',', event['name']
        exp_cnt, min_et, max_et = conn.cursor().execute(event_exposure_time, (event['id'],)).fetchone()
        if exp_cnt > 0:
            min_date = dt.date.fromtimestamp(min_et)
            max_date = dt.date.fromtimestamp(max_et)
        else:
            cnt, min_ts, max_ts = conn.cursor().execute(event_timestamp, (event['id'],)).fetchone()
            if cnt == 0:
                continue

            min_date = dt.date.fromtimestamp(min_ts)
            max_date = dt.date.fromtimestamp(max_ts)

        if event['name']:
            # we have an event name
            event_name = min_date.strftime(date_format) + ' - ' + event['name'].replace('/', '-')
        else:
            # no event name
            event_name = min_date.strftime(date_format)
            if min_date != max_date:
                event_name += ' - ' + max_date.strftime(date_format)

        new_folder_name = os.path.join(dest_dir, event_name)
        if not os.path.exists(new_folder_name):
            os.mkdir(new_folder_name)

        photos = conn.cursor().execute(photo_select, (event['id'],event['id'])).fetchall()

        for photo in photos:
            # create new file name
            old_path = photo['filename']
            filename = os.path.basename(old_path)
            new_path = os.path.join(new_folder_name, filename)

            if old_path != new_path:
                dupl = 1
                while os.path.exists(new_path):
                    name, ext = os.path.splitext(filename)
                    name += '_%d' % dupl
                    dupl += 1
                    new_path = os.path.join(new_folder_name, name + ext)
                print new_path
                # update database
                upd = conn.cursor()
                upd.execute(photo_update, (new_path, photo['id']))

                # move to new position
                process_file(old_path, new_path)

                # conn.commit()

                if clean_dirs:
                    # delete directory if empty
                    old_dir = os.path.dirname(old_path)
                    while os.listdir(old_dir) == []:
                        os.rmdir(old_dir)
                        old_dir = os.path.dirname(old_dir)

    return 0


if __name__ == '__main__':
    sys.exit(main())
