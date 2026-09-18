"""Hybrid retrieval over the real VLearn slide pages."""
from __future__ import annotations
import json, math, re
from pathlib import Path
from openai import OpenAI
from pypdf import PdfReader
from ai_service import configuration

ROOT=Path(__file__).resolve().parent; SLIDES_ROOT=ROOT/'K4-3A-Day05-06-AI-Product-Hackathon'/'data'/'vlearn-pack'/'slides'; CACHE=ROOT/'logs'/'slide_embeddings.json'; EMBEDDING_MODEL='text-embedding-3-small'; TOKEN_RE=re.compile(r"[\wÀ-ỹ]+",re.UNICODE)
DECKS={'d1':{'file':'d1-slide-hackathon.pdf','id':'day01','title':'Day01 · AI & LLM Foundation'},'d2':{'file':'d2-slide-hackathon.pdf','id':'day02','title':'Day02 · Xác định bài toán cho AI'}}
DECK_ALIASES={'day01':'d1','day02':'d2'}
def _tokens(s): return [x.casefold() for x in TOKEN_RE.findall(s)]
def _load_pages():
    pages=[]
    for deck_id,meta in DECKS.items():
        for n,p in enumerate(PdfReader(str(SLIDES_ROOT/meta['file'])).pages,1):
            text=' '.join((p.extract_text() or '').split())
            pages.append({'id':f'{deck_id}-p{n}','deck_id':deck_id,'lesson_title':meta['title'],'lesson':meta['title'],'page':n,'page_text':text,'tokens':_tokens(text)})
    return pages
PAGES=_load_pages()
def deck_meta(deck_id): return DECKS.get(deck_id)
def page_record(deck_id,page):
    deck_id=DECK_ALIASES.get(deck_id,deck_id)
    try: page=int(page)
    except (TypeError,ValueError): return None
    return next((x for x in PAGES if x['deck_id']==deck_id and x['page']==page),None)
def _cosine(a,b):
    dot=sum(x*y for x,y in zip(a,b)); na=math.sqrt(sum(x*x for x in a)); nb=math.sqrt(sum(x*x for x in b)); return dot/(na*nb) if na and nb else 0.0
def _lexical(query,item):
    q=_tokens(query); terms=item['tokens'];
    if not q:return 0.0
    scores=[]
    for term in q:
        tf=terms.count(term); scores.append(min(1.0,tf/3) if tf else 0.0)
    return sum(scores)/len(q)
def _result(item,score,mode):
    text=item['page_text']; snippet=text[:260].strip(); return {'id':item['id'],'deck_id':item['deck_id'],'lesson':item['lesson'],'page':item['page'],'snippet':snippet,'score':round(score,4),'mode':mode}
def _keyword_rank(query):
    ranked=sorted(((_lexical(query,x),x) for x in PAGES),key=lambda z:z[0],reverse=True); return [(s,x) for s,x in ranked if s>0]
def _load_embeddings(key,model):
    if CACHE.exists():
        try:
            c=json.loads(CACHE.read_text(encoding='utf-8'))
            if c.get('model')==model and [x['id'] for x in c.get('pages',[])]==[x['id'] for x in PAGES]: return [x['embedding'] for x in c['pages']]
        except (OSError,ValueError,TypeError,KeyError): pass
    client=OpenAI(api_key=key,base_url='https://api.openai.com/v1',timeout=45,max_retries=0); response=client.embeddings.create(model=model,input=[x['page_text'] for x in PAGES]); vectors=[x.embedding for x in sorted(response.data,key=lambda x:x.index)]
    try:CACHE.parent.mkdir(exist_ok=True);CACHE.write_text(json.dumps({'model':model,'pages':[{'id':x['id'],'embedding':v} for x,v in zip(PAGES,vectors)]}),encoding='utf-8')
    except OSError: pass
    return vectors
def _accepted(ranked):
    if not ranked:return []
    top=ranked[0][0]; accepted=[]
    for hybrid,sem,lex,item in ranked:
        meaningful=(sem>=0.42 or lex>=0.18) and (hybrid>=top*0.62 or lex>=0.45)
        if meaningful: accepted.append((hybrid,item))
    return accepted[:5]
def search_slides(payload):
    if not isinstance(payload,dict) or set(payload)!= {'query'} or not isinstance(payload['query'],str): raise ValueError('Cần gửi đúng trường query dạng chuỗi.')
    query=payload['query'].strip()
    if not query or len(query)>300: raise ValueError('Từ khóa tìm kiếm không hợp lệ.')
    key,model=configuration(); lexical=_keyword_rank(query)
    if not key:
        accepted=[(s,x) for s,x in lexical if s>=0.18][:5]; return {'results':[_result(x,s,'hybrid-keyword') for s,x in accepted],'mode':'hybrid-keyword','source':'2 PDF VLearn'}
    try:
        vectors=_load_embeddings(key,EMBEDDING_MODEL); client=OpenAI(api_key=key,base_url='https://api.openai.com/v1',timeout=30,max_retries=0); qv=client.embeddings.create(model=EMBEDDING_MODEL,input=query).data[0].embedding
        ranked=[]
        for item,vector in zip(PAGES,vectors):
            sem=max(0.0,_cosine(qv,vector)); lex=_lexical(query,item); ranked.append((.75*sem+.25*lex,sem,lex,item))
        ranked.sort(reverse=True,key=lambda x:x[0]); accepted=_accepted(ranked); return {'results':[_result(x,s,'hybrid') for s,x in accepted],'mode':'hybrid','source':'2 PDF VLearn'}
    except Exception:
        accepted=[(s,x) for s,x in lexical if s>=0.18][:5]; return {'results':[_result(x,s,'hybrid-keyword') for s,x in accepted],'mode':'hybrid-keyword','source':'2 PDF VLearn'}
