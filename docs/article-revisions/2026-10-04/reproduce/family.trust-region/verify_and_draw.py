from pathlib import Path
import re,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt,font_manager
P=Path(__file__).parent
text=(P/'family-trust-region.md').read_text();exec(re.search(r'```python\n(.*?)```',text,re.S).group(1))
rows=[]
for d in [2.,.5]:
 ps=np.linspace(-d,d,10001);vals=np.array([model(float(p)) for p in ps]);assert ps[np.argmin(vals)]==d
 pred=model(0)-model(d);actual=f(.5)-f(.5+d)
 rows.append(dict(radius=d,step=d,trial_x=.5+d,predicted=pred,actual=actual,ratio=actual/pred))
assert rows[0]['ratio']==-5.4 and abs(rows[1]['ratio']-9/14)<1e-14
(P/'verified-numbers.json').write_text(json.dumps(rows,indent=2))
font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc');plt.rcParams.update({'font.family':'Noto Sans CJK JP','svg.fonttype':'path','axes.unicode_minus':False})
fig,axs=plt.subplots(2,1,figsize=(8.4,9),layout='constrained');fig.set_facecolor('#faf9f5')
for ax,r in zip(axs,rows):
 d=r['radius'];ps=np.linspace(-d,d,401)
 ax.set_facecolor('#faf9f5');ax.plot(ps,[f(.5+p) for p in ps],c='#365467',lw=2.4,label='実際の f(0.5 + p)');ax.plot(ps,[model(p) for p in ps],'--',c='#d28a39',lw=2,label='現在点の二次モデル m(p)')
 ax.scatter([0],[f(.5)],c='#365467',s=40);ax.axvline(0,c='#a9b2b5',lw=.8)
 ax.plot([d,d],[model(d),f(.5+d)],c='#bb684c',lw=2);ax.scatter([d],[f(.5+d)],c='#bb684c' if d==2 else '#158078',s=65)
 ax.set(xlabel='移動量 p（0 が現在点）',ylabel='関数値',title=f"半径 {d:g}："+('近似では下がるのに、実際には上がる → 棄却' if d==2 else '予測ほどではないが実際に下がる → 受理'))
 ax.spines[['top','right']].set_visible(False);ax.legend(fontsize=10);ax.grid(alpha=.13)
fig.suptitle('信頼領域：棄却したら、同じ場所から狭く試す',fontsize=16)
fig.savefig(P/'media/trust-region-model-agreement.svg',bbox_inches='tight');fig.savefig(P/'media/trust-region-model-agreement.png',dpi=130,bbox_inches='tight')
print('PASS: article code, exact ratios and 20002-point independent endpoint oracle')
