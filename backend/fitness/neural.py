"""CPU MLP: two tanh hidden layers, backpropagation, Adam, validation early stopping.

Weights use JSON numeric arrays, never pickle or executable model imports.
This module predicts RPE, not injuries, diagnoses or optimal causal treatment.
"""
import copy
import numpy as np
from .learning_contracts import Features,PATTERNS

VERSION='rpe-mlp-1'
NUMERIC=('experience','sleep_hours','energy','soreness','stress','reps','load_kg','target_rpe','set_number','previous_load_kg','previous_rpe','history_sessions')
N_INPUT=len(NUMERIC)+len(PATTERNS)
SHAPES=((N_INPUT,32),(32,),(32,16),(16,),(16,1),(1,))

def vector(features):
    f=Features.model_validate(features).model_dump()
    return [float(f[k]) for k in NUMERIC]+[float(f['pattern']==p) for p in PATTERNS]

def forward(x,weights):
    w1,b1,w2,b2,w3,b3=weights
    a=np.tanh(x@w1+b1);b=np.tanh(a@w2+b2);y=b@w3+b3
    return y,(a,b)

def gradients(x,y,weights):
    pred,(a,b)=forward(x,weights)
    d=2*(pred-y)/len(y)
    g3=b.T@d;gb3=d.sum(axis=0)
    d2=(d@weights[4].T)*(1-b*b)
    g2=a.T@d2;gb2=d2.sum(axis=0)
    d1=(d2@weights[2].T)*(1-a*a)
    return [x.T@d1,d1.sum(axis=0),g2,gb2,g3,gb3]

def fit(train,validation,seed=42,epochs=250):
    rng=np.random.default_rng(seed)
    raw=np.array([vector(r['features']) for r in train])
    mean=raw.mean(axis=0);scale=raw.std(axis=0);scale[scale<1e-6]=1
    x=(raw-mean)/scale;y=(np.array([r['actual_rpe'] for r in train])[:,None]-5.5)/4.5
    vx=(np.array([vector(r['features']) for r in validation])-mean)/scale
    vy=np.array([r['actual_rpe'] for r in validation])
    weights=[rng.normal(0,1/np.sqrt(s[0]),s) if len(s)==2 else np.zeros(s) for s in SHAPES]
    m=[np.zeros_like(w) for w in weights];v=[np.zeros_like(w) for w in weights]
    best=copy.deepcopy(weights);best_error=float('inf');stale=0;step=0;trace=[]
    for epoch in range(epochs):
        for batch in np.array_split(rng.permutation(len(x)),max(1,(len(x)+63)//64)):
            gs=gradients(x[batch],y[batch],weights);step+=1
            for i,g in enumerate(gs):
                g=np.clip(g,-5,5);m[i]=0.9*m[i]+0.1*g;v[i]=0.999*v[i]+0.001*g*g
                weights[i]-=0.003*(m[i]/(1-0.9**step))/(np.sqrt(v[i]/(1-0.999**step))+1e-8)
        error=float(np.mean(np.abs(np.clip(5.5+4.5*forward(vx,weights)[0][:,0],1,10)-vy)))
        trace.append(error)
        if error<best_error-0.0001:best_error=error;best=copy.deepcopy(weights);stale=0
        else:stale+=1
        if stale>=25:break
    return {'version':VERSION,'weights':[w.tolist() for w in best],'mean':mean.tolist(),'scale':scale.tolist(),
            'lower':raw.min(axis=0).tolist(),'upper':raw.max(axis=0).tolist(),
            'epochs':len(trace),'validation_mae_trace':trace,'numpy_version':np.__version__,'seed':seed}

def predict(artifact,features,check_domain=True):
    if artifact.get('version')!=VERSION:raise ValueError('Unsupported model feature version')
    weights=[np.asarray(w,dtype=float) for w in artifact['weights']]
    if len(weights)!=6 or any(w.shape!=s or not np.isfinite(w).all() for w,s in zip(weights,SHAPES)):
        raise ValueError('Invalid model weights')
    mean,scale,lo,hi=[np.asarray(artifact[k],dtype=float) for k in ('mean','scale','lower','upper')]
    if any(a.shape!=(N_INPUT,) or not np.isfinite(a).all() for a in (mean,scale,lo,hi)) or np.any(scale<=0):
        raise ValueError('Invalid model normalization')
    x=np.array(vector(features))
    if check_domain and (np.any(x<lo-1e-6) or np.any(x>hi+1e-6)):
        return None
    value=float(np.clip(5.5+4.5*forward(((x-mean)/scale)[None,:],weights)[0][0,0],1,10))
    if not np.isfinite(value):raise ValueError('Non-finite prediction')
    return value
