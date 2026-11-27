"""Free-tier cloud model proxy for the coach.

The mobile app never holds a provider key. The server holds it in the environment
(GEMINI_API_KEY for Google AI Studio, or OPENROUTER_API_KEY for OpenRouter ':free' models).
Safety-critical text is answered deterministically before any provider is called.
"""
import json,os,re,urllib.request,urllib.error

GUARD=("You are the cloud tier of a fitness coach inside a training app. The app's engine is the source of truth "
       "for workouts, loads and safety. Never invent exercises, weights, sets or medical advice. If asked about pain, "
       "injury or symptoms, tell the user to stop and seek a professional. Keep answers short and practical.")
EMERGENCY=re.compile(r'\b(chest pain|chest pressure|fainting|severe breathlessness)\b',re.I)
PAIN=re.compile(r'\b(pain|painful|hurt|hurts|injury|injured|dizzy)\b',re.I)
DAILY_LIMIT=40

class CloudUnavailable(Exception):pass

def configured():
    return 'gemini' if os.getenv('GEMINI_API_KEY') else ('openrouter' if os.getenv('OPENROUTER_API_KEY') else None)

def safety_reply(text):
    if EMERGENCY.search(text):return 'Stop training and seek urgent medical help for chest pain, chest pressure, fainting or severe breathlessness.'
    if PAIN.search(text):return 'Pause if you have pain or alarming symptoms. Update readiness so the safety layer can review your session.'
    return None

def _post(url,headers,body):
    req=urllib.request.Request(url,data=json.dumps(body).encode(),headers={'Content-Type':'application/json',**headers},method='POST')
    try:
        with urllib.request.urlopen(req,timeout=25) as r:return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise CloudUnavailable('Cloud model is busy or rate-limited (%s). Try again later.'%e.code)
    except (urllib.error.URLError,TimeoutError,ValueError):
        raise CloudUnavailable('Cloud model could not be reached.')

def complete(system,history,message):
    """history: [{role:'user'|'assistant',content:str}]. Returns (reply, provider)."""
    provider=configured()
    if not provider:raise CloudUnavailable('Cloud coach is not configured on the server.')
    sys_text=GUARD+'\n\n'+system
    turns=[*history,{'role':'user','content':message}]
    if provider=='gemini':
        model=os.getenv('COACH_CLOUD_MODEL','gemini-2.5-flash')
        data=_post('https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent'%model,{'x-goog-api-key':os.environ['GEMINI_API_KEY']},
            {'systemInstruction':{'parts':[{'text':sys_text}]},
             'contents':[{'role':'user' if t['role']=='user' else 'model','parts':[{'text':t['content']}]} for t in turns],
             'generationConfig':{'maxOutputTokens':700,'temperature':0.6}})
        try:text=''.join(p.get('text','') for p in data['candidates'][0]['content']['parts'])
        except (KeyError,IndexError,TypeError):raise CloudUnavailable('Cloud model returned no answer.')
    else:
        model=os.getenv('COACH_CLOUD_MODEL','meta-llama/llama-3.3-70b-instruct:free')
        data=_post('https://openrouter.ai/api/v1/chat/completions',{'Authorization':'Bearer '+os.environ['OPENROUTER_API_KEY']},
            {'model':model,'max_tokens':700,'temperature':0.6,'messages':[{'role':'system','content':sys_text},*turns]})
        try:text=data['choices'][0]['message']['content']
        except (KeyError,IndexError,TypeError):raise CloudUnavailable('Cloud model returned no answer.')
    text=(text or '').strip()
    if not text:raise CloudUnavailable('Cloud model returned no answer.')
    return text,provider
