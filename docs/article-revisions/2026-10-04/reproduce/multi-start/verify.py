from pathlib import Path
import json,os
os.environ.setdefault('MPLCONFIGDIR','/tmp/optimization-compass-mpl')
import numpy as np,scipy,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from scipy.optimize import minimize
OUT=Path(__file__).parent
MEDIA=OUT/'media';MEDIA.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc').get_name(),'font.size':11,'axes.unicode_minus':False,'svg.fonttype':'path'})
def f(x):return float(10.*len(x)+np.sum(x**2-10.*np.cos(2.*np.pi*x)))
rng=np.random.default_rng(7);rows=[];clusters=[];best=np.inf;total=0
for j in range(25):
 x0=rng.uniform(-5.12,5.12,size=2);r=minimize(f,x0,method='BFGS')
 match=next((i for i,c in enumerate(clusters) if np.linalg.norm(r.x-np.array(c['representative']))<1e-3),None)
 if match is None:match=len(clusters);clusters.append({'representative':r.x.tolist(),'count':0})
 clusters[match]['count']+=1;best=min(best,r.fun);total+=r.nfev
 rows.append({'run':j+1,'start':x0.tolist(),'end':r.x.tolist(),'fun':float(r.fun),'success':bool(r.success),'message':r.message,'nfev':r.nfev,'total_nfev':total,'best':float(best),'cluster':match+1})
assert len(clusters)==23;assert total==882;assert np.isclose(best,.9949590570932934);assert all(a['success'] for a in rows);assert f(np.zeros(2))==0
fig,axes=plt.subplots(1,3,figsize=(14,5),layout='constrained',gridspec_kw={'width_ratios':[1.15,1.05,.6]})
ax=axes[0];u=np.linspace(-5.3,5.3,450);X,Y=np.meshgrid(u,u);Z=20+X*X+Y*Y-10*np.cos(2*np.pi*X)-10*np.cos(2*np.pi*Y)
ax.contourf(X,Y,Z,levels=18,cmap='Greys',alpha=.14)
for a in rows:
 start=np.array(a['start']);end=np.array(a['end']);ax.annotate('',xy=end,xytext=start,arrowprops={'arrowstyle':'->','color':'#2f5b95','alpha':.6,'lw':1})
ax.scatter(*np.array([a['start'] for a in rows]).T,facecolors='white',edgecolors='#2f5b95',s=28,label='初期点')
ax.scatter(*np.array([a['end'] for a in rows]).T,color='#168879',s=30,label='局所求解後')
ax.scatter(0,0,marker='*',color='#bf543b',s=140,label='既知の最小点（未到達）')
ax.set(xlim=(-5.3,5.3),ylim=(-5.3,5.3),xlabel='x1',ylabel='x2',title='25初期点 → 23個の到達点',aspect='equal');ax.legend(fontsize=9,loc='upper left')
ax=axes[1];ax.step([a['total_nfev'] for a in rows],[a['best'] for a in rows],where='post',color='#168879')
ax.scatter([a['total_nfev'] for a in rows],[a['fun'] for a in rows],color='#8497ae',s=20,label='各局所求解の目的値')
ax.axhline(0,color='#bf543b',ls='--',label='解析的な最小値 0')
ax.set(xlabel='累積目的関数評価回数',ylabel='目的値',title=f'882評価後の最良値 {best:.6f}')
ax.legend(fontsize=9)
ax=axes[2];counts=[sum(c['count']==k for c in clusters) for k in [1,2,3]]
ax.bar([1,2,3],counts,color=['#2f5b95','#168879','#8497ae'])
for x,y in zip([1,2,3],counts):ax.text(x,y+.25,str(y),ha='center')
ax.set(xticks=[1,2,3],xlabel='1到達点への本数',ylabel='到達点の数',title='距離 < 0.001 で同一判定',ylim=(0,24))
fig.suptitle('Multi-start  |  局所求解が全25本成功しても大域最適解は見つかるとは限らない',fontsize=14)
for ext in ['svg','png']:fig.savefig(MEDIA/f'multi-start-basins.{ext}',dpi=170)
report={'numpy':np.__version__,'scipy':scipy.__version__,'rng':'numpy.default_rng(7)','local_solver':'BFGS, jac=None, default options','initial_sampling_box':[-5.12,5.12],'local_bounds':None,'distinct_tolerance':.001,'runs':rows,'clusters':clusters,'summary':{'distinct':len(clusters),'duplicates':25-len(clusters),'successes':sum(a['success'] for a in rows),'nfev':total,'best':float(best)},'oracle':{'x':[0,0],'f':0},'tests':'passed'}
(OUT/'verified-numbers.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report['summary']));print(clusters)
