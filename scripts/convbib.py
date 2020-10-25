import bibtexparser

def dumps(bib):
    bibstr = ''
    bibstr += '@{}'.format(bib['ENTRYTYPE'])
    bibstr += '{'
    bibstr += '{},\n'.format(bib['ID'])
    for f in ['author','year','booktitle','journal','year','volume','number','pages']:
        if f in bib.keys():
            bibstr += ' {}="{}",\n'.format(f,bib[f])
    bibstr += '}'
    return bibstr

def astr(authors):
    tokens = authors.split(' and ')
    if len(tokens) == 1:
        return tokens[0]
    else:
        return ", ".join(tokens[:-1])+' and '+tokens[-1]

with open('refs.bib') as bibtex_file:
    bib_database = bibtexparser.load(bibtex_file)

for e in bib_database.entries:
    pid = e['ID']
    y = e['year']
    if 'month' in e.keys():
        m = e['month']
    else:
        m = '01'
    d = e['year']+'-'+m+'-01'
    name = d+'-'+pid+'.md'
    img = '/images/papers/{}.png'.format(pid)
    pdf = '/pdfs/papers/{}.pdf'.format(pid)
    if 'booktitle' in e.keys():
        venue = e['booktitle']
    elif 'journal' in e.keys():
        venue = e['journal']
    else:
        venue = 'NA'
    authors = e['author'].split(' and ')
    if len(authors) == 1:
        ref = '{}, {}'.format(authors[0],y)
    elif len(authors) == 2:
        ref = '{} and {}, {}'.format(authors[0],authors[1],y)
    else:
        ref =  '{} et al., {}'.format(authors[0],y)
    
    with open('../papers/_posts/{}'.format(name),'w') as f:
        f.write('---\n')
        f.write('layout: paper\n')
        f.write('title: "{}"\n'.format(e['title']))
        f.write('image: {}\n'.format(img))
        f.write('pdf: {}\n'.format(pdf))
        f.write('ref: {}\n'.format(ref))
        if 'doi' in e.keys():
            f.write('doi: {}\n'.format(e['doi']))
        f.write('authors: {}\n'.format(astr(e['author'])))
        f.write('journal: {}\n'.format(venue))

        f.write('---\n')
        f.write('\n# Abstract\n\n')
        f.write(e['abstract']+'\n\n')
        f.write('---\n')
        f.write('\n# BibTex\n\n')
        f.write('```bibtex\n')
        f.write(dumps(e)+'\n')
        f.write('```\n')


