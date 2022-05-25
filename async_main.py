import asyncio
import re
import sqlite3
import time
from unicodedata import category
from requests_html import AsyncHTMLSession, HTMLSession
from bs4 import BeautifulSoup
import datetime
import sys
from work_db import cursor, con
from fake_useragent import UserAgent

pause_between_ask = 0.5
search_deep = 100
highest_plank_of_goods = 10
lowest_plank_of_goods = 0
start_time = time.time()
sellers_we_already_have = []
autocleaning_db_in_days = 6
bad_qualities = ['Новое']#

while True:
    try: 
      
      how_much_results_need = int(input('Число объявлений >> '))
      break
    except: 
      print('Invalid type, try again')
    
requests_list = {'c-36-zhenskaya-odezhda': 'Женская одежда',


                 'c-80-aksessuary': 'Аксессуары',
                 'c-50-zhenskaya-obuv': 'Женская обувь',
                 'c-71-muzhskaya-obuv': 'Мужская обувь',
                 'c-99-odezhda-i-aksessuary-prochee': 'Одежда и аксессуары, прочее',
                 'c-61-muzhskaya-odezhda': 'Мужская одежда',
                 'c-176-odezhda-dlya-devochek': 'Одежда для девочек',
                 'c-190-odezhda-dlya-malyshey': 'Одежда для малышей',
                 'c-163-odezhda-dlya-malchikov': 'Одежда для мальчиков',
                 'c-270-razvitie-i-tvorchestvo': 'Развитие и творчество',
                 'c-256-igrushki': 'Игрушки',
                 'c-507-kompyutery-i-komplektuyushchie': 'Компьютеры и комплектующие',
                 'c-489-telefony-i-aksessuary': 'Телефоны и аксессуары',
                 'c-536-tv-i-videotekhnika': 'TV и видеотехник',
                 'c-494-bytovaya-tekhnika': 'Телефоны и аксессуары',
                 'c-494-bytovaya-tekhnika': 'Бытовая техника',
                 'c-555-elektronika-prochee': 'Электроника, прочее',
                 'c-544-audiotekhnika': 'Аудиотехника',
                 'c-899-kuritelnie-prinadlezhnosti': 'Курительные принадлежности',
                 'c-351-knigi-i-zhurnaly': 'Книги и журналы',
                 'c-364-rukodelie': 'Рукоделие',
                 'c-310-aktivnie-igry': 'Активные игры',
                 'c-897-intimnie-tovary': 'Интимные товары',
                 'c-3-parfyumeriya': 'Парфюмерия',
                 'c-14-kosmetika-po-ukhodu': 'Косметика по уходу',
                 'c-25-tovary-dlya-zdorovya': 'Товары для здоровья',
                 'c-438-domashniy-tekstil': 'Домашний текстиль',
                 'c-449-interer': 'Интерьер',
                 'c-462-osveshchenie': 'Освещение',
                 'c-656-promyshlennoe-oborudovanie': 'Промышленное оборудование',
                 'c-775-syre': 'Сырье',
                 'c-729-oborudovanie-dlya-sfery-uslug': 'Оборудование для сферы услуг',
                 'c-755-izmeritelnoe-oborudovanie': 'Измерительное оборудование'}
ua = UserAgent()

today_date = datetime.datetime.now()

yesterday = today_date - datetime.timedelta(days=1) 
day_before_yesterday = today_date - datetime.timedelta(days=2) 
today_date = today_date.strftime('%d.%m.%y')
yesterday = yesterday.strftime('%d.%m.%y')
day_before_yesterday = day_before_yesterday.strftime('%d.%m.%y')

nice_dates = [today_date,
yesterday,
day_before_yesterday]


res_counter = 0

