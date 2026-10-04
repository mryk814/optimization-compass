from pathlib import Path
import json,os
os.environ.setdefault('MPLCONFIGDIR','/tmp/optimization-compass-mpl')
import numpy as np,scipy,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from scipy.optimize import basinhopping
OUT=Path(__file__).parent
MEDIA=OUT/'media';MEDIA.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc').get_name(),'font.size':11,'axes.unicode_minus':False,'svg.fonttype':'path'})
class LoggingRNG(np.random.RandomState):
 def __init__(self,seed):super().__init__(seed);self.draws=[]
 def uniform(self,*args,**kwargs):
  value=super().uniform(*args,**kwargs);self.draws.append(np.asarray(value).tolist());return value
rng=LoggingRNG(7);evaluations=[];rows=[];state=None;state_f=None;best=np.inf;draw_index=0;last_nfev=0
f=lambda x:float(np.sum(x**2-10*np.cos(2*np.pi*x)+10))
def counted(x):evaluations.append({'x':x.tolist(),'f':f(x)});return f(x)
def cb(x,fx,accepted):
 global state,state_f,best,draw_index,last_nfev
 if state is None:
  state=x.copy();state_f=fx;best=fx
  row={'iteration':0,'local_start':[2.5,-1.5],'candidate':x.tolist(),'candidate_f':fx,'accepted':bool(accepted),'nfev':len(evaluations)}
 else:
  draws=rng.draws[draw_index:];assert len(draws)==2
  displacement=np.array(draws[0]);u=float(draws[1]);p=float(np.exp(min(0.,-(fx-state_f))))
  proposal=state+displacement
  row={'iteration':len(rows),'current_before':state.tolist(),'current_f_before':state_f,'displacement':displacement.tolist(),'local_start':proposal.tolist(),'raw_f':f(proposal),'candidate':x.tolist(),'candidate_f':fx,'p':p,'u':u,'accepted':bool(accepted),'nfev':len(evaluations)-last_nfev}
  # No local failures in this run. Compare against actual SciPy Metropolis decision.
  assert bool(u<=p)==bool(accepted)
  if accepted:state=x.copy();state_f=fx
  best=min(best,fx)
 row.update(current_after=state.tolist(),current_f_after=state_f,best=best,total_nfev=len(evaluations));rows.append(row);draw_index=len(rng.draws);last_nfev=len(evaluations)
r=basinhopping(counted,[2.5,-1.5],niter=50,T=1.,stepsize=.5,seed=rng,minimizer_kwargs={'method':'BFGS'},callback=cb)
assert [a['accepted'] for a in rows[:4]]==[True,False,False,True]
assert np.allclose(rows[1]['current_after'],rows[0]['candidate']);assert len(evaluations)==r.nfev;assert r.minimization_failures==0
fig,axes=plt.subplots(1,3,figsize=(14,4.9),layout='constrained')
for ax,a in zip(axes,rows[1:4]):
 pts=np.array([a['current_before'],a['local_start'],a['candidate']]);lo=pts.min(0)-.65;hi=pts.max(0)+.65
 X,Y=np.meshgrid(np.linspace(lo[0],hi[0],250),np.linspace(lo[1],hi[1],250));Z=X*X+Y*Y-10*np.cos(2*np.pi*X)-10*np.cos(2*np.pi*Y)+20
 ax.contour(X,Y,Z,levels=[5,10,20,30,40],colors='#d0d9e4',linewidths=.7)
 for start,end,col,ls in [(pts[0],pts[1],'#c77d25','--'),(pts[1],pts[2],'#2f5b95','-')]:ax.annotate('',xy=end,xytext=start,arrowprops={'arrowstyle':'->','color':col,'lw':2,'linestyle':ls})
 ax.scatter(*pts[0],color='#18334f',s=65,label='現在の谷底',zorder=6)
 ax.scatter(*pts[1],marker='^',color='#c77d25',s=65,label='ランダム移動後',zorder=5)
 ax.scatter(*pts[2],marker='X',color='#168879' if a['accepted'] else '#bf543b',s=95,label='局所求解後',zorder=7)
 decision='受理して移る' if a['accepted'] else '棄却、現在点は変わらない'
 ax.set(xlabel='x1',ylabel='x2',title=f"候補{a['iteration']}：{decision}\np={a['p']:.4f}, u={a['u']:.4f}")
 ax.text(.02,.02,f"谷底の値 {a['current_f_before']:.4f} → {a['candidate_f']:.4f}\n局所求解 {a['nfev']}評価",transform=ax.transAxes,fontsize=10,bbox={'facecolor':'white','edgecolor':'none','alpha':.9})
 ax.legend(fontsize=9,loc='upper left')
fig.suptitle('Basin Hopping  |  跳ぶ → 局所求解 → 谷底の値で受理判定',fontsize=15)
for ext in ['svg','png']:fig.savefig(MEDIA/f'basin-hopping-three-stages.{ext}',dpi=170)
report={'numpy':np.__version__,'scipy':scipy.__version__,'rng':'legacy RandomState(7), uniform calls logged without changing draws','T':1.,'stepsize_initial':.5,'niter':50,'local_solver':'BFGS, jac=None, default options','rows':rows,'evaluations':evaluations,'result':{'x':r.x.tolist(),'fun':float(r.fun),'nfev':r.nfev,'minimization_failures':r.minimization_failures,'message':r.message},'oracle':{'x':[0,0],'f':0},'tests':'passed'}
(OUT/'verified-numbers.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(rows[:4],ensure_ascii=False,indent=2));print(report['result'])
