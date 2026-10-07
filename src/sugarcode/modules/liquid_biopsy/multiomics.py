"""Fitted logistic classification on supplied numeric features, not a clinical model."""
from __future__ import annotations
import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp


def _matrix(X):
    x=np.asarray(X,float)
    if x.ndim!=2 or min(x.shape)==0 or not np.isfinite(x).all():
        raise ValueError('nonempty finite samples-by-features matrix required')
    return x


def _labels(y, count):
    y=list(y)
    if len(y)!=count or any(not isinstance(v,str) or not v for v in y):
        raise ValueError('one nonempty string label per sample required')
    return y


def fit_multiomics_classifier(X, labels, *, feature_names=None, l2=1., max_iter=1000):
    """Train regularized multiclass logistic regression; stats fit on X only.

    Dataset source, split independence, batch confounding and clinical validity
    must be checked by the caller. No pretrained disease model is bundled.
    """
    x=_matrix(X); y=_labels(labels,len(x)); classes=sorted(set(y))
    if len(classes)<2:
        raise ValueError('at least two label classes required')
    if isinstance(l2,bool) or not np.isfinite(l2) or l2<=0:
        raise ValueError('positive finite regularization required')
    if isinstance(max_iter,bool) or not isinstance(max_iter,int) or max_iter<1:
        raise ValueError('positive integer max_iter required')
    names=list(feature_names) if feature_names is not None else ['feature_'+str(i) for i in range(x.shape[1])]
    if len(names)!=x.shape[1] or len(set(names))!=len(names) or any(not isinstance(v,str) or not v for v in names):
        raise ValueError('unique feature names must match feature columns')
    mean=x.mean(0); scale=x.std(0); scale=np.where(scale>0,scale,1.)
    z=(x-mean)/scale
    if not np.isfinite(z).all():
        raise ValueError('standardization overflow')
    z=np.column_stack([z,np.ones(len(z))]); k=len(classes)
    encoded=np.array([classes.index(v) for v in y]); target=np.eye(k)[encoded]
    def objective(flat):
        w=flat.reshape(z.shape[1],k); logits=z@w
        logp=logits-logsumexp(logits,axis=1,keepdims=True)
        loss=-np.sum(target*logp)/len(z)+l2*np.sum(w[:-1]**2)/(2*len(z))
        grad=z.T@(np.exp(logp)-target)/len(z); grad[:-1]+=l2*w[:-1]/len(z)
        return loss,grad.ravel()
    result=minimize(objective,np.zeros(z.shape[1]*k),jac=True,method='L-BFGS-B',options={'maxiter':max_iter,'ftol':1e-12})
    if not result.success or not np.isfinite(result.x).all():
        raise RuntimeError('classifier optimizer did not converge: '+str(result.message))
    weights=result.x.reshape(z.shape[1],k)
    return {'trained':True,'model':'L2 multinomial logistic regression','classes':classes,
            'feature_names':names,'mean':mean.tolist(),'scale':scale.tolist(),
            'weights':weights[:-1].tolist(),'intercept':weights[-1].tolist(),
            'sample_count':len(x),'class_counts':{c:y.count(c) for c in classes},
            'l2':float(l2),'converged':True,'iterations':int(result.nit),
            'training_objective':float(result.fun),
            'scope':'Fitted to supplied labels; no clinical validation or calibrated disease probabilities'}


def predict_multiomics_classifier(model,X):
    x=_matrix(X)
    try:
        mean=np.asarray(model['mean'],float);scale=np.asarray(model['scale'],float)
        weights=np.asarray(model['weights'],float);intercept=np.asarray(model['intercept'],float)
        classes=list(model['classes'])
    except (KeyError,TypeError,ValueError) as exc:
        raise ValueError('invalid fitted model') from exc
    if (model.get('trained') is not True or mean.shape!=(x.shape[1],) or scale.shape!=mean.shape or
        weights.shape!=(x.shape[1],len(classes)) or intercept.shape!=(len(classes),) or len(classes)<2 or
        len(set(classes))!=len(classes) or not np.isfinite(mean).all() or not np.isfinite(scale).all() or
        not np.isfinite(weights).all() or not np.isfinite(intercept).all() or np.any(scale<=0)):
        raise ValueError('model shapes/classes/finite parameters do not match features')
    logits=((x-mean)/scale)@weights+intercept
    if not np.isfinite(logits).all():
        raise ValueError('prediction overflow')
    probabilities=np.exp(logits-logsumexp(logits,axis=1,keepdims=True))
    return {'classes':classes,'probabilities':probabilities.tolist(),
            'predicted_labels':[classes[i] for i in probabilities.argmax(1)],
            'scope':'Fitted label-class softmax scores, not clinical calibrated probabilities'}


def evaluate_multiomics_classifier(model,X,labels):
    result=predict_multiomics_classifier(model,X);y=_labels(labels,len(result['probabilities']))
    classes=result['classes']
    if set(y)-set(classes):
        raise ValueError('evaluation labels include unseen class')
    predicted=result['predicted_labels']; p=np.asarray(result['probabilities'])
    encoded=np.array([classes.index(v) for v in y]); confusion=np.zeros((len(classes),len(classes)),int)
    for actual,guess in zip(encoded,p.argmax(1)):
        confusion[actual,guess]+=1
    majority=max(model['class_counts'],key=model['class_counts'].get)
    return {'sample_count':len(y),'accuracy':float(np.mean(np.array(predicted)==np.array(y))),
            'majority_baseline_accuracy':y.count(majority)/len(y),
            'log_loss':float(-np.log(np.maximum(p[np.arange(len(y)),encoded],1e-300)).mean()),
            'confusion_matrix':confusion.tolist(),'classes':classes,
            'scope':'Supplied labeled evaluation set; independence and assay validity not verified'}
