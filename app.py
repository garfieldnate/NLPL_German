# Note: run fst-infl2-daemon 7100 ~/Downloads/zmorge-20150315-smor_newlemma.ca separately
# SFST: http://www.cis.uni-muenchen.de/~schmid/tools/SFST/
# zmorge: http://kitt.ifi.uzh.ch/kitt/zmorge/
import socket
import re

import spacy

from flask import Flask, jsonify, request

nlp = spacy.load('de')

app = Flask(__name__)

SFST_HOST = 'localhost'
SFST_PORT = 7100

def run_sfst(word):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SFST_HOST, SFST_PORT))
        s.sendall(word.encode())
        s.shutdown(socket.SHUT_WR)
        all_data = b''
        while 1:
            data = s.recv(1024)
            all_data += data
            if len(data) == 0:
                break
    return all_data.decode("utf-8")

# Geburtenraten does not work :(
zmorge_tags_pattern = re.compile(r'<.*?>')
def parse_zmorge(sfst_output):
    if not sfst_output or "no result for" in sfst_output:
        return None
    lines = sfst_output.splitlines()
    # first line just echoes the input
    analysis = lines[1].split('<#>')
    if len(analysis) == 1:
        return None
    parts = []
    for part in analysis:
        fugen_laut_idx = part.find('<->')
        if fugen_laut_idx != -1:
            part = part[0:fugen_laut_idx]
        part = zmorge_tags_pattern.sub('', part)
        parts.append(part)
    return parts

def get_compound_info(word):
    sfst_output = run_sfst(word)
    return parse_zmorge(sfst_output)

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
            compound_info = None
            details = {
                "POS": word.pos_,
                "TAG": word.tag_
            }

            if word.pos_ != "PROPN":
                parts = get_compound_info(word.text)
                if parts:
                    details['parts'] = parts

            ent_type = ''
            if word.like_email:
                ent_type = 'email'
            elif word.like_url:
                ent_type = 'url'
            else:
                ent_type = word.ent_type_
            if ent_type:
                details["ENT_type"] = ent_type
            # Apparently everything is an OOV!
            # if word.is_oov:
            #     details['OOV'] = word.is_oov
            tokens.append({'start': word.idx, 'end': word.idx + len(word.text), 'lemma': word.lemma_, 'details': details, 'original': word.text})
        return jsonify({'result': {'tokens': tokens, 'text': text}})
    # except Exception as e:
    #     return jsonify({'errorMessage': str(e), 'result': None})

if __name__ == '__main__':
    app.run()
