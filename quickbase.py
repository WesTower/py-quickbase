"""quickbase

A Pythonic interface to the QuickBase API.

"""

import os
import logging
import urllib2
import json
import csv

from bs4 import BeautifulSoup
from xml.dom import minidom



class Connection(object):
    """Represents a persistent QuickBase connection.  Implements the
    same interface as the v Ticket did, but with more options"""
    def __init__(self, url, userid, ticket, username, password, apptoken):
        self.url = url
        self.userid = userid
        self.ticket = ticket
        self.username = username
        self.password = password # remembered so we can relogin
        self.apptoken = apptoken
        return

    def do_query(self, dbid, query=None, clist=None, slist=None, options={}, raw=False, udata=None):
        """Execute API_DoQuery against the current QuickBase
        connection.  QUERY may be either a string query or an integer
        query ID.  If RAW is specified, return the raw BeautifulSoup
        XML node structure, otherwise return a list of
        QuickBaseRecords."""
        params = {'ticket':self.ticket}
        if self.apptoken:
            params['apptoken'] = self.apptoken
        if query:
            if type(query) == int:
                params['qid'] = str(query)
            else:
                params['query'] = query
        if clist:
            if type(clist) == str:
                params['clist'] = clist
            elif type(clist) == list:
                params['clist'] = '.'.join(clist)
        if slist:
            if type(slist) in (list, tuple):
                params['slist'] = '.'.join([str(fid) for fid in slist])
            elif type(slist) in (str, int):
                params['slist'] = str(slist)
        if options:
            if type(options) == dict:
                params['options'] = '.'.join('%s-%s' % (k,v) for k,v in options.items() if k != 'onlynew')
                if 'onlynew' in options:
                    params['options'] += ".onlynew"
            else:
                raise Exception("You passed a %s for options instead of a dict" % type(options))
        if udata:
            params['udata'] = udata

        results = []

        try:
            result = _execute_api_call(self.url+'db/'+dbid,
                                       'API_DoQuery',
                                       params)
            # by default, return a list of live QuickBaseRecords
            results += [QuickBaseRecord(dict((field.name, field.text) for field in record.findChildren())) for record in result.find_all('record')]

        except QuickBaseException as error:
            # If QuickBase returns a 'Request too large' error, 
            # then divide the last requested count in half and try again.
            if error.errcode == u'75':
                if options and 'num' in options:
                    count = int(options['num'])
                else:
                    count = self.do_query_count(dbid, query=query)

                new_count = count/2
                skp = options.get('skp', 0)
                    
                new_options = options.copy()
                new_options['num'] = new_count
                new_options['skp'] = skp

                results += self.do_query(dbid, query=query, clist=clist, slist=slist, options=new_options)

                # Increment skip to grab the second half
                skp += new_count
                new_options['skp'] = skp
                new_options['num'] = count - new_options['num']

                results += self.do_query(dbid, query=query, clist=clist, slist=slist, options=new_options)

                skp += new_count
                new_options['skp'] = skp

            else:
                raise(error)
        if raw:
            return result

        return results
    
    def do_query_count(self, dbid, query=None, raw=False):
        """QUERY is either a string indicating a query or an integer
        query ID."""
        params = {'ticket': self.ticket}
        if self.apptoken:
            params['apptoken'] = self.apptoken
        if query:
            if type(query) == int:
                params['qid'] = str(query)
            else:
                params['query'] = query
        result = _execute_api_call(self.url+'db/'+dbid,
                                   'API_DoQueryCount',
                                   params)
        if raw:
            return result
        return int(result.find('numMatches').text)

    def add_record(self, dbid, record, raw=False):
        """Add RECORD, a QuickBaseRecord or dict, to DBID.  If a key
        is an integer then it is a QuickBase field ID; if it is a
        string then it is a field name."""
        if not (isinstance(record, QuickBaseRecord) or isinstance(record, dict)):
            raise QuickBaseRecordException("record must be a QuickBaseRecord or dictionary")
        params = {'ticket': self.ticket}
        if self.apptoken:
            params['apptoken'] = self.apptoken

        for col in record.keys():
            if type(col) == int:
                params['_fid_'+str(col)] = record[col]
            else:
                params['_fnm_'+col] = record[col]
                
        result = _execute_api_call(self.url+'/db/'+dbid,
                                   'API_AddRecord',
                                   params)
        if raw:
            return result
        return (int(result.find('rid').text), result.find('update_id').text)

    def edit_record(self, dbid, record_id, values, raw=False):
        """VALUES is a QuickBaseRecord or dict; if a key is an integer
        then it is an FID; if it is text then it is a field name"""
        params = {'ticket': self.ticket,
                  'rid': record_id
                  }
        if self.apptoken:
            params['apptoken'] = self.apptoken
        for col in values.keys():
            if type(col) == int:
                params['_fid_'+str(col)] = values[col]
            else:
                params['_fnm_'+col] = values[col]
        results = _execute_api_call(self.url+'db/'+dbid,
                                    'API_EditRecord',
                                    params)
        if raw:
            return results
        return (int(results.find('num_fields_changed').text), results.find('update_id').text)

    def run_import(self, dbid, import_id, raw=False):
        params = {'ticket': self.ticket,
                  'id': import_id
                  }
        if self.apptoken:
            params['apptoken'] = self.apptoken
        result = _execute_api_call(self.url+'db/'+dbid, 'API_RunImport', params)
        if raw:
            return result
        return result.find('import_status').text

    def import_from_csv(self, dbid, csv_file, clist, encoding='utf-8', skipfirst=True, raw=False):
        outbound_csv_filepath = os.path.join(os.path.dirname(csv_file.name), 'csv_segment.csv')
        inbound_csv_reader = csv.reader(csv_file)
        
        header = inbound_csv_reader.next()
        outbound_csv = open(outbound_csv_filepath, 'wb')
        outbound_csv_writer = csv.writer(outbound_csv)
        outbound_csv_writer.writerow(header)
        
        count = 0
        num_recs_added = 0
        num_recs_input = 0
        num_recs_updated = 0
        records = []

        for row in inbound_csv_reader:
            outbound_csv_writer.writerow(row)
            count += 1

            if count % 5000 == 0: # every n rows write to file
                outbound_csv.close()

                results = self._import_from_csv(dbid, open(outbound_csv_filepath), clist, encoding, skipfirst, raw)
                num_recs_added += results['num_recs_added']
                num_recs_input += results['num_recs_input']
                num_recs_updated += results['num_recs_updated']
                records += results['records']
                print num_recs_input, num_recs_added, num_recs_updated, len(records)

                outbound_csv = open(outbound_csv_filepath, 'wb')
                outbound_csv_writer = csv.writer(outbound_csv)
                outbound_csv_writer.writerow(header)

        outbound_csv.close()

        if count % 5000 != 0:
            print count
            results = self._import_from_csv(dbid, open(outbound_csv_filepath), clist, encoding, skipfirst, raw)
            num_recs_added += results['num_recs_added']
            num_recs_input += results['num_recs_input']
            num_recs_updated += results['num_recs_updated']
            records += results['records']
            print num_recs_input, num_recs_added, num_recs_updated, len(records)

        os.remove(outbound_csv_filepath)
        return {'num_recs_added': num_recs_added,
                'num_recs_input': num_recs_input,
                'num_recs_updated': num_recs_updated,
                'records': records}

    def _import_from_csv(self, dbid, csv_file, clist, encoding='utf-8', skipfirst=True, raw=False):
        records_csv = ''.join(csv_file.readlines()).decode(encoding)
        params = {'ticket':self.ticket, 'clist':clist, 'records_csv':records_csv, 'skipfirst':'1' if skipfirst else '0'}
        if self.apptoken:
            params['apptoken'] = self.apptoken
        results = _execute_api_call(self.url+'db/'+dbid, 'API_ImportFromCSV', params)
        if raw:
            return results
        return {'num_recs_added': int(results.find('num_recs_added').text),
                'num_recs_input': int(results.find('num_recs_input').text),
                'num_recs_updated': int(results.find('num_recs_updated').text),
                'records': [(int(record.text), record.attrs['update_id']) for record in results.find_all('rid')]}
    
    """
    def import_from_csv(self, dbid, csv_file, clist, encoding='utf-8', skipfirst=True, raw=False):
        num_recs_added = 0
        num_recs_input = 0
        num_recs_updated = 0
        records = []
    
        csv_header = ""    
        csv_list = []
        index = 0
        max_row_count = 1000
    
        for row in csv_file:
            if not csv_header:
                csv_header = row
                csv_list.append( csv_header )
            else:
                index += 1
                csv_list.append( row )
                if index == max_row_count:
                    print "records to import: " + str(len(csv_list))
                    results = self.import_from_list(dbid, csv_list, clist, encoding, skipfirst, raw)
                    num_recs_added += results['num_recs_added']
                    num_recs_input += results['num_recs_input']
                    num_recs_updated += results['num_recs_updated']
                    records += results['records']

                    index = 0
                    csv_list = []
                    csv_list.append( csv_header )

        if index > 0:
            print "records to import: " + str(len(csv_list))
            results = self.import_from_list(dbid, csv_list, clist, encoding, skipfirst, raw)
            num_recs_added += results['num_recs_added']
            num_recs_input += results['num_recs_input']
            num_recs_updated += results['num_recs_updated']
            records += results['records']

        return {'num_recs_added': num_recs_added,
                'num_recs_input': num_recs_input,
                'num_recs_updated': num_recs_updated,
                'records': records}

    def import_from_list(self, dbid, csv_list, clist, encoding='utf-8', skipfirst=True, raw=False ):
        records_csv = ''.join(csv_list).decode(encoding)
        params = {'ticket':self.ticket, 'clist':clist, 'records_csv':records_csv, 'skipfirst':'1' if skipfirst else '0'}
        if self.apptoken:
            params['apptoken'] = self.apptoken
        results = _execute_api_call(self.url+'db/'+dbid, 'API_ImportFromCSV', params)
        if raw:
            return results
        num_recs_added = results.find('num_recs_added')
        if num_recs_added:
            num_recs_added = int(num_recs_added.text)
        else:
            num_recs_added = 0
        num_recs_input = results.find('num_recs_input')
        if num_recs_input:
            num_recs_input = int(num_recs_input.text)
        else:
            num_recs_input = 0
        num_recs_updated = results.find('num_recs_updated')
        if num_recs_updated:
            num_recs_updated = int(num_recs_updated.text)
        else:
            num_recs_updated = 0
        return {'num_recs_added': num_recs_added,
                'num_recs_input': num_recs_input,
                'num_recs_updated': num_recs_updated,
                'records': [(int(record.text), record.attrs['update_id']) for record in results.find_all('rid')]}
    """

    def download(self, dbid, rid, fid, vid="0"):
        url = '%sup/%s/a/r%s/e%s/v%s?ticket=%s&apptoken=%s' % (self.url, dbid, rid, fid, vid, self.ticket, self.apptoken)
        return urllib2.urlopen(url)

