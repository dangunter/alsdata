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

## Experiments / plans

### Classify the diversity of the schemas

8/18/2017: The plan is to set up a pipeline that extracts all the distinct types of documents from each collection. What we want in the end is a list, per-collection, of N schemas. Now, the tricky part is that we want to show the variations in an easy to
digest form.

As a first pass, show a "tree" of the fields/types.

	{"address": {"street": "123 fake street", "city": "berkeley"}}
	{"address": {"street": "123 fake street", "city": "berkeley", "zip": 97402}}
	{"addresses" [ {"address": {"street": "123 fake street", "city": "berkeley"}}]}
	{"address": {"street": "123 fake street", "city": "berkeley", "zip": 97402}, "phone": {"office": "510-111-1111"}}

Could yield (compact form)

	2 address{street:str, city:str, zip:int<1>}
	1 addresses[:{address{street:str, city:str}}]
	1 address{street:str, city:str, zip:int}, phone{office:str}

8/20/17

On further thought, a "significant" difference is hard to say offhand, and confusing to represent in a tree-diff form. So, I took a simpler and faster approach. I wrote code to extract a document into an internal representation that is easily "diffed" against another such representation. Initially, the only averaging is to combine repeated scalar values in an array into a single type, e.g.

	{"a": [1,2,3,4, "a"]} => a is an array with types "int" and "str"

8/22/17

On further-further thought, this scalar combination is a subset of the full problem of combining array entries. For example,
if I had two documents

	{"numbers": [ {"num": 1, "name": "one"}, {"num": 2, "name": "two"} ]}
	and
	{"numbers": [ {"num": 3, "name": "three"}, {"num": 4, "name": "four"},  {"num": 5, "name": "five"}]}

I would like to say these are the same schema. This will work if I am able to recognize similarities both between items
in the list and between the lists in the different documents.

So, this seems to work now in the code..

