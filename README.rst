"py-quickbase" -- Python bindings for Intuit's QuickBase
********************************************************

* Introduction

  * Project History

* Usage

* License


Indices and tables
==================

* Index

* Module Index

* Search Page

Introduction
************

py-quickbase provides easy-to-use bindings to Intuit's QuickBase API.
QuickBase is a Web-accessible non-SQL relational database.  While it
does have some limitations and quirks, it is an extremely effective
tool for rapid prototyping and development of end-user business
applications.

We've used py-quickbase at WesTower Communications and its acquirer
MasTec since summer 2012; it's been through three major internal
revisions and has been battle-hardened through extensive use and
debugging.  Our hope is that it will prove useful to other QuickBase
users.

py-quickbase does not implement every QuickBase API call, but simply
those which we needed over the past several years.  There's still
plenty more to be added by the enterprising developer.


Project History
===============

   2012-06
      Bob Uhl first writes py-QuickBase while part of Systems
      Development at WesTower Communications

   2013-10
      Systems Development becomes Operations Systems Development (OSD)

   2013-12
      OSD team merges all software into a common repository

   2014-10
      MasTec acquires WesTower Communications; OSD becomes part of
      MasTec IT

   2015-04
      MasTec IT open-sources py-quickbase

Usage
*****

connect(url, username, password[, apptoken=None, hours=4])

   Connect to the QuickBase instance at *url* with the specified
   *username* & *password*.  *apptoken* is stored in the connection
   for future use, but is *not* validated against the QuickBase
   application.  If *hours* is given, then request that the returned
   ticket be valid for that many hours.  Returns an instance of the
   "Connection" class.

   Warning: *url* should be of the form
     'https://example.quickbase.com/'; future enhancement should use a
     URL library to Do the Right Thing.

