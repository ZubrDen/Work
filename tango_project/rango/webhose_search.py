import json, os
import urllib.parse
import urllib.request

def read_webhose_key():
    """
    Считывает ключ API Webhose из файла с именем search.key.
    Возвращает либо None (ключ не найден), либо строку, представляющую ключ.
    Помните: поместите search.key в свой файл .gitignore, чтобы избежать его фиксации!
    """
    # См. Python Anti-Patterns - это отличный ресурс!
    # Здесь мы используем «with» при открытии файлов.
    # http://docs.quantifiedcode.com/python-anti-patterns/maintainability/
    webhose_api_key = None

    if os.path.isfile('search.key'):
        dir_path = 'search.key'
    else:
        dir_path = '../search.key'


    try:
        with open(dir_path, 'r') as f:
            webhose_api_key = f.readline().strip()
    except:
        raise IOError('search.key file not found')

    return webhose_api_key

def run_query(search_terms, size=10):
    """
    Учитывая строку, содержащую условия поиска (запрос) и
    количество возвращаемых результатов (по умолчанию 10), возвращает список
    результатов из API Webhose, каждый из которых состоит из заголовка, ссылки и резюме.
    """
    webhose_api_key = read_webhose_key()
    if not webhose_api_key:
        raise KeyError('Webhose key not found')

    # Какой базовый URL-адрес для API Webhose?
    root_url = 'http://webhose.io/search'

    # Отформатируйте строку запроса - экранируйте специальные символы.
    query_string = urllib.parse.quote(search_terms)

    # Используйте форматирование строки для создания полного URL-адреса API.
    # search_url - это строка, разделенная на несколько строк.
    search_url = ('{root_url}?token={key}&format=json&q={query}'
                  '&sort=relevancy&size={size}').format(root_url=root_url,
                                                        key=webhose_api_key,
                                                        query=query_string,
                                                        size=size)
    # print(search_url)     # Выводит в терминал строку запроса

    results = []

    try:
        # Подключитесь к API Webhose и преобразуйте ответ в
        # словарь Python.
        response = urllib.request.urlopen(search_url).read().decode('utf-8')
        json_response = json.loads(response)

        # Просматривайте сообщения, добавляя каждую в список результатов в виде словаря.
        # Мы ограничиваем сводку первыми 200 символами, поскольку сводные ответы от
        # Webhose могут быть длинными!
        for post in json_response['posts']:
            results.append({'title': post['title'],
                            'link': post['url'],
                            'summary': post['text'][:200]})
    except:
        print('Error when querying the Webhose API')

    # Вернуть список результатов вызывающей функции.
    # print(results)
    return results


# Start execution here!
if __name__ == '__main__':
    print('Starting hel script ...')
    run_query('gasprom')