class QuickBaseRecord(object):
    """Simple dict-like object which may be accessed as
    INSTANCE['record_id_'] or as INSTANCE.record_id_.  Implements
    Python container interface but NOT .iterkeys()."""
    def __init__(self, fields):
        object.__setattr__(self, '_fields', fields)
        return

    def __getattr__(self, attr):
        return self._fields[attr]

    def __setattr__(self, attr, value):
        self._fields[attr] = value

    def __getitem__(self, attr):
        return self._fields[attr]

    def __setitem__(self, attr, value):
        self._fields[attr] = value

    def __iter__(self):
        return self._fields.iterkeys()

    def __contains__(self, x):
        return x in self._fields

    def _keys(self):
        return self._fields.keys()

def diff_records(r1, r2):
    diffs = {}
    for key in record.keys():
        if key not in self._fields.keys():
            raise QuickBaseRecordException('compare contains key not found in initial QuickBaseRecord: "%s"' % key, self)
        else:
            if record[key] != self._fields[key]:
                diffs[key] = (self._fields[key], record[key])

    
    r1_keys = r1._keys() if isinstance(r1, QuickBaseRecord) else r1.keys()
    r2_keys = r2._keys() if isinstance(r2, QuickBaseRecord) else r2.keys()


    return diffs
            
