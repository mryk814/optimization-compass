"""Standalone textbook trace, not a complete GPS/MADS implementation."""
from pathlib import Path
import json, os
os.environ.setdefault('MPLCONFIGDIR','/tmp/optimization-compass-mpl')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
OUT=Path(__file__).parent
MEDIA=OUT/'media';MEDIA.mkdir(exist_ok=True)
FONT=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc').get_name()
plt.rcParams.update({'font.family':FONT,'font.size':11,'axes.unicode_minus':False,'svg.fonttype':'path'})

def objective(x):
    return float((1-x[0])**2+20*(x[1]-x[0]**2)**2)

def trace():
    x=np.array([-1.2,1.0]); step=.5; fx=objective(x); nfev=1
    directions=np.array([[1,0],[0,1],[-1,0],[0,-1]])
    records=[]
    for k in range(1,4):
        candidates=x+step*directions
        values=np.array([objective(q) for q in candidates]); nfev+=len(values)
        j=int(values.argmin()); success=bool(values[j]<fx)
        next_x=candidates[j].copy() if success else x.copy()
        next_f=float(values[j]) if success else fx
        next_step=min(1.2*step,1.0) if success else step*.5
        records.append(dict(poll=k,x=x.tolist(),f=fx,step=step,candidates=candidates.tolist(),values=values.tolist(),best_index=j,success=success,next_x=next_x.tolist(),next_f=next_f,next_step=next_step,nfev=nfev))
        x,fx,step=next_x,next_f,next_step
    return records

r=trace()
assert [a['success'] for a in r]==[True,False,False]
assert np.allclose(r[0]['values'],[8.092,4.912,78.732,22.512])
assert np.allclose([a['next_step'] for a in r],[.6,.3,.15])
assert r[-1]['nfev']==13
fig,axes=plt.subplots(1,3,figsize=(13.2,4.8),layout='constrained')
u=np.linspace(-1.9,-.5,350);v=np.linspace(.3,2.2,350);X,Y=np.meshgrid(u,v);Z=(1-X)**2+20*(Y-X**2)**2
names=['+e1','+e2','−e1','−e2']
for ax,a in zip(axes,r):
 ax.contour(X,Y,Z,levels=[4,5,8,12,20,40,80],colors='#c8d3df',linewidths=.8)
 x=np.array(a['x']); c=np.array(a['candidates']);
 for i,(p,val) in enumerate(zip(c,a['values'])):
  col='#168879' if a['success'] and i==a['best_index'] else '#ba593b'
  ax.annotate('',xy=p,xytext=x,arrowprops={'arrowstyle':'->','color':col,'lw':1.4})
  ax.scatter(*p,c=col,s=42,zorder=4)
  ax.annotate(f'{names[i]}  {val:.3f}',p,xytext=(-5,7) if i==0 else ((5,-17) if i==2 else (5,6)),ha='right' if i==0 else 'left',textcoords='offset points',fontsize=10)
 ax.scatter(*x,c='#18334f',s=65,zorder=5,label='調査開始点')
 ax.set(xlim=(-1.97,-.35),ylim=(.2,2.3),xlabel='x1',ylabel='x2')
 result='採用して幅を拡大' if a['success'] else '点を保ち幅を半分に'
 ax.set_title(f"調査{a['poll']}  Δ={a['step']:.2f}\n{result}",fontsize=12)
 ax.text(.02,.02,f"採用点の値 {a['next_f']:.3f}\n次の Δ={a['next_step']:.2f} / 累積{a['nfev']}評価",transform=ax.transAxes,fontsize=10,bbox={'facecolor':'white','edgecolor':'none','alpha':.9})
fig.suptitle('4方向をすべて試す座標方向探索  |  改善しない回も探索幅が変わる',fontsize=15)
for ext in ['svg','png']:fig.savefig(MEDIA/f'pattern-search-poll.{ext}',dpi=170)
(OUT/'verified-numbers.json').write_text(json.dumps({'numpy':np.__version__,'matplotlib':matplotlib.__version__,'type':'educational coordinate poll','objective':'(1-x1)^2+20*(x2-x1^2)^2','records':r,'oracle':{'global_minimizer':[1,1],'global_minimum':0},'tests':'passed'},ensure_ascii=False,indent=2)+'\n')
print(json.dumps(r,ensure_ascii=False,indent=2))
