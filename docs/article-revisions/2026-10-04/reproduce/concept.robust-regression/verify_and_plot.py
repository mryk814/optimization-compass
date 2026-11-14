"""Huber location fitting with exact threshold and independent least_squares checks."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/oc-foundations-mpl')
import json
from pathlib import Path
import numpy as np
import scipy
from scipy.optimize import least_squares
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
P=Path(__file__).resolve().parent;(P/'media').mkdir(exist_ok=True)
font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams.update({'font.family':'Noto Sans CJK JP','font.size':11,'svg.fonttype':'path','axes.spines.top':False,'axes.spines.right':False})
def rho(r,d):
 r=np.asarray(r);return np.where(abs(r)<=d,.5*r*r,d*(abs(r)-.5*d))
def psi(r,d):return np.clip(r,-d,d)
def fit_exact(m,d):
 assert d>0
 return np.sign(m)*min(abs(m)/4,d/3)
y=np.array([0.,0.,0.,10.]);results={}
for loss in ['linear','huber']:
 r=least_squares(lambda x:x[0]-y,[0.],method='trf',loss=loss,f_scale=1.,ftol=1e-12,xtol=1e-12,gtol=1e-12)
 x=float(r.x[0]);res=x-y;cost=float(.5*res@res if loss=='linear' else rho(res,1).sum());slopes=res if loss=='linear' else psi(res,1)
 assert r.success and np.isclose(r.cost,cost)
 assert abs(slopes.sum())<1e-8
 results[loss]={'x':x,'residuals':res.tolist(),'loss_contributions':(.5*res**2 if loss=='linear' else rho(res,1)).tolist(),'gradient_contributions':slopes.tolist(),'cost':cost,'success':bool(r.success)}
assert np.isclose(results['linear']['x'],2.5) and np.isclose(results['linear']['cost'],37.5)
assert np.isclose(results['huber']['x'],1/3) and np.isclose(results['huber']['cost'],28/3)
# Include exact threshold (m=4d/3), zero, both signs and larger scales.
cases=[]
for m,d in [(0,1),(4/3,1),(-4/3,1),(1,1),(10,.25),(10,1),(10,3),(10,7.5),(10,10),(-10,1),(100,1)]:
 x=fit_exact(m,d);obs=np.array([0.,0.,0.,m]);res=x-obs
 assert abs(psi(res,d).sum())<1e-12
 rr=least_squares(lambda z:z[0]-obs,[0.],method='trf',loss='huber',f_scale=d,ftol=1e-12,xtol=1e-12,gtol=1e-12)
 assert rr.success and np.isclose(rr.x[0],x,atol=1e-8) and np.isclose(rr.cost,rho(res,d).sum())
 cases.append({'outlier':m,'delta':d,'analytic_x':float(x),'solver_x':float(rr.x[0]),'cost':float(rr.cost),'gradient_sum':float(psi(res,d).sum())})
# Value and first derivative match at +/-delta.
for d in [.25,1,7.5]:
 assert np.isclose(.5*d*d,d*(d-.5*d))
 assert psi(d,d)==d and psi(-d,d)==-d
# Standardizing residuals is equivalent after a common positive rescaling of the objective.
sigma=10.;scaled=least_squares(lambda z:(z[0]-y)/sigma,[0.],loss='huber',f_scale=.1,gtol=1e-12,ftol=1e-12,xtol=1e-12)
assert np.isclose(scaled.x[0],1/3)
fig,axs=plt.subplots(1,3,figsize=(13.5,4.7),layout='constrained')
r=np.linspace(-3,3,500);ax=axs[0]
ax.plot(r,r,lw=2,color='#718ca8',label='二乗損失の傾き r')
ax.plot(r,psi(r,1),lw=3,color='#c45b30',label='Huberの傾き（δ=1）')
ax.axvline(-1,color='#aaa',lw=.8,ls=':');ax.axvline(1,color='#aaa',lw=.8,ls=':');ax.axhline(0,color='#bbb',lw=.7)
ax.set(xlabel='残差 r',ylabel='一観測の勾配への寄与',title='① 残差が大きくても傾きは±1');ax.legend(frameon=False,fontsize=9,loc='upper left');ax.grid(alpha=.12)
ax=axs[1];pos=np.arange(4);width=.34
bars1=ax.bar(pos-width/2,results['linear']['gradient_contributions'],width,color='#718ca8',label='二乗の解 x=2.5')
bars2=ax.bar(pos+width/2,results['huber']['gradient_contributions'],width,color='#c45b30',label='Huberの解 x=1/3')
ax.bar_label(bars1,labels=['2.5','2.5','2.5','−7.5'],fontsize=9,padding=2)
ax.bar_label(bars2,labels=['1/3','1/3','1/3','−1'],fontsize=9,padding=2)
ax.axhline(0,color='#888',lw=.8);ax.set(xticks=pos,xticklabels=['0①','0②','0③','10'],xlabel='四つの観測値',ylabel='各解での勾配への寄与',ylim=(-8.7,5),title='② どちらの解でも寄与の和は0');ax.legend(frameon=False,fontsize=9,loc='upper right')
ax=axs[2];ds=np.linspace(.01,10,500);ax.plot(ds,np.minimum(2.5,ds/3),lw=2.7,color='#c45b30');ax.axhline(2.5,color='#718ca8',ls='--',label='二乗の解 2.5')
ax.scatter([1,7.5],[1/3,2.5],color='#c45b30',zorder=4)
ax.annotate('δ=1 → x=1/3',(1,1/3),xytext=(12,5),textcoords='offset points',fontsize=10)
ax.annotate('δ≥7.5：二乗と同じ',(7.5,2.5),xytext=(-112,-28),textcoords='offset points',fontsize=10)
ax.set(xlim=(0,10),ylim=(0,3),xlabel='Huberの尺度 δ',ylabel='推定値 x',title='③ 尺度で推定の意味が変わる');ax.grid(alpha=.12);ax.legend(frameon=False,fontsize=9,loc='upper left')
fig.suptitle('観測 (0, 0, 0, 10)：外れた一観測を「消す」のではなく、傾きを制限する',fontsize=14)
for ext in ['svg','png']:fig.savefig(P/'media'/f'robust-regression-huber.{ext}',dpi=180)
plt.close(fig)
report={'versions':{'numpy':np.__version__,'scipy':scipy.__version__,'matplotlib':matplotlib.__version__},'fits':results,'threshold_formula':'sign(m)*min(abs(m)/4, delta/3), delta>0','cases':cases,'boundary_checks':'rho and first derivative continuous at +/-delta for delta .25,1,7.5','standardized_residual_equivalence':{'sigma':10,'delta_standardized':.1,'x':float(scaled.x[0])},'tests':'all assertions passed'}
(P/'verified-numbers.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
