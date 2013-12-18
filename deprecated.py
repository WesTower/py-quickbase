'''deprecated.py implements the v1 API in terms of the v2 API; it
cannot be relied upon past version 2'''

from xml.dom import minidom
import urllib2
#from BeautifulSoup import BeautifulStoneSoup
from bs4 import BeautifulSoup
import tempfile
import csv
import logging
import ConfigParser
import os.path
import re
import base64
import quickbase



def get_table_schema(ticket, apptoken, table):
    raise Exception("Not reimplemented yet")
    logging.info('getting schema for table %s', table)
    return _parse_table_schema(_execute_api_call(host + '/db/' + table,
                                                 'API_GetSchema',
                                                 {'ticket':ticket.ticket,
                                                  'apptoken':apptoken,
                                                  }))


def _parse_table_schema(schema):
    """Turn an XML table schema into an object tree"""
    logging.debug('parsing table schema')
    variables = {}
    # for var in schema.table.variables:
    #     if hasattr(var, 'name'):
    #         variables[var['name']] = var.string
    ## oddly, the query information returned from QuickBase changed;
    ## this old code may come in handy again if it changes back
    # queries = []
    # for query in schema.table.queries:
    #     if hasattr(query, 'id'):
    #         print dir(query.qytype)
    #         queries.append({'id':query['id'],
    #                         'name':query.qyname.string,
    #                         'type':query.qytype.string,
    #                         'criterion':query.qycrit.string,
    #                         'calst':query.qycrit.calst})
    fields = []
    for field in schema.table.fields:
        if hasattr(field, 'id'):
            f = {'id':int(field['id']),}
            ## below find the more-complex field information QuickBase
            ## might return; I believe it doesn't do this reliably
            # f = {'id':field['id'],
            #      'type':field['field_type'],
            #      'base_type':field['base_type'],
            #      'role':field['role']}
            for prop in field:
                if hasattr(prop, 'text'):
                    f[prop.name] = prop.string
                    ## below see an example of fetching extended field properties
                    # print prop.name, prop.string
                    #        'label':field.label.string,
                    #        'nowrap':field.nowrap.string,
                    #        'bold':field.bold.string,
                    #        'required':field.required.string
                else:
                    # FIXME: handle multiple choices
                    pass
            f['field_type'] = field['field_type']
            fields.append(f)
    desc = schema.table.find('desc')
    if desc:
        desc = desc.string
    return {
        'name':schema.table.find('name').string,
        'desc':desc,
        'id':schema.table.original.table_id.string,
        'variables':variables,
        #'queries':queries,
        'fields':fields,
        }


def _clone_table(database, table, ticket, apptoken):
    """Not for use--in development"""
    # FIXME: set pnoun of newly-created table; no doc appears to cover this
    # pull DATABASE's information
    db = Application(ticket, database, apptoken)
    # if TABLE is not in DATABASE: error
    if table not in db.schema()['tables'].values():
        raise QuickBaseException('%s not found in %s' % (table, database))
    # pull TABLE's information
    # FIXME: abstract away
    table_schema = _execute_api_call(host + '/db/' + table,
                                     'API_GetSchema',
                                     {'ticket':ticket.ticket,
                                      'apptoken':apptoken,
                                      })
    #print parse_table_schema(table_schema)
    # if TABLE.name + ' copy' is in DATABASE, drop it
    # create TABLE.name + ' copy'
    # for each variable set in TABLE, call API_SetDBvar
    # for each field in TABLE, call API_AddField to add it to the copy
    # pull all fields of TABLE as a CSV
    # load all fields into copy from CSV
    pass


def get_database_schema(ticket, apptoken, database):
    raise Exception("Not reimplemented yet")
    logging.debug('getting schema for %s', database)
    return _parse_database_schema(_execute_api_call(host + '/db/' + database,
                                                   'API_GetSchema',
                                                   {'ticket':ticket.ticket,
                                                    'apptoken':apptoken,
                                                    }))


def _parse_database_schema(xml):
    """Parse an XML database schema as returned by QuickBase into a structure of the form:

{'name':'FooBase',
 'tables':{'_dbid_english_name':'bxcwsdlg',
           '_dbif_another_db':'bghgjwkf',
           },
}
"""
    logging.debug('parsing database schema')
    schema = {'name':xml.table.find('name').string,}
    schema['tables'] = {}
    for table in xml.table.chdbids:
        if hasattr(table, 'name'):
            schema['tables'][table['name']] = table.string
    return schema


