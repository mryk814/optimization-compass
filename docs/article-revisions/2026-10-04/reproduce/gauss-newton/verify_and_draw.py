from pathlib import Path
import re,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt,font_manager
P=Path(__file__).parent;s=(P/'gauss-newton.md').read_text();exec(re.search(r'```python\n(.*?)```',s,re.S).group(1))
x=np.array([1.,.1]);x+=np.linalg.lstsq(jacobian(x),-residuals(x),rcond=None)[0]
r=residuals(x);J=jacobian(x);p=np.linalg.lstsq(J,-r,rcond=None)[0];pred=r+J@p;actual=residuals(x+p)
assert np.allclose(J.T@pred,0,atol=1e-13)
assert .5*actual@actual>.5*r@r>.5*pred@pred
rng=np.random.default_rng(11)
errs=[]
for _ in range(20):
 v=rng.normal(size=2);eps=1e-6
 fd=(residuals(x+eps*v)-residuals(x-eps*v))/(2*eps)
 errs.append(float(np.max(abs(fd-J@v))))
assert max(errs)<1e-8
negstep=np.linalg.lstsq(-J,r,rcond=None)[0];assert np.allclose(negstep,p)
(P/'verified-numbers.json').write_text(json.dumps(dict(current=x.tolist(),step=p.tolist(),predicted=pred.tolist(),actual=actual.tolist(),max_jac_error=max(errs)),indent=2))
font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc');plt.rcParams.update({'font.family':'Noto Sans CJK JP','svg.fonttype':'path','axes.unicode_minus':False})
fig,ax=plt.subplots(figsize=(8.5,5.5),layout='constrained');fig.set_facecolor('#faf9f5');ax.set_facecolor('#faf9f5')
ax.bar(t-.18,pred,.36,color='#365467',label='予想：線形化した残差 r + Jp');ax.bar(t+.18,actual,.36,color='#d28a39',label='実測：非線形モデルの残差 r(x + p)')
ax.axhline(0,c='#72818a',lw=.7);ax.set_xticks(t);ax.set(xlabel='観測時刻 t',ylabel='残差（予測 − 観測）',title='Gauss–Newton：線形計算が解けても、その予想が当たるとは限らない');ax.legend(fontsize=10);ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',alpha=.12)
fig.savefig(P/'media/gauss-newton-residual-prediction.svg',bbox_inches='tight');fig.savefig(P/'media/gauss-newton-residual-prediction.png',dpi=140,bbox_inches='tight')
print('PASS: article trace, predicted residual LS optimality, 20 Jacobian directions and sign-invariance')
