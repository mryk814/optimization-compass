from pathlib import Path
import json
import numpy as np
from scipy.optimize import minimize,minimize_scalar
from example import solve,values,gradients,approximation
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'Noto Sans CJK JP','font.size':10,'svg.fonttype':'none'})
ROOT=Path(__file__).parent;MEDIA=ROOT/'site/public/media';MEDIA.mkdir(parents=True,exist_ok=True)
history=solve();checks=[]
for row in history:
 x,L,U=row['x'],row['L'],row['U'];p,q,r=approximation(x,L,U)
 model=lambda z:r+p/(U-z)+q/(z-L)
 dmodel=lambda z:p/(U-z)**2-q/(z-L)**2
 assert np.max(abs(model(x)-values(x)))<1e-12
 assert np.max(abs(dmodel(x)-gradients(x)))<1e-12
 eps=1e-6;fd=(model(x+eps)-model(x-eps))/(2*eps)
 assert np.max(abs(fd-gradients(x)))<1e-8
 candidate=row['candidate'];assert model(candidate)[1]<1e-10 and values(candidate)[1]<1e-10
 res=minimize(lambda z:float(model(z[0])[0]),[x],jac=lambda z:np.array([dmodel(z[0])[0]]),method='SLSQP',bounds=[(row['alpha'],row['beta'])],constraints={'type':'ineq','fun':lambda z:-model(z[0])[1],'jac':lambda z:np.array([-dmodel(z[0])[1]])},options={'ftol':1e-12,'maxiter':100})
 assert abs(res.x[0]-candidate)<1e-7
 checks.append(dict(k=row['k'],contact_value_error=float(np.max(abs(model(x)-values(x)))),contact_gradient_error=float(np.max(abs(dmodel(x)-gradients(x)))),independent_candidate=float(res.x[0]),independent_error=float(abs(res.x[0]-candidate))))
assert abs(history[-1]['candidate']-1.25)<1e-9
# Reproduce the original fixed-width introductory toy independently.
toy=[];x=0.
for k in range(3):
 L,U=x-1,x+1;g=2*(x-2);p=max(g,0)+.01;q=max(-g,0)+.01;r=(x-2)**2-p/(U-x)-q/(x-L)
 stat=(np.sqrt(q)*U+np.sqrt(p)*L)/(np.sqrt(p)+np.sqrt(q));candidate=np.clip(stat,x-.5,x+.5)
 alt=minimize_scalar(lambda z:r+p/(U-z)+q/(z-L),bounds=(x-.5,x+.5),method='bounded',options={'xatol':1e-13})
 assert abs(candidate-alt.x)<1e-7
 toy.append(dict(x=x,L=L,U=U,p=p,q=q,r=r,candidate=float(candidate),cost=float((candidate-2)**2)));x=candidate
# Prescribed histories exercise both asymptote-update branches, not solver traces.
branches=[dict(name='同方向',history=[.6,.8,1.],factor=1.2,L=-.2,U=2.2),dict(name='反転',history=[1.,1.2,1.],factor=.7,L=.3,U=1.7)]
for z in branches:
 older,last,now=z['history'];product=(now-last)*(last-older);factor=1.2 if product>0 else .7
 assert factor==z['factor'];assert abs(now-factor-z['L'])<1e-12
fig,ax=plt.subplots(2,2,figsize=(11,7.5),layout='constrained')
t=toy[0];xx=np.linspace(-.9,.9,400);ff=(xx-2)**2;mm=t['r']+t['p']/(t['U']-xx)+t['q']/(xx-t['L']);ax[0,0].plot(xx,ff,c='#22354b',label='元の目的');ax[0,0].plot(xx,mm,c='#d47a1f',label='逆数近似');ax[0,0].axvspan(-.5,.5,color='#128174',alpha=.1,label='move limit');ax[0,0].scatter([0,.5],[4,2.25],c=['#22354b','#128174']);ax[0,0].set_ylim(0,14);ax[0,0].set_title('導入toy：L=-1, U=1、最初の一手');ax[0,0].legend(fontsize=9)
t=history[2];p,q,r=approximation(t['x'],t['L'],t['U']);xx=np.linspace(.5,1.5,300);ax[0,1].plot(xx,xx**2-1.25**2,c='#22354b',label='元の制約');ax[0,1].plot(xx,r[1]+p[1]/(t['U']-xx)+q[1]/(xx-t['L']),c='#d47a1f',label='近似制約');ax[0,1].axhline(0,c='#888',ls='--');ax[0,1].axvline(t['candidate'],c='#128174',label=f"候補 {t['candidate']:.4f}");ax[0,1].set_title('制約付きの3手目：近似制約 ≤ 0');ax[0,1].legend(fontsize=9)
kk=np.arange(len(history));ax[1,0].plot(kk,[r['candidate'] for r in history],'o-',c='#128174',label='採用候補');ax[1,0].axhline(1.25,c='#22354b',ls='--',label='解析解 1.25');ax[1,0].set_xlabel('提案番号 k');ax[1,0].set_title('同じ目的に x² ≤ 1.25² を追加');ax[1,0].legend(fontsize=9)
for j,z in enumerate(branches):
 ax[1,1].plot([z['L'],z['U']],[j,j],lw=8,c=['#128174','#bf4c58'][j],solid_capstyle='butt');ax[1,1].scatter(1,j,c='#22354b',zorder=5);ax[1,1].text(1,j+.12,f"{z['history']} → 倍率{z['factor']}",ha='center',fontsize=10)
ax[1,1].set_yticks([0,1],['同方向','反転']);ax[1,1].set_xlim(-.4,2.4);ax[1,1].set_ylim(-.35,1.5);ax[1,1].set_title('規則の単体テスト：旧距離を1と固定');ax[1,1].set_xlabel('新しい漸近線の位置（現在点は1）')
for a in ax.flat:a.grid(alpha=.2)
for a in ax[0]:a.set_xlabel('x')
fig.suptitle('MMAの機構を分けて読む：逆数近似・制約・履歴・移動上限',fontsize=15)
for ext in ('svg','png'):fig.savefig(MEDIA/f'mma-reciprocal-constraints.{ext}',dpi=160)
(ROOT/'verified-numbers.json').write_text(json.dumps({'intro_toy':toy,'constrained_history':history,'subproblem_checks':checks,'prescribed_history_tests':branches,'analytic_solution':1.25,'analytic_cost':.5625},indent=2,ensure_ascii=False)+'\n')
