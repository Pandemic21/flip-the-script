import praw
import sqlite3
import time
import random

# Functions
#perform_action(message)
#add_submission(message, user)
#shuffle_and_send()
#get_row_exists(table, column, value)
#get_column_by_user(table, column, user)
#gen_log(data)
#initialization()


def perform_action(message):
	#submission
	if message.subject == text_submission:
		gen_log(str(message.author) + ' sent a submission')
		if get_row_exists("submissions", "user", str(message.author)):
			gen_log(str(message.author) + ' already sent a submission, rejecting...')
			message.reply("Your submission was rejected as you already sent a submission on " + str(get_column_by_user("submissions","date",str(message.author))))
			return
		add_submission(message, message.author)

	#check submission
	elif message.subject == text_check_submission:
		gen_log(str(message.author) + ' issued a check submission for ' + message.body)
		#if they are checking somebody else's submission and not an admin
		if message.body != str(message.author) and str(message.author).upper() not in admins:
			gen_log(str(message.author) + ' issued a submission check by proxy command and is NOT an admin')
			message.reply("You cannot check somebody else's submission, as you are not an admin.")
			return
		#make 
		if not get_row_exists("submissions", "user", message.body):
			gen_log(str(message.author) + ' has no current submission')
			message.reply('No submission found for "' + message.body + '"')
			return 
		submission = get_column_by_user("submissions", "submission", str(message.author))
		message.reply('Here is ' + message.body + '\'s submission:\n\n' + submission)

	#submission removal
	elif message.subject == text_submission_removal:
		gen_log(str(message.author) + ' issued a submission removal for ' + message.body)
		#if they are checking somebody else's submission and not an admin
		if message.body != str(message.author) and str(message.author).upper() not in admins:
			gen_log(str(message.author) + ' issued a submission removal by proxy command and is NOT an admin')
			message.reply("You cannot remove somebody else's submission, as you are not an admin.")
			return
		#if they have no submission
		if not get_row_exists("submissions", "user", message.body):
			gen_log('No submission found for ' + message.body)
			message.reply("No submission found for " + message.body)
			return
		c.execute("DELETE FROM submissions WHERE user=?", (message.body,))
		conn.commit()
		message.reply(message.body + "'s submission has been removed.")

	#shuffle and send lyrics
	elif message.subject == text_shuffle_and_send:
		if str(message.author).upper() not in admins:
			gen_log(str(message.author) + ' issued a shuffle and send command and is NOT an admin')
			message.reply("This function requires admin privileges and you are not an admin.")
			return
		gen_log(str(message.author) + ' issued a shuffle and send command successfully')
		shuffle_and_send()
		
	#else, they sent gibberish
	else:
		#is not an admin
		if str(message.author).upper() not in admins:
			gen_log(str(message.author) + ' sent gibberish and is not an admin. Body = "' + message.body + '" created_utc = ' + str(time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(message.created_utc))))
			message.reply(text_gibberish)
			return
		#is an admin
		gen_log(str(message.author) + ' sent gibberish and is an admin. Subject = "' + message.subject + '", Body = "' + message.body + '"')
		message.reply(text_gibberish_admin)
		

def add_submission(message, user):
	gen_log(str(message.author) + "'s submission was accepted")
	c.execute("INSERT INTO submissions VALUES (?,?,?)", (str(user), str(message.body), str(time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(message.created_utc))),))
	conn.commit()
	message.reply("Your submission was accepted!")


def shuffle_and_send():
	c.execute("SELECT * FROM submissions")
	rows = c.fetchall()
	shuffled_rows = []
	for row in rows:
		c.execute("INSERT INTO historical_submissions VALUES (?,?,?)", (row[0], row[1], row[2],))
		shuffled_rows.append(row[0])
	conn.commit()
	#drop old submissions
	c.execute("DELETE FROM submissions")
	conn.commit()
	#shuffle submissions
	random.shuffle(shuffled_rows)
	done = False
	gen_log("Shuffling...")
	while not done:
		done = True
		for k in range(0, len(rows)):	
			if shuffled_rows[k] == rows[k][0]:
				done = False
				random.shuffle(shuffled_rows)
				break
	results = "Results of shuffle:"
	for k in range(0, len(rows)):
		results = results + "\n" + rows[k][0] + " --> " + shuffled_rows[k]
		r.send_message(shuffled_rows[k], "Here's the script from " + rows[k][0], rows[k][1]) #TODO: uncomment me to send the scripts
	gen_log(results)


def get_row_exists(table, column, value):
	c.execute("SELECT count(*) FROM "+table+" WHERE "+column+"=?", (value,))
	data = c.fetchone()[0]
	if data==0:
		return False
	else:
		return True


def get_column_by_user(table, column, value):
	c.execute("SELECT "+column+" FROM "+table+" WHERE user=?", (value,))
	return c.fetchone()[0]
	

def gen_log(data):
	f = open(LOGFILE, 'a')
	datetime =  str(time.strftime("%Y/%m/%d")) + " " + str(time.strftime("%H:%M:%S"))
	f.write(datetime + ": " + data + "\n")
	f.close()
	print datetime + ": " + data


def initialization():
	gen_log("Starting ......................")
	#create tables if they don't exist
	c.execute("CREATE TABLE IF NOT EXISTS submissions (user text, submission text, submission_date text)")
	c.execute("CREATE TABLE IF NOT EXISTS historical_submissions (user text, submission text, submission_date text)")
	conn.commit()
	r = praw.Reddit("Flip the Script by /u/pandemic21")
	r.login(USERNAME,PASSWORD,disable_warning="True")
	f = open(ADMINSFILE, 'r')
	for admin in f:
		admins.append(admin.upper().strip())
		gen_log('added admin: "' + admin.upper().strip() + '"')
	return r


# MAIN ###########################################################################

# Constants
USERNAME=""
PASSWORD=""
LOGFILE='/home/pandemic/Documents/scripts/lyrics/lyrics.log'
ADMINSFILE='/home/pandemic/Documents/scripts/lyrics/admins.txt'
admins = []
conn = sqlite3.connect('/home/pandemic/Documents/scripts/lyrics/lyrics.db')
c = conn.cursor()
r = initialization()

# Strings
text_submission = "add submission"
text_check_submission = "check submission"
text_submission_removal = "remove submission"
text_shuffle_and_send = "shuffle and send"
text_gibberish = 'Please send me a valid command. Valid commands are: \n\n* Sending a submission: have the subject as "add submission" and the body as your submission.\n* Remove submission: have the subject as "remove submission" and the body as your name.\n* Check submission: have the subject as "check submission" and the body as your name.'
text_gibberish_admin = text_gibberish + '\n\nValid admin commands are: \n\n* Send out submissions: have the subject as "shuffle and send"\n\nAdditionally, all admins can issue "check submission" and "remove submission" commands for any user, just change the body to the user whose submission you want to check or remove.'

# Main
while True:
	messages = r.get_unread()

	for message in messages:
		perform_action(message)	
		message.mark_as_read()
	time.sleep(30)
