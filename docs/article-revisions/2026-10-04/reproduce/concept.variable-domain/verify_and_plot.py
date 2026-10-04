"""Reproduce the article's production example; no network or extra packages."""
import os
os.environ.setdefault('MPLCONFIGDIR', '/tmp/oc-foundations-mpl')
import json
from pathlib import Path
import numpy as np
import scipy
from scipy.optimize import linprog
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'media'; OUT.mkdir(exist_ok=True)
FONT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
if Path(FONT).exists():
    font_manager.fontManager.addfont(FONT)
    plt.rcParams['font.family'] = 'Noto Sans CJK JP'
plt.rcParams.update({'font.size': 11, 'svg.fonttype': 'path', 'axes.spines.top': False, 'axes.spines.right': False})
A = np.array([[6., 4.], [1., 2.]])
b = np.array([24., 6.]); c = np.array([5., 4.])
r = linprog(-c, A_ub=A, b_ub=b, bounds=(0, None), method='highs')
assert r.success
ints = np.array([(i,j) for i in range(5) for j in range(4) if np.all(A @ [i,j] <= b)])
bins = np.array([(i,j) for i in range(2) for j in range(2) if np.all(A @ [i,j] <= b)])
ibest = ints[np.argmax(ints @ c)]; bbest = bins[np.argmax(bins @ c)]
assert np.allclose(r.x, [3,1.5]) and np.isclose(-r.fun, 21)
assert np.array_equal(ibest,[4,0]) and np.array_equal(bbest,[1,1])
assert np.array_equal(A @ [3,2] - b,[2,1])
assert np.all(A @ [3,1] <= b) and c @ [3,1] == 19
# Independent LP certificate: nonnegative weighted sum of constraints.
y = np.array([.75,.5]); assert np.allclose(y @ A,c); assert y @ b == 21
polygon = np.array([[0,0],[4,0],[3,1.5],[0,3]])
fig, axs = plt.subplots(1,3,figsize=(12,4.4),layout='constrained',sharex=True,sharey=True)
for ax,title in zip(axs,['連続量：面の中を選べる','整数個：格子点を選べる','採否：0か1を選べる']):
    ax.plot(*np.vstack([polygon,polygon[0]]).T,color='#9baec0',lw=1.3)
    ax.set(xlim=(-.25,4.45),ylim=(-.3,3.5),xlabel='製品Aの量  x1',title=title)
    ax.set_xticks(range(5));ax.set_yticks(range(4));ax.grid(alpha=.15);ax.set_aspect('equal')
axs[0].set_ylabel('製品Bの量  x2')
axs[0].fill(*polygon.T,color='#d4e6f5')
axs[1].scatter(*ints.T,s=44,color='#2373a5',zorder=3)
axs[2].scatter(*bins.T,s=55,color='#2373a5',zorder=3)
for ax,point,label,offset in zip(axs,[r.x,ibest,bbest],['(3, 1.5)\n利益 21','(4, 0)\n利益 20','(1, 1)\n利益 9'],[(-12,24),(-75,22),(12,20)]):
    ax.scatter(*point,marker='*',s=210,color='#cf5c2b',zorder=5)
    ax.annotate(label,point,xytext=offset,textcoords='offset points',color='#9b3e18',weight='bold')
axs[1].scatter(3,2,marker='x',s=75,color='#b63242',zorder=6)
axs[1].annotate('丸めた (3, 2)\n制約を2本とも破る',(3,2),xytext=(-82,35),textcoords='offset points',fontsize=10,arrowprops={'arrowstyle':'-','color':'#b63242'})
fig.suptitle('利益と資源の式は同じでも、「選べる集合」が答えを変える',fontsize=15)
for ext in ['svg','png']: fig.savefig(OUT/f'variable-domain-comparison.{ext}',dpi=180)
plt.close(fig)
report={'versions':{'numpy':np.__version__,'scipy':scipy.__version__,'matplotlib':matplotlib.__version__},'continuous':{'x':r.x.tolist(),'profit':float(-r.fun),'slack':(b-A@r.x).tolist(),'upper_bound_certificate_multipliers':y.tolist()},'integer':{'feasible_points':ints.tolist(),'x':ibest.tolist(),'profit':float(ibest@c)},'binary':{'feasible_points':bins.tolist(),'x':bbest.tolist(),'profit':float(bbest@c)},'round_up':{'x':[3,2],'constraint_excess':(A@[3,2]-b).tolist()},'round_down':{'x':[3,1],'profit':19,'slack':(b-A@[3,1]).tolist()},'tests':'all assertions passed'}
(ROOT/'verified-numbers.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
