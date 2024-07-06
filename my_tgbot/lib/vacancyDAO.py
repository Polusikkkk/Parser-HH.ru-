import logging
import psycopg2

# Конфигурация базы данных
db_config = {
    'dbname': 'practica_db',
    'user': 'practica',
    'password': '12345',
    'host': 'db',
    'port': '5432'
}

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Функция для создания таблицы vacancies
def getVacancies(city, title, experience):
    results = ""
    with psycopg2.connect(**db_config) as conn:
        cursor = conn.cursor()

        select_query = """
            SELECT * FROM public.vacancies
            WHERE city = '""" + city + """'  
            AND title ILIKE '""" + title + """%'  
            AND LOWER(experience) = LOWER('""" + experience + """') 
            ORDER BY id ASC 
        """

        cursor.execute(select_query)
        results = list(cursor.fetchall())
        cursor.close()
        logging.info("Запрос getVacancies выполнен.\n" + select_query)
        logging.info(results)
    return results

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


