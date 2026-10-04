from pathlib import Path
import json,re
import numpy as np
from scipy.optimize import minimize
import scipy
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt,font_manager
P=Path(__file__).parent
text=(P/'bfgs.md').read_text();exec(re.search(r'```python\n(.*?)```',text,re.S).group(1))
A=np.diag([2.,40.]);x=np.array([4.,3.]);c=np.array([1.,-2.]);g=A@(x-c);p=-g
alpha=-g@p/(p@A@p);s=alpha*p;y=A@s;rho=1/(y@s)
H=(np.eye(2)-rho*np.outer(s,y))@(np.eye(2)-rho*np.outer(y,s))+rho*np.outer(s,s)
assert np.allclose(H@y,s)
assert H[1,1]!=.025
print('H1:',H)
D=-(g@p)*alpha/2
records=[]
for t in [.01,.5,1.,1.95,2.1]:
 al=t*alpha
 f0=.5*(x-c)@A@(x-c);xx=x+al*p;ff=.5*(xx-c)@A@(xx-c)
 change=(ff-f0)/D;arm=ff<=f0+1e-4*al*(g@p)
 strong=abs((A@(xx-c))@p)<=.9*abs(g@p)
 weak=(A@(xx-c))@p>=.9*(g@p)
 assert np.isclose(change,t*t-2*t)
 records.append(dict(t=t,change=change,armijo=bool(arm),strong=bool(strong),weak=bool(weak)))
assert [(r['armijo'],r['strong']) for r in records]==[(True,False),(True,True),(True,True),(True,False),(False,False)]
(P/'verified-numbers.json').write_text(json.dumps(dict(scipy=scipy.__version__,alpha_star=float(alpha),D=float(D),H1=H.tolist(),trials=records),indent=2))
font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams.update({'font.family':'Noto Sans CJK JP','svg.fonttype':'path','axes.unicode_minus':False})
fig,ax=plt.subplots(figsize=(9,5.6),layout='constrained');fig.set_facecolor('#faf9f5');ax.set_facecolor('#faf9f5')
t=np.linspace(0,2.2,500)
ax.axvspan(.1,1.9,alpha=.12,color='#158078',label='Armijo + 強い曲率条件の受理範囲')
ax.plot(t,t*t-2*t,color='#365467',lw=2.5,label='直線上の目的変化（正規化）')
ax.plot(t,-2e-4*t,'--',color='#d28a39',lw=1.8,label='Armijo の上限')
for r in records:
 ax.scatter(r['t'],r['change'],s=45,color='#158078' if r['armijo'] and r['strong'] else '#bb684c',zorder=5)
ax.annotate('小さすぎる一歩も\nArmijo だけなら通る',(.01,-.0199),(.12,-.31),arrowprops={'arrowstyle':'->','color':'#bb684c'},fontsize=10)
ax.annotate('最小点まで進まなくてもよい',(.5,-.75),(.13,-1.05),arrowprops={'arrowstyle':'->','color':'#158078'},fontsize=10)
ax.annotate('通り越した上りが急すぎる',(1.95,-.0975),(1.11,.25),arrowprops={'arrowstyle':'->','color':'#bb684c'},fontsize=10)
ax.set(xlim=(-.03,2.22),ylim=(-1.24,.49),xlabel='歩幅の比 t = α / α*（1 が直線上の最小点）',ylabel='目的変化 / 厳密直線探索での減少量',title='BFGS の直線探索：下がっただけでは、まだ足りない')
ax.legend(loc='lower right',fontsize=9);ax.spines[['top','right']].set_visible(False);ax.grid(alpha=.12)
fig.savefig(P/'media/bfgs-line-search-window.svg',bbox_inches='tight');fig.savefig(P/'media/bfgs-line-search-window.png',dpi=130,bbox_inches='tight')
print('PASS: article scipy code, secant identity and five independent line-search trials')
