from pathlib import Path
import json, re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
P=Path(__file__).parent
text=(P/'augmented-lagrangian.md').read_text()
code=re.search(r'```python\n(.*?)```',text,re.S).group(1)
exec(code)
rows=[]
l=0.;rho=1.;a=np.ones(2);t=np.array([3.,2.]);H=2*np.eye(2)+rho*np.outer(a,a)
for k in range(28):
 x=np.linalg.solve(H,2*t+(3*rho-l)*a);h=float(a@x-3);next_l=l+rho*h
 assert np.isclose(h,2**(-k),rtol=0,atol=2e-15)
 assert np.linalg.norm(2*(x-t)+next_l*a,np.inf)<1e-12
 rows.append(dict(k=k,x=x.tolist(),residual=h,multiplier=l,next_multiplier=next_l,f=float((x-t)@(x-t))))
 l=next_l
assert rows[-2]['residual']>=1e-8 and rows[-1]['residual']<1e-8
for rho in [0.1,1.,10.,100.,1000.]:
 H=2*np.eye(2)+rho*np.outer(a,a)
 assert np.isclose(np.linalg.cond(H),1+rho)
 for l in [0.,.5,1.,2.,3.]:
  x=np.linalg.solve(H,2*t+(3*rho-l)*a)
  assert np.isclose(a@x-3,(2-l)/(1+rho),atol=2e-13)
(P/'verified-numbers.json').write_text(json.dumps(rows,indent=2))
font=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams.update({'font.family':font.get_name(),'svg.fonttype':'path','axes.unicode_minus':False})
from matplotlib import font_manager
font_manager.fontManager.addfont(font.get_file())
fig,axs=plt.subplots(2,1,figsize=(9,9),gridspec_kw={'height_ratios':[1.45,1]},layout='constrained')
fig.set_facecolor('#faf9f5')
for ax in axs: ax.set_facecolor('#faf9f5');ax.spines[['top','right']].set_visible(False)
ax=axs[0]
xx,yy=np.meshgrid(np.linspace(.8,3.5,160),np.linspace(-.2,2.5,160))
ax.contour(xx,yy,(xx-3)**2+(yy-2)**2,levels=[.125,.5,1.125,2.,3.125],colors='#bcc9ce',linewidths=.8)
xline=np.linspace(.8,3.3,100)
ax.plot(xline,3-xline,c='#365467',lw=2,label='制約 x1 + x2 = 3')
pts=np.array([r['x'] for r in rows[:5]])
ax.plot(pts[:,0],pts[:,1],'o-',color='#158078',lw=2,ms=6,label='内側の解：ρ = 1 のまま')
ax.scatter([3],[2],marker='x',s=80,color='#d28a39')
ax.annotate('制約なしの最小点 (3, 2)',(3,2),xytext=(2.25,2.25),fontsize=11)
ax.scatter([2],[1],color='#365467',s=55)
ax.annotate('制約付きの答え (2, 1)',(2,1),xytext=(1.0,.30),arrowprops={'arrowstyle':'->','color':'#365467'},fontsize=11)
ax.annotate('最初の内側の解 (2.5, 1.5)',(2.5,1.5),xytext=(2.48,.60),arrowprops={'arrowstyle':'->','color':'#158078'},fontsize=10)
ax.set(xlim=(.85,3.4),ylim=(-.05,2.5),xlabel='x1',ylabel='x2',title='① 乗数を更新すると、次に目指す点が制約へ寄る')
ax.set_aspect('equal');ax.legend(loc='lower left',fontsize=9)
ax=axs[1]
k=np.arange(7);errs=2.**(-k)
ax.semilogy(k,errs,'o-',c='#158078',lw=2,label='拡張Lagrangian法：乗数を更新')
ax.semilogy(k,np.ones(7),'--',c='#d28a39',lw=2,label='純粋なペナルティ法：ρ = 1 固定')
ax.set(xlabel='外側の反復 k（0が最初の内側の解）',ylabel='制約残差 |h|（対数目盛）',title='② 残差は半分へ。ペナルティの強さは変えていない')
ax.set_xticks(k);ax.legend(fontsize=9,loc='lower left');ax.grid(alpha=.15)
fig.suptitle('拡張Lagrangian法：罰を強める代わりに、乗数を直す',fontsize=16)
fig.savefig(P/'media/augmented-lagrangian-multiplier.svg',bbox_inches='tight')
fig.savefig(P/'media/augmented-lagrangian-multiplier.png',dpi=130,bbox_inches='tight')
print('PASS: exact article code, 28 residuals, 25 inner solutions, five condition numbers')
