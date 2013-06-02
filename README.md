shotwell-db-org
===============

A quickly hacked tool to reorganise shotwell's photo directory structure.

This tool reads the shotwell photo photo organiser database and restructures
the photos into folders based on events defined in shotwell. This is
just a quick and dirty tool to work around a missing feature in shotwell
itself, which only allows to organise photos by their exposure date.

Beware of bugs in the code, I have not tested it throroughly. It just
worked well enough to reorganise my personal photo database. So please,
backup everything before running it. If you find any bugs, let
me know.

Quick Howto
===========

The script looks for the shotwell database at ~/.local/share/shotwell/data/photo.db.
If you use multiple databases or your system stores the database somewhere
else, you can use a command line parameter to set it. Assuming it is in
the standard location, you just need to pass the destination directory
of the freshly organised photo library. The call is then roughly

python organise-shotwell-database.py /path/to/new/photo/library

The other command line parameters are quite self-explanatory
