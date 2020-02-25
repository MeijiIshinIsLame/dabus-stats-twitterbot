import os
import psycopg2
from datetime import datetime
from pytz import timezone

ssl_cert_path = "client-cert.pem"
ssl_key_path = "client-key.pem"
ssl_root_cert_path = "server-ca.pem"

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
	except:
		create_ssl_certs()

	try:
		conn = psycopg2.connect(database=str(os.environ["DB_NAME"]),
							user=str(os.environ["DB_USERNAME"]),
							password=str(os.environ["DB_PASSWORD"]),
							host=str(os.environ["DB_HOSTNAME"]),
							port=str(os.environ["DB_PORT"]),
							sslcert=ssl_cert_path,
							sslmode=str(os.environ["SSL_MODE"]),
							sslrootcert=ssl_root_cert_path,
							sslkey=ssl_key_path)
		c = conn.cursor()
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