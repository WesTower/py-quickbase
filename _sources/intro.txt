.. py-quickbase - Python bindings for Intuit's QuickBase
   Copyright (C) 2012-2014 WesTower Communications
   Copyright (C) 2014-2015 MasTec
   
   This file is part of py-quickbase.
   
   py-quickbase is free software: you can redistribute it and/or
   modify it under the terms of the GNU Lesser General Public License
   as published by the Free Software Foundation, either version 3 of
   the License, or (at your option) any later version.
   
   This program is distributed in the hope that it will be useful, but
   WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
   Lesser General Public License for more details.
   
   You should have received a copy of the GNU Lesser General Public
   License along with this program.  If not, see
   <http://www.gnu.org/licenses/>.

Introduction
============

py-quickbase provides easy-to-use bindings to Intuit's `QuickBase API
<http://www.quickbase.com/api-guide/index.html>`_.  QuickBase is a
Web-accessible non-SQL relational database.  While it does have some
limitations and quirks, it is an extremely effective tool for rapid
prototyping and development of end-user business applications.

We've used py-quickbase at WesTower Communications and its acquirer
MasTec since summer 2012; it's been through three major internal
revisions and has been battle-hardened through extensive use and
debugging.  Our hope is that it will prove useful to other QuickBase
users.

py-quickbase does not implement every QuickBase API call, but simply
those which we needed over the past several years.  There's still
plenty more to be added by the enterprising developer.

Project History
---------------

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