class class Connection

   A "Connection" represents a persistent QuickBase connection.

   do_query(dbid, [query=None, clist=None,
   slist=None, options={}, raw=False, fmt=None]):

      Execute API_DoQuery, by default returning a list of
      "QuickBaseRecord".  If the resulting reply is too big for
      QuickBase to return, it will split the result set in half and
      re-request, recursively.  This means that one shouldn't need to
      worry about too-large queries as a matter of course; note that
      it's more efficient to chunk the queries manually, as that will
      eliminate superfluous failed requests.

      *dbid*

         The QuickBase database ID.

      *query*

         The QuickBase query to execute With no *query*,
         "Connection.do_query()" will return all records in *dbid*.

         If *query* is an integer, then it represents a QuickBase
         query ID; otherwise, it's a string, e.g.
         ""{'7'.EX.'Foobar'}"".

      *clist*

         A QuickBase clist, i.e. a dot-delimited list of field IDs,
         e.g. "'3.7.42'".  *slist* is similar, but indicates the
         fields to sort by.

      *options*

         A dict representing the appropriate QuickBase options to
         pass; it is turned into a QuickBase option string via an
         arcane process (which is ripe for fixing).  If either
         "'onlynew'" or "'nosort'" is present, *even if its associated
         value is false*, then "'onlynew'" or "'nosort'",
         respectively, will be inserted into the option string.  All
         other keys and values will be inserted as hyphen-separated
         pairs.

      *raw*

         If "True", then "Connection.do_query()" returns the complete
         XML node structure as parsed by BeautifulSoup from the
         QuickBase response.  One should not normally need to do this,
         but it does come in handy sometimes when debugging
         particularly hairy issues.

   do_query_count(dbid, query=None, raw=False):

      Execute API_DoQueryCount, by default returning an integer
      indicating the number of records which would be returned by
      *query*.  If *raw* is "True", then the raw XML node tree of the
      response will be returned instead.

   add_record(dbid, record, raw=false):

      execute api_addrecord to add a new record to the quickbase table
      identified by *dbid*, returning a tuple containing the record id
      and update id of the new record, unless *raw* is "true", in
      which case the raw xml node tree of the response will be
      returned instead.

      *record* is a dict.  the keys are either integer field ids or
      string field names.  the values are either string data or "File"
      instances.

   edit_record(dbid, record_id, values, raw=False):

      Execute API_EditRecord to edit an existing record with the
      record ID *record_id* in the QuickBase table identified by
      *dbid*, returning a tuple containing the number of fields
      changed and the new update ID of the record, unless *raw* is
      "True", in which case the raw XML node tree of the response will
      be returned instead.  *values* is a dict in the same format as
      *record* as for "Connection.edit_record()".

   delete_record(dbid, record_id, raw=False):

      Execute API_DeleteRecord to delete record ID *record_id* from
      QuickBase table *dbid*, returning the record ID of the deleted
      record, unless *raw* is "True", in which case the raw XML node
      tree of the response will be returned instead.

   run_import(dbid, import_id, raw=False):

      Execute API_RunImport to run a saved table-to-table import in
      Quickbase identified by *import_id*, returning the
      *import_status*, unless *raw* is "True", in which case the raw
      XML node tree of the response will be returned instead.
      "Connection.run_import()".

   import_from_csv(dbid, csv_file, clist, encoding='utf-8', skipfirst=True, raw=False, split=5000):

      Execute API_ImportFromCSV to add or update records in QuickBase
      table *dbid*, by default returning a dict with the keys
      *num_recs_added*, *num_recs_input*, *num_recs_updated* and
      *records*; the first three are all integers and the last is a
      list of (record ID, update ID) tuples.  If *raw* is "True", then
      the raw XML node tree of the response will be returned instead.

      Since QuickBase can choke on too-large imports, *split*
      indicates how many records at a time should be uploaded.  Across
      the data we've normally been importing, 5,000 was a decent
      number; YMMV.

      *csv_file*

         An open file-like object to be passed to "csv.reader()".

      *clist*

         A standard QuickBase column list, used to indicate which
         fields are to be imported.

      *encoding*

         A Python encoding string (e.g. 'utf-8') used to decode the
         data after it's read in by "csv.reader.readlines()".

      *skipfirst*

         Whether the first row of data in the CSV file should be
         skipped.  Should be set to "False" if one's CSV doesn't have
         a header line.

   download(dbid, rid, fid, vid="0"):

      http://quickbase.intuit.com/developer/articles/downloading-
      files>`_ to download an attached file in the Quickbase table
      identified by *dbid*, for the record ID *rid*, field ID *fid*
      and verion ID *vid*, where the default version ID of "0"
      downloads the latest version. "Connection.download()".

   user_roles(dbid, raw=False):

      Execute API_UserRoles to request the list of users and their
      roles in the QuickBase application identified by *dbid*,
      returning a list of users as dicts. If *raw* is "True", then the
      raw XML node tree of the reponse will be returned instead.
      "Connection.edit_record()".

   add_user_to_role(dbid, userid, roleid):

      Execute API_AddUserToRole to add a user with ID *userid* to the
      role with ID *roleid* for the Quickbase application identified
      by *dbid*. "Connection.add_user_to_role()".

   remove_user_from_role(dbid, userid, roleid):

      Execute API_RemoveUserFromRole to remove a user with ID *userid*
      from the role with ID *roleid* for the Quickbase application
      identified by *dbid*. "Connection.remove_user_to_role()".

   get_schema(dbid, [raw=False]):

      Execute API_GetSchema, returning a "TableInfo" object associated
      with QuickBase table *dbid*.  "Connection.get_schema()" can be
      given a *dbid* pointing to a single table or a full app. If the
      *dbid* passed is a table, the response will contain a list of
      fields, among other info. If the *dbid* passed is an app, the
      response will contain a list of chdbids (child dbids), but will
      not be useful as a "TableInfo" object, and thus must be given
      *raw* = "True" if the intent is to access the chdbid info.

      *dbid*

         The QuickBase database ID.

      *raw*

         If "True", then "Connection.get_schema()" returns the
         complete XML node structure as parsed by BeautifulSoup from
         the QuickBase response.

class class TableInfo

   A representation of the QuickBase table that makes schema data
   easily accessible.

class class QuickBaseRecord

   A "QuickBaseRecord" represents a single QuickBase record. It's a
   dict-like object which allows accessing fields as both items and
   attributes, although it doesn't implement "iterkeys()". Each
   QuickBase field is accessible with its field label, e.g.
   "record.record_id_" or "record['record_id_']" will both be the
   'Record Id#' field.  There is also a special field _fields, which
   records the record's data.

   Warning: QuickBase allows the definition of multiple fields with
     different names but the same label, e.g. two fields named "foo+"
     and "foo*" will have the same label "foo_". "QuickBaseRecord"
     does not support this.  A future enhancement should allow
     accessing fields by name as well as label using the dict-like
     syntax.

class class File(filename, data)

   Files have to be uploaded to QuickBase specially.  The path of
   least resistance was create a special class whose instance are
   recognized by "Connection:add_record()" and
   "Connection:edit_record()".  Use by attaching it as one of the
   values in an add or edit dict.

   *filename* is the filename as it will appear in QuickBase.

   *data* is a string containing the contents of the file, as they
   will be uploaded to QuickBase.

License
*******

Copyright (C) 2012-2014 WesTower Communications Copyright (C)
2014-2015 MasTec

py-quickbase is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this program.  If not, see
<http://www.gnu.org/licenses/>.
