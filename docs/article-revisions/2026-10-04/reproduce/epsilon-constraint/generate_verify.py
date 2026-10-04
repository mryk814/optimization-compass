"""Enumerate the original bounded production model and each epsilon problem."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/discrete-mpl');os.environ.setdefault('XDG_CACHE_HOME','/tmp/discrete-cache')
from pathlib import Path
from fractions import Fraction as F
import json,platform,numpy as np,scipy
from scipy.optimize import milp,LinearConstraint,Bounds
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
P=Path(__file__).resolve().parent
font=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc');plt.rcParams.update({'font.family':font.get_name(),'font.size':11,'svg.fonttype':'path'})
plans=[{'x':x,'y':y,'output':3*x+2*y,'cost':8*x+7*y,'emissions':6*x+2*y} for x in range(11) for y in range(11) if 3*x+2*y>=18]
def dominated(a,b):return b['cost']<=a['cost'] and b['emissions']<=a['emissions'] and (b['cost']<a['cost'] or b['emissions']<a['emissions'])
front=sorted([a for a in plans if not any(dominated(a,b) for b in plans)],key=lambda x:x['emissions'])
def solve(e):
 eligible=[p for p in plans if p['emissions']<=e]
 return min(eligible,key=lambda p:(p['cost'],p['emissions'],p['x'],p['y'])) if eligible else None
assert len(plans)==88 and len(front)==4
checks=[]
for e in [36,30,24,18,12]:
 best=solve(e)
 r=milp(c=[8,7],integrality=[1,1],bounds=Bounds([0,0],[10,10]),constraints=LinearConstraint([[3,2],[6,2]],[18,-np.inf],[np.inf,e]))
 if best is None:assert r.status==2
 else:
  assert r.success and abs(r.fun-best['cost'])<1e-9
  assert best in front
  assert F(best['cost'])==78-F(5,6)*e
 checks.append({'epsilon':e,'plan':best,'milp_status':r.status,'milp_fun':float(r.fun) if r.fun is not None else None})
assert solve(29.9)==solve(24)
assert solve(25)==solve(26)==solve(27)==solve(24)
# A wider box independently confirms that bounds 10 do not hide nondominated points here.
wide=[{'x':x,'y':y,'output':3*x+2*y,'cost':8*x+7*y,'emissions':6*x+2*y} for x in range(31) for y in range(31) if 3*x+2*y>=18]
wide_front=[a for a in wide if not any(dominated(a,b) for b in wide)]
assert sorted(wide_front,key=lambda x:x['emissions'])==front
# All four are supported: cost+(5/6)*emission equals 78.
assert all(F(p['cost'])+F(5,6)*p['emissions']==78 for p in front)
fig,ax=plt.subplots(figsize=(10.8,4.7),layout='constrained')
ax.axvspan(12,18,color='#f4d8d2',alpha=.75)
ax.text(15,55,'実行不能\n排出の下限は18',ha='center',va='center',color='#a65545',fontsize=12)
for left,right,cost in [(18,24,63),(24,30,58),(30,36,53),(36,40,48)]:
 ax.plot([left,right],[cost,cost],color='#3c8c7c',lw=3)
 ax.scatter([left],[cost],color='#3c8c7c',s=60,zorder=4)
 if right!=40:ax.scatter([right],[cost],facecolors='white',edgecolors='#3c8c7c',s=60,zorder=5,linewidth=2)
for e,x,y,c in [(18,0,9,63),(24,2,6,58),(30,4,3,53),(36,6,0,48)]:
 ax.annotate(f'X={x}, Y={y}\n費用{c}',xy=(e,c),xytext=(8,12),textcoords='offset points',fontsize=11,color='#276d61')
ax.scatter([29.9],[58],color='#d18b39',s=50,zorder=6)
ax.annotate('ε: 30 → 29.9\n費用: 53 → 58',xy=(29.9,58),xytext=(32,61.5),arrowprops={'arrowstyle':'->','color':'#b9792e'},color='#a36a28',fontsize=11)
ax.set(xlim=(12,40),ylim=(45,68),xlabel='排出上限 ε（右ほど緩い）',ylabel='最小費用',title='上限を少し変えても、整数計画の選択は滑らかに動かない');ax.set_xticks([12,18,24,30,36,40]);ax.grid(alpha=.15);ax.set_axisbelow(True)
for ext in ['svg','png']:fig.savefig(P/f'epsilon-constraint-threshold-steps.{ext}',dpi=180)
report={'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'domain':'X,Y integers in 0..10; output>=18','total_grid_points':121,'demand_feasible_plans':len(plans),'pareto_plans':front,'epsilon_results':checks,'epsilon_29_9':solve(29.9),'emission_lower_bound':18,'cost_lower_bound_formula':'78 - 5*epsilon/6','all_four_frontier_points_supported_at_cost_plus_lambda_emissions':{'lambda':'5/6','common_score':78,'normalized_cost_weight':'6/11'},'wide_box_0_30_same_frontier':True,'all_plans':plans,'tie_breaking':'lexicographic (cost, emissions, X, Y)'}
(P/'verified-numbers.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'plans':len(plans),'front':front,'eps':checks},ensure_ascii=False))
