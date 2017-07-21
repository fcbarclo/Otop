# Otop
it's a curses client-server app for linux, to take a real-time quick look to major kpi (key performance indicator) of a running oracle database (rac and standalone).

OS/Python/Oracle system requirements: 
- CPython 2.7 (not tested with > 2.7)
- Oracle client,  or instant client, better if 12c version
- Oracle server 12c version (soon 11g and 10g)
- python cx_oracle module (tested with >= 5.2)
- set LD_LIBRARY_PATH to ORACLE_HOME libs directory  into user's profile starting Otop.py

Oracle dbms requirements:
- oracle database user with CONNECT and SELECT_CATALOG_ROLE granted

Edit Otop.py  and put the db data connection into LoginInfo[] struct.

Set terminal (rows,cols) size to (39,174) for default output, and to (39,232) for  more details.

Start Otop.py


[Watch demo ](https://youtu.be/FzfSzVO7JHo)
