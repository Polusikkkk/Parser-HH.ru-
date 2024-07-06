import time
import random
import logging
import requests
import psycopg2
import schedule
# Установка токена API HeadHunter
hh_api_token = 'APPLRUGOAS7RJBS1K702RKJOPOPU6I08PUILD2EI43G557G4QVRBDLU8RJTKL18U'

# Конфигурация базы данных
db_config = {
    'dbname': 'mydb',
    'user': 'postgres',
    'password': '12345',
    'host': 'localhost',
    'port': '5432'
}
# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# Функция для создания таблицы vacancies
def create_table(conn):
    cursor = conn.cursor()

    create_table_query = """
        CREATE TABLE IF NOT EXISTS vacancies (
            id SERIAL PRIMARY KEY,
            city VARCHAR(50),
            company VARCHAR(200),
            industry VARCHAR(200),
            title VARCHAR(200),
            keywords TEXT,
            skills TEXT,
            experience VARCHAR(50),
            salary VARCHAR(50),
            url VARCHAR(200)
        )
    """
    cursor.execute(create_table_query)

    conn.commit()
    cursor.close()
    logging.info("Таблица 'vacancies' успешно создана.")

    # Функция для удаления таблицы vacancies
def drop_table(conn):
    cursor = conn.cursor()

    drop_table_query = "DROP TABLE IF EXISTS vacancies"
    cursor.execute(drop_table_query)

    conn.commit()
    cursor.close()
    logging.info("Таблица 'vacancies' успешно удалена.")

def get_token():
    url = 'https://api.hh.ru/token'
    params = {
        'client_id': "SOQ3M6D5U53DFGVKO2M2OM94BIK9531TBUNVM1QCBLBJFAC8QS2OTPMT9AGQK6KH",
        'client_secret': "T2OF1GCCM7LFH4R74HB006N891UF4QQN4PRDLAN6EQKAAUMM1PHONM1LHOL577HJ",
        'grant_type': "client_credentials" 
    }
    headers = {
     #   'Authorization': f'Bearer {hh_api_token}'
    }

    response = requests.post(url, params=params, headers=headers)
    response.raise_for_status()
    return response.json()

# Функция для получения вакансий
def get_vacancies(city, vacancy, page):
    url = 'https://api.hh.ru/vacancies'
    params = {
        'text': f"{vacancy} {city}",
        'area': city,
        'specialization': 1,
        'per_page': 100,
        'page': page
    }
    headers = {
        'Authorization': f'Bearer {hh_api_token}'
    }

    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    #logging.info(response.json())
    return response.json()

# Функция для получения навыков вакансии
def get_vacancy_skills(vacancy_id):
    url = f'https://api.hh.ru/vacancies/{vacancy_id}'
    headers = {
        'Authorization': f'Bearer {hh_api_token}'
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()

    skills = [skill['name'] for skill in data.get('key_skills', [])]
    return ', '.join(skills)

# Функция для получения отрасли компании
def get_industry(company_id):
    # Получение отрасли компании по ее идентификатору
    if company_id is None:
        return 'Unknown'

    url = f'https://api.hh.ru/employers/{company_id}'
    response = requests.get(url)
    if response.status_code == 404:
        return 'Unknown'
    response.raise_for_status()
    data = response.json()

    if 'industries' in data and len(data['industries']) > 0:
        return data['industries'][0].get('name')
    return 'Unknown'

# Функция для парсинга вакансий
def parse_vacancies():
    cities = {
        'Москва': 1,
        'Санкт-Петербург': 2
    }

    vacancies = [
        'разработчик bi','BI Developer', 'Business Development Manager', 'Machine Learning Engineer'
    ]

    with psycopg2.connect(**db_config) as conn:
        drop_table(conn)
        create_table(conn)

        for city, city_id in cities.items():
            for vacancy in vacancies:
                page = 0
                while True:
                    try:
                        data = get_vacancies(city_id, vacancy, page)
                        logging.info("{} and {}".format("data.length: ", len(data)))

                        if not data.get('items'):
                            break

                        with conn.cursor() as cursor:
                            for item in data['items']:
                                if vacancy.lower() not in item['name'].lower():
                                    #logging.info("пропуск vacancy["+vacancy.lower()+"], item[" + item['name'].lower() + "]")
                                    continue  # Пропустить, если название вакансии не совпадает
                                logging.info("найдена вакансия")

                                #title = f"{item['name']} ({city})"
                                title = f"{item['name']}"
                                keywords = item['snippet'].get('requirement', '')
                                skills = get_vacancy_skills(item['id'])
                                company = item['employer']['name']
                                industry = get_industry(item['employer'].get('id'))
                                experience = item['experience'].get('name', '')
                                salary = item['salary']
                                if salary is None:
                                    salary = "з/п не указана"
                                else:
                                    salary = salary.get('from', '')
                                url = item['alternate_url']

                                insert_query = """
                                    INSERT INTO vacancies 
                                    (city, company, industry, title, keywords, skills, experience, salary, url) 
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                                """
                                logging.info("запись в базу")
                                cursor.execute(insert_query,
                                               (city, company, industry, title, keywords, skills, experience, salary, url))
                                conn.commit()

                            if page >= data['pages'] - 1:
                                break

                            page += 1

                            # Задержка между запросами в пределах 1-3 секунд
                            time.sleep(random.uniform(3, 6))

                    except requests.HTTPError as e:
                        logging.error(f"Ошибка при обработке города {city}: {e}")
                        continue  # Перейти к следующему городу, если произошла ошибка

        conn.commit()

    logging.info("Парсинг завершен. Данные сохранены в базе данных PostgreSQL.")

# Функция для удаления дубликотов на основе столбца «url»
def remove_duplicates():
    with psycopg2.connect(**db_config) as conn:
        cursor = conn.cursor()

        # Удалить дубликаты на основе столбца «url»
        delete_duplicates_query = """
            DELETE FROM vacancies
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM vacancies
                GROUP BY url
            )
        """
        cursor.execute(delete_duplicates_query)

        conn.commit()
        cursor.close()

    logging.info("Дубликаты в таблице 'vacancies' успешно удалены.")


def run_parsing_job():
    logging.info("Запуск парсинга...")

    try:
        parse_vacancies()
        remove_duplicates()
    except Exception as e:
        logging.error(f"Ошибка при выполнении задачи парсинга: {e}")


# Планировщик задач
'''schedule.every().day.at("12:00").do(run_parsing_job)

while True:
    schedule.run_pending()
    time.sleep(1)
'''
run_parsing_job()
#get_token()