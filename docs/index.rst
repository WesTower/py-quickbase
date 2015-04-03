.. py-quickbase documentation master file, created by
   sphinx-quickstart on Thu Mar 26 11:31:29 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

=============================================================
:mod:`py-quickbase` -- Python bindings for Intuit's QuickBase
=============================================================

.. module:: quickbase
            :synopsis: Python bindings for QuickBase's HTTP(S) API
.. moduleauthor:: Bob Uhl <robert.uhl@mastec.com>
.. moduleauthor:: Mike Safko <mike.safko@mastec.com>
.. moduleauthor:: Aaron Scott <aaron.scott@mastec.com>
.. moduleauthor:: Martin Pedersen <martin.pedersen@mastec.com>
.. moduleauthor:: Dan Pastusek <dan.pastusek@mastec.com>

Contents:

.. toctree::
   :maxdepth: 2

Usage
=====

.. function:: connect(url, username, password, [apptoken=None, hours=4])
              
   Connect to the QuickBase instance at *url* with the specified
   *username* & *password*.  *apptoken* is stored in the connection
   for future use, but is *not* validated against the QuickBase
   application.  If *hours* is given, then request that the returned
   ticket be valid for that many hours.  Returns an instance of the
   :class:`Connection` class.

   .. warning::

      *url* should be of the form 'https://example.quickbase.com/';
      future enhancement should use a URL library to Do the Right
      Thing.

.. class:: Connection

   A connection represents a persistent QuickBase connection.

   .. method:: do_query(dbid, [query=None, clist=None,
               slist=None, options={}, raw=False, fmt=None]):

      Execute `API_DoQuery
      <http://www.quickbase.com/api-guide/index.html#do_query.html>`_,
      by default returning a list of :class:`QuickBaseRecord`.  If the
      resulting reply is too big for QuickBase to return, it will
      split the result set in half and re-request, recursively.  This
      means that one shouldn't need to worry about too-large queries
      as a matter of course; note that it's more efficient to chunk
      the queries manually, as that will eliminate superfluous failed
      requests.

      *dbid*
         The QuickBase database ID.

      *query*
         The QuickBase query to execute With no *query*,
         :meth:`Connection.do_query()` will return all records in
         *dbid*.

         If *query* is an integer, then it represents a QuickBase
         query ID; otherwise, it's a string,
         e.g. ``"{'7'.EX.'Foobar'}"``.

      *clist*
         A QuickBase clist, i.e. a dot-delimited list of field IDs,
         e.g. ``'3.7.42'``.  *slist* is similar, but indicates the
         fields to sort by.

      *options*
         A dict representing the appropriate QuickBase options to
         pass; it is turned into a QuickBase option string via an
         arcane process (which is ripe for fixing).  If either
         ``'onlynew'`` or ``'nosort'`` is present, *even if its
         associated value is false*, then ``'onlynew'`` or
         ``'nosort'``, respectively, will be inserted into the option
         string.  All other keys and values will be inserted as
         hyphen-separated pairs.

      *raw*
         If ``True``, then :meth:`Connection.do_query()` returns the
         complete XML node structure as parsed by BeautifulSoup from
         the QuickBase response.

   .. method:: do_query_count(dbid, query=None, raw=False):

      Execute `API_DoQueryCount
      <http://www.quickbase.com/api-guide/index.html#do_query_count.html>`_,
      by default returning an integer indicating the number of records
      which would be returned by *query*.  If *raw* is ``True``, then the
      raw XML node tree of the response will be returned instead.

   .. method:: add_record(dbid, record, raw=False):

      Execute `API_AddRecord
      <http://www.quickbase.com/api-guide/index.html#add_record.html>`_
      to add a new record to the QuickBase table identified by *dbid*,
      returning a tuple containing the record ID and update ID of the
      new record, unless *raw* is ``True``, in which case the raw XML
      node tree of the response will be returned instead.

      *record* is a dict.  The keys are either integer field IDs or
      string field names.  The values are either string data or
      :class:`File` instances.

   .. method:: edit_record(dbid, record_id, values, raw=False):

      Execute `API_EditRecord
      <http://www.quickbase.com/api-guide/index.html#edit_record.html>`_
      to edit an existing record with the record ID *record_id* in the
      QuickBase table identified by *dbid*, returning a tuple
      containing the number of fields changed and the new update ID of
      the record, unless *raw* is ``True``, in which case the raw XML
      node tree of the response will be returned instead.  *values* is
      a dict in the same format as *record* as for
      :meth:`Connection.add_record()`.

.. class:: File(filename, data)

   Files have to be uploaded to QuickBase specially.  The path of least
   resistance was create a special class whose instance are recognized
   by :meth:`Connection:add_record()` and
   :meth:`Connection:edit_record()`.  Use by attaching it as one of
   the values in an add or edit dict.

   *filename* is the filename as it will appear in QuickBase.

   *data* is a string containing the contents of the file, as they
   will be uploaded to QuickBase.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

