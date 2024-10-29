from flask import Flask, render_template, request, redirect
import search

app = Flask(__name__)
app.secret_key = 'your_secret_key'
# пустые представители своего класса для глобальных переменных
query = ''
regex_df = search.RegexDF('+++')


@app.route('/')
def main():
    return render_template('main.html')


@app.route('/results', methods=['POST'])
def results(name=None):
    global query, regex_df
    query = request.form.get('query')

    # преобразование запроса в регулярное выражение
    regex = search.reg_from_req(query)

    # проверяем, что вернулось не None
    if regex:
        # обрабатываем базу регуляркой
        regex_df = search.RegexDF(regex)

        # результаты запроса
        res = regex_df.pretty_print()

        # что-то нашлось
        if res:
            all_texts = len(res)
            all_examples = sum(len(values) for values in res.values())

            return render_template('results.html',
                                   name=name,
                                   results=res,
                                   query=query,
                                   all_texts=all_texts,
                                   all_examples=all_examples)
        else:
            return render_template('no_result.html',
                                   name=name,
                                   query=query)
    else:
        return handle_error()


@app.route('/download')
def download():
    global regex_df
    try:
        # создаем и скачиваем файл
        file_id = regex_df.download_csv()
        csv_file_path = f'static/corpora_content_{file_id}.csv'
        return redirect(csv_file_path)
    except RuntimeError:
        return handle_error()


@app.route('/statistics')
def statistics():
    global query, regex_df
    # выводим статистику
    tokens, lemmas, pos = regex_df.freq_dicts()
    return render_template('statistics.html',
                           query=query,
                           lemmas=lemmas,
                           tokens=tokens,
                           pos=pos)


@app.route('/help')
def help_page():
    return render_template('help.html')


@app.errorhandler(RuntimeError)
def handle_error():
    return render_template('errors.html')


if __name__ == '__main__':
    app.run(debug=False, port=5001)