class QuickBaseException(Exception):
    def __init__(self, response):
        Exception.__init__(self, str(response))
        self.response = response
        self.errcode = response.errcode.string
        self.errtext = response.errtext.string
        self.errdetail = response.errdetail.string
   
class QuickBaseRecordException(Exception):
    def __init__(self, message, record=None):
        Exception.__init__(self, message)
        self.record = record

    def __str__(self):
        if self.record:
            self.message += '\n'+json.dumps(self.record._fields)
        return self.message

def connect(url, username, password, apptoken=None, hours=4):
    """Connect to the QuickBase instance at URL (FIXME: of the form
    'https://westower.quickbase.com/', without the /db/ or other
    portions) with the specified USERNAME & PASSWORD.  If HOURS is
    given, pass that on.  APPTOKEN is stored in the connection for
    future use, but is NOT validated against the QuickBase
    application."""
    # FIXME: properly extend url
    # FIXME: validate hours
    response = _execute_api_call(url + 'db/main',
                                'API_Authenticate',
                                {'username':username,
                                 'password':password,
                                 'hours':hours,
                                 })
    return Connection(url, response.userid.string, response.ticket.string, username, password, apptoken)

def _execute_raw_api_call(url, api_call, parameters):
    """Execute an api call API_CALL on URL.  PARAMETERS is a
    dictionary, e.g. {'username':'foo', 'password':'bar'}."""
    xml = minidom.Document()
    qdbapi = xml.createElement('qdbapi')
    xml.appendChild(qdbapi)
    for key in parameters:
        element = xml.createElement(key)
        if type(parameters[key]) == File:
            if element.tagName.startswith('_fnm_'):
                element.setAttribute('name', element.tagName[5:])
            else:
                element.setAttribute('fid', element.tagName[5:])
            element.tagName = 'field'
            element.setAttribute('filename', parameters[key].filename)
        qdbapi.appendChild(element)
        text = xml.createTextNode(unicode(parameters[key]))
        element.appendChild(text)
    logging.debug('creating request')
    #print xml.toxml('utf-8')
    request = urllib2.Request(url,
                              data=xml.toxml('utf-8'),
                              headers={'QUICKBASE-ACTION':api_call,
                                       'Content-Type':'application/xml',
                                       })
    #consider a @retry decorator to had some robustness again random network errors
    response = urllib2.urlopen(request)
    return response.readlines()


def _execute_api_call(url, api_call, parameters):
    response = BeautifulSoup(''.join(_execute_raw_api_call(url, api_call, parameters)), 'xml')
    logging.debug('request returned')
    if response.qdbapi.errcode.string != u'0':
        raise QuickBaseException(response.qdbapi)
    return response.qdbapi


class File(object):
    def __init__(self, filename, data):
        self.filename = filename
        self.data = data
        return

    def __unicode__(self):
        return unicode(base64.b64encode(self.data))
