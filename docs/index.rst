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

   .. method:: do_query(self, dbid, [query=None, clist=None,
               slist=None, options={}, raw=False, fmt=None]):

      Execute API_DoQuery, by default returning a list of :class:`QuickBaseRecord`.

      *dbid* is a QuickBase database ID.

      With no *query*, :meth:`Connection.do_query()` will return all
      records in *dbid*.

      If *query* is an integer, then it represents a QuickBase query
      ID; otherwise, it's a string, e.g. ``"{'7'.EX.'Foobar'}"``.

      *clist* is a QuickBase clist, i.e. a dot-delimited list of field
      IDs, e.g. ``'3.7.42'``.  *slist* is similar, but indicates the
      fields to sort by.

      *options* is a dict; it is turned into a QuickBase option string
      via an arcane process (which is ripe for fixing).  If either
      ``'onlynew'`` or ``'nosort'`` is present, *even if its
      associated value is false*, then ``'onlynew'`` or ``'nosort'``,
      respectively, will be inserted into the option string.  All
      other keys and values will be inserted as hyphen-separated
      pairs.

      If *raw* is true, then :meth:`Connection.do_query()` returns
      the complete XML node structure as parsed by BeautifulSoup from
      the QuickBase response.

.. class:: File


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