"""
    НУ ПАРСИНГ СТРАНИЦЫ СООТВЕТСВЕННО(С КАЖДОЙ СТРАНИЦЫ
    ВЫДАЮТСЯ ССЫЛКИ НА ТАВАРЫ С АЙДИШНИКАМИ (ПРОДАВЦОВ) БАРЫГ АХАХАХА)
    И СЕТ АЙДИШНИКОВ БАРЫГ
                                                            
    TODO СБОР ВСЕЙ ИНФЫ С КАТЕГОРИИ И ЗАКИДЫВАНИЕ В ФУНКЦИЮ parse_ids
    TODO ОНА СВЕРХУ, И ВЫВОД СООТВЕТСВЕННО, И ПОТОМ ТАКУЮ ЖЕ ФУНКЦИЮ
    TODO СДЕЛАТЬ С ПАРСИНГОМ СТРАНИЦ НОРМАЛЬНЫХ ПРОДАВЦОВ, ДОБАВЛЕНИЕ В БД
    TODO И ВСЁ ВОТ ЭТО
"""
async def get_category_pages_data_(s, requests_items):
  links_getted = {}
  # with open('results.txt', 'a', encoding='utf8') as file_to_save_results:
  #   file_to_save_results.write(f'{requests_list[requests_items]}:\n\n')
  links_getted = {}
  ids_ = []
  # print(f'Status: waiting for {pause_between_ask} seconds')
  headers = {'User-Agent': str(ua.random)}

  result_of_parsing = await s.get(requests_items, headers=headers)
  soup = BeautifulSoup(result_of_parsing.text, 'html.parser')
  cards = soup.find_all('div', {'class':'js-catalog-product-item'})
  #print(cards)
  for i in cards:
    url = i.find('a', {'class': 'ek-link'})
    # print(url)
    seller_id = i['data-stats-owner-id']
    #print(f"https://izi.ua{url['href']}", seller_id)
    links_getted[f"https://izi.ua{url['href']}"] = seller_id
    ids_.append(seller_id)

  return links_getted, set(ids_)

async def check_users_(s, user_id):
  headers = {'User-Agent': str(ua.random)}
  #print(f'https://izi.ua/m-{user_id}-id{user_id}')
  user_profile_data = await s.get(f'https://izi.ua/m-{user_id}-id{user_id}', headers=headers)
  soup = BeautifulSoup(user_profile_data.text, 'html.parser')
  try:
    is_revs = 'Отзыв' in user_profile_data.text
    goods_count = soup.find('sup', {'class':'b-tabs__counter'}).text.replace('(', '').replace(')', '').strip()
    #print(user_id, goods_count)
    if int(goods_count) <= highest_plank_of_goods and \
        int(goods_count) >= lowest_plank_of_goods and \
        not is_revs:
      #print(user_id, goods_count, 'good)')
      return user_id, True
      
    else:
      return user_id, False
  except (ValueError, AttributeError):
    print(f'value err {user_id}')
    return user_id, False


"""
    ЧЕ ЗА ХУЙНЯ, НОНАТАЙП ЕРОРР ВЫКИДЫВАЕТСЯ ПОЧЕМУ ТО ИНОГДА(
    ДОВОЛЬНО ЧАСТО) ФИКСАНУТЬ TODO  
"""
async def check_and_parse_cards_(s, link, category_users_data, urls_data, count):
  global res_counter
  #print(link)
  is_good_seller = category_users_data[urls_data[link]]
  #print(res_counter, count)
  if res_counter < count:
    if is_good_seller:
      headers = {'User-Agent': str(ua.random)}
      user_id = urls_data[link] 
      result_of_parsing = await s.get(link, headers=headers)

      page_ = BeautifulSoup(result_of_parsing.text, 'html.parser')

      table = page_.find('ul', {'class': 'ek-list_indent_s'})

      try:
        if 'Состояние' in table.text:
          li = table.find('li', {'class': 'ek-list__item'})

          quality = li.text.replace('Состояние', '').strip()
          card_pub_date_digits = re.findall(r'Опубликовано<!-- --> <!-- -->(\d\d)\.(\d\d)\.(\d\d)', result_of_parsing.text)
          card_pub_date = '.'.join(x for x in card_pub_date_digits[0])
          
          # print(card_pub_date, nice_dates)
          if card_pub_date not in nice_dates:
            return False
          if quality in bad_qualities:
            return False
          if user_id in sellers_we_already_have:
            return False
          else:
            if not user_id in sellers_we_already_have:
              sellers_we_already_have.append(user_id)

            try:
              cursor.execute('INSERT INTO urls(url, date) VALUES (?, ?)', (link, today_date))
              con.commit()

              with open('results.txt', 'a', encoding='utf8') as file_to_save_results:
                file_to_save_results.write(f"{link}\n")
                
                res_counter += 1
                print(res_counter, link)
            except sqlite3.IntegrityError as e:
              return False
              #print(f'url {link} already in db')

            #print(link, goods_status)
            return True
      except (AttributeError, IndexError) as e:
        print(f'{e} {link}')
        return False
      
    return link
  else:
    
    raise IOError


