# ALS data

Notes from August 2017, onwards, on ALS data work

Dan Gunter <dkgunter@lbl.gov>

## Setup

8/16/2017: Downloaded mongodump from /project dirs on NERSC: 
dump-20170622075506

8/18/2017: Set up 'alsdata' repository on Github at https://github.com/dangunter/alsdata

8/18/2017: Restore downloaded dump to local (laptop) MongoDB server.
Running mongodb 
  - Got an insertion error on the big DB (jobstatus), about 635K records in:

	$ mongorestore -d alsdata dump-20170622075506/alsdata/jobstatus.bson 
	...
	2017-08-18T03:44:06.162-0700	restoring alsdata.jobstatus from dump-20170622075506/alsdata/jobstatus.bson
	...
	2017-08-18T03:44:32.505-0700	[##......................]  alsdata.jobstatus  9.43GB/85.8GB  (11.0%)
	2017-08-18T03:44:32.505-0700	Failed: alsdata.jobstatus: error restoring from dump-20170622075506/alsdata/jobstatus.bson: insertion error: EOF
