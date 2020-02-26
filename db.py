import os
import random
import time
import psycopg2
from datetime import datetime, timedelta
from pytz import timezone

ssl_cert_path = "client-cert.pem"
ssl_key_path = "client-key.pem"
ssl_root_cert_path = "server-ca.pem"

def connect_to_database():
	conn = psycopg2.connect(database=str(os.environ["DB_NAME"]),
							user=str(os.environ["DB_USERNAME"]),
							password=str(os.environ["DB_PASSWORD"]),
							host=str(os.environ["DB_HOSTNAME"]),
							port=str(os.environ["DB_PORT"]),
							sslcert=ssl_cert_path,
							sslmode=str(os.environ["SSL_MODE"]),
							sslrootcert=ssl_root_cert_path,
							sslkey=ssl_key_path)
	return conn

def create_ssl_certs():
	with open(ssl_cert_path, 'w+') as f:
		f.write(os.environ["SSL_CERT"])

	with open(ssl_key_path, 'w+') as f:
		f.write(os.environ["SSL_KEY"])

	with open(ssl_root_cert_path, 'w+') as f:
		f.write(os.environ["SSL_ROOT_CERT"])

def get_prompts():
	conn = None
	prompts_unweighted = []
	prompts_weighted = []

	try:
		file = open(ssl_cert_path, 'r')
		file.close()

		file = open(ssl_key_path, 'r')
		file.close()

		file = open(ssl_root_cert_path, 'r')
		file.close()
	except:
		create_ssl_certs()

	try:
		conn = connect_to_database()
		cur = conn.cursor()
		cur.execute("SELECT prompt, weight FROM tweet_prompts")

		row = cur.fetchone()
		while row is not None:
			prompt = row[0]
			weight = row[1]
			prompts_unweighted.append(prompt)
			prompts_weighted.extend([prompt] * int(weight))
			row = cur.fetchone()
		cur.close()

	except (Exception, psycopg2.DatabaseError) as error:
		print(error)
	finally:
		if conn is not None:
			conn.close()
		return prompts_unweighted, prompts_weighted

def get_first_date():
	conn = None
	try:
		conn = connect_to_database()
		cur = conn.cursor()
		cur.execute("SELECT insertdate FROM arrivals LIMIT 1")

		first_date = cur.fetchone()
		cur.close()

	except (Exception, psycopg2.DatabaseError) as error:
		print(error)
	finally:
		if conn is not None:
			conn.close()
		return first_date[0]

def get_random_date():
	#date_format = "%m-%d-%Y"
	first_date = get_first_date()
	yesterday = datetime.now(timezone('US/Hawaii')).date() - timedelta(days=1)
	prop =  random.random()

	ptime = first_date + prop * (yesterday - first_date)
	return ptime #.strftime(date_format)

def fetch_results_from_date(date_object):
	conn = None
	results = ()
	try:
		conn = connect_to_database()
		cur = conn.cursor()

		cur.execute("SELECT * FROM arrivals WHERE insertdate=%s", (date_object,))
		results = cur.fetchall()
		cur.close()
	except (Exception, psycopg2.DatabaseError) as error:
		print(error)
	finally:
		if conn is not None:
			conn.close()
		return results

def get_random_stop(result_list):
	random_entry = random.choice(result_list)
	stop = random_entry[2]
	return stop

def build_tweet_from_weighted_list(prompts_unweighted, prompts_weighted):
	prompt = random.choice(prompts_weighted)

	if prompt == prompts_unweighted[0]:
		random_date = get_random_date()
		results = fetch_results_from_date(random_date)
		stop = get_random_stop(results)

		num_of_arrivals = 0
		for entry in results:
			if entry[2] == stop:
				num_of_arrivals += 1

		namespace = {"num_of_arrivals": num_of_arrivals, "stop": stop.strip('\n'), "date": random_date}
		tweet = prompt.format(**namespace)

		print(tweet)

prompts_unweighted, prompts_weighted = get_prompts()

while True:
	build_tweet_from_weighted_list(prompts_unweighted, prompts_weighted)
	time.sleep(5)