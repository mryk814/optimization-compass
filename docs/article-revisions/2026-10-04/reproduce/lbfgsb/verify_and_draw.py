from pathlib import Path
import re,json
import numpy as np
import scipy
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt,font_manager
P=Path(__file__).parent;s=(P/'lbfgsb.md').read_text();exec(re.search(r'```python\n(.*?)```',s,re.S).group(1))
assert result.success and np.allclose(result.x,[1,-1])
assert all(np.all(p>=lower) and np.all(p<=upper) for p in path)
assert np.isclose(np.linalg.norm(gradient(result.x)),40)
assert np.linalg.norm(projected,np.inf)<1e-8
assert path[1][0]==0 and path[2][0]>0
rows=[dict(k=k,x=p.tolist(),f=objective(p),gradient=gradient(p).tolist(),mapping=(p-np.clip(p-gradient(p),lower,upper)).tolist()) for k,p in enumerate(path)]
(P/'verified-numbers.json').write_text(json.dumps(dict(scipy=scipy.__version__,rows=rows),indent=2))
font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc');plt.rcParams.update({'font.family':'Noto Sans CJK JP','svg.fonttype':'path','axes.unicode_minus':False})
fig,axs=plt.subplots(2,1,figsize=(8,8.8),layout='constrained',gridspec_kw={'height_ratios':[1.8,1]});fig.set_facecolor('#faf9f5')
pts=np.array(path)
for ax in axs:ax.set_facecolor('#faf9f5');ax.spines[['top','right']].set_visible(False);ax.grid(alpha=.12)
ax=axs[0];ax.fill([0,5,5,0],[-1,-1,5,5],c='#158078',alpha=.08);ax.plot([0,5,5,0,0],[-1,-1,5,5,-1],c='#158078',lw=1.5);ax.plot(pts[:,0],pts[:,1],'-o',c='#365467',ms=6)
ax.scatter([1],[-2],marker='x',c='#d28a39',s=80);ax.annotate('無制約の答え (1, −2)',(1,-2),xytext=(1.4,-2),fontsize=10)
ax.annotate('出発点 (4, 3)',(4,3),xytext=(3.1,3.45),fontsize=11);ax.annotate('箱の答え (1, −1)',(1,-1),xytext=(1.5,-.3),arrowprops={'arrowstyle':'->','color':'#365467'},fontsize=11)
ax.set(xlim=(-.4,5.4),ylim=(-2.5,5.4),xlabel='x',ylabel='y',title='① 許された箱の中で、同じ目的を最小化する');ax.set_aspect('equal')
ax=axs[1];ax.axhline(-1,c='#158078',lw=2)
ax.plot(pts[1:,0],pts[1:,1],'-o',c='#365467',ms=7)
for i in [1,2]:ax.annotate('',pts[i+1],pts[i],arrowprops={'arrowstyle':'->','color':'#365467','lw':2})
for i in range(1,len(pts)):ax.annotate(f'反復{i}',pts[i],xytext=(pts[i,0],-1.065 if i%2 else -.94),fontsize=11,ha='center')
ax.set(xlim=(-.12,1.15),ylim=(-1.14,-.85),xlabel='x（下辺の拡大）',ylabel='y',title='② 下限の x = 0 から離れ、自由な向きへ進む')
fig.suptitle('L-BFGS-B：境界に着いても、永久に固定されるわけではない',fontsize=14)
fig.savefig(P/'media/lbfgsb-bound-release.svg',bbox_inches='tight');fig.savefig(P/'media/lbfgsb-bound-release.png',dpi=130,bbox_inches='tight')
print('PASS: original SciPy trace, bound feasibility, final KKT/map and active-bound release')
