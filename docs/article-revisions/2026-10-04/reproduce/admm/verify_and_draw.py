from pathlib import Path
import re,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt,font_manager
P=Path(__file__).parent
s=(P/'admm.md').read_text();exec(re.search(r'```python\n(.*?)```',s,re.S).group(1))
z=0.;u=0.;rows=[]
for k in range(1,11):
 x=(3+z-u)/2;oldz=z;z=max(x+u-.8,0);u+=x-z
 primal=x-z;dual=z-oldz
 assert abs((x-3)+u+dual)<1e-14
 assert abs(u-.8)<1e-14
 F=.5*(z-3)**2+.8*abs(z)
 rows.append(dict(k=k,x=x,z=z,u=u,primal=primal,dual=dual,F=F,gap=F-2.08))
assert np.allclose([r['F'] for r in rows[:4]],[3.205,2.36125,2.1503125,2.097578125])
assert abs(rows[1]['primal'])<1e-14 and abs(rows[1]['dual']-.75)<1e-14
(P/'verified-numbers.json').write_text(json.dumps(rows,indent=2))
font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc');plt.rcParams.update({'font.family':'Noto Sans CJK JP','svg.fonttype':'path','axes.unicode_minus':False})
fig,axs=plt.subplots(2,1,figsize=(8.7,8),layout='constrained');fig.set_facecolor('#faf9f5');ks=[r['k'] for r in rows]
for ax in axs:ax.set_facecolor('#faf9f5');ax.spines[['top','right']].set_visible(False);ax.set_xticks(ks);ax.grid(alpha=.12)
axs[0].plot(ks,[r['x'] for r in rows],'-o',c='#365467',label='x：データへの近さ',ms=6)
axs[0].plot(ks,[r['z'] for r in rows],'--o',mfc='none',c='#d28a39',label='z：L1正則化',ms=10)
axs[0].axhline(2.2,c='#158078',lw=1,label='答え 2.2')
axs[0].set(title='① 2反復目から x と z が重なる。それでも答えにはまだ遠い',ylabel='変数の値');axs[0].legend(fontsize=10,loc='lower right')
axs[1].plot(ks,[abs(r['primal']) for r in rows],'-o',c='#158078',label='主残差 |x − z|')
axs[1].plot(ks,[abs(r['dual']) for r in rows],'-o',c='#bb684c',label='双対残差 ρ |z − 前のz|')
axs[1].set(title='② 主残差が消えても、双対残差が残っている',xlabel='反復番号（1 が最初の更新）',ylabel='残差の大きさ');axs[1].legend(fontsize=10)
fig.suptitle('ADMM：同じ値を持つことと、最適であることは違う',fontsize=16)
fig.savefig(P/'media/admm-two-residuals.svg',bbox_inches='tight');fig.savefig(P/'media/admm-two-residuals.png',dpi=130,bbox_inches='tight')
print('PASS: vector article code, scalar table, primal/dual stationarity identity')
