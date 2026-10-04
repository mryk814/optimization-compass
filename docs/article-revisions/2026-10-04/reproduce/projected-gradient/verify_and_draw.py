from pathlib import Path
import re,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt,font_manager
P=Path(__file__).parent;s=(P/'projected-gradient.md').read_text();exec(re.search(r'```python\n(.*?)```',s,re.S).group(1))
answer=(1-1/np.sqrt(2))*np.ones(2);eta=.25;rows=[]
for x in [np.array([.375,.375]),answer]:
 trial=x-eta*2*x;out=project_disk(trial);mapping=(x-out)/eta
 assert np.linalg.norm(out-center)<=1+1e-14
 d=out-x;assert 2*x@d<=-d@d/eta+1e-13
 assert objective(out)<=objective(x)-(1/eta-1)*d@d+1e-13
 rows.append(dict(x=x.tolist(),trial=trial.tolist(),out=out.tolist(),mapping_norm=float(np.linalg.norm(mapping)),gradient_norm=float(np.linalg.norm(2*x))))
assert np.isclose(np.sum((np.array([.1875,.1875])-center)**2),1.3203125)
rng=np.random.default_rng(11)
for _ in range(1000):
 q=rng.normal(size=2);q=center+q/max(np.linalg.norm(q),1)
 assert (2*answer)@(q-answer)>-1e-13
(P/'verified-numbers.json').write_text(json.dumps(rows,indent=2))
font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc');plt.rcParams.update({'font.family':'Noto Sans CJK JP','svg.fonttype':'path','axes.unicode_minus':False})
fig,axs=plt.subplots(1,2,figsize=(10,5.3),layout='constrained');fig.set_facecolor('#faf9f5')
for ax,r,ttl in zip(axs,rows,['反復2：戻しても、まだ少し進む','反復3：戻すと同じ点になる']):
 ax.set_facecolor('#faf9f5');angle=np.linspace(0,2*np.pi,1000);ax.fill(1+np.cos(angle),1+np.sin(angle),color='#158078',alpha=.08);ax.plot(1+np.cos(angle),1+np.sin(angle),c='#158078',lw=2)
 x=np.array(r['x']);trial=np.array(r['trial']);out=np.array(r['out'])
 ax.annotate('',trial,x,arrowprops={'arrowstyle':'->','color':'#365467','lw':2.5})
 offset=np.array([-.008,.008]);ax.annotate('',out+offset,trial+offset,arrowprops={'arrowstyle':'->','color':'#d28a39','lw':2.5})
 ax.scatter(*x,c='#365467',s=60);ax.scatter(*trial,c='#365467',s=40,marker='x');ax.scatter(*out,edgecolors='#d28a39',s=100,marker='o',facecolors='none',linewidths=2)
 ax.annotate('現在点',x,xytext=(x[0]+.03,x[1]-.035),fontsize=11);ax.annotate('勾配の候補',trial,xytext=(trial[0]+.02,trial[1]-.06),fontsize=10);ax.annotate('射影後',out,xytext=(out[0]-.16,out[1]+.015),fontsize=11)
 ax.set(xlim=(.05,.52),ylim=(.05,.52),xlabel='x1',ylabel='x2',title=ttl);ax.set_aspect('equal');ax.spines[['top','right']].set_visible(False);ax.grid(alpha=.12)
fig.suptitle('射影勾配法：勾配の候補と、実際に動いた先を分ける',fontsize=15)
fig.savefig(P/'media/projected-gradient-disk-step.svg',bbox_inches='tight');fig.savefig(P/'media/projected-gradient-disk-step.png',dpi=140,bbox_inches='tight')
print('PASS: article code, projection/feasibility/descent bounds, 1000 feasible-direction checks')
