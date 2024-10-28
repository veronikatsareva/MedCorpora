import re
import pandas as pd
from pymystem3 import Mystem
from collections import defaultdict


def reg_from_req(request: str) -> str | None:
    """
    Функция приводит запрос разрешенного формата к нижнему регистру и преобразует его в регулярное выражение под корпус.
    :param request: строка изначального запроса.
    :returns: регулярное выражение или None при некоторых неправильных запросах.
    """
    # разрешенные теги
    tags = ['adj', 'adv', 'intj', 'noun', 'propn', 'verb', 'adp', 'aux', 'cconj', 'det', 'num', 'part', 'pron', 'sconj']
    request = request.lower()
    parts = request.split()
    # рекурсия, если в запросе несколько слов
    if len(parts) > 1:
        return ' '.join(reg_from_req(part) for part in parts)
    # одно слово
    elif len(parts) == 1:
        # "слово" -> слово+буквы(с дефисом)+буквы
        if request[0] == request[-1] == '"':
            request = request[1:len(request) - 1]
            return fr'{request}\+[\w\-]+\+\w+'
        # tag -> буквы(с дефисом)+буквы(с дефисом)+tag
        elif request in tags:
            return fr'[\w\-]+\+[\w\-]+\+{request}'
        # слово+tag -> буквы(с дефисом)+слово+tag
        elif '+' in request:
            request = request.replace('+', r'\+')
            return fr'[\w\-]+\+{request}'
        # слово (и всякий мусор, по которому ничего не найдется: NOIN...) ->
        # буквы(с дефисом)+лемма(от слово)+буквы
        else:
            mystem = Mystem()
            words = mystem.lemmatize(request)
            # проверяем что это одно слово (уберет запрос скажи-ка)
            if len(words) == 2:
                return fr'[\w\-]+\+{words[0]}\+\w+'


