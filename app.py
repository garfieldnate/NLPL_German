import spacy

from flask import Flask, jsonify, request

nlp = spacy.load('de')

app = Flask(__name__)


@app.route('/api/v1/tokenize/de', methods = ['POST'])
def tokenize():
    # try:
        text = request.get_data().decode('utf-8')
        doc = nlp(text)
        result = {'text': text}
        tokens = []
        for word in doc:
            if word.is_punct or word.is_digit or word.is_currency:
                continue
            details = {
                "POS": word.pos_,
                "TAG": word.tag_
            }
            ent_type = ''
            if word.like_email:
                ent_type = 'email'
            elif word.like_url:
                ent_type = 'url'
            else:
                ent_type = word.ent_type_
            if ent_type:
                details["ENT_type"] = ent_type
            if word.is_oov:
                details['OOV'] = True
            tokens.append({'start': word.idx, 'end': word.idx + len(word.text), 'lemma': word.lemma_, 'details': details})
        return jsonify({'result': {'tokens': tokens, 'text': text}})
    # except Exception as e:
    #     return jsonify({'errorMessage': str(e), 'result': None})

if __name__ == '__main__':
    app.run()
