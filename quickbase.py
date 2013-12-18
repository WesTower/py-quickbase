"""quickbase

A Pythonic interface to the QuickBase API.

"""

import logging
import urllib2

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

    def do_query(self, dbid, query=None, clist=None, slist=None, options=None, raw=False):
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
            if type(slist) in (list, tuple):
                params['options'] = '.'.join(option for option in options)
            elif type(options) == str:
                params['options'] = options
        result = _execute_api_call(self.url+'db/'+dbid,
                                   'API_DoQuery',
                                   params)
        if raw:
            return result
        # by default, return a list of live QuickBaseRecords
        return [QuickBaseRecord(dict((field.name, field.text) for field in record.findChildren())) for record in result.find_all('record')]
    
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
            raise Exception("record must be a QuickBaseRecord or dictionary")
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


class QuickBaseException(BaseException):
    def __init__(self, response):
        self.response = response
        return

    def __str__(self):
        return str(self.response)


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
