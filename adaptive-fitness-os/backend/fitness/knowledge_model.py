"""Train a real source-only neural classifier: exercise names -> source target labels.
No user records, textbook prose, media, exercise IDs or targets enter model inputs.
This predicts dataset categories, not optimal programming, anatomy truth or safety.
"""
import argparse, copy, hashlib, json, re
from pathlib import Path
import numpy as np
VERSION='exercise-target-mlp-1'
SEED=42
VARIANTS=set('barbell dumbbell cable band assisted weighted machine smith leverage body weight kettlebell ez v up one two single arm leg standing seated lying kneeling alternate alternating reverse grip close wide narrow neutral palms inward outward pronated supinated incline decline flat bench stability ball on with and the to of at a an using version variation'.split())

def words(text):return re.findall(r'[a-z]+',text.lower())

def family(name):
    # Keep equipment/position variants together, even if changing grip changes target.
    base=re.sub(r'\([^)]*\)','',name.lower())
    return ' '.join(t for t in words(base) if t not in VARIANTS) or ' '.join(words(base))

def split_rows(rows):
    out={'train':[],'validation':[],'test':[]}
    for r in rows:
        n=int(hashlib.sha256((str(SEED)+':'+family(r['name'])).encode()).hexdigest()[:8],16)%100
        out['train' if n<70 else 'validation' if n<85 else 'test'].append(r)
    if any(not part for part in out.values()):raise ValueError('Need nonempty train, validation and test family partitions')
    return out

def features(text):
    w=words(text)
    return w+[a+'_'+b for a,b in zip(w,w[1:])]

def encode(names,vocabulary):
    lookup={v:i for i,v in enumerate(vocabulary)};x=np.zeros((len(names),len(vocabulary)))
    for j,name in enumerate(names):
        for t in set(features(name)):
            if t in lookup:x[j,lookup[t]]=1
    return x/np.maximum(np.linalg.norm(x,axis=1,keepdims=True),1)

def forward(x,weights):
    w1,b1,w2,b2=weights;h=np.tanh(x@w1+b1);z=h@w2+b2;z-=z.max(axis=1,keepdims=True)
    exp=np.exp(z)
    return exp/exp.sum(axis=1,keepdims=True),h

def gradients(x,y,weights,class_weights):
    p,h=forward(x,weights);d=p.copy();d[np.arange(len(y)),y]-=1;d*=class_weights[y,None]/len(y)
    dh=(d@weights[2].T)*(1-h*h)
    return [x.T@dh,dh.sum(axis=0),h.T@d,d.sum(axis=0)]

def metrics(y,p,labels):
    pred=p.argmax(axis=1);classes={}
    for i,label in enumerate(labels):
        tp=int(((y==i)&(pred==i)).sum());fp=int(((y!=i)&(pred==i)).sum());fn=int(((y==i)&(pred!=i)).sum())
        classes[label]={'support':int((y==i).sum()),'f1':2*tp/max(2*tp+fp+fn,1)}
    return {'accuracy':float((y==pred).mean()),'macro_f1_supported_classes':float(np.mean([r['f1'] for r in classes.values() if r['support']])),
            'per_class':classes,'cross_entropy':float(-np.log(np.maximum(p[np.arange(len(y)),y],1e-12)).mean())}

