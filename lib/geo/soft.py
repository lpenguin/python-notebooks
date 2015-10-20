import sys
from optparse import OptionParser
import re
import os
import os.path
import sqlite3

# GEO SOFT format is documented here:
# http://www.ncbi.nlm.nih.gov/projects/geo/info/soft2.html#SOFTformat

# ID field in platform joins with ID_REF field in samples

entity = re.compile(r'\^(\S+) = (.+)')
kvp = re.compile(r'!(\S+) = (.+)')

STATE_START = 0
STATE_IN_SERIES = 1001
STATE_IN_PLATFORM = 1002
STATE_IN_SAMPLE = 1003


def overwrite(name):
    if os.path.exists(name):
        os.remove(name)
        return True
    return False


def parse_series_file(file, conn):
    entity_id = None
    state = STATE_START

    # create an attributes table
    try:
        cursor = conn.cursor()
        cursor.execute('create table attributes (entity_id, key, value);')
        conn.commit()
        cursor.close()
    finally:
        cursor.close()

    for line in file:
        line = line.strip()

        # read entity tags
        if line.startswith('^'):
            m = entity.match(line)
            if m:
                entity_type = m.group(1)
                entity_id = m.group(2)
                print(entity_id)
                if entity_type == 'SERIES':
                    state = STATE_IN_SERIES
                elif entity_type == 'PLATFORM':
                    state = STATE_IN_PLATFORM
                elif entity_type == 'SAMPLE':
                    state = STATE_IN_SAMPLE

        # read attribute key-value pairs and tab-separated tables
        elif line.startswith('!'):
            m = kvp.match(line)
            if m:
                key = m.group(1)
                value = m.group(2)
                handle_attribute(conn, entity_id, key, value)
            elif state == STATE_IN_PLATFORM and line == '!platform_table_begin':
                parse_platform_table(file, conn, entity_id)
            elif state == STATE_IN_SAMPLE and line == '!sample_table_begin':
                parse_sample_table(file, conn, entity_id)


def parse_platform_table(file, conn, platform_id):
    """
 Read the tab-separated platform section of a SOFT file and store the ID,
 sequence, strand, start, and end columns in a SQLite database.

 file: a file object open for reading
 conn: a SQLite database connection
 platform_id: a string identifying a GEO platform
 """
    cursor = conn.cursor()
    try:
        # throw away line containing column headers
        file.readline()
        # create platform table
        cursor.execute(
            'create table %s (id text primary key not null, sequence text not null, \
            strand not null, start integer not null, end integer not null, control_type integer);' % (
            platform_id))
        conn.commit()
        sql = 'insert into %s values(?,?,?,?,?,?)' % (platform_id)
        for line in file:
            line = line.strip('\n')
            if (line.strip() == '!platform_table_end'):
                break
            fields = line.split("\t")
            # print(fields)
            cursor.execute(sql, (fields[0], fields[6], fields[10], fields[7], fields[8], fields[4]))
        conn.commit()
    finally:
        cursor.close()


def parse_sample_table(file, conn, sample_id):
    """
 Read a tab separated sample section from a SOFT file and store ID_REF and
 value in a SQLite DB.

 file: a file object open for reading
 conn: a SQLite database connection
 sample_id: a string identifying a GEO sample
 """
    cursor = conn.cursor()
    try:
        # throw away line containing column headers
        file.readline()
        # create sample table
        cursor.execute('create table %s (id_ref text not null, value numeric not null);' % (sample_id))
        conn.commit()
        sql = 'insert into %s values(?,?)' % (sample_id)
        for line in file:
            line = line.strip('\n')
            if (line.strip() == '!sample_table_end'):
                break
            fields = line.split("\t")
            cursor.execute(sql, (fields[0], float(fields[1])))
        conn.commit()
    finally:
        cursor.close()


def handle_attribute(conn, entity_id, key, value):
    """
 Store an entity attribute in the attributes table
 """
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("insert into attributes values(?,?,?);", (entity_id, key, value))
        conn.commit()
    finally:
        if cursor:
            cursor.close()


def main():
    usage = "%prog [options] input_file"
    parser = OptionParser(usage=usage)
    parser.add_option("-o", "--overwrite", dest="overwrite", default=False, action="store_true",
                      help="if output db file exists, overwrite it")
    (options, args) = parser.parse_args()
    print(options)
    print(args)
    # parser.error("missing required arguments.")
    if len(args) < 2:
        exit(2)

    input_filename = args[0]
    db_filename = args[1]

    if options.overwrite:
        overwrite(db_filename)

    input_file = None
    conn = None
    try:
        conn = sqlite3.connect(db_filename)
        input_file = open(input_filename, 'r')
        parse_series_file(input_file, conn)
    finally:
        if input_file:
            input_file.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    sys.exit(main())
