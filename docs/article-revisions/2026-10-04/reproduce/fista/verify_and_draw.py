from pathlib import Path
import re,json,math
import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt,font_manager
P=Path(__file__).parent;s=(P/'fista.md').read_text();exec(re.search(r'```python\n(.*?)```',s,re.S).group(1))
x=y=0.;t=1.;basic=0.;best=4.5;rows=[]
for k in range(1,31):
 xn=prox_step(y);tn=(1+math.sqrt(1+4*t*t))/2;yn=xn+(t-1)/tn*(xn-x);basic=prox_step(basic);best=min(best,objective(xn))
 assert abs(mapping(xn)-(xn-2.2))<2e-14
 rows.append(dict(k=k,x=xn,y=yn,basic=basic,F=objective(xn),gap=objective(xn)-2.08,best_gap=best-2.08,mapping=abs(mapping(xn))))
 x,y,t=xn,yn,tn
assert rows[7]['F']>rows[6]['F'] and rows[8]['F']>rows[7]['F']
assert np.isclose(rows[2]['basic'],1.271875)
assert abs(soft(0.-1.*(0.-3),.8)-2.2)<1e-14
(P/'verified-numbers.json').write_text(json.dumps(rows,indent=2))
font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc');plt.rcParams.update({'font.family':'Noto Sans CJK JP','svg.fonttype':'path','axes.unicode_minus':False})
fig,axs=plt.subplots(2,1,figsize=(8.7,8.7),layout='constrained');fig.set_facecolor('#faf9f5');ks=[r['k'] for r in rows]
for ax in axs:ax.set_facecolor('#faf9f5');ax.spines[['top','right']].set_visible(False);ax.grid(alpha=.12)
axs[0].plot(ks,[r['x'] for r in rows],'-o',c='#158078',ms=3,label='FISTA（再始動なし）')
axs[0].plot(ks,[r['basic'] for r in rows],'--',c='#365467',label='近接勾配法（同じ歩幅）');axs[0].axhline(2.2,c='#d28a39',lw=1,label='答え 2.2');axs[0].set(title='① 外挿で先へ出る。答えを越えることもある',ylabel='反復点 x');axs[0].legend(fontsize=10,loc='lower right')
axs[1].semilogy(ks,[r['gap'] for r in rows],'-o',ms=3,c='#158078',label='FISTA：現在の目的ギャップ')
axs[1].semilogy(ks,[r['best_gap'] for r in rows],'--',c='#bb684c',label='FISTA：これまでの最良ギャップ');axs[1].semilogy(ks,[objective(r['basic'])-2.08 for r in rows],':',c='#365467',label='近接勾配法：目的ギャップ')
axs[1].set(title='② 現在値は振動する。最良値とは分けて読む',xlabel='反復番号',ylabel='F(x) − F*（対数目盛）');axs[1].legend(fontsize=9,loc='upper right')
fig.suptitle('FISTA：加速は、毎回の単調な改善ではない',fontsize=16)
fig.savefig(P/'media/fista-overshoot.svg',bbox_inches='tight');fig.savefig(P/'media/fista-overshoot.png',dpi=130,bbox_inches='tight')
print('PASS: exact article snippet, scalar mapping identity, basic-step and oscillation checks')
