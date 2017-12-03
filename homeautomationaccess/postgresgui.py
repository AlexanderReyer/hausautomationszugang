from 	flask	import 	Flask
from 	flask	import	request
from 	flask	import	make_response, render_template
import	psycopg2
import 	os
from 	urllib	import	parse


app = Flask(__name__)

dbconnection 	= None
dbcursor		= None

def connect_to_database(localhostname):
	global dbconnection
	global dbcursor
	
	if(localhostname == "nsamainframe"):
		dbconnection 	= psycopg2.connect("dbname='herokutest' user='postgres' host='localhost' password='postgres' port=5432")
	else:
		parse.uses_netloc.append("postgres")
		'''
		(venv) Z:\python\obscure-fortress-32728>heroku config
		=== obscure-fortress-32728 Config Vars
		DATABASE_URL: postgres://katznmraflxqax:361e0d8657a4709b7fd701949c796447e2ef9840a4edb83a9bb24440552a1e80@ec2-107-22-167-179.compute-1.amazonaws.com:5432/d57b0rvjm6l8ha
		TIMES:        66'''
		os.environ["DATABASE_URL"] = 'postgres://katznmraflxqax:361e0d8657a4709b7fd701949c796447e2ef9840a4edb83a9bb24440552a1e80@ec2-107-22-167-179.compute-1.amazonaws.com:5432/d57b0rvjm6l8ha'
		url = parse.urlparse(os.environ["DATABASE_URL"])

		dbconnection = psycopg2.connect(
						database=url.path[1:],
						user=url.username,
						password=url.password,
						host=url.hostname,
						port=url.port)

		print(
			url.path[1:],
			url.username,
			url.password,
			url.hostname,
			url.port)
	#Make sure you're using the right encodind by running: print conn.encoding, and if you need, 
	#you can set the right encoding by conn.set_client_encoding('UNICODE'), or conn.set_client_encoding('UTF8').
	dbconnection.set_client_encoding('UTF8')
	dbconnection.autocommit = True
	dbcursor 				= dbconnection.cursor()
	
	print(dbconnection.dsn)
	print(dbconnection.notices)

	return
	
def	close_database_connection():
	dbcursor.close()
	dbconnection.close()
	return



def create_table(tablename, dbcursor):
	result = dbcursor.execute("create table orte(orteid serial PRIMARY KEY, ort varchar(50) NOT NULL, dyndns varchar(50) NOT NULL)")
	print(result)

	
def	get_fetchallstring():
	global dbcursor
	rows = dbcursor.fetchall()
	result = ""
	print("rows: ", rows, "\r\n")
	for r in rows:
		print(r)
		for item in r:
			if item is not None:
				result += str(item) + str(" ")
		result += "<br>\r\n"
	return result
	
def show_public_tables():
	global dbcursor
	sqlquery = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
	result = dbcursor.execute(sqlquery)
	print(dbconnection.notices)
	return get_fetchallstring()

# --get_devices_values -------------------	
# select forwardport, dyndns, dialogflowname, herstellername 
# to be changed by webhook
# returns:  [(80, 'marssonde.ddns.org', 'wohnzimmerdeckenlampe', 'yeelight')]
def get_devices_values(ortnameparam, herstellernameparam, dialogflownameparam):
	# select forwardport, dyndns, dialogflowname, herstellername 
	# from devices 
	# inner join ort on ortname = 'steinburg' and devices.ortid = ort.ortid 
	# inner join hersteller on hersteller.herstellername = 'sonoff' and hersteller.herstellerid = devices.herstellerid 
	# inner join dialogflow on dialogflow.dialogflowid = devices.dialogflowid;
	global dbcursor
	sqlquery = "select forwardport, dyndns, dialogflowname, herstellername, yeelightid \
				 from devices \
				 inner join ort on ortname = '" + ortnameparam + "' and devices.ortid = ort.ortid \
				 inner join hersteller on hersteller.herstellername = '" + herstellernameparam + "' and hersteller.herstellerid = devices.herstellerid \
				 inner join dialogflow on dialogflow.dialogflowname = '" + dialogflownameparam + "' and dialogflow.dialogflowid = devices.dialogflowid;"
	print("sqlquery: ", sqlquery, "\r\n")
	dbcursor.execute(sqlquery)
	print(dbcursor.statusmessage)
	print("notices: ", dbconnection.notices, " count: ", dbcursor.rowcount)
	#result = get_fetchallstring()
	return dbcursor.fetchone()
	   
def show_tables():
	global dbcursor
	result = dbcursor.execute("select * from information_schema.tables")
	rows = dbcursor.fetchall()
	result = ""
	for r in rows:
		print(r)
		for item in r:
			if item is not None:
				result += str(item) + str(" ")
		result += "<br>\r\n"
		
	print(result)
	
	return result

def exec_query(sqlquery):
	global dbcursor
	result	= ""
	e 		= ""
	try:
		print("exec_query: " + sqlquery)
		dbcursor.execute(sqlquery)
		print("status : " + dbcursor.statusmessage)
		for note in dbconnection.notices:
			print("notices: " + note)
		if 0 < dbcursor.rowcount:
			rows = dbcursor.fetchall()
			result = ""
			for r in rows:
				print(r)
				for item in r:
					if item is not None:
						result += str(item) + str(" ")
				result += "<br>\r\n"
	except psycopg2.Error as e:
		print(e.diag.severity)
		print(str(e.pgerror))
		print(str(e.pgcode))
		result = str(e.diag.severity) + str(e.pgerror) + str(e.pgcode) #e.diag.message_primary)
		pass
	result += "<br>" + dbcursor.statusmessage
	return result
	

if __name__ == '__main__':
	app.run(debug=True)