""" 
    АСИНХРОННЫЙ ЗАПУСК ФУНКЦИИ get_category_pages_data_ С ПЕРЕДАЧЕЙ СЕССИИ И ССЫЛКИ НА СТРАНИЦУ
    КОТОРУЮ ПАРСИТЬ
"""
async def get_category_pages_data(urls):
  s = AsyncHTMLSession()
  print('\nbegin parsing pages')
  tasks = (get_category_pages_data_(s, requests_items=url) for url in urls)
  return await asyncio.gather(*tasks, return_exceptions=True)



async def check_users(users):
  s = AsyncHTMLSession()
  print('\nbegin parsing users')
  tasks = (check_users_(s, user_id=user) for user in users)
  return await asyncio.gather(*tasks)


async def check_and_parse_cards(category_users_data, urls_data, count):
  s = AsyncHTMLSession()
  print('\nbegin checking and parsing cards')
  #print(urls_data)
  tasks = (check_and_parse_cards_(s, link=link, category_users_data=category_users_data, urls_data=urls_data, count=count) for link in urls_data)

  return await asyncio.gather(*tasks)
  

""" 
    ПОСЛЕДОВАТЕЛЬНО ЗАПУСКАТЬ АСИНХРОННЫЕ ПРОЦЕССЫ(ФУНКЦИЯ main) 
"""
with open('results.txt', 'w', encoding='utf8') as file_to_save_results:
      file_to_save_results.write('')

def main(count: int):
  #print(count)
  for requests_category in requests_list:
    with open('results.txt', 'a', encoding='utf8') as file_to_save_results:
        file_to_save_results.write(f'{requests_list[requests_category]}:\n')
    category_users_data = {}
    urls_data = {}

    urls = []

    for j in range(1, search_deep + 1):
      url = f'https://izi.ua/{requests_category}/page{j}?sort=-updated_at'
      urls.append(url)

    category_pages_data = asyncio.run(get_category_pages_data(urls))
    user_ids = []

    for page_data in category_pages_data:
      for item in page_data[0]:
        urls_data[item] = page_data[0][item]
      for item in page_data[1]:
        user_ids.append(item)
    
    user_ids = list(set(user_ids))
    #print(len(urls_data), len(set(user_ids)), time.time()-start_time,'\nASYNC WAY')
    users = asyncio.run(check_users(user_ids))
    for user in users:
      category_users_data[user[0]] = user[1]

    try: 
    #print(count)
      asyncio.run(check_and_parse_cards(category_users_data, urls_data, count))
    except IOError:
      time_ = time.time() - start_time 
      with open('results.txt', 'a', encoding='utf8') as file_to_save_results:
        file_to_save_results.write(f'\nВремени заняло: {time_} secs') 
      print('Набралось нужное колво')
      sys.exit()

    with open('results.txt', 'a', encoding='utf8') as file_to_save_results:
        file_to_save_results.write(f"\n\n")



if __name__=='__main__':
  main(how_much_results_need)

"""
    ============================
    TEST SYNC WAY
    ============================
"""
# def get_category_pages_data_():
#   links_getted = {}
#   ids_ = []
#   # with open('results.txt', 'a', encoding='utf8') as file_to_save_results:
#   #   file_to_save_results.write(f'{requests_list[requests_items]}:\n\n')
#   for requests_items in range(search_deep):
#     print(f'Status: waiting for {pause_between_ask} seconds')
#     headers = {'User-Agent': str(ua.random)}

#     result_of_parsing = requests.get(f'https://izi.ua/c-36-zhenskaya-odezhda/page{requests_items}?sort=-updated_at', headers=headers)
#     soup = BeautifulSoup(result_of_parsing.text, 'html.parser')
#     cards = soup.find_all('div', {'class':'js-catalog-product-item'})
#     #print(cards)
#     for i in cards:
#       url = i.find('a', {'class': 'ek-link'})
#       # print(url)
#       seller_id = i['data-stats-owner-id']
#       #print(f"https://izi.ua{url['href']}", seller_id)
#       links_getted[f"https://izi.ua{url['href']}"] = seller_id
#       ids_.append(seller_id)
#   return links_getted, set(ids_)


# res = get_category_pages_data_()
# print(res, start_time-time.time(),'\nxSYNC WAY')