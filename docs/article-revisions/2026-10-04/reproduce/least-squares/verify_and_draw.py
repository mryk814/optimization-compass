from pathlib import Path
import re,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt,font_manager
P=Path(__file__).parent;s=(P/'least-squares.md').read_text()
for code in re.findall(r'```python\n(.*?)```',s,re.S):exec(code)
q=np.array([1.,.1]);damping=.01;rows=[]
for trial in range(1,9):
 r=residuals(q);J=jacobian(q);H=J.T@J+damping*np.eye(2);step=np.linalg.solve(H,-J.T@r)
 augJ=np.vstack([J,np.sqrt(damping)*np.eye(2)]);augR=np.r_[-r,np.zeros(2)]
 independent=np.linalg.lstsq(augJ,augR,rcond=None)[0];assert np.allclose(step,independent,atol=1e-13)
 cost=.5*r@r;rr=residuals(q+step);cc=.5*rr@rr;pred=cost-.5*np.sum((r+J@step)**2);ratio=(cost-cc)/pred
 accepted=bool(ratio>0);rows.append(dict(trial=trial,current=q.tolist(),damping=damping,cost=float(cost),candidate_cost=float(cc),predicted=float(pred),ratio=float(ratio),accepted=accepted))
 if accepted:q+=step;damping/=3
 else:damping*=10
assert [r['accepted'] for r in rows[:6]]==[True,False,False,False,True,True]
assert all(rows[k]['current']==rows[1]['current'] for k in [2,3,4])
(P/'verified-numbers.json').write_text(json.dumps(rows,indent=2))
font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc');plt.rcParams.update({'font.family':'Noto Sans CJK JP','svg.fonttype':'path','axes.unicode_minus':False})
fig,axs=plt.subplots(2,1,figsize=(8.8,8.2),layout='constrained');fig.set_facecolor('#faf9f5')
for ax in axs:ax.set_facecolor('#faf9f5');ax.spines[['top','right']].set_visible(False);ax.grid(alpha=.12)
ks=[r['trial'] for r in rows]
axs[0].semilogy(ks,[r['cost'] for r in rows],'--o',c='#365467',label='試行直前の現在点の費用')
for accept,color,marker,label in [(True,'#158078','o','受理した候補'),(False,'#bb684c','x','棄却した候補')]:
 subset=[r for r in rows if r['accepted']==accept];axs[0].scatter([r['trial'] for r in subset],[r['candidate_cost'] for r in subset],c=color,marker=marker,s=65,label=label,zorder=4)
axs[0].set(title='① 棄却した点は、現在の推定値に採用しない',ylabel='費用（対数目盛）');axs[0].legend(fontsize=10)
axs[1].semilogy(ks,[r['damping'] for r in rows],'-o',c='#d28a39');axs[1].set(title='② 同じ点で減衰を強めて、もう一度試す',xlabel='試行番号',ylabel='減衰 λ（対数目盛）');axs[1].set_xticks(ks)
fig.suptitle('LMの教材用更新：試すことと、採用することを分ける',fontsize=15)
fig.savefig(P/'media/lm-rejected-trials.svg',bbox_inches='tight');fig.savefig(P/'media/lm-rejected-trials.png',dpi=130,bbox_inches='tight')
print('PASS: both standalone snippets, augmented-LS step oracle, unchanged rejected-state invariant')