def report_too_large_p(raw_result):
    """Returns True if RAW_RESULT contains a QuickBase error message.
    This might fail if QuickBase changes their error report format."""
    # FIXME: ugly NOTting here...use DeMorgan's to prettify
    return not ('<font face="verdana,arial,geneva,helvetica">' not in raw_result[0] \
        and (len(raw_result) < 5 \
                 or '<td colspan="2"><font color=red size=+1>Report too large</font></td>' \
                 not in raw_result[4]))


def dump_table(ticket, apptoken, table, columns, outcsv):
    raise Exception("Not reimplemented yet")
    """Dump TABLE to OUTCSV, a csv.Writer.  Should correctly handle
    even very large tables, very large rows and very large columns."""
    logging.debug('dumping %s', columns)
    
    # try to get the entire table with one request; if that fails, try
    # to get half the columns and then the other half of the columns,
    # then stitch the two data sets together
    result = _execute_raw_api_call(ticket.url + '/db/' + table, 
                                   'API_GenResultsTable',
                                   {'clist':'.'.join(['%d' % int(x) for x in columns]),
                                    'options':'csv',
                                    'slist':'3',
                                    'ticket':ticket.ticket,
                                    'apptoken':apptoken})
    if not report_too_large_p(result):
        logging.debug('got entire table in one go')
        reader = csv.reader(result)
        for row in reader:
            outcsv.writerow(row)
        return
    
    # couldn't read it in one go; switching to stitching
    if len(columns) == 1:
        # If we're at the point of trying to retrieve a single column
        # and _still_ find that it's too big, it's no longer possible
        # to subdivide the list of columns to retrieve--but we can try
        # to get half of the rows in the column, then the other half
        # the rows in the column, and stitch _that_ file together.  To
        # do this, we grab the first and the last record ID, divide by
        # half and try to fetch each half (assuming that the record
        # IDs are evenly scattered throughout the range); if either
        # fetch fails, we divide _that_ into halves and try again.

        first = int(_execute_api_call(ticket.url + '/db/' + table, 
                                      'API_DoQuery',
                                      {'clist':'3',
                                       'options':'num-1.sortorder-A',
                                       'slist':'3',
                                       'fmt':'structured',
                                       'ticket':ticket.ticket,
                                       'apptoken':apptoken}).table.records.record.f.string)
        last = int(_execute_api_call(ticket.url + '/db/' + table, 
                                     'API_DoQuery',
                                     {'clist':'3',
                                      'options':'num-1.sortorder-D',
                                      'slist':'3',
                                      'fmt':'structured',
                                      'ticket':ticket.ticket,
                                      'apptoken':apptoken}).table.records.record.f.string)
        # don't know the actual name of the column at this point; it's
        # not worth another API roundtrip, since we don't use the name
        # for anything; but need to have some value in the first line of the CSV file
        outcsv.writerow(['dummy header'])
        def retrieve_column(i, j):
            logging.debug("{'3'.GTE.'%d'}AND{'3'.LT.'%d'}" % (i, j))
            result = _execute_raw_api_call(ticket.url + '/db/' + table, 
                                           'API_GenResultsTable',
                                           {'clist':columns[0],
                                            'query':"{'3'.GTE.'%d'}AND{'3'.LT.'%d'}" % (i, j),
                                            'options':'csv',
                                            'slist':'3',
                                            'ticket':ticket.ticket,
                                            'apptoken':apptoken})
            logging.debug(len(result))

            
            if not report_too_large_p(result):
                reader = csv.reader(result)
                throwaway_header = reader.next()
                for row in reader:
                    outcsv.writerow(row)
                return
            if i == j:
                # this is not good at all: a single datum in a row is too large to download
                raise QuickBaseException('Row %d, column %d of table %s is too large to download' % (i, columns[0], table))
            retrieve_column(i, i + (j-i)//2)
            retrieve_column(i + (j-i)//2, j)
        retrieve_column(first, first + (last-first)//2)
        retrieve_column(first + (last-first)//2, last+1)
        return

    file1 = tempfile.TemporaryFile()
    writer1 = csv.writer(file1)
    file2 = tempfile.TemporaryFile()
    writer2 = csv.writer(file2)
    dump_table(ticket, apptoken, table, columns[0:len(columns)//2], writer1)
    dump_table(ticket, apptoken, table, columns[len(columns)//2:], writer2)
    # now that the files have been read, rewind them, read them and
    # copy into OUTCSV.  Remember to pad any missing fields with blanks
    file1.seek(0)
    reader1 = csv.reader(file1)
    header1 = reader1.next()
    num1 = len(header1)
    file2.seek(0)
    reader2 = csv.reader(file2)
    header2 = reader2.next()
    num2 = len(header2)
    outcsv.writerow(header1 + header2)
    for row1 in reader1:
        row2 = reader2.next()
        # add padding, since trailing empty fields are truncated in CSV
        row1 += [''] * (num1 - len(row1))
        row2 += [''] * (num2 - len(row2))
        outcsv.writerow(row1 + row2)
    return


def add_row(ticket, apptoken, table, row):
    """ROW is a dict; if a key is an integer then it is an FID; if it
    is text then it is a field name"""
    # the v1 ticket parameter is really a Connection instance now
    connection = ticket
    # save the old apptoken value
    old_apptoken = connection.apptoken
    try:
        connection.apptoken = apptoken
        return connection.add_record(table, record=row, raw=True)
    finally:
        connection.apptoken = old_apptoken


def execute_query_count(ticket, apptoken, table, query=None):
    """QUERY is either a string indicating a query or an integer query ID"""
    # the v1 ticket parameter is really a Connection instance now
    connection = ticket
    # save the old apptoken value
    old_apptoken = connection.apptoken
    try:
        connection.apptoken = apptoken
        return connection.do_query_count(table, query=query, raw=True)
    finally:
        connection.apptoken = old_apptoken

def execute_query(ticket, apptoken, table, query=None, clist=None, slist=None, options=None):
    """QUERY is either a string indicating a query or an integer query ID"""
    # the v1 ticket parameter is really a Connection instance now
    connection = ticket
    # save the old apptoken value
    old_apptoken = connection.apptoken
    try:
        connection.apptoken = apptoken
        results = connection.do_query(dbid=table, query=query, clist=clist, slist=slist, options=options, raw=True)
        return results
    finally:
        connection.apptoken = old_apptoken


def add_or_replace_page(ticket, apptoken, dbid, pathname, pagename):
    raise Exception("Not reimplemented yet")
    return _execute_api_call(ticket.url + '/db/' + dbid, 'API_AddReplaceDBPage', {'pagename':pagename, 
                                                                                  'pagetype':'1', 
                                                                                  'pagebody':open(pathname).read().decode('utf8'),
                                                                                  'ticket':ticket.ticket,
                                                                                  'apptoken':apptoken,
                                                                                  })

def empty_table(ticket, apptoken, table):
    raise Exception("Not reimplemented yet")
    return _execute_api_call(ticket.url + '/db/' + table, 'API_PurgeRecords', {'ticket':ticket.ticket,
                                                                               'apptoken':apptoken,
                                                                               })
def edit_record(ticket, apptoken, table, record, values):
    # the v1 ticket parameter is really a Connection instance now
    connection = ticket
    # save the old apptoken value
    old_apptoken = connection.apptoken
    try:
        connection.apptoken = apptoken
        return connection.edit_record(table, record, values, raw=True)
    finally:
        connection.apptoken = old_apptoken


def import_from_csv(ticket, apptoken, table, csv_file, clist, encoding='utf-8'):
    connection = ticket
    old_apptoken = connection.apptoken
    
    try:
        connection.apptoken = apptoken
        return connection.import_from_csv(dbid=table, csvfile=csv_file, clist=clist, encoding=encoding, skipfirst=True, raw=True)
    finally:
        connection.apptoken = old_apptoken


def label_to_name(label):
    return re.sub('[^a-zA-z0-9]', '_', label.lower())

def delete_record(ticket, apptoken, table, rid):
    raise Exception("Not reimplemented yet")
    params = {'ticket': ticket.ticket,
              'apptoken': apptoken,
              'rid': rid}
    return _execute_api_call(ticket.url+'db/'+table,
                             'API_DeleteRecord',
                             params)


class File(object):
    def __init__(self, filename, data):
        self.filename = filename
        self.data = data
        return

    def __unicode__(self):
        return unicode(base64.b64encode(self.data))

def change_record_owner(ticket, apptoken, table, record, owner):
    params = {'ticket': ticket.ticket,
              'apptoken': apptoken,
              'rid': record,
              'newowner': owner
              }
    return _execute_api_call(ticket.url + 'db/' + table, 'API_ChangeRecordOwner', params)
