from pathlib import Path
import json, platform, os
os.environ.setdefault('MPLCONFIGDIR','/tmp/compass-mpl');os.environ.setdefault('XDG_CACHE_HOME','/tmp/compass-cache')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
ROOT=Path(__file__).resolve().parent
FONT=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams.update({'font.family':FONT.get_name(),'font.size':11,'svg.fonttype':'path'})
target=np.array([.65,.25,.1])
def loss(p): return float(.5*np.sum((p-target)**2))
def eg(p,g,eta):
    if np.any(p<=0) or not np.all(np.isfinite(p)): raise ValueError('strictly positive p required')
    z=np.log(p)-eta*g;z-=z.max();w=np.exp(z)
    return w/w.sum()
def pg(p,g,eta):
    v=p-eta*g;u=np.sort(v)[::-1];s=np.cumsum(u)-1
    rho=np.nonzero(u*np.arange(1,len(v)+1)>s)[0][-1]
    return np.maximum(v-s[rho]/(rho+1),0)
def trajectory(method,steps=166):
    p=np.ones(3)/3;rows=[p.copy()]
    for _ in range(steps): p=method(p,p-target,.8);rows.append(p.copy())
    return np.array(rows)
def main():
    e=trajectory(eg);u=trajectory(pg)
    p=e[0];g=p-target;mult=np.exp(-.8*g);raw=p*mult
    zero=np.array([.5,.5,0.]);
    for _ in range(500):
        w=zero*np.exp(-.8*(zero-target));zero=w/w.sum()
    assert np.allclose(zero,[.7,.3,0])
    assert np.all(e>0) and np.max(abs(e.sum(axis=1)-1))<1e-14
    assert np.allclose(e[1],raw/raw.sum())
    assert np.allclose(eg(p,np.array([1000.,1001.,1002.]),.8),eg(p,np.array([0.,1.,2.]),.8))
    em=int(np.nonzero(np.linalg.norm(e-target,axis=1)<1e-9)[0][0]);um=int(np.nonzero(np.linalg.norm(u-target,axis=1)<1e-9)[0][0])
    eta3={'unprojected':(p-3*g).tolist(),'projected':pg(p,g,3).tolist(),'entropic':eg(p,g,3).tolist()}
    out={'environment':{'python':platform.python_version(),'numpy':np.__version__,'matplotlib':matplotlib.__version__},'target':target.tolist(),'eta':.8,
         'first_four':[{'k':k,'p':v.tolist(),'loss':loss(v)} for k,v in enumerate(e[:4])],
         'first_step':{'gradient':g.tolist(),'multipliers':mult.tolist(),'unnormalized':raw.tolist(),'normalizer':float(raw.sum())},
         'same_eta_comparison':{'entropic_loss_after_1':loss(e[1]),'projected_point_after_1':u[1].tolist(),'projected_loss_after_1':loss(u[1]),'updates_to_gradient_1e-9':{'entropic':em,'projected':um}},
         'eta3':eta3,'zero_support_limit':zero.tolist(),'zero_support_loss':loss(zero),'maximum_simplex_error':float(np.max(abs(e.sum(axis=1)-1))),'assertions':'passed'}
    (ROOT/'verified-numbers.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    vertices=np.array([[0.,0.],[1.,0.],[.5,np.sqrt(3)/2]])
    fig,axs=plt.subplots(1,3,figsize=(14,4.8),layout='constrained')
    ax=axs[0];vv=vertices[[0,1,2,0]];ax.plot(*vv.T,color='#839496')
    ep=e[:7]@vertices;up=u[:4]@vertices
    ax.plot(*ep.T,'o-',color='#166e99',label='Mirror：6更新');ax.plot(*up.T,'s--',color='#c46b22',label='射影勾配：3更新')
    ax.scatter(*(target@vertices),s=140,marker='*',color='#253746',label='目標 t',zorder=5)
    for i,(x,y) in enumerate(vertices):ax.text(x,y+.035 if i==2 else y-.06,f'p{i+1}=1',ha='center')
    ax.set(xlim=(-.15,1.15),ylim=(-.18,1.02),title='A. 同じ単体・同じ η=0.8');ax.set_aspect('equal');ax.axis('off');ax.legend(loc='upper left',bbox_to_anchor=(-.06,.90),fontsize=9)
    ax=axs[1];a=np.arange(3);width=.25
    ax.bar(a-width,p,width,label='初期 p0',color='#99a9b4');ax.bar(a,raw,width,label='乗算後 q',color='#166e99');ax.bar(a+width,e[1],width,label='正規化後 p1',color='#c46b22')
    ax.set(xticks=a,xticklabels=['成分1','成分2','成分3'],ylim=(0,.53),ylabel='成分の大きさ',title='B. 乗算してから、合計で割る');ax.legend(fontsize=9)
    ax=axs[2];ax.semilogy(range(14),[loss(v) for v in e[:14]],'o-',color='#166e99',label='Mirror')
    ax.semilogy(range(14),[loss(v) for v in u[:14]],'s--',color='#c46b22',label='射影勾配')
    ax.set(xlabel='更新数',ylabel='損失（対数目盛）',title='C. この二次損失では射影勾配が速い');ax.grid(alpha=.18);ax.legend()
    fig.suptitle('Mirror Descent：同じ勾配でも、幾何が一手を変える',fontsize=16)
    (ROOT/'media').mkdir(exist_ok=True)
    for ext in ['svg','png']:fig.savefig(ROOT/'media'/f'mirror-simplex-step.{ext}',dpi=180)
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
