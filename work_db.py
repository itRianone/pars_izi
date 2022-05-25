
import sqlite3
import datetime
from datetime import date, timedelta

con = sqlite3.connect(r'urls.sqlite3', check_same_thread=False)
cursor = con.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS urls(url text unique, date text)')

# cursor.execute('INSERT INTO urls_(url) VALUES (?)', ('http/url',))
con.commit()

def clear_db():
  data = cursor.execute('SELECT date FROM urls')
  urls = [url for url in data.fetchall()]
  last_date = urls[0][0]
  last_date = datetime.datetime.today() - datetime.timedelta(days=3)
  today = datetime.datetime.today()
  print((today - last_date).days)

# clear_db()

#def clear_db():
  # data = cursor.execute('SELECT date FROM urls')
  # urls = [url for url in data.fetchall()]
  # last_date = urls[0][0]
  # last_date = datetime.datetime.strptime(last_date, '%d.%m.%y')
  # #last_date = datetime.datetime.today() - datetime.timedelta(days=autocleaning_db_in_days)
  # today = datetime.datetime.today()


  # print(today, last_date, (today - last_date).days)
  # if (today - last_date).days > (autocleaning_db_in_days-1):
  #   cursor.execute('DROP TABLE urls;')