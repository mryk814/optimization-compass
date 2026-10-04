from pathlib import Path
import json,os
os.environ.setdefault('MPLCONFIGDIR','/tmp/optimization-compass-mpl')
import numpy as np,scipy,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from scipy.special import logsumexp
from scipy.integrate import quad
OUT=Path(__file__).parent
MEDIA=OUT/'media';MEDIA.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc').get_name(),'font.size':11,'axes.unicode_minus':False,'svg.fonttype':'path'})
good=np.array([.8,1.2]);bad=np.array([-1.,0.,3.]);bandwidth=.5;candidates=np.array([0.,1.,2.])
def log_density(x,observed,h=.5):
 x=np.atleast_1d(x);z=-.5*((x[:,None]-observed[None,:])/h)**2
 return logsumexp(z,axis=1)-np.log(len(observed))-np.log(h*np.sqrt(2*np.pi))
def density(x,obs,h=.5):return np.exp(log_density(x,obs,h))
logratio=log_density(candidates,good)-log_density(candidates,bad);ratios=np.exp(logratio);chosen=float(candidates[logratio.argmax()])
assert np.allclose(ratios,[.441507,20.361931,3.694666],atol=1e-6);assert chosen==1
integrals=[quad(lambda x:float(density(x,g)[0]),-np.inf,np.inf,epsabs=1e-10)[0] for g in [good,bad]]
assert np.allclose(integrals,[1,1],atol=1e-10)
# Log ratio stays finite even when both ordinary densities underflow at a remote point.
far=100.;assert density(far,good)[0]==0 and density(far,bad)[0]==0
assert np.isfinite(log_density(far,good)[0]-log_density(far,bad)[0])
f=lambda x:(x-1)**2
contrast_x=1.45;contrast_ratio=float(np.exp(log_density(contrast_x,good)[0]-log_density(contrast_x,bad)[0]));assert contrast_ratio>ratios.max() and f(contrast_x)>.04
fig,axes=plt.subplots(1,3,figsize=(14,4.8),layout='constrained');xs=np.linspace(-2,4,700)
ax=axes[0];ax.scatter(good,f(good),color='#168879',s=70,label='良い群 2点');ax.scatter(bad,f(bad),color='#7d8c9e',s=60,label='残りの群 3点');ax.axhline(.5,color='#bf543b',ls='--',label='分割閾値 y* = 0.5');ax.scatter([chosen],[f(chosen)],facecolors='none',edgecolors='#bf543b',marker='o',s=130,lw=2,label='提案後に初めて評価')
ax.set(xlabel='設定 x',ylabel='観測した目的値',title='1. 同じ5観測を良い群と残りへ');ax.legend(fontsize=9,loc='upper center');ax.set_ylim(-.4,5.2)
ax=axes[1];ax.plot(xs,density(xs,good),color='#168879',lw=2,label='l(x): 良い群');ax.plot(xs,density(xs,bad),color='#7d8c9e',lw=2,label='g(x): 残りの群');ax.scatter(good,np.full(2,-.025),marker='|',s=140,color='#168879');ax.scatter(bad,np.full(3,-.025),marker='|',s=140,color='#7d8c9e');ax.set(xlabel='設定 x',ylabel='正規化した確率密度',title='2. 固定帯域 0.5 のGaussian KDE');ax.legend(fontsize=10)
ax=axes[2];ax.plot(xs,np.exp(log_density(xs,good)-log_density(xs,bad)),color='#2f5b95',lw=2,label='密度比 l(x) / g(x)')
ax.scatter(candidates,ratios,color='#bf543b',s=60,zorder=4)
for x,y in zip(candidates,ratios):ax.annotate(f'x={x:.0f}: {y:.2f}',(x,y),xytext=(7,7),textcoords='offset points',fontsize=10)
ax.set(xlabel='候補 x（比較するのは 0, 1, 2）',ylabel='密度比',title='3. この3候補なら x=1 を選ぶ');ax.legend(fontsize=10)
fig.suptitle('TPEの密度比の教材  |  観測5点、モデル、次候補を同じ例で追う',fontsize=15)
for ext in ['svg','png']:fig.savefig(MEDIA/f'tpe-five-observations.{ext}',dpi=170)
report={'numpy':np.__version__,'scipy':scipy.__version__,'type':'fixed-bandwidth unbounded Gaussian KDE teaching example; not Optuna implementation','optuna_run':'not run: not installed','good':good.tolist(),'bad':bad.tolist(),'observed_objective':'(x-1)^2','threshold':.5,'gamma':.4,'bandwidth':bandwidth,'candidates':candidates.tolist(),'l':density(candidates,good).tolist(),'g':density(candidates,bad).tolist(),'unnormalized_l':(density(candidates,good)*bandwidth*np.sqrt(2*np.pi)).tolist(),'unnormalized_g':(density(candidates,bad)*bandwidth*np.sqrt(2*np.pi)).tolist(),'ratio':ratios.tolist(),'log_ratio':logratio.tolist(),'chosen':chosen,'chosen_actual_value':f(chosen),'normalization_integrals':integrals,'remote_point':far,'remote_log_ratio':float(log_density(far,good)[0]-log_density(far,bad)[0]),'density_ratio_counterexample':{'x':contrast_x,'ratio':contrast_ratio,'true_value':f(contrast_x),'prior_best':.04},'tests':'passed'}
(OUT/'verified-numbers.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
