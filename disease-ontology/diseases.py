import pandas as pd
import obo

header, terms = obo.read_obo('/Users/nikita/Sources/python-notebooks/data/doid.obo')
q = pd.DataFrame(terms)


def extract_synonim(synonim_str):
    return synonim_str.split(" EXACT ")[0].split(" RELATED ")[0]
    
cleaned_diseases = q['id,name,synonym,is_a,def,is_obsolete'.split(',')]
cleaned_diseases[['id', 'def', 'name', 'is_obsolete']] = cleaned_diseases[['id', 'def', 'name', 'is_obsolete']].applymap(lambda x: x[0] if isinstance(x, list) else x)
cleaned_diseases['synonym'] = cleaned_diseases['synonym'].map(lambda syns: [extract_synonim(syn) for syn in syns] if isinstance(syns, list) else [])
cleaned_diseases['synonym'] = cleaned_diseases['synonym'].map(lambda syns: [syn.strip('"') for syn in syns])

cleaned_diseases['synonym.str'] = cleaned_diseases['synonym'].map(lambda syns: ','.join(syns) if isinstance(syns, list) else syns)

actual_diseases = cleaned_diseases[cleaned_diseases.is_obsolete.map(lambda x: x != 'true')]


import json
with open('annotations.json') as f:
    annotations = json.load(f)

bucket = []
for accession, matches in annotations.items():
    for score, doid in matches:
        bucket.append({'accession': accession, 
                       'score': score,
                       'doid': doid})
                       
a = pd.DataFrame(bucket).drop_duplicates()
dods = a.groupby('accession')['doid'].apply(list)
dods[dods.map(lambda x: len(x) == 1)]