def train(rows,source_sha256,epochs=180):
    if len({str(r['id']) for r in rows})!=len(rows):raise ValueError('Duplicate source exercise IDs')
    parts=split_rows(rows);labels=sorted({r['target'] for r in rows})
    vocab=sorted({t for r in parts['train'] for t in features(r['name'])})
    x={k:encode([r['name'] for r in v],vocab) for k,v in parts.items()}
    y={k:np.array([labels.index(r['target']) for r in v]) for k,v in parts.items()}
    support=np.bincount(y['train'],minlength=len(labels))
    cw=np.minimum(3,np.sqrt(len(y['train'])/(len(labels)*np.maximum(support,1))))
    rng=np.random.default_rng(SEED)
    weights=[rng.normal(0,1/np.sqrt(len(vocab)),(len(vocab),64)),np.zeros(64),rng.normal(0,1/8,(64,len(labels))),np.zeros(len(labels))]
    m=[np.zeros_like(w) for w in weights];v=[np.zeros_like(w) for w in weights]
    best=copy.deepcopy(weights);best_loss=float('inf');stale=0;step=0;trace=[];best_epoch=0
    for epoch in range(epochs):
        for batch in np.array_split(rng.permutation(len(y['train'])),max(1,(len(y['train'])+63)//64)):
            gs=gradients(x['train'][batch],y['train'][batch],weights,cw);step+=1
            for i,g in enumerate(gs):
                g=np.clip(g,-5,5);m[i]=.9*m[i]+.1*g;v[i]=.999*v[i]+.001*g*g
                weights[i]-=.003*(m[i]/(1-.9**step))/(np.sqrt(v[i]/(1-.999**step))+1e-8)
        loss=metrics(y['validation'],forward(x['validation'],weights)[0],labels)['cross_entropy'];trace.append(loss)
        if loss<best_loss-.0001:best_loss=loss;best=copy.deepcopy(weights);stale=0;best_epoch=epoch+1
        else:stale+=1
        if stale>=20:break
    artifact={'version':VERSION,'source_sha256':source_sha256,'seed':SEED,'vocabulary':vocab,'labels':labels,
              'training_support':support.tolist(),'weights':[w.tolist() for w in best],'hidden_units':64,
              'purpose':'Experimental source target-category suggestions only; no program authority'}
    report={'version':VERSION,'source_sha256':source_sha256,'seed':SEED,'numpy_version':np.__version__,
            'input':'Exercise names only; binary words and bigrams with L2 normalization',
            'training':'64-unit tanh hidden layer, softmax, weighted cross-entropy, Adam; validation early stopping',
            'split_policy':'SHA256(seed:normalized family) mod100: train<70, validation<85, test>=85',
            'source_count':len(rows),'vocabulary_size':len(vocab),'epochs_run':len(trace),'best_epoch':best_epoch,'validation_loss_trace':trace,
            'partitions':{k:{'count':len(v),'families':len({family(r['name']) for r in v}),'exercise_ids':[str(r['id']) for r in v]} for k,v in parts.items()},
            'metrics':{k:metrics(y[k],forward(x[k],best)[0],labels) for k in parts},
            'test_majority_baseline':float((y['test']==int(support.argmax())).mean()),
            'limitations':['Measures agreement with source categories, not anatomical truth or clinical outcomes.',
              'Family grouping is a text heuristic; related exercises may still cross partitions.',
              'Rare categories may have no train or held-out support; inspect per-class counts.',
              'Name-only model does not understand biomechanics, video, optimal order or safety.',
              'Softmax scores are not calibrated probabilities. Inference is an experimental suggestion.',
              'No user records or external textbook text were used; no real-user RPE model was trained.']}
    nearest=(x['test']@x['train'].T).argmax(axis=1)
    report['test_nearest_name_baseline']=float((y['test']==y['train'][nearest]).mean())
    guesses=[predict(artifact,r['name']) for r in parts['test']]
    suggested=[(r,g) for r,g in zip(parts['test'],guesses) if g['status']=='experimental_suggestion']
    report['test_suggestion_gate']={'suggested_count':len(suggested),'heldout_count':len(guesses),
        'coverage':len(suggested)/len(guesses),
        'accuracy_when_suggesting':sum(r['target']==g['suggestions'][0]['target'] for r,g in suggested)/len(suggested) if suggested else None,
        'note':'Fixed conservative engineering thresholds, not calibrated safety or clinical confidence.'}
    return artifact,report

def validate(artifact):
    if artifact.get('version')!=VERSION:raise ValueError('Unsupported exercise model')
    vocab,labels=artifact['vocabulary'],artifact['labels']
    if not 1<=len(vocab)<=20000 or not 2<=len(labels)<=100 or len(set(vocab))!=len(vocab) or len(set(labels))!=len(labels):raise ValueError('Invalid exercise model vocabulary')
    shapes=[(len(vocab),64),(64,),(64,len(labels)),(len(labels),)]
    weights=[np.asarray(w,dtype=float) for w in artifact['weights']];support=np.asarray(artifact['training_support'])
    if len(weights)!=4 or any(w.shape!=s or not np.isfinite(w).all() for w,s in zip(weights,shapes)):raise ValueError('Invalid exercise model weights')
    if support.shape!=(len(labels),) or not np.isfinite(support).all() or np.any(support<0):raise ValueError('Invalid exercise model support')
    return weights

def predict(artifact,name):
    weights=validate(artifact);tokens=set(words(name));known=tokens&set(artifact['vocabulary']);coverage=len(known)/max(len(tokens),1)
    p=forward(encode([name],artifact['vocabulary']),weights)[0][0];order=p.argsort()[::-1][:3]
    enough=coverage>=.8 and len(known)>=2 and p[order[0]]>=.75 and p[order[0]]-p[order[1]]>=.25 and artifact['training_support'][order[0]]>=20
    return {'status':'experimental_suggestion' if enough else 'uncertain',
            'suggestions':[{'target':artifact['labels'][i],'model_score':float(p[i]),'training_support':artifact['training_support'][i]} for i in order] if known else [],
            'known_word_fraction':coverage,'model_version':VERSION,
            'note':'Uncalibrated model scores; confirm the exact exercise in the catalog. Never a safety clearance.'}

def main():
    from .media_assets import data_dir
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=data_dir()/'exercises.json');parser.add_argument('--output',type=Path,default=data_dir()/'knowledge')
    parser.add_argument('--epochs',type=int,default=180);args=parser.parse_args()
    if not 1<=args.epochs<=1000:parser.error('--epochs must be 1..1000')
    raw=args.source.read_bytes();artifact,report=train(json.loads(raw),hashlib.sha256(raw).hexdigest(),args.epochs)
    args.output.mkdir(parents=True,exist_ok=True);model=json.dumps(artifact,separators=(',',':'),allow_nan=False).encode()
    report['model_sha256']=hashlib.sha256(model).hexdigest();(args.output/'exercise-model.json').write_bytes(model)
    (args.output/'training-report.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'source_count':report['source_count'],'best_epoch':report['best_epoch'],'test':report['metrics']['test'],
                      'test_majority_baseline':report['test_majority_baseline'],'partitions':{k:v['count'] for k,v in report['partitions'].items()}},indent=2))
if __name__=='__main__':main()