class RegexDF:
    """
    Этот класс создает базу данных и осуществляет поиск по ней при помощи
    регулярного выражения.
    """
    def __init__(self, regex: str):
        """
        Считывает регулярное выражение и датафрейм из файла.
        :param regex: строка регулярного выражения.
        """
        self.regex = regex
        self.df = pd.read_csv('MedNewsCorpora-short.csv', sep=';')

    def indexes(self) -> list:
        """
        Находит все индексы текстов, в которых встречается нужное.
        :returns: список индексов.
        """
        inside = []
        for row in self.df.itertuples():
            # ищем в размеченном тексте
            text = row.Разбор
            if re.search(self.regex, text):
                inside.append(row.Index)
        return inside

    def matches(self, index: int) -> list:
        """
        Для одного текста находит внешний вид всех вхождений нужного типа.
        :param index: индекс рассматриваемого текста.
        :returns: список строк в формате 'слово+лемма+тег'.
        """
        text = self.df['Разбор'][index]
        # разрешаем пересечение, но следим, чтобы начало было несловным
        return re.findall(fr'(?=(\b{self.regex}))', text)

    def matchesbatch(self, indexes: list) -> dict:
        """
        Для списка текстов находит внешний вид всех вхождений нужного типа.
        :param indexes: список индексов интересуещих текстов.
        :returns: словарь, ключ -- индекс, значение -- список вхождений, в т.ч. пустой.
        """
        matches = dict()
        for index in indexes:
            matches[index] = self.matches(index)
        return matches

    def matchesall(self) -> dict:
        """
        Находит внешний вид всех вхождений в тексты, в которых нужное есть.
        :returns: словарь, ключ -- индекс, значение -- список вхождений, точно не пуст.
        """
        return self.matchesbatch(self.indexes())

    @staticmethod
    def split_words_info(match: str) -> tuple[str, str, str]:
        """
        Разделяет строку в формате 'слово+лемма+тег' на три отдельные строки со словоформами, леммами и тегами слов.
        :param match: строка со словами в формате 'слово+лемма+тег'.
        :returns: три строки 'слово1 слово2...', 'лемма1 лемма2...', 'тег1 тег2...'.
        """
        words = ' '.join(x.split('+')[0] for x in match.split())
        lemmas = ' '.join(x.split('+')[1] for x in match.split())
        poses = ' '.join(x.split('+')[2] for x in match.split())
        return words, lemmas, poses

    def highlight(self, index: int) -> list:
        """
        Для одного текста находит индексы всех вхождений нужного типа.
        :param index: индекс рассматриваемого текста.
        :returns: список кортежей (индекс первой буквы, индекс последней буквы).
        """
        found = []
        # теперь ищем в неразмеченном тексте
        text = self.df['Текст'][index]
        for match in self.matches(index):
            # для неразмеченного актуальны только словоформы
            words = RegexDF.split_words_info(match)[0]
            # слова в тексте разделяются несловными символами (', ', '-')
            regex_words = r'\b' + r'\W+?'.join(words.split()) + r'\b'
            for i in re.finditer(regex_words, text, flags=re.IGNORECASE):
                # одно словоформа может встречаться несколько раз, берем один
                if i.span() not in found:
                    found.append(i.span())
        return found

    def highlightbatch(self, indexes: list) -> dict:
        """
        Для списка текстов находит индексы всех вхождений нужного типа.
        :param indexes: список индексов интересуещих текстов.
        :returns: словарь, ключ -- индекс, значение -- список кортежей (индекс первой, последней букв), в т.ч. пустой.
        """
        to_highlight = dict()
        for index in indexes:
            to_highlight[index] = self.highlight(index)
        return to_highlight

    def highlightall(self) -> dict:
        """
        Находит индексы всех вхождений в тексты, в которых нужное есть.
        :returns: словарь, ключ -- индекс, значение -- список кортежей (индекс первой, последней буквы), точно не пуст.
        """
        return self.highlightbatch(self.indexes())

    def pretty_print(self) -> dict:
        """
        Создание словаря для выдачи результатов пользователя по запросу.
        :returns: словарь, где ключ –– текст предложения, а значение –– список кортежей из левого контекста, центра,
        правого контекста, метаинформации и ссылки на статью.
        """

        highlighted = self.highlightall()

        # словарь для результатов
        to_print = {}

        for idx in highlighted:
            # для каждого предложения с подходящим результатом по запросу
            # вытаскиваем текст и мета-данные из датафрейма
            sentence = self.df["Текст"][idx]
            author = self.df["Автор"][idx]
            date = self.df["Дата"][idx]
            source = self.df["Источник"][idx]
            url = self.df["Ссылка"][idx]
            name = self.df["Название статьи"][idx]

            meta_text = [info.strip() for info in [author, name, source, date] if isinstance(info, str)]

            to_print[sentence] = []

            # добавляем каждый разбор в словарь
            for res in highlighted[idx]:
                left, right = res[0], res[1]
                to_print[sentence].append(
                    (sentence[:left], sentence[left:right], sentence[right:],
                     ". ".join(meta_text), url)
                )
        return to_print

    def download_csv(self) -> int:
        """
        Создание csv-файла для скачивания по результатам запроса.
        :returns: 0 при завершении работы.
        """

        # словарь для будущего датафрейма
        result = {
            "Левый контекст": [],
            "Центр": [],
            "Правый контекст": [],
            "Полный контекст": [],
            "Автор": [],
            "Название статьи": [],
            "Дата": [],
            "Источник": [],
            "Ссылка": []
        }

        highlighted = self.highlightall()

        for idx in highlighted:
            # для каждого предложения с подходящим результатом по запросу
            # вытаскиваем текст и мета-данные из датафрейма
            sentence = self.df["Текст"][idx]

            for res in highlighted[idx]:
                left, right = res[0], res[1]

                # добавляем информацию в словарь-выдачу
                for key in ["Автор", "Название статьи", "Дата", "Источник", "Ссылка"]:
                    result[key].append(self.df[key][idx])

                result["Левый контекст"].append(sentence[:left])
                result["Центр"].append(sentence[left:right])
                result["Правый контекст"].append(sentence[right:])
                result["Полный контекст"].append(sentence)

        # создание файла для скачивания
        df = pd.DataFrame.from_dict(result)
        df.to_csv('static/corpora_content.csv')

        return 0

    def freq_dicts(self) -> tuple[dict, dict, dict]:
        """
        Находит самые частые заполнители для вхождений, отдельно по каждому из параметров для слов (форма, лемма, тег).
        :returns: три частотных словаря (для слов, лемм и тегов).
        """
        # создаем defaultdict для каждого из трех параметров
        dict_words = defaultdict(int)
        dict_lemmas = defaultdict(int)
        dict_poses = defaultdict(int)
        # проходим по всем отмеченным в текстах вхождениям
        for value in self.matchesall().values():
            for match in value:
                # делим информацию и подсчитываем
                words, lemmas, poses = RegexDF.split_words_info(match)
                dict_words[words] += 1
                dict_lemmas[lemmas] += 1
                dict_poses[poses] += 1
        # сортируем
        dict_words = dict(sorted(dict_words.items(),
                                 key=lambda item: item[1], reverse=True))
        dict_lemmas = dict(sorted(dict_lemmas.items(),
                                  key=lambda item: item[1], reverse=True))
        dict_poses = dict(sorted(dict_poses.items(),
                                 key=lambda item: item[1], reverse=True))
        return dict_words, dict_lemmas, dict_poses
