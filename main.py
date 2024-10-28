from flask import Flask, render_template, request, session, redirect, url_for
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'


@app.route('/')
def main():
    return render_template('main.html')


@app.route('/results', methods=['POST'])
def results(name=None):
    query = request.form.get('query')
    session['query'] = query

    # Обработайте запрос и верните results
    results = None

    if results:
        all_texts = len(results)
        all_examples = sum(len(values) for values in results.values())

        # Заполните переменные lemmas, tokens и pos
        lemmas = None
        session['lemmas'] = lemmas

        tokens = None
        session['tokens'] = tokens

        pos = None
        session['pos'] = pos

        csv_file_path = 'static/corpora_content.csv'
        file_exists = os.path.isfile(csv_file_path)

        return render_template('results.html',
                               name=name,
                               results=results,
                               query=query,
                               all_texts=all_texts,
                               all_examples=all_examples,
                               lemmas=lemmas,
                               tokens=tokens,
                               pos=pos,
                               file_exists=file_exists)
    else:
        return render_template('no_result.html',
                               name=name,
                               query=query)


@app.route('/download')
def download():
    csv_file_path = 'static/corpora_content.csv'
    if not os.path.isfile(csv_file_path):
        return redirect(url_for('handle_error'))

    return redirect(csv_file_path)


@app.route('/statistics')
def statistics():
    query = session.get('query')
    lemmas = session.get('lemmas')
    tokens = session.get('tokens')
    pos = session.get('pos')
    return render_template('statistics.html',
                           query=query,
                           lemmas=lemmas,
                           tokens=tokens,
                           pos=pos)


@app.route('/help')
def help_page():
    return render_template('help.html')


@app.errorhandler(Exception)
def handle_error():
    return render_template('errors.html')


if __name__ == '__main__':
    app.run(debug=False, port=5001)
